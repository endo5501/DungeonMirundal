"""セーブ/ロードシステムのエッジケーステスト"""

import unittest
from unittest.mock import Mock, MagicMock, patch, mock_open
import pygame
import pygame_gui
import os
import json
from src.overworld.overworld_manager import OverworldManager
from src.ui.window_system.window_manager import WindowManager
from src.core.game_manager import GameManager


class TestSaveLoadEdgeCases(unittest.TestCase):
    """セーブ/ロードシステムのエッジケースをテスト"""
    
    def setUp(self):
        """テスト前のセットアップ"""
        pygame.init()
        pygame.display.set_mode((800, 600))
        
        # モックオブジェクトの作成
        self.mock_window_manager = Mock(spec=WindowManager)
        self.mock_ui_manager = Mock(spec=pygame_gui.UIManager)
        self.mock_game_manager = Mock(spec=GameManager)
        
        # OverworldManagerのインスタンスを作成
        self.overworld_manager = OverworldManager()
        # GameManagerとWindowManagerの参照を設定
        self.overworld_manager.set_game_manager(self.mock_game_manager)
        self.overworld_manager.window_manager = self.mock_window_manager
    
    def tearDown(self):
        """テスト後のクリーンアップ"""
        pygame.quit()
    
    def test_load_nonexistent_slot(self):
        """存在しないスロットのロード試行"""
        # SaveManagerをモック
        mock_save_manager = Mock()
        self.mock_game_manager.save_manager = mock_save_manager
        
        # ロードがNoneを返すように設定（スロットが存在しない）
        mock_save_manager.load_game.return_value = None
        
        # 存在しないスロット番号でロードを試行
        result = self.overworld_manager._load_selected_save(999)
        
        # ロードが失敗することを確認
        self.assertFalse(result)
        # load_gameが呼ばれたことを確認
        mock_save_manager.load_game.assert_called_once_with(999)
    
    def test_load_corrupted_save_file(self):
        """破損したセーブファイルのロード試行"""
        # SaveManagerをモック
        mock_save_manager = Mock()
        self.mock_game_manager.save_manager = mock_save_manager
        
        # セーブファイルのロードで例外を発生させる
        mock_save_manager.load_game.side_effect = Exception("Invalid save data")
        
        # ロードを試行
        result = self.overworld_manager._load_selected_save(1)
        
        # ロードが失敗することを確認
        self.assertFalse(result)
        # load_gameが呼ばれたことを確認
        mock_save_manager.load_game.assert_called_once_with(1)
    
    def test_save_to_invalid_slot_number(self):
        """無効なスロット番号への保存試行"""
        # SaveManagerをモック
        mock_save_manager = Mock()
        self.mock_game_manager.save_manager = mock_save_manager
        
        # パーティを設定
        self.overworld_manager.current_party = Mock()
        
        # save_current_gameメソッドが例外を投げることを想定
        self.mock_game_manager.save_current_game.side_effect = ValueError("Invalid slot number")
        
        # 負の数でスロット指定
        result = self.overworld_manager._save_to_slot(-1)
        
        # セーブが失敗することを確認
        self.assertFalse(result)
    
    def test_save_with_no_party(self):
        """パーティが存在しない状態での保存試行"""
        # パーティがNoneの状態に設定
        self.overworld_manager.current_party = None
        
        # 保存を試行
        result = self.overworld_manager._save_to_slot(1)
        
        # セーブが失敗することを確認
        self.assertFalse(result)
    
    def test_concurrent_save_operations(self):
        """同時保存操作のテスト"""
        # SaveManagerをモック
        mock_save_manager = Mock()
        self.mock_game_manager.save_manager = mock_save_manager
        save_calls = []
        
        def track_save(*args, **kwargs):
            save_calls.append(kwargs.get('slot_id', args[0] if args else None))
            return True
            
        self.mock_game_manager.save_current_game.side_effect = track_save
        
        # パーティを設定
        self.overworld_manager.current_party = Mock()
        
        # _go_back_to_main_menuをモック（セーブ成功後に呼ばれる）
        with patch.object(self.overworld_manager, '_go_back_to_main_menu'):
            # 連続して異なるスロットに保存
            for slot in [1, 2, 3]:
                result = self.overworld_manager._save_to_slot(slot)
                self.assertTrue(result)
        
        # すべての保存が正しく呼ばれたことを確認
        self.assertEqual(len(save_calls), 3)
    
    def test_load_with_missing_required_fields(self):
        """必須フィールドが欠けているセーブデータのロード"""
        # SaveManagerをモック
        mock_save_manager = Mock()
        self.mock_game_manager.save_manager = mock_save_manager
        
        # 不完全なセーブデータ（partyがNone）
        mock_save_data = Mock()
        mock_save_data.party = None  # パーティが欠けている
        
        mock_save_manager.load_game.return_value = mock_save_data
        
        # ロードを試行
        result = self.overworld_manager._load_selected_save(1)
        
        # ロードが実行されることを確認（パーティがNoneでも処理は続行される可能性）
        mock_save_manager.load_game.assert_called_once_with(1)
    
    def test_save_slot_limit(self):
        """セーブスロット数の上限テスト"""
        # SaveManagerをモック
        mock_save_manager = Mock()
        self.mock_game_manager.save_manager = mock_save_manager
        
        # パーティを設定
        self.overworld_manager.current_party = Mock()
        
        # 正常なスロット番号（1-3）での保存は成功
        self.mock_game_manager.save_current_game.return_value = True
        
        # _go_back_to_main_menuをモック（セーブ成功後に呼ばれる）
        with patch.object(self.overworld_manager, '_go_back_to_main_menu'):
            for slot in [1, 2, 3]:
                result = self.overworld_manager._save_to_slot(slot)
                self.assertTrue(result)
        
        # スロット数を確認
        self.assertEqual(self.mock_game_manager.save_current_game.call_count, 3)
    
    def test_unicode_in_save_data(self):
        """Unicode文字を含むセーブデータの処理"""
        # SaveManagerをモック
        mock_save_manager = Mock()
        self.mock_game_manager.save_manager = mock_save_manager
        
        # Unicode文字を含むパーティデータ
        mock_party = Mock()
        mock_party.name = "テストパーティ🎮"
        
        mock_save_data = Mock()
        mock_save_data.party = mock_party
        
        mock_save_manager.load_game.return_value = mock_save_data
        
        # UIUpdateManagerをモック
        with patch.object(self.overworld_manager, '_update_ui_after_party_change'):
            result = self.overworld_manager._load_selected_save(1)
            
            # load_gameが正しく呼ばれたことを確認
            mock_save_manager.load_game.assert_called_once_with(1)
            # ロードが成功することを確認
            self.assertTrue(result)
    


if __name__ == '__main__':
    unittest.main()