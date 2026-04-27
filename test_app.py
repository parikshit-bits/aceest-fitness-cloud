import pytest
import json
from app import app, init_db, PROGRAMS


@pytest.fixture
def client(tmp_path, monkeypatch):
    """Create a fresh test client with an isolated in-memory DB for each test."""
    monkeypatch.setattr("app.DB_NAME", str(tmp_path / "test.db"))
    init_db()
    app.config["TESTING"] = True
    with app.test_client() as c:
        yield c


# ── Index ─────────────────────────────────────────────────────────────────────

def test_index_returns_200(client):
    res = client.get("/")
    assert res.status_code == 200


def test_index_message(client):
    data = json.loads(client.get("/").data)
    assert data["status"] == "running"
    assert "ACEest" in data["message"]


# ── Programs ──────────────────────────────────────────────────────────────────

def test_get_programs(client):
    res = client.get("/programs")
    assert res.status_code == 200
    data = json.loads(res.data)
    assert "programs" in data
    assert len(data["programs"]) == len(PROGRAMS)


def test_get_valid_program(client):
    res = client.get("/programs/Beginner (BG)")
    assert res.status_code == 200
    data = json.loads(res.data)
    assert "factor" in data
    assert data["factor"] == 26


def test_get_invalid_program(client):
    res = client.get("/programs/NonExistentProgram")
    assert res.status_code == 404


# ── Clients ───────────────────────────────────────────────────────────────────

def test_add_client_success(client):
    payload = {"name": "Arjun", "age": 28, "weight": 75.0, "program": "Beginner (BG)"}
    res = client.post("/clients", json=payload)
    assert res.status_code == 201
    data = json.loads(res.data)
    assert data["name"] == "Arjun"
    assert data["calories"] == int(75.0 * 26)


def test_add_client_missing_name(client):
    res = client.post("/clients", json={"program": "Beginner (BG)"})
    assert res.status_code == 400


def test_add_client_missing_program(client):
    res = client.post("/clients", json={"name": "Priya"})
    assert res.status_code == 400


def test_add_client_invalid_program(client):
    res = client.post("/clients", json={"name": "Priya", "program": "Yoga"})
    assert res.status_code == 400


def test_get_existing_client(client):
    payload = {"name": "Ravi", "weight": 80.0, "program": "Muscle Gain (MG) - PPL"}
    client.post("/clients", json=payload)
    res = client.get("/clients/Ravi")
    assert res.status_code == 200
    assert json.loads(res.data)["name"] == "Ravi"


def test_get_nonexistent_client(client):
    res = client.get("/clients/Ghost")
    assert res.status_code == 404


def test_delete_client(client):
    client.post("/clients", json={"name": "Temp", "program": "Beginner (BG)"})
    res = client.delete("/clients/Temp")
    assert res.status_code == 200
    assert client.get("/clients/Temp").status_code == 404


def test_get_all_clients(client):
    client.post("/clients", json={"name": "A", "program": "Beginner (BG)"})
    client.post("/clients", json={"name": "B", "program": "Beginner (BG)"})
    data = json.loads(client.get("/clients").data)
    assert len(data["clients"]) == 2


# ── Calorie Calculation ───────────────────────────────────────────────────────

def test_calorie_calculation_fat_loss(client):
    res = client.post(
        "/calories",
        json={"weight": 70.0, "program": "Fat Loss (FL) - 3 day"}
    )
    assert res.status_code == 200
    assert json.loads(res.data)["calories"] == 70 * 22


def test_calorie_calculation_muscle_gain(client):
    res = client.post(
        "/calories",
        json={"weight": 80.0, "program": "Muscle Gain (MG) - PPL"}
    )
    assert res.status_code == 200
    assert json.loads(res.data)["calories"] == 80 * 35


def test_calorie_missing_fields(client):
    res = client.post("/calories", json={"weight": 70.0})
    assert res.status_code == 400


def test_calorie_invalid_program(client):
    res = client.post("/calories", json={"weight": 70.0, "program": "Zumba"})
    assert res.status_code == 400


# ── Progress ──────────────────────────────────────────────────────────────────

def test_save_progress(client):
    payload = {"client_name": "Arjun", "week": "Week 01", "adherence": 85}
    res = client.post("/progress", json=payload)
    assert res.status_code == 201


def test_save_progress_missing_fields(client):
    res = client.post("/progress", json={"client_name": "Arjun"})
    assert res.status_code == 400


def test_get_progress(client):
    p1 = {"client_name": "Arjun", "week": "Week 01", "adherence": 80}
    p2 = {"client_name": "Arjun", "week": "Week 02", "adherence": 90}
    client.post("/progress", json=p1)
    client.post("/progress", json=p2)
    data = json.loads(client.get("/progress/Arjun").data)
    assert len(data["progress"]) == 2
