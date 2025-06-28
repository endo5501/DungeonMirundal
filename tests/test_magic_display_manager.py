"""MagicDisplayManager テストケース

Fowler Extract Classパターンで抽出されたクラスのテスト
"""

import pytest
from unittest.mock import Mock

from src.ui.window_system.magic_display_manager import MagicDisplayManager, SpellDisplayFormat
from src.character.party import Party
from src.character.character import Character
from src.magic.spells import SpellBook


class TestMagicDisplayManager:
    """MagicDisplayManager テストクラス"""
    
    def setup_method(self):
        """テスト前セットアップ"""
        self.display_manager = MagicDisplayManager()
        
        # モックオブジェクト
        self.mock_party = Mock(spec=Party)
        self.mock_character = Mock(spec=Character)
        self.mock_spellbook = Mock(spec=SpellBook)
        
        # キャラクターのモック設定
        self.mock_character.name = "テストキャラクター"
        self.mock_character.get_spellbook.return_value = self.mock_spellbook
        self.mock_party.get_all_characters.return_value = [self.mock_character]
        
        # 魔法書のモック設定
        self.mock_spellbook.get_spell_summary.return_value = {
            'learned_count': 5,
            'equipped_slots': 3,
            'total_slots': 6,
            'available_uses': 2,
            'slots_by_level': {
                1: {'equipped': 2, 'total': 3, 'available': 1},
                2: {'equipped': 1, 'total': 3, 'available': 1}
            }
        }
    
    def test_format_party_magic_summary(self):
        """パーティ魔法サマリーのフォーマットテスト"""
        summaries = self.display_manager.format_party_magic_summary(self.mock_party)
        
        assert len(summaries) == 1
        summary = summaries[0]
        
        assert summary['character'] == self.mock_character
        assert summary['name'] == "テストキャラクター"
        assert summary['learned_count'] == 5
        assert summary['equipped_slots'] == 3
        assert "習得:5" in summary['display_text']
        assert "装備:3" in summary['display_text']
    
    def test_format_party_magic_summary_empty_party(self):
        """空のパーティでのテスト"""
        summaries = self.display_manager.format_party_magic_summary(None)
        assert summaries == []
    
    def test_format_character_spell_slots(self):
        """キャラクター魔法スロットのフォーマットテスト"""
        slots = self.display_manager.format_character_spell_slots(self.mock_character)
        
        assert 1 in slots
        assert 2 in slots
        
        level1_slot = slots[1]
        assert level1_slot['level'] == 1
        assert level1_slot['equipped'] == 2
        assert level1_slot['total'] == 3
        assert level1_slot['available'] == 1
        assert "レベル1" in level1_slot['display_text']
    
    def test_format_character_spell_slots_no_character(self):
        """キャラクターなしでのテスト"""
        slots = self.display_manager.format_character_spell_slots(None)
        assert slots == {}
    
    def test_format_party_magic_statistics(self):
        """パーティ魔法統計のフォーマットテスト"""
        stats = self.display_manager.format_party_magic_statistics(self.mock_party)
        
        assert stats['total_learned'] == 5
        assert stats['total_equipped'] == 3
        assert stats['total_available'] == 2
        assert len(stats['character_stats']) == 1
        
        char_stat = stats['character_stats'][0]
        assert char_stat['name'] == "テストキャラクター"
        assert char_stat['learned'] == 5
        assert char_stat['equipped'] == 3
        assert char_stat['available'] == 2
    
    def test_get_school_name(self):
        """学派名取得のテスト"""
        assert self.display_manager.get_school_name('mage') == "魔術"
        assert self.display_manager.get_school_name('priest') == "神聖"
        assert self.display_manager.get_school_name('both') == "汎用"
        assert self.display_manager.get_school_name('unknown') == "unknown"
    
    def test_get_type_name(self):
        """魔法種別名取得のテスト"""
        assert self.display_manager.get_type_name('offensive') == "攻撃"
        assert self.display_manager.get_type_name('healing') == "回復"
        assert self.display_manager.get_type_name('buff') == "強化"
        assert self.display_manager.get_type_name('unknown') == "unknown"