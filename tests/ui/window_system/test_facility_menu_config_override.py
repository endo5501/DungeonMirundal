"""
施設メニュー設定のオーバーライド問題を修正するテスト

TDDアプローチで問題を修正する
"""

import unittest
import pygame
from unittest.mock import Mock, patch

from src.ui.window_system import WindowManager
from src.overworld.facilities.guild import AdventurersGuild
from src.overworld.base_facility import facility_manager, initialize_facilities
from src.character.party import Party
from src.character.character import Character, CharacterStatus


class TestFacilityMenuConfigOverride(unittest.TestCase):
    """施設メニュー設定オーバーライド問題の修正テスト"""
    
    def setUp(self):
        """テスト前の準備"""
        pygame.init()
        pygame.display.set_mode((800, 600))
        
        # WindowManagerのインスタンスをリセット
        WindowManager._instance = None
        
        # 施設の初期化
        initialize_facilities()
        
        # テスト用パーティを作成
        self.test_party = self._create_test_party()
        
    def tearDown(self):
        """テスト後のクリーンアップ"""
        facility_manager.cleanup()
        WindowManager._instance = None
        pygame.quit()
    
    def _create_test_party(self) -> Party:
        """テスト用のパーティを作成"""
        party = Party("テストパーティ")
        party.gold = 1000
        
        character = Character()
        character.name = "テストキャラクター"
        character.status = CharacterStatus.GOOD
        
        party.add_character(character)
        return party
    
    def test_adventurers_guild_should_override_create_facility_menu_config(self):
        """
        AdventurersGuildが_create_facility_menu_config()メソッドを
        正しくオーバーライドすべき（現在失敗するテスト）
        """
        guild = facility_manager.get_facility("guild")
        guild.current_party = self.test_party
        
        # メソッドが存在するかチェック
        self.assertTrue(hasattr(guild, '_create_facility_menu_config'), 
                       "AdventurersGuildに_create_facility_menu_config()メソッドが存在しません")
        
        # メソッドを呼び出し
        menu_config = guild._create_facility_menu_config()
        
        # 基本設定の確認
        self.assertIn('facility_type', menu_config)
        self.assertIn('menu_items', menu_config)
        
        # メニュー項目数の確認（これが現在失敗する）
        menu_items = menu_config['menu_items']
        self.assertGreater(len(menu_items), 1, 
                          f"AdventurersGuildのメニュー項目は1つ以上であるべき、実際: {len(menu_items)}")
        
        # 期待される項目の確認
        item_ids = [item['id'] for item in menu_items]
        expected_ids = ['character_creation', 'party_formation', 'character_list', 'class_change', 'exit']
        
        for expected_id in expected_ids:
            self.assertIn(expected_id, item_ids, f"{expected_id} が見つかりません")
    
    def test_base_facility_create_facility_menu_config_vs_guild_implementation(self):
        """
        AdventurersGuildの実装が正しく動作することを確認
        """
        # AdventurersGuildの実装をテスト
        guild = facility_manager.get_facility("guild")
        guild.current_party = self.test_party
        
        # _create_guild_menu_config()の結果を確認
        guild_config = guild._create_guild_menu_config()
        guild_items = guild_config['menu_items']
        
        print(f"AdventurersGuildのメニュー項目数: {len(guild_items)}")
        for item in guild_items:
            print(f"  - {item['id']}: {item['label']}")
        
        # _create_facility_menu_config()も同じ結果を返すべき（修正後）
        facility_config = guild._create_facility_menu_config()
        facility_items = facility_config['menu_items']
        
        print(f"_create_facility_menu_config()のメニュー項目数: {len(facility_items)}")
        
        # オーバーライドが正しく動作していることを確認
        self.assertEqual(len(guild_items), len(facility_items),
                        "_create_facility_menu_config()が正しくオーバーライドされていません")
    
    def test_guild_create_facility_menu_config_method_missing_fix(self):
        """
        AdventurersGuildに_create_facility_menu_config()メソッドが
        不足している問題の修正をテスト
        """
        guild = facility_manager.get_facility("guild")
        guild.current_party = self.test_party
        
        # 現在の実装では、_create_facility_menu_config()が
        # BaseFacilityのデフォルト実装を呼び出している
        
        # _create_guild_menu_config()は正常に動作する
        guild_specific_config = guild._create_guild_menu_config()
        guild_specific_items = guild_specific_config['menu_items']
        
        # _create_facility_menu_config()の結果（修正前は基本項目のみ）
        facility_config = guild._create_facility_menu_config()
        facility_items = facility_config['menu_items']
        
        print(f"Guild固有メソッド項目数: {len(guild_specific_items)}")
        print(f"Facility汎用メソッド項目数: {len(facility_items)}")
        
        # この差がある場合、_create_facility_menu_config()のオーバーライドが必要
        if len(guild_specific_items) != len(facility_items):
            print("⚠️  _create_facility_menu_config()がオーバーライドされていません")
            print("修正が必要: AdventurersGuildで_create_facility_menu_config()をオーバーライド")
            
            # 修正後の期待値をアサート
            self.assertEqual(len(guild_specific_items), len(facility_items),
                           "_create_facility_menu_config()が正しくオーバーライドされていません")


if __name__ == '__main__':
    unittest.main()