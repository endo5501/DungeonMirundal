"""状態回復パネルのテスト"""

import pytest
import pygame
import pygame_gui
from unittest.mock import Mock, MagicMock, patch


@pytest.fixture
def mock_ui_setup():
    """UI要素のモック"""
    rect = pygame.Rect(0, 0, 420, 400)
    parent = Mock()
    ui_manager = Mock()
    controller = Mock()
    service = Mock()
    return rect, parent, ui_manager, controller, service


@pytest.fixture
def sample_afflicted_members():
    """サンプル状態異常メンバーデータ"""
    return [
        {
            "id": "char1",
            "name": "戦士アレン",
            "level": 5,
            "status": "poisoned",
            "status_name": "毒"
        },
        {
            "id": "char2",
            "name": "魔法使いベラ",
            "level": 3,
            "status": "cursed",
            "status_name": "呪い"
        }
    ]


@pytest.fixture
def sample_character_detail():
    """サンプルキャラクター詳細データ"""
    return {
        "status": "poisoned",
        "status_name": "毒",
        "cost": 250,
        "party_gold": 2000
    }


@pytest.fixture
def sample_service_result():
    """サンプルサービス結果"""
    def create_result(success=True, data=None, message="", result_type=None):
        result = Mock()
        result.success = success
        result.data = data or {}
        result.message = message
        result.result_type = result_type or Mock()
        result.result_type.name = "SUCCESS" if success else "ERROR"
        return result
    return create_result


class TestCurePanelBasic:
    """CurePanelの基本機能テスト"""
    
    def test_initialization(self, mock_ui_setup):
        """正常に初期化される"""
        from src.facilities.ui.temple.cure_panel import CurePanel
        
        rect, parent, ui_manager, controller, service = mock_ui_setup
        
        with patch('pygame_gui.elements.UIPanel'), \
             patch('pygame_gui.elements.UILabel'), \
             patch('pygame_gui.elements.UISelectionList'), \
             patch('pygame_gui.elements.UIButton'), \
             patch.object(CurePanel, '_refresh_members'):
            
            panel = CurePanel(rect, parent, ui_manager, controller, service)
            
            # 基本属性の確認
            assert panel.rect == rect
            assert panel.parent == parent
            assert panel.ui_manager == ui_manager
            assert panel.controller == controller
            assert panel.service == service
            
            # 初期状態の確認
            assert panel.selected_member is None
            assert panel.selected_status is None
            assert panel.members_data == []
            assert panel.current_character_data is None
    
    def test_create_ui_elements(self, mock_ui_setup):
        """UI要素が正常に作成される"""
        from src.facilities.ui.temple.cure_panel import CurePanel
        
        rect, parent, ui_manager, controller, service = mock_ui_setup
        
        with patch('pygame_gui.elements.UIPanel') as mock_panel, \
             patch('pygame_gui.elements.UILabel') as mock_label, \
             patch('pygame_gui.elements.UISelectionList') as mock_list, \
             patch('pygame_gui.elements.UIButton') as mock_button, \
             patch.object(CurePanel, '_refresh_members'):
            
            mock_button_instance = Mock()
            mock_button.return_value = mock_button_instance
            
            panel = CurePanel(rect, parent, ui_manager, controller, service)
            
            # UI要素が作成される
            mock_panel.assert_called_once()
            assert mock_label.call_count == 5  # タイトル、状態、コスト、所持金、結果
            mock_list.assert_called_once()
            mock_button.assert_called_once()
            
            # 治療ボタンが初期無効化される
            mock_button_instance.disable.assert_called_once()


class TestCurePanelDataLoading:
    """CurePanelのデータ読み込みテスト"""
    
    def test_refresh_members_success(self, mock_ui_setup, sample_service_result, sample_afflicted_members):
        """メンバー更新成功"""
        from src.facilities.ui.temple.cure_panel import CurePanel
        
        panel = Mock()
        panel.service = Mock()
        panel.members_list = Mock()
        panel.result_label = Mock()
        
        # サービス結果のモック
        result = sample_service_result(
            success=True,
            data={"members": sample_afflicted_members},
            message="状態異常のメンバーが見つかりました"
        )
        panel.service.execute_action.return_value = result
        
        CurePanel._refresh_members(panel)
        
        # データが設定される
        assert panel.members_data == sample_afflicted_members
        
        # リストが更新される
        expected_items = [
            "戦士アレン (Lv.5) - 毒",
            "魔法使いベラ (Lv.3) - 呪い"
        ]
        panel.members_list.set_item_list.assert_called_with(expected_items)
        
        # 結果メッセージが表示される
        panel.result_label.set_text.assert_called_with("状態異常のメンバーが見つかりました")
    
    def test_refresh_members_failure(self, mock_ui_setup, sample_service_result):
        """メンバー更新失敗"""
        from src.facilities.ui.temple.cure_panel import CurePanel
        
        panel = Mock()
        panel.service = Mock()
        panel.members_list = Mock()
        panel.result_label = Mock()
        panel.members_data = []
        
        # 失敗結果
        result = sample_service_result(
            success=False,
            message="状態異常のメンバーはいません"
        )
        panel.service.execute_action.return_value = result
        
        CurePanel._refresh_members(panel)
        
        # 空リストが設定される
        panel.members_list.set_item_list.assert_called_with([])
        assert panel.members_data == []
        
        # エラーメッセージが表示される
        panel.result_label.set_text.assert_called_with("状態異常のメンバーはいません")
    
    def test_refresh_character_ailments_success(self, sample_service_result, sample_character_detail):
        """キャラクター状態異常詳細取得成功"""
        from src.facilities.ui.temple.cure_panel import CurePanel
        
        panel = Mock()
        panel.service = Mock()
        panel.status_label = Mock()
        panel.cost_label = Mock()
        panel.gold_label = Mock()
        panel.cure_button = Mock()
        panel.result_label = Mock()
        
        # サービス結果のモック
        result = sample_service_result(
            success=True,
            data=sample_character_detail
        )
        panel.service.execute_action.return_value = result
        
        CurePanel._refresh_character_ailments(panel, "char1")
        
        # データが設定される
        assert panel.current_character_data == sample_character_detail
        assert panel.selected_status == "poisoned"
        
        # UI表示が更新される
        panel.status_label.set_text.assert_called_with("状態: 毒")
        panel.cost_label.set_text.assert_called_with("費用: 250 G")
        panel.gold_label.set_text.assert_called_with("所持金: 2000 G")
        
        # 治療ボタンが有効化される
        panel.cure_button.enable.assert_called_once()
        
        # 結果がクリアされる
        panel.result_label.set_text.assert_called_with("")
    
    def test_refresh_character_ailments_failure(self, sample_service_result):
        """キャラクター状態異常詳細取得失敗"""
        from src.facilities.ui.temple.cure_panel import CurePanel
        
        panel = Mock()
        panel.service = Mock()
        panel.cure_button = Mock()
        panel.result_label = Mock()
        
        # 失敗結果
        result = sample_service_result(
            success=False,
            message="キャラクターが見つかりません"
        )
        panel.service.execute_action.return_value = result
        
        CurePanel._refresh_character_ailments(panel, "invalid_char")
        
        # ボタンが無効化される
        panel.cure_button.disable.assert_called_once()
        
        # エラーメッセージが表示される
        panel.result_label.set_text.assert_called_with("キャラクターが見つかりません")


class TestCurePanelEventHandling:
    """CurePanelのイベント処理テスト"""
    
    def test_handle_event_member_selection(self, sample_afflicted_members):
        """メンバー選択イベントの処理"""
        from src.facilities.ui.temple.cure_panel import CurePanel
        
        panel = Mock()
        panel.members_data = sample_afflicted_members
        panel.members_list = Mock()
        panel.selected_member = None
        
        # 選択イベントのモック
        event = Mock()
        event.type = pygame_gui.UI_SELECTION_LIST_NEW_SELECTION
        event.ui_element = panel.members_list
        
        # メンバーが選択された
        panel.members_list.get_single_selection.return_value = 0
        
        with patch.object(panel, '_refresh_character_ailments') as mock_refresh:
            CurePanel.handle_event(panel, event)
            
            # 選択されたメンバーが設定される
            assert panel.selected_member == "char1"
            
            # キャラクター詳細が取得される
            mock_refresh.assert_called_with("char1")
    
    def test_handle_event_cure_button(self):
        """治療ボタン押下イベントの処理"""
        from src.facilities.ui.temple.cure_panel import CurePanel
        
        panel = Mock()
        panel.cure_button = Mock()
        
        # ボタン押下イベントのモック
        event = Mock()
        event.type = pygame_gui.UI_BUTTON_PRESSED
        event.ui_element = panel.cure_button
        
        with patch.object(panel, '_perform_cure') as mock_cure:
            CurePanel.handle_event(panel, event)
            
            mock_cure.assert_called_once()


class TestCurePanelCurePerformance:
    """CurePanelの治療実行テスト"""
    
    def test_perform_cure_success(self, sample_service_result):
        """状態回復実行成功"""
        from src.facilities.ui.temple.cure_panel import CurePanel
        
        panel = Mock()
        panel.selected_member = "char1"
        panel.selected_status = "poisoned"
        panel.service = Mock()
        panel.result_label = Mock()
        panel.cure_button = Mock()
        panel.cost_label = Mock()
        panel.status_label = Mock()
        panel.gold_label = Mock()
        
        # 確認結果
        confirm_result = sample_service_result(
            success=True,
            result_type=Mock()
        )
        confirm_result.result_type.name = "CONFIRM"
        
        # 実行結果
        execute_result = sample_service_result(
            success=True,
            message="戦士アレンの毒を治療しました"
        )
        
        panel.service.execute_action.side_effect = [confirm_result, execute_result]
        
        with patch.object(panel, '_refresh_members') as mock_refresh:
            CurePanel._perform_cure(panel)
            
            # サービスが2回呼ばれる（確認、実行）
            assert panel.service.execute_action.call_count == 2
            
            # 確認呼び出し
            panel.service.execute_action.assert_any_call("cure", {
                "character_id": "char1",
                "status_type": "poisoned"
            })
            
            # 実行呼び出し
            panel.service.execute_action.assert_any_call("cure", {
                "character_id": "char1",
                "status_type": "poisoned",
                "confirmed": True
            })
            
            # 成功メッセージが表示される
            panel.result_label.set_text.assert_called_with("戦士アレンの毒を治療しました")
            
            # リストがリフレッシュされる
            mock_refresh.assert_called_once()
            
            # 選択がクリアされる
            assert panel.selected_member is None
            assert panel.selected_status is None
            panel.cure_button.disable.assert_called_once()
            panel.cost_label.set_text.assert_called_with("費用: -")
            panel.status_label.set_text.assert_called_with("状態: -")
            panel.gold_label.set_text.assert_called_with("所持金: 0 G")
    
    def test_perform_cure_failure(self, sample_service_result):
        """状態回復実行失敗"""
        from src.facilities.ui.temple.cure_panel import CurePanel
        
        panel = Mock()
        panel.selected_member = "char1"
        panel.selected_status = "poisoned"
        panel.service = Mock()
        panel.result_label = Mock()
        
        # 失敗結果
        result = sample_service_result(
            success=False,
            message="所持金が不足しています"
        )
        panel.service.execute_action.return_value = result
        
        CurePanel._perform_cure(panel)
        
        # エラーメッセージが表示される
        panel.result_label.set_text.assert_called_with("所持金が不足しています")
    
    def test_perform_cure_no_member_selection(self):
        """メンバー未選択での治療実行"""
        from src.facilities.ui.temple.cure_panel import CurePanel
        
        panel = Mock()
        panel.selected_member = None
        panel.selected_status = "poisoned"
        panel.service = Mock()
        
        CurePanel._perform_cure(panel)
        
        # サービスが呼ばれない
        panel.service.execute_action.assert_not_called()
    
    def test_perform_cure_no_status_selection(self):
        """状態未選択での治療実行"""
        from src.facilities.ui.temple.cure_panel import CurePanel
        
        panel = Mock()
        panel.selected_member = "char1"
        panel.selected_status = None
        panel.service = Mock()
        
        CurePanel._perform_cure(panel)
        
        # サービスが呼ばれない
        panel.service.execute_action.assert_not_called()


class TestCurePanelActions:
    """CurePanelのアクション機能テスト"""
    
    def test_refresh(self):
        """パネルのリフレッシュ"""
        from src.facilities.ui.temple.cure_panel import CurePanel
        
        panel = Mock()
        panel.selected_member = "char1"
        panel.selected_status = "poisoned"
        panel.current_character_data = {"test": "data"}
        panel.cure_button = Mock()
        panel.cost_label = Mock()
        panel.status_label = Mock()
        panel.gold_label = Mock()
        panel.result_label = Mock()
        
        with patch.object(panel, '_refresh_members') as mock_refresh:
            CurePanel.refresh(panel)
            
            # データがリフレッシュされる
            mock_refresh.assert_called_once()
            
            # 選択がクリアされる
            assert panel.selected_member is None
            assert panel.selected_status is None
            assert panel.current_character_data is None
            
            # ボタンが無効化される
            panel.cure_button.disable.assert_called_once()
            
            # 表示がリセットされる
            panel.cost_label.set_text.assert_called_with("費用: -")
            panel.status_label.set_text.assert_called_with("状態: -")
            panel.gold_label.set_text.assert_called_with("所持金: 0 G")
            panel.result_label.set_text.assert_called_with("")
    
    def test_show(self):
        """パネル表示"""
        from src.facilities.ui.temple.cure_panel import CurePanel
        
        panel = Mock()
        panel.container = Mock()
        
        CurePanel.show(panel)
        
        panel.container.show.assert_called_once()
    
    def test_hide(self):
        """パネル非表示"""
        from src.facilities.ui.temple.cure_panel import CurePanel
        
        panel = Mock()
        panel.container = Mock()
        
        CurePanel.hide(panel)
        
        panel.container.hide.assert_called_once()
    
    def test_destroy(self):
        """パネル破棄"""
        from src.facilities.ui.temple.cure_panel import CurePanel
        
        panel = Mock()
        panel.container = Mock()
        
        CurePanel.destroy(panel)
        
        panel.container.kill.assert_called_once()
    
    def test_show_hide_destroy_no_container(self):
        """コンテナなしでの表示・非表示・破棄"""
        from src.facilities.ui.temple.cure_panel import CurePanel
        
        panel = Mock()
        panel.container = None
        
        # エラーが発生しないことを確認
        try:
            CurePanel.show(panel)
            CurePanel.hide(panel)
            CurePanel.destroy(panel)
            assert True
        except Exception as e:
            pytest.fail(f"Unexpected exception: {e}")