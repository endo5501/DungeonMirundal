"""
Equipment関連の型定義

装備システムの型安全性を保証
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Any, Optional, Union


class EquipmentSlotType(Enum):
    """装備スロットタイプ"""
    WEAPON = "weapon"
    ARMOR = "armor"
    HELMET = "helmet"
    SHIELD = "shield"
    GLOVES = "gloves"
    BOOTS = "boots"
    ACCESSORY = "accessory"
    RING = "ring"
    NECKLACE = "necklace"


class EquipmentActionType(Enum):
    """装備アクションタイプ"""
    EQUIP = "equip"
    UNEQUIP = "unequip"
    SWAP = "swap"
    EXAMINE = "examine"
    COMPARE = "compare"
    QUICK_EQUIP = "quick_equip"


class StatType(Enum):
    """ステータスタイプ"""
    ATTACK = "attack"
    DEFENSE = "defense"
    MAGIC_ATTACK = "magic_attack"
    MAGIC_DEFENSE = "magic_defense"
    AGILITY = "agility"
    DEXTERITY = "dexterity"
    LUCK = "luck"
    HP = "hp"
    MP = "mp"


@dataclass
class EquipmentSlotInfo:
    """装備スロット情報"""
    slot_type: EquipmentSlotType
    item: Optional[Any] = None
    is_equipped: bool = False
    is_locked: bool = False
    position: tuple = (0, 0)  # UI上の位置
    
    def __post_init__(self):
        if isinstance(self.slot_type, str):
            self.slot_type = EquipmentSlotType(self.slot_type)


@dataclass
class EquipmentAction:
    """装備アクション"""
    action_type: EquipmentActionType
    label: str
    enabled: bool = True
    requires_confirmation: bool = False
    tooltip: str = ""
    
    def __post_init__(self):
        if isinstance(self.action_type, str):
            self.action_type = EquipmentActionType(self.action_type)


@dataclass
class CharacterStats:
    """キャラクター統計"""
    base_stats: Dict[StatType, int] = field(default_factory=dict)
    equipment_bonus: Dict[StatType, int] = field(default_factory=dict)
    total_stats: Dict[StatType, int] = field(default_factory=dict)
    
    def __post_init__(self):
        # 文字列キーを StatType に変換（辞書の場合のみ）
        if self.base_stats and hasattr(self.base_stats, 'keys') and len(self.base_stats) > 0:
            try:
                keys = list(self.base_stats.keys())
                if isinstance(keys[0], str):
                    self.base_stats = {StatType(k): v for k, v in self.base_stats.items()}
            except (TypeError, ValueError):
                pass
        
        if self.equipment_bonus and hasattr(self.equipment_bonus, 'keys') and len(self.equipment_bonus) > 0:
            try:
                keys = list(self.equipment_bonus.keys())
                if isinstance(keys[0], str):
                    self.equipment_bonus = {StatType(k): v for k, v in self.equipment_bonus.items()}
            except (TypeError, ValueError):
                pass
        
        if self.total_stats and hasattr(self.total_stats, 'keys') and len(self.total_stats) > 0:
            try:
                keys = list(self.total_stats.keys())
                if isinstance(keys[0], str):
                    self.total_stats = {StatType(k): v for k, v in self.total_stats.items()}
            except (TypeError, ValueError):
                pass


@dataclass
class EquipmentComparison:
    """装備比較情報"""
    current_item: Optional[Any] = None
    new_item: Optional[Any] = None
    stat_differences: Dict[StatType, int] = field(default_factory=dict)
    overall_improvement: bool = False
    
    def __post_init__(self):
        # 文字列キーを StatType に変換
        if self.stat_differences and isinstance(list(self.stat_differences.keys())[0], str):
            self.stat_differences = {StatType(k): v for k, v in self.stat_differences.items()}


@dataclass
class EquipmentLayout:
    """装備UIレイアウト"""
    slot_size: int = 64
    slot_spacing: int = 10
    panel_padding: int = 20
    detail_panel_width: int = 300
    stats_panel_height: int = 150
    comparison_panel_height: int = 200
    window_min_width: int = 800
    window_min_height: int = 600
    
    def calculate_slot_position(self, slot_type: EquipmentSlotType) -> tuple:
        """スロットタイプに基づいてUI位置を計算"""
        # 人体レイアウトに基づく配置
        positions = {
            EquipmentSlotType.HELMET: (100, 50),
            EquipmentSlotType.NECKLACE: (100, 100),
            EquipmentSlotType.WEAPON: (50, 150),
            EquipmentSlotType.ARMOR: (100, 150),
            EquipmentSlotType.SHIELD: (150, 150),
            EquipmentSlotType.GLOVES: (50, 200),
            EquipmentSlotType.RING: (100, 200),
            EquipmentSlotType.BOOTS: (100, 250),
            EquipmentSlotType.ACCESSORY: (150, 100)
        }
        return positions.get(slot_type, (0, 0))


@dataclass
class EquipmentFilter:
    """装備フィルター"""
    slot_type: Optional[EquipmentSlotType] = None
    min_level: int = 0
    max_level: int = 999
    equipped_only: bool = False
    unequipped_only: bool = False
    search_text: str = ""
    
    def matches_item(self, item: Any) -> bool:
        """アイテムがフィルター条件に一致するかチェック"""
        if not item:
            return False
        
        # スロットタイプフィルター
        if self.slot_type:
            if hasattr(item, 'equipment_slot'):
                item_slot = item.equipment_slot
                if isinstance(item_slot, str):
                    item_slot = EquipmentSlotType(item_slot)
                if item_slot != self.slot_type:
                    return False
        
        # レベルフィルター
        if hasattr(item, 'required_level'):
            if not (self.min_level <= item.required_level <= self.max_level):
                return False
        
        # 検索テキストフィルター
        if self.search_text:
            if hasattr(item, 'name'):
                if self.search_text.lower() not in item.name.lower():
                    return False
        
        return True


@dataclass
class EquipmentConfig:
    """装備ウィンドウ設定"""
    character: Any
    equipment_slots: Any
    inventory: Any
    enable_comparison: bool = True
    enable_quick_equip: bool = True
    enable_auto_sort: bool = True
    show_stat_preview: bool = True
    show_requirements: bool = True
    layout: EquipmentLayout = field(default_factory=EquipmentLayout)
    
    def validate(self) -> None:
        """設定の検証"""
        if not self.character:
            raise ValueError("Character is required")
        if not self.equipment_slots:
            raise ValueError("Equipment slots are required")
        if not self.inventory:
            raise ValueError("Inventory is required")


@dataclass
class EquipmentValidationResult:
    """装備検証結果"""
    can_equip: bool
    reasons: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    stat_changes: Dict[StatType, int] = field(default_factory=dict)
    
    def __post_init__(self):
        # 文字列キーを StatType に変換
        if self.stat_changes and isinstance(list(self.stat_changes.keys())[0], str):
            self.stat_changes = {StatType(k): v for k, v in self.stat_changes.items()}


@dataclass
class QuickSlotAssignment:
    """クイックスロット割り当て"""
    slot_index: int
    item_id: Optional[str] = None
    slot_type: Optional[EquipmentSlotType] = None
    
    def __post_init__(self):
        if isinstance(self.slot_type, str):
            self.slot_type = EquipmentSlotType(self.slot_type)