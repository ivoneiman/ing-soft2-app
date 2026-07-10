import logging
import os
import random
from html import escape
from pathlib import Path

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv

try:
    from models import SystemSetting
except ModuleNotFoundError:
    from .models import SystemSetting


load_dotenv(Path(__file__).with_name(".env"))

logger = logging.getLogger(__name__)


DEFAULT_EMAIL_FROM = "noreply@siempregym.com"
DEFAULT_GYM_SITE_URL = "https://ing-soft2-app-git-develop-ivoneimans-projects.vercel.app"


def _email_from():
    return os.getenv("EMAIL_FROM", DEFAULT_EMAIL_FROM)


def _gym_site_url():
    return os.getenv("GYM_SITE_URL", DEFAULT_GYM_SITE_URL).rstrip("/")


def _has_valid_email(user):
    email = getattr(user, "email", None)
    if not email or "@" not in email:
        user_id = getattr(user, "id", "desconocido")
        logger.warning("[Email] Usuario sin email válido: %s", user_id)
        return False
    return True


def _send_email(to_email, subject, html):
    smtp_server = os.getenv("SMTP_SERVER", "smtp.gmail.com")
    smtp_port = int(os.getenv("SMTP_PORT", 587))
    smtp_username = os.getenv("SMTP_USERNAME")
    smtp_password = os.getenv("SMTP_PASSWORD")
    email_from = _email_from()

    if not smtp_username or not smtp_password:
        logger.warning("[Email] Credenciales SMTP no configuradas. Email omitido para %s", to_email)
        return False

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = email_from
    msg["To"] = to_email

    part = MIMEText(html, "html")
    msg.attach(part)

    try:
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(smtp_username, smtp_password)
            server.sendmail(email_from, to_email, msg.as_string())
        logger.info("[Email] Email enviado correctamente a %s", to_email)
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


def send_temporary_password_email(user, temporary_password):
    if not _has_valid_email(user):
        return False

    html = f"""
    <h1>Contraseña temporal - SiempreGym</h1>
    <p>Hola {escape(getattr(user, 'username', '') or '')},</p>
    <p>Se generó automáticamente una contraseña temporal para tu cuenta.</p>
    <p><strong>{escape(temporary_password)}</strong></p>
    <p>Ingresá con esta contraseña y cámbiala cuando lo necesites.</p>
    """

    return _send_email(
        user.email,
        "Contraseña temporal - SiempreGym",
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


def send_waitlist_promotion_email(user, class_obj, new_enrollment, other_pending_enrollments=None):
    if not _has_valid_email(user):
        return False

    activity_name = escape(_activity_name(class_obj))
    class_datetime = escape(_format_class_datetime(class_obj))
    site_url = _gym_site_url()
    offer_url = f"{site_url}/lista-espera/oferta/{new_enrollment.id}"

    pending_enrollments_section = ""
    if other_pending_enrollments:
        rows = "".join(
            f"<li>{escape(e.class_.actividad.name)} - {escape(e.class_.name)} ({escape(_format_class_datetime(e.class_))})</li>"
            for e in other_pending_enrollments
        )
        pending_enrollments_section = f"""
        <hr>
        <p><strong>Pagos pendientes adicionales:</strong></p>
        <ul>{rows}</ul>
        <p>Recordá que también debés abonar estas inscripciones para asegurar tu lugar.</p>
        """

    html = f"""
    <h1>¡Conseguiste un lugar de la lista de espera!</h1>
    <p>Hola {escape(getattr(user, 'username', '') or '')},</p>
    <p>Fuiste seleccionado/a de la lista de espera para la clase <strong>{activity_name} {class_datetime}</strong>, ya que se liberó un cupo.</p>
    <p>Entrá al siguiente link para decidir qué hacer: <a href="{offer_url}"><b>Ver mi lugar en la lista de espera</b></a></p>
    <p>Ahí vas a poder <strong>inscribirte y pagar</strong> para confirmar tu lugar, o <strong>liberarlo</strong> si en
    realidad ya no te interesa, para que se lo ofrezcamos a la siguiente persona en la lista de espera.</p>
    <p>También podés gestionarlo entrando a la página del gimnasio: <a href="{site_url}">{site_url}</a></p>
    {pending_enrollments_section}
    """

    return _send_email(
        user.email,
        f"Fuiste inscripto a la clase de {activity_name} - SiempreGym",
        html,
    )


def send_class_room_changed_email(user, class_obj, old_room, new_room):
    """
    Notifica a un usuario inscripto que el salón de su clase ha cambiado.
    """
    if not _has_valid_email(user):
        return False

    activity_name = escape(_activity_name(class_obj))
    class_datetime = escape(_format_class_datetime(class_obj))

    html = f"""
    <h1>Cambio de sala para tu clase</h1>
    <p>Hola {escape(getattr(user, 'username', '') or '')},</p>
    <p>Te informamos que hubo un cambio en una de tus próximas clases:</p>
    <p><strong>Clase:</strong> {activity_name}<br>
    <strong>Fecha y hora:</strong> {class_datetime}</p>
    <p>La sala fue modificado:</p>
    <ul>
        <li><strong>Sala anterior:</strong> {escape(old_room or 'No asignado')}</li>
        <li><strong>Nueva sala:</strong> {escape(new_room or 'No asignado')}</li>
    </ul>
    <p>¡Te esperamos!</p>
    """

    return _send_email(user.email, f"Cambio de sala para {activity_name}", html)
