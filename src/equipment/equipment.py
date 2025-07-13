"""装備システム"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Tuple
from enum import Enum
import uuid

from src.items.item import ItemInstance, Item, ItemManager, item_manager, ItemType
from src.character.stats import BaseStats, DerivedStats
from src.utils.logger import logger

# 装備システム定数
MIN_CONDITION_FOR_EQUIP = 0
DEFAULT_BONUS_VALUE = 0
INITIAL_TOTAL_WEIGHT = 0.0


class EquipmentSlot(Enum):
    """装備スロット"""
    WEAPON = "weapon"           # 武器
    ARMOR = "armor"             # 防具
    ACCESSORY_1 = "accessory_1" # アクセサリ1
    ACCESSORY_2 = "accessory_2" # アクセサリ2


@dataclass
class EquipmentBonus:
    """装備ボーナス"""
    strength: int = 0
    agility: int = 0
    intelligence: int = 0
    faith: int = 0
    luck: int = 0
    
    attack_power: int = 0
    defense: int = 0
    magic_power: int = 0
    magic_resistance: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        """辞書形式でシリアライズ"""
        return {
            'strength': self.strength,
            'agility': self.agility,
            'intelligence': self.intelligence,
            'faith': self.faith,
            'luck': self.luck,
            'attack_power': self.attack_power,
            'defense': self.defense,
            'magic_power': self.magic_power,
            'magic_resistance': self.magic_resistance
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'EquipmentBonus':
        """辞書からデシリアライズ"""
        return cls(
            strength=data.get('strength', 0),
            agility=data.get('agility', 0),
            intelligence=data.get('intelligence', 0),
            faith=data.get('faith', 0),
            luck=data.get('luck', 0),
            attack_power=data.get('attack_power', 0),
            defense=data.get('defense', 0),
            magic_power=data.get('magic_power', 0),
            magic_resistance=data.get('magic_resistance', 0)
        )
    
    def __add__(self, other: 'EquipmentBonus') -> 'EquipmentBonus':
        """ボーナスの加算"""
        return EquipmentBonus(
            strength=self.strength + other.strength,
            agility=self.agility + other.agility,
            intelligence=self.intelligence + other.intelligence,
            faith=self.faith + other.faith,
            luck=self.luck + other.luck,
            attack_power=self.attack_power + other.attack_power,
            defense=self.defense + other.defense,
            magic_power=self.magic_power + other.magic_power,
            magic_resistance=self.magic_resistance + other.magic_resistance
        )


class Equipment:
    """装備システムクラス"""
    
    def __init__(self, owner_id: str):
        self.owner_id = owner_id
        self.equipped_items: Dict[EquipmentSlot, Optional[ItemInstance]] = {}
        
        # 全スロットを初期化
        for slot in EquipmentSlot:
            self.equipped_items[slot] = None
        
        self.item_manager = item_manager
        logger.debug(f"装備システムを初期化: {owner_id}")
    
    def can_equip_item(self, item_instance: ItemInstance, slot: EquipmentSlot, character_class: str) -> Tuple[bool, str]:
        """アイテムを装備可能かチェック"""
        item = self.item_manager.get_item(item_instance.item_id)
        if not item:
            return False, "アイテムが見つかりません"
        
        # 各種チェックを実行
        slot_check = self._check_slot_compatibility(item, slot)
        if not slot_check[0]:
            return slot_check
            
        class_check = self._check_class_restriction(item, character_class)
        if not class_check[0]:
            return class_check
            
        condition_check = self._check_item_condition(item_instance)
        if not condition_check[0]:
            return condition_check
        
        return True, ""
    
    def _check_slot_compatibility(self, item: Item, slot: EquipmentSlot) -> Tuple[bool, str]:
        """スロットとアイテムの適合性チェック"""
        if slot == EquipmentSlot.WEAPON and not item.is_weapon():
            return False, "武器スロットには武器のみ装備できます"
        elif slot == EquipmentSlot.ARMOR and not item.is_armor():
            return False, "防具スロットには防具のみ装備できます"
        elif slot in [EquipmentSlot.ACCESSORY_1, EquipmentSlot.ACCESSORY_2]:
            if item.item_type not in [ItemType.TREASURE]:
                return False, "アクセサリスロットにはアクセサリのみ装備できます"
        return True, ""
    
    def _check_class_restriction(self, item: Item, character_class: str) -> Tuple[bool, str]:
        """クラス制限チェック"""
        if not item.can_use(character_class):
            return False, f"クラス '{character_class}' は このアイテムを使用できません"
        return True, ""
    
    def _check_item_condition(self, item_instance: ItemInstance) -> Tuple[bool, str]:
        """アイテム状態チェック"""
        if item_instance.condition <= MIN_CONDITION_FOR_EQUIP:
            return False, "破損したアイテムは装備できません"
        return True, ""
    
    def equip_item(self, item_instance: ItemInstance, slot: EquipmentSlot, character_class: str) -> Tuple[bool, str, Optional[ItemInstance]]:
        """アイテムを装備"""
        can_equip, reason = self.can_equip_item(item_instance, slot, character_class)
        if not can_equip:
            return False, reason, None
        
        # 既に装備されているアイテムを取得
        previous_item = self.equipped_items[slot]
        
        # 新しいアイテムを装備
        self.equipped_items[slot] = item_instance
        
        logger.info(f"アイテム '{item_instance.item_id}' を {slot.value} に装備しました")
        
        return True, "装備成功", previous_item
    
    def unequip_item(self, slot: EquipmentSlot) -> Optional[ItemInstance]:
        """アイテムの装備を解除"""
        item_instance = self.equipped_items[slot]
        if item_instance:
            self.equipped_items[slot] = None
            logger.info(f"スロット {slot.value} の装備を解除しました")
            return item_instance
        return None
    
    def get_equipped_item(self, slot: EquipmentSlot) -> Optional[ItemInstance]:
        """指定スロットの装備アイテムを取得"""
        return self.equipped_items[slot]
    
    def get_all_equipped_items(self) -> Dict[EquipmentSlot, Optional[ItemInstance]]:
        """全装備アイテムを取得"""
        return self.equipped_items.copy()
    
    def calculate_equipment_bonus(self) -> EquipmentBonus:
        """装備による総ボーナスを計算"""
        total_bonus = EquipmentBonus()
        
        for slot, item_instance in self.equipped_items.items():
            if item_instance:
                item = self.item_manager.get_item(item_instance.item_id)
                if item:
                    bonus = self._calculate_item_bonus(item, item_instance)
                    total_bonus = total_bonus + bonus
        
        return total_bonus
    
    def _calculate_item_bonus(self, item: Item, item_instance: ItemInstance) -> EquipmentBonus:
        """個別アイテムのボーナスを計算"""
        bonus = self._get_basic_item_bonus(item)
        self._apply_additional_bonuses(bonus, item)
        self._apply_condition_modifier(bonus, item_instance.condition)
        
        return bonus
    
    def _get_basic_item_bonus(self, item: Item) -> EquipmentBonus:
        """アイテムの基本ボーナスを取得"""
        bonus = EquipmentBonus()
        
        if item.is_weapon():
            bonus.attack_power = item.get_attack_power()
        elif item.is_armor():
            bonus.defense = item.get_defense()
            
        return bonus
    
    def _apply_additional_bonuses(self, bonus: EquipmentBonus, item: Item):
        """追加ボーナスを適用"""
        item_bonuses = item.item_data.get('bonuses', {})
        bonus.strength += item_bonuses.get('strength', DEFAULT_BONUS_VALUE)
        bonus.agility += item_bonuses.get('agility', DEFAULT_BONUS_VALUE)
        bonus.intelligence += item_bonuses.get('intelligence', DEFAULT_BONUS_VALUE)
        bonus.faith += item_bonuses.get('faith', DEFAULT_BONUS_VALUE)
        bonus.luck += item_bonuses.get('luck', DEFAULT_BONUS_VALUE)
        bonus.magic_power += item_bonuses.get('magic_power', DEFAULT_BONUS_VALUE)
        bonus.magic_resistance += item_bonuses.get('magic_resistance', DEFAULT_BONUS_VALUE)
    
    def _apply_condition_modifier(self, bonus: EquipmentBonus, condition_modifier: float):
        """状態による補正を適用"""
        bonus.attack_power = int(bonus.attack_power * condition_modifier)
        bonus.defense = int(bonus.defense * condition_modifier)
        bonus.magic_power = int(bonus.magic_power * condition_modifier)
        bonus.magic_resistance = int(bonus.magic_resistance * condition_modifier)
    
    def get_total_weight(self) -> float:
        """装備の総重量を取得"""
        total_weight = INITIAL_TOTAL_WEIGHT
        
        for item_instance in self.equipped_items.values():
            weight = self._get_item_weight(item_instance)
            total_weight += weight
            
        return total_weight
    
    def _get_item_weight(self, item_instance: Optional[ItemInstance]) -> float:
        """個別アイテムの重量を取得"""
        if not item_instance:
            return INITIAL_TOTAL_WEIGHT
            
        item = self.item_manager.get_item(item_instance.item_id)
        return item.weight if item else INITIAL_TOTAL_WEIGHT
    
    def get_equipment_summary(self) -> Dict[str, Any]:
        """装備要約を取得"""
        summary = {
            'equipped_count': sum(1 for item in self.equipped_items.values() if item is not None),
            'total_weight': self.get_total_weight(),
            'total_bonus': self.calculate_equipment_bonus(),
            'items': {}
        }
        
        for slot, item_instance in self.equipped_items.items():
            if item_instance:
                item = self.item_manager.get_item(item_instance.item_id)
                if item:
                    summary['items'][slot.value] = {
                        'name': item.get_name(),
                        'condition': item_instance.condition,
                        'identified': item_instance.identified
                    }
            else:
                summary['items'][slot.value] = None
        
        return summary
    
    def is_slot_empty(self, slot: EquipmentSlot) -> bool:
        """スロットが空かどうか"""
        return self.equipped_items[slot] is None
    
    def get_empty_slots(self) -> List[EquipmentSlot]:
        """空のスロット一覧を取得"""
        return [slot for slot, item in self.equipped_items.items() if item is None]
    
    def to_dict(self) -> Dict[str, Any]:
        """辞書形式でシリアライズ"""
        return {
            'owner_id': self.owner_id,
            'equipped_items': {
                slot.value: item_instance.to_dict() if item_instance else None
                for slot, item_instance in self.equipped_items.items()
            }
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Equipment':
        """辞書からデシリアライズ"""
        equipment = cls(owner_id=data.get('owner_id', ''))
        
        equipped_items_data = data.get('equipped_items', {})
        for slot_str, item_data in equipped_items_data.items():
            try:
                slot = EquipmentSlot(slot_str)
                if item_data:
                    item_instance = ItemInstance.from_dict(item_data)
                    equipment.equipped_items[slot] = item_instance
                else:
                    equipment.equipped_items[slot] = None
            except ValueError:
                logger.warning(f"無効な装備スロット: {slot_str}")
        
        return equipment


class EquipmentManager:
    """装備管理システム"""
    
    def __init__(self):
        self.character_equipment: Dict[str, Equipment] = {}
        logger.debug("EquipmentManagerを初期化しました")
    
    def create_character_equipment(self, character_id: str) -> Equipment:
        """キャラクター用装備システムを作成"""
        equipment = Equipment(owner_id=character_id)
        self.character_equipment[character_id] = equipment
        logger.info(f"キャラクター装備システムを作成: {character_id}")
        return equipment
    
    def get_character_equipment(self, character_id: str) -> Optional[Equipment]:
        """キャラクターの装備システムを取得"""
        return self.character_equipment.get(character_id)
    
    def remove_character_equipment(self, character_id: str):
        """キャラクターの装備システムを削除"""
        if character_id in self.character_equipment:
            del self.character_equipment[character_id]
            logger.info(f"キャラクター装備システムを削除: {character_id}")
    
    def to_dict(self) -> Dict[str, Any]:
        """辞書形式でシリアライズ"""
        return {
            'character_equipment': {
                char_id: equipment.to_dict()
                for char_id, equipment in self.character_equipment.items()
            }
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'EquipmentManager':
        """辞書からデシリアライズ"""
        manager = cls()
        
        char_equipment_data = data.get('character_equipment', {})
        for char_id, equipment_data in char_equipment_data.items():
            manager.character_equipment[char_id] = Equipment.from_dict(equipment_data)
        
        return manager


# グローバルインスタンス
equipment_manager = EquipmentManager()