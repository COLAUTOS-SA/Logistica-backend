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
from app.models.claims import NotificacionEnviada, Reclamacion
from app.models.users import Usuario

# Estados activos donde todavía puede vencer el plazo
ESTADOS_ACTIVOS = ["abierta", "en_gestion"]


def verificar_vencimientos() -> None:
    """Revisa todas las reclamaciones activas y envía alertas si corresponde."""
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
        destinatarios = [u.email for u in admins if u.email]

        if not destinatarios:
            print("[SCHEDULER] No hay administradores con correo registrado.")
            return

        enviar_correo_vencimientos(destinatarios, alertas, vencidas)

        # Solo registrar si el correo se envió sin errores
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
