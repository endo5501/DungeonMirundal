"""ヘルプシステム共通列挙型

ヘルプシステムで使用される列挙型を定義。
循環インポートを避けるため、独立したモジュールとして分離。
"""

from enum import Enum


class HelpCategory(Enum):
    """ヘルプカテゴリ"""
    BASIC_CONTROLS = "basic_controls"
    DUNGEON_EXPLORATION = "dungeon_exploration"
    COMBAT_SYSTEM = "combat_system"
    MAGIC_SYSTEM = "magic_system"
    EQUIPMENT_SYSTEM = "equipment_system"
    INVENTORY_MANAGEMENT = "inventory_management"
    CHARACTER_DEVELOPMENT = "character_development"
    OVERWORLD_NAVIGATION = "overworld_navigation"


class HelpContext(Enum):
    """ヘルプコンテキスト"""
    COMBAT = "combat"
    DUNGEON = "dungeon"
    OVERWORLD = "overworld"
    INVENTORY = "inventory"
    EQUIPMENT = "equipment"
    MAGIC = "magic"