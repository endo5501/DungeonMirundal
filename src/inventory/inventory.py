"""インベントリシステム"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Tuple
from enum import Enum
import uuid

from src.items.item import ItemInstance, Item, ItemManager, item_manager
from src.utils.logger import logger


class InventorySlotType(Enum):
    """インベントリスロットタイプ"""
    CHARACTER = "character"  # キャラクター個別
    PARTY = "party"  # パーティ共有


@dataclass
class InventorySlot:
    """インベントリスロット"""
    slot_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    item_instance: Optional[ItemInstance] = None
    slot_type: InventorySlotType = InventorySlotType.CHARACTER
    
    def is_empty(self) -> bool:
        """スロットが空かどうか"""
        return self.item_instance is None
    
    def can_store_item(self, item_instance: ItemInstance) -> bool:
        """アイテムを格納できるかチェック"""
        if self.is_empty():
            return True
        
        # 同じアイテムでスタック可能な場合
        if (self.item_instance.item_id == item_instance.item_id and
            self.item_instance.condition == item_instance.condition and
            self.item_instance.identified == item_instance.identified):
            
            # アイテム情報を取得してスタック可能かチェック
            item = item_manager.get_item(item_instance.item_id)
            if item and item.is_consumable():
                return True
        
        return False
    
    def add_item(self, item_instance: ItemInstance) -> bool:
        """アイテムを追加"""
        if self.is_empty():
            self.item_instance = item_instance
            return True
        
        # スタック処理
        if self.can_store_item(item_instance):
            self.item_instance.quantity += item_instance.quantity
            return True
        
        return False
    
    def remove_item(self, quantity: int = None) -> Optional[ItemInstance]:
        """アイテムを削除"""
        if self.is_empty():
            return None
        
        if quantity is None or quantity >= self.item_instance.quantity:
            # 全て削除
            removed_item = self.item_instance
            self.item_instance = None
            return removed_item
        else:
            # 一部削除
            if quantity <= 0:
                return None
            
            # 新しいインスタンスを作成
            removed_item = ItemInstance(
                item_id=self.item_instance.item_id,
                quantity=quantity,
                identified=self.item_instance.identified,
                condition=self.item_instance.condition,
                enchantments=self.item_instance.enchantments.copy(),
                custom_properties=self.item_instance.custom_properties.copy()
            )
            
            # 元のアイテムの数量を減らす
            self.item_instance.quantity -= quantity
            
            return removed_item
    
    def to_dict(self) -> Dict[str, Any]:
        """辞書形式でシリアライズ"""
        return {
            'slot_id': self.slot_id,
            'item_instance': self.item_instance.to_dict() if self.item_instance else None,
            'slot_type': self.slot_type.value
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'InventorySlot':
        """辞書からデシリアライズ"""
        item_instance = None
        if data.get('item_instance'):
            item_instance = ItemInstance.from_dict(data['item_instance'])
        
        return cls(
            slot_id=data.get('slot_id', str(uuid.uuid4())),
            item_instance=item_instance,
            slot_type=InventorySlotType(data.get('slot_type', 'character'))
        )


class Inventory:
    """インベントリクラス"""
    
    def __init__(self, owner_id: str, inventory_type: InventorySlotType, max_slots: int = 10):
        self.owner_id = owner_id
        self.inventory_type = inventory_type
        self.max_slots = max_slots
        self.slots: List[InventorySlot] = []
        
        # 空のスロットで初期化
        for i in range(max_slots):
            self.slots.append(InventorySlot(slot_type=inventory_type))
        
        self.item_manager = item_manager
        logger.debug(f"インベントリを初期化: {owner_id} ({inventory_type.value}, {max_slots}スロット)")
    
    def get_empty_slot_count(self) -> int:
        """空きスロット数を取得"""
        return sum(1 for slot in self.slots if slot.is_empty())
    
    def get_used_slot_count(self) -> int:
        """使用中スロット数を取得"""
        return sum(1 for slot in self.slots if not slot.is_empty())
    
    def is_full(self) -> bool:
        """インベントリが満杯かどうか"""
        return self.get_empty_slot_count() == 0
    
    def find_empty_slot(self) -> Optional[int]:
        """空きスロットのインデックスを取得"""
        for i, slot in enumerate(self.slots):
            if slot.is_empty():
                return i
        return None
    
    def find_stackable_slot(self, item_instance: ItemInstance) -> Optional[int]:
        """スタック可能なスロットのインデックスを取得"""
        for i, slot in enumerate(self.slots):
            if slot.can_store_item(item_instance):
                return i
        return None
    
    def add_item(self, item_instance: ItemInstance) -> bool:
        """アイテムを追加"""
        if not item_instance:
            return False
        
        # まずスタック可能なスロットを探す
        stackable_slot_index = self.find_stackable_slot(item_instance)
        if stackable_slot_index is not None:
            slot = self.slots[stackable_slot_index]
            if slot.add_item(item_instance):
                logger.debug(f"アイテムをスタック: {item_instance.item_id} x{item_instance.quantity}")
                return True
        
        # 空きスロットを探す
        empty_slot_index = self.find_empty_slot()
        if empty_slot_index is not None:
            slot = self.slots[empty_slot_index]
            if slot.add_item(item_instance):
                logger.debug(f"アイテムを追加: {item_instance.item_id} x{item_instance.quantity}")
                return True
        
        logger.warning(f"インベントリが満杯のためアイテムを追加できません: {item_instance.item_id}")
        return False
    
    def remove_item(self, slot_index: int, quantity: int = None) -> Optional[ItemInstance]:
        """指定スロットからアイテムを削除"""
        if slot_index < 0 or slot_index >= len(self.slots):
            return None
        
        slot = self.slots[slot_index]
        removed_item = slot.remove_item(quantity)
        
        if removed_item:
            logger.debug(f"アイテムを削除: {removed_item.item_id} x{removed_item.quantity}")
        
        return removed_item
    
    def remove_item_by_id(self, item_id: str, quantity: int = 1) -> Optional[ItemInstance]:
        """アイテムIDで指定してアイテムを削除"""
        for i, slot in enumerate(self.slots):
            if (not slot.is_empty() and 
                slot.item_instance.item_id == item_id and
                slot.item_instance.quantity >= quantity):
                return self.remove_item(i, quantity)
        
        return None
    
    def has_item(self, item_id: str, quantity: int = 1) -> bool:
        """指定したアイテムを指定数量持っているかチェック"""
        total_quantity = 0
        for slot in self.slots:
            if not slot.is_empty() and slot.item_instance.item_id == item_id:
                total_quantity += slot.item_instance.quantity
                if total_quantity >= quantity:
                    return True
        return False
    
    def get_item_count(self, item_id: str) -> int:
        """指定したアイテムの総数量を取得"""
        total_quantity = 0
        for slot in self.slots:
            if not slot.is_empty() and slot.item_instance.item_id == item_id:
                total_quantity += slot.item_instance.quantity
        return total_quantity
    
    def get_all_items(self) -> List[Tuple[int, ItemInstance]]:
        """全アイテムを取得（スロットインデックス付き）"""
        items = []
        for i, slot in enumerate(self.slots):
            if not slot.is_empty():
                items.append((i, slot.item_instance))
        return items
    
    def move_item(self, from_slot: int, to_slot: int) -> bool:
        """アイテムを移動"""
        if (from_slot < 0 or from_slot >= len(self.slots) or
            to_slot < 0 or to_slot >= len(self.slots)):
            return False
        
        from_slot_obj = self.slots[from_slot]
        to_slot_obj = self.slots[to_slot]
        
        if from_slot_obj.is_empty():
            return False
        
        # 移動先が空の場合
        if to_slot_obj.is_empty():
            to_slot_obj.item_instance = from_slot_obj.item_instance
            from_slot_obj.item_instance = None
            logger.debug(f"アイテムを移動: スロット{from_slot} → スロット{to_slot}")
            return True
        
        # 移動先にアイテムがある場合（スワップ）
        temp_item = from_slot_obj.item_instance
        from_slot_obj.item_instance = to_slot_obj.item_instance
        to_slot_obj.item_instance = temp_item
        logger.debug(f"アイテムをスワップ: スロット{from_slot} ⇄ スロット{to_slot}")
        return True
    
    def sort_items(self):
        """アイテムをソート（アイテムタイプ→ID順）"""
        # 全アイテムを取得
        items = []
        for slot in self.slots:
            if not slot.is_empty():
                items.append(slot.item_instance)
                slot.item_instance = None
        
        # ソート（アイテムタイプ→ID順）
        def sort_key(item_instance):
            item = self.item_manager.get_item(item_instance.item_id)
            if item:
                return (item.item_type.value, item.item_id)
            return ('zzz', item_instance.item_id)
        
        items.sort(key=sort_key)
        
        # 再配置
        for i, item_instance in enumerate(items):
            if i < len(self.slots):
                self.slots[i].item_instance = item_instance
        
        logger.debug("インベントリをソートしました")
    
    def get_total_weight(self) -> float:
        """総重量を取得"""
        total_weight = 0.0
        for slot in self.slots:
            if not slot.is_empty():
                item = self.item_manager.get_item(slot.item_instance.item_id)
                if item:
                    total_weight += item.weight * slot.item_instance.quantity
        return total_weight
    
    def get_total_value(self) -> int:
        """総価値を取得"""
        total_value = 0
        for slot in self.slots:
            if not slot.is_empty():
                item = self.item_manager.get_item(slot.item_instance.item_id)
                if item:
                    total_value += item.price * slot.item_instance.quantity
        return total_value
    
    def to_dict(self) -> Dict[str, Any]:
        """辞書形式でシリアライズ"""
        return {
            'owner_id': self.owner_id,
            'inventory_type': self.inventory_type.value,
            'max_slots': self.max_slots,
            'slots': [slot.to_dict() for slot in self.slots]
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Inventory':
        """辞書からデシリアライズ"""
        inventory = cls(
            owner_id=data.get('owner_id', ''),
            inventory_type=InventorySlotType(data.get('inventory_type', 'character')),
            max_slots=data.get('max_slots', 10)
        )
        
        # スロットデータを復元
        slots_data = data.get('slots', [])
        inventory.slots = []
        for slot_data in slots_data:
            inventory.slots.append(InventorySlot.from_dict(slot_data))
        
        # スロット数が足りない場合は空のスロットで埋める
        while len(inventory.slots) < inventory.max_slots:
            inventory.slots.append(InventorySlot(slot_type=inventory.inventory_type))
        
        return inventory


class InventoryManager:
    """インベントリ管理システム"""
    
    def __init__(self):
        self.character_inventories: Dict[str, Inventory] = {}
        self.party_inventory: Optional[Inventory] = None
        
        logger.info("InventoryManagerを初期化しました")
    
    def create_character_inventory(self, character_id: str) -> Inventory:
        """キャラクター用インベントリを作成"""
        inventory = Inventory(
            owner_id=character_id,
            inventory_type=InventorySlotType.CHARACTER,
            max_slots=10
        )
        self.character_inventories[character_id] = inventory
        logger.info(f"キャラクターインベントリを作成: {character_id}")
        return inventory
    
    def create_party_inventory(self, party_id: str) -> Inventory:
        """パーティ用インベントリを作成"""
        self.party_inventory = Inventory(
            owner_id=party_id,
            inventory_type=InventorySlotType.PARTY,
            max_slots=50  # パーティは大容量
        )
        logger.info(f"パーティインベントリを作成: {party_id}")
        return self.party_inventory
    
    def get_character_inventory(self, character_id: str) -> Optional[Inventory]:
        """キャラクターインベントリを取得"""
        return self.character_inventories.get(character_id)
    
    def get_party_inventory(self) -> Optional[Inventory]:
        """パーティインベントリを取得"""
        return self.party_inventory
    
    def transfer_item(self, from_inventory: Inventory, from_slot: int, 
                     to_inventory: Inventory, quantity: int = None) -> bool:
        """インベントリ間でアイテムを移動"""
        # アイテムを取得
        removed_item = from_inventory.remove_item(from_slot, quantity)
        if not removed_item:
            return False
        
        # 移動先に追加
        if to_inventory.add_item(removed_item):
            logger.debug(f"アイテムを移動: {removed_item.item_id} x{removed_item.quantity}")
            return True
        else:
            # 追加に失敗した場合は元に戻す
            from_inventory.add_item(removed_item)
            return False
    
    def to_dict(self) -> Dict[str, Any]:
        """辞書形式でシリアライズ"""
        return {
            'character_inventories': {
                char_id: inventory.to_dict() 
                for char_id, inventory in self.character_inventories.items()
            },
            'party_inventory': self.party_inventory.to_dict() if self.party_inventory else None
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'InventoryManager':
        """辞書からデシリアライズ"""
        manager = cls()
        
        # キャラクターインベントリを復元
        char_inventories_data = data.get('character_inventories', {})
        for char_id, inventory_data in char_inventories_data.items():
            manager.character_inventories[char_id] = Inventory.from_dict(inventory_data)
        
        # パーティインベントリを復元
        party_inventory_data = data.get('party_inventory')
        if party_inventory_data:
            manager.party_inventory = Inventory.from_dict(party_inventory_data)
        
        return manager


# グローバルインスタンス
inventory_manager = InventoryManager()