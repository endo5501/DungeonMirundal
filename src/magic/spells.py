"""魔法・祈祷システム"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Tuple
from enum import Enum
import uuid

from src.core.config_manager import config_manager
from src.utils.logger import logger

# 魔法システム定数
DEFAULT_SPELL_LEVEL = 1
DEFAULT_COST = 100
DEFAULT_BASE_VALUE = 0
DEFAULT_DURATION = 0
DEFAULT_MAX_USES = 1
SCALING_MULTIPLIER = 2
SCALING_DIVISOR = 3
ZERO_USES = 0
MINIMUM_MP_COST = 1


class SpellSchool(Enum):
    """魔法学派"""
    MAGE = "mage"       # 攻撃魔法
    PRIEST = "priest"   # 神聖魔法
    BOTH = "both"       # 汎用魔法


class SpellType(Enum):
    """魔法タイプ"""
    OFFENSIVE = "offensive"     # 攻撃
    HEALING = "healing"         # 回復
    BUFF = "buff"              # 強化
    DEBUFF = "debuff"          # 弱体化
    UTILITY = "utility"        # 汎用
    REVIVAL = "revival"        # 蘇生
    ULTIMATE = "ultimate"      # 究極


class SpellTarget(Enum):
    """魔法対象"""
    SELF = "self"                   # 自分
    SINGLE_ALLY = "single_ally"     # 味方1体
    SINGLE_ENEMY = "single_enemy"   # 敵1体
    GROUP_ALLY = "group_ally"       # 味方グループ
    GROUP_ENEMY = "group_enemy"     # 敵グループ
    ALL_ALLIES = "all_allies"       # 全味方
    ALL_ENEMIES = "all_enemies"     # 全敵
    SINGLE_TARGET = "single_target" # 任意1体
    PARTY = "party"                 # パーティ
    AREA = "area"                   # エリア
    BATTLEFIELD = "battlefield"     # 戦場全体


@dataclass
class SpellEffect:
    """魔法効果"""
    effect_type: str                           # 効果タイプ
    base_value: int = 0                       # 基本値
    scaling_stat: Optional[str] = None        # スケーリング能力値
    element: Optional[str] = None             # 属性
    duration: int = 0                         # 持続時間（ターン）
    stat_boosts: Dict[str, int] = field(default_factory=dict)  # 能力値補正
    status_effects: List[str] = field(default_factory=list)    # 状態異常
    special_properties: Dict[str, Any] = field(default_factory=dict)  # 特殊効果


class Spell:
    """魔法クラス"""
    
    def __init__(self, spell_id: str, spell_data: Dict[str, Any]):
        self.spell_id = spell_id
        self.spell_data = spell_data.copy()
        
        # 基本プロパティ
        self.name_key = spell_data.get('name_key', f'spell.{spell_id}')
        self.description_key = spell_data.get('description_key', f'spell.{spell_id}_desc')
        self.level = spell_data.get('level', DEFAULT_SPELL_LEVEL)
        self.school = SpellSchool(spell_data.get('school', 'both'))
        self.spell_type = SpellType(spell_data.get('type', 'utility'))
        self.target = SpellTarget(spell_data.get('target', 'self'))
        self.cost = spell_data.get('cost', DEFAULT_COST)
        self.mp_cost = spell_data.get('mp_cost', max(MINIMUM_MP_COST, self.level))
        
        # 効果
        self.effect = self._parse_effect(spell_data)
        
    
    def _parse_effect(self, data: Dict[str, Any]) -> SpellEffect:
        """効果データを解析"""
        effect_type = data.get('effect_type', 'none')
        base_value, scaling_stat = self._parse_spell_values(data)
        
        return SpellEffect(
            effect_type=effect_type,
            base_value=base_value,
            scaling_stat=scaling_stat,
            element=data.get('element'),
            duration=data.get('duration', DEFAULT_DURATION),
            stat_boosts=data.get('stat_boosts', {}),
            status_effects=data.get('status_effects', []),
            special_properties=data.get('special_properties', {})
        )
    
    def _parse_spell_values(self, data: Dict[str, Any]) -> Tuple[int, Optional[str]]:
        """魔法の基本値とスケーリング能力値を解析"""
        # ダメージ系
        if 'base_damage' in data:
            return data['base_damage'], data.get('damage_scaling', 'intelligence')
        # 回復系
        elif 'base_heal' in data:
            return data['base_heal'], data.get('heal_scaling', 'faith')
        # その他
        else:
            return data.get('base_value', DEFAULT_BASE_VALUE), data.get('scaling_stat')
    
    @property
    def name(self) -> str:
        """魔法名を取得"""
        return config_manager.get_text(self.name_key)
    
    def get_name(self) -> str:
        """魔法名を取得"""
        return self.name
    
    def get_description(self) -> str:
        """魔法説明を取得"""
        return config_manager.get_text(self.description_key)
    
    def can_use_by_class(self, character_class: str) -> bool:
        """指定されたクラスが使用可能かチェック"""
        spell_config = config_manager.load_config("spells")
        class_access = spell_config.get("class_spell_access", {})
        
        class_info = class_access.get(character_class, {})
        
        # 学派チェック
        if not self._check_school_access(class_info):
            return False
        
        # タイプチェック
        if not self._check_type_access(class_info):
            return False
        
        return True
    
    def _check_school_access(self, class_info: Dict[str, Any]) -> bool:
        """学派アクセス権限をチェック"""
        allowed_schools = class_info.get("allowed_schools", [])
        return self.school.value in allowed_schools
    
    def _check_type_access(self, class_info: Dict[str, Any]) -> bool:
        """タイプアクセス権限をチェック"""
        allowed_types = class_info.get("allowed_types", [])
        return self.spell_type.value in allowed_types
    
    def calculate_effect_value(self, caster_stats: Dict[str, int]) -> int:
        """効果値を計算"""
        base_value = self.effect.base_value
        
        if self.effect.scaling_stat and self.effect.scaling_stat in caster_stats:
            scaling_value = caster_stats[self.effect.scaling_stat]
            # レベルと能力値による補正
            modifier = (self.level * SCALING_MULTIPLIER) + (scaling_value // SCALING_DIVISOR)
            return base_value + modifier
        
        return base_value
    
    def get_spell_info(self) -> Dict[str, Any]:
        """魔法情報を取得"""
        return {
            'id': self.spell_id,
            'name': self.get_name(),
            'description': self.get_description(),
            'level': self.level,
            'school': self.school.value,
            'type': self.spell_type.value,
            'target': self.target.value,
            'cost': self.cost,
            'effect_type': self.effect.effect_type,
            'base_value': self.effect.base_value,
            'scaling_stat': self.effect.scaling_stat,
            'element': self.effect.element,
            'duration': self.effect.duration
        }


@dataclass
class SpellSlot:
    """魔法スロット"""
    slot_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    level: int = 1                              # スロットレベル
    spell_id: Optional[str] = None              # 装備中の魔法ID
    max_uses: int = 1                          # 最大使用回数
    current_uses: int = 1                      # 現在の使用回数
    
    def is_empty(self) -> bool:
        """スロットが空かどうか"""
        return self.spell_id is None
    
    def can_use(self) -> bool:
        """使用可能かどうか"""
        return not self.is_empty() and self.current_uses > 0
    
    def equip_spell(self, spell_id: str) -> bool:
        """魔法を装備"""
        self.spell_id = spell_id
        self.current_uses = self.max_uses
        return True
    
    def unequip_spell(self) -> Optional[str]:
        """魔法の装備を解除"""
        spell_id = self.spell_id
        self.spell_id = None
        self.current_uses = 0
        return spell_id
    
    def use_spell(self) -> bool:
        """魔法を使用"""
        if self.can_use():
            self.current_uses -= 1
            return True
        return False
    
    def restore_uses(self):
        """使用回数を回復"""
        self.current_uses = self.max_uses
    
    def to_dict(self) -> Dict[str, Any]:
        """辞書形式でシリアライズ"""
        return {
            'slot_id': self.slot_id,
            'level': self.level,
            'spell_id': self.spell_id,
            'max_uses': self.max_uses,
            'current_uses': self.current_uses
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SpellSlot':
        """辞書からデシリアライズ"""
        return cls(
            slot_id=data.get('slot_id', str(uuid.uuid4())),
            level=data.get('level', 1),
            spell_id=data.get('spell_id'),
            max_uses=data.get('max_uses', 1),
            current_uses=data.get('current_uses', 1)
        )


class SpellBook:
    """魔法書（スロット管理）"""
    
    def __init__(self, owner_id: str):
        self.owner_id = owner_id
        self.learned_spells: List[str] = []        # 習得済み魔法ID
        self.spell_slots: Dict[int, List[SpellSlot]] = {}  # レベル別スロット
        
        # スロットを初期化
        self._initialize_slots()
        
        logger.debug(f"魔法書を初期化: {owner_id}")
    
    def _initialize_slots(self):
        """スロットを初期化"""
        spell_config = config_manager.load_config("spells")
        slots_config = spell_config.get("settings", {}).get("slots_per_level", {})
        
        for level, slot_count in slots_config.items():
            level_int = int(level)
            self.spell_slots[level_int] = []
            
            for _ in range(slot_count):
                slot = SpellSlot(level=level_int, max_uses=level_int)
                self.spell_slots[level_int].append(slot)
    
    def learn_spell(self, spell_id: str) -> bool:
        """魔法を習得"""
        if spell_id not in self.learned_spells:
            self.learned_spells.append(spell_id)
            logger.info(f"魔法を習得: {spell_id}")
            return True
        return False
    
    def forget_spell(self, spell_id: str) -> bool:
        """魔法を忘却"""
        if spell_id in self.learned_spells:
            self.learned_spells.remove(spell_id)
            
            # 装備中のスロットからも解除
            for level_slots in self.spell_slots.values():
                for slot in level_slots:
                    if slot.spell_id == spell_id:
                        slot.unequip_spell()
            
            logger.info(f"魔法を忘却: {spell_id}")
            return True
        return False
    
    def equip_spell_to_slot(self, spell_id: str, level: int, slot_index: int) -> bool:
        """スロットに魔法を装備"""
        # 基本バリデーション
        if not self._validate_spell_learning(spell_id):
            return False
        
        if not self._validate_slot_parameters(level, slot_index):
            return False
        
        slot = self.spell_slots[level][slot_index]
        
        # 魔法レベルチェック
        if not self._validate_spell_level(spell_id, level):
            return False
        
        return slot.equip_spell(spell_id)
    
    def _validate_spell_learning(self, spell_id: str) -> bool:
        """魔法習得状態をバリデーション"""
        if spell_id not in self.learned_spells:
            logger.warning(f"未習得の魔法: {spell_id}")
            return False
        return True
    
    def _validate_slot_parameters(self, level: int, slot_index: int) -> bool:
        """スロットパラメータをバリデーション"""
        if level not in self.spell_slots:
            logger.warning(f"無効なスロットレベル: {level}")
            return False
        
        level_slots = self.spell_slots[level]
        if slot_index < 0 or slot_index >= len(level_slots):
            logger.warning(f"無効なスロットインデックス: {slot_index}")
            return False
        
        return True
    
    def _validate_spell_level(self, spell_id: str, slot_level: int) -> bool:
        """魔法レベルをバリデーション"""
        from src.magic.spells import spell_manager
        spell = spell_manager.get_spell(spell_id)
        if spell and spell.level > slot_level:
            logger.warning(f"魔法レベル {spell.level} はスロットレベル {slot_level} より高い")
            return False
        return True
    
    def unequip_spell_from_slot(self, level: int, slot_index: int) -> Optional[str]:
        """スロットから魔法を解除"""
        if level not in self.spell_slots:
            return None
        
        level_slots = self.spell_slots[level]
        if slot_index < 0 or slot_index >= len(level_slots):
            return None
        
        return level_slots[slot_index].unequip_spell()
    
    def use_spell(self, level: int, slot_index: int) -> bool:
        """魔法を使用"""
        if level not in self.spell_slots:
            return False
        
        level_slots = self.spell_slots[level]
        if slot_index < 0 or slot_index >= len(level_slots):
            return False
        
        slot = level_slots[slot_index]
        return slot.use_spell()
    
    def restore_all_uses(self):
        """全スロットの使用回数を回復"""
        for level_slots in self.spell_slots.values():
            for slot in level_slots:
                slot.restore_uses()
        
        logger.info(f"魔法使用回数を回復: {self.owner_id}")
    
    def get_available_spells(self, level: int) -> List[Tuple[int, SpellSlot]]:
        """使用可能な魔法スロットを取得"""
        available = []
        if level in self.spell_slots:
            for i, slot in enumerate(self.spell_slots[level]):
                if slot.can_use():
                    available.append((i, slot))
        return available
    
    def get_spell_summary(self) -> Dict[str, Any]:
        """魔法書要約を取得"""
        summary = {
            'learned_count': len(self.learned_spells),
            'learned_spells': self.learned_spells.copy(),
            'slots_by_level': {},
            'total_slots': 0,
            'equipped_slots': 0,
            'available_uses': 0
        }
        
        for level, slots in self.spell_slots.items():
            level_info = {
                'total': len(slots),
                'equipped': sum(1 for slot in slots if not slot.is_empty()),
                'available': sum(1 for slot in slots if slot.can_use()),
                'slots': [
                    {
                        'spell_id': slot.spell_id,
                        'uses': f"{slot.current_uses}/{slot.max_uses}"
                    } for slot in slots
                ]
            }
            
            summary['slots_by_level'][level] = level_info
            summary['total_slots'] += level_info['total']
            summary['equipped_slots'] += level_info['equipped']
            summary['available_uses'] += level_info['available']
        
        return summary
    
    def to_dict(self) -> Dict[str, Any]:
        """辞書形式でシリアライズ"""
        return {
            'owner_id': self.owner_id,
            'learned_spells': self.learned_spells.copy(),
            'spell_slots': {
                str(level): [slot.to_dict() for slot in slots]
                for level, slots in self.spell_slots.items()
            }
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SpellBook':
        """辞書からデシリアライズ"""
        spellbook = cls(owner_id=data.get('owner_id', ''))
        
        # 習得済み魔法を復元
        spellbook.learned_spells = data.get('learned_spells', [])
        
        # スロットを復元
        spell_slots_data = data.get('spell_slots', {})
        spellbook.spell_slots = {}
        
        for level_str, slots_data in spell_slots_data.items():
            level = int(level_str)
            spellbook.spell_slots[level] = []
            
            for slot_data in slots_data:
                slot = SpellSlot.from_dict(slot_data)
                spellbook.spell_slots[level].append(slot)
        
        return spellbook


class SpellManager:
    """魔法管理システム"""
    
    def __init__(self):
        self.spells: Dict[str, Spell] = {}
        self.spell_config = {}
        
        self._load_spells()
        logger.debug("SpellManagerを初期化しました")
    
    def _load_spells(self):
        """魔法定義の読み込み"""
        self.spell_config = config_manager.load_config("spells")
        
        # 各カテゴリの魔法を読み込み
        categories = ['offensive_spells', 'divine_spells', 'utility_spells', 'advanced_spells']
        
        for category in categories:
            category_spells = self.spell_config.get(category, {})
            
            for spell_id, spell_data in category_spells.items():
                spell = Spell(spell_id, spell_data)
                self.spells[spell_id] = spell
        
        logger.info(f"{len(self.spells)} 個の魔法を読み込みました")
    
    def get_spell(self, spell_id: str) -> Optional[Spell]:
        """魔法を取得"""
        return self.spells.get(spell_id)
    
    def get_spells_by_level(self, level: int) -> List[Spell]:
        """レベル別魔法一覧を取得"""
        return [spell for spell in self.spells.values() if spell.level == level]
    
    def get_spells_by_school(self, school: SpellSchool) -> List[Spell]:
        """学派別魔法一覧を取得"""
        return [spell for spell in self.spells.values() if spell.school == school]
    
    def get_spells_by_class(self, character_class: str) -> List[Spell]:
        """クラス別使用可能魔法一覧を取得"""
        return [spell for spell in self.spells.values() if spell.can_use_by_class(character_class)]
    
    def get_learnable_spells(self, character_class: str, character_level: int) -> List[Spell]:
        """習得可能魔法一覧を取得"""
        spells = self.get_spells_by_class(character_class)
        return [spell for spell in spells if spell.level <= character_level]
    
    def reload_spells(self):
        """魔法定義の再読み込み"""
        self.spells.clear()
        self._load_spells()
        logger.info("魔法定義を再読み込みしました")


# グローバルインスタンス
spell_manager = SpellManager()