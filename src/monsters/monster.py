"""モンスターシステム"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from enum import Enum
import random

from src.character.stats import BaseStats
from src.dungeon.dungeon_generator import DungeonAttribute
from src.core.config_manager import config_manager
from src.utils.logger import logger


class MonsterType(Enum):
    """モンスタータイプ"""
    BEAST = "beast"         # 野獣
    UNDEAD = "undead"       # アンデッド
    DEMON = "demon"         # 悪魔
    DRAGON = "dragon"       # ドラゴン
    HUMANOID = "humanoid"   # 人型
    CONSTRUCT = "construct" # 構造体
    ELEMENTAL = "elemental" # 精霊
    ABERRATION = "aberration" # 異形


class MonsterSize(Enum):
    """モンスターサイズ"""
    TINY = "tiny"           # 極小
    SMALL = "small"         # 小型
    MEDIUM = "medium"       # 中型
    LARGE = "large"         # 大型
    HUGE = "huge"           # 超大型
    GARGANTUAN = "gargantuan" # 巨大


class MonsterResistance(Enum):
    """モンスター耐性"""
    IMMUNE = "immune"           # 完全耐性
    RESISTANT = "resistant"     # 耐性
    VULNERABLE = "vulnerable"   # 弱点
    NORMAL = "normal"           # 通常


@dataclass
class MonsterStats:
    """モンスター統計値"""
    level: int = 1
    hit_points: int = 10
    armor_class: int = 10
    attack_bonus: int = 0
    damage_dice: str = "1d6"
    
    # 基本能力値
    strength: int = 10
    agility: int = 10
    intelligence: int = 10
    faith: int = 10
    luck: int = 10
    
    def to_base_stats(self) -> BaseStats:
        """BaseStatsに変換"""
        return BaseStats(
            strength=self.strength,
            agility=self.agility,
            intelligence=self.intelligence,
            faith=self.faith,
            luck=self.luck
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """辞書形式に変換"""
        return {
            'level': self.level,
            'hit_points': self.hit_points,
            'armor_class': self.armor_class,
            'attack_bonus': self.attack_bonus,
            'damage_dice': self.damage_dice,
            'strength': self.strength,
            'agility': self.agility,
            'intelligence': self.intelligence,
            'faith': self.faith,
            'luck': self.luck
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MonsterStats':
        """辞書から復元"""
        return cls(
            level=data.get('level', 1),
            hit_points=data.get('hit_points', 10),
            armor_class=data.get('armor_class', 10),
            attack_bonus=data.get('attack_bonus', 0),
            damage_dice=data.get('damage_dice', '1d6'),
            strength=data.get('strength', 10),
            agility=data.get('agility', 10),
            intelligence=data.get('intelligence', 10),
            faith=data.get('faith', 10),
            luck=data.get('luck', 10)
        )


@dataclass
class MonsterAbility:
    """モンスター特殊能力"""
    ability_id: str
    name: str
    description: str
    ability_type: str = "active"  # active, passive, reaction
    cooldown: int = 0
    usage_count: int = -1  # -1は無制限
    target_type: str = "enemy"  # enemy, self, ally, area
    
    def to_dict(self) -> Dict[str, Any]:
        """辞書形式に変換"""
        return {
            'ability_id': self.ability_id,
            'name': self.name,
            'description': self.description,
            'ability_type': self.ability_type,
            'cooldown': self.cooldown,
            'usage_count': self.usage_count,
            'target_type': self.target_type
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MonsterAbility':
        """辞書から復元"""
        return cls(
            ability_id=data['ability_id'],
            name=data['name'],
            description=data['description'],
            ability_type=data.get('ability_type', 'active'),
            cooldown=data.get('cooldown', 0),
            usage_count=data.get('usage_count', -1),
            target_type=data.get('target_type', 'enemy')
        )


@dataclass
class Monster:
    """モンスタークラス"""
    monster_id: str
    name: str
    description: str
    monster_type: MonsterType
    size: MonsterSize
    stats: MonsterStats
    
    # 属性耐性
    resistances: Dict[DungeonAttribute, MonsterResistance] = field(default_factory=dict)
    
    # 特殊能力
    abilities: List[MonsterAbility] = field(default_factory=list)
    
    # 戦闘データ
    current_hp: Optional[int] = None
    status_effects: List[str] = field(default_factory=list)
    ability_cooldowns: Dict[str, int] = field(default_factory=dict)
    
    # ドロップアイテム
    loot_table: List[Dict[str, Any]] = field(default_factory=list)
    experience_value: int = 0
    
    def __post_init__(self):
        """初期化後処理"""
        if self.current_hp is None:
            self.current_hp = self.stats.hit_points
    
    @property
    def is_alive(self) -> bool:
        """生存状態"""
        return self.current_hp > 0
    
    @property
    def max_hp(self) -> int:
        """最大HP"""
        return self.stats.hit_points
    
    def take_damage(self, damage: int, damage_type: DungeonAttribute = DungeonAttribute.PHYSICAL) -> int:
        """ダメージを受ける"""
        # 耐性による軽減
        resistance = self.resistances.get(damage_type, MonsterResistance.NORMAL)
        
        if resistance == MonsterResistance.IMMUNE:
            actual_damage = 0
        elif resistance == MonsterResistance.RESISTANT:
            actual_damage = damage // 2
        elif resistance == MonsterResistance.VULNERABLE:
            actual_damage = int(damage * 1.5)
        else:
            actual_damage = damage
        
        self.current_hp = max(0, self.current_hp - actual_damage)
        
        logger.debug(f"{self.name}が{actual_damage}ダメージを受けました（HP: {self.current_hp}/{self.max_hp}）")
        return actual_damage
    
    def heal(self, amount: int) -> int:
        """回復"""
        old_hp = self.current_hp
        self.current_hp = min(self.max_hp, self.current_hp + amount)
        actual_heal = self.current_hp - old_hp
        
        logger.debug(f"{self.name}が{actual_heal}回復しました（HP: {self.current_hp}/{self.max_hp}）")
        return actual_heal
    
    def has_ability(self, ability_id: str) -> bool:
        """特殊能力の保有確認"""
        return any(ability.ability_id == ability_id for ability in self.abilities)
    
    def get_ability(self, ability_id: str) -> Optional[MonsterAbility]:
        """特殊能力を取得"""
        for ability in self.abilities:
            if ability.ability_id == ability_id:
                return ability
        return None
    
    def can_use_ability(self, ability_id: str) -> bool:
        """特殊能力使用可能かチェック"""
        ability = self.get_ability(ability_id)
        if not ability:
            return False
        
        # クールダウンチェック
        if self.ability_cooldowns.get(ability_id, 0) > 0:
            return False
        
        return True
    
    def use_ability(self, ability_id: str) -> bool:
        """特殊能力使用"""
        if not self.can_use_ability(ability_id):
            return False
        
        ability = self.get_ability(ability_id)
        if not ability:
            return False
        
        # クールダウン設定
        if ability.cooldown > 0:
            self.ability_cooldowns[ability_id] = ability.cooldown
        
        logger.debug(f"{self.name}が{ability.name}を使用しました")
        return True
    
    def update_cooldowns(self):
        """クールダウン更新"""
        for ability_id in list(self.ability_cooldowns.keys()):
            self.ability_cooldowns[ability_id] -= 1
            if self.ability_cooldowns[ability_id] <= 0:
                del self.ability_cooldowns[ability_id]
    
    def add_status_effect(self, effect: str):
        """状態効果追加"""
        if effect not in self.status_effects:
            self.status_effects.append(effect)
            logger.debug(f"{self.name}に{effect}が付与されました")
    
    def remove_status_effect(self, effect: str):
        """状態効果除去"""
        if effect in self.status_effects:
            self.status_effects.remove(effect)
            logger.debug(f"{self.name}の{effect}が除去されました")
    
    def has_status_effect(self, effect: str) -> bool:
        """状態効果保有確認"""
        return effect in self.status_effects
    
    def get_attack_damage(self) -> int:
        """攻撃ダメージ計算"""
        # 基本的なダイスロール実装
        dice_parts = self.stats.damage_dice.split('d')
        if len(dice_parts) == 2:
            num_dice = int(dice_parts[0])
            die_size = int(dice_parts[1])
            damage = sum(random.randint(1, die_size) for _ in range(num_dice))
        else:
            damage = 1  # デフォルト
        
        return damage
    
    def get_loot(self) -> List[Dict[str, Any]]:
        """ドロップアイテム取得"""
        dropped_items = []
        
        for loot_entry in self.loot_table:
            drop_chance = loot_entry.get('chance', 0.1)
            if random.random() < drop_chance:
                dropped_items.append({
                    'item_id': loot_entry['item_id'],
                    'quantity': loot_entry.get('quantity', 1),
                    'identified': loot_entry.get('identified', False)
                })
        
        return dropped_items
    
    def to_dict(self) -> Dict[str, Any]:
        """辞書形式に変換"""
        return {
            'monster_id': self.monster_id,
            'name': self.name,
            'description': self.description,
            'monster_type': self.monster_type.value,
            'size': self.size.value,
            'stats': self.stats.to_dict(),
            'resistances': {attr.value: res.value for attr, res in self.resistances.items()},
            'abilities': [ability.to_dict() for ability in self.abilities],
            'current_hp': self.current_hp,
            'status_effects': self.status_effects,
            'ability_cooldowns': self.ability_cooldowns,
            'loot_table': self.loot_table,
            'experience_value': self.experience_value
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Monster':
        """辞書から復元"""
        monster = cls(
            monster_id=data['monster_id'],
            name=data['name'],
            description=data['description'],
            monster_type=MonsterType(data['monster_type']),
            size=MonsterSize(data['size']),
            stats=MonsterStats.from_dict(data['stats']),
            current_hp=data.get('current_hp'),
            status_effects=data.get('status_effects', []),
            ability_cooldowns=data.get('ability_cooldowns', {}),
            loot_table=data.get('loot_table', []),
            experience_value=data.get('experience_value', 0)
        )
        
        # 耐性復元
        for attr_str, res_str in data.get('resistances', {}).items():
            attr = DungeonAttribute(attr_str)
            res = MonsterResistance(res_str)
            monster.resistances[attr] = res
        
        # 特殊能力復元
        for ability_data in data.get('abilities', []):
            ability = MonsterAbility.from_dict(ability_data)
            monster.abilities.append(ability)
        
        return monster


class MonsterManager:
    """モンスター管理システム"""
    
    def __init__(self):
        self.monsters: Dict[str, Monster] = {}
        self.monster_templates: Dict[str, Dict[str, Any]] = {}
        self._load_monster_data()
        
        logger.info("MonsterManager初期化完了")
    
    def _load_monster_data(self):
        """モンスターデータ読み込み"""
        try:
            # 設定ファイルからモンスターデータを読み込み
            monster_config = config_manager.load_config("monsters")
            self.monster_templates = monster_config.get("monsters", {})
            
            logger.info(f"モンスターテンプレート{len(self.monster_templates)}種類を読み込みました")
            
            # モンスターテンプレートが空の場合はデフォルトを作成
            if not self.monster_templates:
                self._create_default_monsters()
            
        except Exception as e:
            logger.warning(f"モンスターデータの読み込みに失敗: {e}")
            # デフォルトモンスターを設定
            self._create_default_monsters()
    
    def _create_default_monsters(self):
        """デフォルトモンスター作成"""
        self.monster_templates = {
            "goblin": {
                "name": "ゴブリン",
                "description": "小さな緑色の人型モンスター",
                "monster_type": "humanoid",
                "size": "small",
                "stats": {
                    "level": 1,
                    "hit_points": 8,
                    "armor_class": 12,
                    "attack_bonus": 2,
                    "damage_dice": "1d6",
                    "strength": 8,
                    "agility": 14,
                    "intelligence": 10,
                    "faith": 8,
                    "luck": 10
                },
                "resistances": {},
                "abilities": [],
                "loot_table": [
                    {"item_id": "copper_coin", "quantity": 5, "chance": 0.8},
                    {"item_id": "dagger", "quantity": 1, "chance": 0.1}
                ],
                "experience_value": 25
            },
            "orc": {
                "name": "オーク",
                "description": "大柄で凶暴な戦士",
                "monster_type": "humanoid",
                "size": "medium",
                "stats": {
                    "level": 3,
                    "hit_points": 24,
                    "armor_class": 14,
                    "attack_bonus": 4,
                    "damage_dice": "1d8+2",
                    "strength": 16,
                    "agility": 10,
                    "intelligence": 8,
                    "faith": 8,
                    "luck": 8
                },
                "resistances": {},
                "abilities": [
                    {
                        "ability_id": "rage",
                        "name": "激怒",
                        "description": "攻撃力が上昇する",
                        "ability_type": "active",
                        "cooldown": 3
                    }
                ],
                "loot_table": [
                    {"item_id": "silver_coin", "quantity": 10, "chance": 0.7},
                    {"item_id": "battle_axe", "quantity": 1, "chance": 0.15}
                ],
                "experience_value": 75
            },
            "skeleton": {
                "name": "スケルトン",
                "description": "動く骸骨の戦士",
                "monster_type": "undead",
                "size": "medium",
                "stats": {
                    "level": 2,
                    "hit_points": 16,
                    "armor_class": 13,
                    "attack_bonus": 3,
                    "damage_dice": "1d6+1",
                    "strength": 12,
                    "agility": 12,
                    "intelligence": 6,
                    "faith": 6,
                    "luck": 8
                },
                "resistances": {
                    "physical": "resistant"
                },
                "abilities": [],
                "loot_table": [
                    {"item_id": "bone", "quantity": 1, "chance": 0.5},
                    {"item_id": "rusty_sword", "quantity": 1, "chance": 0.2}
                ],
                "experience_value": 50
            }
        }
        
        logger.info("デフォルトモンスターテンプレートを作成しました")
    
    def create_monster(self, monster_id: str, level_modifier: int = 0) -> Optional[Monster]:
        """モンスター作成"""
        if monster_id not in self.monster_templates:
            logger.error(f"未知のモンスターID: {monster_id}")
            return None
        
        template = self.monster_templates[monster_id]
        
        # 統計値作成
        stats_data = template['stats'].copy()
        if level_modifier != 0:
            # レベル修正を適用
            stats_data['level'] += level_modifier
            stats_data['hit_points'] += level_modifier * 4
            stats_data['attack_bonus'] += level_modifier // 2
        
        stats = MonsterStats.from_dict(stats_data)
        
        # モンスター作成
        monster = Monster(
            monster_id=monster_id,
            name=template['name'],
            description=template['description'],
            monster_type=MonsterType(template['monster_type']),
            size=MonsterSize(template['size']),
            stats=stats,
            loot_table=template.get('loot_table', []),
            experience_value=template.get('experience_value', 0)
        )
        
        # 耐性設定
        for attr_str, res_str in template.get('resistances', {}).items():
            attr = DungeonAttribute(attr_str)
            res = MonsterResistance(res_str)
            monster.resistances[attr] = res
        
        # 特殊能力設定
        for ability_data in template.get('abilities', []):
            ability = MonsterAbility.from_dict(ability_data)
            monster.abilities.append(ability)
        
        logger.debug(f"モンスター作成: {monster.name} (Lv.{monster.stats.level})")
        return monster
    
    def get_monster_template(self, monster_id: str) -> Optional[Dict[str, Any]]:
        """モンスターテンプレート取得"""
        return self.monster_templates.get(monster_id)
    
    def get_available_monsters(self) -> List[str]:
        """利用可能モンスターID一覧"""
        return list(self.monster_templates.keys())
    
    def create_monster_group(self, monster_ids: List[str], level_modifier: int = 0) -> List[Monster]:
        """モンスターグループ作成"""
        monsters = []
        
        for monster_id in monster_ids:
            monster = self.create_monster(monster_id, level_modifier)
            if monster:
                monsters.append(monster)
        
        logger.debug(f"モンスターグループ作成: {len(monsters)}体")
        return monsters
    
    def scale_monster_for_party(self, monster: Monster, party_level: int, party_size: int) -> Monster:
        """パーティに応じたモンスタースケーリング"""
        # パーティレベルと現在のモンスターレベルの差を計算
        level_diff = party_level - monster.stats.level
        
        if level_diff > 2:
            # パーティが強すぎる場合はモンスターを強化
            scaling_factor = 1 + (level_diff - 2) * 0.1
            monster.stats.hit_points = int(monster.stats.hit_points * scaling_factor)
            monster.stats.attack_bonus += level_diff // 3
            monster.current_hp = monster.stats.hit_points
            
        elif level_diff < -2:
            # パーティが弱すぎる場合はモンスターを弱体化
            scaling_factor = 1 - (abs(level_diff) - 2) * 0.1
            scaling_factor = max(0.5, scaling_factor)  # 最低50%まで
            monster.stats.hit_points = int(monster.stats.hit_points * scaling_factor)
            monster.stats.attack_bonus = max(0, monster.stats.attack_bonus - abs(level_diff) // 3)
            monster.current_hp = monster.stats.hit_points
        
        return monster


# グローバルインスタンス
monster_manager = MonsterManager()