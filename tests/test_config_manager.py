"""ConfigManagerのテスト"""

import pytest
import tempfile
import yaml
from pathlib import Path
from src.core.config_manager import ConfigManager


class TestConfigManager:
    """ConfigManagerのテストクラス"""
    
    def setup_method(self):
        """各テストメソッドの前に実行"""
        # 一時ディレクトリの作成
        self.temp_dir = tempfile.TemporaryDirectory()
        self.config_dir = Path(self.temp_dir.name)
        self.config_manager = ConfigManager(str(self.config_dir))
        
        # テスト用設定ファイルの作成
        self._create_test_config()
        self._create_test_text()
    
    def teardown_method(self):
        """各テストメソッドの後に実行"""
        self.temp_dir.cleanup()
    
    def _create_test_config(self):
        """テスト用設定ファイルの作成"""
        test_config = {
            "window": {
                "width": 800,
                "height": 600
            },
            "audio": {
                "volume": 0.8
            }
        }
        
        config_path = self.config_dir / "test_config.yaml"
        with open(config_path, 'w', encoding='utf-8') as f:
            yaml.dump(test_config, f, allow_unicode=True)
    
    def _create_test_text(self):
        """テスト用テキストファイルの作成"""
        text_dir = self.config_dir / "text"
        text_dir.mkdir(exist_ok=True)
        
        test_text = {
            "menu": {
                "start": "開始"
            },
            "common": {
                "ok": "OK"
            }
        }
        
        text_path = text_dir / "ja.yaml"
        with open(text_path, 'w', encoding='utf-8') as f:
            yaml.dump(test_text, f, allow_unicode=True)
    
    def test_load_config(self):
        """設定ファイル読み込みのテスト"""
        config = self.config_manager.load_config("test_config")
        
        assert config is not None
        assert config["window"]["width"] == 800
        assert config["window"]["height"] == 600
        assert config["audio"]["volume"] == 0.8
    
    def test_get_config(self):
        """設定値取得のテスト"""
        width = self.config_manager.get_config("test_config", "window")["width"]
        assert width == 800
        
        # デフォルト値のテスト
        default_value = self.config_manager.get_config("test_config", "nonexistent", "default")
        assert default_value == "default"
    
    def test_load_text_data(self):
        """テキストデータ読み込みのテスト"""
        text_data = self.config_manager.load_text_data("ja")
        
        assert text_data is not None
        assert text_data["menu"]["start"] == "開始"
        assert text_data["common"]["ok"] == "OK"
    
    def test_get_text(self):
        """テキスト取得のテスト"""
        text = self.config_manager.get_text("menu.start", "ja")
        assert text == "開始"
        
        # 存在しないキーのテスト
        missing_text = self.config_manager.get_text("nonexistent.key", "ja")
        assert missing_text == "[nonexistent.key]"
    
    def test_set_language(self):
        """言語設定のテスト"""
        self.config_manager.set_language("en")
        assert self.config_manager.current_language == "en"
    
    def test_nonexistent_file(self):
        """存在しないファイルの処理テスト"""
        config = self.config_manager.load_config("nonexistent")
        assert config == {}
        
        text_data = self.config_manager.load_text_data("nonexistent")
        assert text_data == {}