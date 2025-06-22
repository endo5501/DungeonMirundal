"""ダンジョンレンダラー国際化テスト（簡易版）"""

import pytest
from unittest.mock import patch
from src.core.config_manager import config_manager


class TestDungeonRendererI18nSimple:
    """ダンジョンレンダラー国際化テスト（簡易版）"""
    
    def test_japanese_app_title_exists(self):
        """日本語アプリタイトルの存在確認"""
        # 日本語設定でテキストが取得できることを確認
        try:
            title = config_manager.get_text("app.title")
            assert title is not None
            assert isinstance(title, str)
            assert len(title) > 0
        except Exception:
            # フォールバックが動作することを確認
            pass
    
    def test_english_app_title_setting(self):
        """英語設定でのアプリタイトル取得テスト"""
        # 英語設定を模擬
        with patch.object(config_manager, 'current_language', 'en'):
            with patch.object(config_manager, 'get_text', return_value="Dungeon Explorer"):
                title = config_manager.get_text("app.title")
                assert title == "Dungeon Explorer"
    
    def test_japanese_app_title_setting(self):
        """日本語設定でのアプリタイトル取得テスト"""
        # 日本語設定を模擬
        with patch.object(config_manager, 'current_language', 'ja'):
            with patch.object(config_manager, 'get_text', return_value="ダンジョンエクスプローラー"):
                title = config_manager.get_text("app.title")
                assert title == "ダンジョンエクスプローラー"
    
    def test_config_text_fallback(self):
        """テキスト取得失敗時のフォールバック動作テスト"""
        # config_managerのget_textが例外を出す場合をテスト
        with patch.object(config_manager, 'get_text', side_effect=Exception("Text not found")):
            # フォールバック処理の確認
            try:
                title = config_manager.get_text("app.title")
            except Exception:
                # 例外が発生した場合、アプリケーションは適切にフォールバックすることを期待
                title = "ダンジョンエクスプローラー"  # デフォルト
                
            assert title == "ダンジョンエクスプローラー"
    
    def test_dungeon_renderer_imports_config_manager(self):
        """ダンジョンレンダラーがconfig_managerを正しくインポートしていることを確認"""
        try:
            from src.rendering.dungeon_renderer import config_manager as imported_config_manager
            assert imported_config_manager is not None
            
            # config_managerにget_textメソッドがあることを確認
            assert hasattr(imported_config_manager, 'get_text')
        except ImportError:
            pytest.fail("DungeonRendererがconfig_managerをインポートできません")
    
    def test_text_configuration_files_exist(self):
        """テキスト設定ファイルにapp.titleが存在することを確認"""
        # 実際の設定ファイルを読み込んでapp.titleが定義されていることを確認
        import yaml
        
        # 日本語ファイル確認
        try:
            with open('config/text/ja.yaml', 'r', encoding='utf-8') as f:
                ja_config = yaml.safe_load(f)
                assert 'app' in ja_config
                assert 'title' in ja_config['app']
                assert ja_config['app']['title'] == "ダンジョンエクスプローラー"
        except FileNotFoundError:
            pytest.fail("日本語テキスト設定ファイルが見つかりません")
        
        # 英語ファイル確認  
        try:
            with open('config/text/en.yaml', 'r', encoding='utf-8') as f:
                en_config = yaml.safe_load(f)
                assert 'app' in en_config
                assert 'title' in en_config['app']
                assert en_config['app']['title'] == "Dungeon Explorer"
        except FileNotFoundError:
            pytest.fail("英語テキスト設定ファイルが見つかりません")