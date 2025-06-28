"""
EquipmentManager クラス

装備ロジックと管理

Fowler式リファクタリング：Extract Class パターン
"""

from typing import Dict, List, Any, Optional, Tuple
from src.ui.window_system.equipment_types import (
    EquipmentSlotType, EquipmentSlotInfo, EquipmentActionType, 
    CharacterStats, EquipmentFilter, EquipmentComparison,
    EquipmentValidationResult, QuickSlotAssignment
)
from src.utils.logger import logger


class EquipmentManager:
    """
    装備管理クラス
    
    装備ロジック、アイテム操作、統計計算を担当
    """
    
    def __init__(self, character: Any, equipment_slots: Any, inventory: Any):
        """
        装備マネージャーを初期化
        
        Args:
            character: キャラクター
            equipment_slots: 装備スロット
            inventory: インベントリ
        """
        self.character = character
        self.equipment_slots = equipment_slots
        self.inventory = inventory
        self.selected_slot: Optional[str] = None
        self.quick_slots: Dict[int, str] = {}
        self.filter = EquipmentFilter()
        
        logger.debug("EquipmentManagerを初期化")
    
    def get_slot_info(self, slot_type: str) -> Optional[EquipmentSlotInfo]:
        """スロット情報を取得"""
        if hasattr(self.equipment_slots, 'get_slot'):
            slot = self.equipment_slots.get_slot(slot_type)
            if slot:
                return EquipmentSlotInfo(
                    slot_type=EquipmentSlotType(slot_type),
                    item=getattr(slot, 'item', None),
                    is_equipped=getattr(slot, 'is_equipped', False),
                    is_locked=getattr(slot, 'is_locked', False)
                )
        return None
    
    def get_all_slot_infos(self) -> Dict[str, EquipmentSlotInfo]:
        """全スロット情報を取得"""
        slot_infos = {}
        if hasattr(self.equipment_slots, 'get_all_slots'):
            all_slots = self.equipment_slots.get_all_slots()
            if hasattr(all_slots, 'items'):
                for slot_type, slot_data in all_slots.items():
                    slot_info = EquipmentSlotInfo(
                        slot_type=EquipmentSlotType(slot_type),
                        item=getattr(slot_data, 'item', None),
                        is_equipped=getattr(slot_data, 'is_equipped', False),
                        is_locked=getattr(slot_data, 'is_locked', False)
                    )
                    slot_infos[slot_type] = slot_info
        
        return slot_infos
    
    def select_slot(self, slot_type: str) -> bool:
        """スロットを選択"""
        slot_info = self.get_slot_info(slot_type)
        if slot_info:
            self.selected_slot = slot_type
            logger.debug(f"スロット選択: {slot_type}")
            return True
        return False
    
    def get_selected_slot_info(self) -> Optional[EquipmentSlotInfo]:
        """選択されたスロットの情報を取得"""
        if self.selected_slot:
            return self.get_slot_info(self.selected_slot)
        return None
    
    def can_equip_item(self, item: Any, slot_type: str) -> bool:
        """アイテムが装備可能かチェック"""
        if not item:
            return False
        
        # 基本的な装備可能性チェック
        if hasattr(self.equipment_slots, 'can_equip'):
            return self.equipment_slots.can_equip(item, slot_type)
        
        return True
    
    def equip_item(self, item: Any, slot_type: str) -> bool:
        """アイテムを装備"""
        if not self.can_equip_item(item, slot_type):
            return False
        
        if hasattr(self.equipment_slots, 'equip_item'):
            self.equipment_slots.equip_item(item, slot_type)
            logger.debug(f"アイテム装備: {item} -> {slot_type}")
            return True
        
        return False
    
    def unequip_item(self, slot_type: str) -> bool:
        """アイテムを装備解除"""
        slot_info = self.get_slot_info(slot_type)
        if not slot_info or not slot_info.item:
            return False
        
        if hasattr(self.equipment_slots, 'unequip_item'):
            self.equipment_slots.unequip_item(slot_type)
            logger.debug(f"アイテム装備解除: {slot_type}")
            return True
        
        return False
    
    def swap_equipment(self, from_slot: str, to_slot: str) -> bool:
        """装備をスワップ"""
        if hasattr(self.equipment_slots, 'swap_equipment'):
            self.equipment_slots.swap_equipment(from_slot, to_slot)
            logger.debug(f"装備スワップ: {from_slot} <-> {to_slot}")
            return True
        
        return False
    
    def calculate_character_stats(self) -> CharacterStats:
        """キャラクター統計を計算"""
        if hasattr(self.character, 'get_total_stats'):
            total_stats = self.character.get_total_stats()
            return CharacterStats(total_stats=total_stats)
        
        return CharacterStats()
    
    def get_equippable_items(self, slot_type: Optional[str] = None) -> List[Any]:
        """装備可能なアイテム一覧を取得"""
        items = []
        
        if hasattr(self.inventory, 'get_items_by_category'):
            all_items = self.inventory.get_items_by_category('equipment')
            
            for item in all_items:
                if slot_type:
                    # 特定スロットタイプでフィルタリング
                    if hasattr(item, 'equipment_slot') and item.equipment_slot == slot_type:
                        if self.filter.matches_item(item):
                            items.append(item)
                else:
                    # 全装備品
                    if self.filter.matches_item(item):
                        items.append(item)
        
        return items
    
    def apply_filter(self, filter_obj: EquipmentFilter) -> None:
        """フィルターを適用"""
        self.filter = filter_obj
        logger.debug(f"フィルター適用: {filter_obj.slot_type}")
    
    def create_comparison(self, current_item: Any, new_item: Any) -> EquipmentComparison:
        """装備比較情報を作成"""
        comparison = EquipmentComparison(
            current_item=current_item,
            new_item=new_item
        )
        
        # ステータス差分を計算
        if hasattr(current_item, 'stats') and hasattr(new_item, 'stats'):
            for stat_name in new_item.stats:
                current_value = getattr(current_item.stats, stat_name, 0)
                new_value = getattr(new_item.stats, stat_name, 0)
                comparison.stat_differences[stat_name] = new_value - current_value
            
            # 全体的な改善かどうか判定
            comparison.overall_improvement = sum(comparison.stat_differences.values()) > 0
        
        return comparison
    
    def assign_quick_slot(self, slot_type: str, quick_slot_index: int) -> bool:
        """クイックスロットに割り当て"""
        slot_info = self.get_slot_info(slot_type)
        if slot_info and slot_info.item:
            self.quick_slots[quick_slot_index] = slot_type
            logger.debug(f"クイックスロット割り当て: {slot_type} -> {quick_slot_index}")
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
        
        for quick_index, slot_type in self.quick_slots.items():
            slot_info = self.get_slot_info(slot_type)
            assignment = QuickSlotAssignment(
                slot_index=quick_index,
                item_id=getattr(slot_info.item, 'item_id', None) if slot_info and slot_info.item else None,
                slot_type=EquipmentSlotType(slot_type)
            )
            assignments.append(assignment)
        
        return assignments
    
    def validate_equipment_state(self) -> List[str]:
        """装備状態の検証"""
        errors = []
        
        # 基本的な整合性チェック
        slot_infos = self.get_all_slot_infos()
        
        for slot_type, slot_info in slot_infos.items():
            if slot_info.item and slot_info.is_equipped:
                # 装備品の要件チェック
                if hasattr(slot_info.item, 'required_level') and hasattr(self.character, 'level'):
                    if self.character.level < slot_info.item.required_level:
                        errors.append(f"スロット {slot_type}: レベル不足")
        
        # クイックスロットの整合性チェック
        for quick_index, slot_type in self.quick_slots.items():
            slot_info = self.get_slot_info(slot_type)
            if not slot_info or not slot_info.item:
                errors.append(f"クイックスロット {quick_index}: 無効なスロット参照")
        
        return errors
    
    def get_manager_summary(self) -> Dict[str, Any]:
        """マネージャーサマリーを取得"""
        stats = self.calculate_character_stats()
        errors = self.validate_equipment_state()
        
        return {
            'character': self.character,
            'selected_slot': self.selected_slot,
            'quick_slots_count': len(self.quick_slots),
            'filter_slot_type': self.filter.slot_type.value if self.filter.slot_type else None,
            'character_stats': stats.total_stats,
            'validation_errors': errors
        }