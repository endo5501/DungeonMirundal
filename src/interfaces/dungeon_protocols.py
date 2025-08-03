"""
ダンジョンシステムProtocol定義

ダンジョンセル、レベル、宝箱システム等で使用される型安全なインターフェースを定義します。
セル情報・レベル管理のアクセスで使用されるhasattrパターンを型安全な呼び出しに置き換えます。
"""

from typing import Protocol, Any, Dict, Optional, List, Tuple, TYPE_CHECKING, runtime_checkable

if TYPE_CHECKING:
    from typing import Any as Party


@runtime_checkable
class DungeonCell(Protocol):
    """ダンジョンセルのインターフェース"""
    
    def get_contents(self) -> List[Any]:
        """セルの内容物を取得"""
        ...
    
    def is_passable(self) -> bool:
        """通行可能かチェック"""
        ...
    
    def has_treasure(self) -> bool:
        """宝箱があるかチェック"""
        ...
    
    def has_monster(self) -> bool:
        """モンスターがいるかチェック"""
        ...
    
    def get_cell_type(self) -> str:
        """セルタイプを取得"""
        ...


@runtime_checkable
class DungeonLevel(Protocol):
    """ダンジョンレベルのインターフェース"""
    
    def get_cell(self, x: int, y: int) -> Optional[DungeonCell]:
        """指定座標のセルを取得"""
        ...
    
    def get_size(self) -> Tuple[int, int]:
        """ダンジョンサイズを取得"""
        ...
    
    def get_level_number(self) -> int:
        """レベル番号を取得"""
        ...
    
    def get_entrance_position(self) -> Tuple[int, int]:
        """入口位置を取得"""
        ...
    
    def get_exit_position(self) -> Tuple[int, int]:
        """出口位置を取得"""
        ...


@runtime_checkable
class DungeonManager(Protocol):
    """ダンジョン管理インターフェース"""
    
    def get_current_level(self) -> Optional[DungeonLevel]:
        """現在のレベルを取得"""
        ...
    
    def change_level(self, level_number: int) -> bool:
        """レベルを変更"""
        ...
    
    def get_party_position(self) -> Tuple[int, int]:
        """パーティ位置を取得"""
        ...
    
    def move_party(self, direction: str) -> bool:
        """パーティを移動"""
        ...
    
    def can_move_to(self, x: int, y: int) -> bool:
        """指定位置に移動可能かチェック"""
        ...


@runtime_checkable
class TreasureSystem(Protocol):
    """宝箱システムのインターフェース"""
    
    def open_treasure(self, party: "Party", treasure_id: str) -> Dict[str, Any]:
        """宝箱を開く"""
        ...
    
    def is_treasure_opened(self, treasure_id: str) -> bool:
        """宝箱が開かれているかチェック"""
        ...
    
    def get_treasure_contents(self, treasure_id: str) -> List[Dict[str, Any]]:
        """宝箱の内容物を取得"""
        ...
    
    def generate_random_treasure(self, level: int) -> Dict[str, Any]:
        """ランダム宝箱を生成"""
        ...


@runtime_checkable
class MonsterEncounter(Protocol):
    """モンスター遭遇システムのインターフェース"""
    
    def check_encounter(self, party: "Party", cell: DungeonCell) -> bool:
        """モンスター遭遇をチェック"""
        ...
    
    def generate_encounter(self, level: int) -> List[Dict[str, Any]]:
        """モンスター遭遇を生成"""
        ...
    
    def get_encounter_rate(self, cell_type: str) -> float:
        """遭遇率を取得"""
        ...


@runtime_checkable
class DungeonNavigation(Protocol):
    """ダンジョンナビゲーションインターフェース"""
    
    def get_visible_area(self, x: int, y: int, vision_range: int) -> List[Tuple[int, int]]:
        """見える範囲を取得"""
        ...
    
    def is_wall(self, x: int, y: int) -> bool:
        """壁かどうかチェック"""
        ...
    
    def get_direction_to(self, from_pos: Tuple[int, int], to_pos: Tuple[int, int]) -> str:
        """目標への方向を取得"""
        ...
    
    def find_path(self, start: Tuple[int, int], goal: Tuple[int, int]) -> List[Tuple[int, int]]:
        """経路を探索"""
        ...


@runtime_checkable
class DungeonRenderer(Protocol):
    """ダンジョン描画インターフェース"""
    
    def render_3d_view(self, party_pos: Tuple[int, int], direction: str) -> Any:
        """3Dビューを描画"""
        ...
    
    def render_minimap(self, level: DungeonLevel, party_pos: Tuple[int, int]) -> Any:
        """ミニマップを描画"""
        ...
    
    def get_wall_texture(self, cell_type: str) -> str:
        """壁テクスチャを取得"""
        ...


# 複合Protocol（複数機能の組み合わせ）

class CompleteDungeonSystem(DungeonManager, TreasureSystem, MonsterEncounter, DungeonNavigation, Protocol):
    """完全なダンジョンシステムインターフェース"""
    
    def initialize_dungeon(self, dungeon_id: str) -> bool:
        """ダンジョンを初期化"""
        ...
    
    def save_dungeon_state(self) -> Dict[str, Any]:
        """ダンジョン状態を保存"""
        ...
    
    def load_dungeon_state(self, state: Dict[str, Any]) -> bool:
        """ダンジョン状態を読み込み"""
        ...


class InteractiveDungeonCell(DungeonCell, TreasureSystem, MonsterEncounter, Protocol):
    """インタラクティブなダンジョンセル"""
    
    def interact_with_party(self, party: "Party") -> Dict[str, Any]:
        """パーティとの相互作用"""
        ...
    
    def get_interaction_options(self) -> List[str]:
        """利用可能な相互作用オプション"""
        ...