"""
EquipmentWindow のテスト

t-wada式TDDによるテストファースト開発
装備システムから新Window Systemへの移行
"""

import pytest
import pygame
import pygame_gui
from unittest.mock import Mock, patch, MagicMock
from src.ui.window_system import Window, WindowState
from src.ui.window_system.equipment_window import EquipmentWindow, EquipmentSlotType


class TestEquipmentWindow:
    """EquipmentWindow のテストクラス"""
    
    def setup_method(self):
        """各テストメソッドの前に実行される"""
        pygame.init()
        pygame.display.set_mode((1, 1), pygame.NOFRAME)
    
    def teardown_method(self):
        """各テストメソッドの後に実行される"""
        pygame.quit()
    
    def test_equipment_window_inherits_from_window(self):
        """EquipmentWindowがWindowクラスを継承することを確認"""
        # Given: 装備設定
        mock_character = Mock()
        mock_character.get_total_stats.return_value = {'attack': 45}
        
        mock_equipment_slots = Mock()
        mock_equipment_slots.get_all_slots.return_value = {}
        
        equipment_config = {
            'character': mock_character,
            'equipment_slots': mock_equipment_slots,
            'inventory': Mock()
        }
        
        # When: EquipmentWindowを作成
        equipment_window = EquipmentWindow('equipment', equipment_config)
        
        # Then: Windowクラスを継承している
        assert isinstance(equipment_window, Window)
        assert equipment_window.window_id == 'equipment'
        assert equipment_window.character is not None
    
    def test_equipment_validates_config_structure(self):
        """装備の設定構造が検証されることを確認"""
        # When: characterが無い設定でウィンドウを作成しようとする
        # Then: 例外が発生する
        with pytest.raises(ValueError, match="Equipment config must contain 'character'"):
            EquipmentWindow('invalid_equipment', {})
        
        # When: equipment_slotsが無い設定でウィンドウを作成しようとする
        # Then: 例外が発生する
        with pytest.raises(ValueError, match="Equipment config must contain 'equipment_slots'"):
            EquipmentWindow('invalid_equipment', {'character': Mock()})
    
    def test_equipment_displays_slot_layout(self):
        """装備スロットレイアウトが表示されることを確認"""
        # Given: 装備スロットを含む設定
        mock_character = Mock()
        mock_equipment_slots = Mock()
        mock_equipment_slots.get_all_slots.return_value = {
            'weapon': Mock(item=None, slot_type='weapon'),
            'armor': Mock(item=None, slot_type='armor'),
            'accessory': Mock(item=None, slot_type='accessory')
        }
        
        equipment_config = {
            'character': mock_character,
            'equipment_slots': mock_equipment_slots,
            'inventory': Mock()
        }
        
        equipment_window = EquipmentWindow('char_equipment', equipment_config)
        equipment_window.create()
        
        # Then: 装備スロットが作成される
        assert equipment_window.equipment_panel is not None
        assert len(equipment_window.slot_buttons) == 3
    
    def test_equipment_shows_item_details_on_selection(self):
        """装備選択時に詳細が表示されることを確認"""
        # Given: 装備されたアイテムを含む設定
        mock_weapon = Mock()
        mock_weapon.name = 'エクスカリバー'
        mock_weapon.description = '聖なる剣'
        mock_weapon.attack_power = 100
        mock_weapon.weight = 3.5
        mock_weapon.value = 5000
        
        mock_weapon_slot = Mock()
        mock_weapon_slot.item = mock_weapon
        mock_weapon_slot.slot_type = 'weapon'
        mock_weapon_slot.is_equipped = True
        
        mock_equipment_slots = Mock()
        mock_equipment_slots.get_all_slots.return_value = {
            'weapon': mock_weapon_slot
        }
        mock_equipment_slots.get_slot.return_value = mock_weapon_slot
        
        mock_character = Mock()
        mock_character.get_total_stats.return_value = {'attack': 45}
        
        equipment_config = {
            'character': mock_character,
            'equipment_slots': mock_equipment_slots,
            'inventory': Mock()
        }
        
        equipment_window = EquipmentWindow('detail_equipment', equipment_config)
        equipment_window.create()
        
        # When: 武器スロットを選択
        result = equipment_window.select_equipment_slot('weapon')
        
        # Then: 詳細パネルが更新される
        assert result is True
        assert equipment_window.selected_slot == 'weapon'
        assert equipment_window.detail_panel is not None
    
    def test_equipment_supports_equip_unequip_actions(self):
        """装備・装備解除アクションが動作することを確認"""
        # Given: 装備可能なアイテムを持つキャラクター
        mock_sword = Mock()
        mock_sword.item_id = 'iron_sword'
        mock_sword.name = 'アイアンソード'
        mock_sword.is_equippable.return_value = True
        mock_sword.equipment_slot = 'weapon'
        mock_sword.weight = 2.0
        mock_sword.value = 150
        
        mock_inventory = Mock()
        mock_inventory.get_items_by_category.return_value = [mock_sword]
        
        mock_equipment_slots = Mock()
        mock_equipment_slots.get_all_slots.return_value = {}
        mock_equipment_slots.get_slot.return_value = Mock(item=None)
        mock_equipment_slots.can_equip.return_value = True
        
        mock_character = Mock()
        mock_character.get_total_stats.return_value = {'attack': 50}
        
        equipment_config = {
            'character': mock_character,
            'equipment_slots': mock_equipment_slots,
            'inventory': mock_inventory
        }
        
        equipment_window = EquipmentWindow('action_equipment', equipment_config)
        equipment_window.create()
        equipment_window.selected_slot = 'weapon'
        equipment_window.selected_item = mock_sword
        
        # When: アイテムを装備
        with patch.object(equipment_window, 'send_message') as mock_send:
            result = equipment_window.equip_selected_item()
        
        # Then: 装備メッセージが送信される
        assert result is True
        mock_send.assert_called_once_with('item_equipped', {
            'item_id': 'iron_sword',
            'slot_type': 'weapon',
            'character_id': equipment_window.character
        })
    
    def test_equipment_displays_character_stats(self):
        """キャラクター統計が表示されることを確認"""
        # Given: ステータスを持つキャラクター
        mock_character = Mock()
        mock_character.get_total_stats.return_value = {
            'attack': 45,
            'defense': 30,
            'agility': 25,
            'magic_power': 15
        }
        mock_character.name = 'テストヒーロー'
        mock_character.level = 5
        
        mock_equipment_slots = Mock()
        mock_equipment_slots.get_all_slots.return_value = {}
        
        equipment_config = {
            'character': mock_character,
            'equipment_slots': mock_equipment_slots,
            'inventory': Mock()
        }
        
        equipment_window = EquipmentWindow('stats_equipment', equipment_config)
        equipment_window.create()
        
        # Then: ステータスパネルが表示される
        assert equipment_window.stats_panel is not None
        assert equipment_window.character_stats is not None
    
    def test_equipment_handles_slot_changes(self):
        """装備スロット変更が処理されることを確認"""
        # Given: 装備変更可能な設定
        mock_equipment_slots = Mock()
        mock_equipment_slots.get_all_slots.return_value = {
            'weapon': Mock(item=None),
            'armor': Mock(item=None)
        }
        
        equipment_config = {
            'character': Mock(),
            'equipment_slots': mock_equipment_slots,
            'inventory': Mock()
        }
        
        equipment_window = EquipmentWindow('change_equipment', equipment_config)
        equipment_window.create()
        
        # When: 装備スロットを変更
        result = equipment_window.change_equipment_slot('weapon', 'armor')
        
        # Then: 変更が処理される
        assert result is True
        mock_equipment_slots.swap_equipment.assert_called_once_with('weapon', 'armor')
    
    def test_equipment_supports_comparison_mode(self):
        """装備比較モードが動作することを確認"""
        # Given: 比較可能な装備
        current_weapon = Mock()
        current_weapon.name = '現在の剣'
        current_weapon.attack_power = 50
        
        new_weapon = Mock()
        new_weapon.name = '新しい剣'
        new_weapon.attack_power = 70
        new_weapon.weight = 2.5
        new_weapon.value = 300
        
        mock_equipment_slots = Mock()
        mock_equipment_slots.get_slot.return_value = Mock(item=current_weapon)
        
        equipment_config = {
            'character': Mock(),
            'equipment_slots': mock_equipment_slots,
            'inventory': Mock(),
            'enable_comparison': True
        }
        
        equipment_window = EquipmentWindow('comparison_equipment', equipment_config)
        equipment_window.create()
        
        # When: 比較モードを開始
        result = equipment_window.start_comparison_mode('weapon', new_weapon)
        
        # Then: 比較が開始される
        assert result is True
        assert equipment_window.comparison_mode is True
        assert equipment_window.comparison_item == new_weapon
    
    def test_equipment_filters_by_slot_type(self):
        """スロットタイプによるフィルタリングが動作することを確認"""
        # Given: 複数タイプのアイテムを持つインベントリ
        mock_sword = Mock(equipment_slot='weapon', name='剣')
        mock_armor = Mock(equipment_slot='armor', name='鎧')
        mock_ring = Mock(equipment_slot='accessory', name='指輪')
        
        mock_inventory = Mock()
        mock_inventory.get_items_by_category.return_value = [mock_sword, mock_armor, mock_ring]
        
        equipment_config = {
            'character': Mock(),
            'equipment_slots': Mock(),
            'inventory': mock_inventory
        }
        
        equipment_window = EquipmentWindow('filter_equipment', equipment_config)
        equipment_window.create()
        
        # When: 武器でフィルタリング
        result = equipment_window.filter_by_slot_type('weapon')
        
        # Then: 武器のみが表示される
        assert result is True
        assert equipment_window.current_filter == 'weapon'
        filtered_items = equipment_window.get_filtered_items()
        assert len([item for item in filtered_items if item.equipment_slot == 'weapon']) > 0
    
    def test_equipment_handles_keyboard_navigation(self):
        """キーボードナビゲーションが動作することを確認"""
        # Given: 複数スロットのある装備ウィンドウ
        mock_equipment_slots = Mock()
        mock_equipment_slots.get_all_slots.return_value = {
            'weapon': Mock(item=None),
            'armor': Mock(item=None),
            'accessory': Mock(item=None)
        }
        
        equipment_config = {
            'character': Mock(),
            'equipment_slots': mock_equipment_slots,
            'inventory': Mock()
        }
        
        equipment_window = EquipmentWindow('nav_equipment', equipment_config)
        equipment_window.create()
        equipment_window.selected_slot = 'weapon'  # 初期選択
        
        # When: TABキーで次のスロットに移動
        tab_event = Mock()
        tab_event.type = pygame.KEYDOWN
        tab_event.key = pygame.K_TAB
        tab_event.mod = 0
        
        result = equipment_window.handle_event(tab_event)
        
        # Then: 選択が次のスロットに移動する
        assert result is True
        assert equipment_window.selected_slot == 'armor'
    
    def test_equipment_supports_quick_equip(self):
        """クイック装備機能が動作することを確認"""
        # Given: クイック装備可能な設定
        mock_item = Mock()
        mock_item.item_id = 'quick_sword'
        mock_item.equipment_slot = 'weapon'
        mock_item.weight = 1.5
        mock_item.value = 200
        
        mock_equipment_slots = Mock()
        mock_equipment_slots.can_equip.return_value = True
        
        equipment_config = {
            'character': Mock(),
            'equipment_slots': mock_equipment_slots,
            'inventory': Mock(),
            'enable_quick_equip': True
        }
        
        equipment_window = EquipmentWindow('quick_equipment', equipment_config)
        equipment_window.create()
        
        # When: アイテムをダブルクリック（クイック装備）
        with patch.object(equipment_window, 'send_message') as mock_send:
            result = equipment_window.quick_equip_item(mock_item)
        
        # Then: クイック装備が実行される
        assert result is True
        mock_send.assert_called_once()
    
    def test_equipment_escape_key_closes(self):
        """ESCキーで装備ウィンドウが閉じることを確認"""
        # Given: 装備ウィンドウ
        mock_character = Mock()
        mock_character.get_total_stats.return_value = {'attack': 45}
        
        mock_equipment_slots = Mock()
        mock_equipment_slots.get_all_slots.return_value = {}
        
        equipment_config = {
            'character': mock_character,
            'equipment_slots': mock_equipment_slots,
            'inventory': Mock()
        }
        
        equipment_window = EquipmentWindow('esc_equipment', equipment_config)
        equipment_window.create()
        
        # When: ESCキーを押す
        with patch.object(equipment_window, 'send_message') as mock_send:
            result = equipment_window.handle_escape()
        
        # Then: 閉じるメッセージが送信される
        assert result is True
        mock_send.assert_called_once_with('equipment_close_requested', {
            'character_id': equipment_window.character
        })
    
    def test_equipment_validates_equip_requirements(self):
        """装備要件の検証が動作することを確認"""
        # Given: レベル制限のあるアイテム
        mock_high_level_sword = Mock()
        mock_high_level_sword.required_level = 10
        mock_high_level_sword.equipment_slot = 'weapon'
        mock_high_level_sword.weight = 4.0
        mock_high_level_sword.value = 1000
        
        mock_character = Mock()
        mock_character.level = 5  # レベル不足
        
        equipment_config = {
            'character': mock_character,
            'equipment_slots': Mock(),
            'inventory': Mock()
        }
        
        equipment_window = EquipmentWindow('validation_equipment', equipment_config)
        equipment_window.create()
        
        # When: レベル不足のアイテムを装備しようとする
        result = equipment_window.can_equip_item(mock_high_level_sword)
        
        # Then: 装備できない
        assert result is False
    
    def test_equipment_cleanup_removes_ui_elements(self):
        """クリーンアップでUI要素が適切に削除されることを確認"""
        # Given: 作成された装備ウィンドウ
        mock_character = Mock()
        mock_character.get_total_stats.return_value = {'attack': 45}
        
        mock_equipment_slots = Mock()
        mock_equipment_slots.get_all_slots.return_value = {}
        
        equipment_config = {
            'character': mock_character,
            'equipment_slots': mock_equipment_slots,
            'inventory': Mock()
        }
        
        equipment_window = EquipmentWindow('cleanup_equipment', equipment_config)
        equipment_window.create()
        
        # When: クリーンアップを実行
        equipment_window.cleanup_ui()
        
        # Then: UI要素が削除される
        assert equipment_window.slot_buttons == []
        assert equipment_window.equipment_panel is None
        assert equipment_window.detail_panel is None
        assert equipment_window.ui_manager is None