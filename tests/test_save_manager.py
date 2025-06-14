"""SaveManagerのテスト"""

import pytest
import tempfile
import shutil
from pathlib import Path
from src.core.save_manager import SaveManager, SaveSlot, GameSave
from src.character.character import Character
from src.character.party import Party
from src.character.stats import BaseStats


class TestSaveManager:
    """SaveManagerのテストクラス"""
    
    def setup_method(self):
        """各テストメソッドの前に実行"""
        # 一時ディレクトリの作成
        self.temp_dir = tempfile.TemporaryDirectory()
        self.save_manager = SaveManager(self.temp_dir.name)
        
        # テストパーティの作成
        self.test_party = self._create_test_party()
    
    def teardown_method(self):
        """各テストメソッドの後に実行"""
        self.temp_dir.cleanup()
    
    def _create_test_party(self) -> Party:
        """テスト用パーティの作成"""
        party = Party(name="Test Party")
        
        # テストキャラクター作成
        stats = BaseStats(strength=15, agility=12, intelligence=14, faith=10, luck=13)
        character = Character.create_character("TestHero", "human", "fighter", stats)
        party.add_character(character)
        party.add_gold(100)
        
        return party
    
    def test_save_game(self):
        """ゲーム保存のテスト"""
        success = self.save_manager.save_game(
            party=self.test_party,
            slot_id=1,
            save_name="Test Save"
        )
        
        assert success == True
        assert self.save_manager.has_save(1) == True
        
        # ファイルが実際に作成されているかチェック
        save_path = self.save_manager.get_save_path(1)
        assert save_path.exists()
    
    def test_load_game(self):
        """ゲームロードのテスト"""
        # まず保存
        self.save_manager.save_game(self.test_party, 1, "Test Save")
        
        # ロード
        game_save = self.save_manager.load_game(1)
        
        assert game_save is not None
        assert game_save.party.name == "Test Party"
        assert game_save.party.gold == 100
        assert len(game_save.party.characters) == 1
    
    def test_delete_save(self):
        """セーブデータ削除のテスト"""
        # 保存してから削除
        self.save_manager.save_game(self.test_party, 1, "Test Save")
        success = self.save_manager.delete_save(1)
        
        assert success == True
        assert self.save_manager.has_save(1) == False
        
        # ファイルが削除されているかチェック
        save_path = self.save_manager.get_save_path(1)
        assert not save_path.exists()
    
    def test_get_save_slots(self):
        """セーブスロット一覧取得のテスト"""
        # 複数のセーブを作成
        self.save_manager.save_game(self.test_party, 1, "Save 1")
        self.save_manager.save_game(self.test_party, 2, "Save 2")
        
        slots = self.save_manager.get_save_slots()
        
        assert len(slots) == 2
        assert slots[0].name in ["Save 1", "Save 2"]
        assert slots[1].name in ["Save 1", "Save 2"]
    
    def test_auto_save(self):
        """オートセーブのテスト"""
        # オートセーブ間隔を短く設定
        self.save_manager.auto_save_interval = 0
        
        success = self.save_manager.auto_save(self.test_party)
        
        assert success == True
        assert self.save_manager.has_save(0) == True  # スロット0がオートセーブ用
    
    def test_backup_creation(self):
        """バックアップ作成のテスト"""
        # 最初のセーブ
        self.save_manager.save_game(self.test_party, 1, "Original Save")
        
        # 2回目のセーブでバックアップが作成されるか
        self.test_party.add_gold(50)  # データを変更
        self.save_manager.save_game(self.test_party, 1, "Updated Save")
        
        backup_path = self.save_manager.get_backup_path(1)
        assert backup_path.exists()
    
    def test_save_with_game_state(self):
        """ゲーム状態付きセーブのテスト"""
        game_state = {
            'location': 'dungeon',
            'current_floor': 3,
            'flags': {'boss_defeated': False}
        }
        
        success = self.save_manager.save_game(
            party=self.test_party,
            slot_id=1,
            save_name="Dungeon Save",
            game_state=game_state
        )
        
        assert success == True
        
        # ロードして確認
        game_save = self.save_manager.load_game(1)
        assert game_save.game_state['location'] == 'dungeon'
        assert game_save.game_state['current_floor'] == 3


class TestSaveSlot:
    """SaveSlotのテスト"""
    
    def test_serialization(self):
        """シリアライゼーションのテスト"""
        slot = SaveSlot(
            slot_id=1,
            name="Test Save",
            party_name="Test Party",
            party_level=5,
            location="town"
        )
        
        # 辞書化してから復元
        data = slot.to_dict()
        restored = SaveSlot.from_dict(data)
        
        assert restored.slot_id == slot.slot_id
        assert restored.name == slot.name
        assert restored.party_name == slot.party_name
        assert restored.party_level == slot.party_level
        assert restored.location == slot.location


class TestGameSave:
    """GameSaveのテスト"""
    
    def test_serialization(self):
        """シリアライゼーションのテスト"""
        # テストデータ作成
        party = Party(name="Test Party")
        stats = BaseStats(strength=15, agility=12, intelligence=14, faith=10, luck=13)
        character = Character.create_character("TestHero", "human", "fighter", stats)
        party.add_character(character)
        
        save_slot = SaveSlot(slot_id=1, name="Test", party_name=party.name)
        
        game_save = GameSave(
            save_slot=save_slot,
            party=party,
            game_state={'location': 'town'},
            flags={'tutorial_completed': True}
        )
        
        # 辞書化してから復元
        data = game_save.to_dict()
        restored = GameSave.from_dict(data)
        
        assert restored.save_slot.slot_id == game_save.save_slot.slot_id
        assert restored.party.name == game_save.party.name
        assert restored.game_state['location'] == 'town'
        assert restored.flags['tutorial_completed'] == True