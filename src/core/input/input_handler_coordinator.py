"""Input handling coordination module."""

import pygame
from typing import Any, Dict, List, Optional, Callable, Union
from enum import Enum
from src.core.interfaces import ManagedComponent
from src.utils.logger import logger
from src.utils.constants import GameLocation


class InputType(Enum):
    """入力タイプの列挙"""
    KEYBOARD = "keyboard"
    GAMEPAD = "gamepad"
    MOUSE = "mouse"


class InputHandlerCoordinator(ManagedComponent):
    """入力処理の統合コーディネーター
    
    GameManagerから抽出された入力処理を統合管理し、
    複数の入力ハンドラーを優先順位付きで処理する。
    """
    
    def __init__(self):
        super().__init__()
        
        # 外部依存コンポーネント
        self.game_config = None
        self.current_location = GameLocation.OVERWORLD
        self.dungeon_renderer = None
        self.overworld_manager = None
        
        # 入力ハンドラー管理
        self._action_handlers: Dict[str, List[Callable]] = {}
        self._priority_handlers: List[tuple] = []  # (priority, handler) のリスト
        
        # 基本アクションマッピング
        self._action_mappings = {
            'menu': self._on_menu_action,
            'confirm': self._on_confirm_action,
            'cancel': self._on_cancel_action,
            'action': self._on_action_action,
            'debug_toggle': self._on_debug_toggle,
            '3d_stage_advance': self._on_3d_stage_advance,
            '3d_stage_reset': self._on_3d_stage_reset,
            'pause': self._on_pause_action,
            'inventory': self._on_inventory_action,
            'magic': self._on_magic_action,
            'equipment': self._on_equipment_action,
            'status': self._on_status_action,
            'camp': self._on_camp_action,
            'help': self._on_help_action,
            'movement': self._on_movement_action
        }
        
        # 状態管理コールバック
        self._toggle_pause_callback = None
        self._get_text_callback = None
    
    def _do_initialize(self, context: Dict[str, Any]) -> bool:
        """InputHandlerCoordinatorの初期化"""
        try:
            # 必要なコンポーネントを取得
            self.game_config = context.get('game_config')
            self.current_location = context.get('current_location', GameLocation.OVERWORLD)
            self.dungeon_renderer = context.get('dungeon_renderer')
            self.overworld_manager = context.get('overworld_manager')
            
            # コールバック関数を取得
            self._toggle_pause_callback = context.get('toggle_pause_callback')
            self._get_text_callback = context.get('get_text_callback')
            
            if not self.game_config:
                logger.error("InputHandlerCoordinator: game_config not provided")
                return False
            
            logger.info("InputHandlerCoordinator initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"InputHandlerCoordinator initialization failed: {e}")
            return False
    
    def _do_cleanup(self) -> None:
        """InputHandlerCoordinatorのクリーンアップ"""
        self._action_handlers.clear()
        self._priority_handlers.clear()
        logger.info("InputHandlerCoordinator cleaned up")
    
    def handle_game_event(self, event: Any) -> bool:
        """ゲームイベントの処理（現在は使用しない）"""
        return False
    
    def update_location(self, location: GameLocation) -> None:
        """現在位置の更新"""
        old_location = self.current_location
        self.current_location = location
        logger.debug(f"InputHandlerCoordinator.update_location: {old_location} -> {location}")
    
    def register_action_handler(self, action: str, handler: Callable) -> None:
        """アクション専用ハンドラーの登録"""
        if action not in self._action_handlers:
            self._action_handlers[action] = []
        if handler not in self._action_handlers[action]:
            self._action_handlers[action].append(handler)
    
    def register_priority_handler(self, priority: int, handler: Callable) -> None:
        """優先順位付きハンドラーの登録
        
        Args:
            priority: 優先順位（数値が小さいほど高優先）
            handler: イベント処理関数
        """
        handler_entry = (priority, handler)
        if handler_entry not in self._priority_handlers:
            self._priority_handlers.append(handler_entry)
            # 優先順位でソート
            self._priority_handlers.sort(key=lambda x: x[0])
    
    def handle_input_action(self, action: str, pressed: bool, input_type: str) -> bool:
        """入力アクションの処理
        
        Args:
            action: アクション名
            pressed: 押下状態
            input_type: 入力タイプ文字列
            
        Returns:
            bool: アクションが処理された場合True
        """
        try:
            # 入力タイプを列挙型に変換
            input_type_enum = InputType(input_type) if input_type else InputType.KEYBOARD
        except ValueError:
            input_type_enum = InputType.KEYBOARD
        
        # 登録されたアクションハンドラーで処理
        if action in self._action_handlers:
            for handler in self._action_handlers[action]:
                try:
                    if handler(action, pressed, input_type_enum):
                        return True
                except Exception as e:
                    logger.error(f"Action handler error for {action}: {e}")
        
        # 基本アクションマッピングで処理
        if action in self._action_mappings:
            try:
                self._action_mappings[action](action, pressed, input_type_enum)
                return True
            except Exception as e:
                logger.error(f"Action mapping error for {action}: {e}")
        
        return False
    
    def process_priority_events(self, events: List[pygame.event.Event]) -> List[pygame.event.Event]:
        """優先順位付きイベント処理
        
        Args:
            events: 処理対象のイベントリスト
            
        Returns:
            List[pygame.event.Event]: 未処理のイベントリスト
        """
        unhandled_events = []
        
        for event in events:
            handled = False
            
            # 優先順位順にハンドラーを実行
            for priority, handler in self._priority_handlers:
                try:
                    if handler(event):
                        handled = True
                        break
                except Exception as e:
                    logger.error(f"Priority handler error (priority={priority}): {e}")
            
            if not handled:
                unhandled_events.append(event)
        
        return unhandled_events
    
    # === アクションハンドラー群（GameManagerから抽出） ===
    
    def _on_menu_action(self, action: str, pressed: bool, input_type: InputType):
        """メニューアクションの処理"""
        location_str = getattr(self.current_location, 'value', str(self.current_location))
        logger.debug(f"InputHandlerCoordinator._on_menu_action: 呼び出し開始 pressed={pressed}, location={location_str}")
        
        if pressed:
            logger.info(self._get_log_message("menu_action", input_type))
            
            # ダンジョン内ではメニュー表示
            if self.current_location == GameLocation.DUNGEON and self.dungeon_renderer:
                logger.debug(f"InputHandlerCoordinator._on_menu_action: ダンジョンメニュー表示実行")
                self.dungeon_renderer._show_menu()
                logger.debug(f"InputHandlerCoordinator._on_menu_action: ダンジョンメニュー表示完了")
            # 地上部では設定画面をオーバーワールドマネージャーに委譲
            elif self.current_location == GameLocation.OVERWORLD and self.overworld_manager:
                logger.debug(f"InputHandlerCoordinator._on_menu_action: 地上部のため処理スキップ")
                # オーバーワールドマネージャーが独自にESCキーを処理するため、
                # ここでは何もしない（重複処理を避ける）
                pass
            else:
                logger.debug(f"InputHandlerCoordinator._on_menu_action: フォールバック処理 location={location_str}")
                if self._toggle_pause_callback:
                    self._toggle_pause_callback()
    
    def _on_confirm_action(self, action: str, pressed: bool, input_type: InputType):
        """確認アクションの処理"""
        if pressed:
            logger.info(self._get_log_message("confirm_action", input_type))
    
    def _on_cancel_action(self, action: str, pressed: bool, input_type: InputType):
        """キャンセルアクションの処理"""
        if pressed:
            logger.info(self._get_log_message("cancel_action", input_type))
    
    def _on_action_action(self, action: str, pressed: bool, input_type: InputType):
        """アクションボタンの処理"""
        if pressed:
            logger.info(self._get_log_message("action_button", input_type))
            
            # ダンジョン内でのセル調査
            if self.current_location == GameLocation.DUNGEON and self.dungeon_renderer:
                try:
                    # GameManagerのinteract_with_dungeon_cellメソッドを呼び出し
                    # 注意: この部分は将来的にDungeonManagerに移行する必要がある
                    if hasattr(self.dungeon_renderer, '_game_manager_ref'):
                        game_manager = self.dungeon_renderer._game_manager_ref
                        if hasattr(game_manager, 'interact_with_dungeon_cell'):
                            interaction_result = game_manager.interact_with_dungeon_cell()
                            logger.info(f"セル調査結果: {interaction_result}")
                        else:
                            logger.warning("interact_with_dungeon_cell method not found")
                    else:
                        logger.warning("GameManager reference not available in dungeon_renderer")
                except Exception as e:
                    logger.error(f"セル調査エラー: {e}")
    
    def _on_debug_toggle(self, action: str, pressed: bool, input_type: InputType):
        """デバッグ表示切り替え"""
        if pressed:
            logger.info("デバッグ表示切り替え")
            # 将来的にはDebugManagerに委譲
    
    def _on_3d_stage_advance(self, action: str, pressed: bool, input_type: InputType):
        """3Dステージ前進"""
        if pressed:
            logger.info("3Dステージ前進処理")
            if self.current_location == GameLocation.DUNGEON and self.dungeon_renderer:
                try:
                    if hasattr(self.dungeon_renderer, 'enable_3d_rendering'):
                        if not self.dungeon_renderer.enabled:
                            success = self.dungeon_renderer.enable_3d_rendering()
                            if success:
                                logger.info("3D描画を有効化しました")
                            else:
                                logger.warning("3D描画の有効化に失敗しました")
                        else:
                            logger.info("3D描画は既に有効です")
                    else:
                        logger.warning("3D描画機能が利用できません")
                except Exception as e:
                    logger.error(f"3D描画処理エラー: {e}")
    
    def _on_3d_stage_reset(self, action: str, pressed: bool, input_type: InputType):
        """3Dステージリセット"""
        if pressed:
            logger.info("3Dステージリセット処理")
            if self.current_location == GameLocation.DUNGEON and self.dungeon_renderer:
                try:
                    if hasattr(self.dungeon_renderer, 'disable_3d_rendering'):
                        if self.dungeon_renderer.enabled:
                            self.dungeon_renderer.disable_3d_rendering()
                            logger.info("3D描画を無効化しました")
                        else:
                            logger.info("3D描画は既に無効です")
                    else:
                        logger.warning("3D描画機能が利用できません")
                except Exception as e:
                    logger.error(f"3D描画リセットエラー: {e}")
    
    def _on_pause_action(self, action: str, pressed: bool, input_type: InputType):
        """ポーズアクション"""
        if pressed:
            logger.info("ポーズ処理")
            if self._toggle_pause_callback:
                self._toggle_pause_callback()
    
    def _on_inventory_action(self, action: str, pressed: bool, input_type: InputType):
        """インベントリアクション"""
        if pressed:
            logger.info("インベントリ画面表示")
            # 将来的にはInventoryManagerに委譲
    
    def _on_magic_action(self, action: str, pressed: bool, input_type: InputType):
        """魔法アクション"""
        if pressed:
            logger.info("魔法画面表示")
            # 将来的にはMagicManagerに委譲
    
    def _on_equipment_action(self, action: str, pressed: bool, input_type: InputType):
        """装備アクション"""
        if pressed:
            logger.info("装備画面表示")
            # 将来的にはEquipmentManagerに委譲
    
    def _on_status_action(self, action: str, pressed: bool, input_type: InputType):
        """ステータスアクション"""
        if pressed:
            logger.info("ステータス画面表示")
            # 将来的にはStatusManagerに委譲
    
    def _on_camp_action(self, action: str, pressed: bool, input_type: InputType):
        """キャンプアクション"""
        if pressed:
            logger.info("キャンプ画面表示")
            # 将来的にはCampManagerに委譲
    
    def _on_help_action(self, action: str, pressed: bool, input_type: InputType):
        """ヘルプアクション"""
        if pressed:
            logger.info("ヘルプ画面表示")
            
            # ダンジョン内でのヘルプ表示
            if self.current_location == GameLocation.DUNGEON and self.dungeon_renderer:
                try:
                    if hasattr(self.dungeon_renderer, 'show_help'):
                        self.dungeon_renderer.show_help()
                    else:
                        logger.info("ダンジョン内ヘルプは利用できません")
                except Exception as e:
                    logger.error(f"ヘルプ表示エラー: {e}")
    
    def _on_movement_action(self, action: str, pressed: bool, input_type: InputType):
        """移動アクション"""
        if pressed:
            logger.info(f"移動処理: {action}")
            
            # ダンジョン内での移動処理
            if self.current_location == GameLocation.DUNGEON and self.dungeon_renderer:
                try:
                    # 移動処理はDungeonManagerが処理するため、ここでは情報のみログ出力
                    logger.debug(f"ダンジョン内移動アクション: {action}")
                except Exception as e:
                    logger.error(f"移動処理エラー: {e}")
    
    def _get_log_message(self, action_key: str, input_type: InputType) -> str:
        """ログメッセージの取得"""
        if self._get_text_callback and self.game_config:
            try:
                prefix_template = self.game_config.get_text("app_log.action_log_prefix")
                action_text = self.game_config.get_text(f"app_log.{action_key}")
                return prefix_template.format(action=action_text, input_type=input_type.value)
            except Exception as e:
                logger.warning(f"Log message generation error: {e}")
        
        return f"Action: {action_key} ({input_type.value})"