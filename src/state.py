"""
Turn state: whose turn it is. Red moves first.

Income is collected at the start of each team's turn via economy.collect_income().
end_turn() triggers collection for the incoming team immediately after the flip,
so balances accumulate each time a new turn begins.  Red's very first turn
(turn 1) does not pre-collect income; income first lands at the moment the
game engine calls end_turn() and flips to each team.
"""

from .territory import Team

TEAMS: tuple[Team, ...] = ("Red", "Blue")

# Red moves first (documented in module docstring).
_current_team: Team = "Red"
_turn: int = 1


def other_team(team: Team) -> Team:
    """Return the team that is not the given team."""
    return next(t for t in TEAMS if t != team)


def current_team() -> Team:
    """Return the team that may act this turn."""
    return _current_team


def turn() -> int:
    """Return the current turn number (starts at 1)."""
    return _turn


def end_turn() -> None:
    """
    Flip current team to the other side and collect income for the new team.

    Income collection (economy.collect_income) is called once per turn start,
    immediately after the team flip, so balances grow each time a team's turn
    begins.
    """
    global _current_team, _turn
    _current_team = other_team(_current_team)
    if _current_team == TEAMS[0]:
        _turn += 1
    # Lazy import avoids a circular dependency at module-load time.
    from .economy import collect_income  # noqa: PLC0415
    collect_income(_current_team)
