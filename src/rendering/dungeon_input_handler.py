"""ダンジョン入力処理システム

DungeonRendererから入力処理ロジックを分離。
Fowlerの「Extract Class」と「Move Method」パターンを適用。
"""

from typing import Optional, Dict, Callable, Any
from enum import Enum
import pygame

from src.dungeon.dungeon_manager import DungeonManager, DungeonState, PlayerPosition
from src.rendering.direction_helper import DirectionHelper
from src.utils.logger import logger


class DungeonInputAction(Enum):
    """ダンジョン内入力アクション"""
    MOVE_FORWARD = "move_forward"
    MOVE_BACKWARD = "move_backward"
    MOVE_LEFT = "move_left"
    MOVE_RIGHT = "move_right"
    TURN_LEFT = "turn_left"
    TURN_RIGHT = "turn_right"
    STRAFE_LEFT = "strafe_left"
    STRAFE_RIGHT = "strafe_right"
    SHOW_MENU = "show_menu"
    INTERACT = "interact"
    RUN = "run"
    SNEAK = "sneak"


class MovementResult:
    """移動結果"""
    def __init__(self, success: bool, message: str = "", effects: Dict[str, Any] = None):
        self.success = success
        self.message = message
        self.effects = effects or {}


class DungeonInputHandler:
    """ダンジョン入力処理クラス
    
    DungeonRendererから入力処理の責務を分離し、
    より柔軟で拡張可能な入力システムを提供。
    """
    
    def __init__(self, dungeon_manager: Optional[DungeonManager] = None):
        self.dungeon_manager = dungeon_manager
        self.input_enabled = True
        self.movement_speed = 1.0
        self.turn_speed = 1.0
        
        # アクションハンドラーのマッピング
        self._action_handlers: Dict[DungeonInputAction, Callable] = {
            DungeonInputAction.MOVE_FORWARD: self._handle_move_forward,
            DungeonInputAction.MOVE_BACKWARD: self._handle_move_backward,
            DungeonInputAction.MOVE_LEFT: self._handle_move_left,
            DungeonInputAction.MOVE_RIGHT: self._handle_move_right,
            DungeonInputAction.TURN_LEFT: self._handle_turn_left,
            DungeonInputAction.TURN_RIGHT: self._handle_turn_right,
            DungeonInputAction.STRAFE_LEFT: self._handle_strafe_left,
            DungeonInputAction.STRAFE_RIGHT: self._handle_strafe_right,
            DungeonInputAction.SHOW_MENU: self._handle_show_menu,
            DungeonInputAction.INTERACT: self._handle_interact,
            DungeonInputAction.RUN: self._handle_run,
            DungeonInputAction.SNEAK: self._handle_sneak
        }
        
        # 移動状態フラグ
        self.is_running = False
        self.is_sneaking = False
        
        logger.info("ダンジョン入力ハンドラー初期化完了")
    
    def set_dungeon_manager(self, dungeon_manager: DungeonManager):
        """ダンジョンマネージャーを設定"""
        self.dungeon_manager = dungeon_manager
    
    def handle_action(self, action: DungeonInputAction) -> MovementResult:
        """アクションを処理"""
        if not self.input_enabled:
            return MovementResult(False, "入力が無効化されています")
        
        if not self.dungeon_manager or not self.dungeon_manager.current_dungeon:
            return MovementResult(False, "ダンジョンが設定されていません")
        
        handler = self._action_handlers.get(action)
        if not handler:
            return MovementResult(False, f"未知のアクション: {action.value}")
        
        try:
            return handler()
        except Exception as e:
            logger.error(f"アクション処理エラー ({action.value}): {e}")
            return MovementResult(False, f"アクション実行に失敗: {e}")
    
    def handle_key_input(self, key: int) -> Optional[MovementResult]:
        """キー入力を処理してアクションにマッピング"""
        action = self._map_key_to_action(key)
        if action:
            return self.handle_action(action)
        return None
    
    def handle_string_action(self, action_str: str) -> MovementResult:
        """文字列アクションを処理（後方互換性用）"""
        try:
            action = DungeonInputAction(action_str)
            return self.handle_action(action)
        except ValueError:
            return MovementResult(False, f"無効なアクション文字列: {action_str}")
    
    def _map_key_to_action(self, key: int) -> Optional[DungeonInputAction]:
        """キーをアクションにマッピング"""
        key_mapping = {
            pygame.K_w: DungeonInputAction.MOVE_FORWARD,
            pygame.K_UP: DungeonInputAction.MOVE_FORWARD,
            pygame.K_s: DungeonInputAction.MOVE_BACKWARD,
            pygame.K_DOWN: DungeonInputAction.MOVE_BACKWARD,
            pygame.K_a: DungeonInputAction.TURN_LEFT,
            pygame.K_LEFT: DungeonInputAction.TURN_LEFT,
            pygame.K_d: DungeonInputAction.TURN_RIGHT,
            pygame.K_RIGHT: DungeonInputAction.TURN_RIGHT,
            pygame.K_q: DungeonInputAction.STRAFE_LEFT,
            pygame.K_e: DungeonInputAction.STRAFE_RIGHT,
            pygame.K_p: DungeonInputAction.SHOW_MENU,
            pygame.K_SPACE: DungeonInputAction.INTERACT,
            pygame.K_LSHIFT: DungeonInputAction.RUN,
            pygame.K_LCTRL: DungeonInputAction.SNEAK
        }
        
        return key_mapping.get(key)
    
    # === 具体的なアクションハンドラー ===
    
    def _handle_move_forward(self) -> MovementResult:
        """前進処理"""
        if not self._can_move():
            return MovementResult(False, "移動できません")
        
        current_pos = self.dungeon_manager.current_dungeon.player_position
        facing_direction = current_pos.facing
        
        success = self.dungeon_manager.move_player(facing_direction)
        
        if success:
            message = "前進しました"
            if self.is_running:
                message += "（走行中）"
            elif self.is_sneaking:
                message += "（忍び足）"
            
            return MovementResult(True, message, {
                "movement_type": "forward",
                "running": self.is_running,
                "sneaking": self.is_sneaking,
                "needs_redraw": True  # 移動時は再描画が必要
            })
        else:
            return MovementResult(False, "前進できません")
    
    def _handle_move_backward(self) -> MovementResult:
        """後退処理"""
        if not self._can_move():
            return MovementResult(False, "移動できません")
        
        current_pos = self.dungeon_manager.current_dungeon.player_position
        facing_direction = current_pos.facing
        backward_direction = DirectionHelper.get_opposite_direction(facing_direction)
        
        success = self.dungeon_manager.move_player(backward_direction)
        
        if success:
            return MovementResult(True, "後退しました", {
                "movement_type": "backward",
                "running": self.is_running,
                "sneaking": self.is_sneaking,
                "needs_redraw": True  # 移動時は再描画が必要
            })
        else:
            return MovementResult(False, "後退できません")
    
    def _handle_move_left(self) -> MovementResult:
        """左移動処理"""
        if not self._can_move():
            return MovementResult(False, "移動できません")
        
        current_pos = self.dungeon_manager.current_dungeon.player_position
        facing_direction = current_pos.facing
        left_direction = DirectionHelper.get_left_direction(facing_direction)
        
        success = self.dungeon_manager.move_player(left_direction)
        
        if success:
            return MovementResult(True, "左に移動しました", {
                "movement_type": "left",
                "running": self.is_running,
                "sneaking": self.is_sneaking
            })
        else:
            return MovementResult(False, "左に移動できません")
    
    def _handle_move_right(self) -> MovementResult:
        """右移動処理"""
        if not self._can_move():
            return MovementResult(False, "移動できません")
        
        current_pos = self.dungeon_manager.current_dungeon.player_position
        facing_direction = current_pos.facing
        right_direction = DirectionHelper.get_right_direction(facing_direction)
        
        success = self.dungeon_manager.move_player(right_direction)
        
        if success:
            return MovementResult(True, "右に移動しました", {
                "movement_type": "right",
                "running": self.is_running,
                "sneaking": self.is_sneaking
            })
        else:
            return MovementResult(False, "右に移動できません")
    
    def _handle_turn_left(self) -> MovementResult:
        """左回転処理"""
        if not self._can_turn():
            return MovementResult(False, "回転できません")
        
        success = self.dungeon_manager.turn_player_left()
        
        if success:
            return MovementResult(True, "左を向きました", {
                "movement_type": "turn_left",
                "needs_redraw": True  # 回転時は再描画が必要
            })
        else:
            return MovementResult(False, "左に回転できません")
    
    def _handle_turn_right(self) -> MovementResult:
        """右回転処理"""
        if not self._can_turn():
            return MovementResult(False, "回転できません")
        
        success = self.dungeon_manager.turn_player_right()
        
        if success:
            return MovementResult(True, "右を向きました", {
                "movement_type": "turn_right",
                "needs_redraw": True  # 回転時は再描画が必要
            })
        else:
            return MovementResult(False, "右に回転できません")
    
    def _handle_strafe_left(self) -> MovementResult:
        """左ストライフ処理（向きを変えずに左移動）"""
        if not self._can_move():
            return MovementResult(False, "移動できません")
        
        current_pos = self.dungeon_manager.current_dungeon.player_position
        facing_direction = current_pos.facing
        left_direction = DirectionHelper.get_left_direction(facing_direction)
        
        success = self.dungeon_manager.move_player(left_direction)
        
        if success:
            return MovementResult(True, "左にストライフしました", {
                "movement_type": "strafe_left",
                "running": self.is_running,
                "sneaking": self.is_sneaking
            })
        else:
            return MovementResult(False, "左にストライフできません")
    
    def _handle_strafe_right(self) -> MovementResult:
        """右ストライフ処理（向きを変えずに右移動）"""
        if not self._can_move():
            return MovementResult(False, "移動できません")
        
        current_pos = self.dungeon_manager.current_dungeon.player_position
        facing_direction = current_pos.facing
        right_direction = DirectionHelper.get_right_direction(facing_direction)
        
        success = self.dungeon_manager.move_player(right_direction)
        
        if success:
            return MovementResult(True, "右にストライフしました", {
                "movement_type": "strafe_right",
                "running": self.is_running,
                "sneaking": self.is_sneaking
            })
        else:
            return MovementResult(False, "右にストライフできません")
    
    def _handle_show_menu(self) -> MovementResult:
        """メニュー表示処理"""
        logger.info("ダンジョン内メニューが要求されました")
        return MovementResult(True, "メニューを表示", {
            "action_type": "menu"
        })
    
    def _handle_interact(self) -> MovementResult:
        """インタラクション処理"""
        logger.info("インタラクションが要求されました")
        
        # 現在位置でのインタラクションをチェック
        # TODO: 実際のインタラクションシステムと連携
        
        return MovementResult(True, "周囲を調べました", {
            "action_type": "interact"
        })
    
    def _handle_run(self) -> MovementResult:
        """走行モード切り替え"""
        self.is_running = not self.is_running
        self.is_sneaking = False  # 走行時は忍び足を解除
        
        message = "走行モードON" if self.is_running else "走行モードOFF"
        return MovementResult(True, message, {
            "action_type": "toggle_run",
            "running": self.is_running
        })
    
    def _handle_sneak(self) -> MovementResult:
        """忍び足モード切り替え"""
        self.is_sneaking = not self.is_sneaking
        self.is_running = False  # 忍び足時は走行を解除
        
        message = "忍び足モードON" if self.is_sneaking else "忍び足モードOFF"
        return MovementResult(True, message, {
            "action_type": "toggle_sneak",
            "sneaking": self.is_sneaking
        })
    
    # === ヘルパーメソッド ===
    
    def _can_move(self) -> bool:
        """移動可能かチェック"""
        if not self.dungeon_manager or not self.dungeon_manager.current_dungeon:
            return False
        
        # TODO: パーティの状態、状態異常などをチェック
        # 例：麻痺状態では移動不可など
        
        return True
    
    def _can_turn(self) -> bool:
        """回転可能かチェック"""
        if not self.dungeon_manager or not self.dungeon_manager.current_dungeon:
            return False
        
        # TODO: パーティの状態をチェック
        
        return True
    
    def enable_input(self):
        """入力を有効化"""
        self.input_enabled = True
        logger.debug("ダンジョン入力が有効化されました")
    
    def disable_input(self):
        """入力を無効化"""
        self.input_enabled = False
        logger.debug("ダンジョン入力が無効化されました")
    
    def set_movement_speed(self, speed: float):
        """移動速度を設定"""
        self.movement_speed = max(0.1, min(2.0, speed))
    
    def set_turn_speed(self, speed: float):
        """回転速度を設定"""
        self.turn_speed = max(0.1, min(2.0, speed))
    
    def get_movement_state(self) -> Dict[str, Any]:
        """現在の移動状態を取得"""
        return {
            "input_enabled": self.input_enabled,
            "movement_speed": self.movement_speed,
            "turn_speed": self.turn_speed,
            "is_running": self.is_running,
            "is_sneaking": self.is_sneaking
        }
    
    def reset_movement_state(self):
        """移動状態をリセット"""
        self.is_running = False
        self.is_sneaking = False
        self.movement_speed = 1.0
        self.turn_speed = 1.0