"""Main game loop management module."""

import pygame
from typing import Any, Dict, List, Optional, Callable
from src.core.interfaces import ManagedComponent
from src.utils.logger import logger


class MainLoopManager(ManagedComponent):
    """メインループとフレーム処理の統合管理
    
    GameManagerから抽出されたメインループ処理を統合管理し、
    重複コードを削除して単一責任を持つ。
    """
    
    def __init__(self):
        super().__init__()
        self.screen: Optional[pygame.Surface] = None
        self.clock: Optional[pygame.time.Clock] = None
        self.target_fps: int = 60
        self.running: bool = False
        
        # 外部依存コンポーネント
        self.scene_manager = None
        self.input_manager = None
        self.ui_manager = None
        self.debug_enabled: bool = False
        
        # イベントハンドラー
        self._event_handlers: List[Callable[[pygame.event.Event], bool]] = []
        self._update_handlers: List[Callable[[float], None]] = []
        self._render_handlers: List[Callable[[pygame.Surface], None]] = []
    
    def _do_initialize(self, context: Dict[str, Any]) -> bool:
        """MainLoopManagerの初期化"""
        try:
            # 必要なコンポーネントを取得
            self.screen = context.get('screen')
            self.clock = context.get('clock')
            self.target_fps = context.get('target_fps', 60)
            
            # 依存コンポーネント
            self.scene_manager = context.get('scene_manager')
            self.input_manager = context.get('input_manager')
            self.ui_manager = context.get('ui_manager')
            self.debug_enabled = context.get('debug_enabled', False)
            
            if not self.screen or not self.clock:
                logger.error("MainLoopManager: screen or clock not provided")
                return False
            
            logger.info("MainLoopManager initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"MainLoopManager initialization failed: {e}")
            return False
    
    def _do_cleanup(self) -> None:
        """MainLoopManagerのクリーンアップ"""
        self.stop()
        self._event_handlers.clear()
        self._update_handlers.clear()
        self._render_handlers.clear()
        logger.info("MainLoopManager cleaned up")
    
    def handle_game_event(self, event: Any) -> bool:
        """ゲームイベントの処理（現在は使用しない）"""
        return False
    
    def register_event_handler(self, handler: Callable[[pygame.event.Event], bool]) -> None:
        """イベントハンドラーの登録
        
        Args:
            handler: イベントを処理する関数。Trueを返すとイベントが消費される
        """
        if handler not in self._event_handlers:
            self._event_handlers.append(handler)
    
    def register_update_handler(self, handler: Callable[[float], None]) -> None:
        """更新ハンドラーの登録
        
        Args:
            handler: 時間デルタを受け取って更新処理を行う関数
        """
        if handler not in self._update_handlers:
            self._update_handlers.append(handler)
    
    def register_render_handler(self, handler: Callable[[pygame.Surface], None]) -> None:
        """描画ハンドラーの登録
        
        Args:
            handler: サーフェスを受け取って描画処理を行う関数
        """
        if handler not in self._render_handlers:
            self._render_handlers.append(handler)
    
    def run_main_loop(self) -> None:
        """統合されたメインループ実行
        
        重複していたメインループコードを統一し、
        拡張可能なハンドラーシステムを提供。
        """
        if self.state != "running":
            logger.error("MainLoopManager is not properly initialized")
            return
        
        self.running = True
        logger.info("Main loop started")
        
        try:
            while self.running:
                # イベント処理
                self._handle_frame_events()
                
                # システム更新
                self._update_systems()
                
                # フレーム描画
                self._render_frame()
                
        except Exception as e:
            logger.error(f"Main loop error: {e}")
            raise
        finally:
            logger.info("Main loop ended")
    
    def stop(self) -> None:
        """メインループの停止"""
        self.running = False
        logger.info("Main loop stop requested")
    
    def _handle_frame_events(self) -> None:
        """フレームごとのイベント処理
        
        GameManagerの_main_loop_refactoredから抽出した
        イベント処理ロジックを統合。
        """
        events = pygame.event.get()
        
        for event in events:
            # 終了イベントの処理
            if event.type == pygame.QUIT:
                self.running = False
                continue
            
            # デバッグログ（WASDキー専用）
            if event.type == pygame.KEYDOWN and event.key in [pygame.K_w, pygame.K_a, pygame.K_s, pygame.K_d]:
                logger.info(f"[DEBUG] MainLoopManager: WASD key detected key={pygame.key.name(event.key)}")
            
            # 登録されたイベントハンドラーで処理
            handled = False
            for handler in self._event_handlers:
                try:
                    if handler(event):
                        handled = True
                        break
                except Exception as e:
                    logger.error(f"Event handler error: {e}")
            
            if handled:
                continue
            
            # シーンマネージャーでイベント処理（優先）
            if self.scene_manager:
                scene_handled = self.scene_manager.handle_event(event)
                
                if event.type == pygame.KEYDOWN and event.key in [pygame.K_w, pygame.K_a, pygame.K_s, pygame.K_d]:
                    logger.info(f"[DEBUG] MainLoopManager: scene_handled={scene_handled}")
                
                if scene_handled:
                    continue
            
            # UI イベント処理
            ui_handled = self._handle_ui_events(event)
            
            if event.type == pygame.KEYDOWN and event.key in [pygame.K_w, pygame.K_a, pygame.K_s, pygame.K_d]:
                logger.info(f"[DEBUG] MainLoopManager: ui_handled={ui_handled}")
            
            # UIで処理されなかった場合のみ入力マネージャーに送信
            if not ui_handled and self.input_manager:
                self.input_manager.handle_event(event)
                if event.type == pygame.KEYDOWN and event.key in [pygame.K_w, pygame.K_a, pygame.K_s, pygame.K_d]:
                    logger.info(f"[DEBUG] MainLoopManager: sent to InputManager")
    
    def _handle_ui_events(self, event: pygame.event.Event) -> bool:
        """統合UIイベント処理
        
        GameManagerの_handle_ui_eventsから抽出。
        """
        ui_handled = False
        
        # ダンジョン内での移動キー（WASD）はUIで処理せず、InputManagerに委譲
        if (event.type == pygame.KEYDOWN and 
            event.key in [pygame.K_w, pygame.K_a, pygame.K_s, pygame.K_d]):
            # ダンジョン内かどうかの判定が必要だが、ここでは簡略化
            logger.info(f"[DEBUG] MainLoopManager._handle_ui_events: ダンジョン内移動キーのため、UIスキップしてInputManagerに委譲")
            return False
        
        # WindowManagerでイベント処理
        try:
            from src.ui.window_system import WindowManager
            window_manager = WindowManager.get_instance()
            
            if not window_manager.screen:
                window_manager.initialize_pygame(self.screen, self.clock)
            
            ui_handled = window_manager.handle_global_events([event])
            
            # デバッグ: WASDキーの処理をログ出力
            if event.type == pygame.KEYDOWN and event.key in [pygame.K_w, pygame.K_a, pygame.K_s, pygame.K_d]:
                logger.info(f"[DEBUG] MainLoopManager._handle_ui_events: WindowManager処理結果={ui_handled}")
            
            # WindowManagerで処理されなかった場合のみ、既存UIマネージャーで処理
            if not ui_handled and self.ui_manager:
                ui_handled = self.ui_manager.handle_event(event)
                if event.type == pygame.KEYDOWN and event.key in [pygame.K_w, pygame.K_a, pygame.K_s, pygame.K_d]:
                    logger.info(f"[DEBUG] MainLoopManager._handle_ui_events: ui_manager処理結果={ui_handled}")
                    
        except Exception as e:
            logger.error(f"UI event handling error: {e}")
        
        return ui_handled
    
    def _update_systems(self) -> None:
        """システム更新処理
        
        GameManagerの_update_systemsから抽出。
        """
        # FPS制限と時間更新
        time_delta = self.clock.tick(self.target_fps) / 1000.0
        
        # 入力マネージャー更新
        if self.input_manager:
            self.input_manager.update()
        
        # 登録された更新ハンドラーの実行
        for handler in self._update_handlers:
            try:
                handler(time_delta)
            except Exception as e:
                logger.error(f"Update handler error: {e}")
        
        # シーンマネージャー更新
        if self.scene_manager:
            self.scene_manager.update(time_delta)
        
        # WindowManager更新
        try:
            from src.ui.window_system import WindowManager
            window_manager = WindowManager.get_instance()
            window_manager.update(time_delta)
            
            # 既存UIマネージャー更新（WindowManagerがアクティブでない場合のみ）
            if not window_manager.get_active_window() and self.ui_manager:
                self.ui_manager.update(time_delta)
        except Exception as e:
            logger.error(f"UI update error: {e}")
    
    def _render_frame(self) -> None:
        """フレーム描画処理
        
        GameManagerの_render_frameから抽出。
        """
        # 画面をクリア
        self.screen.fill((0, 0, 0))
        
        # シーン描画（ダンジョン3D描画など）- 常に実行
        if self.scene_manager:
            self.scene_manager.render(self.screen)
        
        # 登録された描画ハンドラーの実行
        for handler in self._render_handlers:
            try:
                handler(self.screen)
            except Exception as e:
                logger.error(f"Render handler error: {e}")
        
        # WindowManager描画
        try:
            from src.ui.window_system import WindowManager
            window_manager = WindowManager.get_instance()
            window_manager.draw(self.screen)
            
            # UI描画の判定と実行
            if window_manager.get_active_window():
                # WindowManagerがアクティブな場合でも永続要素は描画
                self._render_persistent_elements()
            elif self.ui_manager:
                # WindowManagerがアクティブでない場合は既存UIマネージャーで描画
                self.ui_manager.render()
            else:
                # フォールバック：永続要素のみ描画
                self._render_persistent_elements()
                
        except Exception as e:
            logger.error(f"UI render error: {e}")
        
        # デバッグ情報描画
        if self.debug_enabled:
            self._render_debug_info()
        
        # 画面更新
        pygame.display.flip()
    
    def _render_persistent_elements(self) -> None:
        """永続要素の描画
        
        GameManagerの_render_persistent_elementsを呼び出し。
        将来的にはここに移行予定。
        """
        # 現在はGameManagerの実装を使用
        # TODO: 実装をここに移行
        pass
    
    def _render_debug_info(self) -> None:
        """デバッグ情報の描画
        
        GameManagerの_render_debug_infoを呼び出し。
        将来的にはここに移行予定。
        """
        # 現在はGameManagerの実装を使用
        # TODO: 実装をここに移行
        pass