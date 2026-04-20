"""
Tests for Neutrals D.2: Neutral territory starting setup (axis-eez).

Covers:
- NEUTRAL_TERRITORIES constant is defined and contains 4-6 territories
- All NEUTRAL_TERRITORIES are low-value (ipc_value 1 or 2)
- is_neutral_start(tid) returns True for territories in NEUTRAL_TERRITORIES
- is_neutral_start(tid) returns False for non-neutral-start territories
- init_game() leaves NEUTRAL_TERRITORIES with Neutral ownership and no units
- init_game() does NOT change Red/Blue ownership for non-neutral territories
"""

import pytest

from src.territory import ALL_TERRITORY_IDS, ipc_value, owner, set_owner
from src.units import init_game, units, total_units, NEUTRAL_TERRITORIES, is_neutral_start
from src.state import TEAMS

RED, BLUE = TEAMS[0], TEAMS[1]


def _restore_initial() -> None:
    """Restore initial ownership: first 15 Red, last 14 Blue."""
    for i, tid in enumerate(ALL_TERRITORY_IDS):
        set_owner(tid, RED if i < 15 else BLUE)


# ---------------------------------------------------------------------------
# NEUTRAL_TERRITORIES constant
# ---------------------------------------------------------------------------

def test_neutral_territories_constant_is_defined() -> None:
    """NEUTRAL_TERRITORIES is a non-empty frozenset or tuple exported from units."""
    assert NEUTRAL_TERRITORIES is not None
    assert len(NEUTRAL_TERRITORIES) >= 4


def test_neutral_territories_has_4_to_6_entries() -> None:
    """NEUTRAL_TERRITORIES contains between 4 and 6 territories."""
    assert 4 <= len(NEUTRAL_TERRITORIES) <= 6


def test_neutral_territories_are_valid_territory_ids() -> None:
    """All entries in NEUTRAL_TERRITORIES are valid TerritoryIds."""
    for tid in NEUTRAL_TERRITORIES:
        assert tid in ALL_TERRITORY_IDS, f"{tid} is not a valid TerritoryId"


def test_neutral_territories_are_low_value() -> None:
    """All neutral-start territories have ipc_value of 1 or 2 (remote/minor)."""
    for tid in NEUTRAL_TERRITORIES:
        val = ipc_value(tid)
        assert val in (1, 2), f"{tid} has ipc_value={val}, expected 1 or 2"


def test_neutral_territories_includes_expected_candidates() -> None:
    """Neutral territories include some of the described remote atolls."""
    expected_candidates = {"clipperton", "pitcairn", "johnston", "tokelau", "nauru"}
    # At least 3 of the expected candidates must be present
    overlap = set(NEUTRAL_TERRITORIES) & expected_candidates
    assert len(overlap) >= 3, (
        f"Expected at least 3 of {expected_candidates} in NEUTRAL_TERRITORIES, "
        f"got {overlap}"
    )


# ---------------------------------------------------------------------------
# is_neutral_start()
# ---------------------------------------------------------------------------

def test_is_neutral_start_returns_true_for_neutral_territories() -> None:
    """is_neutral_start(tid) returns True for every territory in NEUTRAL_TERRITORIES."""
    for tid in NEUTRAL_TERRITORIES:
        assert is_neutral_start(tid), f"is_neutral_start({tid!r}) should be True"


def test_is_neutral_start_returns_false_for_non_neutral_territories() -> None:
    """is_neutral_start(tid) returns False for territories NOT in NEUTRAL_TERRITORIES."""
    non_neutral = [t for t in ALL_TERRITORY_IDS if t not in NEUTRAL_TERRITORIES]
    assert len(non_neutral) > 0, "There must be some non-neutral territories"
    for tid in non_neutral:
        assert not is_neutral_start(tid), f"is_neutral_start({tid!r}) should be False"


def test_is_neutral_start_with_known_non_neutral() -> None:
    """Strategic territories (japan, hawaii) are never neutral starts."""
    assert not is_neutral_start("japan")
    assert not is_neutral_start("hawaii")


# ---------------------------------------------------------------------------
# init_game(): neutral territories start ownerless with no units
# ---------------------------------------------------------------------------

def test_neutral_start_territories_have_neutral_ownership_after_init() -> None:
    """After init_game(), all NEUTRAL_TERRITORIES have Neutral ownership."""
    init_game()
    try:
        for tid in NEUTRAL_TERRITORIES:
            state = owner(tid)
            assert state == "Neutral", (
                f"Expected {tid} to be Neutral after init_game(), got {state!r}"
            )
    finally:
        _restore_initial()


def test_neutral_start_territories_have_no_units_after_init() -> None:
    """After init_game(), all NEUTRAL_TERRITORIES have 0 units for both teams."""
    init_game()
    try:
        for tid in NEUTRAL_TERRITORIES:
            red_units = total_units(tid, "Red")
            blue_units = total_units(tid, "Blue")
            assert red_units == 0, f"{tid}: Red should have 0 units, got {red_units}"
            assert blue_units == 0, f"{tid}: Blue should have 0 units, got {blue_units}"
    finally:
        _restore_initial()


def test_non_neutral_red_territories_unchanged_after_init() -> None:
    """After init_game(), non-neutral Red territories (first 15) are still Red."""
    init_game()
    try:
        red_start = [
            t for i, t in enumerate(ALL_TERRITORY_IDS)
            if i < 15 and t not in NEUTRAL_TERRITORIES
        ]
        for tid in red_start:
            state = owner(tid)
            assert state == RED, (
                f"Expected {tid} to be Red after init_game(), got {state!r}"
            )
    finally:
        _restore_initial()


def test_non_neutral_blue_territories_unchanged_after_init() -> None:
    """After init_game(), non-neutral Blue territories (last 14) are still Blue."""
    init_game()
    try:
        blue_start = [
            t for i, t in enumerate(ALL_TERRITORY_IDS)
            if i >= 15 and t not in NEUTRAL_TERRITORIES
        ]
        for tid in blue_start:
            state = owner(tid)
            assert state == BLUE, (
                f"Expected {tid} to be Blue after init_game(), got {state!r}"
            )
    finally:
        _restore_initial()


def test_non_neutral_red_territories_have_units_after_init() -> None:
    """After init_game(), non-neutral Red starting territories have Red units."""
    init_game()
    try:
        red_start = [
            t for i, t in enumerate(ALL_TERRITORY_IDS)
            if i < 15 and t not in NEUTRAL_TERRITORIES
        ]
        for tid in red_start:
            assert total_units(tid, "Red") > 0, (
                f"{tid}: Red should have units after init_game()"
            )
    finally:
        _restore_initial()


def test_non_neutral_blue_territories_have_units_after_init() -> None:
    """After init_game(), non-neutral Blue starting territories have Blue units."""
    init_game()
    try:
        blue_start = [
            t for i, t in enumerate(ALL_TERRITORY_IDS)
            if i >= 15 and t not in NEUTRAL_TERRITORIES
        ]
        for tid in blue_start:
            assert total_units(tid, "Blue") > 0, (
                f"{tid}: Blue should have units after init_game()"
            )
    finally:
        _restore_initial()
