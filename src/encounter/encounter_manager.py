"""エンカウンター管理システム"""

from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass, field
from enum import Enum
import random
import hashlib

from src.dungeon.dungeon_manager import DungeonState
from src.dungeon.dungeon_generator import DungeonAttribute, DungeonLevel
from src.character.party import Party
from src.utils.logger import logger

# エンカウンター定数
MAX_DUNGEON_LEVEL = 20
BASE_LEVELS_PER_TIER = 4
MAX_TIER_LEVEL = 5
ATTRIBUTE_ABILITY_CHANCE = 0.3
AMBUSH_ABILITY_CHANCE = 0.5
TREASURE_GUARDIAN_ABILITY_CHANCE = 0.7
DEEP_DUNGEON_THRESHOLD = 15
ENHANCED_MONSTER_CHANCE = 0.2

# 成功率関連定数
BASE_FLEE_CHANCE = 0.5
BASE_NEGOTIATION_CHANCE = 0.2
TREASURE_GUARDIAN_NEGOTIATION_BONUS = 0.3
AGILITY_BONUS_RATE = 0.05
CHARISMA_BONUS_RATE = 0.03
BASE_AGILITY = 12
BASE_CHARISMA = 12
MIN_FLEE_CHANCE = 0.05
MAX_FLEE_CHANCE = 0.95
MIN_NEGOTIATION_CHANCE = 0.01
MAX_NEGOTIATION_CHANCE = 0.8


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
    dungeon_attribute: DungeonAttribute
    can_flee: bool = True
    can_negotiate: bool = False
    special_conditions: Dict[str, Any] = field(default_factory=dict)
    description: str = ""


class EncounterManager:
    """エンカウンター管理システム"""
    
    def __init__(self):
        self.current_party: Optional[Party] = None
        self.current_dungeon: Optional[DungeonState] = None
        
        # エンカウンターテーブル（属性別）
        self.encounter_tables: Dict[DungeonAttribute, Dict[int, List[str]]] = {}
        self._initialize_encounter_tables()
        
        # エンカウンター統計
        self.encounter_statistics: Dict[str, int] = {
            'total_encounters': 0,
            'combat_victories': 0,
            'fled_encounters': 0,
            'avoided_encounters': 0
        }
        
        logger.info("EncounterManager初期化完了")
    
    def set_party(self, party: Optional[Party]):
        """パーティ設定"""
        self.current_party = party
        if party is not None:
            logger.info(f"パーティ{party.name}を設定しました")
        else:
            logger.info("パーティをクリアしました")
    
    def set_dungeon(self, dungeon_state: DungeonState):
        """ダンジョン設定"""
        self.current_dungeon = dungeon_state
        logger.info(f"ダンジョン{dungeon_state.dungeon_id}を設定しました")
    
    def generate_encounter(self, encounter_type: str, level: int, 
                          dungeon_attribute: DungeonAttribute,
                          location: Tuple[int, int, int]) -> EncounterEvent:
        """エンカウンター生成"""
        encounter_enum = self._parse_encounter_type(encounter_type)
        monster_group = self._generate_monster_group(encounter_enum, level, dungeon_attribute, location)
        
        encounter_event = self._create_encounter_event(encounter_enum, monster_group, location, dungeon_attribute)
        self._finalize_encounter(encounter_event, level)
        
        logger.info(f"エンカウンター生成: {encounter_enum.value} at {location}")
        return encounter_event
    
    def _create_encounter_event(self, encounter_enum: EncounterType, monster_group: MonsterGroup,
                               location: Tuple[int, int, int], dungeon_attribute: DungeonAttribute) -> EncounterEvent:
        """エンカウンターイベント作成"""
        return EncounterEvent(
            encounter_type=encounter_enum,
            monster_group=monster_group,
            location=location,
            dungeon_attribute=dungeon_attribute
        )
    
    def _finalize_encounter(self, encounter_event: EncounterEvent, level: int):
        """エンカウンターの最終化処理"""
        self._apply_special_conditions(encounter_event, level)
        encounter_event.description = self._generate_encounter_description(encounter_event)
        self.encounter_statistics['total_encounters'] += 1
    
    def _initialize_encounter_tables(self):
        """エンカウンターテーブル初期化"""
        # 各属性・レベル別のモンスターテーブル
        # 実際の実装では外部ファイル（YAML）から読み込み
        
        base_monsters = {
            1: ["goblin", "rat", "skeleton"],
            2: ["orc", "spider", "zombie"],
            3: ["hobgoblin", "dire_wolf", "wraith"],
            4: ["ogre", "troll", "vampire"],
            5: ["dragon", "lich", "demon"]
        }
        
        for attribute in DungeonAttribute:
            self.encounter_tables[attribute] = {}
            
            for level in range(1, MAX_DUNGEON_LEVEL + 1):  # レベル1-20
                # 基本レベルを計算
                base_level = min(MAX_TIER_LEVEL, (level - 1) // BASE_LEVELS_PER_TIER + 1)
                monsters = base_monsters.get(base_level, ["unknown"])
                
                # 属性による変更
                attribute_monsters = self._apply_attribute_variation(monsters, attribute)
                self.encounter_tables[attribute][level] = attribute_monsters
    
    def _apply_attribute_variation(self, base_monsters: List[str], attribute: DungeonAttribute) -> List[str]:
        """属性によるモンスター変化"""
        attribute_prefixes = {
            DungeonAttribute.FIRE: "flame_",
            DungeonAttribute.ICE: "frost_",
            DungeonAttribute.LIGHTNING: "storm_",
            DungeonAttribute.DARK: "shadow_",
            DungeonAttribute.LIGHT: "holy_"
        }
        
        prefix = attribute_prefixes.get(attribute, "")
        if prefix:
            return [f"{prefix}{monster}" for monster in base_monsters] + base_monsters
        return base_monsters
    
    def _parse_encounter_type(self, encounter_type: str) -> EncounterType:
        """エンカウンタータイプ解析"""
        type_map = {
            "normal": EncounterType.NORMAL,
            "ambush": EncounterType.AMBUSH,
            "treasure_guardian": EncounterType.TREASURE_GUARDIAN
        }
        return type_map.get(encounter_type, EncounterType.NORMAL)
    
    def _generate_monster_group(self, encounter_type: EncounterType, level: int,
                               attribute: DungeonAttribute, location: Tuple[int, int, int]) -> MonsterGroup:
        """モンスターグループ生成"""
        
        # 位置ベースのシード生成（一貫性のため）
        location_seed = hashlib.md5(f"{location[0]}_{location[1]}_{location[2]}".encode()).hexdigest()
        rng = random.Random(int(location_seed[:8], 16) + level)
        
        # エンカウンタータイプによるグループサイズ決定
        group_sizes = {
            EncounterType.NORMAL: (1, 4),
            EncounterType.AMBUSH: (2, 6),
            EncounterType.TREASURE_GUARDIAN: (1, 2),
            EncounterType.BOSS: (1, 1),
            EncounterType.TRAP_MONSTER: (1, 3)
        }
        
        min_size, max_size = group_sizes.get(encounter_type, (1, 3))
        group_size = rng.randint(min_size, max_size)
        
        # モンスター選択
        available_monsters = self.encounter_tables.get(attribute, {}).get(level, ["unknown"])
        
        monster_ids = []
        for _ in range(group_size):
            monster_id = rng.choice(available_monsters)
            monster_ids.append(monster_id)
        
        # ランク決定
        rank = self._determine_monster_rank(encounter_type, level, rng)
        
        # 特殊能力
        special_abilities = self._generate_special_abilities(encounter_type, attribute, rng)
        
        # 修正値計算
        treasure_modifier, exp_modifier = self._calculate_modifiers(encounter_type, rank)
        
        return MonsterGroup(
            monster_ids=monster_ids,
            formation=self._determine_formation(group_size, encounter_type),
            total_level=level * group_size,
            rank=rank,
            special_abilities=special_abilities,
            treasure_modifier=treasure_modifier,
            experience_modifier=exp_modifier
        )
    
    def _determine_monster_rank(self, encounter_type: EncounterType, level: int, rng: random.Random) -> MonsterRank:
        """モンスターランク決定"""
        if encounter_type == EncounterType.BOSS:
            return MonsterRank.BOSS
        
        rank_probabilities = self._calculate_base_rank_probabilities(level)
        self._adjust_probabilities_by_encounter_type(rank_probabilities, encounter_type)
        self._normalize_probabilities(rank_probabilities)
        
        return self._select_rank_by_probability(rank_probabilities, rng)
    
    def _calculate_base_rank_probabilities(self, level: int) -> Dict[MonsterRank, float]:
        """レベルベースのランク確率を計算"""
        return {
            MonsterRank.WEAK: max(0.1, 0.4 - level * 0.02),
            MonsterRank.NORMAL: 0.5,
            MonsterRank.STRONG: min(0.3, level * 0.02),
            MonsterRank.ELITE: min(0.1, max(0, level - 10) * 0.01)
        }
    
    def _adjust_probabilities_by_encounter_type(self, probabilities: Dict[MonsterRank, float], encounter_type: EncounterType):
        """エンカウンタータイプによる確率調整"""
        if encounter_type == EncounterType.AMBUSH:
            probabilities[MonsterRank.STRONG] *= 1.5
        elif encounter_type == EncounterType.TREASURE_GUARDIAN:
            probabilities[MonsterRank.ELITE] *= 2.0
    
    def _normalize_probabilities(self, probabilities: Dict[MonsterRank, float]):
        """確率の正規化"""
        total_prob = sum(probabilities.values())
        for rank in probabilities:
            probabilities[rank] /= total_prob
    
    def _select_rank_by_probability(self, probabilities: Dict[MonsterRank, float], rng: random.Random) -> MonsterRank:
        """確率に基づいたランク選択"""
        rand_val = rng.random()
        cumulative = 0
        for rank, prob in probabilities.items():
            cumulative += prob
            if rand_val <= cumulative:
                return rank
        return MonsterRank.NORMAL
    
    def _generate_special_abilities(self, encounter_type: EncounterType, 
                                   attribute: DungeonAttribute, rng: random.Random) -> List[str]:
        """特殊能力生成"""
        abilities = []
        
        # 属性ベースの能力
        attribute_abilities = {
            DungeonAttribute.FIRE: ["fire_breath", "burning_aura"],
            DungeonAttribute.ICE: ["ice_blast", "freezing_touch"],
            DungeonAttribute.LIGHTNING: ["lightning_bolt", "shock_aura"],
            DungeonAttribute.DARK: ["shadow_step", "darkness"],
            DungeonAttribute.LIGHT: ["holy_light", "blessing"]
        }
        
        if attribute in attribute_abilities and rng.random() < ATTRIBUTE_ABILITY_CHANCE:
            abilities.append(rng.choice(attribute_abilities[attribute]))
        
        # エンカウンタータイプベースの能力
        if encounter_type == EncounterType.AMBUSH and rng.random() < AMBUSH_ABILITY_CHANCE:
            abilities.append("surprise_attack")
        elif encounter_type == EncounterType.TREASURE_GUARDIAN and rng.random() < TREASURE_GUARDIAN_ABILITY_CHANCE:
            abilities.append("treasure_bond")
        
        return abilities
    
    def _determine_formation(self, group_size: int, encounter_type: EncounterType) -> str:
        """隊形決定"""
        if group_size == 1:
            return "single"
        elif group_size <= 2:
            return "pair"
        elif group_size <= 4:
            return "line" if encounter_type == EncounterType.AMBUSH else "standard"
        else:
            return "horde"
    
    def _calculate_modifiers(self, encounter_type: EncounterType, rank: MonsterRank) -> Tuple[float, float]:
        """修正値計算"""
        base_treasure = 1.0
        base_exp = 1.0
        
        # エンカウンタータイプによる修正
        type_modifiers = {
            EncounterType.TREASURE_GUARDIAN: (2.0, 1.5),
            EncounterType.BOSS: (3.0, 2.0),
            EncounterType.AMBUSH: (0.8, 1.2),
            EncounterType.TRAP_MONSTER: (0.5, 0.8)
        }
        
        if encounter_type in type_modifiers:
            treasure_mod, exp_mod = type_modifiers[encounter_type]
            base_treasure *= treasure_mod
            base_exp *= exp_mod
        
        # ランクによる修正
        rank_modifiers = {
            MonsterRank.WEAK: (0.5, 0.7),
            MonsterRank.NORMAL: (1.0, 1.0),
            MonsterRank.STRONG: (1.5, 1.3),
            MonsterRank.ELITE: (2.0, 1.8),
            MonsterRank.BOSS: (4.0, 3.0)
        }
        
        if rank in rank_modifiers:
            treasure_mod, exp_mod = rank_modifiers[rank]
            base_treasure *= treasure_mod
            base_exp *= exp_mod
        
        return base_treasure, base_exp
    
    def _apply_special_conditions(self, encounter: EncounterEvent, level: int):
        """特殊条件適用"""
        
        # 奇襲の場合
        if encounter.encounter_type == EncounterType.AMBUSH:
            encounter.can_flee = False  # 最初のターンは逃走不可
            encounter.special_conditions["surprise_round"] = True
        
        # ボスの場合
        elif encounter.encounter_type == EncounterType.BOSS:
            encounter.can_flee = False
            encounter.special_conditions["boss_battle"] = True
        
        # 宝箱守護者の場合
        elif encounter.encounter_type == EncounterType.TREASURE_GUARDIAN:
            encounter.can_negotiate = True
            encounter.special_conditions["guarding_treasure"] = True
        
        # 深い階層での特殊条件
        if level > DEEP_DUNGEON_THRESHOLD:
            encounter.special_conditions["deep_dungeon"] = True
            if random.random() < ENHANCED_MONSTER_CHANCE:
                encounter.special_conditions["enhanced_monsters"] = True
    
    def _generate_encounter_description(self, encounter: EncounterEvent) -> str:
        """エンカウンター説明文生成"""
        if not encounter.monster_group:
            return "何かが近づいてくる..."
        
        group = encounter.monster_group
        count = len(group.monster_ids)
        
        # 基本的な説明
        if count == 1:
            description = f"{group.monster_ids[0]}が現れた！"
        else:
            description = f"{count}体の{group.monster_ids[0]}たちが現れた！"
        
        # エンカウンタータイプによる修飾
        type_descriptions = {
            EncounterType.AMBUSH: "突然、",
            EncounterType.TREASURE_GUARDIAN: "宝箱を守る",
            EncounterType.BOSS: "巨大な",
            EncounterType.TRAP_MONSTER: "罠から飛び出した"
        }
        
        if encounter.encounter_type in type_descriptions:
            prefix = type_descriptions[encounter.encounter_type]
            description = f"{prefix}{description}"
        
        # ランクによる修飾
        if group.rank == MonsterRank.ELITE:
            description += " (エリート)"
        elif group.rank == MonsterRank.BOSS:
            description += " (ボス)"
        
        return description
    
    def resolve_encounter_attempt(self, action: str, encounter: EncounterEvent) -> Tuple[EncounterResult, str]:
        """エンカウンター解決試行"""
        if not self.current_party:
            return EncounterResult.COMBAT_START, "パーティが設定されていません"
        
        if action == "fight":
            return EncounterResult.COMBAT_START, "戦闘を開始します！"
        
        elif action == "flee":
            if not encounter.can_flee:
                return EncounterResult.COMBAT_START, "逃げることができません！戦闘開始！"
            
            # 逃走判定
            success_chance = self._calculate_flee_chance(encounter)
            if random.random() < success_chance:
                self.encounter_statistics['fled_encounters'] += 1
                return EncounterResult.FLED, "うまく逃げることができました"
            else:
                return EncounterResult.COMBAT_START, "逃走に失敗しました！戦闘開始！"
        
        elif action == "negotiate":
            if not encounter.can_negotiate:
                return EncounterResult.COMBAT_START, "交渉はできません！戦闘開始！"
            
            # 交渉判定
            success_chance = self._calculate_negotiation_chance(encounter)
            if random.random() < success_chance:
                return EncounterResult.NEGOTIATED, "交渉が成功しました"
            else:
                return EncounterResult.COMBAT_START, "交渉に失敗しました！戦闘開始！"
        
        else:
            return EncounterResult.COMBAT_START, "無効な行動です。戦闘開始！"
    
    def _calculate_flee_chance(self, encounter: EncounterEvent) -> float:
        """逃走成功率計算"""
        if not self.current_party:
            return 0.3
        
        # パーティの平均敏捷性
        living_chars = self.current_party.get_living_characters()
        if not living_chars:
            return 0.1
        
        avg_agility = sum(char.base_stats.agility for char in living_chars) / len(living_chars)
        
        # 基本成功率
        base_chance = BASE_FLEE_CHANCE
        
        # 敏捷性による修正
        agility_bonus = (avg_agility - BASE_AGILITY) * AGILITY_BONUS_RATE
        
        # エンカウンタータイプによる修正
        type_penalties = {
            EncounterType.AMBUSH: -0.3,
            EncounterType.BOSS: -0.5,
            EncounterType.TRAP_MONSTER: -0.2
        }
        
        type_penalty = type_penalties.get(encounter.encounter_type, 0)
        
        # モンスターランクによる修正
        rank_penalties = {
            MonsterRank.WEAK: 0.1,
            MonsterRank.NORMAL: 0,
            MonsterRank.STRONG: -0.1,
            MonsterRank.ELITE: -0.2,
            MonsterRank.BOSS: -0.4
        }
        
        rank_penalty = 0
        if encounter.monster_group:
            rank_penalty = rank_penalties.get(encounter.monster_group.rank, 0)
        
        final_chance = base_chance + agility_bonus + type_penalty + rank_penalty
        return max(MIN_FLEE_CHANCE, min(MAX_FLEE_CHANCE, final_chance))
    
    def _calculate_negotiation_chance(self, encounter: EncounterEvent) -> float:
        """交渉成功率計算"""
        if not self.current_party:
            return 0.1
        
        # パーティの最高カリスマ
        living_chars = self.current_party.get_living_characters()
        if not living_chars:
            return 0.05
        
        max_charisma = max(char.base_stats.intelligence for char in living_chars)  # 知力を交渉力として使用
        
        # 基本成功率
        base_chance = BASE_NEGOTIATION_CHANCE
        
        # 知力による修正
        charisma_bonus = (max_charisma - BASE_CHARISMA) * CHARISMA_BONUS_RATE
        
        # エンカウンタータイプによる修正
        if encounter.encounter_type == EncounterType.TREASURE_GUARDIAN:
            base_chance += TREASURE_GUARDIAN_NEGOTIATION_BONUS
        
        final_chance = base_chance + charisma_bonus
        return max(MIN_NEGOTIATION_CHANCE, min(MAX_NEGOTIATION_CHANCE, final_chance))
    
    def get_encounter_statistics(self) -> Dict[str, Any]:
        """エンカウンター統計取得"""
        return {
            **self.encounter_statistics,
            'flee_rate': (self.encounter_statistics['fled_encounters'] / 
                         max(1, self.encounter_statistics['total_encounters'])),
            'combat_victory_rate': (self.encounter_statistics['combat_victories'] / 
                                   max(1, self.encounter_statistics['total_encounters']))
        }
    
    def cleanup(self):
        """リソースのクリーンアップ"""
        try:
            # パーティ参照をクリア
            self.current_party = None
            
            # ダンジョン参照をクリア
            self.current_dungeon = None
            
            # アクティブエンカウンターをクリア
            self.active_encounters.clear()
            
            # テーブルをクリア
            self.encounter_tables.clear()
            
            # 統計をリセット
            self.encounter_statistics = {
                'total_encounters': 0,
                'combat_victories': 0,
                'fled_encounters': 0,
                'avoided_encounters': 0
            }
            
            logger.info("EncounterManager リソースをクリーンアップしました")
        except Exception as e:
            logger.error(f"EncounterManager クリーンアップ中にエラー: {e}")


# グローバルインスタンス
encounter_manager = EncounterManager()