# Wireless Network Digital Twin for Smart Campus

A fully software-based mini project: a virtual campus Wi-Fi network in which access points (APs) and
students are placed, students move around, and the system calculates distance, signal strength,
best-AP selection, AP congestion and weak-signal areas in real time.

> **No hardware is used.** Everything is simulated in software. The signal strength is a
> **SIMULATED, simplified distance-based model, not a real RF measurement.**

## 1. Project description

A *digital twin* is a virtual copy of a real system that can be observed and experimented on safely.
This project is a digital twin of a campus wireless network: a 2D campus with 6 areas, 4 Wi-Fi APs
and 25 virtual students. It lets you answer questions such as *"What happens to the canteen AP at
lunch time?"*, *"Where is the Wi-Fi weak?"* and *"What if this AP fails or is moved?"*

## 2. Objectives

- Build a virtual campus network with buildings, APs and users.
- Simulate user movement and recalculate distance and signal strength continuously.
- Automatically connect each user to the most suitable AP.
- Measure AP utilization and detect congested APs, weak-signal users and weak-signal areas.
- Show live statistics, tables, charts and alerts, with Start / Pause / Reset controls.

## 3. Features

- 2D SVG campus map: Classroom Block, Computer Lab, Library, Canteen, Administration Block, Open Ground and Central Corridor (works offline, no map API).
- 4 APs with ID, name, position, coverage range, capacity, live user count, utilization and status.
- 25 virtual users moving between buildings; they stay inside the campus.
- Simulated RSSI (dBm) and signal bands: Strong / Good / Medium / Weak / No Connection.
- Best-AP selection that considers signal **and** congestion (with hysteresis to avoid flip-flopping).
- Congestion levels: Normal, Moderate, High, Overloaded.
- 8 dashboard cards, AP table, user table (search + filter), alerts, 4 live Chart.js charts.
- Coverage analysis: signal heat-map and per-building weak-area percentage.
- "What-if" tools: **drag an AP** to a new place, or **turn an AP off**, and watch the network react.
- Campus "activity" phases (lectures, lunch break, lab session, library rush, free time) that create realistic crowds.
- Simulation speed 0.5x / 1x / 2x.
- SQLite database created automatically.

## 4. Technology stack

| Part | Technology |
|---|---|
| Frontend | React 18, Vite, JavaScript, HTML, CSS, SVG |
| Charts | Chart.js with react-chartjs-2 |
| Backend | Python, Flask, Flask-CORS |
| Database | SQLite (Python `sqlite3`) |

## 5. System architecture

```
+------------------------+   HTTP / JSON (polling every 0.8 s)   +--------------------------------+
|   React frontend       | <-----------------------------------> |   Flask backend (port 5000)    |
|   (Vite, port 5173)    |      Start / Pause / Reset / Move AP   |  app.py  -> REST API           |
|  map, cards, tables,   |                                        |  simulation.py -> tick loop    |
|  charts, alerts        |                                        |  signal_model.py, congestion.py|
+------------------------+                                        |  database.py -> SQLite file    |
                                                                  +--------------------------------+
```

The backend runs the simulation in a background thread (one tick per second). The browser only asks
for the latest state and draws it.

## 6. Folder structure

```
wireless-network-digital-twin/
├── frontend/
│   ├── package.json
│   ├── vite.config.js
│   ├── index.html
│   └── src/
│       ├── main.jsx, App.jsx, App.css, api.js, utils.js
│       └── components/
│           ├── CampusMap.jsx      (SVG campus, drag & drop of APs)
│           ├── AccessPoint.jsx    (Wi-Fi icon + coverage circle)
│           ├── UserMarker.jsx     (moving user dot)
│           ├── Dashboard.jsx      (Overview page)
│           ├── NetworkStats.jsx   (8 cards + coverage analysis)
│           ├── APTable.jsx, UserTable.jsx, Alerts.jsx, Charts.jsx
├── backend/
│   ├── app.py            REST API
│   ├── database.py       SQLite functions
│   ├── models.py         campus layout, default APs, AccessPoint / User classes
│   ├── simulation.py     movement, AP selection, statistics, alerts
│   ├── signal_model.py   distance, RSSI, signal bands, coverage analysis
│   ├── congestion.py     utilization and congestion levels
│   ├── requirements.txt
│   └── database/         digital_twin.db is created here
├── README.md
├── RUN_INSTRUCTIONS.md
└── .gitignore
```

> The signal module is named `signal_model.py` instead of `signal.py` on purpose: a file called
> `signal.py` would hide Python's built-in `signal` module and make Flask crash at start-up.

## 7. Installation requirements

- Windows 10/11 (also works on macOS / Linux)
- Python 3.9 or newer
- Node.js 18 or newer
- VS Code (optional, recommended)

## 8. Installation commands

```
cd backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt

cd ..\frontend
npm install
```

## 9. How to run the backend

```
cd backend
venv\Scripts\activate
python app.py
```
The API is now on http://127.0.0.1:5000.

## 10. How to run the frontend

```
cd frontend
npm run dev
```
Open http://localhost:5173. (Step-by-step version: see `RUN_INSTRUCTIONS.md`.)

## 11. API details

Base URL: `http://127.0.0.1:5000/api`

| Method | Endpoint | Description |
|---|---|---|
| GET | `/health` | Server check |
| GET | `/campus` | Campus size and buildings |
| GET | `/access-points` | All APs with live load |
| GET | `/users` | All users with AP, signal, distance, status |
| GET | `/network/stats` | Summary statistics (the 8 card values, coverage) |
| GET | `/alerts` | Current alerts |
| GET | `/coverage` | Coverage grid (heat-map) and per-zone coverage |
| GET | `/history?limit=60` | Per-tick rows from the `simulation_logs` table |
| GET | `/simulation/state` | Everything above in one response (used by the dashboard) |
| POST | `/simulation/start` | Start the simulation |
| POST | `/simulation/pause` | Pause the simulation |
| POST | `/simulation/reset` | Reset users, APs and logs to the starting demo |
| POST | `/simulation/speed` | Body `{"speed": 0.5 \| 1 \| 2}` |
| POST | `/access-points/<id>/position` | Body `{"x": 170, "y": 500}` - move an AP |
| POST | `/access-points/<id>/toggle` | Turn an AP off / on |

Errors are returned as JSON: `{"error": "message"}` with status 400 / 404 / 500.

## 12. Simulation logic

Every tick (1 second at 1x speed) `simulation.py` does:

1. **Move users.** Each user walks `speed` units (14-30) in a straight line towards a target point. On arrival the user waits 2-6 ticks, then picks a new target. Targets are chosen with weights that depend on the current *campus activity*, which changes every 20 ticks (e.g. most users walk to the canteen during the lunch break). Positions are clamped so users stay inside the campus.
2. **Measure.** Distance, RSSI and signal band are calculated from each user to each AP.
3. **Select the AP** (next section).
4. **Compute** AP load, statistics and alerts.
5. **Save** users, AP loads and one log row in SQLite.

The demo uses a fixed random seed, so Reset always returns to the same starting situation.

**Best-AP selection.** For each user (in random order):
1. calculate the distance to every online AP;
2. ignore APs whose coverage range does not reach the user;
3. score = RSSI minus a congestion penalty (0.5 dB for every 1 % that the AP would be above 80 % utilization);
4. choose the highest score; keep the current AP unless the new one is better by more than 3 dB (hysteresis);
5. if no AP is in range the user is **Disconnected**.

## 13. Signal-strength logic (SIMULATED)

Distance: `d = sqrt((x_user - x_ap)^2 + (y_user - y_ap)^2)`

| Distance | Quality |
|---|---|
| d <= 50 | Strong |
| 50 < d <= 100 | Good |
| 100 < d <= 150 | Medium |
| 150 < d <= AP range | Weak |
| d > AP range | No Connection |

RSSI uses a log-distance path-loss formula:

`RSSI = -40 - 10 * 2.7 * log10(d / 10)`  (distance is at least 10)

Examples: 10 -> -40 dBm, 50 -> -59 dBm, 100 -> -67 dBm, 150 -> -72 dBm, 230 -> -77 dBm.
A random fluctuation of up to +/-1.5 dB is added to the connected user's value so the dashboard looks alive.

**This is a simplified academic model. It ignores walls, interference, antennas and real radio
propagation, and it is not a real RF measurement.**

Weak-signal **areas** are found by splitting the campus into 20 x 20 cells and checking the best
signal in every cell. With the default AP layout the Administration Block and the Open Ground have
weak or no coverage on purpose, so the twin has something to detect. Drag an AP towards them and the
coverage numbers update.

## 14. Congestion logic

`utilization = connected_users / capacity * 100`

| Utilization | Status |
|---|---|
| 0 - 50 % | Normal |
| 50 - 80 % | Moderate |
| 80 - 100 % | High |
| over 100 % | Overloaded |

Default capacities: AP1 = 12, AP2 = 10, AP3 = 10, AP4 = 12 users. An AP is counted as *congested*
when it is High or Overloaded. Capacities are small so that congestion appears with only 25 users.

## 15. Database structure (SQLite)

File: `backend/database/digital_twin.db` (created automatically).

- **access_points**: `id`, `name`, `location`, `x`, `y`, `coverage_range`, `capacity`, `online`, `connected_users`, `utilization`, `status`
- **users**: `id`, `name`, `x`, `y`, `connected_ap`, `distance`, `rssi`, `quality`, `status`
- **simulation_logs**: `id`, `tick`, `timestamp`, `connected_users`, `disconnected_users`, `avg_signal`, `avg_utilization`, `congested_aps`, `weak_users`, `ap_loads` (JSON)

AP positions you change by dragging are saved; **Reset** restores the default layout. Logs are cleared on start-up and on reset.

## 16. Screenshots

_Add your screenshots here after running the project:_

- Overview dashboard
- Campus map with coverage circles
- Signal heat-map
- Analytics charts

## 17. Future scope

- Real RF propagation with walls and floors (ray tracing or ITU indoor models).
- More APs, channel assignment and interference modelling.
- Different user types (laptop, phone) with different traffic demand and bandwidth/throughput.
- Import a real floor plan and real AP inventory.
- Automatic AP placement suggestions that maximize coverage.
- Machine-learning prediction of congestion and roaming.
- Export reports (CSV / PDF) and user accounts for administrators.
