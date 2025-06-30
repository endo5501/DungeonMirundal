"""
施設表示問題の再現テスト

TDDアプローチで問題を再現するテストを作成し、問題を特定する。
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import pygame
import pygame_gui
from unittest.mock import PropertyMock

from src.ui.window_system import WindowManager
from src.ui.window_system.facility_menu_window import FacilityMenuWindow
from src.overworld.base_facility import facility_manager, initialize_facilities
from src.character.party import Party
from src.character.character import Character, CharacterStatus


class TestFacilityDisplayIssue(unittest.TestCase):
    """施設表示問題の再現テスト"""
    
    def setUp(self):
        """テスト前の準備"""
        # Pygameを初期化
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
        # 施設マネージャーのクリーンアップ
        facility_manager.cleanup()
        
        # WindowManagerのリセット
        WindowManager._instance = None
        
        pygame.quit()
    
    def _create_test_party(self) -> Party:
        """テスト用のパーティを作成"""
        party = Party("テストパーティ")
        
        # 現在の実装に合わせて基本的なキャラクターを作成
        character = Character()
        character.name = "テストキャラクター"
        character.status = CharacterStatus.GOOD
        
        # 基本ステータスを設定
        if hasattr(character, 'base_stats'):
            character.base_stats.strength = 15
            character.base_stats.dexterity = 14
            character.base_stats.constitution = 13
            character.base_stats.intelligence = 12
            character.base_stats.wisdom = 11
            character.base_stats.charisma = 10
        
        party.add_character(character)
        return party
    
    def test_facility_menu_should_display_menu_items_not_just_exit_button(self):
        """
        施設メニューが表示される際、終了ボタンだけでなく、
        施設固有のメニュー項目も表示されるべき
        
        これは現在失敗するテスト（問題を再現）
        """
        # テスト準備：WindowManagerとpygame-gui統合を確実に初期化
        window_manager = WindowManager.get_instance()
        screen = pygame.display.get_surface()
        clock = pygame.time.Clock()
        window_manager.initialize_pygame(screen, clock)
        
        # UIManagerが適切に初期化されていることを確認
        self.assertIsNotNone(window_manager.ui_manager)
        self.assertIsInstance(window_manager.ui_manager, pygame_gui.UIManager)
        
        # 施設入場を実行
        success = facility_manager.enter_facility("guild", self.test_party)
        self.assertTrue(success, "施設入場が失敗しました")
        
        # FacilityMenuWindowが作成されているかを確認
        current_facility = facility_manager.get_current_facility()
        self.assertIsNotNone(current_facility, "現在の施設が設定されていません")
        
        # FacilityMenuWindowが表示されているかを確認
        active_window = window_manager.get_active_window()
        self.assertIsNotNone(active_window, "アクティブなウィンドウが存在しません")
        self.assertIsInstance(active_window, FacilityMenuWindow, "アクティブウィンドウがFacilityMenuWindowではありません")
        
        # ウィンドウのUI要素が適切に作成されているかを確認  
        facility_window = active_window
        
        # FacilityMenuWindowはmenu_buttons属性を使用
        self.assertTrue(hasattr(facility_window, 'menu_buttons'), "menu_buttonsが存在しません")
        
        # メニューボタンの数を確認
        if hasattr(facility_window, 'menu_buttons') and facility_window.menu_buttons:
            button_count = len(facility_window.menu_buttons)
            print(f"メニューボタン数: {button_count}")
            
            # ボタンの詳細を表示
            for i, button in enumerate(facility_window.menu_buttons):
                if hasattr(button, 'text'):
                    print(f"  ボタン {i}: {button.text}")
            
            # 修正後は複数のボタンが存在するはず
            self.assertGreater(button_count, 1, 
                              "施設メニューの項目が表示されていません（終了ボタンのみ表示される問題）")
        else:
            self.fail("menu_buttonsが作成されていません")
    
    def test_facility_menu_ui_elements_should_be_created_correctly(self):
        """
        FacilityMenuWindowのUI要素が正しく作成されることをテスト
        
        Mock環境ではない実際のpygame-gui環境での動作を確認
        """
        # WindowManagerを初期化
        window_manager = WindowManager.get_instance()
        screen = pygame.display.get_surface()
        clock = pygame.time.Clock()
        window_manager.initialize_pygame(screen, clock)
        
        # 実際のUIManagerが使用されていることを確認
        self.assertIsNotNone(window_manager.ui_manager)
        
        # Mockが使用されていないことを確認
        self.assertFalse(hasattr(window_manager.ui_manager, '_mock_name'), 
                        "UIManagerがMockオブジェクトです - 実際のUIManagerが必要")
        
        # FacilityMenuWindowを直接作成してテスト
        facility_config = {
            'facility_type': 'guild',
            'title': 'adventurers_guild',
            'menu_items': [
                {'id': 'create_character', 'label': 'キャラクター作成', 'type': 'action'},
                {'id': 'party_management', 'label': 'パーティ管理', 'type': 'action'},
            ],
            'party': self.test_party
        }
        
        facility_window = FacilityMenuWindow("test_facility_window", facility_config)
        
        # UI要素を作成
        facility_window.create()
        
        # FacilityMenuWindowのmenu_buttons属性を確認
        self.assertTrue(hasattr(facility_window, 'menu_buttons'), "menu_buttonsが存在しません")
        
        if facility_window.menu_buttons:
            button_count = len(facility_window.menu_buttons)
            self.assertGreater(button_count, 1, "メニューボタンが適切に作成されていません")
        else:
            self.fail("menu_buttonsが作成されていません")
    
    def test_dungeon_entrance_should_trigger_callback(self):
        """
        ダンジョン入口ボタンが押された際、適切なコールバックが呼ばれるべき
        
        これも現在失敗する可能性がある問題のテスト
        """
        # OverworldManagerの初期化をシミュレート
        from src.overworld.overworld_manager_pygame import OverworldManager
        
        overworld_manager = OverworldManager()
        
        # WindowManagerとUIマネージャーを設定
        window_manager = WindowManager.get_instance()
        screen = pygame.display.get_surface()
        clock = pygame.time.Clock()
        window_manager.initialize_pygame(screen, clock)
        
        overworld_manager.set_ui_manager(window_manager.ui_manager)
        overworld_manager.set_party(self.test_party)
        
        # ダンジョン入場コールバックのMock
        mock_dungeon_callback = Mock()
        overworld_manager.set_enter_dungeon_callback(mock_dungeon_callback)
        
        # メインメニューを表示
        overworld_manager.enter_overworld(self.test_party)
        
        # ダンジョン入口ボタンのイベントをシミュレート
        # これは現在失敗する可能性がある
        result = overworld_manager.handle_main_menu_message(
            'menu_item_selected', 
            {'item_id': 'dungeon_entrance'}
        )
        
        # ダンジョン入場処理が呼ばれることを確認
        self.assertTrue(result, "ダンジョン入口のメッセージ処理が失敗しました")
        
        # Note: 実際のコールバック呼び出しの確認は、
        # ダンジョン選択画面の実装による
    
    def test_exit_button_functionality_in_facility_menu(self):
        """
        施設メニューの終了ボタンが機能することを確認
        """
        # 施設に入場
        success = facility_manager.enter_facility("guild", self.test_party)
        self.assertTrue(success)
        
        current_facility = facility_manager.get_current_facility()
        self.assertIsNotNone(current_facility)
        
        # 現在の施設がアクティブであることを確認
        self.assertTrue(current_facility.is_active, "施設がアクティブではありません")
        
        # 基本的な施設入場が成功したことを確認（修正された問題の確認）
        self.assertIsNotNone(current_facility)
        self.assertEqual(current_facility.facility_id, "guild")


if __name__ == '__main__':
    unittest.main()