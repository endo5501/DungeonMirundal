"""
FacilityMenuWindowのUI作成プロセスをデバッグするテスト

具体的にどこでUI作成が失敗しているのかを特定する
"""

import unittest
import pygame
import pygame_gui
from unittest.mock import Mock

from src.ui.window_system.facility_menu_window import FacilityMenuWindow
from src.ui.window_system import WindowManager
from src.character.party import Party
from src.character.character import Character, CharacterStatus


class TestFacilityMenuUICreationDebug(unittest.TestCase):
    """FacilityMenuWindowのUI作成デバッグテスト"""
    
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
        
        character = Character()
        character.name = "テストキャラクター"
        character.status = CharacterStatus.GOOD
        
        party.add_character(character)
        return party
    
    def test_facility_menu_window_ui_creation_step_by_step(self):
        """
        FacilityMenuWindowのUI作成プロセスを段階的にテスト
        どの段階で失敗するかを特定する
        """
        # Step 1: WindowManagerの初期化
        window_manager = WindowManager.get_instance()
        screen = pygame.display.get_surface()
        clock = pygame.time.Clock()
        window_manager.initialize_pygame(screen, clock)
        
        # UIManagerが初期化されていることを確認
        self.assertIsNotNone(window_manager.ui_manager)
        
        # Step 2: 施設設定の作成
        facility_config = {
            'facility_type': 'guild',
            'facility_name': '冒険者ギルド',
            'menu_items': [
                {'id': 'create_character', 'label': 'キャラクター作成', 'type': 'action'},
                {'id': 'party_management', 'label': 'パーティ管理', 'type': 'action'},
                {'id': 'exit', 'label': '終了', 'type': 'exit'},
            ],
            'party': self.test_party,
            'show_party_info': True,
            'show_gold': True
        }
        
        # Step 3: FacilityMenuWindowの作成
        facility_window = FacilityMenuWindow("test_facility_window", facility_config)
        
        # 設定が正しく処理されていることを確認
        self.assertEqual(facility_window.facility_type.value, 'guild')
        self.assertEqual(facility_window.facility_name, '冒険者ギルド')
        self.assertEqual(len(facility_window.menu_items), 3)
        
        # Step 4: UI作成前の状態確認
        self.assertIsNone(facility_window.main_container)
        self.assertIsNone(facility_window.facility_title)
        self.assertEqual(len(facility_window.menu_buttons), 0)
        
        # Step 5: UIManager確認
        # create()を呼ぶ前にUIManagerが設定されるかチェック
        self.assertIsNone(facility_window.ui_manager)
        
        # Step 6: UI作成実行
        facility_window.create()
        
        # Step 7: UI作成後の状態確認
        self.assertIsNotNone(facility_window.ui_manager, "UIManagerが設定されていません")
        
        # UIManagerがMockかどうか確認
        if hasattr(facility_window.ui_manager, '_mock_name'):
            print("UIManagerがMockオブジェクトです - これが問題の原因")
            self.fail("UIManagerがMockオブジェクトのため、UI要素が作成されません")
        
        # UI要素が作成されているかチェック
        self.assertIsNotNone(facility_window.main_container, "main_containerが作成されていません")
        self.assertIsNotNone(facility_window.facility_title, "facility_titleが作成されていません")
        self.assertGreater(len(facility_window.menu_buttons), 0, "menu_buttonsが作成されていません")
        
        # 具体的なボタン数の確認
        self.assertEqual(len(facility_window.menu_buttons), 3, 
                        f"期待されるボタン数: 3, 実際: {len(facility_window.menu_buttons)}")
    
    def test_ui_manager_initialization_process(self):
        """
        UIManager初期化プロセスの詳細テスト
        """
        # WindowManagerを初期化
        window_manager = WindowManager.get_instance()
        screen = pygame.display.get_surface()
        clock = pygame.time.Clock()
        window_manager.initialize_pygame(screen, clock)
        
        # FacilityMenuWindowを作成（UIManagerはまだ設定されていない）
        facility_config = {
            'facility_type': 'guild',
            'facility_name': '冒険者ギルド',
            'menu_items': [
                {'id': 'test_action', 'label': 'テストアクション', 'type': 'action'},
                {'id': 'exit', 'label': '終了', 'type': 'exit'},
            ],
            'party': self.test_party
        }
        
        facility_window = FacilityMenuWindow("test_window", facility_config)
        
        # UIManagerの初期化をテスト
        facility_window._initialize_ui_manager()
        
        # UIManagerが適切に設定されているかチェック
        self.assertIsNotNone(facility_window.ui_manager)
        self.assertIsInstance(facility_window.ui_manager, pygame_gui.UIManager)
        
        # Mockではないことを確認
        self.assertFalse(hasattr(facility_window.ui_manager, '_mock_name'),
                        "UIManagerがMockオブジェクトです")
    
    def test_menu_items_configuration(self):
        """
        メニュー項目の設定が正しく処理されるかテスト
        """
        menu_items_config = [
            {'id': 'action1', 'label': 'アクション1', 'type': 'action'},
            {'id': 'action2', 'label': 'アクション2', 'type': 'action'},
            {'id': 'submenu1', 'label': 'サブメニュー1', 'type': 'submenu'},
            {'id': 'exit', 'label': '終了', 'type': 'exit'},
        ]
        
        facility_config = {
            'facility_type': 'guild',
            'facility_name': 'テスト施設',
            'menu_items': menu_items_config,
            'party': self.test_party
        }
        
        facility_window = FacilityMenuWindow("test_menu_items", facility_config)
        
        # メニュー項目が正しく設定されているか確認
        self.assertEqual(len(facility_window.menu_items), 4)
        
        # 各メニュー項目の内容確認
        menu_ids = [item.item_id for item in facility_window.menu_items]
        self.assertIn('action1', menu_ids)
        self.assertIn('action2', menu_ids)
        self.assertIn('submenu1', menu_ids)
        self.assertIn('exit', menu_ids)


if __name__ == '__main__':
    unittest.main()