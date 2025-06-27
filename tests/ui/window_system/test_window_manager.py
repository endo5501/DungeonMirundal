"""
WindowManager のテスト

t-wada式TDDによるテストファースト開発
"""

import pytest
import pygame
from unittest.mock import Mock, patch
from src.ui.window_system import WindowManager, Window, WindowState
from .mock_window import MockWindow


class TestWindowManager:
    """WindowManager のテストクラス"""
    
    def setup_method(self):
        """各テストメソッドの前に実行される"""
        # WindowManagerのシングルトンをリセット
        WindowManager._instance = None
        
        # Pygameを初期化（テスト用）
        pygame.init()
        # ダミーディスプレイを設定（テスト用）
        pygame.display.set_mode((1, 1), pygame.NOFRAME)
        
    def teardown_method(self):
        """各テストメソッドの後に実行される"""
        # WindowManagerをクリーンアップ
        if WindowManager._instance:
            WindowManager._instance.cleanup()
            WindowManager._instance = None
        
        pygame.quit()
    
    def test_singleton_pattern(self):
        """シングルトンパターンが正しく動作することを確認"""
        # Given: WindowManagerが存在しない
        
        # When: 2つのインスタンスを取得
        manager1 = WindowManager.get_instance()
        manager2 = WindowManager.get_instance()
        
        # Then: 同じインスタンスが返される
        assert manager1 is manager2
        assert WindowManager._instance is manager1
    
    def test_create_window_with_unique_id(self):
        """一意のIDでウィンドウが作成されることを確認"""
        # Given: WindowManager
        manager = WindowManager.get_instance()
        
        # When: ウィンドウを作成
        window = manager.create_window(MockWindow, window_id="test_window", title="Test")
        
        # Then: ウィンドウが正しく作成され、レジストリに登録される
        assert window.window_id == "test_window"
        assert window in manager.window_registry.values()
        assert manager.statistics_manager.get_counter('windows_created') == 1
    
    def test_create_window_duplicate_id_raises_error(self):
        """重複するIDでウィンドウ作成時にエラーが発生することを確認"""
        # Given: WindowManagerと既存のウィンドウ
        manager = WindowManager.get_instance()
        manager.create_window(MockWindow, window_id="duplicate_id", title="First")
        
        # When: 同じIDでウィンドウを作成しようとする
        # Then: ValueErrorが発生する
        with pytest.raises(ValueError, match="ウィンドウID 'duplicate_id' は既に使用されています"):
            manager.create_window(MockWindow, window_id="duplicate_id", title="Second")
    
    def test_show_window_updates_stack_and_focus(self):
        """ウィンドウ表示時にスタックとフォーカスが更新されることを確認"""
        # Given: WindowManagerとウィンドウ
        manager = WindowManager.get_instance()
        window = manager.create_window(MockWindow, window_id="test_window", title="Test")
        
        # When: ウィンドウを表示
        manager.show_window(window)
        
        # Then: スタックに追加され、フォーカスが設定される
        assert manager.window_stack.peek() == window
        assert manager.focus_manager.get_focused_window() == window
        assert window.state == WindowState.SHOWN
    
    def test_hide_window_removes_from_stack(self):
        """ウィンドウ非表示時にスタックから削除されることを確認"""
        # Given: 表示されているウィンドウ
        manager = WindowManager.get_instance()
        window = manager.create_window(MockWindow, window_id="test_window", title="Test")
        manager.show_window(window)
        
        # When: ウィンドウを非表示
        manager.hide_window(window)
        
        # Then: スタックから削除され、状態が更新される
        assert manager.window_stack.peek() != window
        assert window.state == WindowState.HIDDEN
    
    def test_close_window_destroys_and_cleans_up(self):
        """ウィンドウクローズ時に適切に破棄・クリーンアップされることを確認"""
        # Given: 表示されているウィンドウ
        manager = WindowManager.get_instance()
        window = manager.create_window(MockWindow, window_id="test_window", title="Test")
        manager.show_window(window)
        
        # When: ウィンドウを閉じる
        manager.close_window(window)
        
        # Then: レジストリから削除され、破棄される
        assert window.window_id not in manager.window_registry
        assert window.state == WindowState.DESTROYED
        assert manager.statistics_manager.get_counter('windows_destroyed') == 1
    
    def test_modal_window_locks_focus(self):
        """モーダルウィンドウがフォーカスをロックすることを確認"""
        # Given: WindowManagerと通常ウィンドウ
        manager = WindowManager.get_instance()
        normal_window = manager.create_window(MockWindow, window_id="normal", title="Normal")
        manager.show_window(normal_window)
        
        # When: モーダルウィンドウを表示
        modal_window = manager.create_window(MockWindow, window_id="modal", title="Modal", modal=True)
        manager.show_window(modal_window)
        
        # Then: フォーカスがロックされる
        assert manager.focus_manager.is_focus_locked()
        assert manager.focus_manager.get_focused_window() == modal_window
    
    def test_go_back_returns_to_previous_window(self):
        """戻る操作で前のウィンドウに戻ることを確認"""
        # Given: 複数のウィンドウが表示されている
        manager = WindowManager.get_instance()
        window1 = manager.create_window(MockWindow, window_id="window1", title="Window 1")
        window2 = manager.create_window(MockWindow, window_id="window2", title="Window 2")
        
        manager.show_window(window1)
        manager.show_window(window2)
        
        # When: 戻る操作を実行
        result = manager.go_back()
        
        # Then: 前のウィンドウがアクティブになる
        assert result is True
        assert manager.get_active_window() == window1
        assert window2.state == WindowState.DESTROYED
    
    def test_go_back_to_root_clears_stack_to_first_window(self):
        """ルートまで戻る操作でスタックが最初のウィンドウまでクリアされることを確認"""
        # Given: 複数階層のウィンドウ
        manager = WindowManager.get_instance()
        root = manager.create_window(MockWindow, window_id="root", title="Root")
        child1 = manager.create_window(MockWindow, window_id="child1", title="Child 1")
        child2 = manager.create_window(MockWindow, window_id="child2", title="Child 2")
        
        manager.show_window(root)
        manager.show_window(child1)
        manager.show_window(child2)
        
        # When: ルートまで戻る
        result = manager.go_back_to_root()
        
        # Then: ルートウィンドウのみが残る
        assert result is True
        assert manager.get_active_window() == root
        assert manager.window_stack.size() == 1
    
    def test_statistics_are_tracked_correctly(self):
        """統計情報が正しく追跡されることを確認"""
        # Given: WindowManager
        manager = WindowManager.get_instance()
        
        # When: ウィンドウの作成・破棄を行う
        window1 = manager.create_window(MockWindow, window_id="window1", title="Window 1")
        window2 = manager.create_window(MockWindow, window_id="window2", title="Window 2")
        manager.destroy_window(window1)
        
        # Then: 統計情報が正しく更新される
        stats = manager.get_statistics()
        assert stats['windows_created'] == 2
        assert stats['windows_destroyed'] == 1
        assert stats['total_windows'] == 1  # window2のみ残っている
    
    def test_debug_mode_can_be_toggled(self):
        """デバッグモードの切り替えができることを確認"""
        # Given: WindowManager
        manager = WindowManager.get_instance()
        
        # When: デバッグモードを有効にする
        manager.set_debug_mode(True)
        
        # Then: デバッグモードが有効になる
        assert manager.debug_mode is True
        assert manager.event_router.debug_mode is True
        
        # When: デバッグモードを無効にする
        manager.set_debug_mode(False)
        
        # Then: デバッグモードが無効になる
        assert manager.debug_mode is False
        assert manager.event_router.debug_mode is False
    
    def test_system_state_validation_detects_issues(self):
        """システム状態の検証で問題が検出されることを確認"""
        # Given: WindowManagerと問題のある状態
        manager = WindowManager.get_instance()
        window = manager.create_window(MockWindow, window_id="test", title="Test")
        manager.show_window(window)
        
        # When: ウィンドウを強制的に破棄状態にする（問題のある状態を作る）
        window.state = WindowState.DESTROYED
        
        # Then: 検証で問題が検出される
        issues = manager.validate_system_state()
        assert len(issues) > 0
        assert any("破棄されたウィンドウ" in issue for issue in issues)
    
    def test_cleanup_removes_all_windows(self):
        """クリーンアップで全ウィンドウが削除されることを確認"""
        # Given: 複数のウィンドウが存在する
        manager = WindowManager.get_instance()
        window1 = manager.create_window(MockWindow, window_id="window1", title="Window 1")
        window2 = manager.create_window(MockWindow, window_id="window2", title="Window 2")
        manager.show_window(window1)
        manager.show_window(window2)
        
        # When: クリーンアップを実行
        manager.cleanup()
        
        # Then: 全ウィンドウが削除される
        assert len(manager.window_registry) == 0
        assert manager.window_stack.size() == 0
        assert manager.focus_manager.get_focused_window() is None
        assert manager.running is False