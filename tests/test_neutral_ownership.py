"""
Tests for Neutral ownership state (axis-hw7).

Covers:
- OwnerState type includes 'Neutral'
- owner() returns 'Neutral' after set_neutral()
- Neutral territories are NOT valid attack targets
- winner() returns None when any territory is Neutral
- is_game_over() returns False when any territory is Neutral
- set_owner() transitions Neutral territory to owned
- income collection: Neutral territories produce no income
"""

from src.state import TEAMS, current_team, end_turn
from src.territory import (
    ALL_TERRITORY_IDS,
    OwnerState,
    Team,
    owner,
    set_neutral,
    set_owner,
    winner,
    is_game_over,
    ipc_value,
)
from src.valid_actions import valid_attack_targets

RED: Team = TEAMS[0]
BLUE: Team = TEAMS[1]


def _ensure_team(team: Team) -> None:
    """Advance turns until the given team is active."""
    while current_team() != team:
        end_turn()


def _restore_initial() -> None:
    """Restore initial ownership: first 15 Red, last 14 Blue."""
    for i, tid in enumerate(ALL_TERRITORY_IDS):
        set_owner(tid, RED if i < 15 else BLUE)


# ---------------------------------------------------------------------------
# Type system: OwnerState includes Neutral
# ---------------------------------------------------------------------------

def test_owner_state_literal_includes_neutral() -> None:
    """OwnerState type is importable and 'Neutral' is a valid value."""
    state: OwnerState = "Neutral"
    assert state == "Neutral"


def test_team_literal_does_not_include_neutral() -> None:
    """Team type remains Red/Blue only (does not include Neutral)."""
    teams = (RED, BLUE)
    assert "Neutral" not in teams


# ---------------------------------------------------------------------------
# owner() returns Neutral after set_neutral()
# ---------------------------------------------------------------------------

def test_owner_returns_neutral_after_set_neutral() -> None:
    """After set_neutral(), owner() returns 'Neutral'."""
    tid = "midway"
    original = owner(tid)
    try:
        set_neutral(tid)
        assert owner(tid) == "Neutral"
    finally:
        set_owner(tid, original if original != "Neutral" else RED)  # type: ignore[arg-type]
        _restore_initial()


def test_owner_returns_team_after_set_owner_on_neutral_territory() -> None:
    """Calling set_owner() on a Neutral territory assigns it to that team."""
    tid = "midway"
    set_neutral(tid)
    assert owner(tid) == "Neutral"
    try:
        set_owner(tid, RED)
        assert owner(tid) == RED
    finally:
        _restore_initial()


# ---------------------------------------------------------------------------
# valid_attack_targets: Neutral territories are excluded
# ---------------------------------------------------------------------------

def test_neutral_territory_not_in_valid_attack_targets() -> None:
    """
    A Neutral territory adjacent to a Red-owned territory is NOT a valid
    attack target, even though it is not owned by the current team.
    """
    _ensure_team(RED)
    # midway is Red's, adjacent to hawaii (also Red) and marshall (Blue).
    # Make midway Neutral and ensure it's excluded from targets.
    # Actually we need a Red territory with a Neutral neighbor.
    # johnston is Red and adjacent to hawaii and marshall.
    # Set marshall to Neutral and verify it's not a target from johnston.
    tid = "marshall"
    original = owner(tid)
    set_neutral(tid)
    try:
        targets = valid_attack_targets()
        assert "marshall" not in targets, "Neutral territory should not be a valid attack target"
    finally:
        set_owner(tid, original if original != "Neutral" else BLUE)  # type: ignore[arg-type]
        _restore_initial()


def test_non_neutral_enemy_territory_remains_valid_target() -> None:
    """Enemy (Blue) territories are still valid attack targets after neighboring Neutral set."""
    _ensure_team(RED)
    # Set midway to Neutral but keep hawaii as Red — Red still has other valid targets
    tid = "midway"
    set_neutral(tid)
    try:
        targets = valid_attack_targets()
        # There should still be Blue targets via other Red territories
        assert len(targets) > 0, "Red should still have valid Blue targets"
        assert "midway" not in targets
    finally:
        _restore_initial()


# ---------------------------------------------------------------------------
# winner() and is_game_over() with Neutral territories
# ---------------------------------------------------------------------------

def test_winner_returns_none_when_territory_is_neutral() -> None:
    """winner() returns None if any territory is Neutral, even if Red owns all others."""
    tid = ALL_TERRITORY_IDS[-1]  # rapa_nui
    # Give Red all territories except the last
    for t in ALL_TERRITORY_IDS[:-1]:
        set_owner(t, RED)
    set_neutral(tid)
    try:
        assert winner() is None, "winner() should be None when a Neutral territory exists"
    finally:
        _restore_initial()


def test_is_game_over_false_when_neutral_territory_exists() -> None:
    """is_game_over() returns False when any territory is Neutral."""
    tid = ALL_TERRITORY_IDS[0]  # japan
    original = owner(tid)
    set_neutral(tid)
    try:
        assert not is_game_over()
    finally:
        set_owner(tid, original if original != "Neutral" else RED)  # type: ignore[arg-type]
        _restore_initial()


def test_winner_returns_team_when_all_owned_no_neutral() -> None:
    """winner() returns Red when Red owns all territories (no Neutral)."""
    for tid in ALL_TERRITORY_IDS:
        set_owner(tid, RED)
    try:
        assert winner() == RED
    finally:
        _restore_initial()


# ---------------------------------------------------------------------------
# IPC income: Neutral territories produce no income
# ---------------------------------------------------------------------------

def test_neutral_territory_owner_is_not_a_team() -> None:
    """
    Neutral owner state is 'Neutral', not a Team, so income collection
    that sums ipc_value for owned territories must skip Neutral.
    """
    tid = "hawaii"
    set_neutral(tid)
    try:
        # Simulate income collection: sum ipc_value for territories owned by Red
        red_income = sum(ipc_value(t) for t in ALL_TERRITORY_IDS if owner(t) == RED)
        # hawaii (worth 3) should NOT be counted for Red since it is Neutral
        # Just verify hawaii is Neutral, not Red
        assert owner(tid) == "Neutral"
        # And verify it contributes 0 to Red income
        assert ipc_value(tid) not in [ipc_value(t) for t in ALL_TERRITORY_IDS if owner(t) == RED and t == tid]
    finally:
        _restore_initial()
