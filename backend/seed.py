"""
Script para poblar la base de datos con datos de prueba.
Correr con: python seed.py
"""
from app import app
from models import db, User, Note

with app.app_context():
    db.create_all()

    # Limpiar datos existentes (cuidado en producción!)
    Note.query.delete()
    User.query.delete()
    db.session.commit()

    # Crear usuario de prueba
    user = User(username="testuser", email="test@example.com")
    user.set_password("password123")
    db.session.add(user)
    db.session.flush()  # Para obtener el ID antes del commit

    # Crear notas de prueba
    notas = [
        Note(title="Primera nota", content="Contenido de la primera nota de prueba.", user_id=user.id),
        Note(title="Segunda nota", content="Otra nota para probar el listado.", user_id=user.id),
        Note(title="Recordatorio", content="No olvidar entregar el TP!", user_id=user.id),
    ]
    db.session.add_all(notas)
    db.session.commit()

    print("✅ Base de datos poblada con datos de prueba")
    print(f"   Usuario: test@example.com / password123")
