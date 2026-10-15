"""
congestion.py
-------------
Congestion (load) calculation for Access Points.

    utilization = connected_users / capacity * 100

    0   - 50 %   -> Normal
    50  - 80 %   -> Moderate
    80  - 100 %  -> High
    > 100 %      -> Overloaded
"""


def calculate_utilization(connected_users, capacity):
    """Percentage of an AP's capacity that is in use."""
    if capacity <= 0:
        return 0.0
    return round(connected_users / capacity * 100.0, 1)


def congestion_level(utilization):
    """Turn a utilization percentage into a label."""
    if utilization > 100:
        return "Overloaded"
    if utilization >= 80:
        return "High"
    if utilization >= 50:
        return "Moderate"
    return "Normal"


def is_congested(level):
    """An AP counts as 'congested' when it is High or Overloaded."""
    return level in ("High", "Overloaded")


def selection_penalty(utilization_after_joining):
    """Used while choosing an AP. A crowded AP looks less attractive:
    for every 1 % above 80 % utilization, 0.5 dB is subtracted from its score.
    This makes users prefer a slightly weaker but emptier AP (load balancing)."""
    return max(0.0, utilization_after_joining - 80.0) * 0.5
