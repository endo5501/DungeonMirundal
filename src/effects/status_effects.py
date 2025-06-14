"""ステータス効果システム"""

from typing import Dict, List, Optional, Any, Tuple
from enum import Enum
from abc import ABC, abstractmethod
import time

from src.utils.logger import logger


class StatusEffectType(Enum):
    """ステータス効果の種類"""
    POISON = "poison"           # 毒
    PARALYSIS = "paralysis"     # 麻痺
    SLEEP = "sleep"             # 睡眠
    CONFUSION = "confusion"     # 混乱
    CHARM = "charm"             # 魅力
    FEAR = "fear"               # 恐怖
    BLIND = "blind"             # 盲目
    SILENCE = "silence"         # 沈黙
    STONE = "stone"             # 石化
    REGEN = "regen"             # 再生
    HASTE = "haste"             # 加速
    SLOW = "slow"               # 減速
    STRENGTH_UP = "strength_up" # 筋力強化
    DEFENSE_UP = "defense_up"   # 防御強化
    MAGIC_UP = "magic_up"       # 魔力強化
    RESIST_UP = "resist_up"     # 耐性強化


class StatusEffect(ABC):
    """ステータス効果の基底クラス"""
    
    def __init__(self, effect_type: StatusEffectType, duration: int, 
                 strength: int = 1, source: str = "unknown"):
        self.effect_type = effect_type
        self.duration = duration  # ターン数
        self.strength = strength  # 効果の強さ
        self.source = source      # 効果の発生源
        self.applied_time = time.time()
        
    @abstractmethod
    def apply_effect(self, character) -> Dict[str, Any]:
        """効果を適用"""
        pass
    
    @abstractmethod
    def remove_effect(self, character) -> Dict[str, Any]:
        """効果を除去"""
        pass
    
    def tick(self, character) -> Tuple[bool, Dict[str, Any]]:
        """ターン経過処理
        
        Returns:
            Tuple[bool, Dict[str, Any]]: (効果が継続するか, 効果の結果)
        """
        self.duration -= 1
        
        # 継続ダメージや回復効果をここで処理
        result = self._process_turn_effect(character)
        
        return self.duration > 0, result
    
    def _process_turn_effect(self, character) -> Dict[str, Any]:
        """ターン毎の効果処理"""
        return {}
    
    def get_description(self) -> str:
        """効果の説明を取得"""
        return f"{self.effect_type.value}（残り{self.duration}ターン）"
    
    def to_dict(self) -> Dict[str, Any]:
        """辞書形式に変換"""
        return {
            'effect_type': self.effect_type.value,
            'duration': self.duration,
            'strength': self.strength,
            'source': self.source,
            'applied_time': self.applied_time
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'StatusEffect':
        """辞書から復元"""
        effect_type = StatusEffectType(data['effect_type'])
        effect = effect_registry[effect_type](
            duration=data['duration'],
            strength=data.get('strength', 1),
            source=data.get('source', 'unknown')
        )
        effect.applied_time = data.get('applied_time', time.time())
        return effect


class PoisonEffect(StatusEffect):
    """毒効果"""
    
    def __init__(self, duration: int = 5, strength: int = 1, source: str = "poison"):
        super().__init__(StatusEffectType.POISON, duration, strength, source)
    
    def apply_effect(self, character) -> Dict[str, Any]:
        """毒効果を適用"""
        logger.info(f"{character.name}が毒状態になりました")
        return {
            'message': f"{character.name}が毒に冒されました",
            'applied': True
        }
    
    def remove_effect(self, character) -> Dict[str, Any]:
        """毒効果を除去"""
        logger.info(f"{character.name}の毒が治りました")
        return {
            'message': f"{character.name}の毒が治りました",
            'removed': True
        }
    
    def _process_turn_effect(self, character) -> Dict[str, Any]:
        """ターン毎のダメージ処理"""
        poison_damage = max(1, character.derived_stats.max_hp // 20 * self.strength)
        old_hp = character.derived_stats.current_hp
        character.take_damage(poison_damage)
        actual_damage = old_hp - character.derived_stats.current_hp
        
        return {
            'poison_damage': actual_damage,
            'message': f"{character.name}は毒により{actual_damage}のダメージを受けた",
            'current_hp': character.derived_stats.current_hp
        }


class ParalysisEffect(StatusEffect):
    """麻痺効果"""
    
    def __init__(self, duration: int = 3, strength: int = 1, source: str = "paralysis"):
        super().__init__(StatusEffectType.PARALYSIS, duration, strength, source)
    
    def apply_effect(self, character) -> Dict[str, Any]:
        """麻痺効果を適用"""
        logger.info(f"{character.name}が麻痺状態になりました")
        return {
            'message': f"{character.name}の体が麻痺して動けません",
            'applied': True
        }
    
    def remove_effect(self, character) -> Dict[str, Any]:
        """麻痺効果を除去"""
        logger.info(f"{character.name}の麻痺が治りました")
        return {
            'message': f"{character.name}が麻痺から回復しました",
            'removed': True
        }


class SleepEffect(StatusEffect):
    """睡眠効果"""
    
    def __init__(self, duration: int = 4, strength: int = 1, source: str = "sleep"):
        super().__init__(StatusEffectType.SLEEP, duration, strength, source)
    
    def apply_effect(self, character) -> Dict[str, Any]:
        """睡眠効果を適用"""
        logger.info(f"{character.name}が睡眠状態になりました")
        return {
            'message': f"{character.name}が深い眠りに落ちました",
            'applied': True
        }
    
    def remove_effect(self, character) -> Dict[str, Any]:
        """睡眠効果を除去"""
        logger.info(f"{character.name}が目を覚ましました")
        return {
            'message': f"{character.name}が目を覚ましました",
            'removed': True
        }


class RegenEffect(StatusEffect):
    """再生効果"""
    
    def __init__(self, duration: int = 10, strength: int = 1, source: str = "regen"):
        super().__init__(StatusEffectType.REGEN, duration, strength, source)
    
    def apply_effect(self, character) -> Dict[str, Any]:
        """再生効果を適用"""
        logger.info(f"{character.name}に再生効果がかかりました")
        return {
            'message': f"{character.name}の体が再生の力に包まれました",
            'applied': True
        }
    
    def remove_effect(self, character) -> Dict[str, Any]:
        """再生効果を除去"""
        logger.info(f"{character.name}の再生効果が終了しました")
        return {
            'message': f"{character.name}の再生効果が終了しました",
            'removed': True
        }
    
    def _process_turn_effect(self, character) -> Dict[str, Any]:
        """ターン毎の回復処理"""
        regen_amount = max(1, character.derived_stats.max_hp // 20 * self.strength)
        old_hp = character.derived_stats.current_hp
        character.heal(regen_amount)
        actual_heal = character.derived_stats.current_hp - old_hp
        
        return {
            'regen_amount': actual_heal,
            'message': f"{character.name}は再生により{actual_heal}回復した",
            'current_hp': character.derived_stats.current_hp
        }


class StrengthUpEffect(StatusEffect):
    """筋力強化効果"""
    
    def __init__(self, duration: int = 6, strength: int = 3, source: str = "buff"):
        super().__init__(StatusEffectType.STRENGTH_UP, duration, strength, source)
    
    def apply_effect(self, character) -> Dict[str, Any]:
        """筋力強化効果を適用"""
        logger.info(f"{character.name}の筋力が強化されました")
        return {
            'message': f"{character.name}の筋力が+{self.strength}強化されました",
            'applied': True,
            'strength_bonus': self.strength
        }
    
    def remove_effect(self, character) -> Dict[str, Any]:
        """筋力強化効果を除去"""
        logger.info(f"{character.name}の筋力強化が終了しました")
        return {
            'message': f"{character.name}の筋力強化が終了しました",
            'removed': True,
            'strength_bonus': -self.strength
        }


class DefenseUpEffect(StatusEffect):
    """防御強化効果"""
    
    def __init__(self, duration: int = 6, strength: int = 3, source: str = "buff"):
        super().__init__(StatusEffectType.DEFENSE_UP, duration, strength, source)
    
    def apply_effect(self, character) -> Dict[str, Any]:
        """防御強化効果を適用"""
        logger.info(f"{character.name}の防御力が強化されました")
        return {
            'message': f"{character.name}の防御力が+{self.strength}強化されました",
            'applied': True,
            'defense_bonus': self.strength
        }
    
    def remove_effect(self, character) -> Dict[str, Any]:
        """防御強化効果を除去"""
        logger.info(f"{character.name}の防御強化が終了しました")
        return {
            'message': f"{character.name}の防御強化が終了しました",
            'removed': True,
            'defense_bonus': -self.strength
        }


class StatusEffectManager:
    """ステータス効果管理クラス"""
    
    def __init__(self, character_id: str):
        self.character_id = character_id
        self.active_effects: Dict[StatusEffectType, StatusEffect] = {}
        
    def add_effect(self, effect: StatusEffect, character=None) -> Tuple[bool, Dict[str, Any]]:
        """ステータス効果を追加"""
        effect_type = effect.effect_type
        
        # 既存の同じ効果がある場合は上書き（より強い効果または長い効果を優先）
        if effect_type in self.active_effects:
            existing = self.active_effects[effect_type]
            if effect.duration <= existing.duration and effect.strength <= existing.strength:
                return False, {'message': f'より強い{effect_type.value}効果が既にかかっています'}
        
        # 効果を適用（キャラクターオブジェクトを直接受け取る）
        if not character:
            return False, {'message': 'キャラクターが指定されていません'}
        
        result = effect.apply_effect(character)
        self.active_effects[effect_type] = effect
        
        logger.info(f"ステータス効果追加: {self.character_id} - {effect_type.value}")
        return True, result
    
    def remove_effect(self, effect_type: StatusEffectType, character=None) -> Tuple[bool, Dict[str, Any]]:
        """ステータス効果を除去"""
        if effect_type not in self.active_effects:
            return False, {'message': f'{effect_type.value}効果はかかっていません'}
        
        effect = self.active_effects[effect_type]
        
        if not character:
            return False, {'message': 'キャラクターが指定されていません'}
        
        result = effect.remove_effect(character)
        del self.active_effects[effect_type]
        
        logger.info(f"ステータス効果除去: {self.character_id} - {effect_type.value}")
        return True, result
    
    def has_effect(self, effect_type: StatusEffectType) -> bool:
        """指定された効果がかかっているかチェック"""
        return effect_type in self.active_effects
    
    def get_effect(self, effect_type: StatusEffectType) -> Optional[StatusEffect]:
        """指定された効果を取得"""
        return self.active_effects.get(effect_type)
    
    def process_turn(self, character=None) -> List[Dict[str, Any]]:
        """ターン処理（効果の継続・除去）"""
        results = []
        effects_to_remove = []
        
        if not character:
            return results
        
        for effect_type, effect in self.active_effects.items():
            continues, result = effect.tick(character)
            
            if result:
                results.append(result)
            
            if not continues:
                # 効果終了
                remove_result = effect.remove_effect(character)
                results.append(remove_result)
                effects_to_remove.append(effect_type)
        
        # 終了した効果を除去
        for effect_type in effects_to_remove:
            del self.active_effects[effect_type]
            logger.info(f"ステータス効果終了: {self.character_id} - {effect_type.value}")
        
        return results
    
    def cure_negative_effects(self, character=None) -> List[Dict[str, Any]]:
        """負の効果を全て治療"""
        negative_effects = [
            StatusEffectType.POISON,
            StatusEffectType.PARALYSIS,
            StatusEffectType.SLEEP,
            StatusEffectType.CONFUSION,
            StatusEffectType.CHARM,
            StatusEffectType.FEAR,
            StatusEffectType.BLIND,
            StatusEffectType.SILENCE,
            StatusEffectType.STONE,
            StatusEffectType.SLOW
        ]
        
        results = []
        for effect_type in negative_effects:
            if self.has_effect(effect_type):
                success, result = self.remove_effect(effect_type, character)
                if success:
                    results.append(result)
        
        return results
    
    def get_active_effects_summary(self) -> List[str]:
        """現在かかっている効果の一覧を取得"""
        return [effect.get_description() for effect in self.active_effects.values()]
    
    def get_stat_modifiers(self) -> Dict[str, int]:
        """ステータス修正値を取得"""
        modifiers = {
            'strength': 0,
            'agility': 0,
            'intelligence': 0,
            'faith': 0,
            'luck': 0,
            'attack': 0,
            'defense': 0
        }
        
        for effect in self.active_effects.values():
            if effect.effect_type == StatusEffectType.STRENGTH_UP:
                modifiers['strength'] += effect.strength
                modifiers['attack'] += effect.strength
            elif effect.effect_type == StatusEffectType.DEFENSE_UP:
                modifiers['defense'] += effect.strength
        
        return modifiers
    
    def can_act(self) -> Tuple[bool, str]:
        """行動可能かチェック"""
        if self.has_effect(StatusEffectType.PARALYSIS):
            return False, "麻痺している"
        if self.has_effect(StatusEffectType.SLEEP):
            return False, "睡眠中"
        if self.has_effect(StatusEffectType.STONE):
            return False, "石化している"
        
        return True, ""
    
    def to_dict(self) -> Dict[str, Any]:
        """辞書形式に変換"""
        return {
            'character_id': self.character_id,
            'active_effects': {
                effect_type.value: effect.to_dict()
                for effect_type, effect in self.active_effects.items()
            }
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'StatusEffectManager':
        """辞書から復元"""
        manager = cls(data['character_id'])
        
        for effect_type_str, effect_data in data.get('active_effects', {}).items():
            effect_type = StatusEffectType(effect_type_str)
            effect = StatusEffect.from_dict(effect_data)
            manager.active_effects[effect_type] = effect
        
        return manager


# エフェクトレジストリ
effect_registry: Dict[StatusEffectType, type] = {
    StatusEffectType.POISON: PoisonEffect,
    StatusEffectType.PARALYSIS: ParalysisEffect,
    StatusEffectType.SLEEP: SleepEffect,
    StatusEffectType.REGEN: RegenEffect,
    StatusEffectType.STRENGTH_UP: StrengthUpEffect,
    StatusEffectType.DEFENSE_UP: DefenseUpEffect
}


class GlobalStatusEffectManager:
    """グローバルステータス効果管理"""
    
    def __init__(self):
        self.character_managers: Dict[str, StatusEffectManager] = {}
    
    def get_character_effects(self, character_id: str) -> StatusEffectManager:
        """キャラクターのステータス効果管理を取得"""
        if character_id not in self.character_managers:
            self.character_managers[character_id] = StatusEffectManager(character_id)
        return self.character_managers[character_id]
    
    def remove_character_effects(self, character_id: str):
        """キャラクターのステータス効果管理を削除"""
        if character_id in self.character_managers:
            del self.character_managers[character_id]
    
    def process_party_turn(self, characters: List) -> Dict[str, List[Dict[str, Any]]]:
        """パーティ全体のターン処理"""
        results = {}
        for character in characters:
            manager = self.get_character_effects(character.character_id)
            results[character.character_id] = manager.process_turn(character)
        return results
    
    def to_dict(self) -> Dict[str, Any]:
        """辞書形式に変換"""
        return {
            'character_managers': {
                char_id: manager.to_dict()
                for char_id, manager in self.character_managers.items()
            }
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'GlobalStatusEffectManager':
        """辞書から復元"""
        manager = cls()
        
        for char_id, manager_data in data.get('character_managers', {}).items():
            manager.character_managers[char_id] = StatusEffectManager.from_dict(manager_data)
        
        return manager


# グローバルインスタンス
status_effect_manager = GlobalStatusEffectManager()