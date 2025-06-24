"""ダイアログ閉じる時の問題テスト"""

import unittest
from unittest.mock import Mock, patch
from src.ui.dialog_template import DialogTemplate
from src.ui.menu_stack_manager import MenuStackManager, MenuType
from src.ui.base_ui_pygame import UIMenu, UIDialog


class TestDialogCloseIssue(unittest.TestCase):
    """ダイアログ閉じる時の問題テスト"""
    
    def setUp(self):
        """テストの準備"""
        self.mock_ui_manager = Mock()
        self.stack_manager = MenuStackManager(self.mock_ui_manager)
        self.dialog_template = DialogTemplate(self.stack_manager)
    
    def tearDown(self):
        """テストの後処理"""
        self.stack_manager.clear_stack()
    
    def test_dialog_close_without_dialog_in_stack(self):
        """ダイアログがスタックにない状態でダイアログを閉じるテスト"""
        # 1. 施設メインメニューを表示
        facility_menu = Mock(spec=UIMenu)
        facility_menu.menu_id = "inn_main_menu"
        self.stack_manager.push_menu(facility_menu, MenuType.FACILITY_MAIN)
        
        # 現在の状態を確認
        self.assertIsNotNone(self.stack_manager.current_entry)
        self.assertEqual(self.stack_manager.current_entry.menu_type, MenuType.FACILITY_MAIN)
        self.assertEqual(len(self.stack_manager.stack), 0)
        
        # 2. ダイアログをスタックに積まずに閉じる処理をシミュレート
        # （実際のshow_information_dialogはダイアログをスタックに積まない）
        self.dialog_template._handle_dialog_close("test_dialog", None)
        
        # 期待: メニュースタックは変更されない
        self.assertIsNotNone(self.stack_manager.current_entry)
        self.assertEqual(self.stack_manager.current_entry.menu.menu_id, "inn_main_menu")
        self.assertEqual(self.stack_manager.current_entry.menu_type, MenuType.FACILITY_MAIN)
        self.assertEqual(len(self.stack_manager.stack), 0)
    
    def test_dialog_close_with_dialog_in_stack(self):
        """ダイアログがスタックにある状態でダイアログを閉じるテスト"""
        # 1. 施設メインメニューを表示
        facility_menu = Mock(spec=UIMenu)
        facility_menu.menu_id = "inn_main_menu"
        self.stack_manager.push_menu(facility_menu, MenuType.FACILITY_MAIN)
        
        # 2. ダイアログをスタックに積む
        dialog_menu = Mock(spec=UIMenu)
        dialog_menu.menu_id = "test_dialog"
        self.stack_manager.push_menu(dialog_menu, MenuType.DIALOG)
        
        # 現在の状態を確認
        self.assertIsNotNone(self.stack_manager.current_entry)
        self.assertEqual(self.stack_manager.current_entry.menu_type, MenuType.DIALOG)
        self.assertEqual(len(self.stack_manager.stack), 1)
        
        # 3. ダイアログ閉じる処理
        self.dialog_template._handle_dialog_close("test_dialog", None)
        
        # 期待: 施設メインメニューに戻る
        self.assertIsNotNone(self.stack_manager.current_entry)
        self.assertEqual(self.stack_manager.current_entry.menu.menu_id, "inn_main_menu")
        self.assertEqual(self.stack_manager.current_entry.menu_type, MenuType.FACILITY_MAIN)
        self.assertEqual(len(self.stack_manager.stack), 0)
    
    def test_inn_innkeeper_scenario_fixed(self):
        """宿屋の主人と話すシナリオ（修正版）"""
        # 1. 地上マップ
        overworld_menu = Mock(spec=UIMenu)
        overworld_menu.menu_id = "overworld_map"
        self.stack_manager.push_menu(overworld_menu, MenuType.ROOT)
        
        # 2. 宿屋メインメニュー
        inn_menu = Mock(spec=UIMenu)
        inn_menu.menu_id = "inn_main_menu"
        self.stack_manager.push_menu(inn_menu, MenuType.FACILITY_MAIN)
        
        # 3. 主人と話すダイアログ（新システムではスタックに積まれない）
        # show_information_dialogは直接ダイアログを表示するだけ
        
        # 4. ダイアログのOKボタンを押す（_handle_dialog_closeが呼ばれる）
        self.dialog_template._handle_dialog_close("innkeeper_dialog", None)
        
        # 期待: 宿屋メインメニューが維持される（スタック操作されない）
        self.assertIsNotNone(self.stack_manager.current_entry)
        self.assertEqual(self.stack_manager.current_entry.menu.menu_id, "inn_main_menu")
        self.assertEqual(self.stack_manager.current_entry.menu_type, MenuType.FACILITY_MAIN)
        self.assertEqual(len(self.stack_manager.stack), 1)  # 地上マップが残っている
    
    def test_callback_execution_during_dialog_close(self):
        """ダイアログ閉じる時のコールバック実行テスト"""
        callback_called = False
        
        def test_callback():
            nonlocal callback_called
            callback_called = True
        
        # 施設メインメニューを表示
        facility_menu = Mock(spec=UIMenu)
        facility_menu.menu_id = "inn_main_menu"
        self.stack_manager.push_menu(facility_menu, MenuType.FACILITY_MAIN)
        
        # コールバック付きでダイアログ閉じる処理
        self.dialog_template._handle_dialog_close("test_dialog", test_callback)
        
        # コールバックが実行されることを確認
        self.assertTrue(callback_called)
        
        # メニュースタックは変更されない
        self.assertIsNotNone(self.stack_manager.current_entry)
        self.assertEqual(self.stack_manager.current_entry.menu.menu_id, "inn_main_menu")


if __name__ == '__main__':
    unittest.main()