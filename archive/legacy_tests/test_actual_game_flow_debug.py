"""
実際のゲーム実行フローでの施設表示問題をデバッグするテスト

実際のゲーム起動シーケンスを再現し、どこで問題が発生するかを特定する
"""

import unittest
import pygame
import pygame_gui
from unittest.mock import Mock, patch

from src.ui.window_system import WindowManager
from src.ui.window_system.overworld_main_window import OverworldMainWindow
from src.overworld.overworld_manager_pygame import OverworldManager
from src.overworld.base_facility import facility_manager, initialize_facilities
from src.character.party import Party
from src.character.character import Character, CharacterStatus


class TestActualGameFlowDebug(unittest.TestCase):
    """実際のゲーム実行フローでの問題調査テスト"""
    
    def setUp(self):
        """テスト前の準備"""
        pygame.init()
        pygame.display.set_mode((1024, 768))
        
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
    
    def test_full_overworld_manager_initialization_and_facility_access(self):
        """
        実際のOverworldManagerの初期化から施設アクセスまでの完全なフロー
        """
        # Step 1: WindowManagerの初期化（実際のゲームと同じ）
        window_manager = WindowManager.get_instance()
        screen = pygame.display.get_surface()
        clock = pygame.time.Clock()
        window_manager.initialize_pygame(screen, clock)
        
        # Step 2: OverworldManagerの初期化
        overworld_manager = OverworldManager()
        overworld_manager.set_ui_manager(window_manager.ui_manager)
        overworld_manager.set_party(self.test_party)
        
        # Step 3: OverworldMainWindowが正しく作成されているか確認
        self.assertIsNotNone(overworld_manager.overworld_main_window)
        self.assertEqual(overworld_manager.overworld_main_window.window_id, "overworld_main")
        
        # Step 4: WindowManagerにOverworldMainWindowが登録されているか確認
        # (実際のゲームでは enter_overworld で実行される)
        success = overworld_manager.enter_overworld(self.test_party)
        self.assertTrue(success, "地上部入場が失敗")
        
        # Step 5: アクティブウィンドウの確認
        active_window = window_manager.get_active_window()
        self.assertIsNotNone(active_window, "アクティブウィンドウが存在しません")
        
        # Step 6: 施設入場を試行（実際のゲームの動作をシミュレート）
        # handle_main_menu_message を直接呼び出して施設入場をテスト
        result = overworld_manager.handle_main_menu_message(
            'menu_item_selected', 
            {'facility_id': 'guild', 'item_id': 'guild'}
        )
        
        self.assertTrue(result, "施設メニューメッセージの処理が失敗")
        
        # Step 7: 施設に入場したことを確認
        current_facility = facility_manager.get_current_facility()
        self.assertIsNotNone(current_facility, "現在の施設が設定されていません")
        self.assertEqual(current_facility.facility_id, "guild")
        self.assertTrue(current_facility.is_active, "施設がアクティブではありません")
        
        # Step 8: 施設のFacilityMenuWindowが表示されているか確認
        facility_window = window_manager.get_active_window()
        
        # 施設ウィンドウが表示されている場合の詳細チェック
        if facility_window:
            print(f"アクティブウィンドウ: {type(facility_window).__name__}")
            print(f"ウィンドウID: {facility_window.window_id}")
            
            # FacilityMenuWindowの場合の詳細チェック
            from src.ui.window_system.facility_menu_window import FacilityMenuWindow
            if isinstance(facility_window, FacilityMenuWindow):
                print(f"FacilityMenuWindow詳細:")
                print(f"  - facility_type: {facility_window.facility_type}")
                print(f"  - menu_items数: {len(facility_window.menu_items)}")
                print(f"  - main_container: {facility_window.main_container}")
                print(f"  - facility_title: {facility_window.facility_title}")
                print(f"  - menu_buttons数: {len(facility_window.menu_buttons)}")
                
                # UI要素の確認
                self.assertIsNotNone(facility_window.main_container, "main_containerが作成されていません")
                self.assertGreater(len(facility_window.menu_buttons), 0, "メニューボタンが作成されていません")
                
                # 終了ボタン以外のボタンが存在するか確認
                non_exit_buttons = [btn for btn in facility_window.menu_buttons 
                                  if hasattr(btn, 'text') and 'exit' not in btn.text.lower()]
                self.assertGreater(len(non_exit_buttons), 0, 
                                  "終了ボタン以外のメニューボタンが存在しません - これが報告された問題です")
        else:
            self.fail("施設入場後にアクティブウィンドウが存在しません")
    
    def test_ui_manager_consistency_check(self):
        """
        ゲーム全体でUIManagerの一貫性をチェック
        """
        # WindowManagerを初期化
        window_manager = WindowManager.get_instance()
        screen = pygame.display.get_surface()
        clock = pygame.time.Clock()
        window_manager.initialize_pygame(screen, clock)
        
        # OverworldManagerを初期化
        overworld_manager = OverworldManager()
        overworld_manager.set_ui_manager(window_manager.ui_manager)
        
        # UIManagerの一貫性をチェック
        self.assertIs(overworld_manager.ui_manager, window_manager.ui_manager,
                     "OverworldManagerとWindowManagerのUIManagerが異なります")
        
        # FacilityManagerのUIManagerもチェック
        self.assertIs(facility_manager.ui_manager, window_manager.ui_manager,
                     "FacilityManagerとWindowManagerのUIManagerが異なります")
    
    def test_window_manager_event_routing_and_update_cycle(self):
        """
        WindowManagerのイベントルーティングと更新サイクルをテスト
        
        実際のゲームループでのWindowManagerの動作を確認
        """
        # WindowManagerを初期化
        window_manager = WindowManager.get_instance()
        screen = pygame.display.get_surface()
        clock = pygame.time.Clock()
        window_manager.initialize_pygame(screen, clock)
        
        # OverworldManagerを初期化して地上部に入場
        overworld_manager = OverworldManager()
        overworld_manager.set_ui_manager(window_manager.ui_manager)
        overworld_manager.enter_overworld(self.test_party)
        
        # イベントと更新の処理をシミュレート
        time_delta = 0.016  # 60FPS
        
        # OverworldMainWindowが適切に更新されるかテスト
        active_window = window_manager.get_active_window()
        if active_window:
            # 更新処理
            active_window.update(time_delta)
            
            # イベント処理のテスト（キーボードイベント）
            test_event = pygame.event.Event(pygame.KEYDOWN, key=pygame.K_ESCAPE)
            handled = active_window.handle_event(test_event)
            
            print(f"ESCキーイベント処理結果: {handled}")
        
        # 施設入場後のイベント処理をテスト
        result = overworld_manager.handle_main_menu_message(
            'menu_item_selected', 
            {'facility_id': 'guild', 'item_id': 'guild'}
        )
        
        if result:
            # 施設ウィンドウのイベント処理をテスト
            facility_window = window_manager.get_active_window()
            if facility_window:
                facility_window.update(time_delta)


if __name__ == '__main__':
    unittest.main()