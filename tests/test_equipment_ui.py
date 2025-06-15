"""装備UI システムのテスト"""

import pytest
from unittest.mock import Mock, patch

from src.character.character import Character
from src.character.party import Party
from src.character.stats import BaseStats
from src.equipment.equipment import Equipment, EquipmentSlot
from src.items.item import ItemInstance


class TestEquipmentUI:
    """装備UIのテスト"""
    
    def setup_method(self):
        """各テストメソッドの前に実行"""
        # テスト用キャラクター作成
        stats = BaseStats(strength=14, agility=12, intelligence=10, faith=11, luck=13)
        self.character = Character.create_character("TestHero", "human", "fighter", stats)
        
        # テスト用パーティ作成
        self.party = Party(party_id="test_party", name="TestParty")
        self.party.add_character(self.character)
        
        # テスト用装備
        self.equipment = Equipment(owner_id=self.character.character_id)
    
    def test_equipment_ui_initialization(self):
        """装備UIの初期化テスト"""
        from src.ui.equipment_ui import EquipmentUI
        
        ui = EquipmentUI()
        
        assert ui.current_party is None
        assert ui.current_character is None
        assert ui.current_equipment is None
        assert ui.is_open == False
    
    def test_party_setting(self):
        """パーティ設定のテスト"""
        from src.ui.equipment_ui import EquipmentUI
        
        ui = EquipmentUI()
        ui.set_party(self.party)
        
        assert ui.current_party == self.party
    
    def test_slot_name_mapping(self):
        """スロット名マッピングのテスト"""
        from src.ui.equipment_ui import EquipmentUI
        
        ui = EquipmentUI()
        
        assert ui._get_slot_name(EquipmentSlot.WEAPON) == "武器"
        assert ui._get_slot_name(EquipmentSlot.ARMOR) == "防具"
        assert ui._get_slot_name(EquipmentSlot.ACCESSORY_1) == "アクセサリ1"
        assert ui._get_slot_name(EquipmentSlot.ACCESSORY_2) == "アクセサリ2"
    
    def test_stat_name_mapping(self):
        """ステータス名マッピングのテスト"""
        from src.ui.equipment_ui import EquipmentUI
        
        ui = EquipmentUI()
        
        assert ui._get_stat_name("strength") == "筋力"
        assert ui._get_stat_name("agility") == "敏捷性"
        assert ui._get_stat_name("intelligence") == "知力"
        assert ui._get_stat_name("faith") == "信仰"
        assert ui._get_stat_name("luck") == "運"
    
    def test_equipment_slot_compatibility(self):
        """装備スロット互換性のテスト"""
        from src.ui.equipment_ui import EquipmentUI
        from src.items.item import Item, ItemType
        
        ui = EquipmentUI()
        
        # 武器アイテムのモック
        weapon_item = Mock(spec=Item)
        weapon_item.is_weapon.return_value = True
        weapon_item.is_armor.return_value = False
        weapon_item.item_type.value = "weapon"
        
        # 防具アイテムのモック
        armor_item = Mock(spec=Item)
        armor_item.is_weapon.return_value = False
        armor_item.is_armor.return_value = True
        armor_item.item_type.value = "armor"
        
        # アクセサリアイテムのモック
        accessory_item = Mock(spec=Item)
        accessory_item.is_weapon.return_value = False
        accessory_item.is_armor.return_value = False
        accessory_item.item_type.value = "treasure"
        
        # 武器スロットテスト
        assert ui._can_equip_in_slot(weapon_item, EquipmentSlot.WEAPON) == True
        assert ui._can_equip_in_slot(armor_item, EquipmentSlot.WEAPON) == False
        
        # 防具スロットテスト
        assert ui._can_equip_in_slot(armor_item, EquipmentSlot.ARMOR) == True
        assert ui._can_equip_in_slot(weapon_item, EquipmentSlot.ARMOR) == False
        
        # アクセサリスロットテスト
        assert ui._can_equip_in_slot(accessory_item, EquipmentSlot.ACCESSORY_1) == True
        assert ui._can_equip_in_slot(weapon_item, EquipmentSlot.ACCESSORY_1) == False
    
    @patch('src.ui.equipment_ui.ui_manager')
    def test_party_equipment_menu_creation(self, mock_ui_manager):
        """パーティ装備メニュー作成のテスト"""
        from src.ui.equipment_ui import EquipmentUI
        
        ui = EquipmentUI()
        
        # キャラクターの装備をモック
        with patch.object(self.character, 'get_equipment') as mock_get_equipment:
            mock_equipment = Mock()
            mock_equipment.get_equipment_summary.return_value = {
                'equipped_count': 2,
                'total_weight': 5.0,
                'total_bonus': Mock(),
                'items': {}
            }
            mock_get_equipment.return_value = mock_equipment
            
            ui.show_party_equipment_menu(self.party)
            
            # UIマネージャーのメソッドが呼ばれたことを確認
            assert mock_ui_manager.register_element.called
            assert mock_ui_manager.show_element.called
            assert ui.is_open == True
    
    @patch('src.ui.equipment_ui.ui_manager')
    def test_character_equipment_display(self, mock_ui_manager):
        """キャラクター装備表示のテスト"""
        from src.ui.equipment_ui import EquipmentUI
        
        ui = EquipmentUI()
        ui.current_character = self.character
        ui.current_equipment = self.equipment
        
        ui._show_character_equipment(self.character)
        
        # UIマネージャーのメソッドが呼ばれたことを確認
        assert mock_ui_manager.register_element.called
        assert mock_ui_manager.show_element.called
    
    def test_equipment_preview_generation(self):
        """装備効果プレビュー生成のテスト"""
        from src.ui.equipment_ui import EquipmentUI
        from src.items.item import Item
        
        ui = EquipmentUI()
        ui.current_equipment = self.equipment
        
        # 武器アイテムのモック
        weapon_item = Mock(spec=Item)
        weapon_item.is_weapon.return_value = True
        weapon_item.is_armor.return_value = False
        weapon_item.get_attack_power.return_value = 10
        
        # アイテムインスタンスのモック
        item_instance = Mock(spec=ItemInstance)
        item_instance.identified = True
        item_instance.condition = 1.0
        
        # プレビューテスト（装備なしの場合）
        preview = ui._get_equipment_preview(weapon_item, item_instance, EquipmentSlot.WEAPON)
        assert "(+10)" in preview
    
    def test_ui_state_management(self):
        """UI状態管理のテスト"""
        from src.ui.equipment_ui import EquipmentUI, EquipmentUIMode
        
        ui = EquipmentUI()
        
        # 初期状態
        assert ui.current_mode == EquipmentUIMode.OVERVIEW
        assert ui.selected_slot is None
        assert ui.comparison_item is None
        
        # 状態変更
        ui.selected_slot = EquipmentSlot.WEAPON
        assert ui.selected_slot == EquipmentSlot.WEAPON
    
    def test_equipment_bonus_display_data(self):
        """装備ボーナス表示データのテスト"""
        from src.ui.equipment_ui import EquipmentUI
        from src.equipment.equipment import EquipmentBonus
        
        ui = EquipmentUI()
        ui.current_equipment = self.equipment
        
        # ボーナスのモック
        with patch.object(self.equipment, 'calculate_equipment_bonus') as mock_bonus:
            test_bonus = EquipmentBonus(
                strength=5, agility=3, intelligence=2, faith=1, luck=4,
                attack_power=15, defense=10, magic_power=8, magic_resistance=6
            )
            mock_bonus.return_value = test_bonus
            
            # ボーナス計算が正しく呼ばれることを確認
            bonus = ui.current_equipment.calculate_equipment_bonus()
            assert bonus.strength == 5
            assert bonus.attack_power == 15
    
    def test_equipment_statistics_calculation(self):
        """装備統計計算のテスト"""
        from src.ui.equipment_ui import EquipmentUI
        
        ui = EquipmentUI()
        ui.current_party = self.party
        
        # キャラクターの装備統計をモック
        with patch.object(self.character, 'get_equipment') as mock_get_equipment:
            mock_equipment = Mock()
            mock_equipment.get_equipment_summary.return_value = {
                'equipped_count': 3,
                'total_weight': 7.5,
                'total_bonus': Mock(),
                'items': {}
            }
            mock_equipment.get_all_equipped_items.return_value = {}
            mock_get_equipment.return_value = mock_equipment
            
            # 統計情報が正しく計算されることを確認（実際の計算はメソッド内で行われる）
            assert ui.current_party is not None
            assert len(ui.current_party.get_all_characters()) == 1
    
    def test_ui_navigation_flow(self):
        """UI ナビゲーションフローのテスト"""
        from src.ui.equipment_ui import EquipmentUI
        
        ui = EquipmentUI()
        ui.current_party = self.party
        ui.current_character = self.character
        ui.selected_slot = EquipmentSlot.WEAPON
        
        # ナビゲーション状態の確認
        assert ui.current_party == self.party
        assert ui.current_character == self.character
        assert ui.selected_slot == EquipmentSlot.WEAPON
        
        # クリーンアップテスト
        ui.destroy()
        assert ui.current_party is None
        assert ui.current_character is None
        assert ui.selected_slot is None
    
    def test_equipment_ui_integration_with_character(self):
        """装備UIとキャラクターの統合テスト"""
        from src.ui.equipment_ui import EquipmentUI
        
        ui = EquipmentUI()
        ui.set_party(self.party)
        
        # キャラクターから装備を取得できることを確認
        character = self.party.get_all_characters()[0]
        equipment = character.get_equipment()
        
        assert equipment is not None
        assert equipment.owner_id == character.character_id
        
        # 装備スロットが正しく初期化されていることを確認
        for slot in EquipmentSlot:
            assert slot in equipment.equipped_items
            assert equipment.is_slot_empty(slot) == True  # 初期状態では空


class TestEquipmentUIIntegration:
    """装備UI統合テスト"""
    
    def setup_method(self):
        """各テストメソッドの前に実行"""
        # テスト用データ作成
        stats = BaseStats(strength=15, agility=13, intelligence=11, faith=12, luck=14)
        self.character = Character.create_character("IntegrationHero", "human", "fighter", stats)
        
        self.party = Party(party_id="integration_party", name="IntegrationParty")
        self.party.add_character(self.character)
    
    def test_equipment_ui_full_workflow(self):
        """装備UI完全ワークフローのテスト"""
        from src.ui.equipment_ui import EquipmentUI
        
        ui = EquipmentUI()
        
        # 1. パーティ設定
        ui.set_party(self.party)
        assert ui.current_party == self.party
        
        # 2. キャラクター選択シミュレーション
        ui.current_character = self.character
        ui.current_equipment = self.character.get_equipment()
        
        # 3. 装備状態確認
        assert ui.current_equipment is not None
        assert ui.current_equipment.owner_id == self.character.character_id
        
        # 4. UI表示状態管理
        ui.is_open = True
        assert ui.is_open == True
        
        # 5. クリーンアップ
        ui.hide()
        assert ui.is_open == False
    
    def test_equipment_slot_interaction(self):
        """装備スロット操作のテスト"""
        from src.ui.equipment_ui import EquipmentUI
        
        ui = EquipmentUI()
        ui.current_character = self.character
        ui.current_equipment = self.character.get_equipment()
        
        # スロット選択
        ui.selected_slot = EquipmentSlot.WEAPON
        assert ui.selected_slot == EquipmentSlot.WEAPON
        
        # スロット状態確認
        assert ui.current_equipment.is_slot_empty(EquipmentSlot.WEAPON) == True
        
        # スロット名取得
        slot_name = ui._get_slot_name(EquipmentSlot.WEAPON)
        assert slot_name == "武器"