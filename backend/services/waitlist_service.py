import logging
from datetime import datetime
from calendar import monthrange

try:
    from models import Class, Enrollment, WaitlistEntry, db
    from email_service import send_waitlist_promotion_email
    from constants import (
        ENROLLMENT_TYPE_MONTHLY,
        ENROLLMENT_CAPACITY_STATUSES,
        WAITLIST_TYPE_MONTHLY,
    )
    from services.class_service import enrollment_counts
    from services.enrollment_service import class_capacity
except ModuleNotFoundError:
    from ..models import Class, Enrollment, WaitlistEntry, db
    from ..email_service import send_waitlist_promotion_email
    from ..constants import (
        ENROLLMENT_TYPE_MONTHLY,
        ENROLLMENT_CAPACITY_STATUSES,
        WAITLIST_TYPE_MONTHLY,
    )
    from .class_service import enrollment_counts
    from .enrollment_service import class_capacity

logger = logging.getLogger(__name__)


def _series_classes_for_month(class_obj):
    if not class_obj or not class_obj.fecha_hora or not class_obj.id_actividad:
        return []

    year = class_obj.fecha_hora.year
    month = class_obj.fecha_hora.month
    start = datetime(year, month, 1, 0, 0, 0)
    end = datetime(year, month, monthrange(year, month)[1], 23, 59, 59)

    classes = (
        Class.query
        .filter(Class.id_actividad == class_obj.id_actividad)
        .filter(Class.estado == Class.STATUS_ACTIVE)
        .filter(Class.fecha_hora >= start)
        .filter(Class.fecha_hora <= end)
        .all()
    )

    return [
        c for c in classes
        if c.fecha_hora and c.fecha_hora.weekday() == class_obj.fecha_hora.weekday()
        and c.fecha_hora.strftime("%H:%M") == class_obj.fecha_hora.strftime("%H:%M")
    ]


def _user_has_monthly_implicit_enrollment(user, class_obj):
    if not class_obj or not user:
        return False

    target_weekday = class_obj.fecha_hora.weekday()
    target_time = class_obj.fecha_hora.strftime("%H:%M")
    month_start = datetime(class_obj.fecha_hora.year, class_obj.fecha_hora.month, 1)
    month_end = datetime(class_obj.fecha_hora.year, class_obj.fecha_hora.month, monthrange(class_obj.fecha_hora.year, class_obj.fecha_hora.month)[1], 23, 59, 59)

    monthly_enrollments = (
        Enrollment.query
        .filter_by(user_id=user.id, tipo=ENROLLMENT_TYPE_MONTHLY)
        .filter(Enrollment.estado.in_(ENROLLMENT_CAPACITY_STATUSES))
        .join(Class)
        .filter(Class.id_actividad == class_obj.id_actividad)
        .filter(Class.fecha_hora >= month_start)
        .filter(Class.fecha_hora <= month_end)
        .all()
    )

    for enrollment in monthly_enrollments:
        if not enrollment.class_ or not enrollment.class_.fecha_hora:
            continue
        if enrollment.class_.fecha_hora.weekday() != target_weekday:
            continue
        if enrollment.class_.fecha_hora.strftime("%H:%M") != target_time:
            continue
        return True

    return False


def user_is_enrolled_in_class(user, class_obj):
    if not user or not class_obj:
        return False

    direct_enrollment = (
        Enrollment.query
        .filter_by(user_id=user.id, class_id=class_obj.id)
        .filter(Enrollment.estado.in_(ENROLLMENT_CAPACITY_STATUSES))
        .first()
    )
    if direct_enrollment:
        return True

    return _user_has_monthly_implicit_enrollment(user, class_obj)


def add_waitlist_entry(user, class_obj, waitlist_type):
    if not user:
        return None, "No autenticado"
    if not class_obj:
        return None, "Clase no encontrada"
    if class_obj.estado != Class.STATUS_ACTIVE:
        return None, "La clase no está disponible para lista de espera"
    if user_is_enrolled_in_class(user, class_obj):
        return None, "Ya estás inscripto a esta clase"

    existing = (
        WaitlistEntry.query
        .filter_by(user_id=user.id, class_id=class_obj.id, type=waitlist_type)
        .first()
    )
    if existing:
        return None, "Ya te encuentras inscripto en la lista de espera de esta clase"

    if waitlist_type != WAITLIST_TYPE_MONTHLY:
        return None, "Tipo de lista de espera inválido"

    entry = WaitlistEntry(user_id=user.id, class_id=class_obj.id, type=waitlist_type)
    db.session.add(entry)
    return entry, None


def get_next_waitlist_entry(class_obj, entry_type=None):
    query = WaitlistEntry.query.filter_by(class_id=class_obj.id)
    if entry_type:
        query = query.filter_by(type=entry_type)
    return query.order_by(WaitlistEntry.created_at.asc(), WaitlistEntry.id.asc()).first()


def _available_spots(class_obj):
    if not class_obj:
        return 0
    counts = enrollment_counts()
    return class_capacity(class_obj) - counts.get(class_obj.id, 0)


def get_pending_payments_for_user(user, exclude_class_id=None):
    if not user:
        return []

    query = Enrollment.query.filter_by(user_id=user.id, estado=Enrollment.STATUS_PENDING_PAYMENT)
    if exclude_class_id is not None:
        query = query.filter(Enrollment.class_id != exclude_class_id)
    pending = query.all()

    results = []
    for enrollment in pending:
        if not enrollment.class_:
            continue
        results.append({
            "class_name": enrollment.class_.name,
            "actividad": enrollment.class_.actividad.name if enrollment.class_.actividad else None,
            "fecha_hora": enrollment.class_.fecha_hora.isoformat() if enrollment.class_.fecha_hora else None,
            "status": enrollment.estado,
        })
    return results


def _discard_waitlist_entry(entry, reason):
    logger.info(
        "[Waitlist] descarta_entry entry_id=%s user_id=%s class_id=%s type=%s reason=%s",
        getattr(entry, "id", None),
        getattr(entry, "user_id", None),
        getattr(entry, "class_id", None),
        getattr(entry, "type", None),
        reason,
    )
    db.session.delete(entry)


def promote_next_waitlisted_user(class_obj):
    if not class_obj:
        return None
    if class_obj.estado != Class.STATUS_ACTIVE:
        return None

    if _available_spots(class_obj) <= 0:
        logger.info("[Waitlist] sin_cupo class_id=%s", class_obj.id)
        return None

    entries = (
        WaitlistEntry.query
        .filter_by(class_id=class_obj.id, type=WAITLIST_TYPE_MONTHLY)
        .order_by(WaitlistEntry.created_at.asc(), WaitlistEntry.id.asc())
        .all()
    )
    for entry in entries:
        if _available_spots(class_obj) <= 0:
            return None

        user = entry.user
        if not user:
            _discard_waitlist_entry(entry, "missing_user")
            continue
        if user_is_enrolled_in_class(user, class_obj):
            _discard_waitlist_entry(entry, "already_enrolled")
            continue

        enrollment = Enrollment.query.filter_by(user_id=user.id, class_id=class_obj.id).first()
        if enrollment and enrollment.estado in Enrollment.CAPACITY_STATUSES:
            _discard_waitlist_entry(entry, "active_enrollment")
            continue

        if enrollment:
            enrollment.estado = Enrollment.STATUS_PENDING_PAYMENT
            enrollment.tipo = ENROLLMENT_TYPE_MONTHLY
            enrollment.requiere_reembolso = False
        else:
            enrollment = Enrollment(
                user_id=user.id,
                class_id=class_obj.id,
                tipo=ENROLLMENT_TYPE_MONTHLY,
                estado=Enrollment.STATUS_PENDING_PAYMENT,
            )
            db.session.add(enrollment)

        db.session.delete(entry)
        db.session.flush()

        pending_payments = get_pending_payments_for_user(user, exclude_class_id=class_obj.id)
        email_sent = send_waitlist_promotion_email(user, class_obj, pending_payments=pending_payments)

        logger.info(
            "[Waitlist] promovido user_id=%s class_id=%s enrollment_id=%s email_sent=%s",
            user.id,
            class_obj.id,
            enrollment.id,
            email_sent,
        )
        return {
            "type": WAITLIST_TYPE_MONTHLY,
            "user": user,
            "class_obj": class_obj,
            "enrollment": enrollment,
            "email_sent": email_sent,
        }

    return None


def delete_waitlists_for_user_and_series(user, base_class_obj):
    if not user or not base_class_obj:
        return 0

    classes = _series_classes_for_month(base_class_obj)
    class_ids = [c.id for c in classes]
    deleted = (
        WaitlistEntry.query
        .filter(WaitlistEntry.user_id == user.id)
        .filter(WaitlistEntry.class_id.in_(class_ids))
        .delete(synchronize_session=False)
    )
    return deleted


def _full_classes_in_series(base_class_obj, enrollment_map):
    full_classes = []
    for class_obj in _series_classes_for_month(base_class_obj):
        capacity = class_capacity(class_obj)
        current = enrollment_map.get(class_obj.id, 0)
        if current >= capacity:
            full_classes.append(class_obj)
    return full_classes


def monthly_series_has_full_class(base_class_obj, enrollment_map):
    """La inscripción mensual cubre todas las semanas del mes en ese horario, así que
    alcanza con que UNA sola fecha de la serie esté llena para que la suscripción
    completa deba pasar por la lista de espera en vez de cobrarse."""
    return bool(_full_classes_in_series(base_class_obj, enrollment_map))


def create_monthly_waitlist_for_full_series(user, base_class_obj, enrollment_map):
    """Anota al usuario en la lista de espera de cada fecha de la serie mensual que ya
    esté llena (incluida la clase elegida, si corresponde), para que se lo promueva
    fecha por fecha a medida que se liberen lugares."""
    if not user or not base_class_obj:
        return []

    waitlist_entries = []
    for class_obj in _full_classes_in_series(base_class_obj, enrollment_map):
        existing = (
            WaitlistEntry.query
            .filter_by(user_id=user.id, class_id=class_obj.id, type=WAITLIST_TYPE_MONTHLY)
            .first()
        )
        if existing:
            continue
        entry = WaitlistEntry(user_id=user.id, class_id=class_obj.id, type=WAITLIST_TYPE_MONTHLY)
        db.session.add(entry)
        waitlist_entries.append(entry)

    return waitlist_entries
