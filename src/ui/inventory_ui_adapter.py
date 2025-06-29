"""インベントリUI移行アダプタ - 旧UIMenuから新WindowSystemへの橋渡し"""

from typing import Optional, Callable, Tuple
from src.ui.windows.inventory_manager import inventory_manager
from src.character.party import Party
from src.character.character import Character
from src.inventory.inventory import Inventory
from src.utils.logger import logger


class InventoryUIAdapter:
    """
    インベントリUI移行アダプタクラス
    
    旧inventory_ui.pyのインターフェースを維持しながら、
    内部では新しいWindowSystemベースのインベントリUIを使用する
    """
    
    def __init__(self):
        """アダプタを初期化"""
        self.current_party: Optional[Party] = None
        self.current_inventory: Optional[Inventory] = None
        self.current_character: Optional[Character] = None
        self.selected_slot: Optional[int] = None
        self.transfer_source: Optional[Tuple[Inventory, int]] = None
        self.callback_on_close: Optional[Callable] = None
        
        logger.info("InventoryUIAdapter初期化完了")
    
    def set_party(self, party: Party) -> None:
        """パーティを設定（旧インターフェース互換）"""
        self.current_party = party
        logger.debug(f"アダプタ: パーティを設定 - {party.name}")
    
    def show_party_inventory_menu(self, party: Party) -> None:
        """パーティインベントリメニューを表示（旧インターフェース互換）"""
        try:
            self.set_party(party)
            
            # 新しいWindowSystemベースのUIを使用
            inventory_manager.show_party_inventory_menu(
                party, 
                callback_on_close=self._on_close
            )
            
            logger.info(f"アダプタ: パーティインベントリメニュー表示 - {party.name}")
            
        except Exception as e:
            logger.error(f"アダプタ: パーティインベントリメニュー表示エラー - {e}")
            raise
    
    def show(self) -> None:
        """インベントリUIを表示（旧インターフェース互換）"""
        if self.current_party:
            self.show_party_inventory_menu(self.current_party)
        else:
            logger.warning("アダプタ: パーティが設定されていません")
    
    def hide(self) -> None:
        """インベントリUIを非表示（旧インターフェース互換）"""
        try:
            inventory_manager.close_inventory_ui()
            logger.debug("アダプタ: インベントリUIを非表示")
        except Exception as e:
            logger.error(f"アダプタ: インベントリUI非表示エラー - {e}")
    
    def destroy(self) -> None:
        """インベントリUIを破棄（旧インターフェース互換）"""
        try:
            self.hide()
            self.current_party = None
            self.current_inventory = None
            self.current_character = None
            self.selected_slot = None
            self.transfer_source = None
            self.callback_on_close = None
            logger.debug("アダプタ: インベントリUIを破棄")
        except Exception as e:
            logger.error(f"アダプタ: インベントリUI破棄エラー - {e}")
    
    def set_close_callback(self, callback: Callable) -> None:
        """閉じるコールバックを設定（旧インターフェース互換）"""
        self.callback_on_close = callback
    
    def _on_close(self) -> None:
        """ウィンドウが閉じられた時の処理"""
        if self.callback_on_close:
            try:
                self.callback_on_close()
            except Exception as e:
                logger.error(f"アダプタ: 閉じるコールバックエラー - {e}")
    
    # 以下、旧インターフェースで使用されていた他のメソッドも必要に応じて実装
    def _show_party_shared_inventory(self) -> None:
        """パーティ共有インベントリを表示（旧インターフェース内部メソッド）"""
        if self.current_party:
            shared_inventory = self.current_party.get_party_inventory()
            inventory_manager.show_inventory_contents(
                shared_inventory, 
                "パーティ共有アイテム", 
                "party"
            )
    
    def _show_character_inventory(self, character: Character) -> None:
        """キャラクターインベントリを表示（旧インターフェース内部メソッド）"""
        inventory_manager.show_character_inventory(character)
    
    def _close_inventory_ui(self) -> None:
        """インベントリUIを閉じる（旧インターフェース内部メソッド）"""
        self.hide()
    
    # プロパティでアクセスできるようにする（旧コードとの互換性）
    @property
    def is_open(self) -> bool:
        """インベントリUIが開いているかどうか"""
        return inventory_manager.is_open()


# グローバルインスタンス - 旧システムとの互換性を保つ
inventory_ui = InventoryUIAdapter()