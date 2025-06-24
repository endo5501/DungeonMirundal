"""メニュースタック問題のテスト"""

import unittest
from unittest.mock import Mock, patch
from src.ui.menu_stack_manager import MenuStackManager, MenuStackEntry, MenuType
from src.ui.base_ui_pygame import UIMenu
from src.utils.logger import logger


class TestMenuStackIssue(unittest.TestCase):
    """メニュースタック問題のテスト"""
    
    def setUp(self):
        """テストの準備"""
        self.mock_ui_manager = Mock()
        self.stack_manager = MenuStackManager(self.mock_ui_manager)
    
    def tearDown(self):
        """テストの後処理"""
        self.stack_manager.clear_stack()
    
    def test_menu_stack_becomes_empty_after_dialog_close(self):
        """ダイアログを閉じた後にメニュースタックが空になる問題を再現"""
        # 1. 地上マップ（ROOT）を表示
        root_menu = Mock(spec=UIMenu)
        root_menu.menu_id = "overworld_map"
        self.stack_manager.push_menu(root_menu, MenuType.ROOT)
        
        # 2. 施設メインメニュー（FACILITY_MAIN）を表示
        facility_menu = Mock(spec=UIMenu)
        facility_menu.menu_id = "inn_main_menu"
        self.stack_manager.push_menu(facility_menu, MenuType.FACILITY_MAIN)
        
        # 3. ダイアログ（DIALOG）を表示
        dialog_menu = Mock(spec=UIMenu)
        dialog_menu.menu_id = "innkeeper_dialog"
        self.stack_manager.push_menu(dialog_menu, MenuType.DIALOG)
        
        # 現在の状態を確認
        self.assertEqual(len(self.stack_manager.stack), 2)  # ROOT, FACILITY_MAIN
        self.assertEqual(self.stack_manager.current_entry.menu.menu_id, "innkeeper_dialog")
        
        # 4. ダイアログを閉じる（ポップ）
        popped_entry = self.stack_manager.pop_menu()
        
        # 期待: 施設メインメニューに戻る
        self.assertIsNotNone(self.stack_manager.current_entry)
        self.assertEqual(self.stack_manager.current_entry.menu.menu_id, "inn_main_menu")
        self.assertEqual(len(self.stack_manager.stack), 1)  # ROOT のみ
        
        # 5. 再度ポップ（施設から地上マップに戻る）
        popped_entry = self.stack_manager.pop_menu()
        
        # 期待: 地上マップに戻る
        self.assertIsNotNone(self.stack_manager.current_entry)
        self.assertEqual(self.stack_manager.current_entry.menu.menu_id, "overworld_map")
        self.assertEqual(len(self.stack_manager.stack), 0)
        
        # 6. 再度ポップ（修正後: ROOTメニューは保持される）
        popped_entry = self.stack_manager.pop_menu()
        
        # 修正: ROOTメニューが保持されてメニュー消失が防がれる
        self.assertIsNotNone(self.stack_manager.current_entry)  # 修正により保持される
        self.assertEqual(self.stack_manager.current_entry.menu.menu_id, "overworld_map")
        self.assertEqual(len(self.stack_manager.stack), 0)
    
    def test_inn_innkeeper_dialog_scenario(self):
        """宿屋の主人と話すシナリオを再現"""
        # 1. 地上マップ
        overworld_menu = Mock(spec=UIMenu)
        overworld_menu.menu_id = "overworld_map"
        self.stack_manager.push_menu(overworld_menu, MenuType.ROOT)
        
        # 2. 宿屋メインメニュー
        inn_main_menu = Mock(spec=UIMenu)
        inn_main_menu.menu_id = "inn_main_menu"
        self.stack_manager.push_menu(inn_main_menu, MenuType.FACILITY_MAIN)
        
        # 3. 主人と話すダイアログ
        innkeeper_dialog = Mock(spec=UIMenu)
        innkeeper_dialog.menu_id = "innkeeper_dialog"
        self.stack_manager.push_menu(innkeeper_dialog, MenuType.DIALOG)
        
        # 状態確認
        self.assertEqual(self.stack_manager.current_entry.menu.menu_id, "innkeeper_dialog")
        self.assertEqual(len(self.stack_manager.stack), 2)
        
        # 4. ダイアログのOKボタンを押す（ポップ）
        self.stack_manager.pop_menu()
        
        # 期待: 宿屋メインメニューに戻る
        self.assertIsNotNone(self.stack_manager.current_entry)
        self.assertEqual(self.stack_manager.current_entry.menu.menu_id, "inn_main_menu")
        
        # しかし、実際の問題では何らかの理由で更にポップされてしまい、
        # 結果的にROOTまで戻ってしまったり、スタックが空になる
    
    def test_back_to_facility_main_when_already_at_facility_main(self):
        """既に施設メインメニューにいる場合のback_to_facility_main動作"""
        # 1. 地上マップ
        overworld_menu = Mock(spec=UIMenu)
        overworld_menu.menu_id = "overworld_map"
        self.stack_manager.push_menu(overworld_menu, MenuType.ROOT)
        
        # 2. 施設メインメニュー
        facility_menu = Mock(spec=UIMenu)
        facility_menu.menu_id = "facility_main"
        self.stack_manager.push_menu(facility_menu, MenuType.FACILITY_MAIN)
        
        # 現在の状態確認
        self.assertEqual(self.stack_manager.current_entry.menu.menu_id, "facility_main")
        self.assertEqual(self.stack_manager.current_entry.menu_type, MenuType.FACILITY_MAIN)
        self.assertEqual(len(self.stack_manager.stack), 1)
        
        # back_to_facility_mainを呼び出し
        result = self.stack_manager.back_to_facility_main()
        
        # 期待: 何も変わらない（既に施設メインメニューにいるため）
        self.assertTrue(result)
        self.assertEqual(self.stack_manager.current_entry.menu.menu_id, "facility_main")
        self.assertEqual(len(self.stack_manager.stack), 1)
    
    def test_pop_empty_stack_issue_fixed(self):
        """空のスタックでポップした場合の修正版テスト"""
        # 1. 単一メニューのみ（スタックは空）
        root_menu = Mock(spec=UIMenu)
        root_menu.menu_id = "overworld_map"
        self.stack_manager.push_menu(root_menu, MenuType.ROOT)
        
        # 状態確認
        self.assertEqual(len(self.stack_manager.stack), 0)
        self.assertIsNotNone(self.stack_manager.current_entry)
        
        # 2. ポップ実行（ROOTメニュー）
        popped = self.stack_manager.pop_menu()
        
        # 修正: ROOTメニューは残る
        self.assertIsNotNone(self.stack_manager.current_entry)
        self.assertEqual(self.stack_manager.current_entry.menu.menu_id, "overworld_map")
        self.assertEqual(len(self.stack_manager.stack), 0)
        
        # 3. 非ROOTメニューでテスト
        dialog_menu = Mock(spec=UIMenu)
        dialog_menu.menu_id = "test_dialog"
        self.stack_manager.push_menu(dialog_menu, MenuType.DIALOG)
        
        # 4. ダイアログをポップ
        popped = self.stack_manager.pop_menu()
        
        # ROOTメニューに戻る
        self.assertIsNotNone(self.stack_manager.current_entry)
        self.assertEqual(self.stack_manager.current_entry.menu.menu_id, "overworld_map")


if __name__ == '__main__':
    unittest.main()