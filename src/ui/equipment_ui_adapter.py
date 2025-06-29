"""装備UI移行アダプタ - 旧UIMenuから新WindowSystemへの橋渡し"""

from typing import Optional, Callable
from src.ui.windows.equipment_manager import equipment_manager
from src.character.party import Party
from src.character.character import Character
from src.utils.logger import logger


class EquipmentUIAdapter:
    """
    装備UI移行アダプタクラス
    
    旧equipment_ui.pyのインターフェースを維持しながら、
    内部では新しいWindowSystemベースの装備UIを使用する
    """
    
    def __init__(self):
        """アダプタを初期化"""
        self.current_party: Optional[Party] = None
        self.current_character: Optional[Character] = None
        self.is_open = False
        self.callback_on_close: Optional[Callable] = None
        
        logger.info("EquipmentUIAdapter初期化完了")
    
    def set_party(self, party: Party) -> None:
        """パーティを設定（旧インターフェース互換）"""
        self.current_party = party
        logger.debug(f"アダプタ: パーティを設定 - {party.name}")
    
    def show_party_equipment_menu(self, party: Party) -> None:
        """パーティ装備メニューを表示（旧インターフェース互換）"""
        try:
            self.set_party(party)
            self.is_open = True
            
            # 新しいWindowSystemベースのUIを使用
            equipment_manager.show_party_equipment_menu(
                party, 
                callback_on_close=self._on_close
            )
            
            logger.info(f"アダプタ: パーティ装備メニュー表示 - {party.name}")
            
        except Exception as e:
            logger.error(f"アダプタ: パーティ装備メニュー表示エラー - {e}")
            self.is_open = False
            raise
    
    def show(self) -> None:
        """装備UIを表示（旧インターフェース互換）"""
        if self.current_party:
            self.show_party_equipment_menu(self.current_party)
        else:
            logger.warning("アダプタ: パーティが設定されていません")
    
    def hide(self) -> None:
        """装備UIを非表示（旧インターフェース互換）"""
        try:
            equipment_manager.close_equipment_ui()
            self.is_open = False
            logger.debug("アダプタ: 装備UIを非表示")
        except Exception as e:
            logger.error(f"アダプタ: 装備UI非表示エラー - {e}")
    
    def destroy(self) -> None:
        """装備UIを破棄（旧インターフェース互換）"""
        try:
            self.hide()
            self.current_party = None
            self.current_character = None
            self.callback_on_close = None
            logger.debug("アダプタ: 装備UIを破棄")
        except Exception as e:
            logger.error(f"アダプタ: 装備UI破棄エラー - {e}")
    
    def set_close_callback(self, callback: Callable) -> None:
        """閉じるコールバックを設定（旧インターフェース互換）"""
        self.callback_on_close = callback
    
    def _on_close(self) -> None:
        """ウィンドウが閉じられた時の処理"""
        self.is_open = False
        if self.callback_on_close:
            try:
                self.callback_on_close()
            except Exception as e:
                logger.error(f"アダプタ: 閉じるコールバックエラー - {e}")
    
    # 以下、旧インターフェースで使用されていた他のメソッドも必要に応じて実装
    def _show_character_equipment(self, character: Character) -> None:
        """キャラクター装備画面を表示（旧インターフェース内部メソッド）"""
        # 新システムでは直接equipment_managerを呼ぶ
        equipment_manager.show_character_equipment(character)
    
    def _close_equipment_ui(self) -> None:
        """装備UIを閉じる（旧インターフェース内部メソッド）"""
        self.hide()


# グローバルインスタンス - 旧システムとの互換性を保つ
equipment_ui = EquipmentUIAdapter()