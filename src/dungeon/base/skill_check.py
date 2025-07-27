"""ダンジョンスキルチェック基底クラス"""

from typing import Dict, Any, Optional
from abc import ABC, abstractmethod
import random

from src.character.character import Character
from src.utils.logger import logger


class SkillCheckBase(ABC):
    """スキルチェックの基底クラス"""
    
    def __init__(self):
        self.base_success_rate = 0.1
        self.class_bonuses = {
            'thief': 0.4,
            'ninja': 0.3,
            'ranger': 0.2,
            'monk': 0.1
        }
    
    def can_perform_skill(self, character: Character, skill_type: str, difficulty: float = 1.0) -> bool:
        """スキル実行可能性チェック"""
        success_rate = self._calculate_success_rate(character, skill_type, difficulty)
        return random.random() < min(0.95, max(0.05, success_rate))
    
    def _calculate_success_rate(self, character: Character, skill_type: str, difficulty: float) -> float:
        """成功率計算"""
        base_rate = self.base_success_rate
        
        # クラスボーナス
        if hasattr(character, 'character_class'):
            class_bonus = self._get_class_bonus(character.character_class, skill_type)
            base_rate += class_bonus
        
        # ステータスボーナス
        if hasattr(character, 'base_stats'):
            stat_bonus = self._get_stat_bonus(character.base_stats, skill_type)
            base_rate += stat_bonus
        
        # レベルボーナス
        if hasattr(character, 'experience'):
            level_bonus = character.experience.level * 0.01
            base_rate += level_bonus
        
        # 難易度調整
        return base_rate / difficulty
    
    @abstractmethod
    def _get_class_bonus(self, character_class: str, skill_type: str) -> float:
        """クラス固有のボーナス計算（サブクラスで実装）"""
        pass
    
    @abstractmethod
    def _get_stat_bonus(self, stats: Any, skill_type: str) -> float:
        """ステータスボーナス計算（サブクラスで実装）"""
        pass


class TrapSkillChecker(SkillCheckBase):
    """トラップ関連スキルチェッカー"""
    
    def _get_class_bonus(self, character_class: str, skill_type: str) -> float:
        """トラップスキルのクラスボーナス"""
        if skill_type == "detect":
            return self.class_bonuses.get(character_class, 0.0)
        elif skill_type == "disarm":
            if character_class == 'thief':
                return 0.5
            elif character_class == 'ninja':
                return 0.3
            elif character_class == 'ranger':
                return 0.1
        return 0.0
    
    def _get_stat_bonus(self, stats: Any, skill_type: str) -> float:
        """トラップスキルのステータスボーナス"""
        if skill_type == "detect":
            return (stats.intelligence - 10) * 0.02
        elif skill_type == "disarm":
            return (stats.agility - 10) * 0.02
        return 0.0


class TreasureSkillChecker(SkillCheckBase):
    """宝箱関連スキルチェッカー"""
    
    def _get_class_bonus(self, character_class: str, skill_type: str) -> float:
        """鍵開けスキルのクラスボーナス"""
        if skill_type == "lock_picking":
            if character_class == 'thief':
                return 0.4
            elif character_class == 'ninja':
                return 0.2
        return 0.0
    
    def _get_stat_bonus(self, stats: Any, skill_type: str) -> float:
        """鍵開けスキルのステータスボーナス"""
        if skill_type == "lock_picking":
            return (stats.agility - 10) * 0.02
        return 0.0


# グローバルインスタンス
trap_skill_checker = TrapSkillChecker()
treasure_skill_checker = TreasureSkillChecker()