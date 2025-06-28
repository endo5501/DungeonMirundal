"""ステータス効果管理クラス

Fowler Extract Classパターンにより、StatusEffectsWindowからステータス効果管理に関する責任を抽出。
単一責任の原則に従い、効果の統計・分析・フィルタリング機能を専門的に扱う。
"""

from typing import Dict, List, Optional, Any, Tuple
from enum import Enum
import time

from src.utils.logger import logger


class EffectType(Enum):
    """効果タイプ"""
    BUFF = "buff"
    DEBUFF = "debuff"
    NEUTRAL = "neutral"


class EffectCategory(Enum):
    """効果カテゴリ"""
    DAMAGE_OVER_TIME = "damage_over_time"  # 毒、出血等
    STAT_MODIFIER = "stat_modifier"        # 能力値変更
    CONDITION = "condition"                # 麻痺、睡眠等
    ENHANCEMENT = "enhancement"            # 強化系
    PROTECTION = "protection"              # 防御系


class StatusEffectManager:
    """ステータス効果管理クラス
    
    ステータス効果の統計・分析・フィルタリング・管理を担当。
    Extract Classパターンにより、StatusEffectsWindowから効果管理ロジックを分離。
    """
    
    def __init__(self):
        """ステータス効果マネージャー初期化"""
        # 効果タイプの定義
        self.effect_types: Dict[str, EffectType] = {
            # デバフ系
            'poison': EffectType.DEBUFF,
            'paralysis': EffectType.DEBUFF,
            'sleep': EffectType.DEBUFF,
            'confusion': EffectType.DEBUFF,
            'fear': EffectType.DEBUFF,
            'blindness': EffectType.DEBUFF,
            'silence': EffectType.DEBUFF,
            'slow': EffectType.DEBUFF,
            'weakness': EffectType.DEBUFF,
            'curse': EffectType.DEBUFF,
            
            # バフ系
            'regeneration': EffectType.BUFF,
            'haste': EffectType.BUFF,
            'strength': EffectType.BUFF,
            'defense': EffectType.BUFF,
            'magic_power': EffectType.BUFF,
            'resistance': EffectType.BUFF,
            'blessing': EffectType.BUFF,
            'protection': EffectType.BUFF,
            
            # ニュートラル
            'mark': EffectType.NEUTRAL,
            'tracking': EffectType.NEUTRAL
        }
        
        # 効果カテゴリの定義
        self.effect_categories: Dict[str, EffectCategory] = {
            'poison': EffectCategory.DAMAGE_OVER_TIME,
            'regeneration': EffectCategory.DAMAGE_OVER_TIME,
            'strength': EffectCategory.STAT_MODIFIER,
            'defense': EffectCategory.STAT_MODIFIER,
            'paralysis': EffectCategory.CONDITION,
            'sleep': EffectCategory.CONDITION,
            'blessing': EffectCategory.ENHANCEMENT,
            'protection': EffectCategory.PROTECTION
        }
        
        # 除去可能性の定義
        self.removable_effects = {
            'poison', 'paralysis', 'sleep', 'confusion', 
            'fear', 'blindness', 'silence', 'slow', 'weakness', 'curse'
        }
        
        logger.debug("StatusEffectManagerを初期化しました")
    
    def get_party_effect_summary(self, party) -> Dict[str, Any]:
        """パーティ効果サマリーを取得
        
        Args:
            party: パーティオブジェクト
            
        Returns:
            Dict: 効果サマリー
        """
        if not party:
            return {
                'total_effects': 0,
                'by_character': {},
                'by_type': {'buff': 0, 'debuff': 0, 'neutral': 0},
                'by_category': {}
            }
        
        summary = {
            'total_effects': 0,
            'by_character': {},
            'by_type': {'buff': 0, 'debuff': 0, 'neutral': 0},
            'by_category': {cat.value: 0 for cat in EffectCategory}
        }
        
        characters = getattr(party, 'characters', [])
        for character in characters:
            char_name = getattr(character, 'name', 'Unknown')
            char_effects = getattr(character, 'status_effects', [])
            
            char_summary = {
                'total': len(char_effects),
                'buffs': 0,
                'debuffs': 0,
                'effects': char_effects
            }
            
            # 効果タイプ別カウント
            for effect in char_effects:
                effect_name = effect.get('name', '') if isinstance(effect, dict) else str(effect)
                effect_type = self.effect_types.get(effect_name, EffectType.NEUTRAL)
                
                if effect_type == EffectType.BUFF:
                    char_summary['buffs'] += 1
                    summary['by_type']['buff'] += 1
                elif effect_type == EffectType.DEBUFF:
                    char_summary['debuffs'] += 1
                    summary['by_type']['debuff'] += 1
                else:
                    summary['by_type']['neutral'] += 1
                
                # カテゴリ別カウント
                category = self.effect_categories.get(effect_name, EffectCategory.CONDITION)
                summary['by_category'][category.value] += 1
            
            summary['by_character'][char_name] = char_summary
            summary['total_effects'] += len(char_effects)
        
        return summary
    
    def get_effect_statistics(self, party) -> Dict[str, Any]:
        """効果統計を取得
        
        Args:
            party: パーティオブジェクト
            
        Returns:
            Dict: 効果統計
        """
        if not party:
            return {
                'debuff_count': 0,
                'buff_count': 0,
                'total_count': 0,
                'removable_count': 0,
                'permanent_count': 0,
                'temporary_count': 0,
                'severity_distribution': {},
                'most_common_effects': [],
                'affected_characters': 0
            }
        
        stats = {
            'debuff_count': 0,
            'buff_count': 0,
            'total_count': 0,
            'removable_count': 0,
            'permanent_count': 0,
            'temporary_count': 0,
            'severity_distribution': {'low': 0, 'medium': 0, 'high': 0},
            'most_common_effects': [],
            'affected_characters': 0
        }
        
        effect_counts = {}
        characters = getattr(party, 'characters', [])
        
        for character in characters:
            char_effects = getattr(character, 'status_effects', [])
            if char_effects:
                stats['affected_characters'] += 1
            
            for effect in char_effects:
                effect_name = effect.get('name', '') if isinstance(effect, dict) else str(effect)
                effect_type = self.effect_types.get(effect_name, EffectType.NEUTRAL)
                
                # タイプ別カウント
                if effect_type == EffectType.BUFF:
                    stats['buff_count'] += 1
                elif effect_type == EffectType.DEBUFF:
                    stats['debuff_count'] += 1
                
                stats['total_count'] += 1
                
                # 除去可能性
                if effect_name in self.removable_effects:
                    stats['removable_count'] += 1
                
                # 持続性
                if isinstance(effect, dict):
                    turns_remaining = effect.get('turns_remaining', -1)
                    if turns_remaining < 0:
                        stats['permanent_count'] += 1
                    else:
                        stats['temporary_count'] += 1
                    
                    # 深刻度
                    severity = effect.get('severity', 'medium')
                    if severity in stats['severity_distribution']:
                        stats['severity_distribution'][severity] += 1
                
                # 効果の頻度カウント
                effect_counts[effect_name] = effect_counts.get(effect_name, 0) + 1
        
        # 最も一般的な効果を取得
        stats['most_common_effects'] = sorted(
            effect_counts.items(), 
            key=lambda x: x[1], 
            reverse=True
        )[:5]
        
        return stats
    
    def filter_removable_effects(self, effects: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """除去可能な効果をフィルタリング
        
        Args:
            effects: 効果リスト
            
        Returns:
            List: 除去可能な効果リスト
        """
        removable = []
        for effect in effects:
            if isinstance(effect, dict):
                effect_name = effect.get('name', '')
                # 明示的にremovableが設定されている場合はそれを優先
                if 'removable' in effect:
                    if effect['removable']:
                        removable.append(effect)
                # そうでなければ定義済みの除去可能効果を確認
                elif effect_name in self.removable_effects:
                    removable.append(effect)
        
        return removable
    
    def filter_effects_by_type(self, effects: List[Dict[str, Any]], 
                              effect_type: EffectType) -> List[Dict[str, Any]]:
        """タイプ別に効果をフィルタリング
        
        Args:
            effects: 効果リスト
            effect_type: フィルタリングする効果タイプ
            
        Returns:
            List: フィルタリングされた効果リスト
        """
        filtered = []
        for effect in effects:
            effect_name = effect.get('name', '') if isinstance(effect, dict) else str(effect)
            if self.effect_types.get(effect_name, EffectType.NEUTRAL) == effect_type:
                filtered.append(effect)
        
        return filtered
    
    def filter_effects_by_category(self, effects: List[Dict[str, Any]], 
                                  category: EffectCategory) -> List[Dict[str, Any]]:
        """カテゴリ別に効果をフィルタリング
        
        Args:
            effects: 効果リスト
            category: フィルタリングするカテゴリ
            
        Returns:
            List: フィルタリングされた効果リスト
        """
        filtered = []
        for effect in effects:
            effect_name = effect.get('name', '') if isinstance(effect, dict) else str(effect)
            if self.effect_categories.get(effect_name, EffectCategory.CONDITION) == category:
                filtered.append(effect)
        
        return filtered
    
    def get_effect_info(self, effect_name: str) -> Dict[str, Any]:
        """効果情報を取得
        
        Args:
            effect_name: 効果名
            
        Returns:
            Dict: 効果情報
        """
        return {
            'name': effect_name,
            'type': self.effect_types.get(effect_name, EffectType.NEUTRAL).value,
            'category': self.effect_categories.get(effect_name, EffectCategory.CONDITION).value,
            'removable': effect_name in self.removable_effects,
            'description': self._get_effect_description(effect_name)
        }
    
    def calculate_effect_priority(self, effect: Dict[str, Any]) -> int:
        """効果の優先度を計算
        
        Args:
            effect: 効果データ
            
        Returns:
            int: 優先度（高いほど重要）
        """
        priority = 0
        effect_name = effect.get('name', '')
        
        # デバフは高優先度
        if self.effect_types.get(effect_name, EffectType.NEUTRAL) == EffectType.DEBUFF:
            priority += 50
        
        # 深刻度による調整
        severity = effect.get('severity', 'medium')
        severity_values = {'low': 10, 'medium': 20, 'high': 40}
        priority += severity_values.get(severity, 20)
        
        # 残りターンによる調整
        turns_remaining = effect.get('turns_remaining', -1)
        if 0 < turns_remaining <= 3:  # 残り少ない効果は高優先度
            priority += 30
        
        return priority
    
    def _get_effect_description(self, effect_name: str) -> str:
        """効果の説明を取得"""
        descriptions = {
            'poison': '毒により継続的にHPが減少',
            'paralysis': '麻痺により行動不能',
            'sleep': '睡眠により行動不能',
            'confusion': '混乱により行動が不安定',
            'fear': '恐怖により能力値が低下',
            'blindness': '盲目により命中率が低下',
            'silence': '沈黙により魔法が使用不可',
            'slow': '減速により行動速度が低下',
            'regeneration': '再生により継続的にHPが回復',
            'haste': '加速により行動速度が向上',
            'strength': '筋力が強化',
            'defense': '防御力が強化',
            'blessing': '祝福により全能力値が向上'
        }
        return descriptions.get(effect_name, f'{effect_name}の効果')
    
    def validate_effect_data(self, effect: Dict[str, Any]) -> bool:
        """効果データの妥当性を検証
        
        Args:
            effect: 効果データ
            
        Returns:
            bool: 妥当な場合True
        """
        if not isinstance(effect, dict):
            return False
        
        # 必須フィールドの確認
        required_fields = ['name']
        for field in required_fields:
            if field not in effect:
                return False
        
        # 効果名の確認
        effect_name = effect.get('name', '')
        if not effect_name or not isinstance(effect_name, str):
            return False
        
        # 残りターン数の確認
        turns_remaining = effect.get('turns_remaining')
        if turns_remaining is not None and not isinstance(turns_remaining, int):
            return False
        
        return True