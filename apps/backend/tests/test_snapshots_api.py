from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_snapshots_json():
    resp = client.get("/api/snapshots/query")
    assert resp.status_code == 200
    data = resp.json()
    assert "snapshots" in data


def test_snapshots_csv():
    resp = client.get("/api/snapshots/query?format=csv")
    assert resp.status_code == 200
    assert resp.text.splitlines()[0] == "symbol,regime,probability"
