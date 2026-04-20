"""
Combat Movement phase: the first step of each turn, before combat.

During the movement phase the current player may move any number of their units.
Each territory (stack) may be moved FROM at most once per phase.

Moving into an enemy-owned territory:
  - Repositions the units (subtracts from source, adds to destination).
  - Registers that territory as a pending battle for the combat phase.

Moving into a friendly territory:
  - Repositions the units only (no battle registered).

Public API
----------
move_unit(from_tid, to_tid, team, unit_type, count)
    Reposition `count` units of `unit_type` belonging to `team` from
    `from_tid` to `to_tid`.

    Raises:
        ValueError: if count <= 0
        ValueError: if the team does not have enough units of that type at from_tid
        ValueError: if from_tid has already been moved from this phase

end_movement_phase() -> None
    Finalise movement and advance the phase to "combat".

pending_battles() -> list[TerritoryId]
    Return territory IDs with pending battles, in insertion order.

current_phase() -> PhaseState
    Return the current phase: "movement" or "combat".

reset_movement_phase() -> None
    Reset to the movement phase (clears moved-from set and pending battles).
    Called at the start of a new turn.
"""

from typing import Literal

from .territory import Team, TerritoryId, owner
from .units import units as get_units, set_units, UnitType

# Phase states for the turn structure.
PhaseState = Literal["movement", "combat"]

# Current phase; starts as movement at each turn.
_current_phase: PhaseState = "movement"

# Set of territory IDs that have already been moved from in this phase.
_moved_from: set[TerritoryId] = set()

# Ordered list of enemy territories moved into this phase (pending battles).
# Uses a list to preserve insertion order; a set is used for O(1) membership.
_pending_battles: list[TerritoryId] = []
_pending_battles_set: set[TerritoryId] = set()


def current_phase() -> PhaseState:
    """Return the current turn phase: 'movement' or 'combat'."""
    return _current_phase


def pending_battles() -> list[TerritoryId]:
    """Return territory IDs with pending battles in the order they were registered."""
    return list(_pending_battles)


def reset_movement_phase() -> None:
    """
    Reset state to the beginning of a movement phase.

    Clears the moved-from set, pending battle list, and sets phase to 'movement'.
    Called at the start of a new turn.
    """
    global _current_phase, _moved_from, _pending_battles, _pending_battles_set
    _current_phase = "movement"
    _moved_from = set()
    _pending_battles = []
    _pending_battles_set = set()


def move_unit(
    from_tid: TerritoryId,
    to_tid: TerritoryId,
    team: Team,
    unit_type: UnitType,
    count: int,
) -> None:
    """
    Reposition `count` units of `unit_type` belonging to `team` from
    `from_tid` to `to_tid`.

    Parameters
    ----------
    from_tid:
        The territory to move units out of.
    to_tid:
        The territory to move units into.
    team:
        The team performing the move ("Red" or "Blue").
    unit_type:
        The type of unit being moved ("infantry" or "tanks").
    count:
        The number of units to move (must be >= 1).

    Side effects
    ------------
    - Subtracts `count` units of `unit_type` from `from_tid` for `team`.
    - Adds `count` units of `unit_type` to `to_tid` for `team`.
    - If `to_tid` is owned by the enemy, registers it as a pending battle.
    - Marks `from_tid` as having been moved from; further moves from the
      same territory this phase will raise ValueError.

    Raises
    ------
    ValueError:
        If count < 1.
    ValueError:
        If the team has fewer than `count` units of `unit_type` at `from_tid`.
    ValueError:
        If `from_tid` has already been moved from this phase.
    """
    if count < 1:
        raise ValueError(f"count must be >= 1, got {count!r}")

    if from_tid in _moved_from:
        raise ValueError(
            f"Territory {from_tid!r} has already moved this phase; "
            "each territory may only move once per movement phase."
        )

    current_stack = get_units(from_tid, team)
    available = current_stack.get(unit_type, 0)
    if available < count:
        raise ValueError(
            f"Not enough {unit_type} at {from_tid!r} for team {team!r}: "
            f"requested {count}, have {available}."
        )

    # Deduct units from source territory.
    new_from = dict(current_stack)
    new_from[unit_type] = available - count
    set_units(from_tid, team, new_from)

    # Add units to destination territory.
    dest_stack = get_units(to_tid, team)
    new_to = dict(dest_stack)
    new_to[unit_type] = new_to.get(unit_type, 0) + count
    set_units(to_tid, team, new_to)

    # Mark source territory as having been moved from this phase.
    _moved_from.add(from_tid)

    # If the destination is enemy-owned, register it as a pending battle.
    dest_owner = owner(to_tid)
    if dest_owner != team and dest_owner != "Neutral":
        if to_tid not in _pending_battles_set:
            _pending_battles.append(to_tid)
            _pending_battles_set.add(to_tid)


def end_movement_phase() -> None:
    """
    Finalise the movement phase and advance the turn to the combat phase.

    The moved-from set and pending battles are intentionally preserved until
    reset_movement_phase() is called (so the combat phase can consume them).
    """
    global _current_phase
    _current_phase = "combat"
