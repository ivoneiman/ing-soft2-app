#!/usr/bin/env python3
"""
Script de migración para agregar los campos necesarios para la funcionalidad de cancelación de clases.
Ejecutar con: python migrate_cancellations.py

Este script agrega:
- Campo 'estado' a la tabla 'classes' (default: 'Activa')
- Campos 'tipo', 'estado' y 'requiere_reembolso' a la tabla 'enrollments'
"""

import os
from dotenv import load_dotenv
from flask import Flask
from sqlalchemy import inspect, text

from models import db, Class, Enrollment

# Carga variables de entorno
load_dotenv()

app = Flask(__name__)
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "dev-secret-key")
app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("SQLALCHEMY_DATABASE_URI", "sqlite:///app.db")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db.init_app(app)

def migrate_database():
    """Agrega los campos faltantes a las tablas existentes."""
    with app.app_context():
        inspector = inspect(db.engine)
        
        # ───── Migrar tabla 'classes' ─────
        if "classes" in inspector.get_table_names():
            columns = [column["name"] for column in inspector.get_columns("classes")]
            
            if "estado" not in columns:
                print("➕ Agregando campo 'estado' a tabla 'classes'...")
                try:
                    db.session.execute(text("ALTER TABLE classes ADD COLUMN estado VARCHAR(20) DEFAULT 'Activa'"))
                    db.session.commit()
                    print("✓ Campo 'estado' agregado a 'classes'")
                except Exception as e:
                    print(f"⚠ Error al agregar 'estado': {e}")
                    db.session.rollback()
            else:
                print("✓ Campo 'estado' ya existe en 'classes'")
        
        # ───── Migrar tabla 'enrollments' ─────
        if "enrollments" in inspector.get_table_names():
            columns = [column["name"] for column in inspector.get_columns("enrollments")]
            
            if "tipo" not in columns:
                print("➕ Agregando campo 'tipo' a tabla 'enrollments'...")
                try:
                    db.session.execute(text("ALTER TABLE enrollments ADD COLUMN tipo VARCHAR(20) DEFAULT 'Suelta'"))
                    db.session.commit()
                    print("✓ Campo 'tipo' agregado a 'enrollments'")
                except Exception as e:
                    print(f"⚠ Error al agregar 'tipo': {e}")
                    db.session.rollback()
            else:
                print("✓ Campo 'tipo' ya existe en 'enrollments'")
            
            if "estado" not in columns:
                print("➕ Agregando campo 'estado' a tabla 'enrollments'...")
                try:
                    db.session.execute(text("ALTER TABLE enrollments ADD COLUMN estado VARCHAR(20) DEFAULT 'Activa'"))
                    db.session.commit()
                    print("✓ Campo 'estado' agregado a 'enrollments'")
                except Exception as e:
                    print(f"⚠ Error al agregar 'estado': {e}")
                    db.session.rollback()
            else:
                print("✓ Campo 'estado' ya existe en 'enrollments'")
            
            if "requiere_reembolso" not in columns:
                print("➕ Agregando campo 'requiere_reembolso' a tabla 'enrollments'...")
                try:
                    db.session.execute(text("ALTER TABLE enrollments ADD COLUMN requiere_reembolso BOOLEAN DEFAULT 0"))
                    db.session.commit()
                    print("✓ Campo 'requiere_reembolso' agregado a 'enrollments'")
                except Exception as e:
                    print(f"⚠ Error al agregar 'requiere_reembolso': {e}")
                    db.session.rollback()
            else:
                print("✓ Campo 'requiere_reembolso' ya existe en 'enrollments'")

        print("\n✅ Migración completada exitosamente!")

if __name__ == "__main__":
    print("🔄 Iniciando migración de base de datos...")
    print("=" * 60)
    migrate_database()
    print("=" * 60)
