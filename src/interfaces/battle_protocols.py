"""
戦闘関連Protocol定義

戦闘システムで使用される型安全なインターフェースを定義します。
"""

from typing import Protocol, Any, Dict, List, Optional, runtime_checkable
from .core_protocols import MessageSender, Cleanupable


class BattleWindow(MessageSender, Cleanupable, Protocol):
    """戦闘ウィンドウのインターフェース"""
    
    def cleanup_ui(self) -> None:
        """UIリソースのクリーンアップ"""
        ...


class BattleManager(Protocol):
    """戦闘管理のインターフェース"""
    
    def start_battle(self, party: Any, enemies: List[Any], context: Any) -> bool:
        """戦闘を開始"""
        ...
    
    def end_battle(self, victory: bool = False) -> bool:
        """戦闘を終了"""
        ...
    
    def is_battle_active(self) -> bool:
        """戦闘が進行中かどうか"""
        ...


@runtime_checkable
class WindowMessageHandler(Protocol):
    """ウィンドウメッセージハンドラーのインターフェース"""
    
    def handle_orphan_message(self, sender: Any, message_type: str, data: Dict[str, Any]) -> None:
        """孤立メッセージを処理"""
        ...