"""
EquipmentManager統合テスト

window_system版EquipmentManagerがEquipmentOperationHandlerに正しく委譲されることを確認
"""

import pytest
import pygame
from unittest.mock import Mock, patch
from src.ui.window_system.equipment_manager import EquipmentManager
from src.ui.window_system.equipment_types import EquipmentSlotInfo, EquipmentSlotType
from src.equipment.equipment_operation_handler import EquipmentOperationResult


class TestEquipmentManagerIntegration:
    """EquipmentManager統合テストクラス"""
    
    def setup_method(self):
        """各テストメソッドの前に実行される"""
        pygame.init()
        pygame.display.set_mode((1, 1), pygame.NOFRAME)
        
        # モックオブジェクト作成
        self.mock_character = Mock()
        self.mock_character.name = "Test Character"
        self.mock_character.level = 10
        
        self.mock_equipment_slots = Mock()
        self.mock_inventory = Mock()
        
        # EquipmentManager作成
        self.manager = EquipmentManager(
            character=self.mock_character,
            equipment_slots=self.mock_equipment_slots,
            inventory=self.mock_inventory
        )
    
    def teardown_method(self):
        """各テストメソッドの後に実行される"""
        pygame.quit()
    
    def test_equipment_manager_delegates_to_operation_handler(self):
        """EquipmentManagerがEquipmentOperationHandlerに正しく委譲することを確認"""
        # Then: EquipmentOperationHandlerが作成されている
        assert self.manager.operation_handler is not None
        assert self.manager.operation_handler.character == self.mock_character
        assert self.manager.operation_handler.equipment_slots == self.mock_equipment_slots
        assert self.manager.operation_handler.inventory == self.mock_inventory
    
    def test_get_slot_info_delegation(self):
        """get_slot_info の委譲を確認"""
        # Given: EquipmentOperationHandlerからの成功結果
        with patch.object(self.manager.operation_handler, 'execute_equipment_operation') as mock_execute:
            mock_execute.return_value = EquipmentOperationResult(
                success=True,
                data={
                    'slot_type': 'weapon',
                    'item': Mock(),
                    'is_empty': False
                }
            )
            
            # When: スロット情報を取得
            result = self.manager.get_slot_info('weapon')
            
            # Then: 正しく委譲され、EquipmentSlotInfoが返される
            assert result is not None
            assert isinstance(result, EquipmentSlotInfo)
            assert result.slot_type == EquipmentSlotType.WEAPON
            mock_execute.assert_called_once_with('get_slot_info', slot_type='weapon')
    
    def test_get_all_slot_infos_delegation(self):
        """get_all_slot_infos の委譲を確認"""
        # Given: 複数スロットの結果
        with patch.object(self.manager.operation_handler, 'execute_equipment_operation') as mock_execute:
            mock_execute.return_value = EquipmentOperationResult(
                success=True,
                data={
                    'weapon': {'slot_type': 'weapon', 'item': Mock(), 'is_empty': False},
                    'armor': {'slot_type': 'armor', 'item': None, 'is_empty': True}
                }
            )
            
            # When: 全スロット情報を取得
            result = self.manager.get_all_slot_infos()
            
            # Then: 正しく委譲され、辞書型で返される
            assert isinstance(result, dict)
            assert len(result) == 2
            assert 'weapon' in result
            assert 'armor' in result
            mock_execute.assert_called_once_with('get_all_slots')
    
    def test_equip_item_delegation(self):
        """equip_item の委譲を確認"""
        # Given: アイテム装備の成功結果
        mock_item = Mock()
        
        with patch.object(self.manager.operation_handler, 'execute_equipment_operation') as mock_execute:
            mock_execute.return_value = EquipmentOperationResult(success=True)
            
            # When: アイテムを装備
            result = self.manager.equip_item(mock_item, 'weapon')
            
            # Then: 正しく委譲され、成功が返される
            assert result is True
            mock_execute.assert_called_once_with('equip_item', item=mock_item, slot_type='weapon')
    
    def test_unequip_item_delegation(self):
        """unequip_item の委譲を確認"""
        # Given: アイテム装備解除の成功結果
        with patch.object(self.manager.operation_handler, 'execute_equipment_operation') as mock_execute:
            mock_execute.return_value = EquipmentOperationResult(success=True)
            
            # When: アイテムを装備解除
            result = self.manager.unequip_item('weapon')
            
            # Then: 正しく委譲され、成功が返される
            assert result is True
            mock_execute.assert_called_once_with('unequip_item', slot_type='weapon')
    
    def test_can_equip_item_delegation(self):
        """can_equip_item の委譲を確認"""
        # Given: 装備可能性チェックの成功結果
        mock_item = Mock()
        
        with patch.object(self.manager.operation_handler, '_can_equip_item') as mock_can_equip:
            mock_can_equip.return_value = EquipmentOperationResult(success=True)
            
            # When: 装備可能性をチェック
            result = self.manager.can_equip_item(mock_item, 'weapon')
            
            # Then: 正しく委譲され、結果が返される
            assert result is True
            mock_can_equip.assert_called_once_with(mock_item, 'weapon')
    
    def test_swap_equipment_delegation(self):
        """swap_equipment の委譲を確認"""
        # Given: 装備交換の成功結果
        with patch.object(self.manager.operation_handler, 'execute_equipment_operation') as mock_execute:
            mock_execute.return_value = EquipmentOperationResult(success=True)
            
            # When: 装備を交換
            result = self.manager.swap_equipment('weapon', 'armor')
            
            # Then: 正しく委譲され、成功が返される
            assert result is True
            mock_execute.assert_called_once_with('swap_equipment', from_slot='weapon', to_slot='armor')
    
    def test_get_equippable_items_delegation(self):
        """get_equippable_items の委譲を確認"""
        # Given: 装備可能アイテムの結果
        mock_items = [Mock(), Mock()]
        
        with patch.object(self.manager.operation_handler, 'execute_equipment_operation') as mock_execute:
            mock_execute.return_value = EquipmentOperationResult(
                success=True,
                data={'items': mock_items}
            )
            
            # フィルターの設定
            self.manager.filter.matches_item = Mock(return_value=True)
            
            # When: 装備可能アイテムを取得
            result = self.manager.get_equippable_items('weapon')
            
            # Then: 正しく委譲され、フィルタリングされた結果が返される
            assert len(result) == 2
            mock_execute.assert_called_once_with('get_equippable_items', slot_type='weapon')
    
    def test_assign_quick_slot_delegation(self):
        """assign_quick_slot の委譲を確認"""
        # Given: クイックスロット割り当ての成功結果
        with patch.object(self.manager.operation_handler, 'execute_equipment_operation') as mock_execute:
            mock_execute.return_value = EquipmentOperationResult(success=True)
            
            # When: クイックスロットを割り当て
            result = self.manager.assign_quick_slot('weapon', 1)
            
            # Then: 正しく委譲され、成功が返される
            assert result is True
            mock_execute.assert_called_once_with(
                'assign_quick_slot', 
                quick_slot_index=1, 
                slot_type='weapon'
            )
    
    def test_validate_equipment_state_delegation(self):
        """validate_equipment_state の委譲を確認"""
        # Given: 装備状態検証の結果
        with patch.object(self.manager.operation_handler, 'execute_equipment_operation') as mock_execute:
            mock_execute.return_value = EquipmentOperationResult(
                success=True,
                data={
                    'valid': True,
                    'results': [
                        {'valid': True, 'messages': []},
                        {'valid': False, 'messages': ['テストエラー']}
                    ]
                }
            )
            
            # When: 装備状態を検証
            result = self.manager.validate_equipment_state()
            
            # Then: 正しく委譲され、エラーリストが返される
            assert isinstance(result, list)
            assert 'テストエラー' in result
            mock_execute.assert_called_once_with('validate_equipment')
    
    def test_selected_slot_synchronization(self):
        """選択スロットの同期を確認"""
        # Given: スロット選択が可能な状態
        with patch.object(self.manager, 'get_slot_info') as mock_get_slot:
            mock_slot_info = Mock()
            mock_get_slot.return_value = mock_slot_info
            
            # When: スロットを選択
            result = self.manager.select_slot('weapon')
            
            # Then: EquipmentOperationHandlerの選択スロットが更新される
            assert result is True
            assert self.manager.operation_handler.selected_slot == 'weapon'
    
    def test_quick_slots_synchronization(self):
        """クイックスロットの同期を確認"""
        # Given: クイックスロットデータ
        self.manager.operation_handler.quick_slots[1] = 'weapon'
        self.manager.operation_handler.quick_slots[2] = 'armor'
        
        # When: クイックスロット一覧を取得
        with patch.object(self.manager, 'get_slot_info') as mock_get_slot:
            mock_slot_info = Mock()
            mock_slot_info.item = Mock()
            mock_slot_info.item.item_id = 'test_item'
            mock_get_slot.return_value = mock_slot_info
            
            result = self.manager.get_quick_slot_assignments()
            
            # Then: EquipmentOperationHandlerのクイックスロットデータが使用される
            assert len(result) == 2
            assert any(assignment.slot_index == 1 for assignment in result)
            assert any(assignment.slot_index == 2 for assignment in result)
    
    def test_manager_summary_integration(self):
        """マネージャーサマリーの統合を確認"""
        # Given: サマリー取得に必要な状態
        self.manager.operation_handler.selected_slot = 'weapon'
        self.manager.operation_handler.quick_slots[1] = 'armor'
        
        with patch.object(self.manager, 'calculate_character_stats') as mock_stats, \
             patch.object(self.manager, 'validate_equipment_state') as mock_validate:
            
            mock_stats.return_value = Mock(total_stats={'strength': 10})
            mock_validate.return_value = ['テストエラー']
            
            # When: サマリーを取得
            result = self.manager.get_manager_summary()
            
            # Then: 統合されたデータが返される
            assert result['character'] == self.mock_character
            assert result['selected_slot'] == 'weapon'
            assert result['quick_slots_count'] == 1
            assert result['validation_errors'] == ['テストエラー']
    
    def test_backward_compatibility(self):
        """後方互換性を確認"""
        # EquipmentManagerの既存インターフェースが保たれていることを確認
        assert hasattr(self.manager, 'get_slot_info')
        assert hasattr(self.manager, 'get_all_slot_infos')
        assert hasattr(self.manager, 'equip_item')
        assert hasattr(self.manager, 'unequip_item')
        assert hasattr(self.manager, 'can_equip_item')
        assert hasattr(self.manager, 'swap_equipment')
        assert hasattr(self.manager, 'get_equippable_items')
        assert hasattr(self.manager, 'assign_quick_slot')
        assert hasattr(self.manager, 'validate_equipment_state')
        assert hasattr(self.manager, 'get_manager_summary')
        
        # 戻り値の型も期待されるものであることを確認
        assert callable(self.manager.get_slot_info)
        assert callable(self.manager.equip_item)
        assert callable(self.manager.unequip_item)