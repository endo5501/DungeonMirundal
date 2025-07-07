"""NavigationPanelのテスト"""

import unittest
from unittest.mock import Mock, MagicMock, patch
import pygame
import pygame_gui
from src.facilities.ui.navigation_panel import NavigationPanel
from src.facilities.core.facility_service import MenuItem


class TestNavigationPanel(unittest.TestCase):
    """NavigationPanelのテストクラス"""
    
    def setUp(self):
        """テスト前のセットアップ"""
        # pygameの初期化（テスト用）
        pygame.init()
        pygame.display.set_mode((800, 600))
        
        # モックUIマネージャーを作成
        self.mock_ui_manager = Mock(spec=pygame_gui.UIManager)
        
        # モック親パネルを作成
        self.mock_parent = Mock(spec=pygame_gui.elements.UIPanel)
        
        # テスト用のメニューアイテム
        self.test_menu_items = [
            MenuItem("item1", "アイテム1", enabled=True),
            MenuItem("item2", "アイテム2", enabled=True),
            MenuItem("exit", "退出", enabled=True),
        ]
        
        # モックコールバック関数
        self.mock_callback = Mock()
        
        # テスト用の矩形
        self.test_rect = pygame.Rect(10, 10, 800, 60)
    
    def tearDown(self):
        """テスト後のクリーンアップ"""
        pygame.quit()
    
    @patch('pygame_gui.elements.UIPanel')
    @patch('pygame_gui.elements.UIButton')
    def test_navigation_panel_creation(self, mock_button, mock_panel):
        """NavigationPanelの作成テスト"""
        # モックボタンのインスタンスを作成
        mock_button_instance = Mock()
        mock_button.return_value = mock_button_instance
        
        # NavigationPanelを作成
        panel = NavigationPanel(
            rect=self.test_rect,
            parent=self.mock_parent,
            menu_items=self.test_menu_items,
            on_select_callback=self.mock_callback,
            ui_manager=self.mock_ui_manager
        )
        
        # 基本プロパティが正しく設定されていることを確認
        self.assertEqual(panel.rect, self.test_rect)
        self.assertEqual(panel.parent, self.mock_parent)
        self.assertEqual(panel.menu_items, self.test_menu_items)
        self.assertEqual(panel.on_select_callback, self.mock_callback)
        self.assertEqual(panel.ui_manager, self.mock_ui_manager)
        
        # ボタンが作成されていることを確認
        self.assertEqual(len(panel.nav_buttons), 3)
        
        # コンテナパネルが作成されていることを確認
        mock_panel.assert_called_once()
    
    @patch('pygame_gui.elements.UIPanel')
    @patch('pygame_gui.elements.UIButton')
    def test_button_creation_with_shortcut_keys(self, mock_button, mock_panel):
        """ショートカットキー付きボタン作成のテスト"""
        mock_button_instances = []
        for i in range(3):
            mock_btn = Mock()
            mock_button_instances.append(mock_btn)
        mock_button.side_effect = mock_button_instances
        
        # NavigationPanelを作成
        panel = NavigationPanel(
            rect=self.test_rect,
            parent=self.mock_parent,
            menu_items=self.test_menu_items,
            on_select_callback=self.mock_callback,
            ui_manager=self.mock_ui_manager
        )
        
        # ショートカットキーが正しく設定されていることを確認
        buttons = list(panel.nav_buttons.values())
        for i, button in enumerate(buttons):
            self.assertEqual(button.button_index, i)
            self.assertEqual(button.shortcut_key, str(i + 1))
    
    @patch('pygame_gui.elements.UIPanel')
    @patch('pygame_gui.elements.UIButton')
    def test_button_layout_calculation(self, mock_button, mock_panel):
        """ボタンレイアウト計算のテスト"""
        mock_button_instances = []
        for i in range(3):
            mock_btn = Mock()
            mock_button_instances.append(mock_btn)
        mock_button.side_effect = mock_button_instances
        
        # NavigationPanelを作成
        panel = NavigationPanel(
            rect=self.test_rect,
            parent=self.mock_parent,
            menu_items=self.test_menu_items,
            on_select_callback=self.mock_callback,
            ui_manager=self.mock_ui_manager
        )
        
        # ボタンが正しい数だけ作成されていることを確認
        self.assertEqual(mock_button.call_count, 3)
        
        # 各ボタンが適切な引数で作成されていることを確認
        for call in mock_button.call_args_list:
            args, kwargs = call
            # 矩形領域が指定されていることを確認
            self.assertIn('relative_rect', kwargs)
            # テキストが指定されていることを確認
            self.assertIn('text', kwargs)
            # UIマネージャーが指定されていることを確認
            self.assertIn('manager', kwargs)
    
    @patch('pygame_gui.elements.UIPanel')
    @patch('pygame_gui.elements.UIButton')
    def test_empty_menu_items(self, mock_button, mock_panel):
        """空のメニューアイテムでの作成テスト"""
        # NavigationPanelを空のメニューで作成
        panel = NavigationPanel(
            rect=self.test_rect,
            parent=self.mock_parent,
            menu_items=[],
            on_select_callback=self.mock_callback,
            ui_manager=self.mock_ui_manager
        )
        
        # ボタンが作成されていないことを確認
        self.assertEqual(len(panel.nav_buttons), 0)
        # ボタン作成関数が呼ばれていないことを確認
        mock_button.assert_not_called()
    
    @patch('pygame_gui.elements.UIPanel')
    @patch('pygame_gui.elements.UIButton')
    def test_button_style_assignment(self, mock_button, mock_panel):
        """ボタンスタイル割り当てのテスト"""
        # 特別なボタンを含むメニューアイテム
        special_menu_items = [
            MenuItem("wizard_item", "ウィザード", service_type="wizard"),
            MenuItem("exit", "退出"),
            MenuItem("normal_item", "通常"),
        ]
        
        mock_button_instances = []
        for i in range(3):
            mock_btn = Mock()
            mock_button_instances.append(mock_btn)
        mock_button.side_effect = mock_button_instances
        
        # NavigationPanelを作成
        panel = NavigationPanel(
            rect=self.test_rect,
            parent=self.mock_parent,
            menu_items=special_menu_items,
            on_select_callback=self.mock_callback,
            ui_manager=self.mock_ui_manager
        )
        
        # スタイルが正しく設定されていることを確認
        call_args_list = mock_button.call_args_list
        
        # ウィザードボタンのスタイル
        wizard_call = call_args_list[0]
        self.assertEqual(wizard_call[1]['object_id'], '#wizard_button')
        
        # 退出ボタンのスタイル
        exit_call = call_args_list[1]
        self.assertEqual(exit_call[1]['object_id'], '#exit_button')
        
        # 通常ボタンのスタイル
        normal_call = call_args_list[2]
        self.assertEqual(normal_call[1]['object_id'], '#nav_button')
    
    def test_set_selected(self):
        """選択状態設定のテスト"""
        with patch('pygame_gui.elements.UIPanel'), patch('pygame_gui.elements.UIButton'):
            panel = NavigationPanel(
                rect=self.test_rect,
                parent=self.mock_parent,
                menu_items=self.test_menu_items,
                on_select_callback=self.mock_callback,
                ui_manager=self.mock_ui_manager
            )
            
            # 選択状態を設定
            panel.set_selected("item1")
            
            # 選択状態が正しく設定されていることを確認
            self.assertEqual(panel.selected_item_id, "item1")
    
    @patch('pygame_gui.elements.UIPanel')
    @patch('pygame_gui.elements.UIButton')
    def test_button_click_handling(self, mock_button, mock_panel):
        """ボタンクリック処理のテスト"""
        mock_button_instances = []
        for i in range(3):
            mock_btn = Mock()
            mock_btn.is_enabled = True
            mock_button_instances.append(mock_btn)
        mock_button.side_effect = mock_button_instances
        
        # NavigationPanelを作成
        panel = NavigationPanel(
            rect=self.test_rect,
            parent=self.mock_parent,
            menu_items=self.test_menu_items,
            on_select_callback=self.mock_callback,
            ui_manager=self.mock_ui_manager
        )
        
        # ボタンクリックイベントをシミュレート
        mock_event = Mock()
        mock_event.type = pygame_gui.UI_BUTTON_PRESSED
        mock_event.ui_element = mock_button_instances[0]
        
        # ボタンクリックを処理
        result = panel.handle_button_click(mock_event)
        
        # コールバックが呼ばれたことを確認
        self.assertTrue(result)
        self.mock_callback.assert_called_once_with("item1")
    
    @patch('pygame_gui.elements.UIPanel')
    @patch('pygame_gui.elements.UIButton')
    def test_disabled_button_click(self, mock_button, mock_panel):
        """無効化されたボタンのクリック処理テスト"""
        mock_button_instance = Mock()
        mock_button_instance.is_enabled = False
        mock_button.return_value = mock_button_instance
        
        # 無効化されたメニューアイテム
        disabled_menu_items = [
            MenuItem("disabled_item", "無効アイテム", enabled=False)
        ]
        
        # NavigationPanelを作成
        panel = NavigationPanel(
            rect=self.test_rect,
            parent=self.mock_parent,
            menu_items=disabled_menu_items,
            on_select_callback=self.mock_callback,
            ui_manager=self.mock_ui_manager
        )
        
        # ボタンクリックイベントをシミュレート
        mock_event = Mock()
        mock_event.type = pygame_gui.UI_BUTTON_PRESSED
        mock_event.ui_element = mock_button_instance
        
        # ボタンクリックを処理
        result = panel.handle_button_click(mock_event)
        
        # コールバックが呼ばれていないことを確認
        self.assertFalse(result)
        self.mock_callback.assert_not_called()
    
    def test_destroy(self):
        """破棄処理のテスト"""
        with patch('pygame_gui.elements.UIPanel') as mock_panel, \
             patch('pygame_gui.elements.UIButton') as mock_button:
            
            mock_button_instance = Mock()
            mock_button.return_value = mock_button_instance
            mock_container = Mock()
            mock_panel.return_value = mock_container
            
            # NavigationPanelを作成
            panel = NavigationPanel(
                rect=self.test_rect,
                parent=self.mock_parent,
                menu_items=self.test_menu_items,
                on_select_callback=self.mock_callback,
                ui_manager=self.mock_ui_manager
            )
            
            # 破棄処理を実行
            panel.destroy()
            
            # ボタンのkillが呼ばれたことを確認
            mock_button_instance.kill.assert_called()
            
            # コンテナのkillが呼ばれたことを確認
            mock_container.kill.assert_called_once()
            
            # ボタン辞書がクリアされたことを確認
            self.assertEqual(len(panel.nav_buttons), 0)


class TestNavigationPanelEdgeCases(unittest.TestCase):
    """NavigationPanelのエッジケースのテスト"""
    
    def setUp(self):
        """テスト前のセットアップ"""
        pygame.init()
        pygame.display.set_mode((800, 600))
        
        self.mock_ui_manager = Mock(spec=pygame_gui.UIManager)
        self.mock_parent = Mock(spec=pygame_gui.elements.UIPanel)
        self.mock_callback = Mock()
        self.test_rect = pygame.Rect(10, 10, 800, 60)
    
    def tearDown(self):
        """テスト後のクリーンアップ"""
        pygame.quit()
    
    @patch('pygame_gui.elements.UIPanel')
    @patch('pygame_gui.elements.UIButton')
    def test_many_buttons_shortcut_limit(self, mock_button, mock_panel):
        """多数のボタンでのショートカットキー制限テスト"""
        # 10個のメニューアイテム（ショートカットキーは1-9まで）
        many_menu_items = [
            MenuItem(f"item{i}", f"アイテム{i}") for i in range(10)
        ]
        
        mock_button_instances = []
        for i in range(10):
            mock_btn = Mock()
            mock_button_instances.append(mock_btn)
        mock_button.side_effect = mock_button_instances
        
        # NavigationPanelを作成
        panel = NavigationPanel(
            rect=self.test_rect,
            parent=self.mock_parent,
            menu_items=many_menu_items,
            on_select_callback=self.mock_callback,
            ui_manager=self.mock_ui_manager
        )
        
        # 最初の9個のボタンのみショートカットキーが設定されていることを確認
        buttons = list(panel.nav_buttons.values())
        for i in range(9):
            self.assertTrue(hasattr(buttons[i], 'shortcut_key'))
            self.assertEqual(buttons[i].shortcut_key, str(i + 1))
        
        # 10個目のボタンにはショートカットキーが設定されていないことを確認
        self.assertFalse(hasattr(buttons[9], 'shortcut_key'))
    
    def test_unknown_event_type(self):
        """未知のイベントタイプの処理テスト"""
        with patch('pygame_gui.elements.UIPanel'), patch('pygame_gui.elements.UIButton'):
            panel = NavigationPanel(
                rect=self.test_rect,
                parent=self.mock_parent,
                menu_items=[MenuItem("test", "テスト")],
                on_select_callback=self.mock_callback,
                ui_manager=self.mock_ui_manager
            )
            
            # 未知のイベントタイプ
            mock_event = Mock()
            mock_event.type = 999999  # 存在しないイベントタイプ
            
            # イベント処理
            result = panel.handle_button_click(mock_event)
            
            # 処理されないことを確認
            self.assertFalse(result)
            self.mock_callback.assert_not_called()


if __name__ == '__main__':
    unittest.main()