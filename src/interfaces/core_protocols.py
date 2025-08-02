"""
コアProtocol定義

型安全性を向上させるための基本的なProtocolを定義します。
これらのProtocolにより、hasattr/getattrによるランタイムチェックから
静的型チェックへ移行できます。
"""

from typing import Protocol, Any, Dict, Union, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    import pygame


class Cleanupable(Protocol):
    """リソースクリーンアップが可能なオブジェクト"""
    
    def cleanup(self) -> None:
        """リソースのクリーンアップを実行"""
        ...


class MessageSender(Protocol):
    """メッセージ送信が可能なオブジェクト"""
    
    def send_message(self, message_type: str, data: Dict[str, Any] = None) -> None:  # type: ignore
        """メッセージを送信"""
        ...


class MessageReceiver(Protocol):
    """メッセージ受信が可能なオブジェクト"""
    
    def receive_message(self, sender: Any, message_type: str, data: Dict[str, Any]) -> None:
        """メッセージを受信・処理"""
        ...


class Renderable(Protocol):
    """描画が可能なオブジェクト"""
    
    def draw(self, surface: "pygame.Surface") -> None:
        """指定されたサーフェースに描画"""
        ...


class Updatable(Protocol):
    """更新が可能なオブジェクト"""
    
    def update(self, delta_time: float) -> None:
        """指定された時間分だけ状態を更新"""
        ...


# 複合Protocol（複数の機能を組み合わせ）

class UIComponent(MessageSender, Cleanupable, Protocol):
    """UI要素の基本インターフェース"""
    pass


class GameComponent(Updatable, Renderable, Cleanupable, Protocol):
    """ゲーム要素の基本インターフェース"""
    pass


class WindowComponent(UIComponent, Updatable, Renderable, Protocol):
    """ウィンドウ要素の基本インターフェース"""
    pass