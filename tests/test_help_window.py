"""HelpWindow テストケース

t-wada式TDD：
1. Red: 失敗するテストを書く
2. Green: テストを通すための最小限の実装
3. Refactor: Fowlerリファクタリングパターンでコードを改善
"""

import pytest
import pygame
from unittest.mock import Mock, patch, MagicMock
from enum import Enum

from src.ui.window_system.help_window import HelpWindow
from src.ui.window_system.help_enums import HelpCategory, HelpContext
from src.ui.window_system.window import Window
from src.ui.window_system.menu_window import MenuWindow
from src.ui.window_system.dialog_window import DialogWindow


class TestHelpWindow:
    """HelpWindow テストクラス
    
    テスト戦略：
    - Window System 基本機能のテスト
    - ヘルプシステム特有の機能のテスト
    - カテゴリ別ヘルプ表示機能のテスト
    - コンテキストヘルプ機能のテスト
    - エラーハンドリングのテスト
    """
    
    def setup_method(self):
        """テスト前セットアップ"""
        pygame.init()
        self.screen = pygame.display.set_mode((800, 600))
        
        # モックオブジェクトの作成
        self.mock_window_manager = Mock()
    
    def test_help_window_creation_success(self):
        """HelpWindowクラスが正常に作成できることを確認（Green段階）"""
        # HelpWindowが正常に作成できることを確認
        help_window = HelpWindow(
            window_manager=self.mock_window_manager,
            rect=pygame.Rect(100, 100, 600, 500)
        )
        
        # Windowクラスを継承していることを確認
        assert isinstance(help_window, Window)
        assert help_window.window_manager == self.mock_window_manager
    
    def test_help_window_inherits_from_window(self):
        """HelpWindowがWindowクラスを継承することを確認"""
        help_window = HelpWindow(
            window_manager=self.mock_window_manager,
            rect=pygame.Rect(100, 100, 600, 500)
        )
        assert isinstance(help_window, Window)
    
    def test_help_window_has_help_categories(self):
        """HelpWindowがヘルプカテゴリを持つことを確認"""
        help_window = HelpWindow(
            window_manager=self.mock_window_manager,
            rect=pygame.Rect(100, 100, 600, 500)
        )
        
        # ヘルプカテゴリプロパティの存在確認
        assert hasattr(help_window, 'help_categories')
        assert help_window.help_categories is not None
        assert len(help_window.help_categories) > 0
    
    def test_help_window_show_main_help_menu(self):
        """show_main_help_menu メソッドの動作を確認"""
        help_window = HelpWindow(
            window_manager=self.mock_window_manager,
            rect=pygame.Rect(100, 100, 600, 500)
        )
        
        # メインヘルプメニューの表示
        help_window.show_main_help_menu()
        
        # ウィンドウマネージャーの呼び出し確認
        self.mock_window_manager.show_window.assert_called_once()
    
    def test_help_window_show_category_help(self):
        """show_category_help メソッドの動作を確認"""
        help_window = HelpWindow(
            window_manager=self.mock_window_manager,
            rect=pygame.Rect(100, 100, 600, 500)
        )
        
        # カテゴリ別ヘルプ表示
        help_window.show_category_help("basic_controls")
        
        # 現在カテゴリが設定されていることを確認
        assert hasattr(help_window, 'current_category')
        assert help_window.current_category == HelpCategory.BASIC_CONTROLS
    
    def test_help_window_show_context_help(self):
        """show_context_help メソッドの動作を確認"""
        
        
        help_window = HelpWindow(
            window_manager=self.mock_window_manager,
            rect=pygame.Rect(100, 100, 600, 500)
        )
        
        # コンテキストヘルプ表示
        help_window.show_context_help("combat")
        
        # コンテキストが設定されていることを確認
        assert hasattr(help_window, 'current_context')
        assert help_window.current_context == HelpContext.COMBAT
    
    def test_help_window_quick_reference(self):
        """クイックリファレンス機能のテスト"""
        
        
        help_window = HelpWindow(
            window_manager=self.mock_window_manager,
            rect=pygame.Rect(100, 100, 600, 500)
        )
        
        # クイックリファレンス表示
        help_window.show_quick_reference()
        
        # クイックリファレンスの内容が取得できることを確認
        reference_content = help_window.get_quick_reference_content()
        assert isinstance(reference_content, dict)
    
    def test_help_window_controls_guide(self):
        """操作ガイド機能のテスト"""
        
        
        help_window = HelpWindow(
            window_manager=self.mock_window_manager,
            rect=pygame.Rect(100, 100, 600, 500)
        )
        
        # 操作ガイド表示
        help_window.show_controls_guide()
        
        # 操作ガイドの内容が取得できることを確認
        controls_content = help_window.get_controls_guide_content()
        assert isinstance(controls_content, dict)
    
    def test_help_window_first_time_help(self):
        """初回起動時ヘルプ機能のテスト"""
        
        
        help_window = HelpWindow(
            window_manager=self.mock_window_manager,
            rect=pygame.Rect(100, 100, 600, 500)
        )
        
        # 初回起動時ヘルプ表示
        help_window.show_first_time_help()
        
        # 初回ヘルプフラグが適切に管理されることを確認
        assert hasattr(help_window, 'first_time_shown')
        assert help_window.first_time_shown is True
    
    def test_help_window_error_handling(self):
        """エラーハンドリングのテスト"""
        
        
        help_window = HelpWindow(
            window_manager=self.mock_window_manager,
            rect=pygame.Rect(100, 100, 600, 500)
        )
        
        # 無効なカテゴリでのエラーハンドリング
        help_window.show_category_help("invalid_category")
        # エラーが発生せずに適切に処理されることを確認
        
        # 無効なコンテキストでのエラーハンドリング
        help_window.show_context_help("invalid_context")
        # エラーが発生せずに適切に処理されることを確認
    
    def teardown_method(self):
        """テスト後クリーンアップ"""
        pygame.quit()


class TestHelpWindowIntegration:
    """HelpWindow 統合テスト"""
    
    def setup_method(self):
        """統合テスト用セットアップ"""
        pygame.init()
        self.screen = pygame.display.set_mode((800, 600))
        
        # より実際に近いモックオブジェクト
        self.mock_window_manager = Mock()
        
    def test_help_window_with_menu_window_integration(self):
        """MenuWindowとの統合テスト"""
        
        
        # MenuWindowからHelpWindowへの遷移をテスト
        help_window = HelpWindow(
            window_manager=self.mock_window_manager,
            rect=pygame.Rect(100, 100, 600, 500)
        )
        
        # メニューからの遷移を模擬
        help_window.show_main_help_menu()
        
        # 適切にウィンドウが表示されることを確認
        self.mock_window_manager.show_window.assert_called()
    
    def test_help_window_with_dialog_window_integration(self):
        """DialogWindowとの統合テスト"""
        
        
        # DialogWindowとの連携をテスト
        help_window = HelpWindow(
            window_manager=self.mock_window_manager,
            rect=pygame.Rect(100, 100, 600, 500)
        )
        
        # 詳細ヘルプダイアログの表示を模擬
        help_window.show_detailed_help_dialog("基本操作について")
        
        # ダイアログウィンドウが作成されることを確認
        # （実際の実装で検証）
    
    def teardown_method(self):
        """統合テスト後クリーンアップ"""
        pygame.quit()


class TestHelpWindowRefactoring:
    """HelpWindow リファクタリングテスト（Fowlerパターン）"""
    
    def setup_method(self):
        """リファクタリングテスト用セットアップ"""
        pygame.init()
        self.screen = pygame.display.set_mode((800, 600))
        
        # モックオブジェクトの作成
        self.mock_window_manager = Mock()
        
    def teardown_method(self):
        """リファクタリングテスト後クリーンアップ"""
        pygame.quit()
    
    def test_extract_help_content_manager_class(self):
        """Extract Class: ヘルプコンテンツ管理クラスの抽出"""
        help_window = HelpWindow(
            window_manager=self.mock_window_manager,
            rect=pygame.Rect(100, 100, 600, 500)
        )
        
        # HelpContentManagerが抽出されていることを確認
        assert hasattr(help_window, 'content_manager')
        assert help_window.content_manager is not None
        
        # コンテンツ取得機能
        categories = help_window.get_help_categories()
        assert isinstance(categories, list)
        assert len(categories) > 0
        
        # カテゴリコンテンツ取得
        content = help_window.get_category_content(HelpCategory.BASIC_CONTROLS)
        assert isinstance(content, dict)
    
    def test_extract_help_display_manager_class(self):
        """Extract Class: ヘルプ表示管理クラスの抽出"""
        help_window = HelpWindow(
            window_manager=self.mock_window_manager,
            rect=pygame.Rect(100, 100, 600, 500)
        )
        
        # HelpDisplayManagerが抽出されていることを確認
        assert hasattr(help_window, 'display_manager')
        assert help_window.display_manager is not None
        
        # 表示フォーマット機能
        formatted_help = help_window.get_formatted_category_help(HelpCategory.BASIC_CONTROLS)
        assert isinstance(formatted_help, dict)
        
        # メニューアイテム生成
        menu_items = help_window.get_help_menu_items()
        assert isinstance(menu_items, list)
    
    def test_extract_context_help_manager_class(self):
        """Extract Class: コンテキストヘルプ管理クラスの抽出"""
        help_window = HelpWindow(
            window_manager=self.mock_window_manager,
            rect=pygame.Rect(100, 100, 600, 500)
        )
        
        # ContextHelpManagerが抽出されていることを確認
        assert hasattr(help_window, 'context_manager')
        assert help_window.context_manager is not None
        
        # コンテキスト設定機能
        help_window.set_help_context(HelpContext.COMBAT)
        
        # コンテキストヘルプ要求機能
        help_window.request_context_help(HelpContext.DUNGEON)
        
        # 初回ヘルプ機能
        help_window.show_first_time_help()
        assert help_window.first_time_shown is True
    
    def test_refactored_method_delegation(self):
        """リファクタリング後のメソッド委譲テスト"""
        help_window = HelpWindow(
            window_manager=self.mock_window_manager,
            rect=pygame.Rect(100, 100, 600, 500)
        )
        
        # コンテンツ管理の委譲
        quick_ref = help_window.get_quick_reference_content()
        assert isinstance(quick_ref, dict)
        
        controls_guide = help_window.get_controls_guide_content()
        assert isinstance(controls_guide, dict)
        
        first_time_content = help_window.get_first_time_help_content()
        assert isinstance(first_time_content, dict)