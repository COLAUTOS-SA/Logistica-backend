import smtplib
from datetime import date
from email.message import EmailMessage
from pathlib import Path
from dotenv import dotenv_values

# Lee el .env directamente desde su ruta (no depende de os.environ)
_env_path = Path(__file__).resolve().parent.parent.parent / ".env"


def enviar_correo_vencimientos(
    destinatarios: list,
    alertas: list,
    vencidas: list,
) -> None:
    """Envía el correo diario de alertas de vencimiento a los administradores."""

    if not destinatarios or (not alertas and not vencidas):
        return

    cfg = dotenv_values(_env_path)   # lee el archivo directamente, sin caché
    smtp_host = "smtp.gmail.com"
    smtp_port = 587
    smtp_user = cfg.get("EMAIL_USER", "")
    smtp_pass = cfg.get("EMAIL_PASS", "").replace(" ", "")  # quita espacios de la app password

    print(f"[EMAIL] Conectando a {smtp_host}:{smtp_port} con usuario: {smtp_user}")

    if not smtp_user or not smtp_pass:
        print("[EMAIL] Credenciales no configuradas – omitiendo envio")
        return

    total = len(alertas) + len(vencidas)
    fecha_str = date.today().strftime("%d/%m/%Y")

    from email.mime.multipart import MIMEMultipart
    from email.mime.text import MIMEText

    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"COLAUTOS - {total} alertas de vencimiento - {fecha_str}"
    msg["From"]    = smtp_user
    msg["To"]      = ", ".join(destinatarios)
    msg.attach(MIMEText(_html(alertas, vencidas, fecha_str), "html", "utf-8"))

    with smtplib.SMTP(smtp_host, smtp_port, timeout=15) as server:
        server.ehlo()
        server.starttls()
        server.login(smtp_user, smtp_pass)
        server.sendmail(smtp_user, destinatarios, msg.as_bytes())  # as_bytes evita error ASCII
    print(f"[EMAIL] Enviado a {destinatarios} — {len(vencidas)} vencidas, {len(alertas)} en alerta")


# ── Template HTML ─────────────────────────────────────────────────────────────

def _filas_tabla(items: list, color: str) -> str:
    filas = ""
    for r in items:
        filas += f"""
        <tr>
          <td style="padding:10px 12px;border-bottom:1px solid #f0f0f0;font-weight:600;color:#1d4ed8">{r['id']}</td>
          <td style="padding:10px 12px;border-bottom:1px solid #f0f0f0">{r['vin']}</td>
          <td style="padding:10px 12px;border-bottom:1px solid #f0f0f0">{r['vehiculo']}</td>
          <td style="padding:10px 12px;border-bottom:1px solid #f0f0f0">{r['transportadora']}</td>
          <td style="padding:10px 12px;border-bottom:1px solid #f0f0f0;text-align:center">
            <span style="background:{color};color:white;padding:3px 10px;border-radius:20px;font-size:12px;font-weight:700">
              {r['dias_habiles']}/{r['dias_limite']} días
            </span>
          </td>
          <td style="padding:10px 12px;border-bottom:1px solid #f0f0f0;font-size:13px;color:#6b7280">{r['responsable']}</td>
        </tr>"""
    return filas


def _seccion(titulo: str, color: str, icono: str, items: list) -> str:
    if not items:
        return ""
    return f"""
    <div style="margin-bottom:28px">
      <div style="background:{color};color:white;padding:12px 20px;border-radius:8px 8px 0 0;display:flex;align-items:center;gap:8px">
        <span style="font-size:18px">{icono}</span>
        <span style="font-weight:700;font-size:15px">{titulo} ({len(items)})</span>
      </div>
      <table style="width:100%;border-collapse:collapse;background:white;border-radius:0 0 8px 8px;overflow:hidden;box-shadow:0 1px 4px rgba(0,0,0,0.08)">
        <thead>
          <tr style="background:#f8fafc">
            <th style="padding:10px 12px;text-align:left;font-size:12px;color:#6b7280;font-weight:600;text-transform:uppercase">ID</th>
            <th style="padding:10px 12px;text-align:left;font-size:12px;color:#6b7280;font-weight:600;text-transform:uppercase">VIN</th>
            <th style="padding:10px 12px;text-align:left;font-size:12px;color:#6b7280;font-weight:600;text-transform:uppercase">Vehículo</th>
            <th style="padding:10px 12px;text-align:left;font-size:12px;color:#6b7280;font-weight:600;text-transform:uppercase">Transportadora</th>
            <th style="padding:10px 12px;text-align:center;font-size:12px;color:#6b7280;font-weight:600;text-transform:uppercase">Días hábiles</th>
            <th style="padding:10px 12px;text-align:left;font-size:12px;color:#6b7280;font-weight:600;text-transform:uppercase">Responsable</th>
          </tr>
        </thead>
        <tbody>{_filas_tabla(items, color)}</tbody>
      </table>
    </div>"""


def _html(alertas: list, vencidas: list, fecha_str: str) -> str:
    total = len(alertas) + len(vencidas)
    return f"""<!DOCTYPE html>
<html lang="es">
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1"></head>
<body style="margin:0;padding:0;background:#f1f5f9;font-family:Arial,sans-serif">
  <div style="max-width:720px;margin:30px auto;background:#f1f5f9">

    <!-- Header -->
    <div style="background:#111827;padding:28px 32px;border-radius:12px 12px 0 0;text-align:center">
      <div style="font-size:22px;font-weight:800;color:white;letter-spacing:1px">COLAUTOS</div>
      <div style="font-size:13px;color:#9ca3af;margin-top:4px">Sistema de Gestión Logística</div>
    </div>

    <!-- Alert banner -->
    <div style="background:#fef3c7;border-left:4px solid #f59e0b;padding:16px 24px;display:flex;align-items:center;gap:12px">
      <span style="font-size:24px">⚠️</span>
      <div>
        <div style="font-weight:700;font-size:15px;color:#92400e">Reporte de vencimientos – {fecha_str}</div>
        <div style="font-size:13px;color:#b45309;margin-top:2px">
          {total} reclamación(es) requieren atención inmediata
        </div>
      </div>
    </div>

    <!-- Body -->
    <div style="padding:24px 28px;background:#f8fafc">

      {_seccion('Reclamaciones VENCIDAS', '#dc2626', '🔴', vencidas)}
      {_seccion('Próximas a vencer (8+ días hábiles)', '#d97706', '🟡', alertas)}

      <div style="background:#e0f2fe;border-radius:8px;padding:14px 18px;font-size:13px;color:#0369a1;margin-top:8px">
        <strong>Acción requerida:</strong> Ingrese al sistema y gestione estas reclamaciones
        antes de que superen el plazo establecido con la transportadora.
      </div>
    </div>

    <!-- Footer -->
    <div style="background:#111827;padding:16px 24px;border-radius:0 0 12px 12px;text-align:center">
      <div style="font-size:12px;color:#6b7280">
        Este correo fue generado automáticamente por el sistema COLAUTOS.<br>
        No responda a este mensaje.
      </div>
    </div>

  </div>
</body>
</html>"""
