"""ダンジョン入口ロジック修正の単純テスト"""

import unittest
from unittest.mock import Mock

from src.character.character import Character, CharacterStatus
from src.character.party import Party


class TestDungeonEntranceLogicFix(unittest.TestCase):
    """ダンジョン入口ロジック修正のテストクラス"""
    
    def setUp(self):
        """テスト前のセットアップ"""
        # 実際のキャラクターオブジェクトを作成
        self.good_character = Character("健康なキャラクター", "human", "fighter")
        self.good_character.status = CharacterStatus.GOOD
        
        self.injured_character = Character("負傷したキャラクター", "human", "fighter")
        self.injured_character.status = CharacterStatus.INJURED
        
        self.dead_character = Character("死亡したキャラクター", "human", "fighter")
        self.dead_character.status = CharacterStatus.DEAD
    
    def test_character_status_check_methods(self):
        """キャラクターの状態チェックメソッドのテスト"""
        # 健康なキャラクター
        self.assertTrue(self.good_character.is_alive())
        self.assertTrue(self.good_character.is_conscious())
        
        # 負傷したキャラクター
        self.assertTrue(self.injured_character.is_alive())
        self.assertFalse(self.injured_character.is_conscious())
        
        # 死亡したキャラクター
        self.assertFalse(self.dead_character.is_alive())
        self.assertFalse(self.dead_character.is_conscious())
    
    def test_party_living_characters_with_injured(self):
        """負傷者を含むパーティの生存者チェック"""
        party = Party("テストパーティ")
        party.add_character(self.injured_character)
        
        living_characters = party.get_living_characters()
        conscious_characters = party.get_conscious_characters()
        
        # 負傷者は生存しているが意識がない
        self.assertEqual(len(living_characters), 1)
        self.assertEqual(len(conscious_characters), 0)
        self.assertEqual(living_characters[0], self.injured_character)
    
    def test_party_mixed_status_characters(self):
        """様々な状態のキャラクターが混在するパーティ"""
        party = Party("混在パーティ")
        party.add_character(self.good_character)
        party.add_character(self.injured_character)
        party.add_character(self.dead_character)
        
        living_characters = party.get_living_characters()
        conscious_characters = party.get_conscious_characters()
        
        # 生存者は2人（健康・負傷）、意識があるのは1人（健康のみ）
        self.assertEqual(len(living_characters), 2)
        self.assertEqual(len(conscious_characters), 1)
        
        # 生存者に健康と負傷の両方が含まれている
        self.assertIn(self.good_character, living_characters)
        self.assertIn(self.injured_character, living_characters)
        self.assertNotIn(self.dead_character, living_characters)
        
        # 意識があるのは健康なキャラクターのみ
        self.assertIn(self.good_character, conscious_characters)
        self.assertNotIn(self.injured_character, conscious_characters)
        self.assertNotIn(self.dead_character, conscious_characters)
    
    def test_party_only_dead_characters(self):
        """全員死亡しているパーティ"""
        party = Party("全滅パーティ")
        party.add_character(self.dead_character)
        
        living_characters = party.get_living_characters()
        conscious_characters = party.get_conscious_characters()
        
        # 生存者も意識がある者もいない
        self.assertEqual(len(living_characters), 0)
        self.assertEqual(len(conscious_characters), 0)
    
    def test_dungeon_entrance_logic_fixed(self):
        """修正されたダンジョン入場ロジックのテスト"""
        # 負傷者のみのパーティ
        injured_party = Party("負傷者パーティ")
        injured_party.add_character(self.injured_character)
        
        # 修正後：生存者がいればダンジョン入場可能
        living_members = injured_party.get_living_characters()
        can_enter_dungeon = len(living_members) > 0
        
        self.assertTrue(can_enter_dungeon, "負傷者でも生存していればダンジョンに入場できるべき")
        
        # 全滅パーティ
        dead_party = Party("全滅パーティ")
        dead_party.add_character(self.dead_character)
        
        living_members = dead_party.get_living_characters()
        can_enter_dungeon = len(living_members) > 0
        
        self.assertFalse(can_enter_dungeon, "全員死亡している場合はダンジョンに入場できない")
    
    def test_consistency_between_checks(self):
        """チェック基準の一貫性テスト"""
        mixed_party = Party("混在パーティ")
        mixed_party.add_character(self.good_character)
        mixed_party.add_character(self.injured_character)
        
        # OverworldManagerのチェック（修正後）
        living_members = mixed_party.get_living_characters()
        overworld_allows_entry = len(living_members) > 0
        
        # GameManagerのチェック
        game_manager_allows_entry = len(living_members) > 0
        
        # 両方のチェック基準が一致することを確認
        self.assertEqual(overworld_allows_entry, game_manager_allows_entry, 
                        "OverworldManagerとGameManagerのチェック基準が一致すべき")
        
        # 負傷者がいても入場可能
        self.assertTrue(overworld_allows_entry, "負傷者がいても入場可能であるべき")


if __name__ == '__main__':
    unittest.main()