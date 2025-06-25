"""キャラクター統計システム"""

from dataclasses import dataclass, field
from typing import Dict, Optional
import random
from src.utils.logger import logger


@dataclass
class BaseStats:
    """基本統計値"""
    strength: int = 10
    agility: int = 10
    intelligence: int = 10
    faith: int = 10
    vitality: int = 10
    luck: int = 10
    
    def apply_modifiers(self, modifiers: Dict[str, float]) -> 'BaseStats':
        """修正値を適用した新しい統計値を返す"""
        return BaseStats(
            strength=int(self.strength * modifiers.get('strength', 1.0)),
            agility=int(self.agility * modifiers.get('agility', 1.0)),
            intelligence=int(self.intelligence * modifiers.get('intelligence', 1.0)),
            faith=int(self.faith * modifiers.get('faith', 1.0)),
            vitality=int(self.vitality * modifiers.get('vitality', 1.0)),
            luck=int(self.luck * modifiers.get('luck', 1.0))
        )
    
    def add_bonuses(self, bonuses: Dict[str, int]) -> 'BaseStats':
        """ボーナス値を加算した新しい統計値を返す"""
        return BaseStats(
            strength=self.strength + bonuses.get('strength', 0),
            agility=self.agility + bonuses.get('agility', 0),
            intelligence=self.intelligence + bonuses.get('intelligence', 0),
            faith=self.faith + bonuses.get('faith', 0),
            vitality=self.vitality + bonuses.get('vitality', 0),
            luck=self.luck + bonuses.get('luck', 0)
        )
    
    def to_dict(self) -> Dict[str, int]:
        """辞書形式での出力"""
        return {
            'strength': self.strength,
            'agility': self.agility,
            'intelligence': self.intelligence,
            'faith': self.faith,
            'vitality': self.vitality,
            'luck': self.luck
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, int]) -> 'BaseStats':
        """辞書から統計値を作成"""
        return cls(
            strength=data.get('strength', 10),
            agility=data.get('agility', 10),
            intelligence=data.get('intelligence', 10),
            faith=data.get('faith', 10),
            vitality=data.get('vitality', 10),
            luck=data.get('luck', 10)
        )


@dataclass
class DerivedStats:
    """派生統計値（HP、MPなど）"""
    max_hp: int = 0
    current_hp: int = 0
    max_mp: int = 0
    current_mp: int = 0
    armor_class: int = 10
    attack_bonus: int = 0
    attack_power: int = 0
    defense: int = 0
    accuracy: int = 80
    evasion: int = 10
    critical_chance: int = 5
    
    def to_dict(self) -> Dict[str, int]:
        """辞書形式での出力"""
        return {
            'max_hp': self.max_hp,
            'current_hp': self.current_hp,
            'max_mp': self.max_mp,
            'current_mp': self.current_mp,
            'armor_class': self.armor_class,
            'attack_bonus': self.attack_bonus,
            'attack_power': self.attack_power,
            'defense': self.defense,
            'accuracy': self.accuracy,
            'evasion': self.evasion,
            'critical_chance': self.critical_chance
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, int]) -> 'DerivedStats':
        """辞書から派生統計値を作成"""
        return cls(
            max_hp=data.get('max_hp', 0),
            current_hp=data.get('current_hp', 0),
            max_mp=data.get('max_mp', 0),
            current_mp=data.get('current_mp', 0),
            armor_class=data.get('armor_class', 10),
            attack_bonus=data.get('attack_bonus', 0),
            attack_power=data.get('attack_power', 0),
            defense=data.get('defense', 0),
            accuracy=data.get('accuracy', 80),
            evasion=data.get('evasion', 10),
            critical_chance=data.get('critical_chance', 5)
        )


class StatGenerator:
    """統計値生成システム"""
    
    @staticmethod
    def roll_3d6() -> int:
        """3d6でダイスロール"""
        return sum(random.randint(1, 6) for _ in range(3))
    
    @staticmethod
    def roll_4d6_drop_lowest() -> int:
        """4d6で最低値を除外"""
        rolls = [random.randint(1, 6) for _ in range(4)]
        rolls.sort()
        return sum(rolls[1:])  # 最低値を除外
    
    @classmethod
    def generate_stats(cls, method: str = "4d6_drop_lowest") -> BaseStats:
        """統計値の生成"""
        if method == "3d6":
            roll_func = cls.roll_3d6
        elif method == "4d6_drop_lowest":
            roll_func = cls.roll_4d6_drop_lowest
        else:
            logger.warning(f"未知の統計値生成方法: {method}, 4d6_drop_lowestを使用")
            roll_func = cls.roll_4d6_drop_lowest
        
        stats = BaseStats(
            strength=roll_func(),
            agility=roll_func(),
            intelligence=roll_func(),
            faith=roll_func(),
            luck=roll_func()
        )
        
        logger.debug(f"統計値を生成しました ({method}): {stats.to_dict()}")
        return stats
    
    @staticmethod
    def calculate_derived_stats(
        base_stats: BaseStats, 
        level: int, 
        class_config: Dict,
        race_config: Dict
    ) -> DerivedStats:
        """派生統計値の計算"""
        # HP計算
        base_hp = 10  # 基本HP
        con_bonus = (base_stats.vitality - 10) // 2  # 体力ボーナス（vitalityを使用）
        class_hp_mult = class_config.get('hp_multiplier', 1.0)
        max_hp = int((base_hp + con_bonus + level * 2) * class_hp_mult)
        
        # MP計算
        base_mp = 5  # 基本MP
        int_bonus = (base_stats.intelligence - 10) // 2  # 知力ボーナス
        faith_bonus = (base_stats.faith - 10) // 2  # 信仰ボーナス
        class_mp_mult = class_config.get('mp_multiplier', 1.0)
        max_mp = int((base_mp + int_bonus + faith_bonus + level) * class_mp_mult)
        
        # AC計算
        dex_bonus = (base_stats.agility - 10) // 2  # 敏捷ボーナス
        armor_class = 10 + dex_bonus
        
        # 攻撃ボーナス計算
        str_bonus = (base_stats.strength - 10) // 2  # 筋力ボーナス
        attack_bonus = str_bonus + (level // 2)
        
        derived = DerivedStats(
            max_hp=max(1, max_hp),
            current_hp=max(1, max_hp),
            max_mp=max(0, max_mp),
            current_mp=max(0, max_mp),
            armor_class=armor_class,
            attack_bonus=attack_bonus
        )
        
        logger.debug(f"派生統計値を計算しました: {derived.to_dict()}")
        return derived


class StatValidator:
    """統計値検証システム"""
    
    @staticmethod
    def check_class_requirements(stats: BaseStats, class_config: Dict) -> bool:
        """職業要件の確認"""
        requirements = class_config.get('requirements', {})
        
        for stat_name, min_value in requirements.items():
            current_value = getattr(stats, stat_name, 0)
            if current_value < min_value:
                logger.debug(f"職業要件未満: {stat_name} {current_value} < {min_value}")
                return False
        
        return True
    
    @staticmethod
    def get_available_classes(stats: BaseStats, classes_config: Dict) -> list:
        """選択可能な職業一覧を取得"""
        available = []
        
        for class_id, class_config in classes_config.items():
            if StatValidator.check_class_requirements(stats, class_config):
                available.append(class_id)
        
        logger.debug(f"選択可能な職業: {available}")
        return available