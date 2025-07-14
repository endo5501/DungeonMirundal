"""InnServiceのテスト"""

import unittest
from unittest.mock import Mock, patch
from src.facilities.services.inn_service import InnService
from src.facilities.core.service_result import ServiceResult, ResultType
from src.character.party import Party
from src.character.character import Character


class TestInnService(unittest.TestCase):
    """InnServiceのテストクラス"""
    
    def setUp(self):
        """テスト前のセットアップ"""
        self.service = InnService()
        self.mock_party = Mock(spec=Party)
        self.mock_party.name = "テストパーティ"
        self.mock_party.gold = 1000
        self.mock_party.members = []
        self.service.party = self.mock_party
        
    def test_initialization(self):
        """初期化のテスト"""
        service = InnService()
        self.assertEqual(service.facility_id, "inn")
        self.assertIsNone(service.game)
        self.assertEqual(service.base_rest_cost, 10)
        self.assertIsNone(service._controller)
        self.assertIsNotNone(service.storage_manager)
        
    def test_set_controller(self):
        """コントローラー設定のテスト"""
        mock_controller = Mock()
        self.service.set_controller(mock_controller)
        self.assertEqual(self.service._controller, mock_controller)
        
    def test_get_menu_items(self):
        """メニュー項目取得のテスト"""
        items = self.service.get_menu_items()
        
        # メニュー項目数の確認
        self.assertEqual(len(items), 4)
        
        # 各メニュー項目の確認
        item_ids = [item.id for item in items]
        self.assertIn("adventure_prep", item_ids)
        self.assertIn("storage", item_ids)
        self.assertIn("party_name", item_ids)
        self.assertIn("exit", item_ids)
        
        # 休憩メニューが削除されていることを確認
        self.assertNotIn("rest", item_ids)
        
    def test_can_execute(self):
        """アクション実行可能チェックのテスト"""
        # 有効なアクション
        self.assertTrue(self.service.can_execute("adventure_prep"))
        self.assertTrue(self.service.can_execute("storage"))
        self.assertTrue(self.service.can_execute("party_name"))
        self.assertTrue(self.service.can_execute("exit"))
        
        # 削除された休憩アクション
        self.assertFalse(self.service.can_execute("rest"))
        
        # 無効なアクション
        self.assertFalse(self.service.can_execute("invalid_action"))
        
    def test_execute_action_adventure_prep(self):
        """冒険準備アクション実行のテスト"""
        result = self.service.execute_action("adventure_prep", {})
        
        self.assertTrue(result.is_success())
        self.assertEqual(result.message, "冒険準備画面を表示します")
        self.assertEqual(result.result_type, ResultType.SUCCESS)
        
    def test_execute_action_storage(self):
        """アイテム保管アクション実行のテスト"""
        result = self.service.execute_action("storage", {})
        
        self.assertTrue(result.is_success())
        self.assertEqual(result.message, "アイテム保管画面を表示します")
        self.assertEqual(result.result_type, ResultType.SUCCESS)
        
    def test_execute_action_party_name_without_name(self):
        """パーティ名変更アクション（名前なし）のテスト"""
        result = self.service.execute_action("party_name", {})
        
        self.assertTrue(result.is_success())
        self.assertEqual(result.message, "新しいパーティ名を入力してください")
        self.assertEqual(result.result_type, ResultType.INPUT)
        self.assertEqual(result.data["current_name"], "テストパーティ")
        self.assertEqual(result.data["input_type"], "text")
        self.assertEqual(result.data["max_length"], 20)
        
    def test_execute_action_party_name_with_name(self):
        """パーティ名変更アクション（名前あり）のテスト"""
        result = self.service.execute_action("party_name", {"name": "新しいパーティ名"})
        
        self.assertTrue(result.is_success())
        self.assertIn("テストパーティ", result.message)
        self.assertIn("新しいパーティ名", result.message)
        self.assertEqual(result.result_type, ResultType.SUCCESS)
        self.assertEqual(self.mock_party.name, "新しいパーティ名")
        
    def test_execute_action_party_name_empty(self):
        """パーティ名変更アクション（空文字列）のテスト"""
        # 空文字列は名前未指定として扱われるため、入力要求が返される
        result = self.service.execute_action("party_name", {"name": ""})
        
        self.assertTrue(result.is_success())
        self.assertEqual(result.message, "新しいパーティ名を入力してください")
        self.assertEqual(result.result_type, ResultType.INPUT)
        
    def test_execute_action_party_name_too_long(self):
        """パーティ名変更アクション（名前が長すぎる）のテスト"""
        long_name = "あ" * 21
        result = self.service.execute_action("party_name", {"name": long_name})
        
        self.assertFalse(result.is_success())
        self.assertIn("1～20文字", result.message)
        self.assertEqual(result.result_type, ResultType.WARNING)
        
    def test_execute_action_party_name_no_party(self):
        """パーティ名変更アクション（パーティなし）のテスト"""
        self.service.party = None
        result = self.service.execute_action("party_name", {})
        
        self.assertFalse(result.is_success())
        self.assertEqual(result.message, "パーティが存在しません")
        self.assertEqual(result.result_type, ResultType.ERROR)
        
    def test_execute_action_exit(self):
        """退出アクション実行のテスト"""
        result = self.service.execute_action("exit", {})
        
        self.assertTrue(result.is_success())
        self.assertEqual(result.message, "宿屋から退出しました")
        
    def test_execute_action_invalid(self):
        """無効なアクション実行のテスト"""
        result = self.service.execute_action("invalid_action", {})
        
        self.assertFalse(result.is_success())
        self.assertIn("不明なアクション", result.message)
        
    @patch('src.facilities.services.inn_service.logger')
    def test_execute_action_exception(self, mock_logger):
        """アクション実行時の例外処理のテスト"""
        # 例外を発生させる
        self.service._handle_adventure_prep = Mock(side_effect=Exception("Test error"))
        
        result = self.service.execute_action("adventure_prep", {})
        
        self.assertFalse(result.is_success())
        self.assertIn("エラーが発生しました", result.message)
        mock_logger.error.assert_called()
        
    def test_create_service_panel_adventure_prep(self):
        """冒険準備パネル作成のテスト"""
        mock_rect = Mock()
        mock_parent = Mock()
        mock_ui_manager = Mock()
        
        with patch('src.facilities.ui.inn.adventure_prep_panel.AdventurePrepPanel') as mock_panel_class:
            mock_panel = Mock()
            mock_panel_class.return_value = mock_panel
            
            panel = self.service.create_service_panel(
                "adventure_prep", mock_rect, mock_parent, mock_ui_manager
            )
            
            self.assertEqual(panel, mock_panel)
            mock_panel_class.assert_called_once_with(
                rect=mock_rect,
                parent=mock_parent,
                controller=self.service._controller,
                ui_manager=mock_ui_manager
            )
            
    def test_create_service_panel_storage(self):
        """アイテム保管パネル作成のテスト"""
        mock_rect = Mock()
        mock_parent = Mock()
        mock_ui_manager = Mock()
        
        with patch('src.facilities.ui.inn.storage_panel.StoragePanel') as mock_panel_class:
            mock_panel = Mock()
            mock_panel_class.return_value = mock_panel
            
            panel = self.service.create_service_panel(
                "storage", mock_rect, mock_parent, mock_ui_manager
            )
            
            self.assertEqual(panel, mock_panel)
            mock_panel_class.assert_called_once_with(
                rect=mock_rect,
                parent=mock_parent,
                controller=self.service._controller,
                ui_manager=mock_ui_manager
            )
            
    def test_create_service_panel_unknown(self):
        """未知のサービスパネル作成のテスト"""
        mock_rect = Mock()
        mock_parent = Mock()
        mock_ui_manager = Mock()
        
        panel = self.service.create_service_panel(
            "unknown_service", mock_rect, mock_parent, mock_ui_manager
        )
        
        self.assertIsNone(panel)
        
    @patch('src.facilities.services.inn_service.logger')
    def test_create_service_panel_exception(self, mock_logger):
        """パネル作成時の例外処理のテスト"""
        mock_rect = Mock()
        mock_parent = Mock()
        mock_ui_manager = Mock()
        
        with patch('src.facilities.ui.inn.adventure_prep_panel.AdventurePrepPanel', side_effect=Exception("Test error")):
            panel = self.service.create_service_panel(
                "adventure_prep", mock_rect, mock_parent, mock_ui_manager
            )
            
            self.assertIsNone(panel)
            mock_logger.error.assert_called()


    def test_storage_deposit_item_action(self):
        """アイテム保管 - 預ける動作のテスト"""
        params = {"action": "deposit", "item_id": "potion1", "quantity": 2}
        result = self.service.execute_action("storage", params)
        
        # アクションが正しく処理されることを確認
        self.assertTrue(result.is_success())
        self.assertIn("預け", result.message)  # 預ける処理のメッセージを期待
        
    def test_storage_withdraw_item_action(self):
        """アイテム保管 - 引き出す動作のテスト"""
        params = {"action": "withdraw", "item_id": "stored_item1", "quantity": 1}
        result = self.service.execute_action("storage", params)
        
        # アクションが正しく処理されることを確認
        self.assertTrue(result.is_success())
        self.assertIn("引き出し", result.message)  # 引き出す処理のメッセージを期待
        
    def test_storage_get_inventory_action(self):
        """アイテム保管 - インベントリ取得のテスト"""
        params = {"action": "get_inventory"}
        result = self.service.execute_action("storage", params)
        
        # インベントリ取得が正しく処理されることを確認
        self.assertTrue(result.is_success())
        self.assertIsNotNone(result.data)  # データが返されることを期待


if __name__ == '__main__':
    unittest.main()