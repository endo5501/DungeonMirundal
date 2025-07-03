"""
EquipmentOperationHandler のテスト

Equipment Manager 85-94%重複を統合したハンドラーのテスト
具体的な装備操作に焦点を当てた機能テスト
"""

import pytest
import pygame
from unittest.mock import Mock, patch, MagicMock
from src.equipment.equipment_operation_handler import (
    EquipmentOperationHandler, EquipmentOperationResult, EquipmentCommand, 
    EquipmentOperationType
)
from src.character.character import Character


class TestEquipmentOperationHandler:
    """EquipmentOperationHandler のテストクラス"""
    
    def setup_method(self):
        """各テストメソッドの前に実行される"""
        pygame.init()
        pygame.display.set_mode((1, 1), pygame.NOFRAME)
        
        # モックオブジェクト作成
        self.mock_character = Mock(spec=Character)
        self.mock_character.name = "Test Character"
        self.mock_character.level = 10
        self.mock_character.character_class = "fighter"
        
        self.mock_equipment_slots = Mock()
        self.mock_inventory = Mock()
        
        # ハンドラー作成
        self.handler = EquipmentOperationHandler(
            character=self.mock_character,
            equipment_slots=self.mock_equipment_slots,
            inventory=self.mock_inventory
        )
    
    def teardown_method(self):
        """各テストメソッドの後に実行される"""
        pygame.quit()
    
    def test_equipment_operation_handler_initialization(self):
        """EquipmentOperationHandlerの初期化を確認"""
        # Then: 正しく初期化される
        assert self.handler.character == self.mock_character
        assert self.handler.equipment_slots == self.mock_equipment_slots
        assert self.handler.inventory == self.mock_inventory
        assert self.handler.selected_slot is None
        assert self.handler.quick_slots == {}
    
    def test_equipment_operation_template_method_pattern(self):
        """Template Methodパターンが正しく動作することを確認"""
        # Given: 有効なスロット情報を持つequipment_slots
        self.mock_equipment_slots.get_slot.return_value = Mock(item=None)
        
        # When: スロット情報取得操作を実行
        result = self.handler.execute_equipment_operation('get_slot_info', slot_type='weapon')
        
        # Then: Template Methodの流れで実行される
        assert isinstance(result, EquipmentOperationResult)
        assert result.success is True
        assert result.data is not None
    
    def test_operation_validation_no_character(self):
        """キャラクター未設定時の検証を確認"""
        # Given: キャラクター未設定のハンドラー
        handler_no_char = EquipmentOperationHandler(
            character=None,
            equipment_slots=self.mock_equipment_slots,
            inventory=self.mock_inventory
        )
        
        # When: 装備操作を実行
        result = handler_no_char.execute_equipment_operation('equip_item', slot_type='weapon', item=Mock())
        
        # Then: 検証エラーが返される
        assert result.success is False
        assert result.error_type == 'no_character'
        assert 'キャラクターが設定されていません' in result.message
    
    def test_equip_item_operation_validation(self):
        """装備操作の検証を確認"""
        # When: 必須パラメータなしで装備操作を実行
        result = self.handler.execute_equipment_operation('equip_item')
        
        # Then: 検証エラーが返される
        assert result.success is False
        assert result.error_type == 'missing_slot_type'
        
        # When: アイテムなしで装備操作を実行
        result2 = self.handler.execute_equipment_operation('equip_item', slot_type='weapon')
        
        # Then: 検証エラーが返される
        assert result2.success is False
        assert result2.error_type == 'missing_item'
    
    def test_equip_item_successful_operation(self):
        """アイテム装備の成功ケースを確認"""
        # Given: 装備可能なアイテム
        mock_item = Mock()
        mock_item.name = "Test Sword"
        mock_item.required_level = 5
        mock_item.allowed_classes = ['fighter', 'warrior']
        
        # equipment_slotsのモック設定
        self.mock_equipment_slots.equip_item.return_value = True
        
        # When: アイテムを装備
        result = self.handler.execute_equipment_operation(
            'equip_item', 
            item=mock_item, 
            slot_type='weapon'
        )
        
        # Then: 装備が成功する
        assert result.success is True
        assert mock_item.name in result.message
        assert result.data['item'] == mock_item
        assert result.data['slot_type'] == 'weapon'
    
    def test_equip_item_level_requirement_check(self):
        """レベル制限チェックを確認"""
        # Given: レベル要求の高いアイテム
        mock_item = Mock()
        mock_item.required_level = 20  # キャラクターレベル10より高い
        mock_item.allowed_classes = ['fighter']
        
        # When: アイテムを装備
        result = self.handler.execute_equipment_operation(
            'equip_item', 
            item=mock_item, 
            slot_type='weapon'
        )
        
        # Then: レベル制限で失敗する
        assert result.success is False
        assert result.error_type == 'level_requirement'
        assert 'レベル 20 以上が必要です' in result.message
    
    def test_equip_item_class_restriction_check(self):
        """クラス制限チェックを確認"""
        # Given: クラス制限のあるアイテム
        mock_item = Mock()
        mock_item.required_level = 5
        mock_item.allowed_classes = ['wizard', 'cleric']  # fighterは含まれない
        
        # When: アイテムを装備
        result = self.handler.execute_equipment_operation(
            'equip_item', 
            item=mock_item, 
            slot_type='weapon'
        )
        
        # Then: クラス制限で失敗する
        assert result.success is False
        assert result.error_type == 'class_restriction'
        assert 'このクラスでは装備できません' in result.message
    
    def test_unequip_item_successful_operation(self):
        """装備解除の成功ケースを確認"""
        # Given: 装備されているアイテム
        equipped_item = Mock()
        equipped_item.name = "Current Armor"
        
        # スロット情報のモック
        self.mock_equipment_slots.get_slot.return_value = Mock(item=equipped_item)
        self.mock_equipment_slots.unequip_item.return_value = equipped_item
        
        # When: アイテムを装備解除
        result = self.handler.execute_equipment_operation('unequip_item', slot_type='armor')
        
        # Then: 装備解除が成功する
        assert result.success is True
        assert equipped_item.name in result.message
        assert result.data['item'] == equipped_item
        assert result.data['slot_type'] == 'armor'
    
    def test_unequip_item_nothing_equipped(self):
        """何も装備されていない場合の装備解除を確認"""
        # Given: 空のスロット
        self.mock_equipment_slots.get_slot.return_value = Mock(item=None)
        
        # When: 装備解除を試行
        result = self.handler.execute_equipment_operation('unequip_item', slot_type='weapon')
        
        # Then: 適切なエラーが返される
        assert result.success is False
        assert result.error_type == 'nothing_equipped'
        assert 'には何も装備されていません' in result.message
    
    def test_swap_equipment_successful_operation(self):
        """装備交換の成功ケースを確認"""
        # Given: 交換元にアイテムがある
        source_item = Mock()
        self.mock_equipment_slots.get_slot.side_effect = [
            Mock(item=source_item),  # from_slot
            Mock(item=None)          # to_slot (空でも可)
        ]
        self.mock_equipment_slots.swap_equipment.return_value = True
        
        # When: 装備を交換
        result = self.handler.execute_equipment_operation(
            'swap_equipment', 
            from_slot='weapon', 
            to_slot='armor'
        )
        
        # Then: 交換が成功する
        assert result.success is True
        assert 'weapon <-> armor' in result.message
        assert result.data['from_slot'] == 'weapon'
        assert result.data['to_slot'] == 'armor'
    
    def test_swap_equipment_source_empty(self):
        """交換元が空の場合の装備交換を確認"""
        # Given: 交換元が空
        self.mock_equipment_slots.get_slot.return_value = Mock(item=None)
        
        # When: 装備交換を試行
        result = self.handler.execute_equipment_operation(
            'swap_equipment', 
            from_slot='weapon', 
            to_slot='armor'
        )
        
        # Then: 適切なエラーが返される
        assert result.success is False
        assert result.error_type == 'source_slot_empty'
        assert 'にアイテムがありません' in result.message
    
    def test_get_all_slots_operation(self):
        """全スロット情報取得を確認"""
        # Given: 複数スロットのデータ
        slots_data = {
            'weapon': Mock(),
            'armor': Mock(),
            'accessory': Mock()
        }
        self.mock_equipment_slots.get_all_slots.return_value = slots_data
        self.mock_equipment_slots.get_slot.return_value = Mock()
        
        # When: 全スロット情報を取得
        result = self.handler.execute_equipment_operation('get_all_slots')
        
        # Then: 全スロット情報が返される
        assert result.success is True
        assert '全スロット情報を取得しました' in result.message
        assert isinstance(result.data, dict)
        assert len(result.data) == 3
    
    def test_validate_equipment_operation(self):
        """装備状態検証を確認"""
        # Given: 検証対象のスロット
        slots_data = {'weapon': Mock(), 'armor': Mock()}
        self.mock_equipment_slots.get_all_slots.return_value = slots_data
        
        # When: 装備状態を検証
        result = self.handler.execute_equipment_operation('validate_equipment')
        
        # Then: 検証結果が返される
        assert result.success is True
        assert '装備状態検証完了' in result.message
        assert 'valid' in result.data
        assert 'results' in result.data
    
    def test_create_comparison_operation(self):
        """装備比較作成を確認"""
        # Given: 現在のアイテムと新しいアイテム
        current_item = Mock()
        new_item = Mock()
        
        # スロット情報のモック
        self.mock_equipment_slots.get_slot.return_value = Mock(item=current_item)
        
        # When: 装備比較を作成
        result = self.handler.execute_equipment_operation(
            'create_comparison', 
            item=new_item, 
            slot_type='weapon'
        )
        
        # Then: 比較情報が作成される
        assert result.success is True
        assert '装備比較を作成しました' in result.message
        assert result.data['current_item'] == current_item
        assert result.data['new_item'] == new_item
        assert result.data['slot_type'] == 'weapon'
    
    def test_assign_quick_slot_operation(self):
        """クイックスロット割り当てを確認"""
        # When: クイックスロットを割り当て
        result = self.handler.execute_equipment_operation(
            'assign_quick_slot', 
            quick_slot_index=1, 
            slot_type='weapon'
        )
        
        # Then: 割り当てが成功する
        assert result.success is True
        assert 'クイックスロット 1 に weapon を割り当てました' in result.message
        assert self.handler.quick_slots[1] == 'weapon'
    
    def test_get_equippable_items_operation(self):
        """装備可能アイテム取得を確認"""
        # Given: インベントリにアイテム
        mock_items = [Mock(), Mock(), Mock()]
        self.mock_inventory.get_items.return_value = mock_items
        
        # アイテムの装備可能性をモック
        for item in mock_items:
            item.equipment_slot = 'weapon'
        
        # When: 装備可能アイテムを取得
        result = self.handler.execute_equipment_operation(
            'get_equippable_items', 
            slot_type='weapon'
        )
        
        # Then: 装備可能アイテムが返される
        assert result.success is True
        assert '装備可能アイテムを取得しました: 3個' in result.message
        assert len(result.data['items']) == 3
    
    def test_command_pattern_execution(self):
        """Commandパターンによる操作実行を確認"""
        # Given: 装備操作コマンド
        command = EquipmentCommand(
            operation='get_slot_info',
            params={'slot_type': 'weapon'},
            handler=self.handler
        )
        
        # スロット情報のモック
        self.mock_equipment_slots.get_slot.return_value = Mock(item=None)
        
        # When: コマンドを実行
        result = command.execute()
        
        # Then: コマンドが正常に実行される
        assert isinstance(result, EquipmentOperationResult)
        assert result.success is True
    
    def test_unknown_operation_handling(self):
        """未知の操作に対するエラーハンドリングを確認"""
        # When: 未知の操作を実行
        result = self.handler.execute_equipment_operation('unknown_operation')
        
        # Then: 適切なエラーが返される
        assert result.success is False
        assert result.error_type == 'unknown_operation'
        assert 'unknown_operation' in result.message
    
    def test_error_handling_during_execution(self):
        """実行中のエラーハンドリングを確認"""
        # Given: 例外を発生させるequipment_slots
        self.mock_equipment_slots.get_slot.side_effect = Exception("Test error")
        
        # When: スロット情報取得を実行
        result = self.handler.execute_equipment_operation('get_slot_info', slot_type='weapon')
        
        # Then: エラーが適切に処理される
        assert result.success is False
        assert result.error_type == 'slot_info_error'
        assert 'Test error' in result.message
    
    def test_post_operation_processing(self):
        """操作後処理を確認"""
        # Given: 装備操作が成功
        mock_item = Mock()
        mock_item.name = "Test Item"
        mock_item.required_level = 1
        mock_item.allowed_classes = ['fighter']
        
        self.mock_equipment_slots.equip_item.return_value = True
        
        # When: 装備操作を実行
        result = self.handler.execute_equipment_operation(
            'equip_item', 
            item=mock_item, 
            slot_type='weapon'
        )
        
        # Then: 後処理が実行される（ステータス再計算など）
        assert result.success is True
        # ステータス再計算のログ等で確認可能
    
    def test_state_management_for_undo(self):
        """Undo用の状態管理を確認"""
        # Given: 初期状態
        self.handler.selected_slot = 'weapon'
        self.handler.quick_slots[1] = 'armor'
        
        # When: 現在の状態を取得
        state = self.handler.get_current_state()
        
        # Then: 状態が正しく取得される
        assert state['selected_slot'] == 'weapon'
        assert state['quick_slots'][1] == 'armor'
        
        # When: 状態を復元
        new_state = {'selected_slot': 'armor', 'quick_slots': {2: 'weapon'}}
        restore_result = self.handler.restore_state(new_state)
        
        # Then: 状態が復元される
        assert restore_result.success is True
        assert self.handler.selected_slot == 'armor'
        assert self.handler.quick_slots[2] == 'weapon'