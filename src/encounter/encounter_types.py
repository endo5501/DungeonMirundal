"""エンカウンター関連の型定義

循環インポートを避けるため、共通の型定義を分離したモジュール
"""

from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass, field
from enum import Enum


class EncounterType(Enum):
    """エンカウンタータイプ"""
    NORMAL = "normal"                   # 通常エンカウンター
    AMBUSH = "ambush"                   # 奇襲
    TREASURE_GUARDIAN = "treasure_guardian"  # 宝箱の守護者
    BOSS = "boss"                       # ボス
    SPECIAL_EVENT = "special_event"     # 特殊イベント
    TRAP_MONSTER = "trap_monster"       # トラップモンスター


class EncounterResult(Enum):
    """エンカウンター結果"""
    COMBAT_START = "combat_start"       # 戦闘開始
    AVOIDED = "avoided"                 # 回避成功
    NEGOTIATED = "negotiated"          # 交渉成功
    SPECIAL_EVENT = "special_event"     # 特殊イベント
    FLED = "fled"                      # 逃走成功


class MonsterRank(Enum):
    """モンスターランク"""
    WEAK = "weak"           # 弱い
    NORMAL = "normal"       # 通常
    STRONG = "strong"       # 強い
    ELITE = "elite"         # エリート
    BOSS = "boss"           # ボス


@dataclass
class MonsterGroup:
    """モンスターグループ"""
    monster_ids: List[str]
    formation: str = "standard"        # 隊形
    total_level: int = 0               # 総レベル
    rank: MonsterRank = MonsterRank.NORMAL
    special_abilities: List[str] = field(default_factory=list)
    treasure_modifier: float = 1.0     # 宝物倍率
    experience_modifier: float = 1.0   # 経験値倍率


@dataclass 
class EncounterEvent:
    """エンカウンターイベント"""
    encounter_type: EncounterType
    monster_group: Optional[MonsterGroup]
    location: Tuple[int, int, int]     # (x, y, level)
    dungeon_attribute: Any             # DungeonAttributeの循環インポートを避けるため Any
    can_flee: bool = True
    can_negotiate: bool = False
    special_conditions: Dict[str, Any] = field(default_factory=dict)
    description: str = ""
    
    def __post_init__(self):
        """EncounterEvent初期化後の処理"""
        # dungeon_attributeの型チェックを実行時に行う
        if hasattr(self.dungeon_attribute, 'value'):
            # DungeonAttributeのEnum値として扱う
            pass
        else:
            # 必要に応じて変換処理
            pass