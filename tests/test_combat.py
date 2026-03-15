"""Tests for combat dice rolls (axis-fio 3.1)."""

import pytest

from src.combat import roll_combat

RED = "Red"
BLUE: str = "Blue"


def test_roll_combat_returns_two_ints_in_range() -> None:
    """Rolls (no seed) should be in 1–6 each. Run multiple times to sample."""
    for _ in range(50):
        a, d = roll_combat(RED, BLUE, "B")
        assert 1 <= a <= 6
        assert 1 <= d <= 6


def test_roll_combat_with_seed_is_deterministic() -> None:
    """Same seed must produce the same (attacker_roll, defender_roll)."""
    r1 = roll_combat(RED, BLUE, "C", seed=42)
    r2 = roll_combat(RED, BLUE, "C", seed=42)
    assert r1 == r2
    assert 1 <= r1[0] <= 6 and 1 <= r1[1] <= 6


def test_roll_combat_different_seeds_differ() -> None:
    """Different seeds should usually produce different rolls (probabilistic)."""
    results = {roll_combat(RED, BLUE, "A", seed=s) for s in range(100)}
    assert len(results) > 1


def test_roll_combat_with_injectable_rng() -> None:
    """Passing rng callable yields those values as attacker and defender rolls."""
    rolls = [3, 5]
    it = iter(rolls)

    def fixed_rng() -> int:
        return next(it)

    a, d = roll_combat(RED, BLUE, "D", rng=fixed_rng)
    assert a == 3
    assert d == 5


def test_roll_combat_rng_must_return_1_to_6() -> None:
    """If rng returns out of range, raise ValueError."""
    with pytest.raises(ValueError, match="1–6"):
        roll_combat(RED, BLUE, "A", rng=lambda: 0)
    with pytest.raises(ValueError, match="1–6"):
        roll_combat(RED, BLUE, "A", rng=lambda: 7)
