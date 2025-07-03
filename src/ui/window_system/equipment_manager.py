"""
EquipmentManager クラス - EquipmentOperationHandler統合版

装備ロジックと管理

Fowler式リファクタリング：Extract Class パターン
EquipmentOperationHandlerへの委譲による重複解消
"""

from typing import Dict, List, Any, Optional, Tuple
from src.ui.window_system.equipment_types import (
    EquipmentSlotType, EquipmentSlotInfo, EquipmentActionType, 
    CharacterStats, EquipmentFilter, EquipmentComparison,
    EquipmentValidationResult, QuickSlotAssignment
)
from src.equipment.equipment_operation_handler import EquipmentOperationHandler
from src.utils.logger import logger


class EquipmentManager:
    """
    装備管理クラス - EquipmentOperationHandler統合版
    
    装備ロジック、アイテム操作、統計計算を担当
    EquipmentOperationHandlerに実際の処理を委譲し、重複を解消
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
        self.filter = EquipmentFilter()
        
        # EquipmentOperationHandlerに処理を委譲
        self.operation_handler = EquipmentOperationHandler(
            character=character,
            equipment_slots=equipment_slots,
            inventory=inventory
        )
        
        logger.debug("EquipmentManager初期化（EquipmentOperationHandler統合版）")
    
    def get_slot_info(self, slot_type: str) -> Optional[EquipmentSlotInfo]:
        """スロット情報を取得 - EquipmentOperationHandler委譲版"""
        result = self.operation_handler.execute_equipment_operation('get_slot_info', slot_type=slot_type)
        if result.success and result.data:
            # EquipmentOperationHandlerの結果をEquipmentSlotInfo形式に変換
            slot_data = result.data
            return EquipmentSlotInfo(
                slot_type=EquipmentSlotType(slot_data.get('slot_type', slot_type)),
                item=slot_data.get('item'),
                is_equipped=not slot_data.get('is_empty', True),
                is_locked=False  # デフォルト値
            )
        return None
    
    def get_all_slot_infos(self) -> Dict[str, EquipmentSlotInfo]:
        """全スロット情報を取得 - EquipmentOperationHandler委譲版"""
        result = self.operation_handler.execute_equipment_operation('get_all_slots')
        slot_infos = {}
        
        if result.success and result.data:
            for slot_type, slot_data in result.data.items():
                slot_info = EquipmentSlotInfo(
                    slot_type=EquipmentSlotType(slot_type),
                    item=slot_data.get('item') if slot_data else None,
                    is_equipped=not slot_data.get('is_empty', True) if slot_data else False,
                    is_locked=False  # デフォルト値
                )
                slot_infos[slot_type] = slot_info
        
        return slot_infos
    
    def select_slot(self, slot_type: str) -> bool:
        """スロットを選択"""
        slot_info = self.get_slot_info(slot_type)
        if slot_info:
            self.operation_handler.selected_slot = slot_type
            logger.debug(f"スロット選択: {slot_type}")
            return True
        return False
    
    def get_selected_slot_info(self) -> Optional[EquipmentSlotInfo]:
        """選択されたスロットの情報を取得"""
        if self.operation_handler.selected_slot:
            return self.get_slot_info(self.operation_handler.selected_slot)
        return None
    
    def can_equip_item(self, item: Any, slot_type: str) -> bool:
        """アイテムが装備可能かチェック - EquipmentOperationHandler委譲版"""
        # EquipmentOperationHandlerの内部メソッドを利用
        can_equip_result = self.operation_handler._can_equip_item(item, slot_type)
        return can_equip_result.success
    
    def equip_item(self, item: Any, slot_type: str) -> bool:
        """アイテムを装備 - EquipmentOperationHandler委譲版"""
        result = self.operation_handler.execute_equipment_operation('equip_item', item=item, slot_type=slot_type)
        return result.success
    
    def unequip_item(self, slot_type: str) -> bool:
        """アイテムを装備解除 - EquipmentOperationHandler委譲版"""
        result = self.operation_handler.execute_equipment_operation('unequip_item', slot_type=slot_type)
        return result.success
    
    def swap_equipment(self, from_slot: str, to_slot: str) -> bool:
        """装備をスワップ - EquipmentOperationHandler委譲版"""
        result = self.operation_handler.execute_equipment_operation('swap_equipment', from_slot=from_slot, to_slot=to_slot)
        return result.success
    
    def calculate_character_stats(self) -> CharacterStats:
        """キャラクター統計を計算"""
        if hasattr(self.character, 'get_total_stats'):
            total_stats = self.character.get_total_stats()
            return CharacterStats(total_stats=total_stats)
        
        return CharacterStats()
    
    def get_equippable_items(self, slot_type: Optional[str] = None) -> List[Any]:
        """装備可能なアイテム一覧を取得 - EquipmentOperationHandler委譲版"""
        result = self.operation_handler.execute_equipment_operation('get_equippable_items', slot_type=slot_type)
        if result.success and result.data:
            # フィルターを適用
            items = result.data.get('items', [])
            filtered_items = [item for item in items if self.filter.matches_item(item)]
            return filtered_items
        return []
    
    def apply_filter(self, filter_obj: EquipmentFilter) -> None:
        """フィルターを適用"""
        self.filter = filter_obj
        logger.debug(f"フィルター適用: {filter_obj.slot_type}")
    
    def create_comparison(self, current_item: Any, new_item: Any) -> EquipmentComparison:
        """装備比較情報を作成 - EquipmentOperationHandler委譲版"""
        # スロットタイプを判定（簡単なロジック）
        slot_type = 'weapon'  # デフォルト
        if hasattr(new_item, 'equipment_slot'):
            slot_type = new_item.equipment_slot
        
        result = self.operation_handler.execute_equipment_operation(
            'create_comparison', 
            item=new_item, 
            slot_type=slot_type
        )
        
        if result.success and result.data:
            comparison_data = result.data
            comparison = EquipmentComparison(
                current_item=comparison_data.get('current_item'),
                new_item=comparison_data.get('new_item')
            )
            comparison.stat_differences = comparison_data.get('stat_differences', {})
            comparison.overall_improvement = sum(comparison.stat_differences.values()) > 0
            return comparison
        
        # フォールバック
        return EquipmentComparison(current_item=current_item, new_item=new_item)
    
    def assign_quick_slot(self, slot_type: str, quick_slot_index: int) -> bool:
        """クイックスロットに割り当て - EquipmentOperationHandler委譲版"""
        result = self.operation_handler.execute_equipment_operation(
            'assign_quick_slot', 
            quick_slot_index=quick_slot_index, 
            slot_type=slot_type
        )
        return result.success
    
    def remove_quick_slot(self, quick_slot_index: int) -> bool:
        """クイックスロットから削除"""
        if quick_slot_index in self.operation_handler.quick_slots:
            del self.operation_handler.quick_slots[quick_slot_index]
            logger.debug(f"クイックスロット削除: {quick_slot_index}")
            return True
        
        return False
    
    def get_quick_slot_assignments(self) -> List[QuickSlotAssignment]:
        """クイックスロット割り当て一覧を取得"""
        assignments = []
        
        for quick_index, slot_type in self.operation_handler.quick_slots.items():
            slot_info = self.get_slot_info(slot_type)
            assignment = QuickSlotAssignment(
                slot_index=quick_index,
                item_id=getattr(slot_info.item, 'item_id', None) if slot_info and slot_info.item else None,
                slot_type=EquipmentSlotType(slot_type)
            )
            assignments.append(assignment)
        
        return assignments
    
    def validate_equipment_state(self) -> List[str]:
        """装備状態の検証 - EquipmentOperationHandler委譲版"""
        result = self.operation_handler.execute_equipment_operation('validate_equipment')
        
        if result.success and result.data:
            validation_results = result.data.get('results', [])
            errors = []
            for validation in validation_results:
                if not validation.get('valid', True):
                    errors.extend(validation.get('messages', []))
            
            # クイックスロットの整合性チェック
            for quick_index, slot_type in self.operation_handler.quick_slots.items():
                slot_info = self.get_slot_info(slot_type)
                if not slot_info or not slot_info.item:
                    errors.append(f"クイックスロット {quick_index}: 無効なスロット参照")
            
            return errors
        
        return []
    
    def get_manager_summary(self) -> Dict[str, Any]:
        """マネージャーサマリーを取得"""
        stats = self.calculate_character_stats()
        errors = self.validate_equipment_state()
        
        return {
            'character': self.character,
            'selected_slot': self.operation_handler.selected_slot,
            'quick_slots_count': len(self.operation_handler.quick_slots),
            'filter_slot_type': self.filter.slot_type.value if self.filter.slot_type else None,
            'character_stats': stats.total_stats,
            'validation_errors': errors
        }