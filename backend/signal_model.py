"""
signal_model.py
---------------
SIMULATED wireless signal model (NOT a real RF measurement).

Step 1 - distance:   plain Pythagoras between a user and an AP.
Step 2 - quality:    the distance is placed in a band (Strong, Good, ...).
Step 3 - RSSI (dBm): a simplified "log-distance path-loss" formula gives a
                     number such as -52 dBm for the dashboard.

NOTE: this file is called signal_model.py (not signal.py) on purpose.
A file named signal.py would hide Python's built-in "signal" module and
break Flask at start-up.
"""
import math

# Distance bands (in units) from the project specification
STRONG_MAX = 50
GOOD_MAX = 100
MEDIUM_MAX = 150

NO_CONNECTION = "No Connection"

# Quality -> numeric level (used by the coverage heat-map)
LEVELS = {"Strong": 4, "Good": 3, "Medium": 2, "Weak": 1, NO_CONNECTION: 0}

# Log-distance path-loss parameters:  RSSI = REF_RSSI - 10 * n * log10(d / REF_DIST)
REF_RSSI = -40.0          # signal at the reference distance (dBm)
REF_DIST = 10.0           # reference distance (units)
PATH_LOSS_EXPONENT = 2.7  # typical value for indoor / campus environments


def calculate_distance(x1, y1, x2, y2):
    """Straight-line (Euclidean) distance: sqrt(dx^2 + dy^2)."""
    return math.hypot(x2 - x1, y2 - y1)


def distance_to_rssi(distance):
    """Convert a distance into an approximate RSSI in dBm.
    Closer = stronger (less negative). Examples with the default values:
    10 -> -40 dBm, 50 -> -59 dBm, 100 -> -67 dBm, 150 -> -72 dBm, 230 -> -77 dBm."""
    distance = max(distance, REF_DIST)  # avoid log of 0 when a user stands on the AP
    return REF_RSSI - 10 * PATH_LOSS_EXPONENT * math.log10(distance / REF_DIST)


def classify_signal(distance, ap_range):
    """Place a distance into one of the quality bands."""
    if distance > ap_range:
        return NO_CONNECTION
    if distance <= STRONG_MAX:
        return "Strong"
    if distance <= GOOD_MAX:
        return "Good"
    if distance <= MEDIUM_MAX:
        return "Medium"
    return "Weak"          # between 150 and the AP range


def measure(x, y, ap):
    """Measure one point (x, y) against one AP.
    Returns (distance, rssi_dbm, quality)."""
    d = calculate_distance(x, y, ap.x, ap.y)
    return d, distance_to_rssi(d), classify_signal(d, ap.coverage_range)


def coverage_analysis(aps, zones, width, height, cell=20):
    """Divide the campus into small square cells and find the best signal
    available in each cell. This is how WEAK-SIGNAL AREAS are detected.

    Returns the grid (for the heat-map) and coverage percentages for the
    whole campus and for every zone (building / open area)."""
    cols, rows = width // cell, height // cell
    levels = []
    for r in range(rows):
        for c in range(cols):
            cx, cy = c * cell + cell / 2, r * cell + cell / 2
            best = 0
            for ap in aps:
                if not ap.online:
                    continue
                q = classify_signal(calculate_distance(cx, cy, ap.x, ap.y), ap.coverage_range)
                best = max(best, LEVELS[q])
            levels.append(best)

    def percent(count, total):
        return round(100.0 * count / total, 1) if total else 0.0

    zone_stats = []
    for z in zones:
        total = weak = covered = 0
        for r in range(rows):
            for c in range(cols):
                cx, cy = c * cell + cell / 2, r * cell + cell / 2
                if z["x"] <= cx <= z["x"] + z["w"] and z["y"] <= cy <= z["y"] + z["h"]:
                    total += 1
                    lvl = levels[r * cols + c]
                    if lvl >= 1:
                        covered += 1
                    if lvl <= 1:           # Weak or no signal
                        weak += 1
        zone_stats.append({
            "id": z["id"], "name": z["name"], "type": z["type"],
            "coverage_percent": percent(covered, total),
            "weak_area_percent": percent(weak, total),
        })

    total_cells = len(levels)
    return {
        "cell": cell, "cols": cols, "rows": rows, "levels": levels,
        "coverage_percent": percent(sum(1 for v in levels if v >= 1), total_cells),
        "weak_area_percent": percent(sum(1 for v in levels if v <= 1), total_cells),
        "zones": zone_stats,
    }
