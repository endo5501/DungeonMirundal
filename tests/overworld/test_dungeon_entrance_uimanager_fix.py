"""
ダンジョン入口UIManager型混同問題の修正テスト

pygame_gui.UIManagerと独自UIManagerクラスの混同によるエラーを修正する。
"""

import pytest
import pygame
from unittest.mock import Mock, patch, MagicMock
import pygame_gui

from src.overworld.overworld_manager_pygame import OverworldManager
from src.ui.base_ui_pygame import UIManager as BaseUIManager
from src.ui.character_status_bar import CharacterStatusBar, create_character_status_bar


class TestDungeonEntranceUIManagerFix:
    """ダンジョン入口UIManager型修正テストクラス"""
    
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
    
    @pytest.fixture
    def base_ui_manager(self, pygame_setup):
        """BaseUIManager作成"""
        screen = pygame_setup
        return BaseUIManager(screen)
    
    def test_pygame_gui_manager_lacks_add_persistent_element(self, pygame_gui_manager):
        """pygame_gui.UIManagerにadd_persistent_elementメソッドがないことを確認"""
        # これがエラーの原因
        assert not hasattr(pygame_gui_manager, 'add_persistent_element')
    
    def test_base_ui_manager_has_add_persistent_element(self, base_ui_manager):
        """BaseUIManagerにadd_persistent_elementメソッドがあることを確認"""
        assert hasattr(base_ui_manager, 'add_persistent_element')
        assert callable(base_ui_manager.add_persistent_element)
    
    def test_overworld_manager_receives_wrong_ui_manager_type(self, pygame_gui_manager):
        """OverworldManagerが間違ったUIManagerタイプを受け取ることを確認"""
        manager = OverworldManager()
        
        # WindowManagerはpygame_gui.UIManagerを渡す
        manager.set_ui_manager(pygame_gui_manager)
        
        # しかしOverworldManagerはBaseUIManagerのメソッドを期待している
        assert manager.ui_manager == pygame_gui_manager
        assert isinstance(manager.ui_manager, pygame_gui.UIManager)
        assert not hasattr(manager.ui_manager, 'add_persistent_element')
    
    def test_character_status_bar_initialization_succeeds_with_pygame_gui_manager_after_fix(self, pygame_gui_manager):
        """修正後：pygame_gui.ManagerでもCharacterStatusBar初期化が成功することを確認"""
        manager = OverworldManager()
        manager.set_ui_manager(pygame_gui_manager)
        
        # 修正後は初期化処理が成功することを確認
        assert manager.character_status_bar is not None
        
        # 独自管理の永続要素辞書が作成されていることを確認
        assert hasattr(manager, '_persistent_elements')
        assert manager.character_status_bar.element_id in manager._persistent_elements
    
    def test_character_status_bar_initialization_succeeds_with_base_ui_manager(self, base_ui_manager):
        """BaseUIManagerではCharacterStatusBar初期化が成功することを確認"""
        manager = OverworldManager()
        manager.set_ui_manager(base_ui_manager)
        
        # 初期化処理が成功することを確認
        assert manager.character_status_bar is not None
        assert hasattr(manager.ui_manager, 'add_persistent_element')
    
    def test_create_character_status_bar_function(self, pygame_setup):
        """create_character_status_bar関数が正常に動作することを確認"""
        screen = pygame_setup
        
        status_bar = create_character_status_bar(screen.get_width(), screen.get_height())
        
        assert status_bar is not None
        assert isinstance(status_bar, CharacterStatusBar)
        assert hasattr(status_bar, 'element_id')
    
    def test_ui_manager_compatibility_wrapper(self, pygame_gui_manager):
        """UIManager互換性ラッパーのテスト"""
        # pygame_gui.UIManagerをBaseUIManagerのインターフェースでラップするテスト
        
        class UIManagerWrapper:
            """pygame_gui.UIManagerをラップしてBaseUIManagerのインターフェースを提供"""
            
            def __init__(self, pygame_gui_manager):
                self.pygame_gui_manager = pygame_gui_manager
                self.persistent_elements = {}
            
            def add_persistent_element(self, element):
                """永続要素を追加（カスタム実装）"""
                if hasattr(element, 'element_id'):
                    self.persistent_elements[element.element_id] = element
            
            def __getattr__(self, name):
                """その他の属性はpygame_gui_managerに委譲"""
                return getattr(self.pygame_gui_manager, name)
        
        wrapped_manager = UIManagerWrapper(pygame_gui_manager)
        
        # 基本的なpygame_gui.UIManagerの機能が使用可能
        assert hasattr(wrapped_manager, 'process_events')
        assert hasattr(wrapped_manager, 'update')
        assert hasattr(wrapped_manager, 'draw_ui')
        
        # カスタムメソッドも使用可能
        assert hasattr(wrapped_manager, 'add_persistent_element')
        
        # テスト用要素でテスト
        test_element = Mock()
        test_element.element_id = "test"
        
        wrapped_manager.add_persistent_element(test_element)
        assert "test" in wrapped_manager.persistent_elements
    
    def test_proposed_fix_for_overworld_manager(self, pygame_gui_manager):
        """OverworldManagerの修正案テスト"""
        
        # 修正版の初期化メソッド
        def fixed_initialize_character_status_bar(self):
            """修正版：キャラクターステータスバーを初期化"""
            try:
                screen_width = 1024
                screen_height = 768
                
                self.character_status_bar = create_character_status_bar(screen_width, screen_height)
                
                # UIマネージャーの型を確認してから適切に処理
                if self.ui_manager and self.character_status_bar:
                    if hasattr(self.ui_manager, 'add_persistent_element'):
                        # BaseUIManagerの場合
                        self.ui_manager.add_persistent_element(self.character_status_bar)
                    else:
                        # pygame_gui.UIManagerの場合は独自管理
                        if not hasattr(self, '_persistent_elements'):
                            self._persistent_elements = {}
                        self._persistent_elements[self.character_status_bar.element_id] = self.character_status_bar
                
                return True
                
            except Exception as e:
                print(f"キャラクターステータスバー初期化エラー: {e}")
                self.character_status_bar = None
                return False
        
        # テスト
        manager = OverworldManager()
        manager.set_ui_manager(pygame_gui_manager)
        
        # 修正版メソッドを適用
        success = fixed_initialize_character_status_bar(manager)
        
        # 成功することを確認
        assert success
        assert manager.character_status_bar is not None
        assert hasattr(manager, '_persistent_elements')
        assert manager.character_status_bar.element_id in manager._persistent_elements
    
    def test_dungeon_selection_menu_with_fixed_ui_manager(self, pygame_gui_manager):
        """修正後のUIManagerでダンジョン選択メニューが正常動作することを確認"""
        manager = OverworldManager()
        manager.set_ui_manager(pygame_gui_manager)
        
        # ダンジョン一覧のモック
        with patch.object(manager, '_get_available_dungeons') as mock_get_dungeons:
            mock_get_dungeons.return_value = [
                {"id": "test_dungeon", "name": "テストダンジョン", "level": 1}
            ]
            
            with patch.object(manager, '_format_dungeon_info') as mock_format:
                mock_format.return_value = "テストダンジョン (Lv.1)"
                
                # エラーなしでダンジョン選択メニューが表示できることを確認
                try:
                    manager._show_dungeon_selection_menu()
                    
                    assert manager.dungeon_selection_list is not None
                    
                    # クリーンアップ
                    manager.dungeon_selection_list.kill()
                    manager.dungeon_selection_list = None
                    
                except Exception as e:
                    pytest.fail(f"ダンジョン選択メニューでエラー発生: {e}")
    
    def test_ui_manager_type_detection(self, pygame_gui_manager, base_ui_manager):
        """UIManagerの型検出テスト"""
        
        def detect_ui_manager_type(ui_manager):
            """UIManagerの型を検出"""
            if hasattr(ui_manager, 'add_persistent_element'):
                return "BaseUIManager"
            elif hasattr(ui_manager, 'process_events'):
                return "pygame_gui.UIManager"
            else:
                return "Unknown"
        
        # 型検出が正しく動作することを確認
        assert detect_ui_manager_type(pygame_gui_manager) == "pygame_gui.UIManager"
        assert detect_ui_manager_type(base_ui_manager) == "BaseUIManager"