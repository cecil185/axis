"""Converts module-level game state to a JSON-safe dict."""

from .economy import get_balance
from .state import current_team, turn
from .territory import ALL_TERRITORY_IDS, owner
from .units import units as get_units


def serialize_state() -> dict:
    """Read module-level state from all game modules and return a plain dict."""
    territories = {}
    for tid in ALL_TERRITORY_IDS:
        territories[tid] = {
            "owner": owner(tid),
            "units": {
                "Red": dict(get_units(tid, "Red")),
                "Blue": dict(get_units(tid, "Blue")),
            },
        }
    return {
        "territories": territories,
        "current_team": current_team(),
        "balances": {
            "Red": get_balance("Red"),
            "Blue": get_balance("Blue"),
        },
        "turn": turn(),
    }
