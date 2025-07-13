"""モンスターシステム"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from enum import Enum
import random

from src.character.stats import BaseStats
from src.dungeon.dungeon_generator import DungeonAttribute
from src.core.config_manager import config_manager
from src.utils.logger import logger

# モンスターシステム定数
DEFAULT_LEVEL = 1
DEFAULT_HIT_POINTS = 10
DEFAULT_ARMOR_CLASS = 10
DEFAULT_ATTACK_BONUS = 0
DEFAULT_DAMAGE_DICE = "1d6"
DEFAULT_STAT_VALUE = 10
DEFAULT_DROP_CHANCE = 0.1
DEFAULT_DROP_QUANTITY = 1
FALLBACK_LANGUAGE = 'ja'
MINIMUM_DAMAGE = 1
DEFAULT_AC_BASE = 10
LEVEL_HP_MODIFIER = 4
LEVEL_ATTACK_DIVISOR = 2
FIRST_ELEMENT_INDEX = 0
RESISTANT_THRESHOLD = 50
VULNERABLE_THRESHOLD = -30
SCALING_LEVEL_THRESHOLD = 2
SCALING_FACTOR_BASE = 0.1
SCALING_DIVISOR = 3
MINIMUM_SCALING_FACTOR = 0.5
UNLIMITED_USAGE = -1
COOLDOWN_EXPIRED = 0


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
        actual_damage = self._calculate_damage_with_resistance(damage, damage_type)
        self.current_hp = max(COOLDOWN_EXPIRED, self.current_hp - actual_damage)
        
        logger.debug(f"{self.name}が{actual_damage}ダメージを受けました（HP: {self.current_hp}/{self.max_hp}）")
        return actual_damage
    
    def _calculate_damage_with_resistance(self, damage: int, damage_type: DungeonAttribute) -> int:
        """耐性を考慮したダメージ計算"""
        resistance = self.resistances.get(damage_type, MonsterResistance.NORMAL)
        
        if resistance == MonsterResistance.IMMUNE:
            return COOLDOWN_EXPIRED
        elif resistance == MonsterResistance.RESISTANT:
            return damage // LEVEL_ATTACK_DIVISOR
        elif resistance == MonsterResistance.VULNERABLE:
            return int(damage * 1.5)
        else:
            return damage
    
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
        if self.ability_cooldowns.get(ability_id, COOLDOWN_EXPIRED) > COOLDOWN_EXPIRED:
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
        if ability.cooldown > COOLDOWN_EXPIRED:
            self.ability_cooldowns[ability_id] = ability.cooldown
        
        logger.debug(f"{self.name}が{ability.name}を使用しました")
        return True
    
    def update_cooldowns(self):
        """クールダウン更新"""
        for ability_id in list(self.ability_cooldowns.keys()):
            self.ability_cooldowns[ability_id] -= MINIMUM_DAMAGE
            if self.ability_cooldowns[ability_id] <= COOLDOWN_EXPIRED:
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
        return self._roll_damage_dice(self.stats.damage_dice)
    
    def _roll_damage_dice(self, dice_string: str) -> int:
        """ダイスロール計算"""
        dice_parts = dice_string.split('d')
        if len(dice_parts) == LEVEL_ATTACK_DIVISOR:
            num_dice = int(dice_parts[FIRST_ELEMENT_INDEX])
            die_size = int(dice_parts[FIRST_ELEMENT_INDEX + 1])
            return sum(random.randint(MINIMUM_DAMAGE, die_size) for _ in range(num_dice))
        else:
            return MINIMUM_DAMAGE
    
    def get_loot(self) -> List[Dict[str, Any]]:
        """ドロップアイテム取得"""
        dropped_items = []
        
        for loot_entry in self.loot_table:
            if self._should_drop_item(loot_entry):
                dropped_items.append(self._create_drop_item(loot_entry))
        
        return dropped_items
    
    def _should_drop_item(self, loot_entry: Dict[str, Any]) -> bool:
        """アイテムをドロップするかどうか判定"""
        drop_chance = loot_entry.get('chance', DEFAULT_DROP_CHANCE)
        return random.random() < drop_chance
    
    def _create_drop_item(self, loot_entry: Dict[str, Any]) -> Dict[str, Any]:
        """ドロップアイテムを作成"""
        return {
            'item_id': loot_entry['item_id'],
            'quantity': loot_entry.get('quantity', DEFAULT_DROP_QUANTITY),
            'identified': loot_entry.get('identified', False)
        }
    
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
        
        logger.debug("MonsterManager初期化完了")
    
    def _load_monster_data(self):
        """モンスターデータ読み込み"""
        try:
            # 設定ファイルからモンスターデータを読み込み
            monster_config = config_manager.load_config("monsters")
            self.monster_templates = monster_config.get("monsters", {})
            
            logger.info(f"モンスターテンプレート{len(self.monster_templates)}種類を読み込みました")
            
        except Exception as e:
            logger.error(f"モンスターデータの読み込みに失敗: {e}")
            self.monster_templates = {}
    
    
    def create_monster(self, monster_id: str, level_modifier: int = COOLDOWN_EXPIRED) -> Optional[Monster]:
        """モンスター作成"""
        if monster_id not in self.monster_templates:
            logger.error(f"未知のモンスターID: {monster_id}")
            return None
        
        template = self.monster_templates[monster_id]
        
        # 多言語対応の名前と説明を取得
        name = self._get_localized_name(template)
        description = self._get_localized_description(template)
        
        # 統計値作成
        stats = self._create_monster_stats(template, level_modifier)
        
        # モンスター作成
        monster = Monster(
            monster_id=monster_id,
            name=name,
            description=description,
            monster_type=MonsterType.HUMANOID,
            size=MonsterSize.MEDIUM,
            stats=stats,
            loot_table=self._convert_drops_to_loot_table(template.get('drops', [])),
            experience_value=template.get('exp_reward', COOLDOWN_EXPIRED)
        )
        
        # 耐性と特殊能力設定
        self._setup_monster_resistances(monster, template)
        self._setup_monster_abilities(monster, template)
        
        logger.debug(f"モンスター作成: {monster.name} (Lv.{monster.stats.level})")
        return monster
    
    def _get_localized_name(self, template: Dict[str, Any]) -> str:
        """ローカライズされた名前を取得"""
        current_language = getattr(config_manager, 'current_language', FALLBACK_LANGUAGE)
        
        if 'names' in template:
            names = template['names']
            if current_language in names:
                return names[current_language]
            elif FALLBACK_LANGUAGE in names:
                return names[FALLBACK_LANGUAGE]
            else:
                return list(names.values())[FIRST_ELEMENT_INDEX]
        else:
            return template.get('name', '')
    
    def _get_localized_description(self, template: Dict[str, Any]) -> str:
        """ローカライズされた説明を取得"""
        current_language = getattr(config_manager, 'current_language', FALLBACK_LANGUAGE)
        
        if 'descriptions' in template:
            descriptions = template['descriptions']
            if current_language in descriptions:
                return descriptions[current_language]
            elif FALLBACK_LANGUAGE in descriptions:
                return descriptions[FALLBACK_LANGUAGE]
            else:
                return list(descriptions.values())[FIRST_ELEMENT_INDEX]
        else:
            return template.get('description', '')
    
    def _create_monster_stats(self, template: Dict[str, Any], level_modifier: int) -> MonsterStats:
        """モンスター統計値を作成"""
        stats_data = {
            'level': template.get('level', DEFAULT_LEVEL),
            'hit_points': template.get('hp', DEFAULT_HIT_POINTS),
            'armor_class': DEFAULT_AC_BASE + template.get('defense', COOLDOWN_EXPIRED),
            'attack_bonus': template.get('attack', DEFAULT_ATTACK_BONUS),
            'damage_dice': DEFAULT_DAMAGE_DICE,
            'strength': template.get('attack', DEFAULT_STAT_VALUE),
            'agility': template.get('agility', DEFAULT_STAT_VALUE),
            'intelligence': template.get('intelligence', DEFAULT_STAT_VALUE),
            'faith': template.get('faith', DEFAULT_STAT_VALUE),
            'luck': template.get('luck', DEFAULT_STAT_VALUE)
        }
        
        if level_modifier != COOLDOWN_EXPIRED:
            self._apply_level_modifier(stats_data, level_modifier)
        
        return MonsterStats.from_dict(stats_data)
    
    def _apply_level_modifier(self, stats_data: Dict[str, Any], level_modifier: int):
        """レベル修正を適用"""
        stats_data['level'] += level_modifier
        stats_data['hit_points'] += level_modifier * LEVEL_HP_MODIFIER
        stats_data['attack_bonus'] += level_modifier // LEVEL_ATTACK_DIVISOR
    
    def _setup_monster_resistances(self, monster: Monster, template: Dict[str, Any]):
        """モンスターの耐性を設定"""
        resistances = template.get('resistances', {})
        for attr_name, resistance_value in resistances.items():
            try:
                attr = self._convert_attribute_name(attr_name)
                if attr:
                    res = self._determine_resistance_level(resistance_value)
                    monster.resistances[attr] = res
            except Exception as e:
                logger.warning(f"耐性設定エラー: {attr_name}={resistance_value}, {e}")
    
    def _convert_attribute_name(self, attr_name: str) -> Optional[DungeonAttribute]:
        """属性名をDungeonAttributeに変換"""
        attribute_map = {
            'physical': DungeonAttribute.PHYSICAL,
            'fire': DungeonAttribute.FIRE,
            'ice': DungeonAttribute.ICE,
            'lightning': DungeonAttribute.LIGHTNING,
            'dark': DungeonAttribute.DARK,
            'light': DungeonAttribute.LIGHT
        }
        return attribute_map.get(attr_name)
    
    def _determine_resistance_level(self, resistance_value: int) -> MonsterResistance:
        """耐性レベルを判定"""
        if resistance_value >= RESISTANT_THRESHOLD:
            return MonsterResistance.RESISTANT
        elif resistance_value <= VULNERABLE_THRESHOLD:
            return MonsterResistance.VULNERABLE
        else:
            return MonsterResistance.NORMAL
    
    def _setup_monster_abilities(self, monster: Monster, template: Dict[str, Any]):
        """モンスターの特殊能力を設定"""
        for ability_data in template.get('special_abilities', []):
            try:
                ability = MonsterAbility(
                    ability_id=ability_data.get('name', '').lower().replace(' ', '_'),
                    name=ability_data.get('name', ''),
                    description=ability_data.get('description', ''),
                    ability_type='active',
                    cooldown=COOLDOWN_EXPIRED,
                    usage_count=UNLIMITED_USAGE,
                    target_type='enemy'
                )
                monster.abilities.append(ability)
            except Exception as e:
                logger.warning(f"特殊能力設定エラー: {ability_data}, {e}")
    
    def _convert_drops_to_loot_table(self, drops: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """ドロップ情報をルートテーブルに変換"""
        loot_table = []
        for drop in drops:
            loot_table.append({
                'item_id': drop.get('item_id', ''),
                'quantity': drop.get('quantity', 1),
                'chance': drop.get('probability', 0.1),
                'identified': True
            })
        return loot_table
    
    def get_monster_template(self, monster_id: str) -> Optional[Dict[str, Any]]:
        """モンスターテンプレート取得"""
        return self.monster_templates.get(monster_id)
    
    def is_boss_monster(self, monster_id: str) -> bool:
        """ボスモンスターかどうか判定"""
        template = self.get_monster_template(monster_id)
        if template:
            return template.get('is_boss', False)
        return False
    
    def get_boss_monsters(self) -> List[str]:
        """ボスモンスター一覧を取得"""
        return [monster_id for monster_id, template in self.monster_templates.items() 
                if template.get('is_boss', False)]
    
    def get_regular_monsters(self) -> List[str]:
        """通常モンスター一覧を取得"""
        return [monster_id for monster_id, template in self.monster_templates.items() 
                if not template.get('is_boss', False)]
    
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
    
    def scale_monster_for_party(self, monster: Monster, party_level: int, _party_size: int) -> Monster:
        """パーティに応じたモンスタースケーリング"""
        level_diff = party_level - monster.stats.level
        
        if level_diff > SCALING_LEVEL_THRESHOLD:
            self._scale_monster_up(monster, level_diff)
        elif level_diff < -SCALING_LEVEL_THRESHOLD:
            self._scale_monster_down(monster, level_diff)
        
        return monster
    
    def _scale_monster_up(self, monster: Monster, level_diff: int):
        """モンスターを強化"""
        scaling_factor = MINIMUM_DAMAGE + (level_diff - SCALING_LEVEL_THRESHOLD) * SCALING_FACTOR_BASE
        monster.stats.hit_points = int(monster.stats.hit_points * scaling_factor)
        monster.stats.attack_bonus += level_diff // SCALING_DIVISOR
        monster.current_hp = monster.stats.hit_points
    
    def _scale_monster_down(self, monster: Monster, level_diff: int):
        """モンスターを弱体化"""
        scaling_factor = MINIMUM_DAMAGE - (abs(level_diff) - SCALING_LEVEL_THRESHOLD) * SCALING_FACTOR_BASE
        scaling_factor = max(MINIMUM_SCALING_FACTOR, scaling_factor)
        monster.stats.hit_points = int(monster.stats.hit_points * scaling_factor)
        monster.stats.attack_bonus = max(COOLDOWN_EXPIRED, monster.stats.attack_bonus - abs(level_diff) // SCALING_DIVISOR)
        monster.current_hp = monster.stats.hit_points


# グローバルインスタンス
monster_manager = MonsterManager()