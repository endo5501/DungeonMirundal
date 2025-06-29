"""ダンジョンメニューシステム管理 - UIMenuからWindowSystemへの移行管理"""

from typing import Optional, Callable, Any
from src.ui.windows.dungeon_menu_window import DungeonMenuWindow
from src.ui.window_system.window_manager import WindowManager
from src.character.party import Party
from src.utils.logger import logger


class DungeonMenuManager:
    """
    ダンジョンメニューシステム管理クラス
    
    UIMenuベースの旧システムとWindowSystemベースの新システムの
    統一インターフェースを提供する
    """
    
    def __init__(self):
        """ダンジョンメニューマネージャーを初期化"""
        self.window_manager = WindowManager.get_instance()
        self.current_window: Optional[DungeonMenuWindow] = None
        self.callbacks: dict[str, Callable] = {}
        
        logger.debug("DungeonMenuManager初期化完了")
    
    def create_dungeon_menu(self, screen=None) -> DungeonMenuWindow:
        """
        ダンジョンメニューウィンドウを作成
        
        Args:
            screen: 画面サーフェス（互換性のため）
            
        Returns:
            DungeonMenuWindow: 作成されたダンジョンメニューウィンドウ
        """
        try:
            # 既存のウィンドウがある場合は破棄
            if self.current_window:
                self.close_dungeon_menu()
            
            # 新しいウィンドウを作成
            self.current_window = DungeonMenuWindow("dungeon_menu_main")
            
            # 既存のコールバックを設定
            for action, callback in self.callbacks.items():
                self.current_window.set_callback(action, callback)
            
            # ウィンドウを表示
            self.current_window.show()
            
            logger.info("ダンジョンメニューウィンドウを作成")
            return self.current_window
            
        except Exception as e:
            logger.error(f"ダンジョンメニューウィンドウ作成エラー: {e}")
            raise
    
    def set_party(self, party: Party) -> None:
        """
        パーティを設定
        
        Args:
            party: 設定するパーティ
        """
        if self.current_window:
            self.current_window.set_party(party)
        logger.debug(f"パーティを設定: {party.name}")
    
    def set_dungeon_state(self, dungeon_state: Any) -> None:
        """
        ダンジョン状態を設定
        
        Args:
            dungeon_state: ダンジョン状態オブジェクト
        """
        if self.current_window:
            self.current_window.set_dungeon_state(dungeon_state)
        logger.debug("ダンジョン状態を設定")
    
    def set_callback(self, action: str, callback: Callable) -> None:
        """
        コールバックを設定
        
        Args:
            action: アクション名
            callback: コールバック関数
        """
        # マネージャーで保持
        self.callbacks[action] = callback
        
        # 既存ウィンドウにも設定
        if self.current_window:
            self.current_window.set_callback(action, callback)
        
        logger.debug(f"コールバック設定: {action}")
    
    def toggle_main_menu(self) -> None:
        """メインメニューの表示/非表示を切り替え"""
        if self.current_window:
            self.current_window.toggle_main_menu()
    
    def show_main_menu(self) -> None:
        """メインメニューを表示"""
        if self.current_window:
            self.current_window.show_main_menu()
    
    def close_menu(self) -> None:
        """メニューを閉じる"""
        if self.current_window:
            self.current_window.close_menu()
    
    def handle_input(self, event) -> bool:
        """
        入力処理
        
        Args:
            event: Pygameイベント
            
        Returns:
            bool: イベントが処理されたかどうか
        """
        if self.current_window:
            return self.current_window.handle_input(event)
        return False
    
    def render(self) -> None:
        """UIを描画"""
        if self.current_window:
            self.current_window.render()
    
    def render_overlay(self) -> None:
        """オーバーレイUIを描画"""
        if self.current_window:
            self.current_window.render_overlay()
    
    def update(self) -> None:
        """UI更新"""
        if self.current_window:
            self.current_window.on_update(0.0)  # time_deltaは0.0で固定
    
    def close_dungeon_menu(self) -> None:
        """ダンジョンメニューを閉じる"""
        if self.current_window:
            try:
                self.current_window.hide()
                self.current_window.destroy()
                self.current_window = None
                logger.debug("ダンジョンメニューを閉じました")
            except Exception as e:
                logger.error(f"ダンジョンメニュー終了エラー: {e}")
                self.current_window = None
    
    def cleanup(self) -> None:
        """リソースのクリーンアップ"""
        try:
            self.close_dungeon_menu()
            self.callbacks.clear()
            logger.info("DungeonMenuManager リソースをクリーンアップしました")
        except Exception as e:
            logger.error(f"クリーンアップ中にエラー: {e}")
    
    def is_menu_open(self) -> bool:
        """メニューが開いているかどうか"""
        return self.current_window is not None and self.current_window.is_menu_open
    
    def is_window_open(self) -> bool:
        """ウィンドウが開いているかどうか"""
        return self.current_window is not None and self.current_window.state.value == "shown"


# グローバルインスタンス
dungeon_menu_manager = DungeonMenuManager()


def create_pygame_dungeon_ui(screen=None) -> DungeonMenuWindow:
    """
    Pygame版ダンジョンUI作成（互換性関数）
    
    Args:
        screen: 画面サーフェス（互換性のため）
        
    Returns:
        DungeonMenuWindow: ダンジョンメニューウィンドウ
    """
    return dungeon_menu_manager.create_dungeon_menu(screen)