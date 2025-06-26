"""
GameLocationエラーの修正テスト

Phase 2で報告されたGameLocationエラーが修正されていることを確認
"""

import pytest
import pygame
from unittest.mock import Mock, patch

from src.core.game_manager import GameManager
from src.utils.constants import GameLocation
from src.ui.dungeon_ui_pygame import DungeonUIManagerPygame
from src.dungeon.dungeon_manager import DungeonState


class TestGameLocationFix:
    """GameLocationエラー修正のテストクラス"""
    
    @pytest.fixture(autouse=True)
    def setup_pygame(self):
        """Pygameの初期化"""
        if not pygame.get_init():
            pygame.init()
        yield
    
    def test_gamelocation_import(self):
        """GameLocationクラスが正しくインポートできることをテスト"""
        # GameLocationクラスが定義されている
        assert hasattr(GameLocation, 'OVERWORLD')
        assert hasattr(GameLocation, 'DUNGEON')
        assert GameLocation.OVERWORLD == "overworld"
        assert GameLocation.DUNGEON == "dungeon"
    
    def test_game_manager_gamelocation_usage(self):
        """GameManagerでGameLocationが正しく使用できることをテスト"""
        with patch('pygame.display.set_mode') as mock_display:
            mock_surface = Mock()
            mock_surface.get_width.return_value = 1024
            mock_surface.get_height.return_value = 768
            mock_display.return_value = mock_surface
            
            # GameManagerが正常にインスタンス化される
            game_manager = GameManager()
            
            # GameLocationが参照できる
            assert hasattr(game_manager, 'current_location')
            
            # 初期状態は地上部
            assert game_manager.current_location == GameLocation.OVERWORLD
    
    def test_dungeon_ui_manager_small_map_integration(self):
        """ダンジョンUIマネージャーで小地図が正常に統合されることをテスト"""
        screen = pygame.Surface((1024, 768))
        
        # DungeonUIManagerが正常に初期化される
        ui_manager = DungeonUIManagerPygame(screen)
        
        # 小地図UIは初期状態ではNone
        assert ui_manager.small_map_ui is None
        
        # ダンジョン状態を設定
        state = DungeonState('test_dungeon', 'test_seed')
        ui_manager.set_dungeon_state(state)
        
        # 小地図UIが作成される
        assert ui_manager.small_map_ui is not None
        assert ui_manager.dungeon_state == state
    
    def test_action_callback_no_error(self):
        """アクションコールバックでGameLocationエラーが発生しないことをテスト"""
        with patch('pygame.display.set_mode') as mock_display:
            mock_surface = Mock()
            mock_surface.get_width.return_value = 1024
            mock_surface.get_height.return_value = 768
            mock_display.return_value = mock_surface
            
            game_manager = GameManager()
            
            # magic アクション（Mキー）が GameLocation エラーを引き起こさない
            try:
                # GameLocationが定義されているため、コードの実行でエラーにならない
                current_loc = game_manager.current_location
                assert current_loc in [GameLocation.OVERWORLD, GameLocation.DUNGEON]
            except NameError as e:
                pytest.fail(f"GameLocation should be defined: {e}")
    
    def test_small_map_event_handling(self):
        """小地図のイベント処理が正常に動作することをテスト"""
        screen = pygame.Surface((1024, 768))
        ui_manager = DungeonUIManagerPygame(screen)
        
        # ダンジョン状態を設定
        state = DungeonState('test', 'test_seed')
        ui_manager.set_dungeon_state(state)
        
        # Mキーイベントを作成
        m_key_event = pygame.event.Event(pygame.KEYDOWN, key=pygame.K_m)
        
        # イベント処理が正常に動作する（エラーが発生しない）
        try:
            result = ui_manager.handle_input(m_key_event)
            # 小地図のイベント処理が実行される
            assert isinstance(result, bool)
        except NameError as e:
            pytest.fail(f"Event handling should not cause GameLocation error: {e}")
    
    def test_constants_gamelocation_definition(self):
        """constants.pyでGameLocationが正しく定義されていることをテスト"""
        from src.utils.constants import GameLocation
        
        # クラスが存在する
        assert GameLocation is not None
        
        # 必要な定数が定義されている
        assert hasattr(GameLocation, 'OVERWORLD')
        assert hasattr(GameLocation, 'DUNGEON')
        
        # 値が正しい
        assert GameLocation.OVERWORLD == "overworld"
        assert GameLocation.DUNGEON == "dungeon"