"""
Script para poblar la base de datos con datos de prueba.
Crea tablas, usuarios, clases y enrollments de forma idempotente.
Correr con: python seed.py
"""
from datetime import datetime, timedelta

from app import app
from models import db, User, Class, Enrollment, Attendance


def user_exists(email):
    """Verifica si un usuario ya exista por email."""
    return User.query.filter_by(email=email).first() is not None


def class_exists(name):
    """Verifica si una clase ya existe por nombre."""
    return Class.query.filter_by(name=name).first() is not None


def enrollment_exists(user_id, class_id):
    """Verifica si un enrollment ya existe."""
    return Enrollment.query.filter_by(user_id=user_id, class_id=class_id).first() is not None


def create_test_user(username, apellido, email, password, dni, telefono, role="client"):
    if user_exists(email):
        print(f"   ⊘ Usuario {email} ya existe, omitiendo...")
        return User.query.filter_by(email=email).first()
    
    user = User(username=username, apellido=apellido, email=email, dni=dni, telefono=telefono, role=role)
    user.set_password(password)
    db.session.add(user)
    db.session.flush()
    print(f"   ✓ Usuario creado: {email} ({role})")
    return user


def create_test_class(name):
    """Crea una clase si no existe."""
    if class_exists(name):
        print(f"   ⊘ Clase '{name}' ya existe, omitiendo...")
        return Class.query.filter_by(name=name).first()
    
    class_obj = Class(name=name)
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

        # ─── Crear clases de prueba ───────────────────────────────────────

        print("📚 Creando clases de prueba...")
        
        class1 = create_test_class("Ingeniería de Software 2")
        class2 = create_test_class("Programación Avanzada")
        class3 = create_test_class("Bases de Datos")

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
