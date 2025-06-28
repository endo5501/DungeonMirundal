"""
CharacterCreationStatsGenerator クラス

キャラクターステータス生成専門クラス
"""

import random
from typing import Dict, Any, Optional, List
from .character_creation_types import CharacterStats, WizardConfig
from src.utils.logger import logger


class CharacterCreationStatsGenerator:
    """
    キャラクターステータス生成クラス
    
    種族ボーナスとランダム生成を担当
    """
    
    def __init__(self, config: WizardConfig):
        """
        CharacterCreationStatsGeneratorを初期化
        
        Args:
            config: ウィザード設定
        """
        self.config = config
        self.race_modifiers = self._get_race_modifiers()
    
    def generate_stats(self, race: str = '') -> CharacterStats:
        """
        ステータスを生成
        
        Args:
            race: 種族名
            
        Returns:
            CharacterStats: 生成されたステータス
        """
        # 基本ステータスを3d6で生成
        base_stats = {
            'strength': self._roll_3d6(),
            'dexterity': self._roll_3d6(),
            'constitution': self._roll_3d6(),
            'intelligence': self._roll_3d6(),
            'wisdom': self._roll_3d6(),
            'charisma': self._roll_3d6()
        }
        
        # 種族ボーナスを適用
        final_stats = self._apply_race_modifiers(base_stats, race)
        
        stats = CharacterStats(
            strength=final_stats['strength'],
            dexterity=final_stats['dexterity'],
            constitution=final_stats['constitution'],
            intelligence=final_stats['intelligence'],
            wisdom=final_stats['wisdom'],
            charisma=final_stats['charisma']
        )
        
        logger.debug(f"ステータス生成完了: {race}, {stats}")
        return stats
    
    def _roll_3d6(self) -> int:
        """3d6でダイスロール"""
        return sum(random.randint(1, 6) for _ in range(3))
    
    def _apply_race_modifiers(self, base_stats: Dict[str, int], race: str) -> Dict[str, int]:
        """種族ボーナスを適用"""
        modifiers = self.race_modifiers.get(race, {})
        
        final_stats = base_stats.copy()
        for stat, modifier in modifiers.items():
            if stat in final_stats:
                final_stats[stat] = max(3, min(18, final_stats[stat] + modifier))
        
        return final_stats
    
    def _get_race_modifiers(self) -> Dict[str, Dict[str, int]]:
        """種族ボーナステーブルを取得"""
        return {
            '人間': {
                # 人間はボーナスなし（バランス型）
            },
            'エルフ': {
                'dexterity': 1,
                'intelligence': 1,
                'constitution': -1
            },
            'ドワーフ': {
                'strength': 1,
                'constitution': 1,
                'charisma': -1
            },
            'ハーフリング': {
                'dexterity': 2,
                'strength': -1
            },
            'ノーム': {
                'intelligence': 1,
                'constitution': 1,
                'strength': -1
            }
        }
    
    def get_race_description(self, race: str) -> str:
        """種族の説明を取得"""
        descriptions = {
            '人間': "バランスの取れた種族。どの職業にも適している。",
            'エルフ': "器用で知的だが体力に劣る。魔法使いや盗賊に向いている。",
            'ドワーフ': "頑丈で力強いが社交性に欠ける。戦士や僧侶に向いている。",
            'ハーフリング': "小柄で素早いが力が弱い。盗賊に向いている。",
            'ノーム': "知的で丈夫だが力が弱い。魔法使いに向いている。"
        }
        return descriptions.get(race, "")
    
    def calculate_stat_totals(self, stats: CharacterStats) -> Dict[str, Any]:
        """ステータス合計と平均を計算"""
        stat_values = [
            stats.strength, stats.dexterity, stats.constitution,
            stats.intelligence, stats.wisdom, stats.charisma
        ]
        
        return {
            'total': sum(stat_values),
            'average': sum(stat_values) / len(stat_values),
            'highest': max(stat_values),
            'lowest': min(stat_values)
        }
    
    def is_exceptional_stats(self, stats: CharacterStats) -> bool:
        """exceptional statsかどうか判定"""
        totals = self.calculate_stat_totals(stats)
        
        # 合計が75以上、または最高値が16以上なら exceptional
        return totals['total'] >= 75 or totals['highest'] >= 16
    
    def get_recommended_classes(self, stats: CharacterStats) -> List[str]:
        """ステータスに基づく推奨職業を取得"""
        recommendations = []
        
        # 戦士系：筋力・体力重視
        if stats.strength >= 13 and stats.constitution >= 12:
            recommendations.append('戦士')
        
        # 魔法使い系：知力重視
        if stats.intelligence >= 13:
            recommendations.append('魔法使い')
        
        # 僧侶系：精神重視
        if stats.wisdom >= 13:
            recommendations.append('僧侶')
        
        # 盗賊系：敏捷重視
        if stats.dexterity >= 13:
            recommendations.append('盗賊')
        
        # パラディン：全体的に高水準
        if (stats.strength >= 12 and stats.wisdom >= 13 and 
            stats.charisma >= 13 and stats.constitution >= 12):
            recommendations.append('パラディン')
        
        return recommendations if recommendations else ['戦士']  # デフォルトは戦士