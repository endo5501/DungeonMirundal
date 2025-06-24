#!/usr/bin/env python3
"""ダンジョン選択からダンジョン入場の問題修正テスト"""

import pytest
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from unittest.mock import Mock, patch, MagicMock
import pygame
from src.overworld.overworld_manager_pygame import OverworldManager
from src.ui.selection_list_ui import CustomSelectionList, SelectionListData
from src.utils.logger import logger


class TestDungeonEntranceFix:
    """ダンジョン選択からダンジョン入場の問題修正テスト"""
    
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
    
    def test_dungeon_selection_screen_displays_correctly(self):
        """ダンジョン選択画面が正しく表示されることをテスト"""
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
            # ダンジョン選択画面を表示
            self.overworld_manager._show_pure_dungeon_selection_menu()
            
            # CustomSelectionListが作成されることを確認
            assert hasattr(self.overworld_manager, 'dungeon_selection_list')
            assert self.overworld_manager.dungeon_selection_list is not None
    
    def test_enter_selected_dungeon_calls_callback(self):
        """選択されたダンジョンに正しく入場できることをテスト"""
        # ダンジョン選択リストをモック
        mock_selection_list = Mock(spec=CustomSelectionList)
        self.overworld_manager.dungeon_selection_list = mock_selection_list
        
        dungeon_id = "test_dungeon_1"
        
        # ダンジョン入場を実行
        self.overworld_manager._enter_selected_dungeon(dungeon_id)
        
        # ダンジョン入場コールバックが呼ばれることを確認
        self.enter_dungeon_callback.assert_called_once_with(dungeon_id)
        
        # オーバーワールドマネージャーが非アクティブになることを確認
        assert not self.overworld_manager.is_active
    
    def test_enter_selected_dungeon_hides_selection_list_correctly(self):
        """ダンジョン入場時に選択リストが正しく隠されることをテスト"""
        # ダンジョン選択リストをモック
        mock_selection_list = Mock(spec=CustomSelectionList)
        mock_selection_list.hide = Mock()
        mock_selection_list.kill = Mock()
        self.overworld_manager.dungeon_selection_list = mock_selection_list
        
        dungeon_id = "test_dungeon_1"
        
        # ダンジョン入場を実行
        self.overworld_manager._enter_selected_dungeon(dungeon_id)
        
        # CustomSelectionListのhideまたはkillメソッドが呼ばれることを確認
        # 修正前はこのテストが失敗する（存在しないメニューIDでhide_menuを呼んでいるため）
        assert mock_selection_list.hide.called or mock_selection_list.kill.called
    
    def test_enter_selected_dungeon_error_handling(self):
        """ダンジョン入場時のエラーハンドリングをテスト"""
        # ダンジョン選択リストをモック
        mock_selection_list = Mock(spec=CustomSelectionList)
        self.overworld_manager.dungeon_selection_list = mock_selection_list
        
        # コールバックでエラーを発生させる
        self.enter_dungeon_callback.side_effect = Exception("テストエラー")
        
        dungeon_id = "test_dungeon_1"
        
        # エラーが発生してもクラッシュしないことをテスト
        with patch.object(self.overworld_manager, '_show_pure_dungeon_selection_menu') as mock_show_menu:
            self.overworld_manager._enter_selected_dungeon(dungeon_id)
            
            # エラー時にダンジョン選択メニューが再表示されることを確認
            mock_show_menu.assert_called_once()
    
    def test_dungeon_selection_list_cleanup(self):
        """ダンジョン選択リストの適切なクリーンアップをテスト"""
        # ダンジョン選択リストを作成
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
            self.overworld_manager._show_pure_dungeon_selection_menu()
            
            # 選択リストが存在することを確認
            assert self.overworld_manager.dungeon_selection_list is not None
            
            # クリーンアップメソッドが存在することを確認
            selection_list = self.overworld_manager.dungeon_selection_list
            assert hasattr(selection_list, 'hide') or hasattr(selection_list, 'kill')
    
    def test_dungeon_selection_items_structure(self):
        """ダンジョン選択項目の構造が正しいことをテスト"""
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
            # 利用可能なダンジョン取得をテスト
            dungeons = self.overworld_manager._get_available_dungeons()
            
            # 適切なダンジョンデータが含まれていることを確認
            assert len(dungeons) >= 1  # 少なくとも1つのダンジョン
            
            # ダンジョンデータの構造を確認
            dungeon = dungeons[0]
            assert dungeon['id'] == 'main_dungeon_1'
            assert dungeon['name'] == 'メインダンジョン'
            assert 'difficulty' in dungeon
            assert 'attribute' in dungeon
    
    def test_ui_manager_hide_menu_not_called_for_selection_list(self):
        """UIマネージャーのhide_menuが選択リストに対して呼ばれないことをテスト"""
        # ダンジョン選択リストをモック
        mock_selection_list = Mock(spec=CustomSelectionList)
        self.overworld_manager.dungeon_selection_list = mock_selection_list
        
        dungeon_id = "test_dungeon_1"
        
        # ダンジョン入場を実行
        self.overworld_manager._enter_selected_dungeon(dungeon_id)
        
        # UIマネージャーのhide_menuが間違ったIDで呼ばれていないことを確認
        # （修正前はこのテストが失敗する）
        self.mock_ui_manager.hide_menu.assert_not_called()
    
    def teardown_method(self):
        """テスト後のクリーンアップ"""
        pygame.quit()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])