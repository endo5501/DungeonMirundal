"""商店サービスのテスト"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import pytest

from src.facilities.services.shop_service import ShopService
from src.facilities.core.service_result import ServiceResult, ResultType
from src.character.party import Party
from src.character.character import Character
from src.items.item import ItemInstance, Item, ItemManager
from src.inventory.inventory import Inventory, InventoryManager, InventorySlotType


class TestShopService(unittest.TestCase):
    """商店サービスのテストクラス"""
    
    def setUp(self):
        """各テストの前に実行される初期化処理"""
        self.shop_service = ShopService()
        
        # モックパーティを作成
        self.party = Mock(spec=Party)
        self.party.party_id = "test_party"
        self.party.gold = 1000
        self.party.members = []
        
        # モックキャラクターを作成
        self.character = Mock(spec=Character)
        self.character.character_id = "test_char"
        self.character.name = "Test Hero"
        self.character.is_alive.return_value = True
        self.party.members.append(self.character)
        
        # サービスにパーティを設定
        self.shop_service.set_party(self.party)
        
        # モックアイテムマネージャーを設定
        self.mock_item_manager = Mock(spec=ItemManager)
        self.shop_service.item_manager = self.mock_item_manager
        
        # モックアイテムを作成
        self.mock_item = Mock(spec=Item)
        self.mock_item.get_name.return_value = "テストアイテム"
        self.mock_item.get_description.return_value = "テスト用のアイテム"
        self.mock_item.price = 100
        
        # item_typeとrarityのモック設定
        mock_item_type = Mock()
        mock_item_type.value = "consumable"
        self.mock_item.item_type = mock_item_type
        
        mock_rarity = Mock()
        mock_rarity.value = "common"
        self.mock_item.rarity = mock_rarity
    
    def test_init(self):
        """初期化のテスト"""
        shop = ShopService()
        self.assertEqual(shop.facility_id, "shop")
        self.assertEqual(shop.sell_rate, 0.5)
        self.assertIsNotNone(shop.item_manager)
    
    def test_get_menu_items(self):
        """メニュー項目取得のテスト"""
        with patch.object(self.shop_service, '_has_items_to_sell', return_value=True), \
             patch.object(self.shop_service, '_has_unidentified_items', return_value=True):
            
            menu_items = self.shop_service.get_menu_items()
            
            self.assertEqual(len(menu_items), 4)
            
            # メニュー項目のIDをチェック
            menu_ids = [item.id for item in menu_items]
            expected_ids = ["buy", "sell", "identify", "exit"]
            self.assertEqual(menu_ids, expected_ids)
            
            # 有効状態をチェック
            for item in menu_items:
                self.assertTrue(item.enabled)
    
    def test_can_execute(self):
        """実行可能アクションのテスト"""
        valid_actions = ["buy", "sell", "identify", "exit"]
        invalid_actions = ["invalid", "unknown", ""]
        
        for action in valid_actions:
            self.assertTrue(self.shop_service.can_execute(action))
        
        for action in invalid_actions:
            self.assertFalse(self.shop_service.can_execute(action))
    
    @patch('src.facilities.services.shop_service.inventory_manager')
    def test_generate_shop_inventory(self, mock_inventory_manager):
        """商店在庫生成のテスト"""
        # アイテムマネージャーのモック設定
        self.mock_item_manager.items = {
            "test_item": self.mock_item
        }
        
        self.shop_service._generate_shop_inventory()
        
        # 在庫が生成されたことを確認
        self.assertIn("test_item", self.shop_service._shop_inventory)
        inventory_item = self.shop_service._shop_inventory["test_item"]
        
        self.assertEqual(inventory_item["name"], "テストアイテム")
        self.assertEqual(inventory_item["price"], 100)
        self.assertEqual(inventory_item["category"], "items")  # consumable -> items
        self.assertGreater(inventory_item["stock"], 0)
    
    @patch('src.facilities.services.shop_service.inventory_manager')
    def test_purchase_success(self, mock_inventory_manager):
        """購入成功のテスト"""
        # 在庫を設定
        self.shop_service._shop_inventory = {
            "test_item": {
                "name": "テストアイテム",
                "price": 100,
                "stock": 5,
                "item_object": self.mock_item
            }
        }
        
        # パーティインベントリのモック
        mock_party_inventory = Mock(spec=Inventory)
        mock_party_inventory.add_item.return_value = True
        mock_inventory_manager.get_party_inventory.return_value = mock_party_inventory
        
        # アイテムインスタンス作成のモック
        mock_item_instance = Mock(spec=ItemInstance)
        self.mock_item_manager.create_item_instance.return_value = mock_item_instance
        
        # 購入実行
        result = self.shop_service._execute_purchase("test_item", 2)
        
        # 結果をチェック
        self.assertTrue(result.success)
        self.assertEqual(result.result_type, ResultType.SUCCESS)
        
        # 所持金が減ったことを確認
        self.assertEqual(self.party.gold, 800)  # 1000 - (100 * 2)
        
        # 在庫が減ったことを確認
        self.assertEqual(self.shop_service._shop_inventory["test_item"]["stock"], 3)
    
    def test_purchase_insufficient_gold(self):
        """所持金不足での購入失敗テスト"""
        # パーティの所持金を少なく設定
        self.party.gold = 50
        
        # 在庫を設定
        self.shop_service._shop_inventory = {
            "test_item": {
                "name": "テストアイテム",
                "price": 100,
                "stock": 5
            }
        }
        
        # 購入実行
        result = self.shop_service._execute_purchase("test_item", 1)
        
        # 失敗することを確認
        self.assertFalse(result.success)
        self.assertIn("所持金が不足", result.message)
    
    def test_purchase_insufficient_stock(self):
        """在庫不足での購入失敗テスト"""
        # 在庫を設定
        self.shop_service._shop_inventory = {
            "test_item": {
                "name": "テストアイテム",
                "price": 100,
                "stock": 1
            }
        }
        
        # 購入実行（在庫以上の数量）
        result = self.shop_service._execute_purchase("test_item", 5)
        
        # 失敗することを確認
        self.assertFalse(result.success)
        self.assertIn("在庫が不足", result.message)
    
    @patch('src.facilities.services.shop_service.inventory_manager')
    def test_sell_success(self, mock_inventory_manager):
        """売却成功のテスト"""
        # アイテムインスタンスのモック
        mock_item_instance = Mock(spec=ItemInstance)
        mock_item_instance.item_id = "test_item"
        mock_item_instance.quantity = 3
        mock_item_instance.identified = True
        mock_item_instance.condition = 1.0
        
        # パーティインベントリのモック
        mock_party_inventory = Mock(spec=Inventory)
        mock_party_inventory.get_all_items.return_value = [(0, mock_item_instance)]
        mock_party_inventory.remove_item.return_value = mock_item_instance
        mock_inventory_manager.get_party_inventory.return_value = mock_party_inventory
        
        # アイテム情報のモック
        self.mock_item_manager.get_item_info.return_value = self.mock_item
        self.mock_item_manager.get_sell_price.return_value = 50
        self.mock_item_manager.get_item_display_name.return_value = "テストアイテム"
        
        # 売却実行
        result = self.shop_service._execute_sell("test_item", 1)
        
        # 結果をチェック
        self.assertTrue(result.success)
        self.assertEqual(result.result_type, ResultType.SUCCESS)
        
        # 所持金が増えたことを確認（実際には確認処理を通るため厳密なテストは複雑）
        # ここでは基本的な成功チェックのみ行う
    
    @patch('src.facilities.services.shop_service.inventory_manager')
    def test_identify_success(self, mock_inventory_manager):
        """鑑定成功のテスト"""
        # 未鑑定アイテムインスタンスのモック
        mock_item_instance = Mock(spec=ItemInstance)
        mock_item_instance.item_id = "test_item"
        mock_item_instance.instance_id = "test_instance"
        mock_item_instance.identified = False
        
        # パーティインベントリのモック
        mock_party_inventory = Mock(spec=Inventory)
        mock_party_inventory.get_all_items.return_value = [(0, mock_item_instance)]
        mock_party_inventory.slots = [Mock()]
        mock_party_inventory.slots[0].is_empty.return_value = False
        mock_party_inventory.slots[0].item_instance = mock_item_instance
        mock_inventory_manager.get_party_inventory.return_value = mock_party_inventory
        
        # アイテム情報のモック
        self.mock_item_manager.get_item_info.return_value = self.mock_item
        self.mock_item_manager.get_item_display_name.return_value = "?テストアイテム?"
        self.mock_item_manager.identify_item.return_value = True
        self.mock_item_manager.get_identification_cost.return_value = 100
        
        # 鑑定費用を設定
        self.shop_service.identify_cost = 100
        
        # 鑑定実行
        result = self.shop_service._execute_identify("test_instance")
        
        # 結果をチェック
        self.assertTrue(result.success)
        self.assertEqual(result.result_type, ResultType.SUCCESS)
        
        # 鑑定費用が支払われたことを確認
        self.assertEqual(self.party.gold, 900)  # 1000 - 100
    
    def test_identify_insufficient_gold(self):
        """鑑定料金不足のテスト"""
        # パーティの所持金を少なく設定
        self.party.gold = 50
        self.shop_service.identify_cost = 100
        
        # 鑑定実行
        result = self.shop_service._execute_identify("test_item")
        
        # 失敗することを確認
        self.assertFalse(result.success)
        self.assertIn("鑑定料金が不足", result.message)
    
    @patch('src.facilities.services.shop_service.inventory_manager')
    def test_has_items_to_sell(self, mock_inventory_manager):
        """売却可能アイテム存在チェックのテスト"""
        # パーティインベントリのモック
        mock_party_inventory = Mock(spec=Inventory)
        mock_item_instance = Mock(spec=ItemInstance)
        mock_party_inventory.get_all_items.return_value = [(0, mock_item_instance)]
        mock_inventory_manager.get_party_inventory.return_value = mock_party_inventory
        
        # キャラクターインベントリのモック
        mock_char_inventory = Mock(spec=Inventory)
        mock_char_inventory.get_all_items.return_value = []
        mock_inventory_manager.get_character_inventory.return_value = mock_char_inventory
        
        # テスト実行
        result = self.shop_service._has_items_to_sell()
        
        # アイテムが存在するのでTrueになることを確認
        self.assertTrue(result)
    
    @patch('src.facilities.services.shop_service.inventory_manager')
    def test_has_unidentified_items(self, mock_inventory_manager):
        """未鑑定アイテム存在チェックのテスト"""
        # 未鑑定アイテムインスタンスのモック
        mock_item_instance = Mock(spec=ItemInstance)
        mock_item_instance.identified = False
        
        # パーティインベントリのモック
        mock_party_inventory = Mock(spec=Inventory)
        mock_party_inventory.get_all_items.return_value = [(0, mock_item_instance)]
        mock_inventory_manager.get_party_inventory.return_value = mock_party_inventory
        
        # キャラクターインベントリのモック
        mock_char_inventory = Mock(spec=Inventory)
        mock_char_inventory.get_all_items.return_value = []
        mock_inventory_manager.get_character_inventory.return_value = mock_char_inventory
        
        # テスト実行
        result = self.shop_service._has_unidentified_items()
        
        # 未鑑定アイテムが存在するのでTrueになることを確認
        self.assertTrue(result)
    
    def test_exit_action(self):
        """退出アクションのテスト"""
        result = self.shop_service.execute_action("exit", {})
        
        self.assertTrue(result.success)
        self.assertIn("商店から退出", result.message)


if __name__ == '__main__':
    unittest.main()