"""キャラクター詳細表示クラッシュ修正テスト"""

import unittest
from unittest.mock import Mock, patch

from src.character.character import Character
from src.character.stats import BaseStats, DerivedStats
from src.overworld.overworld_manager import OverworldManager


class TestCharacterDetailsCrashFix(unittest.TestCase):
    """キャラクター詳細表示クラッシュ修正テストクラス"""
    
    def setUp(self):
        """テスト前のセットアップ"""
        # テスト用キャラクターを作成
        self.character = Character("テストキャラクター", "human", "fighter")
        
        # 基本ステータスの設定
        self.character.base_stats = BaseStats(
            strength=15, 
            intelligence=10, 
            faith=10,
            vitality=14,  # 追加予定の属性
            agility=12, 
            luck=10
        )
        
        # 導出ステータスの設定
        self.character.derived_stats = DerivedStats(
            max_hp=50,
            current_hp=50,
            max_mp=10,
            current_mp=10,
            attack_power=18,    # 追加予定の属性
            defense=12,         # 追加予定の属性
            accuracy=85,        # 追加予定の属性
            evasion=10,         # 追加予定の属性
            critical_chance=5   # 追加予定の属性
        )
    
    def test_character_has_equipment_attribute(self):
        """キャラクターにequipment属性があることをテスト"""
        # equipment属性が存在することを確認
        self.assertTrue(hasattr(self.character, 'equipment'))
        
        # equipmentがNoneでも問題ないことを確認
        equipment = getattr(self.character, 'equipment', None)
        self.assertIsNotNone(equipment)
    
    def test_character_has_get_personal_inventory_method(self):
        """キャラクターにget_personal_inventory()メソッドがあることをテスト"""
        # get_personal_inventory()メソッドが存在することを確認
        self.assertTrue(hasattr(self.character, 'get_personal_inventory'))
        self.assertTrue(callable(getattr(self.character, 'get_personal_inventory')))
        
        # メソッドが実行できることを確認
        personal_inventory = self.character.get_personal_inventory()
        self.assertIsNotNone(personal_inventory)
    
    def test_base_stats_has_vitality(self):
        """BaseStatsにvitality属性があることをテスト"""
        self.assertTrue(hasattr(self.character.base_stats, 'vitality'))
        self.assertIsInstance(self.character.base_stats.vitality, int)
    
    def test_derived_stats_has_combat_attributes(self):
        """DerivedStatsに戦闘関連属性があることをテスト"""
        combat_attributes = ['attack_power', 'defense', 'accuracy', 'evasion', 'critical_chance']
        
        for attr in combat_attributes:
            with self.subTest(attribute=attr):
                self.assertTrue(hasattr(self.character.derived_stats, attr))
                value = getattr(self.character.derived_stats, attr)
                self.assertIsInstance(value, (int, float))
    
    def test_show_character_details_does_not_crash(self):
        """_show_character_detailsメソッドがクラッシュしないことをテスト"""
        with patch('src.overworld.overworld_manager.OverworldManager.__init__', return_value=None):
            overworld_manager = OverworldManager()
            overworld_manager._show_info_dialog = Mock()
            
            # _show_character_detailsメソッドを呼び出してもクラッシュしないことを確認
            try:
                overworld_manager._show_character_details(self.character)
                success = True
            except AttributeError as e:
                success = False
                print(f"AttributeError発生: {e}")
            except Exception as e:
                success = False
                print(f"その他のエラー発生: {e}")
            
            self.assertTrue(success, "_show_character_detailsでクラッシュが発生")
    
    def test_equipment_display_handling(self):
        """装備品表示の処理テスト"""
        # 装備品が存在する場合
        mock_equipment = Mock()
        mock_equipment.weapon = Mock()
        mock_equipment.weapon.name = "テスト武器"
        mock_equipment.armor = Mock()
        mock_equipment.armor.name = "テスト防具"
        
        self.character.equipment = mock_equipment
        
        with patch('src.overworld.overworld_manager.OverworldManager.__init__', return_value=None):
            overworld_manager = OverworldManager()
            overworld_manager._show_info_dialog = Mock()
            
            # 装備品情報を含む詳細表示が正常に動作することを確認
            overworld_manager._show_character_details(self.character)
            
            # _show_info_dialogが呼ばれることを確認
            overworld_manager._show_info_dialog.assert_called_once()
    
    def test_personal_inventory_display_handling(self):
        """個人インベントリ表示の処理テスト"""
        # 個人インベントリが存在する場合
        mock_inventory = Mock()
        mock_inventory.get_items.return_value = [
            Mock(name="アイテム1", quantity=2),
            Mock(name="アイテム2", quantity=1)
        ]
        
        # get_personal_inventoryメソッドのモック
        self.character.get_personal_inventory = Mock(return_value=mock_inventory)
        
        with patch('src.overworld.overworld_manager.OverworldManager.__init__', return_value=None):
            overworld_manager = OverworldManager()
            overworld_manager._show_info_dialog = Mock()
            
            # 個人インベントリ情報を含む詳細表示が正常に動作することを確認
            overworld_manager._show_character_details(self.character)
            
            # _show_info_dialogが呼ばれることを確認
            overworld_manager._show_info_dialog.assert_called_once()
    
    def test_error_handling_with_missing_attributes(self):
        """属性が不足している場合のエラーハンドリングテスト"""
        # 一部の属性を削除
        delattr(self.character, 'derived_stats')
        
        with patch('src.overworld.overworld_manager.OverworldManager.__init__', return_value=None):
            overworld_manager = OverworldManager()
            overworld_manager._show_info_dialog = Mock()
            
            # 属性が不足していてもクラッシュしないことを確認
            try:
                overworld_manager._show_character_details(self.character)
                success = True
            except Exception as e:
                success = False
                print(f"予期しないエラー: {e}")
            
            # エラーハンドリングが機能してクラッシュしないことを確認
            self.assertTrue(success, "属性不足時のエラーハンドリングが機能していない")


if __name__ == '__main__':
    unittest.main()