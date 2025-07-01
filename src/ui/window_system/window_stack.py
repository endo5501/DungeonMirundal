"""
WindowStack クラス

ウィンドウの階層管理とナビゲーション機能を提供
"""

from typing import List, Optional
from src.utils.logger import logger
from .window import Window, WindowState


class WindowStack:
    """
    ウィンドウスタック管理クラス
    
    ウィンドウの階層管理と確実なナビゲーション機能を提供する：
    - LIFO（Last In, First Out）方式でのウィンドウ管理
    - 階層の可視化とデバッグ機能
    - 確実な戻り処理
    """
    
    def __init__(self):
        """ウィンドウスタックを初期化"""
        self.stack: List[Window] = []
        self.history: List[Window] = []  # 閉じられたウィンドウの履歴
        self.max_history_size = 50  # 履歴の最大サイズ
        
        logger.debug("WindowStackを初期化しました")
    
    def push(self, window: Window) -> None:
        """
        ウィンドウをスタックにプッシュ
        
        Args:
            window: プッシュするウィンドウ
        """
        if window in self.stack:
            logger.warning(f"ウィンドウは既にスタックに存在します: {window.window_id}")
            return
        
        # 現在のトップウィンドウの処理
        current_top = self.peek()
        if current_top:
            if window.modal:
                # モーダルウィンドウの場合、前のウィンドウのUI要素を無効化
                logger.debug(f"モーダルウィンドウ {window.window_id} が {current_top.window_id} の上に表示されます")
                # UI要素を無効化（非表示にはしない）
                if hasattr(current_top, 'disable_ui'):
                    current_top.disable_ui()
            else:
                # 非モーダルウィンドウの場合も前のウィンドウを隠す
                logger.debug(f"非モーダルウィンドウ {window.window_id} が {current_top.window_id} に代わって表示されます")
                current_top.hide()
        
        self.stack.append(window)
        logger.debug(f"ウィンドウをプッシュ: {window.window_id} (stack size: {len(self.stack)})")
        
        # デバッグ情報を出力
        if logger.isEnabledFor(10):  # DEBUG level
            logger.debug(f"現在のスタック: {self.get_stack_trace()}")
    
    def pop(self) -> Optional[Window]:
        """
        スタックからウィンドウをポップ
        
        Returns:
            Optional[Window]: ポップされたウィンドウ、スタックが空の場合はNone
        """
        if not self.stack:
            logger.debug("スタックは空です")
            return None
        
        window = self.stack.pop()
        
        # 履歴に追加
        self.history.append(window)
        if len(self.history) > self.max_history_size:
            self.history.pop(0)
        
        # ウィンドウを非表示にして破棄
        if window.state == WindowState.SHOWN:
            window.hide()
        
        # モーダルウィンドウだった場合、前のウィンドウのUIを再度有効化
        if window.modal:
            new_top = self.peek()
            if new_top and hasattr(new_top, 'enable_ui'):
                new_top.enable_ui()
        
        # 新しいトップウィンドウを表示
        new_top = self.peek()
        if new_top:
            logger.info(f"新しいトップウィンドウ: {new_top.window_id}, 状態: {new_top.state}")
            if new_top.state == WindowState.HIDDEN:
                new_top.show()
                logger.info(f"前のウィンドウを再表示: {new_top.window_id}")
            else:
                logger.info(f"前のウィンドウは既に表示済み: {new_top.window_id}")
        else:
            logger.warning("新しいトップウィンドウがありません")
        
        logger.info(f"ウィンドウをポップ完了: {window.window_id} (stack size: {len(self.stack)})")
        
        # デバッグ情報を出力
        if logger.isEnabledFor(10):  # DEBUG level
            logger.debug(f"現在のスタック: {self.get_stack_trace()}")
        
        return window
    
    def peek(self) -> Optional[Window]:
        """
        スタックのトップウィンドウを取得（ポップしない）
        
        Returns:
            Optional[Window]: トップウィンドウ、スタックが空の場合はNone
        """
        return self.stack[-1] if self.stack else None
    
    def get_at_index(self, index: int) -> Optional[Window]:
        """
        指定されたインデックスのウィンドウを取得
        
        Args:
            index: インデックス（0が最初、-1が最後）
            
        Returns:
            Optional[Window]: 指定されたウィンドウ、範囲外の場合はNone
        """
        try:
            return self.stack[index]
        except IndexError:
            return None
    
    def find_window(self, window_id: str) -> Optional[Window]:
        """
        指定されたIDのウィンドウを検索
        
        Args:
            window_id: 検索するウィンドウID
            
        Returns:
            Optional[Window]: 見つかったウィンドウ、存在しない場合はNone
        """
        for window in self.stack:
            if window.window_id == window_id:
                return window
        return None
    
    def remove_window(self, window: Window) -> bool:
        """
        指定されたウィンドウをスタックから削除
        
        Args:
            window: 削除するウィンドウ
            
        Returns:
            bool: 削除に成功した場合True
        """
        if window not in self.stack:
            return False
        
        # トップウィンドウの場合はpopを使用
        if window == self.peek():
            self.pop()
            return True
        
        # 中間のウィンドウを削除
        self.stack.remove(window)
        if window.state == WindowState.SHOWN:
            window.hide()
        
        logger.debug(f"ウィンドウを削除: {window.window_id} (stack size: {len(self.stack)})")
        return True
    
    def go_back(self) -> bool:
        """
        前のウィンドウに戻る
        
        Returns:
            bool: 戻り処理が実行された場合True
        """
        logger.info(f"go_back開始: スタックサイズ={len(self.stack)}")
        if len(self.stack) <= 1:
            logger.info("戻るウィンドウがありません")
            return False
        
        current_window = self.pop()
        if current_window:
            logger.info(f"現在のウィンドウを破棄: {current_window.window_id}")
            # WindowManagerを通してウィンドウを破棄（レジストリ削除含む）
            from .window_manager import WindowManager
            window_manager = WindowManager.get_instance()
            window_manager.destroy_window(current_window)
        
        logger.info("前のウィンドウに戻りました")
        return True
    
    def go_back_to_root(self) -> bool:
        """
        ルートウィンドウまで戻る
        
        Returns:
            bool: 戻り処理が実行された場合True
        """
        if len(self.stack) <= 1:
            return False
        
        # トップ以外の全てのウィンドウを閉じる
        while len(self.stack) > 1:
            window = self.pop()
            if window:
                from .window_manager import WindowManager
                window_manager = WindowManager.get_instance()
                window_manager.destroy_window(window)
        
        logger.debug("ルートウィンドウまで戻りました")
        return True
    
    def go_back_to_window(self, target_window_id: str) -> bool:
        """
        指定されたウィンドウまで戻る
        
        Args:
            target_window_id: 戻り先のウィンドウID
            
        Returns:
            bool: 戻り処理が実行された場合True
        """
        # ターゲットウィンドウを検索
        target_index = -1
        for i, window in enumerate(self.stack):
            if window.window_id == target_window_id:
                target_index = i
                break
        
        if target_index == -1:
            logger.warning(f"ターゲットウィンドウが見つかりません: {target_window_id}")
            return False
        
        # ターゲットより上のウィンドウを全て閉じる
        while len(self.stack) > target_index + 1:
            window = self.pop()
            if window:
                from .window_manager import WindowManager
                window_manager = WindowManager.get_instance()
                window_manager.destroy_window(window)
        
        logger.debug(f"ウィンドウまで戻りました: {target_window_id}")
        return True
    
    def clear(self) -> None:
        """
        スタックを全てクリア
        """
        while self.stack:
            window = self.pop()
            if window:
                from .window_manager import WindowManager
                window_manager = WindowManager.get_instance()
                window_manager.destroy_window(window)
        
        logger.debug("ウィンドウスタックをクリアしました")
    
    def size(self) -> int:
        """
        スタックのサイズを取得
        
        Returns:
            int: スタック内のウィンドウ数
        """
        return len(self.stack)
    
    def is_empty(self) -> bool:
        """
        スタックが空かどうかチェック
        
        Returns:
            bool: 空の場合True
        """
        return len(self.stack) == 0
    
    def get_stack_trace(self) -> List[str]:
        """
        スタックの状態を文字列リストで取得（デバッグ用）
        
        Returns:
            List[str]: スタック内の各ウィンドウの情報
        """
        trace = []
        for i, window in enumerate(self.stack):
            prefix = "→ " if i == len(self.stack) - 1 else "  "
            modal_mark = "[M]" if window.modal else "   "
            trace.append(f"{prefix}{modal_mark} {window.window_id} ({window.state.value})")
        return trace
    
    def get_hierarchy_info(self) -> str:
        """
        階層情報を文字列で取得（デバッグ用）
        
        Returns:
            str: 階層情報の文字列表現
        """
        if not self.stack:
            return "<empty stack>"
        
        lines = ["Window Stack:"]
        lines.extend(self.get_stack_trace())
        
        # 履歴情報を追加
        if self.history:
            lines.append("\nRecent History:")
            for window in self.history[-5:]:  # 最新5件
                lines.append(f"  × {window.window_id}")
        
        return "\n".join(lines)
    
    def validate_stack(self) -> List[str]:
        """
        スタックの整合性をチェック
        
        Returns:
            List[str]: 発見された問題のリスト
        """
        issues = []
        
        # 重複チェック
        window_ids = [w.window_id for w in self.stack]
        if len(window_ids) != len(set(window_ids)):
            issues.append("スタック内にIDの重複があります")
        
        # 状態チェック
        for i, window in enumerate(self.stack):
            if window.state == WindowState.DESTROYED:
                issues.append(f"破棄されたウィンドウがスタックに残っています: {window.window_id}")
            
            # トップウィンドウ以外は非表示であるべき（モーダルウィンドウ除く）
            if i < len(self.stack) - 1:  # トップウィンドウでない
                if window.state == WindowState.SHOWN and not self.stack[-1].modal:
                    issues.append(f"非トップウィンドウが表示状態です: {window.window_id}")
        
        return issues
    
    def __len__(self) -> int:
        return len(self.stack)
    
    def __iter__(self):
        return iter(self.stack)
    
    def __contains__(self, window: Window) -> bool:
        return window in self.stack
    
    def __str__(self) -> str:
        if not self.stack:
            return "WindowStack(empty)"
        return f"WindowStack({len(self.stack)} windows, top: {self.peek().window_id})"