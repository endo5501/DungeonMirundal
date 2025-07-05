"""Phase 6: API整合性テスト

システム間のAPI整合性を検証し、不整合を修正するためのテスト
"""

import unittest
from unittest.mock import MagicMock

from src.core.game_manager import GameManager
from src.character.party import Party
from src.character.character import Character, CharacterStatus
from src.character.stats import BaseStats, DerivedStats
from src.character.character import Experience


class TestPhase6APIConsistency(unittest.TestCase):
    """Phase 6 API整合性テスト"""
    
    def setUp(self):
        self.game_manager = GameManager()
        
    def test_party_api_consistency(self):
        """パーティAPIの整合性テスト"""
        party = Party("TestParty")
        
        # パーティの基本属性確認
        self.assertTrue(hasattr(party, 'characters'), "Partyにcharacters属性が必要です")
        self.assertTrue(hasattr(party, 'name'), "Partyにname属性が必要です")
        
        # パーティのメソッド確認
        self.assertTrue(hasattr(party, 'add_character'), "Partyにadd_characterメソッドが必要です")
        self.assertTrue(hasattr(party, 'remove_character'), "Partyにremove_characterメソッドが必要です")
        self.assertTrue(hasattr(party, 'get_all_characters'), "Partyにget_all_charactersメソッドが必要です")
        
        # charactersがdictであることを確認
        self.assertIsInstance(party.characters, dict, "Party.charactersはdictである必要があります")
        
        # 文字列表現確認
        party_str = str(party)
        self.assertIsInstance(party_str, str, "Partyの文字列表現が取得できません")
    
    def test_character_api_consistency(self):
        """キャラクターAPIの整合性テスト"""
        character = Character(
            character_id="test_001",
            name="テストキャラクター",
            race="human",
            character_class="fighter",
            base_stats=BaseStats(strength=15, vitality=14, agility=12, intelligence=10, faith=8, luck=11),
            derived_stats=DerivedStats(),
            experience=Experience(current_xp=500, level=2)
        )
        
        # 基本属性確認
        self.assertTrue(hasattr(character, 'character_id'), "Characterにcharacter_id属性が必要です")
        self.assertTrue(hasattr(character, 'name'), "Characterにname属性が必要です")
        self.assertTrue(hasattr(character, 'base_stats'), "Characterにbase_stats属性が必要です")
        self.assertTrue(hasattr(character, 'derived_stats'), "Characterにderived_stats属性が必要です")
        
        # 統計値属性の型確認
        self.assertIsInstance(character.base_stats, BaseStats, "base_statsはBaseStats型である必要があります")
        self.assertIsInstance(character.derived_stats, DerivedStats, "derived_statsはDerivedStats型である必要があります")
        
        # 必須メソッド確認
        expected_methods = [
            'get_attack_power', 'get_defense', 'initialize_derived_stats',
            'get_inventory', 'get_equipment', 'get_status_effects'
        ]
        
        for method_name in expected_methods:
            self.assertTrue(hasattr(character, method_name), 
                          f"Characterに{method_name}メソッドが必要です")
    
    def test_game_manager_api_consistency(self):
        """GameManagerAPIの整合性テスト"""
        
        # パーティ管理メソッド確認
        party_methods = ['set_current_party', 'get_current_party']
        for method_name in party_methods:
            self.assertTrue(hasattr(self.game_manager, method_name), 
                          f"GameManagerに{method_name}メソッドが必要です")
        
        # ダンジョン管理メソッド確認
        dungeon_methods = ['transition_to_dungeon']
        for method_name in dungeon_methods:
            self.assertTrue(hasattr(self.game_manager, method_name), 
                          f"GameManagerに{method_name}メソッドが必要です")
        
        # 戦闘管理メソッド確認
        combat_methods = ['trigger_encounter', 'check_combat_state', 'end_combat']
        for method_name in combat_methods:
            self.assertTrue(hasattr(self.game_manager, method_name), 
                          f"GameManagerに{method_name}メソッドが必要です")
        
        # システム状態プロパティ確認
        state_properties = ['in_dungeon', 'current_location']
        for prop_name in state_properties:
            self.assertTrue(hasattr(self.game_manager, prop_name), 
                          f"GameManagerに{prop_name}プロパティが必要です")
    
    def test_party_character_integration(self):
        """パーティとキャラクターの統合テスト"""
        party = Party("IntegrationTestParty")
        
        character = Character(
            character_id="integration_001",
            name="統合テストキャラ",
            race="human",
            character_class="fighter",
            base_stats=BaseStats(strength=15, vitality=14, agility=12, intelligence=10, faith=8, luck=11),
            derived_stats=DerivedStats(),
            experience=Experience(current_xp=500, level=2)
        )
        
        # キャラクターをパーティに追加
        add_result = party.add_character(character)
        self.assertTrue(add_result, "キャラクターのパーティ追加が失敗しました")
        
        # パーティにキャラクターが追加されているか確認
        self.assertEqual(len(party.characters), 1, "パーティのキャラクター数が正しくありません")
        self.assertIn(character.character_id, party.characters, "キャラクターIDがパーティに登録されていません")
        
        # パーティからキャラクターを取得
        retrieved_character = party.get_character(character.character_id)
        self.assertIsNotNone(retrieved_character, "パーティからキャラクターが取得できません")
        self.assertEqual(retrieved_character.name, character.name, "取得したキャラクターの名前が一致しません")
        
        # 全キャラクター取得
        all_characters = party.get_all_characters()
        self.assertEqual(len(all_characters), 1, "全キャラクター取得の結果が正しくありません")
        self.assertEqual(all_characters[0].character_id, character.character_id, "キャラクターIDが一致しません")
    
    def test_save_load_data_consistency(self):
        """セーブ・ロードデータの整合性テスト"""
        # パーティ作成
        party = Party("SaveTestParty")
        character = Character(
            character_id="save_001",
            name="セーブテストキャラ",
            race="human",
            character_class="fighter",
            base_stats=BaseStats(strength=15, vitality=14, agility=12, intelligence=10, faith=8, luck=11),
            derived_stats=DerivedStats(),
            experience=Experience(current_xp=500, level=2)
        )
        party.add_character(character)
        
        # パーティをdictに変換
        party_dict = party.to_dict()
        self.assertIsInstance(party_dict, dict, "パーティのdict変換が失敗しました")
        
        # 必要な要素が含まれているか確認
        required_keys = ['party_id', 'name', 'characters', 'gold']
        for key in required_keys:
            self.assertIn(key, party_dict, f"パーティのdict変換に{key}が含まれていません")
        
        # キャラクターデータの確認
        character_dict = character.to_dict()
        self.assertIsInstance(character_dict, dict, "キャラクターのdict変換が失敗しました")
        
        # キャラクター必要要素確認
        char_required_keys = ['character_id', 'name', 'race', 'character_class', 'base_stats']
        for key in char_required_keys:
            self.assertIn(key, character_dict, f"キャラクターのdict変換に{key}が含まれていません")
    
    def test_system_manager_initialization(self):
        """システムマネージャー初期化の整合性テスト"""
        # GameManagerが適切に各マネージャーを初期化しているか
        managers_to_check = [
            'dungeon_manager', 'combat_manager', 'encounter_manager', 
            'overworld_manager', 'save_manager'
        ]
        
        for manager_name in managers_to_check:
            self.assertTrue(hasattr(self.game_manager, manager_name), 
                          f"GameManagerに{manager_name}が初期化されていません")
            
            manager = getattr(self.game_manager, manager_name)
            self.assertIsNotNone(manager, f"{manager_name}がNoneです")
    
    def test_error_handling_consistency(self):
        """エラーハンドリングの整合性テスト"""
        
        # パーティなしでのダンジョン遷移
        self.game_manager.set_current_party(None)
        
        try:
            self.game_manager.transition_to_dungeon("test_dungeon")
            transition_failed = False
        except Exception as e:
            transition_failed = True
            self.assertIsInstance(e, Exception, "適切な例外が発生していません")
        
        self.assertTrue(transition_failed, "パーティなしでのダンジョン遷移が例外を発生させませんでした")
        
        # 無効なキャラクターIDでのパーティ操作
        party = Party("ErrorTestParty")
        
        # 存在しないキャラクターの取得
        non_existent_char = party.get_character("non_existent_id")
        self.assertIsNone(non_existent_char, "存在しないキャラクターの取得がNoneを返しませんでした")
        
        # 存在しないキャラクターの削除
        remove_result = party.remove_character("non_existent_id")
        self.assertFalse(remove_result, "存在しないキャラクターの削除がFalseを返しませんでした")
    
    def test_logging_integration(self):
        """ログ出力の整合性テスト"""
        # ログが適切に出力されるかの基本確認
        # （ログの詳細検証は別途）
        
        party = Party("LogTestParty")
        character = Character(
            character_id="log_001",
            name="ログテストキャラ",
            race="human",
            character_class="fighter"
        )
        
        # パーティ操作でログが出力されることを確認（例外が発生しないこと）
        try:
            party.add_character(character)
            party.remove_character(character.character_id)
            log_operations_successful = True
        except Exception as e:
            log_operations_successful = False
            self.fail(f"ログ出力操作でエラーが発生しました: {e}")
        
        self.assertTrue(log_operations_successful, "ログ出力操作が失敗しました")


if __name__ == '__main__':
    unittest.main()