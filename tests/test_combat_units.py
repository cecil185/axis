"""Tests for unit-stat-aware combat resolution (axis-9f4)."""

import pytest

from src.combat import resolve_combat_with_units
from src.units import set_units, units, init_game
from src.territory import ALL_TERRITORY_IDS


@pytest.fixture(autouse=True)
def reset_stacks() -> None:
    """Re-initialize unit stacks before each test."""
    init_game()


def _save_stacks() -> dict:
    """Snapshot all unit stacks for teardown."""
    return {
        tid: {
            "Red": dict(units(tid, "Red")),
            "Blue": dict(units(tid, "Blue")),
        }
        for tid in ALL_TERRITORY_IDS
    }


def _restore_stacks(snapshot: dict) -> None:
    for tid, teams in snapshot.items():
        set_units(tid, "Red", teams["Red"])
        set_units(tid, "Blue", teams["Blue"])


# Use two adjacent territories for attacker/defender
ATT_TID = "japan"
DEF_TID = "marianas"


def test_resolve_combat_with_units_tanks_attack_bonus() -> None:
    """Attacker with tanks gets +1 per tank on their roll."""
    snapshot = _save_stacks()
    try:
        # Attacker (Red) has 0 infantry, 1 tank -> +1 attack
        set_units(ATT_TID, "Red", {"infantry": 0, "tanks": 1})
        # Defender (Blue) has 0 units -> +0 defense
        set_units(DEF_TID, "Blue", {"infantry": 0, "tanks": 0})
        # att_roll=3 + 1 tank bonus = 4; def_roll=4 + 0 = 4 -> tie -> defender wins
        result = resolve_combat_with_units(3, 4, "Red", ATT_TID, DEF_TID)
        assert result == "defender"
        # att_roll=4 + 1 = 5 > def_roll=4 + 0 = 4 -> attacker wins
        result = resolve_combat_with_units(4, 4, "Red", ATT_TID, DEF_TID)
        assert result == "attacker"
    finally:
        _restore_stacks(snapshot)


def test_resolve_combat_with_units_infantry_defense_bonus() -> None:
    """Defender with infantry gets +2 per infantry on their effective roll."""
    snapshot = _save_stacks()
    try:
        # Attacker (Red) has no units -> no bonus
        set_units(ATT_TID, "Red", {"infantry": 0, "tanks": 0})
        # Defender (Blue) has 1 infantry -> +2 defense
        set_units(DEF_TID, "Blue", {"infantry": 1, "tanks": 0})
        # att_roll=5 + 0 = 5; def_roll=3 + 2 = 5 -> tie -> defender wins
        result = resolve_combat_with_units(5, 3, "Red", ATT_TID, DEF_TID)
        assert result == "defender"
        # att_roll=6 + 0 = 6 > def_roll=3 + 2 = 5 -> attacker wins
        result = resolve_combat_with_units(6, 3, "Red", ATT_TID, DEF_TID)
        assert result == "attacker"
    finally:
        _restore_stacks(snapshot)


def test_resolve_combat_with_units_no_units_same_as_base() -> None:
    """With no units on either side, result should equal plain resolve_combat."""
    from src.combat import resolve_combat
    snapshot = _save_stacks()
    try:
        set_units(ATT_TID, "Red", {"infantry": 0, "tanks": 0})
        set_units(DEF_TID, "Blue", {"infantry": 0, "tanks": 0})
        for att_r in range(1, 7):
            for def_r in range(1, 7):
                result = resolve_combat_with_units(att_r, def_r, "Red", ATT_TID, DEF_TID)
                expected = resolve_combat(att_r, def_r)
                assert result == expected, f"att={att_r} def={def_r}: got {result}, want {expected}"
    finally:
        _restore_stacks(snapshot)


def test_resolve_combat_with_units_bonus_capped_at_3() -> None:
    """Bonuses are capped at 3 even with many tanks/infantry."""
    snapshot = _save_stacks()
    try:
        # Attacker (Red) has 5 tanks -> +5 but capped at 3
        set_units(ATT_TID, "Red", {"infantry": 0, "tanks": 5})
        set_units(DEF_TID, "Blue", {"infantry": 0, "tanks": 0})
        # att_roll=1 + 3(capped) = 4; def_roll=4 + 0 = 4 -> tie -> defender
        result = resolve_combat_with_units(1, 4, "Red", ATT_TID, DEF_TID)
        assert result == "defender"
        # att_roll=2 + 3 = 5 > 4 -> attacker
        result = resolve_combat_with_units(2, 4, "Red", ATT_TID, DEF_TID)
        assert result == "attacker"
    finally:
        _restore_stacks(snapshot)


def test_resolve_combat_with_units_blue_attacks_red() -> None:
    """Blue can also be the attacker; stats apply symmetrically."""
    snapshot = _save_stacks()
    try:
        # Blue attacks from marianas; Red defends japan
        set_units(DEF_TID, "Blue", {"infantry": 0, "tanks": 1})  # attacker: +1
        set_units(ATT_TID, "Red", {"infantry": 1, "tanks": 0})   # defender: +2
        # att_roll=3 + 1(tank) = 4; def_roll=2 + 2(inf) = 4 -> tie -> defender
        result = resolve_combat_with_units(3, 2, "Blue", DEF_TID, ATT_TID)
        assert result == "defender"
        # att_roll=4 + 1 = 5 > def_roll=2 + 2 = 4 -> attacker
        result = resolve_combat_with_units(4, 2, "Blue", DEF_TID, ATT_TID)
        assert result == "attacker"
    finally:
        _restore_stacks(snapshot)
