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
    app,
)
from models import db, User, Class, Enrollment, Attendance, Actividades


def user_exists(email):
    """Verifica si un usuario ya exista por email."""
    return User.query.filter_by(email=email).first() is not None


def find_class_by_name_and_activity(name, actividad_id):
    """Busca una clase semilla por nombre y actividad."""
    return Class.query.filter_by(name=name, id_actividad=actividad_id).first()


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


def create_test_class(name, fecha_hora, actividad, descuento=0, legacy_names=None):
    """Crea o actualiza una clase semilla sin duplicarla."""
    fecha_hora = as_naive_datetime(fecha_hora)
    existing_by_name = find_class_by_name_and_activity(name, actividad.id)
    found_legacy_name = False
    if not existing_by_name:
        for legacy_name in legacy_names or []:
            existing_by_name = find_class_by_name_and_activity(legacy_name, actividad.id)
            if existing_by_name:
                found_legacy_name = True
                break

    if existing_by_name:
        fecha_hora = next_available_datetime(
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

        action = "actualizada" if changed else "ya existe"
        print_class_log(existing_by_name, action)
        return existing_by_name

    fecha_hora = next_available_datetime(actividad.id, fecha_hora)

    class_obj = Class(
        name=name,
        fecha_hora=fecha_hora,
        id_actividad=actividad.id,
        descuento=descuento,
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
            "Yoga Mañana",
            at_app_time(today + timedelta(days=1), 9),
            actividad1,
        )
        class2 = create_test_class(
            "Funcional Tarde",
            at_app_time(today + timedelta(days=2), 14),
            actividad2,
        )
        class3 = create_test_class(
            "Pilates Noche",
            at_app_time(today + timedelta(days=3), 20),
            actividad3,
        )
        create_test_class(
            "Yoga Caso No Payable",
            today - timedelta(hours=2),
            actividad1,
            descuento=0,
            legacy_names=["Yoga Pasada", "Yoga Pasada No Payable"],
        )
        create_test_class(
            "Yoga Caso Pago Futuro",
            at_app_time(today + timedelta(days=4), 10),
            actividad1,
            descuento=0,
            legacy_names=["Yoga Caso Descuento 0%"],
        )
        create_test_class(
            "Pilates Caso Clase Activa",
            at_app_time(today + timedelta(days=5), 17),
            actividad3,
            descuento=0,
            legacy_names=["Pilates Caso Descuento 40%"],
        )
        create_test_class(
            "Funcional Caso Clase Premium",
            at_app_time(today + timedelta(days=6), 19),
            actividad2,
            descuento=0,
            legacy_names=["Funcional Caso Descuento 70%"],
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
