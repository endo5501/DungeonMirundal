"""
施設メニューボタン機能のテスト

0056の問題：施設メニューボタンを押しても何も起きない
TDDアプローチで問題を特定・修正する
"""

import unittest
import pygame
from unittest.mock import Mock, patch

from src.ui.window_system import WindowManager
from src.ui.window_system.facility_menu_window import FacilityMenuWindow
from src.overworld.base_facility import facility_manager, initialize_facilities
from src.character.party import Party
from src.character.character import Character, CharacterStatus


class TestFacilityMenuButtonFunctionality(unittest.TestCase):
    """施設メニューボタン機能のテスト"""
    
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
    
    def test_facility_menu_button_click_should_trigger_action(self):
        """
        施設メニューボタンをクリックした際、適切なアクションが呼ばれるべき
        
        これは現在失敗するテスト（問題を再現）
        """
        # WindowManagerを初期化
        window_manager = WindowManager.get_instance()
        screen = pygame.display.get_surface()
        clock = pygame.time.Clock()
        window_manager.initialize_pygame(screen, clock)
        
        # 施設に入場
        success = facility_manager.enter_facility("guild", self.test_party)
        self.assertTrue(success, "施設入場が失敗")
        
        # アクティブなウィンドウを取得
        active_window = window_manager.get_active_window()
        self.assertIsNotNone(active_window, "アクティブウィンドウが存在しない")
        self.assertIsInstance(active_window, FacilityMenuWindow, "アクティブウィンドウがFacilityMenuWindowではない")
        
        facility_window = active_window
        
        # メニューボタンが存在することを確認
        self.assertTrue(hasattr(facility_window, 'menu_buttons'), "menu_buttonsが存在しない")
        self.assertGreater(len(facility_window.menu_buttons), 1, "メニューボタンが不足")
        
        # メッセージハンドラーを設定
        mock_message_handler = Mock()
        facility_window.message_handler = mock_message_handler
        
        # 最初のボタン（キャラクター作成）をクリック
        character_creation_button = None
        for button in facility_window.menu_buttons:
            if hasattr(button, 'text') and 'キャラクター作成' in button.text:
                character_creation_button = button
                break
        
        self.assertIsNotNone(character_creation_button, "キャラクター作成ボタンが見つからない")
        
        # ボタンクリックイベントを生成
        import pygame_gui
        click_event = pygame.event.Event(
            pygame_gui.UI_BUTTON_PRESSED, 
            {'ui_element': character_creation_button}
        )
        
        # ボタンクリックを処理
        handled = facility_window.handle_event(click_event)
        
        # イベントが処理されることを確認
        self.assertTrue(handled, "ボタンクリックイベントが処理されなかった")
        
        # メッセージハンドラーが呼ばれることを確認
        # これが現在失敗する可能性がある
        mock_message_handler.assert_called_once()
        
        # 呼び出された引数を確認
        call_args = mock_message_handler.call_args
        self.assertEqual(call_args[0][0], 'menu_item_selected', "メッセージタイプが正しくない")
        self.assertIn('item_id', call_args[0][1], "item_idが含まれていない")
    
    def test_message_handler_connection_in_facility_window(self):
        """
        FacilityMenuWindowのメッセージハンドラーが正しく設定されているかテスト
        """
        # 冒険者ギルドの設定を取得
        guild = facility_manager.get_facility("guild")
        guild.current_party = self.test_party
        
        # FacilityMenuWindowを直接作成
        facility_config = guild._create_facility_menu_config()
        facility_window = FacilityMenuWindow("test_facility_menu", facility_config)
        
        # メッセージハンドラーが設定されているかチェック
        self.assertTrue(hasattr(facility_window, 'message_handler'), "message_handlerプロパティが存在しない")
        
        # 初期状態ではNoneの可能性
        print(f"Initial message_handler: {facility_window.message_handler}")
        
        # メッセージハンドラーを設定
        mock_handler = Mock()
        facility_window.message_handler = mock_handler
        
        # 設定されたことを確認
        self.assertEqual(facility_window.message_handler, mock_handler, "メッセージハンドラーが正しく設定されない")
    
    def test_guild_facility_message_handling_integration(self):
        """
        冒険者ギルドのメッセージハンドリング統合テスト
        """
        # 施設に入場
        success = facility_manager.enter_facility("guild", self.test_party)
        self.assertTrue(success)
        
        # 現在の施設を取得
        current_facility = facility_manager.get_current_facility()
        self.assertIsNotNone(current_facility)
        
        # 施設のメッセージハンドリングメソッドが存在することを確認
        self.assertTrue(hasattr(current_facility, 'handle_facility_message'), 
                       "handle_facility_messageメソッドが存在しない")
        
        # 退場メッセージをテスト（実装済みで安全）
        result = current_facility.handle_facility_message(
            'facility_exit_requested', 
            {'facility_type': 'guild'}
        )
        
        # メッセージが処理されることを確認
        self.assertTrue(result, "退場メッセージが処理されなかった")
    
    def test_party_info_display_content(self):
        """
        パーティ情報表示の内容をテスト
        
        0056の問題：パーティ情報が「0人」「0G」「0/0」と表示される
        """
        # WindowManagerを初期化
        window_manager = WindowManager.get_instance()
        screen = pygame.display.get_surface()
        clock = pygame.time.Clock()
        window_manager.initialize_pygame(screen, clock)
        
        # 施設に入場
        success = facility_manager.enter_facility("guild", self.test_party)
        self.assertTrue(success)
        
        # アクティブなウィンドウを取得
        active_window = window_manager.get_active_window()
        facility_window = active_window
        
        # パーティ情報パネルが存在するかチェック
        if hasattr(facility_window, 'party_info_panel'):
            print(f"Party info panel exists: {facility_window.party_info_panel}")
            
        # テストパーティの情報が正しく表示されるかチェック
        expected_member_count = len(self.test_party.get_all_characters())
        expected_gold = self.test_party.gold
        
        print(f"Expected member count: {expected_member_count}")
        print(f"Expected gold: {expected_gold}")
        print(f"Test party details: members={len(self.test_party.get_all_characters())}, gold={self.test_party.gold}")
        
        # パーティが正しく設定されていることを確認
        self.assertEqual(facility_window.party, self.test_party, "パーティが正しく設定されていない")
        self.assertGreater(expected_member_count, 0, "テストパーティにメンバーがいない")
        self.assertGreater(expected_gold, 0, "テストパーティにゴールドがない")
    
    def test_send_message_method_functionality(self):
        """
        FacilityMenuWindowのsend_messageメソッドの動作をテスト
        """
        # FacilityMenuWindowを作成
        guild = facility_manager.get_facility("guild")
        guild.current_party = self.test_party
        
        facility_config = guild._create_facility_menu_config()
        facility_window = FacilityMenuWindow("test_facility_menu", facility_config)
        
        # send_messageメソッドが存在することを確認
        self.assertTrue(hasattr(facility_window, 'send_message'), "send_messageメソッドが存在しない")
        
        # メッセージハンドラーを設定
        mock_handler = Mock()
        facility_window.message_handler = mock_handler
        
        # send_messageを呼び出し
        facility_window.send_message('test_message', {'test_data': 'value'})
        
        # メッセージハンドラーが呼ばれることを確認
        mock_handler.assert_called_once_with('test_message', {'test_data': 'value'})


if __name__ == '__main__':
    unittest.main()