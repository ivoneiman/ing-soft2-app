import logging
import os
from html import escape
from pathlib import Path

from dotenv import load_dotenv
try:
    import resend
except ModuleNotFoundError:
    resend = None


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


def send_class_cancelled_email(user, class_obj, credit_generated=False):
    if not _has_valid_email(user):
        return False

    class_name = escape(getattr(class_obj, "name", "Clase"))
    activity_name = escape(_activity_name(class_obj))
    class_datetime = escape(_format_class_datetime(class_obj))
    credit_note = (
        "<p>Además, se generó un crédito reutilizable en tu cuenta.</p>"
        if credit_generated
        else ""
    )
    html = f"""
    <h1>Clase cancelada - SiempreGym</h1>
    <p>Hola {escape(getattr(user, "username", "") or "")},</p>
    <p>La clase <strong>{class_name}</strong> de <strong>{activity_name}</strong> fue cancelada.</p>
    <p><strong>Fecha y hora:</strong> {class_datetime}</p>
    <p>Te avisamos para que puedas reorganizar tu agenda.</p>
    {credit_note}
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
