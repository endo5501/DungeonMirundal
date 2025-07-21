"""ゲーム管理システム - リファクタリング版

Fowlerのリファクタリング手法を適用:
- Extract Class: SceneManager, EventBus
- Move Method: シーン固有のメソッドを各シーンに移動
- Replace Data Value with Object: イベント駆動アーキテクチャ
"""

import pygame
import sys
import random
from typing import Dict, List, Any, Optional
from . import dbg_api
from src.core.config_manager import config_manager
from src.core.input_manager import InputManager
from src.core.save_manager import SaveManager
from src.core.scene_manager import SceneManager, SceneType
from src.core.event_bus import EventBus, EventType, GameEvent, EventHandler, publish_event
from src.overworld.overworld_manager import OverworldManager
from src.dungeon.dungeon_manager import DungeonManager
from src.combat.combat_manager import CombatManager
from src.encounter.encounter_manager import EncounterManager
from src.character.party import Party
from src.rendering.dungeon_renderer_pygame import DungeonRendererPygame
from src.ui.dungeon_ui_pygame import create_pygame_dungeon_ui
from src.utils.logger import logger
from src.utils.constants import *
from src.utils.constants import GameLocation
from src.core.loop import MainLoopManager
from src.core.combat import CombatStateManager
from src.core.input import InputHandlerCoordinator
from src.core.scene import SceneTransitionManager
from src.core.state import GameStateManager


class GameManager(EventHandler):
    """メインゲーム管理クラス - リファクタリング版
    
    責務を大幅に削減し、シーン管理とイベント処理に特化。
    個別の機能は各シーンとマネージャーに移譲。
    """
    
    def __init__(self):
        # Pygame初期化
        pygame.init()
        
        # ディスプレイ設定
        self.screen = None
        self.clock = pygame.time.Clock()
        self.running = False
        
        # ゲーム状態（簡素化）
        self.game_state = "startup"
        self.paused = False
        self.current_location = GameLocation.OVERWORLD
        
        # コア設定
        self.game_config = config_manager
        self.input_manager = InputManager()
        self.save_manager = SaveManager()
        
        # マネージャー（シーンから参照される）
        self.overworld_manager = None
        self.dungeon_manager = None
        self.combat_manager = None
        self.encounter_manager = None
        self.dungeon_renderer = None
        
        # パーティ情報
        self.current_party = None
        
        # 新アーキテクチャコンポーネント
        self.event_bus = EventBus()
        self.scene_manager = None  # 後で初期化
        
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
        
        # シーン管理システム初期化
        self._setup_scene_management()
        
        # イベントバス設定
        self._setup_event_handlers()
        
        # MainLoopManager初期化
        self._setup_main_loop_manager()
        
        # CombatStateManager初期化
        self._setup_combat_state_manager()
        
        # InputHandlerCoordinator初期化
        self._setup_input_handler_coordinator()
        
        # SceneTransitionManager初期化
        self._setup_scene_transition_manager()
        
        # GameStateManager初期化
        self._setup_game_state_manager()
        
        logger.info(self.game_config.get_text("app_log.game_manager_initialized"))
    
    def _setup_scene_management(self):
        """シーン管理システム初期化"""
        self.scene_manager = SceneManager(self)
        logger.debug("シーン管理システム初期化完了")
    
    def _setup_event_handlers(self):
        """イベントハンドラーの設定"""
        # GameManagerをイベントハンドラーとして登録
        event_types = [
            EventType.SCENE_TRANSITION_REQUESTED,
            EventType.PARTY_CREATED,
            EventType.COMBAT_STARTED,
            EventType.COMBAT_ENDED
        ]
        
        for event_type in event_types:
            self.event_bus.subscribe(event_type, self)
        
        logger.info("イベントハンドラー設定完了")
    
    def _setup_main_loop_manager(self):
        """MainLoopManagerの初期化"""
        self.main_loop_manager = MainLoopManager()
        
        # 初期化コンテキストを準備
        context = {
            'screen': self.screen,
            'clock': self.clock,
            'target_fps': self.target_fps,
            'scene_manager': self.scene_manager,
            'input_manager': getattr(self, 'input_manager', None),
            'ui_manager': getattr(self, 'ui_manager', None),
            'debug_enabled': getattr(self, 'debug_enabled', False)
        }
        
        # MainLoopManagerを初期化
        if self.main_loop_manager.initialize(context):
            logger.info("MainLoopManager初期化完了")
        else:
            logger.error("MainLoopManager初期化失敗")
    
    def _setup_combat_state_manager(self):
        """CombatStateManagerの初期化"""
        self.combat_state_manager = CombatStateManager()
        
        # 初期化コンテキストを準備
        context = {
            'combat_manager': getattr(self, 'combat_manager', None),
            'encounter_manager': getattr(self, 'encounter_manager', None),
            'dungeon_manager': getattr(self, 'dungeon_manager', None),
            'current_party': getattr(self, 'current_party', None),
            'set_game_state_callback': self.set_game_state,
            'get_game_state_callback': lambda: self.game_state
        }
        
        # CombatStateManagerを初期化
        if self.combat_state_manager.initialize(context):
            # 戦闘結果処理ハンドラーを登録
            self.combat_state_manager.register_victory_handler(self._legacy_handle_combat_victory)
            self.combat_state_manager.register_defeat_handler(self._legacy_handle_combat_defeat)
            self.combat_state_manager.register_fled_handler(self._legacy_handle_combat_fled)
            self.combat_state_manager.register_negotiated_handler(self._legacy_handle_combat_negotiated)
            
            logger.info("CombatStateManager初期化完了")
        else:
            logger.error("CombatStateManager初期化失敗")
    
    def _setup_input_handler_coordinator(self):
        """InputHandlerCoordinatorの初期化"""
        self.input_handler_coordinator = InputHandlerCoordinator()
        
        # 初期化コンテキストを準備
        context = {
            'game_config': self.game_config,
            'current_location': self.current_location,
            'dungeon_renderer': getattr(self, 'dungeon_renderer', None),
            'overworld_manager': getattr(self, 'overworld_manager', None),
            'toggle_pause_callback': self.toggle_pause,
            'get_text_callback': self.get_text
        }
        
        # InputHandlerCoordinatorを初期化
        if self.input_handler_coordinator.initialize(context):
            logger.info("InputHandlerCoordinator初期化完了")
        else:
            logger.error("InputHandlerCoordinator初期化失敗")
    
    def _setup_scene_transition_manager(self):
        """SceneTransitionManagerの初期化"""
        self.scene_transition_manager = SceneTransitionManager()
        
        # 初期化コンテキストを準備
        context = {
            'game_config': self.game_config,
            'current_location': self.current_location,
            'game_state': self.game_state,
            'current_party': self.current_party,
            'overworld_manager': getattr(self, 'overworld_manager', None),
            'dungeon_manager': getattr(self, 'dungeon_manager', None),
            'dungeon_renderer': getattr(self, 'dungeon_renderer', None),
            'encounter_manager': getattr(self, 'encounter_manager', None)
        }
        
        # SceneTransitionManagerを初期化
        if self.scene_transition_manager.initialize(context):
            logger.info("SceneTransitionManager初期化完了")
        else:
            logger.error("SceneTransitionManager初期化失敗")
    
    def _setup_game_state_manager(self):
        """GameStateManagerの初期化"""
        self.game_state_manager = GameStateManager()
        
        # 初期化コンテキストを準備
        context = {
            'save_manager': self.save_manager,
            'current_party': self.current_party,
            'current_location': self.current_location,
            'overworld_manager': getattr(self, 'overworld_manager', None),
            'dungeon_manager': getattr(self, 'dungeon_manager', None),
            'auto_save_enabled': True
        }
        
        # GameStateManagerを初期化
        if self.game_state_manager.initialize(context):
            logger.info("GameStateManager初期化完了")
        else:
            logger.error("GameStateManager初期化失敗")
    
    def handle_event(self, event: GameEvent) -> bool:
        """EventHandler インターフェースの実装"""
        try:
            if event.event_type == EventType.SCENE_TRANSITION_REQUESTED:
                return self._handle_scene_transition_request(event)
            elif event.event_type == EventType.PARTY_CREATED:
                return self._handle_party_created(event)
            elif event.event_type == EventType.COMBAT_STARTED:
                return self._handle_combat_started(event)
            elif event.event_type == EventType.COMBAT_ENDED:
                return self._handle_combat_ended(event)
            
            return False
            
        except Exception as e:
            logger.error(f"イベント処理エラー: {event.event_type.value}: {e}")
            return False
    
    def _handle_scene_transition_request(self, event: GameEvent) -> bool:
        """シーン遷移リクエストの処理"""
        scene_type_str = event.data.get('scene_type')
        context = event.data.get('context', {})
        
        if scene_type_str == 'overworld':
            return self.scene_manager.transition_to_overworld(context.get('from_dungeon', False))
        elif scene_type_str == 'dungeon':
            return self.scene_manager.transition_to_dungeon(context.get('dungeon_id', 'main_dungeon'))
        elif scene_type_str == 'combat':
            return self.scene_manager.transition_to_combat(context.get('monsters', []))
        
        return False
    
    def _handle_party_created(self, event: GameEvent) -> bool:
        """パーティ作成イベントの処理"""
        party = event.data.get('party')
        if party:
            self.set_current_party(party)
        return True
    
    def _handle_combat_started(self, event: GameEvent) -> bool:
        """戦闘開始イベントの処理"""
        logger.info("戦闘開始イベントを受信")
        return True
    
    def _handle_combat_ended(self, event: GameEvent) -> bool:
        """戦闘終了イベントの処理"""
        logger.info("戦闘終了イベントを受信")
        return True
        
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

        # デバッグサーバ起動（GameManagerインスタンスを登録）
        dbg_api.start(self.screen, self)
        
        # main.pyのgame_manager変数を確実に更新
        try:
            import main
            if hasattr(main, 'game_manager'):
                main.game_manager = self
                logger.info(f"main.game_manager updated to {hex(id(self))}")
        except Exception as e:
            logger.warning(f"Failed to update main.game_manager: {e}")

        logger.info(self.game_config.get_text("app_log.debug_setting").format(status=status))
    
    def _on_menu_action(self, action: str, pressed: bool, input_type):
        """メニューアクションの処理 - InputHandlerCoordinatorに委譲"""
        if hasattr(self, 'input_handler_coordinator'):
            return self.input_handler_coordinator.handle_input_action('menu', pressed, input_type.value if hasattr(input_type, 'value') else str(input_type))
        else:
            logger.error("InputHandlerCoordinator not initialized")
    
    def _on_confirm_action(self, action: str, pressed: bool, input_type):
        """確認アクションの処理 - InputHandlerCoordinatorに委譲"""
        if hasattr(self, 'input_handler_coordinator'):
            return self.input_handler_coordinator.handle_input_action('confirm', pressed, input_type.value if hasattr(input_type, 'value') else str(input_type))
        else:
            logger.error("InputHandlerCoordinator not initialized")
    
    def _on_cancel_action(self, action: str, pressed: bool, input_type):
        """キャンセルアクションの処理 - InputHandlerCoordinatorに委譲"""
        if hasattr(self, 'input_handler_coordinator'):
            return self.input_handler_coordinator.handle_input_action('cancel', pressed, input_type.value if hasattr(input_type, 'value') else str(input_type))
        else:
            logger.error("InputHandlerCoordinator not initialized")
    
    def _on_action_action(self, action: str, pressed: bool, input_type):
        """アクションボタンの処理 - InputHandlerCoordinatorに委譲"""
        if hasattr(self, 'input_handler_coordinator'):
            return self.input_handler_coordinator.handle_input_action('action', pressed, input_type.value if hasattr(input_type, 'value') else str(input_type))
        else:
            logger.error("InputHandlerCoordinator not initialized")
            
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
        logger.info(f"[DEBUG] 移動アクション: action={action}, pressed={pressed}, location={self.current_location}, renderer={self.dungeon_renderer is not None}")
        
        if pressed and self.current_location == GameLocation.DUNGEON and self.dungeon_renderer:
            # ダンジョンレンダラーに移動処理を委譲
            from src.core.input_manager import InputAction
            
            logger.info(f"[DEBUG] ダンジョン移動処理開始: {action}")
            
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
        logger.debug("WindowManagerをPygameで初期化しました")
        
        # 地上部マネージャーの初期化
        try:
            self.overworld_manager = OverworldManager()
            # GameManagerの参照を設定
            self.overworld_manager.set_game_manager(self)
            # set_ui_managerメソッドは存在しないため削除
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
        self.dungeon_manager.set_force_retreat_callback(self._handle_force_retreat)
        
        # 戦闘・エンカウンターマネージャーの初期化
        self.combat_manager = CombatManager()
        self.encounter_manager = EncounterManager()
        
        logger.debug("戦闘・エンカウンターシステム初期化完了")
        
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
        """ゲーム状態の設定 - SceneTransitionManagerに委譲"""
        if hasattr(self, 'scene_transition_manager'):
            self.scene_transition_manager.set_game_state(state)
            # ローカル状態も同期
            self.game_state = state
        else:
            # フォールバック: 従来の処理
            old_state = self.game_state
            self.game_state = state
            logger.info(self.game_config.get_text("app_log.game_state_changed").format(old_state=old_state, new_state=state))
    
    def set_current_location(self, location: GameLocation):
        """現在のロケーション設定 - SceneTransitionManagerに委譲"""
        if hasattr(self, 'scene_transition_manager'):
            self.scene_transition_manager.set_current_location(location)
            # ローカル状態も同期
            self.current_location = location
        else:
            # フォールバック: 従来の処理
            old_location = self.current_location
            self.current_location = location
            logger.info(f"Location changed: {old_location.value} -> {location.value}")
    
    def set_current_party(self, party: Party):
        """現在のパーティを設定 - イベント駆動版"""
        # 循環参照防止：既に同じパーティが設定されている場合はスキップ
        if self.current_party is party:
            return
            
        old_party = self.current_party
        self.current_party = party
        
        # マネージャーにパーティを設定（既存の依存関係を維持）
        if self.encounter_manager:
            self.encounter_manager.set_party(party)
        
        if self.dungeon_renderer:
            self.dungeon_renderer.set_party(party)
        
        # CombatStateManagerにも反映
        if hasattr(self, 'combat_state_manager'):
            self.combat_state_manager.set_current_party(party)
            
            # dungeon_ui_managerは既にdungeon_renderer.set_party()内で設定されるので重複呼び出しを削除
            # if hasattr(self.dungeon_renderer, 'dungeon_ui_manager') and self.dungeon_renderer.dungeon_ui_manager:
            #     self.dungeon_renderer.dungeon_ui_manager.set_party(party)
        
        # パーティ変更イベントを発行
        if party is not None:
            publish_event(
                EventType.PARTY_CREATED,
                "game_manager",
                {
                    "party": party,
                    "old_party": old_party,
                    "member_count": len(party.get_living_characters())
                }
            )
            logger.info(self.game_config.get_text("app_log.party_set").format(name=party.name, count=len(party.get_living_characters())))
        else:
            logger.info("パーティをクリアしました")
    
    def get_current_party(self) -> Party:
        """現在のパーティを取得"""
        return self.current_party
    
    def set_party(self, party: Party):
        """パーティを設定（GuildService用のエイリアス）"""
        self.set_current_party(party)
    
    # === ダンジョン管理メソッド ===
    
    def get_dungeon_list(self):
        """作成済みダンジョン一覧を取得"""
        try:
            if not self.save_manager.current_save:
                logger.warning("セーブデータが存在しません")
                return []
            
            return self.save_manager.current_save.dungeon_list
            
        except Exception as e:
            logger.error(f"ダンジョン一覧取得エラー: {e}")
            return []
    
    def add_dungeon_to_list(self, dungeon_info: Dict[str, Any]):
        """ダンジョン情報をセーブデータに追加し、自動保存する"""
        try:
            if not self.save_manager.current_save:
                logger.warning("セーブデータが存在しません。新しいセーブデータを作成します")
                return False
            
            # 重複チェック
            current_dungeons = self.save_manager.current_save.dungeon_list
            for existing_dungeon in current_dungeons:
                if existing_dungeon.get('hash_value') == dungeon_info.get('hash_value'):
                    logger.warning(f"ダンジョン {dungeon_info.get('hash_value')} は既に登録済みです")
                    return False
            
            current_dungeons.append(dungeon_info)
            logger.info(f"ダンジョンを追加しました: {dungeon_info.get('hash_value', 'Unknown')}")
            
            # 重要: ダンジョン追加後、即座にセーブデータを保存
            if self.current_party:
                slot_id = self.save_manager.current_save.save_slot.slot_id
                save_success = self.save_current_game(slot_id, self.save_manager.current_save.save_slot.name)
                if save_success:
                    logger.info(f"ダンジョン追加後の自動保存が完了しました (スロット{slot_id})")
                else:
                    logger.error("ダンジョン追加後の自動保存に失敗しました")
                    return False
            else:
                logger.warning("現在のパーティが存在しないため、自動保存をスキップしました")
            
            return True
            
        except Exception as e:
            logger.error(f"ダンジョン追加エラー: {e}")
            return False
    
    def remove_dungeon_from_list(self, hash_value: str):
        """ダンジョン情報をセーブデータから削除し、自動保存する"""
        try:
            if not self.save_manager.current_save:
                logger.warning("セーブデータが存在しません")
                return False
            
            dungeons = self.save_manager.current_save.dungeon_list
            
            for i, dungeon in enumerate(dungeons):
                if dungeon.get('hash_value') == hash_value:
                    removed_dungeon = dungeons.pop(i)
                    logger.info(f"ダンジョン {removed_dungeon.get('hash_value')} を削除しました")
                    
                    # 重要: ダンジョン削除後、即座にセーブデータを保存
                    if self.current_party:
                        slot_id = self.save_manager.current_save.save_slot.slot_id
                        save_success = self.save_current_game(slot_id, self.save_manager.current_save.save_slot.name)
                        if save_success:
                            logger.info(f"ダンジョン削除後の自動保存が完了しました (スロット{slot_id})")
                        else:
                            logger.error("ダンジョン削除後の自動保存に失敗しました")
                            return False
                    else:
                        logger.warning("現在のパーティが存在しないため、自動保存をスキップしました")
                    
                    return True
            
            logger.warning(f"ダンジョン {hash_value} が見つかりません")
            return False
            
        except Exception as e:
            logger.error(f"ダンジョン削除エラー: {e}")
            return False
    
    # === ギルド管理メソッド ===
    
    def add_guild_character(self, character):
        """ギルド登録済み冒険者一覧にキャラクターを追加"""
        try:
            # 現在のセーブデータを取得または作成
            if not self.save_manager.current_save:
                logger.warning("セーブデータが存在しません。新しいセーブデータを作成します")
                return False
            
            # ギルド登録済み冒険者一覧にキャラクターを追加
            current_guild_characters = self.save_manager.current_save.guild_characters
            
            # 重複チェック
            for existing_char in current_guild_characters:
                if existing_char.character_id == character.character_id:
                    logger.warning(f"キャラクター {character.name} は既にギルドに登録済みです")
                    return False
            
            current_guild_characters.append(character)
            logger.info(f"キャラクター {character.name} をギルドに登録しました")
            return True
            
        except Exception as e:
            logger.error(f"ギルドキャラクター追加エラー: {e}")
            return False
    
    def remove_guild_character(self, character_id: str):
        """ギルド登録済み冒険者一覧からキャラクターを削除"""
        try:
            if not self.save_manager.current_save:
                logger.warning("セーブデータが存在しません")
                return False
            
            guild_characters = self.save_manager.current_save.guild_characters
            
            for i, character in enumerate(guild_characters):
                if character.character_id == character_id:
                    removed_char = guild_characters.pop(i)
                    logger.info(f"キャラクター {removed_char.name} をギルドから削除しました")
                    return True
            
            logger.warning(f"キャラクターID {character_id} がギルドに見つかりません")
            return False
            
        except Exception as e:
            logger.error(f"ギルドキャラクター削除エラー: {e}")
            return False
    
    def get_guild_characters(self):
        """ギルド登録済み冒険者一覧を取得"""
        try:
            if not self.save_manager.current_save:
                logger.warning("セーブデータが存在しません")
                return []
            
            return self.save_manager.current_save.guild_characters
            
        except Exception as e:
            logger.error(f"ギルドキャラクター取得エラー: {e}")
            return []
    
    def get_guild_character_by_id(self, character_id: str):
        """指定IDのギルド登録済み冒険者を取得"""
        try:
            guild_characters = self.get_guild_characters()
            
            for character in guild_characters:
                if character.character_id == character_id:
                    return character
            
            return None
            
        except Exception as e:
            logger.error(f"ギルドキャラクター取得エラー: {e}")
            return None
    
    def save_current_game(self, slot_id: int, save_name: str = "") -> bool:
        """現在のゲーム状態を保存 - GameStateManagerに委譲"""
        if hasattr(self, 'game_state_manager'):
            # 現在のパーティ状態を更新
            self.game_state_manager.current_party = self.current_party
            self.game_state_manager.current_location = self.current_location
            return self.game_state_manager.save_current_game(slot_id, save_name)
        else:
            # フォールバック: 従来の処理
            try:
                if not self.current_party:
                    logger.error("保存するパーティがありません")
                    return False
                
                # ギルドキャラクターを取得
                guild_characters = self.get_guild_characters()
                
                # ダンジョン情報を取得
                dungeon_list = self.get_dungeon_list()
                
                # ゲーム状態を作成
                game_state = {
                    'location': self.current_location.value if hasattr(self.current_location, 'value') else str(self.current_location)
                }
                
                # セーブ実行
                success = self.save_manager.save_game(
                    party=self.current_party,
                    slot_id=slot_id,
                    save_name=save_name,
                    game_state=game_state,
                    guild_characters=guild_characters,
                    dungeon_list=dungeon_list
                )
                
                if success:
                    logger.info(f"ゲームを保存しました: スロット{slot_id}, ギルドキャラクター{len(guild_characters)}人, ダンジョン{len(dungeon_list)}個")
                
                return success
                
            except Exception as e:
                logger.error(f"ゲーム保存エラー: {e}")
                return False
    
    @property
    def in_dungeon(self) -> bool:
        """ダンジョン内にいるかどうか"""
        return self.current_location == GameLocation.DUNGEON
    
    def transition_to_dungeon(self, dungeon_id: str = "main_dungeon"):
        """ダンジョンへの遷移 - SceneTransitionManagerに委譲"""
        if hasattr(self, 'scene_transition_manager'):
            # 現在のパーティ状態を更新
            self.scene_transition_manager.current_party = self.current_party
            return self.scene_transition_manager.transition_to_dungeon(dungeon_id)
        else:
            # フォールバック: イベント駆動版
            if not self.current_party:
                logger.error(self.game_config.get_text("game_manager.party_error_no_party"))
                raise Exception(self.game_config.get_text("game_manager.party_error_no_party"))
            
            if not self.current_party.get_living_characters():
                logger.error(self.game_config.get_text("game_manager.party_error_no_living"))
                raise Exception(self.game_config.get_text("game_manager.party_error_no_living"))
            
            # イベントでシーン遷移をリクエスト
            publish_event(
                EventType.SCENE_TRANSITION_REQUESTED,
                "game_manager",
                {
                    "scene_type": "dungeon",
                    "context": {"dungeon_id": dungeon_id}
                }
            )
            
            return True
    
    def transition_to_overworld(self):
        """地上部への遷移 - SceneTransitionManagerに委譲"""
        if hasattr(self, 'scene_transition_manager'):
            # 現在のパーティ状態を更新
            self.scene_transition_manager.current_party = self.current_party
            return self.scene_transition_manager.transition_to_overworld()
        else:
            # フォールバック: イベント駆動版
            if not self.current_party:
                logger.error(self.game_config.get_text("game_manager.party_error_no_party"))
                return False
            
            # イベントでシーン遷移をリクエスト
            from_dungeon = (self.current_location == GameLocation.DUNGEON)
            publish_event(
                EventType.SCENE_TRANSITION_REQUESTED,
                "game_manager",
                {
                    "scene_type": "overworld",
                    "context": {"from_dungeon": from_dungeon}
                }
            )
            
            return True
    
    def _generate_dungeon_seed(self, dungeon_id: str) -> str:
        """ダンジョンIDに基づいてシードを生成"""
        # ダンジョンIDがハッシュ値の場合（ダンジョン選択で渡される）は直接使用
        if len(dungeon_id) == 32 and all(c in '0123456789abcdef' for c in dungeon_id):
            # 32文字の16進文字列（MD5ハッシュ）の場合はそのまま使用
            logger.info(f"ハッシュ値をシードとして使用: {dungeon_id[:8]}...")
            return dungeon_id
        
        # 従来の処理（固定ダンジョン名等）
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
        """ゲーム状態の保存 - GameStateManagerに委譲"""
        if hasattr(self, 'game_state_manager'):
            # 現在のパーティ状態を更新
            self.game_state_manager.current_party = self.current_party
            self.game_state_manager.current_location = self.current_location
            return self.game_state_manager.save_game_state(slot_id)
        else:
            # フォールバック: 従来の処理
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
        """ゲーム状態の読み込み - GameStateManagerに委譲"""
        if hasattr(self, 'game_state_manager'):
            # GameStateManagerでロード実行
            success = self.game_state_manager.load_game_state(slot_id)
            if success:
                # ローカル状態も同期
                self.current_party = self.game_state_manager.current_party
                self.current_location = self.game_state_manager.current_location
            return success
        else:
            # フォールバック: 従来の処理
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
        """ゲームの実行 - リファクタリング版（MainLoopManager使用）"""
        logger.info(self.game_config.get_text("game_manager.game_start"))
        
        # 初回起動処理
        self._initialize_game_flow()
        
        # MainLoopManagerでメインループを実行
        self.running = True
        
        # 永続要素の描画ハンドラーを登録
        self.main_loop_manager.register_render_handler(self._render_persistent_elements_handler)
        
        # デバッグ情報の描画ハンドラーを登録
        if self.debug_enabled:
            self.main_loop_manager.register_render_handler(self._render_debug_info_handler)
        
        # メインループ実行
        try:
            self.main_loop_manager.run_main_loop()
        except KeyboardInterrupt:
            logger.info("ユーザーによる中断")
        except Exception as e:
            logger.error(f"メインループエラー: {e}")
            raise
        finally:
            self.running = False
    
    def _render_persistent_elements_handler(self, surface: pygame.Surface) -> None:
        """永続要素描画ハンドラー（MainLoopManager用）"""
        self._render_persistent_elements()
    
    def _render_debug_info_handler(self, surface: pygame.Surface) -> None:
        """デバッグ情報描画ハンドラー（MainLoopManager用）"""
        self._render_debug_info()
    
    def _handle_ui_events(self, event) -> bool:
        """統合UIイベント処理"""
        ui_handled = False
        
        # ダンジョン内での移動キー（WASD）はUIで処理せず、InputManagerに委譲
        if (event.type == pygame.KEYDOWN and 
            event.key in [pygame.K_w, pygame.K_a, pygame.K_s, pygame.K_d] and 
            self.current_location == GameLocation.DUNGEON):
            if event.type == pygame.KEYDOWN and event.key in [pygame.K_w, pygame.K_a, pygame.K_s, pygame.K_d]:
                logger.info(f"[DEBUG] GameManager._handle_ui_events: ダンジョン内移動キーのため、UIスキップしてInputManagerに委譲")
            return False
        
        # WindowManagerでイベント処理
        from src.ui.window_system import WindowManager
        window_manager = WindowManager.get_instance()
        
        if not window_manager.screen:
            window_manager.initialize_pygame(self.screen, self.clock)
        
        ui_handled = window_manager.handle_global_events([event])
        
        # デバッグ: WASDキーの処理をログ出力
        if event.type == pygame.KEYDOWN and event.key in [pygame.K_w, pygame.K_a, pygame.K_s, pygame.K_d]:
            logger.info(f"[DEBUG] GameManager._handle_ui_events: WindowManager処理結果={ui_handled}")
        
        # WindowManagerで処理されなかった場合のみ、既存UIマネージャーで処理
        if not ui_handled and hasattr(self, 'ui_manager') and self.ui_manager:
            ui_handled = self.ui_manager.handle_event(event)
            if event.type == pygame.KEYDOWN and event.key in [pygame.K_w, pygame.K_a, pygame.K_s, pygame.K_d]:
                logger.info(f"[DEBUG] GameManager._handle_ui_events: ui_manager処理結果={ui_handled}")
        
        return ui_handled
    
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
        """ゲーム開始時の初期化フロー - リファクタリング版"""
        # 自動セーブデータロードを試行
        auto_load_success = self._try_auto_load()
        
        # 自動ロードに失敗した場合はテスト用パーティを作成
        if not auto_load_success and not self.current_party:
            self._create_test_party()
        
        # シーンマネージャーでスタートアップシーンから開始
        self.scene_manager.transition_to(SceneType.STARTUP)
    
    def _try_auto_load(self):
        """自動セーブデータロードを試行 - GameStateManagerに委譲"""
        if hasattr(self, 'game_state_manager'):
            # GameStateManagerで自動ロード実行
            success = self.game_state_manager.try_auto_load()
            if success:
                # ローカル状態も同期
                self.current_party = self.game_state_manager.current_party
                self.current_location = self.game_state_manager.current_location
            else:
                logger.info(self.game_config.get_text("game_manager.new_game_start"))
            return success
        else:
            # フォールバック: 従来の処理
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
    
    # === Phase 5: 戦闘・エンカウンター統合メソッド ===
    
    def trigger_encounter(self, encounter_type: str = "normal", level: int = 1):
        """エンカウンターを発生させる - CombatStateManagerに委譲"""
        if hasattr(self, 'combat_state_manager'):
            return self.combat_state_manager.trigger_encounter(encounter_type, level)
        else:
            logger.error("CombatStateManager not initialized")
            return False
    
    def start_combat(self, monsters):
        """戦闘開始 - CombatStateManagerに委譲"""
        if hasattr(self, 'combat_state_manager'):
            return self.combat_state_manager.start_combat(monsters)
        else:
            logger.error("CombatStateManager not initialized")
            return False
    
    def check_combat_state(self):
        """戦闘状態の確認・戦闘終了処理 - CombatStateManagerに委譲"""
        if hasattr(self, 'combat_state_manager'):
            self.combat_state_manager.check_combat_state()
        else:
            logger.error("CombatStateManager not initialized")
    
    def end_combat(self):
        """戦闘終了処理 - CombatStateManagerに委譲"""
        if hasattr(self, 'combat_state_manager'):
            self.combat_state_manager.end_combat()
        else:
            logger.error("CombatStateManager not initialized")
    
    def _legacy_handle_combat_victory(self):
        """戦闘勝利時の処理"""
        logger.info("戦闘勝利!")
        
        if not self.current_party or not self.combat_manager:
            return
        
        try:
            # 戦闘統計から報酬情報を取得
            combat_stats = self.combat_manager.monster_stats
            
            # 経験値獲得
            total_exp = getattr(combat_stats, 'total_experience', 0)
            if total_exp > 0:
                for character in self.current_party.get_living_characters():
                    character.gain_experience(total_exp)
                logger.info(f"経験値 {total_exp} を獲得しました")
            
            # 金獲得
            total_gold = getattr(combat_stats, 'total_gold', 0)
            if total_gold > 0:
                self.current_party.gold += total_gold
                logger.info(f"金 {total_gold} を獲得しました")
            
            # アイテム獲得
            dropped_items = getattr(combat_stats, 'dropped_items', [])
            if dropped_items:
                for item in dropped_items:
                    # パーティインベントリに追加
                    if hasattr(self.current_party, 'shared_inventory'):
                        self.current_party.shared_inventory.add_item(item)
                    logger.info(f"アイテム「{item.name}」を獲得しました")
            
        except Exception as e:
            logger.error(f"戦闘勝利処理エラー: {e}")
    
    def _legacy_handle_combat_defeat(self):
        """戦闘敗北時の処理"""
        logger.info("戦闘敗北...")
        
        if not self.current_party:
            return
        
        try:
            # パーティ全滅チェック
            living_characters = self.current_party.get_living_characters()
            
            if not living_characters:
                # 全滅時の処理
                logger.info("パーティが全滅しました")
                
                # 金の半分を失う
                lost_gold = self.current_party.gold // 2
                self.current_party.gold -= lost_gold
                if lost_gold > 0:
                    logger.info(f"金 {lost_gold} を失いました")
                
                # 全キャラクターのHPを1に設定（死亡状態から救済）
                for character in self.current_party.members:
                    if character.hp <= 0:
                        character.hp = 1
                        character.status = "normal"  # 状態異常も回復
                
                # 地上部に強制帰還
                self._force_return_to_overworld("パーティ全滅のため地上に帰還しました")
            else:
                # 生存者がいる場合は通常の敗北処理
                logger.info("戦闘に敗北しましたが、生存者がいます")
                
        except Exception as e:
            logger.error(f"戦闘敗北処理エラー: {e}")
    
    def _legacy_handle_combat_fled(self):
        """戦闘逃走時の処理"""
        logger.info("戦闘から逃走しました")
        
        if not self.dungeon_manager or not self.dungeon_manager.current_dungeon:
            return
        
        try:
            # 現在位置から後退（来た方向に1マス戻る）
            current_dungeon = self.dungeon_manager.current_dungeon
            player_pos = current_dungeon.player_position
            
            # 逃走方向を決定（現在の向きと逆方向）
            from src.dungeon.dungeon_generator import Direction
            
            escape_direction = {
                Direction.NORTH: Direction.SOUTH,
                Direction.SOUTH: Direction.NORTH,
                Direction.EAST: Direction.WEST,
                Direction.WEST: Direction.EAST
            }.get(player_pos.facing, Direction.SOUTH)
            
            # 逃走先の座標計算
            direction_offsets = {
                Direction.NORTH: (0, -1),
                Direction.SOUTH: (0, 1),
                Direction.EAST: (1, 0),
                Direction.WEST: (-1, 0)
            }
            
            offset_x, offset_y = direction_offsets[escape_direction]
            new_x = player_pos.x + offset_x
            new_y = player_pos.y + offset_y
            
            # 移動可能かチェック
            current_level = current_dungeon.levels.get(player_pos.level)
            if current_level and self.dungeon_manager.can_move_to(new_x, new_y, player_pos.level):
                # 移動実行
                self.dungeon_manager.move_player(escape_direction)
                logger.info(f"逃走により位置が移動しました: ({new_x}, {new_y})")
            else:
                logger.info("逃走したが、移動できませんでした")
                
        except Exception as e:
            logger.error(f"戦闘逃走処理エラー: {e}")
    
    def _legacy_handle_combat_negotiated(self):
        """戦闘交渉成功時の処理"""
        logger.info("交渉成功!")
        
        if not self.current_party or not self.combat_manager:
            return
        
        try:
            # 交渉による特別報酬（戦闘せずに報酬獲得）
            combat_stats = self.combat_manager.monster_stats
            
            # 経験値は半分程度
            negotiation_exp = getattr(combat_stats, 'total_experience', 0) // 2
            if negotiation_exp > 0:
                for character in self.current_party.get_living_characters():
                    character.gain_experience(negotiation_exp)
                logger.info(f"交渉により経験値 {negotiation_exp} を獲得しました")
            
            # 金は通常通り
            negotiation_gold = getattr(combat_stats, 'total_gold', 0)
            if negotiation_gold > 0:
                self.current_party.gold += negotiation_gold
                logger.info(f"交渉により金 {negotiation_gold} を獲得しました")
            
            # 特別なアイテムが手に入る可能性
            import random
            if random.random() < 0.3:  # 30%の確率で特別アイテム
                logger.info("交渉により特別な情報を得ました")
                # TODO: 特別アイテムやヒントの実装
                
        except Exception as e:
            logger.error(f"戦闘交渉処理エラー: {e}")
    
    def _force_return_to_overworld(self, reason: str = ""):
        """地上部への強制帰還"""
        try:
            logger.info(f"地上部へ強制帰還: {reason}")
            
            # ダンジョン状態をクリア
            if self.dungeon_manager and self.dungeon_manager.current_dungeon:
                self.dungeon_manager.exit_dungeon()
            
            # 地上部に遷移
            self.current_location = GameLocation.OVERWORLD
            self.set_game_state("overworld")
            
            # 地上部マネージャーを表示
            if self.overworld_manager:
                self.overworld_manager.enter_overworld()
            
        except Exception as e:
            logger.error(f"強制帰還処理エラー: {e}")
    
    def _handle_force_retreat(self, reason: str):
        """ダンジョンマネージャーからの強制撤退処理"""
        logger.critical(f"ダンジョン強制撤退: {reason}")
        
        if not self.current_party:
            return
        
        try:
            # 撤退による救済処理
            if reason == "パーティ全滅":
                # 全員のHPを1に設定して救済
                for member in self.current_party.members:
                    if member.derived_stats.current_hp <= 0:
                        member.derived_stats.current_hp = 1
                        member.status = "normal"
                
                # 金の半分を失う
                lost_gold = self.current_party.gold // 2
                self.current_party.gold -= lost_gold
                if lost_gold > 0:
                    logger.info(f"撤退により金 {lost_gold} を失いました")
            
            elif reason == "残り1名が重傷":
                # 軽微な救済処理
                for member in self.current_party.members:
                    if member.derived_stats.current_hp <= 0:
                        member.derived_stats.current_hp = 1
                
                # 金の1/4を失う
                lost_gold = self.current_party.gold // 4
                self.current_party.gold -= lost_gold
                if lost_gold > 0:
                    logger.info(f"緊急撤退により金 {lost_gold} を失いました")
            
            # 地上部に強制帰還
            self._force_return_to_overworld(f"緊急撤退: {reason}")
            
        except Exception as e:
            logger.error(f"強制撤退処理エラー: {e}")
    
    def check_party_status_in_dungeon(self):
        """ダンジョン内でのパーティ状態監視"""
        if (self.current_location != GameLocation.DUNGEON or 
            not self.dungeon_manager or 
            not self.current_party):
            return
        
        try:
            # ダンジョンマネージャーでパーティ状態をチェック
            status = self.dungeon_manager.check_party_status(self.current_party)
            
            # 状態に応じた警告
            if status["needs_healing"] and status["critically_injured"]:
                logger.warning(f"重傷者がいます: {', '.join(status['critically_injured'])}")
            
            if status["dead_members"]:
                logger.warning(f"死亡メンバー: {', '.join(status['dead_members'])}")
                
                # 強制撤退チェック
                should_retreat, retreat_reason = self.dungeon_manager.should_force_retreat(self.current_party)
                if should_retreat:
                    self._handle_force_retreat(retreat_reason)
            
        except Exception as e:
            logger.error(f"パーティ状態チェックエラー: {e}")
    
    # === Phase 5 Day 25-26: ダンジョンインタラクション統合 ===
    
    def interact_with_dungeon_cell(self, character = None) -> Dict[str, Any]:
        """現在位置のダンジョンセルとインタラクション"""
        if (self.current_location != GameLocation.DUNGEON or 
            not self.dungeon_manager or 
            not self.current_party):
            return {"success": False, "message": "ダンジョンにいません"}
        
        try:
            # ダンジョンマネージャーでセルインタラクションを実行
            result = self.dungeon_manager.interact_with_current_cell(self.current_party, character)
            
            # インタラクション結果の処理
            for interaction in result.get("interactions", []):
                self._process_interaction_result(interaction)
            
            return result
            
        except Exception as e:
            logger.error(f"ダンジョンセルインタラクションエラー: {e}")
            return {"success": False, "message": f"インタラクションエラー: {e}"}
    
    def _process_interaction_result(self, interaction: Dict[str, Any]):
        """インタラクション結果の処理"""
        interaction_type = interaction.get("type")
        
        if interaction_type == "trap":
            self._process_trap_result(interaction)
        elif interaction_type == "treasure":
            self._process_treasure_result(interaction)
        elif interaction_type == "boss":
            self._process_boss_result(interaction)
    
    def _process_trap_result(self, trap_result: Dict[str, Any]):
        """トラップ結果の処理"""
        if trap_result.get("teleport"):
            # テレポートトラップの場合、ランダム位置に移動
            self._handle_teleport_trap()
        
        # その他のトラップ効果は既にtrap_systemで処理済み
        logger.info(f"トラップ処理完了: {trap_result.get('message', '')}")
    
    def _process_treasure_result(self, treasure_result: Dict[str, Any]):
        """宝箱結果の処理"""
        if treasure_result.get("start_combat") and treasure_result.get("mimic_monster"):
            # ミミック戦闘開始
            mimic = treasure_result["mimic_monster"]
            self.start_combat([mimic])
            logger.info("ミミックとの戦闘開始！")
    
    def _process_boss_result(self, boss_result: Dict[str, Any]):
        """ボス戦結果の処理"""
        if boss_result.get("start_combat") and boss_result.get("boss_monster"):
            # ボス戦開始
            boss_monster = boss_result["boss_monster"]
            boss_encounter = boss_result.get("boss_encounter")
            encounter_id = boss_result.get("encounter_id")
            
            # 現在のエンカウンター情報を保存
            if hasattr(self, 'current_boss_encounter'):
                self.current_boss_encounter = {
                    "encounter": boss_encounter,
                    "encounter_id": encounter_id
                }
            
            self.start_combat([boss_monster])
            logger.info(f"ボス戦開始: {boss_result.get('message', '')}")
    
    def _handle_teleport_trap(self):
        """テレポートトラップの処理"""
        if not self.dungeon_manager or not self.dungeon_manager.current_dungeon:
            return
        
        try:
            current_dungeon = self.dungeon_manager.current_dungeon
            player_pos = current_dungeon.player_position
            current_level = current_dungeon.levels.get(player_pos.level)
            
            if not current_level:
                return
            
            # ランダムな歩行可能位置を探す
            walkable_cells = []
            for x in range(current_level.width):
                for y in range(current_level.height):
                    if current_level.is_walkable(x, y):
                        walkable_cells.append((x, y))
            
            if walkable_cells:
                new_x, new_y = random.choice(walkable_cells)
                player_pos.x = new_x
                player_pos.y = new_y
                logger.info(f"テレポートトラップにより位置が移動: ({new_x}, {new_y})")
                
        except Exception as e:
            logger.error(f"テレポートトラップ処理エラー: {e}")
    
    def search_for_secrets(self) -> Dict[str, Any]:
        """隠された要素の探索"""
        if (self.current_location != GameLocation.DUNGEON or 
            not self.dungeon_manager or 
            not self.current_party):
            return {"success": False, "message": "ダンジョンにいません"}
        
        try:
            # 隠し要素の探索
            result = self.dungeon_manager.check_for_secret_interactions(self.current_party)
            
            if result.get("interactions"):
                for interaction in result["interactions"]:
                    logger.info(f"隠し要素発見: {interaction['message']}")
            
            return result
            
        except Exception as e:
            logger.error(f"隠し要素探索エラー: {e}")
            return {"success": False, "message": f"探索エラー: {e}"}
    
    def handle_boss_encounter_completion(self, victory: bool):
        """ボス戦完了処理"""
        if not hasattr(self, 'current_boss_encounter') or not self.current_boss_encounter:
            return
        
        try:
            encounter_id = self.current_boss_encounter["encounter_id"]
            result = self.dungeon_manager.complete_boss_encounter(encounter_id, victory, self.current_party)
            
            logger.info(f"ボス戦完了: {result.get('message', '')}")
            
            # エンカウンター情報をクリア
            self.current_boss_encounter = None
            
            return result
            
        except Exception as e:
            logger.error(f"ボス戦完了処理エラー: {e}")
            return {"success": False, "message": f"ボス戦完了エラー: {e}"}


def create_game() -> GameManager:
    """ゲームインスタンスの作成"""
    logger.info(config_manager.get_text("game_manager.new_game_instance"))
    return GameManager()