"""戦闘状態管理システム

CombatManagerの状態管理をStateパターンで分離。
Fowlerの「Replace State Code with State」パターンを適用。
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional, Union, Tuple
from enum import Enum

from src.character.character import Character
from src.character.party import Party
from src.monsters.monster import Monster
from src.combat.combat_strategies import CombatContext, ActionResult, CombatStrategyFactory
from src.utils.logger import logger


class CombatPhase(Enum):
    """戦闘フェーズ"""
    PREPARATION = "preparation"     # 準備段階
    TURN_ORDER = "turn_order"       # ターン順決定
    PLAYER_TURN = "player_turn"     # プレイヤーターン
    MONSTER_TURN = "monster_turn"   # モンスターターン
    RESOLUTION = "resolution"       # 結果判定
    VICTORY = "victory"             # 勝利
    DEFEAT = "defeat"               # 敗北
    FLED = "fled"                   # 逃走
    NEGOTIATED = "negotiated"       # 交渉成功


class CombatState(ABC):
    """戦闘状態の基底クラス"""
    
    def __init__(self, combat_manager: 'CombatManager'):
        self.combat_manager = combat_manager
    
    @abstractmethod
    def enter(self) -> bool:
        """状態に入る際の処理"""
        pass
    
    @abstractmethod
    def execute(self) -> Optional['CombatState']:
        """状態の実行処理。次の状態を返す"""
        pass
    
    @abstractmethod
    def exit(self):
        """状態から出る際の処理"""
        pass
    
    @abstractmethod
    def get_phase(self) -> CombatPhase:
        """現在のフェーズを取得"""
        pass
    
    def can_transition_to(self, next_state: 'CombatState') -> bool:
        """指定された状態に遷移可能かチェック"""
        return True  # デフォルトは遷移可能


class PreparationState(CombatState):
    """準備段階状態"""
    
    def get_phase(self) -> CombatPhase:
        return CombatPhase.PREPARATION
    
    def enter(self) -> bool:
        """準備段階に入る"""
        logger.info("戦闘準備段階に入りました")
        
        # 戦闘統計の初期化
        self.combat_manager.initialize_combat_stats()
        
        # パーティとモンスターの状態確認
        if not self._validate_combatants():
            return False
        
        # 戦闘開始ログ
        party_names = [char.name for char in self.combat_manager.party.get_living_characters()]
        monster_names = [monster.name for monster in self.combat_manager.monsters]
        
        logger.info(f"戦闘開始: {', '.join(party_names)} vs {', '.join(monster_names)}")
        
        return True
    
    def execute(self) -> Optional['CombatState']:
        """準備段階の実行"""
        # ターン順決定段階に移行
        return TurnOrderState(self.combat_manager)
    
    def exit(self):
        """準備段階から出る"""
        logger.debug("準備段階を終了")
    
    def _validate_combatants(self) -> bool:
        """戦闘参加者の妥当性を確認"""
        living_characters = self.combat_manager.party.get_living_characters()
        if not living_characters:
            logger.error("生存しているパーティメンバーがいません")
            return False
        
        alive_monsters = [m for m in self.combat_manager.monsters if m.is_alive()]
        if not alive_monsters:
            logger.error("生存しているモンスターがいません")
            return False
        
        return True


class TurnOrderState(CombatState):
    """ターン順決定状態"""
    
    def get_phase(self) -> CombatPhase:
        return CombatPhase.TURN_ORDER
    
    def enter(self) -> bool:
        """ターン順決定に入る"""
        logger.debug("ターン順を決定中")
        
        # ターン順の計算
        self._calculate_turn_order()
        
        return True
    
    def execute(self) -> Optional['CombatState']:
        """ターン順決定の実行"""
        # 最初のアクターがプレイヤーかモンスターかで次の状態を決定
        current_actor = self.combat_manager.get_current_actor()
        
        if isinstance(current_actor, Character):
            return PlayerTurnState(self.combat_manager)
        else:
            return MonsterTurnState(self.combat_manager)
    
    def exit(self):
        """ターン順決定から出る"""
        logger.debug("ターン順決定完了")
    
    def _calculate_turn_order(self):
        """ターン順を計算"""
        all_actors = []
        
        # パーティメンバーを追加
        for char in self.combat_manager.party.get_living_characters():
            agility = getattr(char.base_stats, 'agility', 10) if hasattr(char, 'base_stats') else 10
            initiative = agility + random.randint(1, 10)
            all_actors.append((char, initiative))
        
        # モンスターを追加
        for monster in self.combat_manager.monsters:
            if monster.is_alive():
                agility = getattr(monster, 'agility', 10)
                initiative = agility + random.randint(1, 10)
                all_actors.append((monster, initiative))
        
        # イニシアチブの高い順にソート
        all_actors.sort(key=lambda x: x[1], reverse=True)
        
        # ターン順を設定
        self.combat_manager.turn_order = [actor for actor, init in all_actors]
        self.combat_manager.current_turn_index = 0
        
        logger.debug(f"ターン順: {[actor.name for actor in self.combat_manager.turn_order]}")


class PlayerTurnState(CombatState):
    """プレイヤーターン状態"""
    
    def get_phase(self) -> CombatPhase:
        return CombatPhase.PLAYER_TURN
    
    def enter(self) -> bool:
        """プレイヤーターンに入る"""
        current_character = self.combat_manager.get_current_actor()
        logger.debug(f"{current_character.name}のターン開始")
        
        # 状態異常のターン経過処理
        if hasattr(current_character, 'status_effects') and current_character.status_effects:
            expired_effects = current_character.status_effects.process_turn_effects()
            for effect in expired_effects:
                logger.info(f"{current_character.name}の{effect.name}が切れた")
        
        return True
    
    def execute(self) -> Optional['CombatState']:
        """プレイヤーターンの実行"""
        # プレイヤーの行動が完了したら次のターンまたは結果判定に移行
        if self.combat_manager.is_action_completed():
            return self._determine_next_state()
        
        # 行動が未完了の場合は現在の状態を維持
        return None
    
    def exit(self):
        """プレイヤーターンから出る"""
        current_character = self.combat_manager.get_current_actor()
        logger.debug(f"{current_character.name}のターン終了")
    
    def _determine_next_state(self) -> Optional['CombatState']:
        """次の状態を決定"""
        # 戦闘終了条件をチェック
        if self._check_victory_condition():
            return VictoryState(self.combat_manager)
        elif self._check_defeat_condition():
            return DefeatState(self.combat_manager)
        elif self._check_flee_condition():
            return FledState(self.combat_manager)
        elif self._check_negotiate_condition():
            return NegotiatedState(self.combat_manager)
        
        # 次のアクターに移行
        self.combat_manager.advance_turn()
        next_actor = self.combat_manager.get_current_actor()
        
        if isinstance(next_actor, Character):
            return PlayerTurnState(self.combat_manager)
        else:
            return MonsterTurnState(self.combat_manager)
    
    def _check_victory_condition(self) -> bool:
        """勝利条件をチェック"""
        alive_monsters = [m for m in self.combat_manager.monsters if m.is_alive()]
        return len(alive_monsters) == 0
    
    def _check_defeat_condition(self) -> bool:
        """敗北条件をチェック"""
        living_characters = self.combat_manager.party.get_living_characters()
        return len(living_characters) == 0
    
    def _check_flee_condition(self) -> bool:
        """逃走条件をチェック"""
        return self.combat_manager.flee_attempted and self.combat_manager.flee_successful
    
    def _check_negotiate_condition(self) -> bool:
        """交渉条件をチェック"""
        return self.combat_manager.negotiate_attempted and self.combat_manager.negotiate_successful


class MonsterTurnState(CombatState):
    """モンスターターン状態"""
    
    def get_phase(self) -> CombatPhase:
        return CombatPhase.MONSTER_TURN
    
    def enter(self) -> bool:
        """モンスターターンに入る"""
        current_monster = self.combat_manager.get_current_actor()
        logger.debug(f"{current_monster.name}のターン開始")
        
        return True
    
    def execute(self) -> Optional['CombatState']:
        """モンスターターンの実行"""
        current_monster = self.combat_manager.get_current_actor()
        
        # モンスターAIで行動を決定
        action_result = self._execute_monster_ai(current_monster)
        
        # 行動結果をログ出力
        logger.info(action_result.message)
        
        # 戦闘統計を更新
        self.combat_manager.update_combat_stats(current_monster, action_result)
        
        return self._determine_next_state()
    
    def exit(self):
        """モンスターターンから出る"""
        current_monster = self.combat_manager.get_current_actor()
        logger.debug(f"{current_monster.name}のターン終了")
    
    def _execute_monster_ai(self, monster: Monster) -> ActionResult:
        """モンスターAIを実行"""
        # 簡単なAI：基本的に攻撃
        living_characters = self.combat_manager.party.get_living_characters()
        if not living_characters:
            return ActionResult(
                success=False,
                message=f"{monster.name}は攻撃対象を見つけられない"
            )
        
        # ランダムに対象を選択
        import random
        target = random.choice(living_characters)
        
        # 攻撃戦略を使用
        context = CombatContext(
            attacker=monster,
            target=target,
            party=self.combat_manager.party,
            monsters=self.combat_manager.monsters,
            turn_number=self.combat_manager.current_turn,
            action_data={}
        )
        
        attack_strategy = CombatStrategyFactory.get_strategy('attack')
        return attack_strategy.execute(context)
    
    def _determine_next_state(self) -> Optional['CombatState']:
        """次の状態を決定"""
        # 戦闘終了条件をチェック
        if self._check_victory_condition():
            return VictoryState(self.combat_manager)
        elif self._check_defeat_condition():
            return DefeatState(self.combat_manager)
        
        # 次のアクターに移行
        self.combat_manager.advance_turn()
        next_actor = self.combat_manager.get_current_actor()
        
        if isinstance(next_actor, Character):
            return PlayerTurnState(self.combat_manager)
        else:
            return MonsterTurnState(self.combat_manager)
    
    def _check_victory_condition(self) -> bool:
        """勝利条件をチェック"""
        alive_monsters = [m for m in self.combat_manager.monsters if m.is_alive()]
        return len(alive_monsters) == 0
    
    def _check_defeat_condition(self) -> bool:
        """敗北条件をチェック"""
        living_characters = self.combat_manager.party.get_living_characters()
        return len(living_characters) == 0


class VictoryState(CombatState):
    """勝利状態"""
    
    def get_phase(self) -> CombatPhase:
        return CombatPhase.VICTORY
    
    def enter(self) -> bool:
        """勝利状態に入る"""
        logger.info("戦闘勝利！")
        
        # 勝利処理
        self._process_victory_rewards()
        
        return True
    
    def execute(self) -> Optional['CombatState']:
        """勝利状態の実行"""
        # 戦闘終了
        self.combat_manager.end_combat('victory')
        return None
    
    def exit(self):
        """勝利状態から出る"""
        logger.debug("勝利処理完了")
    
    def _process_victory_rewards(self):
        """勝利報酬の処理"""
        # 経験値とゴールドの計算
        total_exp = sum(getattr(m, 'experience_value', 50) for m in self.combat_manager.monsters)
        total_gold = sum(getattr(m, 'gold_value', 20) for m in self.combat_manager.monsters)
        
        # パーティに報酬を付与
        for character in self.combat_manager.party.get_living_characters():
            character.experience.add_experience(total_exp, {})  # XPテーブルは空で簡単に
        
        self.combat_manager.party.gold += total_gold
        
        logger.info(f"獲得経験値: {total_exp}, 獲得ゴールド: {total_gold}")


class DefeatState(CombatState):
    """敗北状態"""
    
    def get_phase(self) -> CombatPhase:
        return CombatPhase.DEFEAT
    
    def enter(self) -> bool:
        """敗北状態に入る"""
        logger.info("戦闘敗北...")
        
        # 敗北処理
        self._process_defeat_penalty()
        
        return True
    
    def execute(self) -> Optional['CombatState']:
        """敗北状態の実行"""
        # 戦闘終了
        self.combat_manager.end_combat('defeat')
        return None
    
    def exit(self):
        """敗北状態から出る"""
        logger.debug("敗北処理完了")
    
    def _process_defeat_penalty(self):
        """敗北ペナルティの処理"""
        # 金の半分を失う
        lost_gold = self.combat_manager.party.gold // 2
        self.combat_manager.party.gold -= lost_gold
        
        logger.info(f"敗北により{lost_gold}ゴールドを失いました")


class FledState(CombatState):
    """逃走状態"""
    
    def get_phase(self) -> CombatPhase:
        return CombatPhase.FLED
    
    def enter(self) -> bool:
        """逃走状態に入る"""
        logger.info("戦闘から逃走しました")
        return True
    
    def execute(self) -> Optional['CombatState']:
        """逃走状態の実行"""
        # 戦闘終了
        self.combat_manager.end_combat('fled')
        return None
    
    def exit(self):
        """逃走状態から出る"""
        logger.debug("逃走処理完了")


class NegotiatedState(CombatState):
    """交渉成功状態"""
    
    def get_phase(self) -> CombatPhase:
        return CombatPhase.NEGOTIATED
    
    def enter(self) -> bool:
        """交渉成功状態に入る"""
        logger.info("交渉成功！")
        
        # 交渉成功による報酬
        self._process_negotiation_rewards()
        
        return True
    
    def execute(self) -> Optional['CombatState']:
        """交渉成功状態の実行"""
        # 戦闘終了
        self.combat_manager.end_combat('negotiated')
        return None
    
    def exit(self):
        """交渉成功状態から出る"""
        logger.debug("交渉処理完了")
    
    def _process_negotiation_rewards(self):
        """交渉成功報酬の処理"""
        # 経験値は半分、ゴールドは通常通り
        total_exp = sum(getattr(m, 'experience_value', 50) for m in self.combat_manager.monsters) // 2
        total_gold = sum(getattr(m, 'gold_value', 20) for m in self.combat_manager.monsters)
        
        # パーティに報酬を付与
        for character in self.combat_manager.party.get_living_characters():
            character.experience.add_experience(total_exp, {})
        
        self.combat_manager.party.gold += total_gold
        
        logger.info(f"交渉により獲得 - 経験値: {total_exp}, ゴールド: {total_gold}")


class CombatStateMachine:
    """戦闘状態機械"""
    
    def __init__(self, combat_manager: 'CombatManager'):
        self.combat_manager = combat_manager
        self.current_state: Optional[CombatState] = None
        self.state_history: List[str] = []
    
    def start_combat(self) -> bool:
        """戦闘を開始"""
        initial_state = PreparationState(self.combat_manager)
        return self.transition_to(initial_state)
    
    def update(self) -> bool:
        """状態機械を更新"""
        if not self.current_state:
            return False
        
        # 現在の状態を実行
        next_state = self.current_state.execute()
        
        # 次の状態がある場合は遷移
        if next_state:
            return self.transition_to(next_state)
        
        return True
    
    def transition_to(self, new_state: CombatState) -> bool:
        """指定された状態に遷移"""
        # 現在の状態を終了
        if self.current_state:
            if not self.current_state.can_transition_to(new_state):
                logger.warning(f"状態遷移が許可されていません: {self.current_state.__class__.__name__} -> {new_state.__class__.__name__}")
                return False
            
            self.current_state.exit()
            self.state_history.append(self.current_state.__class__.__name__)
        
        # 新しい状態に入る
        self.current_state = new_state
        success = self.current_state.enter()
        
        if success:
            logger.debug(f"戦闘状態遷移: {new_state.__class__.__name__}")
        else:
            logger.error(f"状態遷移に失敗: {new_state.__class__.__name__}")
            self.current_state = None
        
        return success
    
    def get_current_phase(self) -> Optional[CombatPhase]:
        """現在のフェーズを取得"""
        if self.current_state:
            return self.current_state.get_phase()
        return None
    
    def is_combat_active(self) -> bool:
        """戦闘がアクティブかチェック"""
        if not self.current_state:
            return False
        
        phase = self.current_state.get_phase()
        return phase not in [CombatPhase.VICTORY, CombatPhase.DEFEAT, CombatPhase.FLED, CombatPhase.NEGOTIATED]