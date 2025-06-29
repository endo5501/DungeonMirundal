"""キャラクター作成システム管理 - UIMenuからWindowSystemへの移行管理"""

from typing import Optional, Callable
from src.ui.windows.character_creation_wizard import CharacterCreationWizard
from src.ui.window_system.window_manager import WindowManager
from src.character.character import Character
from src.utils.logger import logger


class CharacterCreationManager:
    """
    キャラクター作成システム管理クラス
    
    UIMenuベースの旧システムとWindowSystemベースの新システムの
    統一インターフェースを提供する
    """
    
    def __init__(self):
        """キャラクター作成マネージャーを初期化"""
        self.window_manager = WindowManager.get_instance()
        self.current_wizard: Optional[CharacterCreationWizard] = None
        self.creation_callback: Optional[Callable] = None
        self.cancel_callback: Optional[Callable] = None
        
        logger.debug("CharacterCreationManager初期化完了")
    
    def start_character_creation(self, 
                                creation_callback: Optional[Callable] = None,
                                cancel_callback: Optional[Callable] = None) -> None:
        """
        キャラクター作成ウィザードを開始
        
        Args:
            creation_callback: キャラクター作成完了時のコールバック
            cancel_callback: キャンセル時のコールバック
        """
        try:
            # 既存のウィザードがある場合は閉じる
            if self.current_wizard:
                self.close_character_creation()
            
            # コールバックを保存
            self.creation_callback = creation_callback
            self.cancel_callback = cancel_callback
            
            # 新しいウィザードを作成
            self.current_wizard = CharacterCreationWizard(
                "character_creation_wizard",
                callback=self._on_character_created
            )
            
            # キャンセルコールバックを設定
            self.current_wizard.set_cancel_callback(self._on_wizard_cancel)
            
            # ウィザードを表示して開始
            self.current_wizard.show()
            self.current_wizard.start_wizard()
            
            logger.info("キャラクター作成ウィザードを開始")
            
        except Exception as e:
            logger.error(f"キャラクター作成ウィザード開始エラー: {e}")
            raise
    
    def close_character_creation(self) -> None:
        """キャラクター作成ウィザードを閉じる"""
        if self.current_wizard:
            try:
                self.current_wizard.hide()
                self.current_wizard.destroy()
                self.current_wizard = None
                logger.debug("キャラクター作成ウィザードを閉じました")
            except Exception as e:
                logger.error(f"キャラクター作成ウィザード終了エラー: {e}")
                self.current_wizard = None
    
    def is_creating_character(self) -> bool:
        """キャラクター作成中かどうか"""
        return self.current_wizard is not None and self.current_wizard.state.value == "shown"
    
    def get_current_creation_step(self) -> Optional[str]:
        """現在の作成ステップを取得"""
        if self.current_wizard:
            return self.current_wizard.current_step.value
        return None
    
    def _on_character_created(self, character: Character) -> None:
        """キャラクターが作成された時の処理"""
        try:
            logger.info(f"キャラクター作成完了: {character.name}")
            
            # 元のコールバックを呼び出し
            if self.creation_callback:
                callback = self.creation_callback
                self.creation_callback = None
                callback(character)
            
            # 少し時間を置いてウィザードを閉じる（ユーザーに完了メッセージを見せるため）
            # 実際の実装では、タイマーやユーザーのアクションを待つ
            
        except Exception as e:
            logger.error(f"キャラクター作成完了処理エラー: {e}")
    
    def _on_wizard_cancel(self) -> None:
        """ウィザードがキャンセルされた時の処理"""
        try:
            logger.info("キャラクター作成がキャンセルされました")
            
            # ウィザードを閉じる
            self.close_character_creation()
            
            # 元のコールバックを呼び出し
            if self.cancel_callback:
                callback = self.cancel_callback
                self.cancel_callback = None
                callback()
                
        except Exception as e:
            logger.error(f"キャラクター作成キャンセル処理エラー: {e}")


# グローバルインスタンス
character_creation_manager = CharacterCreationManager()