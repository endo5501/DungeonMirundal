"""ダンジョンスキルチェック基底クラス"""

from typing import Dict, Any, Optional
from abc import ABC, abstractmethod
import random

from src.character.character import Character
from src.core.config_manager import ConfigManager
from src.utils.logger import logger


class SkillCheckBase(ABC):
    """スキルチェックの基底クラス"""
    
    def __init__(self):
        self.base_success_rate = 0.1
        self.config_manager = ConfigManager()
        self.character_config = self.config_manager.load_config('characters')
        self.skill_bonuses = self.character_config.get('skill_bonuses', {})
        self.skill_stats = self.skill_bonuses.get('skill_stats', {})
    
    def can_perform_skill(self, character: Character, skill_type: str, difficulty: float = 1.0) -> bool:
        """スキル実行可能性チェック"""
        success_rate = self._calculate_success_rate(character, skill_type, difficulty)
        return random.random() < min(0.95, max(0.05, success_rate))
    
    def _calculate_success_rate(self, character: Character, skill_type: str, difficulty: float) -> float:
        """成功率計算"""
        base_rate = self.base_success_rate
        
        # クラスボーナス（設定ファイルから取得）
        character_class = getattr(character, 'character_class', None)
        if character_class:
            class_bonus = self._get_class_bonus_from_config(character.character_class, skill_type)
            base_rate += class_bonus
        
        # ステータスボーナス（設定ファイルから取得）
        base_stats = getattr(character, 'base_stats', None)
        if base_stats:
            stat_bonus = self._get_stat_bonus_from_config(character.base_stats, skill_type)
            base_rate += stat_bonus
        
        # レベルボーナス
        experience = getattr(character, 'experience', None)
        if experience:
            level_bonus = character.experience.level * 0.01
            base_rate += level_bonus
        
        # 難易度調整
        return base_rate / difficulty
    
    def _get_class_bonus_from_config(self, character_class: str, skill_type: str) -> float:
        """設定ファイルからクラスボーナスを取得"""
        skill_bonuses = self.skill_bonuses.get(skill_type, {})
        return skill_bonuses.get(character_class, 0.0)
    
    def _get_stat_bonus_from_config(self, stats: Any, skill_type: str) -> float:
        """設定ファイルからステータスボーナスを取得"""
        stat_name = self.skill_stats.get(skill_type)
        stat_value = getattr(stats, stat_name, None) if stat_name and stats else None
        if stat_name and stat_value is not None:
            stat_value = getattr(stats, stat_name)
            return (stat_value - 10) * 0.02
        return 0.0
    


class TrapSkillChecker(SkillCheckBase):
    """トラップ関連スキルチェッカー"""
    
    def can_detect_trap(self, character: Character, trap_type=None) -> bool:
        """トラップ探知チェック"""
        return self.can_perform_skill(character, "trap_detection", 1.0)
    
    def can_disarm_trap(self, character: Character, trap_type=None) -> bool:
        """トラップ解除チェック"""
        return self.can_perform_skill(character, "trap_disarm", 1.0)


class TreasureSkillChecker(SkillCheckBase):
    """宝箱関連スキルチェッカー"""
    
    def can_pick_lock(self, character: Character, difficulty: float = 1.0) -> bool:
        """鍵開けチェック"""
        return self.can_perform_skill(character, "lockpick", difficulty)


# グローバルインスタンス
trap_skill_checker = TrapSkillChecker()
treasure_skill_checker = TreasureSkillChecker()