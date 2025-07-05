"""Phase 6: 全体システム統合テスト

Phase 4施設システム ⇔ Phase 5ダンジョン・戦闘システムの完全統合を検証
"""

import unittest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch, MagicMock
import time

from src.core.game_manager import GameManager
from src.character.party import Party
from src.character.character import Character, CharacterStatus
from src.character.stats import BaseStats, DerivedStats
from src.character.character import Experience
from src.core.save_manager import SaveManager
from src.facilities.core.facility_registry import facility_registry
from src.dungeon.dungeon_manager import DungeonManager
from src.combat.combat_manager import CombatManager


class TestPhase6SystemIntegration(unittest.TestCase):
    """Phase 6 全体システム統合テスト"""
    
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.game_manager = GameManager()
        self.party = self._create_test_party()
        
    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def _create_test_party(self) -> Party:
        """統合テスト用パーティ作成"""
        party = Party("IntegrationTestParty")
        
        # 戦士
        fighter = Character(
            character_id="fighter_001",
            name="統合テスト戦士",
            race="human",
            character_class="fighter",
            base_stats=BaseStats(strength=16, vitality=15, agility=12, intelligence=10, faith=8, luck=11),
            derived_stats=DerivedStats(),
            experience=Experience(current_xp=1000, level=3)
        )
        fighter.status = CharacterStatus.GOOD
        
        # 魔法使い
        mage = Character(
            character_id="mage_001", 
            name="統合テスト魔法使い",
            race="elf",
            character_class="mage",
            base_stats=BaseStats(strength=8, vitality=10, agility=14, intelligence=17, faith=12, luck=13),
            derived_stats=DerivedStats(),
            experience=Experience(current_xp=1200, level=3)
        )
        mage.status = CharacterStatus.GOOD
        
        party.add_character(fighter)
        party.add_character(mage)
        
        return party
    
    def test_overworld_to_dungeon_flow(self):
        """地上部からダンジョンへの遷移フロー統合テスト"""
        # 地上部でパーティ設定
        self.game_manager.set_current_party(self.party)
        
        # 地上部システムが正常に動作しているか
        current_party = self.game_manager.get_current_party()
        self.assertIsNotNone(current_party)
        self.assertEqual(len(current_party.characters), 2)
        
        # ダンジョン入場処理
        try:
            self.game_manager.transition_to_dungeon("training_dungeon")
            dungeon_entry_success = True
        except Exception as e:
            logger.error(f"ダンジョン入場エラー: {e}")
            dungeon_entry_success = False
        
        self.assertTrue(dungeon_entry_success, "ダンジョン入場が失敗しました")
        
        # ダンジョンマネージャーが正しく初期化されているか
        self.assertIsNotNone(self.game_manager.dungeon_manager)
        self.assertTrue(self.game_manager.in_dungeon)
        
        # パーティ情報がダンジョンに正しく渡されているか
        dungeon_party = self.game_manager.dungeon_manager.party
        self.assertIsNotNone(dungeon_party)
        self.assertEqual(len(dungeon_party.characters), 2)
        self.assertEqual(dungeon_party.name, "IntegrationTestParty")
    
    def test_dungeon_combat_integration(self):
        """ダンジョン探索・戦闘システム統合テスト"""
        # ダンジョンに入る
        self.game_manager.set_current_party(self.party)
        self.game_manager.enter_dungeon("training_dungeon", 1)
        
        # エンカウンター発生テスト
        encounter_result = self.game_manager.trigger_encounter("normal", 1)
        self.assertIsNotNone(encounter_result, "エンカウンターが発生しませんでした")
        
        # 戦闘マネージャーが正しく初期化されているか
        self.assertIsNotNone(self.game_manager.combat_manager)
        
        # 戦闘状態確認
        combat_state = self.game_manager.check_combat_state()
        self.assertIsNotNone(combat_state)
        
        # 戦闘終了処理テスト（勝利想定）
        with patch.object(self.game_manager.combat_manager, 'is_combat_over', return_value=True):
            with patch.object(self.game_manager.combat_manager, 'get_combat_result', return_value="victory"):
                self.game_manager.end_combat()
                
                # 戦闘後にダンジョンに戻ることができるか
                self.assertTrue(self.game_manager.in_dungeon)
                self.assertIsNotNone(self.game_manager.dungeon_manager)
    
    def test_dungeon_interaction_systems(self):
        """ダンジョン内インタラクションシステム統合テスト"""
        # ダンジョンに入る
        self.game_manager.set_current_party(self.party)
        self.game_manager.enter_dungeon("training_dungeon", 1)
        
        # トラップシステム統合確認
        trap_result = self.game_manager.interact_with_dungeon_cell()
        self.assertIsNotNone(trap_result, "ダンジョンセル操作が機能しません")
        
        # 隠し通路探索
        search_result = self.game_manager.search_for_secrets()
        self.assertIsNotNone(search_result, "隠し通路探索が機能しません")
        
        # パーティステータス監視
        party_status = self.game_manager.check_party_status_in_dungeon()
        self.assertIsNotNone(party_status)
        
        # パーティが生存している場合の確認
        self.assertIn("alive_members", party_status)
        self.assertGreater(party_status["alive_members"], 0)
    
    def test_equipment_magic_integration(self):
        """装備・魔法システム統合テスト（Phase 4 ⇔ Phase 5）"""
        # パーティメンバーの装備・魔法効果が戦闘に反映されるか
        fighter = list(self.party.characters.values())[0]
        
        # 基本攻撃力・防御力取得（Phase 4システム統合）
        attack_power = fighter.get_attack_power()
        defense_power = fighter.get_defense()
        
        self.assertIsInstance(attack_power, (int, float))
        self.assertIsInstance(defense_power, (int, float))
        self.assertGreater(attack_power, 0)
        self.assertGreaterEqual(defense_power, 0)
        
        # 戦闘での使用確認
        self.game_manager.set_current_party(self.party)
        self.game_manager.enter_dungeon("training_dungeon", 1)
        
        # エンカウンター発生
        self.game_manager.trigger_encounter("normal", 1)
        
        # 戦闘マネージャーが正しく装備効果を取得できるか
        if self.game_manager.combat_manager:
            # 戦闘計算で装備効果が使用されているかを間接的に確認
            self.assertIsNotNone(self.game_manager.combat_manager.party)
            self.assertEqual(len(self.game_manager.combat_manager.party.characters), 2)
    
    def test_save_load_integration(self):
        """セーブ・ロードシステム統合テスト"""
        save_manager = SaveManager()
        
        # ダンジョン状態を含む包括的なゲーム状態をセーブ
        self.game_manager.set_current_party(self.party)
        self.game_manager.enter_dungeon("training_dungeon", 1)
        
        # セーブ実行
        save_result = save_manager.save_game(
            slot=1, 
            party=self.party,
            current_location="dungeon_level_1",
            playtime=1800
        )
        self.assertTrue(save_result, "セーブが失敗しました")
        
        # ロード実行
        load_result = save_manager.load_game(1)
        self.assertIsNotNone(load_result, "ロードが失敗しました")
        
        # ロードされたデータの検証
        self.assertIsNotNone(load_result.party)
        self.assertEqual(len(load_result.party.characters), 2)
        
        # Phase 5システムの状態も保存されているか確認
        self.assertIsInstance(load_result.current_location, str)
    
    def test_error_handling_resilience(self):
        """エラーハンドリング・耐障害性テスト"""
        # 無効なダンジョンID
        result = self.game_manager.enter_dungeon("invalid_dungeon", 1)
        self.assertFalse(result, "無効なダンジョンIDでも入場できてしまいます")
        
        # パーティなしでの操作
        self.game_manager.set_current_party(None)
        result = self.game_manager.enter_dungeon("training_dungeon", 1)
        self.assertFalse(result, "パーティなしでダンジョンに入れてしまいます")
        
        # 破損したパーティデータ
        broken_party = Party("BrokenParty")
        # メンバーを追加せずに操作
        self.game_manager.set_current_party(broken_party)
        result = self.game_manager.enter_dungeon("training_dungeon", 1)
        # 空のパーティでも適切に処理されるか
        self.assertIsInstance(result, bool)
    
    def test_memory_and_resource_management(self):
        """メモリ・リソース管理テスト"""
        # 複数回のダンジョン入退場でメモリリークがないか
        initial_party = self.party
        
        for i in range(5):
            # ダンジョン入場
            self.game_manager.set_current_party(initial_party)
            self.game_manager.enter_dungeon("training_dungeon", 1)
            
            # エンカウンター・戦闘
            self.game_manager.trigger_encounter("normal", 1)
            
            # 戦闘終了
            if self.game_manager.combat_manager:
                with patch.object(self.game_manager.combat_manager, 'is_combat_over', return_value=True):
                    with patch.object(self.game_manager.combat_manager, 'get_combat_result', return_value="victory"):
                        self.game_manager.end_combat()
            
            # ダンジョン退場
            self.game_manager.exit_dungeon()
            
            # オブジェクトが適切にクリーンアップされているか
            # （完全なメモリプロファイリングは別途実施）
            self.assertFalse(self.game_manager.in_dungeon)
    
    def test_performance_benchmarks(self):
        """パフォーマンスベンチマークテスト"""
        # システム統合でのレスポンス時間測定
        
        # ダンジョン入場時間
        start_time = time.time()
        self.game_manager.set_current_party(self.party)
        self.game_manager.enter_dungeon("training_dungeon", 1)
        dungeon_entry_time = time.time() - start_time
        
        # 1秒以内での入場を期待
        self.assertLess(dungeon_entry_time, 1.0, f"ダンジョン入場に{dungeon_entry_time:.3f}秒かかりました")
        
        # エンカウンター発生時間
        start_time = time.time()
        self.game_manager.trigger_encounter("normal", 1)
        encounter_time = time.time() - start_time
        
        # 0.5秒以内でのエンカウンター発生を期待
        self.assertLess(encounter_time, 0.5, f"エンカウンター発生に{encounter_time:.3f}秒かかりました")
        
        # セーブ・ロード時間
        save_manager = SaveManager()
        
        start_time = time.time()
        save_result = save_manager.save_game(slot=1, party=self.party, current_location="test", playtime=0)
        save_time = time.time() - start_time
        
        if save_result:
            start_time = time.time()
            load_result = save_manager.load_game(1)
            load_time = time.time() - start_time
            
            # セーブ・ロードが各々2秒以内を期待
            self.assertLess(save_time, 2.0, f"セーブに{save_time:.3f}秒かかりました")
            self.assertLess(load_time, 2.0, f"ロードに{load_time:.3f}秒かかりました")
    
    def test_data_flow_consistency(self):
        """システム間データフロー一貫性テスト"""
        # パーティデータがシステム間で一貫して管理されているか
        
        # 1. 地上部でのパーティ設定
        original_party = self.party
        self.game_manager.set_current_party(original_party)
        
        # GameManagerのパーティ
        gm_party = self.game_manager.get_current_party()
        self.assertEqual(gm_party.name, original_party.name)
        self.assertEqual(len(gm_party.characters), len(original_party.characters))
        
        # 2. ダンジョン入場後のパーティデータ
        self.game_manager.enter_dungeon("training_dungeon", 1)
        dungeon_party = self.game_manager.dungeon_manager.party
        
        # 同じパーティオブジェクトが使用されているか
        self.assertEqual(dungeon_party.name, original_party.name)
        self.assertEqual(len(dungeon_party.characters), len(original_party.characters))
        
        # 3. 戦闘開始時のパーティデータ
        self.game_manager.trigger_encounter("normal", 1)
        if self.game_manager.combat_manager:
            combat_party = self.game_manager.combat_manager.party
            self.assertEqual(combat_party.name, original_party.name)
            self.assertEqual(len(combat_party.characters), len(original_party.characters))
        
        # 4. キャラクターステータスの一貫性
        original_characters = list(original_party.characters.values())
        dungeon_characters = list(dungeon_party.characters.values())
        
        for i, member in enumerate(original_characters):
            # ダンジョンパーティでの同じキャラクター
            dungeon_member = dungeon_characters[i]
            self.assertEqual(member.character_id, dungeon_member.character_id)
            self.assertEqual(member.name, dungeon_member.name)
            self.assertEqual(member.status, dungeon_member.status)


if __name__ == '__main__':
    unittest.main()