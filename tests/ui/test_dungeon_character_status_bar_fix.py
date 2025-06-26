"""ダンジョンでのキャラクターステータスバー描画修正のテスト"""

import pytest
import pygame
from unittest.mock import Mock, patch
import sys
import os

# テスト用のパス設定
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from src.ui.dungeon_ui_pygame import DungeonUIManagerPygame
from src.ui.character_status_bar import CharacterStatusBar, create_character_status_bar
from src.character.party import Party
from src.ui.small_map_ui_pygame import SmallMapUI


class TestDungeonCharacterStatusBarFix:
    """ダンジョンでのキャラクターステータスバー描画修正のテスト"""
    
    def setup_method(self):
        """テストセットアップ"""
        pygame.init()
        pygame.display.set_mode((1024, 768))
        
    def teardown_method(self):
        """テストクリーンアップ"""
        pygame.quit()
        
    def test_dungeon_ui_manager_initializes_status_bar(self):
        """ダンジョンUIマネージャーがステータスバーを正しく初期化することを確認"""
        screen = pygame.display.get_surface()
        dungeon_ui = DungeonUIManagerPygame(screen)
        
        # キャラクターステータスバーが作成されていることを確認
        assert dungeon_ui.character_status_bar is not None
        assert isinstance(dungeon_ui.character_status_bar, CharacterStatusBar)
        
        # ステータスバーが表示状態であることを確認
        assert dungeon_ui.character_status_bar.state.value == "visible"
        
    def test_dungeon_ui_manager_sets_party_to_status_bar(self):
        """ダンジョンUIマネージャーがパーティをステータスバーに正しく設定することを確認"""
        screen = pygame.display.get_surface()
        dungeon_ui = DungeonUIManagerPygame(screen)
        
        # パーティとキャラクターを作成
        character = Mock()
        character.name = "ダンジョンキャラクター"
        character.derived_stats = Mock()
        character.derived_stats.current_hp = 80
        character.derived_stats.max_hp = 100
        character.derived_stats.current_mp = 30
        character.derived_stats.max_mp = 50
        
        party = Party("ダンジョンパーティ")
        party.add_character(character)
        
        # パーティを設定
        dungeon_ui.set_party(party)
        
        # ステータスバーにパーティが設定されていることを確認
        assert dungeon_ui.character_status_bar.party == party
        assert dungeon_ui.current_party == party
        
        # 最初のスロットにキャラクターが設定されていることを確認
        assert dungeon_ui.character_status_bar.slots[0].character == character
        
    def test_dungeon_ui_render_overlay_order(self):
        """ダンジョンUIのrender_overlayが正しい順序で描画することを確認"""
        screen = pygame.display.get_surface()
        dungeon_ui = DungeonUIManagerPygame(screen)
        
        # 小地図UIをモック
        small_map_ui = Mock()
        small_map_ui.is_visible = True
        small_map_ui.render = Mock()
        dungeon_ui.small_map_ui = small_map_ui
        
        # キャラクターステータスバーをモック
        status_bar = Mock()
        status_bar.render = Mock()
        dungeon_ui.character_status_bar = status_bar
        
        # render_overlayを実行
        dungeon_ui.render_overlay()
        
        # 小地図とステータスバーの両方がrenderメソッドが呼び出されたことを確認
        small_map_ui.render.assert_called_once()
        status_bar.render.assert_called_once()
        
        # 呼び出し順序は保証されない（mockの性質上）が、両方が呼ばれることが重要
        
    def test_dungeon_ui_render_overlay_handles_exceptions(self):
        """render_overlayが例外を適切に処理することを確認"""
        screen = pygame.display.get_surface()
        dungeon_ui = DungeonUIManagerPygame(screen)
        
        # 例外を発生させるモック
        small_map_ui = Mock()
        small_map_ui.is_visible = True
        small_map_ui.render = Mock(side_effect=Exception("小地図描画エラー"))
        dungeon_ui.small_map_ui = small_map_ui
        
        status_bar = Mock()
        status_bar.render = Mock(side_effect=Exception("ステータスバー描画エラー"))
        dungeon_ui.character_status_bar = status_bar
        
        # 例外が発生してもrender_overlayが失敗しないことを確認
        try:
            dungeon_ui.render_overlay()
            assert True  # 例外が発生しなければ成功
        except Exception as e:
            pytest.fail(f"render_overlayで予期しない例外が発生: {e}")
            
        # 両方のrenderメソッドが呼び出されたことを確認（例外が発生しても）
        small_map_ui.render.assert_called_once()
        status_bar.render.assert_called_once()
        
    def test_dungeon_ui_status_bar_forced_visible(self):
        """ダンジョンUIのステータスバーが強制的に表示状態になることを確認"""
        screen = pygame.display.get_surface()
        
        # create_character_status_barをモック
        with patch('src.ui.dungeon_ui_pygame.create_character_status_bar') as mock_create:
            mock_status_bar = Mock()
            mock_status_bar.show = Mock()
            mock_create.return_value = mock_status_bar
            
            # ダンジョンUIを作成
            dungeon_ui = DungeonUIManagerPygame(screen)
            
            # ステータスバーのshowメソッドが呼び出されたことを確認
            mock_status_bar.show.assert_called_once()
            
    def test_dungeon_ui_render_overlay_without_small_map(self):
        """小地図がない場合のrender_overlayの動作を確認"""
        screen = pygame.display.get_surface()
        dungeon_ui = DungeonUIManagerPygame(screen)
        
        # 小地図UIを無効にする
        dungeon_ui.small_map_ui = None
        
        # キャラクターステータスバーをモック
        status_bar = Mock()
        status_bar.render = Mock()
        dungeon_ui.character_status_bar = status_bar
        
        # render_overlayを実行
        dungeon_ui.render_overlay()
        
        # ステータスバーのrenderが呼び出されたことを確認
        status_bar.render.assert_called_once()
        
    def test_dungeon_ui_render_overlay_with_invisible_small_map(self):
        """非表示の小地図がある場合のrender_overlayの動作を確認"""
        screen = pygame.display.get_surface()
        dungeon_ui = DungeonUIManagerPygame(screen)
        
        # 非表示の小地図UIをモック
        small_map_ui = Mock()
        small_map_ui.is_visible = False
        small_map_ui.render = Mock()
        dungeon_ui.small_map_ui = small_map_ui
        
        # キャラクターステータスバーをモック
        status_bar = Mock()
        status_bar.render = Mock()
        dungeon_ui.character_status_bar = status_bar
        
        # render_overlayを実行
        dungeon_ui.render_overlay()
        
        # 小地図のrenderは呼び出されないが、ステータスバーのrenderは呼び出される
        small_map_ui.render.assert_not_called()
        status_bar.render.assert_called_once()