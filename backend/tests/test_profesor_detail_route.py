import importlib
import os
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


class ProfesorDetailRouteTest(unittest.TestCase):
    def test_get_profesor_detail_requires_authentication(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            os.environ["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{Path(tmpdir) / 'app_test.db'}"

            import app as app_module
            app_module = importlib.reload(app_module)

            with app_module.app.test_client() as client:
                response = client.get("/api/profesores/1")

                self.assertNotEqual(response.status_code, 404)
                self.assertIn(response.status_code, {401, 403})


if __name__ == "__main__":
    unittest.main()
