"""
inventory_ui.pyのInventoryWindow移行テスト

t-wada式TDDに従って、既存のUIMenu形式から新WindowSystem形式への移行をテスト
"""
import pytest
import pygame
from unittest.mock import Mock, patch, MagicMock

from src.ui.window_system import WindowManager
from src.ui.window_system.inventory_window import InventoryWindow
from src.character.party import Party
from src.character.character import Character
from src.inventory.inventory import Inventory, InventorySlot
from src.items.item import Item, ItemInstance
from src.core.config_manager import config_manager
from src.utils.logger import logger


class TestInventoryUIInventoryWindowMigration:
    """インベントリUIのInventoryWindow移行テスト"""
    
    def setup_method(self):
        """テスト前の準備"""
        # Pygameを初期化
        if not pygame.get_init():
            pygame.init()
        
        # WindowManagerをリセット
        WindowManager._instance = None
        self.window_manager = WindowManager.get_instance()
        
        # モックキャラクターを作成
        self.mock_character = Mock()
        self.mock_character.name = "テストキャラクター"
        self.mock_character.get_inventory = Mock(return_value=Mock())
        
        # モックパーティを作成
        self.mock_party = Mock()
        self.mock_party.name = "テストパーティ"
        self.mock_party.get_all_characters = Mock(return_value=[self.mock_character])
        self.mock_party.get_party_inventory = Mock(return_value=Mock())
        
        # モックインベントリを作成
        self.mock_inventory = Mock(spec=Inventory)
        self.mock_inventory.get_all_items.return_value = []
        self.mock_inventory.get_item_count.return_value = 5
        
    def test_migrated_inventory_ui_should_use_window_manager(self):
        """移行後のInventoryUIはWindowManagerを使用すべき"""
        # Given: 移行後のInventoryUI（新形式）
        from src.ui.inventory_ui import InventoryUI
        
        # When: 新形式のInventoryUIを作成
        inventory_ui = InventoryUI()
        
        # Then: WindowManagerが設定されている
        assert hasattr(inventory_ui, 'window_manager')
        assert inventory_ui.window_manager is not None
        assert isinstance(inventory_ui.window_manager, WindowManager)
    
    def test_migrated_inventory_ui_should_create_inventory_window(self):
        """移行後のInventoryUIはInventoryWindowを作成すべき"""
        # Given: 移行後のInventoryUI
        from src.ui.inventory_ui import InventoryUI
        inventory_ui = InventoryUI()
        inventory_ui.set_party(self.mock_party)
        
        # When: インベントリUIを表示
        inventory_ui.show_party_inventory_menu(self.mock_party)
        
        # Then: InventoryWindowが作成される
        assert hasattr(inventory_ui, 'inventory_window')
        assert inventory_ui.inventory_window is not None
        assert isinstance(inventory_ui.inventory_window, InventoryWindow)
    
    def test_migrated_inventory_ui_should_not_use_legacy_ui_menu(self):
        """移行後のInventoryUIは旧UIMenuを使用しないべき"""
        # Given: 移行後のInventoryUI
        from src.ui.inventory_ui import InventoryUI
        inventory_ui = InventoryUI()
        
        # When: InventoryUIのソースコードを確認
        import inspect
        source = inspect.getsource(InventoryUI)
        
        # Then: 旧UIMenuクラスのインポートや使用がない
        assert 'UIMenu' not in source
        assert 'UIDialog' not in source
        assert 'ui_manager' not in source
        assert 'base_ui' not in source
    
    def test_migrated_inventory_ui_should_delegate_inventory_actions_to_window(self):
        """移行後のInventoryUIはインベントリアクションをInventoryWindowに委譲すべき"""
        # Given: 移行後のInventoryUI with InventoryWindow
        from src.ui.inventory_ui import InventoryUI
        inventory_ui = InventoryUI()
        inventory_ui.set_party(self.mock_party)
        
        # InventoryWindowを表示
        inventory_ui.show_party_inventory_menu(self.mock_party)
        
        # When: キャラクターインベントリを表示
        result = inventory_ui.show_character_inventory(self.mock_character)
        
        # Then: InventoryWindowにインベントリ表示が委譲される
        assert result is True
        assert inventory_ui.inventory_window is not None
    
    def test_migrated_inventory_ui_should_handle_item_operations_through_window(self):
        """移行後のInventoryUIはアイテム操作をInventoryWindowを通して行うべき"""
        # Given: 移行後のInventoryUI with InventoryWindow
        from src.ui.inventory_ui import InventoryUI
        inventory_ui = InventoryUI()
        inventory_ui.set_party(self.mock_party)
        
        # InventoryWindowを表示
        inventory_ui.show_party_inventory_menu(self.mock_party)
        
        # When: アイテム使用
        mock_item = Mock()
        mock_item.item_id = "test_item"
        
        with patch.object(inventory_ui.inventory_window, 'use_item', return_value=True) as mock_use:
            result = inventory_ui.use_item(mock_item, self.mock_character)
        
        # Then: InventoryWindowのuse_itemが呼ばれる
        assert result is True
        mock_use.assert_called_once_with(mock_item, self.mock_character)
    
    def test_migrated_inventory_ui_should_preserve_existing_public_api(self):
        """移行後のInventoryUIは既存の公開APIを保持すべき"""
        # Given: 移行後のInventoryUI
        from src.ui.inventory_ui import InventoryUI
        inventory_ui = InventoryUI()
        
        # Then: 既存の公開メソッドが保持されている
        assert hasattr(inventory_ui, 'set_party')
        assert hasattr(inventory_ui, 'show_party_inventory_menu')
        assert hasattr(inventory_ui, 'show_character_inventory')
        assert hasattr(inventory_ui, 'use_item')
        assert hasattr(inventory_ui, 'transfer_item')
        assert hasattr(inventory_ui, 'drop_item')
        assert hasattr(inventory_ui, 'sort_inventory')
        assert hasattr(inventory_ui, 'close_inventory_ui')
    
    def test_migrated_inventory_ui_should_use_window_system_configuration(self):
        """移行後のInventoryUIはWindowSystem設定を使用すべき"""
        # Given: 移行後のInventoryUI
        from src.ui.inventory_ui import InventoryUI
        inventory_ui = InventoryUI()
        inventory_ui.current_inventory = self.mock_inventory
        
        # When: WindowSystem設定でInventoryWindowを作成
        inventory_config = inventory_ui._create_inventory_window_config("character")
        
        # Then: WindowSystem形式の設定が作成される
        assert isinstance(inventory_config, dict)
        assert 'inventory_type' in inventory_config or 'inventory' in inventory_config
    
    def test_migrated_inventory_ui_should_handle_item_transfer_operations(self):
        """移行後のInventoryUIはアイテム転送操作を適切に処理すべき"""
        # Given: 移行後のInventoryUI with InventoryWindow
        from src.ui.inventory_ui import InventoryUI
        inventory_ui = InventoryUI()
        inventory_ui.set_party(self.mock_party)
        
        # InventoryWindowを表示
        inventory_ui.show_party_inventory_menu(self.mock_party)
        
        # モックアイテムとインベントリ
        mock_item = Mock()
        mock_item.item_id = "test_item"
        source_inventory = Mock()
        target_inventory = Mock()
        
        # When: アイテム転送を試行
        with patch.object(inventory_ui.inventory_window, 'transfer_item', return_value=True) as mock_transfer:
            result = inventory_ui.transfer_item(mock_item, source_inventory, target_inventory)
        
        # Then: InventoryWindowで転送が実行される
        mock_transfer.assert_called_once_with(mock_item, source_inventory, target_inventory)
        assert result is True
    
    def test_migrated_inventory_ui_should_cleanup_resources_properly(self):
        """移行後のInventoryUIはリソースを適切にクリーンアップすべき"""
        # Given: 移行後のInventoryUI with InventoryWindow
        from src.ui.inventory_ui import InventoryUI
        inventory_ui = InventoryUI()
        inventory_ui.set_party(self.mock_party)
        
        # InventoryWindowを表示
        inventory_ui.show_party_inventory_menu(self.mock_party)
        
        # When: クリーンアップを実行
        inventory_ui.cleanup()
        
        # Then: InventoryWindowもクリーンアップされる
        assert inventory_ui.inventory_window is None or hasattr(inventory_ui.inventory_window, 'cleanup')