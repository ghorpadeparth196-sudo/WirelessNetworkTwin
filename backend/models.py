"""
models.py
---------
Data definitions for the digital twin: the campus layout, the default Wi-Fi
Access Points and the two main objects (AccessPoint, User).

Coordinate system: the campus is a flat 2D plane of 900 x 600 "units".
(0, 0) is the top-left corner, x grows to the right, y grows downwards.
1 unit is treated as roughly 1 metre in the simulated model.
"""
from dataclasses import dataclass

CAMPUS_WIDTH = 900
CAMPUS_HEIGHT = 600

# Every area of the campus. "building" areas are enclosed; "open" areas are
# outdoors / walkways. Users walk between these zones during the simulation.
BUILDINGS = [
    {"id": "classroom", "name": "Classroom Block", "type": "building",
     "x": 30, "y": 30, "w": 250, "h": 140, "color": "#d6e4f5"},
    {"id": "lab", "name": "Computer Lab", "type": "building",
     "x": 325, "y": 30, "w": 250, "h": 140, "color": "#d9efe6"},
    {"id": "library", "name": "Library", "type": "building",
     "x": 620, "y": 30, "w": 250, "h": 140, "color": "#e6dff3"},
    {"id": "admin", "name": "Administration Block", "type": "building",
     "x": 30, "y": 430, "w": 250, "h": 140, "color": "#f3e2d3"},
    {"id": "canteen", "name": "Canteen", "type": "building",
     "x": 325, "y": 430, "w": 250, "h": 140, "color": "#f6ecc9"},
    {"id": "ground", "name": "Open Ground", "type": "open",
     "x": 620, "y": 430, "w": 250, "h": 140, "color": "#dcebd2"},
    {"id": "corridor", "name": "Central Corridor", "type": "open",
     "x": 30, "y": 185, "w": 840, "h": 230, "color": "#eef1f4"},
]

# The 4 Access Points that exist when the project starts.
# Each AP sits in the middle of its building. "coverage_range" is the radius
# (in units) inside which a device can still receive a signal.
DEFAULT_ACCESS_POINTS = [
    {"id": "AP1", "name": "Classroom AP", "location": "Classroom Block",
     "x": 155, "y": 100, "coverage_range": 230, "capacity": 12, "online": 1},
    {"id": "AP2", "name": "Computer Lab AP", "location": "Computer Lab",
     "x": 450, "y": 100, "coverage_range": 240, "capacity": 10, "online": 1},
    {"id": "AP3", "name": "Library AP", "location": "Library",
     "x": 745, "y": 100, "coverage_range": 230, "capacity": 10, "online": 1},
    {"id": "AP4", "name": "Canteen AP", "location": "Canteen",
     "x": 450, "y": 500, "coverage_range": 260, "capacity": 12, "online": 1},
]

STUDENT_NAMES = [
    "Aarav", "Diya", "Rohan", "Ananya", "Karan", "Priya", "Vikram", "Sneha",
    "Arjun", "Meera", "Rahul", "Isha", "Aditya", "Kavya", "Siddharth", "Neha",
    "Manish", "Pooja", "Nikhil", "Riya", "Varun", "Tanvi", "Harsh", "Simran",
    "Yash", "Divya", "Tarun", "Nisha", "Kunal", "Aisha",
]


@dataclass
class AccessPoint:
    """A virtual Wi-Fi Access Point."""
    id: str
    name: str
    location: str
    x: float
    y: float
    coverage_range: float
    capacity: int
    online: bool = True
    # --- values recalculated on every simulation tick ---
    connected_users: int = 0
    utilization: float = 0.0
    congestion: str = "Normal"      # Normal / Moderate / High / Overloaded / Offline
    avg_signal: float = None        # average RSSI (dBm) of connected users

    def to_dict(self):
        return {
            "id": self.id, "name": self.name, "location": self.location,
            "x": round(self.x, 1), "y": round(self.y, 1),
            "coverage_range": self.coverage_range, "capacity": self.capacity,
            "online": self.online,
            "status": "Online" if self.online else "Offline",
            "connected_users": self.connected_users,
            "utilization": self.utilization,
            "congestion": self.congestion,
            "avg_signal": self.avg_signal,
        }


@dataclass
class User:
    """A virtual student / device that walks around the campus."""
    id: str
    name: str
    x: float
    y: float
    speed: float                    # units walked per simulation tick
    # --- movement state (internal, not sent to the browser) ---
    tx: float = 0.0                 # target x the user is walking to
    ty: float = 0.0                 # target y
    wait: int = 0                   # ticks left to stand still at the target
    # --- network state (recalculated on every tick) ---
    connected_ap: str = None
    distance: float = 0.0           # distance to the connected AP (or nearest AP if disconnected)
    rssi: int = None                # simulated signal strength in dBm
    quality: str = "No Connection"  # Strong / Good / Medium / Weak / No Connection
    status: str = "Disconnected"    # Connected / Disconnected

    def to_dict(self):
        return {
            "id": self.id, "name": self.name,
            "x": round(self.x, 1), "y": round(self.y, 1),
            "connected_ap": self.connected_ap,
            "distance": self.distance, "rssi": self.rssi,
            "quality": self.quality, "status": self.status,
        }
