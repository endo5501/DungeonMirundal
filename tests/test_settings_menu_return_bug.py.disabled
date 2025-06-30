"""設定メニューの戻るボタンが機能しない問題を検証するテスト"""

import pytest
from unittest.mock import Mock, MagicMock, patch
from src.ui.settings_ui import SettingsUI, SettingsCategory
from src.ui.base_ui_pygame import UIMenu


class TestSettingsMenuReturnBug:
    """設定メニューの戻るボタン問題を検証するテスト"""
    
    @pytest.fixture
    def mock_ui_manager(self):
        """モックUIマネージャー"""
        mock = Mock()
        mock.add_menu = Mock()
        mock.show_menu = Mock()
        mock.hide_menu = Mock()
        mock.hide_all = Mock()
        mock.menus = {}
        return mock
    
    @pytest.fixture
    def mock_config_manager(self):
        """モック設定マネージャー"""
        mock = Mock()
        mock.get_text = Mock(side_effect=lambda key: f"text_{key}")
        mock.load_config = Mock(return_value={})
        return mock
    
    @pytest.fixture
    def settings_ui(self, mock_ui_manager, mock_config_manager):
        """テスト用設定UI"""
        # グローバルなui_managerとconfig_managerをモックに置き換え
        import src.ui.settings_ui
        original_ui_manager = getattr(src.ui.settings_ui, 'ui_manager', None)
        original_config_manager = getattr(src.ui.settings_ui, 'config_manager', None)
        
        # モックを設定
        src.ui.settings_ui.ui_manager = mock_ui_manager
        src.ui.settings_ui.config_manager = mock_config_manager
        
        try:
            settings_ui = SettingsUI()
            yield settings_ui
        finally:
            # 元に戻す
            src.ui.settings_ui.ui_manager = original_ui_manager  
            src.ui.settings_ui.config_manager = original_config_manager
    
    def test_gameplay_settings_return_button_fails(self, settings_ui, mock_ui_manager):
        """ゲームプレイ設定の戻るボタンが失敗することを確認"""
        # 設定メインメニューを表示
        settings_ui.show_settings_menu()
        
        # メインメニューが表示されたことを確認
        assert mock_ui_manager.add_menu.called
        assert mock_ui_manager.show_menu.called
        main_menu_calls = [call for call in mock_ui_manager.add_menu.call_args_list 
                          if call[0][0].menu_id == "settings_main"]
        assert len(main_menu_calls) == 1
        
        # ゲームプレイ設定を開く
        settings_ui._show_gameplay_settings()
        
        # ゲームプレイメニューが表示されたことを確認
        gameplay_menu_calls = [call for call in mock_ui_manager.add_menu.call_args_list 
                              if call[0][0].menu_id == "gameplay_settings"]
        assert len(gameplay_menu_calls) == 1
        
        # ゲームプレイメニューの戻るボタンのコマンドを取得
        gameplay_menu = gameplay_menu_calls[0][0][0]
        back_item = None
        for element in gameplay_menu.elements:
            if hasattr(element, 'text') and ("back" in element.text.lower() or "戻る" in element.text):
                back_item = element
                break
        
        assert back_item is not None, "戻るボタンが見つかりません"
        
        # 戻るボタンのコマンドを実行
        back_command = back_item.on_click
        
        # UIマネージャーの状態をリセット
        mock_ui_manager.reset_mock()
        
        # 戻るボタンを実行
        back_command()
        
        # メインメニューが再表示されることを確認
        # 現在の実装では、_back_to_main_settingsはshow_settings_menuを呼び出すので
        # add_menuとshow_menuが呼ばれるはず
        assert mock_ui_manager.add_menu.called, "メインメニューが再追加されていません"
        assert mock_ui_manager.show_menu.called, "メインメニューが再表示されていません"
    
    def test_all_category_return_buttons(self, settings_ui, mock_ui_manager):
        """すべてのカテゴリの戻るボタンをテスト"""
        categories = [
            (SettingsCategory.GAMEPLAY, "_show_gameplay_settings"),
            (SettingsCategory.CONTROLS, "_show_controls_settings"),
            (SettingsCategory.AUDIO, "_show_audio_settings"),
            (SettingsCategory.GRAPHICS, "_show_graphics_settings"),
            (SettingsCategory.ACCESSIBILITY, "_show_accessibility_settings"),
        ]
        
        for category, method_name in categories:
            # リセット
            mock_ui_manager.reset_mock()
            
            # カテゴリ設定を表示
            method = getattr(settings_ui, method_name)
            method()
            
            # メニューが追加されたことを確認
            assert mock_ui_manager.add_menu.called, f"{category.value}メニューが追加されていません"
            
            # 戻るボタンの動作を確認
            menu_calls = mock_ui_manager.add_menu.call_args_list
            if menu_calls:
                menu = menu_calls[-1][0][0]  # 最後に追加されたメニュー
                
                # 戻るボタンを探す
                back_item = None
                for element in menu.elements:
                    if hasattr(element, 'text') and ("back" in element.text.lower() or "戻る" in element.text):
                        back_item = element
                        break
                
                assert back_item is not None, f"{category.value}の戻るボタンが見つかりません"
                
                # コマンドが_back_to_main_settingsであることを確認
                assert back_item.on_click == settings_ui._back_to_main_settings, \
                    f"{category.value}の戻るボタンが正しいコマンドを持っていません"
    
    def test_keybind_settings_return_to_controls(self, settings_ui, mock_ui_manager):
        """キーバインド設定の戻るボタンがコントロール設定に戻ることを確認"""
        # コントロール設定を表示
        settings_ui._show_controls_settings()
        
        # キーバインド設定を表示
        mock_ui_manager.reset_mock()
        settings_ui._show_keybind_settings()
        
        # キーバインドメニューが表示されたことを確認
        assert mock_ui_manager.add_menu.called
        keybind_menu_calls = [call for call in mock_ui_manager.add_menu.call_args_list
                             if call[0][0].menu_id == "keybind_settings"]
        assert len(keybind_menu_calls) == 1
        
        # 戻るボタンを探す
        keybind_menu = keybind_menu_calls[0][0][0]
        back_item = None
        for element in keybind_menu.elements:
            if hasattr(element, 'text') and ("back" in element.text.lower() or "戻る" in element.text):
                back_item = element
                break
        
        assert back_item is not None, "キーバインド設定の戻るボタンが見つかりません"
        
        # 戻るボタンがコントロール設定に戻ることを確認
        assert back_item.on_click == settings_ui._show_controls_settings, \
            "キーバインド設定の戻るボタンがコントロール設定に戻りません"
    
    def test_dialog_close_behavior(self, settings_ui, mock_ui_manager):
        """ダイアログの閉じる動作をテスト"""
        # _close_dialogメソッドの動作を確認
        settings_ui._close_dialog()
        
        # hide_allが呼ばれることを確認
        assert mock_ui_manager.hide_all.called, "ダイアログを閉じる際にhide_allが呼ばれていません"
    
    def test_menu_persistence_issue(self, settings_ui, mock_ui_manager):
        """メニューの永続性の問題を確認"""
        # メインメニューを表示
        settings_ui.show_settings_menu()
        initial_add_menu_count = mock_ui_manager.add_menu.call_count
        
        # ゲームプレイ設定を開く
        settings_ui._show_gameplay_settings()
        
        # メインメニューに戻る
        settings_ui._back_to_main_settings()
        
        # add_menuが再度呼ばれていることを確認
        # 正しい実装では、メニューを再度追加する必要がある
        final_add_menu_count = mock_ui_manager.add_menu.call_count
        assert final_add_menu_count > initial_add_menu_count + 1, \
            "メインメニューに戻る際にメニューが再追加されていません"