"""
FocusManager のテスト

t-wada式TDDによるテストファースト開発
"""

import pytest
from unittest.mock import Mock
from src.ui.window_system import FocusManager, Window, WindowState
from src.ui.window_system.focus_manager import FocusChange


class MockWindow(Window):
    """テスト用のモックウィンドウ"""
    
    def __init__(self, window_id: str, parent=None, modal=False):
        super().__init__(window_id, parent, modal)
        
    def create(self):
        pass
        
    def handle_event(self, event):
        return False


class TestFocusManager:
    """FocusManager のテストクラス"""
    
    def setup_method(self):
        """各テストメソッドの前に実行される"""
        self.focus_manager = FocusManager()
    
    def test_initial_state_has_no_focus(self):
        """初期状態でフォーカスがないことを確認"""
        # Given: 新しいFocusManager
        
        # When: 初期状態をチェック
        focused = self.focus_manager.get_focused_window()
        locked = self.focus_manager.is_focus_locked()
        
        # Then: フォーカスがない状態
        assert focused is None
        assert locked is False
    
    def test_set_focus_to_valid_window(self):
        """有効なウィンドウにフォーカスを設定できることを確認"""
        # Given: 表示状態のウィンドウ
        window = MockWindow("test_window")
        window.state = WindowState.SHOWN
        
        # When: フォーカスを設定
        result = self.focus_manager.set_focus(window)
        
        # Then: フォーカスが設定される
        assert result is True
        assert self.focus_manager.get_focused_window() == window
        assert len(self.focus_manager.focus_history) == 1
    
    def test_set_focus_to_hidden_window_fails(self):
        """非表示ウィンドウへのフォーカス設定が失敗することを確認"""
        # Given: 非表示状態のウィンドウ
        window = MockWindow("hidden_window")
        window.state = WindowState.HIDDEN
        
        # When: フォーカスを設定しようとする
        result = self.focus_manager.set_focus(window)
        
        # Then: フォーカス設定が失敗する
        assert result is False
        assert self.focus_manager.get_focused_window() is None
    
    def test_set_focus_to_destroyed_window_fails(self):
        """破棄されたウィンドウへのフォーカス設定が失敗することを確認"""
        # Given: 破棄状態のウィンドウ
        window = MockWindow("destroyed_window")
        window.state = WindowState.DESTROYED
        
        # When: フォーカスを設定しようとする
        result = self.focus_manager.set_focus(window)
        
        # Then: フォーカス設定が失敗する
        assert result is False
        assert self.focus_manager.get_focused_window() is None
    
    def test_clear_focus_removes_current_focus(self):
        """フォーカスクリアで現在のフォーカスが削除されることを確認"""
        # Given: フォーカスされているウィンドウ
        window = MockWindow("focused_window")
        window.state = WindowState.SHOWN
        self.focus_manager.set_focus(window)
        
        # When: フォーカスをクリア
        self.focus_manager.clear_focus()
        
        # Then: フォーカスがなくなる
        assert self.focus_manager.get_focused_window() is None
    
    def test_lock_focus_prevents_focus_change(self):
        """フォーカスロックがフォーカス変更を防ぐことを確認"""
        # Given: フォーカスされているウィンドウ
        window1 = MockWindow("window1")
        window2 = MockWindow("window2")
        window1.state = WindowState.SHOWN
        window2.state = WindowState.SHOWN
        
        self.focus_manager.set_focus(window1)
        
        # When: フォーカスをロックし、別のウィンドウにフォーカスを設定しようとする
        self.focus_manager.lock_focus()
        result = self.focus_manager.set_focus(window2)
        
        # Then: フォーカス変更が失敗する
        assert result is False
        assert self.focus_manager.get_focused_window() == window1
        assert self.focus_manager.is_focus_locked() is True
    
    def test_lock_focus_allows_focus_to_locked_window(self):
        """フォーカスロック中でもロック対象ウィンドウへのフォーカスは許可されることを確認"""
        # Given: フォーカスロックされた状態
        window = MockWindow("locked_window")
        window.state = WindowState.SHOWN
        self.focus_manager.set_focus(window)
        self.focus_manager.lock_focus(window)
        
        # When: ロック対象と同じウィンドウにフォーカスを設定
        result = self.focus_manager.set_focus(window)
        
        # Then: フォーカス設定が成功する
        assert result is True
        assert self.focus_manager.get_focused_window() == window
    
    def test_unlock_focus_restores_normal_behavior(self):
        """フォーカスロック解除で通常動作が復旧することを確認"""
        # Given: フォーカスロックされた状態
        window1 = MockWindow("window1")
        window2 = MockWindow("window2")
        window1.state = WindowState.SHOWN
        window2.state = WindowState.SHOWN
        
        self.focus_manager.set_focus(window1)
        self.focus_manager.lock_focus()
        
        # When: フォーカスロックを解除し、別のウィンドウにフォーカスを設定
        self.focus_manager.unlock_focus()
        result = self.focus_manager.set_focus(window2)
        
        # Then: フォーカス変更が成功する
        assert result is True
        assert self.focus_manager.get_focused_window() == window2
        assert self.focus_manager.is_focus_locked() is False
    
    def test_focus_change_history_is_recorded(self):
        """フォーカス変更履歴が記録されることを確認"""
        # Given: 複数のウィンドウ
        window1 = MockWindow("window1")
        window2 = MockWindow("window2")
        window3 = MockWindow("window3")
        
        for window in [window1, window2, window3]:
            window.state = WindowState.SHOWN
        
        # When: フォーカスを順次変更
        self.focus_manager.set_focus(window1)
        self.focus_manager.set_focus(window2)
        self.focus_manager.set_focus(window3)
        
        # Then: 履歴が正しく記録される
        history = self.focus_manager.get_focus_history()
        assert len(history) == 3
        assert history[-1].new_window == window3
        assert history[-2].new_window == window2
        assert history[-3].new_window == window1
    
    def test_focus_change_listeners_are_notified(self):
        """フォーカス変更リスナーが通知されることを確認"""
        # Given: フォーカス変更リスナー
        listener_calls = []
        
        def mock_listener(change: FocusChange):
            listener_calls.append(change)
        
        self.focus_manager.add_focus_change_listener(mock_listener)
        
        # When: フォーカスを変更
        window = MockWindow("test_window")
        window.state = WindowState.SHOWN
        self.focus_manager.set_focus(window)
        
        # Then: リスナーが呼び出される
        assert len(listener_calls) == 1
        assert listener_calls[0].new_window == window
    
    def test_cleanup_destroyed_windows_removes_invalid_focus(self):
        """破棄されたウィンドウのクリーンアップで無効なフォーカスが削除されることを確認"""
        # Given: フォーカスされているウィンドウを破棄状態にする
        window = MockWindow("window_to_destroy")
        window.state = WindowState.SHOWN
        self.focus_manager.set_focus(window)
        
        # ウィンドウを破棄状態にする
        window.state = WindowState.DESTROYED
        
        # When: クリーンアップを実行
        self.focus_manager.cleanup_destroyed_windows()
        
        # Then: フォーカスがクリアされる
        assert self.focus_manager.get_focused_window() is None
    
    def test_cleanup_destroyed_windows_unlocks_invalid_lock(self):
        """破棄されたウィンドウのクリーンアップで無効なロックが解除されることを確認"""
        # Given: ロックされているウィンドウを破棄状態にする
        window = MockWindow("locked_window")
        window.state = WindowState.SHOWN
        self.focus_manager.set_focus(window)
        self.focus_manager.lock_focus(window)
        
        # ウィンドウを破棄状態にする
        window.state = WindowState.DESTROYED
        
        # When: クリーンアップを実行
        self.focus_manager.cleanup_destroyed_windows()
        
        # Then: ロックが解除される
        assert self.focus_manager.is_focus_locked() is False
    
    def test_validate_focus_state_detects_issues(self):
        """フォーカス状態検証で問題が検出されることを確認"""
        # Given: 問題のあるフォーカス状態
        window = MockWindow("invalid_window")
        window.state = WindowState.DESTROYED
        
        # 無効な状態を強制的に設定
        self.focus_manager.current_focus = window
        
        # When: 状態を検証
        issues = self.focus_manager.validate_focus_state()
        
        # Then: 問題が検出される
        assert len(issues) > 0
        assert any("破棄されたウィンドウ" in issue for issue in issues)
    
    def test_reset_clears_all_state(self):
        """リセットで全状態がクリアされることを確認"""
        # Given: 設定済みのフォーカス状態
        window = MockWindow("test_window")
        window.state = WindowState.SHOWN
        self.focus_manager.set_focus(window)
        self.focus_manager.lock_focus()
        
        # When: リセットを実行
        self.focus_manager.reset()
        
        # Then: 全状態がクリアされる
        assert self.focus_manager.get_focused_window() is None
        assert self.focus_manager.is_focus_locked() is False
        assert len(self.focus_manager.focus_history) == 0
    
    def test_focus_change_object_stores_correct_data(self):
        """FocusChangeオブジェクトが正しいデータを保存することを確認"""
        # Given: 2つのウィンドウ
        old_window = MockWindow("old_window")
        new_window = MockWindow("new_window")
        
        # When: FocusChangeオブジェクトを作成
        change = FocusChange(old_window, new_window)
        
        # Then: 正しいデータが保存される
        assert change.old_window == old_window
        assert change.new_window == new_window
        assert change.old_window_id == "old_window"
        assert change.new_window_id == "new_window"
        assert change.timestamp is not None