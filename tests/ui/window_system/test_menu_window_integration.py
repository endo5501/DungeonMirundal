"""
MenuWindow の統合テスト

WindowManagerとの連携を含む統合的な動作確認
"""

import pytest
import pygame
import pygame_gui
from unittest.mock import Mock, patch
from src.ui.window_system import WindowManager, MenuWindow, WindowState


class TestMenuWindowIntegration:
    """MenuWindow の統合テストクラス"""
    
    def setup_method(self):
        """各テストメソッドの前に実行される"""
        pygame.init()
        pygame.display.set_mode((1024, 768), pygame.NOFRAME)
        self.screen = pygame.display.get_surface()
        self.clock = pygame.time.Clock()
        
        # WindowManagerをリセット
        WindowManager._instance = None
        self.window_manager = WindowManager.get_instance()
        self.window_manager.initialize_pygame(self.screen, self.clock)
    
    def teardown_method(self):
        """各テストメソッドの後に実行される"""
        self.window_manager.shutdown()
        WindowManager._instance = None
        pygame.quit()
    
    def test_menu_window_back_action_returns_to_previous_window(self):
        """戻るボタンを押したときに前の画面に戻ることを確認"""
        # Given: 2つのメニューウィンドウ（親と子）
        parent_config = {
            'title': 'Parent Menu',
            'buttons': [
                {'id': 'open_child', 'text': 'Open Child', 'action': 'open_child_menu'}
            ]
        }
        child_config = {
            'title': 'Child Menu', 
            'buttons': [
                {'id': 'test', 'text': 'Test', 'action': 'test_action'}
            ]
        }
        
        # 親メニューを作成して表示
        parent_window = self.window_manager.create_window(MenuWindow, 'parent_menu', menu_config=parent_config)
        self.window_manager.show_window(parent_window)
        
        # 子メニューを作成して表示
        child_window = self.window_manager.create_window(MenuWindow, 'child_menu', menu_config=child_config)
        self.window_manager.show_window(child_window)
        
        # When: WindowStackのgo_backメソッドを直接呼び出し
        result = self.window_manager.window_stack.go_back()
        
        # Then: 戻り処理が成功し、親メニューが表示される
        assert result is True
        assert self.window_manager.get_active_window() == parent_window
        assert parent_window.state == WindowState.SHOWN
    
    def test_menu_window_escape_key_returns_to_previous_window(self):
        """ESCキーを押したときに前の画面に戻ることを確認"""
        # Given: 2つのメニューウィンドウ
        parent_config = {
            'title': 'Parent Menu',
            'buttons': [
                {'id': 'test', 'text': 'Test', 'action': 'test'}
            ]
        }
        child_config = {
            'title': 'Child Menu',
            'buttons': [
                {'id': 'test2', 'text': 'Test2', 'action': 'test2'}
            ]
        }
        
        parent_window = self.window_manager.create_window(MenuWindow, 'parent', menu_config=parent_config)
        self.window_manager.show_window(parent_window)
        
        child_window = self.window_manager.create_window(MenuWindow, 'child', menu_config=child_config)
        self.window_manager.show_window(child_window)
        
        # When: ESCキーイベントを処理
        esc_event = Mock()
        esc_event.type = pygame.KEYDOWN
        esc_event.key = pygame.K_ESCAPE
        
        events = [esc_event]
        self.window_manager.handle_global_events(events)
        
        # Then: 親ウィンドウに戻る
        assert self.window_manager.get_active_window() == parent_window
        assert parent_window.state == WindowState.SHOWN
    
    def test_deep_menu_navigation_and_back(self):
        """深い階層のメニューナビゲーションと戻り処理を確認"""
        # Given: 3階層のメニュー
        menu1_config = {
            'title': 'Menu 1',
            'buttons': [{'id': 'to_2', 'text': 'To Menu 2', 'action': 'open_menu_2'}]
        }
        menu2_config = {
            'title': 'Menu 2', 
            'buttons': [{'id': 'to_3', 'text': 'To Menu 3', 'action': 'open_menu_3'}]
        }
        menu3_config = {
            'title': 'Menu 3',
            'buttons': [{'id': 'test', 'text': 'Test', 'action': 'test'}]
        }
        
        # メニューを順番に開く
        menu1 = self.window_manager.create_window(MenuWindow, 'menu1', menu_config=menu1_config)
        self.window_manager.show_window(menu1)
        
        menu2 = self.window_manager.create_window(MenuWindow, 'menu2', menu_config=menu2_config)
        self.window_manager.show_window(menu2)
        
        menu3 = self.window_manager.create_window(MenuWindow, 'menu3', menu_config=menu3_config)
        self.window_manager.show_window(menu3)
        
        # When: menu3から戻る
        self.window_manager.window_stack.go_back()
        
        # Then: menu2が表示される
        assert self.window_manager.get_active_window() == menu2
        
        # When: menu2からも戻る
        self.window_manager.window_stack.go_back()
        
        # Then: menu1が表示される
        assert self.window_manager.get_active_window() == menu1
    
    def test_root_menu_has_no_back_functionality(self):
        """ルートメニューでは戻る機能が動作しないことを確認"""
        # Given: ルートメニュー
        root_config = {
            'title': 'Root Menu',
            'buttons': [
                {'id': 'test', 'text': 'Test', 'action': 'test'}
            ],
            'is_root': True
        }
        
        root_window = self.window_manager.create_window(MenuWindow, 'root', menu_config=root_config)
        self.window_manager.show_window(root_window)
        
        # When: ESCキーを押す
        esc_event = Mock()
        esc_event.type = pygame.KEYDOWN
        esc_event.key = pygame.K_ESCAPE
        
        initial_stack_size = self.window_manager.window_stack.size()
        self.window_manager.handle_global_events([esc_event])
        
        # Then: 何も起こらない（スタックサイズが変わらない）
        assert self.window_manager.window_stack.size() == initial_stack_size
        assert self.window_manager.get_active_window() == root_window
    
    def test_menu_remembers_parent_window_context(self):
        """メニューが親ウィンドウのコンテキストを記憶することを確認"""
        # Given: コンテキスト情報を持つ親メニュー
        parent_config = {
            'title': 'Parent Menu',
            'buttons': [
                {'id': 'open', 'text': 'Open Child', 'action': 'open_child'}
            ]
        }
        
        parent_window = self.window_manager.create_window(
            MenuWindow, 
            'parent',
            menu_config=parent_config
        )
        parent_window.context_data = {'selected_item': 'item_123'}  # コンテキストデータ
        self.window_manager.show_window(parent_window)
        
        # 子メニューを開く
        child_config = {
            'title': 'Child Menu',
            'buttons': [
                {'id': 'action', 'text': 'Action', 'action': 'do_action'}
            ]
        }
        child_window = self.window_manager.create_window(
            MenuWindow,
            'child', 
            menu_config=child_config,
            parent=parent_window
        )
        self.window_manager.show_window(child_window)
        
        # When: 子メニューから戻る
        self.window_manager.window_stack.go_back()
        
        # Then: 親ウィンドウのコンテキストが保持されている
        active_window = self.window_manager.get_active_window()
        assert active_window == parent_window
        assert hasattr(active_window, 'context_data')
        assert active_window.context_data['selected_item'] == 'item_123'