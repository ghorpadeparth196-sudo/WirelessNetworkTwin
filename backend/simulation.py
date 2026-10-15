"""
simulation.py
-------------
The heart of the digital twin. One Simulation object holds the virtual campus
(APs + users) and advances it one "tick" at a time (default 1 tick = 1 second).

Every tick:
  1. move every user a little                     (user movement)
  2. measure distance + signal to every AP        (distance / signal strength)
  3. connect every user to the most suitable AP   (best-AP selection)
  4. compute AP load, statistics and alerts       (congestion)
  5. save the result in SQLite
"""
import statistics
import threading
from collections import deque
import random

import congestion as cg
import database as db
import signal_model as sm
from models import (AccessPoint, User, BUILDINGS, CAMPUS_WIDTH, CAMPUS_HEIGHT,
                    STUDENT_NAMES)

SEED = 2024                 # fixed seed -> the demo always starts the same way
NUM_USERS = 25
BASE_TICK_SECONDS = 1.0
PHASE_LENGTH_TICKS = 20     # the "campus activity" changes every 20 ticks
HISTORY_LENGTH = 60         # points kept for the charts
HYSTERESIS_DB = 3.0         # a user only changes AP if the new one is clearly better
EDGE_MARGIN = 8             # users never walk closer than this to the campus border
ALERT_LIST_LIMIT = 6        # max weak / disconnected user alerts shown

ZONES = {b["id"]: b for b in BUILDINGS}

# What is happening on campus decides WHERE users want to walk.
# Weights are relative: a bigger number = more users go there.
# This is what creates realistic crowds and therefore congestion.
PHASES = [
    {"name": "Lectures in Classroom Block",
     "weights": {"classroom": 45, "lab": 14, "library": 8, "admin": 4, "canteen": 5, "corridor": 20, "ground": 4}},
    {"name": "Lunch break at the Canteen",
     "weights": {"classroom": 4, "lab": 4, "library": 5, "admin": 3, "canteen": 60, "corridor": 16, "ground": 8}},
    {"name": "Practical session in the Computer Lab",
     "weights": {"classroom": 8, "lab": 55, "library": 8, "admin": 3, "canteen": 5, "corridor": 17, "ground": 4}},
    {"name": "Study rush at the Library",
     "weights": {"classroom": 6, "lab": 8, "library": 55, "admin": 3, "canteen": 6, "corridor": 18, "ground": 4}},
    {"name": "Free time on campus",
     "weights": {"classroom": 12, "lab": 12, "library": 12, "admin": 8, "canteen": 16, "corridor": 24, "ground": 16}},
]


class Simulation:
    def __init__(self):
        self.lock = threading.RLock()
        self.running = False
        self.speed = 1.0
        self.config_version = 0
        self.history = deque(maxlen=HISTORY_LENGTH)
        self._stop_event = threading.Event()
        self._thread = None
        self._load_world(reset_aps=False)

    # ------------------------------------------------------------------ setup
    @property
    def tick_seconds(self):
        return BASE_TICK_SECONDS / self.speed

    def _load_world(self, reset_aps):
        """Build a fresh campus: APs from the database + 25 new users."""
        if reset_aps:
            db.reset_access_points()
        self.aps = [AccessPoint(**row) for row in db.load_access_points()]
        for ap in self.aps:
            ap.online = bool(ap.online)
        self.rng = random.Random(SEED)
        self.tick = 0
        self.phase_index = 0
        self.history.clear()
        self.users = self._create_users()
        db.clear_logs()
        self._refresh_coverage()
        self._recompute()
        self._persist()
        self._log_tick()
        self.config_version += 1

    def _create_users(self):
        users = []
        zone_ids = list(ZONES)
        for i in range(NUM_USERS):
            zone = ZONES[self.rng.choice(zone_ids)]
            x, y = self._random_point(zone)
            user = User(id=f"U{i + 1:02d}", name=STUDENT_NAMES[i % len(STUDENT_NAMES)],
                        x=x, y=y, speed=self.rng.uniform(14, 30))
            self._pick_destination(user)
            users.append(user)
        return users

    def _refresh_coverage(self):
        self.coverage = sm.coverage_analysis(self.aps, BUILDINGS, CAMPUS_WIDTH, CAMPUS_HEIGHT)

    # --------------------------------------------------------------- movement
    def _random_point(self, zone, pad=14):
        return (self.rng.uniform(zone["x"] + pad, zone["x"] + zone["w"] - pad),
                self.rng.uniform(zone["y"] + pad, zone["y"] + zone["h"] - pad))

    def _pick_destination(self, user):
        """Choose a new walking target. The zone is picked using the weights
        of the current campus activity (e.g. most users go to the canteen at lunch)."""
        weights = PHASES[self.phase_index]["weights"]
        zone_id = self.rng.choices(list(weights.keys()), weights=list(weights.values()))[0]
        user.tx, user.ty = self._random_point(ZONES[zone_id])

    def _move_user(self, user):
        """Walk `speed` units towards the target in a straight line.
        When the target is reached: stand still for a few ticks, then pick a new one."""
        if user.wait > 0:
            user.wait -= 1
            # tiny random shuffle so a standing user does not look frozen
            user.x += self.rng.uniform(-1.5, 1.5)
            user.y += self.rng.uniform(-1.5, 1.5)
        else:
            dx, dy = user.tx - user.x, user.ty - user.y
            dist = sm.calculate_distance(user.x, user.y, user.tx, user.ty)
            if dist <= user.speed:
                user.x, user.y = user.tx, user.ty        # arrived
                user.wait = self.rng.randint(2, 6)
                self._pick_destination(user)
            else:
                user.x += dx / dist * user.speed         # unit vector * speed
                user.y += dy / dist * user.speed
        # keep every user inside the campus boundaries
        user.x = min(max(user.x, EDGE_MARGIN), CAMPUS_WIDTH - EDGE_MARGIN)
        user.y = min(max(user.y, EDGE_MARGIN), CAMPUS_HEIGHT - EDGE_MARGIN)

    def _update_phase(self):
        """Every PHASE_LENGTH_TICKS the campus activity changes and most users
        immediately head for the new hot-spot."""
        if self.tick % PHASE_LENGTH_TICKS == 0:
            self.phase_index = (self.phase_index + 1) % len(PHASES)
            for user in self.users:
                if self.rng.random() < 0.75:
                    user.wait = 0
                    self._pick_destination(user)

    # ---------------------------------------------------------- AP selection
    def _assign_aps(self):
        """Connect every user to the most suitable AP.

        For each user:
          1. measure distance and RSSI to every online AP
          2. ignore APs whose range does not reach the user
          3. score = RSSI - congestion penalty  (crowded APs lose points)
          4. pick the highest score; keep the current AP unless the new one
             is better by more than HYSTERESIS_DB (stops constant switching)
          5. nobody in range -> the user is Disconnected
        """
        loads = {ap.id: 0 for ap in self.aps}
        order = list(self.users)
        self.rng.shuffle(order)          # fair order: nobody is always first
        for user in order:
            candidates = []
            for ap in self.aps:
                if not ap.online:
                    continue
                d, rssi, quality = sm.measure(user.x, user.y, ap)
                if quality == sm.NO_CONNECTION:
                    continue
                util_after = cg.calculate_utilization(loads[ap.id] + 1, ap.capacity)
                score = rssi - cg.selection_penalty(util_after)
                candidates.append({"ap": ap, "d": d, "rssi": rssi, "q": quality, "score": score})

            if not candidates:
                self._disconnect(user)
                continue

            best = max(candidates, key=lambda c: c["score"])
            if user.connected_ap:
                for c in candidates:
                    if c["ap"].id == user.connected_ap and best["score"] - c["score"] <= HYSTERESIS_DB:
                        best = c
            loads[best["ap"].id] += 1
            user.connected_ap = best["ap"].id
            user.distance = round(best["d"], 1)
            # small random "fading" (+/- 1.5 dB) so the dashboard values look alive
            user.rssi = int(round(best["rssi"] + self.rng.uniform(-1.5, 1.5)))
            user.quality = best["q"]
            user.status = "Connected"

    def _disconnect(self, user):
        online = [ap for ap in self.aps if ap.online]
        user.connected_ap = None
        user.rssi = None
        user.quality = sm.NO_CONNECTION
        user.status = "Disconnected"
        user.distance = round(min((sm.calculate_distance(user.x, user.y, ap.x, ap.y)
                                   for ap in online), default=0.0), 1)

    # ------------------------------------------------- statistics and alerts
    def _update_ap_stats(self):
        for ap in self.aps:
            mine = [u for u in self.users if u.connected_ap == ap.id]
            ap.connected_users = len(mine)
            if ap.online:
                ap.utilization = cg.calculate_utilization(len(mine), ap.capacity)
                ap.congestion = cg.congestion_level(ap.utilization)
            else:
                ap.utilization = 0.0
                ap.congestion = "Offline"
            ap.avg_signal = round(statistics.mean(u.rssi for u in mine), 1) if mine else None

    def _compute_stats(self):
        connected = [u for u in self.users if u.status == "Connected"]
        online = [a for a in self.aps if a.online]
        counts = {q: 0 for q in sm.LEVELS}
        for u in self.users:
            counts[u.quality] += 1
        return {
            "total_aps": len(self.aps),
            "online_aps": len(online),
            "total_users": len(self.users),
            "connected_users": len(connected),
            "disconnected_users": len(self.users) - len(connected),
            "avg_signal": round(statistics.mean(u.rssi for u in connected), 1) if connected else None,
            "avg_utilization": round(statistics.mean(a.utilization for a in online), 1) if online else 0.0,
            "max_utilization": max((a.utilization for a in online), default=0.0),
            "congested_aps": sum(1 for a in online if cg.is_congested(a.congestion)),
            "weak_signal_users": counts["Weak"],
            "quality_counts": counts,
            "coverage": {
                "coverage_percent": self.coverage["coverage_percent"],
                "weak_area_percent": self.coverage["weak_area_percent"],
                "zones": self.coverage["zones"],
            },
        }

    def _build_alerts(self):
        alerts = []

        def add(level, message):
            alerts.append({"level": level, "message": message})

        for ap in self.aps:
            load = f"{ap.connected_users}/{ap.capacity} users, {ap.utilization:.0f}%"
            if not ap.online:
                add("critical", f"{ap.id} is offline.")
            elif ap.congestion == "Overloaded":
                add("critical", f"{ap.id} is overloaded ({load}).")
            elif ap.congestion == "High":
                add("warning", f"{ap.id} has high congestion ({load}).")
            elif ap.congestion == "Moderate":
                add("info", f"{ap.id} has a moderate load ({load}).")
            else:
                add("info", f"{ap.id} is operating normally ({load}).")

        weak = [u for u in self.users if u.quality == "Weak"]
        for u in weak[:ALERT_LIST_LIMIT]:
            add("warning", f"User {u.id} has weak signal ({u.rssi} dBm on {u.connected_ap}).")
        if len(weak) > ALERT_LIST_LIMIT:
            add("warning", f"{len(weak) - ALERT_LIST_LIMIT} more users have weak signal.")

        lost = [u for u in self.users if u.status == "Disconnected"]
        for u in lost[:ALERT_LIST_LIMIT]:
            add("warning", f"User {u.id} is disconnected.")
        if len(lost) > ALERT_LIST_LIMIT:
            add("warning", f"{len(lost) - ALERT_LIST_LIMIT} more users are disconnected.")

        for z in self.coverage["zones"]:
            if z["type"] == "building" and z["weak_area_percent"] >= 50:
                add("warning", f"{z['name']} has weak or no Wi-Fi in {z['weak_area_percent']:.0f}% of its area.")

        order = {"critical": 0, "warning": 1, "info": 2}
        alerts.sort(key=lambda a: order[a["level"]])     # stable: keeps AP order inside a level
        return alerts

    def _recompute(self):
        """Everything that depends on user/AP positions (no movement here)."""
        self._assign_aps()
        self._update_ap_stats()
        self.stats = self._compute_stats()
        self.alerts = self._build_alerts()

    # ------------------------------------------------------------ persistence
    def _persist(self):
        try:
            db.save_snapshot(self.users, self.aps)
        except Exception as exc:                         # never kill the simulation thread
            print(f"[database] could not save snapshot: {exc}")

    def _log_tick(self):
        """Add one point to the chart history and to simulation_logs."""
        s = self.stats
        entry = {
            "tick": self.tick,
            "avg_signal": s["avg_signal"],
            "avg_utilization": s["avg_utilization"],
            "max_utilization": s["max_utilization"],
            "congested_aps": s["congested_aps"],
            "connected_users": s["connected_users"],
            "disconnected_users": s["disconnected_users"],
            "weak_users": s["weak_signal_users"],
        }
        self.history.append(entry)
        try:
            db.insert_log(self.tick, entry, {a.id: a.connected_users for a in self.aps})
        except Exception as exc:
            print(f"[database] could not write log: {exc}")

    # --------------------------------------------------------------- the loop
    def step(self):
        """Advance the simulation by exactly one tick."""
        with self.lock:
            self.tick += 1
            self._update_phase()
            for user in self.users:
                self._move_user(user)
            self._recompute()
            self._persist()
            self._log_tick()

    def _run_loop(self, stop_event):
        while not stop_event.is_set():
            try:
                self.step()
            except Exception as exc:
                print(f"[simulation] error in tick: {exc}")
            stop_event.wait(self.tick_seconds)

    # ---------------------------------------------------------------- control
    def start(self):
        with self.lock:
            if self.running:
                return
            self.running = True
            self._stop_event = threading.Event()
            self._thread = threading.Thread(target=self._run_loop, args=(self._stop_event,), daemon=True)
            self._thread.start()

    def pause(self):
        with self.lock:
            self.running = False
            self._stop_event.set()

    def reset(self):
        with self.lock:
            self.pause()
            self.speed = 1.0
            self._load_world(reset_aps=True)

    def set_speed(self, speed):
        with self.lock:
            self.speed = speed

    def move_access_point(self, ap_id, x, y):
        """What-if tool: drag an AP to a new place and watch the effect."""
        with self.lock:
            ap = self._find_ap(ap_id)
            ap.x = min(max(float(x), 10), CAMPUS_WIDTH - 10)
            ap.y = min(max(float(y), 10), CAMPUS_HEIGHT - 10)
            db.update_access_point_position(ap.id, ap.x, ap.y)
            self._after_ap_change()
            return ap.to_dict()

    def toggle_access_point(self, ap_id):
        """What-if tool: switch an AP off / on to see how the others cope."""
        with self.lock:
            ap = self._find_ap(ap_id)
            ap.online = not ap.online
            db.set_access_point_online(ap.id, ap.online)
            self._after_ap_change()
            return ap.to_dict()

    def _after_ap_change(self):
        self._refresh_coverage()
        self._recompute()
        self._persist()
        self.config_version += 1

    def _find_ap(self, ap_id):
        for ap in self.aps:
            if ap.id == ap_id:
                return ap
        raise KeyError(ap_id)

    # ------------------------------------------------------------------ reads
    def snapshot(self):
        with self.lock:
            return {
                "running": self.running,
                "tick": self.tick,
                "tick_ms": int(self.tick_seconds * 1000),
                "speed": self.speed,
                "phase": PHASES[self.phase_index]["name"],
                "config_version": self.config_version,
                "access_points": [a.to_dict() for a in self.aps],
                "users": [u.to_dict() for u in self.users],
                "stats": self.stats,
                "alerts": self.alerts,
                "history": list(self.history),
            }

    def get_coverage(self):
        with self.lock:
            return self.coverage
