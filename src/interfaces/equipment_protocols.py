"""
装備システムProtocol定義

装備アイテム、消費アイテム、装備管理で使用される型安全なインターフェースを定義します。
装備アイテムの特性チェックで使用されるhasattrパターンを型安全な呼び出しに置き換えます。
"""

from typing import Protocol, Any, Dict, Optional, List, TYPE_CHECKING, runtime_checkable

if TYPE_CHECKING:
    from typing import Any as Character


@runtime_checkable
class EquippableItem(Protocol):
    """装備可能アイテムのインターフェース"""
    
    def can_equip(self, character: "Character") -> bool:
        """キャラクターが装備可能かチェック"""
        ...
    
    def get_slot_type(self) -> str:
        """装備スロットタイプを取得"""
        ...
    
    def get_stats_bonus(self) -> Dict[str, int]:
        """装備時のステータスボーナスを取得"""
        ...


@runtime_checkable
class ConsumableItem(Protocol):
    """消費可能アイテムのインターフェース"""
    
    def can_use(self, character: "Character") -> bool:
        """キャラクターが使用可能かチェック"""
        ...
    
    def use_item(self, character: "Character") -> Dict[str, Any]:
        """アイテムを使用"""
        ...
    
    def get_effect_description(self) -> str:
        """効果説明を取得"""
        ...


@runtime_checkable
class EnchantableItem(Protocol):
    """エンチャント可能アイテムのインターフェース"""
    
    def can_enchant(self) -> bool:
        """エンチャント可能かチェック"""
        ...
    
    def add_enchantment(self, enchantment_id: str) -> bool:
        """エンチャントを追加"""
        ...
    
    def get_enchantments(self) -> List[str]:
        """エンチャント一覧を取得"""
        ...


@runtime_checkable
class ItemContainer(Protocol):
    """アイテム格納可能なコンテナ"""
    
    def add_item(self, item_id: str, quantity: int = 1) -> bool:
        """アイテムを追加"""
        ...
    
    def remove_item(self, item_id: str, quantity: int = 1) -> bool:
        """アイテムを削除"""
        ...
    
    def has_item(self, item_id: str, quantity: int = 1) -> bool:
        """アイテムを所持しているかチェック"""
        ...
    
    def get_item_count(self, item_id: str) -> int:
        """アイテム数を取得"""
        ...


@runtime_checkable
class EquipmentSlots(Protocol):
    """装備スロット管理インターフェース"""
    
    def equip_item(self, slot: str, item: EquippableItem) -> bool:
        """アイテムを装備"""
        ...
    
    def unequip_item(self, slot: str) -> Optional[EquippableItem]:
        """アイテムを装備解除"""
        ...
    
    def get_equipped_item(self, slot: str) -> Optional[EquippableItem]:
        """装備中のアイテムを取得"""
        ...
    
    def get_available_slots(self) -> List[str]:
        """利用可能なスロット一覧を取得"""
        ...


@runtime_checkable
class EquipmentManager(Protocol):
    """装備管理インターフェース"""
    
    def get_character_equipment(self, character: "Character") -> Dict[str, EquippableItem]:
        """キャラクターの装備を取得"""
        ...
    
    def calculate_total_stats(self, character: "Character") -> Dict[str, int]:
        """装備込みの総合ステータスを計算"""
        ...
    
    def validate_equipment_compatibility(self, character: "Character", item: EquippableItem) -> bool:
        """装備互換性を検証"""
        ...


# 複合Protocol（複数機能の組み合わせ）

class WeaponItem(EquippableItem, EnchantableItem, Protocol):
    """武器アイテムのインターフェース"""
    
    def get_damage_range(self) -> tuple[int, int]:
        """ダメージ範囲を取得"""
        ...
    
    def get_attack_speed(self) -> float:
        """攻撃速度を取得"""
        ...


class ArmorItem(EquippableItem, EnchantableItem, Protocol):
    """防具アイテムのインターフェース"""
    
    def get_defense_value(self) -> int:
        """防御力を取得"""
        ...
    
    def get_resistance(self) -> Dict[str, int]:
        """属性耐性を取得"""
        ...


class MagicalItem(EquippableItem, ConsumableItem, Protocol):
    """魔法アイテムのインターフェース"""
    
    def get_magic_power(self) -> int:
        """魔力を取得"""
        ...
    
    def get_spell_effects(self) -> List[str]:
        """呪文効果一覧を取得"""
        ...