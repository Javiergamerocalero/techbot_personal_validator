"""Envío de correo por SMTP.

Lo usa el botón de generar token del panel de administración. Va aparte
para que el router no sepa de SMTP y para poder probarlo suelto.

Las credenciales salen de la configuración (`.env`), nunca del código.
Si no están cargadas, `enviar` avisa con un error claro en vez de
fingir que mandó el correo: el operador tiene que saber que el token se
generó pero no llegó a ningún lado.
"""
import logging
import smtplib
import ssl
from email.message import EmailMessage

from app.core.config import get_settings

logger = logging.getLogger(__name__)


class MailNotConfigured(RuntimeError):
    """Faltan datos de SMTP en la configuración."""


class MailSendFailed(RuntimeError):
    """El servidor de correo rechazó el envío."""


def enviar(asunto: str, cuerpo: str, destinatario: str | None = None) -> str:
    """Manda un correo de texto plano. Devuelve el destinatario usado."""
    cfg = get_settings()

    faltantes = [
        nombre
        for nombre, valor in (
            ("SMTP_HOST", cfg.smtp_host),
            ("SMTP_USER", cfg.smtp_user),
            ("SMTP_PASSWORD", cfg.smtp_password),
            ("MAIL_FROM", cfg.mail_from),
        )
        if not valor
    ]
    if faltantes:
        raise MailNotConfigured(
            "Falta configurar " + ", ".join(faltantes) + " en el .env"
        )

    para = (destinatario or cfg.admin_token_mail_to or "").strip()
    if not para:
        raise MailNotConfigured("Falta configurar ADMIN_TOKEN_MAIL_TO")

    mensaje = EmailMessage()
    mensaje["Subject"] = asunto
    mensaje["From"] = cfg.mail_from
    mensaje["To"] = para
    mensaje.set_content(cuerpo)

    try:
        if cfg.smtp_use_ssl:
            contexto = ssl.create_default_context()
            with smtplib.SMTP_SSL(
                cfg.smtp_host, cfg.smtp_port, context=contexto, timeout=20
            ) as servidor:
                servidor.login(cfg.smtp_user, cfg.smtp_password)
                servidor.send_message(mensaje)
        else:
            with smtplib.SMTP(cfg.smtp_host, cfg.smtp_port, timeout=20) as servidor:
                servidor.ehlo()
                if cfg.smtp_use_starttls:
                    servidor.starttls(context=ssl.create_default_context())
                    servidor.ehlo()
                servidor.login(cfg.smtp_user, cfg.smtp_password)
                servidor.send_message(mensaje)
    except Exception as exc:  # noqa: BLE001 — se reempaqueta con contexto
        logger.error("mail.send_failed", extra={"error": str(exc), "to": para})
        raise MailSendFailed(str(exc)) from exc

    logger.info("mail.sent", extra={"to": para, "subject": asunto})
    return para
