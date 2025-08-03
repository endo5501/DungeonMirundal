"""
UIライフサイクルProtocol定義

UI要素の生成・破棄・更新に関する型安全なインターフェースを定義します。
hasattr(element, 'kill') パターンを型安全な呼び出しに置き換えます。
"""

from typing import Protocol, Any, List, Optional, Dict, TYPE_CHECKING, runtime_checkable
from .core_protocols import Cleanupable

if TYPE_CHECKING:
    from typing import Any as pygame
    from typing import Any as pygame_gui


@runtime_checkable
class UIDestructible(Protocol):
    """UI要素の破棄が可能なオブジェクト"""
    
    def kill(self) -> None:
        """UI要素を破棄（pygame_gui標準）"""
        ...


@runtime_checkable
class UIContainer(Protocol):
    """UI要素のコンテナ管理が可能なオブジェクト"""
    
    def add_element(self, element: Any) -> None:
        """UI要素をコンテナに追加"""
        ...
    
    def remove_element(self, element: Any) -> None:
        """UI要素をコンテナから削除"""
        ...
    
    def get_elements(self) -> List[Any]:
        """コンテナ内の全UI要素を取得"""
        ...


@runtime_checkable
class UIRefreshable(Protocol):
    """UI表示の更新が可能なオブジェクト"""
    
    def refresh(self) -> None:
        """UI表示を更新"""
        ...
    
    def update_display(self) -> None:
        """表示内容を最新状態に更新"""
        ...


@runtime_checkable
class UISelectable(Protocol):
    """UI要素の選択が可能なオブジェクト"""
    
    def select(self) -> None:
        """UI要素を選択状態にする"""
        ...
    
    def deselect(self) -> None:
        """UI要素の選択を解除する"""
        ...
    
    def is_selected(self) -> bool:
        """選択状態かどうかを確認"""
        ...


class ServicePanel(UIDestructible, UIRefreshable, Cleanupable, Protocol):
    """サービスパネルのインターフェース"""
    
    def setup_ui(self) -> None:
        """UIセットアップ"""
        ...
    
    def handle_action(self, action: str, params: Dict[str, Any]) -> Any:
        """アクション処理"""
        ...


class NavigationPanel(UIDestructible, Protocol):
    """ナビゲーションパネルのインターフェース"""
    
    def navigate_to(self, target: str) -> bool:
        """指定されたターゲットにナビゲート"""
        ...
    
    def get_current_location(self) -> str:
        """現在の場所を取得"""
        ...


# 複合Protocol（UI要素の組み合わせ）

class ManagedUIElement(UIDestructible, UIRefreshable, Protocol):
    """管理されたUI要素の基本インターフェース"""
    pass


class InteractiveUIElement(ManagedUIElement, UISelectable, Protocol):
    """対話型UI要素のインターフェース"""
    pass


class UIElementContainer(UIContainer, ManagedUIElement, Protocol):
    """UI要素コンテナの統合インターフェース"""
    pass