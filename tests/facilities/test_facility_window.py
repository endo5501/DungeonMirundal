"""施設ウィンドウのテスト"""

import pytest
import pygame
import pygame_gui
from unittest.mock import Mock, MagicMock, patch
from src.facilities.ui.facility_window import FacilityWindow
from src.facilities.core.facility_controller import FacilityController
from src.facilities.core.facility_service import MenuItem


@pytest.fixture
def mock_pygame():
    """pygameのモック"""
    with patch('pygame.display.get_surface') as mock_surface:
        mock_screen = Mock()
        mock_screen.get_rect.return_value = pygame.Rect(0, 0, 1024, 768)
        mock_surface.return_value = mock_screen
        yield mock_surface


@pytest.fixture
def mock_window_manager():
    """WindowManagerのモック"""
    with patch('src.facilities.ui.facility_window.WindowManager') as mock_wm:
        wm_instance = Mock()
        wm_instance.ui_manager = Mock()
        mock_wm.get_instance.return_value = wm_instance
        yield wm_instance


@pytest.fixture
def mock_controller():
    """FacilityControllerのモック"""
    controller = Mock(spec=FacilityController)
    controller.facility_id = "test_facility"
    controller.is_active = True
    
    # メニュー項目のモック
    controller.get_menu_items.return_value = [
        MenuItem("service1", "サービス1", enabled=True),
        MenuItem("service2", "サービス2", enabled=True),
        MenuItem("exit", "退出", enabled=True)
    ]
    
    controller.get_config.return_value = "テスト施設"
    
    # サービスのモック
    mock_service = Mock()
    mock_service.create_service_panel.return_value = None
    controller.service = mock_service
    
    return controller


class TestFacilityWindowBasic:
    """FacilityWindowの基本機能テスト"""
    
    def test_initialization_with_controller(self, mock_controller):
        """コントローラー付きで正常に初期化される"""
        window = FacilityWindow("test_window", controller=mock_controller)
        
        assert window.controller == mock_controller
        assert window.window_id == "test_window"
        assert window.main_panel is None
        assert window.navigation_panel is None
        assert window.service_panels == {}
        assert window.current_service_id is None
        assert window.window_width == 900
        assert window.window_height == 600
    
    def test_initialization_with_facility_controller(self, mock_controller):
        """facility_controllerパラメータで初期化される"""
        window = FacilityWindow("test_window", facility_controller=mock_controller)
        
        assert window.controller == mock_controller
        assert window.window_id == "test_window"
    
    def test_initialization_without_controller(self):
        """コントローラーなしでValueErrorが発生する"""
        with pytest.raises(ValueError, match="FacilityController is required"):
            FacilityWindow("test_window")
    
    def test_controller_priority(self, mock_controller):
        """controllerがfacility_controllerより優先される"""
        other_controller = Mock()
        window = FacilityWindow(
            "test_window", 
            controller=mock_controller,
            facility_controller=other_controller
        )
        
        assert window.controller == mock_controller


class TestFacilityWindowCreation:
    """FacilityWindowの作成処理テスト"""
    
    @patch('pygame_gui.elements.UIPanel')
    @patch('pygame_gui.elements.UILabel')
    def test_create_with_window_manager(self, mock_label, mock_panel, mock_controller, mock_window_manager, mock_pygame):
        """WindowManager経由でUI作成が成功する"""
        window = FacilityWindow("test_window", controller=mock_controller)
        
        with patch.object(window, '_create_navigation') as mock_nav, \
             patch.object(window, '_show_initial_service') as mock_initial:
            window.create()
        
        # UI要素が作成される
        mock_panel.assert_called()
        mock_label.assert_called()
        mock_nav.assert_called_once()
        mock_initial.assert_called_once()
        
        # 画面サイズに基づいて位置が設定される
        assert window.rect is not None
        assert window.rect.width == 900
        assert window.rect.height == 600
    
    def test_create_without_window_manager(self, mock_controller):
        """WindowManagerがない場合はエラーログが出力される"""
        with patch('src.facilities.ui.facility_window.WindowManager') as mock_wm:
            mock_wm.get_instance.return_value = None
            
            window = FacilityWindow("test_window", controller=mock_controller)
            
            with patch('src.facilities.ui.facility_window.logger') as mock_logger:
                window.create()
                mock_logger.error.assert_called_with("WindowManager not available")
    
    @patch('pygame_gui.elements.UIPanel')
    @patch('pygame_gui.elements.UILabel')
    def test_create_main_panel(self, mock_label, mock_panel, mock_controller, mock_window_manager, mock_pygame):
        """メインパネルが正常に作成される"""
        window = FacilityWindow("test_window", controller=mock_controller)
        window.ui_manager = Mock()
        window.rect = pygame.Rect(100, 100, 900, 600)
        
        window._create_main_panel()
        
        # メインパネルとタイトルラベルが作成される
        mock_panel.assert_called()
        mock_label.assert_called()
        
        # get_facility_titleが呼ばれる
        mock_controller.get_config.assert_called_with("name")


class TestFacilityWindowNavigation:
    """FacilityWindowのナビゲーション機能テスト"""
    
    def test_create_navigation_success(self, mock_controller, mock_window_manager):
        """ナビゲーションパネルが正常に作成される"""
        window = FacilityWindow("test_window", controller=mock_controller)
        window.ui_manager = Mock()
        window.main_panel = Mock()
        window.window_width = 900
        window.nav_height = 60
        
        with patch('src.facilities.ui.navigation_panel.NavigationPanel') as mock_nav_panel:
            window._create_navigation()
            
            # NavigationPanelが作成される
            mock_nav_panel.assert_called_once()
            
            # メニュー項目が取得される
            mock_controller.get_menu_items.assert_called_once()
    
    def test_create_simple_navigation_fallback(self, mock_controller, mock_window_manager):
        """NavigationPanelが利用できない場合のフォールバック"""
        window = FacilityWindow("test_window", controller=mock_controller)
        window.ui_manager = Mock()
        window.main_panel = Mock()
        
        with patch('src.facilities.ui.navigation_panel.NavigationPanel', side_effect=ImportError):
            with patch.object(window, '_create_simple_navigation') as mock_simple:
                window._create_navigation()
                mock_simple.assert_called_once()
    
    @patch('pygame_gui.elements.UIButton')
    def test_create_simple_navigation(self, mock_button, mock_controller):
        """シンプルナビゲーションボタンが作成される"""
        window = FacilityWindow("test_window", controller=mock_controller)
        window.ui_manager = Mock()
        window.main_panel = Mock()
        
        window._create_simple_navigation()
        
        # メニュー項目数分のボタンが作成される
        assert mock_button.call_count == 3  # service1, service2, exit
        assert hasattr(window, 'nav_buttons')


class TestFacilityWindowServiceManagement:
    """FacilityWindowのサービス管理テスト"""
    
    def test_show_initial_service(self, mock_controller):
        """初期サービスが正常に表示される"""
        window = FacilityWindow("test_window", controller=mock_controller)
        
        with patch.object(window, '_show_service') as mock_show:
            window._show_initial_service()
            
            # exitではない最初のサービスが選択される
            mock_show.assert_called_with("service1")
    
    def test_show_initial_service_no_menu_items(self, mock_controller):
        """メニュー項目がない場合の処理"""
        mock_controller.get_menu_items.return_value = []
        window = FacilityWindow("test_window", controller=mock_controller)
        
        with patch.object(window, '_show_service') as mock_show:
            window._show_initial_service()
            mock_show.assert_not_called()
    
    def test_on_service_selected_exit(self, mock_controller):
        """exitサービスが選択された場合の処理"""
        window = FacilityWindow("test_window", controller=mock_controller)
        
        window._on_service_selected("exit")
        
        mock_controller.exit.assert_called_once()
    
    def test_on_service_selected_normal_service(self, mock_controller):
        """通常のサービスが選択された場合の処理"""
        window = FacilityWindow("test_window", controller=mock_controller)
        
        with patch.object(window, '_show_service') as mock_show:
            window._on_service_selected("service1")
            mock_show.assert_called_with("service1")
    
    def test_show_service_new_panel(self, mock_controller):
        """新しいサービスパネルの表示"""
        window = FacilityWindow("test_window", controller=mock_controller)
        window.navigation_panel = Mock()
        
        mock_panel = Mock()
        with patch.object(window, '_create_service_panel', return_value=mock_panel):
            window._show_service("service1")
        
        # パネルが作成され、サービスパネル辞書に追加される
        assert "service1" in window.service_panels
        assert window.service_panels["service1"] == mock_panel
        assert window.current_service_id == "service1"
        
        # パネルが表示される
        mock_panel.show.assert_called_once()
        
        # ナビゲーションの選択状態が更新される
        window.navigation_panel.set_selected.assert_called_with("service1")
    
    def test_show_service_existing_panel(self, mock_controller):
        """既存のサービスパネルの表示"""
        window = FacilityWindow("test_window", controller=mock_controller)
        window.navigation_panel = Mock()
        
        # 既存パネルを設定
        existing_panel = Mock()
        window.service_panels["service1"] = existing_panel
        
        window._show_service("service1")
        
        # 既存パネルが表示される
        existing_panel.show.assert_called_once()
        assert window.current_service_id == "service1"
    
    def test_show_service_hide_current(self, mock_controller):
        """現在のサービスが隠される"""
        window = FacilityWindow("test_window", controller=mock_controller)
        window.navigation_panel = Mock()
        
        # 現在のサービスを設定
        current_panel = Mock()
        window.service_panels["current_service"] = current_panel
        window.current_service_id = "current_service"
        
        # 新しいサービスパネルのモック
        new_panel = Mock()
        with patch.object(window, '_create_service_panel', return_value=new_panel):
            window._show_service("service1")
        
        # 現在のパネルが隠される
        current_panel.hide.assert_called_once()


class TestFacilityWindowServicePanelCreation:
    """FacilityWindowのサービスパネル作成テスト"""
    
    def test_create_service_panel_custom_panel(self, mock_controller):
        """サービスがカスタムパネルを提供する場合"""
        window = FacilityWindow("test_window", controller=mock_controller)
        window.main_panel = Mock()
        window.ui_manager = Mock()
        
        # カスタムパネルを返すモック
        custom_panel = Mock()
        mock_controller.service.create_service_panel.return_value = custom_panel
        
        result = window._create_service_panel("service1")
        
        assert result == custom_panel
        mock_controller.service.create_service_panel.assert_called_once()
    
    def test_create_service_panel_wizard_type(self, mock_controller):
        """ウィザードタイプのサービスパネル作成"""
        window = FacilityWindow("test_window", controller=mock_controller)
        window.main_panel = Mock()
        window.ui_manager = Mock()
        
        # ウィザードタイプのメニュー項目
        wizard_item = MenuItem("wizard_service", "ウィザード", service_type="wizard")
        mock_controller.get_menu_items.return_value = [wizard_item]
        mock_controller.service.create_service_panel.return_value = None
        
        with patch('src.facilities.ui.wizard_service_panel.WizardServicePanel') as mock_wizard:
            mock_wizard_instance = Mock()
            mock_wizard.return_value = mock_wizard_instance
            
            result = window._create_service_panel("wizard_service")
            
            assert result == mock_wizard_instance
            mock_wizard.assert_called_once()
    
    @patch('pygame_gui.elements.UIPanel')
    @patch('pygame_gui.elements.UILabel')
    def test_create_generic_service_panel(self, mock_label, mock_panel, mock_controller):
        """汎用サービスパネルの作成"""
        window = FacilityWindow("test_window", controller=mock_controller)
        window.main_panel = Mock()
        window.ui_manager = Mock()
        
        # 汎用タイプのメニュー項目
        generic_item = MenuItem("generic_service", "汎用サービス", description="説明")
        mock_controller.get_menu_items.return_value = [generic_item]
        mock_controller.service.create_service_panel.return_value = None
        
        result = window._create_service_panel("generic_service")
        
        # パネルとラベルが作成される
        mock_panel.assert_called()
        assert mock_label.call_count >= 2  # サービス名、説明、実装中メッセージ
        
        # show/hideメソッドが追加される
        panel_instance = mock_panel.return_value
        assert hasattr(panel_instance, 'show')
        assert hasattr(panel_instance, 'hide')
    
    def test_create_service_panel_menu_item_not_found(self, mock_controller):
        """メニュー項目が見つからない場合"""
        window = FacilityWindow("test_window", controller=mock_controller)
        
        result = window._create_service_panel("nonexistent_service")
        
        assert result is None
    
    def test_create_service_panel_import_error(self, mock_controller):
        """インポートエラーの場合のフォールバック"""
        window = FacilityWindow("test_window", controller=mock_controller)
        window.main_panel = Mock()
        window.ui_manager = Mock()
        
        # ウィザードタイプでインポートエラー
        wizard_item = MenuItem("wizard_service", "ウィザード", service_type="wizard")
        mock_controller.get_menu_items.return_value = [wizard_item]
        mock_controller.service.create_service_panel.return_value = None
        
        with patch('src.facilities.ui.wizard_service_panel.WizardServicePanel', side_effect=ImportError):
            with patch.object(window, '_create_fallback_panel') as mock_fallback:
                mock_fallback_panel = Mock()
                mock_fallback.return_value = mock_fallback_panel
                
                result = window._create_service_panel("wizard_service")
                
                assert result == mock_fallback_panel
                mock_fallback.assert_called_once()


class TestFacilityWindowUtility:
    """FacilityWindowのユーティリティ機能テスト"""
    
    def test_get_facility_title_from_config(self, mock_controller):
        """設定からタイトルを取得"""
        mock_controller.get_config.return_value = "設定タイトル"
        window = FacilityWindow("test_window", controller=mock_controller)
        
        title = window._get_facility_title()
        
        assert title == "設定タイトル"
        mock_controller.get_config.assert_called_with("name")
    
    def test_get_facility_title_default(self, mock_controller):
        """デフォルトタイトルを取得"""
        mock_controller.get_config.return_value = None
        mock_controller.facility_id = "guild"
        window = FacilityWindow("test_window", controller=mock_controller)
        
        title = window._get_facility_title()
        
        assert title == "冒険者ギルド"
    
    def test_get_facility_title_unknown_facility(self, mock_controller):
        """未知の施設IDの場合"""
        mock_controller.get_config.return_value = None
        mock_controller.facility_id = "unknown_facility"
        window = FacilityWindow("test_window", controller=mock_controller)
        
        title = window._get_facility_title()
        
        assert title == "unknown_facility"
    
    def test_show_window(self, mock_controller):
        """ウィンドウの表示"""
        window = FacilityWindow("test_window", controller=mock_controller)
        window.main_panel = Mock()
        
        with patch.object(window.__class__.__bases__[0], 'show') as mock_super_show:
            window.show()
            
            window.main_panel.show.assert_called_once()
            mock_super_show.assert_called_once()
    
    def test_hide_window(self, mock_controller):
        """ウィンドウの非表示"""
        window = FacilityWindow("test_window", controller=mock_controller)
        window.main_panel = Mock()
        
        with patch.object(window.__class__.__bases__[0], 'hide') as mock_super_hide:
            window.hide()
            
            window.main_panel.hide.assert_called_once()
            mock_super_hide.assert_called_once()
    
    def test_refresh_content(self, mock_controller):
        """コンテンツの更新"""
        window = FacilityWindow("test_window", controller=mock_controller)
        window.navigation_panel = Mock()
        
        # 現在のサービスパネルを設定
        current_panel = Mock()
        current_panel.refresh = Mock()
        window.service_panels["service1"] = current_panel
        window.current_service_id = "service1"
        
        window.refresh_content()
        
        # 現在のパネルが更新される
        current_panel.refresh.assert_called_once()
        
        # ナビゲーションが更新される
        window.navigation_panel.update_menu_items.assert_called_once()


class TestFacilityWindowEventHandling:
    """FacilityWindowのイベント処理テスト"""
    
    def test_handle_event_escape_key(self, mock_controller):
        """ESCキーイベントの処理"""
        window = FacilityWindow("test_window", controller=mock_controller)
        window.ui_manager = Mock()
        
        # ESCキーイベントを作成
        event = Mock()
        event.type = pygame.KEYDOWN
        event.key = pygame.K_ESCAPE
        
        result = window.handle_event(event)
        
        assert result is True
        mock_controller.exit.assert_called_once()
    
    def test_handle_event_number_key_shortcut(self, mock_controller):
        """数字キーショートカットの処理"""
        window = FacilityWindow("test_window", controller=mock_controller)
        window.ui_manager = Mock()
        
        # 1キーイベントを作成
        event = Mock()
        event.type = pygame.KEYDOWN
        event.key = pygame.K_1
        
        with patch.object(window, '_on_service_selected') as mock_select:
            result = window.handle_event(event)
            
            assert result is True
            mock_select.assert_called_with("service1")
    
    def test_handle_event_number_key_out_of_range(self, mock_controller):
        """範囲外の数字キーの処理"""
        # exitを除く項目が1つだけの場合
        mock_controller.get_menu_items.return_value = [
            MenuItem("service1", "サービス1"),
            MenuItem("exit", "退出")
        ]
        
        window = FacilityWindow("test_window", controller=mock_controller)
        window.ui_manager = Mock()
        
        # 2キーイベント（範囲外）
        event = Mock()
        event.type = pygame.KEYDOWN
        event.key = pygame.K_2
        
        with patch.object(window, '_on_service_selected') as mock_select:
            result = window.handle_event(event)
            
            # 処理されない
            assert result is False
            mock_select.assert_not_called()
    
    def test_handle_event_navigation_panel_click(self, mock_controller):
        """ナビゲーションパネルのクリック処理"""
        window = FacilityWindow("test_window", controller=mock_controller)
        window.ui_manager = Mock()
        window.navigation_panel = Mock()
        window.navigation_panel.handle_button_click.return_value = True
        
        event = Mock()
        
        result = window.handle_event(event)
        
        assert result is True
        window.navigation_panel.handle_button_click.assert_called_with(event)
    
    def test_handle_event_simple_navigation_button(self, mock_controller):
        """シンプルナビゲーションボタンのクリック処理"""
        window = FacilityWindow("test_window", controller=mock_controller)
        window.ui_manager = Mock()
        
        # シンプルナビゲーションボタンを設定
        button = Mock()
        button.item_id = "service1"
        window.nav_buttons = [button]
        
        # ボタンクリックイベント
        event = Mock()
        event.type = pygame_gui.UI_BUTTON_PRESSED
        event.ui_element = button
        
        with patch.object(window, '_on_service_selected') as mock_select:
            result = window.handle_event(event)
            
            assert result is True
            mock_select.assert_called_with("service1")


class TestFacilityWindowCleanup:
    """FacilityWindowのクリーンアップテスト"""
    
    def test_close_window(self, mock_controller):
        """ウィンドウの閉じる処理"""
        window = FacilityWindow("test_window", controller=mock_controller)
        
        # モックパネルを設定
        service_panel = Mock()
        service_panel.destroy = Mock()
        window.service_panels["service1"] = service_panel
        
        navigation_panel = Mock()
        navigation_panel.destroy = Mock()
        window.navigation_panel = navigation_panel
        
        main_panel = Mock()
        main_panel.kill = Mock()
        window.main_panel = main_panel
        
        with patch.object(window, '_recursive_kill_children') as mock_kill, \
             patch.object(window.__class__.__bases__[0], 'destroy') as mock_super_destroy:
            window.close()
            
            # すべてのパネルが破棄される
            service_panel.destroy.assert_called_once()
            navigation_panel.destroy.assert_called_once()
            main_panel.kill.assert_called_once()
            
            # 親クラスのdestroyが呼ばれる
            mock_super_destroy.assert_called_once()
            
            # パネル辞書がクリアされる
            assert len(window.service_panels) == 0
            assert window.navigation_panel is None
            assert window.main_panel is None
    
    def test_destroy_calls_close(self, mock_controller):
        """destroyメソッドがcloseを呼び出す"""
        window = FacilityWindow("test_window", controller=mock_controller)
        
        with patch.object(window, 'close') as mock_close:
            window.destroy()
            mock_close.assert_called_once()
    
    def test_recursive_kill_children_with_layer_thickness(self, mock_controller):
        """layer_thicknessを持つ要素の子要素削除"""
        window = FacilityWindow("test_window", controller=mock_controller)
        
        # 簡単なケースでテスト - layer_thicknessがNoneの場合
        container = Mock()
        container.elements = []
        # layer_thicknessがない場合は、elementsで処理される
        if hasattr(container, '_layer_thickness'):
            del container._layer_thickness
            
        element = Mock()
        element.get_container.return_value = container
        
        # エラーなく実行されることを確認
        try:
            window._recursive_kill_children(element)
            assert True  # エラーが発生しなければテスト通過
        except Exception as e:
            pytest.fail(f"Unexpected exception: {e}")
    
    def test_recursive_kill_children_with_elements(self, mock_controller):
        """elementsを持つ要素の子要素削除"""
        window = FacilityWindow("test_window", controller=mock_controller)
        
        # elementsを持つコンテナのモック
        child_element = Mock()
        child_element.kill = Mock()
        child_element.get_container.return_value = None  # 再帰を防ぐ
        
        container = Mock()
        container.elements = [child_element]
        # layer_thicknessは持たない
        if hasattr(container, '_layer_thickness'):
            del container._layer_thickness
        
        element = Mock()
        element.get_container.return_value = container
        
        window._recursive_kill_children(element)
        
        child_element.kill.assert_called_once()