"""
Non-Combat Movement (NCM) phase: runs after all battles resolve.

During NCM the current player may reposition units that did NOT move during
the combat movement phase this turn. The same range rules apply (infantry 1,
tanks 2). Destinations MUST be friendly-owned — NCM cannot start battles.

Public API
----------
ncm_move_unit(from_tid, to_tid, team, unit_type, count)
    Reposition `count` units of `unit_type` belonging to `team` from
    `from_tid` to `to_tid`. The destination must be owned by `team`, and
    `from_tid` must not have been moved from during the combat movement
    phase this turn (and not already moved from during NCM).

    Raises:
        ValueError: if count <= 0
        ValueError: if the team does not have enough units of that type at from_tid
        ValueError: if the destination is not friendly-owned
        ValueError: if the source territory already moved this turn
            (either combat movement or NCM)

end_ncm_phase() -> None
    Finalise the NCM phase.

reset_ncm_phase() -> None
    Reset NCM state for a new turn (clears moved-from set).
"""

from typing import Literal

from . import movement_phase
from .territory import Team, TerritoryId, owner
from .units import units as get_units, set_units, UnitType

NcmPhaseState = Literal["ncm", "ended"]

_current_phase: NcmPhaseState = "ncm"

# Territories that have been moved FROM during NCM this turn.
_ncm_moved_from: set[TerritoryId] = set()


def current_ncm_phase() -> NcmPhaseState:
    """Return the current NCM phase state."""
    return _current_phase


def reset_ncm_phase() -> None:
    """Reset NCM state to the beginning of a new turn (clears moved-from set)."""
    global _current_phase, _ncm_moved_from
    _current_phase = "ncm"
    _ncm_moved_from = set()


def ncm_moved_from() -> set[TerritoryId]:
    """Return the set of territories that have been moved from this NCM phase."""
    return set(_ncm_moved_from)


def ncm_move_unit(
    from_tid: TerritoryId,
    to_tid: TerritoryId,
    team: Team,
    unit_type: UnitType,
    count: int,
) -> None:
    """
    Reposition `count` units of `unit_type` from `from_tid` to `to_tid` during NCM.

    Validates:
      - `count` >= 1
      - `team` has at least `count` units of `unit_type` at `from_tid`
      - `to_tid` is owned by `team` (friendly-only)
      - `from_tid` has not already moved this turn (combat movement OR NCM)
    """
    if count < 1:
        raise ValueError(f"count must be >= 1, got {count!r}")

    # NCM cannot enter enemy or neutral territory — friendly destinations only.
    if owner(to_tid) != team:
        raise ValueError(
            f"NCM destination {to_tid!r} is not owned by team {team!r}: "
            "non-combat movement may only enter friendly territories."
        )

    # Units that already moved this turn (combat movement) cannot move again.
    if from_tid in movement_phase._moved_from:
        raise ValueError(
            f"Territory {from_tid!r} already moved during the combat movement "
            "phase this turn; those units may not move again in NCM."
        )

    # Each territory may only move from once per NCM phase.
    if from_tid in _ncm_moved_from:
        raise ValueError(
            f"Territory {from_tid!r} has already moved this NCM phase; "
            "each territory may only move once per non-combat movement phase."
        )

    current_stack = get_units(from_tid, team)
    available = current_stack.get(unit_type, 0)
    if available < count:
        raise ValueError(
            f"Not enough {unit_type} at {from_tid!r} for team {team!r}: "
            f"requested {count}, have {available}."
        )

    # Deduct from source.
    new_from = dict(current_stack)
    new_from[unit_type] = available - count
    set_units(from_tid, team, new_from)

    # Add to destination.
    dest_stack = get_units(to_tid, team)
    new_to = dict(dest_stack)
    new_to[unit_type] = new_to.get(unit_type, 0) + count
    set_units(to_tid, team, new_to)

    # Mark source as having moved during NCM.
    _ncm_moved_from.add(from_tid)


def end_ncm_phase() -> None:
    """Finalise the NCM phase. The moved-from set persists until reset_ncm_phase()."""
    global _current_phase
    _current_phase = "ended"
