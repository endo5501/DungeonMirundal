"""
修正されたCustomSelectionListの動作検証テスト
"""

import pytest
import pygame
from unittest.mock import Mock, patch
import pygame_gui

from src.ui.selection_list_ui import CustomSelectionList, SelectionListData


class TestCustomSelectionListFixVerification:
    """修正されたCustomSelectionListの検証テストクラス"""
    
    @pytest.fixture
    def pygame_setup(self):
        """pygame初期化"""
        pygame.init()
        screen = pygame.display.set_mode((800, 600))
        yield screen
        pygame.quit()
    
    @pytest.fixture
    def pygame_gui_manager(self, pygame_setup):
        """pygame_gui.UIManager作成"""
        screen = pygame_setup
        return pygame_gui.UIManager((screen.get_width(), screen.get_height()))
    
    def test_customselectionlist_with_valid_pygame_gui_manager(self, pygame_gui_manager):
        """修正後：有効なpygame_gui.UIManagerでCustomSelectionListが正常動作することを確認"""
        list_rect = pygame.Rect(100, 100, 600, 500)
        
        # 修正後の動作：正常に作成される
        selection_list = CustomSelectionList(
            relative_rect=list_rect,
            manager=pygame_gui_manager,
            title="修正後テストリスト"
        )
        
        assert selection_list is not None
        assert selection_list.manager == pygame_gui_manager
        assert selection_list.panel is not None
        
        # アイテム追加テスト
        test_item = SelectionListData(
            display_text="テストアイテム",
            data={"id": "test"},
            callback=lambda: print("テストアイテム選択")
        )
        selection_list.add_item(test_item)
        
        assert len(selection_list.items) == 1
        assert selection_list.items[0].display_text == "テストアイテム"
        
        # クリーンアップ
        selection_list.kill()
    
    def test_customselectionlist_with_invalid_manager_falls_back(self, pygame_setup):
        """無効なUIManagerでフォールバック実装に切り替わることを確認"""
        list_rect = pygame.Rect(100, 100, 600, 500)
        
        # get_sprite_groupメソッドを持たない疑似UIManager
        fake_manager = Mock()
        fake_manager.get_sprite_group = None  # メソッドが存在しない
        
        # フォールバック実装が使用される
        selection_list = CustomSelectionList(
            relative_rect=list_rect,
            manager=fake_manager,
            title="フォールバックテストリスト"
        )
        
        assert selection_list is not None
        assert selection_list.manager == fake_manager
        assert selection_list.panel is None  # フォールバックモード
        
        # アイテム追加は動作する
        test_item = SelectionListData(
            display_text="フォールバックアイテム",
            data={"id": "fallback"}
        )
        selection_list.add_item(test_item)
        
        assert len(selection_list.items) == 1
        
        # クリーンアップ
        selection_list.kill()
    
    def test_customselectionlist_handles_creation_error_gracefully(self, pygame_setup):
        """UI作成エラーが発生した場合のグレースフル処理を確認"""
        list_rect = pygame.Rect(100, 100, 600, 500)
        
        # get_sprite_groupメソッドはあるが、UIPanel作成でエラーが発生するマネージャー
        error_manager = Mock()
        error_manager.get_sprite_group = Mock(side_effect=Exception("UI作成エラー"))
        
        # エラーが発生してもフォールバックに切り替わる
        selection_list = CustomSelectionList(
            relative_rect=list_rect,
            manager=error_manager,
            title="エラーハンドリングテスト"
        )
        
        assert selection_list is not None
        assert selection_list.panel is None  # フォールバックモード
        
        # 基本機能は動作する
        test_item = SelectionListData(display_text="エラー後アイテム")
        selection_list.add_item(test_item)
        assert len(selection_list.items) == 1
        
        # クリーンアップ
        selection_list.kill()
    
    def test_customselectionlist_show_hide_kill_with_fallback(self, pygame_setup):
        """フォールバックモードでのshow/hide/killメソッドの動作確認"""
        list_rect = pygame.Rect(100, 100, 600, 500)
        fake_manager = Mock()
        
        selection_list = CustomSelectionList(
            relative_rect=list_rect,
            manager=fake_manager,
            title="フォールバック動作テスト"
        )
        
        # フォールバックモードではエラーが発生せずに動作する
        selection_list.show()  # エラーが発生しない
        selection_list.hide()  # エラーが発生しない
        selection_list.kill()  # エラーが発生しない
        
        # 状態確認
        assert selection_list.panel is None
        assert selection_list.selection_list is None
    
    def test_dungeon_entrance_scenario_with_fixed_customselectionlist(self, pygame_gui_manager):
        """修正後のダンジョン入口シナリオテスト"""
        
        # OverworldManagerの_show_dungeon_selection_menuシナリオを模擬
        from src.overworld.overworld_manager_pygame import DUNGEON_SELECTION_RECT_X, DUNGEON_SELECTION_RECT_Y, DUNGEON_SELECTION_RECT_WIDTH, DUNGEON_SELECTION_RECT_HEIGHT
        
        list_rect = pygame.Rect(DUNGEON_SELECTION_RECT_X, DUNGEON_SELECTION_RECT_Y, DUNGEON_SELECTION_RECT_WIDTH, DUNGEON_SELECTION_RECT_HEIGHT)
        
        # ダンジョン選択リスト作成（修正後の実装）
        dungeon_selection_list = CustomSelectionList(
            relative_rect=list_rect,
            manager=pygame_gui_manager,
            title="ダンジョン選択"
        )
        
        assert dungeon_selection_list is not None
        assert dungeon_selection_list.panel is not None
        
        # ダンジョンデータ追加
        test_dungeon = {
            "id": "main_dungeon",
            "name": "メインダンジョン",
            "difficulty": "Normal", 
            "attribute": "Mixed",
            "completed": False,
            "hash": "default"
        }
        
        dungeon_info = f"{test_dungeon['name']} - {test_dungeon['difficulty']} ({test_dungeon['attribute']})"
        
        def create_callback(dungeon_id):
            def callback():
                print(f"ダンジョン {dungeon_id} に入場")
            return callback
        
        dungeon_data = SelectionListData(
            display_text=dungeon_info,
            data=test_dungeon,
            callback=create_callback(test_dungeon['id'])
        )
        
        dungeon_selection_list.add_item(dungeon_data)
        
        # 検証
        assert len(dungeon_selection_list.items) == 1
        assert dungeon_selection_list.items[0].display_text == dungeon_info
        assert dungeon_selection_list.items[0].data == test_dungeon
        assert dungeon_selection_list.items[0].callback is not None
        
        # 表示テスト
        dungeon_selection_list.show()
        
        # クリーンアップ
        dungeon_selection_list.kill()
    
    def test_overworld_manager_integration_after_fix(self, pygame_gui_manager):
        """修正後のOverworldManager統合テスト"""
        from src.overworld.overworld_manager_pygame import OverworldManager
        
        manager = OverworldManager()
        manager.set_ui_manager(pygame_gui_manager)
        
        # 修正後はエラーが発生しない
        try:
            manager._show_dungeon_selection_menu()
            
            # ダンジョン選択リストが作成されている
            assert manager.dungeon_selection_list is not None
            
            # クリーンアップ
            if manager.dungeon_selection_list:
                manager.dungeon_selection_list.kill()
                manager.dungeon_selection_list = None
                
        except Exception as e:
            pytest.fail(f"修正後のダンジョン選択メニューでエラー発生: {e}")