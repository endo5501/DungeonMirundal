"""
WindowManager クラス

Window Systemの中核となる管理クラス
"""

from typing import Dict, Optional, List, Type, Any
import pygame
import pygame_gui
import os
from datetime import datetime

from src.utils.logger import logger
from .window import Window, WindowState
from .window_stack import WindowStack
from .focus_manager import FocusManager
from .event_router import EventRouter
from .statistics_manager import StatisticsManager
from .window_pool import get_window_pool


class WindowManager:
    """
    ウィンドウマネージャー
    
    Window Systemの最上位管理者として以下の機能を提供する：
    - 全ウィンドウの作成・管理・破棄
    - フォーカス管理とイベント分配
    - ウィンドウスタックによる階層管理
    - システム全体の統合管理
    """
    
    _instance: Optional['WindowManager'] = None
    
    def __new__(cls) -> 'WindowManager':
        """シングルトンパターンで唯一のインスタンスを保証"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        """ウィンドウマネージャーを初期化"""
        if hasattr(self, '_initialized'):
            return
        
        self._initialize_core_components()
        self._initialize_system_state()
        self._initialize_statistics()
        self._initialize_event_handling()
        
        self._initialized = True
        logger.info("WindowManagerを初期化しました")
    
    def _initialize_core_components(self):
        """コアコンポーネントを初期化"""
        self.window_stack = WindowStack()
        self.focus_manager = FocusManager()
        self.event_router = EventRouter()
        self.statistics_manager = StatisticsManager()
        self.window_pool = get_window_pool()
        self.window_registry: Dict[str, Window] = {}
    
    def _initialize_system_state(self):
        """システム状態を初期化"""
        self.screen: Optional[pygame.Surface] = None
        self.clock: Optional[pygame.time.Clock] = None
        self.ui_manager: Optional['pygame_gui.UIManager'] = None
        self.running = False
        self.debug_mode = False
    
    def _initialize_statistics(self):
        """統計情報を初期化"""
        # StatisticsManagerで管理されるため、ここでは何もしない
        pass
    
    def _initialize_event_handling(self):
        """イベントハンドリングを初期化"""
        self.escape_handlers: List[callable] = []
    
    @classmethod
    def get_instance(cls) -> 'WindowManager':
        """シングルトンインスタンスを取得"""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
    
    def initialize_pygame(self, screen: pygame.Surface, clock: pygame.time.Clock) -> None:
        """
        Pygameとの統合初期化
        
        Args:
            screen: メインスクリーン
            clock: ゲームクロック
        """
        self.screen = screen
        self.clock = clock
        self.running = True
        
        # UIManagerを初期化（既存システムと同じ方法）
        if not self.ui_manager:
            import pygame_gui
            
            # pygameフォントシステムを事前に初期化
            pygame.font.init()
            
            # 日本語フォントを事前にロード（pygame-guiが認識できるようにする）
            try:
                japanese_font_path = "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"
                if os.path.exists(japanese_font_path):
                    # フォントを事前ロード
                    test_font = pygame.font.Font(japanese_font_path, 14)
                    logger.info(f"WindowManager: 日本語フォントを事前ロード: {japanese_font_path}")
            except Exception as pre_e:
                logger.warning(f"WindowManager: 日本語フォント事前ロードエラー: {pre_e}")
            
            # pygame-gui マネージャー（既存システムと同じテーマファイル）
            try:
                theme_path = "/home/satorue/Dungeon/config/ui_theme.json"
                self.ui_manager = pygame_gui.UIManager((screen.get_width(), screen.get_height()), theme_path)
                logger.info(f"WindowManager: UIテーマを読み込みました: {theme_path}")
                
                # デバッグ：pygame-guiのフォント状態を確認
                theme = self.ui_manager.get_theme()
                logger.debug(f"WindowManager: pygame-gui theme loaded: {theme}")
                
                # フォント辞書を確認
                try:
                    font_dict = theme.get_font_dictionary()
                    logger.debug(f"WindowManager: pygame-gui font dictionary: {font_dict}")
                    
                    # デフォルトフォントを確認
                    default_font_info = theme.get_font_info(theme_target=None, element_type='defaults')
                    logger.debug(f"WindowManager: default font info: {default_font_info}")
                    
                except Exception as debug_e:
                    logger.debug(f"WindowManager: Error getting font debug info: {debug_e}")
                    
            except Exception as e:
                logger.warning(f"WindowManager: UIテーマの読み込みに失敗、デフォルトテーマを使用: {e}")
                self.ui_manager = pygame_gui.UIManager((screen.get_width(), screen.get_height()))
            
            # フォント初期化（既存システムと同じ）
            self._initialize_fonts()
            
            # pygame-guiに日本語フォントを直接登録
            self._register_japanese_fonts_to_pygame_gui()
        
        # デバッグモードの設定
        self.event_router.set_debug_mode(self.debug_mode)
        
        logger.info("WindowManager: Pygame統合を初期化しました")
    
    def _initialize_fonts(self):
        """フォント初期化（既存システムと同じ方法）"""
        try:
            from src.ui.font_manager_pygame import font_manager
            # 日本語フォントを優先して取得
            self.default_font = font_manager.get_japanese_font(24)
            self.title_font = font_manager.get_japanese_font(32)
            
            # フォールバック処理
            if not self.default_font:
                self.default_font = font_manager.get_font('default', 24)
            if not self.title_font:
                self.title_font = font_manager.get_font('default', 32)
                
            logger.debug("WindowManager: フォント初期化完了")
                
        except Exception as e:
            logger.error(f"WindowManager: フォント初期化エラー: {e}")
    
    def _register_japanese_fonts_to_pygame_gui(self):
        """pygame-guiに日本語フォントを直接登録"""
        try:
            import pygame.freetype
            
            # pygame-guiのフォント辞書を取得
            theme = self.ui_manager.get_theme()
            font_dict = theme.get_font_dictionary()
            
            # 日本語フォントパス
            japanese_font_path = "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"
            
            # notoフォントとして登録
            if os.path.exists(japanese_font_path):
                # フォントをロード
                try:
                    # pygame.fontでフォントをロード
                    import pygame.font
                    test_font = pygame.font.Font(japanese_font_path, 14)
                    
                    # フォント辞書に登録
                    font_dict.add_font_path('noto', japanese_font_path, 'regular')
                    
                    logger.info(f"WindowManager: pygame-guiに日本語フォントを登録: {japanese_font_path}")
                    
                except Exception as font_e:
                    logger.warning(f"WindowManager: pygame.fontでのフォントロードエラー: {font_e}")
                    
                    # pygame.freetypeで試す
                    try:
                        ft_font = pygame.freetype.Font(japanese_font_path, 14)
                        logger.info(f"WindowManager: pygame.freetypeで日本語フォントをロード成功")
                    except Exception as ft_e:
                        logger.error(f"WindowManager: pygame.freetypeでのフォントロードエラー: {ft_e}")
            else:
                logger.warning(f"WindowManager: 日本語フォントが見つかりません: {japanese_font_path}")
                
        except Exception as e:
            logger.error(f"WindowManager: pygame-guiへのフォント登録エラー: {e}")
    
    def create_window(self, window_class: Type[Window], window_id: str = None, 
                     parent: Optional[Window] = None, **kwargs) -> Window:
        """
        新しいウィンドウを作成
        
        Args:
            window_class: ウィンドウクラス
            window_id: ウィンドウID（自動生成される場合もある）
            parent: 親ウィンドウ
            **kwargs: ウィンドウ固有の引数
            
        Returns:
            Window: 作成されたウィンドウ
        """
        # ウィンドウIDの生成
        if window_id is None:
            window_id = f"{window_class.__name__}_{datetime.now().strftime('%H%M%S_%f')}"
        
        # 既存のウィンドウIDと重複チェック
        if window_id in self.window_registry:
            existing_window = self.window_registry[window_id]
            
            # 破棄されたまたは非表示ウィンドウの場合は、レジストリから削除
            if existing_window.state in [WindowState.DESTROYED, WindowState.HIDDEN]:
                logger.debug(f"非アクティブウィンドウをレジストリから削除: {window_id} (状態: {existing_window.state})")
                del self.window_registry[window_id]
            else:
                logger.error(f"ウィンドウID重複エラー: '{window_id}' は既に使用中")
                logger.error(f"既存ウィンドウ状態: {existing_window.state}")
                logger.error(f"スタック内の存在: {window_id in [w.window_id for w in self.window_stack.stack]}")
                raise ValueError(f"ウィンドウID '{window_id}' は既に使用されています")
        
        # ウィンドウを作成（プールから再利用または新規作成）
        window = self.window_pool.get_window(window_class, window_id, parent=parent, **kwargs)
        
        # レジストリに登録
        self.window_registry[window_id] = window
        self.statistics_manager.increment_counter('windows_created')
        
        logger.debug(f"ウィンドウを作成: {window_id} ({window_class.__name__})")
        return window
    
    def show_window(self, window: Window, push_to_stack: bool = True) -> None:
        """
        ウィンドウを表示
        
        Args:
            window: 表示するウィンドウ
            push_to_stack: スタックにプッシュするかどうか
        """
        if window.window_id not in self.window_registry:
            raise ValueError(f"未登録のウィンドウです: {window.window_id}")
        
        # 現在表示中のウィンドウを非表示にする
        current_window = self.get_active_window()
        if current_window and current_window != window:
            logger.debug(f"背後のウィンドウを非表示にします: {current_window.window_id}")
            if hasattr(current_window, 'hide_ui_elements'):
                current_window.hide_ui_elements()
            # ウィンドウの状態は変更せず、UI要素のみ非表示
        
        # ウィンドウを表示
        window.show()
        
        # スタックに追加
        if push_to_stack:
            self.window_stack.push(window)
            logger.info(f"ウィンドウをスタックに追加: {window.window_id}")
        
        # フォーカスを設定
        self.focus_manager.set_focus(window)
        # モーダルウィンドウの場合はフォーカスをロック
        if window.modal:
            self.focus_manager.lock_focus(window)
    
    def hide_window(self, window: Window, remove_from_stack: bool = True) -> None:
        """
        ウィンドウを非表示
        
        Args:
            window: 非表示にするウィンドウ
            remove_from_stack: スタックから削除するかどうか
        """
        # ウィンドウのUI要素を非表示にする
        window.hide_ui_elements()
        
        # ウィンドウの状態を非表示に変更
        window.hide()
        
        # スタックから削除
        if remove_from_stack:
            self.window_stack.remove_window(window)
        
        # フォーカスロックを解除（モーダルウィンドウの場合）
        if window.modal and self.focus_manager.is_focus_locked():
            self.focus_manager.unlock_focus()
        
        # 新しいトップウィンドウにフォーカスを設定し、再表示
        new_top = self.get_active_window()
        if new_top:
            self.focus_manager.set_focus(new_top)
            # 背後のウィンドウを明示的に再表示
            new_top.show_ui_elements()
            new_top.show()
            logger.debug(f"背後のウィンドウを再表示: {new_top.window_id}")
        
        logger.debug(f"ウィンドウを非表示: {window.window_id}")
    
    def close_window(self, window: Window) -> None:
        """
        ウィンドウを閉じる（非表示 + 破棄）
        
        Args:
            window: 閉じるウィンドウ
        """
        # 背後のウィンドウを先に取得（destroy前に取得する必要がある）
        self.window_stack.remove_window(window)
        new_top = self.get_active_window()
        
        # ウィンドウのUI要素を破棄
        window.destroy()
        
        # レジストリから削除
        if window.window_id in self.window_registry:
            del self.window_registry[window.window_id]
        
        # フォーカスロックを解除（モーダルウィンドウの場合）
        if window.modal and self.focus_manager.is_focus_locked():
            self.focus_manager.unlock_focus()
        
        # 背後のウィンドウを再表示
        if new_top:
            self.focus_manager.set_focus(new_top)
            new_top.show_ui_elements()
            new_top.show()
            logger.debug(f"背後のウィンドウを再表示: {new_top.window_id}")
        
        # イベントリスナーをクリーンアップ
        self.event_router.cleanup_window_listeners(window.window_id)
        
        # フォーカス状態をクリーンアップ
        self.focus_manager.cleanup_destroyed_windows()
        
        self.statistics_manager.increment_counter('windows_destroyed')
        logger.debug(f"ウィンドウを閉じました: {window.window_id}")
    
    def destroy_window(self, window: Window) -> None:
        """
        ウィンドウを破棄
        
        Args:
            window: 破棄するウィンドウ
        """
        # 子ウィンドウを先に破棄（カスケード削除）
        children_to_destroy = [w for w in self.window_registry.values() if w.parent == window]
        for child in children_to_destroy:
            self.destroy_window(child)
        
        # ウィンドウスタックから削除
        self.window_stack.remove_window(window)
        
        # ウィンドウのUI要素を完全に破棄
        window.destroy()
        
        # レジストリから削除
        if window.window_id in self.window_registry:
            del self.window_registry[window.window_id]
        else:
            logger.warning(f"破棄対象ウィンドウがレジストリに存在しません: {window.window_id}")
        
        # イベントリスナーをクリーンアップ
        self.event_router.cleanup_window_listeners(window.window_id)
        
        # フォーカス状態をクリーンアップ
        self.focus_manager.cleanup_destroyed_windows()
        
        self.statistics_manager.increment_counter('windows_destroyed')
        logger.debug(f"ウィンドウを破棄: {window.window_id}")
    
    def get_window(self, window_id: str) -> Optional[Window]:
        """
        ウィンドウを取得
        
        Args:
            window_id: ウィンドウID
            
        Returns:
            Optional[Window]: 見つかったウィンドウ
        """
        return self.window_registry.get(window_id)
    
    def get_active_window(self) -> Optional[Window]:
        """
        アクティブウィンドウを取得
        
        Returns:
            Optional[Window]: アクティブウィンドウ
        """
        return self.window_stack.peek()
    
    def get_focused_window(self) -> Optional[Window]:
        """
        フォーカスされているウィンドウを取得
        
        Returns:
            Optional[Window]: フォーカスされているウィンドウ
        """
        return self.focus_manager.get_focused_window()
    
    def handle_global_events(self, events: List[pygame.event.Event]) -> None:
        """
        グローバルイベントを処理
        
        Args:
            events: Pygameイベントリスト
        """
        for event in events:
            self.statistics_manager.increment_counter('events_processed')
            
            # UIManagerでのイベント処理
            if self.ui_manager:
                self.ui_manager.process_events(event)
            
            # ESCキーの処理
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                if self.handle_escape_key():
                    continue
            
            # 数字キー（1-9）の処理：ボタンショートカット
            if (event.type == pygame.KEYDOWN and 
                pygame.K_1 <= event.key <= pygame.K_9):
                button_number = event.key - pygame.K_1 + 1  # 1-9
                if self.handle_button_shortcut(button_number):
                    continue
            
            # アクティブウィンドウにイベントをルーティング
            active_window = self.get_active_window()
            if active_window:
                # 直接ウィンドウのhandle_eventを呼び出し（EventRouterを迂回）
                if active_window.handle_event(event):
                    continue
        
        # メッセージキューを処理
        self.event_router.process_message_queue(self.window_registry)
    
    def handle_escape_key(self) -> bool:
        """
        ESCキーを処理
        
        Returns:
            bool: 処理された場合True
        """
        # カスタムESCハンドラーを先に実行
        for handler in self.escape_handlers:
            try:
                if handler():
                    return True
            except Exception as e:
                logger.error(f"ESCハンドラーでエラー: {e}")
        
        # アクティブウィンドウのESC処理
        active_window = self.get_active_window()
        if active_window:
            if active_window.handle_escape():
                return True
    
    def handle_button_shortcut(self, button_number: int) -> bool:
        """
        数字キーによるボタンショートカットを処理
        
        Args:
            button_number: ボタン番号（1-9）
            
        Returns:
            bool: 処理された場合True
        """
        try:
            # 現在表示されているボタンを取得
            visible_buttons = self.get_visible_buttons()
            
            # 指定された番号のボタンを検索
            target_button = None
            for button in visible_buttons:
                if hasattr(button, '_shortcut_number') and button._shortcut_number == button_number:
                    target_button = button
                    break
            
            if target_button:
                # ボタンクリックイベントを生成して送信
                button_rect = target_button.rect
                click_pos = button_rect.center
                
                # マウスクリックイベントを生成
                click_event = pygame.event.Event(
                    pygame.MOUSEBUTTONDOWN,
                    pos=click_pos,
                    button=1
                )
                
                # UIManagerに送信
                if self.ui_manager:
                    self.ui_manager.process_events(click_event)
                
                # クリック解除イベントも送信
                release_event = pygame.event.Event(
                    pygame.MOUSEBUTTONUP,
                    pos=click_pos,
                    button=1
                )
                
                if self.ui_manager:
                    self.ui_manager.process_events(release_event)
                
                logger.debug(f"ボタンショートカット {button_number} が実行されました")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"ボタンショートカット処理エラー: {e}")
            return False
    
    def get_visible_buttons(self) -> List[Any]:
        """
        現在表示されているボタンを取得
        
        Returns:
            List[Any]: 表示中のボタンリスト
        """
        buttons = []
        
        if not self.ui_manager:
            return buttons
        
        try:
            # UIManagerの全要素を探索してボタンを検索
            root_container = self.ui_manager.get_root_container()
            if root_container:
                self._collect_buttons_recursive(root_container, buttons)
            
            # ボタンに番号を割り当て
            for i, button in enumerate(buttons):
                if i < 9:  # 1-9の数字キーのみ対応
                    button._shortcut_number = i + 1
                else:
                    button._shortcut_number = None
            
        except Exception as e:
            logger.error(f"ボタン収集エラー: {e}")
        
        return buttons
    
    def _collect_buttons_recursive(self, element: Any, buttons: List[Any]) -> None:
        """
        UI要素を再帰的に探索してボタンを収集
        
        Args:
            element: UI要素
            buttons: ボタンリスト（参照渡し）
        """
        try:
            # ボタンかどうかチェック
            if (hasattr(element, 'rect') and hasattr(element, 'visible') and 
                element.visible and 'Button' in type(element).__name__):
                buttons.append(element)
            
            # 子要素を探索
            if hasattr(element, 'elements'):
                for child in element.elements:
                    self._collect_buttons_recursive(child, buttons)
                    
        except Exception as e:
            logger.debug(f"ボタン収集中のエラー（要素: {type(element).__name__}）: {e}")
        
        # デフォルトのESC処理（戻る）
        return self.go_back()
    
    def go_back(self) -> bool:
        """
        前のウィンドウに戻る
        
        Returns:
            bool: 戻り処理が実行された場合True
        """
        return self.window_stack.go_back()
    
    def go_back_to_root(self) -> bool:
        """
        ルートウィンドウまで戻る
        
        Returns:
            bool: 戻り処理が実行された場合True
        """
        return self.window_stack.go_back_to_root()
    
    def update(self, time_delta: float) -> None:
        """
        システム全体の更新
        
        Args:
            time_delta: 前回の更新からの経過時間（秒）
        """
        # UIManagerの更新
        if self.ui_manager:
            self.ui_manager.update(time_delta)
        
        # 全ウィンドウの更新
        for window in self.window_registry.values():
            if window.state == WindowState.SHOWN:
                window.update(time_delta)
        
        # フォーカス状態のクリーンアップ
        self.focus_manager.cleanup_destroyed_windows()
    
    def draw(self, surface: pygame.Surface) -> None:
        """
        全ウィンドウの描画（階層制御あり）
        
        Args:
            surface: 描画対象のサーフェス
        """
        # 最上位ウィンドウのみを描画する
        top_window = self.get_active_window()
        
        if top_window and top_window.state == WindowState.SHOWN:
            # 最上位ウィンドウのみ描画
            top_window.draw(surface)
            logger.debug(f"最上位ウィンドウを描画: {top_window.window_id}")
        else:
            # ウィンドウがない場合は背景をクリア
            surface.fill((0, 0, 0))
            logger.debug("ウィンドウなし: 背景をクリア")
        
        # UIManagerの描画（最上位ウィンドウのUI要素）
        if self.ui_manager:
            self.ui_manager.draw_ui(surface)
        else:
            logger.warning("WindowManager.draw(): UIManagerがありません")
        
        self.statistics_manager.increment_counter('frames_rendered')
    
    def add_escape_handler(self, handler: callable) -> None:
        """
        ESCキーハンドラーを追加
        
        Args:
            handler: ESCキー処理関数
        """
        if handler not in self.escape_handlers:
            self.escape_handlers.append(handler)
    
    def remove_escape_handler(self, handler: callable) -> None:
        """
        ESCキーハンドラーを削除
        
        Args:
            handler: ESCキー処理関数
        """
        if handler in self.escape_handlers:
            self.escape_handlers.remove(handler)
    
    def set_debug_mode(self, enabled: bool) -> None:
        """
        デバッグモードを設定
        
        Args:
            enabled: デバッグモードを有効にするかどうか
        """
        self.debug_mode = enabled
        self.event_router.set_debug_mode(enabled)
        logger.debug(f"デバッグモードを設定: {enabled}")
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        統計情報を取得
        
        Returns:
            Dict[str, Any]: 統計情報
        """
        stats = self.statistics_manager.get_all_statistics()
        stats.update({
            'active_windows': len([w for w in self.window_registry.values() if w.state == WindowState.SHOWN]),
            'total_windows': len(self.window_registry),
            'stack_size': self.window_stack.size(),
            'focus_locked': self.focus_manager.is_focus_locked(),
            **self.event_router.get_statistics()
        })
        return stats
    
    def get_debug_info(self) -> List[str]:
        """
        デバッグ情報を取得
        
        Returns:
            List[str]: デバッグ情報の文字列リスト
        """
        info = []
        
        # システム統計
        stats = self.get_statistics()
        info.append("WindowManager Statistics:")
        for key, value in stats.items():
            info.append(f"  {key}: {value}")
        
        # ウィンドウスタック情報
        info.append("\n" + self.window_stack.get_hierarchy_info())
        
        # フォーカス情報
        info.extend(["\n"] + self.focus_manager.get_focus_trace())
        
        # イベントルーター情報
        info.extend(["\n"] + self.event_router.get_debug_info())
        
        return info
    
    def validate_system_state(self) -> List[str]:
        """
        システム状態の整合性をチェック
        
        Returns:
            List[str]: 発見された問題のリスト
        """
        issues = []
        
        # ウィンドウスタックの検証
        issues.extend(self.window_stack.validate_stack())
        
        # フォーカス状態の検証
        issues.extend(self.focus_manager.validate_focus_state())
        
        # レジストリとスタックの整合性チェック
        for window in self.window_stack:
            if window.window_id not in self.window_registry:
                issues.append(f"スタック内のウィンドウがレジストリに存在しません: {window.window_id}")
        
        return issues
    
    def handle_orphan_message(self, sender: Window, message_type: str, data: Dict[str, Any]) -> None:
        """
        親のないウィンドウからのメッセージを処理
        
        Args:
            sender: 送信者ウィンドウ
            message_type: メッセージの種類
            data: メッセージデータ
        """
        logger.debug(f"孤児メッセージを受信: {message_type} from {sender.window_id}")
        
        # ダイアログの閉じる要求
        if message_type == 'close_requested':
            self.hide_window(sender, remove_from_stack=True)
        # ダイアログの結果通知
        elif message_type == 'dialog_result':
            # ダイアログの結果を直接的に処理するロジックがあれば実行
            logger.info(f"ダイアログ結果: {data}")
        # その他のメッセージタイプ
        else:
            logger.debug(f"未処理の孤児メッセージ: {message_type}")
    
    def cleanup(self) -> None:
        """システム全体のクリーンアップ"""
        # 全ウィンドウを閉じる
        for window in list(self.window_registry.values()):
            self.close_window(window)
        
        # コンポーネントをリセット
        self.window_stack.clear()
        self.focus_manager.reset()
        self.event_router.reset()
        
        # 統計情報をリセット
        self.statistics_manager.reset_all()
        
        self.running = False
        logger.info("WindowManagerをクリーンアップしました")
    
    def render(self, screen):
        """描画処理（drawメソッドのエイリアス）
        
        Args:
            screen: 描画対象のスクリーン
        """
        # drawメソッドを呼び出して一貫性を保つ
        self.draw(screen)
    
    def shutdown(self) -> None:
        """システムをシャットダウン"""
        self.cleanup()
        WindowManager._instance = None
        logger.info("WindowManagerをシャットダウンしました")
    
    def __str__(self) -> str:
        stats = self.get_statistics()
        return f"WindowManager(windows: {stats['total_windows']}, active: {stats['active_windows']}, stack: {stats['stack_size']})"