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
            
        except Exception as e:
            logger.error(f"モンスターデータの読み込みに失敗: {e}")
            self.monster_templates = {}
    
    
    def create_monster(self, monster_id: str, level_modifier: int = 0) -> Optional[Monster]:
        """モンスター作成"""
        if monster_id not in self.monster_templates:
            logger.error(f"未知のモンスターID: {monster_id}")
            return None
        
        template = self.monster_templates[monster_id]
        
        # 多言語対応の名前と説明を取得
        current_language = getattr(config_manager, 'current_language', 'ja')
        
        # 名前取得
        if 'names' in template:
            names = template['names']
            if current_language in names:
                name = names[current_language]
            elif 'ja' in names:
                name = names['ja']
            else:
                name = list(names.values())[0]
        else:
            name = template.get('name', monster_id)
        
        # 説明取得
        if 'descriptions' in template:
            descriptions = template['descriptions']
            if current_language in descriptions:
                description = descriptions[current_language]
            elif 'ja' in descriptions:
                description = descriptions['ja']
            else:
                description = list(descriptions.values())[0]
        else:
            description = template.get('description', '')
        
        # 統計値作成（新しいYAML形式に対応）
        stats_data = {
            'level': template.get('level', 1),
            'hit_points': template.get('hp', 10),
            'armor_class': 10 + template.get('defense', 0),  # 防御力をACに変換
            'attack_bonus': template.get('attack', 0),
            'damage_dice': "1d6",  # デフォルト
            'strength': template.get('attack', 10),  # 攻撃力を筋力として使用
            'agility': template.get('agility', 10),
            'intelligence': template.get('intelligence', 10),
            'faith': template.get('faith', 10),
            'luck': template.get('luck', 10)
        }
        
        if level_modifier != 0:
            # レベル修正を適用
            stats_data['level'] += level_modifier
            stats_data['hit_points'] += level_modifier * 4
            stats_data['attack_bonus'] += level_modifier // 2
        
        stats = MonsterStats.from_dict(stats_data)
        
        # モンスター作成
        monster = Monster(
            monster_id=monster_id,
            name=name,
            description=description,
            monster_type=MonsterType.HUMANOID,  # デフォルト（必要に応じて拡張）
            size=MonsterSize.MEDIUM,  # デフォルト
            stats=stats,
            loot_table=self._convert_drops_to_loot_table(template.get('drops', [])),
            experience_value=template.get('exp_reward', 0)
        )
        
        # 耐性設定（新しい形式に対応）
        resistances = template.get('resistances', {})
        for attr_name, resistance_value in resistances.items():
            try:
                # 属性名をDungeonAttributeに変換
                if attr_name == 'physical':
                    attr = DungeonAttribute.PHYSICAL
                elif attr_name == 'fire':
                    attr = DungeonAttribute.FIRE
                elif attr_name == 'ice':
                    attr = DungeonAttribute.ICE
                elif attr_name == 'lightning':
                    attr = DungeonAttribute.LIGHTNING
                elif attr_name == 'dark':
                    attr = DungeonAttribute.DARK
                elif attr_name == 'light':
                    attr = DungeonAttribute.LIGHT
                else:
                    continue
                
                # 耐性値を判定
                if resistance_value >= 50:
                    res = MonsterResistance.RESISTANT
                elif resistance_value <= -30:
                    res = MonsterResistance.VULNERABLE
                else:
                    res = MonsterResistance.NORMAL
                
                monster.resistances[attr] = res
            except Exception as e:
                logger.warning(f"耐性設定エラー: {attr_name}={resistance_value}, {e}")
        
        # 特殊能力設定
        for ability_data in template.get('special_abilities', []):
            try:
                ability = MonsterAbility(
                    ability_id=ability_data.get('name', '').lower().replace(' ', '_'),
                    name=ability_data.get('name', ''),
                    description=ability_data.get('description', ''),
                    ability_type='active',
                    cooldown=0,
                    usage_count=-1,
                    target_type='enemy'
                )
                monster.abilities.append(ability)
            except Exception as e:
                logger.warning(f"特殊能力設定エラー: {ability_data}, {e}")
        
        logger.debug(f"モンスター作成: {monster.name} (Lv.{monster.stats.level})")
        return monster
    
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