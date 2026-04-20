"""
Tests for the single combat phase pure function (axis-i75).

combat_phase(attackers, defenders, rng) -> PhaseResult

- Rolls dice for each unit (1d6 per unit) using injectable RNG
- Applies damage: each hit removes health from the opposing side
  starting with the weakest units first (infantry health=1, tanks health=2)
- Returns updated stacks (no mutation) + phase metadata
- Pure function: no global state reads or writes
"""

import random
from typing import Callable

import pytest

from src.combat_phase import PhaseResult, combat_phase
from src.units import UnitCounts


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _fixed_rng(values: list[int]) -> Callable[[], int]:
    """Return a callable that yields values in sequence."""
    it = iter(values)
    return lambda: next(it)


def _total_units(counts: UnitCounts) -> int:
    return sum(counts.values())


# ---------------------------------------------------------------------------
# Return shape
# ---------------------------------------------------------------------------


def test_combat_phase_returns_phase_result() -> None:
    """Return value must be a PhaseResult TypedDict with required keys."""
    attackers: UnitCounts = {"infantry": 1, "tanks": 0}
    defenders: UnitCounts = {"infantry": 1, "tanks": 0}
    # Provide enough rolls: 1 attacker roll + 1 defender roll
    rng = _fixed_rng([3, 2])
    result = combat_phase(attackers, defenders, rng)
    assert isinstance(result, dict)
    assert "att_rolls" in result
    assert "def_rolls" in result
    assert "att_damage" in result
    assert "def_damage" in result
    assert "remaining_attackers" in result
    assert "remaining_defenders" in result
    assert "winner" in result


def test_combat_phase_rolls_lists_have_one_entry_per_unit() -> None:
    """Each unit rolls one die; roll lists must match unit counts."""
    attackers: UnitCounts = {"infantry": 2, "tanks": 1}
    defenders: UnitCounts = {"infantry": 0, "tanks": 2}
    # 3 attacker rolls + 2 defender rolls = 5 values
    rng = _fixed_rng([4, 3, 5, 2, 6])
    result = combat_phase(attackers, defenders, rng)
    assert len(result["att_rolls"]) == 3
    assert len(result["def_rolls"]) == 2


# ---------------------------------------------------------------------------
# Attacker wins: all defenders eliminated
# ---------------------------------------------------------------------------


def test_attacker_wins_clears_defenders() -> None:
    """When attacker deals enough damage all defenders are eliminated."""
    attackers: UnitCounts = {"infantry": 3, "tanks": 0}
    defenders: UnitCounts = {"infantry": 1, "tanks": 0}
    # All attackers hit (roll >= 4 threshold assumed: any roll), defenders roll low
    # Attack: 3 infantry each roll 4 (hits), damage=3 vs defenders health=1
    # Defense: 1 infantry rolls 1 (miss)
    rng = _fixed_rng([4, 4, 4, 1])
    result = combat_phase(attackers, defenders, rng)
    assert result["winner"] == "attacker"
    assert _total_units(result["remaining_defenders"]) == 0


def test_attacker_wins_with_tanks() -> None:
    """Tanks have health=2; attacker with enough hits removes defender tanks."""
    attackers: UnitCounts = {"infantry": 0, "tanks": 2}
    defenders: UnitCounts = {"infantry": 0, "tanks": 1}
    # 2 attacker rolls (tanks hit on >=4), 1 defender roll
    # att_rolls=[4, 4]: 2 hits, each hit does 1 damage
    # def_tank health=2, receives 2 damage -> eliminated
    # def_rolls=[2]: 1 miss
    rng = _fixed_rng([4, 4, 2])
    result = combat_phase(attackers, defenders, rng)
    assert result["winner"] == "attacker"
    assert result["remaining_defenders"]["tanks"] == 0


# ---------------------------------------------------------------------------
# Defender wins: all attackers eliminated
# ---------------------------------------------------------------------------


def test_defender_wins_clears_attackers() -> None:
    """When defender deals enough damage all attackers are eliminated."""
    attackers: UnitCounts = {"infantry": 1, "tanks": 0}
    defenders: UnitCounts = {"infantry": 3, "tanks": 0}
    # Attacker misses, defenders all hit
    rng = _fixed_rng([1, 4, 4, 4])
    result = combat_phase(attackers, defenders, rng)
    assert result["winner"] == "defender"
    assert _total_units(result["remaining_attackers"]) == 0


# ---------------------------------------------------------------------------
# Partial casualties
# ---------------------------------------------------------------------------


def test_partial_casualties_both_sides_lose_units() -> None:
    """When neither side is fully eliminated, partial casualties remain."""
    attackers: UnitCounts = {"infantry": 2, "tanks": 0}
    defenders: UnitCounts = {"infantry": 2, "tanks": 0}
    # att rolls: [4, 1] -> 1 hit (1 damage to defender)
    # def rolls: [4, 1] -> 1 hit (1 damage to attacker)
    # infantry health=1, so 1 hit kills 1 infantry on each side
    rng = _fixed_rng([4, 1, 4, 1])
    result = combat_phase(attackers, defenders, rng)
    assert result["winner"] is None
    assert result["remaining_attackers"]["infantry"] == 1
    assert result["remaining_defenders"]["infantry"] == 1


def test_partial_casualties_tank_survives_single_hit() -> None:
    """A tank (health=2) survives 1 hit but not 2."""
    attackers: UnitCounts = {"infantry": 1, "tanks": 0}
    defenders: UnitCounts = {"infantry": 0, "tanks": 1}
    # 1 attacker roll hit, 1 defender roll miss
    # defender tank has health=2, receives 1 damage -> still alive at 1 hp
    rng = _fixed_rng([4, 1])
    result = combat_phase(attackers, defenders, rng)
    assert result["winner"] is None
    assert result["remaining_defenders"]["tanks"] == 1


def test_partial_casualties_tank_destroyed_by_two_hits() -> None:
    """A tank (health=2) is eliminated when it receives 2 damage."""
    attackers: UnitCounts = {"infantry": 2, "tanks": 0}
    defenders: UnitCounts = {"infantry": 0, "tanks": 1}
    # 2 attacker infantry each roll hit, defender misses
    rng = _fixed_rng([4, 4, 1])
    result = combat_phase(attackers, defenders, rng)
    assert result["winner"] == "attacker"
    assert result["remaining_defenders"]["tanks"] == 0


# ---------------------------------------------------------------------------
# No mutation of input stacks
# ---------------------------------------------------------------------------


def test_input_stacks_not_mutated() -> None:
    """combat_phase must not modify the input dicts."""
    attackers: UnitCounts = {"infantry": 2, "tanks": 1}
    defenders: UnitCounts = {"infantry": 1, "tanks": 1}
    att_copy = dict(attackers)
    def_copy = dict(defenders)
    rng = _fixed_rng([4, 4, 4, 1, 1])
    combat_phase(attackers, defenders, rng)
    assert attackers == att_copy
    assert defenders == def_copy


# ---------------------------------------------------------------------------
# Hit threshold
# ---------------------------------------------------------------------------


def test_roll_below_4_is_a_miss() -> None:
    """Rolls 1-3 are misses; no damage should be dealt."""
    attackers: UnitCounts = {"infantry": 1, "tanks": 0}
    defenders: UnitCounts = {"infantry": 1, "tanks": 0}
    # Both miss
    rng = _fixed_rng([3, 3])
    result = combat_phase(attackers, defenders, rng)
    assert result["att_damage"] == 0
    assert result["def_damage"] == 0
    assert result["winner"] is None


def test_roll_of_4_is_a_hit() -> None:
    """Roll of exactly 4 should count as a hit."""
    attackers: UnitCounts = {"infantry": 1, "tanks": 0}
    defenders: UnitCounts = {"infantry": 1, "tanks": 0}
    # Attacker hits (4), defender misses (1)
    rng = _fixed_rng([4, 1])
    result = combat_phase(attackers, defenders, rng)
    assert result["att_damage"] >= 1


# ---------------------------------------------------------------------------
# Damage tracking
# ---------------------------------------------------------------------------


def test_att_damage_and_def_damage_match_hits() -> None:
    """att_damage and def_damage must reflect total HP removed per side."""
    attackers: UnitCounts = {"infantry": 2, "tanks": 0}
    defenders: UnitCounts = {"infantry": 0, "tanks": 1}
    # att rolls: [5, 5] -> 2 hits, each 1 damage -> att_damage=2 (removes tank with health=2)
    # def rolls: [6] -> 1 hit (tank hits harder but still 1 hit = 1 dmg)
    rng = _fixed_rng([5, 5, 6])
    result = combat_phase(attackers, defenders, rng)
    # att dealt 2 damage total (enough to kill the tank)
    assert result["att_damage"] == 2
    # def dealt 1 damage total (kills 1 infantry)
    assert result["def_damage"] == 1


# ---------------------------------------------------------------------------
# Determinism via injectable RNG
# ---------------------------------------------------------------------------


def test_injectable_rng_is_deterministic() -> None:
    """Same RNG sequence produces the same result."""
    attackers: UnitCounts = {"infantry": 2, "tanks": 1}
    defenders: UnitCounts = {"infantry": 1, "tanks": 1}

    def make_rng() -> Callable[[], int]:
        return _fixed_rng([4, 2, 5, 3, 6])

    r1 = combat_phase(attackers, defenders, make_rng())
    r2 = combat_phase(attackers, defenders, make_rng())
    assert r1 == r2


def test_random_rng_produces_valid_results() -> None:
    """Using a real Random instance should also work."""
    attackers: UnitCounts = {"infantry": 2, "tanks": 1}
    defenders: UnitCounts = {"infantry": 2, "tanks": 1}
    rng_obj = random.Random(99)
    result = combat_phase(attackers, defenders, rng_obj.randint)
    # Just sanity-check shapes
    total_att = sum(attackers.values())
    total_def = sum(defenders.values())
    assert len(result["att_rolls"]) == total_att
    assert len(result["def_rolls"]) == total_def
