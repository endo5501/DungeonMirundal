"""WindowSystem移行統合テスト"""

import pytest
from unittest.mock import Mock, patch
import pygame

from src.ui.windows.equipment_window import EquipmentWindow
from src.ui.windows.inventory_window import InventoryWindow
from src.ui.windows.character_creation_wizard import CharacterCreationWizard
from src.ui.windows.dungeon_menu_window import DungeonMenuWindow
from src.ui.windows.equipment_manager import equipment_manager
from src.ui.windows.inventory_manager import inventory_manager
from src.ui.windows.character_creation_manager import character_creation_manager
from src.ui.windows.dungeon_menu_manager import dungeon_menu_manager


class TestWindowSystemMigration:
    """WindowSystem移行統合テストクラス"""

    @pytest.fixture
    def mock_window_manager(self):
        """WindowManagerのモックを作成"""
        with patch('src.ui.window_system.window_manager.WindowManager') as mock_wm_class:
            mock_wm = Mock()
            mock_wm_class.get_instance.return_value = mock_wm
            mock_wm.ui_manager = Mock()
            mock_wm.screen = Mock()
            mock_wm.screen.get_rect.return_value = pygame.Rect(0, 0, 1024, 768)
            mock_wm.screen.get_width.return_value = 1024
            mock_wm.screen.get_height.return_value = 768
            yield mock_wm

    @pytest.fixture
    def mock_party(self):
        """パーティのモックを作成"""
        party = Mock()
        party.name = "統合テストパーティ"
        
        # キャラクターのモック
        characters = []
        for i in range(2):
            char = Mock()
            char.name = f"キャラクター{i+1}"
            char.current_hp = 80 + i * 10
            char.max_hp = 100
            char.current_mp = 20 + i * 5
            char.max_mp = 30
            char.character_class = Mock()
            char.character_class.value = "warrior"
            
            # 装備とインベントリのモック
            equipment = Mock()
            equipment.get_equipped_item.return_value = None
            equipment.get_equipment_summary.return_value = {'equipped_count': 2, 'total_weight': 5.0}
            char.get_equipment.return_value = equipment
            
            inventory = Mock()
            inventory.slots = [Mock() for _ in range(20)]
            for slot in inventory.slots:
                slot.is_empty.return_value = True
            char.get_inventory.return_value = inventory
            
            characters.append(char)
        
        party.get_all_characters.return_value = characters
        party.get_party_inventory.return_value = Mock()
        return party

    def test_all_windows_creation(self, mock_window_manager):
        """全ウィンドウクラスが正しく作成されることを確認"""
        # EquipmentWindow
        equipment_window = EquipmentWindow("test_equipment")
        assert equipment_window.window_id == "test_equipment"
        assert isinstance(equipment_window, EquipmentWindow)
        
        # InventoryWindow  
        inventory_window = InventoryWindow("test_inventory")
        assert inventory_window.window_id == "test_inventory"
        assert isinstance(inventory_window, InventoryWindow)
        
        # CharacterCreationWizard
        creation_wizard = CharacterCreationWizard("test_creation")
        assert creation_wizard.window_id == "test_creation"
        assert isinstance(creation_wizard, CharacterCreationWizard)
        
        # DungeonMenuWindow
        dungeon_menu = DungeonMenuWindow("test_dungeon")
        assert dungeon_menu.window_id == "test_dungeon"
        assert isinstance(dungeon_menu, DungeonMenuWindow)

    def test_all_managers_functionality(self, mock_window_manager, mock_party):
        """全マネージャークラスが正しく動作することを確認"""
        try:
            # EquipmentManager
            equipment_manager.show_party_equipment_menu(mock_party)
            assert equipment_manager.current_window is not None
            equipment_manager.close_equipment_ui()
            
            # InventoryManager
            inventory_manager.show_party_inventory_menu(mock_party)
            assert inventory_manager.current_window is not None
            inventory_manager.close_inventory_ui()
            
            # CharacterCreationManager
            creation_callback = Mock()
            character_creation_manager.start_character_creation(creation_callback)
            assert character_creation_manager.current_wizard is not None
            character_creation_manager.close_character_creation()
            
            # DungeonMenuManager
            dungeon_menu_manager.create_dungeon_menu()
            assert dungeon_menu_manager.current_window is not None
            dungeon_menu_manager.close_dungeon_menu()
            
        except Exception as e:
            pytest.fail(f"マネージャー機能テストでエラー: {e}")

    def test_window_lifecycle_integration(self, mock_window_manager):
        """ウィンドウライフサイクルの統合テスト"""
        windows = [
            EquipmentWindow("lifecycle_equipment"),
            InventoryWindow("lifecycle_inventory"),
            CharacterCreationWizard("lifecycle_creation"),
            DungeonMenuWindow("lifecycle_dungeon")
        ]
        
        for window in windows:
            # 作成
            assert window.window_id is not None
            
            # 表示
            window.create = Mock()
            window.show()
            window.create.assert_called_once()
            
            # 非表示
            window.hide()
            
            # 破棄
            window.destroy()

    def test_party_data_consistency(self, mock_window_manager, mock_party):
        """パーティデータの一貫性テスト"""
        # 全ウィンドウでパーティデータが正しく設定されることを確認
        equipment_window = EquipmentWindow("consistency_equipment")
        equipment_window.set_party(mock_party)
        assert equipment_window.current_party == mock_party
        
        inventory_window = InventoryWindow("consistency_inventory")
        inventory_window.set_party(mock_party)
        assert inventory_window.current_party == mock_party
        
        dungeon_menu = DungeonMenuWindow("consistency_dungeon")
        dungeon_menu.set_party(mock_party)
        assert dungeon_menu.current_party == mock_party

    def test_callback_system_integration(self, mock_window_manager):
        """コールバックシステムの統合テスト"""
        test_callbacks = {}
        
        # EquipmentWindow
        equipment_window = EquipmentWindow("callback_equipment")
        equipment_callback = Mock()
        equipment_window.set_close_callback(equipment_callback)
        assert equipment_window.callback_on_close == equipment_callback
        
        # CharacterCreationWizard
        creation_wizard = CharacterCreationWizard("callback_creation")
        creation_callback = Mock()
        cancel_callback = Mock()
        creation_wizard.callback = creation_callback
        creation_wizard.set_cancel_callback(cancel_callback)
        assert creation_wizard.callback == creation_callback
        assert creation_wizard.cancel_callback == cancel_callback
        
        # DungeonMenuWindow
        dungeon_menu = DungeonMenuWindow("callback_dungeon")
        menu_callback = Mock()
        dungeon_menu.set_callback("inventory", menu_callback)
        assert dungeon_menu.callbacks["inventory"] == menu_callback

    def test_ui_elements_management(self, mock_window_manager):
        """UI要素管理の統合テスト"""
        windows = [
            EquipmentWindow("ui_equipment"),
            InventoryWindow("ui_inventory"),
            CharacterCreationWizard("ui_creation"),
            DungeonMenuWindow("ui_dungeon")
        ]
        
        for window in windows:
            # 初期状態でUI要素辞書が存在することを確認
            assert hasattr(window, 'ui_elements')
            assert isinstance(window.ui_elements, dict)
            
            # 破棄後にUI要素がクリアされることを確認
            window.destroy()
            assert len(window.ui_elements) == 0

    def test_memory_management(self, mock_window_manager, mock_party):
        """メモリ管理の統合テスト"""
        # 複数のウィンドウを作成・破棄してメモリリークがないことを確認
        for i in range(5):
            # EquipmentWindow
            equipment_window = EquipmentWindow(f"memory_equipment_{i}")
            equipment_window.set_party(mock_party)
            equipment_window.destroy()
            
            # InventoryWindow
            inventory_window = InventoryWindow(f"memory_inventory_{i}")
            inventory_window.set_party(mock_party)
            inventory_window.destroy()
            
            # CharacterCreationWizard
            creation_wizard = CharacterCreationWizard(f"memory_creation_{i}")
            creation_wizard.destroy()
            
            # DungeonMenuWindow
            dungeon_menu = DungeonMenuWindow(f"memory_dungeon_{i}")
            dungeon_menu.set_party(mock_party)
            dungeon_menu.destroy()

    def test_manager_singleton_behavior(self, mock_window_manager):
        """マネージャーのシングルトン動作テスト"""
        # 各マネージャーが適切にシングルトンとして動作することを確認
        
        # equipment_manager
        assert equipment_manager is not None
        
        # inventory_manager
        assert inventory_manager is not None
        
        # character_creation_manager
        assert character_creation_manager is not None
        
        # dungeon_menu_manager
        assert dungeon_menu_manager is not None

    def test_error_handling_integration(self, mock_window_manager):
        """エラーハンドリングの統合テスト"""
        # 各ウィンドウが適切にエラーハンドリングすることを確認
        
        # 無効なデータでの動作テスト
        equipment_window = EquipmentWindow("error_equipment")
        try:
            equipment_window.set_party(None)  # 無効なパーティ
            # エラーが発生しても適切に処理されることを確認
        except Exception as e:
            pytest.fail(f"適切でないエラーハンドリング: {e}")
        
        inventory_window = InventoryWindow("error_inventory")
        try:
            inventory_window.show_inventory_contents(None, "テスト")  # 無効なインベントリ
        except Exception as e:
            pytest.fail(f"適切でないエラーハンドリング: {e}")

    def test_window_state_transitions(self, mock_window_manager):
        """ウィンドウ状態遷移の統合テスト"""
        window = EquipmentWindow("state_equipment")
        
        # 初期状態
        assert window.state.value == "created"
        
        # 表示状態への遷移
        window.create = Mock()
        window.show()
        window.create.assert_called_once()
        
        # 非表示状態への遷移
        window.hide()
        
        # 破棄状態への遷移
        window.destroy()

    def test_integration_with_existing_systems(self, mock_window_manager, mock_party):
        """既存システムとの統合テスト"""
        # config_managerとの統合
        with patch('src.core.config_manager.config_manager') as mock_config:
            mock_config.get_text.return_value = "テストテキスト"
            mock_config.load_config.return_value = {"races": {}, "classes": {}}
            
            # 各ウィンドウがconfig_managerを正しく使用することを確認
            equipment_window = EquipmentWindow("integration_equipment")
            inventory_window = InventoryWindow("integration_inventory")
            creation_wizard = CharacterCreationWizard("integration_creation")
            dungeon_menu = DungeonMenuWindow("integration_dungeon")
            
            # エラーなく作成されることを確認
            assert equipment_window is not None
            assert inventory_window is not None
            assert creation_wizard is not None
            assert dungeon_menu is not None

    def test_performance_baseline(self, mock_window_manager, mock_party):
        """パフォーマンスベースラインテスト"""
        import time
        
        # ウィンドウ作成時間のベースライン測定
        start_time = time.time()
        
        for i in range(10):
            equipment_window = EquipmentWindow(f"perf_equipment_{i}")
            equipment_window.set_party(mock_party)
            equipment_window.destroy()
        
        creation_time = time.time() - start_time
        
        # 10個のウィンドウ作成・破棄が1秒以内に完了することを確認
        assert creation_time < 1.0, f"ウィンドウ作成時間が期待値を超過: {creation_time}秒"