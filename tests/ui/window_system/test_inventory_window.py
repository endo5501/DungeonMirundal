"""
InventoryWindow のテスト

t-wada式TDDによるテストファースト開発
インベントリシステムから新Window Systemへの移行
"""

import pytest
import pygame
import pygame_gui
from unittest.mock import Mock, patch, MagicMock
from src.ui.window_system import Window, WindowState
from src.ui.window_system.inventory_window import InventoryWindow, InventoryType


class TestInventoryWindow:
    """InventoryWindow のテストクラス"""
    
    def setup_method(self):
        """各テストメソッドの前に実行される"""
        pygame.init()
        pygame.display.set_mode((1, 1), pygame.NOFRAME)
    
    def teardown_method(self):
        """各テストメソッドの後に実行される"""
        pygame.quit()
    
    def test_inventory_window_inherits_from_window(self):
        """InventoryWindowがWindowクラスを継承することを確認"""
        # Given: インベントリ設定
        inventory_config = {
            'inventory_type': 'party',
            'inventory': Mock(),
            'party': Mock()
        }
        
        # When: InventoryWindowを作成
        inventory_window = InventoryWindow('inventory', inventory_config)
        
        # Then: Windowクラスを継承している
        assert isinstance(inventory_window, Window)
        assert inventory_window.window_id == 'inventory'
        assert inventory_window.inventory_type == InventoryType.PARTY
    
    def test_inventory_validates_config_structure(self):
        """インベントリの設定構造が検証されることを確認"""
        # When: inventory_typeが無い設定でウィンドウを作成しようとする
        # Then: 例外が発生する
        with pytest.raises(ValueError, match="Inventory config must contain 'inventory_type'"):
            InventoryWindow('invalid_inventory', {})
        
        # When: inventoryが無い設定でウィンドウを作成しようとする
        # Then: 例外が発生する
        with pytest.raises(ValueError, match="Inventory config must contain 'inventory'"):
            InventoryWindow('invalid_inventory', {'inventory_type': 'party'})
    
    def test_inventory_displays_item_grid(self):
        """アイテムグリッドが表示されることを確認"""
        # Given: アイテムを含むインベントリ
        mock_inventory = Mock()
        mock_slots = []
        for i in range(10):
            slot = Mock()
            slot.item = None
            slot.quantity = 0
            mock_slots.append(slot)
        mock_inventory.slots = mock_slots
        mock_inventory.capacity = 10
        
        inventory_config = {
            'inventory_type': 'character',
            'inventory': mock_inventory,
            'character': Mock()
        }
        
        inventory_window = InventoryWindow('char_inventory', inventory_config)
        inventory_window.create()
        
        # Then: アイテムグリッドが作成される
        assert inventory_window.item_grid is not None
        assert len(inventory_window.slot_buttons) == 10
    
    def test_inventory_shows_item_details_on_selection(self):
        """アイテム選択時に詳細が表示されることを確認"""
        # Given: アイテムを含むインベントリ
        mock_item = Mock()
        mock_item.name = 'ポーション'
        mock_item.description = '体力を回復する薬'
        mock_item.category = 'consumable'
        mock_item.weight = 0.5
        mock_item.value = 100
        
        mock_slot = Mock()
        mock_slot.item = mock_item
        mock_slot.quantity = 5
        
        mock_inventory = Mock()
        mock_inventory.slots = [mock_slot] + [Mock(item=None) for _ in range(9)]
        mock_inventory.capacity = 10
        
        inventory_config = {
            'inventory_type': 'party',
            'inventory': mock_inventory,
            'party': Mock()
        }
        
        inventory_window = InventoryWindow('party_inventory', inventory_config)
        inventory_window.create()
        
        # When: アイテムを選択
        result = inventory_window.select_item_slot(0)
        
        # Then: 詳細パネルが更新される
        assert result is True
        assert inventory_window.selected_slot_index == 0
        assert inventory_window.detail_panel is not None
    
    def test_inventory_supports_item_actions(self):
        """アイテムアクション（使用、装備、破棄）が動作することを確認"""
        # Given: 使用可能なアイテムを含むインベントリ
        mock_item = Mock()
        mock_item.item_id = 'potion_001'
        mock_item.name = 'ポーション'
        mock_item.weight = 0.3
        mock_item.value = 50
        mock_item.is_consumable.return_value = True
        mock_item.is_equippable.return_value = False
        
        mock_slot = Mock()
        mock_slot.item = mock_item
        mock_slot.quantity = 3
        
        mock_inventory = Mock()
        mock_inventory.slots = [mock_slot] + [Mock(item=None) for _ in range(9)]
        mock_inventory.capacity = 10
        
        inventory_config = {
            'inventory_type': 'character',
            'inventory': mock_inventory,
            'character': Mock()
        }
        
        inventory_window = InventoryWindow('action_inventory', inventory_config)
        inventory_window.create()
        inventory_window.selected_slot_index = 0
        
        # When: アイテムを使用
        with patch.object(inventory_window, 'send_message') as mock_send:
            result = inventory_window.use_selected_item()
        
        # Then: 使用メッセージが送信される
        assert result is True
        mock_send.assert_called_once_with('item_used', {
            'item_id': 'potion_001',
            'inventory_type': 'character',
            'slot_index': 0
        })
    
    def test_inventory_handles_item_movement(self):
        """アイテムの移動（ドラッグ&ドロップ）が動作することを確認"""
        # Given: 複数のアイテムを含むインベントリ
        mock_item1 = Mock()
        mock_item1.name = 'ソード'
        mock_item1.weight = 2.5
        mock_item1.value = 300
        mock_slot1 = Mock(item=mock_item1, quantity=1)
        
        mock_item2 = Mock()
        mock_item2.name = 'シールド'
        mock_item2.weight = 3.0
        mock_item2.value = 250
        mock_slot2 = Mock(item=mock_item2, quantity=1)
        
        mock_inventory = Mock()
        remaining_slots = []
        for i in range(8):
            slot = Mock()
            slot.item = None
            slot.quantity = 0
            remaining_slots.append(slot)
        mock_inventory.slots = [mock_slot1, mock_slot2] + remaining_slots
        mock_inventory.capacity = 10
        mock_inventory.can_move_item.return_value = True
        
        inventory_config = {
            'inventory_type': 'party',
            'inventory': mock_inventory,
            'party': Mock()
        }
        
        inventory_window = InventoryWindow('move_inventory', inventory_config)
        inventory_window.create()
        
        # When: アイテムを移動
        result = inventory_window.move_item(0, 5)
        
        # Then: 移動が実行される
        assert result is True
        mock_inventory.move_item.assert_called_once_with(0, 5)
    
    def test_inventory_supports_item_sorting(self):
        """アイテムのソート機能が動作することを確認"""
        # Given: ソート可能なインベントリ
        mock_inventory = Mock()
        mock_slots = []
        for i in range(10):
            slot = Mock()
            slot.item = None
            slot.quantity = 0
            mock_slots.append(slot)
        mock_inventory.slots = mock_slots
        mock_inventory.capacity = 10
        
        inventory_config = {
            'inventory_type': 'party',
            'inventory': mock_inventory,
            'party': Mock(),
            'allow_sorting': True
        }
        
        inventory_window = InventoryWindow('sort_inventory', inventory_config)
        inventory_window.create()
        
        # When: ソートを実行
        with patch.object(inventory_window, 'send_message') as mock_send:
            result = inventory_window.sort_items()
        
        # Then: ソートが実行される
        assert result is True
        mock_inventory.sort_items.assert_called_once()
        mock_send.assert_called_once_with('inventory_sorted', {
            'inventory_type': 'party'
        })
    
    def test_inventory_displays_weight_and_capacity(self):
        """重量と容量が表示されることを確認"""
        # Given: 重量制限のあるインベントリ
        mock_inventory = Mock()
        mock_slots = []
        for i in range(10):
            slot = Mock()
            slot.item = None
            slot.quantity = 0
            mock_slots.append(slot)
        mock_inventory.slots = mock_slots
        mock_inventory.capacity = 10
        mock_inventory.get_total_weight.return_value = 25.5
        mock_inventory.get_total_value.return_value = 1500
        
        inventory_config = {
            'inventory_type': 'character',
            'inventory': mock_inventory,
            'character': Mock(),
            'weight_limit': 50.0
        }
        
        inventory_window = InventoryWindow('weight_inventory', inventory_config)
        inventory_window.create()
        
        # Then: 統計情報が表示される
        assert inventory_window.stats_panel is not None
        # 重量と容量の表示を確認
    
    def test_inventory_supports_filtering(self):
        """アイテムフィルタリング機能が動作することを確認"""
        # Given: フィルタリング可能なインベントリ
        mock_inventory = Mock()
        mock_slots = []
        for i in range(20):
            slot = Mock()
            slot.item = None
            slot.quantity = 0
            mock_slots.append(slot)
        mock_inventory.slots = mock_slots
        mock_inventory.capacity = 20
        
        inventory_config = {
            'inventory_type': 'party',
            'inventory': mock_inventory,
            'party': Mock(),
            'enable_filtering': True
        }
        
        inventory_window = InventoryWindow('filter_inventory', inventory_config)
        inventory_window.create()
        
        # When: カテゴリでフィルタリング
        result = inventory_window.set_filter('weapon')
        
        # Then: フィルタが適用される
        assert result is True
        assert inventory_window.current_filter == 'weapon'
    
    def test_inventory_handles_keyboard_navigation(self):
        """キーボードナビゲーションが動作することを確認"""
        # Given: インベントリウィンドウ
        mock_inventory = Mock()
        mock_slots = []
        for i in range(10):
            slot = Mock()
            slot.item = None
            slot.quantity = 0
            mock_slots.append(slot)
        mock_inventory.slots = mock_slots
        mock_inventory.capacity = 10
        
        inventory_config = {
            'inventory_type': 'party',
            'inventory': mock_inventory,
            'party': Mock()
        }
        
        inventory_window = InventoryWindow('nav_inventory', inventory_config)
        inventory_window.create()
        
        # When: 矢印キーで移動（最初に選択状態にしてから移動）
        inventory_window.selected_slot_index = 0  # 初期選択
        
        arrow_event = Mock()
        arrow_event.type = pygame.KEYDOWN
        arrow_event.key = pygame.K_RIGHT
        arrow_event.mod = 0
        
        result = inventory_window.handle_event(arrow_event)
        
        # Then: 選択が移動する
        assert result is True
        assert inventory_window.selected_slot_index == 1
    
    def test_inventory_supports_quick_slots(self):
        """クイックスロット機能が動作することを確認"""
        # Given: クイックスロット対応のインベントリ
        mock_inventory = Mock()
        mock_slots = []
        for i in range(10):
            slot = Mock()
            slot.item = None
            slot.quantity = 0
            mock_slots.append(slot)
        mock_inventory.slots = mock_slots
        mock_inventory.capacity = 10
        
        inventory_config = {
            'inventory_type': 'character',
            'inventory': mock_inventory,
            'character': Mock(),
            'enable_quick_slots': True,
            'quick_slot_count': 4
        }
        
        inventory_window = InventoryWindow('quick_inventory', inventory_config)
        inventory_window.create()
        
        # When: アイテムをクイックスロットに割り当て
        result = inventory_window.assign_to_quick_slot(0, 1)
        
        # Then: 割り当てが成功する
        assert result is True
        assert inventory_window.quick_slots[1] == 0
    
    def test_inventory_escape_key_closes(self):
        """ESCキーでインベントリが閉じることを確認"""
        # Given: インベントリウィンドウ
        mock_inventory = Mock()
        mock_inventory.slots = []
        mock_inventory.capacity = 10
        
        inventory_config = {
            'inventory_type': 'party',
            'inventory': mock_inventory,
            'party': Mock()
        }
        
        inventory_window = InventoryWindow('esc_inventory', inventory_config)
        inventory_window.create()
        
        # When: ESCキーを押す
        with patch.object(inventory_window, 'send_message') as mock_send:
            result = inventory_window.handle_escape()
        
        # Then: 閉じるメッセージが送信される
        assert result is True
        mock_send.assert_called_once_with('inventory_close_requested', {
            'inventory_type': 'party'
        })
    
    def test_inventory_transfers_between_inventories(self):
        """インベントリ間のアイテム転送が動作することを確認"""
        # Given: 転送元と転送先のインベントリ
        mock_item = Mock()
        mock_item.item_id = 'sword_001'
        mock_item.name = 'ソード'
        mock_item.weight = 2.5
        mock_item.value = 300
        mock_slot = Mock(item=mock_item, quantity=1)
        
        mock_source_inventory = Mock()
        remaining_slots = []
        for i in range(9):
            slot = Mock()
            slot.item = None
            slot.quantity = 0
            remaining_slots.append(slot)
        mock_source_inventory.slots = [mock_slot] + remaining_slots
        mock_source_inventory.capacity = 10
        
        mock_target_inventory = Mock()
        mock_target_inventory.can_add_item.return_value = True
        
        inventory_config = {
            'inventory_type': 'character',
            'inventory': mock_source_inventory,
            'character': Mock(),
            'target_inventory': mock_target_inventory
        }
        
        inventory_window = InventoryWindow('transfer_inventory', inventory_config)
        inventory_window.create()
        inventory_window.selected_slot_index = 0  # アイテムがあるスロットを選択
        
        # When: アイテムを転送
        with patch.object(inventory_window, 'send_message') as mock_send:
            result = inventory_window.transfer_selected_item()
        
        # Then: 転送メッセージが送信される
        assert result is True
        mock_send.assert_called_once()
    
    def test_inventory_cleanup_removes_ui_elements(self):
        """クリーンアップでUI要素が適切に削除されることを確認"""
        # Given: 作成されたインベントリウィンドウ
        mock_inventory = Mock()
        mock_slots = []
        for i in range(10):
            slot = Mock()
            slot.item = None
            slot.quantity = 0
            mock_slots.append(slot)
        mock_inventory.slots = mock_slots
        mock_inventory.capacity = 10
        
        inventory_config = {
            'inventory_type': 'party',
            'inventory': mock_inventory,
            'party': Mock()
        }
        
        inventory_window = InventoryWindow('cleanup_inventory', inventory_config)
        inventory_window.create()
        
        # When: クリーンアップを実行
        inventory_window.cleanup_ui()
        
        # Then: UI要素が削除される
        assert inventory_window.slot_buttons == []
        assert inventory_window.item_grid is None
        assert inventory_window.detail_panel is None
        assert inventory_window.ui_manager is None