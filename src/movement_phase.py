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

pending_battles(team=None) -> list[TerritoryId]
    Return territory IDs with pending battles, in insertion order.
    The optional `team` argument is accepted for API symmetry; the queue
    always belongs to whichever team performed the movement phase.

resolve_next_battle(team, *, rng=None) -> BattleResult
    Resolve the next pending battle for `team`: roll combat with unit-stat
    bonuses, transfer ownership if the attacker wins, and pop the battle
    from the queue. Returns a BattleResult dict with rolls and outcome.

skip_all_battles(team) -> int
    Discard every remaining pending battle for `team` without rolling.
    Returns the number of battles that were skipped.

current_phase() -> PhaseState
    Return the current phase: "movement" or "combat".

reset_movement_phase() -> None
    Reset to the movement phase (clears moved-from set and pending battles).
    Called at the start of a new turn.
"""

from typing import Callable, Literal, TypedDict

from .territory import Team, TerritoryId, owner, set_owner
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


def pending_battles(team: Team | None = None) -> list[TerritoryId]:
    """Return territory IDs with pending battles in the order they were registered.

    The optional `team` argument is accepted for API symmetry — the queue is
    not partitioned by team because only one team acts per turn — and is
    currently ignored. It is kept on the signature so callers can document
    *which* team's battles they intend to resolve.
    """
    del team  # accepted for API symmetry
    return list(_pending_battles)


def reset_movement_phase() -> None:
    """
    Reset state to the beginning of a movement phase.

    Clears the moved-from set, pending battle list, and sets phase to 'movement'.
    Called at the start of a new turn.

    The mutable containers (_moved_from, _pending_battles, _pending_battles_set)
    are cleared in place so external aliases imported via `from ... import _moved_from`
    stay in sync.
    """
    global _current_phase
    _current_phase = "movement"
    _moved_from.clear()
    _pending_battles.clear()
    _pending_battles_set.clear()


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
    - If `to_tid` is Neutral, claims it for `team` (silent, no combat).
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

    # Resolve ownership of the destination.
    dest_owner = owner(to_tid)
    if dest_owner == "Neutral":
        # Claim ownership silently; no combat, no popup.
        set_owner(to_tid, team)
    elif dest_owner != team:
        # Enemy-owned: register a pending battle.
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


# ---------------------------------------------------------------------------
# Multi-attack: resolving and skipping pending battles
# ---------------------------------------------------------------------------

class BattleResult(TypedDict):
    """Outcome of a single resolved battle in the pending-battle queue."""
    territory: TerritoryId
    attacker: Team
    defender: Team
    att_roll: int
    def_roll: int
    winner: Literal["attacker", "defender"]


def resolve_next_battle(
    team: Team,
    *,
    rng: Callable[[], int] | None = None,
) -> BattleResult:
    """
    Resolve the next pending battle for `team`.

    Pops the first territory from the pending-battle queue, rolls combat
    using unit stats from the attacking and defending stacks, and transfers
    ownership of the territory to `team` if the attacker wins.

    Parameters
    ----------
    team:
        The attacking team (the team currently taking its turn).
    rng:
        Optional zero-arg callable returning a die value in 1–6. Used by
        tests to inject deterministic rolls. When None, a real random
        roll is performed.

    Returns
    -------
    BattleResult dict describing the territory, attacker/defender teams,
    rolls, and the winner ("attacker" or "defender").

    Raises
    ------
    ValueError
        If there are no pending battles to resolve.
    """
    # Lazy imports avoid a circular dependency at module-load time.
    from .combat import roll_combat, resolve_combat_with_units  # noqa: PLC0415

    if not _pending_battles:
        raise ValueError("No pending battles to resolve.")

    target = _pending_battles[0]
    defender: Team = "Blue" if team == "Red" else "Red"

    att_roll, def_roll = roll_combat(rng=rng)

    # Find an attacker-owned neighbour to source unit-stat bonuses from.
    # The attacker just moved units into `target`, so the bonuses come from
    # the units they brought (now stacked at `target` under `team`).
    # We pass `target` as the attacking_tid so attack bonuses reflect the
    # invading force; defense bonuses come from the defender's stack at
    # `target`.
    winner = resolve_combat_with_units(
        att_roll, def_roll, team, target, target
    )

    if winner == "attacker":
        set_owner(target, team)
        # Defender's units at this territory are wiped out on a win.
        set_units(target, defender, {"infantry": 0, "tanks": 0})
    else:
        # Defender holds: attacking units sent to this territory are lost.
        set_units(target, team, {"infantry": 0, "tanks": 0})

    # Pop the resolved battle from the queue.
    _pending_battles.pop(0)
    _pending_battles_set.discard(target)

    return BattleResult(
        territory=target,
        attacker=team,
        defender=defender,
        att_roll=att_roll,
        def_roll=def_roll,
        winner=winner,
    )


def skip_all_battles(team: Team) -> int:
    """
    Discard every remaining pending battle for `team` without rolling.

    Returns
    -------
    int
        Number of battles that were skipped.
    """
    del team  # accepted for API symmetry; queue is not partitioned by team
    count = len(_pending_battles)
    _pending_battles.clear()
    _pending_battles_set.clear()
    return count
