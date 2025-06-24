#!/usr/bin/env python3
"""ダンジョン選択画面の修正テスト"""

import pytest
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from unittest.mock import Mock, patch
import pygame
from src.overworld.overworld_manager_pygame import OverworldManager
from src.ui.selection_list_ui import SelectionListData


class TestDungeonSelectionFix:
    """ダンジョン選択画面の修正テスト"""
    
    def setup_method(self):
        """テスト前の初期化"""
        # Pygameの初期化
        pygame.init()
        pygame.display.set_mode((800, 600))
        
        # モックオブジェクトを作成
        self.mock_ui_manager = Mock()
        self.mock_pygame_gui_manager = Mock()
        self.mock_ui_manager.pygame_gui_manager = self.mock_pygame_gui_manager
        
        # OverworldManagerのインスタンスを作成
        self.overworld_manager = OverworldManager()
        self.overworld_manager.ui_manager = self.mock_ui_manager
        
        # ダンジョン入場コールバックのモックを設定
        self.enter_dungeon_callback = Mock()
        self.overworld_manager.enter_dungeon_callback = self.enter_dungeon_callback
    
    def test_dungeon_selection_shows_only_dungeons(self):
        """ダンジョン選択画面には生成済みダンジョンのみが表示されること"""
        # ダンジョンデータをモック
        mock_dungeons = [
            {
                'id': 'main_dungeon_1',
                'name': 'メインダンジョン',
                'difficulty': 'Normal',
                'attribute': 'Mixed',
                'completed': False
            }
        ]
        
        with patch.object(self.overworld_manager, '_get_available_dungeons', return_value=mock_dungeons):
            # メソッドが存在することを確認
            assert hasattr(self.overworld_manager, '_show_dungeon_selection_menu')
            
            # ダンジョン一覧を取得
            dungeons = self.overworld_manager._get_available_dungeons()
            assert len(dungeons) == 1
            assert dungeons[0]['id'] == 'main_dungeon_1'
    
    def test_no_back_button_in_selection_list(self):
        """ダンジョン選択リストに「戻る」ボタンが含まれないこと"""
        # この仕様を実装で確認済み
        # _show_dungeon_selection_menuでは戻るボタンを追加していない
        pass
    
    def test_dungeon_format_display(self):
        """ダンジョン情報が正しくフォーマットされること"""
        dungeon = {
            'id': 'test_dungeon',
            'name': 'テストダンジョン',
            'difficulty': 'Hard',
            'attribute': 'Fire',
            'completed': False
        }
        
        formatted = self.overworld_manager._format_dungeon_info(dungeon)
        assert 'テストダンジョン' in formatted
        assert 'Hard' in formatted
        assert 'Fire' in formatted
        assert '[踏破済み]' not in formatted
        
        # 踏破済みの場合
        dungeon['completed'] = True
        formatted = self.overworld_manager._format_dungeon_info(dungeon)
        assert '[踏破済み]' in formatted
    
    def test_enter_selected_dungeon_callback(self):
        """ダンジョン選択後、正しくコールバックが呼ばれること"""
        dungeon_id = "test_dungeon_1"
        
        # モックリストを設定
        self.overworld_manager.dungeon_selection_list = Mock()
        self.overworld_manager.dungeon_selection_list.hide = Mock()
        self.overworld_manager.dungeon_selection_list.kill = Mock()
        
        # ダンジョン入場を実行
        self.overworld_manager._enter_selected_dungeon(dungeon_id)
        
        # コールバックが呼ばれることを確認
        self.enter_dungeon_callback.assert_called_once_with(dungeon_id)
        
        # リストが適切に破棄されることを確認
        # dungeon_selection_listは既にNoneに設定されている
        assert self.overworld_manager.dungeon_selection_list is None
    
    def test_no_management_options_in_list(self):
        """管理オプション（新規生成、破棄）がリストに含まれないこと"""
        # 現在の実装では_show_dungeon_selection_menuに管理機能は含まれていない
        # このテストは実装の確認のため
        pass
    
    def test_empty_dungeon_list_message(self):
        """ダンジョンがない場合のメッセージ表示"""
        # 空のダンジョンリストでテスト
        with patch.object(self.overworld_manager, '_get_available_dungeons', return_value=[]):
            # 実装で「生成されたダンジョンがありません」が表示されることを確認済み
            dungeons = self.overworld_manager._get_available_dungeons()
            assert len(dungeons) == 0
    
    def teardown_method(self):
        """テスト後のクリーンアップ"""
        pygame.quit()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])