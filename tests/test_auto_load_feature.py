"""自動セーブデータロード機能のテスト"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import tempfile
import os
import json
from datetime import datetime

from src.core.game_manager import GameManager
from src.core.save_manager import SaveManager
from src.character.party import Party


class TestAutoLoadFeature(unittest.TestCase):
    """自動ロード機能のテストクラス"""
    
    def setUp(self):
        """テスト前のセットアップ"""
        self.temp_dir = tempfile.mkdtemp()
        self.saves_dir = os.path.join(self.temp_dir, "saves")
        os.makedirs(self.saves_dir, exist_ok=True)
        
        # モックのセーブマネージャー設定
        self.mock_save_manager = Mock(spec=SaveManager)
        
    def tearDown(self):
        """テスト後のクリーンアップ"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def _create_test_save_data(self, slot_id: int, save_time: str = None):
        """テスト用セーブデータを作成"""
        if save_time is None:
            save_time = datetime.now().isoformat()
            
        save_data = {
            "party": {
                "name": "テストパーティ",
                "members": [
                    {
                        "name": "テストキャラクター",
                        "race": "Human",
                        "job": "Fighter",
                        "level": 5,
                        "hp": 50,
                        "max_hp": 50
                    }
                ]
            },
            "game_state": {
                "location": "overworld",
                "current_dungeon": None,
                "flags": {}
            },
            "metadata": {
                "save_time": save_time,
                "version": "1.0",
                "slot_id": slot_id
            }
        }
        return save_data
    
    def _create_mock_game_manager(self):
        """モックGameManagerを作成"""
        game_manager = Mock()
        game_manager.current_party = None
        game_manager.current_location = "overworld"
        game_manager.save_manager = self.mock_save_manager
        
        # 実際のメソッドを追加
        from src.core.game_manager import GameManager
        game_manager._try_auto_load = GameManager._try_auto_load.__get__(game_manager)
        game_manager.load_game_state = GameManager.load_game_state.__get__(game_manager)
        
        return game_manager
    
    def test_auto_load_with_existing_save(self):
        """セーブデータが存在する場合の自動ロードテスト"""
        # セーブデータを作成
        save_data = self._create_test_save_data(1)
        
        # SaveManagerのモック設定
        self.mock_save_manager.get_save_slots.return_value = [
            {
                'slot_id': 1,
                'save_time': save_data['metadata']['save_time'],
                'party_name': save_data['party']['name']
            }
        ]
        self.mock_save_manager.load_game.return_value = save_data
        
        # GameManagerのモック
        game_manager = self._create_mock_game_manager()
        
        # Party.from_dictをモック
        mock_party = Mock()
        mock_party.name = "テストパーティ"
        
        with patch('src.core.game_manager.Party') as mock_party_class:
            mock_party_class.from_dict.return_value = mock_party
            
            # 自動ロード処理をテスト
            result = game_manager._try_auto_load()
            
            # 期待される結果
            self.assertTrue(result)
            self.mock_save_manager.get_save_slots.assert_called_once()
            self.mock_save_manager.load_game.assert_called_once_with(1)
            self.assertEqual(game_manager.current_party, mock_party)
    
    def test_auto_load_with_no_save(self):
        """セーブデータが存在しない場合のテスト"""
        # SaveManagerのモック設定（セーブデータなし）
        self.mock_save_manager.get_save_slots.return_value = []
        
        # GameManagerのモック
        game_manager = self._create_mock_game_manager()
        
        # 自動ロード処理をテスト
        result = game_manager._try_auto_load()
        
        # 期待される結果
        self.assertFalse(result)
        self.mock_save_manager.get_save_slots.assert_called_once()
        self.mock_save_manager.load_game.assert_not_called()
        self.assertIsNone(game_manager.current_party)
    
    def test_auto_load_with_multiple_saves(self):
        """複数のセーブデータがある場合、最新を自動ロードするテスト"""
        # 複数のセーブデータを作成
        older_time = "2024-01-01T10:00:00"
        newer_time = "2024-01-02T10:00:00"
        
        newer_save = self._create_test_save_data(2, newer_time)
        newer_save['party']['name'] = "最新パーティ"
        
        # SaveManagerのモック設定（新しい順にソート済み）
        self.mock_save_manager.get_save_slots.return_value = [
            {
                'slot_id': 2,
                'save_time': newer_time,
                'party_name': '最新パーティ'
            },
            {
                'slot_id': 1,
                'save_time': older_time,
                'party_name': 'テストパーティ'
            }
        ]
        self.mock_save_manager.load_game.return_value = newer_save
        
        # GameManagerのモック
        game_manager = self._create_mock_game_manager()
        
        # Party.from_dictをモック
        mock_party = Mock()
        mock_party.name = "最新パーティ"
        
        with patch('src.core.game_manager.Party') as mock_party_class:
            mock_party_class.from_dict.return_value = mock_party
            
            # 自動ロード処理をテスト
            result = game_manager._try_auto_load()
            
            # 期待される結果（最新のセーブデータをロード）
            self.assertTrue(result)
            self.mock_save_manager.load_game.assert_called_once_with(2)
            self.assertEqual(game_manager.current_party.name, "最新パーティ")
    
    def test_auto_load_error_handling(self):
        """自動ロード時のエラーハンドリングテスト"""
        # SaveManagerのモック設定（ロード時にエラー）
        self.mock_save_manager.get_save_slots.return_value = [
            {
                'slot_id': 1,
                'save_time': datetime.now().isoformat(),
                'party_name': 'テストパーティ'
            }
        ]
        self.mock_save_manager.load_game.side_effect = Exception("ロードエラー")
        
        # GameManagerのモック
        game_manager = self._create_mock_game_manager()
        
        # 自動ロード処理をテスト
        result = game_manager._try_auto_load()
        
        # 期待される結果（エラー時はFalseを返す）
        self.assertFalse(result)
        self.assertIsNone(game_manager.current_party)
    
    def test_load_game_state_success(self):
        """load_game_stateメソッドの成功テスト"""
        save_data = self._create_test_save_data(1)
        self.mock_save_manager.load_game.return_value = save_data
        
        # GameManagerのモック
        game_manager = self._create_mock_game_manager()
        
        # Party.from_dictをモック
        mock_party = Mock()
        mock_party.name = "テストパーティ"
        
        with patch('src.core.game_manager.Party') as mock_party_class:
            mock_party_class.from_dict.return_value = mock_party
            
            # load_game_state処理をテスト
            result = game_manager.load_game_state(1)
            
            # 期待される結果
            self.assertTrue(result)
            self.mock_save_manager.load_game.assert_called_once_with(1)
            self.assertEqual(game_manager.current_party, mock_party)
            self.assertEqual(game_manager.current_location, "overworld")
    
    def test_load_game_state_error(self):
        """load_game_stateメソッドのエラーハンドリングテスト"""
        self.mock_save_manager.load_game.side_effect = Exception("ロードエラー")
        
        # GameManagerのモック
        game_manager = self._create_mock_game_manager()
        
        # load_game_state処理をテスト
        result = game_manager.load_game_state(1)
        
        # 期待される結果
        self.assertFalse(result)


if __name__ == '__main__':
    unittest.main()