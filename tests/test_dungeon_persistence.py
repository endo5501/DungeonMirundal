"""ダンジョン永続化の包括的テスト

このテストスイートは、ダンジョン作成からセーブ・ロードまでの
完全なフローを検証し、GameStateManagerの問題も検出できるようにする。
"""

import pytest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, MagicMock, patch
from typing import Dict, Any, List

from src.core.game_manager import GameManager
from src.core.save_manager import SaveManager, GameSave, SaveSlot
from src.core.state.game_state_manager import GameStateManager
from src.character.party import Party
from src.character.character import Character
from src.character.stats import BaseStats


class TestDungeonPersistence:
    """ダンジョン永続化の包括的テスト"""
    
    def setup_method(self):
        """各テストメソッドの前に実行"""
        # 一時ディレクトリの作成
        self.temp_dir = tempfile.TemporaryDirectory()
        
        # SaveManagerのセットアップ
        self.save_manager = SaveManager(self.temp_dir.name)
        
        # GameManagerのセットアップ
        self.game_manager = GameManager()
        self.game_manager.save_manager = self.save_manager
        test_party = self._create_test_party()
        self.game_manager.save_manager.current_save = GameSave(
            save_slot=SaveSlot(slot_id=1, name="Test", party_name=test_party.name),
            party=test_party,
            dungeon_list=[]
        )
        self.game_manager.current_party = self.game_manager.save_manager.current_save.party
        
        # GameStateManagerのセットアップ
        self.game_state_manager = GameStateManager()
        self.game_state_manager.save_manager = self.save_manager
        self.game_state_manager.current_party = self.game_manager.current_party
    
    def teardown_method(self):
        """各テストメソッドの後に実行"""
        self.temp_dir.cleanup()
    
    def _create_test_party(self) -> Party:
        """テスト用パーティの作成"""
        party = Party(name="Test Party")
        stats = BaseStats(strength=15, agility=12, intelligence=14, faith=10, luck=13)
        character = Character.create_character("TestHero", "human", "fighter", stats)
        party.add_character(character)
        party.add_gold(100)
        return party
    
    def _create_test_dungeon(self, dungeon_id: str = "test_dungeon_001") -> Dict[str, Any]:
        """テスト用ダンジョン情報を作成"""
        return {
            'id': dungeon_id,
            'hash_value': dungeon_id,  # GameManagerが使用するフィールド
            'name': f'Test Dungeon {dungeon_id}',
            'difficulty': 5,
            'floors': 10,
            'discovered': True,
            'explored_floors': [],
            'hash': 'test_hash_12345'
        }
    
    def test_add_dungeon_to_list_saves_automatically(self):
        """add_dungeon_to_listが自動的にセーブすることを確認"""
        # セーブメソッドをモック
        with patch.object(self.game_manager, 'save_current_game') as mock_save:
            mock_save.return_value = True
            
            # ダンジョン追加
            dungeon_info = self._create_test_dungeon()
            self.game_manager.add_dungeon_to_list(dungeon_info)
            
            # セーブが呼ばれたことを確認
            mock_save.assert_called_once()
            
            # ダンジョンがリストに追加されたことを確認
            assert len(self.save_manager.current_save.dungeon_list) == 1
            assert self.save_manager.current_save.dungeon_list[0]['hash_value'] == 'test_dungeon_001'
    
    def test_remove_dungeon_from_list_saves_automatically(self):
        """remove_dungeon_from_listが自動的にセーブすることを確認"""
        # まずダンジョンを追加
        dungeon_info = self._create_test_dungeon()
        self.save_manager.current_save.dungeon_list.append(dungeon_info)
        
        # セーブメソッドをモック
        with patch.object(self.game_manager, 'save_current_game') as mock_save:
            mock_save.return_value = True
            
            # ダンジョン削除（hash_valueを使用）
            self.game_manager.remove_dungeon_from_list('test_dungeon_001')
            
            # セーブが呼ばれたことを確認
            mock_save.assert_called_once()
            
            # ダンジョンがリストから削除されたことを確認
            assert len(self.save_manager.current_save.dungeon_list) == 0
    
    def test_game_state_manager_gets_dungeon_list_from_save_manager(self):
        """GameStateManagerがSaveManagerからダンジョンリストを取得することを確認"""
        # ダンジョンをセーブデータに追加
        dungeon1 = self._create_test_dungeon("dungeon1")
        dungeon2 = self._create_test_dungeon("dungeon2")
        self.save_manager.current_save.dungeon_list = [dungeon1, dungeon2]
        
        # GameStateManagerからダンジョンリストを取得
        dungeon_list = self.game_state_manager._get_dungeon_list()
        
        # 正しく取得できることを確認
        assert len(dungeon_list) == 2
        assert dungeon_list[0]['hash_value'] == 'dungeon1'
        assert dungeon_list[1]['hash_value'] == 'dungeon2'
    
    def test_game_state_manager_handles_missing_save_manager(self):
        """GameStateManagerがSaveManagerが無い場合を正しく処理することを確認"""
        # SaveManagerをNoneに設定
        self.game_state_manager.save_manager = None
        
        # ダンジョンリストを取得
        dungeon_list = self.game_state_manager._get_dungeon_list()
        
        # 空のリストが返されることを確認
        assert dungeon_list == []
    
    def test_game_state_manager_handles_missing_current_save(self):
        """GameStateManagerがcurrent_saveが無い場合を正しく処理することを確認"""
        # current_saveをNoneに設定
        self.game_state_manager.save_manager.current_save = None
        
        # ダンジョンリストを取得
        dungeon_list = self.game_state_manager._get_dungeon_list()
        
        # 空のリストが返されることを確認
        assert dungeon_list == []
    
    def test_save_and_load_dungeon_list(self):
        """ダンジョンリストのセーブとロードが正しく動作することを確認"""
        # ダンジョンを追加
        dungeon1 = self._create_test_dungeon("dungeon1")
        dungeon2 = self._create_test_dungeon("dungeon2")
        
        # セーブデータに追加
        self.save_manager.current_save.dungeon_list = [dungeon1, dungeon2]
        
        # セーブ実行
        success = self.save_manager.save_game(
            party=self.game_manager.current_party,
            slot_id=1,
            save_name="Test Save",
            dungeon_list=[dungeon1, dungeon2]
        )
        assert success == True
        
        # ロード実行
        loaded_save = self.save_manager.load_game(1)
        assert loaded_save is not None
        assert len(loaded_save.dungeon_list) == 2
        assert loaded_save.dungeon_list[0]['hash_value'] == 'dungeon1'
        assert loaded_save.dungeon_list[1]['hash_value'] == 'dungeon2'
    
    def test_game_state_manager_save_includes_dungeon_list(self):
        """GameStateManagerのsave_current_gameがダンジョンリストを含むことを確認"""
        # ダンジョンを追加
        dungeon_info = self._create_test_dungeon()
        self.save_manager.current_save.dungeon_list = [dungeon_info]
        
        # セーブ実行
        with patch.object(self.save_manager, 'save_game') as mock_save:
            mock_save.return_value = True
            
            success = self.game_state_manager.save_current_game(1, "Test Save")
            
            # save_gameが正しい引数で呼ばれたことを確認
            mock_save.assert_called_once()
            call_args = mock_save.call_args
            
            # dungeon_listが渡されていることを確認
            assert 'dungeon_list' in call_args.kwargs
            assert len(call_args.kwargs['dungeon_list']) == 1
            assert call_args.kwargs['dungeon_list'][0]['hash_value'] == 'test_dungeon_001'
    
    def test_full_dungeon_persistence_flow(self):
        """ダンジョン作成からセーブ・ロードまでの完全なフローをテスト"""
        # 1. 初期状態確認
        assert len(self.save_manager.current_save.dungeon_list) == 0
        
        # 2. ダンジョン追加（自動セーブをモック）
        with patch.object(self.game_manager, 'save_current_game') as mock_save:
            mock_save.return_value = True
            
            dungeon1 = self._create_test_dungeon("dungeon1")
            self.game_manager.add_dungeon_to_list(dungeon1)
            
            dungeon2 = self._create_test_dungeon("dungeon2")
            self.game_manager.add_dungeon_to_list(dungeon2)
        
        # 3. メモリ上にダンジョンが存在することを確認
        assert len(self.save_manager.current_save.dungeon_list) == 2
        
        # 4. GameStateManager経由でセーブ（実際のファイル保存）
        success = self.game_state_manager.save_current_game(1, "Test Save")
        assert success == True
        
        # 5. 新しいインスタンスでロード
        new_save_manager = SaveManager(self.temp_dir.name)
        loaded_save = new_save_manager.load_game(1)
        
        # 6. ダンジョンが正しくロードされたことを確認
        assert loaded_save is not None
        assert len(loaded_save.dungeon_list) == 2
        assert loaded_save.dungeon_list[0]['hash_value'] == 'dungeon1'
        assert loaded_save.dungeon_list[1]['hash_value'] == 'dungeon2'
        
        # 7. 新しいGameStateManagerでもダンジョンリストが取得できることを確認
        new_game_state_manager = GameStateManager()
        new_game_state_manager.save_manager = new_save_manager
        new_game_state_manager.save_manager.current_save = loaded_save
        
        dungeon_list = new_game_state_manager._get_dungeon_list()
        assert len(dungeon_list) == 2
        assert dungeon_list[0]['hash_value'] == 'dungeon1'
        assert dungeon_list[1]['hash_value'] == 'dungeon2'


class TestDungeonManagerIntegration:
    """DungeonManagerとの統合テスト（実際のAPIに基づく）"""
    
    def setup_method(self):
        """各テストメソッドの前に実行"""
        self.temp_dir = tempfile.TemporaryDirectory()
        
        # 統合環境のセットアップ
        from src.dungeon.dungeon_manager import DungeonManager
        
        self.save_manager = SaveManager(self.temp_dir.name)
        self.game_manager = GameManager()
        self.game_manager.save_manager = self.save_manager
        
        self.dungeon_manager = DungeonManager()
        
        # テストパーティ作成
        test_party = self._create_test_party()
        self.game_manager.save_manager.current_save = GameSave(
            save_slot=SaveSlot(slot_id=1, name="Test", party_name=test_party.name),
            party=test_party,
            dungeon_list=[]
        )
        self.game_manager.current_party = self.game_manager.save_manager.current_save.party
    
    def teardown_method(self):
        """各テストメソッドの後に実行"""
        self.temp_dir.cleanup()
    
    def _create_test_party(self) -> Party:
        """テスト用パーティの作成"""
        party = Party(name="Test Party")
        stats = BaseStats(strength=15, agility=12, intelligence=14, faith=10, luck=13)
        character = Character.create_character("TestHero", "human", "fighter", stats)
        party.add_character(character)
        return party
    
    def test_dungeon_creation_and_manual_integration(self):
        """DungeonManager経由でのダンジョン作成と手動統合をテスト"""
        # GameManagerのsave_current_gameをモック（実際のファイル保存はスキップ）
        with patch.object(self.game_manager, 'save_current_game') as mock_save:
            mock_save.return_value = True
            
            # 1. DungeonManagerでダンジョンを作成（実際のAPIを使用）
            test_dungeon_id = "test_dungeon_001"
            test_seed = "test_seed"
            dungeon_state = self.dungeon_manager.create_dungeon(test_dungeon_id, test_seed)
            
            # ダンジョンが正常に作成されたことを確認
            assert dungeon_state is not None
            assert dungeon_state.dungeon_id == test_dungeon_id
            assert dungeon_state.seed == test_seed
            
            # 2. ダンジョン情報をGameManagerに手動で統合（実際のワークフローを模擬）
            dungeon_info = {
                'id': dungeon_state.dungeon_id,
                'hash_value': dungeon_state.dungeon_id,  # GameManagerが期待するフォーマット
                'name': f'Test Dungeon {dungeon_state.dungeon_id}',
                'difficulty': 5,
                'floors': 10,
                'discovered': True,
                'explored_floors': [],
                'seed': dungeon_state.seed
            }
            
            # 3. GameManagerにダンジョンを追加（自動セーブがトリガーされる）
            self.game_manager.add_dungeon_to_list(dungeon_info)
            
            # 4. 自動セーブが呼ばれたことを確認
            mock_save.assert_called_once()
            
            # 5. ダンジョンリストに追加されたことを確認
            dungeon_list = self.game_manager.save_manager.current_save.dungeon_list
            assert len(dungeon_list) == 1
            assert dungeon_list[0]['hash_value'] == test_dungeon_id
            assert dungeon_list[0]['seed'] == test_seed
    
    def test_dungeon_creation_workflow_with_save_load(self):
        """ダンジョン作成→統合→セーブ→ロードの完全ワークフローをテスト"""
        # 1. ダンジョンを作成
        test_dungeon_id = "workflow_test_dungeon"
        test_seed = "workflow_seed"
        dungeon_state = self.dungeon_manager.create_dungeon(test_dungeon_id, test_seed)
        
        # 2. ダンジョン情報を構築
        dungeon_info = {
            'id': dungeon_state.dungeon_id,
            'hash_value': dungeon_state.dungeon_id,
            'name': f'Workflow Test Dungeon',
            'difficulty': 8,
            'floors': 15,
            'discovered': True,
            'explored_floors': [1, 2],  # 探索済みフロア
            'seed': dungeon_state.seed
        }
        
        # 3. GameManagerに追加（自動セーブを含む）
        self.game_manager.add_dungeon_to_list(dungeon_info)
        
        # 4. GameStateManagerを使用してセーブを実行
        from src.core.state.game_state_manager import GameStateManager
        game_state_manager = GameStateManager()
        game_state_manager.save_manager = self.save_manager
        game_state_manager.current_party = self.game_manager.current_party
        
        save_success = game_state_manager.save_current_game(1, "Integration Test Save")
        assert save_success == True
        
        # 5. 新しいSaveManagerでロード
        new_save_manager = SaveManager(self.temp_dir.name)
        loaded_save = new_save_manager.load_game(1)
        
        # 6. ダンジョンが正しくロードされたことを確認
        assert loaded_save is not None
        assert len(loaded_save.dungeon_list) == 1
        loaded_dungeon = loaded_save.dungeon_list[0]
        assert loaded_dungeon['hash_value'] == test_dungeon_id
        assert loaded_dungeon['seed'] == test_seed
        assert loaded_dungeon['difficulty'] == 8
        assert loaded_dungeon['floors'] == 15
        assert loaded_dungeon['explored_floors'] == [1, 2]
        
        # 7. 新しいDungeonManagerで同じダンジョンを再作成できることを確認
        from src.dungeon.dungeon_manager import DungeonManager
        new_dungeon_manager = DungeonManager()
        recreated_dungeon = new_dungeon_manager.create_dungeon(test_dungeon_id, test_seed)
        assert recreated_dungeon.dungeon_id == test_dungeon_id
        assert recreated_dungeon.seed == test_seed