"""戦闘システム"""

from .combat_manager import (
    CombatManager,
    CombatState,
    CombatAction,
    CombatResult,
    combat_manager
)

__all__ = [
    "CombatManager",
    "CombatState",
    "CombatAction", 
    "CombatResult",
    "combat_manager"
]