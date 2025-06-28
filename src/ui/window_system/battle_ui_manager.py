"""
BattleUIManager クラス

戦闘UI状態管理とロジック

Fowler式リファクタリング：Extract Class パターン
"""

from typing import Dict, List, Any, Optional, Tuple, Callable
from src.ui.window_system.battle_types import (
    BattlePhase, BattleActionType, CharacterStatus, EnemyStatus,
    BattleAction, BattleUIState, BattleLogEntry, TargetType,
    StatusEffect, KeyboardShortcut, ActionMenuEntry, TargetInfo,
    BattleTurn, AnimationInfo
)
from src.utils.logger import logger


class BattleUIManager:
    """
    戦闘UI管理クラス
    
    戦闘状態の管理、アクション処理、ターン進行を担当
    """
    
    def __init__(self, battle_manager: Any, party: Any, enemies: Any):
        """
        戦闘UIマネージャーを初期化
        
        Args:
            battle_manager: 戦闘マネージャー
            party: パーティ
            enemies: 敵グループ
        """
        self.battle_manager = battle_manager
        self.party = party
        self.enemies = enemies
        
        # UI状態
        self.ui_state = BattleUIState(current_phase=BattlePhase.PLAYER_ACTION)
        self.menu_stack: List[str] = []
        self.animations_playing: List[AnimationInfo] = []
        
        # ターン情報
        self.current_turn = BattleTurn(turn_number=1)
        
        # 戦闘ログ
        self.battle_log: List[BattleLogEntry] = []
        self.log_max_entries = 100
        
        logger.debug("BattleUIManagerを初期化")
    
    def get_current_phase(self) -> BattlePhase:
        """現在の戦闘フェーズを取得"""
        return self.ui_state.current_phase
    
    def set_phase(self, new_phase: BattlePhase) -> None:
        """戦闘フェーズを設定"""
        old_phase = self.ui_state.current_phase
        self.ui_state.current_phase = new_phase
        
        logger.debug(f"戦闘フェーズ変更: {old_phase} -> {new_phase}")
    
    def get_party_status(self) -> List[CharacterStatus]:
        """パーティステータスを取得"""
        party_status = []
        
        if hasattr(self.party, 'get_alive_members'):
            alive_members = self.party.get_alive_members()
            if hasattr(alive_members, '__iter__'):
                for character in alive_members:
                    status = CharacterStatus(
                        character=character,
                        hp=getattr(character, 'hp', 0),
                        max_hp=getattr(character, 'max_hp', 1),
                        mp=getattr(character, 'mp', 0),
                        max_mp=getattr(character, 'max_mp', 1),
                        status_effects=getattr(character, 'status_effects', []),
                        is_alive=getattr(character, 'hp', 0) > 0
                    )
                    party_status.append(status)
        
        return party_status
    
    def get_enemy_status(self) -> List[EnemyStatus]:
        """敵ステータスを取得"""
        enemy_status = []
        
        if hasattr(self.enemies, 'get_all_enemies'):
            all_enemies = self.enemies.get_all_enemies()
            if hasattr(all_enemies, '__iter__'):
                for enemy in all_enemies:
                    status = EnemyStatus(
                        enemy=enemy,
                        hp=getattr(enemy, 'hp', 0),
                        max_hp=getattr(enemy, 'max_hp', 1),
                        status_effects=getattr(enemy, 'status_effects', []),
                        is_alive=hasattr(enemy, 'is_alive') and enemy.is_alive() if hasattr(enemy, 'is_alive') else getattr(enemy, 'hp', 0) > 0
                    )
                    enemy_status.append(status)
        
        return enemy_status
    
    def get_available_actions(self) -> List[BattleAction]:
        """利用可能なアクション一覧を取得"""
        actions = []
        
        if hasattr(self.battle_manager, 'get_available_actions'):
            manager_actions = self.battle_manager.get_available_actions()
            if hasattr(manager_actions, '__iter__'):
                for action_data in manager_actions:
                    if isinstance(action_data, dict):
                        action = BattleAction(
                            action_type=BattleActionType(action_data.get('type', 'attack')),
                            name=action_data.get('name', ''),
                            enabled=action_data.get('enabled', True),
                            description=action_data.get('description', ''),
                            mp_cost=action_data.get('mp_cost', 0)
                        )
                        actions.append(action)
        else:
            # デフォルトアクション
            actions = [
                BattleAction(BattleActionType.ATTACK, "攻撃"),
                BattleAction(BattleActionType.MAGIC, "魔法"),
                BattleAction(BattleActionType.ITEM, "アイテム"),
                BattleAction(BattleActionType.DEFEND, "防御")
            ]
        
        return actions
    
    def can_perform_action(self, action_type: BattleActionType) -> bool:
        """アクションが実行可能かチェック"""
        if self.ui_state.current_phase != BattlePhase.PLAYER_ACTION:
            return False
        
        if hasattr(self.battle_manager, 'can_perform_action'):
            return self.battle_manager.can_perform_action(action_type)
        
        return True
    
    def select_action(self, action_type: BattleActionType) -> bool:
        """アクションを選択"""
        if not self.can_perform_action(action_type):
            return False
        
        self.ui_state.selected_action = action_type
        
        # ターゲット選択が必要な場合はフェーズを変更
        if action_type in [BattleActionType.ATTACK, BattleActionType.MAGIC]:
            self.ui_state.current_phase = BattlePhase.TARGET_SELECTION
        
        logger.debug(f"アクション選択: {action_type}")
        return True
    
    def get_valid_targets(self) -> List[TargetInfo]:
        """有効なターゲット一覧を取得"""
        targets = []
        
        if not self.ui_state.selected_action:
            return targets
        
        # アクションタイプに応じてターゲットを決定
        if self.ui_state.selected_action == BattleActionType.ATTACK:
            # 攻撃は生きている敵のみ
            enemy_status = self.get_enemy_status()
            for i, status in enumerate(enemy_status):
                if status.is_alive:
                    target_info = TargetInfo(
                        target=status.enemy,
                        target_type=TargetType.SINGLE_ENEMY,
                        position=(i * 100, 100),
                        selectable=True
                    )
                    targets.append(target_info)
        
        elif self.ui_state.selected_action == BattleActionType.MAGIC:
            # 魔法は敵と味方両方（魔法の種類による）
            # 簡単のため敵のみ
            enemy_status = self.get_enemy_status()
            for i, status in enumerate(enemy_status):
                if status.is_alive:
                    target_info = TargetInfo(
                        target=status.enemy,
                        target_type=TargetType.SINGLE_ENEMY,
                        position=(i * 100, 100),
                        selectable=True
                    )
                    targets.append(target_info)
        
        return targets
    
    def select_target(self, target: Any) -> bool:
        """ターゲットを選択"""
        if self.ui_state.current_phase != BattlePhase.TARGET_SELECTION:
            return False
        
        self.ui_state.selected_target = target
        self.ui_state.current_phase = BattlePhase.ACTION_EXECUTION
        
        logger.debug(f"ターゲット選択: {target}")
        return True
    
    def advance_turn(self) -> bool:
        """ターンを進行"""
        if hasattr(self.battle_manager, 'advance_turn'):
            if self.battle_manager.advance_turn():
                self.current_turn.turn_number += 1
                self.ui_state.current_phase = BattlePhase.ENEMY_TURN
                
                # 選択状態をリセット
                self.ui_state.selected_action = None
                self.ui_state.selected_target = None
                
                logger.debug(f"ターン進行: {self.current_turn.turn_number}")
                return True
        
        return False
    
    def add_battle_log_entry(self, message: str, entry_type: str = "action", 
                           character: Any = None, target: Any = None, value: Optional[int] = None) -> None:
        """戦闘ログエントリを追加"""
        import time
        
        entry = BattleLogEntry(
            message=message,
            timestamp=time.time(),
            entry_type=entry_type,
            character=character,
            target=target,
            value=value
        )
        
        self.battle_log.append(entry)
        
        # ログ数制限
        if len(self.battle_log) > self.log_max_entries:
            self.battle_log = self.battle_log[-self.log_max_entries:]
        
        logger.debug(f"戦闘ログ追加: {message}")
    
    def get_battle_log_messages(self, max_entries: int = 10) -> List[str]:
        """戦闘ログメッセージを取得"""
        if hasattr(self.battle_manager, 'get_battle_log'):
            manager_log = self.battle_manager.get_battle_log()
            if hasattr(manager_log, '__iter__'):
                return list(manager_log)[-max_entries:]
        
        # フォールバック: 内部ログから取得
        return [entry.message for entry in self.battle_log[-max_entries:]]
    
    def get_available_spells(self) -> List[Any]:
        """利用可能な魔法一覧を取得"""
        spells = []
        
        if hasattr(self.battle_manager, 'get_current_character'):
            current_character = self.battle_manager.get_current_character()
            if hasattr(current_character, 'get_available_spells'):
                character_spells = current_character.get_available_spells()
                if hasattr(character_spells, '__iter__'):
                    return list(character_spells)
        
        return spells
    
    def get_usable_items(self) -> List[Any]:
        """使用可能なアイテム一覧を取得"""
        items = []
        
        if hasattr(self.party, 'get_usable_items'):
            party_items = self.party.get_usable_items()
            if hasattr(party_items, '__iter__'):
                return list(party_items)
        
        return items
    
    def push_menu(self, menu_name: str) -> None:
        """メニューをスタックにプッシュ"""
        self.menu_stack.append(menu_name)
        logger.debug(f"メニュープッシュ: {menu_name}")
    
    def pop_menu(self) -> Optional[str]:
        """メニューをスタックからポップ"""
        if self.menu_stack:
            menu_name = self.menu_stack.pop()
            logger.debug(f"メニューポップ: {menu_name}")
            return menu_name
        return None
    
    def get_current_menu(self) -> Optional[str]:
        """現在のメニューを取得"""
        return self.menu_stack[-1] if self.menu_stack else None
    
    def start_animation(self, animation: AnimationInfo) -> None:
        """アニメーションを開始"""
        self.animations_playing.append(animation)
        logger.debug(f"アニメーション開始: {animation.animation_type}")
    
    def update_animations(self, delta_time: float) -> None:
        """アニメーションを更新"""
        completed_animations = []
        
        for animation in self.animations_playing:
            animation.duration -= delta_time
            if animation.duration <= 0:
                if animation.callback:
                    animation.callback()
                completed_animations.append(animation)
        
        # 完了したアニメーションを削除
        for animation in completed_animations:
            self.animations_playing.remove(animation)
    
    def is_animation_playing(self) -> bool:
        """アニメーションが再生中かチェック"""
        return len(self.animations_playing) > 0
    
    def get_keyboard_shortcuts(self) -> Dict[int, BattleActionType]:
        """キーボードショートカットを取得"""
        import pygame
        return {
            pygame.K_a: BattleActionType.ATTACK,
            pygame.K_m: BattleActionType.MAGIC,
            pygame.K_i: BattleActionType.ITEM,
            pygame.K_d: BattleActionType.DEFEND,
            pygame.K_e: BattleActionType.ESCAPE
        }
    
    def reset_battle_state(self) -> None:
        """戦闘状態をリセット"""
        self.ui_state = BattleUIState(current_phase=BattlePhase.PLAYER_ACTION)
        self.menu_stack.clear()
        self.animations_playing.clear()
        self.current_turn = BattleTurn(turn_number=1)
        
        logger.debug("戦闘状態リセット")
    
    def get_manager_summary(self) -> Dict[str, Any]:
        """マネージャーサマリーを取得"""
        return {
            'current_phase': self.ui_state.current_phase.value,
            'selected_action': self.ui_state.selected_action.value if self.ui_state.selected_action else None,
            'selected_target': self.ui_state.selected_target,
            'turn_number': self.current_turn.turn_number,
            'menu_stack': self.menu_stack.copy(),
            'animations_count': len(self.animations_playing),
            'battle_log_entries': len(self.battle_log),
            'party_members': len(self.get_party_status()),
            'enemies_count': len(self.get_enemy_status())
        }