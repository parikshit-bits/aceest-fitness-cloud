from flask import Flask, request, jsonify
import sqlite3

app = Flask(__name__)
DB_NAME = "aceest_fitness.db"

PROGRAMS = {
    "Fat Loss (FL) - 3 day": {
        "factor": 22,
        "desc": "3-day full-body fat loss",
        "workout": "Mon: Back Squat 5x5 | Wed: Bench Press + 21-15-9 | Fri: Zone 2 Cardio",
        "diet": "Egg Whites + Oats | Grilled Chicken + Brown Rice | Fish Curry + Millet Roti",
    },
    "Muscle Gain (MG) - PPL": {
        "factor": 35,
        "desc": "Push/Pull/Legs hypertrophy",
        "workout": "Mon: Push | Tue: Pull | Wed: Legs | Thu: Push | Fri: Pull | Sat: Legs",
        "diet": "Eggs + PB Oats | Chicken Biryani | Mutton Curry + Rice",
    },
    "Beginner (BG)": {
        "factor": 26,
        "desc": "3-day simple beginner full-body",
        "workout": "Mon/Wed/Fri: Air Squats, Ring Rows, Push-ups",
        "diet": "Balanced Tamil Meals: Idli / Dosa / Rice + Dal",
    },
}


# ── DB helpers ────────────────────────────────────────────────────────────────

def get_db():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db()
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS clients (
            id       INTEGER PRIMARY KEY AUTOINCREMENT,
            name     TEXT UNIQUE NOT NULL,
            age      INTEGER,
            weight   REAL,
            program  TEXT,
            calories INTEGER
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS progress (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            client_name TEXT,
            week        TEXT,
            adherence   INTEGER
        )
        """
    )
    conn.commit()
    conn.close()


with app.app_context():
    init_db()


# ── Routes ────────────────────────────────────────────────────────────────────

@app.route("/")
def index():
    return jsonify({"message": "ACEest Fitness API", "status": "running", "version": "1.0"})


@app.route("/programs", methods=["GET"])
def get_programs():
    return jsonify({"programs": list(PROGRAMS.keys())})


@app.route("/programs/<path:name>", methods=["GET"])
def get_program(name):
    if name not in PROGRAMS:
        return jsonify({"error": "Program not found"}), 404
    return jsonify(PROGRAMS[name])


@app.route("/clients", methods=["GET"])
def get_clients():
    conn = get_db()
    rows = conn.execute("SELECT * FROM clients ORDER BY name").fetchall()
    conn.close()
    return jsonify({"clients": [dict(r) for r in rows]})


@app.route("/clients", methods=["POST"])
def add_client():
    data = request.get_json(force=True)
    if not data or not data.get("name") or not data.get("program"):
        return jsonify({"error": "name and program are required"}), 400

    name = data["name"].strip()
    program = data["program"]

    if program not in PROGRAMS:
        return jsonify({"error": "Invalid program"}), 400

    age = data.get("age")
    weight = data.get("weight")
    calories = int(weight * PROGRAMS[program]["factor"]) if weight else None

    try:
        conn = get_db()
        conn.execute(
            "INSERT OR REPLACE INTO clients (name, age, weight, program, calories) "
            "VALUES (?, ?, ?, ?, ?)",
            (name, age, weight, program, calories),
        )
        conn.commit()
        conn.close()
        return jsonify({"message": "Client saved", "name": name, "calories": calories}), 201
    except Exception as exc:
        return jsonify({"error": str(exc)}), 500


@app.route("/clients/<name>", methods=["GET"])
def get_client(name):
    conn = get_db()
    row = conn.execute("SELECT * FROM clients WHERE name = ?", (name,)).fetchone()
    conn.close()
    if not row:
        return jsonify({"error": "Client not found"}), 404
    return jsonify(dict(row))


@app.route("/clients/<name>", methods=["DELETE"])
def delete_client(name):
    conn = get_db()
    conn.execute("DELETE FROM clients WHERE name = ?", (name,))
    conn.commit()
    conn.close()
    return jsonify({"message": f"Client {name} deleted"})


@app.route("/calories", methods=["POST"])
def calculate_calories():
    data = request.get_json(force=True)
    weight = data.get("weight")
    program = data.get("program")
    if not weight or not program:
        return jsonify({"error": "weight and program are required"}), 400
    if program not in PROGRAMS:
        return jsonify({"error": "Invalid program"}), 400
    calories = int(weight * PROGRAMS[program]["factor"])
    return jsonify({"calories": calories, "program": program, "weight": weight})


@app.route("/progress", methods=["POST"])
def save_progress():
    data = request.get_json(force=True)
    client_name = data.get("client_name")
    week = data.get("week", "")
    adherence = data.get("adherence")
    if not client_name or adherence is None:
        return jsonify({"error": "client_name and adherence are required"}), 400
    conn = get_db()
    conn.execute(
        "INSERT INTO progress (client_name, week, adherence) VALUES (?, ?, ?)",
        (client_name, week, adherence),
    )
    conn.commit()
    conn.close()
    return jsonify({"message": "Progress saved"}), 201


@app.route("/progress/<client_name>", methods=["GET"])
def get_progress(client_name):
    conn = get_db()
    rows = conn.execute(
        "SELECT * FROM progress WHERE client_name = ? ORDER BY id", (client_name,)
    ).fetchall()
    conn.close()
    return jsonify({"progress": [dict(r) for r in rows]})


# ── Entry point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
