"""モック活用のベストプラクティス例

このファイルは、テストでのモック使用方法のガイドとして機能します。
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from src.character.character import Character, CharacterStatus
from src.character.stats import BaseStats


@pytest.mark.unit
class TestMockUsageExamples:
    """モック使用例のデモンストレーション"""
    
    def test_mock_external_dependencies(self):
        """外部依存関係のモック化例"""
        # ❌ 悪い例: 実際のファイルシステムを使用
        # with open("config/races.yaml") as f:
        #     data = yaml.load(f)
        
        # ✅ 良い例: ファイルアクセスをモック化
        mock_config_data = {
            'human': {'name': '人間', 'stat_modifiers': {'strength': 1.0}},
            'elf': {'name': 'エルフ', 'stat_modifiers': {'agility': 1.1}}
        }
        
        with patch('builtins.open'), patch('yaml.load', return_value=mock_config_data):
            # この例では、実際のファイルに依存しない
            import yaml
            data = yaml.load("dummy_file")
            assert data['human']['name'] == '人間'
    
    def test_mock_complex_objects(self):
        """複雑なオブジェクトのモック化例"""
        # ❌ 悪い例: DungeonManagerの完全インスタンス化
        # dungeon_manager = DungeonManager()
        # dungeon_manager.create_dungeon("test", "seed")  # 重い処理
        
        # ✅ 良い例: 必要な部分のみモック化
        mock_dungeon_manager = Mock()
        mock_dungeon_manager.current_dungeon.player_position.x = 5
        mock_dungeon_manager.current_dungeon.player_position.y = 3
        mock_dungeon_manager.move_player.return_value = (True, "移動成功")
        
        # テスト実行
        x = mock_dungeon_manager.current_dungeon.player_position.x
        y = mock_dungeon_manager.current_dungeon.player_position.y
        success, message = mock_dungeon_manager.move_player("north")
        
        # 具体的なアサーション
        assert x == 5
        assert y == 3
        assert success is True
        assert message == "移動成功"
    
    def test_spy_on_method_calls(self):
        """メソッド呼び出しの監視例"""
        character = Character.create_character(
            "TestHero", "human", "fighter", 
            BaseStats(strength=15, agility=12, intelligence=10)
        )
        
        # メソッド呼び出しを監視
        with patch.object(character, 'take_damage', wraps=character.take_damage) as spy:
            # テスト対象のコードを実行
            character.take_damage(10)
            
            # メソッドが正しく呼ばれたことを確認
            spy.assert_called_once_with(10)
    
    def test_mock_with_side_effects(self):
        """副作用を持つモックの例"""
        mock_dice_roller = Mock()
        
        # 複数回呼び出されるときの戻り値を設定
        mock_dice_roller.roll_d6.side_effect = [1, 6, 3, 4]
        
        # テスト実行
        results = [mock_dice_roller.roll_d6() for _ in range(4)]
        
        # 期待される順序で値が返されることを確認
        assert results == [1, 6, 3, 4]
        assert mock_dice_roller.roll_d6.call_count == 4
    
    def test_mock_context_manager(self):
        """コンテキストマネージャーのモック例"""
        mock_file = MagicMock()
        mock_file.__enter__.return_value = mock_file
        mock_file.read.return_value = '{"test": "data"}'
        
        with patch('builtins.open', return_value=mock_file):
            # ファイル読み込みをモック化
            with open('test.json', 'r') as f:
                content = f.read()
            
            assert content == '{"test": "data"}'


@pytest.mark.unit
class TestAssertionBestPractices:
    """アサーションのベストプラクティス例"""
    
    def test_specific_assertions_vs_generic(self, mock_character):
        """具体的なアサーション vs 抽象的なアサーション"""
        # ❌ 悪い例: 抽象的なアサーション
        # assert mock_character is not None
        # assert hasattr(mock_character, 'name')
        
        # ✅ 良い例: 具体的なアサーション
        assert mock_character.name == "テストキャラクター"
        assert mock_character.race == "human"
        assert mock_character.character_class == "fighter"
        assert mock_character.level == 1
        assert mock_character.hp == 50
        assert mock_character.max_hp == 50
    
    def test_error_condition_assertions(self, mock_character):
        """エラー条件の具体的なアサーション"""
        # モックキャラクターでダメージ計算をシミュレート
        initial_hp = mock_character.hp
        damage_amount = 25
        
        # ダメージ計算をシミュレート
        new_hp = max(0, initial_hp - damage_amount)
        mock_character.hp = new_hp
        
        # ❌ 悪い例: 抽象的なアサーション
        # assert mock_character.hp < initial_hp
        
        # ✅ 良い例: 具体的なアサーション
        expected_hp = max(0, initial_hp - damage_amount)
        assert mock_character.hp == expected_hp
        
        # HP範囲の検証
        assert mock_character.hp >= 0
        assert mock_character.hp <= mock_character.max_hp
    
    def test_collection_assertions(self):
        """コレクションの具体的なアサーション"""
        from src.character.party import Party
        
        party = Party("TestParty")
        
        char1 = Character.create_character("Hero1", "human", "fighter", BaseStats(strength=15))
        char2 = Character.create_character("Hero2", "elf", "mage", BaseStats(intelligence=16))
        
        party.add_character(char1)
        party.add_character(char2)
        
        # ❌ 悪い例: 抽象的なアサーション
        # assert len(party.characters) > 0
        # assert char1 in party.characters.values()
        
        # ✅ 良い例: 具体的なアサーション
        assert len(party.characters) == 2
        assert char1.character_id in party.characters
        assert char2.character_id in party.characters
        assert party.characters[char1.character_id].name == "Hero1"
        assert party.characters[char2.character_id].name == "Hero2"
    
    def test_floating_point_assertions(self):
        """浮動小数点数の適切なアサーション"""
        # 浮動小数点計算のテスト例（単純な計算でデモ）
        base_value = 10.0
        modifier = 1.15  # 15%ボーナス
        
        calculated_value = base_value * modifier
        
        # ❌ 悪い例: 厳密な等価比較（浮動小数点誤差で失敗する可能性）
        # assert calculated_value == 11.5
        
        # ✅ 良い例: 適切な許容誤差での比較
        expected_value = 11.5
        assert abs(calculated_value - expected_value) < 0.01
        
        # pytest.approx を使用した例
        assert calculated_value == pytest.approx(11.5, rel=1e-2)
    
    def test_exception_assertions(self):
        """例外の具体的なアサーション"""
        # 例外を発生させる関数の例
        def validate_positive_number(value):
            if value <= 0:
                raise ValueError("値は正の数である必要があります")
            return value
        
        # ❌ 悪い例: 例外の種類のみチェック
        # with pytest.raises(Exception):
        #     validate_positive_number(-1)
        
        # ✅ 良い例: 例外の種類とメッセージをチェック
        with pytest.raises(ValueError, match="値は正の数である必要があります"):
            validate_positive_number(-1)
    
    def test_state_transition_assertions(self, mock_character):
        """状態遷移の具体的なアサーション"""
        # 初期状態のシミュレート
        mock_character.status = "good"
        initial_hp = mock_character.hp
        
        # 致命的ダメージのシミュレート
        mock_character.hp = 0
        mock_character.status = "dead"
        
        # ❌ 悪い例: 抽象的な状態チェック
        # assert mock_character.status != "good"
        
        # ✅ 良い例: 具体的な状態チェック
        assert mock_character.status == "dead"
        assert mock_character.hp == 0