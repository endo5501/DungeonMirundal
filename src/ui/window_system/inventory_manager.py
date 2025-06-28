"""
InventoryManager クラス

インベントリロジックとアイテム管理

Fowler式リファクタリング：Extract Class パターン
"""

from typing import Dict, List, Any, Optional, Tuple
from src.ui.window_system.inventory_types import (
    InventoryType, ItemSlotInfo, ItemCategory, ItemActionType, 
    InventoryStats, InventoryFilter, QuickSlotAssignment
)
from src.utils.logger import logger


class InventoryManager:
    """
    インベントリ管理クラス
    
    インベントリロジック、アイテム操作、統計計算を担当
    """
    
    def __init__(self, inventory_type: InventoryType, inventory: Any):
        """
        インベントリマネージャーを初期化
        
        Args:
            inventory_type: インベントリタイプ
            inventory: インベントリオブジェクト
        """
        self.inventory_type = inventory_type
        self.inventory = inventory
        self.selected_slot_index: Optional[int] = None
        self.quick_slots: Dict[int, int] = {}
        self.filter = InventoryFilter()
        
        logger.debug(f"InventoryManagerを初期化: {inventory_type}")
    
    def get_slot_info(self, slot_index: int) -> ItemSlotInfo:
        """スロット情報を取得"""
        if hasattr(self.inventory, 'slots') and slot_index < len(self.inventory.slots):
            slot = self.inventory.slots[slot_index]
            return ItemSlotInfo(
                slot_index=slot_index,
                item=getattr(slot, 'item', None),
                quantity=getattr(slot, 'quantity', 0),
                is_equipped=getattr(slot, 'is_equipped', False),
                is_locked=getattr(slot, 'is_locked', False),
                is_quick_slot=slot_index in self.quick_slots.values(),
                quick_slot_index=self._get_quick_slot_index(slot_index)
            )
        
        return ItemSlotInfo(slot_index=slot_index, item=None)
    
    def _get_quick_slot_index(self, slot_index: int) -> Optional[int]:
        """スロットのクイックスロットインデックスを取得"""
        for quick_index, inventory_index in self.quick_slots.items():
            if inventory_index == slot_index:
                return quick_index
        return None
    
    def select_slot(self, slot_index: int) -> bool:
        """スロットを選択"""
        total_slots = self.get_total_slots()
        if 0 <= slot_index < total_slots:
            self.selected_slot_index = slot_index
            logger.debug(f"スロット選択: {slot_index}")
            return True
        return False
    
    def get_selected_slot_info(self) -> Optional[ItemSlotInfo]:
        """選択されたスロットの情報を取得"""
        if self.selected_slot_index is not None:
            return self.get_slot_info(self.selected_slot_index)
        return None
    
    def move_selection(self, dx: int, dy: int, columns_per_row: int) -> bool:
        """選択を移動"""
        if self.selected_slot_index is None:
            return False
        
        total_slots = self.get_total_slots()
        current_row = self.selected_slot_index // columns_per_row
        current_col = self.selected_slot_index % columns_per_row
        
        new_col = current_col + dx
        new_row = current_row + dy
        
        # 境界チェック
        if new_col < 0 or new_col >= columns_per_row:
            return False
        if new_row < 0:
            return False
        
        new_index = new_row * columns_per_row + new_col
        if new_index >= total_slots:
            return False
        
        self.selected_slot_index = new_index
        logger.debug(f"選択移動: {self.selected_slot_index}")
        return True
    
    def can_use_item(self, slot_index: int) -> bool:
        """アイテムが使用可能かチェック"""
        slot_info = self.get_slot_info(slot_index)
        if not slot_info.item:
            return False
        
        # 消耗品は使用可能
        if hasattr(slot_info.item, 'is_consumable') and slot_info.item.is_consumable():
            return True
        
        # 装備品は装備状態によって使用可能（装備/装備解除）
        if hasattr(slot_info.item, 'is_equippable') and slot_info.item.is_equippable():
            return True
        
        return False
    
    def can_equip_item(self, slot_index: int) -> bool:
        """アイテムが装備可能かチェック"""
        slot_info = self.get_slot_info(slot_index)
        if not slot_info.item:
            return False
        
        if hasattr(slot_info.item, 'is_equippable'):
            return slot_info.item.is_equippable() and not slot_info.is_equipped
        
        return False
    
    def can_drop_item(self, slot_index: int) -> bool:
        """アイテムが破棄可能かチェック"""
        slot_info = self.get_slot_info(slot_index)
        if not slot_info.item:
            return False
        
        # 装備中またはロックされたアイテムは破棄不可
        if slot_info.is_equipped or slot_info.is_locked:
            return False
        
        # クエストアイテムは破棄不可
        if hasattr(slot_info.item, 'is_quest_item') and slot_info.item.is_quest_item():
            return False
        
        return True
    
    def move_item(self, from_slot: int, to_slot: int) -> bool:
        """アイテムを移動"""
        if hasattr(self.inventory, 'can_move_item') and hasattr(self.inventory, 'move_item'):
            if self.inventory.can_move_item(from_slot, to_slot):
                self.inventory.move_item(from_slot, to_slot)
                logger.debug(f"アイテム移動: {from_slot} -> {to_slot}")
                return True
        
        return False
    
    def sort_items(self) -> bool:
        """アイテムをソート"""
        if hasattr(self.inventory, 'sort_items'):
            self.inventory.sort_items()
            logger.debug("インベントリソート実行")
            return True
        
        return False
    
    def calculate_stats(self, weight_limit: Optional[float] = None) -> InventoryStats:
        """インベントリ統計を計算"""
        total_items = 0
        total_weight = 0.0
        total_value = 0
        used_slots = 0
        
        if hasattr(self.inventory, 'slots'):
            for slot in self.inventory.slots:
                if hasattr(slot, 'item') and slot.item:
                    used_slots += 1
                    quantity = getattr(slot, 'quantity', 1)
                    if isinstance(quantity, int):
                        total_items += quantity
                    
                    if hasattr(slot.item, 'weight'):
                        weight = slot.item.weight
                        if isinstance(weight, (int, float)) and isinstance(quantity, int):
                            total_weight += weight * quantity
                    
                    if hasattr(slot.item, 'value'):
                        value = slot.item.value
                        if isinstance(value, int) and isinstance(quantity, int):
                            total_value += value * quantity
        
        total_slots = self.get_total_slots()
        
        return InventoryStats(
            total_items=total_items,
            total_weight=total_weight,
            total_value=total_value,
            used_slots=used_slots,
            total_slots=total_slots,
            weight_limit=weight_limit
        )
    
    def get_total_slots(self) -> int:
        """総スロット数を取得"""
        if hasattr(self.inventory, 'capacity'):
            capacity = self.inventory.capacity
            return capacity if isinstance(capacity, int) else 0
        elif hasattr(self.inventory, 'slots'):
            return len(self.inventory.slots)
        return 0
    
    def get_filtered_slots(self) -> List[int]:
        """フィルター適用後のスロット一覧を取得"""
        filtered_slots = []
        
        if hasattr(self.inventory, 'slots'):
            for i, slot in enumerate(self.inventory.slots):
                if hasattr(slot, 'item') and slot.item:
                    if self.filter.matches_item(slot.item):
                        filtered_slots.append(i)
                elif self.filter.category == ItemCategory.ALL:
                    # 空スロットは「全て」フィルターの場合のみ表示
                    filtered_slots.append(i)
        
        return filtered_slots
    
    def apply_filter(self, filter_obj: InventoryFilter) -> None:
        """フィルターを適用"""
        self.filter = filter_obj
        logger.debug(f"フィルター適用: {filter_obj.category}")
    
    def assign_quick_slot(self, inventory_slot: int, quick_slot_index: int) -> bool:
        """クイックスロットに割り当て"""
        slot_info = self.get_slot_info(inventory_slot)
        if slot_info.item:
            self.quick_slots[quick_slot_index] = inventory_slot
            logger.debug(f"クイックスロット割り当て: スロット {inventory_slot} -> クイック {quick_slot_index}")
            return True
        
        return False
    
    def remove_quick_slot(self, quick_slot_index: int) -> bool:
        """クイックスロットから削除"""
        if quick_slot_index in self.quick_slots:
            del self.quick_slots[quick_slot_index]
            logger.debug(f"クイックスロット削除: {quick_slot_index}")
            return True
        
        return False
    
    def get_quick_slot_assignments(self) -> List[QuickSlotAssignment]:
        """クイックスロット割り当て一覧を取得"""
        assignments = []
        
        for quick_index, inventory_index in self.quick_slots.items():
            slot_info = self.get_slot_info(inventory_index)
            assignment = QuickSlotAssignment(
                quick_slot_index=quick_index,
                inventory_slot_index=inventory_index,
                item_id=getattr(slot_info.item, 'item_id', None) if slot_info.item else None
            )
            assignments.append(assignment)
        
        return assignments
    
    def validate_inventory_state(self) -> List[str]:
        """インベントリ状態の検証"""
        errors = []
        
        # 基本的な整合性チェック
        if not hasattr(self.inventory, 'slots'):
            errors.append("インベントリにslotsが定義されていません")
            return errors
        
        total_slots = self.get_total_slots()
        actual_slots = len(self.inventory.slots)
        
        if total_slots != actual_slots:
            errors.append(f"スロット数の不整合: capacity={total_slots}, actual={actual_slots}")
        
        # スロットの整合性チェック
        for i, slot in enumerate(self.inventory.slots):
            if hasattr(slot, 'item') and slot.item:
                quantity = getattr(slot, 'quantity', 1)
                if not isinstance(quantity, int) or quantity <= 0:
                    errors.append(f"スロット {i}: 無効な数量 {quantity}")
        
        # クイックスロットの整合性チェック
        for quick_index, inventory_index in self.quick_slots.items():
            if inventory_index >= total_slots:
                errors.append(f"クイックスロット {quick_index}: 無効なインベントリインデックス {inventory_index}")
            else:
                slot_info = self.get_slot_info(inventory_index)
                if not slot_info.item:
                    errors.append(f"クイックスロット {quick_index}: 空のスロットを参照")
        
        return errors
    
    def get_manager_summary(self) -> Dict[str, Any]:
        """マネージャーサマリーを取得"""
        stats = self.calculate_stats()
        errors = self.validate_inventory_state()
        
        return {
            'inventory_type': self.inventory_type.value,
            'total_slots': stats.total_slots,
            'used_slots': stats.used_slots,
            'selected_slot': self.selected_slot_index,
            'quick_slots_count': len(self.quick_slots),
            'filter_category': self.filter.category.value,
            'total_weight': stats.total_weight,
            'total_value': stats.total_value,
            'validation_errors': errors
        }