"""SpellSlotManager テストケース

Fowler Extract Classパターンで抽出されたクラスのテスト
"""

import pytest
from unittest.mock import Mock

from src.ui.window_system.spell_slot_manager import (
    SpellSlotManager, 
    SlotOperation, 
    SlotOperationResult
)
from src.character.character import Character
from src.magic.spells import SpellBook


class TestSpellSlotManager:
    """SpellSlotManager テストクラス"""
    
    def setup_method(self):
        """テスト前セットアップ"""
        self.slot_manager = SpellSlotManager()
        
        # モックオブジェクト
        self.mock_character = Mock(spec=Character)
        self.mock_spellbook = Mock(spec=SpellBook)
        
        # キャラクターのモック設定
        self.mock_character.name = "テストキャラクター"
        self.mock_character.get_spellbook.return_value = self.mock_spellbook
    
    def test_equip_spell_to_slot_success(self):
        """魔法装備成功のテスト"""
        result = self.slot_manager.equip_spell_to_slot(
            self.mock_character, "spell_1", 1, 0
        )
        
        assert isinstance(result, SlotOperationResult)
        assert result.success is True
        assert "装備しました" in result.message
        assert result.data['spell_id'] == "spell_1"
        assert result.data['level'] == 1
        assert result.data['slot_index'] == 0
    
    def test_equip_spell_to_slot_no_character(self):
        """キャラクターなしでの装備テスト"""
        result = self.slot_manager.equip_spell_to_slot(None, "spell_1", 1, 0)
        
        assert result.success is False
        assert "キャラクターが指定されていません" in result.message
    
    def test_unequip_spell_from_slot_success(self):
        """魔法装備解除成功のテスト"""
        result = self.slot_manager.unequip_spell_from_slot(
            self.mock_character, 1, 0
        )
        
        assert isinstance(result, SlotOperationResult)
        assert result.success is True
        assert "装備を解除しました" in result.message
        assert result.data['level'] == 1
        assert result.data['slot_index'] == 0
    
    def test_use_spell_from_slot_success(self):
        """魔法使用成功のテスト"""
        result = self.slot_manager.use_spell_from_slot(
            self.mock_character, 1, 0
        )
        
        assert isinstance(result, SlotOperationResult)
        assert result.success is True
        assert "使用しました" in result.message
        assert result.data['level'] == 1
        assert result.data['slot_index'] == 0
    
    def test_restore_slot_uses_success(self):
        """スロット使用回数回復成功のテスト"""
        result = self.slot_manager.restore_slot_uses(
            self.mock_character, 1, 0
        )
        
        assert isinstance(result, SlotOperationResult)
        assert result.success is True
        assert "使用回数を回復しました" in result.message
        assert result.data['level'] == 1
        assert result.data['slot_index'] == 0
    
    def test_restore_all_spell_uses_success(self):
        """全魔法使用回数回復成功のテスト"""
        result = self.slot_manager.restore_all_spell_uses(self.mock_character)
        
        assert isinstance(result, SlotOperationResult)
        assert result.success is True
        assert "全ての魔法スロットの使用回数を回復しました" in result.message
        assert result.data['character'] == "テストキャラクター"
    
    def test_get_available_spells_for_slot(self):
        """スロット用利用可能魔法取得のテスト"""
        # 魔法書のlearned_spellsを設定
        self.mock_spellbook.learned_spells = ["spell_1", "spell_2", "spell_3"]
        
        available_spells = self.slot_manager.get_available_spells_for_slot(
            self.mock_character, 2
        )
        
        assert len(available_spells) == 3
        for spell in available_spells:
            assert 'spell_id' in spell
            assert 'name' in spell
            assert 'level' in spell
            assert 'can_equip' in spell
    
    def test_add_operation_callback(self):
        """操作コールバック追加のテスト"""
        callback_called = False
        callback_data = None
        
        def test_callback(data):
            nonlocal callback_called, callback_data
            callback_called = True
            callback_data = data
        
        # コールバック追加
        self.slot_manager.add_operation_callback(SlotOperation.EQUIP, test_callback)
        
        # 装備操作実行
        self.slot_manager.equip_spell_to_slot(
            self.mock_character, "spell_1", 1, 0
        )
        
        # コールバックが呼ばれたことを確認
        assert callback_called is True
        assert callback_data is not None
        assert callback_data['spell_id'] == "spell_1"
    
    def test_operation_result_class(self):
        """SlotOperationResultクラスのテスト"""
        result = SlotOperationResult(True, "成功", {"key": "value"})
        
        assert result.success is True
        assert result.message == "成功"
        assert result.data == {"key": "value"}
        
        # 失敗ケース
        result_fail = SlotOperationResult(False, "失敗")
        assert result_fail.success is False
        assert result_fail.message == "失敗"
        assert result_fail.data is None