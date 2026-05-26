import logging

try:
    from models import Enrollment, db
    from services.credit_service import generate_credit_for_paid_enrollment
    from services.notification_service import create_cancellation_notification
except ModuleNotFoundError:
    from ..models import Enrollment, db
    from .credit_service import generate_credit_for_paid_enrollment
    from .notification_service import create_cancellation_notification

logger = logging.getLogger(__name__)


def cancel_class(class_obj, current_dt):
    class_obj.estado = class_obj.STATUS_CANCELLED
    enrollments = Enrollment.query.filter_by(class_id=class_obj.id).all()

    credits_created = 0
    notifications_created = 0
    email_jobs = []
    for enrollment in enrollments:
        credit = generate_credit_for_paid_enrollment(enrollment, class_obj, current_dt)
        credited = credit is not None
        if credited:
            credits_created += 1

        create_cancellation_notification(enrollment, class_obj, credited)
        notifications_created += 1

        if enrollment.estado != Enrollment.STATUS_CANCELLED:
            enrollment.estado = Enrollment.STATUS_CANCELLED

        email_jobs.append((enrollment.user, class_obj, credit))

    logger.info(
        "[Cancelaciones] class_id=%s enrollments=%s credits=%s notifications=%s",
        class_obj.id,
        len(enrollments),
        credits_created,
        notifications_created,
    )
    return {
        "credits_created": credits_created,
        "notifications_created": notifications_created,
        "email_jobs": email_jobs,
    }
