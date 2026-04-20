"""Tests for IPC economy: balance state and income collection."""

import pytest
from src.territory import ALL_TERRITORY_IDS, set_owner
from src.state import TEAMS
from src.economy import collect_income, get_balance, reset_balances

RED, BLUE = TEAMS[0], TEAMS[1]


def setup_function() -> None:
    """Reset balances and restore standard ownership before each test."""
    reset_balances()
    for i, tid in enumerate(ALL_TERRITORY_IDS):
        set_owner(tid, RED if i < 15 else BLUE)


# ---------------------------------------------------------------------------
# get_balance: initial state
# ---------------------------------------------------------------------------


def test_initial_balance_red_is_zero() -> None:
    assert get_balance(RED) == 0


def test_initial_balance_blue_is_zero() -> None:
    assert get_balance(BLUE) == 0


# ---------------------------------------------------------------------------
# collect_income: single call
# ---------------------------------------------------------------------------


def test_collect_income_increases_red_balance() -> None:
    collect_income(RED)
    assert get_balance(RED) > 0


def test_collect_income_does_not_affect_other_team() -> None:
    collect_income(RED)
    assert get_balance(BLUE) == 0


def test_collect_income_returns_amount_collected() -> None:
    amount = collect_income(RED)
    assert amount > 0
    assert get_balance(RED) == amount


def test_collect_income_sums_ipc_values_of_owned_territories() -> None:
    """Red owns first 15 territories; income equals sum of their ipc_values."""
    from src.territory import ipc_value
    expected = sum(ipc_value(tid) for tid in ALL_TERRITORY_IDS[:15])
    amount = collect_income(RED)
    assert amount == expected
    assert get_balance(RED) == expected


def test_collect_income_blue_correct_sum() -> None:
    """Blue owns last 14 territories; income equals sum of their ipc_values."""
    from src.territory import ipc_value
    expected = sum(ipc_value(tid) for tid in ALL_TERRITORY_IDS[15:])
    amount = collect_income(BLUE)
    assert amount == expected
    assert get_balance(BLUE) == expected


# ---------------------------------------------------------------------------
# collect_income: accumulation across multiple calls
# ---------------------------------------------------------------------------


def test_balance_accumulates_across_turns() -> None:
    """Calling collect_income twice doubles the balance (same ownership)."""
    from src.territory import ipc_value
    income = sum(ipc_value(tid) for tid in ALL_TERRITORY_IDS[:15])
    collect_income(RED)
    collect_income(RED)
    assert get_balance(RED) == income * 2


def test_balances_accumulate_independently() -> None:
    """Red and Blue balances grow independently when each collects income."""
    from src.territory import ipc_value
    red_income = sum(ipc_value(tid) for tid in ALL_TERRITORY_IDS[:15])
    blue_income = sum(ipc_value(tid) for tid in ALL_TERRITORY_IDS[15:])
    collect_income(RED)
    collect_income(BLUE)
    assert get_balance(RED) == red_income
    assert get_balance(BLUE) == blue_income


def test_balance_reflects_territory_changes() -> None:
    """If Red captures a Blue territory, subsequent income reflects the new holdings."""
    from src.territory import ipc_value
    # Red captures hawaii (already Red, just verify), then gain one Blue territory
    captured = ALL_TERRITORY_IDS[15]  # first Blue territory
    set_owner(captured, RED)
    extra = ipc_value(captured)
    original_income = sum(ipc_value(tid) for tid in ALL_TERRITORY_IDS[:15])
    expected = original_income + extra
    amount = collect_income(RED)
    assert amount == expected


def test_neutral_territories_excluded_from_income() -> None:
    """Neutral territories produce no income."""
    from src.territory import ipc_value, set_neutral
    # Mark one Red territory as neutral; Red's income should drop
    neutralized = ALL_TERRITORY_IDS[0]
    original_income = sum(ipc_value(tid) for tid in ALL_TERRITORY_IDS[:15])
    lost = ipc_value(neutralized)
    set_neutral(neutralized)
    amount = collect_income(RED)
    assert amount == original_income - lost


# ---------------------------------------------------------------------------
# reset_balances
# ---------------------------------------------------------------------------


def test_reset_balances_clears_both_teams() -> None:
    collect_income(RED)
    collect_income(BLUE)
    reset_balances()
    assert get_balance(RED) == 0
    assert get_balance(BLUE) == 0
