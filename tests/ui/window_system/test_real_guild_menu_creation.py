"""
実際のAdventurersGuildクラスのメニュー作成プロセスをテスト

問題の根本原因を特定する
"""

import unittest
import pygame
from unittest.mock import Mock, patch

from src.ui.window_system import WindowManager
from src.overworld.facilities.guild import AdventurersGuild
from src.overworld.base_facility import facility_manager, initialize_facilities
from src.character.party import Party
from src.character.character import Character, CharacterStatus
from src.core.config_manager import config_manager


class TestRealGuildMenuCreation(unittest.TestCase):
    """実際のAdventurersGuildメニュー作成のテスト"""
    
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
    
    def test_adventurers_guild_menu_config_creation(self):
        """
        AdventurersGuildの_create_guild_menu_config()メソッドをテスト
        """
        # WindowManagerを初期化
        window_manager = WindowManager.get_instance()
        screen = pygame.display.get_surface()
        clock = pygame.time.Clock()
        window_manager.initialize_pygame(screen, clock)
        
        # AdventurersGuildインスタンスを取得
        guild = facility_manager.get_facility("guild")
        self.assertIsNotNone(guild, "ギルドが取得できません")
        self.assertIsInstance(guild, AdventurersGuild, "ギルドの型が正しくありません")
        
        # パーティを設定
        guild.current_party = self.test_party
        
        # メニュー設定を作成
        menu_config = guild._create_guild_menu_config()
        
        print(f"作成されたメニュー設定: {menu_config}")
        
        # 基本的な設定の確認
        self.assertIn('facility_type', menu_config)
        self.assertIn('menu_items', menu_config)
        self.assertIn('party', menu_config)
        
        # メニュー項目の確認
        menu_items = menu_config['menu_items']
        print(f"メニュー項目数: {len(menu_items)}")
        
        for i, item in enumerate(menu_items):
            print(f"  {i+1}. {item['id']}: {item['label']} (enabled={item['enabled']})")
        
        # 期待される項目数の確認
        self.assertEqual(len(menu_items), 5, "5つのメニュー項目が作成されるはず")
        
        # 各項目のIDを確認
        item_ids = [item['id'] for item in menu_items]
        expected_ids = ['character_creation', 'party_formation', 'character_list', 'class_change', 'exit']
        
        for expected_id in expected_ids:
            self.assertIn(expected_id, item_ids, f"{expected_id} が見つかりません")
    
    def test_config_manager_text_retrieval(self):
        """
        config_managerのテキスト取得が正常に動作することをテスト
        """
        # ギルド関連のテキストを取得
        test_keys = [
            "guild.menu.character_creation",
            "guild.menu.party_formation", 
            "guild.menu.character_list",
            "guild.menu.class_change",
            "menu.exit",
            "facility.guild"
        ]
        
        for key in test_keys:
            text = config_manager.get_text(key)
            print(f"{key}: '{text}'")
            self.assertIsNotNone(text, f"{key} のテキストが取得できません")
            self.assertNotEqual(text, key, f"{key} のテキストがキーのまま返されています")
    
    def test_guild_facility_enter_and_menu_creation(self):
        """
        実際の施設入場とメニュー作成プロセスをテスト
        """
        # WindowManagerを初期化
        window_manager = WindowManager.get_instance()
        screen = pygame.display.get_surface()
        clock = pygame.time.Clock()
        window_manager.initialize_pygame(screen, clock)
        
        # FacilityManagerにUIManagerを設定
        facility_manager.set_ui_manager(window_manager.ui_manager)
        
        # 施設入場
        success = facility_manager.enter_facility("guild", self.test_party)
        self.assertTrue(success, "施設入場が失敗しました")
        
        # 現在の施設を取得
        current_facility = facility_manager.get_current_facility()
        self.assertIsNotNone(current_facility, "現在の施設が設定されていません")
        
        # アクティブなウィンドウを確認
        active_window = window_manager.get_active_window()
        self.assertIsNotNone(active_window, "アクティブウィンドウが存在しません")
        
        print(f"アクティブウィンドウタイプ: {type(active_window).__name__}")
        print(f"ウィンドウID: {active_window.window_id}")
        
        # FacilityMenuWindowの場合の詳細チェック
        from src.ui.window_system.facility_menu_window import FacilityMenuWindow
        if isinstance(active_window, FacilityMenuWindow):
            print(f"施設タイプ: {active_window.facility_type}")
            print(f"設定されたメニュー項目数: {len(active_window.menu_items)}")
            print(f"作成されたUIボタン数: {len(active_window.menu_buttons)}")
            
            # メニュー項目の詳細表示
            for i, item in enumerate(active_window.menu_items):
                print(f"  項目{i+1}: {item.item_id} - {item.label} (available: {item.is_available(self.test_party)})")
            
            # これが現在の問題：メニュー項目が1つしかない
            self.assertGreater(len(active_window.menu_items), 1, 
                             f"メニュー項目が1つしかありません: {len(active_window.menu_items)}")
            
            # 利用可能な項目のチェック
            available_items = [item for item in active_window.menu_items if item.is_available(self.test_party)]
            self.assertGreater(len(available_items), 1,
                             f"利用可能なメニュー項目が1つしかありません: {len(available_items)}")
    
    def test_guild_menu_items_enabled_status(self):
        """
        ギルドメニュー項目のenabled状態をテスト
        """
        guild = facility_manager.get_facility("guild")
        guild.current_party = self.test_party
        
        menu_config = guild._create_guild_menu_config()
        menu_items = menu_config['menu_items']
        
        # 各項目のenabled状態を確認
        for item in menu_items:
            print(f"{item['id']}: enabled={item['enabled']}")
            
            # 基本的な項目は有効であるべき
            if item['id'] in ['character_creation', 'exit']:
                self.assertTrue(item['enabled'], f"{item['id']} は常に有効であるべき")
            
            # パーティ依存項目のチェック
            if item['id'] in ['party_formation', 'class_change']:
                # パーティがあるので有効であるべき
                self.assertTrue(item['enabled'], f"{item['id']} はパーティがある場合有効であるべき")


if __name__ == '__main__':
    unittest.main()