"""
Turn state: whose turn it is. Red moves first.
"""

from .territory import Team

# Red moves first (documented in module docstring).
_current_team: Team = "Red"


def current_team() -> Team:
    """Return the team that may act this turn."""
    return _current_team


def end_turn() -> None:
    """Flip current team to the other side. No other side effects."""
    global _current_team
    _current_team = "Blue" if _current_team == "Red" else "Red"
