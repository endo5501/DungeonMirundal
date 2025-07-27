"""エンカウンタータイプ固有の処理を管理するストラテジークラス

EncounterManagerの重複コードを解決するため、各エンカウンタータイプの
特殊な処理をストラテジーパターンで分離・統合します。
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any
from enum import Enum
import random

from .encounter_types import EncounterType, EncounterEvent, MonsterGroup
from src.dungeon.dungeon_generator import DungeonAttribute


class EncounterStrategy(ABC):
    """エンカウンタータイプごとの処理を定義する基底クラス"""
    
    @abstractmethod
    def generate_special_abilities(self, attribute: DungeonAttribute, rng: random.Random) -> List[str]:
        """特殊能力を生成する"""
        pass
    
    @abstractmethod
    def apply_special_conditions(self, encounter: EncounterEvent, level: int) -> None:
        """特殊条件を適用する"""
        pass
    
    @abstractmethod
    def get_ability_chance(self) -> float:
        """能力発動の確率を取得する"""
        pass


class NormalEncounterStrategy(EncounterStrategy):
    """通常エンカウンターの処理"""
    
    def generate_special_abilities(self, attribute: DungeonAttribute, rng: random.Random) -> List[str]:
        """通常エンカウンターは属性ベースの能力のみ"""
        return self._generate_attribute_abilities(attribute, rng, self.get_ability_chance())
    
    def apply_special_conditions(self, encounter: EncounterEvent, level: int) -> None:
        """通常エンカウンターは特別な条件なし"""
        pass
    
    def get_ability_chance(self) -> float:
        return 0.3  # ATTRIBUTE_ABILITY_CHANCE
    
    def _generate_attribute_abilities(self, attribute: DungeonAttribute, rng: random.Random, chance: float) -> List[str]:
        """属性ベースの能力生成（共通処理）"""
        abilities = []
        
        attribute_abilities = {
            DungeonAttribute.FIRE: ["fire_breath", "burning_aura"],
            DungeonAttribute.ICE: ["ice_blast", "freezing_touch"],
            DungeonAttribute.LIGHTNING: ["lightning_bolt", "shock_aura"],
            DungeonAttribute.DARK: ["shadow_step", "darkness"],
            DungeonAttribute.LIGHT: ["holy_light", "blessing"]
        }
        
        if attribute in attribute_abilities and rng.random() < chance:
            abilities.append(rng.choice(attribute_abilities[attribute]))
        
        return abilities


class AmbushEncounterStrategy(EncounterStrategy):
    """奇襲エンカウンターの処理"""
    
    def generate_special_abilities(self, attribute: DungeonAttribute, rng: random.Random) -> List[str]:
        """奇襲エンカウンターは属性能力＋奇襲能力"""
        abilities = self._generate_attribute_abilities(attribute, rng, 0.3)
        
        if rng.random() < self.get_ability_chance():
            abilities.append("surprise_attack")
        
        return abilities
    
    def apply_special_conditions(self, encounter: EncounterEvent, level: int) -> None:
        """奇襲エンカウンターの特殊条件"""
        encounter.can_flee = False  # 最初のターンは逃走不可
        encounter.special_conditions["surprise_round"] = True
    
    def get_ability_chance(self) -> float:
        return 0.5  # AMBUSH_ABILITY_CHANCE
    
    def _generate_attribute_abilities(self, attribute: DungeonAttribute, rng: random.Random, chance: float) -> List[str]:
        """属性ベースの能力生成（共通処理）"""
        abilities = []
        
        attribute_abilities = {
            DungeonAttribute.FIRE: ["fire_breath", "burning_aura"],
            DungeonAttribute.ICE: ["ice_blast", "freezing_touch"],
            DungeonAttribute.LIGHTNING: ["lightning_bolt", "shock_aura"],
            DungeonAttribute.DARK: ["shadow_step", "darkness"],
            DungeonAttribute.LIGHT: ["holy_light", "blessing"]
        }
        
        if attribute in attribute_abilities and rng.random() < chance:
            abilities.append(rng.choice(attribute_abilities[attribute]))
        
        return abilities


class TreasureGuardianEncounterStrategy(EncounterStrategy):
    """宝箱守護者エンカウンターの処理"""
    
    def generate_special_abilities(self, attribute: DungeonAttribute, rng: random.Random) -> List[str]:
        """宝箱守護者は属性能力＋宝箱守護能力"""
        abilities = self._generate_attribute_abilities(attribute, rng, 0.3)
        
        if rng.random() < self.get_ability_chance():
            abilities.append("treasure_bond")
        
        return abilities
    
    def apply_special_conditions(self, encounter: EncounterEvent, level: int) -> None:
        """宝箱守護者の特殊条件"""
        encounter.can_negotiate = True
        encounter.special_conditions["guarding_treasure"] = True
    
    def get_ability_chance(self) -> float:
        return 0.7  # TREASURE_GUARDIAN_ABILITY_CHANCE
    
    def _generate_attribute_abilities(self, attribute: DungeonAttribute, rng: random.Random, chance: float) -> List[str]:
        """属性ベースの能力生成（共通処理）"""
        abilities = []
        
        attribute_abilities = {
            DungeonAttribute.FIRE: ["fire_breath", "burning_aura"],
            DungeonAttribute.ICE: ["ice_blast", "freezing_touch"],
            DungeonAttribute.LIGHTNING: ["lightning_bolt", "shock_aura"],
            DungeonAttribute.DARK: ["shadow_step", "darkness"],
            DungeonAttribute.LIGHT: ["holy_light", "blessing"]
        }
        
        if attribute in attribute_abilities and rng.random() < chance:
            abilities.append(rng.choice(attribute_abilities[attribute]))
        
        return abilities


class BossEncounterStrategy(EncounterStrategy):
    """ボスエンカウンターの処理"""
    
    def generate_special_abilities(self, attribute: DungeonAttribute, rng: random.Random) -> List[str]:
        """ボスは強化された属性能力"""
        return self._generate_attribute_abilities(attribute, rng, 0.8)  # 高確率
    
    def apply_special_conditions(self, encounter: EncounterEvent, level: int) -> None:
        """ボスの特殊条件"""
        encounter.can_flee = False
        encounter.special_conditions["boss_battle"] = True
    
    def get_ability_chance(self) -> float:
        return 0.8  # ボス用の高確率
    
    def _generate_attribute_abilities(self, attribute: DungeonAttribute, rng: random.Random, chance: float) -> List[str]:
        """属性ベースの能力生成（共通処理）"""
        abilities = []
        
        attribute_abilities = {
            DungeonAttribute.FIRE: ["fire_breath", "burning_aura"],
            DungeonAttribute.ICE: ["ice_blast", "freezing_touch"],
            DungeonAttribute.LIGHTNING: ["lightning_bolt", "shock_aura"],
            DungeonAttribute.DARK: ["shadow_step", "darkness"],
            DungeonAttribute.LIGHT: ["holy_light", "blessing"]
        }
        
        if attribute in attribute_abilities and rng.random() < chance:
            abilities.append(rng.choice(attribute_abilities[attribute]))
        
        return abilities


class TrapMonsterEncounterStrategy(EncounterStrategy):
    """トラップモンスターエンカウンターの処理"""
    
    def generate_special_abilities(self, attribute: DungeonAttribute, rng: random.Random) -> List[str]:
        """トラップモンスターは属性能力のみ"""
        return self._generate_attribute_abilities(attribute, rng, 0.3)
    
    def apply_special_conditions(self, encounter: EncounterEvent, level: int) -> None:
        """トラップモンスターは特別な条件なし"""
        pass
    
    def get_ability_chance(self) -> float:
        return 0.3
    
    def _generate_attribute_abilities(self, attribute: DungeonAttribute, rng: random.Random, chance: float) -> List[str]:
        """属性ベースの能力生成（共通処理）"""
        abilities = []
        
        attribute_abilities = {
            DungeonAttribute.FIRE: ["fire_breath", "burning_aura"],
            DungeonAttribute.ICE: ["ice_blast", "freezing_touch"],
            DungeonAttribute.LIGHTNING: ["lightning_bolt", "shock_aura"],
            DungeonAttribute.DARK: ["shadow_step", "darkness"],
            DungeonAttribute.LIGHT: ["holy_light", "blessing"]
        }
        
        if attribute in attribute_abilities and rng.random() < chance:
            abilities.append(rng.choice(attribute_abilities[attribute]))
        
        return abilities


class SpecialEventEncounterStrategy(EncounterStrategy):
    """特殊イベントエンカウンターの処理"""
    
    def generate_special_abilities(self, attribute: DungeonAttribute, rng: random.Random) -> List[str]:
        """特殊イベントは特別な能力なし"""
        return []
    
    def apply_special_conditions(self, encounter: EncounterEvent, level: int) -> None:
        """特殊イベントは特別な条件なし"""
        pass
    
    def get_ability_chance(self) -> float:
        return 0.0


class EncounterStrategyFactory:
    """エンカウンターストラテジーのファクトリークラス"""
    
    _strategies: Dict[EncounterType, EncounterStrategy] = {
        EncounterType.NORMAL: NormalEncounterStrategy(),
        EncounterType.AMBUSH: AmbushEncounterStrategy(),
        EncounterType.TREASURE_GUARDIAN: TreasureGuardianEncounterStrategy(),
        EncounterType.BOSS: BossEncounterStrategy(),
        EncounterType.TRAP_MONSTER: TrapMonsterEncounterStrategy(),
        EncounterType.SPECIAL_EVENT: SpecialEventEncounterStrategy()
    }
    
    @classmethod
    def get_strategy(cls, encounter_type: EncounterType) -> EncounterStrategy:
        """エンカウンタータイプに対応するストラテジーを取得"""
        return cls._strategies.get(encounter_type, cls._strategies[EncounterType.NORMAL])


class DeepDungeonModifier:
    """深いダンジョンでの追加処理を管理するクラス"""
    
    DEEP_DUNGEON_THRESHOLD = 15
    ENHANCED_MONSTER_CHANCE = 0.2
    
    @classmethod
    def apply_deep_dungeon_conditions(cls, encounter: EncounterEvent, level: int) -> None:
        """深い階層での特殊条件を適用"""
        if level > cls.DEEP_DUNGEON_THRESHOLD:
            encounter.special_conditions["deep_dungeon"] = True
            if random.random() < cls.ENHANCED_MONSTER_CHANCE:
                encounter.special_conditions["enhanced_monsters"] = True