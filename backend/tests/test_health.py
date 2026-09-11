from fastapi.testclient import TestClient
from app.main import app
from app.db import get_db

class DbProbe:
    def execute(self, statement):
        return None

def test_openapi_and_health():
    app.dependency_overrides[get_db] = lambda: DbProbe()
    client = TestClient(app)
    assert client.get("/openapi.json").status_code == 200
    assert client.get("/health").json()["status"] == "ok"
    app.dependency_overrides.clear()
