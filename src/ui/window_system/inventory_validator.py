"""
InventoryValidator クラス

インベントリアイテムの検証とルール管理

Fowler式リファクタリング：Extract Class パターン
"""

from typing import Dict, List, Any, Optional, Callable
from src.ui.window_system.inventory_types import (
    InventoryType, ItemSlotInfo, ItemCategory, ItemActionType, InventoryFilter
)
from src.utils.logger import logger


class InventoryValidator:
    """
    インベントリ検証クラス
    
    アイテムの利用可能性チェック、制限検証、ルール管理を担当
    """
    
    def __init__(self, inventory_type: InventoryType):
        """
        バリデーターを初期化
        
        Args:
            inventory_type: インベントリタイプ
        """
        self.inventory_type = inventory_type
        self.custom_validators: Dict[str, Callable[[Any, Any], bool]] = {}
        self.weight_limit: Optional[float] = None
        self.value_limit: Optional[int] = None
        
        logger.debug(f"InventoryValidatorを初期化: {inventory_type}")
    
    def set_weight_limit(self, limit: Optional[float]) -> None:
        """重量制限を設定"""
        self.weight_limit = limit
        logger.debug(f"重量制限設定: {limit}")
    
    def set_value_limit(self, limit: Optional[int]) -> None:
        """価値制限を設定"""
        self.value_limit = limit
        logger.debug(f"価値制限設定: {limit}")
    
    def validate_item_usage(self, slot_info: ItemSlotInfo, character: Any = None) -> bool:
        """アイテム使用の検証"""
        if not slot_info.item:
            logger.debug("使用検証失敗: アイテムなし")
            return False
        
        # 装備中のアイテムは使用不可（装備解除が必要）
        if slot_info.is_equipped:
            logger.debug("使用検証失敗: 装備中")
            return False
        
        # ロックされたアイテムは使用不可
        if slot_info.is_locked:
            logger.debug("使用検証失敗: ロック中")
            return False
        
        # 消耗品の使用可能性チェック
        if hasattr(slot_info.item, 'is_consumable') and slot_info.item.is_consumable():
            return self._validate_consumable_usage(slot_info.item, character)
        
        # 装備品の使用（装備）可能性チェック
        if hasattr(slot_info.item, 'is_equippable') and slot_info.item.is_equippable():
            return self._validate_equipment_usage(slot_info.item, character)
        
        logger.debug("使用検証失敗: 使用可能なアイテムタイプではない")
        return False
    
    def _validate_consumable_usage(self, item: Any, character: Any = None) -> bool:
        """消耗品使用の検証"""
        # 基本的に消耗品は使用可能
        if not character:
            return True
        
        # キャラクター固有の制限をチェック
        if hasattr(item, 'required_level'):
            if hasattr(character, 'level') and character.level < item.required_level:
                logger.debug(f"消耗品使用検証失敗: レベル不足 {character.level} < {item.required_level}")
                return False
        
        if hasattr(item, 'required_class'):
            if hasattr(character, 'character_class') and character.character_class != item.required_class:
                logger.debug(f"消耗品使用検証失敗: クラス不適合 {character.character_class} != {item.required_class}")
                return False
        
        return True
    
    def _validate_equipment_usage(self, item: Any, character: Any = None) -> bool:
        """装備品使用の検証"""
        if not character:
            return True
        
        # レベル制限
        if hasattr(item, 'required_level'):
            if hasattr(character, 'level') and character.level < item.required_level:
                logger.debug(f"装備使用検証失敗: レベル不足")
                return False
        
        # クラス制限
        if hasattr(item, 'required_class'):
            if hasattr(character, 'character_class') and character.character_class not in item.required_class:
                logger.debug(f"装備使用検証失敗: クラス不適合")
                return False
        
        # ステータス制限
        if hasattr(item, 'required_stats'):
            for stat_name, required_value in item.required_stats.items():
                if hasattr(character, stat_name):
                    current_value = getattr(character, stat_name)
                    if current_value < required_value:
                        logger.debug(f"装備使用検証失敗: {stat_name}不足 {current_value} < {required_value}")
                        return False
        
        return True
    
    def validate_item_drop(self, slot_info: ItemSlotInfo) -> bool:
        """アイテム破棄の検証"""
        if not slot_info.item:
            return False
        
        # 装備中のアイテムは破棄不可
        if slot_info.is_equipped:
            logger.debug("破棄検証失敗: 装備中")
            return False
        
        # ロックされたアイテムは破棄不可
        if slot_info.is_locked:
            logger.debug("破棄検証失敗: ロック中")
            return False
        
        # クエストアイテムは破棄不可
        if hasattr(slot_info.item, 'is_quest_item') and slot_info.item.is_quest_item():
            logger.debug("破棄検証失敗: クエストアイテム")
            return False
        
        # 重要アイテムは破棄不可
        if hasattr(slot_info.item, 'is_important') and slot_info.item.is_important():
            logger.debug("破棄検証失敗: 重要アイテム")
            return False
        
        return True
    
    def validate_item_transfer(self, slot_info: ItemSlotInfo, target_inventory: Any) -> bool:
        """アイテム転送の検証"""
        if not slot_info.item:
            return False
        
        # 装備中のアイテムは転送不可
        if slot_info.is_equipped:
            logger.debug("転送検証失敗: 装備中")
            return False
        
        # ロックされたアイテムは転送不可
        if slot_info.is_locked:
            logger.debug("転送検証失敗: ロック中")
            return False
        
        # 転送先の容量チェック
        if hasattr(target_inventory, 'can_add_item'):
            if not target_inventory.can_add_item(slot_info.item):
                logger.debug("転送検証失敗: 転送先容量不足")
                return False
        
        # 転送先の重量制限チェック
        if self.weight_limit and hasattr(slot_info.item, 'weight'):
            if hasattr(target_inventory, 'get_total_weight'):
                current_weight = target_inventory.get_total_weight()
                if current_weight + slot_info.item.weight > self.weight_limit:
                    logger.debug("転送検証失敗: 重量制限超過")
                    return False
        
        return True
    
    def validate_item_move(self, from_slot: int, to_slot: int, inventory: Any) -> bool:
        """アイテム移動の検証"""
        if not hasattr(inventory, 'slots'):
            return False
        
        total_slots = len(inventory.slots)
        
        # スロットインデックスの範囲チェック
        if not (0 <= from_slot < total_slots and 0 <= to_slot < total_slots):
            logger.debug(f"移動検証失敗: 無効なスロットインデックス {from_slot} -> {to_slot}")
            return False
        
        # 同じスロットへの移動は無効
        if from_slot == to_slot:
            logger.debug("移動検証失敗: 同じスロット")
            return False
        
        # 移動元にアイテムが存在するかチェック
        from_slot_obj = inventory.slots[from_slot]
        if not hasattr(from_slot_obj, 'item') or not from_slot_obj.item:
            logger.debug("移動検証失敗: 移動元にアイテムなし")
            return False
        
        # 装備中のアイテムは移動不可
        if hasattr(from_slot_obj, 'is_equipped') and from_slot_obj.is_equipped:
            logger.debug("移動検証失敗: 装備中のアイテム")
            return False
        
        # ロックされたアイテムは移動不可
        if hasattr(from_slot_obj, 'is_locked') and from_slot_obj.is_locked:
            logger.debug("移動検証失敗: ロック中のアイテム")
            return False
        
        return True
    
    def validate_quick_slot_assignment(self, inventory_slot: int, quick_slot_index: int, 
                                     inventory: Any, max_quick_slots: int) -> bool:
        """クイックスロット割り当ての検証"""
        # クイックスロットインデックスの範囲チェック
        if not (0 <= quick_slot_index < max_quick_slots):
            logger.debug(f"クイックスロット検証失敗: 無効なインデックス {quick_slot_index}")
            return False
        
        # インベントリスロットの範囲チェック
        if not hasattr(inventory, 'slots'):
            return False
        
        total_slots = len(inventory.slots)
        if not (0 <= inventory_slot < total_slots):
            logger.debug(f"クイックスロット検証失敗: 無効なインベントリスロット {inventory_slot}")
            return False
        
        # スロットにアイテムが存在するかチェック
        slot = inventory.slots[inventory_slot]
        if not hasattr(slot, 'item') or not slot.item:
            logger.debug("クイックスロット検証失敗: アイテムなし")
            return False
        
        # クイックスロットに割り当て可能なアイテムかチェック
        if hasattr(slot.item, 'is_consumable') and slot.item.is_consumable():
            return True
        
        if hasattr(slot.item, 'is_equippable') and slot.item.is_equippable():
            return True
        
        logger.debug("クイックスロット検証失敗: 割り当て不可能なアイテムタイプ")
        return False
    
    def validate_inventory_constraints(self, inventory: Any) -> Dict[str, bool]:
        """インベントリ制約の検証"""
        constraints = {
            'weight_limit': True,
            'slot_limit': True,
            'value_limit': True,
            'category_restrictions': True
        }
        
        if not hasattr(inventory, 'slots'):
            constraints['slot_limit'] = False
            return constraints
        
        total_weight = 0.0
        total_value = 0
        used_slots = 0
        
        # 各スロットをチェック
        for slot in inventory.slots:
            if hasattr(slot, 'item') and slot.item:
                used_slots += 1
                quantity = getattr(slot, 'quantity', 1)
                
                # 重量チェック
                if hasattr(slot.item, 'weight'):
                    total_weight += slot.item.weight * quantity
                
                # 価値チェック
                if hasattr(slot.item, 'value'):
                    total_value += slot.item.value * quantity
        
        # 重量制限チェック
        if self.weight_limit and total_weight > self.weight_limit:
            constraints['weight_limit'] = False
            logger.debug(f"重量制限違反: {total_weight} > {self.weight_limit}")
        
        # 価値制限チェック
        if self.value_limit and total_value > self.value_limit:
            constraints['value_limit'] = False
            logger.debug(f"価値制限違反: {total_value} > {self.value_limit}")
        
        # スロット制限チェック（常に満たされているはず）
        total_slots = getattr(inventory, 'capacity', len(inventory.slots))
        if used_slots > total_slots:
            constraints['slot_limit'] = False
            logger.debug(f"スロット制限違反: {used_slots} > {total_slots}")
        
        return constraints
    
    def add_custom_validator(self, name: str, validator: Callable[[Any, Any], bool]) -> None:
        """カスタムバリデーターを追加"""
        self.custom_validators[name] = validator
        logger.debug(f"カスタムバリデーター追加: {name}")
    
    def remove_custom_validator(self, name: str) -> bool:
        """カスタムバリデーターを削除"""
        if name in self.custom_validators:
            del self.custom_validators[name]
            logger.debug(f"カスタムバリデーター削除: {name}")
            return True
        
        return False
    
    def validate_with_custom_rules(self, item: Any, context: Any) -> bool:
        """カスタムルールで検証"""
        for name, validator in self.custom_validators.items():
            try:
                if not validator(item, context):
                    logger.debug(f"カスタム検証失敗: {name}")
                    return False
            except Exception as e:
                logger.error(f"カスタムバリデーター {name} でエラー: {e}")
                return False
        
        return True
    
    def get_validation_errors(self, inventory: Any) -> List[str]:
        """検証エラーの一覧を取得"""
        errors = []
        
        # 基本制約のチェック
        constraints = self.validate_inventory_constraints(inventory)
        
        if not constraints['weight_limit']:
            errors.append("重量制限を超過しています")
        
        if not constraints['slot_limit']:
            errors.append("スロット制限を超過しています")
        
        if not constraints['value_limit']:
            errors.append("価値制限を超過しています")
        
        # 個別アイテムのチェック
        if hasattr(inventory, 'slots'):
            for i, slot in enumerate(inventory.slots):
                if hasattr(slot, 'item') and slot.item:
                    slot_info = ItemSlotInfo(
                        slot_index=i,
                        item=slot.item,
                        quantity=getattr(slot, 'quantity', 1),
                        is_equipped=getattr(slot, 'is_equipped', False),
                        is_locked=getattr(slot, 'is_locked', False)
                    )
                    
                    # 装備品の整合性チェック
                    if slot_info.is_equipped and hasattr(slot.item, 'is_equippable'):
                        if not slot.item.is_equippable():
                            errors.append(f"スロット {i}: 装備不可能なアイテムが装備状態です")
        
        return errors
    
    def get_validator_summary(self) -> Dict[str, Any]:
        """バリデーターサマリーを取得"""
        return {
            'inventory_type': self.inventory_type.value,
            'weight_limit': self.weight_limit,
            'value_limit': self.value_limit,
            'custom_validators': list(self.custom_validators.keys())
        }