"""
IPC economy: persistent balance state, income collection, and unit purchasing.

Each team accumulates IPC (Industrial Production Certificate) income each
turn.  Income equals the sum of ipc_value() across all territories that team
currently owns.  Teams may spend IPCs to purchase units (infantry, tanks)
which sit in a per-team pending queue until placed on owned territories.
"""

from .territory import ALL_TERRITORY_IDS, Team, ipc_value, owner
from .units import UnitCounts, UnitType

# Persistent per-team IPC balance.  Zero-initialised; never goes below zero.
_balances: dict[Team, int] = {"Red": 0, "Blue": 0}

# Cost in IPCs to purchase one unit of each type.
UNIT_COSTS: dict[UnitType, int] = {"infantry": 3, "tanks": 6}

# Per-team queue of purchased-but-unplaced units.
_pending: dict[Team, UnitCounts] = {
    "Red": {"infantry": 0, "tanks": 0},
    "Blue": {"infantry": 0, "tanks": 0},
}


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
    _pending["Red"] = {"infantry": 0, "tanks": 0}
    _pending["Blue"] = {"infantry": 0, "tanks": 0}


def buy_unit(team: Team, unit_type: UnitType) -> None:
    """
    Deduct the unit cost from *team*'s balance and append the unit to the
    pending queue.  Raises ValueError if the team has insufficient IPCs.
    """
    cost = UNIT_COSTS[unit_type]
    if _balances[team] < cost:
        raise ValueError(
            f"{team} cannot afford {unit_type}: balance {_balances[team]} < cost {cost}"
        )
    _balances[team] -= cost
    _pending[team][unit_type] += 1


def get_pending(team: Team) -> UnitCounts:
    """Return a copy of *team*'s pending purchase queue."""
    return dict(_pending[team])
