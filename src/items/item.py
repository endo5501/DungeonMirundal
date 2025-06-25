"""アイテムシステム"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Union
from enum import Enum
import uuid

from src.core.config_manager import config_manager
from src.utils.logger import logger

# アイテムシステム定数
DEFAULT_SELL_RATIO = 0.5
DEFAULT_REPAIR_RATIO = 0.3
DEFAULT_IDENTIFICATION_COST = 100
PERFECT_CONDITION = 1.0
DEFAULT_QUANTITY = 1
MINIMUM_PRICE = 1
CONDITION_EXCELLENT = 0.8
CONDITION_GOOD = 0.6
CONDITION_DAMAGED = 0.4
FALLBACK_LANGUAGE = 'ja'
FIRST_ELEMENT_INDEX = 0


class ItemType(Enum):
    """アイテムタイプ"""
    WEAPON = "weapon"
    ARMOR = "armor"
    CONSUMABLE = "consumable"
    SPELLBOOK = "spellbook"
    TOOL = "tool"
    TREASURE = "treasure"


class ItemRarity(Enum):
    """アイテム希少度"""
    COMMON = "common"
    UNCOMMON = "uncommon"
    RARE = "rare"
    EPIC = "epic"
    LEGENDARY = "legendary"


@dataclass
class ItemInstance:
    """アイテムインスタンス（個別のアイテム）"""
    instance_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    item_id: str = ""
    quantity: int = 1
    identified: bool = True
    condition: float = 1.0  # 0.0-1.0, 耐久度
    enchantments: List[str] = field(default_factory=list)
    custom_properties: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """辞書形式でシリアライズ"""
        return {
            'instance_id': self.instance_id,
            'item_id': self.item_id,
            'quantity': self.quantity,
            'identified': self.identified,
            'condition': self.condition,
            'enchantments': self.enchantments.copy(),
            'custom_properties': self.custom_properties.copy()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ItemInstance':
        """辞書からデシリアライズ"""
        return cls(
            instance_id=data.get('instance_id', str(uuid.uuid4())),
            item_id=data.get('item_id', ''),
            quantity=data.get('quantity', DEFAULT_QUANTITY),
            identified=data.get('identified', True),
            condition=data.get('condition', PERFECT_CONDITION),
            enchantments=data.get('enchantments', []),
            custom_properties=data.get('custom_properties', {})
        )


class Item:
    """アイテムクラス"""
    
    def __init__(self, item_id: str, item_data: Dict[str, Any]):
        self.item_id = item_id
        self.item_data = item_data.copy()
        
        # 基本プロパティ
        self.name_key = item_data.get('name_key', f'item.{item_id}')
        self.description_key = item_data.get('description_key', f'item.{item_id}_desc')
        self.item_type = ItemType(item_data.get('type', 'treasure'))
        self.price = item_data.get('price', 0)
        self.weight = item_data.get('weight', 1)
        self.rarity = ItemRarity(item_data.get('rarity', 'common'))
        
        # クラス制限
        self.usable_classes = item_data.get('usable_classes', [])
        self.required_class = item_data.get('required_class', [])
        
        # 戦闘関連
        self.usable_in_combat = item_data.get('usable_in_combat', False)
        
        logger.debug(f"アイテムを初期化: {item_id} ({self.item_type.value})")
    
    def get_name(self) -> str:
        """アイテム名を取得"""
        # 新しい多言語対応形式をチェック
        if 'names' in self.item_data:
            return self._get_localized_text('names')
        
        # 従来の形式にフォールバック
        return config_manager.get_text(self.name_key)
    
    def get_description(self) -> str:
        """アイテム説明を取得"""
        # 新しい多言語対応形式をチェック
        if 'descriptions' in self.item_data:
            return self._get_localized_text('descriptions')
        
        # 従来の形式にフォールバック
        return config_manager.get_text(self.description_key)
    
    def _get_localized_text(self, field_name: str) -> str:
        """ローカライズされたテキストを取得"""
        current_language = getattr(config_manager, 'current_language', FALLBACK_LANGUAGE)
        text_data = self.item_data[field_name]
        
        if current_language in text_data:
            return text_data[current_language]
        elif FALLBACK_LANGUAGE in text_data:
            return text_data[FALLBACK_LANGUAGE]
        elif text_data:
            return list(text_data.values())[FIRST_ELEMENT_INDEX]
        
        return ''
    
    def can_use(self, character_class: str) -> bool:
        """指定されたクラスが使用可能かチェック"""
        if self.usable_classes and character_class not in self.usable_classes:
            return False
        
        if self.required_class and character_class not in self.required_class:
            return False
        
        return True
    
    def is_weapon(self) -> bool:
        """武器かどうか"""
        return self.item_type == ItemType.WEAPON
    
    def is_armor(self) -> bool:
        """防具かどうか"""
        return self.item_type == ItemType.ARMOR
    
    def is_consumable(self) -> bool:
        """消費アイテムかどうか"""
        return self.item_type == ItemType.CONSUMABLE
    
    def is_spellbook(self) -> bool:
        """魔法書かどうか"""
        return self.item_type == ItemType.SPELLBOOK
    
    def get_attack_power(self) -> int:
        """攻撃力を取得（武器の場合）"""
        return self.item_data.get('attack_power', 0)
    
    def get_defense(self) -> int:
        """防御力を取得（防具の場合）"""
        return self.item_data.get('defense', 0)
    
    def get_attribute(self) -> str:
        """属性を取得"""
        return self.item_data.get('attribute', 'physical')
    
    def get_effect_type(self) -> str:
        """効果タイプを取得（消費アイテムの場合）"""
        return self.item_data.get('effect_type', '')
    
    def get_effect_value(self) -> int:
        """効果値を取得（消費アイテムの場合）"""
        return self.item_data.get('effect_value', 0)
    
    def get_spell_id(self) -> str:
        """魔法IDを取得（魔法書の場合）"""
        return self.item_data.get('spell_id', '')
    
    def get_sell_price(self, sell_ratio: float = DEFAULT_SELL_RATIO) -> int:
        """売却価格を取得"""
        return int(self.price * sell_ratio)
    
    def create_instance(self, quantity: int = DEFAULT_QUANTITY, identified: bool = True) -> ItemInstance:
        """アイテムインスタンスを作成"""
        return ItemInstance(
            item_id=self.item_id,
            quantity=quantity,
            identified=identified
        )


class ItemManager:
    """アイテム管理システム"""
    
    def __init__(self):
        self.items: Dict[str, Item] = {}
        self.item_config = {}
        
        self._load_items()
        logger.info("ItemManagerを初期化しました")
    
    def _load_items(self):
        """アイテム定義の読み込み"""
        self.item_config = config_manager.load_config("items")
        
        # 各カテゴリのアイテムを読み込み
        for category in ['weapons', 'armor', 'consumables', 'spellbooks', 'special']:
            category_items = self.item_config.get(category, {})
            
            for item_id, item_data in category_items.items():
                item = Item(item_id, item_data)
                self.items[item_id] = item
        
        logger.info(f"{len(self.items)} 個のアイテムを読み込みました")
    
    def get_item(self, item_id: str) -> Optional[Item]:
        """アイテムを取得"""
        return self.items.get(item_id)
    
    def get_items_by_type(self, item_type: ItemType) -> List[Item]:
        """タイプ別アイテム一覧を取得"""
        return [item for item in self.items.values() if item.item_type == item_type]
    
    def get_items_by_class(self, character_class: str) -> List[Item]:
        """クラス別使用可能アイテム一覧を取得"""
        return [item for item in self.items.values() if item.can_use(character_class)]
    
    def create_item_instance(self, item_id: str, quantity: int = 1, identified: bool = True) -> Optional[ItemInstance]:
        """アイテムインスタンスを作成"""
        item = self.get_item(item_id)
        if item:
            return item.create_instance(quantity, identified)
        
        logger.warning(f"アイテムが見つかりません: {item_id}")
        return None
    
    def get_item_info(self, instance: ItemInstance) -> Optional[Item]:
        """インスタンスからアイテム情報を取得"""
        return self.get_item(instance.item_id)
    
    def get_item_display_name(self, instance: ItemInstance) -> str:
        """表示名を取得"""
        item = self.get_item_info(instance)
        if not item:
            return "Unknown Item"
        
        name = item.get_name()
        
        # 未鑑定の場合
        if not instance.identified:
            name = f"?{name}?"
        
        # 数量表示
        if instance.quantity > 1:
            name = f"{name} x{instance.quantity}"
        
        # 状態表示
        if instance.condition < 1.0:
            condition_text = ""
            if instance.condition >= 0.8:
                condition_text = " (良好)"
            elif instance.condition >= 0.6:
                condition_text = " (普通)"
            elif instance.condition >= 0.4:
                condition_text = " (損傷)"
            else:
                condition_text = " (破損)"
            name += condition_text
        
        return name
    
    def get_sell_price(self, instance: ItemInstance) -> int:
        """売却価格を取得"""
        item = self.get_item_info(instance)
        if not item:
            return 0
        
        pricing = self.item_config.get('pricing', {})
        sell_ratio = pricing.get('base_sell_ratio', DEFAULT_SELL_RATIO)
        
        # 状態による価格補正
        condition_modifier = instance.condition
        
        base_price = item.get_sell_price(sell_ratio)
        final_price = int(base_price * condition_modifier * instance.quantity)
        
        return max(MINIMUM_PRICE, final_price)
    
    def get_identification_cost(self) -> int:
        """鑑定費用を取得"""
        pricing = self.item_config.get('pricing', {})
        return pricing.get('identification_cost', DEFAULT_IDENTIFICATION_COST)
    
    def identify_item(self, instance: ItemInstance) -> bool:
        """アイテムを鑑定"""
        if instance.identified:
            return False
        
        instance.identified = True
        logger.info(f"アイテムを鑑定しました: {instance.item_id}")
        return True
    
    def repair_item(self, instance: ItemInstance) -> int:
        """アイテム修理費用を計算"""
        if instance.condition >= 1.0:
            return 0
        
        item = self.get_item_info(instance)
        if not item:
            return 0
        
        pricing = self.item_config.get('pricing', {})
        repair_ratio = pricing.get('repair_cost_ratio', DEFAULT_REPAIR_RATIO)
        
        damage_amount = PERFECT_CONDITION - instance.condition
        repair_cost = int(item.price * repair_ratio * damage_amount)
        
        return max(MINIMUM_PRICE, repair_cost)
    
    def perform_repair(self, instance: ItemInstance) -> bool:
        """アイテム修理を実行"""
        if instance.condition >= 1.0:
            return False
        
        instance.condition = PERFECT_CONDITION
        logger.info(f"アイテムを修理しました: {instance.item_id}")
        return True
    
    def reload_items(self):
        """アイテム定義の再読み込み"""
        self.items.clear()
        self._load_items()
        logger.info("アイテム定義を再読み込みしました")


# グローバルインスタンス
item_manager = ItemManager()