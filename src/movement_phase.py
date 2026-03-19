"""
Movement phase: move units before combat.

During the movement phase, the current player may move any number of their unit
stacks; each (territory, unit_type) pair may move at most once per phase.
Moving units into an enemy-owned territory registers it as a pending battle.
After the player confirms, the turn advances to the combat phase.

API:
  current_phase() -> "movement" | "combat"
  move_unit(from_tid, to_tid, team, unit_type, count) -> None
  moved_stacks() -> set of (TerritoryId, UnitType) moved this phase
  pending_battles() -> set of TerritoryId with incoming enemy units
  end_movement_phase() -> None (transition to combat)
  reset_phase() -> None (back to movement, clear state)
"""

from typing import Literal

from .movement import reachable_territories
from .territory import TerritoryId, Team, owner
from .units import UnitType, units, set_units


Phase = Literal["movement", "combat"]

_phase: Phase = "movement"
_moved: set[tuple[TerritoryId, UnitType]] = set()
_pending_battles: set[TerritoryId] = set()


def current_phase() -> Phase:
    """Return the current turn phase."""
    return _phase


def move_unit(
    from_tid: TerritoryId,
    to_tid: TerritoryId,
    team: Team,
    unit_type: UnitType,
    count: int,
) -> None:
    """Move count units of unit_type from from_tid to to_tid for team."""
    global _phase
    if _phase != "movement":
        raise ValueError("Cannot move units: not in movement phase")
    if count <= 0:
        raise ValueError("count must be positive")
    if (from_tid, unit_type) in _moved:
        raise ValueError(f"{unit_type} in {from_tid} already moved this phase")

    reachable = reachable_territories(from_tid, team, unit_type)
    if to_tid not in reachable:
        raise ValueError(f"{to_tid} not reachable from {from_tid} for {team} {unit_type}")

    from_counts = units(from_tid, team)
    if from_counts.get(unit_type, 0) < count:
        raise ValueError(f"Not enough {unit_type} in {from_tid}: have {from_counts.get(unit_type, 0)}, need {count}")

    # Move the units
    to_counts = units(to_tid, team)
    from_counts[unit_type] -= count
    to_counts[unit_type] = to_counts.get(unit_type, 0) + count
    set_units(from_tid, team, from_counts)
    set_units(to_tid, team, to_counts)

    _moved.add((from_tid, unit_type))

    # Register pending battle if destination is enemy-owned
    if owner(to_tid) != team:
        _pending_battles.add(to_tid)


def moved_stacks() -> set[tuple[TerritoryId, UnitType]]:
    """Return set of (territory, unit_type) pairs that have moved this phase."""
    return set(_moved)


def pending_battles() -> set[TerritoryId]:
    """Return set of territory IDs where incoming units will fight."""
    return set(_pending_battles)


def end_movement_phase() -> None:
    """Transition from movement phase to combat phase."""
    global _phase
    if _phase != "movement":
        raise ValueError("Cannot end movement phase: not in movement phase")
    _phase = "combat"


def reset_phase() -> None:
    """Reset to movement phase, clearing moved stacks and pending battles."""
    global _phase
    _phase = "movement"
    _moved.clear()
    _pending_battles.clear()
