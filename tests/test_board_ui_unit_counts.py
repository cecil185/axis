"""Tests for board UI unit count display (axis-8qj).

These tests verify the data layer used by the UI:
- Unit counts per territory are readable via territory_units()
- After combat (ownership change), owner() and units() reflect the new state
- The tooltip/label logic: owning team's infantry and tank counts are correct

We do not test pygame rendering directly (requires display), but we test the
data functions that feed the labels and tooltips.
"""

import pytest
from src.territory import ALL_TERRITORY_IDS, display_name, owner, region, set_owner
from src.units import _STARTING_BLUE_TERRITORIES, _STARTING_RED_TERRITORIES, init_game, set_units, units


@pytest.fixture(autouse=True)
def reset_state() -> None:
    """Reset unit stacks and territory ownership before each test."""
    init_game()
    # Reset ownership to match initial state by re-initialising units
    # (init_game resets stacks; set_owner updates fallback _owners dict too)
    for tid in _STARTING_RED_TERRITORIES:
        set_owner(tid, "Red")
    for tid in _STARTING_BLUE_TERRITORIES:
        set_owner(tid, "Blue")


def _label_text_for(tid: str) -> str:
    """Compute the label text that would be rendered on the map marker."""
    owning_team = owner(tid)
    stack = units(tid, owning_team)  # type: ignore[arg-type]
    inf_count = stack.get("infantry", 0)
    tnk_count = stack.get("tanks", 0)
    return f"{inf_count}i {tnk_count}t"


def _tooltip_lines_for(tid: str) -> list[str]:
    """Compute tooltip lines (owner unit counts) that would be displayed on hover."""
    owning_team = owner(tid)
    own_stack = units(tid, owning_team)  # type: ignore[arg-type]
    own_inf = own_stack.get("infantry", 0)
    own_tnk = own_stack.get("tanks", 0)
    enemy_team = "Blue" if owning_team == "Red" else "Red"
    enemy_stack = units(tid, enemy_team)  # type: ignore[arg-type]
    enemy_inf = enemy_stack.get("infantry", 0)
    enemy_tnk = enemy_stack.get("tanks", 0)
    lines = [
        f"{display_name(tid)} ({region(tid)})",
        f"{owning_team}: {own_inf} inf {own_tnk} tnk",
    ]
    if enemy_inf > 0 or enemy_tnk > 0:
        lines.append(f"{enemy_team}: {enemy_inf} inf {enemy_tnk} tnk")
    return lines


# --- Unit label data (feeds per-territory markers) ---


def test_label_shows_starting_counts_for_red_territory() -> None:
    """Starting label text reflects initial game unit placement for Red."""
    tid = _STARTING_RED_TERRITORIES[0]
    assert _label_text_for(tid) == "2i 1t"


def test_label_shows_starting_counts_for_blue_territory() -> None:
    """Starting label text reflects initial game unit placement for Blue."""
    tid = _STARTING_BLUE_TERRITORIES[0]
    assert _label_text_for(tid) == "2i 1t"


def test_label_reflects_updated_unit_counts() -> None:
    """Label changes when unit counts are updated via set_units."""
    tid = _STARTING_RED_TERRITORIES[0]
    set_units(tid, "Red", {"infantry": 4, "tanks": 2})
    assert _label_text_for(tid) == "4i 2t"


def test_label_reflects_zero_units() -> None:
    """Label shows zeros when the owning team has no units in a territory."""
    tid = _STARTING_RED_TERRITORIES[0]
    set_units(tid, "Red", {"infantry": 0, "tanks": 0})
    assert _label_text_for(tid) == "0i 0t"


def test_label_text_uses_unit_majority_owner() -> None:
    """Label shows the team with the most units (per owner() semantics)."""
    tid = _STARTING_RED_TERRITORIES[0]
    set_units(tid, "Red", {"infantry": 3, "tanks": 1})
    set_units(tid, "Blue", {"infantry": 1, "tanks": 0})
    assert owner(tid) == "Red"
    assert _label_text_for(tid) == "3i 1t"


def test_label_text_reflects_blue_when_blue_has_majority() -> None:
    """Label switches to Blue's counts when Blue gains unit majority."""
    tid = _STARTING_RED_TERRITORIES[0]
    set_units(tid, "Red", {"infantry": 1, "tanks": 0})
    set_units(tid, "Blue", {"infantry": 3, "tanks": 2})
    assert owner(tid) == "Blue"
    assert _label_text_for(tid) == "3i 2t"


def test_label_updates_after_ownership_change() -> None:
    """After combat transfers ownership, label reflects new owner's units."""
    tid = _STARTING_RED_TERRITORIES[0]
    set_units(tid, "Blue", {"infantry": 2, "tanks": 1})
    set_units(tid, "Red", {"infantry": 0, "tanks": 0})
    set_owner(tid, "Blue")
    assert _label_text_for(tid) == "2i 1t"
    assert owner(tid) == "Blue"


def test_all_territories_have_valid_label_data() -> None:
    """Every territory produces a parseable label string after init_game."""
    for tid in ALL_TERRITORY_IDS:
        label = _label_text_for(tid)
        assert "i" in label and "t" in label, f"Unexpected label '{label}' for {tid}"
        parts = label.split()
        assert len(parts) == 2, f"Expected 2 parts in label for {tid}, got: {label}"
        assert parts[0].endswith("i") and parts[1].endswith("t")
        assert parts[0][:-1].isdigit() and parts[1][:-1].isdigit()


# --- Tooltip data (feeds hover popup) ---


def test_tooltip_first_line_is_territory_name_and_region() -> None:
    """Tooltip first line contains territory display name and region."""
    tid = _STARTING_RED_TERRITORIES[0]
    lines = _tooltip_lines_for(tid)
    assert lines[0] == f"{display_name(tid)} ({region(tid)})"


def test_tooltip_second_line_shows_owner_counts() -> None:
    """Tooltip second line shows owning team name and unit counts."""
    tid = _STARTING_RED_TERRITORIES[0]
    lines = _tooltip_lines_for(tid)
    assert lines[1] == "Red: 2 inf 1 tnk"


def test_tooltip_has_two_lines_when_no_enemy_units() -> None:
    """Tooltip has exactly two lines when the enemy has no units present."""
    tid = _STARTING_RED_TERRITORIES[0]
    lines = _tooltip_lines_for(tid)
    assert len(lines) == 2


def test_tooltip_has_three_lines_when_enemy_units_present() -> None:
    """Tooltip appends a third line showing enemy unit counts when present."""
    tid = _STARTING_RED_TERRITORIES[0]
    set_units(tid, "Blue", {"infantry": 1, "tanks": 0})
    lines = _tooltip_lines_for(tid)
    assert len(lines) == 3
    assert "Blue: 1 inf 0 tnk" in lines[2]


def test_tooltip_owner_line_updates_after_ownership_change() -> None:
    """After ownership transfers, tooltip reflects the new owning team."""
    tid = _STARTING_RED_TERRITORIES[0]
    set_units(tid, "Blue", {"infantry": 3, "tanks": 2})
    set_units(tid, "Red", {"infantry": 0, "tanks": 0})
    set_owner(tid, "Blue")
    lines = _tooltip_lines_for(tid)
    assert "Blue: 3 inf 2 tnk" in lines[1]
