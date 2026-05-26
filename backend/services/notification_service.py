try:
    from models import Notification, db
except ModuleNotFoundError:
    from ..models import Notification, db


def create_cancellation_notification(enrollment, class_obj, credited):
    class_datetime = (
        class_obj.fecha_hora.strftime("%d/%m/%Y %H:%M")
        if class_obj.fecha_hora
        else "fecha a confirmar"
    )
    if credited:
        message = (
            f"La clase {class_obj.name} del día {class_datetime} fue cancelada. "
            "Se acreditó un crédito reutilizable en tu cuenta."
        )
    else:
        message = f"La clase {class_obj.name} del día {class_datetime} fue cancelada."

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
