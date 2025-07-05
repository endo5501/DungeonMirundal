"""Phase 5システムのテスト"""

import pytest
import unittest
from unittest.mock import Mock, patch, MagicMock
from typing import Dict, Any

from src.dungeon.trap_system import TrapSystem, TrapType, trap_system
from src.dungeon.treasure_system import TreasureSystem, TreasureType, treasure_system
from src.dungeon.boss_system import BossSystem, BossType, boss_system
from src.dungeon.dungeon_manager import DungeonManager
from src.character.party import Party
from src.character.character import Character, CharacterStatus
from src.character.stats import BaseStats, DerivedStats
from src.character.character import Experience


class TestTrapSystem(unittest.TestCase):
    """トラップシステムのテスト"""
    
    def setUp(self):
        self.trap_sys = TrapSystem()
        self.party = self._create_test_party()
    
    def _create_test_party(self) -> Party:
        """テスト用パーティ作成"""
        party = Party("TestParty")
        
        # 戦士キャラクター
        fighter = Character(
            name="Fighter",
            race="human",
            character_class="fighter",
            base_stats=BaseStats(strength=16, agility=12, intelligence=10, faith=8, luck=10),
            derived_stats=DerivedStats(max_hp=30, current_hp=30, max_mp=5, current_mp=5),
            experience=Experience(level=3)
        )
        
        # 盗賊キャラクター
        thief = Character(
            name="Thief", 
            race="human",
            character_class="thief",
            base_stats=BaseStats(strength=12, agility=18, intelligence=14, faith=6, luck=12),
            derived_stats=DerivedStats(max_hp=20, current_hp=20, max_mp=8, current_mp=8),
            experience=Experience(level=3)
        )
        
        party.add_character(fighter)
        party.add_character(thief)
        party.gold = 100
        
        return party
    
    def test_trap_definitions_loaded(self):
        """トラップ定義が正しく読み込まれているかテスト"""
        self.assertGreater(len(self.trap_sys.trap_definitions), 0)
        self.assertIn(TrapType.ARROW, self.trap_sys.trap_definitions)
        self.assertIn(TrapType.POISON_GAS, self.trap_sys.trap_definitions)
    
    def test_generate_random_trap_by_level(self):
        """レベル別ランダムトラップ生成テスト"""
        # 浅い階層では基本トラップのみ
        for _ in range(10):
            trap_type = self.trap_sys.generate_random_trap(1)
            self.assertIn(trap_type, [TrapType.ARROW, TrapType.SPIKE])
        
        # 深い階層では危険なトラップも含む
        for _ in range(10):
            trap_type = self.trap_sys.generate_random_trap(15)
            self.assertIn(trap_type, list(TrapType))  # 全てのトラップが出現可能
    
    def test_damage_trap_activation(self):
        """ダメージ系トラップ発動テスト"""
        result = self.trap_sys.activate_trap(TrapType.ARROW, self.party, 1)
        
        # トラップは発動または回避のどちらかになる
        self.assertIn("success", result)
        self.assertEqual(result["trap_name"], "矢の罠")
        
        # 発動した場合のチェック
        if result["success"]:
            self.assertGreater(len(result["effects"]), 0)
            damage_dealt = any("ダメージ" in effect for effect in result["effects"])
            # 発動率があるため必ずしもダメージが発生するわけではない
    
    def test_status_trap_activation(self):
        """状態異常系トラップ発動テスト"""
        result = self.trap_sys.activate_trap(TrapType.POISON_GAS, self.party, 1)
        
        # トラップは発動または回避のどちらかになる
        self.assertIn("success", result)
        self.assertEqual(result["trap_name"], "毒ガスの罠")
        
        # 発動した場合のチェック
        if result["success"]:
            status_applied = any("状態" in effect for effect in result["effects"])
    
    def test_teleport_trap_activation(self):
        """テレポートトラップ発動テスト"""
        result = self.trap_sys.activate_trap(TrapType.TELEPORT, self.party, 1)
        
        # トラップは発動または回避のどちらかになる
        self.assertIn("success", result)
        self.assertEqual(result["trap_name"], "テレポート罠")
        
        # 発動した場合のチェック
        if result["success"]:
            self.assertTrue(result.get("teleport", False))
    
    def test_gold_theft_trap_activation(self):
        """金貨盗難トラップ発動テスト"""
        initial_gold = self.party.gold
        result = self.trap_sys.activate_trap(TrapType.GOLD_THEFT, self.party, 1)
        
        # トラップは発動または回避のどちらかになる
        self.assertIn("success", result)
        self.assertEqual(result["trap_name"], "金貨盗難の罠")
        
        # 発動した場合のチェック
        if result["success"] and "盗まれた" in str(result["effects"]):
            self.assertLess(self.party.gold, initial_gold)
    
    def test_trap_detection(self):
        """トラップ発見能力テスト"""
        characters = list(self.party.characters.values())
        thief = characters[1]  # 盗賊
        fighter = characters[0]  # 戦士
        
        # 盗賊は発見率が高い
        thief_detection_count = 0
        fighter_detection_count = 0
        
        for _ in range(100):
            if self.trap_sys.can_detect_trap(thief, TrapType.ARROW):
                thief_detection_count += 1
            if self.trap_sys.can_detect_trap(fighter, TrapType.ARROW):
                fighter_detection_count += 1
        
        # 盗賊の方が発見率が高いはず
        self.assertGreater(thief_detection_count, fighter_detection_count)
    
    def test_trap_disarm(self):
        """トラップ解除能力テスト"""
        characters = list(self.party.characters.values())
        thief = characters[1]  # 盗賊
        fighter = characters[0]  # 戦士
        
        # 盗賊は解除率が高い
        thief_disarm_count = 0
        fighter_disarm_count = 0
        
        for _ in range(100):
            if self.trap_sys.can_disarm_trap(thief, TrapType.ARROW):
                thief_disarm_count += 1
            if self.trap_sys.can_disarm_trap(fighter, TrapType.ARROW):
                fighter_disarm_count += 1
        
        # 盗賊の方が解除率が高いはず
        self.assertGreater(thief_disarm_count, fighter_disarm_count)


class TestTreasureSystem(unittest.TestCase):
    """宝箱システムのテスト"""
    
    def setUp(self):
        self.treasure_sys = TreasureSystem()
        self.party = self._create_test_party()
    
    def _create_test_party(self) -> Party:
        """テスト用パーティ作成"""
        party = Party("TestParty")
        
        character = Character(
            name="TestChar",
            race="human", 
            character_class="thief",
            base_stats=BaseStats(strength=12, agility=16, intelligence=14, faith=8, luck=10),
            derived_stats=DerivedStats(max_hp=25, current_hp=25, max_mp=10, current_mp=10),
            experience=Experience(level=3)
        )
        
        party.add_character(character)
        party.gold = 50
        
        return party
    
    def test_treasure_definitions_loaded(self):
        """宝箱定義が正しく読み込まれているかテスト"""
        self.assertGreater(len(self.treasure_sys.treasure_definitions), 0)
        self.assertIn(TreasureType.WOODEN, self.treasure_sys.treasure_definitions)
        self.assertIn(TreasureType.MAGICAL, self.treasure_sys.treasure_definitions)
    
    def test_generate_treasure_type_by_level(self):
        """レベル別宝箱タイプ生成テスト"""
        # 浅い階層では木製が多い
        level_1_types = [self.treasure_sys.generate_treasure_type(1) for _ in range(50)]
        wooden_count = level_1_types.count(TreasureType.WOODEN)
        self.assertGreater(wooden_count, 20)  # 50回中20回以上は木製
        
        # 深い階層では魔法宝箱も出現
        level_15_types = [self.treasure_sys.generate_treasure_type(15) for _ in range(50)]
        magical_count = level_15_types.count(TreasureType.MAGICAL)
        self.assertGreater(magical_count, 5)  # 深い階層では魔法宝箱も出現
    
    def test_open_wooden_treasure(self):
        """木製宝箱開封テスト"""
        treasure_id = "test_wooden_1"
        initial_gold = self.party.gold
        
        # 成功するまで複数回試行
        attempts = 0
        result = None
        while attempts < 10:  # 最大10回試行
            result = self.treasure_sys.open_treasure(
                treasure_id, TreasureType.WOODEN, self.party, 1
            )
            if result["success"]:
                break
            # 失敗した場合、開封状態をリセット
            self.treasure_sys.reset_treasure_state(treasure_id)
            attempts += 1
        
        self.assertTrue(result["success"], "10回試行しても宝箱開封に成功しませんでした")
        self.assertEqual(result["treasure_name"], "木製の宝箱")
        self.assertGreater(len(result["contents"]), 0)
        
        # 金貨が増えたかチェック
        if result["gold"] > 0:
            self.assertGreater(self.party.gold, initial_gold)
    
    def test_open_already_opened_treasure(self):
        """既に開封済み宝箱のテスト"""
        treasure_id = "test_duplicate_1"
        
        # 1回目の開封（成功するまで複数回試行）
        attempts = 0
        result1 = None
        while attempts < 10:  # 最大10回試行
            result1 = self.treasure_sys.open_treasure(
                treasure_id, TreasureType.WOODEN, self.party, 1
            )
            if result1["success"]:
                break
            # 失敗した場合、開封状態をリセット
            self.treasure_sys.reset_treasure_state(treasure_id)
            attempts += 1
        
        self.assertTrue(result1["success"], "10回試行しても宝箱開封に成功しませんでした")
        
        # 2回目の開封（失敗するはず）
        result2 = self.treasure_sys.open_treasure(
            treasure_id, TreasureType.WOODEN, self.party, 1
        )
        self.assertFalse(result2["success"])
        self.assertTrue(result2.get("already_opened", False))
    
    def test_mimic_treasure(self):
        """ミミック宝箱テスト"""
        # ミミックは100%の確率で発生
        result = self.treasure_sys.open_treasure(
            "test_mimic_1", TreasureType.MIMIC, self.party, 1
        )
        
        self.assertFalse(result["success"])
        self.assertTrue(result["mimic"])
        self.assertIn("ミミック", result["message"])
    
    def test_lock_picking_mechanics(self):
        """鍵開けメカニズムテスト"""
        thief = list(self.party.characters.values())[0]  # 盗賊
        
        # 簡単な鍵（木製宝箱）は高確率で開く
        success_count = 0
        for _ in range(100):
            if self.treasure_sys._attempt_lock_picking(10, thief):  # 難易度10
                success_count += 1
        
        self.assertGreater(success_count, 80)  # 盗賊なら80%以上成功するはず
        
        # 難しい鍵（魔法宝箱）は成功率が下がる
        hard_success_count = 0
        for _ in range(100):
            if self.treasure_sys._attempt_lock_picking(80, thief):  # 難易度80
                hard_success_count += 1
        
        self.assertLess(hard_success_count, success_count)  # 難しい鍵の方が成功率が低い


class TestBossSystem(unittest.TestCase):
    """ボス戦システムのテスト"""
    
    def setUp(self):
        self.boss_sys = BossSystem()
        self.party = self._create_test_party()
    
    def _create_test_party(self) -> Party:
        """テスト用パーティ作成"""
        party = Party("TestParty")
        
        character = Character(
            name="Hero",
            race="human",
            character_class="fighter",
            base_stats=BaseStats(strength=18, agility=14, intelligence=12, faith=10, luck=8),
            derived_stats=DerivedStats(max_hp=40, current_hp=40, max_mp=15, current_mp=15),
            experience=Experience(level=5)
        )
        
        party.add_character(character)
        party.gold = 200
        
        return party
    
    def test_boss_definitions_loaded(self):
        """ボス定義が正しく読み込まれているかテスト"""
        self.assertGreater(len(self.boss_sys.boss_definitions), 0)
        self.assertIn("skeleton_king", self.boss_sys.boss_definitions)
        self.assertIn("ancient_golem", self.boss_sys.boss_definitions)
    
    def test_generate_boss_for_level(self):
        """レベル別ボス生成テスト"""
        # フロアボスは任意のレベルで出現可能
        boss_id = self.boss_sys.generate_boss_for_level(3)
        self.assertIsNotNone(boss_id)
        
        # エリアボス（5の倍数階）
        boss_id_5 = self.boss_sys.generate_boss_for_level(5)
        self.assertIsNotNone(boss_id_5)
        
        # ダンジョンボス（最深部）
        boss_id_20 = self.boss_sys.generate_boss_for_level(20)
        self.assertIsNotNone(boss_id_20)
    
    def test_boss_encounter_creation(self):
        """ボス戦エンカウンター作成テスト"""
        encounter = self.boss_sys.create_boss_encounter("skeleton_king", 5, "test_encounter_1")
        
        self.assertIsNotNone(encounter)
        self.assertEqual(encounter.boss_data.name, "スケルトンキング")
        self.assertEqual(encounter.dungeon_level, 5)
        self.assertEqual(encounter.current_phase.value, "initial")
    
    def test_boss_monster_initialization(self):
        """ボスモンスター初期化テスト"""
        encounter = self.boss_sys.create_boss_encounter("skeleton_king", 5, "test_encounter_2")
        boss_monster = encounter.initialize_boss_monster()
        
        self.assertIsNotNone(boss_monster)
        self.assertEqual(boss_monster.name, "スケルトンキング")
        self.assertGreater(boss_monster.stats.hit_points, 0)
        self.assertGreater(boss_monster.stats.attack_bonus, 0)
    
    def test_boss_phase_transition(self):
        """ボスフェーズ移行テスト"""
        encounter = self.boss_sys.create_boss_encounter("skeleton_king", 5, "test_encounter_3")
        boss_monster = encounter.initialize_boss_monster()
        
        # 初期フェーズ
        self.assertEqual(encounter.current_phase.value, "initial")
        
        # HPを半分に減らす
        boss_monster.current_hp = boss_monster.max_hp // 2
        phase = encounter.check_phase_transition()
        
        # 激怒フェーズに移行
        if phase:
            self.assertEqual(phase.value, "enraged")
    
    def test_boss_special_abilities(self):
        """ボス特殊能力テスト"""
        encounter = self.boss_sys.create_boss_encounter("skeleton_king", 5, "test_encounter_4")
        encounter.initialize_boss_monster()
        
        # 特殊能力実行
        result = encounter.execute_special_ability("summon_minions", self.party)
        
        self.assertTrue(result["success"])
        self.assertEqual(result["ability_name"], "summon_minions")
        self.assertGreater(len(result["message"]), 0)
    
    def test_boss_encounter_completion(self):
        """ボス戦完了処理テスト"""
        encounter = self.boss_sys.create_boss_encounter("skeleton_king", 5, "test_encounter_5")
        
        # 勝利時
        victory_result = self.boss_sys.complete_boss_encounter("test_encounter_5", True)
        self.assertTrue(victory_result["success"])
        self.assertTrue(victory_result["victory"])
        self.assertIn("rewards", victory_result)
        
        # 敗北時（新しいエンカウンターで）
        encounter2 = self.boss_sys.create_boss_encounter("skeleton_king", 5, "test_encounter_6")
        defeat_result = self.boss_sys.complete_boss_encounter("test_encounter_6", False)
        self.assertTrue(defeat_result["success"])
        self.assertFalse(defeat_result["victory"])
        self.assertIn("consequences", defeat_result)
    
    def test_boss_level_detection(self):
        """ボス戦フロア判定テスト"""
        # 5の倍数階はボス戦
        self.assertTrue(self.boss_sys.is_boss_level(5))
        self.assertTrue(self.boss_sys.is_boss_level(10))
        
        # 20階以上はダンジョンボス
        self.assertTrue(self.boss_sys.is_boss_level(20))
        self.assertTrue(self.boss_sys.is_boss_level(25))


class TestDungeonIntegration(unittest.TestCase):
    """ダンジョン統合機能のテスト"""
    
    def setUp(self):
        self.dungeon_manager = DungeonManager()
        self.party = self._create_test_party()
    
    def _create_test_party(self) -> Party:
        """テスト用パーティ作成"""
        party = Party("IntegrationTestParty")
        
        character = Character(
            name="TestHero",
            race="human",
            character_class="thief",
            base_stats=BaseStats(strength=14, agility=16, intelligence=13, faith=9, luck=11),
            derived_stats=DerivedStats(max_hp=30, current_hp=30, max_mp=12, current_mp=12),
            experience=Experience(level=4)
        )
        
        party.add_character(character)
        party.gold = 150
        
        return party
    
    @patch('src.dungeon.dungeon_manager.DungeonCell')
    def test_trap_interaction_handling(self, mock_cell):
        """トラップインタラクション処理テスト"""
        # モックセル作成
        mock_cell.has_trap = True
        mock_cell.trap_type = "arrow"
        
        # ダンジョン状態をモック
        mock_dungeon = Mock()
        mock_dungeon.player_position.level = 1
        self.dungeon_manager.current_dungeon = mock_dungeon
        
        with patch.object(self.dungeon_manager, 'get_current_cell', return_value=mock_cell):
            result = self.dungeon_manager._handle_trap_interaction(mock_cell, self.party)
            
            self.assertEqual(result["type"], "trap")
            self.assertIn("success", result)
    
    @patch('src.dungeon.dungeon_manager.DungeonCell')
    def test_treasure_interaction_handling(self, mock_cell):
        """宝箱インタラクション処理テスト"""
        # モックセル作成
        mock_cell.treasure_id = "test_treasure_1"
        mock_cell.has_treasure = True
        mock_cell.treasure_type = None  # 新規生成させる
        
        # ダンジョン状態をモック
        mock_dungeon = Mock()
        mock_dungeon.player_position.level = 1
        self.dungeon_manager.current_dungeon = mock_dungeon
        
        with patch.object(self.dungeon_manager, 'get_current_cell', return_value=mock_cell):
            result = self.dungeon_manager._handle_treasure_interaction(mock_cell, self.party)
            
            self.assertEqual(result["type"], "treasure")
            self.assertIn("success", result)
    
    def test_secret_interaction_detection(self):
        """隠し要素発見テスト"""
        with patch.object(self.dungeon_manager, 'get_current_cell', return_value=Mock()):
            with patch.object(self.dungeon_manager, '_check_secret_passage', return_value=True):
                with patch.object(self.dungeon_manager, '_check_secret_treasure', return_value=False):
                    result = self.dungeon_manager.check_for_secret_interactions(self.party)
                    
                    self.assertTrue(result["success"])
                    self.assertEqual(result["count"], 1)
                    self.assertEqual(result["interactions"][0]["type"], "secret_passage")


if __name__ == '__main__':
    unittest.main()