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

    # Crear usuario de prueba
    user = User(username="testuser", email="test@example.com")
    user.set_password("password123")
    db.session.add(user)
    db.session.flush()  # Para obtener el ID antes del commit

    
    print(f"   Usuario: test@example.com / password123")
