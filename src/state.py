"""
Turn state: whose turn it is. Red moves first.
"""

from .territory import Team

TEAMS: tuple[Team, ...] = ("Red", "Blue")

# Red moves first (documented in module docstring).
_current_team: Team = "Red"


def other_team(team: Team) -> Team:
    """Return the team that is not the given team."""
    return next(t for t in TEAMS if t != team)


def current_team() -> Team:
    """Return the team that may act this turn."""
    return _current_team


def end_turn() -> None:
    """Flip current team to the other side. No other side effects."""
    global _current_team
    _current_team = other_team(_current_team)
