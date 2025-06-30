"""
OverworldManager.set_party()メソッドのテスト
"""

import pygame
import pytest
from unittest.mock import Mock, patch

from src.character.character import Character
from src.character.party import Party
from src.overworld.overworld_manager_pygame import OverworldManager


class TestOverworldManagerSetParty:
    """OverworldManager.set_party()メソッドのテストクラス"""
    
    def setup_method(self):
        """各テストメソッドの前に呼ばれるセットアップ"""
        pygame.init()
        pygame.font.init()
        self.screen = pygame.display.set_mode((800, 600))
        
    def teardown_method(self):
        """各テストメソッドの後に呼ばれるクリーンアップ"""
        pygame.quit()
    
    def test_set_party_basic_functionality(self):
        """
        テスト: set_party()の基本機能
        
        期待される動作:
        - current_partyが設定される
        - CharacterStatusBarにパーティが設定される
        """
        # Arrange
        with patch('pygame.display.set_mode'), \
             patch('pygame.mixer.init'):
            
            # UIManagerのモック
            mock_ui_manager = Mock()
            
            # OverworldManager初期化
            overworld_manager = OverworldManager()
            overworld_manager.set_ui_manager(mock_ui_manager)
            
            # テストパーティ作成
            mock_char = Mock(spec=Character)
            mock_char.name = "テストキャラ"
            mock_char.character_id = "test_char"
            
            mock_party = Mock(spec=Party)
            mock_party.name = "テストパーティ"
            mock_party.characters = {"test_char": mock_char}
            
            # Act
            overworld_manager.set_party(mock_party)
            
            # Assert
            assert overworld_manager.current_party is mock_party, \
                "current_partyが設定されること"
            
            # CharacterStatusBarにパーティが設定されることを確認
            assert overworld_manager.character_status_bar is not None, \
                "CharacterStatusBarが初期化されていること"
            assert overworld_manager.character_status_bar.party is mock_party, \
                "CharacterStatusBarにパーティが設定されること"
    
    def test_set_party_none_handling(self):
        """
        テスト: set_party(None)の処理
        
        期待される動作:
        - current_partyがNoneになる
        - CharacterStatusBarのパーティもNoneになる
        """
        # Arrange
        with patch('pygame.display.set_mode'), \
             patch('pygame.mixer.init'):
            
            mock_ui_manager = Mock()
            overworld_manager = OverworldManager()
            overworld_manager.set_ui_manager(mock_ui_manager)
            
            # 最初にパーティを設定
            mock_party = Mock(spec=Party)
            mock_party.name = "テストパーティ"
            mock_party.characters = {}
            
            overworld_manager.set_party(mock_party)
            assert overworld_manager.current_party is mock_party
            
            # Act - パーティをNoneに設定
            overworld_manager.set_party(None)
            
            # Assert
            assert overworld_manager.current_party is None, \
                "current_partyがNoneになること"
            assert overworld_manager.character_status_bar.party is None, \
                "CharacterStatusBarのパーティもNoneになること"
    
    def test_set_party_synchronization(self):
        """
        テスト: current_partyとCharacterStatusBarの同期
        
        期待される動作:
        - 複数回のset_party()呼び出しで常に同期が保たれる
        - current_partyとCharacterStatusBarのpartyが常に同じオブジェクトを参照
        """
        # Arrange
        with patch('pygame.display.set_mode'), \
             patch('pygame.mixer.init'):
            
            mock_ui_manager = Mock()
            overworld_manager = OverworldManager()
            overworld_manager.set_ui_manager(mock_ui_manager)
            
            # 複数のパーティを作成
            party1 = Mock(spec=Party)
            party1.name = "パーティ1"
            party1.characters = {}
            
            party2 = Mock(spec=Party)
            party2.name = "パーティ2"
            party2.characters = {}
            
            # Act & Assert
            # パーティ1を設定
            overworld_manager.set_party(party1)
            assert overworld_manager.current_party is party1
            assert overworld_manager.character_status_bar.party is party1
            
            # パーティ2に変更
            overworld_manager.set_party(party2)
            assert overworld_manager.current_party is party2
            assert overworld_manager.character_status_bar.party is party2
            
            # Noneに変更
            overworld_manager.set_party(None)
            assert overworld_manager.current_party is None
            assert overworld_manager.character_status_bar.party is None
    
    def test_enter_overworld_uses_set_party(self):
        """
        テスト: enter_overworld()がset_party()を使用すること
        
        期待される動作:
        - enter_overworld()呼び出し後、set_party()と同じ状態になる
        - パーティの同期が正しく行われる
        """
        # Arrange
        with patch('pygame.display.set_mode'), \
             patch('pygame.mixer.init'):
            
            mock_ui_manager = Mock()
            overworld_manager = OverworldManager()
            overworld_manager.set_ui_manager(mock_ui_manager)
            
            # テストパーティ作成
            mock_party = Mock(spec=Party)
            mock_party.name = "入場テストパーティ"
            mock_party.characters = {}
            
            # Act
            result = overworld_manager.enter_overworld(mock_party)
            
            # Assert
            assert result is True, "enter_overworld()が成功すること"
            assert overworld_manager.current_party is mock_party, \
                "current_partyが設定されること"
            assert overworld_manager.character_status_bar.party is mock_party, \
                "CharacterStatusBarにパーティが設定されること"
            assert overworld_manager.is_active is True, \
                "地上部がアクティブになること"