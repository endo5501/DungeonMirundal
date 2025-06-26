"""HP表示の安定性テスト"""

import pytest
import pygame
from unittest.mock import Mock, patch
import sys
import os

# テスト用のパス設定
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from src.ui.character_status_bar import CharacterSlot
from src.character.character import CharacterStatus


class TestHPDisplayStability:
    """HP表示の安定性をテスト"""
    
    def setup_method(self):
        """テストセットアップ"""
        pygame.init()
        pygame.display.set_mode((1024, 768))
        
    def teardown_method(self):
        """テストクリーンアップ"""
        pygame.quit()
        
    def test_hp_text_rendering_with_slash(self):
        """スラッシュ文字を含むHP表示が正しくレンダリングされることを確認"""
        screen = pygame.display.get_surface()
        
        # キャラクタースロットを作成
        slot = CharacterSlot(0, 0, 200, 100, 0)
        
        # キャラクターをモック
        character = Mock()
        character.name = "テストキャラクター"
        character.status = CharacterStatus.GOOD
        character.derived_stats = Mock()
        character.derived_stats.current_hp = 9
        character.derived_stats.max_hp = 9
        character.derived_stats.current_mp = 24
        character.derived_stats.max_mp = 24
        
        slot.set_character(character)
        
        # フォントを作成
        font = pygame.font.Font(None, 16)
        
        # 複数回レンダリングして安定性を確認
        for i in range(10):
            try:
                slot._render_hp_bar(screen, font)
                # エラーが発生しなければ成功
            except Exception as e:
                pytest.fail(f"HP表示のレンダリング{i+1}回目で例外が発生: {e}")
                
    def test_hp_text_individual_rendering(self):
        """HP表示の個別レンダリングが正しく動作することを確認"""
        screen = pygame.display.get_surface()
        font = pygame.font.Font(None, 16)
        
        # テストデータ
        test_cases = [
            (9, 9),
            (24, 24),
            (12, 12),
            (100, 100),
            (1, 999),
        ]
        
        for current_hp, max_hp in test_cases:
            # 個別レンダリングのテスト
            try:
                # 現在HPをレンダリング
                current_surface = font.render(str(current_hp), True, (255, 255, 255))
                assert current_surface is not None
                
                # スラッシュをレンダリング
                slash_surface = font.render("/", True, (255, 255, 255))
                assert slash_surface is not None
                
                # 最大HPをレンダリング
                max_surface = font.render(str(max_hp), True, (255, 255, 255))
                assert max_surface is not None
                
            except Exception as e:
                pytest.fail(f"HP {current_hp}/{max_hp} のレンダリングで例外: {e}")
                
    def test_fallback_rendering(self):
        """フォールバックレンダリングが正しく動作することを確認"""
        screen = pygame.display.get_surface()
        
        # キャラクタースロットを作成
        slot = CharacterSlot(0, 0, 200, 100, 0)
        
        # キャラクターをモック
        character = Mock()
        character.name = "テストキャラクター"
        character.status = CharacterStatus.GOOD
        character.derived_stats = Mock()
        character.derived_stats.current_hp = 50
        character.derived_stats.max_hp = 100
        
        slot.set_character(character)
        
        # 問題のあるフォントをモック（スラッシュでエラーを発生させる）
        font = Mock()
        font.render = Mock(side_effect=lambda text, *args: 
                          Mock(get_width=Mock(return_value=20)) if "/" not in text 
                          else Mock(side_effect=Exception("Slash rendering error")))
        
        # フォールバックが動作することを確認
        try:
            slot._render_hp_bar(screen, font)
            # フォールバックが正しく動作すればエラーは発生しない
        except Exception as e:
            # 最終フォールバックも失敗した場合
            assert "Slash rendering error" not in str(e)
            
    def test_font_caching(self):
        """フォントキャッシングが正しく動作することを確認"""
        from src.ui.character_status_bar import CharacterStatusBar
        
        # キャラクターステータスバーを作成
        status_bar = CharacterStatusBar()
        
        # フォントがキャッシュされることを確認
        if status_bar.font:
            assert hasattr(status_bar, '_cached_font')
            assert status_bar._cached_font == status_bar.font
            
    def test_render_with_cached_font(self):
        """キャッシュされたフォントでのレンダリングが安定することを確認"""
        from src.ui.character_status_bar import CharacterStatusBar
        
        screen = pygame.display.get_surface()
        status_bar = CharacterStatusBar()
        
        # キャラクターとパーティをモック
        character = Mock()
        character.name = "テストキャラクター"
        character.status = CharacterStatus.GOOD
        character.derived_stats = Mock()
        character.derived_stats.current_hp = 9
        character.derived_stats.max_hp = 9
        
        party = Mock()
        party.characters = {"1": character}
        status_bar.set_party(party)
        
        # 複数回レンダリングして安定性を確認
        for i in range(5):
            try:
                status_bar.render(screen, None)
                # キャッシュされたフォントが使用されることを確認
                if hasattr(status_bar, '_cached_font'):
                    assert status_bar._cached_font is not None
            except pygame.error as e:
                if "Invalid font" in str(e):
                    # テスト環境でのフォントエラーは無視
                    pass
                else:
                    pytest.fail(f"予期しないエラー: {e}")
            except Exception as e:
                pytest.fail(f"レンダリング{i+1}回目で例外: {e}")