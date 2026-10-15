"""
app.py
------
Flask REST API for the Wireless Network Digital Twin.
Run with:  python app.py      (server starts on http://127.0.0.1:5000)
"""
from flask import Flask, jsonify, request
from flask_cors import CORS
from werkzeug.exceptions import HTTPException

import database as db
from models import BUILDINGS, CAMPUS_HEIGHT, CAMPUS_WIDTH
from simulation import Simulation

app = Flask(__name__)
# Allow the React dev server (another port) to call this API.
CORS(app, resources={r"/api/*": {"origins": "*"}})

db.init_db()          # creates the SQLite file + tables + 4 APs if missing
sim = Simulation()    # creates 25 users and computes the first statistics


def error(message, status=400):
    return jsonify({"error": message}), status


# ----------------------------------------------------------------- read APIs
@app.get("/api/health")
def health():
    return jsonify({"status": "ok"})


@app.get("/api/campus")
def campus():
    return jsonify({"width": CAMPUS_WIDTH, "height": CAMPUS_HEIGHT, "buildings": BUILDINGS})


@app.get("/api/access-points")
def access_points():
    return jsonify(sim.snapshot()["access_points"])


@app.get("/api/users")
def users():
    return jsonify(sim.snapshot()["users"])


@app.get("/api/network/stats")
def network_stats():
    return jsonify(sim.snapshot()["stats"])


@app.get("/api/alerts")
def alerts():
    return jsonify(sim.snapshot()["alerts"])


@app.get("/api/coverage")
def coverage():
    return jsonify(sim.get_coverage())


@app.get("/api/history")
def history():
    """Per-tick log rows stored in the simulation_logs table."""
    limit = request.args.get("limit", default=60, type=int)
    return jsonify(db.get_logs(max(1, min(limit, 500))))


@app.get("/api/simulation/state")
def simulation_state():
    return jsonify(sim.snapshot())


# ---------------------------------------------------------------- control APIs
@app.post("/api/simulation/start")
def simulation_start():
    sim.start()
    return jsonify({"running": True})


@app.post("/api/simulation/pause")
def simulation_pause():
    sim.pause()
    return jsonify({"running": False})


@app.post("/api/simulation/reset")
def simulation_reset():
    sim.reset()
    return jsonify({"running": False, "message": "Simulation reset"})


@app.post("/api/simulation/speed")
def simulation_speed():
    data = request.get_json(silent=True) or {}
    speed = data.get("speed")
    if speed not in (0.5, 1, 1.0, 2, 2.0):
        return error("speed must be 0.5, 1 or 2")
    sim.set_speed(float(speed))
    return jsonify({"speed": float(speed)})


@app.post("/api/access-points/<ap_id>/position")
def move_access_point(ap_id):
    data = request.get_json(silent=True) or {}
    try:
        x, y = float(data["x"]), float(data["y"])
    except (KeyError, TypeError, ValueError):
        return error("Body must contain numeric 'x' and 'y'")
    try:
        return jsonify(sim.move_access_point(ap_id, x, y))
    except KeyError:
        return error(f"Unknown access point '{ap_id}'", 404)


@app.post("/api/access-points/<ap_id>/toggle")
def toggle_access_point(ap_id):
    try:
        return jsonify(sim.toggle_access_point(ap_id))
    except KeyError:
        return error(f"Unknown access point '{ap_id}'", 404)


# -------------------------------------------------------------- error handling
@app.errorhandler(Exception)
def handle_exception(exc):
    if isinstance(exc, HTTPException):
        return error(exc.description, exc.code)
    app.logger.exception("Unhandled error")
    return error("Internal server error", 500)


if __name__ == "__main__":
    print("Digital Twin API running on http://127.0.0.1:5000")
    # threaded=True lets the simulation thread and API requests work together.
    # debug=False because the auto-reloader would start the simulation twice.
    app.run(host="127.0.0.1", port=5000, debug=False, threaded=True)
