"""
WindowStack のテスト

t-wada式TDDによるテストファースト開発
"""

import pytest
from unittest.mock import Mock
from src.ui.window_system import WindowStack, Window, WindowState


class MockWindow(Window):
    """テスト用のモックウィンドウ"""
    
    def __init__(self, window_id: str, parent=None, modal=False):
        super().__init__(window_id, parent, modal)
        
    def create(self):
        pass
        
    def handle_event(self, event):
        return False


class TestWindowStack:
    """WindowStack のテストクラス"""
    
    def setup_method(self):
        """各テストメソッドの前に実行される"""
        self.stack = WindowStack()
    
    def test_empty_stack_peek_returns_none(self):
        """空のスタックでpeekするとNoneが返されることを確認"""
        # Given: 空のWindowStack
        
        # When: peekを実行
        result = self.stack.peek()
        
        # Then: Noneが返される
        assert result is None
        assert self.stack.is_empty() is True
        assert self.stack.size() == 0
    
    def test_push_window_adds_to_stack(self):
        """ウィンドウのプッシュでスタックに追加されることを確認"""
        # Given: WindowStackとウィンドウ
        window = MockWindow("test_window")
        window.state = WindowState.CREATED
        
        # When: ウィンドウをプッシュ
        self.stack.push(window)
        
        # Then: スタックに追加される
        assert self.stack.peek() == window
        assert self.stack.size() == 1
        assert window in self.stack
    
    def test_push_duplicate_window_ignored(self):
        """重複するウィンドウのプッシュが無視されることを確認"""
        # Given: スタックに既に存在するウィンドウ
        window = MockWindow("test_window")
        window.state = WindowState.CREATED
        self.stack.push(window)
        
        # When: 同じウィンドウを再度プッシュ
        self.stack.push(window)
        
        # Then: サイズは変わらない
        assert self.stack.size() == 1
    
    def test_pop_removes_and_returns_top_window(self):
        """ポップでトップウィンドウが削除・返却されることを確認"""
        # Given: ウィンドウが入ったスタック
        window1 = MockWindow("window1")
        window2 = MockWindow("window2")
        window1.state = WindowState.SHOWN
        window2.state = WindowState.SHOWN
        
        self.stack.push(window1)
        self.stack.push(window2)
        
        # When: ポップを実行
        popped = self.stack.pop()
        
        # Then: トップウィンドウが返され、履歴に追加される
        assert popped == window2
        assert self.stack.peek() == window1
        assert self.stack.size() == 1
        assert window2 in self.stack.history
    
    def test_pop_empty_stack_returns_none(self):
        """空のスタックでポップするとNoneが返されることを確認"""
        # Given: 空のWindowStack
        
        # When: ポップを実行
        result = self.stack.pop()
        
        # Then: Noneが返される
        assert result is None
    
    def test_find_window_by_id(self):
        """IDによるウィンドウ検索が正しく動作することを確認"""
        # Given: 複数のウィンドウが入ったスタック
        window1 = MockWindow("window1")
        window2 = MockWindow("window2")
        window3 = MockWindow("window3")
        
        self.stack.push(window1)
        self.stack.push(window2)
        self.stack.push(window3)
        
        # When: IDでウィンドウを検索
        found = self.stack.find_window("window2")
        not_found = self.stack.find_window("nonexistent")
        
        # Then: 正しい結果が返される
        assert found == window2
        assert not_found is None
    
    def test_remove_window_from_middle_of_stack(self):
        """スタック中央のウィンドウ削除が正しく動作することを確認"""
        # Given: 3つのウィンドウが入ったスタック
        window1 = MockWindow("window1")
        window2 = MockWindow("window2")
        window3 = MockWindow("window3")
        window2.state = WindowState.SHOWN
        
        self.stack.push(window1)
        self.stack.push(window2)
        self.stack.push(window3)
        
        # When: 中央のウィンドウを削除
        result = self.stack.remove_window(window2)
        
        # Then: 削除に成功し、スタックが正しく更新される
        assert result is True
        assert window2 not in self.stack
        assert self.stack.size() == 2
        assert window2.state == WindowState.HIDDEN
    
    def test_go_back_closes_top_window(self):
        """戻る操作でトップウィンドウが閉じられることを確認"""
        # Given: 複数のウィンドウが入ったスタック
        window1 = MockWindow("window1")
        window2 = MockWindow("window2")
        window1.state = WindowState.SHOWN
        window2.state = WindowState.SHOWN
        
        self.stack.push(window1)
        self.stack.push(window2)
        
        # When: 戻る操作を実行
        result = self.stack.go_back()
        
        # Then: トップウィンドウが削除され、前のウィンドウがアクティブになる
        assert result is True
        assert self.stack.peek() == window1
        assert self.stack.size() == 1
    
    def test_go_back_on_single_window_returns_false(self):
        """単一ウィンドウで戻る操作が失敗することを確認"""
        # Given: ウィンドウが1つだけのスタック
        window = MockWindow("single_window")
        self.stack.push(window)
        
        # When: 戻る操作を実行
        result = self.stack.go_back()
        
        # Then: 失敗が返される
        assert result is False
        assert self.stack.size() == 1
    
    def test_go_back_to_root_keeps_only_first_window(self):
        """ルートまで戻る操作で最初のウィンドウのみが残ることを確認"""
        # Given: 複数階層のウィンドウ
        root = MockWindow("root")
        child1 = MockWindow("child1")
        child2 = MockWindow("child2")
        child3 = MockWindow("child3")
        
        child1.state = WindowState.SHOWN
        child2.state = WindowState.SHOWN
        child3.state = WindowState.SHOWN
        
        self.stack.push(root)
        self.stack.push(child1)
        self.stack.push(child2)
        self.stack.push(child3)
        
        # When: ルートまで戻る
        result = self.stack.go_back_to_root()
        
        # Then: ルートウィンドウのみが残る
        assert result is True
        assert self.stack.peek() == root
        assert self.stack.size() == 1
    
    def test_go_back_to_specific_window(self):
        """特定のウィンドウまで戻る操作が正しく動作することを確認"""
        # Given: 複数階層のウィンドウ
        window1 = MockWindow("window1")
        window2 = MockWindow("window2")
        window3 = MockWindow("window3")
        window4 = MockWindow("window4")
        
        window3.state = WindowState.SHOWN
        window4.state = WindowState.SHOWN
        
        self.stack.push(window1)
        self.stack.push(window2)
        self.stack.push(window3)
        self.stack.push(window4)
        
        # When: 特定のウィンドウまで戻る
        result = self.stack.go_back_to_window("window2")
        
        # Then: 指定されたウィンドウまで戻る
        assert result is True
        assert self.stack.peek() == window2
        assert self.stack.size() == 2
    
    def test_go_back_to_nonexistent_window_returns_false(self):
        """存在しないウィンドウまで戻る操作が失敗することを確認"""
        # Given: ウィンドウが入ったスタック
        window = MockWindow("existing_window")
        self.stack.push(window)
        
        # When: 存在しないウィンドウまで戻ろうとする
        result = self.stack.go_back_to_window("nonexistent")
        
        # Then: 失敗が返される
        assert result is False
        assert self.stack.size() == 1
    
    def test_clear_removes_all_windows(self):
        """クリア操作で全ウィンドウが削除されることを確認"""
        # Given: 複数のウィンドウが入ったスタック
        window1 = MockWindow("window1")
        window2 = MockWindow("window2")
        window3 = MockWindow("window3")
        
        window1.state = WindowState.SHOWN
        window2.state = WindowState.SHOWN
        window3.state = WindowState.SHOWN
        
        self.stack.push(window1)
        self.stack.push(window2)
        self.stack.push(window3)
        
        # When: クリアを実行
        self.stack.clear()
        
        # Then: 全ウィンドウが削除される
        assert self.stack.is_empty()
        assert self.stack.size() == 0
        assert self.stack.peek() is None
    
    def test_get_stack_trace_returns_correct_format(self):
        """スタックトレースが正しい形式で返されることを確認"""
        # Given: 複数のウィンドウが入ったスタック
        window1 = MockWindow("window1")
        window2 = MockWindow("window2", modal=True)
        window3 = MockWindow("window3")
        
        self.stack.push(window1)
        self.stack.push(window2)
        self.stack.push(window3)
        
        # When: スタックトレースを取得
        trace = self.stack.get_stack_trace()
        
        # Then: 正しい形式で返される
        assert len(trace) == 3
        assert "→" in trace[2]  # トップウィンドウに矢印
        assert "[M]" in trace[1]  # モーダルウィンドウにマーク
        assert "window1" in trace[0]
        assert "window2" in trace[1]
        assert "window3" in trace[2]
    
    def test_validate_stack_detects_issues(self):
        """スタック検証で問題が検出されることを確認"""
        # Given: 問題のあるスタック状態
        window1 = MockWindow("window1")
        window2 = MockWindow("duplicate_id")
        window3 = MockWindow("duplicate_id")  # 重複ID
        
        # スタックに直接追加（通常のpushメソッドを迂回）
        self.stack.stack = [window1, window2, window3]
        
        # When: スタックを検証
        issues = self.stack.validate_stack()
        
        # Then: 問題が検出される
        assert len(issues) > 0
        assert any("重複" in issue for issue in issues)