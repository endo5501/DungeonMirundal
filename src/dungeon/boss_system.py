"""ダンジョンボス戦システム"""

from typing import Dict, List, Tuple, Optional, Any, Union
from enum import Enum
from dataclasses import dataclass
import random

from src.character.party import Party
from src.monsters.monster import Monster
from src.utils.logger import logger


class BossType(Enum):
    """ボスタイプ"""
    FLOOR_BOSS = "floor_boss"       # フロアボス（各階の主）
    AREA_BOSS = "area_boss"         # エリアボス（5階層ごと）
    DUNGEON_BOSS = "dungeon_boss"   # ダンジョンボス（最終ボス）
    SECRET_BOSS = "secret_boss"     # 隠しボス
    RAID_BOSS = "raid_boss"         # レイドボス（特別強敵）


class BossPhase(Enum):
    """ボス戦フェーズ"""
    INITIAL = "initial"             # 初期フェーズ
    ENRAGED = "enraged"             # 激怒フェーズ（HP50%以下）
    DESPERATE = "desperate"         # 最後のあがき（HP20%以下）
    DEFEATED = "defeated"           # 撃破


@dataclass
class BossData:
    """ボス戦データ"""
    boss_type: BossType
    name: str
    description: str
    level: int
    max_hp: int
    special_abilities: List[str]
    phase_triggers: Dict[BossPhase, float] = None  # フェーズ移行HP割合
    victory_rewards: Dict[str, Any] = None
    defeat_consequences: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.phase_triggers is None:
            self.phase_triggers = {
                BossPhase.INITIAL: 1.0,
                BossPhase.ENRAGED: 0.5,
                BossPhase.DESPERATE: 0.2
            }
        if self.victory_rewards is None:
            self.victory_rewards = {}
        if self.defeat_consequences is None:
            self.defeat_consequences = {}


class BossEncounter:
    """ボス戦エンカウンター管理"""
    
    def __init__(self, boss_data: BossData, dungeon_level: int):
        self.boss_data = boss_data
        self.dungeon_level = dungeon_level
        self.current_phase = BossPhase.INITIAL
        self.phases_completed = []
        self.special_abilities_used = []
        self.turn_count = 0
        self.boss_monster: Optional[Monster] = None
        logger.info(f"ボス戦開始: {boss_data.name}")
    
    def initialize_boss_monster(self) -> Monster:
        """ボスモンスターを初期化"""
        # 基本ステータス計算
        level_modifier = 1 + (self.dungeon_level - 1) * 0.2
        
        # 簡易的なボスモンスター作成
        from src.monsters.monster import MonsterStats
        
        boss_stats = MonsterStats(
            level=self.boss_data.level + self.dungeon_level,
            hit_points=int(self.boss_data.max_hp * level_modifier),
            armor_class=15 + self.dungeon_level,
            attack_bonus=5 + self.dungeon_level,
            damage_dice="2d8",
            strength=15 + self.dungeon_level * 2,
            agility=12 + self.dungeon_level,
            intelligence=14 + self.dungeon_level,
            faith=10 + self.dungeon_level,
            luck=8 + self.dungeon_level
        )
        
        # ボスモンスター作成  
        from src.monsters.monster import MonsterType, MonsterSize
        
        self.boss_monster = Monster(
            monster_id=f"boss_{self.boss_data.name.lower().replace(' ', '_')}",
            name=self.boss_data.name,
            description=self.boss_data.description,
            monster_type=MonsterType.UNDEAD,  # デフォルトでアンデッド
            size=MonsterSize.LARGE,  # デフォルトで大型
            stats=boss_stats,
            experience_value=self.boss_data.level * 50 + self.dungeon_level * 25
        )
        
        return self.boss_monster
    
    def check_phase_transition(self) -> Optional[BossPhase]:
        """フェーズ移行チェック"""
        if not self.boss_monster:
            return None
        
        hp_ratio = self.boss_monster.current_hp / self.boss_monster.max_hp
        
        # フェーズ移行判定
        for phase, threshold in sorted(self.boss_data.phase_triggers.items(), 
                                     key=lambda x: x[1], reverse=True):
            if hp_ratio <= threshold and phase not in self.phases_completed:
                if phase != self.current_phase:
                    old_phase = self.current_phase
                    self.current_phase = phase
                    self.phases_completed.append(old_phase)
                    logger.info(f"ボス戦フェーズ移行: {old_phase.value} -> {phase.value}")
                    return phase
        
        return None
    
    def get_phase_abilities(self) -> List[str]:
        """現在フェーズで使用可能な特殊能力を取得"""
        base_abilities = self.boss_data.special_abilities.copy()
        
        # フェーズに応じて追加能力
        if self.current_phase == BossPhase.ENRAGED:
            base_abilities.extend(["rage_attack", "intimidating_roar"])
        elif self.current_phase == BossPhase.DESPERATE:
            base_abilities.extend(["desperate_strike", "last_stand", "death_curse"])
        
        return base_abilities
    
    def execute_special_ability(self, ability_name: str, party: Party) -> Dict[str, Any]:
        """特殊能力実行"""
        self.special_abilities_used.append(ability_name)
        logger.info(f"ボス特殊能力発動: {ability_name}")
        
        result = {
            "ability_name": ability_name,
            "success": True,
            "message": "",
            "effects": []
        }
        
        # 特殊能力の効果実装
        if ability_name == "rage_attack":
            result.update(self._execute_rage_attack(party))
        elif ability_name == "intimidating_roar":
            result.update(self._execute_intimidating_roar(party))
        elif ability_name == "desperate_strike":
            result.update(self._execute_desperate_strike(party))
        elif ability_name == "last_stand":
            result.update(self._execute_last_stand())
        elif ability_name == "death_curse":
            result.update(self._execute_death_curse(party))
        elif ability_name == "heal_self":
            result.update(self._execute_heal_self())
        elif ability_name == "summon_minions":
            result.update(self._execute_summon_minions())
        elif ability_name == "area_attack":
            result.update(self._execute_area_attack(party))
        else:
            result.update(self._execute_generic_ability(ability_name, party))
        
        return result
    
    def _execute_rage_attack(self, party: Party) -> Dict[str, Any]:
        """怒りの攻撃"""
        target = random.choice(party.get_living_characters())
        if target:
            damage = (self.boss_monster.stats.attack_bonus * 1.5) + random.randint(5, 15)
            actual_damage = target.take_damage(int(damage))
            return {
                "message": f"{self.boss_data.name}の怒りの攻撃！",
                "effects": [f"{target.name}に{actual_damage}の大ダメージ！"]
            }
        return {"message": "怒りの攻撃は空振りした", "effects": []}
    
    def _execute_intimidating_roar(self, party: Party) -> Dict[str, Any]:
        """威嚇の咆哮"""
        effects = []
        for character in party.get_living_characters():
            if random.random() < 0.6:  # 60%で成功
                character.add_status_effect("fear")
                effects.append(f"{character.name}が恐怖状態になった")
        
        return {
            "message": f"{self.boss_data.name}の威嚇の咆哮！",
            "effects": effects or ["誰も恐怖しなかった"]
        }
    
    def _execute_desperate_strike(self, party: Party) -> Dict[str, Any]:
        """渾身の一撃"""
        target = random.choice(party.get_living_characters())
        if target:
            # 現在HPに比例した威力
            hp_ratio = self.boss_monster.current_hp / self.boss_monster.max_hp
            damage_multiplier = 2.0 - hp_ratio  # HPが少ないほど威力増加
            damage = self.boss_monster.stats.attack_bonus * damage_multiplier
            actual_damage = target.take_damage(int(damage))
            return {
                "message": f"{self.boss_data.name}の渾身の一撃！",
                "effects": [f"{target.name}に{actual_damage}の特大ダメージ！"]
            }
        return {"message": "渾身の一撃は外れた", "effects": []}
    
    def _execute_last_stand(self) -> Dict[str, Any]:
        """最後の抵抗"""
        # 自己回復
        heal_amount = self.boss_monster.max_hp // 4
        self.boss_monster.current_hp = min(
            self.boss_monster.max_hp,
            self.boss_monster.current_hp + heal_amount
        )
        
        return {
            "message": f"{self.boss_data.name}が最後の力を振り絞った！",
            "effects": [f"HP {heal_amount} 回復", "全能力値が一時的に上昇"]
        }
    
    def _execute_death_curse(self, party: Party) -> Dict[str, Any]:
        """死の呪い"""
        effects = []
        for character in party.get_living_characters():
            if random.random() < 0.3:  # 30%で呪い
                character.add_status_effect("curse")
                effects.append(f"{character.name}が呪われた")
        
        return {
            "message": f"{self.boss_data.name}が死の呪いを放った！",
            "effects": effects or ["呪いは誰にも届かなかった"]
        }
    
    def _execute_heal_self(self) -> Dict[str, Any]:
        """自己回復"""
        heal_amount = self.boss_monster.max_hp // 6
        self.boss_monster.current_hp = min(
            self.boss_monster.max_hp,
            self.boss_monster.current_hp + heal_amount
        )
        
        return {
            "message": f"{self.boss_data.name}が魔法で回復した！",
            "effects": [f"HP {heal_amount} 回復"]
        }
    
    def _execute_summon_minions(self) -> Dict[str, Any]:
        """手下召喚"""
        # 実際の手下生成は戦闘システムで処理
        return {
            "message": f"{self.boss_data.name}が手下を召喚した！",
            "effects": ["手下モンスターが出現"],
            "summon_minions": True
        }
    
    def _execute_area_attack(self, party: Party) -> Dict[str, Any]:
        """範囲攻撃"""
        effects = []
        base_damage = self.boss_monster.stats.attack_bonus + 10  # 基本攻撃力
        
        for character in party.get_living_characters():
            damage = base_damage + random.randint(1, 8)
            actual_damage = character.take_damage(damage)
            effects.append(f"{character.name}に{actual_damage}ダメージ")
        
        return {
            "message": f"{self.boss_data.name}の範囲攻撃！",
            "effects": effects
        }
    
    def _execute_generic_ability(self, ability_name: str, party: Party) -> Dict[str, Any]:
        """汎用特殊能力"""
        return {
            "message": f"{self.boss_data.name}が{ability_name}を使用した！",
            "effects": ["特殊な効果が発動"]
        }
    
    def get_victory_rewards(self) -> Dict[str, Any]:
        """勝利報酬を取得"""
        base_rewards = self.boss_data.victory_rewards.copy()
        
        # レベルに応じて報酬調整
        level_modifier = 1 + (self.dungeon_level - 1) * 0.3
        
        if "experience" in base_rewards:
            base_rewards["experience"] = int(base_rewards["experience"] * level_modifier)
        if "gold" in base_rewards:
            base_rewards["gold"] = int(base_rewards["gold"] * level_modifier)
        
        # 特別報酬
        if self.boss_data.boss_type == BossType.DUNGEON_BOSS:
            base_rewards["special_items"] = base_rewards.get("special_items", [])
            base_rewards["title"] = f"ダンジョン征服者"
        
        return base_rewards
    
    def advance_turn(self):
        """ターン進行"""
        self.turn_count += 1


class BossSystem:
    """ボス戦システム管理"""
    
    def __init__(self):
        self.boss_definitions = self._initialize_boss_definitions()
        self.active_encounters: Dict[str, BossEncounter] = {}
        logger.info("BossSystem初期化完了")
    
    def _initialize_boss_definitions(self) -> Dict[str, BossData]:
        """ボス定義を初期化"""
        return {
            "skeleton_king": BossData(
                BossType.FLOOR_BOSS,
                "スケルトンキング",
                "アンデッドの王。骨の軍勢を率いる。",
                level=5,
                max_hp=120,
                special_abilities=["summon_minions", "bone_armor", "death_curse"],
                victory_rewards={"experience": 200, "gold": 100, "items": ["骨の王冠"]},
                defeat_consequences={"level_down": True}
            ),
            "dragon_whelp": BossData(
                BossType.AREA_BOSS,
                "ドラゴンの幼体",
                "まだ若いドラゴン。それでも強大な力を持つ。",
                level=10,
                max_hp=300,
                special_abilities=["fire_breath", "wing_attack", "intimidating_roar"],
                victory_rewards={"experience": 500, "gold": 300, "items": ["ドラゴンの鱗"]},
                defeat_consequences={"treasure_loss": 0.3}
            ),
            "ancient_golem": BossData(
                BossType.DUNGEON_BOSS,
                "古代のゴーレム",
                "古代文明が作り出した最強の守護者。",
                level=20,
                max_hp=800,
                special_abilities=["earthquake", "laser_beam", "self_repair", "magic_immunity"],
                victory_rewards={"experience": 2000, "gold": 1000, "items": ["古代の核"]},
                defeat_consequences={"party_wipe": True}
            ),
            "shadow_lord": BossData(
                BossType.SECRET_BOSS,
                "影の王",
                "闇に潜む邪悪な存在。発見するのも困難。",
                level=25,
                max_hp=1200,
                special_abilities=["shadow_clone", "darkness", "life_drain", "phase_shift"],
                victory_rewards={"experience": 5000, "gold": 2000, "items": ["影の王冠", "闇の宝珠"]},
                defeat_consequences={"curse_all": True}
            )
        }
    
    def create_boss_encounter(self, boss_id: str, dungeon_level: int, encounter_id: str) -> Optional[BossEncounter]:
        """ボス戦エンカウンターを作成"""
        boss_data = self.boss_definitions.get(boss_id)
        if not boss_data:
            logger.error(f"未知のボス: {boss_id}")
            return None
        
        encounter = BossEncounter(boss_data, dungeon_level)
        self.active_encounters[encounter_id] = encounter
        
        return encounter
    
    def get_boss_encounter(self, encounter_id: str) -> Optional[BossEncounter]:
        """ボス戦エンカウンターを取得"""
        return self.active_encounters.get(encounter_id)
    
    def complete_boss_encounter(self, encounter_id: str, victory: bool) -> Dict[str, Any]:
        """ボス戦完了処理"""
        encounter = self.active_encounters.get(encounter_id)
        if not encounter:
            return {"success": False, "message": "ボス戦が見つかりません"}
        
        result = {
            "success": True,
            "victory": victory,
            "boss_name": encounter.boss_data.name,
            "turn_count": encounter.turn_count,
            "phases_completed": len(encounter.phases_completed)
        }
        
        if victory:
            result["rewards"] = encounter.get_victory_rewards()
            result["message"] = f"{encounter.boss_data.name}を撃破した！"
        else:
            result["consequences"] = encounter.boss_data.defeat_consequences
            result["message"] = f"{encounter.boss_data.name}に敗北した..."
        
        # エンカウンター終了
        del self.active_encounters[encounter_id]
        
        return result
    
    def generate_boss_for_level(self, dungeon_level: int) -> Optional[str]:
        """ダンジョンレベルに適したボスを生成"""
        suitable_bosses = []
        
        for boss_id, boss_data in self.boss_definitions.items():
            if boss_data.boss_type == BossType.FLOOR_BOSS:
                # フロアボスは任意のレベルで出現可能
                suitable_bosses.append(boss_id)
            elif boss_data.boss_type == BossType.AREA_BOSS:
                # エリアボスは5の倍数階で出現
                if dungeon_level % 5 == 0:
                    suitable_bosses.append(boss_id)
            elif boss_data.boss_type == BossType.DUNGEON_BOSS:
                # ダンジョンボスは最深部のみ
                if dungeon_level >= 20:
                    suitable_bosses.append(boss_id)
            elif boss_data.boss_type == BossType.SECRET_BOSS:
                # 隠しボスは低確率で出現
                if random.random() < 0.05:  # 5%
                    suitable_bosses.append(boss_id)
        
        return random.choice(suitable_bosses) if suitable_bosses else None
    
    def is_boss_level(self, dungeon_level: int) -> bool:
        """ボス戦フロアかチェック"""
        # 5の倍数階はエリアボス
        if dungeon_level % 5 == 0:
            return True
        
        # 20階以上はダンジョンボス
        if dungeon_level >= 20:
            return True
        
        # 10%の確率でフロアボス
        return random.random() < 0.1


# グローバルインスタンス
boss_system = BossSystem()