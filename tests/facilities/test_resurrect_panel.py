"""蘇生パネルのテスト（簡略化版）"""

import pytest
import pygame
import pygame_gui
from unittest.mock import Mock, MagicMock, patch


@pytest.fixture
def mock_ui_setup():
    """UI要素のモック"""
    rect = pygame.Rect(0, 0, 420, 360)
    parent = Mock()
    ui_manager = Mock()
    controller = Mock()
    
    # ServicePanelパターンに合わせてコントローラー経由でサービスにアクセス
    service = Mock()
    controller.service = service
    
    return rect, parent, ui_manager, controller


@pytest.fixture
def sample_dead_members():
    """サンプル死亡メンバーデータ"""
    return [
        {
            "id": "char1",
            "name": "戦士アレン",
            "level": 5,
            "status": "dead",
            "vitality": 8,
            "cost": 5000
        },
        {
            "id": "char2",
            "name": "魔法使いベラ",
            "level": 3,
            "status": "ash",
            "vitality": 3,
            "cost": 8000
        },
        {
            "id": "char3",
            "name": "盗賊チャーリー",
            "level": 4,
            "status": "dead",
            "vitality": 0,
            "cost": 12000
        }
    ]


class TestResurrectPanelBasic:
    """ResurrectPanelの基本機能テスト"""
    
    def test_initialization(self, mock_ui_setup):
        """正常に初期化される"""
        from src.facilities.ui.temple.resurrect_panel import ResurrectPanel
        
        rect, parent, ui_manager, controller = mock_ui_setup
        
        with patch('src.facilities.ui.service_panel.ServicePanel.__init__', return_value=None):
            panel = ResurrectPanel(rect, parent, controller, ui_manager)
            
            # UI要素の初期状態確認（Noneで初期化される）
            assert panel.title_label is None
            assert panel.members_list is None
            assert panel.resurrect_button is None
            assert panel.cost_label is None
            assert panel.gold_label is None
            assert panel.vitality_label is None
            assert panel.result_label is None
            
            # 初期状態の確認
            assert panel.selected_member is None
            assert panel.members_data == []
    
    def test_create_ui_elements(self, mock_ui_setup):
        """UI要素が正常に作成される（モジュラー構造）"""
        from src.facilities.ui.temple.resurrect_panel import ResurrectPanel
        
        rect, parent, ui_manager, controller = mock_ui_setup
        
        with patch('src.facilities.ui.service_panel.ServicePanel.__init__', return_value=None):
            panel = ResurrectPanel(rect, parent, controller, ui_manager)
            
            # UIElementManagerをNoneに設定してフォールバック動作を強制
            panel.ui_element_manager = None
            panel.container = Mock()
            panel.ui_elements = []
            
            # モジュラーメソッドを直接モック
            with patch.object(panel, '_create_header') as mock_header, \
                 patch.object(panel, '_create_member_list') as mock_list, \
                 patch.object(panel, '_create_action_controls') as mock_action, \
                 patch.object(panel, '_create_status_display') as mock_status, \
                 patch.object(panel, '_refresh_members') as mock_refresh:
                
                panel._create_ui()
                
                # 各メソッドが呼ばれることを確認
                mock_header.assert_called_once()
                mock_list.assert_called_once()
                mock_action.assert_called_once()
                mock_status.assert_called_once()
                mock_refresh.assert_called_once()


class TestResurrectPanelUICreation:
    """ResurrectPanelのUI作成テスト（実際のUI要素作成）"""
    
    def test_create_header_with_fallback(self, mock_ui_setup):
        """ヘッダー作成（フォールバックモード）"""
        from src.facilities.ui.temple.resurrect_panel import ResurrectPanel
        
        rect, parent, ui_manager, controller = mock_ui_setup
        
        with patch('src.facilities.ui.service_panel.ServicePanel.__init__', return_value=None):
            panel = ResurrectPanel(rect, parent, controller, ui_manager)
            panel.ui_element_manager = None
            panel.container = Mock()
            panel.ui_elements = []
            panel.ui_manager = ui_manager
            
            with patch('pygame_gui.elements.UILabel') as mock_label:
                panel._create_header()
                
                # タイトルラベルが作成される
                assert mock_label.call_count == 1
                call_args = mock_label.call_args
                assert "蘇生 - 死亡したメンバーを選択してください" in call_args[1]['text']
    
    def test_create_member_list_with_fallback(self, mock_ui_setup):
        """メンバーリスト作成（フォールバックモード）"""
        from src.facilities.ui.temple.resurrect_panel import ResurrectPanel
        
        rect, parent, ui_manager, controller = mock_ui_setup
        
        with patch('src.facilities.ui.service_panel.ServicePanel.__init__', return_value=None):
            panel = ResurrectPanel(rect, parent, controller, ui_manager)
            panel.ui_element_manager = None
            panel.container = Mock()
            panel.ui_elements = []
            panel.ui_manager = ui_manager
            
            with patch('pygame_gui.elements.UISelectionList') as mock_list:
                panel._create_member_list()
                
                # メンバーリストが作成される
                mock_list.assert_called_once()
                call_args = mock_list.call_args
                assert call_args[1]['item_list'] == []  # 初期状態では空


class TestResurrectPanelActions:
    """ResurrectPanelのアクション機能テスト（基本的な動作）"""
    
    def test_refresh_basic_functionality(self, mock_ui_setup):
        """基本的なリフレッシュ機能"""
        from src.facilities.ui.temple.resurrect_panel import ResurrectPanel
        
        rect, parent, ui_manager, controller = mock_ui_setup
        
        with patch('src.facilities.ui.service_panel.ServicePanel.__init__', return_value=None):
            panel = ResurrectPanel(rect, parent, controller, ui_manager)
            panel.resurrect_button = Mock()
            panel.cost_label = Mock()
            panel.vitality_label = Mock()
            panel.result_label = Mock()
            
            with patch.object(panel, '_refresh_members') as mock_refresh:
                panel.refresh()
                
                # 情報がリフレッシュされる
                mock_refresh.assert_called_once()
                
                # 状態がリセットされる
                assert panel.selected_member is None
                panel.resurrect_button.disable.assert_called_once()
                panel.cost_label.set_text.assert_called_with("費用: -")
                panel.vitality_label.set_text.assert_called_with("生命力: -")
                panel.result_label.set_text.assert_called_with("")
    
    def test_button_click_handling(self, mock_ui_setup):
        """ボタンクリック処理（ServicePanelパターン）"""
        from src.facilities.ui.temple.resurrect_panel import ResurrectPanel
        
        rect, parent, ui_manager, controller = mock_ui_setup
        
        with patch('src.facilities.ui.service_panel.ServicePanel.__init__', return_value=None):
            panel = ResurrectPanel(rect, parent, controller, ui_manager)
            panel.resurrect_button = Mock()
            
            with patch.object(panel, '_perform_resurrect') as mock_resurrect:
                # 蘇生ボタンのクリック
                result = panel.handle_button_click(panel.resurrect_button)
                
                assert result is True
                mock_resurrect.assert_called_once()
                
                # 関係ないボタンのクリック
                other_button = Mock()
                result = panel.handle_button_click(other_button)
                assert result is False
    
    def test_selection_list_changed_handling(self, mock_ui_setup):
        """リスト選択変更処理"""
        from src.facilities.ui.temple.resurrect_panel import ResurrectPanel
        
        rect, parent, ui_manager, controller = mock_ui_setup
        
        with patch('src.facilities.ui.service_panel.ServicePanel.__init__', return_value=None):
            panel = ResurrectPanel(rect, parent, controller, ui_manager)
            panel.members_list = Mock()
            panel.cost_label = Mock()
            panel.vitality_label = Mock()
            panel.resurrect_button = Mock()
            panel.result_label = Mock()
            
            # メンバーデータを設定
            panel.members_data = [
                {"id": "char1", "cost": 5000, "vitality": 8}
            ]
            
            # 選択イベントをモック
            event = Mock()
            event.ui_element = panel.members_list
            panel.members_list.get_single_selection.return_value = 0
            
            result = panel.handle_selection_list_changed(event)
            
            assert result is True
            assert panel.selected_member == "char1"
            panel.cost_label.set_text.assert_called_with("費用: 5000 G")
            panel.vitality_label.set_text.assert_called_with("生命力: 8")
            panel.resurrect_button.enable.assert_called_once()


class TestResurrectPanelServiceIntegration:
    """ResurrectPanelのサービス統合テスト"""
    
    def test_service_action_execution(self, mock_ui_setup):
        """サービスアクション実行テスト"""
        from src.facilities.ui.temple.resurrect_panel import ResurrectPanel
        
        rect, parent, ui_manager, controller = mock_ui_setup
        
        with patch('src.facilities.ui.service_panel.ServicePanel.__init__', return_value=None):
            panel = ResurrectPanel(rect, parent, controller, ui_manager)
            panel.result_label = Mock()
            panel.selected_member = "char1"
            
            # _execute_service_actionをモック
            mock_result = Mock()
            mock_result.success = False
            mock_result.message = "蘇生に失敗しました"
            
            with patch.object(panel, '_execute_service_action', return_value=mock_result):
                panel._perform_resurrect()
                
                # エラーメッセージが表示される
                panel.result_label.set_text.assert_called_with("蘇生に失敗しました")