"""ConfigManagerの包括的テスト"""

import unittest
import tempfile
import yaml
from pathlib import Path
from unittest.mock import patch, mock_open
from src.core.config_manager import ConfigManager, DEFAULT_LANGUAGE, MISSING_TEXT_PREFIX, MISSING_TEXT_SUFFIX


class TestConfigManagerBasic(unittest.TestCase):
    """ConfigManagerの基本機能テスト"""
    
    def setUp(self):
        """テスト前のセットアップ"""
        self.temp_dir = tempfile.mkdtemp()
        self.config_manager = ConfigManager(self.temp_dir)
    
    def test_initialization(self):
        """初期化のテスト"""
        self.assertEqual(str(self.config_manager.config_dir), self.temp_dir)
        self.assertEqual(self.config_manager.current_language, DEFAULT_LANGUAGE)
        self.assertEqual(len(self.config_manager._configs), 0)
        self.assertEqual(len(self.config_manager._text_data), 0)
    
    def test_set_language(self):
        """言語設定のテスト"""
        new_language = "en"
        
        self.config_manager.set_language(new_language)
        
        self.assertEqual(self.config_manager.current_language, new_language)
    
    def test_get_language(self):
        """言語取得のテスト"""
        result = self.config_manager.current_language
        self.assertEqual(result, DEFAULT_LANGUAGE)
        
        # 言語変更後
        self.config_manager.set_language("en")
        result = self.config_manager.current_language
        self.assertEqual(result, "en")
    
    @patch('builtins.open', new_callable=mock_open, read_data='test_key: test_value\nnested:\n  key: nested_value')
    def test_load_config_success(self, mock_file):
        """設定ファイル読み込み成功のテスト"""
        with patch('pathlib.Path.exists', return_value=True):
            result = self.config_manager.load_config("test_config")
            
            self.assertEqual(result["test_key"], "test_value")
            self.assertEqual(result["nested"]["key"], "nested_value")
            self.assertIn("test_config", self.config_manager._configs)
    
    def test_load_config_file_not_found(self):
        """設定ファイルが見つからない場合のテスト"""
        with patch('pathlib.Path.exists', return_value=False):
            result = self.config_manager.load_config("missing_config")
            
            self.assertEqual(result, {})
    
    @patch('builtins.open', side_effect=Exception("Read error"))
    def test_load_config_read_error(self, mock_file):
        """設定ファイル読み込みエラーのテスト"""
        with patch('pathlib.Path.exists', return_value=True):
            result = self.config_manager.load_config("error_config")
            
            self.assertEqual(result, {})
    
    def test_load_config_cached(self):
        """設定ファイルキャッシュのテスト"""
        test_config = {"cached": "data"}
        self.config_manager._configs["cached_config"] = test_config
        
        result = self.config_manager.load_config("cached_config")
        
        self.assertEqual(result, test_config)
    
    def test_get_config_with_default(self):
        """デフォルト値付き設定取得のテスト"""
        test_config = {"existing_key": "existing_value"}
        self.config_manager._configs["test"] = test_config
        
        # 存在するキー
        result = self.config_manager.get_config("test", "existing_key", "default")
        self.assertEqual(result, "existing_value")
        
        # 存在しないキー
        result = self.config_manager.get_config("test", "missing_key", "default")
        self.assertEqual(result, "default")


class TestConfigManagerTextHandling(unittest.TestCase):
    """ConfigManagerのテキスト処理テスト"""
    
    def setUp(self):
        """テスト前のセットアップ"""
        self.temp_dir = tempfile.mkdtemp()
        self.config_manager = ConfigManager(self.temp_dir)
    
    @patch('builtins.open', new_callable=mock_open, read_data='ui:\n  button:\n    ok: "OK"\n    cancel: "Cancel"\napp_log:\n  start: "Game started"')
    def test_load_text_data_success(self, mock_file):
        """テキストデータ読み込み成功のテスト"""
        with patch('pathlib.Path.exists', return_value=True):
            result = self.config_manager.load_text_data("en")
            
            self.assertEqual(result["ui"]["button"]["ok"], "OK")
            self.assertEqual(result["ui"]["button"]["cancel"], "Cancel")
            self.assertEqual(result["app_log"]["start"], "Game started")
            self.assertIn("en", self.config_manager._text_data)
    
    def test_load_text_data_file_not_found(self):
        """テキストファイルが見つからない場合のテスト"""
        with patch('pathlib.Path.exists', return_value=False):
            result = self.config_manager.load_text_data("missing")
            
            self.assertEqual(result, {})
    
    @patch('builtins.open', side_effect=Exception("Read error"))
    def test_load_text_data_read_error(self, mock_file):
        """テキストファイル読み込みエラーのテスト"""
        with patch('pathlib.Path.exists', return_value=True):
            result = self.config_manager.load_text_data("error")
            
            self.assertEqual(result, {})
    
    def test_load_text_data_cached(self):
        """テキストデータキャッシュのテスト"""
        test_text = {"cached": {"text": "data"}}
        self.config_manager._text_data["ja"] = test_text
        
        result = self.config_manager.load_text_data("ja")
        
        self.assertEqual(result, test_text)
    
    def test_get_text_simple_key(self):
        """単純キーでのテキスト取得のテスト"""
        test_text = {"simple_key": "Simple Value"}
        self.config_manager._text_data[DEFAULT_LANGUAGE] = test_text
        
        result = self.config_manager.get_text("simple_key")
        
        self.assertEqual(result, "Simple Value")
    
    def test_get_text_nested_key(self):
        """ネストされたキーでのテキスト取得のテスト"""
        test_text = {
            "ui": {
                "button": {
                    "ok": "OK Button"
                }
            }
        }
        self.config_manager._text_data[DEFAULT_LANGUAGE] = test_text
        
        result = self.config_manager.get_text("ui.button.ok")
        
        self.assertEqual(result, "OK Button")
    
    def test_get_text_missing_key(self):
        """存在しないキーでのテキスト取得のテスト"""
        test_text = {"existing": "value"}
        self.config_manager._text_data[DEFAULT_LANGUAGE] = test_text
        
        result = self.config_manager.get_text("missing.key")
        
        expected = f"{MISSING_TEXT_PREFIX}missing.key{MISSING_TEXT_SUFFIX}"
        self.assertEqual(result, expected)
    
    def test_get_text_with_default(self):
        """デフォルト値付きテキスト取得のテスト"""
        test_text = {"existing": "value"}
        self.config_manager._text_data[DEFAULT_LANGUAGE] = test_text
        
        result = self.config_manager.get_text("missing.key", default="Default Text")
        
        self.assertEqual(result, "Default Text")
    
    def test_get_text_with_language(self):
        """特定言語でのテキスト取得のテスト"""
        test_text_ja = {"key": "日本語"}
        test_text_en = {"key": "English"}
        self.config_manager._text_data["ja"] = test_text_ja
        self.config_manager._text_data["en"] = test_text_en
        
        result_ja = self.config_manager.get_text("key", language="ja")
        result_en = self.config_manager.get_text("key", language="en")
        
        self.assertEqual(result_ja, "日本語")
        self.assertEqual(result_en, "English")


class TestConfigManagerEdgeCases(unittest.TestCase):
    """ConfigManagerのエッジケーステスト"""
    
    def setUp(self):
        """テスト前のセットアップ"""
        self.temp_dir = tempfile.mkdtemp()
        self.config_manager = ConfigManager(self.temp_dir)
    
    @patch('builtins.open', new_callable=mock_open, read_data='')
    def test_load_config_empty_file(self, mock_file):
        """空の設定ファイルのテスト"""
        with patch('pathlib.Path.exists', return_value=True):
            result = self.config_manager.load_config("empty_config")
            
            self.assertEqual(result, {})
    
    @patch('builtins.open', new_callable=mock_open, read_data='invalid: yaml: content: [')
    def test_load_config_invalid_yaml(self, mock_file):
        """無効なYAML形式のテスト"""
        with patch('pathlib.Path.exists', return_value=True):
            result = self.config_manager.load_config("invalid_yaml")
            
            self.assertEqual(result, {})
    
    def test_get_text_empty_key(self):
        """空のキーでのテキスト取得のテスト"""
        test_text = {"key": "value"}
        self.config_manager._text_data[DEFAULT_LANGUAGE] = test_text
        
        result = self.config_manager.get_text("")
        
        expected = f"{MISSING_TEXT_PREFIX}{MISSING_TEXT_SUFFIX}"
        self.assertEqual(result, expected)
    
    def test_get_text_non_dict_nested(self):
        """辞書でないネストされた値のテスト"""
        test_text = {
            "top": "string_value"
        }
        self.config_manager._text_data[DEFAULT_LANGUAGE] = test_text
        
        result = self.config_manager.get_text("top.nested")
        
        expected = f"{MISSING_TEXT_PREFIX}top.nested{MISSING_TEXT_SUFFIX}"
        self.assertEqual(result, expected)
    
    def test_get_config_none_default(self):
        """Noneデフォルト値での設定取得のテスト"""
        test_config = {}
        self.config_manager._configs["test"] = test_config
        
        result = self.config_manager.get_config("test", "missing_key", None)
        
        self.assertIsNone(result)
    
    def test_get_text_numeric_value(self):
        """数値テキスト値の処理テスト"""
        test_text = {"number": 42}
        self.config_manager._text_data[DEFAULT_LANGUAGE] = test_text
        
        result = self.config_manager.get_text("number")
        
        self.assertEqual(result, "42")
    
    def test_config_manager_with_custom_dir(self):
        """カスタムディレクトリでの初期化テスト"""
        custom_dir = "/custom/config/dir"
        config_manager = ConfigManager(custom_dir)
        
        self.assertEqual(str(config_manager.config_dir), custom_dir)


if __name__ == '__main__':
    unittest.main()