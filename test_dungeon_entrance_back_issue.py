"""ダンジョン入口戻るボタン問題のテスト"""

import unittest
from unittest.mock import Mock, patch
from src.ui.selection_list_ui import CustomSelectionList, SelectionListData
from src.overworld.overworld_manager_pygame import OverworldManager


class TestDungeonEntranceBackIssue(unittest.TestCase):
    """ダンジョン入口戻るボタン問題のテスト"""
    
    def setUp(self):
        """テストの準備"""
        # UI関連のモック
        self.mock_ui_manager = Mock()
        self.mock_pygame_gui_manager = Mock()
        self.mock_ui_manager.pygame_gui_manager = self.mock_pygame_gui_manager
        
        # OverworldManagerのインスタンス作成
        self.overworld_manager = OverworldManager()
        self.overworld_manager.ui_manager = self.mock_ui_manager
    
    def test_custom_selection_list_back_button_only_kills(self):
        """CustomSelectionListの戻るボタンがkillのみを実行する問題を再現"""
        import pygame
        pygame.init()
        
        # CustomSelectionListを作成
        list_rect = pygame.Rect(100, 100, 600, 500)
        selection_list = CustomSelectionList(
            relative_rect=list_rect,
            manager=self.mock_pygame_gui_manager,
            title="テスト選択リスト"
        )
        
        # 戻るボタンが存在することを確認
        self.assertTrue(len(selection_list.action_buttons) > 0)
        
        # 戻るボタンを見つける
        back_button = None
        for button in selection_list.action_buttons:
            if hasattr(button, 'text') and button.text == "戻る":
                back_button = button
                break
        
        self.assertIsNotNone(back_button, "戻るボタンが見つかりません")
        
        # 戻るボタンのイベントをシミュレート
        import pygame_gui
        mock_event = Mock()
        mock_event.type = pygame_gui.UI_BUTTON_PRESSED
        mock_event.ui_element = back_button
        
        # 戻るコールバックが設定されていないことを確認
        self.assertIsNone(getattr(selection_list, 'on_back', None))
        
        # イベント処理を実行
        result = selection_list.handle_event(mock_event)
        
        # 戻るボタンが処理されることを確認
        self.assertTrue(result)
        
        pygame.quit()
    
    def test_dungeon_selection_menu_back_behavior(self):
        """ダンジョン選択メニューの戻る動作をテスト"""
        # メインメニューをモック
        self.overworld_manager.main_menu = Mock()
        self.overworld_manager.main_menu.menu_id = "main_menu"
        
        # ダンジョン選択リストをモック
        mock_selection_list = Mock()
        self.overworld_manager.dungeon_selection_list = mock_selection_list
        
        # _close_dungeon_selection_menuの動作を確認
        self.overworld_manager._close_dungeon_selection_menu()
        
        # 選択リストが非表示になることを確認
        mock_selection_list.hide.assert_called_once()
        mock_selection_list.kill.assert_called_once()
        
        # メインメニューが再表示されることを確認
        self.mock_ui_manager.show_menu.assert_called_with("main_menu", modal=True)
    
    def test_dungeon_entrance_back_button_scenario_fixed(self):
        """[ダンジョン入口]-[戻る]のシナリオ（修正版）"""
        # 1. メインメニューからダンジョン入口を選択
        self.overworld_manager.main_menu = Mock()
        self.overworld_manager.main_menu.menu_id = "main_menu"
        
        # 2. ダンジョン選択メニューを表示
        with patch.object(self.overworld_manager, '_get_available_dungeons', return_value=[]):
            self.overworld_manager._show_dungeon_selection_menu()
        
        # ダンジョン選択リストが作成されることを確認
        self.assertIsNotNone(self.overworld_manager.dungeon_selection_list)
        
        # 戻るコールバックが設定されていることを確認
        selection_list = self.overworld_manager.dungeon_selection_list
        self.assertIsNotNone(selection_list.on_back)
        
        # 3. 戻るボタンを押すシミュレート（修正版）
        import pygame_gui
        mock_event = Mock()
        mock_event.type = pygame_gui.UI_BUTTON_PRESSED
        
        # 戻るボタンを模擬
        mock_back_button = Mock()
        mock_back_button.text = "戻る"
        mock_event.ui_element = mock_back_button
        
        # action_buttonsに戻るボタンを追加
        if hasattr(selection_list, 'action_buttons'):
            selection_list.action_buttons = [mock_back_button]
        
        # _close_dungeon_selection_menuをモック
        with patch.object(self.overworld_manager, '_close_dungeon_selection_menu') as mock_close:
            result = selection_list.handle_event(mock_event)
            
            # 戻るボタンが処理されることを確認
            self.assertTrue(result)
            
            # 修正: _close_dungeon_selection_menu()が呼ばれる
            mock_close.assert_called_once()
    
    def test_back_callback_execution(self):
        """戻るコールバック実行のテスト"""
        import pygame
        pygame.init()
        
        callback_called = False
        
        def test_callback():
            nonlocal callback_called
            callback_called = True
        
        # CustomSelectionListを作成
        list_rect = pygame.Rect(100, 100, 600, 500)
        selection_list = CustomSelectionList(
            relative_rect=list_rect,
            manager=self.mock_pygame_gui_manager,
            title="テスト選択リスト"
        )
        
        # 戻るコールバックを設定
        selection_list.on_back = test_callback
        
        # 戻るボタンのイベントを作成
        import pygame_gui
        mock_event = Mock()
        mock_event.type = pygame_gui.UI_BUTTON_PRESSED
        
        mock_back_button = Mock()
        mock_back_button.text = "戻る"
        mock_event.ui_element = mock_back_button
        
        # action_buttonsに戻るボタンを追加
        selection_list.action_buttons = [mock_back_button]
        
        # イベント処理を実行
        result = selection_list.handle_event(mock_event)
        
        # 戻るボタンが処理され、コールバックが実行されることを確認
        self.assertTrue(result)
        self.assertTrue(callback_called)
        
        pygame.quit()


if __name__ == '__main__':
    unittest.main()