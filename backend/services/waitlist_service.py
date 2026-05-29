import logging
from datetime import datetime
from calendar import monthrange

try:
    from models import Class, Enrollment, WaitlistEntry, db
    from constants import (
        ENROLLMENT_TYPE_MONTHLY,
        ENROLLMENT_TYPE_SINGLE,
        ENROLLMENT_CAPACITY_STATUSES,
        WAITLIST_TYPE_INDIVIDUAL,
        WAITLIST_TYPE_MONTHLY,
    )
except ModuleNotFoundError:
    from ..models import Class, Enrollment, WaitlistEntry, db
    from ..constants import (
        ENROLLMENT_TYPE_MONTHLY,
        ENROLLMENT_TYPE_SINGLE,
        ENROLLMENT_CAPACITY_STATUSES,
        WAITLIST_TYPE_INDIVIDUAL,
        WAITLIST_TYPE_MONTHLY,
    )

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
        return None, "Ya estás en la lista de espera de esta clase"

    if waitlist_type != WAITLIST_TYPE_INDIVIDUAL and waitlist_type != WAITLIST_TYPE_MONTHLY:
        return None, "Tipo de lista de espera inválido"

    entry = WaitlistEntry(user_id=user.id, class_id=class_obj.id, type=waitlist_type)
    db.session.add(entry)
    return entry, None


def get_next_waitlist_entry(class_obj, entry_type=None):
    query = WaitlistEntry.query.filter_by(class_id=class_obj.id)
    if entry_type:
        query = query.filter_by(type=entry_type)
    return query.order_by(WaitlistEntry.created_at.asc(), WaitlistEntry.id.asc()).first()


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


def promote_next_waitlisted_user(class_obj):
    if not class_obj:
        return None

    monthly_entry = get_next_waitlist_entry(class_obj, WAITLIST_TYPE_MONTHLY)
    if monthly_entry:
        enrollment = Enrollment(
            user_id=monthly_entry.user_id,
            class_id=class_obj.id,
            tipo=ENROLLMENT_TYPE_MONTHLY,
            estado=Enrollment.STATUS_PENDING_PAYMENT,
        )
        db.session.add(enrollment)
        db.session.delete(monthly_entry)
        return {
            "type": WAITLIST_TYPE_MONTHLY,
            "user": monthly_entry.user,
            "class_obj": class_obj,
            "enrollment": enrollment,
        }

    individual_entry = get_next_waitlist_entry(class_obj, WAITLIST_TYPE_INDIVIDUAL)
    if individual_entry:
        enrollment = Enrollment(
            user_id=individual_entry.user_id,
            class_id=class_obj.id,
            tipo=ENROLLMENT_TYPE_SINGLE,
            estado=Enrollment.STATUS_PENDING_PAYMENT,
        )
        db.session.add(enrollment)
        db.session.delete(individual_entry)
        return {
            "type": WAITLIST_TYPE_INDIVIDUAL,
            "user": individual_entry.user,
            "class_obj": class_obj,
            "enrollment": enrollment,
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


def create_monthly_waitlist_for_full_series(user, base_class_obj, enrollment_map):
    if not user or not base_class_obj:
        return []

    waitlist_entries = []
    for class_obj in _series_classes_for_month(base_class_obj):
        if class_obj.id == base_class_obj.id:
            continue

        capacity = class_obj.cupoMaximo if class_obj.cupoMaximo is not None else 20
        current = enrollment_map.get(class_obj.id, 0)
        if current >= capacity:
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
