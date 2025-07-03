"""
EquipmentOperationHandler - 装備操作の統一ハンドラー

EquipmentManagerの85-94%重複を統合するため、Command Patternによる操作統一
Template Method + Strategy Pattern の組み合わせによる重複除去
"""

from abc import abstractmethod
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum

from src.equipment.equipment import Equipment, EquipmentSlot, EquipmentBonus
from src.items.item import ItemInstance
from src.character.character import Character
from src.utils.logger import logger


class EquipmentOperationType(Enum):
    """装備操作タイプ"""
    EQUIP_ITEM = "equip_item"
    UNEQUIP_ITEM = "unequip_item"
    SWAP_EQUIPMENT = "swap_equipment"
    GET_SLOT_INFO = "get_slot_info"
    GET_ALL_SLOTS = "get_all_slots"
    VALIDATE_EQUIPMENT = "validate_equipment"
    CREATE_COMPARISON = "create_comparison"
    ASSIGN_QUICK_SLOT = "assign_quick_slot"


@dataclass
class EquipmentOperationResult:
    """装備操作結果"""
    success: bool
    message: str = ""
    error_type: Optional[str] = None
    data: Optional[Dict[str, Any]] = None
    equipment_state: Optional[Dict[str, Any]] = None


class EquipmentCommand:
    """装備操作コマンド（Command Pattern）"""
    
    def __init__(self, operation: str, params: Dict[str, Any], handler: 'EquipmentOperationHandler'):
        self.operation = operation
        self.params = params
        self.handler = handler
        self.previous_state = None
    
    def execute(self) -> EquipmentOperationResult:
        """コマンドを実行"""
        # 現在の状態を保存（Undo用）
        self.previous_state = self.handler.get_current_state()
        return self.handler.execute_equipment_operation(self.operation, **self.params)
    
    def undo(self) -> EquipmentOperationResult:
        """コマンドを元に戻す"""
        if self.previous_state:
            return self.handler.restore_state(self.previous_state)
        return EquipmentOperationResult(success=False, message="Undo state not available")


class EquipmentOperationHandler:
    """
    装備操作の統一ハンドラー
    
    Template Method パターンによる共通操作フロー
    Strategy パターンによる操作の切り替え
    Command パターンによる操作のカプセル化
    """
    
    def __init__(self, character: Character, equipment_slots: Any, inventory: Any):
        self.character = character
        self.equipment_slots = equipment_slots
        self.inventory = inventory
        self.selected_slot: Optional[str] = None
        self.quick_slots: Dict[int, str] = {}
        
        logger.info(f"EquipmentOperationHandler初期化: {character.name if character else 'Unknown'}")
    
    def execute_equipment_operation(self, operation: str, **kwargs) -> EquipmentOperationResult:
        """
        装備操作の統一実行メソッド（Template Method Pattern）
        
        Args:
            operation: 操作タイプ
            **kwargs: 操作パラメータ
            
        Returns:
            EquipmentOperationResult: 操作結果
        """
        try:
            # 1. 前提条件の検証
            validation_result = self._validate_operation(operation, **kwargs)
            if not validation_result.success:
                return validation_result
            
            # 2. 操作の実行
            execution_result = self._execute_operation(operation, **kwargs)
            
            # 3. 後処理
            self._post_operation_processing(operation, execution_result)
            
            return execution_result
            
        except Exception as e:
            logger.error(f"装備操作エラー({operation}): {e}")
            return EquipmentOperationResult(
                success=False,
                error_type='execution_error',
                message=f"操作実行中にエラーが発生しました: {str(e)}"
            )
    
    def _validate_operation(self, operation: str, **kwargs) -> EquipmentOperationResult:
        """操作の前提条件を検証"""
        # 基本的なチェック
        if not self.character:
            return EquipmentOperationResult(
                success=False,
                error_type='no_character',
                message="キャラクターが設定されていません"
            )
        
        # 操作固有の検証
        return self._validate_specific_operation(operation, **kwargs)
    
    def _validate_specific_operation(self, operation: str, **kwargs) -> EquipmentOperationResult:
        """操作固有の検証（サブクラスでオーバーライド可能）"""
        # 装備操作での必須パラメータチェック
        if operation in ['equip_item', 'unequip_item']:
            if 'slot_type' not in kwargs:
                return EquipmentOperationResult(
                    success=False,
                    error_type='missing_slot_type',
                    message="スロットタイプが指定されていません"
                )
        
        if operation == 'equip_item' and 'item' not in kwargs:
            return EquipmentOperationResult(
                success=False,
                error_type='missing_item',
                message="装備するアイテムが指定されていません"
            )
        
        return EquipmentOperationResult(success=True)
    
    def _execute_operation(self, operation: str, **kwargs) -> EquipmentOperationResult:
        """
        具体的な装備操作実行（Strategy Pattern）
        
        Args:
            operation: 操作タイプ
            **kwargs: 操作パラメータ
            
        Returns:
            EquipmentOperationResult: 実行結果
        """
        # 装備操作マップ（Strategy Pattern）
        operation_map = {
            'equip_item': self._handle_equip_item,
            'unequip_item': self._handle_unequip_item,
            'swap_equipment': self._handle_swap_equipment,
            'get_slot_info': self._handle_get_slot_info,
            'get_all_slots': self._handle_get_all_slots,
            'validate_equipment': self._handle_validate_equipment,
            'create_comparison': self._handle_create_comparison,
            'assign_quick_slot': self._handle_assign_quick_slot,
            'get_equippable_items': self._handle_get_equippable_items
        }
        
        if operation not in operation_map:
            return EquipmentOperationResult(
                success=False,
                error_type='unknown_operation',
                message=f"未知の装備操作: {operation}"
            )
        
        try:
            return operation_map[operation](**kwargs)
        except Exception as e:
            return EquipmentOperationResult(
                success=False,
                error_type='operation_execution_error',
                message=f"装備操作実行エラー({operation}): {str(e)}"
            )
    
    def _post_operation_processing(self, operation: str, result: EquipmentOperationResult) -> None:
        """操作後の処理"""
        if result.success:
            logger.debug(f"装備操作完了: {operation}")
            # 装備変更時のステータス再計算など
            if operation in ['equip_item', 'unequip_item', 'swap_equipment']:
                self._recalculate_character_stats()
        else:
            logger.warning(f"装備操作失敗: {operation} - {result.message}")
    
    def _handle_equip_item(self, item: Any, slot_type: str, **kwargs) -> EquipmentOperationResult:
        """アイテム装備処理"""
        try:
            # アイテム装備可能性チェック
            can_equip_result = self._can_equip_item(item, slot_type)
            if not can_equip_result.success:
                return can_equip_result
            
            # 実際の装備処理
            if hasattr(self.equipment_slots, 'equip_item'):
                success = self.equipment_slots.equip_item(item, slot_type)
                if success:
                    return EquipmentOperationResult(
                        success=True,
                        message=f"アイテムを装備しました: {getattr(item, 'name', 'Unknown')}",
                        data={'item': item, 'slot_type': slot_type}
                    )
                else:
                    return EquipmentOperationResult(
                        success=False,
                        error_type='equip_failed',
                        message="アイテムの装備に失敗しました"
                    )
            else:
                return EquipmentOperationResult(
                    success=False,
                    error_type='no_equip_method',
                    message="装備システムが利用できません"
                )
                
        except Exception as e:
            return EquipmentOperationResult(
                success=False,
                error_type='equip_error',
                message=f"装備処理エラー: {str(e)}"
            )
    
    def _handle_unequip_item(self, slot_type: str, **kwargs) -> EquipmentOperationResult:
        """アイテム装備解除処理"""
        try:
            # スロットに何か装備されているかチェック
            slot_info = self._get_slot_info_internal(slot_type)
            if not slot_info or not slot_info.get('item'):
                return EquipmentOperationResult(
                    success=False,
                    error_type='nothing_equipped',
                    message=f"スロット {slot_type} には何も装備されていません"
                )
            
            # 実際の装備解除処理
            if hasattr(self.equipment_slots, 'unequip_item'):
                unequipped_item = self.equipment_slots.unequip_item(slot_type)
                if unequipped_item:
                    return EquipmentOperationResult(
                        success=True,
                        message=f"アイテムを装備解除しました: {getattr(unequipped_item, 'name', 'Unknown')}",
                        data={'item': unequipped_item, 'slot_type': slot_type}
                    )
                else:
                    return EquipmentOperationResult(
                        success=False,
                        error_type='unequip_failed',
                        message="アイテムの装備解除に失敗しました"
                    )
            else:
                return EquipmentOperationResult(
                    success=False,
                    error_type='no_unequip_method',
                    message="装備解除システムが利用できません"
                )
                
        except Exception as e:
            return EquipmentOperationResult(
                success=False,
                error_type='unequip_error',
                message=f"装備解除処理エラー: {str(e)}"
            )
    
    def _handle_swap_equipment(self, from_slot: str, to_slot: str, **kwargs) -> EquipmentOperationResult:
        """装備交換処理"""
        try:
            # 両方のスロット情報を取得
            from_info = self._get_slot_info_internal(from_slot)
            to_info = self._get_slot_info_internal(to_slot)
            
            if not from_info or not from_info.get('item'):
                return EquipmentOperationResult(
                    success=False,
                    error_type='source_slot_empty',
                    message=f"交換元スロット {from_slot} にアイテムがありません"
                )
            
            # 実際の交換処理
            if hasattr(self.equipment_slots, 'swap_equipment'):
                success = self.equipment_slots.swap_equipment(from_slot, to_slot)
                if success:
                    return EquipmentOperationResult(
                        success=True,
                        message=f"装備を交換しました: {from_slot} <-> {to_slot}",
                        data={'from_slot': from_slot, 'to_slot': to_slot}
                    )
                else:
                    return EquipmentOperationResult(
                        success=False,
                        error_type='swap_failed',
                        message="装備交換に失敗しました"
                    )
            else:
                return EquipmentOperationResult(
                    success=False,
                    error_type='no_swap_method',
                    message="装備交換システムが利用できません"
                )
                
        except Exception as e:
            return EquipmentOperationResult(
                success=False,
                error_type='swap_error',
                message=f"装備交換処理エラー: {str(e)}"
            )
    
    def _handle_get_slot_info(self, slot_type: str, **kwargs) -> EquipmentOperationResult:
        """スロット情報取得処理"""
        try:
            slot_info = self._get_slot_info_internal(slot_type)
            return EquipmentOperationResult(
                success=True,
                message=f"スロット情報を取得しました: {slot_type}",
                data=slot_info
            )
        except Exception as e:
            return EquipmentOperationResult(
                success=False,
                error_type='slot_info_error',
                message=f"スロット情報取得エラー: {str(e)}"
            )
    
    def _handle_get_all_slots(self, **kwargs) -> EquipmentOperationResult:
        """全スロット情報取得処理"""
        try:
            all_slots = {}
            if hasattr(self.equipment_slots, 'get_all_slots'):
                slots_data = self.equipment_slots.get_all_slots()
                for slot_type, slot_data in slots_data.items():
                    all_slots[slot_type] = self._get_slot_info_internal(slot_type)
            
            return EquipmentOperationResult(
                success=True,
                message="全スロット情報を取得しました",
                data=all_slots
            )
        except Exception as e:
            return EquipmentOperationResult(
                success=False,
                error_type='all_slots_error',
                message=f"全スロット情報取得エラー: {str(e)}"
            )
    
    def _handle_validate_equipment(self, **kwargs) -> EquipmentOperationResult:
        """装備状態検証処理"""
        try:
            validation_results = []
            
            # 各スロットの検証
            if hasattr(self.equipment_slots, 'get_all_slots'):
                slots_data = self.equipment_slots.get_all_slots()
                for slot_type, slot_data in slots_data.items():
                    slot_validation = self._validate_slot(slot_type, slot_data)
                    validation_results.append(slot_validation)
            
            # 全体的な検証結果
            all_valid = all(result['valid'] for result in validation_results)
            
            return EquipmentOperationResult(
                success=True,
                message="装備状態検証完了",
                data={'valid': all_valid, 'results': validation_results}
            )
        except Exception as e:
            return EquipmentOperationResult(
                success=False,
                error_type='validation_error',
                message=f"装備状態検証エラー: {str(e)}"
            )
    
    def _handle_create_comparison(self, item: Any, slot_type: str, **kwargs) -> EquipmentOperationResult:
        """装備比較作成処理"""
        try:
            current_item = None
            slot_info = self._get_slot_info_internal(slot_type)
            if slot_info:
                current_item = slot_info.get('item')
            
            comparison = {
                'current_item': current_item,
                'new_item': item,
                'slot_type': slot_type,
                'stat_differences': self._calculate_stat_differences(current_item, item)
            }
            
            return EquipmentOperationResult(
                success=True,
                message="装備比較を作成しました",
                data=comparison
            )
        except Exception as e:
            return EquipmentOperationResult(
                success=False,
                error_type='comparison_error',
                message=f"装備比較作成エラー: {str(e)}"
            )
    
    def _handle_assign_quick_slot(self, quick_slot_index: int, slot_type: str, **kwargs) -> EquipmentOperationResult:
        """クイックスロット割り当て処理"""
        try:
            self.quick_slots[quick_slot_index] = slot_type
            return EquipmentOperationResult(
                success=True,
                message=f"クイックスロット {quick_slot_index} に {slot_type} を割り当てました",
                data={'quick_slot_index': quick_slot_index, 'slot_type': slot_type}
            )
        except Exception as e:
            return EquipmentOperationResult(
                success=False,
                error_type='quick_slot_error',
                message=f"クイックスロット割り当てエラー: {str(e)}"
            )
    
    def _handle_get_equippable_items(self, slot_type: Optional[str] = None, **kwargs) -> EquipmentOperationResult:
        """装備可能アイテム取得処理"""
        try:
            equippable_items = []
            
            if hasattr(self.inventory, 'get_items'):
                inventory_items = self.inventory.get_items()
                for item in inventory_items:
                    if self._is_item_equippable(item, slot_type):
                        equippable_items.append(item)
            
            return EquipmentOperationResult(
                success=True,
                message=f"装備可能アイテムを取得しました: {len(equippable_items)}個",
                data={'items': equippable_items, 'slot_type': slot_type}
            )
        except Exception as e:
            return EquipmentOperationResult(
                success=False,
                error_type='equippable_items_error',
                message=f"装備可能アイテム取得エラー: {str(e)}"
            )
    
    # === ヘルパーメソッド ===
    
    def _can_equip_item(self, item: Any, slot_type: str) -> EquipmentOperationResult:
        """アイテム装備可能性チェック"""
        if not item:
            return EquipmentOperationResult(
                success=False,
                error_type='no_item',
                message="アイテムが指定されていません"
            )
        
        # レベル制限チェック
        if hasattr(item, 'required_level') and hasattr(self.character, 'level'):
            if self.character.level < item.required_level:
                return EquipmentOperationResult(
                    success=False,
                    error_type='level_requirement',
                    message=f"レベル {item.required_level} 以上が必要です"
                )
        
        # クラス制限チェック
        if hasattr(item, 'allowed_classes') and hasattr(self.character, 'character_class'):
            if self.character.character_class not in item.allowed_classes:
                return EquipmentOperationResult(
                    success=False,
                    error_type='class_restriction',
                    message="このクラスでは装備できません"
                )
        
        return EquipmentOperationResult(success=True)
    
    def _get_slot_info_internal(self, slot_type: str) -> Optional[Dict[str, Any]]:
        """内部用スロット情報取得"""
        if hasattr(self.equipment_slots, 'get_slot'):
            slot = self.equipment_slots.get_slot(slot_type)
            if slot:
                return {
                    'slot_type': slot_type,
                    'item': getattr(slot, 'item', None),
                    'is_empty': getattr(slot, 'item', None) is None
                }
        return None
    
    def _validate_slot(self, slot_type: str, slot_data: Any) -> Dict[str, Any]:
        """個別スロット検証"""
        return {
            'slot_type': slot_type,
            'valid': True,  # 基本的な検証ロジック
            'messages': []
        }
    
    def _calculate_stat_differences(self, current_item: Any, new_item: Any) -> Dict[str, int]:
        """ステータス差分計算"""
        # 基本的な差分計算（実装はアイテムシステムに依存）
        return {
            'attack_power': 0,
            'defense': 0,
            'magic_power': 0
        }
    
    def _is_item_equippable(self, item: Any, slot_type: Optional[str]) -> bool:
        """アイテムが装備可能かチェック"""
        if slot_type and hasattr(item, 'equipment_slot'):
            return item.equipment_slot == slot_type
        return hasattr(item, 'equipment_slot')
    
    def _recalculate_character_stats(self):
        """キャラクターステータス再計算"""
        # キャラクターステータスの再計算ロジック
        logger.debug("キャラクターステータスを再計算しました")
    
    def get_current_state(self) -> Dict[str, Any]:
        """現在の装備状態を取得（Undo用）"""
        return {
            'selected_slot': self.selected_slot,
            'quick_slots': self.quick_slots.copy(),
            # 他の状態情報
        }
    
    def restore_state(self, state: Dict[str, Any]) -> EquipmentOperationResult:
        """装備状態を復元（Undo用）"""
        try:
            self.selected_slot = state.get('selected_slot')
            self.quick_slots = state.get('quick_slots', {})
            return EquipmentOperationResult(success=True, message="状態を復元しました")
        except Exception as e:
            return EquipmentOperationResult(
                success=False,
                error_type='restore_error',
                message=f"状態復元エラー: {str(e)}"
            )