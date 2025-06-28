"""
ListWindow のテスト

t-wada式TDDによるテストファースト開発
"""

import pytest
import pygame
import pygame_gui
from unittest.mock import Mock, patch
from src.ui.window_system import Window, WindowState
from src.ui.window_system.list_window import ListWindow, ListItem, ListColumn, SelectionMode, SortOrder


class TestListWindow:
    """ListWindow のテストクラス"""
    
    def setup_method(self):
        """各テストメソッドの前に実行される"""
        pygame.init()
        pygame.display.set_mode((1, 1), pygame.NOFRAME)
    
    def teardown_method(self):
        """各テストメソッドの後に実行される"""
        pygame.quit()
    
    def test_list_window_inherits_from_window(self):
        """ListWindowがWindowクラスを継承することを確認"""
        # Given: リスト設定
        list_config = {
            'title': 'Test List',
            'columns': [
                {'id': 'name', 'label': 'Name', 'width': 150},
                {'id': 'value', 'label': 'Value', 'width': 100}
            ],
            'items': [
                {'name': 'Item 1', 'value': '10'},
                {'name': 'Item 2', 'value': '20'}
            ]
        }
        
        # When: ListWindowを作成
        list_window = ListWindow('test_list', list_config)
        
        # Then: Windowクラスを継承している
        assert isinstance(list_window, Window)
        assert list_window.window_id == 'test_list'
        assert list_window.list_config == list_config
        assert list_window.modal is False  # デフォルトは非モーダル
    
    def test_list_validates_config_structure(self):
        """リスト設定の構造が検証されることを確認"""
        # Given: 不正なリスト設定
        
        # When: columnsが無い設定でListWindowを作成しようとする
        # Then: 例外が発生する
        with pytest.raises(ValueError, match="List config must contain 'columns'"):
            ListWindow('invalid_list', {})
        
        # When: columnsが空の設定でListWindowを作成しようとする
        # Then: 例外が発生する
        with pytest.raises(ValueError, match="List config 'columns' cannot be empty"):
            ListWindow('empty_list', {'columns': []})
    
    def test_list_creates_columns_from_config(self):
        """設定からカラムが作成されることを確認"""
        # Given: カラム設定
        list_config = {
            'columns': [
                {'id': 'name', 'label': 'Name', 'width': 150, 'sortable': True},
                {'id': 'type', 'label': 'Type', 'width': 100, 'sortable': False}
            ],
            'items': []
        }
        
        list_window = ListWindow('column_list', list_config)
        list_window.create()
        
        # Then: カラムが作成される
        assert len(list_window.columns) == 2
        name_col = list_window.columns[0]
        assert name_col.column_id == 'name'
        assert name_col.label == 'Name'
        assert name_col.width == 150
        assert name_col.sortable is True
        
        type_col = list_window.columns[1]
        assert type_col.column_id == 'type'
        assert type_col.sortable is False
    
    def test_list_creates_items_from_config(self):
        """設定からアイテムが作成されることを確認"""
        # Given: アイテム設定
        list_config = {
            'columns': [
                {'id': 'name', 'label': 'Name', 'width': 150},
                {'id': 'level', 'label': 'Level', 'width': 100}
            ],
            'items': [
                {'name': 'Fighter', 'level': '5'},
                {'name': 'Mage', 'level': '3'},
                {'name': 'Thief', 'level': '4'}
            ]
        }
        
        list_window = ListWindow('item_list', list_config)
        list_window.create()
        
        # Then: アイテムが作成される
        assert len(list_window.items) == 3
        fighter = list_window.items[0]
        assert fighter.data['name'] == 'Fighter'
        assert fighter.data['level'] == '5'
        assert fighter.selected is False
    
    def test_list_supports_single_selection_mode(self):
        """単一選択モードがサポートされることを確認"""
        # Given: 単一選択モードのリスト
        list_config = {
            'columns': [{'id': 'name', 'label': 'Name', 'width': 150}],
            'items': [
                {'name': 'Item 1'},
                {'name': 'Item 2'}
            ],
            'selection_mode': 'single'
        }
        
        list_window = ListWindow('single_list', list_config)
        list_window.create()
        
        # When: 複数のアイテムを選択しようとする
        list_window.select_item(0)
        list_window.select_item(1)
        
        # Then: 最後に選択されたアイテムのみが選択される
        assert list_window.items[0].selected is False
        assert list_window.items[1].selected is True
        assert len(list_window.get_selected_items()) == 1
    
    def test_list_supports_multiple_selection_mode(self):
        """複数選択モードがサポートされることを確認"""
        # Given: 複数選択モードのリスト
        list_config = {
            'columns': [{'id': 'name', 'label': 'Name', 'width': 150}],
            'items': [
                {'name': 'Item 1'},
                {'name': 'Item 2'},
                {'name': 'Item 3'}
            ],
            'selection_mode': 'multiple'
        }
        
        list_window = ListWindow('multi_list', list_config)
        list_window.create()
        
        # When: 複数のアイテムを選択
        list_window.select_item(0)
        list_window.select_item(2)
        
        # Then: 複数のアイテムが選択される
        assert list_window.items[0].selected is True
        assert list_window.items[1].selected is False
        assert list_window.items[2].selected is True
        assert len(list_window.get_selected_items()) == 2
    
    def test_list_keyboard_navigation_with_arrows(self):
        """矢印キーでキーボードナビゲーションが動作することを確認"""
        # Given: アイテムを含むリスト
        list_config = {
            'columns': [{'id': 'name', 'label': 'Name', 'width': 150}],
            'items': [
                {'name': 'Item 1'},
                {'name': 'Item 2'},
                {'name': 'Item 3'}
            ]
        }
        
        list_window = ListWindow('nav_list', list_config)
        list_window.create()
        
        # When: 下矢印キーを押す
        down_event = Mock()
        down_event.type = pygame.KEYDOWN
        down_event.key = pygame.K_DOWN
        down_event.mod = 0
        
        list_window.handle_event(down_event)
        
        # Then: 選択インデックスが増加
        assert list_window.selected_index == 1
        
        # When: 上矢印キーを押す
        up_event = Mock()
        up_event.type = pygame.KEYDOWN
        up_event.key = pygame.K_UP
        up_event.mod = 0
        
        list_window.handle_event(up_event)
        
        # Then: 選択インデックスが減少
        assert list_window.selected_index == 0
    
    def test_list_space_key_toggles_selection(self):
        """スペースキーで選択状態が切り替わることを確認"""
        # Given: 複数選択モードのリスト
        list_config = {
            'columns': [{'id': 'name', 'label': 'Name', 'width': 150}],
            'items': [
                {'name': 'Item 1'},
                {'name': 'Item 2'}
            ],
            'selection_mode': 'multiple'
        }
        
        list_window = ListWindow('toggle_list', list_config)
        list_window.create()
        
        # When: スペースキーを押す
        space_event = Mock()
        space_event.type = pygame.KEYDOWN
        space_event.key = pygame.K_SPACE
        space_event.mod = 0
        
        list_window.handle_event(space_event)
        
        # Then: 現在のアイテムが選択される
        assert list_window.items[0].selected is True
        
        # When: 再度スペースキーを押す
        list_window.handle_event(space_event)
        
        # Then: 選択が解除される
        assert list_window.items[0].selected is False
    
    def test_list_enter_key_activates_item(self):
        """Enterキーでアイテムが実行されることを確認"""
        # Given: リスト
        list_config = {
            'columns': [{'id': 'name', 'label': 'Name', 'width': 150}],
            'items': [
                {'name': 'Executable Item'}
            ]
        }
        
        list_window = ListWindow('exec_list', list_config)
        list_window.create()
        
        # When: Enterキーを押す
        enter_event = Mock()
        enter_event.type = pygame.KEYDOWN
        enter_event.key = pygame.K_RETURN
        enter_event.mod = 0
        
        with patch.object(list_window, 'send_message') as mock_send:
            result = list_window.handle_event(enter_event)
        
        # Then: アイテム実行メッセージが送信される
        assert result is True
        mock_send.assert_called_once_with('item_activated', {
            'list_id': 'exec_list',
            'item_index': 0,
            'item_data': {'name': 'Executable Item'}
        })
    
    def test_list_sorting_by_column(self):
        """カラムによるソートが動作することを確認"""
        # Given: ソート可能なカラムを持つリスト
        list_config = {
            'columns': [
                {'id': 'name', 'label': 'Name', 'width': 150, 'sortable': True},
                {'id': 'value', 'label': 'Value', 'width': 100, 'sortable': True}
            ],
            'items': [
                {'name': 'Charlie', 'value': '30'},
                {'name': 'Alice', 'value': '10'},
                {'name': 'Bob', 'value': '20'}
            ]
        }
        
        list_window = ListWindow('sort_list', list_config)
        list_window.create()
        
        # When: nameカラムでソート
        list_window.sort_by_column('name', SortOrder.ASCENDING)
        
        # Then: 表示されるアイテムがソートされる
        visible_items = list_window.get_visible_items()
        assert visible_items[0].data['name'] == 'Alice'
        assert visible_items[1].data['name'] == 'Bob'
        assert visible_items[2].data['name'] == 'Charlie'
    
    def test_list_filtering_by_search_text(self):
        """検索テキストによるフィルタリングが動作することを確認"""
        # Given: フィルタリング可能なリスト
        list_config = {
            'columns': [{'id': 'name', 'label': 'Name', 'width': 150}],
            'items': [
                {'name': 'Apple'},
                {'name': 'Banana'},
                {'name': 'Cherry'},
                {'name': 'Apricot'}
            ],
            'searchable': True
        }
        
        list_window = ListWindow('filter_list', list_config)
        list_window.create()
        
        # When: "Ap"で検索
        list_window.set_filter_text('Ap')
        
        # Then: マッチするアイテムのみが表示される
        visible_items = list_window.get_visible_items()
        assert len(visible_items) == 2
        assert visible_items[0].data['name'] == 'Apple'
        assert visible_items[1].data['name'] == 'Apricot'
    
    def test_list_mouse_click_selects_item(self):
        """マウスクリックでアイテムが選択されることを確認"""
        # Given: リスト
        list_config = {
            'columns': [{'id': 'name', 'label': 'Name', 'width': 150}],
            'items': [
                {'name': 'Clickable Item'}
            ]
        }
        
        list_window = ListWindow('click_list', list_config)
        list_window.create()
        
        # When: アイテムをクリック
        # pygame-guiのUIイベントをシミュレート
        click_event = Mock()
        click_event.type = pygame_gui.UI_SELECTION_LIST_NEW_SELECTION
        click_event.ui_element = list_window.list_ui_element
        click_event.text = 'Clickable Item'
        
        with patch.object(list_window, 'send_message') as mock_send:
            result = list_window.handle_event(click_event)
        
        # Then: 選択メッセージが送信される
        assert result is True
        mock_send.assert_called_once_with('item_selected', {
            'list_id': 'click_list',
            'item_index': 0,
            'item_data': {'name': 'Clickable Item'}
        })
    
    def test_list_double_click_activates_item(self):
        """ダブルクリックでアイテムが実行されることを確認"""
        # Given: リスト
        list_config = {
            'columns': [{'id': 'name', 'label': 'Name', 'width': 150}],
            'items': [
                {'name': 'Double Click Item'}
            ]
        }
        
        list_window = ListWindow('dclick_list', list_config)
        list_window.create()
        
        # When: アイテムをダブルクリック
        dclick_event = Mock()
        dclick_event.type = pygame_gui.UI_SELECTION_LIST_DOUBLE_CLICKED_SELECTION
        dclick_event.ui_element = list_window.list_ui_element
        dclick_event.text = 'Double Click Item'
        
        with patch.object(list_window, 'send_message') as mock_send:
            result = list_window.handle_event(dclick_event)
        
        # Then: アイテム実行メッセージが送信される
        assert result is True
        mock_send.assert_called_once_with('item_activated', {
            'list_id': 'dclick_list',
            'item_index': 0,
            'item_data': {'name': 'Double Click Item'}
        })
    
    def test_list_add_item_updates_display(self):
        """アイテム追加で表示が更新されることを確認"""
        # Given: リスト
        list_config = {
            'columns': [{'id': 'name', 'label': 'Name', 'width': 150}],
            'items': [
                {'name': 'Original Item'}
            ]
        }
        
        list_window = ListWindow('add_list', list_config)
        list_window.create()
        
        # When: 新しいアイテムを追加
        new_item_data = {'name': 'New Item'}
        list_window.add_item(new_item_data)
        
        # Then: アイテムが追加される
        assert len(list_window.items) == 2
        assert list_window.items[1].data['name'] == 'New Item'
    
    def test_list_remove_item_updates_display(self):
        """アイテム削除で表示が更新されることを確認"""
        # Given: 複数アイテムを持つリスト
        list_config = {
            'columns': [{'id': 'name', 'label': 'Name', 'width': 150}],
            'items': [
                {'name': 'Item 1'},
                {'name': 'Item 2'},
                {'name': 'Item 3'}
            ]
        }
        
        list_window = ListWindow('remove_list', list_config)
        list_window.create()
        
        # When: アイテムを削除
        list_window.remove_item(1)
        
        # Then: アイテムが削除される
        assert len(list_window.items) == 2
        assert list_window.items[0].data['name'] == 'Item 1'
        assert list_window.items[1].data['name'] == 'Item 3'
    
    def test_list_clear_all_items(self):
        """全アイテムクリアが動作することを確認"""
        # Given: アイテムを持つリスト
        list_config = {
            'columns': [{'id': 'name', 'label': 'Name', 'width': 150}],
            'items': [
                {'name': 'Item 1'},
                {'name': 'Item 2'}
            ]
        }
        
        list_window = ListWindow('clear_list', list_config)
        list_window.create()
        
        # When: 全アイテムをクリア
        list_window.clear_items()
        
        # Then: アイテムがクリアされる
        assert len(list_window.items) == 0
        assert list_window.selected_index == -1
    
    def test_list_cleanup_removes_ui_elements(self):
        """クリーンアップでUI要素が適切に削除されることを確認"""
        # Given: 作成されたリスト
        list_config = {
            'columns': [{'id': 'name', 'label': 'Name', 'width': 150}],
            'items': [
                {'name': 'Test Item'}
            ]
        }
        
        list_window = ListWindow('cleanup_list', list_config)
        list_window.create()
        
        # When: クリーンアップを実行
        list_window.cleanup_ui()
        
        # Then: UI要素が削除される
        assert len(list_window.items) == 0
        assert len(list_window.columns) == 0
        assert list_window.ui_manager is None