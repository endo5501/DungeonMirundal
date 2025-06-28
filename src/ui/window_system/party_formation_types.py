"""
PartyFormationWindow 型定義

パーティ編成ウィンドウに関する型定義
"""

from enum import Enum
from typing import Dict, Any, Optional, List, Callable
from dataclasses import dataclass


class PartyPosition(Enum):
    """パーティポジション"""
    FRONT_LEFT = "front_left"
    FRONT_CENTER = "front_center"
    FRONT_RIGHT = "front_right"
    BACK_LEFT = "back_left"
    BACK_CENTER = "back_center"
    BACK_RIGHT = "back_right"
    
    @property
    def is_front_row(self) -> bool:
        """前衛ポジションかどうか"""
        return self in [PartyPosition.FRONT_LEFT, PartyPosition.FRONT_CENTER, PartyPosition.FRONT_RIGHT]
    
    @property
    def is_back_row(self) -> bool:
        """後衛ポジションかどうか"""
        return self in [PartyPosition.BACK_LEFT, PartyPosition.BACK_CENTER, PartyPosition.BACK_RIGHT]
    
    @property
    def index(self) -> int:
        """ポジションのインデックス（0-5）"""
        positions = [
            PartyPosition.FRONT_LEFT, PartyPosition.FRONT_CENTER, PartyPosition.FRONT_RIGHT,
            PartyPosition.BACK_LEFT, PartyPosition.BACK_CENTER, PartyPosition.BACK_RIGHT
        ]
        return positions.index(self)
    
    @classmethod
    def from_index(cls, index: int) -> 'PartyPosition':
        """インデックスからポジションを取得"""
        positions = [
            cls.FRONT_LEFT, cls.FRONT_CENTER, cls.FRONT_RIGHT,
            cls.BACK_LEFT, cls.BACK_CENTER, cls.BACK_RIGHT
        ]
        if 0 <= index < len(positions):
            return positions[index]
        raise ValueError(f"Invalid position index: {index}")
    
    def get_adjacent_positions(self) -> List['PartyPosition']:
        """隣接するポジションを取得"""
        adjacents = {
            PartyPosition.FRONT_LEFT: [PartyPosition.FRONT_CENTER, PartyPosition.BACK_LEFT],
            PartyPosition.FRONT_CENTER: [PartyPosition.FRONT_LEFT, PartyPosition.FRONT_RIGHT, PartyPosition.BACK_CENTER],
            PartyPosition.FRONT_RIGHT: [PartyPosition.FRONT_CENTER, PartyPosition.BACK_RIGHT],
            PartyPosition.BACK_LEFT: [PartyPosition.FRONT_LEFT, PartyPosition.BACK_CENTER],
            PartyPosition.BACK_CENTER: [PartyPosition.BACK_LEFT, PartyPosition.BACK_RIGHT, PartyPosition.FRONT_CENTER],
            PartyPosition.BACK_RIGHT: [PartyPosition.BACK_CENTER, PartyPosition.FRONT_RIGHT]
        }
        return adjacents.get(self, [])


@dataclass
class FormationConfig:
    """パーティ編成設定"""
    party: Any  # Partyオブジェクト
    available_characters: List[Any]  # 利用可能キャラクターリスト
    max_party_size: int = 6
    allow_empty_positions: bool = True
    enable_drag_and_drop: bool = True
    show_character_details: bool = True
    title: str = "パーティ編成"
    
    def validate(self) -> None:
        """設定の妥当性をチェック"""
        if self.party is None:
            raise ValueError("Formation config must contain 'party'")
        if self.available_characters is None:
            raise ValueError("Formation config must contain 'available_characters'")
        if self.max_party_size <= 0 or self.max_party_size > 6:
            raise ValueError("max_party_size must be between 1 and 6")


@dataclass
class FormationValidationResult:
    """編成検証結果"""
    is_valid: bool
    error_message: str = ""
    warnings: List[str] = None
    
    def __post_init__(self):
        if self.warnings is None:
            self.warnings = []
    
    @classmethod
    def valid(cls) -> 'FormationValidationResult':
        """有効な結果を作成"""
        return cls(is_valid=True)
    
    @classmethod
    def invalid(cls, message: str, warnings: List[str] = None) -> 'FormationValidationResult':
        """無効な結果を作成"""
        return cls(is_valid=False, error_message=message, warnings=warnings or [])


@dataclass
class CharacterSlot:
    """キャラクタースロット"""
    position: PartyPosition
    character: Optional[Any] = None
    is_locked: bool = False
    is_selected: bool = False
    ui_element: Optional[Any] = None
    
    @property
    def is_empty(self) -> bool:
        """空のスロットかどうか"""
        return self.character is None
    
    @property
    def is_occupied(self) -> bool:
        """キャラクターが配置されているかどうか"""
        return self.character is not None
    
    def can_accept_character(self, character: Any) -> bool:
        """キャラクターを受け入れ可能かどうか"""
        if self.is_locked:
            return False
        return self.is_empty or character != self.character


@dataclass
class DragDropState:
    """ドラッグアンドドロップ状態"""
    is_active: bool = False
    source_position: Optional[PartyPosition] = None
    target_position: Optional[PartyPosition] = None
    dragged_character: Optional[Any] = None
    
    def start_drag(self, position: PartyPosition, character: Any) -> None:
        """ドラッグ開始"""
        self.is_active = True
        self.source_position = position
        self.dragged_character = character
        self.target_position = None
    
    def set_target(self, position: PartyPosition) -> None:
        """ドラッグターゲット設定"""
        self.target_position = position
    
    def end_drag(self) -> None:
        """ドラッグ終了"""
        self.is_active = False
        self.source_position = None
        self.target_position = None
        self.dragged_character = None


@dataclass
class FormationChange:
    """編成変更情報"""
    change_type: str  # 'add', 'remove', 'move'
    character: Any
    from_position: Optional[PartyPosition] = None
    to_position: Optional[PartyPosition] = None
    timestamp: Optional[float] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """辞書形式に変換"""
        return {
            'change_type': self.change_type,
            'character': self.character,
            'from_position': self.from_position.value if self.from_position else None,
            'to_position': self.to_position.value if self.to_position else None,
            'timestamp': self.timestamp
        }


# コールバック型定義
CharacterValidator = Callable[[Any, PartyPosition], bool]
FormationChangeCallback = Callable[[FormationChange], None]
PositionClickCallback = Callable[[PartyPosition, Any], None]