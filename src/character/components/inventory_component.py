"""インベントリコンポーネント

キャラクターのアイテム管理機能を独立したコンポーネントとして実装。
Fowlerの「Extract Class」パターンを適用。
"""

from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass, field
from src.character.components.base_component import CharacterComponent, ComponentType, ComponentData
from src.utils.logger import logger


@dataclass
class InventoryItem:
    """インベントリアイテム"""
    item_id: str
    item_name: str
    quantity: int = 1
    max_stack: int = 99
    category: str = "misc"
    obtained_at: Optional[str] = None
    
    def can_stack_with(self, other: 'InventoryItem') -> bool:
        """他のアイテムとスタック可能かチェック"""
        return (self.item_id == other.item_id and 
                self.item_name == other.item_name and
                self.category == other.category)
    
    def add_quantity(self, amount: int) -> int:
        """数量を追加し、オーバーフロー分を返す"""
        old_quantity = self.quantity
        self.quantity = min(self.quantity + amount, self.max_stack)
        return amount - (self.quantity - old_quantity)
    
    def remove_quantity(self, amount: int) -> int:
        """数量を削除し、実際に削除された数を返す"""
        removed = min(amount, self.quantity)
        self.quantity -= removed
        return removed


@dataclass
class InventoryData(ComponentData):
    """インベントリデータ"""
    items: Dict[str, InventoryItem] = field(default_factory=dict)
    max_slots: int = 50
    current_slots: int = 0
    
    def __post_init__(self):
        super().__post_init__()
        self.component_type = ComponentType.INVENTORY
    
    def to_dict(self) -> Dict[str, Any]:
        base_dict = super().to_dict()
        base_dict.update({
            'items': {
                item_id: {
                    'item_id': item.item_id,
                    'item_name': item.item_name,
                    'quantity': item.quantity,
                    'max_stack': item.max_stack,
                    'category': item.category,
                    'obtained_at': item.obtained_at
                }
                for item_id, item in self.items.items()
            },
            'max_slots': self.max_slots,
            'current_slots': self.current_slots
        })
        return base_dict
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'InventoryData':
        items = {}
        items_data = data.get('items', {})
        
        for item_id, item_data in items_data.items():
            items[item_id] = InventoryItem(
                item_id=item_data.get('item_id', item_id),
                item_name=item_data.get('item_name', item_id),
                quantity=item_data.get('quantity', 1),
                max_stack=item_data.get('max_stack', 99),
                category=item_data.get('category', 'misc'),
                obtained_at=item_data.get('obtained_at')
            )
        
        return cls(
            component_type=ComponentType.INVENTORY,
            initialized=data.get('initialized', False),
            items=items,
            max_slots=data.get('max_slots', 50),
            current_slots=data.get('current_slots', 0)
        )


class InventoryComponent(CharacterComponent):
    """インベントリ管理コンポーネント"""
    
    def __init__(self, owner):
        super().__init__(owner, ComponentType.INVENTORY)
        self._inventory_data: Optional[InventoryData] = None
    
    def initialize(self) -> bool:
        """インベントリシステムを初期化"""
        try:
            if self.initialized:
                return True
            
            # 職業に応じたインベントリ容量を設定
            max_slots = self._get_max_slots_for_class()
            
            self._inventory_data = InventoryData(
                max_slots=max_slots,
                current_slots=0,
                initialized=True
            )
            
            # 既存のインベントリデータを移行（互換性のため）
            self._migrate_legacy_inventory()
            
            self.initialized = True
            self.set_data(self._inventory_data)
            
            logger.info(f"インベントリシステム初期化完了: {self.owner.name} ({max_slots}スロット)")
            return True
            
        except Exception as e:
            logger.error(f"インベントリシステム初期化エラー ({self.owner.name}): {e}")
            return False
    
    def cleanup(self):
        """インベントリシステムのクリーンアップ"""
        self._inventory_data = None
        self.initialized = False
    
    def _get_max_slots_for_class(self) -> int:
        """職業に応じた最大スロット数を取得"""
        character_class = getattr(self.owner, 'character_class', 'fighter')
        
        class_slots = {
            'fighter': 40,
            'mage': 35,
            'wizard': 35,
            'thief': 60,  # 盗賊は多く持てる
            'rogue': 60,
            'priest': 45,
            'cleric': 45,
            'ranger': 55,
            'bard': 50
        }
        
        return class_slots.get(character_class, 50)
    
    def _migrate_legacy_inventory(self):
        """既存のインベントリデータを新システムに移行"""
        if not hasattr(self.owner, 'inventory') or not self.owner.inventory:
            return
        
        logger.info(f"インベントリデータ移行開始: {self.owner.name}")
        
        for item_id in self.owner.inventory:
            if item_id:
                self.add_item(item_id, item_id, 1)  # item_nameも同じにする
        
        logger.info(f"インベントリデータ移行完了: {self.owner.name}")
    
    def add_item(self, item_id: str, item_name: str = None, quantity: int = 1, category: str = "misc") -> bool:
        """アイテムを追加"""
        if not self.ensure_initialized():
            return False
        
        if quantity <= 0:
            return False
        
        item_name = item_name or item_id
        
        # 既存アイテムとのスタック処理
        for existing_item in self._inventory_data.items.values():
            if existing_item.item_id == item_id and existing_item.item_name == item_name:
                overflow = existing_item.add_quantity(quantity)
                
                if overflow > 0:
                    # スタック上限を超えた場合、新しいスロットに追加
                    if not self._add_new_item_slot(item_id, item_name, overflow, category):
                        logger.warning(f"インベントリ満杯: {self.owner.name} - {item_name} x{overflow}")
                        return False
                
                self._publish_item_acquired_event(item_id, item_name, quantity)
                return True
        
        # 新しいアイテムとして追加
        return self._add_new_item_slot(item_id, item_name, quantity, category)
    
    def _add_new_item_slot(self, item_id: str, item_name: str, quantity: int, category: str) -> bool:
        """新しいアイテムスロットを追加"""
        if self._inventory_data.current_slots >= self._inventory_data.max_slots:
            return False
        
        # 一意なスロットIDを生成
        slot_id = f"{item_id}_{len(self._inventory_data.items)}"
        
        from datetime import datetime
        new_item = InventoryItem(
            item_id=item_id,
            item_name=item_name,
            quantity=quantity,
            category=category,
            obtained_at=datetime.now().isoformat()
        )
        
        self._inventory_data.items[slot_id] = new_item
        self._inventory_data.current_slots += 1
        
        self._publish_item_acquired_event(item_id, item_name, quantity)
        
        logger.info(f"アイテム追加: {self.owner.name} - {item_name} x{quantity}")
        return True
    
    def remove_item(self, item_id: str, quantity: int = 1) -> int:
        """アイテムを削除し、実際に削除された数を返す"""
        if not self.ensure_initialized():
            return 0
        
        removed_total = 0
        items_to_remove = []
        
        for slot_id, item in self._inventory_data.items.items():
            if item.item_id == item_id and removed_total < quantity:
                need_to_remove = quantity - removed_total
                removed = item.remove_quantity(need_to_remove)
                removed_total += removed
                
                if item.quantity <= 0:
                    items_to_remove.append(slot_id)
        
        # 空になったスロットを削除
        for slot_id in items_to_remove:
            del self._inventory_data.items[slot_id]
            self._inventory_data.current_slots -= 1
        
        if removed_total > 0:
            self._publish_item_used_event(item_id, removed_total)
            logger.info(f"アイテム削除: {self.owner.name} - {item_id} x{removed_total}")
        
        return removed_total
    
    def get_item_quantity(self, item_id: str) -> int:
        """指定アイテムの総数を取得"""
        if not self.ensure_initialized():
            return 0
        
        total = 0
        for item in self._inventory_data.items.values():
            if item.item_id == item_id:
                total += item.quantity
        
        return total
    
    def has_item(self, item_id: str, quantity: int = 1) -> bool:
        """指定数のアイテムを持っているかチェック"""
        return self.get_item_quantity(item_id) >= quantity
    
    def get_all_items(self) -> List[InventoryItem]:
        """全アイテムを取得"""
        if not self.ensure_initialized():
            return []
        
        return list(self._inventory_data.items.values())
    
    def get_items_by_category(self, category: str) -> List[InventoryItem]:
        """カテゴリ別アイテムを取得"""
        if not self.ensure_initialized():
            return []
        
        return [item for item in self._inventory_data.items.values() 
                if item.category == category]
    
    def get_inventory_status(self) -> Dict[str, Any]:
        """インベントリ状況を取得"""
        if not self.ensure_initialized():
            return {'current_slots': 0, 'max_slots': 0, 'usage_rate': 0.0}
        
        usage_rate = (self._inventory_data.current_slots / self._inventory_data.max_slots) * 100
        
        return {
            'current_slots': self._inventory_data.current_slots,
            'max_slots': self._inventory_data.max_slots,
            'usage_rate': usage_rate,
            'total_items': sum(item.quantity for item in self._inventory_data.items.values())
        }
    
    def is_full(self) -> bool:
        """インベントリが満杯かチェック"""
        if not self.ensure_initialized():
            return True
        
        return self._inventory_data.current_slots >= self._inventory_data.max_slots
    
    def _publish_item_acquired_event(self, item_id: str, item_name: str, quantity: int):
        """アイテム取得イベントを発行"""
        try:
            from src.core.event_bus import publish_event, EventType
            
            publish_event(
                EventType.ITEM_ACQUIRED,
                f"character_{self.owner.character_id}",
                {
                    'character_id': self.owner.character_id,
                    'character_name': self.owner.name,
                    'item_id': item_id,
                    'item_name': item_name,
                    'quantity': quantity
                }
            )
        except Exception as e:
            logger.warning(f"アイテム取得イベント発行エラー: {e}")
    
    def _publish_item_used_event(self, item_id: str, quantity: int):
        """アイテム使用イベントを発行"""
        try:
            from src.core.event_bus import publish_event, EventType
            
            publish_event(
                EventType.ITEM_USED,
                f"character_{self.owner.character_id}",
                {
                    'character_id': self.owner.character_id,
                    'character_name': self.owner.name,
                    'item_id': item_id,
                    'quantity': quantity
                }
            )
        except Exception as e:
            logger.warning(f"アイテム使用イベント発行エラー: {e}")
    
    def to_dict(self) -> Dict[str, Any]:
        """辞書形式でシリアライズ"""
        if not self._inventory_data:
            return {'initialized': False}
        
        return self._inventory_data.to_dict()
    
    def from_dict(self, data: Dict[str, Any]) -> bool:
        """辞書からデシリアライズ"""
        try:
            self._inventory_data = InventoryData.from_dict(data)
            self.initialized = self._inventory_data.initialized
            self.set_data(self._inventory_data)
            return True
        except Exception as e:
            logger.error(f"インベントリデータデシリアライズエラー: {e}")
            return False
    
    def __repr__(self) -> str:
        if self.initialized and self._inventory_data:
            return f"InventoryComponent(owner={self.owner.name}, items={self._inventory_data.current_slots}/{self._inventory_data.max_slots})"
        return f"InventoryComponent(owner={self.owner.name}, uninitialized)"