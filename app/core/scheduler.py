"""
Scheduler de notificaciones de vencimiento.
Corre todos los días a las 7:00 AM (hora Colombia) y envía
un correo a los administradores con las reclamaciones próximas
a vencer o ya vencidas.
"""
from datetime import date

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

from app.core.database import SessionLocal
from app.core.email import enviar_correo_vencimientos
from app.core.files import dias_habiles_transcurridos
from app.core.tokens import generar_url_acceso
from app.models.claims import NotificacionEnviada, Reclamacion
from app.models.users import Usuario

# Estados activos donde todavía puede vencer el plazo
ESTADOS_ACTIVOS = ["abierta", "en_gestion"]


def verificar_vencimientos(correo_prueba: str = None) -> None:
    """Revisa todas las reclamaciones activas y envía alertas si corresponde.
    Si correo_prueba está definido, envía solo a ese correo (modo test)."""
    print("[SCHEDULER] Verificando vencimientos...")
    db = SessionLocal()
    try:
        hoy = date.today()

        reclamaciones = (
            db.query(Reclamacion)
            .filter(Reclamacion.estado.in_(ESTADOS_ACTIVOS))
            .all()
        )

        alertas  = []   # 8 <= días < límite
        vencidas = []   # días >= límite

        for rec in reclamaciones:
            dias = dias_habiles_transcurridos(rec.fecha_reporte)

            # ¿Ya se notificó hoy esta reclamación?
            ya_enviada = (
                db.query(NotificacionEnviada)
                .filter(
                    NotificacionEnviada.reclamacion_id == rec.id,
                    NotificacionEnviada.fecha == hoy,
                )
                .first()
            )
            if ya_enviada:
                continue

            datos = {
                "id":             rec.id,
                "vin":            rec.vin,
                "vehiculo":       rec.vehiculo,
                "transportadora": rec.transportadora,
                "dias_habiles":   dias,
                "dias_limite":    rec.dias_limite,
                "responsable":    rec.responsable_actual,
            }

            if dias >= rec.dias_limite:
                vencidas.append(datos)
            elif dias >= 8:
                alertas.append(datos)

        if not alertas and not vencidas:
            print("[SCHEDULER] Sin novedades de vencimiento hoy.")
            return

        # Destinatarios: todos los admin activos
        admins = (
            db.query(Usuario)
            .filter(Usuario.rol == "admin", Usuario.activo.is_(True))
            .all()
        )

        if not admins:
            print("[SCHEDULER] No hay administradores con correo registrado.")
            return

        # En modo prueba, enviar solo al correo de prueba (sin token, sin registrar)
        if correo_prueba:
            print(f"[SCHEDULER] Modo prueba – enviando a {correo_prueba}")
            enviar_correo_vencimientos([correo_prueba], alertas, vencidas)
        else:
            # Envío real: correo individual con magic link por admin
            for u in admins:
                if u.email:
                    url = generar_url_acceso(db, u.email, "/reclamaciones")
                    enviar_correo_vencimientos([u.email], alertas, vencidas, url_acceso=url)

        # Solo registrar en DB si es ejecución real (no prueba)
        # En modo prueba el correo fue a un destino alternativo → no marcar como enviado
        # para que el scheduler real del día siga funcionando
        if not correo_prueba:
            for item in alertas:
                db.add(NotificacionEnviada(
                    reclamacion_id=item["id"],
                    tipo="alerta",
                    fecha=hoy,
                ))
            for item in vencidas:
                db.add(NotificacionEnviada(
                    reclamacion_id=item["id"],
                    tipo="vencida",
                    fecha=hoy,
                ))
            db.commit()
            print(f"[SCHEDULER] {len(alertas)} alertas y {len(vencidas)} vencidas notificadas.")
        else:
            print(f"[SCHEDULER] Modo prueba – notificaciones NO registradas en DB.")

    except Exception as exc:
        print(f"[SCHEDULER] Error al enviar correo: {exc}. Las notificaciones NO fueron registradas y se reintentarán.")
    finally:
        db.close()


# ── Instancia del scheduler ───────────────────────────────────────────────────

scheduler = BackgroundScheduler(timezone="America/Bogota")

# Todos los días a las 7:00 AM hora Colombia
scheduler.add_job(
    verificar_vencimientos,
    CronTrigger(hour=7, minute=0, timezone="America/Bogota"),
    id="verificar_vencimientos",
    replace_existing=True,
    misfire_grace_time=3600,   # si el servidor estaba apagado, ejecuta hasta 1h tarde
)
