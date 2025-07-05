"""Phase 5システムのセーブ・ロード統合テスト"""

import unittest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch, MagicMock

from src.core.save_manager import SaveManager, GameSave, SaveSlot
from src.character.party import Party
from src.character.character import Character, CharacterStatus
from src.character.stats import BaseStats, DerivedStats
from src.character.character import Experience
from src.dungeon.trap_system import TrapSystem
from src.dungeon.treasure_system import TreasureSystem
from src.dungeon.boss_system import BossSystem


class TestPhase5SaveIntegration(unittest.TestCase):
    """Phase 5システムのセーブ・ロード統合テスト"""
    
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.save_manager = SaveManager()
        
        # テスト用パーティ作成
        self.party = self._create_test_party()
        
        # Phase 5システムインスタンス
        self.trap_sys = TrapSystem()
        self.treasure_sys = TreasureSystem()
        self.boss_sys = BossSystem()
    
    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def _create_test_party(self) -> Party:
        """テスト用パーティ作成"""
        party = Party("SaveTestParty")
        
        character = Character(
            name="SaveTestChar",
            race="human",
            character_class="fighter",
            base_stats=BaseStats(strength=16, agility=12, intelligence=10, faith=8, luck=10),
            derived_stats=DerivedStats(max_hp=40, current_hp=35, max_mp=15, current_mp=15),
            experience=Experience(level=5)
        )
        
        party.add_character(character)
        party.gold = 500
        
        return party
    
    def test_trap_state_save_load(self):
        """トラップ状態のセーブ・ロード"""
        # 宝箱を開封して状態を変更
        treasure_id = "save_test_treasure_1"
        result = self.treasure_sys.open_treasure(
            treasure_id, self.treasure_sys.generate_treasure_type(5), 
            self.party, 5
        )
        
        # 開封状態を確認
        if result["success"]:
            self.assertTrue(self.treasure_sys.is_treasure_opened(treasure_id))
        
        # 開封状態を強制設定（テスト用）
        self.treasure_sys.opened_treasures[treasure_id] = True
        
        # セーブデータ作成
        save_slot = SaveSlot(
            slot_id=1,
            name="TrapSaveTest",
            party_name=self.party.name,
            total_playtime=100.0,
            location="dungeon_level_5"
        )
        
        game_save = GameSave(
            save_slot=save_slot,
            party=self.party,
            game_state={
                "opened_treasures": self.treasure_sys.opened_treasures.copy()
            }
        )
        
        # セーブ実行
        with patch('src.utils.constants.SAVE_DIR', self.temp_dir):
            success = self.save_manager.save_game(
                party=self.party,
                slot_id=1, 
                save_name="TrapSaveTest",
                game_state={"opened_treasures": self.treasure_sys.opened_treasures.copy()}
            )
            self.assertTrue(success)
            
            # ロード実行
            loaded_save = self.save_manager.load_game(1)
            self.assertIsNotNone(loaded_save)
            
            # 開封状態が復元されているかチェック
            opened_treasures = loaded_save.game_state.get("opened_treasures", {})
            self.assertTrue(opened_treasures.get(treasure_id, False))
    
    def test_boss_encounter_save_load(self):
        """ボス戦状態のセーブ・ロード"""
        # ボス戦開始
        encounter = self.boss_sys.create_boss_encounter("skeleton_king", 5, "save_test_boss")
        self.assertIsNotNone(encounter)
        
        boss_monster = encounter.initialize_boss_monster()
        
        # ボスにダメージを与えて状態変更
        initial_hp = boss_monster.current_hp
        boss_monster.current_hp = initial_hp // 2  # HPを半分に
        
        # フェーズ移行チェック
        new_phase = encounter.check_phase_transition()
        
        # セーブデータ作成
        save_slot = SaveSlot(
            slot_id=2,
            name="BossSaveTest",
            party_name=self.party.name,
            total_playtime=150.0,
            location="boss_floor"
        )
        
        game_save = GameSave(
            save_slot=save_slot,
            party=self.party,
            game_state={
                "active_boss_encounters": {
                    "save_test_boss": {
                        "boss_id": "skeleton_king",
                        "dungeon_level": 5,
                        "current_phase": encounter.current_phase.value,
                        "boss_current_hp": boss_monster.current_hp,
                        "boss_max_hp": boss_monster.max_hp,
                        "turn_count": encounter.turn_count
                    }
                }
            }
        )
        
        # セーブ・ロード実行
        with patch('src.utils.constants.SAVE_DIR', self.temp_dir):
            success = self.save_manager.save_game(2, "BossSaveTest", game_save)
            self.assertTrue(success)
            
            loaded_save = self.save_manager.load_game(2)
            self.assertIsNotNone(loaded_save)
            
            # ボス戦状態が復元されているかチェック
            boss_data = loaded_save.game_state.get("active_boss_encounters", {}).get("save_test_boss")
            self.assertIsNotNone(boss_data)
            self.assertEqual(boss_data["boss_id"], "skeleton_king")
            self.assertEqual(boss_data["current_phase"], encounter.current_phase.value)
            self.assertEqual(boss_data["boss_current_hp"], boss_monster.current_hp)
    
    def test_character_status_effects_save_load(self):
        """キャラクターの状態異常セーブ・ロード"""
        character = list(self.party.characters.values())[0]
        
        # 状態異常を付与
        character.add_status_effect("poison")
        
        # セーブデータ作成
        save_slot = SaveSlot(
            slot_id=3,
            name="StatusSaveTest",
            party_name=self.party.name,
            total_playtime=75.0,
            location="dungeon_level_3"
        )
        
        game_save = GameSave(
            save_slot=save_slot,
            party=self.party,
            game_state={}
        )
        
        # セーブ・ロード実行
        with patch('src.utils.constants.SAVE_DIR', self.temp_dir):
            success = self.save_manager.save_game(3, "StatusSaveTest", game_save)
            self.assertTrue(success)
            
            loaded_save = self.save_manager.load_game(3)
            self.assertIsNotNone(loaded_save)
            
            # パーティとキャラクターが復元されているかチェック
            self.assertEqual(loaded_save.party.name, "SaveTestParty")
            self.assertEqual(len(loaded_save.party.characters), 1)
            
            # キャラクターの基本情報確認
            loaded_char = list(loaded_save.party.characters.values())[0]
            self.assertEqual(loaded_char.name, "SaveTestChar")
            self.assertEqual(loaded_char.character_class, "fighter")
    
    def test_dungeon_progress_save_load(self):
        """ダンジョン進行状況のセーブ・ロード"""
        # ダンジョン進行状況データ
        dungeon_state = {
            "current_floor": 5,
            "visited_cells": [(0, 0), (1, 0), (1, 1)],
            "discovered_secrets": ["secret_passage_1", "hidden_treasure_2"],
            "defeated_monsters": 25,
            "total_encounters": 30
        }
        
        # セーブデータ作成
        save_slot = SaveSlot(
            slot_id=4,
            name="DungeonProgressTest",
            party_name=self.party.name,
            total_playtime=200.0,
            location="dungeon_level_5"
        )
        
        game_save = GameSave(
            save_slot=save_slot,
            party=self.party,
            game_state={
                "dungeon_progress": dungeon_state,
                "party_stats": {
                    "total_gold_earned": 1500,
                    "treasures_found": 12,
                    "traps_triggered": 8,
                    "bosses_defeated": 1
                }
            }
        )
        
        # セーブ・ロード実行
        with patch('src.utils.constants.SAVE_DIR', self.temp_dir):
            success = self.save_manager.save_game(4, "DungeonProgressTest", game_save)
            self.assertTrue(success)
            
            loaded_save = self.save_manager.load_game(4)
            self.assertIsNotNone(loaded_save)
            
            # ダンジョン進行状況が復元されているかチェック
            loaded_dungeon = loaded_save.game_state.get("dungeon_progress", {})
            self.assertEqual(loaded_dungeon.get("current_floor"), 5)
            self.assertEqual(len(loaded_dungeon.get("visited_cells", [])), 3)
            self.assertEqual(len(loaded_dungeon.get("discovered_secrets", [])), 2)
            
            # パーティ統計情報確認
            party_stats = loaded_save.game_state.get("party_stats", {})
            self.assertEqual(party_stats.get("total_gold_earned"), 1500)
            self.assertEqual(party_stats.get("treasures_found"), 12)
    
    def test_equipment_and_inventory_save_load(self):
        """装備・インベントリのセーブ・ロード"""
        character = list(self.party.characters.values())[0]
        
        # 装備・インベントリ状態をシミュレート
        equipment_state = {
            "weapon": "iron_sword",
            "armor": "leather_armor",
            "accessory": "power_ring"
        }
        
        inventory_state = [
            {"item_id": "healing_potion", "quantity": 5},
            {"item_id": "mana_potion", "quantity": 3},
            {"item_id": "antidote", "quantity": 2}
        ]
        
        # セーブデータ作成
        save_slot = SaveSlot(
            slot_id=5,
            name="EquipmentSaveTest",
            party_name=self.party.name,
            total_playtime=125.0,
            location="town_inn"
        )
        
        game_save = GameSave(
            save_slot=save_slot,
            party=self.party,
            game_state={
                "character_equipment": {
                    character.character_id: equipment_state
                },
                "party_inventory": inventory_state
            }
        )
        
        # セーブ・ロード実行
        with patch('src.utils.constants.SAVE_DIR', self.temp_dir):
            success = self.save_manager.save_game(5, "EquipmentSaveTest", game_save)
            self.assertTrue(success)
            
            loaded_save = self.save_manager.load_game(5)
            self.assertIsNotNone(loaded_save)
            
            # 装備状態が復元されているかチェック
            char_equipment = loaded_save.game_state.get("character_equipment", {})
            loaded_char = list(loaded_save.party.characters.values())[0]
            char_eq = char_equipment.get(loaded_char.character_id, {})
            
            self.assertEqual(char_eq.get("weapon"), "iron_sword")
            self.assertEqual(char_eq.get("armor"), "leather_armor")
            
            # インベントリ状態確認
            inventory = loaded_save.game_state.get("party_inventory", [])
            self.assertEqual(len(inventory), 3)
            
            # ポーション類が正しく保存されているかチェック
            healing_potions = next((item for item in inventory if item["item_id"] == "healing_potion"), None)
            self.assertIsNotNone(healing_potions)
            self.assertEqual(healing_potions["quantity"], 5)
    
    def test_save_corruption_recovery(self):
        """セーブデータ破損からの復旧テスト"""
        # 正常なセーブ作成
        save_slot = SaveSlot(
            slot_id=6,
            name="CorruptionTest",
            party_name=self.party.name,
            total_playtime=50.0,
            location="overworld"
        )
        
        game_save = GameSave(
            save_slot=save_slot,
            party=self.party,
            game_state={}
        )
        
        with patch('src.utils.constants.SAVE_DIR', self.temp_dir):
            success = self.save_manager.save_game(6, "CorruptionTest", game_save)
            self.assertTrue(success)
            
            # セーブファイルを意図的に破損
            save_file = Path(self.temp_dir) / "save_06.json"
            if save_file.exists():
                with open(save_file, 'w') as f:
                    f.write("invalid json content")
            
            # ロード試行（失敗するはず）
            loaded_save = self.save_manager.load_game(6)
            self.assertIsNone(loaded_save, "破損したセーブデータの読み込みが失敗していない")
    
    def test_large_save_performance(self):
        """大きなセーブデータの性能テスト"""
        # 大量のデータを含むゲーム状態作成
        large_game_state = {
            "opened_treasures": {f"treasure_{i}": True for i in range(1000)},
            "defeated_monsters": [f"monster_{i}" for i in range(500)],
            "discovered_locations": [f"location_{i}" for i in range(200)],
            "completed_quests": {f"quest_{i}": {"completed": True, "reward_claimed": True} for i in range(100)}
        }
        
        save_slot = SaveSlot(
            slot_id=7,
            name="LargeDataTest",
            party_name=self.party.name,
            total_playtime=1000.0,
            location="deep_dungeon"
        )
        
        game_save = GameSave(
            save_slot=save_slot,
            party=self.party,
            game_state=large_game_state
        )
        
        # セーブ・ロード性能測定
        import time
        
        with patch('src.utils.constants.SAVE_DIR', self.temp_dir):
            # セーブ時間測定
            start_time = time.time()
            success = self.save_manager.save_game(7, "LargeDataTest", game_save)
            save_time = time.time() - start_time
            
            self.assertTrue(success)
            self.assertLess(save_time, 5.0, "セーブ処理に5秒以上かかっています")
            
            # ロード時間測定
            start_time = time.time()
            loaded_save = self.save_manager.load_game(7)
            load_time = time.time() - start_time
            
            self.assertIsNotNone(loaded_save)
            self.assertLess(load_time, 5.0, "ロード処理に5秒以上かかっています")
            
            # データ整合性確認
            loaded_state = loaded_save.game_state
            self.assertEqual(len(loaded_state.get("opened_treasures", {})), 1000)
            self.assertEqual(len(loaded_state.get("defeated_monsters", [])), 500)


if __name__ == '__main__':
    unittest.main()