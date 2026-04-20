"""
IPC economy: persistent balance state and income collection.

Each team accumulates IPC (Industrial Production Certificate) income each
turn.  Income equals the sum of ipc_value() across all territories that team
currently owns.  Spending logic is handled elsewhere.
"""

from .territory import ALL_TERRITORY_IDS, Team, ipc_value, owner

# Persistent per-team IPC balance.  Zero-initialised; never goes below zero.
_balances: dict[Team, int] = {"Red": 0, "Blue": 0}


def get_balance(team: Team) -> int:
    """Return the current IPC balance for *team*."""
    return _balances[team]


def collect_income(team: Team) -> int:
    """
    Sum ipc_value() for every territory owned by *team* and add the total to
    their balance.  Neutral territories contribute nothing.

    Returns the amount collected this call (useful for tests and UI display).
    """
    income = sum(
        ipc_value(tid)
        for tid in ALL_TERRITORY_IDS
        if owner(tid) == team
    )
    _balances[team] += income
    return income


def reset_balances() -> None:
    """Reset all team balances to zero.  Used by tests and new-game setup."""
    _balances["Red"] = 0
    _balances["Blue"] = 0
