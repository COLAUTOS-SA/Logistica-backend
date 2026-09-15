import json
import os
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.files import guardar_documento
from app.models.documents import Documento
from app.schemas.documents import DocumentoResponse

router = APIRouter(prefix="/documentos", tags=["Documentos"])

BASE_URL = "http://localhost:8000"


def _generar_id_doc(db: Session) -> str:
    cantidad = db.query(Documento).count()
    return f"DOC-{str(cantidad + 1).zfill(3)}"


def _to_response(doc: Documento) -> dict:
    vehiculos = None
    if doc.vehiculos_json:
        try:
            vehiculos = json.loads(doc.vehiculos_json)
        except Exception:
            vehiculos = []

    url = None
    if doc.ruta_relativa:
        url = f"{BASE_URL}/archivos/{doc.ruta_relativa.replace(os.sep, '/')}"

    return {
        **doc.__dict__,
        "vehiculos": vehiculos,
        "url_archivo": url,
    }


@router.get("/", response_model=List[DocumentoResponse])
def listar_documentos(
    tipo: Optional[str] = None,
    vin: Optional[str] = None,
    numero: Optional[str] = None,
    db: Session = Depends(get_db)
):
    q = db.query(Documento)
    if tipo:
        q = q.filter(Documento.tipo == tipo)
    if vin:
        q = q.filter(Documento.vin.ilike(f"%{vin}%"))
    if numero:
        q = q.filter(Documento.numero.ilike(f"%{numero}%"))
    docs = q.order_by(Documento.fecha_carga.desc()).all()
    return [_to_response(d) for d in docs]


@router.get("/{doc_id}", response_model=DocumentoResponse)
def obtener_documento(doc_id: str, db: Session = Depends(get_db)):
    doc = db.query(Documento).filter(Documento.id == doc_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Documento no encontrado")
    return _to_response(doc)


@router.put("/{doc_id}", response_model=DocumentoResponse)
async def editar_documento(
    doc_id: str,
    numero: Optional[str] = Form(None),
    fecha: Optional[str] = Form(None),
    vin: Optional[str] = Form(None),
    vehiculo: Optional[str] = Form(None),
    manifiesto_no: Optional[str] = Form(None),
    remesa_no: Optional[str] = Form(None),
    transportadora: Optional[str] = Form(None),
    origen: Optional[str] = Form(None),
    destino: Optional[str] = Form(None),
    conductor: Optional[str] = Form(None),
    placa: Optional[str] = Form(None),
    vehiculos_json: Optional[str] = Form(None),
    peso: Optional[str] = Form(None),
    remitente: Optional[str] = Form(None),
    destinatario: Optional[str] = Form(None),
    observacion: Optional[str] = Form(None),
    archivo: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db)
):
    doc = db.query(Documento).filter(Documento.id == doc_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Documento no encontrado")

    if numero is not None:       doc.numero = numero
    if fecha is not None:        doc.fecha = fecha
    if vin is not None:          doc.vin = vin.strip().upper() if vin.strip() else None
    if vehiculo is not None:     doc.vehiculo = vehiculo
    if manifiesto_no is not None: doc.manifiesto_no = manifiesto_no
    if remesa_no is not None:    doc.remesa_no = remesa_no
    if transportadora is not None: doc.transportadora = transportadora
    if origen is not None:       doc.origen = origen
    if destino is not None:      doc.destino = destino
    if conductor is not None:    doc.conductor = conductor
    if placa is not None:        doc.placa = placa
    if vehiculos_json is not None: doc.vehiculos_json = vehiculos_json
    if peso is not None:         doc.peso = peso
    if remitente is not None:    doc.remitente = remitente
    if destinatario is not None: doc.destinatario = destinatario
    if observacion is not None:  doc.observacion = observacion

    if archivo and archivo.filename:
        ruta = guardar_documento(archivo, doc.tipo, doc.numero)
        doc.nombre_archivo = archivo.filename
        doc.ruta_relativa = ruta

    db.commit()
    db.refresh(doc)
    return _to_response(doc)


@router.delete("/{doc_id}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_documento(doc_id: str, db: Session = Depends(get_db)):
    doc = db.query(Documento).filter(Documento.id == doc_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Documento no encontrado")
    db.delete(doc)
    db.commit()


@router.post("/", response_model=DocumentoResponse, status_code=status.HTTP_201_CREATED)
async def crear_documento(
    tipo: str = Form(...),              # manifiesto | remesa | inventario | inventario_traslado
    numero: str = Form(...),
    subido_por: str = Form(...),
    fecha: Optional[str] = Form(None),
    vin: Optional[str] = Form(None),
    vehiculo: Optional[str] = Form(None),
    manifiesto_no: Optional[str] = Form(None),
    remesa_no: Optional[str] = Form(None),
    transportadora: Optional[str] = Form(None),
    origen: Optional[str] = Form(None),
    destino: Optional[str] = Form(None),
    conductor: Optional[str] = Form(None),
    placa: Optional[str] = Form(None),
    vehiculos_json: Optional[str] = Form(None),   # JSON string de lista de VINs
    peso: Optional[str] = Form(None),
    remitente: Optional[str] = Form(None),
    destinatario: Optional[str] = Form(None),
    observacion: Optional[str] = Form(None),
    archivo: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db)
):
    doc_id = _generar_id_doc(db)
    ruta = None
    nombre_archivo = None

    if archivo and archivo.filename:
        ruta = guardar_documento(archivo, tipo, numero)
        nombre_archivo = archivo.filename

    nuevo = Documento(
        id=doc_id,
        tipo=tipo,
        numero=numero,
        fecha=fecha or datetime.now().strftime("%Y-%m-%d"),
        vin=vin.strip().upper() if vin else None,
        vehiculo=vehiculo,
        manifiesto_no=manifiesto_no,
        remesa_no=remesa_no,
        nombre_archivo=nombre_archivo,
        ruta_relativa=ruta,
        subido_por=subido_por,
        transportadora=transportadora,
        origen=origen,
        destino=destino,
        conductor=conductor,
        placa=placa,
        vehiculos_json=vehiculos_json,
        peso=peso,
        remitente=remitente,
        destinatario=destinatario,
        observacion=observacion,
    )
    db.add(nuevo)
    db.commit()
    db.refresh(nuevo)
    return _to_response(nuevo)
