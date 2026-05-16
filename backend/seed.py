"""
Script para poblar la base de datos con datos de prueba.
Crea tablas, usuarios, clases y enrollments de forma idempotente.
Correr con: python seed.py
"""
from datetime import datetime

from app import app
from models import db, User, Class, Enrollment, Attendance, Actividades


def user_exists(email):
    """Verifica si un usuario ya existe por email."""
    return User.query.filter_by(email=email).first() is not None


def class_exists(name, fecha_hora, actividad_id):
    """Verifica si una clase ya existe por nombre, fecha y actividad."""
    return (
        Class.query.filter_by(
            name=name,
            fecha_hora=fecha_hora,
            id_actividad=actividad_id,
        ).first()
        is not None
    )


def actividad_exists(name):
    """Verifica si una actividad ya existe por nombre."""
    return Actividades.query.filter_by(name=name).first() is not None


def create_test_actividad(name):
    """Crea una actividad si no existe."""
    if actividad_exists(name):
        print(f"   ⊘ Actividad '{name}' ya existe, omitiendo...")
        return Actividades.query.filter_by(name=name).first()

    actividad = Actividades(name=name)
    db.session.add(actividad)
    db.session.flush()
    print(f"   ✓ Actividad creada: {name}")
    return actividad


def enrollment_exists(user_id, class_id):
    """Verifica si un enrollment ya existe."""
    return Enrollment.query.filter_by(user_id=user_id, class_id=class_id).first() is not None


def create_test_user(username, email, password, role="client"):
    """Crea un usuario si no existe."""
    if user_exists(email):
        print(f"   ⊘ Usuario {email} ya existe, omitiendo...")
        return User.query.filter_by(email=email).first()
    
    user = User(username=username, email=email, role=role)
    user.set_password(password)
    db.session.add(user)
    db.session.flush()  # Para obtener el ID generado
    print(f"   ✓ Usuario creado: {email} ({role})")
    return user


def create_test_class(name, fecha_hora, actividad):
    """Crea una clase si no existe."""
    if class_exists(name, fecha_hora, actividad.id):
        print(f"   ⊘ Clase '{name}' ya existe, omitiendo...")
        return (
            Class.query.filter_by(
                name=name,
                fecha_hora=fecha_hora,
                id_actividad=actividad.id,
            ).first()
        )

    class_obj = Class(name=name, fecha_hora=fecha_hora, id_actividad=actividad.id)
    db.session.add(class_obj)
    db.session.flush()  # Para obtener el ID generado
    print(f"   ✓ Clase creada: {name}")
    return class_obj


def create_enrollment(user, class_obj):
    """Crea un enrollment si no existe."""
    if enrollment_exists(user.id, class_obj.id):
        print(f"   ⊘ Enrollment {user.email} → {class_obj.name} ya existe, omitiendo...")
        return
    
    enrollment = Enrollment(user_id=user.id, class_id=class_obj.id)
    db.session.add(enrollment)
    print(f"   ✓ Enrollment creado: {user.email} → {class_obj.name}")


def main():
    """Función principal para poblar la base de datos."""
    with app.app_context():
        # Crear tablas si no existen
        print("\n🔧 Inicializando base de datos...")
        db.create_all()
        print("   ✓ Tablas creadas/verificadas\n")

        # ─── Crear usuarios de prueba ──────────────────────────────────────

        print("👤 Creando usuarios de prueba...")
        
        admin = create_test_user(
            username="admin",
            email="admin@test.com",
            password="admin123",
            role="admin"
        )
        
        employee = create_test_user(
            username="employee",
            email="employee@test.com",
            password="employee123",
            role="employee"
        )
        
        client = create_test_user(
            username="client",
            email="client@test.com",
            password="client123",
            role="client"
        )

        db.session.commit()
        print()

        # ─── Crear actividades de prueba ───────────────────────────────────

        print("🏋️ Creando actividades de prueba...")
        actividad1 = create_test_actividad("Yoga")
        actividad2 = create_test_actividad("Funcional")
        actividad3 = create_test_actividad("Pilates")

        db.session.commit()
        print()

        # ─── Crear clases de prueba ───────────────────────────────────────

        print("📚 Creando clases de prueba...")
        
        class1 = create_test_class(
            "Yoga Mañana",
            datetime(2026, 5, 17, 9, 0),
            actividad1,
        )
        class2 = create_test_class(
            "Funcional Tarde",
            datetime(2026, 5, 17, 14, 0),
            actividad2,
        )
        class3 = create_test_class(
            "Pilates Noche",
            datetime(2026, 5, 18, 16, 0),
            actividad3,
        )

        db.session.commit()
        print()

        # ─── Crear enrollments (inscripciones) de prueba ────────────────────

        print("📋 Creando enrollments de prueba...")
        
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
        print("✅ SEED COMPLETADO EXITOSAMENTE")
        print("=" * 60)
        print(f"📊 Estadísticas de la base de datos:")
        print(f"   • Usuarios: {users_count}")
        print(f"   • Clases: {classes_count}")
        print(f"   • Enrollments: {enrollments_count}")
        print()
        print("🔑 Credenciales de prueba:")
        print("   • Admin:    admin@test.com / admin123")
        print("   • Employee: employee@test.com / employee123")
        print("   • Client:   client@test.com / client123")
        print()
        print("🎓 Clases disponibles:")
        for cls in Class.query.all():
            enrolled = Enrollment.query.filter_by(class_id=cls.id).count()
            print(f"   • {cls.name} ({enrolled} inscritos)")
        print()
        print("💡 Para completar el setup:")
        print("   1. Ejecutar: npm install (en frontend/)")
        print("   2. Ejecutar: npm run dev (en frontend/)")
        print("   3. Ejecutar: python app.py (en backend/)")
        print("=" * 60)


if __name__ == "__main__":
    main()
