"""ダンジョントラップシステム"""

from typing import Dict, List, Tuple, Optional, Any
from enum import Enum
from dataclasses import dataclass
import random

from src.character.character import Character
from src.character.party import Party
from src.utils.logger import logger


class TrapType(Enum):
    """トラップタイプ"""
    ARROW = "arrow"             # 矢の罠
    SPIKE = "spike"             # 棘の罠  
    POISON_GAS = "poison_gas"   # 毒ガス
    PARALYSIS = "paralysis"     # 麻痺の罠
    TELEPORT = "teleport"       # テレポート罠
    SLEEP = "sleep"             # 睡眠の罠
    STAT_DRAIN = "stat_drain"   # 能力値減少
    GOLD_THEFT = "gold_theft"   # 金貨盗難
    ITEM_LOSS = "item_loss"     # アイテム紛失
    ILLUSION = "illusion"       # 幻惑の罠


@dataclass
class TrapData:
    """トラップデータ"""
    trap_type: TrapType
    name: str
    description: str
    damage_range: Tuple[int, int]
    success_rate: float = 0.7
    effect_duration: int = 0
    special_effects: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.special_effects is None:
            self.special_effects = {}


class TrapSystem:
    """トラップシステム管理"""
    
    def __init__(self):
        self.trap_definitions = self._initialize_trap_definitions()
        logger.info("TrapSystem初期化完了")
    
    def _initialize_trap_definitions(self) -> Dict[TrapType, TrapData]:
        """トラップ定義を初期化"""
        return {
            TrapType.ARROW: TrapData(
                TrapType.ARROW,
                "矢の罠",
                "隠された弓から矢が飛び出す",
                (5, 15),
                0.8
            ),
            TrapType.SPIKE: TrapData(
                TrapType.SPIKE,
                "棘の罠", 
                "床から鋭い棘が突き出る",
                (8, 20),
                0.7
            ),
            TrapType.POISON_GAS: TrapData(
                TrapType.POISON_GAS,
                "毒ガスの罠",
                "毒ガスが噴出する",
                (3, 8),
                0.6,
                3,
                {"status_effect": "poison"}
            ),
            TrapType.PARALYSIS: TrapData(
                TrapType.PARALYSIS,
                "麻痺の罠",
                "電撃により身体が麻痺する", 
                (2, 6),
                0.5,
                2,
                {"status_effect": "paralysis"}
            ),
            TrapType.TELEPORT: TrapData(
                TrapType.TELEPORT,
                "テレポート罠",
                "魔法陣によりランダムな場所に転送される",
                (0, 0),
                0.9,
                0,
                {"teleport": True}
            ),
            TrapType.SLEEP: TrapData(
                TrapType.SLEEP,
                "睡眠の罠",
                "眠気を誘う魔法が発動する",
                (0, 0),
                0.4,
                3,
                {"status_effect": "sleep"}
            ),
            TrapType.STAT_DRAIN: TrapData(
                TrapType.STAT_DRAIN,
                "能力値減少の罠",
                "呪いにより能力値が一時的に減少する",
                (0, 0),
                0.6,
                5,
                {"stat_drain": True}
            ),
            TrapType.GOLD_THEFT: TrapData(
                TrapType.GOLD_THEFT,
                "金貨盗難の罠",
                "隠された盗賊により金貨が盗まれる",
                (0, 0),
                0.7,
                0,
                {"gold_theft": True}
            ),
            TrapType.ITEM_LOSS: TrapData(
                TrapType.ITEM_LOSS,
                "アイテム紛失の罠",
                "瞬間移動によりアイテムが紛失する",
                (0, 0),
                0.3,
                0,
                {"item_loss": True}
            ),
            TrapType.ILLUSION: TrapData(
                TrapType.ILLUSION,
                "幻惑の罠",
                "幻覚により一時的に混乱する",
                (0, 0),
                0.5,
                2,
                {"status_effect": "confusion"}
            )
        }
    
    def generate_random_trap(self, dungeon_level: int) -> TrapType:
        """ダンジョンレベルに応じたランダムトラップを生成"""
        # レベルが高いほど危険なトラップが出現しやすい
        if dungeon_level <= 3:
            # 浅い階層: 基本的なトラップのみ
            candidates = [TrapType.ARROW, TrapType.SPIKE]
        elif dungeon_level <= 7:
            # 中層: 状態異常系も追加
            candidates = [TrapType.ARROW, TrapType.SPIKE, TrapType.POISON_GAS, TrapType.SLEEP]
        elif dungeon_level <= 12:
            # 深い階層: より危険なトラップ
            candidates = [
                TrapType.ARROW, TrapType.SPIKE, TrapType.POISON_GAS, 
                TrapType.PARALYSIS, TrapType.STAT_DRAIN, TrapType.GOLD_THEFT
            ]
        else:
            # 最深部: 全てのトラップ
            candidates = list(TrapType)
        
        return random.choice(candidates)
    
    def activate_trap(self, trap_type: TrapType, party: Party, dungeon_level: int = 1) -> Dict[str, Any]:
        """トラップを発動"""
        trap_data = self.trap_definitions.get(trap_type)
        if not trap_data:
            logger.error(f"未知のトラップタイプ: {trap_type}")
            return {"success": False, "message": "トラップの発動に失敗しました"}
        
        logger.info(f"トラップ発動: {trap_data.name}")
        
        # 発動判定
        if random.random() > trap_data.success_rate:
            return {
                "success": False,
                "message": f"{trap_data.name}が発動したが、回避できた！",
                "trap_name": trap_data.name
            }
        
        result = {
            "success": True,
            "message": f"{trap_data.name}が発動！{trap_data.description}",
            "trap_name": trap_data.name,
            "effects": []
        }
        
        # 対象選択（基本的にはランダムな生存メンバー）
        living_members = party.get_living_characters()
        if not living_members:
            result["message"] += "\n生存メンバーがいないため効果なし"
            return result
        
        # トラップ効果の適用
        if trap_type in [TrapType.ARROW, TrapType.SPIKE]:
            # ダメージ系トラップ
            target = random.choice(living_members)
            damage = self._apply_damage_trap(trap_data, target, dungeon_level)
            result["effects"].append(f"{target.name}が{damage}ダメージを受けた")
            
        elif trap_type in [TrapType.POISON_GAS, TrapType.PARALYSIS, TrapType.SLEEP, TrapType.ILLUSION]:
            # 状態異常系トラップ
            target = random.choice(living_members)
            effect_result = self._apply_status_trap(trap_data, target)
            result["effects"].append(effect_result)
            
        elif trap_type == TrapType.TELEPORT:
            # テレポート系トラップ
            teleport_result = self._apply_teleport_trap(party)
            result["effects"].append(teleport_result)
            result["teleport"] = True
            
        elif trap_type == TrapType.STAT_DRAIN:
            # 能力値減少トラップ
            target = random.choice(living_members)
            drain_result = self._apply_stat_drain_trap(trap_data, target)
            result["effects"].append(drain_result)
            
        elif trap_type == TrapType.GOLD_THEFT:
            # 金貨盗難トラップ
            theft_result = self._apply_gold_theft_trap(party)
            result["effects"].append(theft_result)
            
        elif trap_type == TrapType.ITEM_LOSS:
            # アイテム紛失トラップ
            loss_result = self._apply_item_loss_trap(party)
            result["effects"].append(loss_result)
        
        return result
    
    def _apply_damage_trap(self, trap_data: TrapData, target: Character, dungeon_level: int) -> int:
        """ダメージ系トラップの適用"""
        min_damage, max_damage = trap_data.damage_range
        
        # ダンジョンレベルに応じてダメージ調整
        level_modifier = 1 + (dungeon_level - 1) * 0.1
        min_damage = int(min_damage * level_modifier)
        max_damage = int(max_damage * level_modifier)
        
        damage = random.randint(min_damage, max_damage)
        
        # 対象の敏捷性で軽減判定
        if hasattr(target, 'base_stats') and target.base_stats.agility > 15:
            if random.random() < 0.3:  # 30%で部分回避
                damage = damage // 2
                logger.info(f"{target.name}が素早い動きで一部回避！")
        
        actual_damage = target.take_damage(damage)
        return actual_damage
    
    def _apply_status_trap(self, trap_data: TrapData, target: Character) -> str:
        """状態異常系トラップの適用"""
        status_effect = trap_data.special_effects.get("status_effect")
        if not status_effect:
            return f"{target.name}には効果がなかった"
        
        # 対象の抵抗力チェック
        resistance_chance = 0.2
        if hasattr(target, 'base_stats'):
            if status_effect in ["poison", "paralysis"]:
                resistance_chance += target.base_stats.strength * 0.01
            elif status_effect in ["sleep", "confusion"]:
                resistance_chance += target.base_stats.intelligence * 0.01
        
        if random.random() < resistance_chance:
            return f"{target.name}は{status_effect}を抵抗した！"
        
        # 状態異常を付与
        target.add_status_effect(status_effect)
        return f"{target.name}が{status_effect}状態になった"
    
    def _apply_teleport_trap(self, party: Party) -> str:
        """テレポート系トラップの適用"""
        # 実際のテレポート処理はダンジョンマネージャーで行う
        return "パーティがランダムな場所にテレポートした！"
    
    def _apply_stat_drain_trap(self, trap_data: TrapData, target: Character) -> str:
        """能力値減少トラップの適用"""
        # 一時的な能力値減少効果を付与
        drain_types = ["strength", "agility", "intelligence"]
        drain_stat = random.choice(drain_types)
        
        target.add_status_effect(f"stat_drain_{drain_stat}")
        return f"{target.name}の{drain_stat}が一時的に減少した"
    
    def _apply_gold_theft_trap(self, party: Party) -> str:
        """金貨盗難トラップの適用"""
        if party.gold <= 0:
            return "金貨を持っていないため盗まれなかった"
        
        # 5-20%の金貨を盗まれる
        theft_rate = random.uniform(0.05, 0.20)
        stolen_gold = int(party.gold * theft_rate)
        party.gold -= stolen_gold
        
        return f"金貨 {stolen_gold} が盗まれた！"
    
    def _apply_item_loss_trap(self, party: Party) -> str:
        """アイテム紛失トラップの適用"""
        # パーティの共有インベントリからランダムにアイテムを1つ紛失
        if hasattr(party, 'shared_inventory') and party.shared_inventory:
            items = party.shared_inventory.get_all_items()
            if items:
                lost_item = random.choice(items)
                party.shared_inventory.remove_item(lost_item.item_id, 1)
                return f"アイテム「{lost_item.name}」を紛失した！"
        
        return "紛失するアイテムがなかった"
    
    def can_detect_trap(self, character: Character, trap_type: TrapType) -> bool:
        """キャラクターがトラップを発見できるかチェック"""
        base_detection = 0.1  # 基本発見率
        
        # 盗賊系のクラスは発見率が高い
        if hasattr(character, 'character_class'):
            if character.character_class in ['thief', 'ninja']:
                base_detection += 0.4
            elif character.character_class in ['ranger', 'monk']:
                base_detection += 0.2
        
        # 知力による補正
        if hasattr(character, 'base_stats'):
            intelligence_bonus = (character.base_stats.intelligence - 10) * 0.02
            base_detection += intelligence_bonus
        
        # レベルによる補正
        if hasattr(character, 'experience'):
            level_bonus = character.experience.level * 0.01
            base_detection += level_bonus
        
        return random.random() < min(0.9, max(0.05, base_detection))
    
    def can_disarm_trap(self, character: Character, trap_type: TrapType) -> bool:
        """キャラクターがトラップを解除できるかチェック"""
        base_disarm = 0.05  # 基本解除率
        
        # 盗賊系のクラスは解除率が高い
        if hasattr(character, 'character_class'):
            if character.character_class == 'thief':
                base_disarm += 0.5
            elif character.character_class == 'ninja':
                base_disarm += 0.3
            elif character.character_class == 'ranger':
                base_disarm += 0.1
        
        # 敏捷性による補正
        if hasattr(character, 'base_stats'):
            agility_bonus = (character.base_stats.agility - 10) * 0.02
            base_disarm += agility_bonus
        
        # レベルによる補正
        if hasattr(character, 'experience'):
            level_bonus = character.experience.level * 0.02
            base_disarm += level_bonus
        
        return random.random() < min(0.8, max(0.01, base_disarm))


# グローバルインスタンス
trap_system = TrapSystem()