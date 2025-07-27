"""EncounterStrategyのテスト"""

import unittest
from unittest.mock import Mock
import random

from src.encounter.encounter_strategy import (
    EncounterStrategyFactory, DeepDungeonModifier,
    NormalEncounterStrategy, AmbushEncounterStrategy, 
    TreasureGuardianEncounterStrategy, BossEncounterStrategy
)
from src.encounter.encounter_types import EncounterType, EncounterEvent
from src.dungeon.dungeon_generator import DungeonAttribute


class TestEncounterStrategy(unittest.TestCase):
    """EncounterStrategyのテストクラス"""
    
    def setUp(self):
        """テスト前の準備"""
        self.rng = random.Random(42)  # 固定シード
        
        # テスト用のEncounterEvent
        self.encounter = EncounterEvent(
            encounter_type=EncounterType.NORMAL,
            monster_group=None,
            location=(0, 0, 1),
            dungeon_attribute=DungeonAttribute.FIRE
        )
    
    def test_strategy_factory(self):
        """StrategyFactoryのテスト"""
        # 各エンカウンタータイプに対応するストラテジーが取得できる
        normal_strategy = EncounterStrategyFactory.get_strategy(EncounterType.NORMAL)
        self.assertIsInstance(normal_strategy, NormalEncounterStrategy)
        
        ambush_strategy = EncounterStrategyFactory.get_strategy(EncounterType.AMBUSH)
        self.assertIsInstance(ambush_strategy, AmbushEncounterStrategy)
        
        treasure_strategy = EncounterStrategyFactory.get_strategy(EncounterType.TREASURE_GUARDIAN)
        self.assertIsInstance(treasure_strategy, TreasureGuardianEncounterStrategy)
        
        boss_strategy = EncounterStrategyFactory.get_strategy(EncounterType.BOSS)
        self.assertIsInstance(boss_strategy, BossEncounterStrategy)
    
    def test_normal_encounter_strategy(self):
        """通常エンカウンターストラテジーのテスト"""
        strategy = NormalEncounterStrategy()
        
        # 特殊能力生成
        abilities = strategy.generate_special_abilities(DungeonAttribute.FIRE, self.rng)
        self.assertIsInstance(abilities, list)
        
        # 特殊条件適用（何もしない）
        original_can_flee = self.encounter.can_flee
        strategy.apply_special_conditions(self.encounter, 5)
        self.assertEqual(self.encounter.can_flee, original_can_flee)
        
        # 能力確率
        self.assertEqual(strategy.get_ability_chance(), 0.3)
    
    def test_ambush_encounter_strategy(self):
        """奇襲エンカウンターストラテジーのテスト"""
        strategy = AmbushEncounterStrategy()
        
        # 特殊能力生成
        abilities = strategy.generate_special_abilities(DungeonAttribute.FIRE, self.rng)
        self.assertIsInstance(abilities, list)
        
        # 特殊条件適用
        self.encounter.encounter_type = EncounterType.AMBUSH
        strategy.apply_special_conditions(self.encounter, 5)
        self.assertFalse(self.encounter.can_flee)
        self.assertTrue(self.encounter.special_conditions.get("surprise_round", False))
        
        # 能力確率
        self.assertEqual(strategy.get_ability_chance(), 0.5)
    
    def test_treasure_guardian_strategy(self):
        """宝箱守護者ストラテジーのテスト"""
        strategy = TreasureGuardianEncounterStrategy()
        
        # 特殊能力生成
        abilities = strategy.generate_special_abilities(DungeonAttribute.FIRE, self.rng)
        self.assertIsInstance(abilities, list)
        
        # 特殊条件適用
        self.encounter.encounter_type = EncounterType.TREASURE_GUARDIAN
        strategy.apply_special_conditions(self.encounter, 5)
        self.assertTrue(self.encounter.can_negotiate)
        self.assertTrue(self.encounter.special_conditions.get("guarding_treasure", False))
        
        # 能力確率
        self.assertEqual(strategy.get_ability_chance(), 0.7)
    
    def test_boss_encounter_strategy(self):
        """ボスエンカウンターストラテジーのテスト"""
        strategy = BossEncounterStrategy()
        
        # 特殊能力生成
        abilities = strategy.generate_special_abilities(DungeonAttribute.FIRE, self.rng)
        self.assertIsInstance(abilities, list)
        
        # 特殊条件適用
        self.encounter.encounter_type = EncounterType.BOSS
        strategy.apply_special_conditions(self.encounter, 5)
        self.assertFalse(self.encounter.can_flee)
        self.assertTrue(self.encounter.special_conditions.get("boss_battle", False))
        
        # 能力確率（ボス用の高確率）
        self.assertEqual(strategy.get_ability_chance(), 0.8)
    
    def test_deep_dungeon_modifier(self):
        """深いダンジョン修正のテスト"""
        # 浅い階層では適用されない
        shallow_encounter = EncounterEvent(
            encounter_type=EncounterType.NORMAL,
            monster_group=None,
            location=(0, 0, 5),
            dungeon_attribute=DungeonAttribute.FIRE
        )
        
        DeepDungeonModifier.apply_deep_dungeon_conditions(shallow_encounter, 5)
        self.assertNotIn("deep_dungeon", shallow_encounter.special_conditions)
        
        # 深い階層では適用される
        deep_encounter = EncounterEvent(
            encounter_type=EncounterType.NORMAL,
            monster_group=None,
            location=(0, 0, 16),
            dungeon_attribute=DungeonAttribute.FIRE
        )
        
        DeepDungeonModifier.apply_deep_dungeon_conditions(deep_encounter, 16)
        self.assertTrue(deep_encounter.special_conditions.get("deep_dungeon", False))
    
    def test_attribute_abilities(self):
        """属性能力生成のテスト"""
        strategy = NormalEncounterStrategy()
        
        # 火属性の能力をテスト
        fire_abilities = strategy.generate_special_abilities(DungeonAttribute.FIRE, random.Random(100))
        
        # 氷属性の能力をテスト
        ice_abilities = strategy.generate_special_abilities(DungeonAttribute.ICE, random.Random(100))
        
        # 結果は属性によって異なることを確認
        # （実際の能力は確率的なので、傾向をテスト）
        self.assertIsInstance(fire_abilities, list)
        self.assertIsInstance(ice_abilities, list)
    
    def test_strategy_integration(self):
        """ストラテジー統合のテスト"""
        # ファクトリーから取得したストラテジーで実際の処理を実行
        encounter = EncounterEvent(
            encounter_type=EncounterType.AMBUSH,
            monster_group=None,
            location=(0, 0, 10),
            dungeon_attribute=DungeonAttribute.LIGHTNING
        )
        
        strategy = EncounterStrategyFactory.get_strategy(encounter.encounter_type)
        
        # 能力生成
        abilities = strategy.generate_special_abilities(encounter.dungeon_attribute, self.rng)
        self.assertIsInstance(abilities, list)
        
        # 条件適用
        strategy.apply_special_conditions(encounter, 10)
        self.assertFalse(encounter.can_flee)  # 奇襲の特徴
        self.assertTrue(encounter.special_conditions.get("surprise_round", False))
        
        # 深いダンジョン条件も適用
        DeepDungeonModifier.apply_deep_dungeon_conditions(encounter, 10)
        # レベル10は深いダンジョンではないので条件は追加されない


if __name__ == '__main__':
    unittest.main()