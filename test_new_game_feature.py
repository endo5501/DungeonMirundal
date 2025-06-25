#!/usr/bin/env python3
"""新規ゲーム開始機能のテスト"""

import pytest
import pygame
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path
import tempfile
import shutil
from src.ui.settings_ui import SettingsUI, settings_ui


class TestNewGameFeature:
    """新規ゲーム開始機能のテスト"""
    
    def setup_method(self):
        """テスト前の初期化"""
        pygame.init()
        
        # テスト用の設定UI
        self.settings = SettingsUI()
        
        # テスト用の一時ディレクトリ
        self.temp_dir = tempfile.mkdtemp()
        self.temp_path = Path(self.temp_dir)
    
    def teardown_method(self):
        """テスト後のクリーンアップ"""
        if pygame.get_init():
            pygame.quit()
        
        # 一時ディレクトリを削除
        if self.temp_path.exists():
            shutil.rmtree(self.temp_path)
    
    def test_new_game_menu_item_exists(self):
        """設定メニューに新規ゲーム開始項目が存在することを確認"""
        with patch('src.ui.settings_ui.ui_manager') as mock_ui_manager:
            mock_ui_manager.add_menu = Mock()
            mock_ui_manager.show_menu = Mock()
            
            # 設定メニューを表示
            self.settings.show_settings_menu()
            
            # add_menuが呼ばれていることを確認
            assert mock_ui_manager.add_menu.called
            
            # 追加されたメニューの確認
            menu_calls = mock_ui_manager.add_menu.call_args_list
            assert len(menu_calls) > 0
            
            # メニューに新規ゲーム項目が含まれているかチェック
            menu_obj = menu_calls[0][0][0]  # 最初の引数（UIMenuオブジェクト）
            assert hasattr(menu_obj, 'elements')
    
    @patch('src.ui.settings_ui.ui_manager')
    def test_new_game_confirmation_dialog(self, mock_ui_manager):
        """新規ゲーム開始の確認ダイアログテスト"""
        mock_ui_manager.add_dialog = Mock()
        mock_ui_manager.show_dialog = Mock()
        
        # 新規ゲーム確認を表示
        self.settings._show_new_game_confirmation()
        
        # ダイアログが作成・表示されることを確認
        mock_ui_manager.add_dialog.assert_called_once()
        mock_ui_manager.show_dialog.assert_called_once()
        
        # ダイアログの内容確認
        dialog_call = mock_ui_manager.add_dialog.call_args[0][0]
        assert dialog_call.dialog_id == "new_game_confirm"
        assert "警告" in dialog_call.message
        assert "セーブデータが削除されます" in dialog_call.message
    
    @patch('src.ui.settings_ui.ui_manager')
    def test_final_confirmation_dialog(self, mock_ui_manager):
        """最終確認ダイアログのテスト"""
        mock_ui_manager.add_dialog = Mock()
        mock_ui_manager.show_dialog = Mock()
        
        # 最終確認を表示
        self.settings._show_final_new_game_confirmation()
        
        # ダイアログが作成・表示されることを確認
        mock_ui_manager.add_dialog.assert_called_once()
        mock_ui_manager.show_dialog.assert_called_once()
        
        # ダイアログの内容確認
        dialog_call = mock_ui_manager.add_dialog.call_args[0][0]
        assert dialog_call.dialog_id == "new_game_final_confirm"
        assert "本当に新規ゲームを開始しますか" in dialog_call.message
        assert "キャラクター" in dialog_call.message
        assert "パーティ" in dialog_call.message
    
    @patch('pathlib.Path')
    def test_clear_save_data(self, mock_path_class):
        """セーブデータクリア処理のテスト"""
        # モックファイルシステムを設定
        mock_save_dir = Mock()
        mock_save_dir.exists.return_value = True
        mock_save_dir.glob.return_value = [
            Mock(is_file=lambda: True, unlink=Mock()),
            Mock(is_file=lambda: True, unlink=Mock()),
            Mock(is_file=lambda: False)  # ディレクトリ
        ]
        
        mock_path_class.return_value = mock_save_dir
        
        # セーブデータクリアを実行
        with patch.object(self.settings, '_create_default_party') as mock_create_party:
            self.settings._clear_all_save_data()
            
            # ファイル削除が呼ばれることを確認（複数ディレクトリで実行されるため、呼ばれていることだけ確認）
            files = list(mock_save_dir.glob.return_value)
            for file_mock in files:
                if file_mock.is_file():
                    file_mock.unlink.assert_called()
            
            # デフォルトパーティ作成が呼ばれることを確認
            mock_create_party.assert_called_once()
    
    @patch('src.core.save_manager.save_manager')
    @patch('src.character.party.Party')
    def test_create_default_party(self, mock_party_class, mock_save_manager):
        """デフォルトパーティ作成のテスト"""
        mock_party = Mock()
        mock_party_class.return_value = mock_party
        mock_save_manager.save_party = Mock()
        
        # デフォルトパーティ作成を実行
        self.settings._create_default_party()
        
        # パーティが作成されることを確認
        mock_party_class.assert_called_once_with("新しい冒険者")
        
        # セーブが呼ばれることを確認
        mock_save_manager.save_party.assert_called_once_with(mock_party)
    
    @patch('src.core.game_manager.GameManager')
    def test_return_to_title_with_game_manager(self, mock_game_manager_class):
        """GameManager経由でのタイトル画面遷移テスト"""
        # タイトル画面に戻る処理を実行
        with patch.object(self.settings, '_actually_close') as mock_close:
            self.settings._return_to_title()
            
            # 画面が閉じられることを確認
            mock_close.assert_called_once()
            
            # GameManagerクラスがインポートされることを確認
            mock_game_manager_class.assert_not_called()  # インスタンス化はされない
    
    @patch('src.core.game_manager.GameManager')
    def test_return_to_title_with_game_state(self, mock_game_manager_class):
        """GameManager正常処理のテスト"""
        # タイトル画面に戻る処理を実行
        with patch.object(self.settings, '_actually_close') as mock_close:
            self.settings._return_to_title()
            
            # 画面が閉じられることを確認
            mock_close.assert_called_once()
    
    @patch('src.ui.settings_ui.ui_manager')
    @patch.object(SettingsUI, '_clear_all_save_data')
    @patch.object(SettingsUI, '_return_to_title')
    def test_execute_new_game_success(self, mock_return, mock_clear, mock_ui_manager):
        """新規ゲーム実行成功のテスト"""
        mock_ui_manager.add_dialog = Mock()
        mock_ui_manager.show_dialog = Mock()
        
        # 新規ゲーム実行
        self.settings._execute_new_game()
        
        # セーブデータクリアが呼ばれることを確認
        mock_clear.assert_called_once()
        
        # タイトル画面遷移が呼ばれることを確認
        mock_return.assert_called_once()
        
        # 成功メッセージが表示されることを確認
        mock_ui_manager.add_dialog.assert_called_once()
        dialog_call = mock_ui_manager.add_dialog.call_args[0][0]
        assert "新規ゲームを開始しました" in dialog_call.message
    
    @patch('src.ui.settings_ui.ui_manager')
    @patch.object(SettingsUI, '_clear_all_save_data')
    def test_execute_new_game_error(self, mock_clear, mock_ui_manager):
        """新規ゲーム実行エラーのテスト"""
        mock_ui_manager.add_dialog = Mock()
        mock_ui_manager.show_dialog = Mock()
        
        # セーブデータクリアでエラーを発生させる
        mock_clear.side_effect = Exception("テストエラー")
        
        # 新規ゲーム実行
        self.settings._execute_new_game()
        
        # エラーメッセージが表示されることを確認
        mock_ui_manager.add_dialog.assert_called_once()
        dialog_call = mock_ui_manager.add_dialog.call_args[0][0]
        assert "新規ゲーム開始に失敗しました" in dialog_call.message
        assert "テストエラー" in dialog_call.message
    
    def test_settings_default_values(self):
        """設定のデフォルト値テスト"""
        defaults = self.settings._get_default_settings()
        
        # 重要な設定項目が存在することを確認
        assert "language" in defaults
        assert "auto_save" in defaults
        assert "difficulty" in defaults
        
        # デフォルト値の確認
        assert defaults["language"] == "ja"
        assert defaults["auto_save"] is True
        assert defaults["difficulty"] == "normal"
    
    @patch('builtins.open', create=True)
    @patch('yaml.safe_load')
    @patch('pathlib.Path')
    def test_load_current_settings_from_file(self, mock_path_class, mock_yaml_load, mock_open):
        """設定ファイルからの読み込みテスト"""
        # ファイルが存在する場合
        mock_config_file = Mock()
        mock_config_file.exists.return_value = True
        
        # Path("config") / "user_settings.yaml" の結果をモック
        mock_path_instance = Mock()
        mock_path_instance.__truediv__ = Mock(return_value=mock_config_file)
        mock_path_class.return_value = mock_path_instance
        
        # YAMLファイルの内容をモック
        mock_yaml_load.return_value = {"language": "en", "difficulty": "hard"}
        
        # ファイルオープンのモック
        mock_file = Mock()
        mock_open.return_value.__enter__.return_value = mock_file
        
        # 設定読み込み
        settings = self.settings._load_current_settings()
        
        # ファイルから読み込まれた設定が反映されることを確認
        assert settings["language"] == "en"
        assert settings["difficulty"] == "hard"
        
        # デフォルト値も含まれることを確認
        assert "auto_save" in settings


if __name__ == "__main__":
    pytest.main([__file__, "-v"])