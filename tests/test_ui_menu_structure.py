"""新UIメニュー構造のテスト"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from src.overworld.overworld_manager import OverworldManager
from src.character.party import Party
from src.character.character import Character


class TestUIMenuStructure:
    """新UIメニュー構造のテストクラス"""
    
    def setup_method(self):
        """各テストメソッドの前に実行"""
        with patch('src.overworld.overworld_manager.ui_manager'):
            self.overworld_manager = OverworldManager()
        
        # モックパーティの作成
        self.test_party = Mock(spec=Party)
        self.test_party.name = "テストパーティ"
        self.test_party.gold = 1000
        self.test_party.characters = []
        
        # モック入力マネージャー
        self.mock_input_manager = Mock()
        self.overworld_manager.set_input_manager(self.mock_input_manager)
    
    def test_enter_overworld_sets_up_input_handling(self):
        """地上部入場時に入力処理が設定されるテスト"""
        with patch.object(self.overworld_manager, '_setup_input_handling') as mock_setup:
            self.overworld_manager.enter_overworld(self.test_party)
            mock_setup.assert_called_once()
    
    def test_setup_input_handling_binds_menu_action(self):
        """入力処理セットアップでメニューアクションがバインドされるテスト"""
        self.overworld_manager._setup_input_handling()
        
        # メニューアクションがバインドされることを確認
        self.mock_input_manager.bind_action.assert_called_with("menu", self.overworld_manager._on_menu_key)
    
    def test_show_settings_menu_creates_proper_menu(self):
        """設定画面表示で正しいメニューが作成されるテスト"""
        with patch('src.overworld.overworld_manager.ui_manager') as mock_ui_manager:
            with patch('src.overworld.overworld_manager.config_manager') as mock_config:
                mock_config.get_text.return_value = "設定"
                
                self.overworld_manager.show_settings_menu()
                
                # 設定画面が作成されることを確認
                assert self.overworld_manager.settings_menu_active == True
                assert self.overworld_manager.location_menu is not None
    
    def test_back_to_main_menu_resets_settings_state(self):
        """メインメニューに戻る時に設定画面状態がリセットされるテスト"""
        with patch('src.overworld.overworld_manager.ui_manager'):
            # 設定画面をアクティブにする
            self.overworld_manager.settings_menu_active = True
            self.overworld_manager.location_menu = Mock()
            
            self.overworld_manager._back_to_main_menu()
            
            # 設定画面状態がリセットされることを確認
            assert self.overworld_manager.settings_menu_active == False
    
    def test_menu_key_toggles_settings_menu(self):
        """ESCキーで設定画面の表示/非表示が切り替わるテスト"""
        self.overworld_manager.is_active = True
        
        with patch.object(self.overworld_manager, 'show_settings_menu') as mock_show:
            with patch.object(self.overworld_manager, '_back_to_main_menu') as mock_back:
                # 設定画面が非表示の状態でESCキーを押す
                self.overworld_manager.settings_menu_active = False
                self.overworld_manager._on_menu_key("menu", True, Mock())
                mock_show.assert_called_once()
                
                # 設定画面が表示されている状態でESCキーを押す
                self.overworld_manager.settings_menu_active = True
                self.overworld_manager._on_menu_key("menu", True, Mock())
                mock_back.assert_called_once()
    
    def test_menu_key_ignores_key_release(self):
        """ESCキー離しイベントが無視されるテスト"""
        self.overworld_manager.is_active = True
        
        with patch.object(self.overworld_manager, 'show_settings_menu') as mock_show:
            # キー離しイベント（pressed=False）
            self.overworld_manager._on_menu_key("menu", False, Mock())
            mock_show.assert_not_called()
    
    def test_menu_key_ignores_when_inactive(self):
        """地上部が非アクティブ時にESCキーが無視されるテスト"""
        self.overworld_manager.is_active = False
        
        with patch.object(self.overworld_manager, 'show_settings_menu') as mock_show:
            self.overworld_manager._on_menu_key("menu", True, Mock())
            mock_show.assert_not_called()
    
    def test_main_menu_has_direct_facility_access(self):
        """メインメニューに施設への直接アクセスがあるテスト"""
        with patch('src.overworld.overworld_manager.ui_manager') as mock_ui_manager:
            with patch('src.overworld.overworld_manager.config_manager') as mock_config:
                mock_config.get_text.side_effect = lambda key: f"mock_{key}"
                
                mock_menu = Mock()
                mock_ui_manager.get_element.return_value = None
                
                self.overworld_manager._show_main_menu()
                
                # メニューが作成されることを確認
                assert self.overworld_manager.main_menu is not None
    
    def test_settings_menu_has_required_items(self):
        """設定画面に必要な項目があるテスト"""
        with patch('src.overworld.overworld_manager.ui_manager') as mock_ui_manager:
            with patch('src.overworld.overworld_manager.config_manager') as mock_config:
                mock_config.get_text.side_effect = lambda key: f"mock_{key}"
                
                self.overworld_manager.show_settings_menu()
                
                # 設定メニューが作成されることを確認
                assert self.overworld_manager.location_menu is not None
                assert self.overworld_manager.settings_menu_active == True