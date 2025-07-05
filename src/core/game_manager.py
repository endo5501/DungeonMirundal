"""ゲーム管理システム"""

import pygame
import sys
from . import dbg_api
from src.core.config_manager import config_manager
from src.core.input_manager import InputManager
from src.core.save_manager import SaveManager
from src.overworld.overworld_manager import OverworldManager
from src.dungeon.dungeon_manager import DungeonManager
from src.character.party import Party
from src.rendering.dungeon_renderer_pygame import DungeonRendererPygame
from src.ui.dungeon_ui_pygame import create_pygame_dungeon_ui
from src.utils.logger import logger
from src.utils.constants import *
from src.utils.constants import GameLocation


class GameManager:
    """メインゲーム管理クラス"""
    
    def __init__(self):
        # Pygame初期化
        pygame.init()
        
        # ディスプレイ設定
        self.screen = None
        self.clock = pygame.time.Clock()
        self.running = False
        
        # ゲーム状態
        self.game_state = "startup"
        self.paused = False
        self.current_location = GameLocation.OVERWORLD  # GameLocation.OVERWORLD or GameLocation.DUNGEON
        
        # マネージャーの初期化（名前衝突を避ける）
        self.game_config = config_manager
        self.input_manager = InputManager()
        self.overworld_manager = None
        self.dungeon_manager = None
        self.dungeon_renderer = None
        
        # 現在のパーティ
        self.current_party = None
        
        # セーブマネージャー
        self.save_manager = SaveManager()
        
        # 初期設定の読み込み
        self._load_initial_config()
        
        # ウィンドウ設定
        self._setup_window()
        
        # 入力システムの設定
        self._setup_input()
        
        # 入力設定の読み込み（入力システム初期化後）
        self._load_input_settings()
        
        # フォントシステムの初期化
        self._setup_fonts()
        
        # デバッグ情報の表示
        self._setup_debug_info()
        
        # 遷移システムの初期化
        self._setup_transition_system()
        
        logger.info(self.game_config.get_text("app_log.game_manager_initialized"))
        
    def _load_initial_config(self):
        """初期設定の読み込み"""
        # ゲーム設定の読み込み
        game_config = self.game_config.load_config("game_config")
        
        # 言語設定
        language = game_config.get("gameplay", {}).get("language", "ja")
        self.game_config.set_language(language)
        
        logger.info(self.game_config.get_text("app_log.config_loaded").format(language=language))
    
    def _load_input_settings(self):
        """入力設定の読み込み"""
        try:
            input_settings = self.game_config.load_config("input_settings")
            if input_settings and hasattr(self, 'input_manager'):
                self.input_manager.load_bindings(input_settings)
                logger.info(self.game_config.get_text("app_log.input_config_loaded"))
        except Exception as e:
            logger.warning(self.game_config.get_text("app_log.input_config_failed").format(error=e))
        
    def _setup_window(self):
        """ウィンドウの設定"""
        # 設定データを取得
        game_config = self.game_config.load_config("game_config")
        window_config = game_config.get("window", {})
        
        # ウィンドウタイトル
        title = window_config.get("title", GAME_TITLE)
        pygame.display.set_caption(title)
        
        # ウィンドウサイズ
        width = window_config.get("width", WINDOW_WIDTH)
        height = window_config.get("height", WINDOW_HEIGHT)
        self.screen = pygame.display.set_mode((width, height))
        
        # FPS制限
        graphics_config = game_config.get("graphics", {})
        self.target_fps = graphics_config.get("fps", FPS)
        
        logger.info(self.game_config.get_text("app_log.window_configured").format(width=width, height=height, fps=self.target_fps))
    
    def _setup_input(self):
        """入力システムの設定"""
        from src.core.input_manager import InputAction
        
        # アクションハンドラーのバインド
        self.input_manager.bind_action(InputAction.MENU.value, self._on_menu_action)
        self.input_manager.bind_action(InputAction.CONFIRM.value, self._on_confirm_action)
        self.input_manager.bind_action(InputAction.CANCEL.value, self._on_cancel_action)
        self.input_manager.bind_action(InputAction.ACTION.value, self._on_action_action)
        self.input_manager.bind_action(InputAction.DEBUG_TOGGLE.value, self._on_debug_toggle)
        self.input_manager.bind_action(InputAction.PAUSE.value, self._on_pause_action)
        self.input_manager.bind_action(InputAction.HELP.value, self._on_help_action)
        
        # 3D描画段階テスト用デバッグキー（Numpadキーを使用）
        try:
            # Numpad +: 3D描画段階進行
            self.input_manager.bind_key_direct("equal", self._on_3d_stage_advance)  # +キー
            # Numpad -: 3D描画緊急リセット  
            self.input_manager.bind_key_direct("minus", self._on_3d_stage_reset)   # -キー
            logger.info(self.game_config.get_text("app_log.debug_key_setup"))
        except Exception as e:
            logger.warning(self.game_config.get_text("app_log.debug_key_setup_failed").format(error=e))
        
        # ゲーム機能のバインド
        self.input_manager.bind_action(InputAction.INVENTORY.value, self._on_inventory_action)
        self.input_manager.bind_action(InputAction.MAGIC.value, self._on_magic_action)
        self.input_manager.bind_action(InputAction.EQUIPMENT.value, self._on_equipment_action)
        self.input_manager.bind_action(InputAction.STATUS.value, self._on_status_action)
        self.input_manager.bind_action(InputAction.CAMP.value, self._on_camp_action)
        
        # 移動アクションのバインド（ダンジョンレンダラーが処理）
        self.input_manager.bind_action(InputAction.MOVE_FORWARD.value, self._on_movement_action)
        self.input_manager.bind_action(InputAction.MOVE_BACKWARD.value, self._on_movement_action)
        self.input_manager.bind_action(InputAction.MOVE_LEFT.value, self._on_movement_action)
        self.input_manager.bind_action(InputAction.MOVE_RIGHT.value, self._on_movement_action)
        self.input_manager.bind_action(InputAction.TURN_LEFT.value, self._on_movement_action)
        self.input_manager.bind_action(InputAction.TURN_RIGHT.value, self._on_movement_action)
        
        # コントローラーのセットアップ
        self.input_manager.setup_controllers()
        
        logger.info(self.game_config.get_text("app_log.extended_input_configured"))
    
    def _setup_fonts(self):
        """フォントシステムの初期化"""
        try:
            from src.ui.font_manager_pygame import font_manager
            if font_manager.default_font:
                logger.info(self.game_config.get_text("app_log.font_system_initialized"))
            else:
                logger.warning(self.game_config.get_text("app_log.font_system_failed"))
        except Exception as e:
            logger.error(self.game_config.get_text("app_log.font_system_error").format(error=e))
    
    def _setup_debug_info(self):
        """デバッグ情報の設定"""
        game_config = self.game_config.load_config("game_config")
        debug_config = game_config.get("debug", {})
        self.debug_enabled = debug_config.get("enabled", False)
        self.show_fps = debug_config.get("show_fps", False)
        
        # Pygameでのデバッグ情報表示用フォント
        if self.debug_enabled:
            try:
                self.debug_font = pygame.font.Font(None, 24)
            except:
                self.debug_font = None
                
        status = self.game_config.get_text("ui.settings.enabled") if self.debug_enabled else self.game_config.get_text("ui.settings.disabled")

        # デバッグサーバ起動
        dbg_api.start(self.screen)

        logger.info(self.game_config.get_text("app_log.debug_setting").format(status=status))
    
    def _on_menu_action(self, action: str, pressed: bool, input_type):
        """メニューアクションの処理"""
        if pressed:
            logger.info(self.game_config.get_text("app_log.action_log_prefix").format(action=self.game_config.get_text("app_log.menu_action"), input_type=input_type.value))
            
            # ダンジョン内ではメニュー表示
            if self.current_location == GameLocation.DUNGEON and self.dungeon_renderer:
                self.dungeon_renderer._show_menu()
            # 地上部では設定画面をオーバーワールドマネージャーに委譲
            elif self.current_location == GameLocation.OVERWORLD and self.overworld_manager:
                # オーバーワールドマネージャーが独自にESCキーを処理するため、
                # ここでは何もしない（重複処理を避ける）
                pass
            else:
                self.toggle_pause()
    
    def _on_confirm_action(self, action: str, pressed: bool, input_type):
        """確認アクションの処理"""
        if pressed:
            logger.info(self.game_config.get_text("app_log.action_log_prefix").format(action=self.game_config.get_text("app_log.confirm_action"), input_type=input_type.value))
    
    def _on_cancel_action(self, action: str, pressed: bool, input_type):
        """キャンセルアクションの処理"""
        if pressed:
            logger.info(self.game_config.get_text("app_log.action_log_prefix").format(action=self.game_config.get_text("app_log.cancel_action"), input_type=input_type.value))
    
    def _on_action_action(self, action: str, pressed: bool, input_type):
        """アクションボタンの処理"""
        if pressed:
            logger.info(self.game_config.get_text("app_log.action_log_prefix").format(action=self.game_config.get_text("app_log.action_button"), input_type=input_type.value))
            
            # ダンジョン内でのスペースキー: 3D描画復旧を試行
            if self.current_location == GameLocation.DUNGEON and self.dungeon_renderer:
                logger.info(self.game_config.get_text("app_log.3d_manual_recovery_attempt"))
                
                try:
                    if hasattr(self.dungeon_renderer, 'manual_recovery_attempt'):
                        recovery_success = self.dungeon_renderer.manual_recovery_attempt()
                        
                        if recovery_success:
                            logger.info(self.game_config.get_text("app_log.3d_manual_recovery_success"))
                            # UI更新
                            try:
                                self.dungeon_renderer.update_ui()
                            except Exception as ui_error:
                                logger.warning(self.game_config.get_text("app_log.ui_update_error").format(error=ui_error))
                        else:
                            logger.warning(self.game_config.get_text("app_log.3d_manual_recovery_failed"))
                    else:
                        # フォールバック: 旧システムとの互換性
                        logger.info(self.game_config.get_text("app_log.legacy_compatibility_mode"))
                        if hasattr(self.dungeon_renderer, 'ui_manager') and self.dungeon_renderer.ui_manager:
                            self.dungeon_renderer.ui_manager._open_inventory()
                            
                except Exception as e:
                    logger.error(self.game_config.get_text("app_log.3d_recovery_error").format(error=e))
            
            # 地上部では既存の処理
            elif self.current_location == GameLocation.OVERWORLD:
                logger.info(self.game_config.get_text("app_log.overworld_action_button"))
    
    def _on_debug_toggle(self, action: str, pressed: bool, input_type):
        """デバッグ切り替えの処理"""
        if pressed:
            self.debug_enabled = not self.debug_enabled
            status = self.game_config.get_text("app_log.debug_enabled") if self.debug_enabled else self.game_config.get_text("app_log.debug_disabled")
            logger.info(self.game_config.get_text("app_log.debug_mode_toggle_status").format(status=status))
    
    def _on_3d_stage_advance(self, action: str, pressed: bool, input_type):
        """3D描画段階進行デバッグ"""
        if pressed and self.current_location == GameLocation.DUNGEON and self.dungeon_renderer:
            logger.info(self.game_config.get_text("app_log.3d_stage_advance_debug"))
            
            # 現在の状態を表示
            self.dungeon_renderer.log_current_status()
            
            # 次の段階に進行
            success = self.dungeon_renderer.manual_advance_next_stage()
            
            if success:
                logger.info(self.game_config.get_text("app_log.3d_stage_advance_success"))
                # 進行後の状態も表示
                self.dungeon_renderer.log_current_status()
                
                # UIを更新
                try:
                    self.dungeon_renderer.update_ui()
                except Exception as e:
                    logger.warning(self.game_config.get_text("app_log.ui_update_error").format(error=e))
            else:
                logger.info(self.game_config.get_text("app_log.3d_stage_advance_failed"))
    
    def _on_3d_stage_reset(self, action: str, pressed: bool, input_type):
        """3D描画緊急リセットデバッグ"""
        if pressed and self.current_location == GameLocation.DUNGEON and self.dungeon_renderer:
            logger.info(self.game_config.get_text("app_log.3d_emergency_reset_debug"))
            
            # 緊急無効化を実行
            self.dungeon_renderer.emergency_disable()
            logger.info(self.game_config.get_text("app_log.3d_emergency_reset_complete"))
    
    def _on_pause_action(self, action: str, pressed: bool, input_type):
        """ポーズアクションの処理"""
        if pressed:
            logger.info(self.game_config.get_text("app_log.action_log_prefix").format(action=self.game_config.get_text("app_log.pause_action"), input_type=input_type.value))
            self.toggle_pause()
    
    def _on_inventory_action(self, action: str, pressed: bool, input_type):
        """インベントリアクションの処理"""
        if pressed:
            logger.info(self.game_config.get_text("app_log.action_log_prefix").format(action=self.game_config.get_text("app_log.inventory_action"), input_type=input_type.value))
            if self.current_location == GameLocation.DUNGEON and self.dungeon_renderer:
                if hasattr(self.dungeon_renderer, 'ui_manager') and self.dungeon_renderer.ui_manager:
                    self.dungeon_renderer.ui_manager._open_inventory()
    
    def _on_magic_action(self, action: str, pressed: bool, input_type):
        """魔法アクションの処理"""
        if pressed:
            logger.info(self.game_config.get_text("app_log.action_log_prefix").format(action=self.game_config.get_text("app_log.magic_action"), input_type=input_type.value))
            if self.current_location == GameLocation.DUNGEON and self.dungeon_renderer:
                if hasattr(self.dungeon_renderer, 'ui_manager') and self.dungeon_renderer.ui_manager:
                    self.dungeon_renderer.ui_manager._open_magic()
    
    def _on_equipment_action(self, action: str, pressed: bool, input_type):
        """装備アクションの処理"""
        if pressed:
            logger.info(self.game_config.get_text("app_log.action_log_prefix").format(action=self.game_config.get_text("app_log.equipment_action"), input_type=input_type.value))
            if self.current_location == GameLocation.DUNGEON and self.dungeon_renderer:
                if hasattr(self.dungeon_renderer, 'ui_manager') and self.dungeon_renderer.ui_manager:
                    self.dungeon_renderer.ui_manager._open_equipment()
    
    def _on_status_action(self, action: str, pressed: bool, input_type):
        """ステータスアクションの処理"""
        if pressed:
            logger.info(self.game_config.get_text("app_log.action_log_prefix").format(action=self.game_config.get_text("app_log.status_action"), input_type=input_type.value))
            if self.current_location == GameLocation.DUNGEON and self.dungeon_renderer:
                if hasattr(self.dungeon_renderer, 'ui_manager') and self.dungeon_renderer.ui_manager:
                    self.dungeon_renderer.ui_manager._open_status()
    
    def _on_camp_action(self, action: str, pressed: bool, input_type):
        """キャンプアクションの処理"""
        if pressed:
            logger.info(self.game_config.get_text("app_log.action_log_prefix").format(action=self.game_config.get_text("app_log.camp_action"), input_type=input_type.value))
            if self.current_location == GameLocation.DUNGEON and self.dungeon_renderer:
                if hasattr(self.dungeon_renderer, 'ui_manager') and self.dungeon_renderer.ui_manager:
                    self.dungeon_renderer.ui_manager._open_camp()
    
    def _on_help_action(self, action: str, pressed: bool, input_type):
        """ヘルプアクションの処理"""
        if pressed:
            logger.info(self.game_config.get_text("app_log.action_log_prefix").format(action=self.game_config.get_text("app_log.help_action"), input_type=input_type.value))
            # 新WindowSystemのHelpWindowを使用
            from src.ui.window_system.window_manager import WindowManager
            from src.ui.window_system.help_window import HelpWindow
            import pygame
            
            window_manager = WindowManager.get_instance()
            # Pygameが初期化されていない場合は初期化
            if not window_manager.screen and self.screen:
                window_manager.initialize_pygame(self.screen, self.clock)
            
            help_window = window_manager.create_window(
                HelpWindow,
                window_manager=window_manager,
                rect=pygame.Rect(100, 100, 600, 500),
                window_id="main_help_window"
            )
            help_window.show_main_help_menu()
    
    def _on_movement_action(self, action: str, pressed: bool, input_type):
        """移動アクションの処理"""
        if pressed and self.current_location == GameLocation.DUNGEON and self.dungeon_renderer:
            # ダンジョンレンダラーに移動処理を委譲
            from src.core.input_manager import InputAction
            
            if action == InputAction.MOVE_FORWARD.value:
                self.dungeon_renderer._move_forward()
            elif action == InputAction.MOVE_BACKWARD.value:
                self.dungeon_renderer._move_backward()
            elif action == InputAction.MOVE_LEFT.value:
                self.dungeon_renderer._move_left()
            elif action == InputAction.MOVE_RIGHT.value:
                self.dungeon_renderer._move_right()
            elif action == InputAction.TURN_LEFT.value:
                self.dungeon_renderer._turn_left()
            elif action == InputAction.TURN_RIGHT.value:
                self.dungeon_renderer._turn_right()
    
    def toggle_pause(self):
        """ポーズの切り替え"""
        self.paused = not self.paused
        if self.paused:
            logger.info(self.game_config.get_text("app_log.game_paused"))
        else:
            logger.info(self.game_config.get_text("app_log.game_resumed"))
    
    def _setup_transition_system(self):
        """遷移システムの初期化"""
        # UIマネージャーの初期化
        from src.ui.base_ui_pygame import initialize_ui_manager
        self.ui_manager = initialize_ui_manager(self.screen)
        
        # WindowManagerの初期化（screenとclockを渡す）
        from src.ui.window_system.window_manager import WindowManager
        window_manager = WindowManager.get_instance()
        window_manager.initialize_pygame(self.screen, self.clock)
        logger.info("WindowManagerをPygameで初期化しました")
        
        # 地上部マネージャーの初期化
        try:
            self.overworld_manager = OverworldManager()
            self.overworld_manager.set_ui_manager(self.ui_manager)
            self.overworld_manager.set_enter_dungeon_callback(self.transition_to_dungeon)
            self.overworld_manager.set_exit_game_callback(self.exit_game)
            self.overworld_manager.set_input_manager(self.input_manager)
            logger.info(self.game_config.get_text("app_log.overworld_manager_initialized"))
        except Exception as e:
            logger.error(self.game_config.get_text("app_log.overworld_manager_error").format(error=e))
            # エラーの場合は None に設定
            self.overworld_manager = None
        
        # ダンジョンマネージャーの初期化
        self.dungeon_manager = DungeonManager()
        self.dungeon_manager.set_return_to_overworld_callback(self.transition_to_overworld)
        
        # ダンジョンレンダラーの初期化
        try:
            self.dungeon_renderer = DungeonRendererPygame(screen=self.screen)
            # ダンジョンマネージャーを設定
            self.dungeon_renderer.set_dungeon_manager(self.dungeon_manager)
            
            # ダンジョンUIマネージャーの初期化と設定
            dungeon_ui_manager = create_pygame_dungeon_ui(self.screen)
            self.dungeon_renderer.set_dungeon_ui_manager(dungeon_ui_manager)
            
            # 現在のパーティが存在する場合は設定
            if self.current_party:
                dungeon_ui_manager.set_party(self.current_party)
            
            if self.dungeon_renderer.enabled:
                logger.info(self.game_config.get_text("app_log.dungeon_renderer_initialized"))
            else:
                logger.info(self.game_config.get_text("app_log.dungeon_renderer_disabled"))
        except Exception as e:
            logger.error(self.game_config.get_text("app_log.dungeon_renderer_error").format(error=e))
            self.dungeon_renderer = None
        
        logger.info(self.game_config.get_text("app_log.transition_system_initialized"))
    
    def set_game_state(self, state: str):
        """ゲーム状態の設定"""
        old_state = self.game_state
        self.game_state = state
        logger.info(self.game_config.get_text("app_log.game_state_changed").format(old_state=old_state, new_state=state))
    
    def set_current_party(self, party: Party):
        """現在のパーティを設定"""
        self.current_party = party
        
        # ダンジョンレンダラーにもパーティを設定（無効化されていても設定）
        if self.dungeon_renderer:
            self.dungeon_renderer.set_party(party)
            
            # ダンジョンUIマネージャーにもパーティを設定
            if hasattr(self.dungeon_renderer, 'dungeon_ui_manager') and self.dungeon_renderer.dungeon_ui_manager:
                self.dungeon_renderer.dungeon_ui_manager.set_party(party)
        
        logger.info(self.game_config.get_text("app_log.party_set").format(name=party.name, count=len(party.get_living_characters())))
    
    def get_current_party(self) -> Party:
        """現在のパーティを取得"""
        return self.current_party
    
    def transition_to_dungeon(self, dungeon_id: str = "main_dungeon"):
        """ダンジョンへの遷移"""
        if not self.current_party:
            logger.error(self.game_config.get_text("game_manager.party_error_no_party"))
            raise Exception(self.game_config.get_text("game_manager.party_error_no_party"))
        
        if not self.current_party.get_living_characters():
            logger.error(self.game_config.get_text("game_manager.party_error_no_living"))
            raise Exception(self.game_config.get_text("game_manager.party_error_no_living"))
        
        logger.info(self.game_config.get_text("game_manager.dungeon_transition_start").format(dungeon_id=dungeon_id))
        
        try:
            # ダンジョンが存在しない場合は作成
            if dungeon_id not in self.dungeon_manager.active_dungeons:
                # ダンジョン設定に基づいてシードを生成
                dungeon_seed = self._generate_dungeon_seed(dungeon_id)
                self.dungeon_manager.create_dungeon(dungeon_id, dungeon_seed)
            
            # ダンジョンに入場（地上部は保持したまま試行）
            success = self.dungeon_manager.enter_dungeon(dungeon_id, self.current_party)
            
            if success:
                # 成功した場合のみ地上部を退場
                self.overworld_manager.exit_overworld()
                
                self.current_location = GameLocation.DUNGEON
                self.set_game_state("dungeon_exploration")
                
                # ダンジョンUIマネージャーにダンジョン状態を設定（小地図の初期化）
                if self.dungeon_renderer and hasattr(self.dungeon_renderer, 'dungeon_ui_manager'):
                    if self.dungeon_renderer.dungeon_ui_manager:
                        current_dungeon = self.dungeon_manager.current_dungeon
                        if current_dungeon:
                            logger.info(self.game_config.get_text("game_manager.dungeon_ui_set"))
                            self.dungeon_renderer.dungeon_ui_manager.set_dungeon_state(current_dungeon)
                
                # ダンジョンレンダラーで自動復旧試行
                if self.dungeon_renderer:
                    current_dungeon = self.dungeon_manager.current_dungeon
                    if current_dungeon:
                        try:
                            logger.info(self.game_config.get_text("game_manager.3d_auto_recovery_attempt"))
                            
                            # 自動復旧を試行
                            if hasattr(self.dungeon_renderer, 'auto_recover'):
                                recovery_success = self.dungeon_renderer.auto_recover()
                            else:
                                # フォールバック: 旧システムとの互換性
                                recovery_success = self.dungeon_renderer.enabled
                            
                            if recovery_success:
                                logger.info(self.game_config.get_text("game_manager.3d_auto_recovery_success"))
                                # UI更新も安全に実行
                                try:
                                    self.dungeon_renderer.update_ui()
                                except Exception as ui_error:
                                    logger.warning(self.game_config.get_text("app_log.ui_update_error").format(error=ui_error))
                            else:
                                logger.warning(self.game_config.get_text("game_manager.3d_auto_recovery_failed"))
                                logger.info(self.game_config.get_text("game_manager.3d_manual_recovery_hint"))
                                
                        except Exception as render_error:
                            logger.error(self.game_config.get_text("game_manager.3d_render_error").format(error=render_error))
                            logger.info(self.game_config.get_text("game_manager.3d_render_manual_required"))
                            # エラーが発生してもゲーム継続
                
                logger.info(self.game_config.get_text("game_manager.dungeon_transition_complete"))
                return True
            else:
                logger.error(self.game_config.get_text("game_manager.dungeon_transition_failed"))
                raise Exception(self.game_config.get_text("game_manager.dungeon_manager_enter_failed"))
                
        except Exception as e:
            logger.error(self.game_config.get_text("game_manager.dungeon_transition_error").format(error=e))
            # 地上部の状態は保持されているため、エラーを再発生させて上位に処理を委ねる
            raise e
    
    def transition_to_overworld(self):
        """地上部への遷移"""
        if not self.current_party:
            logger.error(self.game_config.get_text("game_manager.party_error_no_party"))
            return False
        
        logger.info(self.game_config.get_text("game_manager.overworld_transition_start"))
        
        # ダンジョンを退場（ダンジョンにいる場合のみ）
        if self.current_location == GameLocation.DUNGEON:
            self.dungeon_manager.exit_dungeon()
        
        # 地上部に入場（自動回復付き）
        from_dungeon = (self.current_location == GameLocation.DUNGEON)
        success = self.overworld_manager.enter_overworld(self.current_party, from_dungeon)
        
        if success:
            self.current_location = GameLocation.OVERWORLD
            self.set_game_state("overworld_exploration")
            logger.info(self.game_config.get_text("game_manager.overworld_transition_complete"))
            return True
        else:
            logger.error(self.game_config.get_text("game_manager.overworld_transition_failed"))
            return False
    
    def _generate_dungeon_seed(self, dungeon_id: str) -> str:
        """ダンジョンIDに基づいてシードを生成"""
        # ダンジョン設定を読み込み
        try:
            import yaml
            with open("config/dungeons.yaml", 'r', encoding='utf-8') as f:
                dungeons_config = yaml.safe_load(f)
            
            dungeon_info = dungeons_config.get("dungeons", {}).get(dungeon_id, {})
            seed_base = dungeon_info.get("seed_base", dungeon_id)
            
            # 基本シードをベースに一意なシードを生成
            return f"{seed_base}_seed"
        except Exception as e:
            logger.warning(self.game_config.get_text("game_manager.dungeon_config_load_failed").format(error=e))
            return f"{dungeon_id}_default_seed"
    
    def save_game_state(self, slot_id: str) -> bool:
        """ゲーム状態の保存"""
        try:
            # 現在の場所に応じてセーブ
            if self.current_location == GameLocation.OVERWORLD:
                success = self.overworld_manager.save_overworld_state(slot_id)
            elif self.current_location == GameLocation.DUNGEON:
                success = self.dungeon_manager.save_dungeon(slot_id)
            else:
                logger.error(self.game_config.get_text("game_manager.unknown_location").format(location=self.current_location))
                return False
            
            if success:
                # 統合状態情報も保存
                state_data = {
                    'current_location': self.current_location,
                    'game_state': self.game_state,
                    'party_id': self.current_party.party_id if self.current_party else None
                }
                
                from src.core.save_manager import save_manager
                save_manager.save_additional_data(slot_id, 'game_state', state_data)
                
                logger.info(self.game_config.get_text("game_manager.game_state_save_success").format(location=self.current_location))
                return True
            else:
                return False
                
        except Exception as e:
            logger.error(self.game_config.get_text("game_manager.game_state_save_error").format(error=e))
            return False
    
    def load_game_state(self, slot_id: str) -> bool:
        """ゲーム状態の読み込み"""
        try:
            from src.core.save_manager import save_manager
            
            # 統合状態情報を読み込み
            state_data = save_manager.load_additional_data(slot_id, 'game_state')
            if not state_data:
                logger.error(self.game_config.get_text("game_manager.game_state_data_not_found"))
                return False
            
            location = state_data.get('current_location', GameLocation.OVERWORLD)
            game_state = state_data.get('game_state', 'overworld_exploration')
            party_id = state_data.get('party_id')
            
            # パーティを読み込み
            if party_id:
                party_data = save_manager.load_additional_data(slot_id, 'party')
                if party_data:
                    from src.character.party import Party
                    party = Party.from_dict(party_data)
                    self.set_current_party(party)
            
            # 場所に応じて読み込み
            if location == GameLocation.OVERWORLD:
                success = self.overworld_manager.load_overworld_state(slot_id)
                if success and self.current_party:
                    self.overworld_manager.enter_overworld(self.current_party)
            elif location == GameLocation.DUNGEON:
                success = self.dungeon_manager.load_dungeon(slot_id)
                if success and self.current_party:
                    # ダンジョン状態を復元
                    pass
            else:
                logger.error(self.game_config.get_text("game_manager.unknown_location").format(location=location))
                return False
            
            if success:
                self.current_location = location
                self.set_game_state(game_state)
                logger.info(self.game_config.get_text("game_manager.game_state_load_success").format(location=location))
                return True
            else:
                return False
                
        except Exception as e:
            logger.error(self.game_config.get_text("game_manager.game_state_load_error").format(error=e))
            return False
    
    def get_text(self, key: str) -> str:
        """テキストの取得"""
        return self.game_config.get_text(key)
    
    def save_input_settings(self):
        """入力設定を保存"""
        try:
            if hasattr(self, 'input_manager'):
                bindings_data = self.input_manager.save_bindings()
                # save_configが未実装のため、一時的にコメントアウト
                # self.game_config.save_config("input_settings", bindings_data)
                logger.info(self.game_config.get_text("game_manager.input_settings_saved"))
                return True
        except Exception as e:
            logger.error(self.game_config.get_text("game_manager.input_settings_save_error").format(error=e))
        return False
    
    def get_input_manager(self):
        """入力マネージャーを取得"""
        return self.input_manager if hasattr(self, 'input_manager') else None
    
    def exit_game(self):
        """ゲーム終了処理"""
        logger.info(self.game_config.get_text("game_manager.exit_game_start"))
        
        # リソースのクリーンアップ
        self.cleanup()
        
        # Panda3Dアプリケーションを終了
        import sys
        sys.exit(0)
    
    def cleanup(self):
        """リソースのクリーンアップ"""
        logger.info(self.game_config.get_text("game_manager.cleanup_start"))
        
        # 入力設定を自動保存
        self.save_input_settings()
        
        if hasattr(self, 'input_manager'):
            self.input_manager.cleanup()
            
        pygame.quit()
        
    def run_game(self):
        """ゲームの実行"""
        logger.info(self.game_config.get_text("game_manager.game_start"))
        
        # 初回起動処理
        self._initialize_game_flow()
        
        # メインループの開始
        self.running = True
        self._main_loop()
    
    def _main_loop(self):
        """Pygameメインループ"""
        while self.running:
            # イベント処理
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                else:
                    # WindowManagerでイベント処理（最優先）
                    ui_handled = False
                    from src.ui.window_system import WindowManager
                    window_manager = WindowManager.get_instance()
                    
                    # WindowManagerが初期化されていない場合は初期化
                    if not window_manager.screen:
                        window_manager.initialize_pygame(self.screen, self.clock)
                    
                    # アクティブなウィンドウがある場合はWindowManagerで処理し、他のUIシステムをスキップ
                    if window_manager.get_active_window():
                        window_manager.handle_global_events([event])
                        ui_handled = True
                    else:
                        # UIマネージャーでイベント処理
                        if hasattr(self, 'ui_manager') and self.ui_manager:
                            ui_handled = self.ui_manager.handle_event(event)
                        
                        # オーバーワールドマネージャーでイベント処理
                        if not ui_handled and self.current_location == GameLocation.OVERWORLD and self.overworld_manager:
                            ui_handled = self.overworld_manager.handle_event(event)
                        
                        # ダンジョンUIマネージャーでイベント処理
                        if not ui_handled and self.current_location == GameLocation.DUNGEON and self.dungeon_renderer:
                            if hasattr(self.dungeon_renderer, 'dungeon_ui_manager') and self.dungeon_renderer.dungeon_ui_manager:
                                ui_handled = self.dungeon_renderer.dungeon_ui_manager.handle_input(event)
                    
                    # UIで処理されなかった場合のみ入力マネージャーに送信
                    if not ui_handled and hasattr(self, 'input_manager'):
                        self.input_manager.handle_event(event)
            
            # 入力マネージャーの更新
            if hasattr(self, 'input_manager'):
                self.input_manager.update()
            
            # FPS制限とUIマネージャーの更新（pygame-gui）
            time_delta = self.clock.tick(self.target_fps) / 1000.0
            
            # WindowManagerの更新
            from src.ui.window_system import WindowManager
            window_manager = WindowManager.get_instance()
            window_manager.update(time_delta)
            
            # WindowManagerがアクティブでない場合のみ既存のUIManagerを更新
            if not window_manager.get_active_window():
                if hasattr(self, 'ui_manager') and self.ui_manager:
                    self.ui_manager.update(time_delta)
            
            # 画面をクリア
            self.screen.fill((0, 0, 0))
            
            # 現在の状態に応じて描画
            self._render_current_state()
            
            # WindowManagerの描画
            from src.ui.window_system import WindowManager
            window_manager = WindowManager.get_instance()
            window_manager.draw(self.screen)
            
            # WindowManagerがアクティブでない場合のみ既存のUIManagerを描画
            if not window_manager.get_active_window():
                if hasattr(self, 'ui_manager') and self.ui_manager:
                    self.ui_manager.render()
            else:
                # WindowManagerがアクティブでも永続要素（CharacterStatusBar）は常に描画
                if hasattr(self, 'ui_manager') and self.ui_manager:
                    self._render_persistent_elements()
            
            # デバッグ情報の描画
            if self.debug_enabled:
                self._render_debug_info()
            
            # 画面更新
            pygame.display.flip()
    
    def _render_persistent_elements(self):
        """
        UIManagerの永続要素（CharacterStatusBarなど）を描画
        
        WindowManagerがアクティブな場合でも、永続要素は常に表示する必要があるため、
        このメソッドで個別に描画を行う。
        """
        try:
            if hasattr(self.ui_manager, 'persistent_elements'):
                for element in self.ui_manager.persistent_elements.values():
                    if element and hasattr(element, 'render'):
                        try:
                            # フォントを取得
                            font = None
                            if hasattr(self.ui_manager, 'default_font'):
                                font = self.ui_manager.default_font
                            
                            element.render(self.screen, font)
                            
                        except Exception as e:
                            logger.warning(f"永続要素の描画でエラーが発生: {type(element).__name__}: {e}")
            
        except Exception as e:
            logger.error(f"永続要素描画処理でエラーが発生: {e}")
    
    def _render_current_state(self):
        """現在の状態に応じた描画"""
        if self.current_location == GameLocation.OVERWORLD and self.overworld_manager:
            # 地上部の描画
            self.overworld_manager.render(self.screen)
        elif self.current_location == GameLocation.DUNGEON and self.dungeon_renderer and self.dungeon_manager:
            # ダンジョンの描画
            current_dungeon = self.dungeon_manager.current_dungeon
            if current_dungeon and current_dungeon.player_position:
                # 現在のレベルを取得
                current_level = current_dungeon.levels.get(current_dungeon.player_position.level)
                if current_level:
                    self.dungeon_renderer.render_dungeon_view(
                        current_dungeon.player_position,
                        current_level
                    )
                    
                    # ダンジョンUIマネージャーの追加描画（小地図等）
                    if hasattr(self.dungeon_renderer, 'dungeon_ui_manager') and self.dungeon_renderer.dungeon_ui_manager:
                        try:
                            # ダンジョン状態を最新に更新
                            self.dungeon_renderer.dungeon_ui_manager.set_dungeon_state(current_dungeon)
                            # オーバーレイを描画
                            self.dungeon_renderer.dungeon_ui_manager.render_overlay()
                        except Exception as e:
                            logger.warning(self.game_config.get_text("game_manager.dungeon_ui_render_error").format(error=e))
        else:
            # スタートアップ画面
            self._render_startup_screen()
    
    def _render_startup_screen(self):
        """スタートアップ画面の描画"""
        if hasattr(self, 'debug_font') and self.debug_font:
            text = self.debug_font.render(self.get_text("system.startup"), True, (255, 255, 255))
            text_rect = text.get_rect(center=(self.screen.get_width()//2, self.screen.get_height()//2))
            self.screen.blit(text, text_rect)
    
    def _render_debug_info(self):
        """デバッグ情報の描画"""
        if self.debug_font and self.show_fps:
            fps_text = f"FPS: {int(self.clock.get_fps())}"
            fps_surface = self.debug_font.render(fps_text, True, (255, 255, 0))
            self.screen.blit(fps_surface, (10, 10))
    
    def _initialize_game_flow(self):
        """ゲーム開始時の初期化フロー"""
        # 自動セーブデータロードを試行
        auto_load_success = self._try_auto_load()
        
        # 自動ロードに失敗した場合はテスト用パーティを作成
        if not auto_load_success and not self.current_party:
            self._create_test_party()
        
        # 地上部に遷移
        self.transition_to_overworld()
        
        self.set_game_state("startup")
    
    def _try_auto_load(self):
        """自動セーブデータロードを試行"""
        try:
            # 利用可能なセーブスロットを取得（最新順にソート済み）
            save_slots = self.save_manager.get_save_slots()
            
            if not save_slots:
                logger.info(config_manager.get_text("game_manager.no_save_data"))
                return False
            
            # 最新のセーブデータを取得（リストの最初の要素）
            latest_save = save_slots[0]
            slot_id = latest_save.slot_id
            
            logger.info(f"{config_manager.get_text('game_manager.auto_load')}: スロット{slot_id} ({latest_save.party_name})")
            
            # セーブデータをロード
            save_data = self.save_manager.load_game(slot_id)
            
            if save_data:
                # パーティ情報を復元
                self.set_current_party(save_data.party)
                logger.info(self.game_config.get_text("game_manager.party_restored").format(name=self.current_party.name))
                
                # ゲーム状態を復元
                if save_data.game_state and 'location' in save_data.game_state:
                    self.current_location = save_data.game_state['location']
                    logger.info(self.game_config.get_text("game_manager.location_restored").format(location=self.current_location))
            
            logger.info(self.game_config.get_text("game_manager.auto_load_success"))
            return True
            
        except Exception as e:
            logger.error(self.game_config.get_text("game_manager.auto_load_failed").format(error=e))
            logger.info(self.game_config.get_text("game_manager.new_game_start"))
            return False
    
    def _create_test_character(self, name: str, is_fallback: bool = False):
        """テスト用キャラクター作成"""
        from src.character.character import Character, CharacterStatus
        from src.character.stats import BaseStats
        
        character = Character(
            name=name,
            race="human",
            character_class="fighter"
        )
        
        # 基本ステータスを設定
        if is_fallback:
            character.base_stats = BaseStats(
                strength=15, intelligence=10, faith=10,
                vitality=14, agility=12, luck=8
            )
        else:
            character.base_stats = BaseStats(
                strength=16, intelligence=10, faith=10,
                vitality=15, agility=12, luck=8
            )
        
        character.status = CharacterStatus.GOOD
        character.experience.level = 1
        character.initialize_derived_stats()
        character.derived_stats.current_hp = character.derived_stats.max_hp
        character.derived_stats.current_mp = character.derived_stats.max_mp
        
        return character
    
    def _create_test_party(self):
        """テスト用パーティの作成"""
        try:
            from src.character.party import Party
            
            # テスト用キャラクターを作成
            character_name = config_manager.get_text("game_manager.test_character")
            test_character = self._create_test_character(character_name)
            
            # テスト用パーティを作成
            party_name = config_manager.get_text("game_manager.test_party")
            test_party = Party(party_name)
            test_party.add_character(test_character)
            test_party.gold = 1000
            
            self.set_current_party(test_party)
            logger.info(self.game_config.get_text("game_manager.test_party_created"))
            
        except Exception as e:
            logger.error(self.game_config.get_text("game_manager.test_party_error").format(error=e))
            self._create_fallback_party()
    
    def _create_fallback_party(self):
        """緊急用パーティの作成"""
        from src.character.party import Party
        
        fallback_character = self._create_test_character(self.game_config.get_text("game_manager.test_character_fallback"), is_fallback=True)
        fallback_party = Party(self.game_config.get_text("game_manager.fallback_party_name"))
        fallback_party.add_character(fallback_character)
        fallback_party.gold = 1000
        
        self.set_current_party(fallback_party)
        logger.info(self.game_config.get_text("game_manager.fallback_party_created"))


def create_game() -> GameManager:
    """ゲームインスタンスの作成"""
    logger.info(config_manager.get_text("game_manager.new_game_instance"))
    return GameManager()