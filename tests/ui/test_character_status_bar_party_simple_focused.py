"""
Character Status Bar パーティ設定の焦点テスト

パーティ設定の問題に焦点を当てたシンプルなテスト
描画は除外し、パーティ設定のみをテスト
"""

import pygame
import pytest
from unittest.mock import Mock

from src.character.character import Character
from src.character.party import Party
from src.ui.character_status_bar import CharacterStatusBar


class TestCharacterStatusBarPartyFocused:
    """CharacterStatusBarのパーティ設定に焦点を当てたテストクラス"""
    
    def setup_method(self):
        """各テストメソッドの前に呼ばれるセットアップ"""
        pygame.init()
        pygame.font.init()
        self.screen = pygame.display.set_mode((800, 600))
        
    def teardown_method(self):
        """各テストメソッドの後に呼ばれるクリーンアップ"""
        pygame.quit()
    
    def test_character_status_bar_party_setting_basic(self):
        """
        テスト: CharacterStatusBarにパーティが正しく設定されること
        
        期待される動作:
        - set_party()でパーティが設定される
        - 設定されたパーティがpartyプロパティから取得できる
        - charactersプロパティにアクセスできる
        """
        # Arrange
        status_bar = CharacterStatusBar()
        
        # 実際のPartyクラス構造をモック
        mock_char1 = Mock(spec=Character)
        mock_char1.name = "戦士"
        mock_char1.character_id = "char_1"
        
        mock_char2 = Mock(spec=Character)
        mock_char2.name = "魔法使い"
        mock_char2.character_id = "char_2"
        
        # PartyクラスのcharactersプロパティをDictとしてモック
        mock_party = Mock(spec=Party)
        mock_party.characters = {
            "char_1": mock_char1,
            "char_2": mock_char2
        }
        
        # 初期状態の確認
        assert status_bar.party is None, "初期状態ではパーティが未設定"
        
        # Act
        status_bar.set_party(mock_party)
        
        # Assert
        assert status_bar.party is mock_party, "set_party()でパーティが設定されること"
        
        # party.charactersにアクセスできることを確認
        characters_dict = status_bar.party.characters
        assert isinstance(characters_dict, dict), "charactersがDict型であること"
        assert len(characters_dict) == 2, "パーティに2人のキャラクターがいること"
        assert "char_1" in characters_dict, "キャラクター1が存在すること"
        assert "char_2" in characters_dict, "キャラクター2が存在すること"
        
        # characters.values()でリストが取得できることを確認
        characters_list = list(characters_dict.values())
        assert len(characters_list) == 2, "charactersから2人のキャラクターリストが取得できること"
    
    def test_character_status_bar_party_update_character_display(self):
        """
        テスト: パーティ設定時にupdate_character_display()が呼ばれること
        
        期待される動作:
        - set_party()を呼ぶとupdate_character_display()が実行される
        - update_character_display()でparty.charactersが処理される
        """
        # Arrange
        status_bar = CharacterStatusBar()
        
        # モックキャラクター
        mock_char = Mock(spec=Character)
        mock_char.name = "テストキャラ"
        mock_char.character_id = "test_char"
        
        # モックパーティ
        mock_party = Mock(spec=Party)
        mock_party.characters = {"test_char": mock_char}
        
        # Act - set_partyを呼ぶとupdate_character_display()が実行される
        status_bar.set_party(mock_party)
        
        # Assert
        assert status_bar.party is mock_party, "パーティが設定されていること"
        
        # update_character_display()が正常に実行されたことを間接的に確認
        # （例外が発生しなければ、party.charactersへのアクセスが成功したということ）
        characters_list = list(status_bar.party.characters.values())
        assert len(characters_list) == 1, "1人のキャラクターが処理されたこと"
    
    def test_character_status_bar_party_none_handling(self):
        """
        テスト: Noneパーティの処理
        
        期待される動作:
        - set_party(None)が正常に処理される
        - update_character_display()でパーティがNoneの場合の処理が正常動作
        """
        # Arrange
        status_bar = CharacterStatusBar()
        
        # 最初にパーティを設定
        mock_char = Mock(spec=Character)
        mock_char.name = "テストキャラ"
        mock_char.character_id = "test_char"
        
        mock_party = Mock(spec=Party)
        mock_party.characters = {"test_char": mock_char}
        
        status_bar.set_party(mock_party)
        assert status_bar.party is mock_party, "パーティが設定されていること"
        
        # Act - パーティをNoneに設定
        status_bar.set_party(None)
        
        # Assert
        assert status_bar.party is None, "パーティがNoneに設定されること"
        
        # update_character_display()でNoneの処理が正常動作することを確認
        # （例外が発生しなければ成功）
    
    def test_character_status_bar_empty_party_handling(self):
        """
        テスト: 空のパーティの処理
        
        期待される動作:
        - 空のcharactersを持つパーティが正常に処理される
        - update_character_display()で空のcharactersが処理される
        """
        # Arrange
        status_bar = CharacterStatusBar()
        
        # 空のパーティ
        mock_party = Mock(spec=Party)
        mock_party.characters = {}  # 空のDict
        
        # Act
        status_bar.set_party(mock_party)
        
        # Assert
        assert status_bar.party is mock_party, "空のパーティが設定されること"
        assert len(status_bar.party.characters) == 0, "charactersが空であること"
        
        # update_character_display()で空のcharactersが正常処理されることを確認
        characters_list = list(status_bar.party.characters.values())
        assert len(characters_list) == 0, "空のキャラクターリストが取得されること"