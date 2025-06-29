"""EquipmentWindowのテスト"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import pygame
import pygame_gui

from src.ui.windows.equipment_window import EquipmentWindow
from src.ui.window_system.window_manager import WindowManager
from src.character.character import Character
from src.character.party import Party
from src.equipment.equipment import Equipment, EquipmentSlot
from src.items.item import ItemInstance


class TestEquipmentWindow:
    """EquipmentWindowのテストクラス"""

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
    def mock_character(self):
        """キャラクターのモックを作成"""
        char = Mock()
        char.name = "テスト戦士"
        char.character_class = Mock()
        char.character_class.value = "warrior"
        
        # 装備モック
        equipment = Mock()
        equipment.get_equipped_item.return_value = None
        equipment.get_equipment_summary.return_value = {'equipped_count': 2, 'total_weight': 5.0}
        equipment.calculate_equipment_bonus.return_value = Mock(
            strength=5, agility=2, intelligence=0, faith=0, luck=1,
            attack_power=10, defense=8, magic_power=0, magic_resistance=0
        )
        equipment.get_total_weight.return_value = 5.0
        equipment.get_all_equipped_items.return_value = {}
        equipment.can_equip_item.return_value = (True, "OK")
        equipment.equip_item.return_value = (True, "装備成功", None)
        equipment.unequip_item.return_value = Mock()
        
        char.get_equipment.return_value = equipment
        
        # インベントリモック
        inventory = Mock()
        inventory.slots = [Mock() for _ in range(20)]
        for slot in inventory.slots:
            slot.is_empty.return_value = True
            slot.item_instance = None
        inventory.remove_item.return_value = True
        inventory.add_item.return_value = True
        char.get_inventory.return_value = inventory
        
        # ステータスモック
        base_stats = Mock()
        base_stats.strength = 10
        base_stats.agility = 8
        base_stats.intelligence = 6
        base_stats.faith = 5
        base_stats.luck = 7
        
        derived_stats = Mock()
        derived_stats.strength = 15
        derived_stats.agility = 10
        derived_stats.intelligence = 6
        derived_stats.faith = 5
        derived_stats.luck = 8
        derived_stats.attack_power = 20
        derived_stats.defense = 15
        derived_stats.magic_power = 6
        derived_stats.magic_resistance = 5
        
        char.get_base_stats.return_value = base_stats
        char.get_derived_stats.return_value = derived_stats
        char.update_derived_stats.return_value = None
        
        return char

    @pytest.fixture 
    def mock_party(self, mock_character):
        """パーティのモックを作成"""
        party = Mock(spec=Party)
        party.name = "テストパーティ"
        party.get_all_characters.return_value = [mock_character]
        return party

    def test_equipment_window_creation(self, mock_window_manager):
        """EquipmentWindowが正しく作成されることを確認"""
        window = EquipmentWindow("test_equipment")
        
        assert window.window_id == "test_equipment"
        assert window.current_party is None
        assert window.current_character is None
        assert window.current_equipment is None

    def test_set_party(self, mock_window_manager, mock_party):
        """パーティの設定が正しく動作することを確認"""
        window = EquipmentWindow("test_equipment")
        window.set_party(mock_party)
        
        assert window.current_party == mock_party

    def test_show_party_equipment_overview(self, mock_window_manager, mock_party, mock_character):
        """パーティ装備概要の表示が正しく動作することを確認"""
        window = EquipmentWindow("test_equipment")
        window.set_party(mock_party)
        
        # createメソッドをモック
        window.create_party_overview = Mock()
        
        window.show_party_equipment_overview()
        
        window.create_party_overview.assert_called_once()

    def test_show_character_equipment(self, mock_window_manager, mock_character):
        """キャラクター装備画面の表示が正しく動作することを確認"""
        window = EquipmentWindow("test_equipment")
        
        # createメソッドをモック
        window.create_character_equipment = Mock()
        
        window.show_character_equipment(mock_character)
        
        assert window.current_character == mock_character
        assert window.current_equipment == mock_character.get_equipment()
        window.create_character_equipment.assert_called_once()

    def test_show_slot_options(self, mock_window_manager, mock_character):
        """スロットオプション表示が正しく動作することを確認"""
        window = EquipmentWindow("test_equipment")
        window.current_character = mock_character
        window.current_equipment = mock_character.get_equipment()
        
        # createメソッドをモック
        window.create_slot_options = Mock()
        
        window.show_slot_options(EquipmentSlot.WEAPON)
        
        assert window.selected_slot == EquipmentSlot.WEAPON
        window.create_slot_options.assert_called_once()

    def test_show_equipment_selection(self, mock_window_manager, mock_character):
        """装備選択画面の表示が正しく動作することを確認"""
        window = EquipmentWindow("test_equipment")
        window.current_character = mock_character
        window.current_equipment = mock_character.get_equipment()
        
        # createメソッドをモック
        window.create_equipment_selection = Mock()
        
        window.show_equipment_selection(EquipmentSlot.WEAPON)
        
        window.create_equipment_selection.assert_called_once_with(EquipmentSlot.WEAPON)

    def test_equip_item_success(self, mock_window_manager, mock_character):
        """アイテム装備の成功ケースをテスト"""
        window = EquipmentWindow("test_equipment")
        window.current_character = mock_character
        window.current_equipment = mock_character.get_equipment()
        
        # 装備成功をモック
        item_instance = Mock(spec=ItemInstance)
        window.current_equipment.equip_item.return_value = (True, "装備成功", None)
        
        # インベントリモック
        inventory = window.current_character.get_inventory()
        inventory.remove_item.return_value = True
        
        # メッセージ表示をモック
        window.show_message = Mock()
        window.refresh_view = Mock()
        
        window.equip_item_from_inventory(item_instance, EquipmentSlot.WEAPON, 0)
        
        window.current_equipment.equip_item.assert_called_once()
        inventory.remove_item.assert_called_once_with(0, 1)
        window.show_message.assert_called_once()
        window.refresh_view.assert_called_once()

    def test_unequip_item_success(self, mock_window_manager, mock_character):
        """アイテム装備解除の成功ケースをテスト"""
        window = EquipmentWindow("test_equipment")
        window.current_character = mock_character
        window.current_equipment = mock_character.get_equipment()
        
        # 装備解除成功をモック
        item_instance = Mock(spec=ItemInstance)
        window.current_equipment.unequip_item.return_value = item_instance
        
        # インベントリモック
        inventory = window.current_character.get_inventory()
        inventory.add_item.return_value = True
        
        # メッセージ表示をモック
        window.show_message = Mock()
        window.refresh_view = Mock()
        
        window.unequip_item(EquipmentSlot.WEAPON)
        
        window.current_equipment.unequip_item.assert_called_once_with(EquipmentSlot.WEAPON)
        inventory.add_item.assert_called_once_with(item_instance)
        window.show_message.assert_called_once()
        window.refresh_view.assert_called_once()

    def test_show_equipment_bonus(self, mock_window_manager, mock_character):
        """装備ボーナス表示が正しく動作することを確認"""
        window = EquipmentWindow("test_equipment")
        window.current_equipment = mock_character.get_equipment()
        
        # ダイアログ表示をモック
        window.show_dialog = Mock()
        
        window.show_equipment_bonus()
        
        window.show_dialog.assert_called_once()

    def test_show_equipment_effects(self, mock_window_manager, mock_character):
        """装備効果確認が正しく動作することを確認"""
        window = EquipmentWindow("test_equipment")
        window.current_character = mock_character
        window.current_equipment = mock_character.get_equipment()
        
        # ダイアログ表示をモック
        window.show_dialog = Mock()
        
        window.show_equipment_effects()
        
        window.show_dialog.assert_called_once()

    def test_show_party_equipment_stats(self, mock_window_manager, mock_party):
        """パーティ装備統計表示が正しく動作することを確認"""
        window = EquipmentWindow("test_equipment")
        window.current_party = mock_party
        
        # ダイアログ表示をモック
        window.show_dialog = Mock()
        
        window.show_party_equipment_stats()
        
        window.show_dialog.assert_called_once()

    def test_window_lifecycle(self, mock_window_manager):
        """ウィンドウのライフサイクルが正しく動作することを確認"""
        window = EquipmentWindow("test_equipment")
        
        # 作成状態の確認
        assert window.window_id == "test_equipment"
        
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
        assert window.current_equipment is None