"""戦闘戦略システム

CombatManagerの複雑な行動処理をStrategyパターンで分離。
Fowlerの「Replace Conditional with Polymorphism」と「Extract Class」を適用。
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional, Union, Tuple
from dataclasses import dataclass
from enum import Enum
import random
import math

from src.character.character import Character
from src.character.party import Party
from src.monsters.monster import Monster
from src.utils.logger import logger


@dataclass
class CombatContext:
    """戦闘コンテキスト（戦略に渡されるデータ）"""
    attacker: Union[Character, Monster]
    target: Optional[Union[Character, Monster]]
    party: Party
    monsters: List[Monster]
    turn_number: int
    action_data: Dict[str, Any]


@dataclass
class ActionResult:
    """行動結果"""
    success: bool
    message: str
    damage_dealt: int = 0
    damage_taken: int = 0
    effects: List[str] = None
    
    def __post_init__(self):
        if self.effects is None:
            self.effects = []


class CombatStrategy(ABC):
    """戦闘戦略の基底クラス"""
    
    @abstractmethod
    def execute(self, context: CombatContext) -> ActionResult:
        """戦略を実行"""
        pass
    
    @abstractmethod
    def can_execute(self, context: CombatContext) -> bool:
        """戦略が実行可能かチェック"""
        pass
    
    def get_strategy_name(self) -> str:
        """戦略名を取得"""
        return self.__class__.__name__


class AttackStrategy(CombatStrategy):
    """攻撃戦略"""
    
    def can_execute(self, context: CombatContext) -> bool:
        """攻撃可能かチェック"""
        if not context.target:
            return False
        
        # 麻痺や意識不明状態では攻撃できない
        if hasattr(context.attacker, 'status_effects'):
            from src.character.components.status_effects_component import StatusEffectType
            if (context.attacker.status_effects and 
                (context.attacker.status_effects.has_status_effect(StatusEffectType.PARALYZED) or
                 context.attacker.status_effects.has_status_effect(StatusEffectType.UNCONSCIOUS))):
                return False
        
        return True
    
    def execute(self, context: CombatContext) -> ActionResult:
        """攻撃を実行"""
        if not self.can_execute(context):
            return ActionResult(
                success=False,
                message=f"{context.attacker.name}は攻撃できません"
            )
        
        target = context.target
        attacker = context.attacker
        
        # 命中判定
        hit_chance = self._calculate_hit_chance(attacker, target)
        if random.random() > hit_chance:
            return ActionResult(
                success=True,
                message=f"{attacker.name}の攻撃は{target.name}に外れた"
            )
        
        # ダメージ計算
        base_damage = self._calculate_base_damage(attacker)
        defense = self._calculate_defense(target)
        damage = max(1, base_damage - defense)
        
        # クリティカルヒット判定
        is_critical = random.random() < 0.05
        if is_critical:
            damage = int(damage * 1.5)
            message = f"{attacker.name}のクリティカルヒット！{target.name}に{damage}ダメージ"
        else:
            message = f"{attacker.name}の攻撃！{target.name}に{damage}ダメージ"
        
        # ダメージ適用
        self._apply_damage(target, damage)
        
        return ActionResult(
            success=True,
            message=message,
            damage_dealt=damage,
            effects=["critical"] if is_critical else []
        )
    
    def _calculate_hit_chance(self, attacker, target) -> float:
        """命中率を計算"""
        base_chance = 0.7
        
        # 攻撃者の敏捷性
        attacker_agility = getattr(attacker, 'base_stats', None)
        if attacker_agility:
            agility_bonus = getattr(attacker_agility, 'agility', 10) * 0.02
        else:
            agility_bonus = 0.2
        
        # 対象の敏捷性
        target_agility = getattr(target, 'base_stats', None)
        if target_agility:
            agility_penalty = getattr(target_agility, 'agility', 10) * 0.01
        else:
            agility_penalty = 0.1
        
        hit_chance = base_chance + agility_bonus - agility_penalty
        return max(0.05, min(0.95, hit_chance))
    
    def _calculate_base_damage(self, attacker) -> int:
        """基本ダメージを計算"""
        if hasattr(attacker, 'base_stats'):
            strength = getattr(attacker.base_stats, 'strength', 10)
            base_damage = strength + random.randint(1, 6)
        else:
            # モンスターの場合
            base_damage = getattr(attacker, 'attack_power', 10) + random.randint(1, 6)
        
        return base_damage
    
    def _calculate_defense(self, target) -> int:
        """防御力を計算"""
        base_defense = 0
        
        if hasattr(target, 'base_stats'):
            vitality = getattr(target.base_stats, 'vitality', 10)
            base_defense = vitality // 2
        else:
            # モンスターの場合
            base_defense = getattr(target, 'defense', 5)
        
        # 装備による防御力ボーナス
        if hasattr(target, 'equipment') and target.equipment:
            # 装備の防御力を考慮（簡単な実装）
            equipped_armor = target.equipment.get_equipped_item('armor')
            if equipped_armor and equipped_armor.item_id:
                base_defense += 3  # 鎧の基本防御力
        
        return base_defense
    
    def _apply_damage(self, target, damage: int):
        """ダメージを適用"""
        if hasattr(target, 'derived_stats') and target.derived_stats:
            target.derived_stats.current_hp = max(0, target.derived_stats.current_hp - damage)
        else:
            # モンスターの場合
            if hasattr(target, 'current_hp'):
                target.current_hp = max(0, target.current_hp - damage)


class DefendStrategy(CombatStrategy):
    """防御戦略"""
    
    def can_execute(self, context: CombatContext) -> bool:
        """防御可能かチェック"""
        # 防御は基本的に常に可能
        return True
    
    def execute(self, context: CombatContext) -> ActionResult:
        """防御を実行"""
        attacker = context.attacker
        
        # 防御効果を適用（次のターンまで防御力上昇）
        if hasattr(attacker, 'status_effects') and attacker.status_effects:
            from src.character.components.status_effects_component import StatusEffectType
            attacker.status_effects.apply_status_effect(
                StatusEffectType.PROTECTION,
                duration=1,
                intensity=1,
                source="defend_action"
            )
        
        return ActionResult(
            success=True,
            message=f"{attacker.name}は身を守っている",
            effects=["defense_up"]
        )


class CastSpellStrategy(CombatStrategy):
    """魔法詠唱戦略"""
    
    def can_execute(self, context: CombatContext) -> bool:
        """魔法詠唱可能かチェック"""
        attacker = context.attacker
        spell_id = context.action_data.get('spell_id')
        
        if not spell_id:
            return False
        
        # キャラクターのMP確認
        if hasattr(attacker, 'derived_stats') and attacker.derived_stats:
            if attacker.derived_stats.current_mp <= 0:
                return False
        
        # 混乱状態では魔法を唱えられない
        if hasattr(attacker, 'status_effects') and attacker.status_effects:
            from src.character.components.status_effects_component import StatusEffectType
            if attacker.status_effects.has_status_effect(StatusEffectType.CONFUSED):
                return False
        
        return True
    
    def execute(self, context: CombatContext) -> ActionResult:
        """魔法詠唱を実行"""
        if not self.can_execute(context):
            return ActionResult(
                success=False,
                message=f"{context.attacker.name}は魔法を唱えられません"
            )
        
        attacker = context.attacker
        spell_id = context.action_data.get('spell_id')
        target = context.target
        
        # MP消費
        mp_cost = self._get_spell_mp_cost(spell_id)
        if hasattr(attacker, 'derived_stats') and attacker.derived_stats:
            attacker.derived_stats.current_mp = max(0, attacker.derived_stats.current_mp - mp_cost)
        
        # 魔法効果を適用
        result = self._apply_spell_effect(spell_id, attacker, target, context)
        
        return result
    
    def _get_spell_mp_cost(self, spell_id: str) -> int:
        """魔法のMP消費量を取得"""
        # 簡単な実装
        spell_costs = {
            'heal': 5,
            'cure': 3,
            'fireball': 8,
            'lightning': 10,
            'blessing': 6
        }
        return spell_costs.get(spell_id, 5)
    
    def _apply_spell_effect(self, spell_id: str, caster, target, context: CombatContext) -> ActionResult:
        """魔法効果を適用"""
        if spell_id == 'heal':
            return self._cast_heal_spell(caster, target)
        elif spell_id == 'fireball':
            return self._cast_damage_spell(caster, target, 'fireball', 15)
        elif spell_id == 'lightning':
            return self._cast_damage_spell(caster, target, 'lightning', 20)
        elif spell_id == 'blessing':
            return self._cast_blessing_spell(caster, target)
        else:
            return ActionResult(
                success=False,
                message=f"不明な魔法: {spell_id}"
            )
    
    def _cast_heal_spell(self, caster, target) -> ActionResult:
        """回復魔法を詠唱"""
        if not target or not hasattr(target, 'derived_stats'):
            return ActionResult(
                success=False,
                message="回復対象が無効です"
            )
        
        heal_amount = random.randint(10, 20)
        old_hp = target.derived_stats.current_hp
        target.derived_stats.current_hp = min(
            target.derived_stats.max_hp,
            target.derived_stats.current_hp + heal_amount
        )
        actual_heal = target.derived_stats.current_hp - old_hp
        
        return ActionResult(
            success=True,
            message=f"{caster.name}の回復魔法！{target.name}のHPが{actual_heal}回復",
            effects=["heal"]
        )
    
    def _cast_damage_spell(self, caster, target, spell_name: str, base_damage: int) -> ActionResult:
        """ダメージ魔法を詠唱"""
        if not target:
            return ActionResult(
                success=False,
                message="攻撃対象が無効です"
            )
        
        # 魔法ダメージ計算
        damage = base_damage + random.randint(-5, 5)
        
        # ダメージ適用
        if hasattr(target, 'derived_stats') and target.derived_stats:
            target.derived_stats.current_hp = max(0, target.derived_stats.current_hp - damage)
        elif hasattr(target, 'current_hp'):
            target.current_hp = max(0, target.current_hp - damage)
        
        return ActionResult(
            success=True,
            message=f"{caster.name}の{spell_name}！{target.name}に{damage}ダメージ",
            damage_dealt=damage,
            effects=["magic_damage"]
        )
    
    def _cast_blessing_spell(self, caster, target) -> ActionResult:
        """祝福魔法を詠唱"""
        if not target or not hasattr(target, 'status_effects'):
            return ActionResult(
                success=False,
                message="祝福対象が無効です"
            )
        
        from src.character.components.status_effects_component import StatusEffectType
        target.status_effects.apply_status_effect(
            StatusEffectType.BLESSED,
            duration=3,
            intensity=1,
            source="blessing_spell"
        )
        
        return ActionResult(
            success=True,
            message=f"{caster.name}の祝福！{target.name}は祝福を受けた",
            effects=["blessing"]
        )


class UseItemStrategy(CombatStrategy):
    """アイテム使用戦略"""
    
    def can_execute(self, context: CombatContext) -> bool:
        """アイテム使用可能かチェック"""
        attacker = context.attacker
        item_id = context.action_data.get('item_id')
        
        if not item_id:
            return False
        
        # アイテムを所持しているかチェック
        if hasattr(attacker, 'items') and attacker.items:
            return attacker.items.has_item(item_id, 1)
        
        return False
    
    def execute(self, context: CombatContext) -> ActionResult:
        """アイテム使用を実行"""
        if not self.can_execute(context):
            return ActionResult(
                success=False,
                message=f"{context.attacker.name}はアイテムを使用できません"
            )
        
        attacker = context.attacker
        item_id = context.action_data.get('item_id')
        target = context.target or attacker
        
        # アイテムを消費
        if hasattr(attacker, 'items') and attacker.items:
            attacker.items.remove_item(item_id, 1)
        
        # アイテム効果を適用
        result = self._apply_item_effect(item_id, attacker, target)
        
        return result
    
    def _apply_item_effect(self, item_id: str, user, target) -> ActionResult:
        """アイテム効果を適用"""
        if item_id == 'healing_potion':
            return self._use_healing_potion(user, target)
        elif item_id == 'antidote':
            return self._use_antidote(user, target)
        elif item_id == 'bomb':
            return self._use_bomb(user, target)
        else:
            return ActionResult(
                success=True,
                message=f"{user.name}は{item_id}を使用した",
                effects=["item_used"]
            )
    
    def _use_healing_potion(self, user, target) -> ActionResult:
        """回復ポーションを使用"""
        if not hasattr(target, 'derived_stats'):
            return ActionResult(
                success=False,
                message="回復対象が無効です"
            )
        
        heal_amount = random.randint(15, 25)
        old_hp = target.derived_stats.current_hp
        target.derived_stats.current_hp = min(
            target.derived_stats.max_hp,
            target.derived_stats.current_hp + heal_amount
        )
        actual_heal = target.derived_stats.current_hp - old_hp
        
        return ActionResult(
            success=True,
            message=f"{user.name}は回復ポーションを使用！{target.name}のHPが{actual_heal}回復",
            effects=["heal", "item_used"]
        )
    
    def _use_antidote(self, user, target) -> ActionResult:
        """解毒剤を使用"""
        if not hasattr(target, 'status_effects'):
            return ActionResult(
                success=False,
                message="対象が無効です"
            )
        
        from src.character.components.status_effects_component import StatusEffectType
        if target.status_effects.has_status_effect(StatusEffectType.POISONED):
            target.status_effects.remove_status_effect(StatusEffectType.POISONED)
            return ActionResult(
                success=True,
                message=f"{user.name}は解毒剤を使用！{target.name}の毒が治った",
                effects=["cure_poison", "item_used"]
            )
        else:
            return ActionResult(
                success=True,
                message=f"{user.name}は解毒剤を使用したが効果がなかった",
                effects=["item_used"]
            )
    
    def _use_bomb(self, user, target) -> ActionResult:
        """爆弾を使用"""
        damage = random.randint(20, 30)
        
        if hasattr(target, 'derived_stats') and target.derived_stats:
            target.derived_stats.current_hp = max(0, target.derived_stats.current_hp - damage)
        elif hasattr(target, 'current_hp'):
            target.current_hp = max(0, target.current_hp - damage)
        
        return ActionResult(
            success=True,
            message=f"{user.name}は爆弾を投げた！{target.name}に{damage}ダメージ",
            damage_dealt=damage,
            effects=["explosion", "item_used"]
        )


class FleeStrategy(CombatStrategy):
    """逃走戦略"""
    
    def can_execute(self, context: CombatContext) -> bool:
        """逃走可能かチェック"""
        # 麻痺状態では逃走できない
        if hasattr(context.attacker, 'status_effects') and context.attacker.status_effects:
            from src.character.components.status_effects_component import StatusEffectType
            if context.attacker.status_effects.has_status_effect(StatusEffectType.PARALYZED):
                return False
        
        return True
    
    def execute(self, context: CombatContext) -> ActionResult:
        """逃走を実行"""
        if not self.can_execute(context):
            return ActionResult(
                success=False,
                message=f"{context.attacker.name}は逃走できません"
            )
        
        attacker = context.attacker
        
        # 逃走判定
        flee_chance = self._calculate_flee_chance(attacker, context.monsters)
        if random.random() < flee_chance:
            return ActionResult(
                success=True,
                message=f"{attacker.name}は戦闘から逃走した",
                effects=["flee_success"]
            )
        else:
            return ActionResult(
                success=True,
                message=f"{attacker.name}は逃走に失敗した",
                effects=["flee_failed"]
            )
    
    def _calculate_flee_chance(self, attacker, monsters: List[Monster]) -> float:
        """逃走成功率を計算"""
        base_chance = 0.5
        
        # 敏捷性ボーナス
        if hasattr(attacker, 'base_stats'):
            agility = getattr(attacker.base_stats, 'agility', 10)
            agility_bonus = (agility - 10) * 0.02
        else:
            agility_bonus = 0
        
        # モンスターの平均敏捷性による修正
        if monsters:
            avg_monster_agility = sum(getattr(m, 'agility', 10) for m in monsters) / len(monsters)
            monster_penalty = (avg_monster_agility - 10) * 0.01
        else:
            monster_penalty = 0
        
        flee_chance = base_chance + agility_bonus - monster_penalty
        return max(0.1, min(0.9, flee_chance))


class NegotiateStrategy(CombatStrategy):
    """交渉戦略"""
    
    def can_execute(self, context: CombatContext) -> bool:
        """交渉可能かチェック"""
        # 混乱状態では交渉できない
        if hasattr(context.attacker, 'status_effects') and context.attacker.status_effects:
            from src.character.components.status_effects_component import StatusEffectType
            if context.attacker.status_effects.has_status_effect(StatusEffectType.CONFUSED):
                return False
        
        return True
    
    def execute(self, context: CombatContext) -> ActionResult:
        """交渉を実行"""
        if not self.can_execute(context):
            return ActionResult(
                success=False,
                message=f"{context.attacker.name}は交渉できません"
            )
        
        attacker = context.attacker
        
        # 交渉判定
        negotiate_chance = self._calculate_negotiate_chance(attacker, context.monsters)
        if random.random() < negotiate_chance:
            return ActionResult(
                success=True,
                message=f"{attacker.name}の交渉が成功した！モンスターたちは去っていく",
                effects=["negotiate_success"]
            )
        else:
            return ActionResult(
                success=True,
                message=f"{attacker.name}の交渉は失敗した",
                effects=["negotiate_failed"]
            )
    
    def _calculate_negotiate_chance(self, attacker, monsters: List[Monster]) -> float:
        """交渉成功率を計算"""
        base_chance = 0.2
        
        # 知性ボーナス
        if hasattr(attacker, 'base_stats'):
            intelligence = getattr(attacker.base_stats, 'intelligence', 10)
            int_bonus = (intelligence - 10) * 0.02
        else:
            int_bonus = 0
        
        # モンスターの知性による修正
        if monsters:
            avg_monster_int = sum(getattr(m, 'intelligence', 5) for m in monsters) / len(monsters)
            monster_factor = avg_monster_int * 0.01
        else:
            monster_factor = 0.05
        
        negotiate_chance = base_chance + int_bonus + monster_factor
        return max(0.05, min(0.6, negotiate_chance))


class CombatStrategyFactory:
    """戦闘戦略ファクトリー"""
    
    _strategies = {
        'attack': AttackStrategy(),
        'defend': DefendStrategy(),
        'cast_spell': CastSpellStrategy(),
        'use_item': UseItemStrategy(),
        'flee': FleeStrategy(),
        'negotiate': NegotiateStrategy()
    }
    
    @classmethod
    def get_strategy(cls, action_type: str) -> Optional[CombatStrategy]:
        """指定された行動タイプの戦略を取得"""
        return cls._strategies.get(action_type)
    
    @classmethod
    def register_strategy(cls, action_type: str, strategy: CombatStrategy):
        """新しい戦略を登録"""
        cls._strategies[action_type] = strategy
    
    @classmethod
    def get_available_strategies(cls) -> List[str]:
        """利用可能な戦略一覧を取得"""
        return list(cls._strategies.keys())