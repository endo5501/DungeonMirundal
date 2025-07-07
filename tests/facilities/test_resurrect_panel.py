"""蘇生パネルのテスト"""

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
    service = Mock()
    return rect, parent, ui_manager, controller, service


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


class TestResurrectPanelBasic:
    """ResurrectPanelの基本機能テスト"""
    
    def test_initialization(self, mock_ui_setup):
        """正常に初期化される"""
        from src.facilities.ui.temple.resurrect_panel import ResurrectPanel
        
        rect, parent, ui_manager, controller, service = mock_ui_setup
        
        with patch('pygame_gui.elements.UIPanel'), \
             patch('pygame_gui.elements.UILabel'), \
             patch('pygame_gui.elements.UISelectionList'), \
             patch('pygame_gui.elements.UIButton'), \
             patch.object(ResurrectPanel, '_refresh_members'):
            
            panel = ResurrectPanel(rect, parent, ui_manager, controller, service)
            
            # 基本属性の確認
            assert panel.rect == rect
            assert panel.parent == parent
            assert panel.ui_manager == ui_manager
            assert panel.controller == controller
            assert panel.service == service
            
            # 初期状態の確認
            assert panel.selected_member is None
            assert panel.members_data == []
    
    def test_create_ui_elements(self, mock_ui_setup):
        """UI要素が正常に作成される"""
        from src.facilities.ui.temple.resurrect_panel import ResurrectPanel
        
        rect, parent, ui_manager, controller, service = mock_ui_setup
        
        with patch('pygame_gui.elements.UIPanel') as mock_panel, \
             patch('pygame_gui.elements.UILabel') as mock_label, \
             patch('pygame_gui.elements.UISelectionList') as mock_list, \
             patch('pygame_gui.elements.UIButton') as mock_button, \
             patch.object(ResurrectPanel, '_refresh_members'):
            
            mock_button_instance = Mock()
            mock_button.return_value = mock_button_instance
            
            panel = ResurrectPanel(rect, parent, ui_manager, controller, service)
            
            # UI要素が作成される
            mock_panel.assert_called_once()
            assert mock_label.call_count == 5  # タイトル、コスト、所持金、生命力、結果
            mock_list.assert_called_once()
            mock_button.assert_called_once()
            
            # 蘇生ボタンが初期無効化される
            mock_button_instance.disable.assert_called_once()


class TestResurrectPanelDataLoading:
    """ResurrectPanelのデータ読み込みテスト"""
    
    def test_refresh_members_success(self, mock_ui_setup, sample_service_result, sample_dead_members):
        """メンバー更新成功"""
        from src.facilities.ui.temple.resurrect_panel import ResurrectPanel
        
        panel = Mock()
        panel.service = Mock()
        panel.members_list = Mock()
        panel.gold_label = Mock()
        panel.result_label = Mock()
        
        # サービス結果のモック
        result = sample_service_result(
            success=True,
            data={
                "members": sample_dead_members,
                "party_gold": 15000
            },
            message="蘇生可能なメンバーが見つかりました"
        )
        panel.service.execute_action.return_value = result
        
        ResurrectPanel._refresh_members(panel)
        
        # データが設定される
        assert panel.members_data == sample_dead_members
        
        # リストが更新される
        expected_items = [
            "戦士アレン (Lv.5) - 死亡 - 生命力:8 - 5000 G",
            "魔法使いベラ (Lv.3) - 灰 - 生命力:3 - 8000 G",
            "盗賊チャーリー (Lv.4) - 死亡 - 生命力:0 - 12000 G"
        ]
        panel.members_list.set_item_list.assert_called_with(expected_items)
        
        # 所持金が更新される
        panel.gold_label.set_text.assert_called_with("所持金: 15000 G")
        
        # 結果メッセージが表示される
        panel.result_label.set_text.assert_called_with("蘇生可能なメンバーが見つかりました")
    
    def test_refresh_members_failure(self, mock_ui_setup, sample_service_result):
        """メンバー更新失敗"""
        from src.facilities.ui.temple.resurrect_panel import ResurrectPanel
        
        panel = Mock()
        panel.service = Mock()
        panel.members_list = Mock()
        panel.result_label = Mock()
        panel.members_data = []
        
        # 失敗結果
        result = sample_service_result(
            success=False,
            message="蘇生が必要なメンバーはいません"
        )
        panel.service.execute_action.return_value = result
        
        ResurrectPanel._refresh_members(panel)
        
        # 空リストが設定される
        panel.members_list.set_item_list.assert_called_with([])
        assert panel.members_data == []
        
        # エラーメッセージが表示される
        panel.result_label.set_text.assert_called_with("蘇生が必要なメンバーはいません")
    
    def test_refresh_members_no_message(self, mock_ui_setup, sample_service_result):
        """メッセージなしの場合のメンバー更新"""
        from src.facilities.ui.temple.resurrect_panel import ResurrectPanel
        
        panel = Mock()
        panel.service = Mock()
        panel.members_list = Mock()
        panel.result_label = Mock()
        
        # メッセージなしの失敗結果
        result = sample_service_result(success=False, message="")
        panel.service.execute_action.return_value = result
        
        ResurrectPanel._refresh_members(panel)
        
        # デフォルトメッセージが表示される
        panel.result_label.set_text.assert_called_with("蘇生が必要なメンバーはいません")


class TestResurrectPanelEventHandling:
    """ResurrectPanelのイベント処理テスト"""
    
    def test_handle_event_member_selection_valid_vitality(self, sample_dead_members):
        """生命力のあるメンバー選択イベントの処理"""
        from src.facilities.ui.temple.resurrect_panel import ResurrectPanel
        
        panel = Mock()
        panel.members_data = sample_dead_members
        panel.members_list = Mock()
        panel.selected_member = None
        panel.cost_label = Mock()
        panel.vitality_label = Mock()
        panel.resurrect_button = Mock()
        panel.result_label = Mock()
        
        # 選択イベントのモック
        event = Mock()
        event.type = pygame_gui.UI_SELECTION_LIST_NEW_SELECTION
        event.ui_element = panel.members_list
        
        # 生命力のあるメンバーが選択された
        panel.members_list.get_single_selection.return_value = 0  # 戦士アレン（生命力8）
        
        ResurrectPanel.handle_event(panel, event)
        
        # 選択されたメンバーが設定される
        assert panel.selected_member == "char1"
        
        # コスト・生命力表示が更新される
        panel.cost_label.set_text.assert_called_with("費用: 5000 G")
        panel.vitality_label.set_text.assert_called_with("生命力: 8")
        
        # 蘇生ボタンが有効化される
        panel.resurrect_button.enable.assert_called_once()
        
        # 結果がクリアされる
        panel.result_label.set_text.assert_called_with("")
    
    def test_handle_event_member_selection_zero_vitality(self, sample_dead_members):
        """生命力0のメンバー選択イベントの処理"""
        from src.facilities.ui.temple.resurrect_panel import ResurrectPanel
        
        panel = Mock()
        panel.members_data = sample_dead_members
        panel.members_list = Mock()
        panel.selected_member = None
        panel.cost_label = Mock()
        panel.vitality_label = Mock()
        panel.resurrect_button = Mock()
        panel.result_label = Mock()
        
        # 選択イベントのモック
        event = Mock()
        event.type = pygame_gui.UI_SELECTION_LIST_NEW_SELECTION
        event.ui_element = panel.members_list
        
        # 生命力0のメンバーが選択された
        panel.members_list.get_single_selection.return_value = 2  # 盗賊チャーリー（生命力0）
        
        ResurrectPanel.handle_event(panel, event)
        
        # 選択されたメンバーが設定される
        assert panel.selected_member == "char3"
        
        # コスト・生命力表示が更新される
        panel.cost_label.set_text.assert_called_with("費用: 12000 G")
        panel.vitality_label.set_text.assert_called_with("生命力: 0")
        
        # 蘇生ボタンが無効化される
        panel.resurrect_button.disable.assert_called_once()
        
        # エラーメッセージが表示される
        panel.result_label.set_text.assert_called_with("生命力が尽きているため蘇生できません")
    
    def test_handle_event_member_selection_invalid_index(self, sample_dead_members):
        """無効なインデックスでの選択処理"""
        from src.facilities.ui.temple.resurrect_panel import ResurrectPanel
        
        panel = Mock()
        panel.members_data = sample_dead_members
        panel.members_list = Mock()
        panel.cost_label = Mock()
        
        # 選択イベントのモック
        event = Mock()
        event.type = pygame_gui.UI_SELECTION_LIST_NEW_SELECTION
        event.ui_element = panel.members_list
        
        # 範囲外のインデックス
        panel.members_list.get_single_selection.return_value = 10
        
        ResurrectPanel.handle_event(panel, event)
        
        # コスト表示は更新されない
        panel.cost_label.set_text.assert_not_called()
    
    def test_handle_event_resurrect_button(self):
        """蘇生ボタン押下イベントの処理"""
        from src.facilities.ui.temple.resurrect_panel import ResurrectPanel
        
        panel = Mock()
        panel.resurrect_button = Mock()
        
        # ボタン押下イベントのモック
        event = Mock()
        event.type = pygame_gui.UI_BUTTON_PRESSED
        event.ui_element = panel.resurrect_button
        
        with patch.object(panel, '_perform_resurrect') as mock_resurrect:
            ResurrectPanel.handle_event(panel, event)
            
            mock_resurrect.assert_called_once()


class TestResurrectPanelResurrectPerformance:
    """ResurrectPanelの蘇生実行テスト"""
    
    def test_perform_resurrect_success(self, sample_service_result):
        """蘇生実行成功"""
        from src.facilities.ui.temple.resurrect_panel import ResurrectPanel
        
        panel = Mock()
        panel.selected_member = "char1"
        panel.service = Mock()
        panel.result_label = Mock()
        panel.resurrect_button = Mock()
        panel.cost_label = Mock()
        panel.vitality_label = Mock()
        
        # 確認結果
        confirm_result = sample_service_result(
            success=True,
            result_type=Mock()
        )
        confirm_result.result_type.name = "CONFIRM"
        
        # 実行結果
        execute_result = sample_service_result(
            success=True,
            message="戦士アレンが蘇生されました"
        )
        
        panel.service.execute_action.side_effect = [confirm_result, execute_result]
        
        with patch.object(panel, '_refresh_members') as mock_refresh:
            ResurrectPanel._perform_resurrect(panel)
            
            # サービスが2回呼ばれる（確認、実行）
            assert panel.service.execute_action.call_count == 2
            
            # 確認呼び出し
            panel.service.execute_action.assert_any_call("resurrect", {
                "character_id": "char1"
            })
            
            # 実行呼び出し
            panel.service.execute_action.assert_any_call("resurrect", {
                "character_id": "char1",
                "confirmed": True
            })
            
            # 成功メッセージが表示される
            panel.result_label.set_text.assert_called_with("戦士アレンが蘇生されました")
            
            # リストがリフレッシュされる
            mock_refresh.assert_called_once()
            
            # 選択がクリアされる
            assert panel.selected_member is None
            panel.resurrect_button.disable.assert_called_once()
            panel.cost_label.set_text.assert_called_with("費用: -")
            panel.vitality_label.set_text.assert_called_with("生命力: -")
    
    def test_perform_resurrect_failure(self, sample_service_result):
        """蘇生実行失敗"""
        from src.facilities.ui.temple.resurrect_panel import ResurrectPanel
        
        panel = Mock()
        panel.selected_member = "char1"
        panel.service = Mock()
        panel.result_label = Mock()
        
        # 失敗結果
        result = sample_service_result(
            success=False,
            message="所持金が不足しています"
        )
        panel.service.execute_action.return_value = result
        
        ResurrectPanel._perform_resurrect(panel)
        
        # エラーメッセージが表示される
        panel.result_label.set_text.assert_called_with("所持金が不足しています")
    
    def test_perform_resurrect_no_selection(self):
        """選択なしでの蘇生実行"""
        from src.facilities.ui.temple.resurrect_panel import ResurrectPanel
        
        panel = Mock()
        panel.selected_member = None
        panel.service = Mock()
        
        ResurrectPanel._perform_resurrect(panel)
        
        # サービスが呼ばれない
        panel.service.execute_action.assert_not_called()


class TestResurrectPanelActions:
    """ResurrectPanelのアクション機能テスト"""
    
    def test_refresh(self):
        """パネルのリフレッシュ"""
        from src.facilities.ui.temple.resurrect_panel import ResurrectPanel
        
        panel = Mock()
        panel.selected_member = "char1"
        panel.resurrect_button = Mock()
        panel.cost_label = Mock()
        panel.vitality_label = Mock()
        panel.result_label = Mock()
        
        with patch.object(panel, '_refresh_members') as mock_refresh:
            ResurrectPanel.refresh(panel)
            
            # データがリフレッシュされる
            mock_refresh.assert_called_once()
            
            # 選択がクリアされる
            assert panel.selected_member is None
            
            # ボタンが無効化される
            panel.resurrect_button.disable.assert_called_once()
            
            # 表示がリセットされる
            panel.cost_label.set_text.assert_called_with("費用: -")
            panel.vitality_label.set_text.assert_called_with("生命力: -")
            panel.result_label.set_text.assert_called_with("")
    
    def test_show(self):
        """パネル表示"""
        from src.facilities.ui.temple.resurrect_panel import ResurrectPanel
        
        panel = Mock()
        panel.container = Mock()
        
        ResurrectPanel.show(panel)
        
        panel.container.show.assert_called_once()
    
    def test_hide(self):
        """パネル非表示"""
        from src.facilities.ui.temple.resurrect_panel import ResurrectPanel
        
        panel = Mock()
        panel.container = Mock()
        
        ResurrectPanel.hide(panel)
        
        panel.container.hide.assert_called_once()
    
    def test_destroy(self):
        """パネル破棄"""
        from src.facilities.ui.temple.resurrect_panel import ResurrectPanel
        
        panel = Mock()
        panel.container = Mock()
        
        ResurrectPanel.destroy(panel)
        
        panel.container.kill.assert_called_once()
    
    def test_show_hide_destroy_no_container(self):
        """コンテナなしでの表示・非表示・破棄"""
        from src.facilities.ui.temple.resurrect_panel import ResurrectPanel
        
        panel = Mock()
        panel.container = None
        
        # エラーが発生しないことを確認
        try:
            ResurrectPanel.show(panel)
            ResurrectPanel.hide(panel)
            ResurrectPanel.destroy(panel)
            assert True
        except Exception as e:
            pytest.fail(f"Unexpected exception: {e}")