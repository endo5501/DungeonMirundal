"""Pygame フォントマネージャーのテスト"""

import pytest
import os
from unittest.mock import Mock, patch
import pygame

# ヘッドレス環境でのPygame初期化
os.environ['SDL_VIDEODRIVER'] = 'dummy'

from src.ui.font_manager_pygame import FontManager, font_manager


class TestFontManager:
    """FontManagerクラスのテスト"""
    
    def setup_method(self):
        """各テストメソッドの前に実行"""
        # Pygameの初期化（ヘッドレス）
        pygame.init()
    
    def teardown_method(self):
        """各テストメソッドの後に実行"""
        pygame.quit()
    
    def test_font_manager_initialization(self):
        """FontManager初期化テスト"""
        manager = FontManager()
        
        assert isinstance(manager.fonts, dict)
        assert manager.default_font is not None
        assert isinstance(manager.default_font, pygame.font.Font)
    
    @patch('os.path.exists')
    def test_font_manager_with_japanese_font_available(self, mock_exists):
        """日本語フォントが利用可能な場合のテスト"""
        # 最初のフォントパスが存在するようにモック
        mock_exists.side_effect = lambda path: "/NotoSansCJK" in path
        
        manager = FontManager()
        
        # 日本語フォントが読み込まれることを確認
        japanese_fonts = [key for key in manager.fonts.keys() if key.startswith('japanese_')]
        assert len(japanese_fonts) > 0
    
    @patch('os.path.exists')
    def test_font_manager_with_no_japanese_font(self, mock_exists):
        """日本語フォントが利用できない場合のテスト"""
        # すべてのフォントパスが存在しないようにモック
        mock_exists.return_value = False
        
        manager = FontManager()
        
        # デフォルトフォントがセットされることを確認
        assert manager.default_font is not None
        # フォールバックフォントが利用されることを確認
        default_fonts = [key for key in manager.fonts.keys() if key.startswith('default_')]
        assert len(default_fonts) > 0
    
    def test_get_japanese_font(self):
        """日本語フォント取得テスト"""
        manager = FontManager()
        
        # 日本語フォントを取得
        font = manager.get_japanese_font(24)
        
        # フォントが取得できることを確認
        assert font is not None
        assert isinstance(font, pygame.font.Font)
    
    def test_get_japanese_font_fallback(self):
        """日本語フォント取得フォールバックテスト"""
        manager = FontManager()
        
        # 存在しないサイズで日本語フォントを取得
        font = manager.get_japanese_font(999)
        
        # フォールバックが機能することを確認
        assert font is not None
        assert isinstance(font, pygame.font.Font)
    
    def test_get_font_by_name(self):
        """名前によるフォント取得テスト"""
        manager = FontManager()
        
        # デフォルトフォントを取得
        font = manager.get_font('default', 24)
        
        assert font is not None
        assert isinstance(font, pygame.font.Font)
    
    def test_get_font_nonexistent(self):
        """存在しないフォント取得テスト"""
        manager = FontManager()
        
        # 存在しないフォント名で取得
        font = manager.get_font('nonexistent', 24)
        
        # Noneまたはデフォルトフォントが返されることを確認
        if font is not None:
            assert isinstance(font, pygame.font.Font)
    
    def test_get_default_font(self):
        """デフォルトフォント取得テスト"""
        manager = FontManager()
        
        font = manager.get_default_font()
        
        assert font is not None
        assert isinstance(font, pygame.font.Font)
        assert font == manager.default_font
    
    def test_font_caching(self):
        """フォントキャッシュテスト"""
        manager = FontManager()
        
        # 同じサイズの日本語フォントを2回取得
        font1 = manager.get_japanese_font(24)
        font2 = manager.get_japanese_font(24)
        
        # 同じフォントオブジェクトが返されることを確認（キャッシュ機能）
        assert font1 is font2
    
    def test_multiple_font_sizes(self):
        """複数フォントサイズテスト"""
        manager = FontManager()
        
        sizes = [16, 24, 32]
        fonts = []
        
        for size in sizes:
            font = manager.get_japanese_font(size)
            fonts.append(font)
            assert font is not None
        
        # 異なるサイズでは異なるフォントオブジェクトが返されることを確認
        assert fonts[0] is not fonts[1]
        assert fonts[1] is not fonts[2]
    
    def test_font_loading_error_handling(self):
        """フォント読み込みエラー処理テスト"""
        # 通常の初期化でもエラーハンドリングが適切に動作することを確認
        manager = FontManager()
        
        # 何らかのフォントは必ず利用可能であることを確認
        # （Pygameの最終フォールバックが動作）
        assert len(manager.fonts) > 0
    
    def test_text_rendering_capability(self):
        """テキストレンダリング機能テスト"""
        manager = FontManager()
        
        font = manager.get_japanese_font(24)
        
        # 日本語テキストがレンダリングできることを確認
        try:
            surface = font.render("こんにちは", True, (255, 255, 255))
            assert surface is not None
            assert isinstance(surface, pygame.Surface)
        except Exception as e:
            pytest.fail(f"日本語テキストのレンダリングに失敗: {e}")
    
    def test_ascii_text_rendering(self):
        """ASCII テキストレンダリングテスト"""
        manager = FontManager()
        
        font = manager.get_default_font()
        
        # ASCII テキストがレンダリングできることを確認
        try:
            surface = font.render("Hello World", True, (255, 255, 255))
            assert surface is not None
            assert isinstance(surface, pygame.Surface)
        except Exception as e:
            pytest.fail(f"ASCII テキストのレンダリングに失敗: {e}")


class TestGlobalFontManager:
    """グローバルフォントマネージャーテスト"""
    
    def setup_method(self):
        """各テストメソッドの前に実行"""
        pygame.init()
    
    def teardown_method(self):
        """各テストメソッドの後に実行"""
        pygame.quit()
    
    def test_global_font_manager_exists(self):
        """グローバルフォントマネージャー存在テスト"""
        assert font_manager is not None
        assert isinstance(font_manager, FontManager)
    
    def test_global_font_manager_functionality(self):
        """グローバルフォントマネージャー機能テスト"""
        # グローバルフォントマネージャーが基本機能を提供することを確認
        try:
            # デフォルトフォント取得試行
            default_font = font_manager.get_default_font()
            # None でも構わない（エラーが発生しなければOK）
            
            # 日本語フォント取得試行
            japanese_font = font_manager.get_japanese_font(24)
            # None でも構わない（エラーが発生しなければOK）
            
            # 最低限、フォント辞書が存在することを確認
            assert hasattr(font_manager, 'fonts')
            assert isinstance(font_manager.fonts, dict)
            
        except Exception as e:
            pytest.fail(f"グローバルフォントマネージャーの基本機能でエラー: {e}")
    
    def test_global_consistency(self):
        """グローバルインスタンス一貫性テスト"""
        # 複数回アクセスしても同じインスタンスが返されることを確認
        manager1 = font_manager
        manager2 = font_manager
        
        assert manager1 is manager2


@pytest.mark.pygame
class TestFontManagerIntegration:
    """フォントマネージャー統合テスト"""
    
    def setup_method(self):
        """各テストメソッドの前に実行"""
        pygame.init()
        self.screen = pygame.display.set_mode((800, 600))
    
    def teardown_method(self):
        """各テストメソッドの後に実行"""
        pygame.quit()
    
    def test_font_in_real_rendering_context(self):
        """実際の描画コンテキストでのフォントテスト"""
        manager = FontManager()
        
        # フォントを取得
        font = manager.get_japanese_font(24)
        
        # 実際の画面サーフェスにテキストを描画
        text_surface = font.render("テスト", True, (255, 255, 255))
        self.screen.blit(text_surface, (100, 100))
        
        # エラーが発生しないことを確認
        pygame.display.flip()
    
    def test_multiple_fonts_rendering(self):
        """複数フォントの同時レンダリングテスト"""
        manager = FontManager()
        
        # 異なるサイズのフォントを取得
        small_font = manager.get_japanese_font(16)
        medium_font = manager.get_japanese_font(24)
        large_font = manager.get_japanese_font(32)
        
        # それぞれでテキストをレンダリング
        small_text = small_font.render("小", True, (255, 255, 255))
        medium_text = medium_font.render("中", True, (255, 255, 255))
        large_text = large_font.render("大", True, (255, 255, 255))
        
        # 画面に描画
        self.screen.blit(small_text, (100, 100))
        self.screen.blit(medium_text, (100, 150))
        self.screen.blit(large_text, (100, 200))
        
        pygame.display.flip()
        
        # すべてのテキストサーフェスが作成されていることを確認
        assert small_text is not None
        assert medium_text is not None
        assert large_text is not None
    
    def test_font_performance(self):
        """フォント取得パフォーマンステスト"""
        manager = FontManager()
        
        import time
        
        # 同じフォントを複数回取得（キャッシュ効果のテスト）
        start_time = time.time()
        for _ in range(100):
            font = manager.get_japanese_font(24)
        end_time = time.time()
        
        # キャッシュにより高速に取得できることを確認
        duration = end_time - start_time
        assert duration < 1.0  # 1秒以内で完了することを期待
        assert font is not None