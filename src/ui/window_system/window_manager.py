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
        
        # ウィンドウを表示
        window.show()
        logger.info(f"ウィンドウ.show()完了: {window.window_id}, state={window.state}")
        
        # スタックに追加
        if push_to_stack:
            self.window_stack.push(window)
            logger.info(f"ウィンドウをスタックに追加: {window.window_id}")
        
        # フォーカスを設定
        self.focus_manager.set_focus(window)
        logger.info(f"フォーカス設定完了: {window.window_id}")
        
        # モーダルウィンドウの場合はフォーカスをロック
        if window.modal:
            self.focus_manager.lock_focus(window)
            logger.info(f"モーダルウィンドウのフォーカスロック: {window.window_id}")
        
        # デバッグ: UIManagerの状態を確認
        if self.ui_manager and hasattr(self.ui_manager, 'get_root_container'):
            element_count = len(self.ui_manager.get_root_container().elements)
            logger.info(f"ウィンドウ表示後のUIManager要素数: {element_count}")
        
        logger.info(f"ウィンドウ表示完了: {window.window_id}, スタックサイズ: {self.window_stack.size()}")
        active = self.get_active_window()
        if active:
            logger.info(f"現在のアクティブウィンドウ: {active.window_id}")
    
    def hide_window(self, window: Window, remove_from_stack: bool = True) -> None:
        """
        ウィンドウを非表示
        
        Args:
            window: 非表示にするウィンドウ
            remove_from_stack: スタックから削除するかどうか
        """
        window.hide()
        
        # スタックから削除
        if remove_from_stack:
            self.window_stack.remove_window(window)
        
        # フォーカスロックを解除（モーダルウィンドウの場合）
        if window.modal and self.focus_manager.is_focus_locked():
            self.focus_manager.unlock_focus()
        
        # 新しいトップウィンドウにフォーカスを設定
        new_top = self.get_active_window()
        if new_top:
            self.focus_manager.set_focus(new_top)
        
        logger.debug(f"ウィンドウを非表示: {window.window_id}")
    
    def close_window(self, window: Window) -> None:
        """
        ウィンドウを閉じる（非表示 + 破棄）
        
        Args:
            window: 閉じるウィンドウ
        """
        # 非表示にしてスタックから削除
        self.hide_window(window, remove_from_stack=True)
        
        # ウィンドウを破棄
        self.destroy_window(window)
    
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
        
        # レジストリから削除
        if window.window_id in self.window_registry:
            del self.window_registry[window.window_id]
            logger.info(f"ウィンドウをレジストリから削除: {window.window_id}")
        else:
            logger.warning(f"破棄対象ウィンドウがレジストリに存在しません: {window.window_id}")
        
        # ウィンドウスタックから削除
        self.window_stack.remove_window(window)
        
        # イベントリスナーをクリーンアップ
        self.event_router.cleanup_window_listeners(window.window_id)
        
        # ウィンドウをプールに返却（失敗した場合は破棄）
        if not self.window_pool.return_window(window):
            window.destroy()
        
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
        全ウィンドウの描画
        
        Args:
            surface: 描画対象のサーフェス
        """
        # モーダルウィンドウを探す
        modal_window = None
        modal_index = -1
        windows_list = list(self.window_stack.stack)
        
        # 最後（最上位）のモーダルウィンドウを探す
        for i in range(len(windows_list) - 1, -1, -1):
            window = windows_list[i]
            if window.modal and window.state == WindowState.SHOWN:
                modal_window = window
                modal_index = i
                break
        
        # モーダルウィンドウがある場合
        if modal_window:
            # モーダルより下のウィンドウは描画しない
            # ただし、デバッグのために背景を描画
            
            # 背景を暗くする（モーダルの下のウィンドウの代わり）
            overlay = pygame.Surface(surface.get_size())
            overlay.set_alpha(200)  # 80%の透明度
            overlay.fill((0, 0, 0))
            surface.blit(overlay, (0, 0))
            
            # モーダルウィンドウのみ描画
            modal_window.draw(surface)
        else:
            # モーダルウィンドウがない場合は通常の描画
            for window in windows_list:
                if window.state == WindowState.SHOWN:
                    window.draw(surface)
        
        # UIManagerの描画
        if self.ui_manager:
            # デバッグ: UI要素数を確認
            if hasattr(self.ui_manager, 'get_root_container'):
                element_count = len(self.ui_manager.get_root_container().elements)
                if element_count > 0:
                    logger.debug(f"WindowManager.draw(): UI要素数={element_count}")
            
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
    
    def shutdown(self) -> None:
        """システムをシャットダウン"""
        self.cleanup()
        WindowManager._instance = None
        logger.info("WindowManagerをシャットダウンしました")
    
    def __str__(self) -> str:
        stats = self.get_statistics()
        return f"WindowManager(windows: {stats['total_windows']}, active: {stats['active_windows']}, stack: {stats['stack_size']})"