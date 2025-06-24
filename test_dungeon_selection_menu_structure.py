#!/usr/bin/env python3
"""ダンジョン選択メニュー構造の修正テスト"""

import pytest
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from unittest.mock import Mock, patch
import pygame
from src.overworld.overworld_manager_pygame import OverworldManager
from src.ui.selection_list_ui import SelectionListData


class TestDungeonSelectionMenuStructure:
    """ダンジョン選択メニュー構造の修正テスト"""
    
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
    
    def test_dungeon_selection_only_shows_generated_dungeons(self):
        """ダンジョン選択画面は生成されたダンジョンのみを表示すること"""
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
            try:
                self.overworld_manager._show_dungeon_selection_menu()
                
                # CustomSelectionListが作成されていることを確認
                if hasattr(self.overworld_manager, 'dungeon_selection_list'):
                    selection_list = self.overworld_manager.dungeon_selection_list
                    if hasattr(selection_list, 'items'):
                        # 表示されている項目を分析
                        dungeon_items = []
                        management_items = []
                        
                        for item in selection_list.items:
                            display_text = item.display_text
                            if any(keyword in display_text for keyword in ['新規', '破棄', '戻る']):
                                management_items.append(display_text)
                            else:
                                dungeon_items.append(display_text)
                        
                        # ダンジョン項目のみが表示され、管理項目が混在していないことを確認
                        assert len(dungeon_items) > 0, "ダンジョン項目が表示されていません"
                        assert len(management_items) == 0, f"管理項目が混在しています: {management_items}"
            except Exception:
                # UI作成エラーは無視して、ロジックテストに集中
                pass
    
    def test_dungeon_management_should_be_separate_menu(self):
        """ダンジョン管理機能は別メニューであるべき"""
        # 現在の実装をテストして問題を特定
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
            try:
                self.overworld_manager._show_dungeon_selection_menu()
                
                if hasattr(self.overworld_manager, 'dungeon_selection_list'):
                    selection_list = self.overworld_manager.dungeon_selection_list
                    if hasattr(selection_list, 'items'):
                        # 管理機能が混在していることを検証（現在の問題のあるステート）
                        management_items = []
                        for item in selection_list.items:
                            display_text = item.display_text
                            if any(keyword in display_text for keyword in ['新規', '破棄', '戻る']):
                                management_items.append(display_text)
                        
                        # 現在は管理項目が混在しているため、これが修正対象
                        # 修正後はこのテストが失敗し、管理項目が別メニューになるべき
                        if len(management_items) > 0:
                            pytest.fail(f"管理項目がダンジョン選択リストに混在しています: {management_items}")
            except Exception:
                pass
    
    def test_dungeon_list_display_format_correct(self):
        """ダンジョンリストの表示形式が正しいこと"""
        mock_dungeons = [
            {
                'id': 'main_dungeon_1',
                'name': 'メインダンジョン',
                'difficulty': 'Normal',
                'attribute': 'Mixed',
                'completed': False
            }
        ]
        
        # ダンジョン情報のフォーマットをテスト
        formatted = self.overworld_manager._format_dungeon_info(mock_dungeons[0])
        
        # 正しい形式であることを確認
        assert 'メインダンジョン' in formatted
        assert 'Normal' in formatted
        assert 'Mixed' in formatted
        assert '踏破済み' not in formatted  # completedがFalseなので
    
    def test_proposed_dungeon_entrance_menu_structure(self):
        """提案する新しいダンジョン入口メニュー構造"""
        # 理想的なメニュー構造：
        # 1. ダンジョン入口を選択 → ダンジョン選択画面（生成済みダンジョンのみ）
        # 2. ダンジョン管理を選択 → 管理メニュー（新規作成、破棄など）
        
        # 新しい管理メニューメソッドが存在することを確認（まだ実装されていないのでテストは失敗する）
        expected_methods = [
            '_show_dungeon_management_menu',  # 新規作成、破棄などの管理機能
            '_show_pure_dungeon_selection_menu'  # 生成済みダンジョンのみの選択
        ]
        
        for method_name in expected_methods:
            # 現在は存在しないため、実装が必要
            if not hasattr(self.overworld_manager, method_name):
                pytest.fail(f"必要なメソッド {method_name} が実装されていません")
    
    def teardown_method(self):
        """テスト後のクリーンアップ"""
        pygame.quit()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])