"""ダンジョン入口バグ修正のテスト"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import sys

# Panda3Dのモック
mock_modules = {
    'direct': Mock(),
    'direct.showbase': Mock(),
    'direct.showbase.ShowBase': Mock(),
    'direct.actor': Mock(),
    'direct.actor.Actor': Mock(),
    'direct.gui': Mock(),
    'direct.gui.DirectGui': Mock(),
    'panda3d': Mock(),
    'panda3d.core': Mock(),
}

for module_name, mock_module in mock_modules.items():
    sys.modules[module_name] = mock_module

from src.character.character import Character, CharacterStatus
from src.character.party import Party
from src.overworld.overworld_manager import OverworldManager
from src.core.game_manager import GameManager


class TestDungeonEntranceBugFix(unittest.TestCase):
    """ダンジョン入口バグ修正のテストクラス"""
    
    def setUp(self):
        """テスト前のセットアップ"""
        # モックキャラクターを作成
        self.good_character = Mock(spec=Character)
        self.good_character.name = "健康なキャラクター"
        self.good_character.status = CharacterStatus.GOOD
        self.good_character.is_alive.return_value = True
        self.good_character.is_conscious.return_value = True
        
        self.injured_character = Mock(spec=Character)
        self.injured_character.name = "負傷したキャラクター"
        self.injured_character.status = CharacterStatus.INJURED
        self.injured_character.is_alive.return_value = True
        self.injured_character.is_conscious.return_value = False
        
        self.dead_character = Mock(spec=Character)
        self.dead_character.name = "死亡したキャラクター"
        self.dead_character.status = CharacterStatus.DEAD
        self.dead_character.is_alive.return_value = False
        self.dead_character.is_conscious.return_value = False
    
    def _create_mock_party(self, characters):
        """モックパーティを作成"""
        party = Mock(spec=Party)
        party.name = "テストパーティ"
        party.members = characters
        
        # get_living_charactersの実装
        living_chars = [char for char in characters if char.is_alive()]
        party.get_living_characters.return_value = living_chars
        
        # get_conscious_charactersの実装
        conscious_chars = [char for char in characters if char.is_conscious()]
        party.get_conscious_characters.return_value = conscious_chars
        
        return party
    
    def test_overworld_manager_with_good_characters(self):
        """健康なキャラクターがいる場合のダンジョン入場テスト"""
        party = self._create_mock_party([self.good_character])
        
        with patch('src.overworld.overworld_manager.OverworldManager.__init__', return_value=None):
            overworld_manager = OverworldManager()
            overworld_manager.current_party = party
            overworld_manager._show_error_dialog = Mock()
            overworld_manager.enter_dungeon_callback = Mock()
            
            # _enter_dungeonメソッドを直接テスト
            overworld_manager._enter_dungeon()
            
            # エラーダイアログが表示されないことを確認
            overworld_manager._show_error_dialog.assert_not_called()
            # ダンジョン入場コールバックが呼ばれることを確認
            overworld_manager.enter_dungeon_callback.assert_called_once()
    
    def test_overworld_manager_with_injured_characters_should_allow_entry(self):
        """負傷したキャラクターがいる場合でもダンジョン入場を許可すべき"""
        party = self._create_mock_party([self.injured_character])
        
        with patch('src.overworld.overworld_manager.OverworldManager.__init__', return_value=None):
            overworld_manager = OverworldManager()
            overworld_manager.current_party = party
            overworld_manager._show_error_dialog = Mock()
            overworld_manager.enter_dungeon_callback = Mock()
            
            # 修正後の_enter_dungeonメソッドをテスト
            overworld_manager._enter_dungeon()
            
            # エラーダイアログが表示されないことを確認（修正後）
            overworld_manager._show_error_dialog.assert_not_called()
            # ダンジョン入場コールバックが呼ばれることを確認
            overworld_manager.enter_dungeon_callback.assert_called_once()
    
    def test_overworld_manager_with_mixed_characters(self):
        """健康・負傷・死亡が混在する場合のテスト"""
        party = self._create_mock_party([
            self.good_character, 
            self.injured_character, 
            self.dead_character
        ])
        
        with patch('src.overworld.overworld_manager.OverworldManager.__init__', return_value=None):
            overworld_manager = OverworldManager()
            overworld_manager.current_party = party
            overworld_manager._show_error_dialog = Mock()
            overworld_manager.enter_dungeon_callback = Mock()
            
            # 生存者がいるのでダンジョン入場を許可すべき
            overworld_manager._enter_dungeon()
            
            overworld_manager._show_error_dialog.assert_not_called()
            overworld_manager.enter_dungeon_callback.assert_called_once()
    
    def test_overworld_manager_with_only_dead_characters(self):
        """全員死亡している場合のテスト"""
        party = self._create_mock_party([self.dead_character])
        
        with patch('src.overworld.overworld_manager.OverworldManager.__init__', return_value=None):
            overworld_manager = OverworldManager()
            overworld_manager.current_party = party
            overworld_manager._show_error_dialog = Mock()
            overworld_manager.enter_dungeon_callback = Mock()
            
            # 全員死亡の場合はダンジョン入場を拒否すべき
            overworld_manager._enter_dungeon()
            
            # エラーダイアログが表示されることを確認
            overworld_manager._show_error_dialog.assert_called_once()
            # ダンジョン入場コールバックは呼ばれないことを確認
            overworld_manager.enter_dungeon_callback.assert_not_called()
    
    def test_game_manager_transition_consistency(self):
        """GameManagerとOverworldManagerのチェック基準の一貫性テスト"""
        party = self._create_mock_party([self.injured_character])
        
        with patch('src.core.game_manager.GameManager.__init__', return_value=None):
            game_manager = GameManager()
            game_manager.current_party = party
            game_manager.current_location = "overworld"
            game_manager.dungeon_manager = Mock()
            game_manager.dungeon_renderer = Mock()
            
            # transition_to_dungeonメソッドをテスト
            try:
                game_manager.transition_to_dungeon()
                # 例外が発生しないことを確認（負傷者でも生存しているため）
                success = True
            except Exception:
                success = False
            
            # 負傷したキャラクターでもダンジョン遷移が成功することを確認
            self.assertTrue(success, "負傷したキャラクターでもダンジョン遷移が可能であるべき")
    
    def test_error_message_consistency(self):
        """エラーメッセージの一貫性テスト"""
        party = self._create_mock_party([self.dead_character])
        
        with patch('src.overworld.overworld_manager.OverworldManager.__init__', return_value=None):
            overworld_manager = OverworldManager()
            overworld_manager.current_party = party
            overworld_manager._show_error_dialog = Mock()
            overworld_manager.enter_dungeon_callback = Mock()
            
            overworld_manager._enter_dungeon()
            
            # エラーメッセージが「生存している」に関する内容であることを確認
            call_args = overworld_manager._show_error_dialog.call_args
            if call_args:
                error_message = call_args[0][1]  # 第2引数がメッセージ
                self.assertIn("生存", error_message, "エラーメッセージに「生存」が含まれるべき")


if __name__ == '__main__':
    unittest.main()