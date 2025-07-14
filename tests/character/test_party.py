"""パーティシステムのテスト"""

import pytest
from src.character.character import Character
from src.character.stats import BaseStats
from src.character.party import Party, PartyPosition


@pytest.mark.unit
class TestParty:
    """Partyのテスト"""
    
    def setup_method(self):
        """各テストメソッドの前に実行"""
        self.party = Party(name="Test Party")
        
        # テストキャラクター作成
        stats = BaseStats(strength=15, agility=12, intelligence=14, faith=10, luck=13)
        self.character1 = Character.create_character("Hero1", "human", "fighter", stats)
        self.character2 = Character.create_character("Hero2", "elf", "mage", stats)
    
    def test_add_character(self):
        """キャラクター追加のテスト"""
        success = self.party.add_character(self.character1)
        
        assert success == True
        assert len(self.party.characters) == 1
        assert self.character1.character_id in self.party.characters
    
    def test_remove_character(self):
        """キャラクター削除のテスト"""
        self.party.add_character(self.character1)
        success = self.party.remove_character(self.character1.character_id)
        
        assert success == True
        assert len(self.party.characters) == 0
    
    def test_party_formation(self):
        """パーティ編成のテスト"""
        self.party.add_character(self.character1, PartyPosition.FRONT_1)
        self.party.add_character(self.character2, PartyPosition.BACK_1)
        
        front_chars = self.party.get_front_row_characters()
        back_chars = self.party.get_back_row_characters()
        
        assert len(front_chars) == 1
        assert front_chars[0].character_id == self.character1.character_id
        assert len(back_chars) == 1
        assert back_chars[0].character_id == self.character2.character_id
    
    def test_party_serialization(self):
        """パーティシリアライゼーションのテスト"""
        self.party.add_character(self.character1)
        self.party.add_character(self.character2)
        
        # 辞書化してから復元
        data = self.party.to_dict()
        restored = Party.from_dict(data)
        
        assert restored.name == self.party.name
        assert len(restored.characters) == 2
        assert restored.gold == self.party.gold
    
    def test_party_capacity(self):
        """パーティ人数制限のテスト"""
        # 6人まで追加可能（仮定）
        for i in range(6):
            stats = BaseStats(strength=10)
            char = Character.create_character(f"Hero{i}", "human", "fighter", stats)
            success = self.party.add_character(char)
            assert success == True
        
        # 7人目は追加できない
        extra_char = Character.create_character("Extra", "human", "fighter", BaseStats(strength=10))
        success = self.party.add_character(extra_char)
        assert success == False or len(self.party.characters) <= 6