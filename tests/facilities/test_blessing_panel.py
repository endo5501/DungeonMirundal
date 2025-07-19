"""祝福パネルのテスト（簡略化版）"""

import pytest
import pygame
import pygame_gui
from unittest.mock import Mock, MagicMock, patch


@pytest.fixture
def mock_ui_setup():
    """UI要素のモック"""
    rect = pygame.Rect(0, 0, 420, 380)
    parent = Mock()
    ui_manager = Mock()
    controller = Mock()
    
    # ServicePanelパターンに合わせてコントローラー経由でサービスにアクセス
    service = Mock()
    service.blessing_cost = 500
    controller.service = service
    
    return rect, parent, ui_manager, controller


class TestBlessingPanelBasic:
    """BlessingPanelの基本機能テスト"""
    
    def test_initialization(self, mock_ui_setup):
        """正常に初期化される"""
        from src.facilities.ui.temple.blessing_panel import BlessingPanel
        
        rect, parent, ui_manager, controller = mock_ui_setup
        
        with patch('src.facilities.ui.service_panel.ServicePanel.__init__', return_value=None):
            panel = BlessingPanel(rect, parent, controller, ui_manager)
            
            # UI要素の初期状態確認（Noneで初期化される）
            assert panel.title_label is None
            assert panel.description_box is None
            assert panel.blessing_button is None
            assert panel.cost_label is None
            assert panel.gold_label is None
            assert panel.result_label is None
    
    def test_create_ui_elements(self, mock_ui_setup):
        """UI要素が正常に作成される（モジュラー構造）"""
        from src.facilities.ui.temple.blessing_panel import BlessingPanel
        
        rect, parent, ui_manager, controller = mock_ui_setup
        
        with patch('src.facilities.ui.service_panel.ServicePanel.__init__', return_value=None):
            panel = BlessingPanel(rect, parent, controller, ui_manager)
            
            # UIElementManagerをNoneに設定してフォールバック動作を強制
            panel.ui_element_manager = None
            panel.container = Mock()
            panel.ui_elements = []
            
            # モジュラーメソッドを直接モック
            with patch.object(panel, '_create_header') as mock_header, \
                 patch.object(panel, '_create_description') as mock_desc, \
                 patch.object(panel, '_create_action_controls') as mock_action, \
                 patch.object(panel, '_create_status_display') as mock_status, \
                 patch.object(panel, '_refresh_info') as mock_refresh:
                
                panel._create_ui()
                
                # 各メソッドが呼ばれることを確認
                mock_header.assert_called_once()
                mock_desc.assert_called_once()
                mock_action.assert_called_once()
                mock_status.assert_called_once()
                mock_refresh.assert_called_once()


class TestBlessingPanelUICreation:
    """BlessingPanelのUI作成テスト（実際のUI要素作成）"""
    
    def test_create_header_with_fallback(self, mock_ui_setup):
        """ヘッダー作成（フォールバックモード）"""
        from src.facilities.ui.temple.blessing_panel import BlessingPanel
        
        rect, parent, ui_manager, controller = mock_ui_setup
        
        with patch('src.facilities.ui.service_panel.ServicePanel.__init__', return_value=None):
            panel = BlessingPanel(rect, parent, controller, ui_manager)
            panel.ui_element_manager = None
            panel.container = Mock()
            panel.ui_elements = []
            panel.ui_manager = ui_manager
            
            with patch('pygame_gui.elements.UILabel') as mock_label:
                panel._create_header()
                
                # タイトルラベルが作成される
                assert mock_label.call_count == 1
                call_args = mock_label.call_args
                assert "祝福 - パーティに神の加護を" in call_args[1]['text']
    
    def test_create_description_with_fallback(self, mock_ui_setup):
        """説明作成（フォールバックモード）"""
        from src.facilities.ui.temple.blessing_panel import BlessingPanel
        
        rect, parent, ui_manager, controller = mock_ui_setup
        
        with patch('src.facilities.ui.service_panel.ServicePanel.__init__', return_value=None):
            panel = BlessingPanel(rect, parent, controller, ui_manager)
            panel.ui_element_manager = None
            panel.container = Mock()
            panel.ui_elements = []
            panel.ui_manager = ui_manager
            
            with patch('pygame_gui.elements.UITextBox') as mock_text_box:
                panel._create_description()
                
                # 説明テキストボックスが作成される
                mock_text_box.assert_called_once()
                call_args = mock_text_box.call_args
                html_text = call_args[1]['html_text']
                
                # 祝福の効果説明が含まれる
                assert "攻撃力・防御力が上昇" in html_text
                assert "クリティカル率が向上" in html_text
                assert "効果は1回の戦闘まで持続" in html_text


class TestBlessingPanelActions:
    """BlessingPanelのアクション機能テスト（基本的な動作）"""
    
    def test_refresh_basic_functionality(self, mock_ui_setup):
        """基本的なリフレッシュ機能"""
        from src.facilities.ui.temple.blessing_panel import BlessingPanel
        
        rect, parent, ui_manager, controller = mock_ui_setup
        
        with patch('src.facilities.ui.service_panel.ServicePanel.__init__', return_value=None):
            panel = BlessingPanel(rect, parent, controller, ui_manager)
            panel.result_label = Mock()
            
            with patch.object(panel, '_refresh_info') as mock_refresh:
                panel.refresh()
                
                # 情報がリフレッシュされる
                mock_refresh.assert_called_once()
                
                # 結果表示がクリアされる
                panel.result_label.set_text.assert_called_with("")
    
    def test_button_click_handling(self, mock_ui_setup):
        """ボタンクリック処理（ServicePanelパターン）"""
        from src.facilities.ui.temple.blessing_panel import BlessingPanel
        
        rect, parent, ui_manager, controller = mock_ui_setup
        
        with patch('src.facilities.ui.service_panel.ServicePanel.__init__', return_value=None):
            panel = BlessingPanel(rect, parent, controller, ui_manager)
            panel.blessing_button = Mock()
            
            with patch.object(panel, '_perform_blessing') as mock_blessing:
                # 祝福ボタンのクリック
                result = panel.handle_button_click(panel.blessing_button)
                
                assert result is True
                mock_blessing.assert_called_once()
                
                # 関係ないボタンのクリック
                other_button = Mock()
                result = panel.handle_button_click(other_button)
                assert result is False


class TestBlessingPanelServiceIntegration:
    """BlessingPanelのサービス統合テスト"""
    
    def test_service_action_execution(self, mock_ui_setup):
        """サービスアクション実行テスト"""
        from src.facilities.ui.temple.blessing_panel import BlessingPanel
        
        rect, parent, ui_manager, controller = mock_ui_setup
        
        with patch('src.facilities.ui.service_panel.ServicePanel.__init__', return_value=None):
            panel = BlessingPanel(rect, parent, controller, ui_manager)
            panel.result_label = Mock()
            
            # _execute_service_actionをモック
            mock_result = Mock()
            mock_result.success = False
            mock_result.message = "テストエラー"
            
            with patch.object(panel, '_execute_service_action', return_value=mock_result):
                panel._perform_blessing()
                
                # エラーメッセージが表示される
                panel.result_label.set_text.assert_called_with("テストエラー")