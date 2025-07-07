"""治療パネルのテスト"""

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
    service = Mock()
    return rect, parent, ui_manager, controller, service


@pytest.fixture
def sample_injured_members():
    """サンプル負傷メンバーデータ"""
    return [
        {
            "id": "char1",
            "name": "戦士アレン",
            "level": 5,
            "hp": 15,
            "max_hp": 50,
            "cost": 300
        },
        {
            "id": "char2",
            "name": "魔法使いベラ",
            "level": 3,
            "hp": 8,
            "max_hp": 25,
            "cost": 200
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


class TestHealPanelBasic:
    """HealPanelの基本機能テスト"""
    
    def test_initialization(self, mock_ui_setup):
        """正常に初期化される"""
        from src.facilities.ui.temple.heal_panel import HealPanel
        
        rect, parent, ui_manager, controller, service = mock_ui_setup
        
        with patch('pygame_gui.elements.UIPanel'), \
             patch('pygame_gui.elements.UILabel'), \
             patch('pygame_gui.elements.UISelectionList'), \
             patch('pygame_gui.elements.UIButton'), \
             patch.object(HealPanel, '_refresh_members'):
            
            panel = HealPanel(rect, parent, ui_manager, controller, service)
            
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
        from src.facilities.ui.temple.heal_panel import HealPanel
        
        rect, parent, ui_manager, controller, service = mock_ui_setup
        
        with patch('pygame_gui.elements.UIPanel') as mock_panel, \
             patch('pygame_gui.elements.UILabel') as mock_label, \
             patch('pygame_gui.elements.UISelectionList') as mock_list, \
             patch('pygame_gui.elements.UIButton') as mock_button, \
             patch.object(HealPanel, '_refresh_members'):
            
            mock_button_instance = Mock()
            mock_button.return_value = mock_button_instance
            
            panel = HealPanel(rect, parent, ui_manager, controller, service)
            
            # UI要素が作成される
            mock_panel.assert_called_once()
            assert mock_label.call_count == 4  # タイトル、コスト、所持金、結果
            mock_list.assert_called_once()
            mock_button.assert_called_once()
            
            # 治療ボタンが初期無効化される
            mock_button_instance.disable.assert_called_once()


class TestHealPanelDataLoading:
    """HealPanelのデータ読み込みテスト"""
    
    def test_refresh_members_success(self, mock_ui_setup, sample_service_result, sample_injured_members):
        """メンバー更新成功"""
        from src.facilities.ui.temple.heal_panel import HealPanel
        
        rect, parent, ui_manager, controller, service = mock_ui_setup
        
        # モックUI要素
        mock_members_list = Mock()
        mock_gold_label = Mock()
        mock_result_label = Mock()
        
        # サービス結果のモック
        result = sample_service_result(
            success=True,
            data={
                "members": sample_injured_members,
                "party_gold": 3000
            },
            message="治療可能なメンバーが見つかりました"
        )
        service.execute_action.return_value = result
        
        panel = Mock()
        panel.service = service
        panel.members_list = mock_members_list
        panel.gold_label = mock_gold_label
        panel.result_label = mock_result_label
        
        HealPanel._refresh_members(panel)
        
        # データが設定される
        assert panel.members_data == sample_injured_members
        
        # リストが更新される
        expected_items = [
            "戦士アレン (Lv.5) - HP: 15 - 300 G",
            "魔法使いベラ (Lv.3) - HP: 8 - 200 G"
        ]
        mock_members_list.set_item_list.assert_called_with(expected_items)
        
        # 所持金が更新される
        mock_gold_label.set_text.assert_called_with("所持金: 3000 G")
        
        # 結果メッセージが表示される
        mock_result_label.set_text.assert_called_with("治療可能なメンバーが見つかりました")
    
    def test_refresh_members_failure(self, mock_ui_setup, sample_service_result):
        """メンバー更新失敗"""
        from src.facilities.ui.temple.heal_panel import HealPanel
        
        panel = Mock()
        panel.service = Mock()
        panel.members_list = Mock()
        panel.result_label = Mock()
        panel.members_data = []
        
        # 失敗結果
        result = sample_service_result(
            success=False,
            message="治療が必要なメンバーはいません"
        )
        panel.service.execute_action.return_value = result
        
        HealPanel._refresh_members(panel)
        
        # 空リストが設定される
        panel.members_list.set_item_list.assert_called_with([])
        assert panel.members_data == []
        
        # エラーメッセージが表示される
        panel.result_label.set_text.assert_called_with("治療が必要なメンバーはいません")
    
    def test_refresh_members_no_message(self, mock_ui_setup, sample_service_result):
        """メッセージなしの場合のメンバー更新"""
        from src.facilities.ui.temple.heal_panel import HealPanel
        
        panel = Mock()
        panel.service = Mock()
        panel.members_list = Mock()
        panel.result_label = Mock()
        
        # メッセージなしの失敗結果
        result = sample_service_result(success=False, message="")
        panel.service.execute_action.return_value = result
        
        HealPanel._refresh_members(panel)
        
        # デフォルトメッセージが表示される
        panel.result_label.set_text.assert_called_with("治療が必要なメンバーはいません")


class TestHealPanelEventHandling:
    """HealPanelのイベント処理テスト"""
    
    def test_handle_event_member_selection(self, sample_injured_members):
        """メンバー選択イベントの処理"""
        from src.facilities.ui.temple.heal_panel import HealPanel
        
        panel = Mock()
        panel.members_data = sample_injured_members
        panel.members_list = Mock()
        panel.selected_member = None
        panel.cost_label = Mock()
        panel.heal_button = Mock()
        panel.result_label = Mock()
        
        # 選択イベントのモック
        event = Mock()
        event.type = pygame_gui.UI_SELECTION_LIST_NEW_SELECTION
        event.ui_element = panel.members_list
        
        # メンバーが選択された
        panel.members_list.get_single_selection.return_value = 0
        
        HealPanel.handle_event(panel, event)
        
        # 選択されたメンバーが設定される
        assert panel.selected_member == "char1"
        
        # コスト表示が更新される
        panel.cost_label.set_text.assert_called_with("費用: 300 G")
        
        # 治療ボタンが有効化される
        panel.heal_button.enable.assert_called_once()
        
        # 結果がクリアされる
        panel.result_label.set_text.assert_called_with("")
    
    def test_handle_event_member_selection_invalid_index(self, sample_injured_members):
        """無効なインデックスでの選択処理"""
        from src.facilities.ui.temple.heal_panel import HealPanel
        
        panel = Mock()
        panel.members_data = sample_injured_members
        panel.members_list = Mock()
        panel.cost_label = Mock()
        
        # 選択イベントのモック
        event = Mock()
        event.type = pygame_gui.UI_SELECTION_LIST_NEW_SELECTION
        event.ui_element = panel.members_list
        
        # 範囲外のインデックス
        panel.members_list.get_single_selection.return_value = 10
        
        HealPanel.handle_event(panel, event)
        
        # コスト表示は更新されない
        panel.cost_label.set_text.assert_not_called()
    
    def test_handle_event_heal_button(self):
        """治療ボタン押下イベントの処理"""
        from src.facilities.ui.temple.heal_panel import HealPanel
        
        panel = Mock()
        panel.heal_button = Mock()
        
        # ボタン押下イベントのモック
        event = Mock()
        event.type = pygame_gui.UI_BUTTON_PRESSED
        event.ui_element = panel.heal_button
        
        with patch.object(panel, '_perform_heal') as mock_heal:
            HealPanel.handle_event(panel, event)
            
            mock_heal.assert_called_once()


class TestHealPanelHealPerformance:
    """HealPanelの治療実行テスト"""
    
    def test_perform_heal_success(self, sample_service_result):
        """治療実行成功"""
        from src.facilities.ui.temple.heal_panel import HealPanel
        
        panel = Mock()
        panel.selected_member = "char1"
        panel.service = Mock()
        panel.result_label = Mock()
        panel.heal_button = Mock()
        panel.cost_label = Mock()
        
        # 確認結果
        confirm_result = sample_service_result(
            success=True,
            result_type=Mock()
        )
        confirm_result.result_type.name = "CONFIRM"
        
        # 実行結果
        execute_result = sample_service_result(
            success=True,
            message="戦士アレンが完全に治療されました"
        )
        
        panel.service.execute_action.side_effect = [confirm_result, execute_result]
        
        with patch.object(panel, '_refresh_members') as mock_refresh:
            HealPanel._perform_heal(panel)
            
            # サービスが2回呼ばれる（確認、実行）
            assert panel.service.execute_action.call_count == 2
            
            # 確認呼び出し
            panel.service.execute_action.assert_any_call("heal", {
                "character_id": "char1"
            })
            
            # 実行呼び出し
            panel.service.execute_action.assert_any_call("heal", {
                "character_id": "char1",
                "confirmed": True
            })
            
            # 成功メッセージが表示される
            panel.result_label.set_text.assert_called_with("戦士アレンが完全に治療されました")
            
            # リストがリフレッシュされる
            mock_refresh.assert_called_once()
            
            # 選択がクリアされる
            assert panel.selected_member is None
            panel.heal_button.disable.assert_called_once()
            panel.cost_label.set_text.assert_called_with("費用: -")
    
    def test_perform_heal_failure(self, sample_service_result):
        """治療実行失敗"""
        from src.facilities.ui.temple.heal_panel import HealPanel
        
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
        
        HealPanel._perform_heal(panel)
        
        # エラーメッセージが表示される
        panel.result_label.set_text.assert_called_with("所持金が不足しています")
    
    def test_perform_heal_no_selection(self):
        """選択なしでの治療実行"""
        from src.facilities.ui.temple.heal_panel import HealPanel
        
        panel = Mock()
        panel.selected_member = None
        panel.service = Mock()
        
        HealPanel._perform_heal(panel)
        
        # サービスが呼ばれない
        panel.service.execute_action.assert_not_called()


class TestHealPanelActions:
    """HealPanelのアクション機能テスト"""
    
    def test_refresh(self):
        """パネルのリフレッシュ"""
        from src.facilities.ui.temple.heal_panel import HealPanel
        
        panel = Mock()
        panel.selected_member = "char1"
        panel.heal_button = Mock()
        panel.cost_label = Mock()
        panel.result_label = Mock()
        
        with patch.object(panel, '_refresh_members') as mock_refresh:
            HealPanel.refresh(panel)
            
            # データがリフレッシュされる
            mock_refresh.assert_called_once()
            
            # 選択がクリアされる
            assert panel.selected_member is None
            
            # ボタンが無効化される
            panel.heal_button.disable.assert_called_once()
            
            # 表示がリセットされる
            panel.cost_label.set_text.assert_called_with("費用: -")
            panel.result_label.set_text.assert_called_with("")
    
    def test_show(self):
        """パネル表示"""
        from src.facilities.ui.temple.heal_panel import HealPanel
        
        panel = Mock()
        panel.container = Mock()
        
        HealPanel.show(panel)
        
        panel.container.show.assert_called_once()
    
    def test_hide(self):
        """パネル非表示"""
        from src.facilities.ui.temple.heal_panel import HealPanel
        
        panel = Mock()
        panel.container = Mock()
        
        HealPanel.hide(panel)
        
        panel.container.hide.assert_called_once()
    
    def test_destroy(self):
        """パネル破棄"""
        from src.facilities.ui.temple.heal_panel import HealPanel
        
        panel = Mock()
        panel.container = Mock()
        
        HealPanel.destroy(panel)
        
        panel.container.kill.assert_called_once()
    
    def test_show_hide_destroy_no_container(self):
        """コンテナなしでの表示・非表示・破棄"""
        from src.facilities.ui.temple.heal_panel import HealPanel
        
        panel = Mock()
        panel.container = None
        
        # エラーが発生しないことを確認
        try:
            HealPanel.show(panel)
            HealPanel.hide(panel)
            HealPanel.destroy(panel)
            assert True
        except Exception as e:
            pytest.fail(f"Unexpected exception: {e}")