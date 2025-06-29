"""装備システム管理 - UIMenuからWindowSystemへの移行管理"""

from typing import Optional, Callable
from src.ui.windows.equipment_window import EquipmentWindow
from src.ui.window_system.window_manager import WindowManager
from src.character.party import Party
from src.character.character import Character
from src.utils.logger import logger


class EquipmentManager:
    """
    装備システム管理クラス
    
    UIMenuベースの旧システムとWindowSystemベースの新システムの
    統一インターフェースを提供する
    """
    
    def __init__(self):
        """装備マネージャーを初期化"""
        self.window_manager = WindowManager.get_instance()
        self.current_window: Optional[EquipmentWindow] = None
        self.callback_on_close: Optional[Callable] = None
        
        logger.debug("EquipmentManager初期化完了")
    
    def show_party_equipment_menu(self, party: Party, callback_on_close: Optional[Callable] = None) -> None:
        """
        パーティ装備メニューを表示
        
        Args:
            party: 表示するパーティ
            callback_on_close: 閉じる時のコールバック
        """
        try:
            # 既存のウィンドウがある場合は閉じる
            if self.current_window:
                self.close_equipment_ui()
            
            # 新しいウィンドウを作成
            self.current_window = EquipmentWindow("party_equipment_main")
            self.callback_on_close = callback_on_close
            
            # パーティを設定
            self.current_window.set_party(party)
            
            # 閉じるコールバックを設定
            self.current_window.set_close_callback(self._on_window_close)
            
            # ウィンドウを表示
            self.current_window.show()
            self.current_window.show_party_equipment_overview()
            
            logger.info(f"パーティ装備メニューを表示: {party.name}")
            
        except Exception as e:
            logger.error(f"パーティ装備メニュー表示エラー: {e}")
            raise
    
    def show_character_equipment(self, character: Character, callback_on_close: Optional[Callable] = None) -> None:
        """
        キャラクター装備画面を直接表示
        
        Args:
            character: 表示するキャラクター
            callback_on_close: 閉じる時のコールバック
        """
        try:
            # 既存のウィンドウがある場合は閉じる
            if self.current_window:
                self.close_equipment_ui()
            
            # 新しいウィンドウを作成
            self.current_window = EquipmentWindow("character_equipment_direct")
            self.callback_on_close = callback_on_close
            
            # 閉じるコールバックを設定
            self.current_window.set_close_callback(self._on_window_close)
            
            # ウィンドウを表示してキャラクター装備を表示
            self.current_window.show()
            self.current_window.show_character_equipment(character)
            
            logger.info(f"キャラクター装備画面を表示: {character.name}")
            
        except Exception as e:
            logger.error(f"キャラクター装備画面表示エラー: {e}")
            raise
    
    def close_equipment_ui(self) -> None:
        """装備UIを閉じる"""
        if self.current_window:
            try:
                self.current_window.hide()
                self.current_window.destroy()
                self.current_window = None
                logger.debug("装備UIを閉じました")
            except Exception as e:
                logger.error(f"装備UI終了エラー: {e}")
                self.current_window = None
    
    def is_open(self) -> bool:
        """装備UIが開いているかどうか"""
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
                
            logger.debug("装備ウィンドウ閉じる処理完了")
            
        except Exception as e:
            logger.error(f"装備ウィンドウ閉じる処理エラー: {e}")


# グローバルインスタンス
equipment_manager = EquipmentManager()