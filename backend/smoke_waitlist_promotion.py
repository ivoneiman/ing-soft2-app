from datetime import datetime, timedelta

import app as app_module
from app import app, db
from constants import (
    ENROLLMENT_STATUS_CANCELLED,
    ENROLLMENT_STATUS_PENDING_PAYMENT,
    ENROLLMENT_TYPE_MONTHLY,
    ENROLLMENT_TYPE_SINGLE,
    WAITLIST_TYPE_INDIVIDUAL,
    WAITLIST_TYPE_MONTHLY,
)
from models import Actividades, Attendance, Class, Enrollment, Notification, Payment, User, WaitlistEntry
from services import waitlist_service


def set_session_user(client, user_id):
    with client.session_transaction() as session:
        session["user_id"] = user_id


def assert_equal(label, actual, expected):
    if actual != expected:
        raise AssertionError(f"{label}: expected {expected!r}, got {actual!r}")


def assert_true(label, value):
    if not value:
        raise AssertionError(f"{label}: expected truthy value, got {value!r}")


def create_user(label, suffix):
    user = User(
        username=f"{label}{suffix[-4:]}",
        apellido="Waitlist",
        email=f"smoke-waitlist-{label}-{suffix}@example.test",
        dni=f"{label[:1]}{suffix[-7:]}",
        telefono="000",
        role="client",
    )
    user.set_password("pass")
    db.session.add(user)
    db.session.flush()
    return user


def create_class(activity, label, capacity=1):
    class_obj = Class(
        name=f"{activity.name} {label}",
        fecha_hora=datetime.now() + timedelta(days=7),
        id_actividad=activity.id,
        cupoMaximo=capacity,
        descuento=0,
    )
    db.session.add(class_obj)
    db.session.flush()
    return class_obj


def create_enrollment(user, class_obj, status=ENROLLMENT_STATUS_PENDING_PAYMENT, tipo=ENROLLMENT_TYPE_SINGLE):
    enrollment = Enrollment(
        user_id=user.id,
        class_id=class_obj.id,
        tipo=tipo,
        estado=status,
    )
    db.session.add(enrollment)
    db.session.flush()
    return enrollment


def waitlist(user, class_obj, waitlist_type, created_at=None):
    entry = WaitlistEntry(
        user_id=user.id,
        class_id=class_obj.id,
        type=waitlist_type,
        created_at=created_at or datetime.now(),
    )
    db.session.add(entry)
    db.session.flush()
    return entry


def main():
    original_send_email = waitlist_service.send_waitlist_promotion_email
    sent_emails = []
    waitlist_service.send_waitlist_promotion_email = (
        lambda user, class_obj, pending_payments=None: sent_emails.append((user.id, class_obj.id, pending_payments or [])) or True
    )

    created = []
    try:
        with app.app_context():
            suffix = datetime.now().strftime("%Y%m%d%H%M%S%f")
            activity = Actividades(name=f"Smoke Waitlist {suffix}")
            db.session.add(activity)
            db.session.flush()
            created.append(("activity", activity.id))
            activity_id = activity.id

            owner = create_user("owner", suffix)
            monthly = create_user("monthly", suffix)
            individual = create_user("individual", suffix)
            fifo_first = create_user("fifoA", suffix)
            fifo_second = create_user("fifoB", suffix)
            already_user = create_user("already", suffix)
            users = [owner, monthly, individual, fifo_first, fifo_second, already_user]
            created.extend([("user", user.id) for user in users])
            owner_id = owner.id
            fifo_first_id = fifo_first.id
            fifo_second_id = fifo_second.id
            already_user_id = already_user.id

            priority_class = create_class(activity, "priority", capacity=1)
            owner_enrollment = create_enrollment(owner, priority_class)
            waitlist(individual, priority_class, WAITLIST_TYPE_INDIVIDUAL, datetime.now() - timedelta(minutes=10))
            waitlist(monthly, priority_class, WAITLIST_TYPE_MONTHLY, datetime.now() - timedelta(minutes=1))
            created.extend([("class", priority_class.id), ("enrollment", owner_enrollment.id)])
            db.session.commit()
            priority_class_id = priority_class.id
            owner_enrollment_id = owner_enrollment.id
            monthly_id = monthly.id
            individual_id = individual.id

        http = app.test_client()
        set_session_user(http, owner_id)
        cancel_res = http.post(f"/api/enrollments/{owner_enrollment_id}/cancel", json={})
        assert_equal("cancel triggers promotion", cancel_res.status_code, 200)
        with app.app_context():
            promoted = Enrollment.query.filter_by(user_id=monthly_id, class_id=priority_class_id).first()
            assert_true("monthly promoted first", promoted)
            assert_equal("monthly promoted pending", promoted.estado, ENROLLMENT_STATUS_PENDING_PAYMENT)
            assert_equal("monthly promoted type", promoted.tipo, ENROLLMENT_TYPE_MONTHLY)
            assert_equal("individual remains waitlisted", WaitlistEntry.query.filter_by(user_id=individual_id, class_id=priority_class_id).count(), 1)
            assert_true("promotion notification", Notification.query.filter_by(user_id=monthly_id, title="Cupo disponible").first())
            assert_equal("promotion email sent", len(sent_emails), 1)
            set_session_user(http, monthly_id)
            pending_res = http.get("/api/enrollments/pending")
            assert_equal("pending endpoint status", pending_res.status_code, 200)
            pending_ids = [item["id"] for item in pending_res.get_json()["enrollments"]]
            assert_true("promoted enrollment visible pending", promoted.id in pending_ids)
            created.append(("enrollment", promoted.id))

        with app.app_context():
            activity = db.session.get(Actividades, activity_id)
            fifo_class = create_class(activity, "fifo", capacity=1)
            owner2 = create_user("owner2", suffix)
            created.append(("user", owner2.id))
            full = create_enrollment(owner2, fifo_class)
            fifo_first = db.session.get(User, fifo_first_id)
            fifo_second = db.session.get(User, fifo_second_id)
            waitlist(fifo_first, fifo_class, WAITLIST_TYPE_INDIVIDUAL, datetime.now() - timedelta(minutes=5))
            waitlist(fifo_second, fifo_class, WAITLIST_TYPE_INDIVIDUAL, datetime.now() - timedelta(minutes=1))
            created.extend([("class", fifo_class.id), ("enrollment", full.id)])
            db.session.commit()
            fifo_class_id = fifo_class.id
            full_id = full.id
            owner2_id = owner2.id

        set_session_user(http, owner2_id)
        fifo_cancel = http.post(f"/api/enrollments/{full_id}/cancel", json={})
        assert_equal("fifo cancel status", fifo_cancel.status_code, 200)
        with app.app_context():
            first_enrollment = Enrollment.query.filter_by(user_id=fifo_first_id, class_id=fifo_class_id).first()
            second_enrollment = Enrollment.query.filter_by(user_id=fifo_second_id, class_id=fifo_class_id).first()
            assert_true("fifo first promoted", first_enrollment)
            assert_equal("fifo second not promoted", second_enrollment, None)
            created.append(("enrollment", first_enrollment.id))

        with app.app_context():
            activity = db.session.get(Actividades, activity_id)
            skip_class = create_class(activity, "skip-invalid", capacity=2)
            owner3 = create_user("owner3", suffix)
            fallback = create_user("fallback", suffix)
            created.extend([("user", owner3.id), ("user", fallback.id)])
            full_skip = create_enrollment(owner3, skip_class)
            already_user = db.session.get(User, already_user_id)
            already_enrollment = create_enrollment(already_user, skip_class, status=ENROLLMENT_STATUS_CANCELLED)
            already_enrollment.estado = ENROLLMENT_STATUS_PENDING_PAYMENT
            waitlist(already_user, skip_class, WAITLIST_TYPE_INDIVIDUAL, datetime.now() - timedelta(minutes=5))
            waitlist(fallback, skip_class, WAITLIST_TYPE_INDIVIDUAL, datetime.now() - timedelta(minutes=1))
            created.extend([("class", skip_class.id), ("enrollment", full_skip.id), ("enrollment", already_enrollment.id)])
            db.session.commit()
            skip_class_id = skip_class.id
            full_skip_id = full_skip.id
            fallback_id = fallback.id
            owner3_id = owner3.id

        set_session_user(http, owner3_id)
        skip_cancel = http.post(f"/api/enrollments/{full_skip_id}/cancel", json={})
        assert_equal("skip invalid cancel status", skip_cancel.status_code, 200)
        with app.app_context():
            fallback_enrollment = Enrollment.query.filter_by(user_id=fallback_id, class_id=skip_class_id).first()
            assert_true("fallback promoted after invalid", fallback_enrollment)
            created.append(("enrollment", fallback_enrollment.id))

        with app.app_context():
            activity = db.session.get(Actividades, activity_id)
            no_space_class = create_class(activity, "no-space", capacity=1)
            no_space_owner = create_user("owner4", suffix)
            no_space_wait = create_user("wait4", suffix)
            created.extend([("user", no_space_owner.id), ("user", no_space_wait.id)])
            no_space_enrollment = create_enrollment(no_space_owner, no_space_class)
            waitlist(no_space_wait, no_space_class, WAITLIST_TYPE_INDIVIDUAL)
            created.extend([("class", no_space_class.id), ("enrollment", no_space_enrollment.id)])
            db.session.commit()
            no_space_result = waitlist_service.promote_next_waitlisted_user(no_space_class)
            assert_equal("no space no promotion", no_space_result, None)

            empty_class = create_class(activity, "empty", capacity=2)
            created.append(("class", empty_class.id))
            db.session.commit()
            empty_result = waitlist_service.promote_next_waitlisted_user(empty_class)
            assert_equal("no waitlist no promotion", empty_result, None)

        print("waitlist promotion smoke ok")
    finally:
        waitlist_service.send_waitlist_promotion_email = original_send_email
        with app.app_context():
            db.session.rollback()
            for _, enrollment_id in [item for item in reversed(created) if item[0] == "enrollment"]:
                Payment.query.filter_by(enrollment_id=enrollment_id).delete()
                enrollment = db.session.get(Enrollment, enrollment_id)
                if enrollment:
                    Notification.query.filter_by(user_id=enrollment.user_id).delete()
                    Attendance.query.filter_by(user_id=enrollment.user_id, class_id=enrollment.class_id).delete()
                    db.session.delete(enrollment)
            for _, class_id in [item for item in reversed(created) if item[0] == "class"]:
                WaitlistEntry.query.filter_by(class_id=class_id).delete()
                class_obj = db.session.get(Class, class_id)
                if class_obj:
                    db.session.delete(class_obj)
            for _, user_id in [item for item in reversed(created) if item[0] == "user"]:
                Notification.query.filter_by(user_id=user_id).delete()
                user = db.session.get(User, user_id)
                if user:
                    db.session.delete(user)
            for _, activity_id in [item for item in reversed(created) if item[0] == "activity"]:
                activity = db.session.get(Actividades, activity_id)
                if activity:
                    db.session.delete(activity)
            db.session.commit()


if __name__ == "__main__":
    main()
