import importlib
import os
import sys
import tempfile
import unittest
from pathlib import Path

from sqlalchemy import text
from sqlalchemy import inspect

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


class UpgradeDatabaseSchemaTest(unittest.TestCase):
    def test_upgrade_database_schema_adds_admin_login_columns(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "app_test.db"
            os.environ["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{db_path}"

            import app as app_module
            app_module = importlib.reload(app_module)

            with app_module.app.app_context():
                app_module.db.session.execute(text("DROP TABLE IF EXISTS users"))
                app_module.db.session.commit()
                app_module.db.session.execute(text("""
                    CREATE TABLE users (
                        id INTEGER NOT NULL,
                        username VARCHAR(80) NOT NULL,
                        apellido VARCHAR(80),
                        email VARCHAR(120) NOT NULL,
                        dni VARCHAR(20),
                        telefono VARCHAR(20),
                        password_hash VARCHAR(256) NOT NULL,
                        role VARCHAR(20),
                        PRIMARY KEY (id),
                        UNIQUE (email)
                    )
                """))
                app_module.db.session.commit()

                app_module.upgrade_database_schema()
                app_module.db.session.remove()
                app_module.db.engine.dispose()

                inspector = inspect(app_module.db.engine)
                columns = [column["name"] for column in inspector.get_columns("users")]

                self.assertIn("admin_login_code", columns)
                self.assertIn("admin_login_code_expiration", columns)


if __name__ == "__main__":
    unittest.main()
