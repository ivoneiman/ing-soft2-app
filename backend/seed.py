"""
Script para poblar la base de datos con datos de prueba.
Correr con: python seed.py
"""
from app import app
from models import db, User

with app.app_context():
    db.create_all()

    # Limpiar datos existentes (cuidado en producción!)
    User.query.delete()
    db.session.commit()

    # Crear usuarios de prueba con diferentes roles
    admin = User(username="admin", email="admin@test.com", role="admin")
    admin.set_password("admin123")
    db.session.add(admin)
    
    employee = User(username="employee", email="employee@test.com", role="employee")
    employee.set_password("employee123")
    db.session.add(employee)
    
    client = User(username="client", email="client@test.com", role="client")
    client.set_password("client123")
    db.session.add(client)
    
    db.session.commit()

    print("✓ Usuarios de prueba creados:")
    print("   ADMIN: admin@test.com / admin123")
    print("   EMPLOYEE: employee@test.com / employee123")
    print("   CLIENT: client@test.com / client123")
