"""ServicePanelのテスト"""

import unittest
from unittest.mock import Mock, MagicMock, patch
import pygame
import pygame_gui
from src.facilities.ui.service_panel import ServicePanel, StandardServicePanel
from src.facilities.core.facility_controller import FacilityController
from src.facilities.core.service_result import ServiceResult


class TestServicePanel(unittest.TestCase):
    """ServicePanelの抽象基底クラスのテスト"""
    
    def setUp(self):
        """テスト前のセットアップ"""
        # pygameの初期化（テスト用）
        pygame.init()
        pygame.display.set_mode((800, 600))
        
        # モックオブジェクトを作成
        self.mock_ui_manager = Mock(spec=pygame_gui.UIManager)
        self.mock_parent = Mock(spec=pygame_gui.elements.UIPanel)
        self.mock_controller = Mock(spec=FacilityController)
        
        # テスト用の矩形
        self.test_rect = pygame.Rect(10, 10, 400, 300)
        self.service_id = "test_service"
    
    def tearDown(self):
        """テスト後のクリーンアップ"""
        pygame.quit()
    
    @patch('pygame_gui.elements.UIPanel')
    def test_service_panel_initialization(self, mock_panel):
        """ServicePanelの初期化テスト"""
        # テスト用の実装クラス
        class TestServicePanelImpl(ServicePanel):
            def _create_ui(self):
                pass
        
        # ServicePanelを作成
        panel = TestServicePanelImpl(
            rect=self.test_rect,
            parent=self.mock_parent,
            controller=self.mock_controller,
            service_id=self.service_id,
            ui_manager=self.mock_ui_manager
        )
        
        # 基本プロパティが正しく設定されていることを確認
        self.assertEqual(panel.rect, self.test_rect)
        self.assertEqual(panel.parent, self.mock_parent)
        self.assertEqual(panel.controller, self.mock_controller)
        self.assertEqual(panel.service_id, self.service_id)
        self.assertEqual(panel.ui_manager, self.mock_ui_manager)
        self.assertFalse(panel.is_visible)
        self.assertEqual(panel._button_index_counter, 0)
        
        # コンテナが作成されていることを確認
        mock_panel.assert_called_once()
    
    @patch('pygame_gui.elements.UIPanel')
    def test_show_hide_methods(self, mock_panel):
        """表示/非表示メソッドのテスト"""
        class TestServicePanelImpl(ServicePanel):
            def _create_ui(self):
                pass
        
        mock_container = Mock()
        mock_panel.return_value = mock_container
        
        panel = TestServicePanelImpl(
            rect=self.test_rect,
            parent=self.mock_parent,
            controller=self.mock_controller,
            service_id=self.service_id,
            ui_manager=self.mock_ui_manager
        )
        
        # 表示テスト
        panel.show()
        self.assertTrue(panel.is_visible)
        mock_container.show.assert_called_once()
        
        # 非表示テスト
        panel.hide()
        self.assertFalse(panel.is_visible)
        mock_container.hide.assert_called_once()
    
    @patch('pygame_gui.elements.UIPanel')
    @patch('pygame_gui.elements.UIButton')
    def test_create_button_with_shortcut_keys(self, mock_button, mock_panel):
        """ショートカットキー付きボタン作成のテスト"""
        class TestServicePanelImpl(ServicePanel):
            def _create_ui(self):
                # テスト用のボタンを3つ作成
                self.button1 = self._create_button("ボタン1", pygame.Rect(10, 10, 100, 30))
                self.button2 = self._create_button("ボタン2", pygame.Rect(10, 50, 100, 30))
                self.button3 = self._create_button("ボタン3", pygame.Rect(10, 90, 100, 30))
        
        mock_button_instances = []
        for i in range(3):
            mock_btn = Mock()
            mock_button_instances.append(mock_btn)
        mock_button.side_effect = mock_button_instances
        
        # ServicePanelを作成
        panel = TestServicePanelImpl(
            rect=self.test_rect,
            parent=self.mock_parent,
            controller=self.mock_controller,
            service_id=self.service_id,
            ui_manager=self.mock_ui_manager
        )
        
        # ショートカットキーが正しく設定されていることを確認
        self.assertEqual(panel.button1.button_index, 0)
        self.assertEqual(panel.button1.shortcut_key, "1")
        self.assertEqual(panel.button2.button_index, 1)
        self.assertEqual(panel.button2.shortcut_key, "2")
        self.assertEqual(panel.button3.button_index, 2)
        self.assertEqual(panel.button3.shortcut_key, "3")
    
    @patch('pygame_gui.elements.UIPanel')
    @patch('pygame_gui.elements.UILabel')
    def test_create_label(self, mock_label, mock_panel):
        """ラベル作成のテスト"""
        class TestServicePanelImpl(ServicePanel):
            def _create_ui(self):
                self.test_label = self._create_label("テストラベル", pygame.Rect(10, 10, 200, 30))
        
        mock_label_instance = Mock()
        mock_label.return_value = mock_label_instance
        
        # ServicePanelを作成
        panel = TestServicePanelImpl(
            rect=self.test_rect,
            parent=self.mock_parent,
            controller=self.mock_controller,
            service_id=self.service_id,
            ui_manager=self.mock_ui_manager
        )
        
        # ラベルが作成されていることを確認
        mock_label.assert_called_once()
        self.assertEqual(panel.test_label, mock_label_instance)
        self.assertIn(mock_label_instance, panel.ui_elements)
    
    @patch('pygame_gui.elements.UIPanel')
    @patch('pygame_gui.elements.UITextBox')
    def test_create_text_box(self, mock_text_box, mock_panel):
        """テキストボックス作成のテスト"""
        class TestServicePanelImpl(ServicePanel):
            def _create_ui(self):
                self.test_text_box = self._create_text_box(
                    "テストテキスト", 
                    pygame.Rect(10, 10, 200, 100)
                )
        
        mock_text_box_instance = Mock()
        mock_text_box.return_value = mock_text_box_instance
        
        # ServicePanelを作成
        panel = TestServicePanelImpl(
            rect=self.test_rect,
            parent=self.mock_parent,
            controller=self.mock_controller,
            service_id=self.service_id,
            ui_manager=self.mock_ui_manager
        )
        
        # テキストボックスが作成されていることを確認
        mock_text_box.assert_called_once()
        self.assertEqual(panel.test_text_box, mock_text_box_instance)
        self.assertIn(mock_text_box_instance, panel.ui_elements)
    
    def test_execute_service_action(self):
        """サービスアクション実行のテスト"""
        class TestServicePanelImpl(ServicePanel):
            def _create_ui(self):
                pass
            
            def test_action(self):
                return self._execute_service_action("test_action", {"param": "value"})
        
        with patch('pygame_gui.elements.UIPanel'):
            # モックの戻り値を設定
            expected_result = ServiceResult.ok("Success")
            self.mock_controller.execute_service.return_value = expected_result
            
            panel = TestServicePanelImpl(
                rect=self.test_rect,
                parent=self.mock_parent,
                controller=self.mock_controller,
                service_id=self.service_id,
                ui_manager=self.mock_ui_manager
            )
            
            # アクションを実行
            result = panel.test_action()
            
            # 正しく実行されたことを確認
            self.assertEqual(result, expected_result)
            self.mock_controller.execute_service.assert_called_once_with(
                "test_action", {"param": "value"}
            )
    
    def test_destroy(self):
        """破棄処理のテスト"""
        class TestServicePanelImpl(ServicePanel):
            def _create_ui(self):
                pass
        
        with patch('pygame_gui.elements.UIPanel') as mock_panel:
            mock_container = Mock()
            mock_panel.return_value = mock_container
            
            # UI要素のモックを作成
            mock_elements = [Mock(), Mock(), Mock()]
            for element in mock_elements:
                element.kill = Mock()
            
            panel = TestServicePanelImpl(
                rect=self.test_rect,
                parent=self.mock_parent,
                controller=self.mock_controller,
                service_id=self.service_id,
                ui_manager=self.mock_ui_manager
            )
            
            # UI要素を手動で追加
            panel.ui_elements = mock_elements
            
            # 破棄処理を実行
            panel.destroy()
            
            # すべてのUI要素のkillが呼ばれたことを確認
            for element in mock_elements:
                element.kill.assert_called_once()
            
            # UI要素リストがクリアされたことを確認
            self.assertEqual(len(panel.ui_elements), 0)
            
            # コンテナのkillが呼ばれたことを確認
            mock_container.kill.assert_called_once()


class TestStandardServicePanel(unittest.TestCase):
    """StandardServicePanelのテスト"""
    
    def setUp(self):
        """テスト前のセットアップ"""
        pygame.init()
        pygame.display.set_mode((800, 600))
        
        self.mock_ui_manager = Mock(spec=pygame_gui.UIManager)
        self.mock_parent = Mock(spec=pygame_gui.elements.UIPanel)
        self.mock_controller = Mock(spec=FacilityController)
        
        self.test_rect = pygame.Rect(10, 10, 400, 300)
        self.service_id = "test_standard_service"
    
    def tearDown(self):
        """テスト後のクリーンアップ"""
        pygame.quit()
    
    @patch('pygame_gui.elements.UIPanel')
    @patch('pygame_gui.elements.UILabel')
    @patch('pygame_gui.elements.UITextBox')
    @patch('pygame_gui.elements.UIButton')
    def test_standard_panel_creation(self, mock_button, mock_text_box, mock_label, mock_panel):
        """StandardServicePanelの作成テスト"""
        # モックの戻り値を設定
        from src.facilities.core.facility_service import MenuItem
        mock_menu_items = [
            MenuItem(self.service_id, "テストサービス", description="テスト用のサービスです")
        ]
        self.mock_controller.get_menu_items.return_value = mock_menu_items
        
        # StandardServicePanelを作成
        panel = StandardServicePanel(
            rect=self.test_rect,
            parent=self.mock_parent,
            controller=self.mock_controller,
            service_id=self.service_id,
            ui_manager=self.mock_ui_manager
        )
        
        # UI要素が作成されていることを確認
        mock_label.assert_called()  # タイトルラベル
        mock_text_box.assert_called()  # 説明テキストボックス
        mock_button.assert_called()  # アクションボタン
    
    @patch('pygame_gui.elements.UIPanel')
    @patch('pygame_gui.elements.UILabel')
    @patch('pygame_gui.elements.UITextBox')
    @patch('pygame_gui.elements.UIButton')
    def test_handle_button_click(self, mock_button, mock_text_box, mock_label, mock_panel):
        """ボタンクリック処理のテスト"""
        mock_button_instance = Mock()
        mock_button.return_value = mock_button_instance
        
        # モックの戻り値を設定
        from src.facilities.core.facility_service import MenuItem
        mock_menu_items = [
            MenuItem(self.service_id, "テストサービス")
        ]
        self.mock_controller.get_menu_items.return_value = mock_menu_items
        self.mock_controller.execute_service.return_value = ServiceResult.ok("実行成功")
        
        # StandardServicePanelを作成
        panel = StandardServicePanel(
            rect=self.test_rect,
            parent=self.mock_parent,
            controller=self.mock_controller,
            service_id=self.service_id,
            ui_manager=self.mock_ui_manager
        )
        
        # ボタンクリックを処理
        result = panel.handle_button_click(mock_button_instance)
        
        # 正しく処理されたことを確認
        self.assertTrue(result)
        self.mock_controller.execute_service.assert_called_once_with(self.service_id)
    
    @patch('pygame_gui.elements.UIPanel')
    @patch('pygame_gui.elements.UILabel')
    @patch('pygame_gui.elements.UITextBox')
    @patch('pygame_gui.elements.UIButton')
    def test_handle_unknown_button_click(self, mock_button, mock_text_box, mock_label, mock_panel):
        """未知のボタンクリック処理のテスト"""
        mock_button_instance = Mock()
        mock_unknown_button = Mock()
        mock_button.return_value = mock_button_instance
        
        # モックの戻り値を設定
        from src.facilities.core.facility_service import MenuItem
        mock_menu_items = [
            MenuItem(self.service_id, "テストサービス")
        ]
        self.mock_controller.get_menu_items.return_value = mock_menu_items
        
        # StandardServicePanelを作成
        panel = StandardServicePanel(
            rect=self.test_rect,
            parent=self.mock_parent,
            controller=self.mock_controller,
            service_id=self.service_id,
            ui_manager=self.mock_ui_manager
        )
        
        # 未知のボタンのクリックを処理
        result = panel.handle_button_click(mock_unknown_button)
        
        # 処理されなかったことを確認
        self.assertFalse(result)
        self.mock_controller.execute_service.assert_not_called()


class TestServicePanelEdgeCases(unittest.TestCase):
    """ServicePanelのエッジケースのテスト"""
    
    def setUp(self):
        """テスト前のセットアップ"""
        pygame.init()
        pygame.display.set_mode((800, 600))
        
        self.mock_ui_manager = Mock(spec=pygame_gui.UIManager)
        self.mock_parent = Mock(spec=pygame_gui.elements.UIPanel)
        self.mock_controller = Mock(spec=FacilityController)
        
        self.test_rect = pygame.Rect(10, 10, 400, 300)
        self.service_id = "test_edge_case_service"
    
    def tearDown(self):
        """テスト後のクリーンアップ"""
        pygame.quit()
    
    @patch('pygame_gui.elements.UIPanel')
    @patch('pygame_gui.elements.UIButton')
    def test_button_limit_reached(self, mock_button, mock_panel):
        """ボタン数制限到達のテスト"""
        class TestServicePanelImpl(ServicePanel):
            def _create_ui(self):
                # 10個のボタンを作成（ショートカットキーは1-9まで）
                self.buttons = []
                for i in range(10):
                    button = self._create_button(f"ボタン{i+1}", pygame.Rect(10, 10+i*40, 100, 30))
                    self.buttons.append(button)
        
        mock_button_instances = []
        for i in range(10):
            mock_btn = Mock()
            mock_button_instances.append(mock_btn)
        mock_button.side_effect = mock_button_instances
        
        # ServicePanelを作成
        panel = TestServicePanelImpl(
            rect=self.test_rect,
            parent=self.mock_parent,
            controller=self.mock_controller,
            service_id=self.service_id,
            ui_manager=self.mock_ui_manager
        )
        
        # 最初の9個のボタンのみショートカットキーが設定されていることを確認
        for i in range(9):
            self.assertTrue(hasattr(panel.buttons[i], 'shortcut_key'))
            self.assertEqual(panel.buttons[i].shortcut_key, str(i + 1))
        
        # 10個目のボタンにはショートカットキーが設定されていないことを確認
        self.assertFalse(hasattr(panel.buttons[9], 'shortcut_key'))
    
    def test_refresh_method(self):
        """リフレッシュメソッドのテスト"""
        class TestServicePanelImpl(ServicePanel):
            def _create_ui(self):
                pass
            
            def _refresh_content(self):
                self.refresh_called = True
        
        with patch('pygame_gui.elements.UIPanel'):
            panel = TestServicePanelImpl(
                rect=self.test_rect,
                parent=self.mock_parent,
                controller=self.mock_controller,
                service_id=self.service_id,
                ui_manager=self.mock_ui_manager
            )
            
            # リフレッシュを実行
            panel.refresh()
            
            # リフレッシュメソッドが呼ばれたことを確認
            self.assertTrue(hasattr(panel, 'refresh_called'))
            self.assertTrue(panel.refresh_called)


if __name__ == '__main__':
    unittest.main()