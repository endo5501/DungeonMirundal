"""
Battle関連の型定義

戦闘システムの型安全性を保証
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Any, Optional, Union, Callable


class BattlePhase(Enum):
    """戦闘フェーズ"""
    BATTLE_START = "battle_start"
    PLAYER_ACTION = "player_action"
    TARGET_SELECTION = "target_selection"
    ACTION_EXECUTION = "action_execution"
    ENEMY_TURN = "enemy_turn"
    TURN_END = "turn_end"
    BATTLE_END = "battle_end"
    VICTORY = "victory"
    DEFEAT = "defeat"
    ESCAPE = "escape"


class BattleActionType(Enum):
    """戦闘アクションタイプ"""
    ATTACK = "attack"
    MAGIC = "magic"
    ITEM = "item"
    DEFEND = "defend"
    ESCAPE = "escape"
    SKILL = "skill"
    SPECIAL = "special"


class TargetType(Enum):
    """ターゲットタイプ"""
    SINGLE_ENEMY = "single_enemy"
    ALL_ENEMIES = "all_enemies"
    SINGLE_ALLY = "single_ally"
    ALL_ALLIES = "all_allies"
    SELF = "self"
    NONE = "none"


class StatusEffectType(Enum):
    """ステータス効果タイプ"""
    POISON = "poison"
    PARALYSIS = "paralysis"
    SLEEP = "sleep"
    CONFUSION = "confusion"
    CHARM = "charm"
    BUFF = "buff"
    DEBUFF = "debuff"
    REGENERATION = "regeneration"
    SHIELD = "shield"


@dataclass
class BattleAction:
    """戦闘アクション"""
    action_type: BattleActionType
    name: str
    description: str = ""
    enabled: bool = True
    mp_cost: int = 0
    target_type: TargetType = TargetType.SINGLE_ENEMY
    icon: Optional[str] = None
    hotkey: Optional[str] = None
    
    def __post_init__(self):
        if isinstance(self.action_type, str):
            self.action_type = BattleActionType(self.action_type)
        if isinstance(self.target_type, str):
            self.target_type = TargetType(self.target_type)


@dataclass
class CharacterStatus:
    """キャラクターステータス"""
    character: Any
    hp: int
    max_hp: int
    mp: int
    max_mp: int
    status_effects: List[Any] = field(default_factory=list)
    is_alive: bool = True
    position: tuple = (0, 0)  # UI上の位置
    
    @property
    def hp_percentage(self) -> float:
        """HP割合を取得"""
        return self.hp / self.max_hp if self.max_hp > 0 else 0.0
    
    @property
    def mp_percentage(self) -> float:
        """MP割合を取得"""
        return self.mp / self.max_mp if self.max_mp > 0 else 0.0


@dataclass
class EnemyStatus:
    """敵ステータス"""
    enemy: Any
    hp: int
    max_hp: int
    status_effects: List[Any] = field(default_factory=list)
    is_alive: bool = True
    position: tuple = (0, 0)  # UI上の位置
    is_visible: bool = True  # プレイヤーに見えるかどうか
    
    @property
    def hp_percentage(self) -> float:
        """HP割合を取得"""
        return self.hp / self.max_hp if self.max_hp > 0 else 0.0


@dataclass
class StatusEffect:
    """ステータス効果"""
    name: str
    effect_type: StatusEffectType
    duration: int
    power: int = 0
    description: str = ""
    icon: Optional[str] = None
    
    def __post_init__(self):
        if isinstance(self.effect_type, str):
            self.effect_type = StatusEffectType(self.effect_type)


@dataclass
class BattleLogEntry:
    """戦闘ログエントリ"""
    message: str
    timestamp: float
    entry_type: str = "action"  # action, damage, healing, status, system
    character: Optional[Any] = None
    target: Optional[Any] = None
    value: Optional[int] = None  # ダメージ量、回復量など


@dataclass
class BattleLayout:
    """戦闘UIレイアウト"""
    party_status_width: int = 300
    party_status_height: int = 200
    enemy_status_width: int = 400
    enemy_status_height: int = 150
    action_menu_width: int = 200
    action_menu_height: int = 300
    battle_log_width: int = 500
    battle_log_height: int = 200
    status_bar_height: int = 20
    button_height: int = 40
    panel_padding: int = 10
    window_min_width: int = 1024
    window_min_height: int = 768
    
    def calculate_party_positions(self, party_size: int) -> List[tuple]:
        """パーティメンバーの位置を計算"""
        positions = []
        for i in range(party_size):
            x = self.panel_padding
            y = self.panel_padding + i * (self.status_bar_height + 10)
            positions.append((x, y))
        return positions
    
    def calculate_enemy_positions(self, enemy_count: int) -> List[tuple]:
        """敵の位置を計算"""
        positions = []
        start_x = self.window_min_width - self.enemy_status_width - self.panel_padding
        for i in range(enemy_count):
            x = start_x
            y = self.panel_padding + i * (self.status_bar_height + 10)
            positions.append((x, y))
        return positions


@dataclass
class BattleConfig:
    """戦闘ウィンドウ設定"""
    battle_manager: Any
    party: Any
    enemies: Any
    show_battle_log: bool = True
    show_status_effects: bool = True
    enable_keyboard_shortcuts: bool = True
    enable_animations: bool = True
    auto_advance_log: bool = False
    log_max_entries: int = 100
    layout: BattleLayout = field(default_factory=BattleLayout)
    
    def validate(self) -> None:
        """設定の検証"""
        if not self.battle_manager:
            raise ValueError("Battle manager is required")
        if not self.party:
            raise ValueError("Party is required")
        if not self.enemies:
            raise ValueError("Enemies are required")


@dataclass
class ActionMenuEntry:
    """アクションメニューエントリ"""
    action: BattleAction
    button: Optional[Any] = None  # pygame_gui.elements.UIButton
    enabled: bool = True
    visible: bool = True


@dataclass
class TargetInfo:
    """ターゲット情報"""
    target: Any
    target_type: TargetType
    position: tuple
    selectable: bool = True
    highlighted: bool = False
    
    def __post_init__(self):
        if isinstance(self.target_type, str):
            self.target_type = TargetType(self.target_type)


@dataclass
class BattleTurn:
    """戦闘ターン情報"""
    turn_number: int
    current_character: Optional[Any] = None
    phase: BattlePhase = BattlePhase.PLAYER_ACTION
    actions_remaining: int = 1
    
    def __post_init__(self):
        if isinstance(self.phase, str):
            self.phase = BattlePhase(self.phase)


@dataclass
class BattleResult:
    """戦闘結果"""
    result_type: str  # victory, defeat, escape
    exp_gained: int = 0
    gold_gained: int = 0
    items_gained: List[Any] = field(default_factory=list)
    battle_duration: float = 0.0
    turns_taken: int = 0


@dataclass
class KeyboardShortcut:
    """キーボードショートカット"""
    key: int  # pygame key constant
    action_type: BattleActionType
    description: str
    modifier: int = 0  # pygame modifier
    
    def __post_init__(self):
        if isinstance(self.action_type, str):
            self.action_type = BattleActionType(self.action_type)


@dataclass
class AnimationInfo:
    """アニメーション情報"""
    animation_type: str
    target: Any
    duration: float
    properties: Dict[str, Any] = field(default_factory=dict)
    callback: Optional[Callable] = None


@dataclass
class BattleUIState:
    """戦闘UI状態"""
    current_phase: BattlePhase
    selected_action: Optional[BattleActionType] = None
    selected_target: Optional[Any] = None
    menu_stack: List[str] = field(default_factory=list)  # メニューの階層
    animations_playing: List[AnimationInfo] = field(default_factory=list)
    
    def __post_init__(self):
        if isinstance(self.current_phase, str):
            self.current_phase = BattlePhase(self.current_phase)
        if isinstance(self.selected_action, str):
            self.selected_action = BattleActionType(self.selected_action)


@dataclass
class BattleMessage:
    """戦闘メッセージ"""
    message_type: str
    content: Dict[str, Any]
    timestamp: float
    priority: int = 0  # 0=normal, 1=high, 2=critical