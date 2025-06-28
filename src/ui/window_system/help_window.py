"""ヘルプシステム用ウィンドウ

Window Systemのヘルプ管理ウィンドウクラス。
旧HelpUIシステムからWindow Systemアーキテクチャへの移行。

t-wada式TDD実装：
1. 最小限の実装でテストを通す（Green段階）
2. 段階的に機能を追加
3. Fowlerリファクタリングパターンで改善
"""

from typing import Optional, Dict, List, Any, Callable
import pygame
from enum import Enum

from src.ui.window_system.window import Window
from src.ui.window_system.menu_window import MenuWindow
from src.ui.window_system.dialog_window import DialogWindow
from src.ui.window_system.help_enums import HelpCategory, HelpContext
from src.ui.window_system.help_content_manager import HelpContentManager
from src.ui.window_system.help_display_manager import HelpDisplayManager, DisplayFormat
from src.ui.window_system.context_help_manager import ContextHelpManager, HelpTriggerType, HelpPriority
from src.utils.logger import logger


class HelpWindow(Window):
    """ヘルプシステム管理ウィンドウ
    
    Window SystemベースのヘルプシステムUI。
    カテゴリ別ヘルプ、コンテキストヘルプ、クイックリファレンスを統括。
    """
    
    def __init__(self, window_manager, rect: pygame.Rect, window_id: str = "help_window", **kwargs):
        """HelpWindow初期化
        
        Args:
            window_manager: ウィンドウマネージャー
            rect: ウィンドウの矩形
            window_id: ウィンドウID
            **kwargs: その他のオプション
        """
        super().__init__(window_id, **kwargs)
        self.window_manager = window_manager
        self.rect = rect
        
        # ヘルプシステム状態
        self.help_categories: Dict[HelpCategory, Dict[str, Any]] = {}
        self.current_category: Optional[HelpCategory] = None
        self.current_context: Optional[HelpContext] = None
        
        # 表示状態
        self.first_time_shown: bool = False
        
        # コールバック
        self.on_close_callback: Optional[Callable] = None
        
        # Fowler Extract Classパターン: 責任の分離
        self.content_manager = HelpContentManager()
        self.display_manager = HelpDisplayManager()
        self.context_manager = ContextHelpManager()
        
        # ヘルプコンテンツを抽出したクラスから取得
        self.help_categories = self.content_manager.help_categories
        
        # コンテキストヘルプのコールバック設定
        self._setup_context_callbacks()
        
        logger.info("HelpWindowを初期化しました（リファクタリング済み）")
    
    def create(self) -> None:
        """UI要素を作成（Window抽象メソッドの実装）"""
        # 最小限の実装でテストを通す
        logger.debug("HelpWindow UI要素を作成しました")
    
    def _setup_context_callbacks(self) -> None:
        """コンテキストヘルプのコールバックを設定"""
        # コンテキスト変更時のコールバック
        self.context_manager.add_help_callback(
            HelpTriggerType.CONTEXT_CHANGE,
            self._on_context_changed
        )
        
        # 初回ヘルプのコールバック
        self.context_manager.add_help_callback(
            HelpTriggerType.FIRST_TIME,
            self._on_first_time_help
        )
    
    def _on_context_changed(self, data: Dict[str, Any]) -> None:
        """コンテキスト変更時のコールバック"""
        new_context = data.get('new_context')
        previous_context = data.get('previous_context')
        logger.info(f"ヘルプコンテキストが変更されました: {previous_context} -> {new_context}")
    
    def _on_first_time_help(self, data: Dict[str, Any]) -> None:
        """初回ヘルプ時のコールバック"""
        logger.info("初回ヘルプが要求されました")
    
    def get_help_categories(self) -> List[HelpCategory]:
        """ヘルプカテゴリ一覧を取得（リファクタリング済み）
        
        Extract Classにより、コンテンツ取得をHelpContentManagerに委譲。
        
        Returns:
            List[HelpCategory]: ヘルプカテゴリ一覧
        """
        return self.content_manager.get_all_categories()
    
    def get_category_content(self, category: HelpCategory) -> Optional[Dict[str, Any]]:
        """カテゴリコンテンツを取得（リファクタリング済み）
        
        Args:
            category: ヘルプカテゴリ
            
        Returns:
            Dict: カテゴリコンテンツ
        """
        return self.content_manager.get_category_content(category)
    
    def get_formatted_category_help(self, category: HelpCategory) -> Dict[str, Any]:
        """フォーマット済みカテゴリヘルプを取得（リファクタリング済み）
        
        Args:
            category: ヘルプカテゴリ
            
        Returns:
            Dict: フォーマット済みヘルプデータ
        """
        content = self.content_manager.get_category_content(category)
        if not content:
            return {}
        
        return self.display_manager.format_category_help(content, DisplayFormat.DETAILED)
    
    def show_main_help_menu(self) -> None:
        """メインヘルプメニューを表示"""
        # ウィンドウマネージャーでウィンドウを表示
        if self.window_manager:
            self.window_manager.show_window(self)
        
        logger.info("メインヘルプメニューを表示しました")
    
    def show_category_help(self, category: str) -> None:
        """カテゴリ別ヘルプを表示
        
        Args:
            category: ヘルプカテゴリ
        """
        try:
            # 文字列をenumに変換
            if isinstance(category, str):
                help_category = HelpCategory(category)
            else:
                help_category = category
            
            self.current_category = help_category
            logger.info(f"カテゴリ別ヘルプを表示: {help_category.value}")
            
        except ValueError:
            logger.warning(f"無効なヘルプカテゴリ: {category}")
            # エラーハンドリング：無効なカテゴリでも適切に処理
            self.current_category = None
    
    def show_context_help(self, context: str) -> None:
        """コンテキストヘルプを表示
        
        Args:
            context: ヘルプコンテキスト
        """
        try:
            # 文字列をenumに変換
            if isinstance(context, str):
                help_context = HelpContext(context)
            else:
                help_context = context
            
            self.current_context = help_context
            logger.info(f"コンテキストヘルプを表示: {help_context.value}")
            
        except ValueError:
            logger.warning(f"無効なヘルプコンテキスト: {context}")
            # エラーハンドリング：無効なコンテキストでも適切に処理
            self.current_context = None
    
    def show_quick_reference(self) -> None:
        """クイックリファレンスを表示"""
        logger.info("クイックリファレンスを表示しました")
    
    def get_quick_reference_content(self) -> Dict[str, Any]:
        """クイックリファレンスの内容を取得（リファクタリング済み）
        
        Returns:
            Dict: クイックリファレンスの内容
        """
        content = self.content_manager.get_quick_reference_content()
        return self.display_manager.format_quick_reference(content)
    
    def show_controls_guide(self) -> None:
        """操作ガイドを表示"""
        logger.info("操作ガイドを表示しました")
    
    def get_controls_guide_content(self) -> Dict[str, Any]:
        """操作ガイドの内容を取得（リファクタリング済み）
        
        Returns:
            Dict: 操作ガイドの内容
        """
        content = self.content_manager.get_controls_guide_content()
        return self.display_manager.format_controls_guide(content)
    
    def show_first_time_help(self) -> None:
        """初回起動時ヘルプを表示（リファクタリング済み）"""
        # コンテキスト管理に委譲
        request = self.context_manager.request_first_time_help()
        if request:
            self.first_time_shown = True
            logger.info("初回起動時ヘルプを表示しました")
        else:
            logger.debug("初回起動時ヘルプは既に表示済みです")
    
    def get_first_time_help_content(self) -> Dict[str, Any]:
        """初回起動時ヘルプの内容を取得（リファクタリング済み）
        
        Returns:
            Dict: 初回ヘルプの内容
        """
        content = self.content_manager.get_first_time_help_content()
        return self.display_manager.format_first_time_help(content)
    
    def set_help_context(self, context: HelpContext) -> None:
        """ヘルプコンテキストを設定（リファクタリング済み）
        
        Args:
            context: ヘルプコンテキスト
        """
        self.context_manager.set_context(context)
    
    def request_context_help(self, context: Optional[HelpContext] = None) -> None:
        """コンテキストヘルプを要求（リファクタリング済み）
        
        Args:
            context: ヘルプコンテキスト
        """
        request = self.context_manager.request_context_help(context, HelpPriority.NORMAL)
        logger.info(f"コンテキストヘルプを要求: {request.context.value}")
    
    def get_help_menu_items(self) -> List[Dict[str, Any]]:
        """ヘルプメニューアイテムを取得（リファクタリング済み）
        
        Returns:
            List[Dict]: メニューアイテム
        """
        categories = self.get_help_categories()
        return self.display_manager.generate_menu_items(categories)
    
    def show_detailed_help_dialog(self, topic: str) -> None:
        """詳細ヘルプダイアログを表示
        
        Args:
            topic: ヘルプトピック
        """
        # DialogWindowを使用して詳細ヘルプを表示
        # 実装は段階的に追加
        logger.info(f"詳細ヘルプダイアログを表示: {topic}")
    
    def handle_event(self, event: pygame.event.Event) -> bool:
        """イベント処理
        
        Args:
            event: Pygameイベント
            
        Returns:
            bool: イベントが処理された場合True
        """
        # 基本的なイベント処理
        handled = super().handle_event(event)
        
        if handled:
            return True
        
        # ヘルプウィンドウ固有のイベント処理
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.close()
                return True
            elif event.key == pygame.K_h:
                # Hキーでヘルプを切り替え
                self.show_main_help_menu()
                return True
        
        return False
    
    def update(self, delta_time: float) -> None:
        """ウィンドウ更新
        
        Args:
            delta_time: 前フレームからの経過時間
        """
        super().update(delta_time)
        
        # ヘルプウィンドウ固有の更新処理
        # 実装は段階的に追加
    
    def render(self, surface: pygame.Surface) -> None:
        """ウィンドウ描画
        
        Args:
            surface: 描画対象サーフェス
        """
        super().render(surface)
        
        # ヘルプウィンドウ固有の描画処理
        # 実装は段階的に追加
        
        # デバッグ情報を表示
        font = pygame.font.Font(None, 24)
        text = font.render("ヘルプシステム", True, (255, 255, 255))
        surface.blit(text, (self.rect.x + 10, self.rect.y + 10))
        
        if self.current_category:
            category_text = font.render(f"カテゴリ: {self.current_category.value}", True, (200, 200, 200))
            surface.blit(category_text, (self.rect.x + 10, self.rect.y + 40))
    
    def close(self) -> None:
        """ウィンドウを閉じる"""
        if self.on_close_callback:
            self.on_close_callback()
        
        if self.window_manager:
            self.window_manager.hide_window(self)
        
        logger.info("HelpWindowを閉じました")