"""
Window基底クラス

独立したUI領域を表現し、ライフサイクル管理を行う
"""

from abc import ABC, abstractmethod
from enum import Enum
from typing import Optional, List, Dict, Any
import pygame
import pygame_gui
from datetime import datetime

from src.utils.logger import logger


class WindowState(Enum):
    """ウィンドウの状態"""
    CREATED = "created"      # 作成済み、未表示
    SHOWN = "shown"          # 表示中
    HIDDEN = "hidden"        # 非表示
    DESTROYED = "destroyed"  # 破棄済み


class Window(ABC):
    """
    Window基底クラス
    
    独立したUI領域を表現し、以下の機能を提供する：
    - ライフサイクル管理（作成→表示→非表示→破棄）
    - 親子関係の管理
    - イベント処理
    - UI要素の統一管理
    """
    
    def __init__(self, window_id: str, parent: Optional['Window'] = None, modal: bool = False):
        """
        ウィンドウを初期化
        
        Args:
            window_id: ウィンドウの一意識別子
            parent: 親ウィンドウ（オプション）
            modal: モーダルウィンドウかどうか
        """
        self.window_id = window_id
        self.parent = parent
        self.children: List['Window'] = []
        self.modal = modal
        self.state = WindowState.CREATED
        
        # UI管理
        self.ui_manager: Optional[pygame_gui.UIManager] = None
        self.surface: Optional[pygame.Surface] = None
        self.rect: Optional[pygame.Rect] = None
        
        # メタデータ
        self.created_at = datetime.now()
        self.data: Dict[str, Any] = {}  # ウィンドウ固有のデータ
        
        # 親子関係の設定
        if self.parent:
            self.parent.add_child(self)
        
        logger.debug(f"ウィンドウを作成: {self.window_id} (parent: {self.parent.window_id if self.parent else 'None'})")
    
    def add_child(self, child: 'Window') -> None:
        """子ウィンドウを追加"""
        if child not in self.children:
            self.children.append(child)
            logger.debug(f"子ウィンドウを追加: {child.window_id} -> {self.window_id}")
    
    def remove_child(self, child: 'Window') -> None:
        """子ウィンドウを削除"""
        if child in self.children:
            self.children.remove(child)
            logger.debug(f"子ウィンドウを削除: {child.window_id} <- {self.window_id}")
    
    @abstractmethod
    def create(self) -> None:
        """
        UI要素を作成
        
        このメソッドをオーバーライドして、ウィンドウ固有のUI要素を作成する
        """
        pass
    
    def show(self) -> None:
        """
        ウィンドウを表示
        
        状態をSHOWNに変更し、UI要素を表示状態にする
        """
        if self.state == WindowState.DESTROYED:
            raise ValueError(f"破棄されたウィンドウは表示できません: {self.window_id}")
        
        if self.state == WindowState.CREATED:
            self.create()
        elif self.state == WindowState.HIDDEN:
            # 非表示状態から表示に戻る場合、UI要素を再表示
            logger.info(f"非表示状態から表示復帰: {self.window_id}, show_ui_elements()を呼び出し")
            self.show_ui_elements()
        
        self.state = WindowState.SHOWN
        self.on_show()
        logger.info(f"ウィンドウを表示: {self.window_id} (状態: {self.state})")
    
    def hide(self) -> None:
        """
        ウィンドウを非表示
        
        状態をHIDDENに変更し、UI要素を非表示にする（削除はしない）
        """
        if self.state == WindowState.SHOWN:
            # UI要素を非表示にするが削除はしない
            self.hide_ui_elements()
            self.state = WindowState.HIDDEN
            self.on_hide()
            logger.debug(f"ウィンドウを非表示: {self.window_id}")
    
    def destroy(self) -> None:
        """
        ウィンドウを破棄
        
        UI要素を削除し、親子関係を解除する
        """
        if self.state == WindowState.DESTROYED:
            return
        
        # 子ウィンドウを再帰的に破棄
        for child in self.children.copy():
            child.destroy()
        
        # 親から自分を削除
        if self.parent:
            self.parent.remove_child(self)
        
        # UI要素のクリーンアップ
        self.cleanup_ui()
        
        self.state = WindowState.DESTROYED
        self.on_destroy()
        logger.debug(f"ウィンドウを破棄: {self.window_id}")
    
    def cleanup_ui(self) -> None:
        """UI要素のクリーンアップ"""
        # 子クラスで定義されたUI要素の破棄処理を呼び出し
        self.destroy_ui_elements()
        
        # UIManagerの参照をクリア
        self.ui_manager = None
    
    def hide_ui_elements(self) -> None:
        """UI要素を非表示にする（子クラスでオーバーライドしてください）"""
        logger.debug(f"hide_ui_elements called for {self.window_id}")
    
    def show_ui_elements(self) -> None:
        """UI要素を表示する（子クラスでオーバーライドしてください）"""
        logger.debug(f"show_ui_elements called for {self.window_id}")
    
    def destroy_ui_elements(self) -> None:
        """UI要素を破棄する（子クラスでオーバーライドしてください）"""
        logger.debug(f"destroy_ui_elements called for {self.window_id}")
    
    @abstractmethod
    def handle_event(self, event: pygame.event.Event) -> bool:
        """
        イベントを処理
        
        Args:
            event: Pygameイベント
            
        Returns:
            bool: イベントが処理された場合True
        """
        pass
    
    def update(self, time_delta: float) -> None:
        """
        ウィンドウの更新
        
        Args:
            time_delta: 前回の更新からの経過時間（秒）
        """
        if self.state == WindowState.SHOWN and self.ui_manager:
            self.ui_manager.update(time_delta)
    
    def draw(self, surface: pygame.Surface) -> None:
        """
        ウィンドウの描画
        
        Args:
            surface: 描画対象のサーフェス
        """
        # WindowManagerから統一UIManagerを使っているため、
        # 個別のウィンドウでdraw_uiを呼ぶ必要はない
        # UIManagerの描画はWindowManager.draw()で一括して行われる
        pass
    
    def handle_escape(self) -> bool:
        """
        ESCキーの処理
        
        Returns:
            bool: ESCキーを処理した場合True
        """
        # デフォルト実装：何もしない
        return False
    
    def set_data(self, key: str, value: Any) -> None:
        """ウィンドウデータを設定"""
        self.data[key] = value
    
    def get_data(self, key: str, default: Any = None) -> Any:
        """ウィンドウデータを取得"""
        return self.data.get(key, default)
    
    def send_message(self, message_type: str, data: Dict[str, Any] = None) -> None:
        """
        親ウィンドウまたはWindowManagerにメッセージを送信
        
        Args:
            message_type: メッセージの種類
            data: メッセージデータ
        """
        if self.parent:
            self.parent.receive_message(self, message_type, data or {})
        else:
            # 親がない場合はWindowManagerに送信
            try:
                from .window_manager import WindowManager
                window_manager = WindowManager.get_instance()
                if hasattr(window_manager, 'handle_orphan_message'):
                    window_manager.handle_orphan_message(self, message_type, data or {})
            except Exception as e:
                logger.debug(f"WindowManager経由のメッセージ送信に失敗: {e}")
    
    def receive_message(self, sender: 'Window', message_type: str, data: Dict[str, Any]) -> None:
        """
        子ウィンドウからのメッセージを受信
        
        Args:
            sender: 送信者ウィンドウ
            message_type: メッセージの種類
            data: メッセージデータ
        """
        # デフォルト実装：何もしない
        pass
    
    def get_hierarchy_path(self) -> str:
        """階層パスを取得（デバッグ用）"""
        if self.parent:
            return f"{self.parent.get_hierarchy_path()}/{self.window_id}"
        return self.window_id
    
    def is_ancestor_of(self, window: 'Window') -> bool:
        """指定されたウィンドウの祖先かどうかチェック"""
        current = window.parent
        while current:
            if current == self:
                return True
            current = current.parent
        return False
    
    def is_descendant_of(self, window: 'Window') -> bool:
        """指定されたウィンドウの子孫かどうかチェック"""
        return window.is_ancestor_of(self)
    
    # イベントハンドラ（オーバーライド可能）
    def on_show(self) -> None:
        """表示時のイベントハンドラ"""
        pass
    
    def on_hide(self) -> None:
        """非表示時のイベントハンドラ"""
        pass
    
    def on_destroy(self) -> None:
        """破棄時のイベントハンドラ"""
        pass
    
    def __str__(self) -> str:
        return f"Window({self.window_id}, {self.state.value}, modal={self.modal})"
    
    def __repr__(self) -> str:
        return f"Window(id={self.window_id}, state={self.state.value}, parent={self.parent.window_id if self.parent else None})"