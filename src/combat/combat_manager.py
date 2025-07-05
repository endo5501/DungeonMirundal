"""戦闘管理システム"""

from typing import Dict, List, Tuple, Optional, Any, Union
from dataclasses import dataclass, field
from enum import Enum
import random
import math

from src.character.character import Character
from src.character.party import Party
from src.monsters.monster import Monster
from src.dungeon.dungeon_generator import DungeonAttribute
from src.magic.spells import spell_manager
from src.items.item_usage import item_usage_manager
from src.utils.logger import logger

# 戦闘定数
BASE_HIT_CHANCE = 0.7
CRITICAL_HIT_CHANCE = 0.05
CRITICAL_DAMAGE_MULTIPLIER = 1.5
BASE_FLEE_CHANCE = 0.5
BASE_NEGOTIATE_CHANCE = 0.2
AGILITY_MODIFIER = 0.02
HIT_CHANCE_MIN = 0.05
HIT_CHANCE_MAX = 0.95
FLEE_CHANCE_MIN = 0.1
FLEE_CHANCE_MAX = 0.9
NEGOTIATE_CHANCE_MIN = 0.05
NEGOTIATE_CHANCE_MAX = 0.6


class CombatState(Enum):
    """戦闘状態"""
    PREPARATION = "preparation"     # 準備段階
    IN_PROGRESS = "in_progress"     # 戦闘中
    VICTORY = "victory"             # 勝利
    DEFEAT = "defeat"               # 敗北
    FLED = "fled"                   # 逃走
    NEGOTIATED = "negotiated"       # 交渉成功


class CombatAction(Enum):
    """戦闘行動"""
    ATTACK = "attack"               # 攻撃
    DEFEND = "defend"               # 防御
    CAST_SPELL = "cast_spell"       # 魔法詠唱
    USE_ITEM = "use_item"           # アイテム使用
    FLEE = "flee"                   # 逃走
    NEGOTIATE = "negotiate"         # 交渉
    SPECIAL_ABILITY = "special_ability"  # 特殊能力


class CombatResult(Enum):
    """戦闘結果"""
    CONTINUE = "continue"           # 戦闘継続
    VICTORY = "victory"             # 勝利
    DEFEAT = "defeat"               # 敗北
    FLED = "fled"                   # 逃走成功
    NEGOTIATED = "negotiated"       # 交渉成功


@dataclass
class CombatTurn:
    """戦闘ターン情報"""
    turn_number: int
    actor: Union[Character, Monster]
    action: CombatAction
    target: Optional[Union[Character, Monster]] = None
    action_data: Dict[str, Any] = field(default_factory=dict)
    result: str = ""
    damage_dealt: int = 0
    damage_taken: int = 0


@dataclass
class CombatStats:
    """戦闘統計"""
    total_damage_dealt: int = 0
    total_damage_taken: int = 0
    spells_cast: int = 0
    items_used: int = 0
    turns_taken: int = 0
    critical_hits: int = 0
    
    def add_damage_dealt(self, amount: int):
        """与えたダメージを追加"""
        self.total_damage_dealt += amount
    
    def add_damage_taken(self, amount: int):
        """受けたダメージを追加"""
        self.total_damage_taken += amount
    
    def add_spell_cast(self):
        """魔法詠唱回数を追加"""
        self.spells_cast += 1
    
    def add_item_used(self):
        """アイテム使用回数を追加"""
        self.items_used += 1
    
    def add_critical_hit(self):
        """クリティカルヒット回数を追加"""
        self.critical_hits += 1
    
    def get_average_damage_per_turn(self) -> float:
        """ターンあたりの平均ダメージを取得"""
        return self.total_damage_dealt / max(1, self.turns_taken)
    
    def get_critical_hit_rate(self) -> float:
        """クリティカルヒット率を取得"""
        return self.critical_hits / max(1, self.turns_taken)


class CombatManager:
    """戦闘管理システム"""
    
    def __init__(self):
        self.combat_state = CombatState.PREPARATION
        self.party: Optional[Party] = None
        self.monsters: List[Monster] = []
        
        # 戦闘データ
        self.turn_order: List[Union[Character, Monster]] = []
        self.current_turn_index = 0
        self.turn_number = 1
        self.combat_log: List[CombatTurn] = []
        
        # 戦闘統計
        self.party_stats = CombatStats()
        self.monster_stats = CombatStats()
        
        # 戦闘設定
        self.auto_sort_dead = True
        self.show_damage_numbers = True
        self.critical_hit_chance = CRITICAL_HIT_CHANCE
        
        logger.info("CombatManager初期化完了")
    
    def start_combat(self, party: Party, monsters: List[Monster]) -> bool:
        """戦闘開始"""
        if self.combat_state != CombatState.PREPARATION:
            logger.error("既に戦闘が開始されています")
            return False
        
        self.party = party
        self.monsters = monsters
        
        # 戦闘可能な状態確認
        living_characters = party.get_living_characters()
        living_monsters = [m for m in monsters if m.is_alive]
        
        if not living_characters:
            logger.error("生存しているパーティメンバーがいません")
            return False
        
        if not living_monsters:
            logger.error("生存しているモンスターがいません")
            return False
        
        # ターン順序決定
        self._determine_turn_order()
        
        # 戦闘状態を開始に設定
        self.combat_state = CombatState.IN_PROGRESS
        self.current_turn_index = 0
        self.turn_number = 1
        
        logger.info(f"戦闘開始: {len(living_characters)}人 vs {len(living_monsters)}体")
        return True
    
    def _determine_turn_order(self):
        """ターン順序決定"""
        self.turn_order = []
        
        # 生存中のキャラクターを追加
        for character in self.party.get_living_characters():
            self.turn_order.append(character)
        
        # 生存中のモンスターを追加
        for monster in self.monsters:
            if monster.is_alive:
                self.turn_order.append(monster)
        
        # 敏捷性でソート（高い順）
        self.turn_order.sort(key=lambda x: self._get_agility(x), reverse=True)
        
        logger.debug(f"ターン順序決定: {len(self.turn_order)}人/体")
    
    def _get_agility(self, actor: Union[Character, Monster]) -> int:
        """敏捷性取得"""
        if isinstance(actor, Character):
            return actor.base_stats.agility
        else:  # Monster
            return actor.stats.agility
    
    def get_current_actor(self) -> Optional[Union[Character, Monster]]:
        """現在のアクター取得"""
        if not self.turn_order or self.current_turn_index >= len(self.turn_order):
            return None
        
        return self.turn_order[self.current_turn_index]
    
    def is_player_turn(self) -> bool:
        """プレイヤーのターンかチェック"""
        current_actor = self.get_current_actor()
        return isinstance(current_actor, Character)
    
    def execute_action(self, action: CombatAction, target: Optional[Union[Character, Monster]] = None, 
                      action_data: Optional[Dict[str, Any]] = None) -> CombatResult:
        """戦闘行動実行"""
        if self.combat_state != CombatState.IN_PROGRESS:
            logger.error("戦闘中ではありません")
            return CombatResult.CONTINUE
        
        current_actor = self.get_current_actor()
        if not current_actor:
            logger.error("有効なアクターがありません")
            return CombatResult.CONTINUE
        
        if action_data is None:
            action_data = {}
        
        # ターン情報作成
        turn = CombatTurn(
            turn_number=self.turn_number,
            actor=current_actor,
            action=action,
            target=target,
            action_data=action_data
        )
        
        # 行動実行
        result = self._execute_specific_action(turn)
        
        # ターン記録
        self.combat_log.append(turn)
        
        # 次のターンへ
        self._advance_turn()
        
        # 戦闘終了条件チェック
        combat_result = self._check_combat_end()
        
        return combat_result
    
    def _execute_specific_action(self, turn: CombatTurn) -> str:
        """具体的な行動実行"""
        action_map = {
            CombatAction.ATTACK: self._execute_attack,
            CombatAction.DEFEND: self._execute_defend,
            CombatAction.CAST_SPELL: self._execute_spell,
            CombatAction.USE_ITEM: self._execute_item_use,
            CombatAction.FLEE: self._execute_flee,
            CombatAction.NEGOTIATE: self._execute_negotiate,
            CombatAction.SPECIAL_ABILITY: self._execute_special_ability,
        }
        
        executor = action_map.get(turn.action)
        if executor:
            if turn.action in [CombatAction.DEFEND, CombatAction.FLEE, CombatAction.NEGOTIATE]:
                return executor(turn.actor, turn)
            else:
                return executor(turn.actor, turn.target, turn)
        else:
            return f"{self._get_actor_name(turn.actor)}は何もしなかった"
    
    def _execute_attack(self, actor: Union[Character, Monster], 
                       target: Optional[Union[Character, Monster]], turn: CombatTurn) -> str:
        """攻撃実行"""
        if not target:
            return f"{self._get_actor_name(actor)}の攻撃対象が無効です"
        
        # 命中判定
        if not self._check_hit(actor, target):
            return f"{self._get_actor_name(actor)}の攻撃は外れた！"
        
        # ダメージ計算
        damage = self._calculate_damage(actor, target)
        
        # クリティカルヒット判定
        is_critical = random.random() < self.critical_hit_chance
        if is_critical:
            damage = int(damage * CRITICAL_DAMAGE_MULTIPLIER)
        
        # ダメージ適用
        actual_damage = self._apply_damage(target, damage)
        turn.damage_dealt = actual_damage
        
        # 統計更新
        if isinstance(actor, Character):
            self.party_stats.add_damage_dealt(actual_damage)
            if is_critical:
                self.party_stats.add_critical_hit()
        else:
            self.monster_stats.add_damage_dealt(actual_damage)
        
        # 結果メッセージ
        critical_text = "クリティカル！" if is_critical else ""
        return f"{self._get_actor_name(actor)}の攻撃！{critical_text} {self._get_actor_name(target)}に{actual_damage}ダメージ！"
    
    def _execute_defend(self, actor: Union[Character, Monster], turn: CombatTurn) -> str:
        """防御実行"""
        # 防御状態を付与（次のターンまで）
        if hasattr(actor, 'add_status_effect'):
            actor.add_status_effect('defending')
        
        return f"{self._get_actor_name(actor)}は身を守っている"
    
    def _execute_spell(self, actor: Union[Character, Monster], 
                      target: Optional[Union[Character, Monster]], turn: CombatTurn) -> str:
        """魔法実行"""
        if not isinstance(actor, Character):
            return f"{self._get_actor_name(actor)}は魔法を使えません"
        
        spell_id = turn.action_data.get('spell_id')
        if not spell_id:
            return f"{self._get_actor_name(actor)}の魔法詠唱に失敗しました"
        
        # 魔法使用可能かチェック
        spell = spell_manager.get_spell(spell_id)
        if not spell:
            return f"未知の魔法: {spell_id}"
        
        # MP消費チェック
        if not actor.can_use_spell(spell):
            return f"{self._get_actor_name(actor)}のMPが足りません"
        
        # 魔法効果適用
        result = self._apply_spell_effect(actor, spell, target)
        
        # MP消費
        actor.use_mp(spell.mp_cost)
        
        # 統計更新
        self.party_stats.add_spell_cast()
        
        return result
    
    def _execute_item_use(self, actor: Union[Character, Monster], 
                         target: Optional[Union[Character, Monster]], turn: CombatTurn) -> str:
        """アイテム使用実行"""
        if not isinstance(actor, Character):
            return f"{self._get_actor_name(actor)}はアイテムを使えません"
        
        item_instance = turn.action_data.get('item_instance')
        if not item_instance:
            return f"{self._get_actor_name(actor)}のアイテム使用に失敗しました"
        
        # アイテム使用
        result, message, results = item_usage_manager.use_item(
            item_instance, actor, target, self.party
        )
        
        # 統計更新
        self.party_stats.add_item_used()
        
        return message
    
    def _execute_flee(self, actor: Union[Character, Monster], turn: CombatTurn) -> str:
        """逃走実行"""
        if not isinstance(actor, Character):
            return f"{self._get_actor_name(actor)}は逃走できません"
        
        # 逃走成功率計算
        flee_chance = self._calculate_flee_chance()
        
        if random.random() < flee_chance:
            self.combat_state = CombatState.FLED
            return f"パーティは戦闘から逃走した！"
        else:
            return f"逃走に失敗した！"
    
    def _execute_negotiate(self, actor: Union[Character, Monster], turn: CombatTurn) -> str:
        """交渉実行"""
        if not isinstance(actor, Character):
            return f"{self._get_actor_name(actor)}は交渉できません"
        
        # 交渉成功率計算
        negotiate_chance = self._calculate_negotiate_chance()
        
        if random.random() < negotiate_chance:
            self.combat_state = CombatState.NEGOTIATED
            return f"交渉が成功した！"
        else:
            return f"交渉に失敗した！"
    
    def _execute_special_ability(self, actor: Union[Character, Monster], 
                                target: Optional[Union[Character, Monster]], turn: CombatTurn) -> str:
        """特殊能力実行"""
        ability_id = turn.action_data.get('ability_id')
        if not ability_id:
            return f"{self._get_actor_name(actor)}の特殊能力実行に失敗しました"
        
        if isinstance(actor, Monster):
            if actor.can_use_ability(ability_id):
                actor.use_ability(ability_id)
                ability = actor.get_ability(ability_id)
                return f"{self._get_actor_name(actor)}は{ability.name}を使用した！"
            else:
                return f"{self._get_actor_name(actor)}は{ability_id}を使用できません"
        
        return f"{self._get_actor_name(actor)}は特殊能力を使用できません"
    
    def _check_hit(self, attacker: Union[Character, Monster], 
                  target: Union[Character, Monster]) -> bool:
        """命中判定"""
        # 基本命中率
        base_hit_chance = BASE_HIT_CHANCE
        
        # 攻撃者の攻撃ボーナス
        if isinstance(attacker, Character):
            attack_bonus = attacker.derived_stats.attack_bonus
            attacker_agility = attacker.base_stats.agility
        else:
            attack_bonus = attacker.stats.attack_bonus
            attacker_agility = attacker.stats.agility
        
        # 対象の回避能力
        if isinstance(target, Character):
            armor_class = target.derived_stats.armor_class
            target_agility = target.base_stats.agility
        else:
            armor_class = target.stats.armor_class
            target_agility = target.stats.agility
        
        # 命中率計算
        hit_chance = base_hit_chance + (attack_bonus - armor_class + attacker_agility - target_agility) * AGILITY_MODIFIER
        hit_chance = max(HIT_CHANCE_MIN, min(HIT_CHANCE_MAX, hit_chance))
        
        return random.random() < hit_chance
    
    def _calculate_damage(self, attacker: Union[Character, Monster], 
                         target: Union[Character, Monster]) -> int:
        """ダメージ計算"""
        if isinstance(attacker, Character):
            # Phase 4装備システムと統合された攻撃力を使用
            damage = attacker.get_attack_power()
        else:
            # モンスターの攻撃力計算
            damage = attacker.get_attack_damage()
        
        # 対象の防御力
        if isinstance(target, Character):
            # Phase 4装備システムと統合された防御力を使用
            defense = target.get_defense()
        else:
            defense = target.stats.armor_class - 10
        
        # 最終ダメージ
        final_damage = max(1, damage - defense // 2)
        
        return final_damage
    
    def _apply_damage(self, target: Union[Character, Monster], damage: int) -> int:
        """ダメージ適用"""
        if isinstance(target, Character):
            target.take_damage(damage)
            actual_damage = damage  # キャラクターのtake_damageは戻り値なし
        else:
            actual_damage = target.take_damage(damage)
        
        return actual_damage
    
    def _calculate_spell_value(self, caster: Character, effect: Any) -> int:
        """魔法の効果量計算"""
        value = effect.base_value
        if effect.scaling_stat:
            scaling_bonus = getattr(caster.base_stats, effect.scaling_stat, 10)
            value += (scaling_bonus - 10) // 2
        return max(1, value)
    
    def _apply_offensive_spell(self, caster: Character, spell: Any, target: Optional[Union[Character, Monster]]) -> str:
        """攻撃系魔法適用"""
        if target and isinstance(target, Monster):
            damage = self._calculate_spell_value(caster, spell.effect)
            actual_damage = target.take_damage(damage)
            return f"{caster.name}の{spell.name}！{target.name}に{actual_damage}ダメージ！"
        else:
            return f"{caster.name}の{spell.name}は失敗した"
    
    def _apply_healing_spell(self, caster: Character, spell: Any, target: Optional[Union[Character, Monster]]) -> str:
        """回復系魔法適用"""
        if target and isinstance(target, Character):
            heal_amount = self._calculate_spell_value(caster, spell.effect)
            actual_heal = target.heal(heal_amount)
            return f"{caster.name}の{spell.name}！{target.name}が{actual_heal}回復！"
        else:
            return f"{caster.name}の{spell.name}は失敗した"
    
    def _apply_status_spell(self, caster: Character, spell: Any, target: Optional[Union[Character, Monster]]) -> str:
        """ステータス系魔法適用"""
        if target:
            effect_name = spell.effect.effect_type
            target.add_status_effect(effect_name)
            return f"{caster.name}の{spell.name}！{target.name}に{effect_name}効果が付与された！"
        else:
            return f"{caster.name}の{spell.name}は失敗した"
    
    def _apply_revival_spell(self, caster: Character, spell: Any, target: Optional[Union[Character, Monster]]) -> str:
        """蘇生系魔法適用"""
        if target and isinstance(target, Character) and not target.is_alive():
            target.revive()
            return f"{caster.name}の{spell.name}！{target.name}が蘇生した！"
        else:
            return f"{caster.name}の{spell.name}は失敗した"
    
    def _apply_spell_effect(self, caster: Character, spell: Any, 
                           target: Optional[Union[Character, Monster]]) -> str:
        """魔法効果適用"""
        spell_type = spell.spell_type.value
        
        if spell_type == 'offensive':
            return self._apply_offensive_spell(caster, spell, target)
        elif spell_type == 'healing':
            return self._apply_healing_spell(caster, spell, target)
        elif spell_type in ['buff', 'debuff']:
            return self._apply_status_spell(caster, spell, target)
        elif spell_type == 'revival':
            return self._apply_revival_spell(caster, spell, target)
        else:
            return f"{caster.name}は{spell.name}を唱えた"
    
    def _calculate_flee_chance(self) -> float:
        """逃走成功率計算"""
        # パーティの平均敏捷性
        living_chars = self.party.get_living_characters()
        if not living_chars:
            return 0.0
        
        avg_agility = sum(char.base_stats.agility for char in living_chars) / len(living_chars)
        
        # モンスターの平均敏捷性
        living_monsters = [m for m in self.monsters if m.is_alive]
        if not living_monsters:
            return 1.0
        
        avg_monster_agility = sum(m.stats.agility for m in living_monsters) / len(living_monsters)
        
        # 基本逃走率 + 敏捷性差
        flee_chance = BASE_FLEE_CHANCE + (avg_agility - avg_monster_agility) * AGILITY_MODIFIER
        return max(FLEE_CHANCE_MIN, min(FLEE_CHANCE_MAX, flee_chance))
    
    def _calculate_negotiate_chance(self) -> float:
        """交渉成功率計算"""
        # パーティの最高知力
        living_chars = self.party.get_living_characters()
        if not living_chars:
            return 0.0
        
        max_intelligence = max(char.base_stats.intelligence for char in living_chars)
        
        # 基本交渉率 + 知力ボーナス
        negotiate_chance = BASE_NEGOTIATE_CHANCE + (max_intelligence - 10) * AGILITY_MODIFIER
        return max(NEGOTIATE_CHANCE_MIN, min(NEGOTIATE_CHANCE_MAX, negotiate_chance))
    
    def _advance_turn(self):
        """ターン進行"""
        self.current_turn_index += 1
        
        # 生存者のみでターン順序を再構築
        if self.current_turn_index >= len(self.turn_order):
            self.current_turn_index = 0
            self.turn_number += 1
            self._update_turn_order()
            self._process_turn_effects()
    
    def _update_turn_order(self):
        """ターン順序更新（生存者のみ）"""
        old_order = self.turn_order.copy()
        self.turn_order = []
        
        # 生存中のキャラクター
        for character in self.party.get_living_characters():
            self.turn_order.append(character)
        
        # 生存中のモンスター
        for monster in self.monsters:
            if monster.is_alive:
                self.turn_order.append(monster)
        
        # 敏捷性でソート
        self.turn_order.sort(key=lambda x: self._get_agility(x), reverse=True)
        
        if len(self.turn_order) != len(old_order):
            logger.debug(f"ターン順序更新: {len(old_order)} -> {len(self.turn_order)}")
    
    def _process_turn_effects(self):
        """ターン効果処理"""
        # キャラクターの状態効果処理
        for character in self.party.get_living_characters():
            if hasattr(character, 'process_turn_effects'):
                character.process_turn_effects()
        
        # モンスターの状態効果処理
        for monster in self.monsters:
            if monster.is_alive:
                monster.update_cooldowns()
                # 状態効果処理（今後実装）
    
    def _check_combat_end(self) -> CombatResult:
        """戦闘終了条件チェック"""
        if self.combat_state in [CombatState.FLED, CombatState.NEGOTIATED]:
            return CombatResult.FLED if self.combat_state == CombatState.FLED else CombatResult.NEGOTIATED
        
        # 全キャラクター死亡チェック
        living_characters = self.party.get_living_characters()
        if not living_characters:
            self.combat_state = CombatState.DEFEAT
            return CombatResult.DEFEAT
        
        # 全モンスター死亡チェック
        living_monsters = [m for m in self.monsters if m.is_alive]
        if not living_monsters:
            self.combat_state = CombatState.VICTORY
            return CombatResult.VICTORY
        
        return CombatResult.CONTINUE
    
    def _get_actor_name(self, actor: Union[Character, Monster]) -> str:
        """アクター名取得"""
        return actor.name
    
    def get_combat_status(self) -> Dict[str, Any]:
        """戦闘状況取得"""
        return {
            'state': self.combat_state.value,
            'turn_number': self.turn_number,
            'current_actor': self._get_actor_name(self.get_current_actor()) if self.get_current_actor() else None,
            'is_player_turn': self.is_player_turn(),
            'party_members': len(self.party.get_living_characters()) if self.party else 0,
            'monsters_alive': len([m for m in self.monsters if m.is_alive]),
            'party_stats': self.party_stats,
            'combat_log_size': len(self.combat_log)
        }
    
    def get_valid_targets(self, actor: Union[Character, Monster], action: CombatAction) -> List[Union[Character, Monster]]:
        """有効な対象一覧取得"""
        targets = []
        
        if action in [CombatAction.ATTACK, CombatAction.CAST_SPELL]:
            if isinstance(actor, Character):
                # キャラクターはモンスターを攻撃
                targets = [m for m in self.monsters if m.is_alive]
            else:
                # モンスターはキャラクターを攻撃
                targets = self.party.get_living_characters()
        
        elif action in [CombatAction.USE_ITEM]:
            if isinstance(actor, Character):
                # アイテムは味方に使用可能
                targets = self.party.get_living_characters()
        
        return targets
    
    def reset_combat(self):
        """戦闘リセット"""
        self.combat_state = CombatState.PREPARATION
        self.party = None
        self.monsters = []
        self.turn_order = []
        self.current_turn_index = 0
        self.turn_number = 1
        self.combat_log = []
        self.party_stats = CombatStats()
        self.monster_stats = CombatStats()
        
        logger.info("戦闘をリセットしました")
    
    def cleanup(self):
        """リソースのクリーンアップ"""
        try:
            # 戦闘データをリセット
            self.reset_combat()
            
            # 追加のクリーンアップ
            self.turn_order.clear()
            self.combat_log.clear()
            
            logger.info("CombatManager リソースをクリーンアップしました")
        except Exception as e:
            logger.error(f"CombatManager クリーンアップ中にエラー: {e}")


# グローバルインスタンス
combat_manager = CombatManager()