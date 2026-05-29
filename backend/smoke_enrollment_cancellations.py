from datetime import datetime, timedelta

import app as app_module
from app import app, db
from constants import (
    ENROLLMENT_PAYMENT_STATUS_PAID,
    ENROLLMENT_PAYMENT_STATUS_PARTIALLY_PAID,
    ENROLLMENT_PAYMENT_STATUS_PENDING,
    ENROLLMENT_STATUS_CANCELLED,
    PAYMENT_TYPE_DEPOSIT,
    PAYMENT_TYPE_FULL,
)
from models import Actividades, Attendance, Class, Credit, Enrollment, Notification, Payment, User
from services import class_service, payment_service


class FakePayment:
    responses = {}

    def get(self, payment_id):
        return {
            "status": 200,
            "response": self.responses.get(str(payment_id), {}),
        }


class FakeMercadoPagoClient:
    def payment(self):
        return FakePayment()


def set_session_user(client, user_id):
    with client.session_transaction() as session:
        session["user_id"] = user_id


def assert_equal(label, actual, expected):
    if actual != expected:
        raise AssertionError(f"{label}: expected {expected!r}, got {actual!r}")


def assert_true(label, value):
    if not value:
        raise AssertionError(f"{label}: expected truthy value, got {value!r}")


def create_user(suffix):
    user = User(
        username=f"Smoke{suffix}",
        apellido="Cancel",
        email=f"smoke-cancel-{suffix}@example.test",
        dni=f"7{suffix[-7:]}",
        telefono="000",
        role="client",
    )
    user.set_password("pass")
    db.session.add(user)
    db.session.flush()
    return user


def create_class(activity, suffix, starts_in_days=7, starts_in_hours=0, capacity=1):
    class_obj = Class(
        name=f"{activity.name} {suffix}",
        fecha_hora=datetime.now() + timedelta(days=starts_in_days, hours=starts_in_hours),
        id_actividad=activity.id,
        cupoMaximo=capacity,
        descuento=0,
    )
    db.session.add(class_obj)
    db.session.flush()
    return class_obj


def create_enrollment(user, class_obj, status=Enrollment.STATUS_PENDING_PAYMENT, payment_status=ENROLLMENT_PAYMENT_STATUS_PENDING):
    enrollment = Enrollment(
        user_id=user.id,
        class_id=class_obj.id,
        estado=status,
        total_amount=3000,
        paid_amount=0,
        remaining_amount=3000,
        payment_status=payment_status,
    )
    db.session.add(enrollment)
    db.session.flush()
    return enrollment


def add_payment(enrollment, payment_type=PAYMENT_TYPE_FULL, method=Payment.METHOD_CASH, amount=3000, status=Payment.STATUS_APPROVED):
    payment = Payment(
        user_id=enrollment.user_id,
        enrollment_id=enrollment.id,
        class_id=enrollment.class_id,
        product_type=payment_service.payment_type_for_enrollment(enrollment),
        payment_type=payment_type,
        payment_method=method,
        amount=amount,
        discount_percentage=0,
        final_amount=amount,
        status=status,
    )
    db.session.add(payment)
    db.session.flush()
    db.session.expire(enrollment, ["payments"])
    payment_service.recompute_enrollment_payment_state(enrollment)
    return payment


def cancel(http, enrollment_id):
    return http.post(f"/api/enrollments/{enrollment_id}/cancel", json={})


def main():
    original_mp_client = app_module.get_mercadopago_client
    original_send_credit_email = app_module.send_credit_generated_email
    sent_emails = []

    app_module.get_mercadopago_client = lambda: FakeMercadoPagoClient()
    app_module.send_credit_generated_email = lambda user, class_obj, credit: sent_emails.append((user.id, class_obj.id, credit.id)) or True

    created = []
    try:
        with app.app_context():
            suffix = datetime.now().strftime("%Y%m%d%H%M%S%f")
            activity = Actividades(name=f"Smoke Cancel {suffix}")
            db.session.add(activity)
            db.session.flush()
            created.append(("activity", activity.id))

            user = create_user(suffix)
            created.append(("user", user.id))
            user_id = user.id

            db.session.commit()

        http = app.test_client()
        set_session_user(http, user_id)

        with app.app_context():
            activity = Actividades.query.filter(Actividades.name.like(f"Smoke Cancel {suffix}%")).first()

            no_pay_class = create_class(activity, "no-pay")
            no_pay = create_enrollment(db.session.get(User, user_id), no_pay_class)
            pending_payment = add_payment(no_pay, amount=3000, status=Payment.STATUS_PENDING)
            created.extend([("class", no_pay_class.id), ("enrollment", no_pay.id)])
            db.session.commit()
            no_pay_id = no_pay.id
            no_pay_class_id = no_pay_class.id
            pending_payment_id = pending_payment.id

        no_pay_res = cancel(http, no_pay_id)
        assert_equal("no pay cancel status", no_pay_res.status_code, 200)
        no_pay_body = no_pay_res.get_json()
        assert_equal("no pay no credit", no_pay_body["credit_generated"], False)
        with app.app_context():
            enrollment = db.session.get(Enrollment, no_pay_id)
            assert_equal("no pay enrollment cancelled", enrollment.estado, ENROLLMENT_STATUS_CANCELLED)
            assert_equal("no pay payment status preserved", enrollment.payment_status, ENROLLMENT_PAYMENT_STATUS_PENDING)
            assert_equal("pending payment expired", db.session.get(Payment, pending_payment_id).status, Payment.STATUS_EXPIRED)
            assert_equal("capacity released", class_service.enrollment_counts().get(no_pay_class_id, 0), 0)
            assert_equal("no pay credits", Credit.query.filter_by(enrollment_id=no_pay_id).count(), 0)

        duplicate_no_pay_res = cancel(http, no_pay_id)
        assert_equal("already cancelled rejected", duplicate_no_pay_res.status_code, 400)

        with app.app_context():
            activity = Actividades.query.filter(Actividades.name.like(f"Smoke Cancel {suffix}%")).first()

            full_class = create_class(activity, "full")
            full_enrollment = create_enrollment(db.session.get(User, user_id), full_class)
            add_payment(full_enrollment, amount=3000, status=Payment.STATUS_APPROVED)
            created.extend([("class", full_class.id), ("enrollment", full_enrollment.id)])

            deposit_class = create_class(activity, "deposit")
            deposit_enrollment = create_enrollment(db.session.get(User, user_id), deposit_class)
            add_payment(deposit_enrollment, payment_type=PAYMENT_TYPE_DEPOSIT, amount=1500, status=Payment.STATUS_APPROVED)
            created.extend([("class", deposit_class.id), ("enrollment", deposit_enrollment.id)])

            credit_class = create_class(activity, "credit")
            credit_enrollment = create_enrollment(db.session.get(User, user_id), credit_class)
            add_payment(credit_enrollment, method=Payment.METHOD_CREDIT, amount=0, status=Payment.STATUS_APPROVED)
            created.extend([("class", credit_class.id), ("enrollment", credit_enrollment.id)])

            soon_class = create_class(activity, "soon", starts_in_days=0, starts_in_hours=12)
            soon_enrollment = create_enrollment(db.session.get(User, user_id), soon_class)
            created.extend([("class", soon_class.id), ("enrollment", soon_enrollment.id)])

            db.session.commit()
            full_id = full_enrollment.id
            deposit_id = deposit_enrollment.id
            credit_id = credit_enrollment.id
            soon_id = soon_enrollment.id

        full_res = cancel(http, full_id)
        assert_equal("full cancel status", full_res.status_code, 200)
        assert_equal("full credit generated", full_res.get_json()["credit_generated"], True)

        deposit_res = cancel(http, deposit_id)
        assert_equal("deposit cancel status", deposit_res.status_code, 200)
        assert_equal("deposit credit generated", deposit_res.get_json()["credit_generated"], True)

        credit_res = cancel(http, credit_id)
        assert_equal("credit cancel status", credit_res.status_code, 200)
        assert_equal("credit payment cancel generates credit", credit_res.get_json()["credit_generated"], True)

        with app.app_context():
            assert_equal("full credit count", Credit.query.filter_by(enrollment_id=full_id).count(), 1)
            assert_equal("deposit credit count", Credit.query.filter_by(enrollment_id=deposit_id).count(), 1)
            assert_equal("credit-paid credit count", Credit.query.filter_by(enrollment_id=credit_id).count(), 1)
            assert_true("notifications created", Notification.query.filter(Notification.user_id == user_id).count() >= 3)
            assert_equal("full state cancelled", db.session.get(Enrollment, full_id).estado, ENROLLMENT_STATUS_CANCELLED)
            assert_equal("full payment status preserved", db.session.get(Enrollment, full_id).payment_status, ENROLLMENT_PAYMENT_STATUS_PAID)
            assert_equal("deposit state cancelled", db.session.get(Enrollment, deposit_id).estado, ENROLLMENT_STATUS_CANCELLED)
            assert_equal("deposit payment status preserved", db.session.get(Enrollment, deposit_id).payment_status, ENROLLMENT_PAYMENT_STATUS_PARTIALLY_PAID)
            assert_equal("emails sent", len(sent_emails), 3)

        duplicate_credit_res = cancel(http, full_id)
        assert_equal("duplicate credit request rejected", duplicate_credit_res.status_code, 400)
        with app.app_context():
            assert_equal("duplicate credit not created", Credit.query.filter_by(enrollment_id=full_id).count(), 1)

        soon_res = cancel(http, soon_id)
        assert_equal("within 24 hours rejected", soon_res.status_code, 400)

        FakePayment.responses["mp-late-cancel"] = {
            "external_reference": str(pending_payment_id),
            "status": "approved",
            "status_detail": "accredited",
        }
        late_callback_res = http.get(
            f"/api/payments/return/success?external_reference={pending_payment_id}"
            "&status=approved&payment_id=mp-late-cancel",
            follow_redirects=False,
        )
        assert_equal("late callback redirects", late_callback_res.status_code, 302)
        with app.app_context():
            assert_equal("late callback keeps payment expired", db.session.get(Payment, pending_payment_id).status, Payment.STATUS_EXPIRED)
            assert_equal("late callback keeps enrollment cancelled", db.session.get(Enrollment, no_pay_id).estado, ENROLLMENT_STATUS_CANCELLED)

        print("enrollment cancellations smoke ok")
    finally:
        app_module.get_mercadopago_client = original_mp_client
        app_module.send_credit_generated_email = original_send_credit_email
        with app.app_context():
            db.session.rollback()
            for _, enrollment_id in [item for item in reversed(created) if item[0] == "enrollment"]:
                Payment.query.filter_by(enrollment_id=enrollment_id).delete()
                Credit.query.filter_by(enrollment_id=enrollment_id).delete()
                enrollment = db.session.get(Enrollment, enrollment_id)
                if enrollment:
                    Notification.query.filter_by(user_id=enrollment.user_id).delete()
                    Attendance.query.filter_by(user_id=enrollment.user_id, class_id=enrollment.class_id).delete()
                    db.session.delete(enrollment)
            for _, class_id in [item for item in reversed(created) if item[0] == "class"]:
                class_obj = db.session.get(Class, class_id)
                if class_obj:
                    db.session.delete(class_obj)
            for _, user_id in [item for item in reversed(created) if item[0] == "user"]:
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
