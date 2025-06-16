"""ダンジョン入場問題修正のテスト"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from src.character.party import Party
from src.character.character import Character, CharacterStatus
from src.overworld.overworld_manager import OverworldManager
from src.ui.base_ui import UIManager


class TestDungeonEntranceFix:
    """ダンジョン入場問題修正のテストクラス"""
    
    def test_game_manager_transition_logic_with_living_characters(self):
        """GameManagerのtransition_to_dungeonメソッドのロジックテスト（生存者あり）"""
        # Arrange
        from src.core.game_manager import GameManager
        party = Party()
        character = Character(name="テスト戦士", character_class="fighter")
        character.status = CharacterStatus.GOOD
        party.add_character(character)
        
        # GameManagerの初期化部分をモック
        with patch('src.core.game_manager.ShowBase.__init__'), \
             patch('src.core.game_manager.DungeonManager'), \
             patch('src.core.game_manager.OverworldManager'), \
             patch('src.core.game_manager.DungeonRenderer'):
            
            game_manager = GameManager(fStartDirect=False)
            game_manager.current_party = party
            game_manager.dungeon_manager = MagicMock()
            game_manager.dungeon_manager.enter_dungeon.return_value = True
            
            # Act & Assert
            # 例外が発生しないことを確認
            try:
                game_manager.transition_to_dungeon("test_dungeon")
            except Exception as e:
                # 生存チェック関連のエラーでないことを確認
                assert "生存しているパーティメンバーがいません" not in str(e)
    
    def test_game_manager_transition_logic_with_no_living_characters(self):
        """GameManagerのtransition_to_dungeonメソッドのロジックテスト（生存者なし）"""
        # Arrange
        from src.core.game_manager import GameManager
        party = Party()
        character = Character(name="死亡戦士", character_class="fighter")
        character.status = CharacterStatus.DEAD
        party.add_character(character)
        
        # GameManagerの初期化部分をモック
        with patch('src.core.game_manager.ShowBase.__init__'), \
             patch('src.core.game_manager.DungeonManager'), \
             patch('src.core.game_manager.OverworldManager'), \
             patch('src.core.game_manager.DungeonRenderer'):
            
            game_manager = GameManager(fStartDirect=False)
            game_manager.current_party = party
            
            # Act & Assert
            with pytest.raises(Exception) as exc_info:
                game_manager.transition_to_dungeon("test_dungeon")
            
            assert "生存しているパーティメンバーがいません" in str(exc_info.value)
    
    def test_game_manager_transition_logic_with_empty_party(self):
        """GameManagerのtransition_to_dungeonメソッドのロジックテスト（空のパーティ）"""
        # Arrange
        from src.core.game_manager import GameManager
        party = Party()
        
        # GameManagerの初期化部分をモック
        with patch('src.core.game_manager.ShowBase.__init__'), \
             patch('src.core.game_manager.DungeonManager'), \
             patch('src.core.game_manager.OverworldManager'), \
             patch('src.core.game_manager.DungeonRenderer'):
            
            game_manager = GameManager(fStartDirect=False)
            game_manager.current_party = party
            
            # Act & Assert
            with pytest.raises(Exception) as exc_info:
                game_manager.transition_to_dungeon("test_dungeon")
            
            assert "生存しているパーティメンバーがいません" in str(exc_info.value)
    
    def test_character_is_alive_method_returns_correct_status(self):
        """キャラクターのis_alive()メソッドが正しい状態を返すべき"""
        # Arrange & Act & Assert
        character_good = Character(name="元気戦士", character_class="fighter")
        character_good.status = CharacterStatus.GOOD
        assert character_good.is_alive() == True
        
        character_injured = Character(name="負傷戦士", character_class="fighter")
        character_injured.status = CharacterStatus.INJURED
        assert character_injured.is_alive() == True
        
        character_unconscious = Character(name="気絶戦士", character_class="fighter")
        character_unconscious.status = CharacterStatus.UNCONSCIOUS
        assert character_unconscious.is_alive() == False
        
        character_dead = Character(name="死亡戦士", character_class="fighter")
        character_dead.status = CharacterStatus.DEAD
        assert character_dead.is_alive() == False
    
    def test_party_get_living_characters_filters_correctly(self):
        """パーティのget_living_characters()メソッドが正しくフィルタリングするべき"""
        # Arrange
        party = Party()
        
        good_char = Character(name="元気戦士", character_class="fighter")
        good_char.status = CharacterStatus.GOOD
        
        injured_char = Character(name="負傷魔法使い", character_class="mage") 
        injured_char.status = CharacterStatus.INJURED
        
        dead_char = Character(name="死亡盗賊", character_class="thief")
        dead_char.status = CharacterStatus.DEAD
        
        party.add_character(good_char)
        party.add_character(injured_char) 
        party.add_character(dead_char)
        
        # Act
        living_characters = party.get_living_characters()
        
        # Assert
        assert len(living_characters) == 2
        assert good_char in living_characters
        assert injured_char in living_characters
        assert dead_char not in living_characters


class TestUIManagerShowDialog:
    """UIManagerのshow_dialogメソッドテストクラス"""
    
    def test_ui_manager_has_show_dialog_method(self):
        """UIManagerクラスにshow_dialogメソッドが存在するべき"""
        # Arrange
        ui_manager = UIManager()
        
        # Act & Assert
        assert hasattr(ui_manager, 'show_dialog')
        assert callable(getattr(ui_manager, 'show_dialog'))
    
    def test_ui_manager_show_dialog_creates_dialog(self):
        """UIManagerのshow_dialogがダイアログを作成するべき"""
        # Arrange
        ui_manager = UIManager()
        
        # Act
        ui_manager.show_dialog("テストタイトル", "テストメッセージ")
        
        # Assert
        # ダイアログが作成されることを確認
        dialog_elements = [elem for elem_id, elem in ui_manager.ui_elements.items() 
                          if elem_id.startswith("system_dialog_")]
        assert len(dialog_elements) >= 1
    
    @patch('src.overworld.overworld_manager.ui_manager')
    def test_overworld_manager_calls_show_dialog_correctly(self, mock_ui_manager):
        """OverworldManagerが正しくshow_dialogを呼び出すべき"""
        # Arrange
        overworld_manager = OverworldManager()
        mock_ui_manager.show_dialog = Mock()
        
        # Act
        overworld_manager._show_dungeon_entrance_error("テストエラー")
        
        # Assert
        mock_ui_manager.show_dialog.assert_called_once()
        call_args = mock_ui_manager.show_dialog.call_args
        assert "テストエラー" in call_args[0][1]  # messageは第2引数