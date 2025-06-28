"""
InventoryWindow 型定義

インベントリウィンドウに関する型定義
"""

from enum import Enum
from typing import Dict, Any, Optional, List, Callable, Tuple
from dataclasses import dataclass


class InventoryType(Enum):
    """インベントリタイプ"""
    CHARACTER = "character"  # キャラクター個人のインベントリ
    PARTY = "party"         # パーティ共有のインベントリ
    SHOP = "shop"          # 商店のインベントリ
    STORAGE = "storage"    # 倉庫のインベントリ


class ItemCategory(Enum):
    """アイテムカテゴリ"""
    ALL = "all"
    WEAPON = "weapon"
    ARMOR = "armor"
    CONSUMABLE = "consumable"
    MISC = "misc"
    QUEST = "quest"
    MATERIAL = "material"


class ItemActionType(Enum):
    """アイテムアクションタイプ"""
    USE = "use"
    EQUIP = "equip"
    UNEQUIP = "unequip"
    DROP = "drop"
    TRANSFER = "transfer"
    SPLIT = "split"
    EXAMINE = "examine"
    REPAIR = "repair"
    SELL = "sell"


@dataclass
class ItemSlotInfo:
    """アイテムスロット情報"""
    slot_index: int
    item: Optional[Any]  # Item object
    quantity: int = 0
    is_equipped: bool = False
    is_locked: bool = False
    is_quick_slot: bool = False
    quick_slot_index: Optional[int] = None


@dataclass
class InventoryConfig:
    """インベントリ設定"""
    inventory_type: str
    inventory: Any  # Inventory object
    character: Optional[Any] = None  # Character object
    party: Optional[Any] = None      # Party object
    weight_limit: Optional[float] = None
    allow_sorting: bool = True
    allow_dropping: bool = True
    enable_filtering: bool = True
    enable_quick_slots: bool = False
    quick_slot_count: int = 4
    columns_per_row: int = 5
    show_weight: bool = True
    show_value: bool = True
    show_item_count: bool = True
    target_inventory: Optional[Any] = None  # For transfers
    
    def validate(self) -> None:
        """設定の妥当性をチェック"""
        if not self.inventory_type:
            raise ValueError("Inventory config must contain 'inventory_type'")
        if self.inventory is None:
            raise ValueError("Inventory config must contain 'inventory'")
        
        # タイプに応じた追加検証
        inv_type = InventoryType(self.inventory_type)
        if inv_type == InventoryType.CHARACTER and not self.character:
            raise ValueError("Character inventory requires 'character'")
        elif inv_type == InventoryType.PARTY and not self.party:
            raise ValueError("Party inventory requires 'party'")


@dataclass
class InventoryStats:
    """インベントリ統計情報"""
    total_items: int
    total_weight: float
    total_value: int
    used_slots: int
    total_slots: int
    weight_limit: Optional[float] = None
    
    @property
    def weight_percentage(self) -> float:
        """重量使用率を取得"""
        if self.weight_limit and self.weight_limit > 0:
            return (self.total_weight / self.weight_limit) * 100.0
        return 0.0
    
    @property
    def capacity_percentage(self) -> float:
        """容量使用率を取得"""
        if self.total_slots > 0:
            return (self.used_slots / self.total_slots) * 100.0
        return 0.0
    
    @property
    def is_overweight(self) -> bool:
        """重量超過かどうか"""
        if self.weight_limit:
            return self.total_weight > self.weight_limit
        return False


@dataclass
class ItemAction:
    """アイテムアクション"""
    action_type: ItemActionType
    label: str
    enabled: bool = True
    hotkey: Optional[int] = None  # pygame key constant
    callback: Optional[Callable] = None
    requires_target: bool = False
    confirm_required: bool = False


@dataclass
class InventoryLayout:
    """インベントリレイアウト"""
    window_width: int = 800
    window_height: int = 600
    slot_size: int = 64
    slot_spacing: int = 8
    grid_padding: int = 20
    detail_panel_width: int = 300
    stats_panel_height: int = 80
    action_button_height: int = 32
    
    def calculate_grid_size(self, total_slots: int, columns_per_row: int) -> Tuple[int, int]:
        """グリッドサイズを計算"""
        rows = (total_slots + columns_per_row - 1) // columns_per_row
        return (columns_per_row, rows)
    
    def calculate_grid_position(self, slot_index: int, columns_per_row: int) -> Tuple[int, int]:
        """スロットのグリッド位置を計算"""
        row = slot_index // columns_per_row
        col = slot_index % columns_per_row
        
        x = self.grid_padding + col * (self.slot_size + self.slot_spacing)
        y = self.grid_padding + self.stats_panel_height + row * (self.slot_size + self.slot_spacing)
        
        return (x, y)


@dataclass
class QuickSlotAssignment:
    """クイックスロット割り当て"""
    quick_slot_index: int
    inventory_slot_index: int
    item_id: Optional[str] = None
    hotkey: Optional[int] = None  # pygame key constant


@dataclass
class InventoryFilter:
    """インベントリフィルター"""
    category: ItemCategory = ItemCategory.ALL
    search_text: str = ""
    show_equipped: bool = True
    show_unidentified: bool = True
    min_value: Optional[int] = None
    max_weight: Optional[float] = None
    
    def matches_item(self, item: Any) -> bool:
        """アイテムがフィルターに一致するかチェック"""
        # カテゴリチェック
        if self.category != ItemCategory.ALL:
            if hasattr(item, 'category') and item.category != self.category.value:
                return False
        
        # 検索テキストチェック
        if self.search_text:
            item_name = getattr(item, 'name', '').lower()
            if self.search_text.lower() not in item_name:
                return False
        
        # 装備品チェック
        if not self.show_equipped and hasattr(item, 'is_equipped') and item.is_equipped:
            return False
        
        # 未鑑定チェック
        if not self.show_unidentified and hasattr(item, 'is_identified') and not item.is_identified:
            return False
        
        # 価値チェック
        if self.min_value is not None:
            item_value = getattr(item, 'value', 0)
            if item_value < self.min_value:
                return False
        
        # 重量チェック
        if self.max_weight is not None:
            item_weight = getattr(item, 'weight', 0.0)
            if item_weight > self.max_weight:
                return False
        
        return True


# ソート関数の型定義
ItemSortFunction = Callable[[Any], Any]
SlotComparator = Callable[[ItemSlotInfo, ItemSlotInfo], int]

# コールバック型定義
ItemActionCallback = Callable[[int, ItemActionType], None]
SlotSelectionCallback = Callable[[int], None]
ItemTransferCallback = Callable[[int, InventoryType, InventoryType], bool]