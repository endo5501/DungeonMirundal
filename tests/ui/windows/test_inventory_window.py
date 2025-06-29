"""InventoryWindowのテスト"""

import pytest
from unittest.mock import Mock, patch
import pygame

from src.ui.windows.inventory_window import InventoryWindow
from src.ui.window_system.window_manager import WindowManager
from src.character.character import Character
from src.character.party import Party
from src.inventory.inventory import Inventory, InventorySlot
from src.items.item import Item, ItemInstance


class TestInventoryWindow:
    """InventoryWindowのテストクラス"""

    @pytest.fixture
    def mock_window_manager(self):
        """WindowManagerのモックを作成"""
        with patch('src.ui.window_system.window_manager.WindowManager') as mock_wm_class:
            mock_wm = Mock()
            mock_wm_class.get_instance.return_value = mock_wm
            mock_wm.ui_manager = Mock()
            mock_wm.screen = Mock()
            mock_wm.screen.get_rect.return_value = pygame.Rect(0, 0, 800, 600)
            yield mock_wm

    @pytest.fixture
    def mock_inventory(self):
        """インベントリのモックを作成"""
        inventory = Mock()
        inventory.slots = [Mock() for _ in range(20)]
        for i, slot in enumerate(inventory.slots):
            slot.is_empty.return_value = True
            slot.item_instance = None
            slot.slot_id = i
        inventory.get_total_weight.return_value = 10.5
        inventory.get_max_weight.return_value = 50.0
        inventory.get_item_count.return_value = 5
        inventory.get_max_items.return_value = 20
        inventory.add_item.return_value = True
        inventory.remove_item.return_value = True
        inventory.can_add_item.return_value = True
        return inventory

    @pytest.fixture 
    def mock_character(self, mock_inventory):
        """キャラクターのモックを作成"""
        char = Mock()
        char.name = "テスト冒険者"
        char.get_inventory.return_value = mock_inventory
        return char

    @pytest.fixture
    def mock_party(self, mock_character, mock_inventory):
        """パーティのモックを作成"""
        party = Mock()
        party.name = "テストパーティ"
        party.get_all_characters.return_value = [mock_character]
        party.get_party_inventory.return_value = mock_inventory
        return party

    @pytest.fixture
    def mock_item(self):
        """アイテムのモックを作成"""
        item = Mock()
        item.item_id = "test_item"
        item.get_name.return_value = "テストアイテム"
        item.get_description.return_value = "テスト用のアイテムです"
        item.item_type.value = "consumable"
        item.weight = 1.0
        item.price = 100
        item.is_usable.return_value = True
        item.is_stackable.return_value = True
        item.get_max_stack.return_value = 10
        return item

    @pytest.fixture
    def mock_item_instance(self, mock_item):
        """アイテムインスタンスのモックを作成"""
        item_instance = Mock()
        item_instance.item_id = "test_item"
        item_instance.quantity = 3
        item_instance.condition = 1.0
        item_instance.identified = True
        return item_instance

    def test_inventory_window_creation(self, mock_window_manager):
        """InventoryWindowが正しく作成されることを確認"""
        window = InventoryWindow("test_inventory")
        
        assert window.window_id == "test_inventory"
        assert window.current_party is None
        assert window.current_character is None
        assert window.current_inventory is None

    def test_set_party(self, mock_window_manager, mock_party):
        """パーティの設定が正しく動作することを確認"""
        window = InventoryWindow("test_inventory")
        window.set_party(mock_party)
        
        assert window.current_party == mock_party

    def test_show_party_inventory_overview(self, mock_window_manager, mock_party):
        """パーティインベントリ概要の表示が正しく動作することを確認"""
        window = InventoryWindow("test_inventory")
        window.set_party(mock_party)
        
        # createメソッドをモック
        window.create_party_inventory_overview = Mock()
        
        window.show_party_inventory_overview()
        
        window.create_party_inventory_overview.assert_called_once()

    def test_show_inventory_contents(self, mock_window_manager, mock_inventory):
        """インベントリ内容表示が正しく動作することを確認"""
        window = InventoryWindow("test_inventory")
        
        # createメソッドをモック
        window.create_inventory_contents = Mock()
        
        window.show_inventory_contents(mock_inventory, "テストインベントリ")
        
        assert window.current_inventory == mock_inventory
        window.create_inventory_contents.assert_called_once()

    def test_show_item_details(self, mock_window_manager, mock_item_instance, mock_item):
        """アイテム詳細表示が正しく動作することを確認"""
        window = InventoryWindow("test_inventory")
        
        # ダイアログ表示をモック
        window.show_dialog = Mock()
        
        window.show_item_details(mock_item_instance, mock_item)
        
        window.show_dialog.assert_called_once()

    def test_use_item_success(self, mock_window_manager, mock_character, mock_item_instance):
        """アイテム使用の成功ケースをテスト"""
        window = InventoryWindow("test_inventory")
        window.current_character = mock_character
        window.current_inventory = mock_character.get_inventory()
        window.selected_slot = 0
        
        # アイテム使用をモック
        with patch('src.items.item_usage.item_usage_manager') as mock_usage_manager:
            mock_usage_result = Mock()
            mock_usage_result.success = True
            mock_usage_result.message = "アイテムを使用しました"
            mock_usage_result.quantity_consumed = 1
            mock_usage_manager.use_item.return_value = mock_usage_result
            
            # メッセージ表示をモック
            window.show_message = Mock()
            window.refresh_view = Mock()
            
            window.use_item(mock_item_instance, 0)
            
            mock_usage_manager.use_item.assert_called_once()
            window.show_message.assert_called_once()
            window.refresh_view.assert_called_once()

    def test_transfer_item_success(self, mock_window_manager, mock_inventory):
        """アイテム移動の成功ケースをテスト"""
        window = InventoryWindow("test_inventory")
        window.current_inventory = mock_inventory
        window.transfer_source = (mock_inventory, 0)
        
        # アイテムインスタンスをモック
        item_instance = Mock()
        mock_inventory.get_item_at_slot.return_value = item_instance
        
        # メッセージ表示をモック
        window.show_message = Mock()
        window.refresh_view = Mock()
        
        window.transfer_item_to_slot(5)
        
        mock_inventory.transfer_item.assert_called_once_with(0, 5)
        window.show_message.assert_called_once()
        window.refresh_view.assert_called_once()

    def test_drop_item_success(self, mock_window_manager, mock_inventory, mock_item_instance):
        """アイテム破棄の成功ケースをテスト"""
        window = InventoryWindow("test_inventory")
        window.current_inventory = mock_inventory
        
        # メッセージ表示をモック
        window.show_message = Mock()
        window.refresh_view = Mock()
        
        window.drop_item(mock_item_instance, 0)
        
        mock_inventory.remove_item.assert_called_once_with(0, mock_item_instance.quantity)
        window.show_message.assert_called_once()
        window.refresh_view.assert_called_once()

    def test_sort_inventory(self, mock_window_manager, mock_inventory):
        """インベントリ整理が正しく動作することを確認"""
        window = InventoryWindow("test_inventory")
        window.current_inventory = mock_inventory
        
        # 整理メソッドをモック
        mock_inventory.sort_items.return_value = None
        
        # メッセージ表示をモック
        window.show_message = Mock()
        window.refresh_view = Mock()
        
        window.sort_inventory()
        
        mock_inventory.sort_items.assert_called_once()
        window.show_message.assert_called_once()
        window.refresh_view.assert_called_once()

    def test_show_inventory_statistics(self, mock_window_manager, mock_inventory):
        """インベントリ統計表示が正しく動作することを確認"""
        window = InventoryWindow("test_inventory")
        window.current_inventory = mock_inventory
        
        # ダイアログ表示をモック
        window.show_dialog = Mock()
        
        window.show_inventory_statistics()
        
        window.show_dialog.assert_called_once()

    def test_filter_items_by_type(self, mock_window_manager, mock_inventory):
        """アイテムタイプフィルタリングが正しく動作することを確認"""
        window = InventoryWindow("test_inventory")
        window.current_inventory = mock_inventory
        
        # フィルタリング結果をモック
        filtered_items = [(0, Mock()), (1, Mock())]
        window._filter_items_by_type = Mock(return_value=filtered_items)
        
        # 表示更新をモック
        window.refresh_filtered_view = Mock()
        
        window.filter_items_by_type("consumable")
        
        window._filter_items_by_type.assert_called_once_with("consumable")
        window.refresh_filtered_view.assert_called_once()

    def test_search_items_by_name(self, mock_window_manager, mock_inventory):
        """アイテム名検索が正しく動作することを確認"""
        window = InventoryWindow("test_inventory")
        window.current_inventory = mock_inventory
        
        # 検索結果をモック
        search_results = [(0, Mock()), (2, Mock())]
        window._search_items_by_name = Mock(return_value=search_results)
        
        # 表示更新をモック
        window.refresh_filtered_view = Mock()
        
        window.search_items_by_name("テスト")
        
        window._search_items_by_name.assert_called_once_with("テスト")
        window.refresh_filtered_view.assert_called_once()

    def test_window_lifecycle(self, mock_window_manager):
        """ウィンドウのライフサイクルが正しく動作することを確認"""
        window = InventoryWindow("test_inventory")
        
        # 作成状態の確認
        assert window.window_id == "test_inventory"
        
        # 表示
        window.create = Mock()
        window.show()
        window.create.assert_called_once()
        
        # 非表示
        window.hide()
        
        # 破棄
        window.destroy()
        assert window.current_party is None
        assert window.current_character is None
        assert window.current_inventory is None