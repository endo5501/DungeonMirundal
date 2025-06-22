"""施設統合システムのテスト"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from src.overworld.overworld_manager import OverworldManager
from src.overworld.base_facility import FacilityManager, BaseFacility, FacilityType
from src.character.party import Party


class MockFacility(BaseFacility):
    """テスト用モック施設"""
    
    def __init__(self, facility_id: str = "test_facility"):
        super().__init__(facility_id, FacilityType.INN, "facility.inn")
        self.enter_called = False
        self.exit_called = False
        self.setup_menu_called = False
    
    def _setup_menu_items(self, menu):
        """メニュー項目設定"""
        self.setup_menu_called = True
    
    def _on_enter(self):
        """入場時処理"""
        self.enter_called = True
    
    def _on_exit(self):
        """退場時処理"""
        self.exit_called = True


class TestFacilityIntegration:
    """施設統合システムのテストクラス"""
    
    def setup_method(self):
        """各テストメソッドの前に実行"""
        with patch('src.overworld.overworld_manager.ui_manager'):
            self.overworld_manager = OverworldManager()
        
        # モックパーティの作成
        self.test_party = Mock(spec=Party)
        self.test_party.name = "テストパーティ"
        
        # モック施設とマネージャーの作成
        self.mock_facility = MockFacility("test_inn")
        self.facility_manager = FacilityManager()
        self.facility_manager.register_facility(self.mock_facility)
        
        # オーバーワールドマネージャーに施設マネージャーを設定
        self.overworld_manager.facility_manager = self.facility_manager
        self.facility_manager.set_facility_exit_callback(self.overworld_manager.on_facility_exit)
        
        # 地上部をアクティブにする
        self.overworld_manager.is_active = True
        self.overworld_manager.current_party = self.test_party
    
    def test_enter_facility_hides_main_menu(self):
        """施設入場時にメインメニューが隠されるテスト"""
        with patch('src.overworld.overworld_manager.ui_manager') as mock_ui:
            # メインメニューを設定
            self.overworld_manager.main_menu = Mock()
            self.overworld_manager.main_menu.element_id = "main_menu"
            
            # 施設に入る
            self.overworld_manager._enter_facility("test_inn")
            
            # メインメニューが隠されることを確認
            mock_ui.hide_element.assert_called_with("main_menu")
            
            # 施設が正しく入場状態になることを確認
            assert self.mock_facility.is_active == True
            assert self.mock_facility.enter_called == True
    
    def test_facility_exit_callback_shows_correct_menu(self):
        """施設退場時に正しいメニューが表示されるテスト"""
        with patch('src.overworld.overworld_manager.ui_manager') as mock_ui:
            # メインメニューを設定
            self.overworld_manager.main_menu = Mock()
            self.overworld_manager.main_menu.element_id = "main_menu"
            
            # 設定画面が非アクティブの状態で施設退場
            self.overworld_manager.settings_menu_active = False
            self.overworld_manager.on_facility_exit()
            
            # メインメニューが表示されることを確認
            mock_ui.show_element.assert_called_with("main_menu")
    
    def test_facility_exit_callback_shows_settings_when_active(self):
        """設定画面がアクティブ時に施設退場で設定画面が表示されるテスト"""
        with patch('src.overworld.overworld_manager.ui_manager') as mock_ui:
            # 設定メニューを設定
            self.overworld_manager.location_menu = Mock()
            self.overworld_manager.location_menu.element_id = "settings_menu"
            self.overworld_manager.settings_menu_active = True
            
            # 施設退場
            self.overworld_manager.on_facility_exit()
            
            # 設定メニューが表示されることを確認
            mock_ui.show_element.assert_called_with("settings_menu")
    
    def test_facility_manager_calls_exit_callback(self):
        """FacilityManagerが退場コールバックを正しく呼び出すテスト"""
        # 施設に入る
        self.facility_manager.enter_facility("test_inn", self.test_party)
        assert self.facility_manager.current_facility == "test_inn"
        
        # オーバーワールドマネージャーのon_facility_exitがモック呼び出しになるように設定
        callback_called = False
        def mock_callback():
            nonlocal callback_called
            callback_called = True
        
        self.facility_manager.set_facility_exit_callback(mock_callback)
        
        # 施設から出る
        result = self.facility_manager.exit_current_facility()
        
        # 退場が成功してコールバックが呼ばれることを確認
        assert result == True
        assert callback_called == True
        assert self.facility_manager.current_facility is None
        assert self.mock_facility.exit_called == True
    
    def test_enter_facility_error_handling(self):
        """存在しない施設入場時のエラーハンドリングテスト"""
        with patch.object(self.overworld_manager, '_show_error_dialog') as mock_error:
            # 存在しない施設に入ろうとする
            self.overworld_manager._enter_facility("nonexistent_facility")
            
            # エラーダイアログが表示されることを確認
            mock_error.assert_called_once()
    
    def test_facility_exit_when_inactive_does_nothing(self):
        """地上部が非アクティブ時に施設退場処理が何もしないテスト"""
        with patch('src.overworld.overworld_manager.ui_manager') as mock_ui:
            # 地上部を非アクティブにする
            self.overworld_manager.is_active = False
            
            # 施設退場
            self.overworld_manager.on_facility_exit()
            
            # UIの操作が呼ばれないことを確認
            mock_ui.show_element.assert_not_called()
    
    def test_facility_exit_without_menus_does_nothing(self):
        """メニューが設定されていない状態での施設退場テスト"""
        with patch('src.overworld.overworld_manager.ui_manager') as mock_ui:
            # メニューを設定しない
            self.overworld_manager.main_menu = None
            self.overworld_manager.location_menu = None
            self.overworld_manager.settings_menu_active = False
            
            # 施設退場
            self.overworld_manager.on_facility_exit()
            
            # UIの操作が呼ばれないことを確認
            mock_ui.show_element.assert_not_called()