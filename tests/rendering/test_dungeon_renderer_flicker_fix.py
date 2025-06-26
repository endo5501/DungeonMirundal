"""ダンジョンレンダラーのちらつき修正テスト"""

import pytest
import pygame
from unittest.mock import Mock, patch, call
import sys
import os

# テスト用のパス設定
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from src.rendering.dungeon_renderer_pygame import DungeonRendererPygame
from src.dungeon.dungeon_manager import DungeonState, PlayerPosition
from src.dungeon.dungeon_generator import Direction, DungeonLevel
from src.character.party import Party


class TestDungeonRendererFlickerFix:
    """ダンジョンレンダラーのちらつき修正テスト"""
    
    def setup_method(self):
        """テストセットアップ"""
        pygame.init()
        self.screen = pygame.display.set_mode((1024, 768))
        
    def teardown_method(self):
        """テストクリーンアップ"""
        pygame.quit()
        
    def test_no_duplicate_display_flip(self):
        """pygame.display.flip()が重複して呼ばれないことを確認"""
        renderer = DungeonRendererPygame(self.screen)
        
        # ダンジョン状態をモック
        dungeon_state = Mock()
        dungeon_state.player_position = PlayerPosition(5, 5, 1, Direction.NORTH)
        
        level = Mock()
        level.level = 1
        level.width = 10
        level.height = 10
        level.is_valid_position = Mock(return_value=True)
        level.get_cell = Mock(return_value=Mock())
        
        dungeon_state.levels = {1: level}
        
        # pygame.display.flipをモック
        with patch('pygame.display.flip') as mock_flip:
            # render_dungeonを実行
            result = renderer.render_dungeon(dungeon_state)
            
            # 成功したことを確認
            assert result is True
            
            # pygame.display.flip()が呼ばれていないことを確認
            mock_flip.assert_not_called()
            
    def test_render_direct_no_duplicate_flip(self):
        """render_directでもpygame.display.flip()が重複しないことを確認"""
        renderer = DungeonRendererPygame(self.screen)
        
        # UIマネージャーをモック
        ui_manager = Mock()
        ui_manager.render_overlay = Mock()
        renderer.dungeon_ui_manager = ui_manager
        
        # ダンジョンマネージャーをモック
        dungeon_manager = Mock()
        player_position = PlayerPosition(5, 5, 1, Direction.NORTH)
        dungeon_state = Mock()
        dungeon_state.player_position = player_position
        dungeon_manager.current_dungeon = dungeon_state
        renderer.dungeon_manager = dungeon_manager
        
        # レベルをモック
        level = Mock()
        level.width = 10
        level.height = 10
        level.is_valid_position = Mock(return_value=True)
        level.get_cell = Mock(return_value=Mock())
        
        # pygame.display.flipをモック
        with patch('pygame.display.flip') as mock_flip:
            # render_directを実行
            result = renderer._render_direct(player_position, level)
            
            # 成功したことを確認
            assert result is True
            
            # pygame.display.flip()が呼ばれていないことを確認
            mock_flip.assert_not_called()
            
    def test_ui_overlay_rendering_order(self):
        """UIオーバーレイが正しい順序で描画されることを確認"""
        renderer = DungeonRendererPygame(self.screen)
        
        # UIマネージャーをモック
        ui_manager = Mock()
        ui_manager.render_overlay = Mock()
        renderer.dungeon_ui_manager = ui_manager
        
        # ダンジョンマネージャーをモック
        dungeon_manager = Mock()
        player_position = PlayerPosition(5, 5, 1, Direction.NORTH)
        dungeon_state = Mock()
        dungeon_state.player_position = player_position
        dungeon_manager.current_dungeon = dungeon_state
        renderer.dungeon_manager = dungeon_manager
        
        # レベルをモック
        level = Mock()
        level.width = 10
        level.height = 10
        level.is_valid_position = Mock(return_value=True)
        level.get_cell = Mock(return_value=Mock())
        
        # render_directを実行
        result = renderer._render_direct(player_position, level)
        
        # UIオーバーレイが描画されたことを確認
        ui_manager.render_overlay.assert_called_once()
        
    def test_font_stability_in_dungeon_ui(self):
        """ダンジョンUIでのフォント安定性を確認"""
        from src.ui.dungeon_ui_pygame import DungeonUIManagerPygame
        
        dungeon_ui = DungeonUIManagerPygame(self.screen)
        
        # フォントが初期化されていることを確認
        assert dungeon_ui.font_small is not None
        assert dungeon_ui.font_medium is not None
        assert dungeon_ui.font_large is not None
        
        # キャラクターステータスバーが強制的に表示状態になっていることを確認
        if dungeon_ui.character_status_bar:
            assert dungeon_ui.character_status_bar.state.value == "visible"
            
    def test_hp_rendering_stability(self):
        """HP表示が安定してレンダリングされることを確認"""
        from src.ui.character_status_bar import CharacterSlot
        from src.character.character import CharacterStatus
        
        screen = self.screen
        slot = CharacterSlot(0, 0, 200, 100, 0)
        
        # キャラクターをモック
        character = Mock()
        character.name = "テストキャラクター"
        character.status = CharacterStatus.GOOD
        character.derived_stats = Mock()
        character.derived_stats.current_hp = 9
        character.derived_stats.max_hp = 9
        
        slot.set_character(character)
        
        # 安定したフォントを使用
        font = pygame.font.Font(None, 16)
        
        # エラーなくレンダリングできることを確認
        try:
            slot._render_hp_bar(screen, font)
            assert True  # 成功
        except Exception as e:
            pytest.fail(f"HP表示のレンダリングで例外: {e}")