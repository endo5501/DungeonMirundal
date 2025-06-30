"""
FacilityMenuWindowでメニュー項目のフィルタリング問題をテスト

具体的に、メニュー項目が適切に表示されない原因を特定し修正する
"""

import unittest
import pygame
from unittest.mock import Mock

from src.ui.window_system.facility_menu_window import FacilityMenuWindow
from src.ui.window_system.facility_menu_types import FacilityMenuItem, MenuItemType, FacilityConfig
from src.ui.window_system import WindowManager
from src.character.party import Party
from src.character.character import Character, CharacterStatus


class TestFacilityMenuItemsFiltering(unittest.TestCase):
    """施設メニュー項目フィルタリングのテスト"""
    
    def setUp(self):
        """テスト前の準備"""
        pygame.init()
        pygame.display.set_mode((800, 600))
        
        # WindowManagerのインスタンスをリセット
        WindowManager._instance = None
        
        # テスト用パーティを作成
        self.test_party = self._create_test_party()
        
    def tearDown(self):
        """テスト後のクリーンアップ"""
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
    
    def test_guild_menu_items_should_all_be_visible(self):
        """
        冒険者ギルドのメニュー項目が全て表示されるべき
        
        現在失敗する：メニュー項目のフィルタリングが原因で表示されない
        """
        # Guildの設定を作成（実際のAdventurersGuild._create_guild_menu_config()と同じ）
        guild_menu_items = [
            {
                'id': 'character_creation',
                'label': 'キャラクター作成',
                'type': 'action',
                'enabled': True
            },
            {
                'id': 'party_formation',
                'label': 'パーティ編成',
                'type': 'action',
                'enabled': self.test_party is not None  # True になるはず
            },
            {
                'id': 'character_list',
                'label': 'キャラクター一覧',
                'type': 'action',
                'enabled': True  # パーティにキャラクターがいるのでTrue
            },
            {
                'id': 'class_change',
                'label': '転職',
                'type': 'action',
                'enabled': self.test_party is not None and len(self.test_party.characters) > 0
            },
            {
                'id': 'exit',
                'label': '終了',
                'type': 'exit',
                'enabled': True
            }
        ]
        
        facility_config = {
            'facility_type': 'guild',
            'facility_name': '冒険者ギルド',
            'menu_items': guild_menu_items,
            'party': self.test_party,
            'show_party_info': True,
            'show_gold': True
        }
        
        # FacilityConfigの変換をテスト
        config_obj = FacilityConfig(
            facility_type=facility_config['facility_type'],
            facility_name=facility_config['facility_name'],
            party=facility_config['party'],
            menu_items=facility_config['menu_items'],
            show_party_info=facility_config['show_party_info'],
            show_gold=facility_config['show_gold']
        )
        
        # メニュー項目の変換をテスト
        menu_items = config_obj.get_menu_items()
        
        print(f"作成されたメニュー項目数: {len(menu_items)}")
        for i, item in enumerate(menu_items):
            print(f"  {i+1}. {item.item_id}: {item.label} (enabled={item.enabled}, visible={item.visible})")
        
        # 全ての項目が作成されることを確認
        self.assertEqual(len(menu_items), 5, "5つのメニュー項目が作成されるはず")
        
        # 各項目のavailabilityをテスト
        available_items = [item for item in menu_items if item.is_available(self.test_party)]
        
        print(f"利用可能なメニュー項目数: {len(available_items)}")
        for i, item in enumerate(available_items):
            print(f"  {i+1}. {item.item_id}: {item.label}")
        
        # 利用可能な項目数の確認（これが現在失敗する可能性）
        self.assertGreaterEqual(len(available_items), 4, 
                              "少なくとも4つの項目が利用可能であるはず（exit以外の項目+exit）")
        
        # 必須項目の確認
        item_ids = [item.item_id for item in available_items]
        self.assertIn('character_creation', item_ids, "キャラクター作成は常に利用可能であるはず")
        self.assertIn('exit', item_ids, "終了は常に利用可能であるはず")
    
    def test_facility_menu_window_with_correct_menu_items_count(self):
        """
        FacilityMenuWindowが正しい数のメニュー項目を表示することをテスト
        """
        # WindowManagerを初期化
        window_manager = WindowManager.get_instance()
        screen = pygame.display.get_surface()
        clock = pygame.time.Clock()
        window_manager.initialize_pygame(screen, clock)
        
        # 正常な設定でFacilityMenuWindowを作成
        facility_config = {
            'facility_type': 'guild',
            'facility_name': '冒険者ギルド',
            'menu_items': [
                {'id': 'action1', 'label': 'アクション1', 'type': 'action', 'enabled': True},
                {'id': 'action2', 'label': 'アクション2', 'type': 'action', 'enabled': True},
                {'id': 'action3', 'label': 'アクション3', 'type': 'action', 'enabled': True},
                {'id': 'exit', 'label': '終了', 'type': 'exit', 'enabled': True},
            ],
            'party': self.test_party
        }
        
        facility_window = FacilityMenuWindow("test_facility", facility_config)
        facility_window.create()
        
        # メニュー項目の数を確認
        self.assertEqual(len(facility_window.menu_items), 4, 
                        f"4つのメニュー項目が設定されるはず、実際: {len(facility_window.menu_items)}")
        
        # UI要素の数を確認
        self.assertEqual(len(facility_window.menu_buttons), 4, 
                        f"4つのメニューボタンが作成されるはず、実際: {len(facility_window.menu_buttons)}")
        
        # 各ボタンが作成されていることを確認
        for i, button in enumerate(facility_window.menu_buttons):
            self.assertIsNotNone(button, f"ボタン{i+1}が作成されていません")
    
    def test_menu_item_filtering_with_enabled_false(self):
        """
        無効化されたメニュー項目のフィルタリングをテスト
        """
        facility_config = {
            'facility_type': 'guild',
            'facility_name': '冒険者ギルド',
            'menu_items': [
                {'id': 'enabled_action', 'label': '有効なアクション', 'type': 'action', 'enabled': True},
                {'id': 'disabled_action', 'label': '無効なアクション', 'type': 'action', 'enabled': False},
                {'id': 'exit', 'label': '終了', 'type': 'exit', 'enabled': True},
            ],
            'party': self.test_party
        }
        
        config_obj = FacilityConfig(
            facility_type=facility_config['facility_type'],
            facility_name=facility_config['facility_name'],
            party=facility_config['party'],
            menu_items=facility_config['menu_items']
        )
        
        menu_items = config_obj.get_menu_items()
        available_items = [item for item in menu_items if item.is_available(self.test_party)]
        
        # 有効な項目のみが利用可能になることを確認
        available_ids = [item.item_id for item in available_items]
        self.assertIn('enabled_action', available_ids)
        self.assertNotIn('disabled_action', available_ids)
        self.assertIn('exit', available_ids)
    
    def test_party_dependent_menu_items(self):
        """
        パーティ状態に依存するメニュー項目のテスト
        """
        # パーティなしの場合
        facility_config = {
            'facility_type': 'guild',
            'facility_name': '冒険者ギルド',
            'menu_items': [
                {'id': 'party_action', 'label': 'パーティアクション', 'type': 'action', 'enabled': False},  # パーティがないため無効
                {'id': 'general_action', 'label': '一般アクション', 'type': 'action', 'enabled': True},
                {'id': 'exit', 'label': '終了', 'type': 'exit', 'enabled': True},
            ],
            'party': None  # パーティなし
        }
        
        config_obj = FacilityConfig(
            facility_type=facility_config['facility_type'],
            facility_name=facility_config['facility_name'],
            party=facility_config['party'],
            menu_items=facility_config['menu_items']
        )
        
        menu_items = config_obj.get_menu_items()
        available_items = [item for item in menu_items if item.is_available(None)]
        
        # パーティに依存しない項目のみが利用可能
        available_ids = [item.item_id for item in available_items]
        self.assertNotIn('party_action', available_ids)
        self.assertIn('general_action', available_ids)
        self.assertIn('exit', available_ids)


if __name__ == '__main__':
    unittest.main()