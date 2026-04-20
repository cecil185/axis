"""
Single combat phase: roll dice, apply damage, return updated stacks and phase metadata.

This is a pure function — it reads no global state and does not mutate its inputs.
An injectable RNG callable (returns int in 1–6) is required for deterministic testing.

Rules:
- Each unit rolls one d6 independently.
- A roll of 4 or higher is a hit (1 damage point dealt to the opposing side).
- Damage is applied to the opposing side's units, removing the weakest units first
  (infantry: health=1, tanks: health=2).
- Units are eliminated when their cumulative received damage equals their health.
- att_damage / def_damage track total HP removed from each side.
- winner is 'attacker' if all defenders eliminated, 'defender' if all attackers
  eliminated, or None if both sides still have units (partial result).
"""

from typing import Callable, Literal, TypedDict

from .units import UnitCounts, UnitType, get_unit_stats

# Roll >= HIT_THRESHOLD counts as a hit.
HIT_THRESHOLD: int = 4

# Removal priority: cheapest/weakest units absorb damage first.
_REMOVAL_ORDER: tuple[UnitType, ...] = ("infantry", "tanks")


class PhaseResult(TypedDict):
    """Result of a single combat phase."""
    att_rolls: list[int]          # one roll per attacking unit
    def_rolls: list[int]          # one roll per defending unit
    att_damage: int               # total HP removed from defenders
    def_damage: int               # total HP removed from attackers
    remaining_attackers: UnitCounts
    remaining_defenders: UnitCounts
    winner: Literal["attacker", "defender"] | None


def _roll_for_stack(stack: UnitCounts, rng: Callable[[], int]) -> list[int]:
    """Roll one die per unit in the stack using a zero-arg rng; return list of results."""
    rolls: list[int] = []
    for unit_type in _REMOVAL_ORDER:
        count = stack.get(unit_type, 0)
        for _ in range(count):
            rolls.append(rng())
    return rolls


def _takes_two_args(rng: Callable) -> bool:
    """Detect whether the RNG callable takes (low, high) args like random.Random.randint."""
    import inspect
    try:
        sig = inspect.signature(rng)
        params = [
            p for p in sig.parameters.values()
            if p.default is inspect.Parameter.empty
        ]
        return len(params) == 2
    except (ValueError, TypeError):
        return False


def _apply_damage(stack: UnitCounts, damage: int) -> tuple[UnitCounts, int]:
    """
    Remove units from stack to absorb `damage` HP, weakest first.

    A unit is only eliminated when it absorbs its full health value.
    Partial damage does not kill a unit; excess damage from an overkill kill
    rolls over to the next unit.

    Returns (updated_stack, actual_damage_absorbed).
    actual_damage_absorbed may be less than `damage` if the stack is fully eliminated.
    """
    remaining = {ut: stack.get(ut, 0) for ut in _REMOVAL_ORDER}
    absorbed = 0
    for unit_type in _REMOVAL_ORDER:
        if damage <= 0:
            break
        health = get_unit_stats(unit_type)["health"]
        while remaining[unit_type] > 0 and damage >= health:
            # Only kill a unit when we have enough damage to fully eliminate it.
            damage -= health
            absorbed += health
            remaining[unit_type] -= 1
    return dict(remaining), absorbed


def combat_phase(
    attackers: UnitCounts,
    defenders: UnitCounts,
    rng: Callable,
) -> PhaseResult:
    """
    Execute one combat phase.

    Parameters
    ----------
    attackers:
        Unit counts for the attacking side (not mutated).
    defenders:
        Unit counts for the defending side (not mutated).
    rng:
        Callable that returns a die value in 1–6.
        Accepted forms:
          - ``lambda: random.randint(1, 6)``  — zero-arg, returns int in [1, 6]
          - ``random.Random(...).randint``     — two-arg (low, high)

    Returns
    -------
    PhaseResult with rolls, damage dealt, remaining stacks, and winner.
    """
    # Normalise rng to a zero-arg callable that returns 1–6.
    if _takes_two_args(rng):
        _rng: Callable[[], int] = lambda: rng(1, 6)  # noqa: E731
    else:
        _rng = rng

    # Roll dice for both sides.
    att_rolls = _roll_for_stack(attackers, _rng)
    def_rolls = _roll_for_stack(defenders, _rng)

    # Count hits (roll >= HIT_THRESHOLD).
    att_hits = sum(1 for r in att_rolls if r >= HIT_THRESHOLD)
    def_hits = sum(1 for r in def_rolls if r >= HIT_THRESHOLD)

    # Apply damage: attacker hits reduce defender HP; defender hits reduce attacker HP.
    new_defenders, att_damage = _apply_damage(defenders, att_hits)
    new_attackers, def_damage = _apply_damage(attackers, def_hits)

    # Determine winner.
    att_remaining = sum(new_attackers.values())
    def_remaining = sum(new_defenders.values())

    if def_remaining == 0 and att_remaining > 0:
        winner: Literal["attacker", "defender"] | None = "attacker"
    elif att_remaining == 0 and def_remaining > 0:
        winner = "defender"
    elif att_remaining == 0 and def_remaining == 0:
        # Mutual annihilation: defender wins ties (consistent with resolve_combat)
        winner = "defender"
    else:
        winner = None

    return PhaseResult(
        att_rolls=att_rolls,
        def_rolls=def_rolls,
        att_damage=att_damage,
        def_damage=def_damage,
        remaining_attackers=new_attackers,
        remaining_defenders=new_defenders,
        winner=winner,
    )
