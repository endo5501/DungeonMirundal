"""FacilityControllerのテスト"""

import unittest
from unittest.mock import Mock, MagicMock, patch
import pygame
from src.facilities.core.facility_controller import FacilityController
from src.facilities.core.facility_service import FacilityService, MenuItem
from src.facilities.core.service_result import ServiceResult, ResultType


class TestFacilityController(unittest.TestCase):
    """FacilityControllerのテストクラス"""
    
    def setUp(self):
        """テスト前のセットアップ"""
        # モックサービスを作成
        self.mock_service = Mock(spec=FacilityService)
        self.mock_service.get_menu_items.return_value = [
            MenuItem("test_item_1", "Test Item 1", enabled=True),
            MenuItem("test_item_2", "Test Item 2", enabled=False),
        ]
        self.mock_service.execute_action.return_value = ServiceResult.ok("Success")
        
        # FacilityControllerを作成（サービスクラスではなくインスタンスを渡すため修正）
        # 実際の実装ではサービスクラスを渡すので、Mockクラスを作成
        mock_service_class = Mock(return_value=self.mock_service)
        self.controller = FacilityController("test_facility", mock_service_class)
    
    def test_initialization(self):
        """初期化のテスト"""
        self.assertEqual(self.controller.facility_id, "test_facility")
        self.assertEqual(self.controller.service, self.mock_service)
        self.assertFalse(self.controller.is_active)
        self.assertIsNone(self.controller.window)
    
    def test_get_menu_items_active(self):
        """メニューアイテム取得（アクティブ状態）のテスト"""
        self.controller.is_active = True
        
        menu_items = self.controller.get_menu_items()
        
        self.assertEqual(len(menu_items), 2)
        self.assertEqual(menu_items[0].id, "test_item_1")
        self.assertEqual(menu_items[1].id, "test_item_2")
        self.mock_service.get_menu_items.assert_called_once()
    
    def test_get_menu_items_inactive(self):
        """メニューアイテム取得（非アクティブ状態）のテスト"""
        self.controller.is_active = False
        
        menu_items = self.controller.get_menu_items()
        
        self.assertEqual(len(menu_items), 0)
    
    def test_execute_service(self):
        """サービス実行のテスト"""
        self.controller.is_active = True
        self.mock_service.can_execute.return_value = True
        self.mock_service.validate_action_params.return_value = True
        
        params = {"test": "value"}
        
        result = self.controller.execute_service("test_action", params)
        
        self.assertTrue(result.is_success())
        self.assertEqual(result.message, "Success")
        self.mock_service.execute_action.assert_called_once_with("test_action", params)
    
    def test_execute_service_with_none_params(self):
        """パラメータなしでのサービス実行のテスト"""
        self.controller.is_active = True
        self.mock_service.can_execute.return_value = True
        self.mock_service.validate_action_params.return_value = True
        
        result = self.controller.execute_service("test_action", None)
        
        self.assertTrue(result.is_success())
        self.mock_service.execute_action.assert_called_once_with("test_action", {})
    
    def test_is_active_property(self):
        """アクティブ状態プロパティのテスト"""
        self.assertFalse(self.controller.is_active)
        
        self.controller.is_active = True
        self.assertTrue(self.controller.is_active)
    
    def test_enter_facility(self):
        """施設入場のテスト"""
        mock_party = Mock()
        
        with patch.object(self.controller, '_create_and_show_window', return_value=True):
            result = self.controller.enter(mock_party)
            
            self.assertTrue(result)
            self.assertTrue(self.controller.is_active)
            self.mock_service.set_party.assert_called_once_with(mock_party)
    
    def test_exit_facility(self):
        """施設退場のテスト"""
        # アクティブ状態に設定
        self.controller.is_active = True
        self.controller.window = Mock()
        
        with patch.object(self.controller, '_close_window') as mock_close, \
             patch.object(self.controller, '_return_to_overworld') as mock_return:
            
            result = self.controller.exit()
            
            self.assertTrue(result)
            self.assertFalse(self.controller.is_active)
            mock_close.assert_called_once()
            mock_return.assert_called_once()
    
    def test_exit_facility_already_inactive(self):
        """すでに非アクティブな施設の退場テスト"""
        self.controller.is_active = False
        
        result = self.controller.exit()
        
        # 非アクティブでも成功とする
        self.assertTrue(result)
        self.assertFalse(self.controller.is_active)
    
    def test_get_service_info(self):
        """サービス情報取得のテスト"""
        self.controller.is_active = True
        self.controller._party = Mock()
        self.controller._party.name = "Test Party"
        
        info = self.controller.get_service_info()
        
        self.assertEqual(info['facility_id'], 'test_facility')
        self.assertTrue(info['is_active'])
        self.assertEqual(info['party_name'], 'Test Party')
    
    def test_set_get_config(self):
        """設定の設定・取得のテスト"""
        test_config = {'setting1': 'value1', 'setting2': 42}
        
        self.controller.set_config(test_config)
        
        self.assertEqual(self.controller.get_config('setting1'), 'value1')
        self.assertEqual(self.controller.get_config('setting2'), 42)
        self.assertEqual(self.controller.get_config('nonexistent'), None)
        self.assertEqual(self.controller.get_config('nonexistent', 'default'), 'default')


class TestFacilityControllerEdgeCases(unittest.TestCase):
    """FacilityControllerのエッジケースのテスト"""
    
    def setUp(self):
        """テスト前のセットアップ"""
        self.mock_service = Mock(spec=FacilityService)
        mock_service_class = Mock(return_value=self.mock_service)
        self.controller = FacilityController("test_facility", mock_service_class)
    
    def test_execute_service_exception(self):
        """サービス実行時の例外処理のテスト"""
        self.controller.is_active = True
        self.mock_service.can_execute.return_value = True
        self.mock_service.validate_action_params.return_value = True
        self.mock_service.execute_action.side_effect = Exception("Test error")
        
        result = self.controller.execute_service("test_action", {})
        
        # 例外が発生しても適切にエラー結果が返される
        self.assertFalse(result.is_success())
    
    def test_get_menu_items_service_exception(self):
        """メニューアイテム取得時の例外処理のテスト"""
        self.controller.is_active = True
        self.mock_service.get_menu_items.side_effect = Exception("Test error")
        
        menu_items = self.controller.get_menu_items()
        
        # 例外が発生した場合は空のリストを返す
        self.assertEqual(len(menu_items), 0)
    
    def test_execute_service_not_active(self):
        """非アクティブ時のサービス実行テスト"""
        self.controller.is_active = False
        
        result = self.controller.execute_service("test_action", {})
        
        self.assertFalse(result.is_success())
        self.assertIn("not active", result.message)


if __name__ == '__main__':
    unittest.main()