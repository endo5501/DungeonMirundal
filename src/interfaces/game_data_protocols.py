"""
ゲームデータアクセスProtocol定義

GameManager、パーティ、キャラクター、インベントリ等へのアクセスで使用される型安全なインターフェースを定義します。
hasattr(obj, 'get_party'), hasattr(char, 'inventory') パターンを型安全な呼び出しに置き換えます。
"""

from typing import Protocol, Any, Dict, Optional, List, TYPE_CHECKING, runtime_checkable
from .core_protocols import Cleanupable

if TYPE_CHECKING:
    from typing import Any as Party
    from typing import Any as Character  
    from typing import Any as Inventory


@runtime_checkable
class PartyAccessible(Protocol):
    """パーティ情報アクセス可能なオブジェクト"""
    
    def get_party(self) -> Optional["Party"]:
        """現在のパーティを取得"""
        ...


@runtime_checkable
class GameManagerAccessible(Protocol):
    """GameManagerアクセス可能なオブジェクト"""
    
    def get_game_manager(self) -> Any:
        """GameManagerを取得"""
        ...
    
    def set_game_manager(self, game_manager: Any) -> None:
        """GameManagerを設定"""
        ...


@runtime_checkable
class InventoryAccessible(Protocol):
    """インベントリアクセス可能なオブジェクト"""
    
    def get_inventory(self) -> Optional["Inventory"]:
        """インベントリを取得"""
        ...
    
    def add_item(self, item_id: str, quantity: int = 1) -> bool:
        """アイテムを追加"""
        ...
    
    def remove_item(self, item_id: str, quantity: int = 1) -> bool:
        """アイテムを削除"""
        ...


@runtime_checkable
class CharacterDataAccessible(Protocol):
    """キャラクターデータアクセス可能なオブジェクト"""
    
    def get_character(self, index: int) -> Optional["Character"]:
        """指定インデックスのキャラクターを取得"""
        ...
    
    def get_character_count(self) -> int:
        """キャラクター数を取得"""
        ...


@runtime_checkable
class PartyMember(Protocol):
    """パーティメンバーのインターフェース"""
    
    @property
    def name(self) -> str:
        """キャラクター名"""
        ...
    
    @property
    def level(self) -> int:
        """レベル"""
        ...
    
    @property
    def hp(self) -> int:
        """現在HP"""
        ...
    
    @property
    def max_hp(self) -> int:
        """最大HP"""
        ...
    
    @property
    def race(self) -> str:
        """種族"""
        ...
    
    @property
    def character_class(self) -> str:
        """職業"""
        ...


@runtime_checkable
class SaveableData(Protocol):
    """セーブ・ロード可能なデータ"""
    
    def save_data(self) -> Dict[str, Any]:
        """データを辞書形式で保存"""
        ...
    
    def load_data(self, data: Dict[str, Any]) -> bool:
        """辞書からデータを読み込み"""
        ...


@runtime_checkable
class PersistentGameManager(GameManagerAccessible, SaveableData, Protocol):
    """永続化対応GameManager"""
    
    def save_game(self, save_name: str) -> bool:
        """ゲームデータを保存"""
        ...
    
    def load_game(self, save_name: str) -> bool:
        """ゲームデータを読み込み"""
        ...
    
    def get_current_party(self) -> Optional["Party"]:
        """現在のパーティを取得"""
        ...


# 複合Protocol（複数機能の組み合わせ）

class FullGameDataAccess(PartyAccessible, GameManagerAccessible, InventoryAccessible, CharacterDataAccessible, Protocol):
    """すべてのゲームデータへのアクセス可能なインターフェース"""
    pass


class PartyManagement(PartyAccessible, CharacterDataAccessible, Protocol):
    """パーティ管理インターフェース"""
    
    def add_character_to_party(self, character: "Character") -> bool:
        """キャラクターをパーティに追加"""
        ...
    
    def remove_character_from_party(self, character_index: int) -> bool:
        """キャラクターをパーティから削除"""
        ...