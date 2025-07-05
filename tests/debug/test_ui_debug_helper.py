"""
UIDebugHelperクラスのテスト

UI階層のダンプ機能、UI要素の検索機能などをテストする。
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
import pygame_gui
from typing import Dict, List, Any, Optional

from src.debug.ui_debug_helper import UIDebugHelper


class TestUIDebugHelper:
    """UIDebugHelperのテストクラス"""
    
    @pytest.fixture
    def mock_ui_manager(self):
        """モックのUIManagerを作成"""
        ui_manager = Mock()
        ui_manager.get_window_stack = Mock(return_value=[])
        ui_manager.get_all_ui_elements = Mock(return_value=[])
        return ui_manager
    
    @pytest.fixture
    def mock_window_manager(self):
        """モックのWindowManagerを作成"""
        window_manager = Mock()
        window_manager.windows = {}
        window_manager.window_stack = []
        return window_manager
    
    @pytest.fixture
    def ui_debug_helper(self, mock_ui_manager, mock_window_manager):
        """UIDebugHelperインスタンスを作成"""
        helper = UIDebugHelper(ui_manager=mock_ui_manager)
        helper._window_manager = mock_window_manager
        return helper
    
    def test_dump_ui_hierarchy_empty(self, ui_debug_helper):
        """UI要素が空の場合のダンプテスト"""
        result = ui_debug_helper.dump_ui_hierarchy()
        
        assert isinstance(result, dict)
        assert 'windows' in result
        assert 'ui_elements' in result
        assert 'window_stack' in result
        assert len(result['windows']) == 0
        assert len(result['ui_elements']) == 0
        assert len(result['window_stack']) == 0
    
    def test_dump_ui_hierarchy_with_windows(self, ui_debug_helper, mock_window_manager):
        """ウィンドウがある場合のダンプテスト"""
        # モックウィンドウを作成
        mock_window = Mock()
        mock_window.window_id = "test_window"
        mock_window.visible = True
        mock_window.rect = Mock(x=100, y=200, width=300, height=400)
        mock_window.__class__.__name__ = "TestWindow"
        
        mock_window_manager.windows = {"test_window": mock_window}
        mock_window_manager.window_stack = ["test_window"]
        
        result = ui_debug_helper.dump_ui_hierarchy()
        
        assert len(result['windows']) == 1
        assert result['windows'][0]['id'] == "test_window"
        assert result['windows'][0]['type'] == "TestWindow"
        assert result['windows'][0]['visible'] == True
        assert result['windows'][0]['position'] == {'x': 100, 'y': 200}
        assert result['windows'][0]['size'] == {'width': 300, 'height': 400}
        
        assert len(result['window_stack']) == 1
        assert result['window_stack'][0] == "test_window"
    
    def test_dump_ui_hierarchy_with_ui_elements(self, ui_debug_helper, mock_ui_manager):
        """UI要素がある場合のダンプテスト"""
        # モックUI要素を作成
        mock_button = Mock()
        mock_button.object_ids = ['test_button']
        mock_button.visible = 1  # pygame-guiでは0/1で表現
        mock_button.rect = Mock(x=50, y=50, width=100, height=30)
        mock_button.__class__.__name__ = "UIButton"
        
        mock_text_box = Mock()
        mock_text_box.object_ids = ['test_textbox']
        mock_text_box.visible = 1
        mock_text_box.rect = Mock(x=200, y=100, width=200, height=100)
        mock_text_box.__class__.__name__ = "UITextBox"
        
        # スプライトグループのモックを作成
        mock_sprite_group = Mock()
        mock_sprite_group.sprites.return_value = [mock_button, mock_text_box]
        mock_ui_manager.get_sprite_group.return_value = mock_sprite_group
        
        result = ui_debug_helper.dump_ui_hierarchy()
        
        assert len(result['ui_elements']) == 2
        
        button_info = result['ui_elements'][0]
        assert button_info['object_id'] == 'test_button'
        assert button_info['type'] == 'UIButton'
        assert button_info['visible'] == True
        assert button_info['position'] == {'x': 50, 'y': 50}
        assert button_info['size'] == {'width': 100, 'height': 30}
        
        textbox_info = result['ui_elements'][1]
        assert textbox_info['object_id'] == 'test_textbox'
        assert textbox_info['type'] == 'UITextBox'
    
    def test_get_active_windows(self, ui_debug_helper, mock_window_manager):
        """アクティブウィンドウ取得のテスト"""
        # 複数のモックウィンドウを作成
        mock_window1 = Mock()
        mock_window1.window_id = "window1"
        mock_window1.visible = True
        mock_window1.rect = Mock(x=0, y=0, width=800, height=600)
        mock_window1.__class__.__name__ = "MainWindow"
        
        mock_window2 = Mock()
        mock_window2.window_id = "window2"
        mock_window2.visible = False
        mock_window2.rect = Mock(x=100, y=100, width=400, height=300)
        mock_window2.__class__.__name__ = "DialogWindow"
        
        mock_window_manager.windows = {
            "window1": mock_window1,
            "window2": mock_window2
        }
        
        active_windows = ui_debug_helper.get_active_windows()
        
        # visibleなウィンドウのみ返される
        assert len(active_windows) == 1
        assert active_windows[0]['id'] == "window1"
        assert active_windows[0]['visible'] == True
    
    def test_get_ui_elements(self, ui_debug_helper, mock_ui_manager):
        """UI要素取得のテスト"""
        # モックUI要素を作成
        mock_element = Mock()
        mock_element.object_ids = ['test_element']
        mock_element.visible = 1
        mock_element.rect = Mock(x=10, y=20, width=30, height=40)
        mock_element.__class__.__name__ = "UIElement"
        
        # スプライトグループのモックを作成
        mock_sprite_group = Mock()
        mock_sprite_group.sprites.return_value = [mock_element]
        mock_ui_manager.get_sprite_group.return_value = mock_sprite_group
        
        ui_elements = ui_debug_helper.get_ui_elements()
        
        assert len(ui_elements) == 1
        assert ui_elements[0]['object_id'] == 'test_element'
        assert ui_elements[0]['type'] == 'UIElement'
    
    def test_find_element_by_id(self, ui_debug_helper, mock_ui_manager):
        """ID指定でのUI要素検索テスト"""
        # 複数のモックUI要素を作成
        mock_button1 = Mock()
        mock_button1.object_ids = ['button1']
        mock_button1.visible = 1
        mock_button1.rect = Mock(x=0, y=0, width=100, height=50)
        mock_button1.__class__.__name__ = "UIButton"
        
        mock_button2 = Mock()
        mock_button2.object_ids = ['button2', 'alt_button2']  # 複数のIDを持つ場合
        mock_button2.visible = 1
        mock_button2.rect = Mock(x=100, y=0, width=100, height=50)
        mock_button2.__class__.__name__ = "UIButton"
        
        # スプライトグループのモックを作成
        mock_sprite_group = Mock()
        mock_sprite_group.sprites.return_value = [mock_button1, mock_button2]
        mock_ui_manager.get_sprite_group.return_value = mock_sprite_group
        
        # 存在するIDで検索
        result = ui_debug_helper.find_element_by_id('button1')
        assert result is not None
        assert result['object_id'] == 'button1'
        
        # 別名IDで検索
        result = ui_debug_helper.find_element_by_id('alt_button2')
        assert result is not None
        assert 'button2' in result['object_ids']
        
        # 存在しないIDで検索
        result = ui_debug_helper.find_element_by_id('non_existent')
        assert result is None
    
    def test_dump_ui_hierarchy_format_tree(self, ui_debug_helper, mock_window_manager, mock_ui_manager):
        """ツリー形式でのダンプテスト"""
        # ウィンドウとUI要素を設定
        mock_window = Mock()
        mock_window.window_id = "main_window"
        mock_window.visible = True
        mock_window.rect = Mock(x=0, y=0, width=800, height=600)
        mock_window.__class__.__name__ = "MainWindow"
        
        mock_button = Mock()
        mock_button.object_ids = ['test_button']
        mock_button.visible = 1
        mock_button.rect = Mock(x=10, y=10, width=100, height=30)
        mock_button.__class__.__name__ = "UIButton"
        
        mock_window_manager.windows = {"main_window": mock_window}
        # スプライトグループのモックを作成
        mock_sprite_group = Mock()
        mock_sprite_group.sprites.return_value = [mock_button]
        mock_ui_manager.get_sprite_group.return_value = mock_sprite_group
        
        # ツリー形式でダンプ
        tree_result = ui_debug_helper.dump_ui_hierarchy(format='tree')
        
        assert isinstance(tree_result, str)
        assert "MainWindow" in tree_result
        assert "UIButton" in tree_result
        assert "test_button" in tree_result
    
    def test_dump_ui_hierarchy_with_error_handling(self, mock_ui_manager, mock_window_manager):
        """エラーハンドリングのテスト"""
        # UI要素の取得時にエラーを発生させる
        mock_ui_manager.get_sprite_group.side_effect = AttributeError("Test error")
        
        helper = UIDebugHelper(ui_manager=mock_ui_manager)
        helper._window_manager = mock_window_manager
        
        # エラーが発生してもダンプは完了する
        result = helper.dump_ui_hierarchy()
        
        assert isinstance(result, dict)
        assert 'ui_elements' in result
        assert 'error' in result  # エラー情報が含まれる
    
    def test_get_element_hierarchy(self, mock_ui_manager, mock_window_manager):
        """UI要素の親子関係取得テスト"""
        # 親子関係を持つUI要素を作成
        mock_parent = Mock()
        mock_parent.object_ids = ['parent_container']
        mock_parent.visible = 1
        mock_parent.rect = Mock(x=0, y=0, width=400, height=300)
        mock_parent.__class__.__name__ = "UIContainer"
        mock_parent.ui_container = None  # 親要素にはui_containerがない（ルート要素）
        
        mock_child = Mock()
        mock_child.object_ids = ['child_button']
        mock_child.visible = 1
        mock_child.rect = Mock(x=10, y=10, width=100, height=30)
        mock_child.__class__.__name__ = "UIButton"
        mock_child.ui_container = mock_parent  # 親への参照
        
        # スプライトグループのモックを作成
        mock_sprite_group = Mock()
        mock_sprite_group.sprites.return_value = [mock_parent, mock_child]
        mock_ui_manager.get_sprite_group.return_value = mock_sprite_group
        
        helper = UIDebugHelper(ui_manager=mock_ui_manager)
        helper._window_manager = mock_window_manager
        
        hierarchy = helper.get_element_hierarchy()
        
        assert len(hierarchy) == 1  # 親要素のみトップレベル
        assert hierarchy[0]['object_id'] == 'parent_container'
        assert 'children' in hierarchy[0]
        assert len(hierarchy[0]['children']) == 1
        assert hierarchy[0]['children'][0]['object_id'] == 'child_button'