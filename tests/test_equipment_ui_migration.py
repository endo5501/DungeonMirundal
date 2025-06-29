"""
equipment_ui.pyのEquipmentWindow移行テスト

t-wada式TDDに従って、既存のUIMenu形式から新WindowSystem形式への移行をテスト
"""
import pytest
import pygame
from unittest.mock import Mock, patch, MagicMock

from src.ui.window_system import WindowManager
from src.ui.window_system.equipment_window import EquipmentWindow
from src.character.party import Party
from src.character.character import Character
from src.equipment.equipment import Equipment, EquipmentSlot
from src.core.config_manager import config_manager
from src.utils.logger import logger


class TestEquipmentUIEquipmentWindowMigration:
    """装備UIのEquipmentWindow移行テスト"""
    
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
        self.mock_character.get_equipment = Mock(return_value=Mock())
        self.mock_character.get_inventory = Mock(return_value=Mock())
        
        # モックパーティを作成
        self.mock_party = Mock()
        self.mock_party.name = "テストパーティ"
        self.mock_party.get_all_characters = Mock(return_value=[self.mock_character])
        
        # モック装備を作成
        self.mock_equipment = Mock(spec=Equipment)
        self.mock_equipment.get_equipment_summary.return_value = {'equipped_count': 2}
        
    def test_migrated_equipment_ui_should_use_window_manager(self):
        """移行後のEquipmentUIはWindowManagerを使用すべき"""
        # Given: 移行後のEquipmentUI（新形式）
        from src.ui.equipment_ui import EquipmentUI
        
        # When: 新形式のEquipmentUIを作成
        equipment_ui = EquipmentUI()
        
        # Then: WindowManagerが設定されている
        assert hasattr(equipment_ui, 'window_manager')
        assert equipment_ui.window_manager is not None
        assert isinstance(equipment_ui.window_manager, WindowManager)
    
    def test_migrated_equipment_ui_should_create_equipment_window(self):
        """移行後のEquipmentUIはEquipmentWindowを作成すべき"""
        # Given: 移行後のEquipmentUI
        from src.ui.equipment_ui import EquipmentUI
        equipment_ui = EquipmentUI()
        equipment_ui.set_party(self.mock_party)
        
        # When: 装備UIを表示
        equipment_ui.show_party_equipment_menu(self.mock_party)
        
        # Then: EquipmentWindowが作成される
        assert hasattr(equipment_ui, 'equipment_window')
        assert equipment_ui.equipment_window is not None
        assert isinstance(equipment_ui.equipment_window, EquipmentWindow)
    
    def test_migrated_equipment_ui_should_not_use_legacy_ui_menu(self):
        """移行後のEquipmentUIは旧UIMenuを使用しないべき"""
        # Given: 移行後のEquipmentUI
        from src.ui.equipment_ui import EquipmentUI
        equipment_ui = EquipmentUI()
        
        # When: EquipmentUIのソースコードを確認
        import inspect
        source = inspect.getsource(EquipmentUI)
        
        # Then: 旧UIMenuクラスのインポートや使用がない
        assert 'UIMenu' not in source
        assert 'UIDialog' not in source
        assert 'UIButton' not in source
        assert 'ui_manager' not in source
        assert 'base_ui' not in source
    
    def test_migrated_equipment_ui_should_delegate_equipment_actions_to_window(self):
        """移行後のEquipmentUIは装備アクションをEquipmentWindowに委譲すべき"""
        # Given: 移行後のEquipmentUI with EquipmentWindow
        from src.ui.equipment_ui import EquipmentUI
        equipment_ui = EquipmentUI()
        equipment_ui.set_party(self.mock_party)
        
        # EquipmentWindowを表示
        equipment_ui.show_party_equipment_menu(self.mock_party)
        
        # When: キャラクター装備を表示
        result = equipment_ui.show_character_equipment(self.mock_character)
        
        # Then: EquipmentWindowに装備表示が委譲される
        assert result is True
        assert equipment_ui.equipment_window is not None
    
    def test_migrated_equipment_ui_should_handle_slot_operations_through_window(self):
        """移行後のEquipmentUIはスロット操作をEquipmentWindowを通して行うべき"""
        # Given: 移行後のEquipmentUI with EquipmentWindow
        from src.ui.equipment_ui import EquipmentUI
        equipment_ui = EquipmentUI()
        equipment_ui.set_party(self.mock_party)
        
        # EquipmentWindowを表示
        equipment_ui.show_party_equipment_menu(self.mock_party)
        
        # When: 装備スロット選択
        mock_slot = EquipmentSlot.WEAPON
        
        with patch.object(equipment_ui.equipment_window, 'select_equipment_slot', return_value=True) as mock_select:
            result = equipment_ui.select_equipment_slot(mock_slot)
        
        # Then: EquipmentWindowのselect_equipment_slotが呼ばれる
        assert result is True
        mock_select.assert_called_once_with(mock_slot)
    
    def test_migrated_equipment_ui_should_preserve_existing_public_api(self):
        """移行後のEquipmentUIは既存の公開APIを保持すべき"""
        # Given: 移行後のEquipmentUI
        from src.ui.equipment_ui import EquipmentUI
        equipment_ui = EquipmentUI()
        
        # Then: 既存の公開メソッドが保持されている
        assert hasattr(equipment_ui, 'set_party')
        assert hasattr(equipment_ui, 'show_party_equipment_menu')
        assert hasattr(equipment_ui, 'show_character_equipment')
        assert hasattr(equipment_ui, 'show_equipment_comparison')
        assert hasattr(equipment_ui, 'equip_item')
        assert hasattr(equipment_ui, 'unequip_item')
        assert hasattr(equipment_ui, 'close_equipment_ui')
    
    def test_migrated_equipment_ui_should_use_window_system_configuration(self):
        """移行後のEquipmentUIはWindowSystem設定を使用すべき"""
        # Given: 移行後のEquipmentUI
        from src.ui.equipment_ui import EquipmentUI
        equipment_ui = EquipmentUI()
        equipment_ui.current_character = self.mock_character
        
        # When: WindowSystem設定でEquipmentWindowを作成
        equipment_config = equipment_ui._create_equipment_window_config()
        
        # Then: WindowSystem形式の設定が作成される
        assert isinstance(equipment_config, dict)
        assert 'character' in equipment_config or 'equipment_slots' in equipment_config
    
    def test_migrated_equipment_ui_should_handle_equipment_validation(self):
        """移行後のEquipmentUIは装備バリデーションを適切に処理すべき"""
        # Given: 移行後のEquipmentUI with EquipmentWindow
        from src.ui.equipment_ui import EquipmentUI
        equipment_ui = EquipmentUI()
        equipment_ui.set_party(self.mock_party)
        
        # EquipmentWindowを表示
        equipment_ui.show_party_equipment_menu(self.mock_party)
        
        # モックアイテムとスロット
        mock_item = Mock()
        mock_item.item_id = "test_weapon"
        mock_slot = EquipmentSlot.WEAPON
        
        # When: アイテム装備を試行
        with patch.object(equipment_ui.equipment_window, 'validate_equipment', return_value=(True, "")) as mock_validate:
            result = equipment_ui.validate_equipment(mock_item, mock_slot)
        
        # Then: EquipmentWindowでバリデーションが実行される
        mock_validate.assert_called_once_with(mock_item, mock_slot)
        assert result == (True, "")
    
    def test_migrated_equipment_ui_should_cleanup_resources_properly(self):
        """移行後のEquipmentUIはリソースを適切にクリーンアップすべき"""
        # Given: 移行後のEquipmentUI with EquipmentWindow
        from src.ui.equipment_ui import EquipmentUI
        equipment_ui = EquipmentUI()
        equipment_ui.set_party(self.mock_party)
        
        # EquipmentWindowを表示
        equipment_ui.show_party_equipment_menu(self.mock_party)
        
        # When: クリーンアップを実行
        equipment_ui.cleanup()
        
        # Then: EquipmentWindowもクリーンアップされる
        assert equipment_ui.equipment_window is None or hasattr(equipment_ui.equipment_window, 'cleanup')