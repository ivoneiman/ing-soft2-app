"""
Script para poblar la base de datos con datos de prueba.
Crea tablas, usuarios, clases y enrollments de forma idempotente.
Correr con: python seed.py
"""
from calendar import monthrange
from datetime import datetime, time, timedelta

from app import (
    _class_has_finished,
    _current_discount_datetime,
    _payment_discount_percentage,
    _payment_quote,
    _payment_type_for_enrollment,
    app,
)
from models import db, User, Class, Enrollment, Attendance, Actividades, Payment, Profesor, WaitlistEntry
from constants import WAITLIST_TYPE_MONTHLY, ROOMS

ROOM_OPTIONS = list(ROOMS)
ROOM_BY_SCHEDULE = {}


def assign_class_room(class_obj):
    """Asigna un salón estable para clases con misma actividad, día y horario."""
    key = (
        class_obj.id_actividad,
        class_obj.fecha_hora.weekday(),
        class_obj.fecha_hora.hour,
        class_obj.fecha_hora.minute,
    )
    if key not in ROOM_BY_SCHEDULE:
        ROOM_BY_SCHEDULE[key] = ROOM_OPTIONS[len(ROOM_BY_SCHEDULE) % len(ROOM_OPTIONS)]

    room = ROOM_BY_SCHEDULE[key]
    if class_obj.room != room:
        class_obj.room = room
    return room


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


def profesor_exists(nombre, apellido):
    """Verifica si un profesor ya existe."""
    return Profesor.query.filter_by(nombre=nombre, apellido=apellido).first() is not None


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

def create_test_profesor(nombre, apellido):
    """Crea un profesor de prueba si no existe."""
    if profesor_exists(nombre, apellido):
        print(f"   [SKIP] Profesor {nombre} {apellido} ya existe, omitiendo...")
        return Profesor.query.filter_by(nombre=nombre, apellido=apellido).first()
    
    profesor = Profesor(nombre=nombre, apellido=apellido)
    db.session.add(profesor)
    db.session.flush()
    print(f"   [OK] Profesor creado: {nombre} {apellido}")
    return profesor


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


def create_test_class(name, fecha_hora, actividad, profesor_id, descuento=0, legacy_names=None, search_direction="forward", cupo_maximo=20):
    """Crea o actualiza una clase semilla sin duplicarla."""
    fecha_hora = as_naive_datetime(fecha_hora)
    find_available_datetime = previous_available_datetime if search_direction == "backward" else next_available_datetime
    existing_by_name = find_class_by_datetime_and_activity(fecha_hora, actividad.id)
    found_legacy_name = False
    if not existing_by_name:
        # OJO: hay que buscar también por el nombre ACTUAL, no solo por legacy_names.
        # Si solo se busca por legacy_names, una clase con fecha relativa (today + N días)
        # deja de encontrarse a sí misma en la siguiente corrida (la fecha ya cambió y el
        # nombre actual nunca se busca), y el seed termina creando una fila nueva cada vez
        # que se ejecuta en un día distinto.
        for candidate_name in [name, *(legacy_names or [])]:
            existing_by_name = find_class_by_name_and_activity(candidate_name, actividad.id)
            if existing_by_name:
                found_legacy_name = candidate_name != name
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
        if existing_by_name.profesor_id != profesor_id:
            existing_by_name.profesor_id = profesor_id
            changed = True

        assigned_room = assign_class_room(existing_by_name)
        if existing_by_name.room != assigned_room:
            existing_by_name.room = assigned_room
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
        profesor_id=profesor_id
    )
    db.session.add(class_obj)
    db.session.flush()  # Para obtener el ID generado
    assign_class_room(class_obj)
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
        f"{fecha} | {payable_text} | salón: {class_obj.room or 'sin asignar'} | "
        f"descuento esperado hoy: {expected_discount}% | descuento clase: {class_obj.descuento}%"
    )


def create_enrollment(user, class_obj):
    """Crea un enrollment si no existe."""
    if enrollment_exists(user.id, class_obj.id):
        print(f"   [SKIP] Enrollment {user.email} -> {class_obj.name} ya existe, omitiendo...")
        return
    
    enrollment = Enrollment(user_id=user.id, class_id=class_obj.id)
    db.session.add(enrollment)
    print(f"   [OK] Enrollment creado: {user.email} -> {class_obj.name}")


def ensure_enrollment(user, class_obj, estado=Enrollment.STATUS_PAID, tipo="Suelta"):
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

"clases para probar reporte de asistencia"
def ensure_attendance(user, class_obj):
    """Crea un registro de asistencia si no existe."""
    if Attendance.query.filter_by(user_id=user.id, class_id=class_obj.id).first():
        print(f"   [SKIP] Asistencia para {user.email} en {class_obj.name} ya existe, omitiendo...")
        return

    attendance = Attendance(user_id=user.id, class_id=class_obj.id)
    db.session.add(attendance)
    print(f"   [OK] Asistencia creada: {user.email} -> {class_obj.name}")


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


def remove_class_and_dependents(class_obj):
    """Elimina una clase de prueba junto con todo lo que depende de ella."""
    enrollment_ids = [e.id for e in Enrollment.query.filter_by(class_id=class_obj.id).all()]
    for enrollment_id in enrollment_ids:
        Payment.query.filter_by(enrollment_id=enrollment_id).delete()
    Enrollment.query.filter_by(class_id=class_obj.id).delete()
    Attendance.query.filter_by(class_id=class_obj.id).delete()
    WaitlistEntry.query.filter_by(class_id=class_obj.id).delete()
    db.session.delete(class_obj)


def purge_classes_by_name(actividad, names):
    """Borra TODAS las filas que coincidan con alguno de los nombres dados (no solo la primera).

    Necesario porque corridas previas del seed (antes de corregir create_test_class) pudieron
    dejar varias filas duplicadas con el mismo nombre para una misma actividad.
    """
    if not actividad:
        return
    removed = 0
    for name in names:
        for class_obj in Class.query.filter_by(name=name, id_actividad=actividad.id).all():
            remove_class_and_dependents(class_obj)
            removed += 1
    if removed:
        print(f"   [OK] {removed} clase(s) de prueba duplicada(s)/antigua(s) eliminada(s) de {actividad.name}")


def purge_all_classes_for_activity(actividad):
    """Deja una actividad en blanco (0 clases), para crearlas/administrarlas en vivo."""
    if not actividad:
        return
    classes = Class.query.filter_by(id_actividad=actividad.id).all()
    for class_obj in classes:
        remove_class_and_dependents(class_obj)
    if classes:
        print(f"   [OK] {len(classes)} clase(s) eliminada(s) de {actividad.name} (queda en blanco)")


def create_client_payment_examples(client, actividad_yoga, actividad_funcional, actividad_pilates, profesor, today):
    """Crea casos de ejemplo para historial de pagos de client@test.com."""
    print("Creando casos de pagos para client@test.com...")

    expired_class = create_test_class(
        "Yoga",
        at_app_time(today - timedelta(days=1), 12),
        actividad_yoga,
        profesor.id,
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


    paid_class = create_test_class(
        "Pilates",
        at_app_time(today + timedelta(days=2), 16),
        actividad_pilates,
        profesor.id,
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
        profesor.id,
        legacy_names=["Yoga Restaurativo", "Seed Pago Rechazado - Yoga"],
    )
    rejected_enrollment = ensure_enrollment(
        client,
        rejected_class,
        estado=Enrollment.STATUS_ACTIVE,
    )
    ensure_payment(
        rejected_enrollment,
        Payment.STATUS_REJECTED,
        created_at=today - timedelta(hours=1),
    )


def create_client_credit_examples(client, actividad_pilates, profesor, today):
    """Crea un flujo claro para probar créditos (individual) por cancelación con client@test.com."""
    print("Creando casos de créditos (individual) para client@test.com...")

    cancellable_class = create_test_class(
        "Pilates - Credito Individual (Origen)",
        at_app_time(today + timedelta(days=7), 15),
        actividad_pilates,
        profesor.id,
        legacy_names=["Pilates", "Credito Test - Pilates Cancelable"],
    )
    ensure_class_active(cancellable_class)
    paid_enrollment = ensure_enrollment(
        client,
        cancellable_class,
        estado=Enrollment.STATUS_PAID,
        tipo="Suelta",
    )
    ensure_payment(
        paid_enrollment,
        Payment.STATUS_APPROVED,
        created_at=today - timedelta(hours=3),
    )

    target_class = create_test_class(
        "Pilates - Credito Individual (Destino)",
        at_app_time(today + timedelta(days=8), 15),
        actividad_pilates,
        profesor.id,
        legacy_names=["Credito Test - Pilates Destino"],
    )
    ensure_class_active(target_class)
    print(
        "   [INFO] Para probar el credito individual: cancelar (dar de baja) la clase "
        "'Pilates - Credito Individual (Origen)' desde Mis Clases -> se genera un "
        "credito tipo 'individual'. Luego inscribir a client@test.com en 'Pilates - "
        "Credito Individual (Destino)' -> el credito se consume automaticamente."
    )


def create_client_monthly_subscription(client, actividad_pilates, profesor, today):
    """Crea una suscripcion mensual paga de Pilates para client@test.com, con varias
    clases en el mismo mes/horario, para poder probar la baja dia por dia (cada baja
    otorga un credito individual para anotarse a otra clase de la misma actividad)."""
    print("Creando suscripcion mensual de Pilates para client@test.com...")

    # Primer miercoles a partir de pasado mañana, a las 09:00hs.
    first_class_date = today + timedelta(days=2)
    while first_class_date.weekday() != 2:  # 0=lunes ... 2=miercoles
        first_class_date += timedelta(days=1)

    last_day = monthrange(first_class_date.year, first_class_date.month)[1]
    month_end = datetime(first_class_date.year, first_class_date.month, last_day, 23, 59, 59)

    monthly_classes = []
    occurrence_date = first_class_date
    week_index = 1
    while at_app_time(occurrence_date, 9) <= month_end:
        class_obj = create_test_class(
            f"Pilates Mensual - Semana {week_index}",
            at_app_time(occurrence_date, 9),
            actividad_pilates,
            profesor.id,
        )
        monthly_classes.append(class_obj)
        occurrence_date += timedelta(days=7)
        week_index += 1

    parent_class = monthly_classes[0]
    parent_enrollment = ensure_enrollment(
        client,
        parent_class,
        estado=Enrollment.STATUS_PAID,
        tipo="Mensual",
    )
    ensure_payment(
        parent_enrollment,
        Payment.STATUS_APPROVED,
        created_at=today - timedelta(hours=1),
    )

    print(
        f"   [INFO] Suscripcion mensual creada: {len(monthly_classes)} clase(s) los "
        f"miercoles a las 09:00 en {actividad_pilates.name}. Para probar creditos desde "
        "Mis Clases: dar de baja cualquiera de esos dias (uno o todos, de a uno por vez) "
        "-> cada baja otorga un credito individual para anotarse otro dia a la misma actividad."
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

        # Administradores del equipo
        create_test_user(
            username="Franco", apellido="Martin", email="francomartin08@hotmail.com",
            password="Admin_123", dni="44444444", telefono="221 4444444", role="admin"
        )
        create_test_user(
            username="Tobias", apellido="Gonzalez", email="tobiasgonzalez07@gmail.com",
            password="Admin_123", dni="55555555", telefono="221 5555555", role="admin"
        )
        create_test_user(
            username="Ivo", apellido="Neiman", email="ivoneiman@gmail.com",
            password="Admin_123", dni="66666666", telefono="221 6666666", role="admin"
        )
        create_test_user(
            username="Siempre", apellido="Gym", email="siempregym1@gmail.com",
            password="siempregym123", dni="12345678", telefono="2211234567", role="admin"
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

        # ─── Crear profesor de prueba ───────────────────────────────────────
        print("Creando profesor de prueba...")
        profesor_test = create_test_profesor("Gustavo", "Martinez")
        db.session.commit()
        print()

        # ─── Crear actividades de prueba ───────────────────────────────────

        print("Creando actividades de prueba...")
        actividad1 = create_test_actividad("Yoga")
        actividad2 = create_test_actividad("Funcional")
        actividad3 = create_test_actividad("Pilates")

        db.session.commit()
        print()

        # ─── Limpiar clases de prueba viejas que se mudaron a Pilates ───────
        # Yoga y Funcional quedan en blanco (0 clases) para crearlas/administrarlas
        # en vivo durante la demo con el cliente. Todos los casos límite de cupo,
        # mensual y reportes se concentran en Pilates.

        print("Reacomodando clases de prueba (consolidando casos límite en Pilates)...")
        # Yoga y Funcional quedan completamente en blanco: se borra TODO lo que tengan
        # (incluye duplicados acumulados por corridas previas con fechas relativas).
        purge_all_classes_for_activity(actividad1)
        purge_all_classes_for_activity(actividad2)
        # Pilates concentra los casos límite: se purgan por nombre (todas las filas,
        # no solo la primera) para eliminar duplicados de corridas previas antes de
        # recrearlas limpias más abajo.
        purge_classes_by_name(actividad3, [
            "Pilates", "Pilates Noche",
            "Pilates Limitado", "Pilates Sin Cupo",
            "Pilates - Clase Individual (Cupo Disponible)",
            "Pilates - Clase Limitada (1 Cupo)",
            "Pilates - Clase Sin Cupo (Llena)",
            "Pilates - Prueba Cupos (19/20)",
            "Pilates - 2 Junio (Martes)", "Pilates - 9 Junio (Martes)",
            "Pilates - 16 Junio (Martes)", "Pilates - 23 Junio (Martes)",
            "Pilates - 30 Junio (Martes)",
            "Pilates - 2 Julio (Jueves)", "Pilates - 9 Julio (Jueves)",
            "Pilates - 16 Julio (Jueves) - 1 Espacio ", "Pilates - 23 Julio (Jueves)",
            "Pilates - 30 Julio (Jueves)",
            "Pilates - 29 Junio 2026 (Asistencia)", "Pilates - 29 Junio 2026 (Sin Inscriptos)",
            "Pilates - 29 Junio 2026",
            "Pilates - Oferta Lista de Espera (Demo)",
        ])
        db.session.commit()
        print()

        # ─── Crear clases de prueba (todas concentradas en Pilates) ────────

        print("Creando clases de prueba dinamicas...")
        today = app_now()
        print(
            f"   Fecha base APP_TIMEZONE: {today.strftime('%Y-%m-%d %H:%M:%S %Z')}"
        )
        print(
            f"   Descuento de pagos esperado según fecha actual: "
            f"{_payment_discount_percentage(today)}%"
        )

        print("   Creando clase individual con cupo disponible...")
        class_con_cupo = create_test_class(
            "Pilates - Clase Individual (Cupo Disponible)",
            at_app_time(today + timedelta(days=3), 20),
            actividad3,
            profesor_test.id,
            cupo_maximo=20,
            legacy_names=["Pilates", "Pilates Noche"],
        )

        print("   Creando clase con cupo limitado a 1 (disponible)...")
        class_limited_cupo = create_test_class(
            "Pilates - Clase Limitada (1 Cupo)",
            at_app_time(today + timedelta(days=7), 11),
            actividad3,
            profesor_test.id,
            cupo_maximo=1,
            legacy_names=["Pilates Limitado"]
        )

        print("   Creando clase individual sin cupo (llena)...")
        class_sin_cupo = create_test_class(
            "Pilates - Clase Sin Cupo (Llena)",
            at_app_time(today + timedelta(days=9), 18),
            actividad3,
            profesor_test.id,
            cupo_maximo=1,
            legacy_names=["Pilates Sin Cupo"],
        )

        print("   Creando clase con oferta de lista de espera lista para demo (client@test.com)...")
        class_oferta_demo = create_test_class(
            "Pilates - Oferta Lista de Espera (Demo)",
            at_app_time(today + timedelta(days=5), 12),
            actividad3,
            profesor_test.id,
            cupo_maximo=1,
        )

        print("   Creando serie mensual con una fecha ya llena (prueba de lista de espera mensual)...")
        # Primer sabado a partir de mañana, dos semanas seguidas al mismo horario.
        serie_mensual_semana1_fecha = today + timedelta(days=1)
        while serie_mensual_semana1_fecha.weekday() != 5:  # 5 = sabado
            serie_mensual_semana1_fecha += timedelta(days=1)

        class_serie_mensual_semana1 = create_test_class(
            "Pilates - Serie Mensual Semana 1 (Cupo Disponible)",
            at_app_time(serie_mensual_semana1_fecha, 16),
            actividad3,
            profesor_test.id,
            cupo_maximo=5,
        )
        class_serie_mensual_semana2 = create_test_class(
            "Pilates - Serie Mensual Semana 2 (Llena)",
            at_app_time(serie_mensual_semana1_fecha + timedelta(days=7), 16),
            actividad3,
            profesor_test.id,
            cupo_maximo=1,
        )

        print("   Creando Clase de prueba para cupos (19/20)...")
        class_19_cupos = create_test_class(
            "Pilates - Prueba Cupos (19/20)",
            at_app_time(today + timedelta(days=8), 19),
            actividad3,
            profesor_test.id,
            cupo_maximo=20,
            legacy_names=["Yoga - Prueba Cupos (19/20)", "Yoga Prueba 19 Cupos"]
        )

        print("   Creando clases de Pilates para Junio (1 x semana, 20 cupos, prueba mensual)...")
        year = today.year
        create_test_class(
            "Pilates - 2 Junio (Martes)",
            datetime(year, 6, 2, 10, 0),
            actividad3,
            profesor_test.id,
            cupo_maximo=20,
            legacy_names=["Yoga - 2 Junio (Martes)", "Yoga Junio 2"]
        )
        create_test_class(
            "Pilates - 9 Junio (Martes)",
            datetime(year, 6, 9, 10, 0),
            actividad3,
            profesor_test.id,
            cupo_maximo=20,
            legacy_names=["Yoga - 9 Junio (Martes)", "Yoga Junio 9"]
        )
        create_test_class(
            "Pilates - 16 Junio (Martes)",
            datetime(year, 6, 16, 10, 0),
            actividad3,
            profesor_test.id,
            cupo_maximo=20,
            legacy_names=["Yoga - 16 Junio (Martes)", "Yoga Junio 16"]
        )
        create_test_class(
            "Pilates - 23 Junio (Martes)",
            datetime(year, 6, 23, 10, 0),
            actividad3,
            profesor_test.id,
            cupo_maximo=20,
            legacy_names=["Yoga - 23 Junio (Martes)", "Yoga Junio 23"]
        )
        create_test_class(
            "Pilates - 30 Junio (Martes)",
            datetime(year, 6, 30, 10, 0),
            actividad3,
            profesor_test.id,
            cupo_maximo=20,
            legacy_names=["Yoga - 30 Junio (Martes)", "Yoga Junio 30"]
        )

        print("   Creando clases de Pilates para Julio (pruebas de lista de espera mensual)...")
        year = today.year
        class_jul2 = create_test_class(
            "Pilates - 2 Julio (Jueves)",
            datetime(year, 7, 2, 7, 0),
            actividad3,
            profesor_test.id,
            cupo_maximo=20,
            legacy_names=["Yoga - 2 Julio (Jueves)", "Yoga Julio 2"]
        )
        class_jul9 = create_test_class(
            "Pilates - 9 Julio (Jueves)",
            datetime(year, 7, 9, 7, 0),
            actividad3,
            profesor_test.id,
            cupo_maximo=20,
            legacy_names=["Yoga - 9 Julio (Jueves)", "Yoga Julio 9"]
        )
        class_jul16 = create_test_class(
            "Pilates - 16 Julio (Jueves) - 1 Espacio ",
            datetime(year, 7, 16, 7, 0),
            actividad3,
            profesor_test.id,
            cupo_maximo=2,
            legacy_names=["Yoga - 16 Julio (Jueves) - 1 Espacio ", "Yoga Julio 16"]
        )
        class_jul23 = create_test_class(
            "Pilates - 23 Julio (Jueves)",
            datetime(year, 7, 23, 7, 0),
            actividad3,
            profesor_test.id,
            cupo_maximo=20,
            legacy_names=["Yoga - 23 Julio (Jueves)", "Yoga Julio 23"]
        )
        class_jul30 = create_test_class(
            "Pilates - 30 Julio (Jueves)",
            datetime(year, 7, 30, 7, 0),
            actividad3,
            profesor_test.id,
            cupo_maximo=20,
            legacy_names=["Yoga - 30 Julio (Jueves)", "Yoga Julio 30"]
        )

        print("   Creando clases específicas para el 29 de Junio de 2026 (reporte de asistencia)...")
        # Clase de Pilates con 3 inscriptos, 1 asiste y 2 no (prueba de reporte de asistencia)
        pilates_asistencia_29 = create_test_class(
            "Pilates - 29 Junio 2026 (Asistencia)",
            datetime(2026, 6, 29, 10, 0),
            actividad3,
            profesor_test.id,
            cupo_maximo=20,
            legacy_names=["Yoga - 29 Junio 2026", "Yoga 29/06/2026"]
        )

        # Clase de Pilates sin inscriptos pagos (prueba del mensaje "no hay inscriptos pagos")
        pilates_sin_inscriptos_29 = create_test_class(
            "Pilates - 29 Junio 2026 (Sin Inscriptos)",
            datetime(2026, 6, 29, 18, 0),
            actividad3,
            profesor_test.id,
            cupo_maximo=20,
            legacy_names=["Pilates - 29 Junio 2026", "Pilates 29/06/2026"]
        )

        # Inscribir 3 usuarios a la clase de Pilates, pero solo 1 con asistencia
        print("   Inscribiendo 3 usuarios a la clase de Pilates del 29/06 (asistencia)...")
        # 1. Usuario que SÍ asiste
        pilates_enrollment = ensure_enrollment(client, pilates_asistencia_29, estado=Enrollment.STATUS_PAID)
        ensure_payment(pilates_enrollment, Payment.STATUS_APPROVED, created_at=datetime(2026, 6, 28))
        ensure_attendance(client, pilates_asistencia_29)

        # 2. Usuarios que NO asisten
        no_asiste_1 = create_test_user(
            "NoAsiste1", "Pilates", "noasiste1@test.com", "client123", "55555501", "221 5555501"
        )
        no_asiste_2 = create_test_user(
            "NoAsiste2", "Pilates", "noasiste2@test.com", "client123", "55555502", "221 5555502"
        )

        enrollment_no_asiste_1 = ensure_enrollment(no_asiste_1, pilates_asistencia_29, estado=Enrollment.STATUS_PAID)
        ensure_payment(enrollment_no_asiste_1, Payment.STATUS_APPROVED, created_at=datetime(2026, 6, 28))

        enrollment_no_asiste_2 = ensure_enrollment(no_asiste_2, pilates_asistencia_29, estado=Enrollment.STATUS_PAID)
        ensure_payment(enrollment_no_asiste_2, Payment.STATUS_APPROVED, created_at=datetime(2026, 6, 28))

        db.session.commit()
        print()

        # ─── Crear enrollments (inscripciones) de prueba ────────────────────

        print("Creando enrollments de prueba...")

        print("   Ocupando la clase 'Pilates - Clase Sin Cupo (Llena)' para dejarla en 0 disponibles...")
        dummy_sin_cupo = create_test_user(
            username="AlumnoSinCupo", apellido="Dummy", email="dummy_sin_cupo@test.com",
            password="password123", dni="77777777", telefono="11111111", role="client"
        )
        enr_sin_cupo = ensure_enrollment(dummy_sin_cupo, class_sin_cupo, estado=Enrollment.STATUS_PAID, tipo="Suelta")
        ensure_payment(enr_sin_cupo, Payment.STATUS_APPROVED, created_at=today - timedelta(days=1))

        print("   Ocupando 'Pilates - Serie Mensual Semana 2 (Llena)' para dejarla en 0 disponibles...")
        dummy_serie_semana2 = create_test_user(
            username="AlumnoSerieSemana2", apellido="Dummy", email="dummy_serie_semana2@test.com",
            password="password123", dni="77777702", telefono="11111111", role="client"
        )
        enr_serie_semana2 = ensure_enrollment(
            dummy_serie_semana2, class_serie_mensual_semana2, estado=Enrollment.STATUS_PAID, tipo="Suelta"
        )
        ensure_payment(enr_serie_semana2, Payment.STATUS_APPROVED, created_at=today - timedelta(days=1))
        print(
            "   [INFO] Para probar la lista de espera MENSUAL cuando una fecha de la serie ya "
            "esta llena: inscribite mensual (o pedi lista de espera) en 'Pilates - Serie Mensual "
            "Semana 1 (Cupo Disponible)' -> como 'Pilates - Serie Mensual Semana 2 (Llena)' no "
            "tiene cupo, no se cobra nada: se te anota en la lista de espera de esa fecha puntual."
        )

        print("   Inscribiendo 19 usuarios ficticios a 'Pilates - Prueba Cupos (19/20)'...")
        for i in range(1, 20):
            dummy = create_test_user(
                username=f"Alumno{i}", apellido="Dummy", email=f"dummy{i}@test.com",
                password="password123", dni=f"888888{i:02d}", telefono="11111111", role="client"
            )
            enr = ensure_enrollment(dummy, class_19_cupos, estado=Enrollment.STATUS_PAID, tipo="Suelta")
            # Distribuimos los pagos de los dummies en los últimos 90 días para verlos en el reporte
            payment_date = today - timedelta(days=(i * 4))
            ensure_payment(enr, Payment.STATUS_APPROVED, created_at=payment_date)

        print("   Ocupando 1 lugar en la clase de Pilates del 16 de Julio para dejar un solo espacio libre...")
        dummy_julio = create_test_user(
            username="AlumnoJulio", apellido="Dummy", email="dummy_julio@test.com",
            password="password123", dni="99999999", telefono="11111111", role="client"
        )
        ensure_enrollment(dummy_julio, class_jul16, estado=Enrollment.STATUS_PAID, tipo="Suelta")

        print("   Dejando a client@test.com con una oferta de lista de espera pendiente de decidir (demo en vivo)...")
        oferta_enrollment = ensure_enrollment(
            client, class_oferta_demo, estado=Enrollment.STATUS_PENDING_PAYMENT, tipo="Suelta"
        )
        oferta_enrollment.waitlist_promoted_at = today
        oferta_enrollment.total_amount = 0
        oferta_enrollment.paid_amount = 0
        oferta_enrollment.remaining_amount = 0
        oferta_enrollment.payment_status = Enrollment.PAYMENT_STATUS_PENDING

        print("   Anotando un segundo usuario en la misma lista de espera (para mostrar el caso 'aún no seleccionado')...")
        espera_demo_user = create_test_user(
            username="EsperaDemo", apellido="Pilates", email="espera_demo@test.com",
            password="client123", dni="55555510", telefono="221 5555510", role="client"
        )
        existing_waitlist_demo = WaitlistEntry.query.filter_by(
            user_id=espera_demo_user.id, class_id=class_oferta_demo.id, type=WAITLIST_TYPE_MONTHLY
        ).first()
        if not existing_waitlist_demo:
            db.session.add(WaitlistEntry(
                user_id=espera_demo_user.id, class_id=class_oferta_demo.id, type=WAITLIST_TYPE_MONTHLY
            ))
            print(f"   [OK] {espera_demo_user.email} anotado en lista de espera de {class_oferta_demo.name}")
        else:
            print(f"   [SKIP] {espera_demo_user.email} ya estaba en la lista de espera de {class_oferta_demo.name}")

        db.session.commit()
        print()

        # ─── Casos de historial de pagos para client@test.com ───────────────

        # COMENTADO: No hay clases para crear ejemplos de pagos
        # create_client_payment_examples(client, actividad1, actividad2, actividad3, profesor_test, today)
        db.session.commit()
        print()

        # ─── Casos para probar créditos por cancelación (individual) ────────

        create_client_credit_examples(client, actividad3, profesor_test, today)
        db.session.commit()
        print()

        # ─── Suscripción mensual paga para probar créditos (mensual) ────────

        create_client_monthly_subscription(client, actividad3, profesor_test, today)
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
