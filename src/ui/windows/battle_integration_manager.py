"""
戦闘UI統合マネージャー

ダンジョンシステムとBattleUIWindowの橋渡しを行う
"""

from typing import Optional, Dict, Any, Callable
from dataclasses import dataclass

from src.ui.window_system import WindowManager
from src.ui.window_system.battle_ui_window import BattleUIWindow
from src.combat.combat_manager import CombatManager, CombatState
from src.character.party import Party
from src.monsters.monster import Monster
from src.utils.logger import logger


@dataclass
class BattleContext:
    """戦闘コンテキスト"""
    dungeon_level: int
    dungeon_x: int
    dungeon_y: int
    encounter_type: str
    return_callback: Optional[Callable] = None


class BattleIntegrationManager:
    """戦闘UI統合マネージャー"""
    
    def __init__(self):
        self.window_manager = WindowManager.get_instance()
        self.current_battle_window: Optional[BattleUIWindow] = None
        self.current_combat_manager: Optional[CombatManager] = None
        self.battle_context: Optional[BattleContext] = None
        
        logger.info("BattleIntegrationManagerを初期化しました")
    
    def start_battle(self, party: Party, enemies: list[Monster], 
                     battle_context: BattleContext) -> bool:
        """
        戦闘を開始
        
        Args:
            party: パーティ
            enemies: 敵リスト
            battle_context: 戦闘コンテキスト
            
        Returns:
            bool: 戦闘開始成功フラグ
        """
        try:
            # 戦闘コンテキストを保存
            self.battle_context = battle_context
            
            # CombatManagerを作成・設定
            self.current_combat_manager = CombatManager()
            self.current_combat_manager.party = party
            self.current_combat_manager.monsters = enemies
            
            # BattleUIWindow用設定を作成
            battle_config = self._create_battle_config(
                self.current_combat_manager, party, enemies
            )
            
            # ユニークなウィンドウIDを生成
            import time
            unique_id = f"integrated_battle_{int(time.time() * 1000000)}"
            
            # BattleUIWindowを作成
            self.current_battle_window = self.window_manager.create_window(
                window_class=BattleUIWindow,
                window_id=unique_id,
                battle_config=battle_config
            )
            
            # 戦闘開始メッセージを送信
            self.current_battle_window.send_message('battle_started', {
                'party': party,
                'enemies': enemies,
                'context': battle_context
            })
            
            logger.info(f"戦闘を開始しました: 敵数={len(enemies)}")
            return True
            
        except Exception as e:
            logger.error(f"戦闘開始エラー: {e}")
            return False
    
    def end_battle(self, victory: bool = False) -> bool:
        """
        戦闘を終了
        
        Args:
            victory: 勝利フラグ
            
        Returns:
            bool: 戦闘終了成功フラグ
        """
        try:
            if not self.current_battle_window:
                logger.warning("終了すべき戦闘がありません")
                return False
            
            # 戦闘結果を取得
            battle_result = None
            if self.current_combat_manager:
                battle_result = self._get_battle_result(victory)
            
            # 戦闘終了メッセージを送信
            self.current_battle_window.send_message('battle_ended', {
                'victory': victory,
                'result': battle_result,
                'context': self.battle_context
            })
            
            # ウィンドウを閉じる
            self.window_manager.hide_window(self.current_battle_window)
            
            # ウィンドウのクリーンアップ（利用可能な場合のみ）
            if hasattr(self.current_battle_window, 'cleanup'):
                self.current_battle_window.cleanup()
            
            # リターンコールバックを実行
            if self.battle_context and self.battle_context.return_callback:
                self.battle_context.return_callback(victory, battle_result)
            
            # リソースクリーンアップ
            self.current_battle_window = None
            self.current_combat_manager = None
            self.battle_context = None
            
            logger.info(f"戦闘を終了しました: 勝利={victory}")
            return True
            
        except Exception as e:
            logger.error(f"戦闘終了エラー: {e}")
            return False
    
    def is_battle_active(self) -> bool:
        """戦闘が進行中かどうか"""
        return (self.current_battle_window is not None and 
                self.current_combat_manager is not None)
    
    def get_battle_state(self) -> Optional[CombatState]:
        """現在の戦闘状態を取得"""
        if self.current_combat_manager:
            return self.current_combat_manager.combat_state
        return None
    
    def _create_battle_config(self, combat_manager: CombatManager, 
                             party: Party, enemies: list[Monster]) -> Dict[str, Any]:
        """BattleUIWindow用設定を作成"""
        return {
            'battle_manager': combat_manager,
            'party': party,
            'enemies': enemies,
            'show_battle_log': True,
            'show_status_effects': True,
            'enable_keyboard_shortcuts': True,
            'enable_animations': True,
            'auto_advance_log': False,
            'log_max_entries': 100,
            'layout': {
                'party_panel_width': 200,
                'enemy_panel_width': 200,
                'action_menu_height': 150,
                'battle_log_height': 200
            }
        }
    
    def _get_battle_result(self, victory: bool) -> Dict[str, Any]:
        """戦闘結果を取得"""
        if not self.current_combat_manager:
            return {}
        
        return {
            'victory': victory,
            'state': self.current_combat_manager.combat_state,
            'turn_count': getattr(self.current_combat_manager, 'turn_count', 0),
            'experience_gained': self._calculate_experience_gained() if victory else 0,
            'items_gained': self._get_dropped_items() if victory else [],
            'gold_gained': self._calculate_gold_gained() if victory else 0
        }
    
    def _calculate_experience_gained(self) -> int:
        """獲得経験値を計算"""
        # 簡単な実装 - 実際のゲームバランスに応じて調整
        if not self.current_combat_manager:
            return 0
        
        total_exp = 0
        # 敵からの経験値を計算（実装に応じて調整）
        # for enemy in self.current_combat_manager.enemies:
        #     total_exp += getattr(enemy, 'experience_value', 10)
        
        return total_exp
    
    def _get_dropped_items(self) -> list:
        """ドロップアイテムを取得"""
        # 簡単な実装 - 実際のドロップシステムに応じて調整
        return []
    
    def _calculate_gold_gained(self) -> int:
        """獲得ゴールドを計算"""
        # 簡単な実装 - 実際のゲームバランスに応じて調整
        return 0
    
    def handle_window_message(self, window_id: str, message_type: str, data: Dict[str, Any]):
        """ウィンドウメッセージを処理"""
        if window_id == "integrated_battle" and self.current_battle_window:
            if message_type == 'battle_action_selected':
                self._handle_battle_action(data)
            elif message_type == 'battle_escape_requested':
                self._handle_escape_request()
            elif message_type == 'battle_victory_achieved':
                self.end_battle(victory=True)
            elif message_type == 'battle_defeat_occurred':
                self.end_battle(victory=False)
    
    def _handle_battle_action(self, action_data: Dict[str, Any]):
        """戦闘アクションを処理"""
        if not self.current_combat_manager:
            return
        
        try:
            # CombatManagerにアクションを委譲
            action_type = action_data.get('action_type')
            actor = action_data.get('actor')
            target = action_data.get('target')
            
            logger.debug(f"戦闘アクション実行: {action_type}")
            
            # 実際のCombatManagerのメソッドに応じて実装を調整
            # result = self.current_combat_manager.perform_action(action_type, actor, target)
            
        except Exception as e:
            logger.error(f"戦闘アクション処理エラー: {e}")
    
    def _handle_escape_request(self):
        """逃走リクエストを処理"""
        if not self.current_combat_manager:
            return
        
        try:
            # 逃走成功判定（実装に応じて調整）
            escape_success = True  # 簡単な実装
            
            if escape_success:
                self.current_combat_manager.combat_state = CombatState.FLED
                self.end_battle(victory=False)
            else:
                logger.info("逃走に失敗しました")
                
        except Exception as e:
            logger.error(f"逃走処理エラー: {e}")
    
    def cleanup(self):
        """リソースクリーンアップ"""
        try:
            if self.current_battle_window:
                self.current_battle_window.cleanup()
            
            self.current_battle_window = None
            self.current_combat_manager = None
            self.battle_context = None
            
            logger.info("BattleIntegrationManagerをクリーンアップしました")
            
        except Exception as e:
            logger.error(f"クリーンアップエラー: {e}")


# シングルトンインスタンス
_battle_integration_manager = None

def get_battle_integration_manager() -> BattleIntegrationManager:
    """BattleIntegrationManagerのシングルトンインスタンスを取得"""
    global _battle_integration_manager
    if _battle_integration_manager is None:
        _battle_integration_manager = BattleIntegrationManager()
    return _battle_integration_manager