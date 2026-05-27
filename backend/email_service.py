import logging
import os
import random
from html import escape
from pathlib import Path

from dotenv import load_dotenv
try:
    import resend
except ModuleNotFoundError:
    resend = None

try:
    from models import SystemSetting
except ModuleNotFoundError:
    from .models import SystemSetting


load_dotenv(Path(__file__).with_name(".env"))

if resend:
    resend.api_key = os.getenv("RESEND_API_KEY")

logger = logging.getLogger(__name__)


DEFAULT_EMAIL_FROM = "onboarding@resend.dev"


def _email_from():
    return os.getenv("EMAIL_FROM", DEFAULT_EMAIL_FROM)


def _has_valid_email(user):
    email = getattr(user, "email", None)
    if not email or "@" not in email:
        user_id = getattr(user, "id", "desconocido")
        logger.warning("[Email] Usuario sin email válido: %s", user_id)
        return False
    return True


def _send_email(to_email, subject, html):
    if not resend:
        logger.warning("[Email] SDK resend no instalado. Email omitido para %s", to_email)
        return False

    if not resend.api_key:
        logger.warning("[Email] RESEND_API_KEY no configurada. Email omitido para %s", to_email)
        return False

    try:
        response = resend.Emails.send({
            "from": _email_from(),
            "to": [to_email],
            "subject": subject,
            "html": html,
        })
        email_id = response.get("id") if isinstance(response, dict) else None
        logger.info("[Email] Email enviado correctamente a %s. resend_id=%s", to_email, email_id)
        return True
    except Exception:
        logger.exception("[Email] Error enviando email a %s", to_email)
        return False


def send_admin_login_code(user, code):
    if not _has_valid_email(user):
        return False

    html = f"""
    <h1>Código de verificación</h1>
    <p>Hola {escape(getattr(user, 'username', '') or '')},</p>
    <p>Utilizá el siguiente código para iniciar sesión como administrador:</p>
    <p><strong>{escape(code)}</strong></p>
    <p>El código expira en 5 minutos.</p>
    """

    return _send_email(
        user.email,
        "Código de verificación - SiempreGym",
        html,
    )


def _format_class_datetime(class_obj):
    if not getattr(class_obj, "fecha_hora", None):
        return "fecha a confirmar"
    return class_obj.fecha_hora.strftime("%d/%m/%Y %H:%M")


def _format_credit_expiration(credit):
    if not credit or not getattr(credit, "expires_at", None):
        return "fecha a confirmar"
    return credit.expires_at.strftime("%d/%m/%Y")


def _activity_name(class_obj):
    activity = getattr(class_obj, "actividad", None)
    return getattr(activity, "name", None) or getattr(class_obj, "name", "Actividad")


def _get_cancellation_notification_message():
    try:
        setting = SystemSetting.query.filter_by(key="cancellation_notification_message").first()
        if setting and isinstance(setting.value, str) and setting.value.strip():
            return setting.value.strip()
    except Exception:
        logger.exception("[Email] Error leyendo mensaje de notificación de cancelación de clase")
    return None


def _render_cancellation_message(template, class_obj, credit_generated=False):
    class_name = escape(getattr(class_obj, "name", "Clase"))
    activity_name = escape(_activity_name(class_obj))
    class_datetime = escape(_format_class_datetime(class_obj))

    safe_template = escape(template)
    safe_template = safe_template.replace("{class_name}", class_name)
    safe_template = safe_template.replace("{activity_name}", activity_name)
    safe_template = safe_template.replace("{class_datetime}", class_datetime)

    html_message = f"<p>{safe_template}</p>"
    if credit_generated:
        html_message += "<p>Además, se generó un crédito reutilizable en tu cuenta.</p>"
    return html_message


def send_class_cancelled_email(user, class_obj, credit_generated=False):
    if not _has_valid_email(user):
        return False

    admin_message = _get_cancellation_notification_message()
    if admin_message:
        message_body = _render_cancellation_message(admin_message, class_obj, credit_generated)
    else:
        class_name = escape(getattr(class_obj, "name", "Clase"))
        activity_name = escape(_activity_name(class_obj))
        class_datetime = escape(_format_class_datetime(class_obj))
        credit_note = (
            "<p>Además, se generó un crédito reutilizable en tu cuenta.</p>"
            if credit_generated
            else ""
        )
        message_body = f"""
        <p>La clase <strong>{class_name}</strong> de <strong>{activity_name}</strong> fue cancelada.</p>
        <p><strong>Fecha y hora:</strong> {class_datetime}</p>
        <p>Te avisamos para que puedas reorganizar tu agenda.</p>
        {credit_note}
        """

    html = f"""
    <h1>Clase cancelada - SiempreGym</h1>
    <p>Hola {escape(getattr(user, 'username', '') or '')},</p>
    {message_body}
    """

    return _send_email(
        user.email,
        "Clase cancelada - SiempreGym",
        html,
    )


def send_credit_generated_email(user, class_obj, credit):
    if not _has_valid_email(user):
        return False

    activity_name = escape(_activity_name(class_obj))
    class_name = escape(getattr(class_obj, "name", "Clase"))
    expires_at = escape(_format_credit_expiration(credit))
    html = f"""
    <h1>Crédito generado - SiempreGym</h1>
    <p>Hola {escape(getattr(user, "username", "") or "")},</p>
    <p>Se generó un crédito reutilizable por la cancelación de <strong>{class_name}</strong>.</p>
    <p><strong>Actividad asociada:</strong> {activity_name}</p>
    <p><strong>Vencimiento:</strong> {expires_at}</p>
    <p>Podés utilizar este crédito para otra clase de la misma actividad con cupos disponibles.</p>
    """

    return _send_email(
        user.email,
        "Crédito generado - SiempreGym",
        html,
    )
