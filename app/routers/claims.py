import os
import shutil
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.email import enviar_correo_nueva_reclamacion, enviar_correo_colision
from app.core.tokens import generar_url_acceso
from app.core.files import guardar_archivo, dias_habiles_transcurridos, BASE_ARCHIVOS
from app.models.claims import Reclamacion, Archivo, HistorialMovimiento
from app.models.users import Usuario
from app.schemas.claims import (
    ReclamacionCreate, ReclamacionResponse, ArchivoResponse,
    CambiarEstadoRequest, SubirCotizacionRequest
)

router = APIRouter(prefix="/reclamaciones", tags=["Reclamaciones"])

ESTADOS_VALIDOS = [
    "abierta", "en_gestion", "radicada_vigia",
    "aprobada", "en_facturacion", "cerrada"
]


# ── Helpers ──────────────────────────────────────────────────────────────────

def _generar_id(db: Session) -> str:
    año = datetime.now().year
    # Contar reclamaciones del año actual
    prefijo = f"REC-{año}-"
    cantidad = db.query(Reclamacion).filter(
        Reclamacion.id.like(f"{prefijo}%")
    ).count()
    return f"{prefijo}{str(cantidad + 1).zfill(3)}"


def _build_response(rec: Reclamacion, base_url: str = "https://logistica.colautos.co/api") -> dict:
    """Construye la respuesta con dias_habiles calculado y URLs de archivos."""
    dias = dias_habiles_transcurridos(rec.fecha_reporte)
    archivos = [
        ArchivoResponse(
            id=a.id,
            categoria=a.categoria,
            nombre_original=a.nombre_original,
            url=f"{base_url}/archivos/{a.ruta_relativa.replace(os.sep, '/')}",
            subido_por=a.subido_por,
            fecha_subida=a.fecha_subida,
        )
        for a in rec.archivos
    ]
    return {**rec.__dict__, "dias_habiles": dias, "archivos": archivos}


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.get("/", response_model=List[ReclamacionResponse])
def listar_reclamaciones(
    estado: Optional[str] = None,
    vin: Optional[str] = None,
    db: Session = Depends(get_db)
):
    q = db.query(Reclamacion)
    if estado:
        q = q.filter(Reclamacion.estado == estado)
    if vin:
        q = q.filter(Reclamacion.vin.ilike(f"%{vin}%"))
    reclamaciones = q.order_by(Reclamacion.fecha_reporte.desc()).all()
    return [_build_response(r) for r in reclamaciones]


@router.get("/{rec_id}", response_model=ReclamacionResponse)
def obtener_reclamacion(rec_id: str, db: Session = Depends(get_db)):
    rec = db.query(Reclamacion).filter(Reclamacion.id == rec_id).first()
    if not rec:
        raise HTTPException(status_code=404, detail="Reclamación no encontrada")
    return _build_response(rec)


@router.put("/{rec_id}", response_model=ReclamacionResponse)
async def editar_reclamacion(
    rec_id: str,
    vin: Optional[str] = Form(None),
    vehiculo: Optional[str] = Form(None),
    tipo_novedad: Optional[str] = Form(None),
    transportadora: Optional[str] = Form(None),
    no_remesa: Optional[str] = Form(None),
    no_manifiesto: Optional[str] = Form(None),
    descripcion: Optional[str] = Form(None),
    sede: Optional[str] = Form(None),
    db: Session = Depends(get_db)
):
    rec = db.query(Reclamacion).filter(Reclamacion.id == rec_id).first()
    if not rec:
        raise HTTPException(status_code=404, detail="Reclamación no encontrada")
    if vin is not None:            rec.vin = vin.strip().upper()
    if vehiculo is not None:       rec.vehiculo = vehiculo
    if tipo_novedad is not None:   rec.tipo_novedad = tipo_novedad
    if transportadora is not None: rec.transportadora = transportadora
    if no_remesa is not None:      rec.no_remesa = no_remesa
    if no_manifiesto is not None:  rec.no_manifiesto = no_manifiesto
    if descripcion is not None:    rec.descripcion = descripcion
    if sede is not None:           rec.sede = sede
    db.commit()
    db.refresh(rec)
    return _build_response(rec)


@router.post("/", response_model=ReclamacionResponse, status_code=status.HTTP_201_CREATED)
async def crear_reclamacion(
    vin: str = Form(...),
    vehiculo: str = Form(...),
    tipo_novedad: str = Form(...),
    descripcion: str = Form(...),
    transportadora: str = Form("BERGE Vigía"),
    no_remesa: str = Form(...),
    no_manifiesto: str = Form(...),
    sede: Optional[str] = Form(None),
    reportado_por: str = Form(...),
    responsable_actual: str = Form(...),
    dias_limite: int = Form(10),
    fotos: List[UploadFile] = File(default=[]),
    videos: List[UploadFile] = File(default=[]),
    soportes: List[UploadFile] = File(default=[]),
    db: Session = Depends(get_db)
):
    rec_id = _generar_id(db)
    año = datetime.now().strftime("%Y")
    mes = datetime.now().strftime("%m")

    nueva = Reclamacion(
        id=rec_id,
        vin=vin.strip().upper(),
        vehiculo=vehiculo,
        tipo_novedad=tipo_novedad,
        descripcion=descripcion,
        transportadora=transportadora,
        no_remesa=no_remesa,
        no_manifiesto=no_manifiesto,
        sede=sede,
        reportado_por=reportado_por,
        responsable_actual=responsable_actual,
        dias_limite=dias_limite,
    )
    db.add(nueva)

    # Historial inicial
    db.add(HistorialMovimiento(
        reclamacion_id=rec_id,
        accion="Reclamación creada",
        usuario=reportado_por,
        detalle=f"Tipo: {tipo_novedad}. {descripcion[:80]}",
    ))

    # Guardar archivos en disco y registrar en DB

    for cat, lista in [("foto", fotos), ("video", videos), ("soporte", soportes)]:
        for f in lista:
            if f and f.filename:
                ruta = guardar_archivo(f, año, mes, rec_id, cat)
                db.add(Archivo(
                    reclamacion_id=rec_id,
                    categoria=cat,
                    nombre_original=f.filename,
                    ruta_relativa=ruta,
                    subido_por=reportado_por,
                ))

    db.commit()
    db.refresh(nueva)

    # Notificar a admins y asistentes — correo individual con magic link por usuario
    try:
        users_notificar = (
            db.query(Usuario)
            .filter(Usuario.rol.in_(["admin", "asistente"]), Usuario.activo.is_(True))
            .all()
        )
        datos_rec = {
            "id":            nueva.id,
            "vin":           nueva.vin,
            "vehiculo":      nueva.vehiculo,
            "tipo_novedad":  nueva.tipo_novedad,
            "descripcion":   nueva.descripcion,
            "transportadora": nueva.transportadora,
            "no_remesa":     nueva.no_remesa,
            "no_manifiesto": nueva.no_manifiesto,
            "sede":          nueva.sede or "—",
            "reportado_por": nueva.reportado_por,
            "fecha_reporte": nueva.fecha_reporte,
        }
        
        for u in users_notificar:
            if u.email:
                url = generar_url_acceso(
                    db,
                    u.email,
                    f"/reclamaciones/{nueva.id}"
                )
                enviar_correo_nueva_reclamacion(
                    [u.email],
                    datos_rec,
                    url_acceso=url
                )

    except Exception as e:
        print(f"[EMAIL] No se pudo enviar notificación de nueva reclamación: {e}")

    return _build_response(nueva)


@router.patch("/{rec_id}/estado")
def cambiar_estado(
    rec_id: str,
    payload: CambiarEstadoRequest,
    db: Session = Depends(get_db)
):
    if payload.nuevo_estado not in ESTADOS_VALIDOS:
        raise HTTPException(status_code=400, detail=f"Estado inválido: {payload.nuevo_estado}")

    rec = db.query(Reclamacion).filter(Reclamacion.id == rec_id).first()
    if not rec:
        raise HTTPException(status_code=404, detail="Reclamación no encontrada")

    estado_anterior = rec.estado
    rec.estado = payload.nuevo_estado

    # Fecha de radicación automática
    if payload.nuevo_estado == "radicada_vigia":
        rec.fecha_radicacion = datetime.utcnow()

    etiquetas = {
        "en_gestion": "Enviada a gestión",
        "radicada_vigia": "Radicada en Vigía",
        "aprobada": "Aprobada por Vigía",
        "en_facturacion": "En proceso de facturación",
        "cerrada": "Reclamación cerrada",
    }
    accion = etiquetas.get(payload.nuevo_estado, f"Estado cambiado a {payload.nuevo_estado}")

    db.add(HistorialMovimiento(
        reclamacion_id=rec_id,
        accion=accion,
        usuario=payload.usuario,
        detalle=payload.detalle or f"Cambio de '{estado_anterior}' a '{payload.nuevo_estado}'",
    ))
    db.commit()

    # ── Notificar a colisión cuando la reclamación pasa a gestión (solo si venía de otro estado) ──
    if payload.nuevo_estado == "en_gestion" and estado_anterior != "en_gestion":
        try:
            # Buscar usuarios colisión de la misma sede primero
            colision_users = (
                db.query(Usuario)
                .filter(Usuario.rol == "colision", Usuario.activo.is_(True), Usuario.sede == rec.sede)
                .all()
            )
            # Si no hay en esa sede, notificar a todos los de colisión
            if not colision_users:
                colision_users = (
                    db.query(Usuario)
                    .filter(Usuario.rol == "colision", Usuario.activo.is_(True))
                    .all()
                )
            datos_rec = {
                "id":            rec.id,
                "vin":           rec.vin,
                "vehiculo":      rec.vehiculo,
                "tipo_novedad":  rec.tipo_novedad,
                "descripcion":   rec.descripcion,
                "transportadora": rec.transportadora,
                "no_remesa":     rec.no_remesa,
                "no_manifiesto": rec.no_manifiesto,
                "sede":          rec.sede or "—",
                "reportado_por": rec.reportado_por,
                "fecha_reporte": rec.fecha_reporte,
            }
            for u in colision_users:
                if u.email:
                    url = generar_url_acceso(db, u.email, f"/reclamaciones/{rec.id}")
                    enviar_correo_colision([u.email], datos_rec, url_acceso=url)
        except Exception as e:
            print(f"[EMAIL] No se pudo notificar a colisión: {e}")

    return {"ok": True, "estado": payload.nuevo_estado}


@router.post("/{rec_id}/radicado-vigia")
def registrar_radicado(
    rec_id: str,
    no_radicado: str = Form(...),
    usuario: str = Form(...),
    db: Session = Depends(get_db)
):
    rec = db.query(Reclamacion).filter(Reclamacion.id == rec_id).first()
    if not rec:
        raise HTTPException(status_code=404, detail="Reclamación no encontrada")

    rec.no_radicado_vigia = no_radicado
    rec.estado = "radicada_vigia"
    rec.fecha_radicacion = datetime.utcnow()

    db.add(HistorialMovimiento(
        reclamacion_id=rec_id,
        accion="Radicada en Vigía",
        usuario=usuario,
        detalle=f"Radicado No. {no_radicado}",
    ))
    db.commit()
    return {"ok": True, "no_radicado_vigia": no_radicado}


@router.post("/{rec_id}/cotizacion")
async def subir_cotizacion(
    rec_id: str,
    valor: str = Form(...),
    descripcion: Optional[str] = Form(None),
    usuario: str = Form(...),
    archivo: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    rec = db.query(Reclamacion).filter(Reclamacion.id == rec_id).first()
    if not rec:
        raise HTTPException(status_code=404, detail="Reclamación no encontrada")

    año = datetime.now().strftime("%Y")
    mes = datetime.now().strftime("%m")
    ruta = guardar_archivo(archivo, año, mes, rec_id, "cotizacion")

    rec.cotizacion = valor
    db.add(Archivo(
        reclamacion_id=rec_id,
        categoria="cotizacion",
        nombre_original=archivo.filename,
        ruta_relativa=ruta,
        subido_por=usuario,
    ))
    db.add(HistorialMovimiento(
        reclamacion_id=rec_id,
        accion="Cotización recibida",
        usuario=usuario,
        detalle=f"Cotización: {valor}" + (f" - {descripcion}" if descripcion else ""),
    ))
    db.commit()
    return {"ok": True, "cotizacion": valor}


@router.post("/{rec_id}/factura")
async def subir_factura(
    rec_id: str,
    usuario: str = Form(...),
    descripcion: Optional[str] = Form(None),
    factura: UploadFile = File(...),
    certificado: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    rec = db.query(Reclamacion).filter(Reclamacion.id == rec_id).first()
    if not rec:
        raise HTTPException(status_code=404, detail="Reclamación no encontrada")

    año = datetime.now().strftime("%Y")
    mes = datetime.now().strftime("%m")

    for archivo, cat in [(factura, "factura"), (certificado, "certificado")]:
        ruta = guardar_archivo(archivo, año, mes, rec_id, cat)
        db.add(Archivo(
            reclamacion_id=rec_id,
            categoria=cat,
            nombre_original=archivo.filename,
            ruta_relativa=ruta,
            subido_por=usuario,
        ))

    rec.estado = "en_facturacion"
    db.add(HistorialMovimiento(
        reclamacion_id=rec_id,
        accion="Factura y certificado enviados",
        usuario=usuario,
        detalle=descripcion or "Documentos de cierre adjuntados",
    ))
    db.commit()
    return {"ok": True}


@router.post("/{rec_id}/archivos")
async def subir_archivos_adicionales(
    rec_id: str,
    categoria: str = Form(...),   # foto | video | soporte
    usuario: str = Form(...),
    archivos: List[UploadFile] = File(...),
    db: Session = Depends(get_db)
):
    rec = db.query(Reclamacion).filter(Reclamacion.id == rec_id).first()
    if not rec:
        raise HTTPException(status_code=404, detail="Reclamación no encontrada")

    año = datetime.now().strftime("%Y")
    mes = datetime.now().strftime("%m")
    guardados = []

    for archivo in archivos:
        if archivo and archivo.filename:
            ruta = guardar_archivo(archivo, año, mes, rec_id, categoria)

            db.add(Archivo(
                reclamacion_id=rec_id,
                categoria=categoria,
                nombre_original=archivo.filename,
                ruta_relativa=ruta,
                subido_por=usuario,
            ))
            
            guardados.append(archivo.filename)

    db.commit()
    return {"ok": True, "guardados": guardados}


@router.get("/dashboard/stats")
def dashboard_stats(db: Session = Depends(get_db)):
    def count_estado(estado):
        return db.query(Reclamacion).filter(Reclamacion.estado == estado).count()

    activas = db.query(Reclamacion).filter(
        Reclamacion.estado.in_(["abierta", "en_gestion"])
    ).all()
    proximas_vencer = sum(
        1 for r in activas
        if dias_habiles_transcurridos(r.fecha_reporte) >= 8
    )

    return {
        "total":           db.query(Reclamacion).count(),
        "abiertas":        count_estado("abierta"),
        "abierta":         count_estado("abierta"),
        "en_gestion":      count_estado("en_gestion"),
        "radicadas":       count_estado("radicada_vigia"),
        "radicada_vigia":  count_estado("radicada_vigia"),
        "aprobadas":       count_estado("aprobada"),
        "aprobada":        count_estado("aprobada"),
        "en_facturacion":  count_estado("en_facturacion"),
        "cerradas":        count_estado("cerrada"),
        "cerrada":         count_estado("cerrada"),
        "proximas_vencer": proximas_vencer,
    }
