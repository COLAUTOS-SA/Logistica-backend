"""
seed.py – Poblar la base de datos con usuarios y datos de prueba.
Ejecutar UNA sola vez:  python seed.py

⚠️  ADVERTENCIA: Borra y recrea todas las tablas.
    Los archivos físicos en archivos_reclamaciones/ NO se tocan.
"""

from datetime import datetime, timedelta
from app.core.database import engine, SessionLocal, Base
from app.core.security import hash_password
import app.models  # importa todos los modelos

# ── 1. Recrear tablas ────────────────────────────────────────────────────────
print("Recreando tablas...")
Base.metadata.drop_all(bind=engine)
Base.metadata.create_all(bind=engine)

db = SessionLocal()

# ── 2. Usuarios ──────────────────────────────────────────────────────────────
from app.models.users import Usuario

usuarios = [
    Usuario(
        nombre="Carolina Aricapa",
        email="carolina.aricapa@colautos.com",
        password_hash=hash_password("admin123"),
        rol="admin",
        sede="Pereira - Av 30 de Agosto",
    ),
    Usuario(
        nombre="Lorena Gómez",
        email="lorena.gomez@colautos.com",
        password_hash=hash_password("asistente123"),
        rol="asistente",
        sede="Pereira - Av 30 de Agosto",
    ),
    Usuario(
        nombre="Pilar Piedrahita",
        email="pilar.piedrahita@colautos.com",
        password_hash=hash_password("asistente123"),
        rol="asistente",
        sede="Dosquebradas",
    ),
    Usuario(
        nombre="Miguel Colisión",
        email="miguel.colision@colautos.com",
        password_hash=hash_password("colision123"),
        rol="colision",
        sede="Pereira - Av 30 de Agosto",
    ),
    Usuario(
        nombre="Kendry Iván",
        email="kendry.ivan@colautos.com",
        password_hash=hash_password("asistente123"),
        rol="asistente",
        sede="Pereira - Av 30 de Agosto",
    ),
]
db.add_all(usuarios)
db.commit()
print(f"  ✓ {len(usuarios)} usuarios creados")

# ── 3. Reclamaciones de prueba ───────────────────────────────────────────────
from app.models.claims import Reclamacion, HistorialMovimiento

hoy = datetime.utcnow()

reclamaciones_data = [
    {
        "id": "REC-2026-001",
        "vin": "3MDDJ2HAAVM461828",
        "vehiculo": "Mazda CX-30 2026 - Machine Gray",
        "tipo_novedad": "Desconche",
        "descripcion": "Desconche en la nave trasera del vehículo. Se detectó al momento de la recepción en bodega Pereira.",
        "estado": "abierta",
        "transportadora": "BERGE Vigía",
        "no_remesa": "VIG-2100766",
        "no_manifiesto": "410900097167",
        "sede": "Pereira - Av 30 de Agosto",
        "reportado_por": "Lorena Gómez",
        "responsable_actual": "Carolina Aricapa",
        "fecha_reporte": hoy - timedelta(days=3),
        "dias_limite": 10,
    },
    {
        "id": "REC-2026-002",
        "vin": "3MVDM2W7AVL319047",
        "vehiculo": "Mazda CX-5 2026 - Blanco Nieve Perlado",
        "tipo_novedad": "Rayón",
        "descripcion": "Rayón profundo en puerta delantera derecha. Posiblemente durante el transporte.",
        "estado": "en_gestion",
        "transportadora": "BERGE Vigía",
        "no_remesa": "VIG-2100765",
        "no_manifiesto": "410900097167",
        "sede": "Pereira - Av 30 de Agosto",
        "reportado_por": "Pilar Piedrahita",
        "responsable_actual": "Miguel Colisión",
        "cotizacion": "$850.000",
        "fecha_reporte": hoy - timedelta(days=7),
        "dias_limite": 10,
    },
    {
        "id": "REC-2026-003",
        "vin": "3MDDJ2SAAVM461905",
        "vehiculo": "Mazda CX-30 2026 - Rojo Cristal",
        "tipo_novedad": "Abolladura",
        "descripcion": "Abolladura en capó. Se identificó al realizar el inventario de llegada.",
        "estado": "radicada_vigia",
        "transportadora": "BERGE Vigía",
        "no_remesa": "VIG-2100764",
        "no_manifiesto": "410900097167",
        "sede": "Pereira - Av 30 de Agosto",
        "reportado_por": "Lorena Gómez",
        "responsable_actual": "Carolina Aricapa",
        "cotizacion": "$1.200.000",
        "no_radicado_vigia": "RAD-VIG-2026-4521",
        "fecha_reporte": hoy - timedelta(days=14),
        "fecha_radicacion": hoy - timedelta(days=9),
        "dias_limite": 10,
    },
    {
        "id": "REC-2026-004",
        "vin": "3MVDM2W7AVL320112",
        "vehiculo": "Mazda CX-5 2026 - Gris Platino",
        "tipo_novedad": "Faltante de accesorios",
        "descripcion": "Faltante de kit de herramientas y gato.",
        "estado": "aprobada",
        "transportadora": "BERGE Vigía",
        "no_remesa": "VIG-2100750",
        "no_manifiesto": "410900097150",
        "sede": "Pereira - Av 30 de Agosto",
        "reportado_por": "Kendry Iván",
        "responsable_actual": "Carolina Aricapa",
        "cotizacion": "$350.000",
        "no_radicado_vigia": "RAD-VIG-2026-4495",
        "fecha_reporte": hoy - timedelta(days=25),
        "fecha_radicacion": hoy - timedelta(days=21),
        "dias_limite": 10,
    },
    {
        "id": "REC-2026-005",
        "vin": "3MDDJ2HAAVM462001",
        "vehiculo": "Mazda CX-30 2026 - Negro Jet",
        "tipo_novedad": "Daño en pintura",
        "descripcion": "Daño generalizado en pintura del techo. Aparentes marcas de granizo.",
        "estado": "cerrada",
        "transportadora": "BERGE Vigía",
        "no_remesa": "VIG-2100720",
        "no_manifiesto": "410900097100",
        "sede": "Pereira - Av 30 de Agosto",
        "reportado_por": "Lorena Gómez",
        "responsable_actual": "Carolina Aricapa",
        "cotizacion": "$2.500.000",
        "no_radicado_vigia": "RAD-VIG-2026-4410",
        "fecha_reporte": hoy - timedelta(days=35),
        "fecha_radicacion": hoy - timedelta(days=32),
        "dias_limite": 10,
    },
]

historial_data = {
    "REC-2026-001": [
        {"accion": "Reclamación creada", "usuario": "Lorena Gómez", "detalle": "Se reporta desconche en nave trasera", "dias": 3},
    ],
    "REC-2026-002": [
        {"accion": "Reclamación creada", "usuario": "Pilar Piedrahita", "detalle": "Se reporta rayón en puerta delantera derecha", "dias": 7},
        {"accion": "Enviada a gestión", "usuario": "Carolina Aricapa", "detalle": "Se solicita evaluación y cotización", "dias": 6},
        {"accion": "Cotización recibida", "usuario": "Miguel Colisión", "detalle": "Cotización: $850.000 - Reparación pintura puerta", "dias": 4},
    ],
    "REC-2026-003": [
        {"accion": "Reclamación creada", "usuario": "Lorena Gómez", "detalle": "Se reporta abolladura en capó", "dias": 14},
        {"accion": "Enviada a gestión", "usuario": "Carolina Aricapa", "detalle": "Se solicita evaluación y cotización", "dias": 13},
        {"accion": "Cotización recibida", "usuario": "Miguel Colisión", "detalle": "Cotización: $1.200.000", "dias": 11},
        {"accion": "Radicada en Vigía", "usuario": "Carolina Aricapa", "detalle": "Radicado No. RAD-VIG-2026-4521", "dias": 9},
    ],
    "REC-2026-004": [
        {"accion": "Reclamación creada", "usuario": "Kendry Iván", "detalle": "Se reporta faltante de herramientas y gato", "dias": 25},
        {"accion": "Enviada a gestión", "usuario": "Carolina Aricapa", "detalle": "Se solicita evaluación", "dias": 23},
        {"accion": "Cotización recibida", "usuario": "Miguel Colisión", "detalle": "Cotización: $350.000", "dias": 22},
        {"accion": "Radicada en Vigía", "usuario": "Carolina Aricapa", "detalle": "Radicado No. RAD-VIG-2026-4495", "dias": 21},
        {"accion": "Aprobada por Vigía", "usuario": "Sistema Vigía", "detalle": "Valor aprobado: $350.000", "dias": 13},
    ],
    "REC-2026-005": [
        {"accion": "Reclamación creada", "usuario": "Lorena Gómez", "detalle": "Se reporta daño por granizo en techo", "dias": 35},
        {"accion": "Enviada a gestión", "usuario": "Carolina Aricapa", "detalle": "Se solicita evaluación", "dias": 34},
        {"accion": "Cotización recibida", "usuario": "Miguel Colisión", "detalle": "Cotización: $2.500.000", "dias": 33},
        {"accion": "Radicada en Vigía", "usuario": "Carolina Aricapa", "detalle": "Radicado No. RAD-VIG-2026-4410", "dias": 32},
        {"accion": "Aprobada por Vigía", "usuario": "Sistema Vigía", "detalle": "Valor aprobado: $2.500.000", "dias": 20},
        {"accion": "Factura y certificado enviados", "usuario": "Carolina Aricapa", "detalle": "Documentos de cierre adjuntados", "dias": 17},
        {"accion": "Reclamación cerrada", "usuario": "Carolina Aricapa", "detalle": "Proceso completado", "dias": 13},
    ],
}

for data in reclamaciones_data:
    hist = historial_data.pop(data["id"], [])
    rec = Reclamacion(**data)
    db.add(rec)
    db.flush()
    for h in hist:
        dias = h.pop("dias")
        db.add(HistorialMovimiento(
            reclamacion_id=data["id"],
            fecha=hoy - timedelta(days=dias),
            **h
        ))

db.commit()
print(f"  ✓ {len(reclamaciones_data)} reclamaciones creadas con historial")

# ── 4. Documentos de prueba ───────────────────────────────────────────────────
from app.models.documents import Documento
import json

docs = [
    Documento(
        id="DOC-001",
        tipo="manifiesto",
        numero="410900097167",
        fecha="2026-03-14",
        transportadora="BERGE Vigía",
        origen="Carport-Yotoco",
        destino="Pereira - Av 30 de Agosto",
        conductor="López Alzate Diego",
        placa="JOW572",
        vehiculos_json=json.dumps(["3MDDJ2SAAVM461905", "3MVDM2W7AVL319047", "3MDDJ2HAAVM461828"]),
        nombre_archivo="manifiesto_410900097167.pdf",
        subido_por="Carolina Aricapa",
    ),
    Documento(id="DOC-002", tipo="remesa", numero="VIG-2100764", fecha="2026-03-14",
              vin="3MDDJ2SAAVM461905", vehiculo="Mazda CX-30 2026 - Rojo Cristal",
              manifiesto_no="410900097167", peso="1542 Kg",
              remitente="MAZDA DE COLOMBIA S.A.S", destinatario="COLOMBIANA DE AUTOS S.A.",
              nombre_archivo="remesa_VIG-2100764.pdf", subido_por="Pilar Piedrahita"),
    Documento(id="DOC-003", tipo="remesa", numero="VIG-2100765", fecha="2026-03-14",
              vin="3MVDM2W7AVL319047", vehiculo="Mazda CX-5 2026 - Blanco Nieve Perlado",
              manifiesto_no="410900097167", peso="1931 Kg",
              remitente="MAZDA DE COLOMBIA S.A.S", destinatario="COLOMBIANA DE AUTOS S.A.",
              nombre_archivo="remesa_VIG-2100765.pdf", subido_por="Pilar Piedrahita"),
    Documento(id="DOC-004", tipo="remesa", numero="VIG-2100766", fecha="2026-03-14",
              vin="3MDDJ2HAAVM461828", vehiculo="Mazda CX-30 2026 - Machine Gray",
              manifiesto_no="410900097167", peso="1522 Kg",
              remitente="MAZDA DE COLOMBIA S.A.S", destinatario="COLOMBIANA DE AUTOS S.A.",
              nombre_archivo="remesa_VIG-2100766.pdf", subido_por="Lorena Gómez"),
    Documento(id="DOC-005", tipo="inventario", numero="INV-2026-001", fecha="2026-03-14",
              vin="3MDDJ2HAAVM461828", vehiculo="Mazda CX-30 2026 - Machine Gray",
              remesa_no="VIG-2100766", nombre_archivo="inventario_3MDDJ2HAAVM461828.pdf",
              subido_por="Lorena Gómez"),
    Documento(id="DOC-006", tipo="inventario", numero="INV-2026-002", fecha="2026-03-14",
              vin="3MVDM2W7AVL319047", vehiculo="Mazda CX-5 2026 - Blanco Nieve Perlado",
              remesa_no="VIG-2100765", nombre_archivo="inventario_3MVDM2W7AVL319047.pdf",
              subido_por="Pilar Piedrahita"),
    Documento(id="DOC-007", tipo="inventario_traslado", numero="TRS-2026-001", fecha="2026-03-16",
              vin="3MDDJ2HAAVM461828", vehiculo="Mazda CX-30 2026 - Machine Gray",
              origen="Pereira - Av 30 de Agosto", destino="Dosquebradas",
              nombre_archivo="traslado_3MDDJ2HAAVM461828.pdf", subido_por="Carolina Aricapa"),
]
db.add_all(docs)
db.commit()
print(f"  ✓ {len(docs)} documentos creados")

db.close()
print("\n✅ Base de datos lista. Puedes arrancar el servidor con:")
print("   uvicorn app.main:app --reload")
