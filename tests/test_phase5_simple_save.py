"""Phase 5システムの簡単なセーブ・ロードテスト"""

import unittest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch

from src.core.save_manager import SaveManager
from src.character.party import Party
from src.character.character import Character
from src.character.stats import BaseStats, DerivedStats
from src.character.character import Experience


class TestPhase5SimpleSave(unittest.TestCase):
    """Phase 5システムの簡単なセーブ・ロードテスト"""
    
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.save_manager = SaveManager()
        self.party = self._create_simple_party()
    
    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def _create_simple_party(self) -> Party:
        """簡単なテスト用パーティ作成"""
        party = Party("SimpleTestParty")
        
        character = Character(
            name="TestHero",
            race="human",
            character_class="fighter",
            base_stats=BaseStats(strength=15, agility=12, intelligence=10, faith=8, luck=10),
            derived_stats=DerivedStats(max_hp=40, current_hp=40, max_mp=10, current_mp=10),
            experience=Experience(level=3)
        )
        
        party.add_character(character)
        party.gold = 200
        
        return party
    
    def test_basic_save_load_functionality(self):
        """基本的なセーブ・ロード機能テスト"""
        game_state = {
            "current_floor": 3,
            "test_data": "phase5_integration_test"
        }
        
        # セーブ実行
        with patch('src.utils.constants.SAVE_DIR', self.temp_dir):
            success = self.save_manager.save_game(
                party=self.party,
                slot_id=1,
                save_name="BasicTest",
                game_state=game_state
            )
            self.assertTrue(success, "セーブ処理が失敗しました")
            
            # ロード実行
            loaded_save = self.save_manager.load_game(1)
            self.assertIsNotNone(loaded_save, "ロード処理が失敗しました")
            
            # データ整合性確認
            self.assertEqual(loaded_save.party.name, "SimpleTestParty")
            self.assertEqual(loaded_save.party.gold, 200)
            self.assertEqual(loaded_save.game_state.get("current_floor"), 3)
            self.assertEqual(loaded_save.game_state.get("test_data"), "phase5_integration_test")
    
    def test_save_with_phase5_data(self):
        """Phase 5関連データのセーブ・ロード"""
        phase5_data = {
            "dungeon_level": 5,
            "trap_states": {"trap_1": "triggered", "trap_2": "detected"},
            "treasure_states": {"chest_1": "opened", "chest_2": "locked"},
            "boss_encounters": {"floor_boss": "defeated"},
            "character_effects": {"hero": ["poison", "haste"]}
        }
        
        with patch('src.utils.constants.SAVE_DIR', self.temp_dir):
            # セーブ
            success = self.save_manager.save_game(
                party=self.party,
                slot_id=2,
                save_name="Phase5Test",
                game_state=phase5_data
            )
            self.assertTrue(success)
            
            # ロード
            loaded_save = self.save_manager.load_game(2)
            self.assertIsNotNone(loaded_save)
            
            # Phase 5データ確認
            loaded_state = loaded_save.game_state
            self.assertEqual(loaded_state.get("dungeon_level"), 5)
            self.assertEqual(loaded_state.get("trap_states", {}).get("trap_1"), "triggered")
            self.assertEqual(loaded_state.get("treasure_states", {}).get("chest_1"), "opened")
            self.assertEqual(loaded_state.get("boss_encounters", {}).get("floor_boss"), "defeated")


if __name__ == '__main__':
    unittest.main()