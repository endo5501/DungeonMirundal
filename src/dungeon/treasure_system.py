"""ダンジョン宝箱システム"""

from typing import Dict, List, Tuple, Optional, Any
from enum import Enum
from dataclasses import dataclass
import random

from src.character.party import Party
from src.items.item import Item, ItemType, ItemRarity
from src.utils.logger import logger


class TreasureType(Enum):
    """宝箱タイプ"""
    WOODEN = "wooden"       # 木製宝箱
    METAL = "metal"         # 金属宝箱
    MAGICAL = "magical"     # 魔法宝箱
    CURSED = "cursed"       # 呪われた宝箱
    MIMIC = "mimic"         # ミミック（偽装）


@dataclass
class TreasureData:
    """宝箱データ"""
    treasure_type: TreasureType
    name: str
    description: str
    lock_difficulty: int = 0    # 鍵開け難易度 (0-100)
    trap_chance: float = 0.0    # トラップ確率
    mimic_chance: float = 0.0   # ミミック確率
    gold_range: Tuple[int, int] = (0, 0)
    item_count_range: Tuple[int, int] = (0, 1)
    rarity_weights: Dict[ItemRarity, float] = None
    
    def __post_init__(self):
        if self.rarity_weights is None:
            self.rarity_weights = {
                ItemRarity.COMMON: 0.6,
                ItemRarity.UNCOMMON: 0.3,
                ItemRarity.RARE: 0.08,
                ItemRarity.EPIC: 0.02,
                ItemRarity.LEGENDARY: 0.001
            }


class TreasureSystem:
    """宝箱システム管理"""
    
    def __init__(self):
        self.treasure_definitions = self._initialize_treasure_definitions()
        self.opened_treasures: Dict[str, bool] = {}  # 開封済み宝箱の記録
        logger.info("TreasureSystem初期化完了")
    
    def _initialize_treasure_definitions(self) -> Dict[TreasureType, TreasureData]:
        """宝箱定義を初期化"""
        return {
            TreasureType.WOODEN: TreasureData(
                TreasureType.WOODEN,
                "木製の宝箱",
                "古い木でできた質素な宝箱",
                lock_difficulty=10,
                trap_chance=0.1,
                gold_range=(10, 50),
                item_count_range=(0, 2),
                rarity_weights={
                    ItemRarity.COMMON: 0.8,
                    ItemRarity.UNCOMMON: 0.2,
                    ItemRarity.RARE: 0.0,
                    ItemRarity.EPIC: 0.0,
                    ItemRarity.LEGENDARY: 0.0
                }
            ),
            TreasureType.METAL: TreasureData(
                TreasureType.METAL,
                "金属製の宝箱",
                "頑丈な金属でできた重厚な宝箱",
                lock_difficulty=30,
                trap_chance=0.25,
                gold_range=(50, 200),
                item_count_range=(1, 3),
                rarity_weights={
                    ItemRarity.COMMON: 0.5,
                    ItemRarity.UNCOMMON: 0.4,
                    ItemRarity.RARE: 0.1,
                    ItemRarity.EPIC: 0.0,
                    ItemRarity.LEGENDARY: 0.0
                }
            ),
            TreasureType.MAGICAL: TreasureData(
                TreasureType.MAGICAL,
                "魔法の宝箱",
                "魔力で守られた神秘的な宝箱",
                lock_difficulty=60,
                trap_chance=0.4,
                gold_range=(100, 500),
                item_count_range=(1, 4),
                rarity_weights={
                    ItemRarity.COMMON: 0.2,
                    ItemRarity.UNCOMMON: 0.4,
                    ItemRarity.RARE: 0.3,
                    ItemRarity.EPIC: 0.09,
                    ItemRarity.LEGENDARY: 0.01
                }
            ),
            TreasureType.CURSED: TreasureData(
                TreasureType.CURSED,
                "呪われた宝箱",
                "禍々しいオーラを放つ危険な宝箱",
                lock_difficulty=80,
                trap_chance=0.8,
                gold_range=(0, 100),
                item_count_range=(0, 2),
                rarity_weights={
                    ItemRarity.COMMON: 0.3,
                    ItemRarity.UNCOMMON: 0.3,
                    ItemRarity.RARE: 0.3,
                    ItemRarity.EPIC: 0.08,
                    ItemRarity.LEGENDARY: 0.02
                }
            ),
            TreasureType.MIMIC: TreasureData(
                TreasureType.MIMIC,
                "ミミック",
                "宝箱に擬態したモンスター",
                lock_difficulty=0,
                trap_chance=0.0,
                mimic_chance=1.0,
                gold_range=(20, 100),
                item_count_range=(0, 1)
            )
        }
    
    def generate_treasure_type(self, dungeon_level: int) -> TreasureType:
        """ダンジョンレベルに応じた宝箱タイプを生成"""
        if dungeon_level <= 3:
            # 浅い階層: 木製が多い
            weights = {
                TreasureType.WOODEN: 0.7,
                TreasureType.METAL: 0.25,
                TreasureType.MIMIC: 0.05
            }
        elif dungeon_level <= 7:
            # 中層: 金属製が増加
            weights = {
                TreasureType.WOODEN: 0.4,
                TreasureType.METAL: 0.45,
                TreasureType.MAGICAL: 0.05,
                TreasureType.MIMIC: 0.1
            }
        elif dungeon_level <= 12:
            # 深い階層: 魔法宝箱の出現
            weights = {
                TreasureType.WOODEN: 0.2,
                TreasureType.METAL: 0.4,
                TreasureType.MAGICAL: 0.25,
                TreasureType.CURSED: 0.05,
                TreasureType.MIMIC: 0.1
            }
        else:
            # 最深部: 危険な宝箱が増加
            weights = {
                TreasureType.WOODEN: 0.1,
                TreasureType.METAL: 0.3,
                TreasureType.MAGICAL: 0.35,
                TreasureType.CURSED: 0.15,
                TreasureType.MIMIC: 0.1
            }
        
        # 重み付きランダム選択
        treasure_types = list(weights.keys())
        weights_list = list(weights.values())
        return random.choices(treasure_types, weights=weights_list)[0]
    
    def open_treasure(self, treasure_id: str, treasure_type: TreasureType, party: Party, 
                     dungeon_level: int = 1, opener_character = None) -> Dict[str, Any]:
        """宝箱を開封"""
        # 既に開封済みかチェック
        if self.opened_treasures.get(treasure_id, False):
            return {
                "success": False,
                "message": "この宝箱は既に開封されている",
                "already_opened": True
            }
        
        treasure_data = self.treasure_definitions.get(treasure_type)
        if not treasure_data:
            logger.error(f"未知の宝箱タイプ: {treasure_type}")
            return {"success": False, "message": "宝箱の開封に失敗しました"}
        
        logger.info(f"宝箱開封: {treasure_data.name} (ID: {treasure_id})")
        
        result = {
            "success": True,
            "message": f"{treasure_data.name}を開封した！",
            "treasure_name": treasure_data.name,
            "contents": [],
            "gold": 0,
            "items": [],
            "mimic": False,
            "trapped": False
        }
        
        # ミミック判定
        if random.random() < treasure_data.mimic_chance:
            result["mimic"] = True
            result["message"] = "宝箱だと思ったらミミックだった！"
            result["success"] = False
            return result
        
        # 鍵開け判定
        if treasure_data.lock_difficulty > 0:
            lock_success = self._attempt_lock_picking(treasure_data.lock_difficulty, opener_character)
            if not lock_success:
                result["success"] = False
                result["message"] = f"{treasure_data.name}の鍵を開けられなかった"
                return result
        
        # トラップ判定
        if random.random() < treasure_data.trap_chance:
            result["trapped"] = True
            trap_result = self._trigger_treasure_trap(party, dungeon_level)
            result["message"] += f"\n{trap_result}"
        
        # 内容物生成
        contents = self._generate_treasure_contents(treasure_data, dungeon_level)
        
        # 金貨
        if contents["gold"] > 0:
            party.gold += contents["gold"]
            result["gold"] = contents["gold"]
            result["contents"].append(f"金貨 {contents['gold']} を獲得")
        
        # アイテム
        for item in contents["items"]:
            # パーティの共有インベントリに追加
            if hasattr(party, 'shared_inventory'):
                party.shared_inventory.add_item(item)
            result["items"].append(item)
            result["contents"].append(f"アイテム「{item.get_name()}」を獲得")
        
        # 開封済みマーク
        self.opened_treasures[treasure_id] = True
        
        return result
    
    def _attempt_lock_picking(self, lock_difficulty: int, opener_character = None) -> bool:
        """鍵開け試行"""
        base_success = max(0.1, 1.0 - (lock_difficulty / 100.0))
        
        if opener_character:
            # キャラクターの能力による補正
            if hasattr(opener_character, 'character_class'):
                if opener_character.character_class == 'thief':
                    base_success += 0.4
                elif opener_character.character_class == 'ninja':
                    base_success += 0.2
            
            # 敏捷性による補正
            if hasattr(opener_character, 'base_stats'):
                agility_bonus = (opener_character.base_stats.agility - 10) * 0.02
                base_success += agility_bonus
            
            # レベルによる補正
            if hasattr(opener_character, 'experience'):
                level_bonus = opener_character.experience.level * 0.01
                base_success += level_bonus
        
        return random.random() < min(0.95, max(0.05, base_success))
    
    def _trigger_treasure_trap(self, party: Party, dungeon_level: int) -> str:
        """宝箱のトラップ発動"""
        # 簡易的なトラップ処理
        trap_types = ["needle", "gas", "explosion", "curse"]
        trap_type = random.choice(trap_types)
        
        living_members = party.get_living_characters()
        if not living_members:
            return "トラップが発動したが対象がいない"
        
        target = random.choice(living_members)
        
        if trap_type == "needle":
            damage = random.randint(3, 8) + dungeon_level
            target.take_damage(damage)
            return f"毒針が飛び出し、{target.name}が{damage}ダメージを受けた！"
            
        elif trap_type == "gas":
            damage = random.randint(1, 4) + dungeon_level // 2
            target.take_damage(damage)
            target.add_status_effect("poison")
            return f"毒ガスが噴出し、{target.name}が{damage}ダメージを受け毒状態になった！"
            
        elif trap_type == "explosion":
            damage = random.randint(5, 12) + dungeon_level
            # 全員にダメージ
            for member in living_members:
                member.take_damage(damage // 2)
            return f"爆発が起こり、パーティ全員が{damage // 2}ダメージを受けた！"
            
        elif trap_type == "curse":
            target.add_status_effect("stat_drain_all")
            return f"呪いがかかり、{target.name}の全能力値が一時的に減少した！"
        
        return "不明なトラップが発動した"
    
    def _generate_treasure_contents(self, treasure_data: TreasureData, dungeon_level: int) -> Dict[str, Any]:
        """宝箱の内容物を生成"""
        contents = {"gold": 0, "items": []}
        
        # 金貨生成
        if treasure_data.gold_range[1] > 0:
            min_gold, max_gold = treasure_data.gold_range
            level_modifier = 1 + (dungeon_level - 1) * 0.2
            min_gold = int(min_gold * level_modifier)
            max_gold = int(max_gold * level_modifier)
            contents["gold"] = random.randint(min_gold, max_gold)
        
        # アイテム生成
        min_items, max_items = treasure_data.item_count_range
        item_count = random.randint(min_items, max_items)
        
        for _ in range(item_count):
            item = self._generate_random_item(treasure_data.rarity_weights, dungeon_level)
            if item:
                contents["items"].append(item)
        
        return contents
    
    def _generate_random_item(self, rarity_weights: Dict[ItemRarity, float], dungeon_level: int) -> Optional[Item]:
        """ランダムアイテムを生成"""
        # レアリティ決定
        rarities = list(rarity_weights.keys())
        weights = list(rarity_weights.values())
        rarity = random.choices(rarities, weights=weights)[0]
        
        # アイテムタイプ決定
        item_types = [ItemType.WEAPON, ItemType.ARMOR, ItemType.CONSUMABLE, ItemType.TREASURE]
        item_type = random.choice(item_types)
        
        # 基本アイテム生成（簡略版）
        item_names = {
            ItemType.WEAPON: {
                ItemRarity.COMMON: ["鉄の剣", "木の杖", "短剣"],
                ItemRarity.UNCOMMON: ["鋼の剣", "魔法の杖", "エルフの短剣"],
                ItemRarity.RARE: ["ミスリルの剣", "賢者の杖", "影の短剣"],
                ItemRarity.EPIC: ["ドラゴンスレイヤー", "大魔法使いの杖", "暗殺者の短剣"],
                ItemRarity.LEGENDARY: ["エクスカリバー", "創世の杖", "神速の短剣"]
            },
            ItemType.ARMOR: {
                ItemRarity.COMMON: ["革の鎧", "布の服", "鉄の兜"],
                ItemRarity.UNCOMMON: ["鎖かたびら", "法衣", "鋼の兜"],
                ItemRarity.RARE: ["プレートメイル", "魔法のローブ", "ミスリルの兜"],
                ItemRarity.EPIC: ["ドラゴンメイル", "大賢者のローブ", "王者の兜"],
                ItemRarity.LEGENDARY: ["神聖な鎧", "時の織り手のローブ", "不滅の兜"]
            },
            ItemType.CONSUMABLE: {
                ItemRarity.COMMON: ["回復ポーション", "MPポーション", "解毒剤"],
                ItemRarity.UNCOMMON: ["中回復ポーション", "中MPポーション", "万能薬"],
                ItemRarity.RARE: ["大回復ポーション", "賢者の薬", "蘇生の薬"],
                ItemRarity.EPIC: ["完全回復薬", "魔力回復薬", "不死の薬"],
                ItemRarity.LEGENDARY: ["神の恵み", "永遠の命薬", "全能の薬"]
            },
            ItemType.TREASURE: {
                ItemRarity.COMMON: ["銅貨", "ガラス玉", "古い本"],
                ItemRarity.UNCOMMON: ["銀貨", "綺麗な石", "魔法の本"],
                ItemRarity.RARE: ["金貨", "宝石", "古代の巻物"],
                ItemRarity.EPIC: ["プラチナ貨", "魔法の宝石", "失われた知識"],
                ItemRarity.LEGENDARY: ["ダイヤモンド", "伝説の宝石", "神の知識"]
            }
        }
        
        if item_type not in item_names or rarity not in item_names[item_type]:
            return None
        
        names = item_names[item_type][rarity]
        item_name = random.choice(names)
        
        # 基本的なアイテム作成
        item_id = f"treasure_{item_name.replace(' ', '_').lower()}_{random.randint(1000, 9999)}"
        item_data = {
            'names': {'ja': item_name},
            'descriptions': {'ja': f"宝箱から見つかった{item_name}"},
            'type': item_type.value,
            'rarity': rarity.value,
            'price': self._calculate_item_value(rarity, dungeon_level),
            'weight': 1
        }
        
        item = Item(item_id, item_data)
        
        return item
    
    def _calculate_item_value(self, rarity: ItemRarity, dungeon_level: int) -> int:
        """アイテム価値の計算"""
        base_values = {
            ItemRarity.COMMON: 10,
            ItemRarity.UNCOMMON: 50,
            ItemRarity.RARE: 200,
            ItemRarity.EPIC: 1000,
            ItemRarity.LEGENDARY: 5000
        }
        
        base_value = base_values.get(rarity, 10)
        level_modifier = 1 + (dungeon_level - 1) * 0.1
        
        return int(base_value * level_modifier)
    
    def is_treasure_opened(self, treasure_id: str) -> bool:
        """宝箱が開封済みかチェック"""
        return self.opened_treasures.get(treasure_id, False)
    
    def reset_treasure_state(self, treasure_id: str):
        """宝箱の状態をリセット（デバッグ用）"""
        if treasure_id in self.opened_treasures:
            del self.opened_treasures[treasure_id]


# グローバルインスタンス
treasure_system = TreasureSystem()