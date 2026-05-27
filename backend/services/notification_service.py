try:
    from models import Notification, db, SystemSetting
except ModuleNotFoundError:
    from ..models import Notification, db, SystemSetting


def _get_cancellation_notification_text(class_obj, credited):
    try:
        setting = SystemSetting.query.filter_by(key="cancellation_notification_message").first()
        if setting and isinstance(setting.value, str) and setting.value.strip():
            template = setting.value.strip()
            class_datetime = (
                class_obj.fecha_hora.strftime("%d/%m/%Y %H:%M")
                if class_obj.fecha_hora
                else "fecha a confirmar"
            )
            message = template.replace("{class_name}", class_obj.name or "Clase")
            message = message.replace("{activity_name}", getattr(class_obj.actividad, "name", class_obj.name or "Actividad"))
            message = message.replace("{class_datetime}", class_datetime)
            if credited:
                message += " Se acreditó un crédito reutilizable en tu cuenta."
            return message
    except Exception:
        pass

    class_datetime = (
        class_obj.fecha_hora.strftime("%d/%m/%Y %H:%M")
        if class_obj.fecha_hora
        else "fecha a confirmar"
    )
    if credited:
        return (
            f"La clase {class_obj.name} del día {class_datetime} fue cancelada. "
            "Se acreditó un crédito reutilizable en tu cuenta."
        )
    return f"La clase {class_obj.name} del día {class_datetime} fue cancelada."


def create_cancellation_notification(enrollment, class_obj, credited):
    message = _get_cancellation_notification_text(class_obj, credited)
    notification = Notification(
        user_id=enrollment.user_id,
        title="Clase cancelada",
        message=message,
    )
    db.session.add(notification)
    return notification


def notifications_for_user(user_id):
    return (
        Notification.query
        .filter_by(user_id=user_id)
        .order_by(Notification.created_at.desc(), Notification.id.desc())
        .all()
    )
