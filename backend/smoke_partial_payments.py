from datetime import datetime, timedelta

from app import app, db
import app as app_module
from constants import (
    ENROLLMENT_PAYMENT_STATUS_PAID,
    ENROLLMENT_PAYMENT_STATUS_PARTIALLY_PAID,
    ENROLLMENT_STATUS_PAID,
    ENROLLMENT_STATUS_PENDING_PAYMENT,
    MERCADO_PAGO_STATUS_APPROVED,
    PAYMENT_TYPE_DEPOSIT,
)
from models import Actividades, Attendance, Class, Enrollment, Payment, User


class FakePreference:
    counter = 0

    def create(self, preference_data):
        FakePreference.counter += 1
        return {
            "status": 201,
            "response": {
                "id": f"pref-smoke-{FakePreference.counter}",
                "init_point": "https://example.test/checkout",
            },
        }


class FakeMercadoPagoClient:
    def preference(self):
        return FakePreference()


def set_session_user(client, user_id):
    with client.session_transaction() as session:
        session["user_id"] = user_id


def assert_equal(label, actual, expected):
    if actual != expected:
        raise AssertionError(f"{label}: expected {expected!r}, got {actual!r}")


def assert_close(label, actual, expected):
    if round(float(actual), 2) != round(float(expected), 2):
        raise AssertionError(f"{label}: expected {expected!r}, got {actual!r}")


def main():
    original_mp_client = app_module.get_mercadopago_client
    app_module.get_mercadopago_client = lambda: FakeMercadoPagoClient()

    created = []
    try:
        with app.app_context():
            suffix = datetime.now().strftime("%Y%m%d%H%M%S%f")
            activity = Actividades(name=f"Smoke Parcial {suffix}")
            db.session.add(activity)
            db.session.flush()
            created.append(("activity", activity.id))

            class_obj = Class(
                name=activity.name,
                fecha_hora=datetime.now() + timedelta(days=7),
                id_actividad=activity.id,
                cupoMaximo=10,
                descuento=0,
            )
            db.session.add(class_obj)
            db.session.flush()
            created.append(("class", class_obj.id))

            client_user = User(
                username="Smoke",
                apellido="Partial",
                email=f"smoke-client-{suffix}@example.test",
                dni=f"9{suffix[-7:]}",
                telefono="000",
                role="client",
            )
            client_user.set_password("pass")
            admin_user = User(
                username="SmokeAdmin",
                apellido="Partial",
                email=f"smoke-admin-{suffix}@example.test",
                dni=f"8{suffix[-7:]}",
                telefono="000",
                role="admin",
            )
            admin_user.set_password("pass")
            db.session.add_all([client_user, admin_user])
            db.session.flush()
            created.extend([("user", client_user.id), ("user", admin_user.id)])

            enrollment = Enrollment(
                user_id=client_user.id,
                class_id=class_obj.id,
                estado=Enrollment.STATUS_PENDING_PAYMENT,
            )
            db.session.add(enrollment)
            db.session.commit()
            created.append(("enrollment", enrollment.id))

            enrollment_id = enrollment.id
            class_id = class_obj.id
            client_user_id = client_user.id
            admin_user_id = admin_user.id

        http = app.test_client()
        set_session_user(http, client_user_id)

        create_res = http.post(
            "/api/payments/create",
            json={
                "enrollment_id": enrollment_id,
                "payment_method": Payment.METHOD_MERCADO_PAGO,
                "payment_type": PAYMENT_TYPE_DEPOSIT,
            },
        )
        if create_res.status_code != 200:
            print("deposit create body", create_res.get_json())
        assert_equal("deposit create status", create_res.status_code, 200)
        create_body = create_res.get_json()
        payment_id = create_body["payment_id"]
        deposit_amount = create_body["final_amount"]

        callback_res = http.get(
            f"/api/payments/return/success?external_reference={payment_id}"
            f"&status={MERCADO_PAGO_STATUS_APPROVED}&payment_id=mp-smoke-deposit",
            follow_redirects=False,
        )
        assert_equal("deposit callback redirect", callback_res.status_code, 302)

        with app.app_context():
            enrollment = db.session.get(Enrollment, enrollment_id)
            deposit_payment = db.session.get(Payment, payment_id)
            assert_equal("deposit approved", deposit_payment.status, Payment.STATUS_APPROVED)
            assert_equal("enrollment still pending operationally", enrollment.estado, ENROLLMENT_STATUS_PENDING_PAYMENT)
            assert_equal("enrollment partially paid", enrollment.payment_status, ENROLLMENT_PAYMENT_STATUS_PARTIALLY_PAID)
            assert_close("paid amount after deposit", enrollment.paid_amount, deposit_amount)
            assert_close("remaining after deposit", enrollment.remaining_amount, enrollment.total_amount - deposit_amount)
            remaining_after_deposit = enrollment.remaining_amount

        attendance_res = http.post(
            "/api/attendance/register",
            json={"user_id": client_user_id, "class_id": class_id},
        )
        assert_equal("QR blocks partial payment", attendance_res.status_code, 403)

        history_res = http.get("/api/payments/history")
        assert_equal("history status after deposit", history_res.status_code, 200)
        history = history_res.get_json()["payments"]
        deposit_history = [item for item in history if item["id"] == payment_id][0]
        assert_equal("history deposit type", deposit_history["payment_type"], PAYMENT_TYPE_DEPOSIT)
        assert_close("history deposit amount", deposit_history["final_amount"], deposit_amount)

        pending_balance_res = http.post(
            "/api/payments/create",
            json={
                "enrollment_id": enrollment_id,
                "payment_method": Payment.METHOD_MERCADO_PAGO,
                "payment_type": "balance",
            },
        )
        assert_equal("pending MP balance create", pending_balance_res.status_code, 200)
        pending_balance_payment_id = pending_balance_res.get_json()["payment_id"]

        set_session_user(http, admin_user_id)
        overpay_res = http.post(
            f"/api/enrollments/{enrollment_id}/manual-payment",
            json={
                "amount": round(remaining_after_deposit + 100, 2),
                "payment_method": Payment.METHOD_CASH,
                "payment_type": Payment.TYPE_FULL,
            },
        )
        assert_equal("manual overpay rejected", overpay_res.status_code, 400)

        manual_res = http.post(
            f"/api/enrollments/{enrollment_id}/manual-payment",
            json={
                "amount": remaining_after_deposit,
                "payment_method": Payment.METHOD_CASH,
                "payment_type": "balance",
                "notes": "Smoke saldo presencial",
            },
        )
        assert_equal("manual balance status", manual_res.status_code, 201)

        with app.app_context():
            enrollment = db.session.get(Enrollment, enrollment_id)
            assert_equal("enrollment paid operationally", enrollment.estado, ENROLLMENT_STATUS_PAID)
            assert_equal("enrollment payment status paid", enrollment.payment_status, ENROLLMENT_PAYMENT_STATUS_PAID)
            assert_close("remaining after balance", enrollment.remaining_amount, 0)

        late_callback_res = http.get(
            f"/api/payments/return/success?external_reference={pending_balance_payment_id}"
            f"&status={MERCADO_PAGO_STATUS_APPROVED}&payment_id=mp-smoke-late-balance",
            follow_redirects=False,
        )
        assert_equal("late MP callback redirects", late_callback_res.status_code, 302)
        with app.app_context():
            enrollment = db.session.get(Enrollment, enrollment_id)
            late_payment = db.session.get(Payment, pending_balance_payment_id)
            assert_equal("late MP overpay rejected", late_payment.status, Payment.STATUS_REJECTED)
            assert_equal("enrollment stays paid after late callback", enrollment.estado, ENROLLMENT_STATUS_PAID)
            assert_equal("payment status stays paid after late callback", enrollment.payment_status, ENROLLMENT_PAYMENT_STATUS_PAID)
            assert_close("remaining stays zero after late callback", enrollment.remaining_amount, 0)

        set_session_user(http, client_user_id)
        attendance_paid_res = http.post(
            "/api/attendance/register",
            json={"user_id": client_user_id, "class_id": class_id},
        )
        assert_equal("QR allows full payment", attendance_paid_res.status_code, 201)

        history_res = http.get("/api/payments/history")
        assert_equal("history status after balance", history_res.status_code, 200)
        final_history = [
            item for item in history_res.get_json()["payments"]
            if item["enrollment_id"] == enrollment_id
        ]
        assert_equal("history has three payments", len(final_history), 3)
        assert_equal("history approved payments", len([item for item in final_history if item["status"] == Payment.STATUS_APPROVED]), 2)
        assert_equal("history rejected payments", len([item for item in final_history if item["status"] == Payment.STATUS_REJECTED]), 1)

        print("partial payments smoke ok")
        print(f"deposit={deposit_amount} remaining={remaining_after_deposit}")
    finally:
        app_module.get_mercadopago_client = original_mp_client
        with app.app_context():
            db.session.rollback()
            for _, enrollment_id in [item for item in reversed(created) if item[0] == "enrollment"]:
                Payment.query.filter_by(enrollment_id=enrollment_id).delete()
                enrollment = db.session.get(Enrollment, enrollment_id)
                if enrollment:
                    Attendance.query.filter_by(user_id=enrollment.user_id, class_id=enrollment.class_id).delete()
            for _, enrollment_id in [item for item in reversed(created) if item[0] == "enrollment"]:
                enrollment = db.session.get(Enrollment, enrollment_id)
                if enrollment:
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
