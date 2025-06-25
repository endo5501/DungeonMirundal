"""設定機能のテスト"""

import pytest
import pygame
import tempfile
import yaml
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path

from src.ui.settings_ui import SettingsUI, SettingsCategory
from src.core.config_manager import config_manager


class TestSettingsFunctionality:
    """設定機能のテスト"""
    
    def setup_method(self):
        """テストセットアップ"""
        pygame.init()
        
        # 一時ディレクトリを作成
        self.temp_dir = tempfile.mkdtemp()
        self.temp_config_path = Path(self.temp_dir)
        
        # SettingsUIインスタンス作成
        self.settings_ui = SettingsUI()
        
        # モック設定
        self.mock_ui_manager = Mock()
        
    def teardown_method(self):
        """テスト後処理"""
        if pygame.get_init():
            pygame.quit()
        
        # 一時ファイルの削除
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_settings_ui_initialization(self):
        """設定UI初期化のテスト"""
        assert self.settings_ui is not None
        assert not self.settings_ui.is_open
        assert self.settings_ui.current_category is None
        assert self.settings_ui.current_settings is not None
        assert isinstance(self.settings_ui.pending_changes, dict)
    
    def test_default_settings_structure(self):
        """デフォルト設定の構造テスト"""
        default_settings = self.settings_ui._get_default_settings()
        
        # 必須キーの存在確認
        required_keys = [
            "language", "auto_save", "difficulty", "battle_speed", "message_speed",
            "controller_enabled", "master_volume", "fullscreen", "feedback_level"
        ]
        
        for key in required_keys:
            assert key in default_settings, f"必須キー '{key}' がデフォルト設定にありません"
        
        # 言語設定のテスト
        assert default_settings["language"] in ["ja", "en"]
        
        # 数値設定の範囲テスト
        assert 0.0 <= default_settings["master_volume"] <= 1.0
        assert 0.0 <= default_settings["analog_deadzone"] <= 1.0
    
    def test_language_switching(self):
        """言語切替機能のテスト"""
        # 初期言語の確認
        current_language = self.settings_ui._get_setting_value("language")
        assert current_language in ["ja", "en"]
        
        # 言語切替のテスト
        new_language = "en" if current_language == "ja" else "ja"
        self.settings_ui._cycle_setting("language", ["ja", "en"])
        
        # 変更が保留されていることを確認
        assert "language" in self.settings_ui.pending_changes
        assert self.settings_ui.pending_changes["language"] == new_language
    
    def test_toggle_setting(self):
        """ON/OFF設定の切り替えテスト"""
        # 初期値を取得
        initial_value = self.settings_ui._get_setting_value("auto_save")
        
        # 切り替え実行
        self.settings_ui._toggle_setting("auto_save")
        
        # 変更が保留されていることを確認
        assert "auto_save" in self.settings_ui.pending_changes
        assert self.settings_ui.pending_changes["auto_save"] == (not initial_value)
    
    def test_cycle_setting(self):
        """循環設定の切り替えテスト"""
        difficulty_options = ["easy", "normal", "hard"]
        
        # 現在の設定を取得
        current_difficulty = self.settings_ui._get_setting_value("difficulty")
        current_index = difficulty_options.index(current_difficulty)
        expected_next = difficulty_options[(current_index + 1) % len(difficulty_options)]
        
        # 循環切り替え実行
        self.settings_ui._cycle_setting("difficulty", difficulty_options)
        
        # 変更が保留されていることを確認
        assert "difficulty" in self.settings_ui.pending_changes
        assert self.settings_ui.pending_changes["difficulty"] == expected_next
    
    def test_adjust_setting(self):
        """数値設定の調整テスト"""
        # 初期値を取得
        initial_volume = self.settings_ui._get_setting_value("master_volume")
        
        # 値を調整（0.1増加、最大1.0、最小0.0）
        self.settings_ui._adjust_setting("master_volume", 0.1, 0.0, 1.0)
        
        # 変更が保留されていることを確認
        assert "master_volume" in self.settings_ui.pending_changes
        expected_value = min(1.0, initial_volume + 0.1)
        assert self.settings_ui.pending_changes["master_volume"] == round(expected_value, 1)
    
    @patch('builtins.open', create=True)
    @patch('yaml.dump')
    @patch('pathlib.Path.mkdir')
    def test_save_settings_to_file(self, mock_mkdir, mock_yaml_dump, mock_open):
        """設定ファイル保存のテスト"""
        # テスト用設定データ
        test_settings = {"language": "en", "auto_save": False}
        self.settings_ui.current_settings = test_settings
        
        # ファイル保存実行
        self.settings_ui._save_settings_to_file()
        
        # ディレクトリ作成の確認
        mock_mkdir.assert_called_once_with(exist_ok=True)
        
        # ファイル書き込みの確認
        mock_open.assert_called_once()
        mock_yaml_dump.assert_called_once_with(
            test_settings, 
            mock_open.return_value.__enter__.return_value,
            default_flow_style=False,
            allow_unicode=True
        )
    
    @patch('builtins.open', create=True)
    @patch('yaml.safe_load')
    @patch('pathlib.Path.exists')
    def test_load_settings_from_file(self, mock_exists, mock_yaml_load, mock_open):
        """設定ファイル読み込みのテスト"""
        # ファイルが存在する場合のテスト
        mock_exists.return_value = True
        test_settings = {"language": "en", "difficulty": "hard"}
        mock_yaml_load.return_value = test_settings
        
        # 新しいSettingsUIインスタンスを作成（読み込みをテスト）
        settings_ui = SettingsUI()
        
        # ファイル読み込みの確認
        mock_open.assert_called()
        mock_yaml_load.assert_called()
        
        # 設定がマージされていることを確認
        assert settings_ui.current_settings["language"] == "en"
        assert settings_ui.current_settings["difficulty"] == "hard"
        # デフォルト値も保持されていることを確認
        assert "auto_save" in settings_ui.current_settings
    
    def test_apply_settings(self):
        """設定適用のテスト"""
        with patch.object(config_manager, 'set_language') as mock_set_language:
            # テスト用設定
            self.settings_ui.current_settings["language"] = "en"
            
            # 設定適用実行
            self.settings_ui._apply_settings()
            
            # 言語設定が適用されることを確認
            mock_set_language.assert_called_once_with("en")
    
    def test_settings_persistence_flow(self):
        """設定の永続化フローのテスト"""
        with patch.object(self.settings_ui, '_save_settings_to_file') as mock_save, \
             patch.object(self.settings_ui, '_apply_settings') as mock_apply, \
             patch.object(self.settings_ui, '_show_message') as mock_message:
            
            # 変更を追加
            self.settings_ui.pending_changes["language"] = "en"
            self.settings_ui.pending_changes["auto_save"] = False
            
            # 設定保存実行
            self.settings_ui._save_settings()
            
            # 各メソッドが呼ばれることを確認
            mock_save.assert_called_once()
            mock_apply.assert_called_once()
            mock_message.assert_called_once()
            
            # 変更が現在の設定にマージされていることを確認
            assert self.settings_ui.current_settings["language"] == "en"
            assert self.settings_ui.current_settings["auto_save"] == False
            
            # 保留中の変更がクリアされていることを確認
            assert len(self.settings_ui.pending_changes) == 0
    
    def test_discard_changes(self):
        """変更破棄のテスト"""
        # 変更を追加
        self.settings_ui.pending_changes["language"] = "en"
        self.settings_ui.pending_changes["auto_save"] = False
        
        with patch.object(self.settings_ui, '_show_message') as mock_message, \
             patch.object(self.settings_ui, '_back_to_main_settings') as mock_back:
            
            # 変更破棄実行
            self.settings_ui._discard_changes()
            
            # 保留中の変更がクリアされていることを確認
            assert len(self.settings_ui.pending_changes) == 0
            
            # メッセージ表示とメニュー復帰が呼ばれることを確認
            mock_message.assert_called_once()
            mock_back.assert_called_once()
    
    def test_reset_all_settings(self):
        """設定初期化のテスト"""
        with patch.object(self.settings_ui, '_save_settings_to_file') as mock_save, \
             patch.object(self.settings_ui, '_apply_settings') as mock_apply, \
             patch.object(self.settings_ui, '_show_message') as mock_message:
            
            # 現在の設定を変更
            self.settings_ui.current_settings["language"] = "en"
            self.settings_ui.pending_changes["auto_save"] = False
            
            # 設定初期化実行
            self.settings_ui._reset_all_settings()
            
            # デフォルト設定に戻っていることを確認
            default_settings = self.settings_ui._get_default_settings()
            assert self.settings_ui.current_settings == default_settings
            
            # 保留中の変更がクリアされていることを確認
            assert len(self.settings_ui.pending_changes) == 0
            
            # 各メソッドが呼ばれることを確認
            mock_save.assert_called_once()
            mock_apply.assert_called_once()
            mock_message.assert_called_once()
    
    @patch('src.ui.settings_ui.ui_manager')
    def test_show_settings_menu(self, mock_ui_manager):
        """設定メニュー表示のテスト"""
        with patch.object(config_manager, 'get_text') as mock_get_text:
            mock_get_text.return_value = "テストメニュー"
            
            # 設定メニュー表示
            self.settings_ui.show_settings_menu()
            
            # UIマネージャーが呼ばれることを確認（新API使用）
            mock_ui_manager.add_menu.assert_called()
            mock_ui_manager.show_menu.assert_called()
            
            # is_openフラグが設定されることを確認
            assert self.settings_ui.is_open
    
    def test_settings_categories(self):
        """設定カテゴリのテスト"""
        # 全てのカテゴリが定義されていることを確認
        categories = [
            SettingsCategory.GAMEPLAY,
            SettingsCategory.CONTROLS,
            SettingsCategory.AUDIO,
            SettingsCategory.GRAPHICS,
            SettingsCategory.ACCESSIBILITY
        ]
        
        for category in categories:
            assert isinstance(category, SettingsCategory)
            assert isinstance(category.value, str)
    
    def test_ui_state_management(self):
        """UI状態管理のテスト"""
        # 初期状態
        assert not self.settings_ui.is_open
        assert self.settings_ui.current_category is None
        
        # カテゴリ設定
        self.settings_ui.current_category = SettingsCategory.GAMEPLAY
        assert self.settings_ui.current_category == SettingsCategory.GAMEPLAY
        
        # UI表示状態設定
        self.settings_ui.is_open = True
        assert self.settings_ui.is_open
        
        # クリーンアップ
        self.settings_ui.destroy()
        assert not self.settings_ui.is_open
        assert self.settings_ui.current_category is None
        assert len(self.settings_ui.pending_changes) == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])