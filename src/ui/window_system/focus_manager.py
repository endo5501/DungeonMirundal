"""
FocusManager クラス

フォーカス管理とイベント制御を行う
"""

from typing import Optional, List, Callable
from datetime import datetime
from src.utils.logger import logger
from .window import Window, WindowState


class FocusChange:
    """フォーカス変更の記録"""
    def __init__(self, old_window: Optional[Window], new_window: Optional[Window], timestamp: datetime = None):
        self.old_window = old_window
        self.new_window = new_window
        self.timestamp = timestamp or datetime.now()
        self.old_window_id = old_window.window_id if old_window else None
        self.new_window_id = new_window.window_id if new_window else None


class FocusManager:
    """
    フォーカス管理クラス
    
    明確なフォーカス制御とイベント分配を行う：
    - アクティブウィンドウの管理
    - フォーカスロック機能（モーダルダイアログ用）
    - フォーカス変更の履歴管理
    - デバッグ・監視機能
    """
    
    def __init__(self):
        """フォーカスマネージャーを初期化"""
        self.current_focus: Optional[Window] = None
        self.focus_locked: bool = False
        self.locked_window: Optional[Window] = None
        
        # フォーカス履歴
        self.focus_history: List[FocusChange] = []
        self.max_history_size = 100
        
        # イベントリスナー
        self.focus_change_listeners: List[Callable[[FocusChange], None]] = []
        
        logger.debug("FocusManagerを初期化しました")
    
    def set_focus(self, window: Optional[Window]) -> bool:
        """
        フォーカスを設定
        
        Args:
            window: フォーカスを設定するウィンドウ（Noneでフォーカスクリア）
            
        Returns:
            bool: フォーカス設定に成功した場合True
        """
        # フォーカスロック中の場合
        if self.focus_locked:
            if window != self.locked_window:
                logger.debug(f"フォーカスがロックされています: {self.locked_window.window_id if self.locked_window else 'None'}")
                return False
        
        # 現在のフォーカスと同じ場合は何もしない
        if self.current_focus == window:
            return True
        
        # ウィンドウがフォーカスを受け取れるかチェック
        if window and not self.can_receive_focus(window):
            logger.debug(f"ウィンドウはフォーカスを受け取れません: {window.window_id}")
            return False
        
        # フォーカス変更を記録
        old_focus = self.current_focus
        self.current_focus = window
        
        # 履歴に追加
        focus_change = FocusChange(old_focus, window)
        self.focus_history.append(focus_change)
        if len(self.focus_history) > self.max_history_size:
            self.focus_history.pop(0)
        
        # イベントリスナーに通知
        for listener in self.focus_change_listeners:
            try:
                listener(focus_change)
            except Exception as e:
                logger.error(f"フォーカス変更リスナーでエラー: {e}")
        
        # ログ出力
        old_id = old_focus.window_id if old_focus else "None"
        new_id = window.window_id if window else "None"
        logger.debug(f"フォーカス変更: {old_id} → {new_id}")
        
        return True
    
    def clear_focus(self) -> None:
        """フォーカスをクリア"""
        self.set_focus(None)
    
    def get_focused_window(self) -> Optional[Window]:
        """
        現在フォーカスされているウィンドウを取得
        
        Returns:
            Optional[Window]: フォーカスされているウィンドウ
        """
        return self.current_focus
    
    def lock_focus(self, window: Optional[Window] = None) -> None:
        """
        フォーカスをロック（モーダルダイアログ用）
        
        Args:
            window: ロック対象のウィンドウ（Noneで現在のフォーカスをロック）
        """
        if window is None:
            window = self.current_focus
        
        self.focus_locked = True
        self.locked_window = window
        
        # ロック対象のウィンドウにフォーカスを設定
        if window:
            self.current_focus = window
        
        logger.debug(f"フォーカスをロック: {window.window_id if window else 'None'}")
    
    def unlock_focus(self) -> None:
        """フォーカスロックを解除"""
        if self.focus_locked:
            locked_window_id = self.locked_window.window_id if self.locked_window else 'None'
            self.focus_locked = False
            self.locked_window = None
            logger.debug(f"フォーカスロックを解除: {locked_window_id}")
    
    def is_focus_locked(self) -> bool:
        """
        フォーカスがロックされているかチェック
        
        Returns:
            bool: ロックされている場合True
        """
        return self.focus_locked
    
    def can_receive_focus(self, window: Window) -> bool:
        """
        ウィンドウがフォーカスを受け取れるかチェック
        
        Args:
            window: チェック対象のウィンドウ
            
        Returns:
            bool: フォーカスを受け取れる場合True
        """
        if not window:
            return False
        
        # 破棄されたウィンドウはフォーカスを受け取れない
        if window.state == WindowState.DESTROYED:
            return False
        
        # フォーカスロック中の場合
        if self.focus_locked:
            return window == self.locked_window
        
        # 表示されていないウィンドウはフォーカスを受け取れない
        if window.state != WindowState.SHOWN:
            return False
        
        return True
    
    def add_focus_change_listener(self, listener: Callable[[FocusChange], None]) -> None:
        """
        フォーカス変更リスナーを追加
        
        Args:
            listener: フォーカス変更時に呼び出される関数
        """
        if listener not in self.focus_change_listeners:
            self.focus_change_listeners.append(listener)
            logger.debug("フォーカス変更リスナーを追加しました")
    
    def remove_focus_change_listener(self, listener: Callable[[FocusChange], None]) -> None:
        """
        フォーカス変更リスナーを削除
        
        Args:
            listener: 削除する関数
        """
        if listener in self.focus_change_listeners:
            self.focus_change_listeners.remove(listener)
            logger.debug("フォーカス変更リスナーを削除しました")
    
    def cleanup_destroyed_windows(self) -> None:
        """破棄されたウィンドウをクリーンアップ"""
        # 現在のフォーカスが破棄されている場合はクリア
        if self.current_focus and self.current_focus.state == WindowState.DESTROYED:
            logger.debug(f"破棄されたウィンドウのフォーカスをクリア: {self.current_focus.window_id}")
            self.current_focus = None
        
        # ロックされたウィンドウが破棄されている場合はロック解除
        if self.locked_window and self.locked_window.state == WindowState.DESTROYED:
            logger.debug(f"破棄されたウィンドウのフォーカスロックを解除: {self.locked_window.window_id}")
            self.unlock_focus()
    
    def get_focus_history(self, limit: int = 10) -> List[FocusChange]:
        """
        フォーカス履歴を取得
        
        Args:
            limit: 取得する履歴の最大数
            
        Returns:
            List[FocusChange]: フォーカス変更の履歴（新しい順）
        """
        return self.focus_history[-limit:] if self.focus_history else []
    
    def get_focus_trace(self) -> List[str]:
        """
        フォーカス追跡情報を文字列リストで取得（デバッグ用）
        
        Returns:
            List[str]: フォーカス状態の情報
        """
        trace = []
        
        # 現在のフォーカス状態
        current_info = f"Current Focus: {self.current_focus.window_id if self.current_focus else 'None'}"
        if self.focus_locked:
            current_info += f" (LOCKED: {self.locked_window.window_id if self.locked_window else 'None'})"
        trace.append(current_info)
        
        # 最近のフォーカス履歴
        if self.focus_history:
            trace.append("\nRecent Focus History:")
            for change in self.get_focus_history(5):
                timestamp = change.timestamp.strftime("%H:%M:%S.%f")[:-3]
                trace.append(f"  {timestamp}: {change.old_window_id} → {change.new_window_id}")
        
        return trace
    
    def validate_focus_state(self) -> List[str]:
        """
        フォーカス状態の整合性をチェック
        
        Returns:
            List[str]: 発見された問題のリスト
        """
        issues = []
        
        # 現在のフォーカスが破棄されているかチェック
        if self.current_focus and self.current_focus.state == WindowState.DESTROYED:
            issues.append(f"現在のフォーカスが破棄されたウィンドウです: {self.current_focus.window_id}")
        
        # ロックされたウィンドウが破棄されているかチェック
        if self.locked_window and self.locked_window.state == WindowState.DESTROYED:
            issues.append(f"ロックされたウィンドウが破棄されています: {self.locked_window.window_id}")
        
        # フォーカスロック状態の整合性チェック
        if self.focus_locked and not self.locked_window:
            issues.append("フォーカスがロックされているがロック対象のウィンドウが存在しません")
        
        # 表示されていないウィンドウにフォーカスがある場合
        if self.current_focus and self.current_focus.state != WindowState.SHOWN:
            issues.append(f"非表示のウィンドウにフォーカスがあります: {self.current_focus.window_id}")
        
        return issues
    
    def reset(self) -> None:
        """フォーカス状態をリセット"""
        self.current_focus = None
        self.focus_locked = False
        self.locked_window = None
        self.focus_history.clear()
        logger.debug("フォーカス状態をリセットしました")
    
    def __str__(self) -> str:
        current = self.current_focus.window_id if self.current_focus else "None"
        status = "LOCKED" if self.focus_locked else "UNLOCKED"
        return f"FocusManager(focus: {current}, {status})"