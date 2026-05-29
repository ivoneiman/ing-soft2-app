"""
Script para poblar la base de datos con datos de prueba.
Crea tablas, usuarios, clases y enrollments de forma idempotente.
Correr con: python seed.py
"""
from datetime import datetime, time, timedelta

from app import (
    _class_has_finished,
    _current_discount_datetime,
    _payment_discount_percentage,
    _payment_quote,
    _payment_type_for_enrollment,
    app,
)
from models import db, User, Class, Enrollment, Attendance, Actividades, Payment


def user_exists(email):
    """Verifica si un usuario ya exista por email."""
    return User.query.filter_by(email=email).first() is not None


def find_class_by_name_and_activity(name, actividad_id):
    """Busca una clase semilla por nombre y actividad."""
    return Class.query.filter_by(name=name, id_actividad=actividad_id).first()


def find_class_by_datetime_and_activity(fecha_hora, actividad_id):
    """Busca una clase por horario y actividad."""
    return Class.query.filter_by(fecha_hora=fecha_hora, id_actividad=actividad_id).first()


def actividad_exists(name):
    """Verifica si una actividad ya existe por nombre."""
    return Actividades.query.filter_by(name=name).first() is not None


def create_test_actividad(name):
    """Crea una actividad si no existe."""
    if actividad_exists(name):
        print(f"   [SKIP] Actividad '{name}' ya existe, omitiendo...")
        return Actividades.query.filter_by(name=name).first()

    actividad = Actividades(name=name)
    db.session.add(actividad)
    db.session.flush()
    print(f"   [OK] Actividad creada: {name}")
    return actividad


def enrollment_exists(user_id, class_id):
    """Verifica si un enrollment ya existe."""
    return Enrollment.query.filter_by(user_id=user_id, class_id=class_id).first() is not None


def create_test_user(username, apellido, email, password, dni, telefono, role="client"):
    if user_exists(email):
        print(f"   [SKIP] Usuario {email} ya existe, omitiendo...")
        return User.query.filter_by(email=email).first()
    
    user = User(username=username, apellido=apellido, email=email, dni=dni, telefono=telefono, role=role)
    user.set_password(password)
    db.session.add(user)
    db.session.flush()
    print(f"   [OK] Usuario creado: {email} ({role})")
    return user


def app_now():
    """Devuelve la fecha actual en la zona horaria configurada para la app."""
    return _current_discount_datetime()


def as_naive_datetime(value):
    """SQLAlchemy guarda DateTime naive; la app lo interpreta en APP_TIMEZONE."""
    return value.replace(tzinfo=None) if value and value.tzinfo else value


def at_app_time(base_datetime, hour, minute=0):
    return as_naive_datetime(datetime.combine(base_datetime.date(), time(hour, minute)))


def next_available_datetime(actividad_id, fecha_hora, ignore_class_id=None):
    """Evita chocar con la restricción única actividad + horario."""
    candidate = fecha_hora
    while True:
        query = Class.query.filter_by(
            fecha_hora=candidate,
            id_actividad=actividad_id,
        )
        if ignore_class_id is not None:
            query = query.filter(Class.id != ignore_class_id)

        if query.first() is None:
            return candidate

        candidate = candidate + timedelta(days=1)


def previous_available_datetime(actividad_id, fecha_hora, ignore_class_id=None):
    """Evita chocar con la restriccion unica buscando fechas anteriores."""
    candidate = fecha_hora
    while True:
        query = Class.query.filter_by(
            fecha_hora=candidate,
            id_actividad=actividad_id,
        )
        if ignore_class_id is not None:
            query = query.filter(Class.id != ignore_class_id)

        if query.first() is None:
            return candidate

        candidate = candidate - timedelta(days=1)


def create_test_class(name, fecha_hora, actividad, descuento=0, legacy_names=None, search_direction="forward", cupo_maximo=20):
    """Crea o actualiza una clase semilla sin duplicarla."""
    fecha_hora = as_naive_datetime(fecha_hora)
    find_available_datetime = previous_available_datetime if search_direction == "backward" else next_available_datetime
    existing_by_name = find_class_by_datetime_and_activity(fecha_hora, actividad.id)
    found_legacy_name = False
    if not existing_by_name:
        for legacy_name in legacy_names or []:
            existing_by_name = find_class_by_name_and_activity(legacy_name, actividad.id)
            if existing_by_name:
                found_legacy_name = True
                break

    if existing_by_name:
        fecha_hora = find_available_datetime(
            actividad.id,
            fecha_hora,
            ignore_class_id=existing_by_name.id,
        )
        changed = found_legacy_name
        if existing_by_name.name != name:
            existing_by_name.name = name
            changed = True
        if existing_by_name.fecha_hora != fecha_hora:
            existing_by_name.fecha_hora = fecha_hora
            changed = True
        if existing_by_name.descuento != descuento:
            existing_by_name.descuento = descuento
            changed = True
        if existing_by_name.cupoMaximo != cupo_maximo:
            existing_by_name.cupoMaximo = cupo_maximo
            changed = True

        action = "actualizada" if changed else "ya existe"
        print_class_log(existing_by_name, action)
        return existing_by_name

    fecha_hora = find_available_datetime(actividad.id, fecha_hora)

    class_obj = Class(
        name=name,
        fecha_hora=fecha_hora,
        id_actividad=actividad.id,
        descuento=descuento,
        cupoMaximo=cupo_maximo,
    )
    db.session.add(class_obj)
    db.session.flush()  # Para obtener el ID generado
    print_class_log(class_obj, "creada")
    return class_obj


def print_class_log(class_obj, action):
    current_datetime = app_now()
    is_payable = not _class_has_finished(class_obj, current_datetime)
    expected_discount = _payment_discount_percentage(current_datetime)
    fecha = class_obj.fecha_hora.strftime("%Y-%m-%d %H:%M")
    payable_text = "payable" if is_payable else "no payable"
    actividad = class_obj.actividad.name if class_obj.actividad else class_obj.id_actividad
    print(
        f"   [OK] Clase {action}: {class_obj.name} | {actividad} | "
        f"{fecha} | {payable_text} | descuento esperado hoy: {expected_discount}% "
        f"| descuento clase: {class_obj.descuento}%"
    )


def create_enrollment(user, class_obj):
    """Crea un enrollment si no existe."""
    if enrollment_exists(user.id, class_obj.id):
        print(f"   [SKIP] Enrollment {user.email} -> {class_obj.name} ya existe, omitiendo...")
        return
    
    enrollment = Enrollment(user_id=user.id, class_id=class_obj.id)
    db.session.add(enrollment)
    print(f"   [OK] Enrollment creado: {user.email} -> {class_obj.name}")


def ensure_enrollment(user, class_obj, estado=Enrollment.STATUS_PENDING_PAYMENT, tipo="Suelta"):
    """Crea o actualiza una inscripcion de ejemplo para un usuario y clase."""
    enrollment = Enrollment.query.filter_by(user_id=user.id, class_id=class_obj.id).first()
    if enrollment:
        changed = False
        if enrollment.estado != estado:
            enrollment.estado = estado
            changed = True
        if enrollment.tipo != tipo:
            enrollment.tipo = tipo
            changed = True
        action = "actualizado" if changed else "ya existe"
        print(f"   [OK] Enrollment {action}: {user.email} -> {class_obj.name} ({estado})")
        return enrollment

    enrollment = Enrollment(
        user_id=user.id,
        class_id=class_obj.id,
        estado=estado,
        tipo=tipo,
    )
    db.session.add(enrollment)
    db.session.flush()
    print(f"   [OK] Enrollment creado: {user.email} -> {class_obj.name} ({estado})")
    return enrollment


def ensure_payment(enrollment, status, created_at=None):
    """Crea o actualiza el pago de ejemplo asociado a una inscripcion."""
    payment = Payment.query.filter_by(enrollment_id=enrollment.id).first()
    quote = _payment_quote(_payment_type_for_enrollment(enrollment), "full", app_now())
    created_at = as_naive_datetime(created_at or app_now())

    if payment:
        payment.user_id = enrollment.user_id
        payment.class_id = enrollment.class_id
        payment.product_type = _payment_type_for_enrollment(enrollment)
        payment.payment_type = Payment.TYPE_FULL
        payment.payment_method = Payment.METHOD_MERCADO_PAGO
        payment.amount = quote["amount"]
        payment.discount_percentage = quote["discount_percentage"]
        payment.final_amount = quote["final_amount"]
        payment.status = status
        payment.created_at = created_at
        print(
            f"   [OK] Pago actualizado: enrollment {enrollment.id} "
            f"-> {status}"
        )
        return payment

    payment = Payment(
        user_id=enrollment.user_id,
        enrollment_id=enrollment.id,
        class_id=enrollment.class_id,
        product_type=_payment_type_for_enrollment(enrollment),
        payment_type=Payment.TYPE_FULL,
        payment_method=Payment.METHOD_MERCADO_PAGO,
        amount=quote["amount"],
        discount_percentage=quote["discount_percentage"],
        final_amount=quote["final_amount"],
        status=status,
        created_at=created_at,
    )
    db.session.add(payment)
    print(f"   [OK] Pago creado: enrollment {enrollment.id} -> {status}")
    return payment


def ensure_class_active(class_obj):
    """Deja una clase semilla disponible para repetir pruebas luego de cancelarla."""
    if class_obj.estado != Class.STATUS_ACTIVE:
        class_obj.estado = Class.STATUS_ACTIVE
        print(f"   [OK] Clase reactivada para pruebas: {class_obj.name}")


def create_client_payment_examples(client, actividad_yoga, actividad_funcional, actividad_pilates, today):
    """Crea casos de ejemplo para historial de pagos de client@test.com."""
    print("Creando casos de pagos para client@test.com...")

    expired_class = create_test_class(
        "Yoga",
        at_app_time(today - timedelta(days=1), 12),
        actividad_yoga,
        legacy_names=["Yoga Mediodia", "Seed Pago Vencido - Yoga"],
        search_direction="backward",
    )
    expired_enrollment = ensure_enrollment(
        client,
        expired_class,
        estado=Enrollment.STATUS_EXPIRED,
    )
    ensure_payment(
        expired_enrollment,
        Payment.STATUS_EXPIRED,
        created_at=expired_class.fecha_hora - timedelta(minutes=1),
    )

    pending_class = create_test_class(
        "Funcional",
        at_app_time(today + timedelta(days=1), 18),
        actividad_funcional,
        legacy_names=["Funcional Intensivo", "Seed Pago Pendiente - Funcional"],
    )
    pending_enrollment = ensure_enrollment(
        client,
        pending_class,
        estado=Enrollment.STATUS_PENDING_PAYMENT,
    )
    ensure_payment(
        pending_enrollment,
        Payment.STATUS_PENDING,
        created_at=today - timedelta(minutes=30),
    )

    paid_class = create_test_class(
        "Pilates",
        at_app_time(today + timedelta(days=2), 16),
        actividad_pilates,
        legacy_names=["Pilates Suave", "Seed Pago Aprobado - Pilates"],
    )
    paid_enrollment = ensure_enrollment(
        client,
        paid_class,
        estado=Enrollment.STATUS_PAID,
    )
    ensure_payment(
        paid_enrollment,
        Payment.STATUS_APPROVED,
        created_at=today - timedelta(hours=2),
    )

    rejected_class = create_test_class(
        "Yoga",
        at_app_time(today + timedelta(days=3), 11),
        actividad_yoga,
        legacy_names=["Yoga Restaurativo", "Seed Pago Rechazado - Yoga"],
    )
    rejected_enrollment = ensure_enrollment(
        client,
        rejected_class,
        estado=Enrollment.STATUS_PENDING_PAYMENT,
    )
    ensure_payment(
        rejected_enrollment,
        Payment.STATUS_REJECTED,
        created_at=today - timedelta(hours=1),
    )


def create_client_credit_examples(client, actividad_pilates, today):
    """Crea un flujo claro para probar créditos por cancelación con client@test.com."""
    print("Creando casos de créditos para client@test.com...")

    cancellable_class = create_test_class(
        "Pilates",
        at_app_time(today + timedelta(days=7), 15),
        actividad_pilates,
        legacy_names=["Credito Test - Pilates Cancelable"],
    )
    ensure_class_active(cancellable_class)
    paid_enrollment = ensure_enrollment(
        client,
        cancellable_class,
        estado=Enrollment.STATUS_PAID,
    )
    ensure_payment(
        paid_enrollment,
        Payment.STATUS_APPROVED,
        created_at=today - timedelta(hours=3),
    )

    target_class = create_test_class(
        "Pilates",
        at_app_time(today + timedelta(days=8), 15),
        actividad_pilates,
        legacy_names=["Credito Test - Pilates Destino"],
    )
    ensure_class_active(target_class)
    print(
        "   [INFO] Para probar creditos: cancelar la clase de Pilates "
        "cancelable y luego inscribir client@test.com en la clase de Pilates destino."
    )


def main():
    """Función principal para poblar la base de datos."""
    with app.app_context():
        # Crear tablas si no existen
        print("\nInicializando base de datos...")
        db.create_all()
        print("   [OK] Tablas creadas/verificadas\n")

    # ─── Crear usuarios de prueba ──────────────────────────────────────

        print("Creando usuarios de prueba...")
        
        admin = create_test_user(
            username="Admin", apellido="Test", email="admin@test.com",
            password="admin123", dni="11111111", telefono="221 1111111", role="admin"
        )
        
        employee = create_test_user(
            username="Employee", apellido="Test", email="employee@test.com",
            password="employee123", dni="22222222", telefono="221 2222222", role="employee"
        )
        
        client = create_test_user(
            username="Client", apellido="Test", email="client@test.com",
            password="client123", dni="33333333", telefono="221 3333333", role="client"
        )

        db.session.commit()
        print()

        # ─── Crear actividades de prueba ───────────────────────────────────

        print("Creando actividades de prueba...")
        actividad1 = create_test_actividad("Yoga")
        actividad2 = create_test_actividad("Funcional")
        actividad3 = create_test_actividad("Pilates")

        db.session.commit()
        print()

        # ─── Crear clases de prueba ───────────────────────────────────────
        
        print("Creando clases de prueba dinamicas...")
        today = app_now()
        print(
            f"   Fecha base APP_TIMEZONE: {today.strftime('%Y-%m-%d %H:%M:%S %Z')}"
        )
        print(
            f"   Descuento de pagos esperado según fecha actual: "
            f"{_payment_discount_percentage(today)}%"
        )

        class1 = create_test_class(
            "Yoga",
            at_app_time(today + timedelta(days=1), 9),
            actividad1,
            legacy_names=["Yoga Mañana"],
        )
        class2 = create_test_class(
            "Funcional",
            at_app_time(today + timedelta(days=2), 14),
            actividad2,
            legacy_names=["Funcional Tarde"],
        )
        class3 = create_test_class(
            "Pilates",
            at_app_time(today + timedelta(days=3), 20),
            actividad3,
            legacy_names=["Pilates Noche"],
        )
        create_test_class(
            "Yoga",
            at_app_time(today - timedelta(days=1), 9),
            actividad1,
            descuento=0,
            legacy_names=["Yoga Caso No Payable", "Yoga Pasada", "Yoga Pasada No Payable"],
            search_direction="backward",
        )
        create_test_class(
            "Yoga",
            at_app_time(today + timedelta(days=4), 10),
            actividad1,
            descuento=0,
            legacy_names=["Yoga Caso Pago Futuro", "Yoga Caso Descuento 0%"],
        )
        create_test_class(
            "Pilates",
            at_app_time(today + timedelta(days=5), 17),
            actividad3,
            descuento=0,
            legacy_names=["Pilates Caso Clase Activa", "Pilates Caso Descuento 40%"],
        )
        create_test_class(
            "Funcional",
            at_app_time(today + timedelta(days=6), 19),
            actividad2,
            descuento=0,
            legacy_names=["Funcional Caso Clase Premium", "Funcional Caso Descuento 70%"],
        )

        print("   Creando clases de Yoga para Junio (pruebas de lista de espera mensual)...")
        year = today.year
        create_test_class(
            "Yoga - 4 Junio (1 Cupo)",
            datetime(year, 6, 4, 10, 0),
            actividad1,
            cupo_maximo=1,
            legacy_names=["Yoga Junio 4"]
        )
        create_test_class(
            "Yoga - 11 Junio",
            datetime(year, 6, 11, 10, 0),
            actividad1,
            cupo_maximo=20,
            legacy_names=["Yoga Junio 11"]
        )
        create_test_class(
            "Yoga - 18 Junio",
            datetime(year, 6, 18, 10, 0),
            actividad1,
            cupo_maximo=20,
            legacy_names=["Yoga Junio 18"]
        )
        create_test_class(
            "Yoga - 25 Junio",
            datetime(year, 6, 25, 10, 0),
            actividad1,
            cupo_maximo=20,
            legacy_names=["Yoga Junio 25"]
        )

        db.session.commit()
        print()

        # ─── Crear enrollments (inscripciones) de prueba ────────────────────

        print("Creando enrollments de prueba...")
        
        # Admin inscrito a todas las clases
        create_enrollment(admin, class1)
        create_enrollment(admin, class2)
        create_enrollment(admin, class3)
        
        # Employee inscrito a dos clases
        create_enrollment(employee, class1)
        create_enrollment(employee, class2)
        
        # Client inscrito a una clase
        create_enrollment(client, class1)
        db.session.commit()
        print()

        # ─── Casos de historial de pagos para client@test.com ───────────────

        create_client_payment_examples(client, actividad1, actividad2, actividad3, today)
        db.session.commit()
        print()

        # ─── Casos para probar créditos por cancelación ─────────────────────

        create_client_credit_examples(client, actividad3, today)
        db.session.commit()
        print()

        # ─── Resumen final ────────────────────────────────────────────────

        users_count = User.query.count()
        classes_count = Class.query.count()
        enrollments_count = Enrollment.query.count()

        print("=" * 60)
        print("SEED COMPLETADO EXITOSAMENTE")
        print("=" * 60)
        print(f"Estadisticas de la base de datos:")
        print(f"   - Usuarios: {users_count}")
        print(f"   - Clases: {classes_count}")
        print(f"   - Enrollments: {enrollments_count}")
        print()
        print("Credenciales de prueba:")
        print("   - Admin:    admin@test.com / admin123")
        print("   - Employee: employee@test.com / employee123")
        print("   - Client:   client@test.com / client123")
        print()
        print("Clases disponibles:")
        for cls in Class.query.all():
            enrolled = Enrollment.query.filter_by(class_id=cls.id).count()
            payable_text = "payable" if not _class_has_finished(cls, app_now()) else "no payable"
            print(
                f"   - {cls.name} | {cls.fecha_hora.strftime('%Y-%m-%d %H:%M')} "
                f"| {payable_text} | descuento clase: {cls.descuento}% "
                f"| {enrolled} inscritos"
            )
        print()
        print("Para completar el setup:")
        print("   1. Ejecutar: npm install (en frontend/)")
        print("   2. Ejecutar: npm run dev (en frontend/)")
        print("   3. Ejecutar: python app.py (en backend/)")
        print("=" * 60)


if __name__ == "__main__":
    main()
