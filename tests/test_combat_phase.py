"""Tests for combat_phase: single combat phase as a pure function."""

from src.combat import combat_phase


def test_attacker_wins_removes_defender_unit() -> None:
    """When attacker wins, 1 casualty is applied to defender's stack (lowest health first)."""
    att = {"infantry": 2, "tanks": 1}
    def_ = {"infantry": 2, "tanks": 1}
    # rng returns 6 for attacker, 1 for defender — attacker wins easily
    rolls = iter([6, 1])
    result = combat_phase(att, def_, rng=lambda: next(rolls))
    assert result["winner"] == "attacker"
    assert result["damage_dealt"] == 1
    # Attacker stack unchanged
    assert result["att_remaining"] == {"infantry": 2, "tanks": 1}
    # Defender lost 1 infantry (lowest health)
    assert result["def_remaining"] == {"infantry": 1, "tanks": 1}


def test_defender_wins_removes_attacker_unit() -> None:
    """When defender wins, 1 casualty is applied to attacker's stack."""
    att = {"infantry": 2, "tanks": 1}
    def_ = {"infantry": 2, "tanks": 1}
    # rng returns 1 for attacker, 6 for defender — defender wins
    rolls = iter([1, 6])
    result = combat_phase(att, def_, rng=lambda: next(rolls))
    assert result["winner"] == "defender"
    assert result["damage_dealt"] == 1
    # Defender stack unchanged
    assert result["def_remaining"] == {"infantry": 2, "tanks": 1}
    # Attacker lost 1 infantry (lowest health)
    assert result["att_remaining"] == {"infantry": 1, "tanks": 1}


def test_tie_goes_to_defender() -> None:
    """Equal effective rolls: defender wins."""
    att = {"infantry": 0, "tanks": 0}
    def_ = {"infantry": 0, "tanks": 0}
    rolls = iter([3, 3])
    result = combat_phase(att, def_, rng=lambda: next(rolls))
    assert result["winner"] == "defender"


def test_attack_bonus_applied() -> None:
    """Tanks provide +1 attack bonus each (capped at 3)."""
    att = {"infantry": 0, "tanks": 2}  # +2 attack bonus
    def_ = {"infantry": 0, "tanks": 0}
    # att rolls 3 + 2 bonus = 5, def rolls 4 + 0 = 4 -> attacker wins
    rolls = iter([3, 4])
    result = combat_phase(att, def_, rng=lambda: next(rolls))
    assert result["att_bonus"] == 2
    assert result["def_bonus"] == 0
    assert result["winner"] == "attacker"


def test_defense_bonus_applied() -> None:
    """Infantry provide +2 defense bonus each (capped at 3)."""
    att = {"infantry": 0, "tanks": 0}
    def_ = {"infantry": 2, "tanks": 0}  # +4 defense, capped at +3
    # att rolls 5, def rolls 2 + 3 cap = 5 -> tie, defender wins
    rolls = iter([5, 2])
    result = combat_phase(att, def_, rng=lambda: next(rolls))
    assert result["def_bonus"] == 3  # capped
    assert result["winner"] == "defender"


def test_casualty_removes_infantry_before_tanks() -> None:
    """Casualties remove lowest-health units first (infantry h=1 before tanks h=2)."""
    att = {"infantry": 1, "tanks": 1}
    def_ = {"infantry": 0, "tanks": 1}
    # Defender wins
    rolls = iter([1, 6])
    result = combat_phase(att, def_, rng=lambda: next(rolls))
    assert result["winner"] == "defender"
    # Attacker loses infantry first
    assert result["att_remaining"] == {"infantry": 0, "tanks": 1}


def test_casualty_removes_tank_when_no_infantry() -> None:
    """When no infantry, casualty removes a tank."""
    att = {"infantry": 0, "tanks": 2}
    def_ = {"infantry": 1, "tanks": 0}
    # Defender wins
    rolls = iter([1, 6])
    result = combat_phase(att, def_, rng=lambda: next(rolls))
    assert result["winner"] == "defender"
    assert result["att_remaining"] == {"infantry": 0, "tanks": 1}


def test_does_not_mutate_input_stacks() -> None:
    """combat_phase is pure: input stacks are not modified."""
    att = {"infantry": 2, "tanks": 1}
    def_ = {"infantry": 2, "tanks": 1}
    att_copy = dict(att)
    def_copy = dict(def_)
    rolls = iter([6, 1])
    combat_phase(att, def_, rng=lambda: next(rolls))
    assert att == att_copy
    assert def_ == def_copy


def test_seed_produces_deterministic_results() -> None:
    """Same seed produces same phase result."""
    att = {"infantry": 2, "tanks": 1}
    def_ = {"infantry": 2, "tanks": 1}
    r1 = combat_phase(att, def_, seed=42)
    r2 = combat_phase(att, def_, seed=42)
    assert r1 == r2


def test_phase_result_contains_all_fields() -> None:
    """PhaseResult has all expected keys."""
    att = {"infantry": 1, "tanks": 0}
    def_ = {"infantry": 1, "tanks": 0}
    rolls = iter([4, 3])
    result = combat_phase(att, def_, rng=lambda: next(rolls))
    assert "att_roll" in result
    assert "def_roll" in result
    assert "att_bonus" in result
    assert "def_bonus" in result
    assert "winner" in result
    assert "damage_dealt" in result
    assert "att_remaining" in result
    assert "def_remaining" in result
    assert result["att_roll"] == 4
    assert result["def_roll"] == 3
