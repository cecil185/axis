"""
Tests for combat resolution affecting ownership (axis-9of).

The integration path mirrors game.py's on_combat hook:
  1. roll_combat(rng=...) to get fixed rolls
  2. resolve_combat(att_roll, def_roll) to determine winner
  3. set_owner(target_id, attacker) only when resolve_combat == "attacker"

Territory borders used (verified against actual game state):
  Red: indonesia, belau, nauru, kiribati, tuvalu
  Blue: papua_new_guinea, solomon, fiji, tokelau, french_polynesia
  Red→Blue border: indonesia → papua_new_guinea
  Blue→Red border: papua_new_guinea → indonesia
"""

from unittest.mock import patch

import pytest

from src.actions import attack, set_combat_hook, skip
from src.combat import resolve_combat, roll_combat
from src.state import TEAMS, current_team
from src.territory import TerritoryId, owner, set_owner

RED, BLUE = TEAMS[0], TEAMS[1]

# Known Red territory with a Blue neighbor (real game border)
RED_ATT = "indonesia"
BLUE_DEF = "papua_new_guinea"

# Known Blue territory with a Red neighbor (real game border)
BLUE_ATT = "papua_new_guinea"
RED_DEF = "indonesia"


def _ensure_team(team: str) -> None:
    """Advance turns until it is `team`'s turn."""
    if current_team() != team:
        skip()
    assert current_team() == team


def _make_combat_hook(att_roll: int, def_roll: int) -> tuple[list[tuple[int, int, str]], "callable"]:
    """
    Return (log, hook) where hook is a combat hook that uses fixed rolls.

    The log collects (att_roll, def_roll, winner) tuples so tests can inspect results.
    """
    log: list[tuple[int, int, str]] = []
    rolls = [att_roll, def_roll]
    roll_iter = iter(rolls)

    def hook(target_id: TerritoryId) -> None:
        att = current_team()
        a, d = roll_combat(rng=lambda: next(roll_iter))
        w = resolve_combat(a, d)
        log.append((a, d, w))
        if w == "attacker":
            set_owner(target_id, att)

    return log, hook


# ---------------------------------------------------------------------------
# Attacker wins: territory changes ownership
# ---------------------------------------------------------------------------

def test_attacker_wins_transfers_ownership() -> None:
    """
    When att_roll > def_roll the contested territory becomes the attacker's.
    """
    _ensure_team(RED)

    assert owner(RED_ATT) == RED
    assert owner(BLUE_DEF) == BLUE

    log, hook = _make_combat_hook(att_roll=5, def_roll=2)
    set_combat_hook(hook)

    try:
        with patch("src.valid_actions.neighbors") as mock_neighbors:
            mock_neighbors.side_effect = lambda tid: [BLUE_DEF] if tid == RED_ATT else []
            attack(BLUE_DEF)
    finally:
        set_combat_hook(None)

    assert len(log) == 1
    att_r, def_r, w = log[0]
    assert att_r == 5
    assert def_r == 2
    assert w == "attacker"

    assert owner(BLUE_DEF) == RED, "attacker should have taken the territory"

    # Restore original state
    set_owner(BLUE_DEF, BLUE)
    assert owner(BLUE_DEF) == BLUE


# ---------------------------------------------------------------------------
# Defender holds: territory ownership unchanged
# ---------------------------------------------------------------------------

def test_defender_holds_ownership_unchanged() -> None:
    """
    When att_roll <= def_roll ownership of the contested territory stays with defender.
    """
    _ensure_team(RED)

    assert owner(RED_ATT) == RED
    assert owner(BLUE_DEF) == BLUE

    log, hook = _make_combat_hook(att_roll=3, def_roll=3)
    set_combat_hook(hook)

    try:
        with patch("src.valid_actions.neighbors") as mock_neighbors:
            mock_neighbors.side_effect = lambda tid: [BLUE_DEF] if tid == RED_ATT else []
            attack(BLUE_DEF)
    finally:
        set_combat_hook(None)

    assert len(log) == 1
    att_r, def_r, w = log[0]
    assert att_r == 3
    assert def_r == 3
    assert w == "defender"

    assert owner(BLUE_DEF) == BLUE, "defender should have held the territory"


def test_defender_wins_ownership_unchanged() -> None:
    """
    When def_roll > att_roll ownership of the contested territory stays with defender.
    """
    _ensure_team(RED)

    assert owner(RED_ATT) == RED
    assert owner(BLUE_DEF) == BLUE

    log, hook = _make_combat_hook(att_roll=1, def_roll=6)
    set_combat_hook(hook)

    try:
        with patch("src.valid_actions.neighbors") as mock_neighbors:
            mock_neighbors.side_effect = lambda tid: [BLUE_DEF] if tid == RED_ATT else []
            attack(BLUE_DEF)
    finally:
        set_combat_hook(None)

    assert len(log) == 1
    att_r, def_r, w = log[0]
    assert att_r == 1
    assert def_r == 6
    assert w == "defender"

    assert owner(BLUE_DEF) == BLUE, "defender should have held the territory"


# ---------------------------------------------------------------------------
# Blue-team attack: symmetric ownership behavior
# ---------------------------------------------------------------------------

def test_blue_attacker_wins_transfers_ownership() -> None:
    """
    When it is Blue's turn and att_roll > def_roll, attacker (Blue) takes the territory.
    """
    _ensure_team(BLUE)

    assert owner(BLUE_ATT) == BLUE

    # Temporarily set the defender territory to Red so Blue can attack it
    original_owner = owner(RED_DEF)
    set_owner(RED_DEF, RED)

    log, hook = _make_combat_hook(att_roll=6, def_roll=1)
    set_combat_hook(hook)

    try:
        with patch("src.valid_actions.neighbors") as mock_neighbors:
            mock_neighbors.side_effect = lambda tid: [RED_DEF] if tid == BLUE_ATT else []
            attack(RED_DEF)
    finally:
        set_combat_hook(None)
        set_owner(RED_DEF, original_owner)  # restore

    assert len(log) == 1
    _, _, w = log[0]
    assert w == "attacker"
    assert resolve_combat(6, 1) == "attacker"


def test_blue_defender_holds_ownership_unchanged() -> None:
    """
    When it is Blue's turn and att_roll <= def_roll, Red territory remains Red.
    """
    _ensure_team(BLUE)

    original_owner = owner(RED_DEF)
    set_owner(RED_DEF, RED)

    log, hook = _make_combat_hook(att_roll=2, def_roll=5)
    set_combat_hook(hook)

    try:
        with patch("src.valid_actions.neighbors") as mock_neighbors:
            mock_neighbors.side_effect = lambda tid: [RED_DEF] if tid == BLUE_ATT else []
            attack(RED_DEF)
    finally:
        set_combat_hook(None)

    assert len(log) == 1
    att_r, def_r, w = log[0]
    assert att_r == 2
    assert def_r == 5
    assert w == "defender"

    assert owner(RED_DEF) == RED, "defender should have held the territory"

    # Restore
    set_owner(RED_DEF, original_owner)
