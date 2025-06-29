"""インベントリシステム管理 - UIMenuからWindowSystemへの移行管理"""

from typing import Optional, Callable
from src.ui.windows.inventory_window import InventoryWindow
from src.ui.window_system.window_manager import WindowManager
from src.character.party import Party
from src.character.character import Character
from src.inventory.inventory import Inventory
from src.utils.logger import logger


class InventoryManager:
    """
    インベントリシステム管理クラス
    
    UIMenuベースの旧システムとWindowSystemベースの新システムの
    統一インターフェースを提供する
    """
    
    def __init__(self):
        """インベントリマネージャーを初期化"""
        self.window_manager = WindowManager.get_instance()
        self.current_window: Optional[InventoryWindow] = None
        self.callback_on_close: Optional[Callable] = None
        
        logger.debug("InventoryManager初期化完了")
    
    def show_party_inventory_menu(self, party: Party, callback_on_close: Optional[Callable] = None) -> None:
        """
        パーティインベントリメニューを表示
        
        Args:
            party: 表示するパーティ
            callback_on_close: 閉じる時のコールバック
        """
        try:
            # 既存のウィンドウがある場合は閉じる
            if self.current_window:
                self.close_inventory_ui()
            
            # 新しいウィンドウを作成
            self.current_window = InventoryWindow("party_inventory_main")
            self.callback_on_close = callback_on_close
            
            # パーティを設定
            self.current_window.set_party(party)
            
            # 閉じるコールバックを設定
            self.current_window.set_close_callback(self._on_window_close)
            
            # ウィンドウを表示
            self.current_window.show()
            self.current_window.show_party_inventory_overview()
            
            logger.info(f"パーティインベントリメニューを表示: {party.name}")
            
        except Exception as e:
            logger.error(f"パーティインベントリメニュー表示エラー: {e}")
            raise
    
    def show_character_inventory(self, character: Character, callback_on_close: Optional[Callable] = None) -> None:
        """
        キャラクターインベントリを直接表示
        
        Args:
            character: 表示するキャラクター
            callback_on_close: 閉じる時のコールバック
        """
        try:
            # 既存のウィンドウがある場合は閉じる
            if self.current_window:
                self.close_inventory_ui()
            
            # 新しいウィンドウを作成
            self.current_window = InventoryWindow("character_inventory_direct")
            self.callback_on_close = callback_on_close
            
            # 閉じるコールバックを設定
            self.current_window.set_close_callback(self._on_window_close)
            
            # ウィンドウを表示してキャラクターインベントリを表示
            self.current_window.show()
            inventory = character.get_inventory()
            self.current_window.current_character = character
            self.current_window.show_inventory_contents(inventory, f"{character.name}のアイテム", "character")
            
            logger.info(f"キャラクターインベントリを表示: {character.name}")
            
        except Exception as e:
            logger.error(f"キャラクターインベントリ表示エラー: {e}")
            raise
    
    def show_inventory_contents(self, inventory: Inventory, title: str, inventory_type: str = "character", callback_on_close: Optional[Callable] = None) -> None:
        """
        インベントリ内容を直接表示
        
        Args:
            inventory: 表示するインベントリ
            title: ウィンドウタイトル
            inventory_type: インベントリタイプ
            callback_on_close: 閉じる時のコールバック
        """
        try:
            # 既存のウィンドウがある場合は閉じる
            if self.current_window:
                self.close_inventory_ui()
            
            # 新しいウィンドウを作成
            self.current_window = InventoryWindow("inventory_contents_direct")
            self.callback_on_close = callback_on_close
            
            # 閉じるコールバックを設定
            self.current_window.set_close_callback(self._on_window_close)
            
            # ウィンドウを表示してインベントリ内容を表示
            self.current_window.show()
            self.current_window.show_inventory_contents(inventory, title, inventory_type)
            
            logger.info(f"インベントリ内容を表示: {title}")
            
        except Exception as e:
            logger.error(f"インベントリ内容表示エラー: {e}")
            raise
    
    def close_inventory_ui(self) -> None:
        """インベントリUIを閉じる"""
        if self.current_window:
            try:
                self.current_window.hide()
                self.current_window.destroy()
                self.current_window = None
                logger.debug("インベントリUIを閉じました")
            except Exception as e:
                logger.error(f"インベントリUI終了エラー: {e}")
                self.current_window = None
    
    def is_open(self) -> bool:
        """インベントリUIが開いているかどうか"""
        return self.current_window is not None and self.current_window.state.value == "shown"
    
    def _on_window_close(self) -> None:
        """ウィンドウが閉じられた時の処理"""
        try:
            # ウィンドウを破棄
            if self.current_window:
                self.current_window.destroy()
                self.current_window = None
            
            # 元のコールバックを呼び出し
            if self.callback_on_close:
                callback = self.callback_on_close
                self.callback_on_close = None
                callback()
                
            logger.debug("インベントリウィンドウ閉じる処理完了")
            
        except Exception as e:
            logger.error(f"インベントリウィンドウ閉じる処理エラー: {e}")


# グローバルインスタンス
inventory_manager = InventoryManager()