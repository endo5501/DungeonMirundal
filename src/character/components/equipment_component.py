"""装備コンポーネント

キャラクターの装備機能を独立したコンポーネントとして実装。
Fowlerの「Extract Class」パターンを適用。
"""

from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from src.character.components.base_component import CharacterComponent, ComponentType, ComponentData
from src.utils.logger import logger


@dataclass
class EquipmentSlot:
    """装備スロット"""
    slot_id: str
    slot_name: str
    item_id: Optional[str] = None
    item_name: Optional[str] = None
    equipped_at: Optional[str] = None  # 装備した時刻


@dataclass
class EquipmentData(ComponentData):
    """装備データ"""
    equipment_slots: Dict[str, EquipmentSlot] = field(default_factory=dict)
    
    def __post_init__(self):
        super().__post_init__()
        self.component_type = ComponentType.EQUIPMENT
    
    def to_dict(self) -> Dict[str, Any]:
        base_dict = super().to_dict()
        base_dict.update({
            'equipment_slots': {
                slot_id: {
                    'slot_id': slot.slot_id,
                    'slot_name': slot.slot_name,
                    'item_id': slot.item_id,
                    'item_name': slot.item_name,
                    'equipped_at': slot.equipped_at
                }
                for slot_id, slot in self.equipment_slots.items()
            }
        })
        return base_dict
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'EquipmentData':
        equipment_slots = {}
        slots_data = data.get('equipment_slots', {})
        
        for slot_id, slot_data in slots_data.items():
            equipment_slots[slot_id] = EquipmentSlot(
                slot_id=slot_data.get('slot_id', slot_id),
                slot_name=slot_data.get('slot_name', slot_id),
                item_id=slot_data.get('item_id'),
                item_name=slot_data.get('item_name'),
                equipped_at=slot_data.get('equipped_at')
            )
        
        return cls(
            component_type=ComponentType.EQUIPMENT,
            initialized=data.get('initialized', False),
            equipment_slots=equipment_slots
        )


class EquipmentComponent(CharacterComponent):
    """装備管理コンポーネント"""
    
    def __init__(self, owner):
        super().__init__(owner, ComponentType.EQUIPMENT)
        self._equipment_data: Optional[EquipmentData] = None
    
    def initialize(self) -> bool:
        """装備システムを初期化"""
        try:
            if self.initialized:
                return True
            
            # デフォルトの装備スロットを設定
            default_slots = self._get_default_equipment_slots()
            self._equipment_data = EquipmentData(
                equipment_slots=default_slots,
                initialized=True
            )
            
            # 既存の装備データを移行（互換性のため）
            self._migrate_legacy_equipment()
            
            self.initialized = True
            self.set_data(self._equipment_data)
            
            logger.info(f"装備システム初期化完了: {self.owner.name}")
            return True
            
        except Exception as e:
            logger.error(f"装備システム初期化エラー ({self.owner.name}): {e}")
            return False
    
    def cleanup(self):
        """装備システムのクリーンアップ"""
        self._equipment_data = None
        self.initialized = False
    
    def _get_default_equipment_slots(self) -> Dict[str, EquipmentSlot]:
        """デフォルトの装備スロットを取得"""
        default_slots = {
            'weapon': EquipmentSlot('weapon', '武器'),
            'armor': EquipmentSlot('armor', '鎧'),
            'shield': EquipmentSlot('shield', '盾'),
            'helmet': EquipmentSlot('helmet', '兜'),
            'gloves': EquipmentSlot('gloves', '手袋'),
            'boots': EquipmentSlot('boots', '靴'),
            'ring1': EquipmentSlot('ring1', '指輪1'),
            'ring2': EquipmentSlot('ring2', '指輪2'),
            'accessory': EquipmentSlot('accessory', '装身具')
        }
        
        # 職業に応じた装備スロットのカスタマイズ
        character_class = getattr(self.owner, 'character_class', 'fighter')
        
        if character_class in ['mage', 'wizard']:
            default_slots['focus'] = EquipmentSlot('focus', '触媒')
        elif character_class in ['thief', 'rogue']:
            default_slots['tool'] = EquipmentSlot('tool', '道具')
        elif character_class in ['priest', 'cleric']:
            default_slots['holy_symbol'] = EquipmentSlot('holy_symbol', '聖印')
        
        return default_slots
    
    def _migrate_legacy_equipment(self):
        """既存の装備データを新システムに移行"""
        if not hasattr(self.owner, 'equipped_items') or not self.owner.equipped_items:
            return
        
        logger.info(f"装備データ移行開始: {self.owner.name}")
        
        for slot_id, item_id in self.owner.equipped_items.items():
            if slot_id in self._equipment_data.equipment_slots and item_id:
                self.equip_item(slot_id, item_id, item_id)  # item_nameも同じにする
        
        logger.info(f"装備データ移行完了: {self.owner.name}")
    
    def equip_item(self, slot_id: str, item_id: str, item_name: str = None) -> bool:
        """アイテムを装備"""
        if not self.ensure_initialized():
            return False
        
        if slot_id not in self._equipment_data.equipment_slots:
            logger.warning(f"未知の装備スロット: {slot_id}")
            return False
        
        # 現在装備されているアイテムを外す
        old_item = self.unequip_item(slot_id)
        
        # 新しいアイテムを装備
        slot = self._equipment_data.equipment_slots[slot_id]
        slot.item_id = item_id
        slot.item_name = item_name or item_id
        
        from datetime import datetime
        slot.equipped_at = datetime.now().isoformat()
        
        logger.info(f"装備変更: {self.owner.name} - {slot.slot_name}: {slot.item_name}")
        
        # 装備変更イベントを発行
        self._publish_equipment_changed_event(slot_id, item_id, old_item)
        
        return True
    
    def unequip_item(self, slot_id: str) -> Optional[str]:
        """アイテムを外す"""
        if not self.ensure_initialized():
            return None
        
        if slot_id not in self._equipment_data.equipment_slots:
            return None
        
        slot = self._equipment_data.equipment_slots[slot_id]
        old_item_id = slot.item_id
        
        if old_item_id:
            slot.item_id = None
            slot.item_name = None
            slot.equipped_at = None
            
            logger.info(f"装備解除: {self.owner.name} - {slot.slot_name}")
            
            # 装備変更イベントを発行
            self._publish_equipment_changed_event(slot_id, None, old_item_id)
        
        return old_item_id
    
    def get_equipped_item(self, slot_id: str) -> Optional[EquipmentSlot]:
        """指定スロットの装備アイテムを取得"""
        if not self.ensure_initialized():
            return None
        
        return self._equipment_data.equipment_slots.get(slot_id)
    
    def get_all_equipped_items(self) -> Dict[str, EquipmentSlot]:
        """装備中の全アイテムを取得"""
        if not self.ensure_initialized():
            return {}
        
        equipped_items = {}
        for slot_id, slot in self._equipment_data.equipment_slots.items():
            if slot.item_id:
                equipped_items[slot_id] = slot
        
        return equipped_items
    
    def is_slot_empty(self, slot_id: str) -> bool:
        """指定スロットが空かどうか"""
        slot = self.get_equipped_item(slot_id)
        return slot is None or slot.item_id is None
    
    def get_available_slots(self) -> List[str]:
        """利用可能な装備スロット一覧を取得"""
        if not self.ensure_initialized():
            return []
        
        return list(self._equipment_data.equipment_slots.keys())
    
    def _publish_equipment_changed_event(self, slot_id: str, new_item_id: Optional[str], old_item_id: Optional[str]):
        """装備変更イベントを発行"""
        try:
            from src.core.event_bus import publish_event, EventType
            
            publish_event(
                EventType.EQUIPMENT_CHANGED,
                f"character_{self.owner.character_id}",
                {
                    'character_id': self.owner.character_id,
                    'character_name': self.owner.name,
                    'slot_id': slot_id,
                    'new_item_id': new_item_id,
                    'old_item_id': old_item_id
                }
            )
        except Exception as e:
            logger.warning(f"装備変更イベント発行エラー: {e}")
    
    def to_dict(self) -> Dict[str, Any]:
        """辞書形式でシリアライズ"""
        if not self._equipment_data:
            return {'initialized': False}
        
        return self._equipment_data.to_dict()
    
    def from_dict(self, data: Dict[str, Any]) -> bool:
        """辞書からデシリアライズ"""
        try:
            self._equipment_data = EquipmentData.from_dict(data)
            self.initialized = self._equipment_data.initialized
            self.set_data(self._equipment_data)
            return True
        except Exception as e:
            logger.error(f"装備データデシリアライズエラー: {e}")
            return False
    
    def __repr__(self) -> str:
        equipped_count = len(self.get_all_equipped_items()) if self.initialized else 0
        return f"EquipmentComponent(owner={self.owner.name}, equipped_items={equipped_count})"