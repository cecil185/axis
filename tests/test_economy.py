"""Tests for IPC economy: balance state, income collection, and unit purchasing."""

import pytest
from src.territory import ALL_TERRITORY_IDS, set_owner
from src.state import TEAMS, current_team, end_turn
from src.economy import (
    UNIT_COSTS,
    buy_unit,
    clear_pending,
    collect_income,
    get_balance,
    get_pending,
    place_unit,
    reset_balances,
)
from src.units import init_game, units as territory_units

RED, BLUE = TEAMS[0], TEAMS[1]


def setup_function() -> None:
    """Reset balances and restore standard ownership before each test."""
    reset_balances()
    for i, tid in enumerate(ALL_TERRITORY_IDS):
        set_owner(tid, RED if i < 15 else BLUE)
    # Ensure turn state is Red (may have drifted due to end_turn calls in other tests)
    from src import state as _state
    _state._current_team = RED


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


# ---------------------------------------------------------------------------
# turn integration: end_turn() triggers income collection
# ---------------------------------------------------------------------------


def test_end_turn_collects_income_for_next_team() -> None:
    """end_turn() should automatically collect income for the team whose turn begins."""
    from src.territory import ipc_value
    assert current_team() == RED
    blue_income = sum(ipc_value(tid) for tid in ALL_TERRITORY_IDS[15:])
    end_turn()  # flips to Blue; Blue's turn starts → Blue collects income
    assert current_team() == BLUE
    assert get_balance(BLUE) == blue_income
    assert get_balance(RED) == 0  # Red has not yet collected
    end_turn()  # restore to Red for subsequent tests


def test_end_turn_income_accumulates_over_multiple_rounds() -> None:
    """Each complete round (Red turn + Blue turn) grows both balances."""
    from src.territory import ipc_value
    red_income = sum(ipc_value(tid) for tid in ALL_TERRITORY_IDS[:15])
    blue_income = sum(ipc_value(tid) for tid in ALL_TERRITORY_IDS[15:])
    assert current_team() == RED
    # Round 1
    end_turn()   # Blue collects
    end_turn()   # Red collects
    # Round 2
    end_turn()   # Blue collects again
    end_turn()   # Red collects again
    assert get_balance(RED) == red_income * 2
    assert get_balance(BLUE) == blue_income * 2


# ---------------------------------------------------------------------------
# Unit purchasing: buy_unit / get_pending / UNIT_COSTS
# ---------------------------------------------------------------------------


def test_unit_costs_match_spec() -> None:
    """Infantry costs 3 IPCs, tanks cost 6 IPCs."""
    assert UNIT_COSTS["infantry"] == 3
    assert UNIT_COSTS["tanks"] == 6


def test_initial_pending_queue_is_empty() -> None:
    assert get_pending(RED) == {"infantry": 0, "tanks": 0}
    assert get_pending(BLUE) == {"infantry": 0, "tanks": 0}


def test_buy_infantry_deducts_cost_and_queues() -> None:
    collect_income(RED)
    starting = get_balance(RED)
    buy_unit(RED, "infantry")
    assert get_balance(RED) == starting - 3
    assert get_pending(RED) == {"infantry": 1, "tanks": 0}


def test_buy_tank_deducts_cost_and_queues() -> None:
    collect_income(RED)
    starting = get_balance(RED)
    buy_unit(RED, "tanks")
    assert get_balance(RED) == starting - 6
    assert get_pending(RED) == {"infantry": 0, "tanks": 1}


def test_buy_unit_appends_multiple_to_queue() -> None:
    collect_income(RED)
    buy_unit(RED, "infantry")
    buy_unit(RED, "infantry")
    buy_unit(RED, "tanks")
    assert get_pending(RED) == {"infantry": 2, "tanks": 1}


def test_buy_unit_does_not_affect_other_team_balance() -> None:
    collect_income(RED)
    collect_income(BLUE)
    blue_balance = get_balance(BLUE)
    buy_unit(RED, "infantry")
    assert get_balance(BLUE) == blue_balance
    assert get_pending(BLUE) == {"infantry": 0, "tanks": 0}


def test_buy_unit_raises_when_insufficient_balance() -> None:
    """Red has 0 IPCs at start; cannot afford anything."""
    assert get_balance(RED) == 0
    with pytest.raises(ValueError):
        buy_unit(RED, "infantry")


def test_buy_unit_raises_when_balance_just_below_cost() -> None:
    """Spend down to 2 IPCs, then fail to buy infantry (cost 3)."""
    collect_income(RED)
    # Spend down close to 0
    while get_balance(RED) >= 3:
        buy_unit(RED, "infantry")
    # Now balance is 0, 1, or 2 — none of which afford infantry
    assert get_balance(RED) < 3
    with pytest.raises(ValueError):
        buy_unit(RED, "infantry")


def test_buy_unit_failure_does_not_modify_balance_or_queue() -> None:
    assert get_balance(RED) == 0
    with pytest.raises(ValueError):
        buy_unit(RED, "tanks")
    assert get_balance(RED) == 0
    assert get_pending(RED) == {"infantry": 0, "tanks": 0}


def test_get_pending_returns_copy() -> None:
    """Mutating the returned dict must not affect internal queue state."""
    collect_income(RED)
    buy_unit(RED, "infantry")
    snapshot = get_pending(RED)
    snapshot["infantry"] = 999
    assert get_pending(RED)["infantry"] == 1


def test_reset_balances_clears_pending_queue() -> None:
    collect_income(RED)
    buy_unit(RED, "infantry")
    reset_balances()
    assert get_pending(RED) == {"infantry": 0, "tanks": 0}
    assert get_pending(BLUE) == {"infantry": 0, "tanks": 0}


# ---------------------------------------------------------------------------
# Unit placement: place_unit / clear_pending
# ---------------------------------------------------------------------------


def _setup_placement_test() -> str:
    """Reset units to game-start state and ensure Red owns ALL_TERRITORY_IDS[0]."""
    init_game()
    # Restore Red ownership where setup_function would have set it
    for i, tid in enumerate(ALL_TERRITORY_IDS):
        set_owner(tid, RED if i < 15 else BLUE)
    return ALL_TERRITORY_IDS[0]


def test_place_unit_moves_infantry_from_queue_to_territory() -> None:
    tid = _setup_placement_test()
    collect_income(RED)
    buy_unit(RED, "infantry")
    before = territory_units(tid, RED).get("infantry", 0)
    place_unit(RED, tid, "infantry")
    assert get_pending(RED)["infantry"] == 0
    assert territory_units(tid, RED).get("infantry", 0) == before + 1


def test_place_unit_moves_tank_from_queue_to_territory() -> None:
    tid = _setup_placement_test()
    collect_income(RED)
    buy_unit(RED, "tanks")
    before = territory_units(tid, RED).get("tanks", 0)
    place_unit(RED, tid, "tanks")
    assert get_pending(RED)["tanks"] == 0
    assert territory_units(tid, RED).get("tanks", 0) == before + 1


def test_place_unit_rejects_when_team_does_not_own_territory() -> None:
    _setup_placement_test()
    collect_income(RED)
    buy_unit(RED, "infantry")
    blue_tid = ALL_TERRITORY_IDS[15]  # owned by Blue per setup
    assert ALL_TERRITORY_IDS  # mypy
    with pytest.raises(ValueError):
        place_unit(RED, blue_tid, "infantry")
    # Queue unaffected on rejection
    assert get_pending(RED)["infantry"] == 1


def test_place_unit_rejects_when_unit_type_not_in_queue() -> None:
    tid = _setup_placement_test()
    collect_income(RED)
    buy_unit(RED, "infantry")  # only infantry queued
    with pytest.raises(ValueError):
        place_unit(RED, tid, "tanks")
    # Queue unaffected on rejection
    assert get_pending(RED) == {"infantry": 1, "tanks": 0}


def test_place_unit_rejects_when_queue_is_empty() -> None:
    tid = _setup_placement_test()
    assert get_pending(RED) == {"infantry": 0, "tanks": 0}
    with pytest.raises(ValueError):
        place_unit(RED, tid, "infantry")


def test_place_unit_decrements_queue_one_at_a_time() -> None:
    tid = _setup_placement_test()
    collect_income(RED)
    buy_unit(RED, "infantry")
    buy_unit(RED, "infantry")
    place_unit(RED, tid, "infantry")
    assert get_pending(RED)["infantry"] == 1
    place_unit(RED, tid, "infantry")
    assert get_pending(RED)["infantry"] == 0


def test_place_unit_does_not_affect_other_team_units_in_territory() -> None:
    tid = _setup_placement_test()
    collect_income(RED)
    buy_unit(RED, "infantry")
    blue_before = territory_units(tid, BLUE)
    place_unit(RED, tid, "infantry")
    assert territory_units(tid, BLUE) == blue_before


def test_clear_pending_empties_the_queue() -> None:
    _setup_placement_test()
    collect_income(RED)
    buy_unit(RED, "infantry")
    buy_unit(RED, "tanks")
    clear_pending(RED)
    assert get_pending(RED) == {"infantry": 0, "tanks": 0}


def test_clear_pending_does_not_refund_balance() -> None:
    """Discarding pending units forfeits the IPCs already spent."""
    _setup_placement_test()
    collect_income(RED)
    starting = get_balance(RED)
    buy_unit(RED, "infantry")
    after_buy = get_balance(RED)
    assert after_buy == starting - 3
    clear_pending(RED)
    assert get_balance(RED) == after_buy  # no refund


def test_clear_pending_only_affects_specified_team() -> None:
    _setup_placement_test()
    collect_income(RED)
    collect_income(BLUE)
    buy_unit(RED, "infantry")
    buy_unit(BLUE, "tanks")
    clear_pending(RED)
    assert get_pending(RED) == {"infantry": 0, "tanks": 0}
    assert get_pending(BLUE) == {"infantry": 0, "tanks": 1}
