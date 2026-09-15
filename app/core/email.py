import html as _html
import smtplib
from datetime import date
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path
from dotenv import dotenv_values


def _e(valor) -> str:
    """Escapa caracteres HTML en valores dinámicos para evitar inyección."""
    return _html.escape(str(valor)) if valor is not None else "—"

_env_path = Path(__file__).resolve().parent.parent.parent / ".env"
LOGO_URL = "https://i.imgur.com/F6hIOU4.png"
print(f"[EMAIL] Logo configurado: {LOGO_URL}")


# ── SMTP ──────────────────────────────────────────────────────────────────────

def _smtp_send(destinatarios: list, subject: str, html: str) -> None:
    cfg = dotenv_values(_env_path)
    smtp_host = cfg.get("EMAIL_HOST", "smtp.gmail.com")
    smtp_port = int(cfg.get("EMAIL_PORT", "587"))
    smtp_user = cfg.get("EMAIL_USER", "")
    smtp_pass = cfg.get("EMAIL_PASS", "").replace(" ", "")
    print(f"[EMAIL] Enviando a {destinatarios}")
    if not smtp_user or not smtp_pass:
        print("[EMAIL] Credenciales no configuradas")
        return
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"]    = smtp_user
    msg["To"]      = ", ".join(destinatarios)
    msg.attach(MIMEText(html, "html", "utf-8"))
    with smtplib.SMTP(smtp_host, smtp_port, timeout=15) as server:
        server.ehlo(); server.starttls()
        server.login(smtp_user, smtp_pass)
        server.sendmail(smtp_user, destinatarios, msg.as_bytes())
    print(f"[EMAIL] '{subject}' enviado")


# ── Estructura base ───────────────────────────────────────────────────────────

def _wrap(titulo: str, subtitulo: str, color_banner: str, cuerpo: str) -> str:
    return f"""<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <link href="https://fonts.googleapis.com/css2?family=Montserrat:wght@400;500;600;700&display=swap" rel="stylesheet">
</head>
<body style="margin:0;padding:0;background:#f4f4f4;font-family:'Montserrat',Arial,sans-serif">
<table width="100%" cellpadding="0" cellspacing="0" border="0" style="background:#f4f4f4;padding:32px 0">
  <tr><td align="center">
  <table width="600" cellpadding="0" cellspacing="0" border="0"
         style="max-width:600px;background:#ffffff;border-radius:6px;overflow:hidden;border:1px solid #dde1e7">

    <!-- LOGO -->
    <tr>
      <td bgcolor="#ffffff" style="background:#ffffff !important;padding:28px 36px 22px;border-bottom:1px solid #e8eaed">
        <table cellpadding="0" cellspacing="0" border="0" width="100%"><tr>
          <td bgcolor="#ffffff" style="background:#ffffff !important;vertical-align:middle">
            <table cellpadding="0" cellspacing="0" border="0">
              <tr>
                <td bgcolor="#ffffff" style="background:#ffffff !important;padding:8px 12px;border-radius:6px">
                  <img src="{LOGO_URL}" alt="Colautos" style="height:130px;display:block;border:0">
                </td>
              </tr>
            </table>
          </td>
          <td bgcolor="#ffffff" style="background:#ffffff !important;text-align:right;vertical-align:middle">
            <span style="font-family:'Montserrat',Arial,sans-serif;font-size:10px;color:#9ca3af;letter-spacing:1.5px;text-transform:uppercase;font-weight:600">Sistema de Gestión Logística</span>
          </td>
        </tr></table>
      </td>
    </tr>

    <!-- BANNER TÍTULO -->
    <tr>
      <td style="background:{color_banner};padding:22px 36px">
        <div style="font-family:'Montserrat',Arial,sans-serif;font-size:17px;font-weight:700;color:#ffffff;margin-bottom:5px">{titulo}</div>
        <div style="font-family:'Montserrat',Arial,sans-serif;font-size:12px;color:rgba(255,255,255,0.80)">{subtitulo}</div>
      </td>
    </tr>

    <!-- CUERPO -->
    <tr>
      <td style="background:#ffffff;padding:30px 36px">
        {cuerpo}
      </td>
    </tr>

    <!-- FOOTER -->
    <tr>
      <td style="background:#f9fafb;border-top:1px solid #e8eaed;padding:16px 36px;text-align:center">
        <p style="font-family:'Montserrat',Arial,sans-serif;font-size:11px;color:#adb5bd;margin:0;line-height:1.7">
          Este mensaje fue generado automáticamente por el sistema COLAUTOS.<br>
          Por favor no responda a este correo.
        </p>
      </td>
    </tr>

  </table>
  </td></tr>
</table>
</body></html>"""


# ── Email 1: Nueva reclamación ────────────────────────────────────────────────

def _boton(url: str, texto: str, color: str) -> str:
    """Genera un botón HTML de acceso directo. Retorna '' si no hay URL."""
    if not url:
        return ""
    return f"""
    <div style="text-align:center;margin-top:28px;margin-bottom:4px">
      <a href="{url}"
         style="background:{color};color:#ffffff;font-family:'Montserrat',Arial,sans-serif;
                font-size:13px;font-weight:700;text-decoration:none;
                padding:13px 32px;border-radius:5px;display:inline-block;letter-spacing:0.3px">
        {texto} &rarr;
      </a>
    </div>"""


# ── Email 1: Nueva reclamación ────────────────────────────────────────────────

def enviar_correo_nueva_reclamacion(destinatarios: list, reclamacion: dict, url_acceso: str = "") -> None:
    if not destinatarios:
        return
    fecha = reclamacion.get("fecha_reporte", "")
    if hasattr(fecha, "strftime"):
        fecha_str = fecha.strftime("%d/%m/%Y %H:%M")
    else:
        fecha_str = str(fecha)[:16].replace("T", " ") if fecha else "—"

    titulo    = f"Nueva reclamación registrada &nbsp;·&nbsp; {reclamacion.get('id', '')}"
    subtitulo = f"Registrada el {fecha_str} por {reclamacion.get('reportado_por', '—')}"

    def fila(label, valor):
        return f"""<tr>
          <td style="padding:11px 0;border-bottom:1px solid #f0f0f0;font-size:12px;font-weight:600;color:#6b7280;text-transform:uppercase;letter-spacing:0.4px;width:38%;vertical-align:top">{label}</td>
          <td style="padding:11px 0 11px 16px;border-bottom:1px solid #f0f0f0;font-size:13px;color:#1f2937;vertical-align:top">{valor}</td>
        </tr>"""

    r = reclamacion
    cuerpo = f"""
    <p style="font-family:'Montserrat',Arial,sans-serif;font-size:11px;font-weight:700;color:#9ca3af;text-transform:uppercase;letter-spacing:1.5px;margin:0 0 16px 0">Información de la reclamación</p>
    <table width="100%" cellpadding="0" cellspacing="0" border="0" style="border-collapse:collapse;margin-bottom:24px">
      {fila("Tipo de novedad", _e(r.get("tipo_novedad")))}
      {fila("VIN del vehículo", f'<span style="font-family:monospace">{_e(r.get("vin"))}</span>')}
      {fila("Vehículo", _e(r.get("vehiculo")))}
      {fila("Transportadora", _e(r.get("transportadora")))}
      {fila("No. Remesa", _e(r.get("no_remesa")))}
      {fila("No. Manifiesto", _e(r.get("no_manifiesto")))}
      {fila("Sede", _e(r.get("sede")))}
      {fila("Reportado por", _e(r.get("reportado_por")))}
    </table>

    <p style="font-family:'Montserrat',Arial,sans-serif;font-size:11px;font-weight:700;color:#9ca3af;text-transform:uppercase;letter-spacing:1.5px;margin:0 0 10px 0">Descripción</p>
    <div style="font-family:'Montserrat',Arial,sans-serif;font-size:13px;color:#374151;border:1px solid #e8eaed;border-radius:4px;padding:14px 16px;line-height:1.7;margin-bottom:24px;background:#fafafa">
      {_e(r.get("descripcion"))}
    </div>

    <p style="font-family:'Montserrat',Arial,sans-serif;font-size:13px;color:#374151;margin:0;line-height:1.7">
      Ingrese al sistema para revisar y gestionar esta reclamación.
    </p>
    {_boton(url_acceso, "Ver reclamación en el sistema", "#1e4d2b")}"""

    html = _wrap(titulo, subtitulo, "#1e4d2b", cuerpo)
    subject = f"COLAUTOS – Nueva reclamación · {_e(r.get('id'))}"
    _smtp_send(destinatarios, subject, html)


# ── Email 2: Alertas de vencimiento ──────────────────────────────────────────

def enviar_correo_vencimientos(destinatarios: list, alertas: list, vencidas: list, url_acceso: str = "") -> None:
    if not destinatarios or (not alertas and not vencidas):
        return
    total     = len(alertas) + len(vencidas)
    fecha_str = date.today().strftime("%d/%m/%Y")
    titulo    = f"Reporte de vencimientos &nbsp;·&nbsp; {fecha_str}"
    subtitulo = f"{total} reclamación(es) requieren atención inmediata"

    def fila(r, badge_color):
        return f"""<tr>
          <td style="padding:10px 10px;border-bottom:1px solid #f0f0f0;font-size:12px;font-weight:700;color:#1f2937">{_e(r['id'])}</td>
          <td style="padding:10px 10px;border-bottom:1px solid #f0f0f0;font-family:monospace;font-size:11px;color:#374151">{_e(r['vin'])}</td>
          <td style="padding:10px 10px;border-bottom:1px solid #f0f0f0;font-size:12px;color:#374151">{_e(r['vehiculo'])}</td>
          <td style="padding:10px 10px;border-bottom:1px solid #f0f0f0;font-size:12px;color:#374151">{_e(r['transportadora'])}</td>
          <td style="padding:10px 10px;border-bottom:1px solid #f0f0f0;text-align:center">
            <span style="background:{badge_color};color:#fff;padding:3px 8px;border-radius:3px;font-size:11px;font-weight:700">{_e(r['dias_habiles'])}/{_e(r['dias_limite'])} días</span>
          </td>
          <td style="padding:10px 10px;border-bottom:1px solid #f0f0f0;font-size:11px;color:#6b7280">{_e(r['responsable'])}</td>
        </tr>"""

    def seccion(titulo_sec, borde, badge_color, items):
        if not items:
            return ""
        filas = "".join(fila(r, badge_color) for r in items)
        return f"""
        <p style="font-family:'Montserrat',Arial,sans-serif;font-size:11px;font-weight:700;color:#9ca3af;text-transform:uppercase;letter-spacing:1.5px;margin:0 0 8px 0;border-left:3px solid {borde};padding-left:10px">{titulo_sec} &nbsp;·&nbsp; {len(items)} registro(s)</p>
        <table width="100%" cellpadding="0" cellspacing="0" border="0" style="border-collapse:collapse;border:1px solid #e8eaed;border-radius:4px;overflow:hidden;margin-bottom:28px">
          <thead><tr style="background:#f9fafb">
            <th style="padding:8px 10px;text-align:left;font-size:10px;color:#9ca3af;font-weight:700;text-transform:uppercase;border-bottom:1px solid #e8eaed">ID</th>
            <th style="padding:8px 10px;text-align:left;font-size:10px;color:#9ca3af;font-weight:700;text-transform:uppercase;border-bottom:1px solid #e8eaed">VIN</th>
            <th style="padding:8px 10px;text-align:left;font-size:10px;color:#9ca3af;font-weight:700;text-transform:uppercase;border-bottom:1px solid #e8eaed">Vehículo</th>
            <th style="padding:8px 10px;text-align:left;font-size:10px;color:#9ca3af;font-weight:700;text-transform:uppercase;border-bottom:1px solid #e8eaed">Transportadora</th>
            <th style="padding:8px 10px;text-align:center;font-size:10px;color:#9ca3af;font-weight:700;text-transform:uppercase;border-bottom:1px solid #e8eaed">Días</th>
            <th style="padding:8px 10px;text-align:left;font-size:10px;color:#9ca3af;font-weight:700;text-transform:uppercase;border-bottom:1px solid #e8eaed">Responsable</th>
          </tr></thead>
          <tbody>{filas}</tbody>
        </table>"""

    cuerpo = f"""
    {seccion("Reclamaciones vencidas", "#991b1b", "#991b1b", vencidas)}
    {seccion("Próximas a vencer (8+ días hábiles)", "#b45309", "#b45309", alertas)}
    <p style="font-family:'Montserrat',Arial,sans-serif;font-size:13px;color:#374151;margin:0;line-height:1.7">
      Ingrese al sistema y gestione estas reclamaciones antes de que superen el plazo establecido con la transportadora.
    </p>
    {_boton(url_acceso, "Ver reclamaciones en el sistema", "#991b1b")}"""

    html = _wrap(titulo, subtitulo, "#991b1b", cuerpo)
    subject = f"COLAUTOS – {total} alerta(s) de vencimiento · {fecha_str}"
    _smtp_send(destinatarios, subject, html)


# ── Email 3: Novedad enviada a Colisión ──────────────────────────────────────

def enviar_correo_colision(destinatarios: list, reclamacion: dict, url_acceso: str = "") -> None:
    """Notifica al área de colisión que una reclamación fue asignada para cotización."""
    if not destinatarios:
        return

    fecha = reclamacion.get("fecha_reporte", "")
    if hasattr(fecha, "strftime"):
        fecha_str = fecha.strftime("%d/%m/%Y %H:%M")
    else:
        fecha_str = str(fecha)[:16].replace("T", " ") if fecha else "—"

    titulo    = f"Novedad asignada a Colisión &nbsp;·&nbsp; {reclamacion.get('id', '')}"
    subtitulo = f"Registrada el {fecha_str} &nbsp;·&nbsp; Sede: {reclamacion.get('sede', '—')}"

    def fila(label, valor):
        return f"""<tr>
          <td style="padding:11px 0;border-bottom:1px solid #f0f0f0;font-size:12px;font-weight:600;color:#6b7280;text-transform:uppercase;letter-spacing:0.4px;width:38%;vertical-align:top">{label}</td>
          <td style="padding:11px 0 11px 16px;border-bottom:1px solid #f0f0f0;font-size:13px;color:#1f2937;vertical-align:top">{valor}</td>
        </tr>"""

    r = reclamacion
    cuerpo = f"""
    <p style="font-family:'Montserrat',Arial,sans-serif;font-size:13px;color:#374151;margin:0 0 22px 0;line-height:1.7">
      Se ha asignado una reclamación a su área para <strong>revisión y cotización</strong>.
      Por favor ingrese al sistema y adjunte la cotización correspondiente a la brevedad posible.
    </p>

    <p style="font-family:'Montserrat',Arial,sans-serif;font-size:11px;font-weight:700;color:#9ca3af;text-transform:uppercase;letter-spacing:1.5px;margin:0 0 16px 0">Información de la reclamación</p>
    <table width="100%" cellpadding="0" cellspacing="0" border="0" style="border-collapse:collapse;margin-bottom:24px">
      {fila("ID reclamación", f'<strong>{_e(r.get("id"))}</strong>')}
      {fila("Tipo de novedad", _e(r.get("tipo_novedad")))}
      {fila("VIN del vehículo", f'<span style="font-family:monospace">{_e(r.get("vin"))}</span>')}
      {fila("Vehículo", _e(r.get("vehiculo")))}
      {fila("Transportadora", _e(r.get("transportadora")))}
      {fila("No. Remesa", _e(r.get("no_remesa")))}
      {fila("No. Manifiesto", _e(r.get("no_manifiesto")))}
      {fila("Sede", _e(r.get("sede")))}
      {fila("Reportado por", _e(r.get("reportado_por")))}
    </table>

    <p style="font-family:'Montserrat',Arial,sans-serif;font-size:11px;font-weight:700;color:#9ca3af;text-transform:uppercase;letter-spacing:1.5px;margin:0 0 10px 0">Descripción de la novedad</p>
    <div style="font-family:'Montserrat',Arial,sans-serif;font-size:13px;color:#374151;border:1px solid #e8eaed;border-radius:4px;padding:14px 16px;line-height:1.7;margin-bottom:24px;background:#fafafa">
      {_e(r.get("descripcion"))}
    </div>

    <div style="background:#eff6ff;border:1px solid #bfdbfe;border-radius:4px;padding:14px 16px;margin-bottom:0">
      <p style="font-family:'Montserrat',Arial,sans-serif;font-size:12px;font-weight:700;color:#1e40af;margin:0 0 4px 0;text-transform:uppercase;letter-spacing:0.5px">Acción requerida</p>
      <p style="font-family:'Montserrat',Arial,sans-serif;font-size:13px;color:#1e3a8a;margin:0;line-height:1.6">
        Adjunte la cotización de reparación en el sistema para continuar con el proceso de reclamación.
      </p>
    </div>
    {_boton(url_acceso, "Adjuntar cotización en el sistema", "#1e3a5f")}"""

    html = _wrap(titulo, subtitulo, "#1e3a5f", cuerpo)
    subject = f"COLAUTOS – Novedad asignada a Colisión · {r.get('id','')}"
    _smtp_send(destinatarios, subject, html)
