"""キャラクター作成UI移行アダプタ - 旧UIMenuから新WindowSystemへの橋渡し"""

from typing import Optional, Callable
from src.ui.windows.character_creation_manager import character_creation_manager
from src.character.character import Character
from src.utils.logger import logger


class CharacterCreationAdapter:
    """
    キャラクター作成UI移行アダプタクラス
    
    旧character_creation.pyのインターフェースを維持しながら、
    内部では新しいWindowSystemベースのキャラクター作成UIを使用する
    """
    
    def __init__(self, callback: Optional[Callable] = None):
        """
        アダプタを初期化
        
        Args:
            callback: キャラクター作成完了時のコールバック
        """
        self.callback = callback
        self.on_cancel: Optional[Callable] = None
        
        # 作成中のキャラクターデータ（互換性のため保持）
        self.character_data = {
            "name": "",
            "race": "",
            "class": "",
            "stats": None
        }
        
        logger.info("CharacterCreationAdapter初期化完了")
    
    def start(self) -> None:
        """ウィザードを開始（旧インターフェース互換）"""
        try:
            # 新しいWindowSystemベースのUIを使用
            character_creation_manager.start_character_creation(
                creation_callback=self._on_character_created,
                cancel_callback=self._on_cancel
            )
            
            logger.info("アダプタ: キャラクター作成ウィザード開始")
            
        except Exception as e:
            logger.error(f"アダプタ: キャラクター作成ウィザード開始エラー - {e}")
            raise
    
    def cancel(self) -> None:
        """ウィザードをキャンセル（旧インターフェース互換）"""
        try:
            character_creation_manager.close_character_creation()
            logger.debug("アダプタ: キャラクター作成ウィザードキャンセル")
        except Exception as e:
            logger.error(f"アダプタ: キャラクター作成ウィザードキャンセルエラー - {e}")
    
    def destroy(self) -> None:
        """ウィザードを破棄（旧インターフェース互換）"""
        try:
            character_creation_manager.close_character_creation()
            self.callback = None
            self.on_cancel = None
            self.character_data = {
                "name": "",
                "race": "",
                "class": "",
                "stats": None
            }
            logger.debug("アダプタ: キャラクター作成ウィザード破棄")
        except Exception as e:
            logger.error(f"アダプタ: キャラクター作成ウィザード破棄エラー - {e}")
    
    def set_callback(self, callback: Callable) -> None:
        """作成完了コールバックを設定（旧インターフェース互換）"""
        self.callback = callback
    
    def set_cancel_callback(self, callback: Callable) -> None:
        """キャンセルコールバックを設定（旧インターフェース互換）"""
        self.on_cancel = callback
    
    def _on_character_created(self, character: Character) -> None:
        """キャラクターが作成された時の処理"""
        # キャラクターデータを更新（互換性のため）
        self.character_data = {
            "name": character.name,
            "race": character.race,
            "class": character.character_class.value if hasattr(character.character_class, 'value') else str(character.character_class),
            "stats": character.base_stats
        }
        
        if self.callback:
            try:
                self.callback(character)
            except Exception as e:
                logger.error(f"アダプタ: 作成完了コールバックエラー - {e}")
    
    def _on_cancel(self) -> None:
        """キャンセルされた時の処理"""
        if self.on_cancel:
            try:
                self.on_cancel()
            except Exception as e:
                logger.error(f"アダプタ: キャンセルコールバックエラー - {e}")
    
    # 以下、旧インターフェースで使用されていた他のメソッドも必要に応じて実装
    def _default_cancel_handler(self) -> None:
        """デフォルトキャンセルハンドラ（旧インターフェース内部メソッド）"""
        self.cancel()
    
    # プロパティでアクセスできるようにする（旧コードとの互換性）
    @property
    def current_step(self) -> Optional[str]:
        """現在のステップ"""
        step = character_creation_manager.get_current_creation_step()
        if step:
            # 新しいenumから旧のenumに変換（必要に応じて）
            return step
        return None
    
    @property
    def is_creating(self) -> bool:
        """作成中かどうか"""
        return character_creation_manager.is_creating_character()


# 旧システムとの互換性を保つためのファクトリ関数
def create_character_creation_wizard(callback: Optional[Callable] = None) -> CharacterCreationAdapter:
    """
    キャラクター作成ウィザードを作成
    
    Args:
        callback: 作成完了時のコールバック
        
    Returns:
        CharacterCreationAdapter: アダプタインスタンス
    """
    return CharacterCreationAdapter(callback)