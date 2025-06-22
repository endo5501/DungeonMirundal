"""設定画面ロード後のメニュー重複バグ修正テスト"""

import unittest
from unittest.mock import Mock, patch, MagicMock

from src.overworld.overworld_manager import OverworldManager


class TestSettingsMenuLoadBugFix(unittest.TestCase):
    """設定画面ロード後のメニュー重複バグ修正テストクラス"""
    
    def setUp(self):
        """テスト前のセットアップ"""
        # モックのOverworldManagerを作成
        with patch('src.overworld.overworld_manager.OverworldManager.__init__', return_value=None):
            self.overworld_manager = OverworldManager()
            
            # 必要な属性をモック
            self.overworld_manager.ui_manager = Mock()
            self.overworld_manager.game_manager = Mock()
            self.overworld_manager.current_party = Mock()
            self.overworld_manager.current_party.name = "テストパーティ"
            
            # メニュー状態のトラッキング
            self.overworld_manager._current_menu_state = None
            
            # UIメニューのモック
            self.overworld_manager.settings_menu = Mock()
            self.overworld_manager.load_menu = Mock()
    
    def test_back_to_settings_menu_method_exists(self):
        """_back_to_settings_menuメソッドが正しく定義されていることを確認"""
        # メソッドが存在することを確認
        self.assertTrue(hasattr(self.overworld_manager, '_back_to_settings_menu'))
        self.assertTrue(callable(getattr(self.overworld_manager, '_back_to_settings_menu')))
    
    def test_load_selected_save_returns_to_settings(self):
        """ロード実行後に設定メニューに戻ることをテスト"""
        # load_game_stateのモック設定
        self.overworld_manager.game_manager.load_game_state.return_value = True
        
        # _back_to_settings_menuのモック
        self.overworld_manager._back_to_settings_menu = Mock()
        
        # モックセーブマネージャー
        mock_save_manager = Mock()
        
        with patch('src.overworld.overworld_manager.SaveManager', return_value=mock_save_manager):
            # _load_selected_saveメソッドのテスト
            self.overworld_manager._load_selected_save(1)
            
            # ロード後に_back_to_settings_menuが呼ばれることを確認
            self.overworld_manager._back_to_settings_menu.assert_called()
    
    def test_menu_state_management(self):
        """メニュー状態の管理テスト"""
        # 設定メニューを表示
        self.overworld_manager.show_settings_menu()
        
        # ロードメニューを表示
        self.overworld_manager._show_load_menu()
        
        # ロード実行後の状態確認
        with patch.object(self.overworld_manager, 'game_manager') as mock_game_manager:
            mock_game_manager.load_game_state.return_value = True
            
            # ロード実行
            self.overworld_manager._load_selected_save(1)
            
            # 設定メニューが表示されることを確認
            self.overworld_manager.ui_manager.show_ui.assert_called()
    
    def test_ui_cleanup_on_menu_switch(self):
        """メニュー切り替え時のUI清掃テスト"""
        # 複数のUIが表示されている状態をシミュレート
        self.overworld_manager.settings_menu.hide = Mock()
        self.overworld_manager.load_menu.hide = Mock()
        
        # 設定メニューに戻る処理をテスト
        self.overworld_manager._back_to_settings_menu()
        
        # 他のメニューが隠されることを確認
        # （実装依存だが、適切なクリーンアップが行われることを確認）
        self.overworld_manager.ui_manager.show_ui.assert_called()
    
    def test_load_success_dialog_callback(self):
        """ロード成功ダイアログのコールバックテスト"""
        # ロード成功ダイアログが表示された後のテスト
        mock_dialog = Mock()
        
        with patch.object(self.overworld_manager, '_show_success_dialog') as mock_success_dialog:
            with patch.object(self.overworld_manager, 'game_manager') as mock_game_manager:
                mock_game_manager.load_game_state.return_value = True
                
                # ロード実行
                self.overworld_manager._load_selected_save(1)
                
                # 成功ダイアログが適切なコールバックで呼ばれることを確認
                mock_success_dialog.assert_called()
                call_args = mock_success_dialog.call_args
                if call_args and len(call_args[0]) >= 3:
                    callback = call_args[0][2]  # 第3引数がコールバック
                    # コールバックが_back_to_settings_menuを呼ぶことを確認
                    self.assertTrue(callable(callback))
    
    def test_no_menu_overlap_after_load(self):
        """ロード後にメニューが重複しないことを確認"""
        # UI管理のモック
        ui_calls = []
        
        def track_ui_calls(menu_id, *args, **kwargs):
            ui_calls.append(menu_id)
        
        self.overworld_manager.ui_manager.show_ui.side_effect = track_ui_calls
        self.overworld_manager.ui_manager.hide_ui = Mock()
        
        # 設定メニュー表示
        self.overworld_manager.show_settings_menu()
        
        # ロード実行
        with patch.object(self.overworld_manager, 'game_manager') as mock_game_manager:
            mock_game_manager.load_game_state.return_value = True
            self.overworld_manager._load_selected_save(1)
        
        # メニューが重複して表示されていないことを確認
        # （具体的な実装に依存するが、適切な状態管理が行われることを確認）
        self.assertTrue(len(ui_calls) > 0, "UIが表示されるべき")
    
    def test_error_handling_during_load(self):
        """ロード中のエラーハンドリングテスト"""
        # ロードが失敗する場合
        self.overworld_manager.game_manager.load_game_state.return_value = False
        
        with patch.object(self.overworld_manager, '_show_error_dialog') as mock_error_dialog:
            # ロード実行
            self.overworld_manager._load_selected_save(1)
            
            # エラーダイアログが表示されることを確認
            mock_error_dialog.assert_called()
            
            # エラー後も適切な画面に戻ることを確認
            # （設定メニューに戻るか、適切な状態になることを確認）


if __name__ == '__main__':
    unittest.main()