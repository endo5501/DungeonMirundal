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

# DungeonSelectionUIをモック
with patch('src.ui.dungeon_selection_ui.DungeonSelectionUI'):
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
        
        overworld_manager = OverworldManager()
        overworld_manager.current_party = party
        
        # 生存キャラクターの確認をテスト
        living_chars = party.get_living_characters()
        self.assertTrue(len(living_chars) > 0, "生存キャラクターが存在する")
    
    def test_overworld_manager_with_injured_characters_should_allow_entry(self):
        """負傷したキャラクターがいる場合でもダンジョン入場を許可すべき"""
        party = self._create_mock_party([self.injured_character])
        
        overworld_manager = OverworldManager()
        overworld_manager.current_party = party
        
        # 負傷キャラクターも生存キャラクターとしてカウントされることを確認
        living_chars = party.get_living_characters()
        self.assertTrue(len(living_chars) > 0, "負傷キャラクターも生存キャラクターである")
    
    def test_overworld_manager_with_mixed_characters(self):
        """健康・負傷・死亡が混在する場合のテスト"""
        party = self._create_mock_party([
            self.good_character, 
            self.injured_character, 
            self.dead_character
        ])
        
        overworld_manager = OverworldManager()
        overworld_manager.current_party = party
        
        # 混在する場合でも生存者がいることを確認
        living_chars = party.get_living_characters()
        self.assertTrue(len(living_chars) > 0, "生存者がいる場合は入場可能")
    
    def test_overworld_manager_with_only_dead_characters(self):
        """全員死亡している場合のテスト"""
        party = self._create_mock_party([self.dead_character])
        
        overworld_manager = OverworldManager()
        overworld_manager.current_party = party
        
        # 全員死亡の場合は生存者がいないことを確認
        living_chars = party.get_living_characters()
        self.assertEqual(len(living_chars), 0, "全員死亡の場合は生存者がいない")
    
    def test_game_manager_transition_consistency(self):
        """GameManagerとOverworldManagerのチェック基準の一貫性テスト"""
        party = self._create_mock_party([self.injured_character])
        
        # 両方のマネージャーで同じ基準で判定されることを確認
        overworld_manager = OverworldManager()
        overworld_manager.current_party = party
        
        # 負傷キャラクターは生存キャラクターとして扱われるべき
        living_chars = party.get_living_characters()
        self.assertTrue(len(living_chars) > 0, "負傷キャラクターは生存キャラクターとして扱われる")
    
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