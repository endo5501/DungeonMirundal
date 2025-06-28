"""
Window System 統合テスト

各コンポーネントの連携動作を確認
"""

import pytest
import pygame
import pygame_gui
from unittest.mock import Mock, patch
from src.ui.window_system import (
    WindowManager, MenuWindow, DialogWindow, 
    DialogType, DialogResult, WindowState
)


class TestWindowSystemIntegration:
    """Window System統合テストクラス"""
    
    def setup_method(self):
        """各テストメソッドの前に実行される"""
        # WindowManagerのシングルトンをリセット
        WindowManager._instance = None
        
        pygame.init()
        pygame.display.set_mode((1, 1), pygame.NOFRAME)
    
    def teardown_method(self):
        """各テストメソッドの後に実行される"""
        if WindowManager._instance:
            WindowManager._instance.cleanup()
            WindowManager._instance = None
        
        pygame.quit()
    
    def test_menu_and_dialog_window_integration(self):
        """MenuWindowとDialogWindowの統合動作を確認"""
        # Given: WindowManagerとMenuWindow
        manager = WindowManager.get_instance()
        
        menu_config = {
            'title': 'Main Menu',
            'buttons': [
                {'id': 'new_game', 'text': 'New Game', 'action': 'new_game'},
                {'id': 'quit', 'text': 'Quit', 'action': 'quit_game'}
            ]
        }
        
        menu_window = manager.create_window(MenuWindow, 'main_menu', menu_config=menu_config)
        manager.show_window(menu_window)
        
        # When: Quitボタンをクリックして確認ダイアログを表示
        quit_dialog = manager.create_window(
            DialogWindow, 
            'quit_confirm', 
            dialog_type=DialogType.CONFIRMATION, 
            message="Are you sure you want to quit?",
            parent=menu_window
        )
        manager.show_window(quit_dialog)
        
        # Then: 適切な階層とフォーカス状態が維持される
        assert manager.get_active_window() == quit_dialog
        assert manager.focus_manager.get_focused_window() == quit_dialog
        assert manager.focus_manager.is_focus_locked()  # モーダルダイアログでロック
        assert manager.window_stack.size() == 2
        
        # When: ダイアログでYesを選択
        yes_button = next(btn for btn in quit_dialog.buttons if btn.result == DialogResult.YES)
        mock_event = Mock()
        mock_event.type = pygame_gui.UI_BUTTON_PRESSED
        mock_event.ui_element = yes_button.ui_element
        
        with patch.object(quit_dialog, 'send_message') as mock_send:
            quit_dialog.handle_event(mock_event)
        
        # Then: 適切なメッセージが送信される
        assert quit_dialog.result == DialogResult.YES
        assert mock_send.call_count == 2
        mock_send.assert_any_call('dialog_result', {'result': DialogResult.YES, 'data': None})
        mock_send.assert_any_call('close_requested')
    
    def test_modal_dialog_focus_management(self):
        """モーダルダイアログのフォーカス管理を確認"""
        # Given: 複数のウィンドウとモーダルダイアログ
        manager = WindowManager.get_instance()
        
        # 基本メニュー
        menu_config = {'title': 'Test', 'buttons': [{'id': 'btn', 'text': 'Button', 'action': 'action'}]}
        menu_window = manager.create_window(MenuWindow, 'menu', menu_config=menu_config)
        manager.show_window(menu_window)
        
        # モーダルダイアログ
        dialog = manager.create_window(DialogWindow, 'dialog', dialog_type=DialogType.INFORMATION, message="Test message")
        manager.show_window(dialog)
        
        # Then: フォーカスがダイアログにロックされる
        assert manager.focus_manager.is_focus_locked()
        assert manager.focus_manager.get_focused_window() == dialog
        
        # When: メニューに直接フォーカスを設定しようとする
        focus_result = manager.focus_manager.set_focus(menu_window)
        
        # Then: フォーカス変更が拒否される
        assert focus_result is False
        assert manager.focus_manager.get_focused_window() == dialog
        
        # When: ダイアログを閉じる
        manager.close_window(dialog)
        
        # Then: フォーカスロックが解除され、メニューにフォーカスが戻る
        assert not manager.focus_manager.is_focus_locked()
        assert manager.focus_manager.get_focused_window() == menu_window
    
    def test_window_hierarchy_navigation(self):
        """ウィンドウ階層のナビゲーションを確認"""
        # Given: 複数階層のウィンドウ
        manager = WindowManager.get_instance()
        
        # Root window
        root_config = {'title': 'Root', 'buttons': [{'id': 'sub', 'text': 'Sub Menu', 'action': 'sub'}]}
        root_window = manager.create_window(MenuWindow, 'root', menu_config=root_config)
        manager.show_window(root_window)
        
        # Sub menu
        sub_config = {'title': 'Sub', 'buttons': [{'id': 'item', 'text': 'Item', 'action': 'item'}]}
        sub_window = manager.create_window(MenuWindow, 'sub', menu_config=sub_config, parent=root_window)
        manager.show_window(sub_window)
        
        # Dialog
        dialog = manager.create_window(DialogWindow, 'confirm', dialog_type=DialogType.CONFIRMATION, message="Confirm?", parent=sub_window)
        manager.show_window(dialog)
        
        # Then: 正しい階層が形成される
        assert manager.window_stack.size() == 3
        assert manager.get_active_window() == dialog
        assert dialog.parent == sub_window
        assert sub_window.parent == root_window
        
        # When: ESCキーで戻る
        manager.go_back()  # dialog -> sub
        
        # Then: 一つ前のウィンドウに戻る
        assert manager.window_stack.size() == 2
        assert manager.get_active_window() == sub_window
        
        # When: ルートまで戻る
        manager.go_back_to_root()
        
        # Then: ルートウィンドウのみ残る
        assert manager.window_stack.size() == 1
        assert manager.get_active_window() == root_window
    
    def test_keyboard_navigation_across_windows(self):
        """ウィンドウ間のキーボードナビゲーションを確認"""
        # Given: MenuWindowとキーボードイベント
        manager = WindowManager.get_instance()
        
        menu_config = {
            'title': 'Navigation Test',
            'buttons': [
                {'id': 'btn1', 'text': 'Button 1', 'action': 'action1'},
                {'id': 'btn2', 'text': 'Button 2', 'action': 'action2'},
                {'id': 'btn3', 'text': 'Button 3', 'action': 'action3'}
            ]
        }
        
        menu_window = manager.create_window(MenuWindow, 'nav_menu', menu_config=menu_config)
        manager.show_window(menu_window)
        
        # When: 下矢印キーを押す
        down_event = Mock()
        down_event.type = pygame.KEYDOWN
        down_event.key = pygame.K_DOWN
        
        manager.handle_global_events([down_event])
        
        # Then: メニューの選択が更新される
        assert menu_window.selected_button_index == 1
        
        # When: Enterキーを押す
        enter_event = Mock()
        enter_event.type = pygame.KEYDOWN
        enter_event.key = pygame.K_RETURN
        
        with patch.object(menu_window, 'send_message') as mock_send:
            manager.handle_global_events([enter_event])
        
        # Then: 選択されたボタンのアクションが実行される
        mock_send.assert_called_once_with('menu_action', {'action': 'action2', 'button_id': 'btn2'})
    
    def test_window_cleanup_cascades_to_children(self):
        """親ウィンドウの削除が子ウィンドウにカスケードすることを確認"""
        # Given: 親子関係のあるウィンドウ
        manager = WindowManager.get_instance()
        
        parent_config = {'title': 'Parent', 'buttons': [{'id': 'btn', 'text': 'Button', 'action': 'action'}]}
        parent_window = manager.create_window(MenuWindow, 'parent', menu_config=parent_config)
        manager.show_window(parent_window)
        
        child_dialog = manager.create_window(DialogWindow, 'child', dialog_type=DialogType.INFORMATION, message="Child", parent=parent_window)
        manager.show_window(child_dialog)
        
        grandchild_dialog = manager.create_window(DialogWindow, 'grandchild', dialog_type=DialogType.INFORMATION, message="Grandchild", parent=child_dialog)
        manager.show_window(grandchild_dialog)
        
        # When: 親ウィンドウを破棄
        manager.destroy_window(parent_window)
        
        # Then: 子・孫ウィンドウも破棄される
        assert parent_window.state == WindowState.DESTROYED
        assert child_dialog.state == WindowState.DESTROYED
        assert grandchild_dialog.state == WindowState.DESTROYED
        
        # レジストリからも削除される
        assert 'parent' not in manager.window_registry
        assert 'child' not in manager.window_registry
        assert 'grandchild' not in manager.window_registry
    
    def test_statistics_tracking_across_operations(self):
        """各種操作での統計情報追跡を確認"""
        # Given: WindowManager
        manager = WindowManager.get_instance()
        
        # When: 複数のウィンドウを作成・操作
        menu_config = {'title': 'Stats Test', 'buttons': [{'id': 'btn', 'text': 'Button', 'action': 'action'}]}
        menu1 = manager.create_window(MenuWindow, 'menu1', menu_config=menu_config)
        menu2 = manager.create_window(MenuWindow, 'menu2', menu_config=menu_config)
        dialog1 = manager.create_window(DialogWindow, 'dialog1', dialog_type=DialogType.INFORMATION, message="Test")
        
        manager.show_window(menu1)
        manager.show_window(dialog1)
        
        # イベント処理をシミュレート
        mock_events = [Mock() for _ in range(5)]
        for event in mock_events:
            event.type = pygame.KEYDOWN
            event.key = pygame.K_SPACE
        
        manager.handle_global_events(mock_events)
        
        # 描画をシミュレート
        mock_surface = Mock()
        for _ in range(3):
            manager.draw(mock_surface)
        
        # ウィンドウを破棄
        manager.destroy_window(menu2)
        
        # Then: 統計情報が正しく記録される
        stats = manager.get_statistics()
        assert stats['windows_created'] == 3
        assert stats['windows_destroyed'] == 1
        assert stats['events_processed'] == 5
        assert stats['frames_rendered'] == 3
        assert stats['total_windows'] == 2  # menu1, dialog1
        assert stats['active_windows'] == 2
    
    def test_error_handling_and_recovery(self):
        """エラーハンドリングと復旧機能を確認"""
        # Given: WindowManager
        manager = WindowManager.get_instance()
        
        # When: 無効なウィンドウを操作しようとする
        fake_window = Mock()
        fake_window.window_id = 'fake'
        fake_window.state = WindowState.DESTROYED
        
        # Then: エラーが適切に処理される
        result = manager.window_stack.remove_window(fake_window)
        assert result is False
        
        # When: システム状態を検証
        issues = manager.validate_system_state()
        
        # Then: 問題が検出されない（健全な状態）
        assert len(issues) == 0
        
        # When: デバッグ情報を取得
        debug_info = manager.get_debug_info()
        
        # Then: デバッグ情報が取得できる
        assert len(debug_info) > 0
        assert any("WindowManager Statistics" in line for line in debug_info)