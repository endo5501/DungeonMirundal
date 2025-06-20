"""宿屋倉庫システム"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
import uuid

from src.inventory.inventory import Inventory, InventorySlot, InventoryManager
from src.items.item import ItemInstance, item_manager
from src.utils.logger import logger


@dataclass
class InnStorage:
    """宿屋倉庫"""
    storage_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    capacity: int = 100  # 倉庫容量（パーティインベントリより大きく）
    slots: List[InventorySlot] = field(default_factory=list)
    
    def __post_init__(self):
        """初期化後処理"""
        if not self.slots:
            self.slots = [InventorySlot() for _ in range(self.capacity)]
        logger.debug(f"宿屋倉庫を初期化: {self.storage_id} (容量: {self.capacity})")
    
    def add_item(self, item_instance: ItemInstance) -> bool:
        """アイテムを倉庫に追加"""
        # 同種アイテムのスタック可能性をチェック
        if item_instance.stackable:
            for slot in self.slots:
                if (not slot.is_empty() and 
                    slot.item_instance.item_id == item_instance.item_id and
                    slot.item_instance.identified == item_instance.identified):
                    
                    # スタック追加
                    slot.item_instance.quantity += item_instance.quantity
                    logger.debug(f"宿屋倉庫でアイテムをスタック: {item_instance.item_id} +{item_instance.quantity}")
                    return True
        
        # 新しいスロットに追加
        for slot in self.slots:
            if slot.is_empty():
                slot.add_item(item_instance)
                logger.info(f"宿屋倉庫にアイテム追加: {item_instance.item_id} x{item_instance.quantity}")
                return True
        
        logger.warning("宿屋倉庫が満杯です")
        return False
    
    def remove_item(self, slot_index: int, quantity: int = 1) -> Optional[ItemInstance]:
        """アイテムを倉庫から削除"""
        if slot_index < 0 or slot_index >= len(self.slots):
            return None
        
        slot = self.slots[slot_index]
        if slot.is_empty():
            return None
        
        item_instance = slot.item_instance
        if quantity >= item_instance.quantity:
            # 全て削除
            removed_item = item_instance
            slot.remove_item()
            logger.info(f"宿屋倉庫からアイテム削除: {removed_item.item_id} x{removed_item.quantity}")
            return removed_item
        else:
            # 一部削除
            item_instance.quantity -= quantity
            removed_item = ItemInstance(
                item_id=item_instance.item_id,
                quantity=quantity,
                identified=item_instance.identified,
                condition=item_instance.condition
            )
            logger.info(f"宿屋倉庫からアイテム一部削除: {removed_item.item_id} x{quantity}")
            return removed_item
    
    def get_item_at_slot(self, slot_index: int) -> Optional[ItemInstance]:
        """指定スロットのアイテムを取得"""
        if slot_index < 0 or slot_index >= len(self.slots):
            return None
        
        slot = self.slots[slot_index]
        return slot.item_instance if not slot.is_empty() else None
    
    def get_used_slots_count(self) -> int:
        """使用中スロット数を取得"""
        return sum(1 for slot in self.slots if not slot.is_empty())
    
    def get_free_slots_count(self) -> int:
        """空きスロット数を取得"""
        return self.capacity - self.get_used_slots_count()
    
    def get_all_items(self) -> List[tuple]:
        """全アイテムを(slot_index, item_instance)のタプルで取得"""
        items = []
        for i, slot in enumerate(self.slots):
            if not slot.is_empty():
                items.append((i, slot.item_instance))
        return items
    
    def is_full(self) -> bool:
        """倉庫が満杯かチェック"""
        return self.get_free_slots_count() == 0
    
    def clear(self):
        """倉庫を空にする"""
        for slot in self.slots:
            slot.remove_item()
        logger.info(f"宿屋倉庫をクリア: {self.storage_id}")
    
    def to_dict(self) -> Dict[str, Any]:
        """辞書形式でシリアライズ"""
        return {
            'storage_id': self.storage_id,
            'capacity': self.capacity,
            'slots': [slot.to_dict() for slot in self.slots]
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'InnStorage':
        """辞書からデシリアライズ"""
        storage = cls(
            storage_id=data.get('storage_id', str(uuid.uuid4())),
            capacity=data.get('capacity', 100)
        )
        
        # スロットを復元
        slots_data = data.get('slots', [])
        storage.slots = [InventorySlot.from_dict(slot_data) for slot_data in slots_data]
        
        # 容量に合わせてスロット数を調整
        while len(storage.slots) < storage.capacity:
            storage.slots.append(InventorySlot())
        
        return storage


class InnStorageManager:
    """宿屋倉庫管理システム"""
    
    def __init__(self):
        self._storage: Optional[InnStorage] = None
        logger.info("宿屋倉庫管理システムを初期化")
    
    def get_storage(self) -> InnStorage:
        """宿屋倉庫を取得（遅延初期化）"""
        if self._storage is None:
            self._storage = InnStorage()
            logger.info("宿屋倉庫を作成")
        return self._storage
    
    def transfer_from_party_inventory(self, party) -> int:
        """パーティインベントリから宿屋倉庫に全アイテムを移動"""
        storage = self.get_storage()
        party_inventory = party.get_party_inventory()
        
        if not party_inventory:
            logger.warning("パーティインベントリが見つかりません")
            return 0
        
        transferred_count = 0
        
        # パーティインベントリの全アイテムを倉庫に移動
        for slot in party_inventory.slots:
            if not slot.is_empty():
                item_instance = slot.item_instance
                if storage.add_item(item_instance):
                    slot.remove_item()  # パーティインベントリから削除
                    transferred_count += 1
                else:
                    logger.warning(f"宿屋倉庫への移動失敗: {item_instance.item_id}")
                    break
        
        logger.info(f"パーティインベントリから宿屋倉庫に {transferred_count} 個のアイテムを移動")
        return transferred_count
    
    def transfer_to_character_inventory(self, character, slot_index: int, quantity: int = 1) -> bool:
        """宿屋倉庫からキャラクターインベントリにアイテムを移動"""
        storage = self.get_storage()
        
        # 倉庫からアイテムを取得
        removed_item = storage.remove_item(slot_index, quantity)
        if not removed_item:
            logger.warning(f"宿屋倉庫のスロット {slot_index} からアイテム取得失敗")
            return False
        
        # キャラクターインベントリに追加
        character_inventory = character.get_inventory()
        if character_inventory.add_item(removed_item):
            logger.info(f"宿屋倉庫からキャラクター {character.name} に移動: {removed_item.item_id} x{quantity}")
            return True
        else:
            # キャラクターインベントリが満杯の場合、倉庫に戻す
            storage.add_item(removed_item)
            logger.warning(f"キャラクター {character.name} のインベントリが満杯です")
            return False
    
    def transfer_from_character_inventory(self, character, char_slot_index: int, quantity: int = 1) -> bool:
        """キャラクターインベントリから宿屋倉庫にアイテムを移動"""
        storage = self.get_storage()
        character_inventory = character.get_inventory()
        
        # キャラクターインベントリからアイテムを取得
        removed_item = character_inventory.remove_item(char_slot_index, quantity)
        if not removed_item:
            logger.warning(f"キャラクター {character.name} のスロット {char_slot_index} からアイテム取得失敗")
            return False
        
        # 宿屋倉庫に追加
        if storage.add_item(removed_item):
            logger.info(f"キャラクター {character.name} から宿屋倉庫に移動: {removed_item.item_id} x{quantity}")
            return True
        else:
            # 宿屋倉庫が満杯の場合、キャラクターインベントリに戻す
            character_inventory.add_item(removed_item)
            logger.warning("宿屋倉庫が満杯です")
            return False
    
    def get_storage_summary(self) -> Dict[str, Any]:
        """倉庫の要約情報を取得"""
        storage = self.get_storage()
        used_slots = storage.get_used_slots_count()
        
        return {
            'capacity': storage.capacity,
            'used_slots': used_slots,
            'free_slots': storage.get_free_slots_count(),
            'usage_percentage': (used_slots / storage.capacity) * 100
        }
    
    def save_storage_data(self) -> Dict[str, Any]:
        """倉庫データを保存用辞書で取得"""
        if self._storage:
            return self._storage.to_dict()
        return {}
    
    def load_storage_data(self, data: Dict[str, Any]):
        """倉庫データを読み込み"""
        if data:
            self._storage = InnStorage.from_dict(data)
            logger.info("宿屋倉庫データを読み込み")
        else:
            self._storage = None
            logger.info("宿屋倉庫データなし - 新規作成")


# グローバルインスタンス
inn_storage_manager = InnStorageManager()