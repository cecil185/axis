"""
Execute actions: skip() and attack(target_id). Skip ends turn; attack validates, invokes combat hook, then ends turn.
"""

from typing import Callable

from .territory import TerritoryId
from .state import end_turn
from .valid_actions import valid_attack_targets

# Combat hook: callable(target_id) invoked when attack(target_id) is valid. No dice/ownership in this module.
_combat_hook: Callable[[TerritoryId], None] | None = None


def set_combat_hook(hook: Callable[[TerritoryId], None] | None) -> None:
    """Set the combat callback (for tests or game). Called with target territory ID on valid attack."""
    global _combat_hook
    _combat_hook = hook


def skip() -> None:
    """End turn only; no combat."""
    end_turn()


def attack(target_id: TerritoryId) -> None:
    """Validate target is in valid_attack_targets(); if invalid raise ValueError. If valid, invoke combat hook then end turn."""
    valid = valid_attack_targets()
    if target_id not in valid:
        raise ValueError(f"Invalid attack target: {target_id}; valid targets: {valid}")
    if _combat_hook is not None:
        _combat_hook(target_id)
    end_turn()
