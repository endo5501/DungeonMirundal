"""地上部-ダンジョン遷移システムの簡易テスト"""

import pytest
from unittest.mock import Mock, patch

from src.character.character import Character
from src.character.party import Party
from src.character.stats import BaseStats


class TestTransitionSystemSimple:
    """遷移システムの簡易テスト（モックなし）"""
    
    def setup_method(self):
        """各テストメソッドの前に実行"""
        # テスト用パーティ作成
        stats = BaseStats(strength=14, agility=12, intelligence=10, faith=11, luck=13)
        character = Character.create_character("TestHero", "human", "fighter", stats)
        
        self.party = Party(party_id="test_party", name="TestParty")
        self.party.add_character(character)
    
    def test_party_living_characters(self):
        """パーティの生存キャラクターテスト"""
        # 初期状態では生存している
        living_chars = self.party.get_living_characters()
        assert len(living_chars) == 1
        assert living_chars[0].name == "TestHero"
        
        # 全員死亡させる
        for character in living_chars:
            character.take_damage(1000)
        
        # 生存キャラクターがいなくなる
        living_chars = self.party.get_living_characters()
        assert len(living_chars) == 0
    
    def test_character_damage_system(self):
        """キャラクターダメージシステムのテスト"""
        character = self.party.get_living_characters()[0]
        initial_hp = character.derived_stats.current_hp
        
        # ダメージを与える
        damage_taken = character.take_damage(10)
        assert damage_taken == 10
        assert character.derived_stats.current_hp == initial_hp - 10
        
        # 瀕死状態のテスト
        character.take_damage(1000)
        assert not character.is_conscious() or not character.is_alive()
    
    @patch('src.core.game_manager.ShowBase')
    def test_game_manager_basic_functionality(self, mock_showbase):
        """GameManagerの基本機能テスト"""
        # ShowBaseをモック化してGameManagerをテスト
        with patch('src.core.game_manager.config_manager') as mock_config:
            mock_config.load_config.return_value = {
                "gameplay": {"language": "ja"}, 
                "window": {}, 
                "graphics": {"fps": 60}, 
                "debug": {"enabled": False}
            }
            mock_config.get_text.return_value = "Test"
            mock_config.set_language = Mock()
            
            with patch('src.core.game_manager.globalClock', create=True) as mock_clock:
                mock_clock.setMode = Mock()
                mock_clock.setFrameRate = Mock()
                mock_clock.MLimited = 1
                
                # ShowBaseインスタンスのモック
                mock_instance = Mock()
                mock_instance.win = Mock()
                mock_instance.win.requestProperties = Mock()
                mock_instance.win.getProperties = Mock(return_value=Mock())
                mock_instance.setFrameRateMeter = Mock()
                mock_instance.config = mock_config
                mock_showbase.return_value = mock_instance
                
                from src.core.game_manager import GameManager
                game_manager = GameManager()
                
                # 基本プロパティの確認
                assert game_manager.current_location == "overworld"
                assert game_manager.game_state == "startup"
                
                # パーティの設定と取得
                game_manager.set_current_party(self.party)
                assert game_manager.get_current_party() == self.party
                assert game_manager.current_party == self.party
    
    def test_dungeon_manager_callback(self):
        """ダンジョンマネージャーのコールバック機能テスト"""
        from src.dungeon.dungeon_manager import DungeonManager
        
        dungeon_manager = DungeonManager()
        
        # コールバック設定前は None
        assert dungeon_manager.return_to_overworld_callback is None
        
        # コールバック設定
        mock_callback = Mock(return_value=True)
        dungeon_manager.set_return_to_overworld_callback(mock_callback)
        assert dungeon_manager.return_to_overworld_callback == mock_callback
        
        # ダンジョンなしでの帰還テスト（失敗する）
        result = dungeon_manager.return_to_overworld()
        assert result == False
    
    def test_party_serialization(self):
        """パーティのシリアライゼーションテスト"""
        # パーティを辞書に変換
        party_dict = self.party.to_dict()
        
        # 基本情報の確認
        assert party_dict['party_id'] == "test_party"
        assert party_dict['name'] == "TestParty"
        assert len(party_dict['characters']) == 1
        
        # パーティを復元
        restored_party = Party.from_dict(party_dict)
        assert restored_party.party_id == self.party.party_id
        assert restored_party.name == self.party.name
        original_chars = self.party.get_living_characters()
        restored_chars = restored_party.get_living_characters()
        assert len(restored_chars) == len(original_chars)
        assert restored_chars[0].name == original_chars[0].name
    
    def test_save_manager_functionality(self):
        """セーブマネージャーの基本機能テスト"""
        from src.core.save_manager import save_manager
        
        # テストデータ
        test_data = {
            'current_location': 'overworld',
            'game_state': 'overworld_exploration',
            'party_id': 'test_party'
        }
        
        # データ保存
        result = save_manager.save_additional_data("test_slot", "game_state", test_data)
        assert result == True
        
        # データ読み込み
        loaded_data = save_manager.load_additional_data("test_slot", "game_state")
        assert loaded_data == test_data
        
        # 存在しないデータの読み込み
        no_data = save_manager.load_additional_data("nonexistent_slot", "game_state")
        assert no_data is None


class TestTransitionIntegration:
    """統合テスト（実際のコンポーネント使用）"""
    
    def setup_method(self):
        """各テストメソッドの前に実行"""
        # テスト用パーティ作成
        stats = BaseStats(strength=14, agility=12, intelligence=10, faith=11, luck=13)
        character = Character.create_character("TestHero", "human", "fighter", stats)
        
        self.party = Party(party_id="test_party", name="TestParty")
        self.party.add_character(character)
    
    def test_overworld_manager_basic(self):
        """地上部マネージャーの基本機能テスト"""
        from src.overworld.overworld_manager import OverworldManager
        
        overworld_manager = OverworldManager()
        
        # パーティ入場
        result = overworld_manager.enter_overworld(self.party)
        assert result == True
        
        # パーティ退場
        result = overworld_manager.exit_overworld()
        assert result == True
    
    def test_dungeon_manager_basic(self):
        """ダンジョンマネージャーの基本機能テスト"""
        from src.dungeon.dungeon_manager import DungeonManager
        
        dungeon_manager = DungeonManager()
        
        # ダンジョン作成
        dungeon_state = dungeon_manager.create_dungeon("test_dungeon", "test_seed")
        assert dungeon_state.dungeon_id == "test_dungeon"
        assert dungeon_state.seed == "test_seed"
        
        # パーティ入場
        result = dungeon_manager.enter_dungeon("test_dungeon", self.party)
        assert result == True
        
        # パーティ退場
        result = dungeon_manager.exit_dungeon()
        assert result == True
    
    def test_integrated_transition_flow(self):
        """統合遷移フローのテスト"""
        from src.overworld.overworld_manager import OverworldManager
        from src.dungeon.dungeon_manager import DungeonManager
        
        overworld_manager = OverworldManager()
        dungeon_manager = DungeonManager()
        
        # 地上部開始
        assert overworld_manager.enter_overworld(self.party) == True
        
        # ダンジョン準備
        dungeon_state = dungeon_manager.create_dungeon("main_dungeon", "seed123")
        assert dungeon_state is not None
        
        # 地上部 → ダンジョン遷移
        assert overworld_manager.exit_overworld() == True
        assert dungeon_manager.enter_dungeon("main_dungeon", self.party) == True
        
        # ダンジョン → 地上部遷移
        assert dungeon_manager.exit_dungeon() == True
        assert overworld_manager.enter_overworld(self.party) == True
        
        # 最終確認
        assert overworld_manager.exit_overworld() == True