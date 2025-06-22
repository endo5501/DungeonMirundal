"""宿屋の冒険準備メニューテスト"""

import pytest
from unittest.mock import Mock, patch, MagicMock

from tests.test_utils import setup_panda3d_mocks
setup_panda3d_mocks()

from src.overworld.facilities.inn import Inn
from src.character.party import Party
from src.character.character import Character
from src.character.stats import BaseStats, DerivedStats
from src.inventory.inventory import Inventory, InventorySlot, InventoryManager
from src.equipment.equipment import Equipment
from src.items.item import ItemInstance, item_manager


class TestInnAdventurePreparation:
    """宿屋の冒険準備メニューテスト"""
    
    def setup_method(self):
        """テストセットアップ"""
        self.inn = Inn()
        
        # テスト用パーティの作成
        self.party = Party("TestParty")
        
        # テスト用キャラクターの作成
        self.mage = Character(
            name="TestMage",
            race="human",
            character_class="mage",
            base_stats=BaseStats(10, 8, 15, 6, 12, 14)
        )
        self.mage.derived_stats = DerivedStats(50, 40, 25, 15)
        self.mage.experience.level = 5
        
        self.priest = Character(
            name="TestPriest", 
            race="elf",
            character_class="priest",
            base_stats=BaseStats(8, 10, 12, 18, 11, 9)
        )
        self.priest.derived_stats = DerivedStats(40, 50, 20, 18)
        self.priest.experience.level = 4
        
        self.fighter = Character(
            name="TestFighter",
            race="dwarf", 
            character_class="fighter",
            base_stats=BaseStats(18, 12, 8, 10, 13, 11)
        )
        self.fighter.derived_stats = DerivedStats(80, 20, 30, 22)
        self.fighter.experience.level = 6
        
        # パーティにキャラクターを追加
        self.party.add_character(self.mage)
        self.party.add_character(self.priest)
        self.party.add_character(self.fighter)
        
        # 宿屋にパーティを設定
        self.inn.enter(self.party)
    
    def test_adventure_preparation_menu_creation(self):
        """冒険準備メニューの作成テスト"""
        # 冒険準備メニューの表示をテスト
        with patch.object(self.inn, '_show_submenu') as mock_show_submenu:
            self.inn._show_adventure_preparation()
            
            # サブメニューが表示されることを確認
            mock_show_submenu.assert_called_once()
            
            # 渡されたメニューの内容を確認
            menu = mock_show_submenu.call_args[0][0]
            assert menu.element_id == "adventure_prep_menu"
            assert menu.title == "冒険の準備"
    
    def test_adventure_preparation_no_party(self):
        """パーティなしでの冒険準備メニューテスト"""
        # パーティを削除
        self.inn.current_party = None
        
        with patch.object(self.inn, '_show_error_message') as mock_error:
            self.inn._show_adventure_preparation()
            
            # エラーメッセージが表示されることを確認
            mock_error.assert_called_once_with("パーティが設定されていません")
    
    @patch('src.overworld.facilities.inn.InventoryManager')
    def test_item_organization_with_inventory(self, mock_inventory_manager):
        """インベントリありでのアイテム整理テスト"""
        # モックインベントリの設定
        mock_inventory = Mock()
        mock_slot1 = Mock()
        mock_slot1.is_empty.return_value = False
        mock_slot1.item_instance = Mock()
        mock_slot1.item_instance.item_id = "healing_potion"
        mock_slot1.item_instance.quantity = 3
        
        mock_slot2 = Mock()
        mock_slot2.is_empty.return_value = True
        
        mock_inventory.slots = [mock_slot1, mock_slot2]
        
        # パーティインベントリのモック
        self.party.get_party_inventory = Mock(return_value=mock_inventory)
        
        # アイテムマネージャーのモック
        mock_item = Mock()
        mock_item.get_name.return_value = "ヒーリングポーション"
        
        with patch('src.overworld.facilities.inn.item_manager') as mock_item_manager:
            mock_item_manager.get_item.return_value = mock_item
            
            with patch.object(self.inn, '_show_dialog') as mock_dialog:
                self.inn._show_item_organization()
                
                # ダイアログが表示されることを確認
                mock_dialog.assert_called_once()
                
                # ダイアログの内容を確認（移行ダイアログが表示される）
                dialog_args = mock_dialog.call_args[0]
                assert dialog_args[0] == "migration_info_dialog"
                assert dialog_args[1] == "アイテム移行完了"
                assert "宿屋倉庫に" in dialog_args[2]
    
    def test_item_organization_no_inventory(self):
        """インベントリなしでのアイテム整理テスト"""
        # パーティインベントリが存在しない場合
        self.party.get_party_inventory = Mock(return_value=None)
        
        with patch.object(self.inn, '_show_error_message') as mock_error:
            self.inn._show_item_organization()
            
            # エラーメッセージが表示されることを確認
            mock_error.assert_called_once_with("パーティインベントリが見つかりません")
    
    def test_spell_slot_management_with_spell_users(self):
        """魔法使いありでの魔術スロット管理テスト"""
        # 魔法使いキャラクターに魔法スロットを追加
        self.mage.spell_slots = [None, None, None]
        
        with patch.object(self.inn, '_show_spell_user_selection') as mock_selection:
            self.inn._show_spell_slot_management()
            
            # 魔法使いキャラクター選択が表示されることを確認
            mock_selection.assert_called_once()
            
            # 魔法使いキャラクターのリストを確認
            spell_users = mock_selection.call_args[0][0]
            assert len(spell_users) >= 2  # mage, priest
            assert self.mage in spell_users
            assert self.priest in spell_users
    
    def test_spell_slot_management_no_spell_users(self):
        """魔法使いなしでの魔術スロット管理テスト"""
        # すべてのキャラクターを戦士クラスに変更
        for character in self.party.get_all_characters():
            character.character_class = "fighter"
        
        with patch.object(self.inn, '_show_dialog') as mock_dialog:
            self.inn._show_spell_slot_management()
            
            # 魔法使いなしのダイアログが表示されることを確認
            mock_dialog.assert_called_once()
            dialog_args = mock_dialog.call_args[0]
            assert dialog_args[0] == "no_spell_users_dialog"
            assert "パーティに魔法を使用できる" in dialog_args[2]
    
    def test_prayer_slot_management_with_prayer_users(self):
        """祈祷使いありでの祈祷スロット管理テスト"""
        with patch.object(self.inn, '_show_prayer_user_selection') as mock_selection:
            self.inn._show_prayer_slot_management()
            
            # 祈祷使いキャラクター選択が表示されることを確認
            mock_selection.assert_called_once()
            
            # 祈祷使いキャラクターのリストを確認
            prayer_users = mock_selection.call_args[0][0]
            assert len(prayer_users) >= 1  # priest
            assert self.priest in prayer_users
    
    def test_prayer_slot_management_no_prayer_users(self):
        """祈祷使いなしでの祈祷スロット管理テスト"""
        # 僧侶を戦士クラスに変更
        self.priest.character_class = "fighter"
        
        with patch.object(self.inn, '_show_dialog') as mock_dialog:
            self.inn._show_prayer_slot_management()
            
            # 祈祷使いなしのダイアログが表示されることを確認
            mock_dialog.assert_called_once()
            dialog_args = mock_dialog.call_args[0]
            assert dialog_args[0] == "no_prayer_users_dialog"
            assert "パーティに祈祷を使用できる" in dialog_args[2]
    
    def test_party_equipment_status_with_equipment(self):
        """装備ありでのパーティ装備状況テスト"""
        # キャラクターに装備を追加
        mock_equipment = Mock()
        mock_equipment.slots = {
            'weapon': Mock(),
            'armor': None,
            'accessory_1': None,
            'accessory_2': None
        }
        
        # 装備ボーナスのモック
        mock_bonus = Mock()
        mock_bonus.strength = 5
        mock_bonus.agility = 0
        mock_bonus.intelligence = 0
        mock_bonus.faith = 0
        mock_bonus.luck = 0
        mock_bonus.attack_power = 10
        mock_bonus.defense_power = 0
        mock_equipment.get_total_bonus.return_value = mock_bonus
        
        self.fighter.equipment = mock_equipment
        
        # アイテムマネージャーのモック
        mock_weapon = Mock()
        mock_weapon.get_name.return_value = "ロングソード"
        
        with patch('src.overworld.facilities.inn.item_manager') as mock_item_manager:
            mock_item_manager.get_item.return_value = mock_weapon
            
            with patch.object(self.inn, '_show_dialog') as mock_dialog:
                self.inn._show_party_equipment_status()
                
                # ダイアログが表示されることを確認
                mock_dialog.assert_called_once()
                
                # ダイアログの内容を確認
                dialog_args = mock_dialog.call_args[0]
                assert dialog_args[0] == "equipment_status_dialog"
                assert dialog_args[1] == "パーティ装備状況"
                assert "TestFighter" in dialog_args[2]
                assert "ロングソード" in dialog_args[2]
                assert "力+5" in dialog_args[2]
                assert "攻+10" in dialog_args[2]
    
    def test_party_equipment_status_no_equipment(self):
        """装備なしでのパーティ装備状況テスト"""
        with patch.object(self.inn, '_show_dialog') as mock_dialog:
            self.inn._show_party_equipment_status()
            
            # ダイアログが表示されることを確認
            mock_dialog.assert_called_once()
            
            # ダイアログの内容を確認
            dialog_args = mock_dialog.call_args[0]
            assert dialog_args[0] == "equipment_status_dialog"
            assert dialog_args[1] == "パーティ装備状況"
            assert "詳細な装備管理は装備画面で行えます" in dialog_args[2]
    
    def test_get_spell_slot_info(self):
        """魔法スロット情報取得テスト"""
        # 魔法スロットありのキャラクター
        self.mage.spell_slots = [None, "fireball", None]
        result = self.inn._get_spell_slot_info(self.mage)
        assert result == "装備中: 1/3スロット"
        
        # 魔法スロットなしのキャラクター
        result = self.inn._get_spell_slot_info(self.fighter)
        assert result == "魔法スロット: 未実装"
    
    def test_get_prayer_slot_info(self):
        """祈祷スロット情報取得テスト"""
        # 祈祷スロットありのキャラクター（魔法スロット共用）
        self.priest.spell_slots = ["heal", None, "cure"]
        result = self.inn._get_prayer_slot_info(self.priest)
        assert result == "装備中: 2/3スロット"
        
        # 祈祷スロットなしのキャラクター
        result = self.inn._get_prayer_slot_info(self.fighter)
        assert result == "祈祷スロット: 未実装"
    
    def test_get_equipment_name(self):
        """装備名取得テスト"""
        # 装備ありの場合
        mock_equipment = Mock()
        mock_item_instance = Mock()
        mock_item_instance.item_id = "long_sword"
        mock_equipment.slots = {'weapon': mock_item_instance}
        
        mock_item = Mock()
        mock_item.get_name.return_value = "ロングソード"
        
        with patch('src.overworld.facilities.inn.item_manager') as mock_item_manager:
            mock_item_manager.get_item.return_value = mock_item
            
            result = self.inn._get_equipment_name(mock_equipment, 'weapon')
            assert result == "ロングソード"
        
        # 装備なしの場合
        mock_equipment.slots = {'weapon': None}
        result = self.inn._get_equipment_name(mock_equipment, 'weapon')
        assert result == "未装備"
    
    def test_character_spell_management_display(self):
        """キャラクター魔法管理表示テスト"""
        # 魔法データをモック
        self.mage.learned_spells = ["fireball", "ice_shard"]
        self.mage.spell_slots = ["fireball", None, None]
        
        with patch.object(self.inn, '_show_dialog') as mock_dialog:
            self.inn._show_character_spell_management(self.mage)
            
            # ダイアログが表示されることを確認
            mock_dialog.assert_called_once()
            
            # ダイアログの内容を確認
            dialog_args = mock_dialog.call_args[0]
            assert dialog_args[0] == "character_spell_dialog"
            assert "TestMage の魔法管理" in dialog_args[1]
            assert "職業: mage" in dialog_args[2]
            assert "レベル: 5" in dialog_args[2]
            assert "fireball" in dialog_args[2]
            assert "ice_shard" in dialog_args[2]
    
    def test_character_prayer_management_display(self):
        """キャラクター祈祷管理表示テスト"""
        # 祈祷データをモック
        self.priest.learned_spells = ["heal", "cure", "fireball"]  # 祈祷と魔法混合
        self.priest.spell_slots = ["heal", None]
        
        with patch.object(self.inn, '_show_dialog') as mock_dialog:
            self.inn._show_character_prayer_management(self.priest)
            
            # ダイアログが表示されることを確認
            mock_dialog.assert_called_once()
            
            # ダイアログの内容を確認
            dialog_args = mock_dialog.call_args[0]
            assert dialog_args[0] == "character_prayer_dialog"
            assert "TestPriest の祈祷管理" in dialog_args[1]
            assert "職業: priest" in dialog_args[2]
            assert "レベル: 4" in dialog_args[2]
            assert "heal" in dialog_args[2]
            assert "cure" in dialog_args[2]
            # fireballは祈祷として表示されない


class TestInnAdventurePreparationIntegration:
    """宿屋冒険準備メニュー統合テスト"""
    
    def setup_method(self):
        """統合テストセットアップ"""
        self.inn = Inn()
        self.party = Party("IntegrationTestParty")
        
        # 統合テスト用キャラクター
        self.character = Character(
            name="IntegrationTest",
            race="human",
            character_class="mage",
            base_stats=BaseStats(10, 10, 15, 10, 10, 10)
        )
        self.character.derived_stats = DerivedStats(40, 30, 20, 15)
        self.character.experience.level = 3
        
        self.party.add_character(self.character)
        self.inn.enter(self.party)
    
    def test_error_handling_in_item_organization(self):
        """アイテム整理のエラーハンドリングテスト"""
        # インベントリマネージャーで例外を発生させる
        with patch('src.overworld.facilities.inn.InventoryManager', side_effect=Exception("Test error")):
            with patch.object(self.inn, '_show_error_message') as mock_error:
                self.inn._show_item_organization()
                
                # エラーハンドリングが機能することを確認
                mock_error.assert_called_once()
                assert "Test error" in mock_error.call_args[0][0]
    
    def test_error_handling_in_spell_management(self):
        """魔術スロット管理のエラーハンドリングテスト"""
        # get_all_charactersで例外を発生させる
        with patch.object(self.party, 'get_all_characters', side_effect=Exception("Spell error")):
            with patch.object(self.inn, '_show_error_message') as mock_error:
                self.inn._show_spell_slot_management()
                
                # エラーハンドリングが機能することを確認
                mock_error.assert_called_once()
                assert "Spell error" in mock_error.call_args[0][0]
    
    def test_error_handling_in_equipment_status(self):
        """装備状況確認のエラーハンドリングテスト"""
        # get_all_charactersで例外を発生させる
        with patch.object(self.party, 'get_all_characters', side_effect=Exception("Equipment error")):
            with patch.object(self.inn, '_show_error_message') as mock_error:
                self.inn._show_party_equipment_status()
                
                # エラーハンドリングが機能することを確認
                mock_error.assert_called_once()
                assert "Equipment error" in mock_error.call_args[0][0]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])