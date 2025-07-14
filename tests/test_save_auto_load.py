"""自動セーブデータロード機能のテスト"""

import unittest
import tempfile
import os
import time

from src.core.save_manager import SaveManager
from src.character.party import Party


class TestAutoLoadFeature(unittest.TestCase):
    """自動ロード機能のテストクラス"""
    
    def setUp(self):
        """テスト前のセットアップ"""
        self.temp_dir = tempfile.mkdtemp()
        self.save_manager = SaveManager(self.temp_dir)
    
    def tearDown(self):
        """テスト後のクリーンアップ"""
        import shutil
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    def _create_test_party(self, name: str) -> Party:
        """テスト用パーティを作成"""
        party = Party()
        party.name = name
        party.gold = 1000
        return party
    
    def test_save_manager_get_latest_save(self):
        """SaveManagerの最新セーブ取得テスト"""
        # セーブデータを作成
        party = self._create_test_party("TEST_PARTY")
        game_state = {"location": "overworld"}
        
        self.save_manager.save_game(party, 1, "TEST_PARTY", game_state)
        
        # 最新セーブ取得
        slots = self.save_manager.get_save_slots()
        self.assertEqual(len(slots), 1)
        self.assertEqual(slots[0].name, "TEST_PARTY")
    
    def test_save_manager_multiple_saves(self):
        """複数セーブからの最新取得テスト"""
        # 複数のセーブを作成
        party1 = self._create_test_party("PARTY_1")
        game_state1 = {"location": "overworld"}
        self.save_manager.save_game(party1, 1, "PARTY_1", game_state1)
        
        time.sleep(0.1)
        
        party2 = self._create_test_party("PARTY_2")
        game_state2 = {"location": "overworld"}
        self.save_manager.save_game(party2, 2, "PARTY_2", game_state2)
        
        # 最新のスロットを確認
        slots = self.save_manager.get_save_slots()
        latest_slot = max(slots, key=lambda s: s.last_saved)
        self.assertEqual(latest_slot.name, "PARTY_2")
    
    def test_save_manager_load_game(self):
        """セーブデータのロードテスト"""
        party = self._create_test_party("LOAD_TEST_PARTY")
        game_state = {"location": "overworld"}
        
        # セーブしてロード
        self.save_manager.save_game(party, 1, "LOAD_TEST_PARTY", game_state)
        loaded_data = self.save_manager.load_game(1)
        
        self.assertIsNotNone(loaded_data)
        self.assertEqual(loaded_data.party.name, "LOAD_TEST_PARTY")
        self.assertEqual(loaded_data.game_state["location"], "overworld")


if __name__ == '__main__':
    unittest.main()