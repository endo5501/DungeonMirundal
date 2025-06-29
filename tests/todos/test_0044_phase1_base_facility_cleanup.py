"""0044 Phase 1: BaseFacility UIMenuレガシー部分削除テスト"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import pygame
from typing import Dict, Any

from src.overworld.base_facility import BaseFacility, FacilityType


class MockBaseFacility(BaseFacility):
    """テスト用の具象BaseFacility"""
    
    def __init__(self):
        super().__init__("test_facility", FacilityType.GUILD, "test.facility.name")
        
    def get_facility_name(self) -> str:
        return "Test Facility"
        
    def show_main_menu(self) -> None:
        pass
        
    def _create_main_menu(self):
        pass
        
    def _on_enter(self) -> None:
        """施設に入ったときの処理"""
        pass
        
    def _on_exit(self) -> None:
        """施設から出るときの処理"""
        pass


class TestBaseFacilityUIMenuCleanup:
    """BaseFacilityのUIMenuレガシー部分削除テスト"""
    
    def setup_method(self):
        """テストのセットアップ"""
        pygame.init()
        self.facility = MockBaseFacility()
        
    def teardown_method(self):
        """テストのクリーンアップ"""
        pygame.quit()
    
    def test_base_facility_no_uimenu_import(self):
        """UIMenuがインポートされていないことを確認"""
        # BaseFacilityモジュールをインポート
        import src.overworld.base_facility as bf_module
        
        # UIMenuがインポートされていないことを確認
        assert not hasattr(bf_module, 'UIMenu'), "UIMenu should not be imported"
        
        # ui_managerもインポートされていないことを確認
        assert not hasattr(bf_module, 'ui_manager'), "ui_manager should not be imported"
    
    def test_show_submenu_method_removed(self):
        """show_submenuメソッドが削除されていることを確認"""
        # show_submenuメソッドが存在しないことを確認
        assert not hasattr(self.facility, 'show_submenu'), \
            "show_submenu method should be removed"
    
    def test_hide_menu_safe_method_removed(self):
        """_hide_menu_safeメソッドが削除されていることを確認"""
        # _hide_menu_safeメソッドが存在しないことを確認
        assert not hasattr(self.facility, '_hide_menu_safe'), \
            "_hide_menu_safe method should be removed"
    
    def test_show_menu_safe_method_removed(self):
        """_show_menu_safeメソッドが削除されていることを確認"""
        # _show_menu_safeメソッドが存在しないことを確認
        assert not hasattr(self.facility, '_show_menu_safe'), \
            "_show_menu_safe method should be removed"
    
    def test_get_effective_ui_manager_uses_menu_stack_manager(self):
        """_get_effective_ui_managerがmenu_stack_managerのみを使用することを確認"""
        # menu_stack_managerが設定されている場合
        mock_manager = Mock()
        mock_manager.ui_manager = Mock()
        self.facility.menu_stack_manager = mock_manager
        
        result = self.facility._get_effective_ui_manager()
        assert result == mock_manager.ui_manager
        
        # menu_stack_managerがNoneの場合
        self.facility.menu_stack_manager = None
        result = self.facility._get_effective_ui_manager()
        assert result is None
    
    def test_dialog_methods_still_work(self):
        """ダイアログメソッドが引き続き動作することを確認"""
        # dialog_templateをモック
        self.facility.dialog_template = Mock()
        self.facility.dialog_template.create_information_dialog.return_value = Mock()
        self.facility.dialog_template.show_dialog.return_value = True
        
        # 情報ダイアログが動作することを確認
        result = self.facility.show_information_dialog("Test", "Message")
        assert result is True
        
        # エラーダイアログが動作することを確認
        self.facility.dialog_template.create_error_dialog.return_value = Mock()
        result = self.facility.show_error_dialog("Error", "Error message")
        assert result is True
    
    def test_window_manager_integration_works(self):
        """WindowManager統合が正常に動作することを確認"""
        # WindowManagerプロパティが存在することを確認
        assert hasattr(self.facility, 'window_manager')
        assert self.facility.window_manager is not None
        
        # WindowManagerのメソッドが利用可能であることを確認
        assert hasattr(self.facility.window_manager, 'show_window')
        assert hasattr(self.facility.window_manager, 'close_window')
    
    def test_no_legacy_comments(self):
        """レガシーコメントが削除されていることを確認"""
        # BaseFacilityのソースコードを読み込む
        import inspect
        source = inspect.getsource(BaseFacility)
        
        # レガシー関連のコメントが存在しないことを確認
        assert "レガシー" not in source, "Legacy comments should be removed"
        assert "UIMenu" not in source, "UIMenu references in comments should be removed"