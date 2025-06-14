"""キャラクタークラス"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from enum import Enum
import uuid
from datetime import datetime

from src.character.stats import BaseStats, DerivedStats, StatGenerator, StatValidator
from src.core.config_manager import config_manager
from src.utils.logger import logger


class CharacterStatus(Enum):
    """キャラクター状態"""
    GOOD = "good"           # 良好
    INJURED = "injured"     # 負傷
    UNCONSCIOUS = "unconscious"  # 意識不明
    DEAD = "dead"          # 死亡
    ASHES = "ashes"        # 灰


@dataclass
class Experience:
    """経験値システム"""
    current_xp: int = 0
    level: int = 1
    
    def add_experience(self, amount: int, xp_table: Dict[int, int]) -> bool:
        """経験値を追加し、レベルアップしたかを返す"""
        self.current_xp += amount
        
        # レベルアップチェック
        old_level = self.level
        for level, required_xp in sorted(xp_table.items()):
            if self.current_xp >= required_xp:
                self.level = level
            else:
                break
        
        leveled_up = self.level > old_level
        if leveled_up:
            logger.info(f"レベルアップ: {old_level} -> {self.level}")
        
        return leveled_up
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'current_xp': self.current_xp,
            'level': self.level
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Experience':
        return cls(
            current_xp=data.get('current_xp', 0),
            level=data.get('level', 1)
        )


@dataclass
class Character:
    """キャラクタークラス"""
    # 基本情報
    character_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    race: str = "human"
    character_class: str = "fighter"
    
    # 統計値
    base_stats: BaseStats = field(default_factory=BaseStats)
    derived_stats: DerivedStats = field(default_factory=DerivedStats)
    
    # 経験値・レベル
    experience: Experience = field(default_factory=Experience)
    
    # 状態
    status: CharacterStatus = CharacterStatus.GOOD
    
    # インベントリ・装備（旧形式、互換性のため残す）
    inventory: List[str] = field(default_factory=list)  # アイテムID（廃止予定）
    equipped_items: Dict[str, str] = field(default_factory=dict)  # スロット -> アイテムID（廃止予定）
    
    # 新しいインベントリシステム
    _inventory_initialized: bool = field(default=False, init=False)
    _equipment_initialized: bool = field(default=False, init=False)
    _status_effects_initialized: bool = field(default=False, init=False)
    
    # メタ情報
    created_at: datetime = field(default_factory=datetime.now)
    
    def __post_init__(self):
        """初期化後処理"""
        if not self.name:
            self.name = f"Character_{self.character_id[:8]}"
    
    def initialize_inventory(self):
        """インベントリを初期化（遅延初期化）"""
        if not self._inventory_initialized:
            from src.inventory.inventory import inventory_manager
            inventory_manager.create_character_inventory(self.character_id)
            self._inventory_initialized = True
            logger.debug(f"キャラクターインベントリを初期化: {self.character_id}")
    
    def get_inventory(self):
        """インベントリを取得"""
        self.initialize_inventory()
        from src.inventory.inventory import inventory_manager
        return inventory_manager.get_character_inventory(self.character_id)
    
    def initialize_equipment(self):
        """装備システムを初期化（遅延初期化）"""
        if not self._equipment_initialized:
            from src.equipment.equipment import equipment_manager
            equipment_manager.create_character_equipment(self.character_id)
            self._equipment_initialized = True
            logger.debug(f"キャラクター装備システムを初期化: {self.character_id}")
    
    def get_equipment(self):
        """装備システムを取得"""
        self.initialize_equipment()
        from src.equipment.equipment import equipment_manager
        return equipment_manager.get_character_equipment(self.character_id)
    
    def initialize_status_effects(self):
        """ステータス効果システムを初期化（遅延初期化）"""
        if not self._status_effects_initialized:
            from src.effects.status_effects import status_effect_manager
            # ステータス効果管理は自動的に作成されるため、ここでは単にフラグを設定
            self._status_effects_initialized = True
            logger.debug(f"キャラクターステータス効果システムを初期化: {self.character_id}")
    
    def get_status_effects(self):
        """ステータス効果管理を取得"""
        self.initialize_status_effects()
        from src.effects.status_effects import status_effect_manager
        return status_effect_manager.get_character_effects(self.character_id)
    
    @classmethod
    def create_character(
        cls,
        name: str,
        race: str,
        character_class: str,
        base_stats: Optional[BaseStats] = None
    ) -> 'Character':
        """新しいキャラクターを作成"""
        # 設定データの読み込み
        char_config = config_manager.load_config("characters")
        races_config = char_config.get("races", {})
        classes_config = char_config.get("classes", {})
        
        # 種族・職業の検証
        if race not in races_config:
            raise ValueError(f"無効な種族: {race}")
        if character_class not in classes_config:
            raise ValueError(f"無効な職業: {character_class}")
        
        # 統計値の生成または適用
        if base_stats is None:
            creation_config = char_config.get("character_creation", {})
            method = creation_config.get("stat_roll_method", "4d6_drop_lowest")
            base_stats = StatGenerator.generate_stats(method)
        
        # 種族ボーナスの適用
        race_config = races_config[race]
        race_bonuses = race_config.get("base_stats", {})
        base_stats = base_stats.add_bonuses(race_bonuses)
        
        # 職業要件の確認
        class_config = classes_config[character_class]
        if not StatValidator.check_class_requirements(base_stats, class_config):
            raise ValueError(f"統計値が職業要件を満たしていません: {character_class}")
        
        # 職業ボーナスの適用
        class_bonuses = class_config.get("base_stats", {})
        final_stats = base_stats.add_bonuses(class_bonuses)
        
        # 派生統計値の計算
        derived_stats = StatGenerator.calculate_derived_stats(
            final_stats, 1, class_config, race_config
        )
        
        character = cls(
            name=name,
            race=race,
            character_class=character_class,
            base_stats=final_stats,
            derived_stats=derived_stats
        )
        
        logger.info(f"キャラクターを作成しました: {name} ({race} {character_class})")
        return character
    
    def level_up(self) -> bool:
        """レベルアップ処理"""
        char_config = config_manager.load_config("characters")
        xp_table = char_config.get("level_progression", {}).get("experience_table", {})
        
        # レベルアップ判定
        old_level = self.experience.level
        leveled_up = self.experience.add_experience(0, xp_table)  # 現在のXPでレベルチェック
        
        if leveled_up:
            # 統計値の再計算
            races_config = char_config.get("races", {})
            classes_config = char_config.get("classes", {})
            
            race_config = races_config.get(self.race, {})
            class_config = classes_config.get(self.character_class, {})
            
            self.derived_stats = StatGenerator.calculate_derived_stats(
                self.base_stats, self.experience.level, class_config, race_config
            )
            
            logger.info(f"{self.name} がレベルアップしました: {old_level} -> {self.experience.level}")
        
        return leveled_up
    
    def add_experience(self, amount: int) -> bool:
        """経験値を追加"""
        char_config = config_manager.load_config("characters")
        xp_table = char_config.get("level_progression", {}).get("experience_table", {})
        
        old_xp = self.experience.current_xp
        leveled_up = self.experience.add_experience(amount, xp_table)
        
        logger.info(f"{self.name} が経験値を獲得: +{amount} ({old_xp} -> {self.experience.current_xp})")
        
        if leveled_up:
            self.level_up()
        
        return leveled_up
    
    def heal(self, amount: int):
        """HP回復"""
        old_hp = self.derived_stats.current_hp
        self.derived_stats.current_hp = min(
            self.derived_stats.max_hp,
            self.derived_stats.current_hp + amount
        )
        healed = self.derived_stats.current_hp - old_hp
        
        if healed > 0:
            logger.info(f"{self.name} がHP回復: +{healed}")
    
    def get_effective_stats(self) -> BaseStats:
        """装備ボーナスとステータス効果を含む実効能力値を取得"""
        effective_stats = BaseStats(
            strength=self.base_stats.strength,
            agility=self.base_stats.agility,
            intelligence=self.base_stats.intelligence,
            faith=self.base_stats.faith,
            luck=self.base_stats.luck
        )
        
        # 装備ボーナスを追加
        if self._equipment_initialized:
            equipment = self.get_equipment()
            if equipment:
                bonus = equipment.calculate_equipment_bonus()
                effective_stats.strength += bonus.strength
                effective_stats.agility += bonus.agility
                effective_stats.intelligence += bonus.intelligence
                effective_stats.faith += bonus.faith
                effective_stats.luck += bonus.luck
        
        # ステータス効果による修正値を追加
        if self._status_effects_initialized:
            status_effects = self.get_status_effects()
            modifiers = status_effects.get_stat_modifiers()
            effective_stats.strength += modifiers.get('strength', 0)
            effective_stats.agility += modifiers.get('agility', 0)
            effective_stats.intelligence += modifiers.get('intelligence', 0)
            effective_stats.faith += modifiers.get('faith', 0)
            effective_stats.luck += modifiers.get('luck', 0)
        
        return effective_stats
    
    def get_attack_power(self) -> int:
        """攻撃力を取得（装備ボーナス・ステータス効果含む）"""
        base_attack = self.base_stats.strength  # 基本攻撃力は力に依存
        
        equipment_bonus = 0
        if self._equipment_initialized:
            equipment = self.get_equipment()
            if equipment:
                bonus = equipment.calculate_equipment_bonus()
                equipment_bonus = bonus.attack_power
        
        # ステータス効果による攻撃力修正
        status_bonus = 0
        if self._status_effects_initialized:
            status_effects = self.get_status_effects()
            modifiers = status_effects.get_stat_modifiers()
            status_bonus = modifiers.get('attack', 0)
        
        return base_attack + equipment_bonus + status_bonus
    
    def get_defense(self) -> int:
        """防御力を取得（装備ボーナス・ステータス効果含む）"""
        base_defense = self.base_stats.strength // 2  # 基本防御力は力の半分
        
        equipment_bonus = 0
        if self._equipment_initialized:
            equipment = self.get_equipment()
            if equipment:
                bonus = equipment.calculate_equipment_bonus()
                equipment_bonus = bonus.defense
        
        # ステータス効果による防御力修正
        status_bonus = 0
        if self._status_effects_initialized:
            status_effects = self.get_status_effects()
            modifiers = status_effects.get_stat_modifiers()
            status_bonus = modifiers.get('defense', 0)
        
        return base_defense + equipment_bonus + status_bonus
    
    def take_damage(self, amount: int):
        """ダメージを受ける"""
        old_hp = self.derived_stats.current_hp
        self.derived_stats.current_hp = max(0, self.derived_stats.current_hp - amount)
        damage_taken = old_hp - self.derived_stats.current_hp
        
        if damage_taken > 0:
            logger.info(f"{self.name} がダメージを受けました: -{damage_taken}")
            
            # 状態の更新
            if self.derived_stats.current_hp == 0:
                if self.status == CharacterStatus.GOOD:
                    self.status = CharacterStatus.UNCONSCIOUS
                elif self.status == CharacterStatus.UNCONSCIOUS:
                    self.status = CharacterStatus.DEAD
                logger.warning(f"{self.name} の状態が変化: {self.status.value}")
    
    def restore_mp(self, amount: int):
        """MP回復"""
        old_mp = self.derived_stats.current_mp
        self.derived_stats.current_mp = min(
            self.derived_stats.max_mp,
            self.derived_stats.current_mp + amount
        )
        restored = self.derived_stats.current_mp - old_mp
        
        if restored > 0:
            logger.info(f"{self.name} がMP回復: +{restored}")
    
    def is_alive(self) -> bool:
        """生存しているかチェック"""
        return self.status in [CharacterStatus.GOOD, CharacterStatus.INJURED]
    
    def is_conscious(self) -> bool:
        """意識があるかチェック"""
        return self.status == CharacterStatus.GOOD
    
    def get_race_name(self) -> str:
        """種族名を取得"""
        return config_manager.get_text(f"race.{self.race}")
    
    def get_class_name(self) -> str:
        """職業名を取得"""
        return config_manager.get_text(f"class.{self.character_class}")
    
    def can_use_spell(self, spell) -> bool:
        """魔法が使用可能かチェック"""
        if not spell:
            return False
        
        # MPチェック
        if hasattr(spell, 'mp_cost'):
            mp_cost = spell.mp_cost
        else:
            # スペルコストから推定（簡易実装）
            mp_cost = getattr(spell, 'cost', 0) // 100  # コストの1/100をMP消費とする
        
        if self.derived_stats.current_mp < mp_cost:
            return False
        
        # レベルチェック
        if hasattr(spell, 'level') and spell.level > self.experience.level:
            return False
        
        # クラス制限チェック
        if hasattr(spell, 'school'):
            school = spell.school.value if hasattr(spell.school, 'value') else str(spell.school)
            if school == 'mage' and self.character_class not in ['mage', 'bishop', 'samurai']:
                return False
            elif school == 'priest' and self.character_class not in ['priest', 'bishop', 'lord']:
                return False
        
        return True
    
    def use_mp(self, amount: int):
        """MPを消費"""
        self.derived_stats.current_mp = max(0, self.derived_stats.current_mp - amount)
        logger.debug(f"{self.name}がMP {amount}を消費（残り: {self.derived_stats.current_mp}/{self.derived_stats.max_mp}）")
    
    def restore_mp(self, amount: int):
        """MPを回復"""
        old_mp = self.derived_stats.current_mp
        self.derived_stats.current_mp = min(self.derived_stats.max_mp, self.derived_stats.current_mp + amount)
        actual_restore = self.derived_stats.current_mp - old_mp
        logger.debug(f"{self.name}がMP {actual_restore}を回復（現在: {self.derived_stats.current_mp}/{self.derived_stats.max_mp}）")
        return actual_restore
    
    def add_status_effect(self, effect: str):
        """状態効果を追加"""
        # 状態効果システムとの連携（簡易実装）
        self.initialize_status_effects()
        from src.effects.status_effects import status_effect_manager, StatusEffectType, effect_registry
        
        # 文字列から StatusEffectType への変換
        try:
            effect_type = StatusEffectType(effect)
            if effect_type in effect_registry:
                effect_instance = effect_registry[effect_type](effect_type, duration=3, strength=1)
                character_manager = status_effect_manager.get_character_effects(self.character_id)
                success, result = character_manager.add_effect(effect_instance, self)
                logger.debug(f"{self.name}に{effect}が付与されました")
            else:
                logger.warning(f"未対応の状態効果: {effect}")
        except ValueError:
            # カスタム効果（defending等）の場合は簡易実装
            logger.debug(f"{self.name}に{effect}が付与されました（簡易実装）")
    
    def initialize_status_effects(self):
        """状態効果システムを初期化（遅延初期化）"""
        if not self._status_effects_initialized:
            from src.effects.status_effects import status_effect_manager
            # 必要に応じて初期化処理
            self._status_effects_initialized = True
    
    def revive(self):
        """蘇生"""
        if self.status in [CharacterStatus.DEAD, CharacterStatus.ASHES]:
            self.status = CharacterStatus.GOOD
            self.derived_stats.current_hp = max(1, self.derived_stats.max_hp // 4)  # 最大HPの1/4で蘇生
            logger.info(f"{self.name}が蘇生しました")
        else:
            logger.warning(f"{self.name}は死亡していないため蘇生できません")
    
    def to_dict(self) -> Dict[str, Any]:
        """辞書形式でシリアライズ"""
        return {
            'character_id': self.character_id,
            'name': self.name,
            'race': self.race,
            'character_class': self.character_class,
            'base_stats': self.base_stats.to_dict(),
            'derived_stats': self.derived_stats.to_dict(),
            'experience': self.experience.to_dict(),
            'status': self.status.value,
            'inventory': self.inventory.copy(),
            'equipped_items': self.equipped_items.copy(),
            'created_at': self.created_at.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Character':
        """辞書からデシリアライズ"""
        character = cls(
            character_id=data.get('character_id', str(uuid.uuid4())),
            name=data.get('name', ''),
            race=data.get('race', 'human'),
            character_class=data.get('character_class', 'fighter'),
            base_stats=BaseStats.from_dict(data.get('base_stats', {})),
            derived_stats=DerivedStats.from_dict(data.get('derived_stats', {})),
            experience=Experience.from_dict(data.get('experience', {})),
            status=CharacterStatus(data.get('status', 'good')),
            inventory=data.get('inventory', []),
            equipped_items=data.get('equipped_items', {}),
            created_at=datetime.fromisoformat(data.get('created_at', datetime.now().isoformat()))
        )
        return character