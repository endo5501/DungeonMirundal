"""魔法鑑定パネルのテスト"""

import pytest
import pygame
import pygame_gui
from unittest.mock import Mock, MagicMock, patch


@pytest.fixture
def mock_ui_setup():
    """UI要素のモック"""
    rect = pygame.Rect(0, 0, 500, 400)
    parent = Mock()
    ui_manager = Mock()
    controller = Mock()
    service = Mock()
    service.identify_magic_cost = 100
    return rect, parent, ui_manager, controller, service


@pytest.fixture
def sample_service_result():
    """サンプルサービス結果"""
    def create_result(success=True, data=None, message="", result_type=None):
        result = Mock()
        result.success = success
        result.data = data or {}
        result.message = message
        result.result_type = result_type or Mock()
        result.result_type.name = "SUCCESS"
        return result
    return create_result


@pytest.fixture
def sample_items_data():
    """サンプルアイテムデータ"""
    return [
        {
            "id": "item1",
            "name": "謎の剣",
            "holder": "戦士アレン"
        },
        {
            "id": "item2", 
            "name": "不明な指輪",
            "holder": "魔法使いベラ"
        }
    ]


class TestMagicIdentifyPanelBasic:
    """MagicIdentifyPanelの基本機能テスト"""
    
    def test_initialization(self, mock_ui_setup):
        """正常に初期化される"""
        from src.facilities.ui.magic_guild.magic_identify_panel import MagicIdentifyPanel
        
        rect, parent, ui_manager, controller, service = mock_ui_setup
        
        with patch('pygame_gui.elements.UIPanel'), \
             patch('pygame_gui.elements.UILabel'), \
             patch('pygame_gui.elements.UISelectionList'), \
             patch('pygame_gui.elements.UIButton'), \
             patch('pygame_gui.elements.UITextBox'), \
             patch.object(MagicIdentifyPanel, '_refresh_items'):
            
            panel = MagicIdentifyPanel(rect, parent, ui_manager, controller, service)
            
            # 基本属性の確認
            assert panel.rect == rect
            assert panel.parent == parent
            assert panel.ui_manager == ui_manager
            assert panel.controller == controller
            assert panel.service == service
            
            # 初期状態の確認
            assert panel.selected_item is None
            assert panel.items_data == []
    
    def test_create_ui_elements(self, mock_ui_setup):
        """UI要素が正常に作成される"""
        from src.facilities.ui.magic_guild.magic_identify_panel import MagicIdentifyPanel
        
        rect, parent, ui_manager, controller, service = mock_ui_setup
        
        with patch('pygame_gui.elements.UIPanel') as mock_panel, \
             patch('pygame_gui.elements.UILabel') as mock_label, \
             patch('pygame_gui.elements.UISelectionList') as mock_list, \
             patch('pygame_gui.elements.UIButton') as mock_button, \
             patch('pygame_gui.elements.UITextBox') as mock_text_box, \
             patch.object(MagicIdentifyPanel, '_refresh_items'):
            
            mock_button_instance = Mock()
            mock_button.return_value = mock_button_instance
            
            panel = MagicIdentifyPanel(rect, parent, ui_manager, controller, service)
            
            # UI要素が作成される
            mock_panel.assert_called_once()
            assert mock_label.call_count == 3  # タイトル、コスト、所持金
            mock_list.assert_called_once()
            mock_button.assert_called_once()
            mock_text_box.assert_called_once()
            
            # 鑑定ボタンが初期無効化される
            mock_button_instance.disable.assert_called_once()


class TestMagicIdentifyPanelItemsRefresh:
    """MagicIdentifyPanelのアイテム更新テスト"""
    
    def test_refresh_items_success(self, mock_ui_setup, sample_service_result, sample_items_data):
        """アイテム更新成功"""
        from src.facilities.ui.magic_guild.magic_identify_panel import MagicIdentifyPanel
        
        rect, parent, ui_manager, controller, service = mock_ui_setup
        
        # モックUI要素
        mock_items_list = Mock()
        mock_gold_label = Mock()
        mock_result_box = Mock()
        
        # サービス結果のモック
        result = sample_service_result(
            success=True,
            data={
                "items": sample_items_data,
                "party_gold": 1500
            },
            message="鑑定可能なアイテムが見つかりました"
        )
        service.execute_action.return_value = result
        
        panel = Mock()
        panel.service = service
        panel.items_list = mock_items_list
        panel.gold_label = mock_gold_label
        panel.result_box = mock_result_box
        
        MagicIdentifyPanel._refresh_items(panel)
        
        # データが設定される
        assert panel.items_data == sample_items_data
        
        # リストが更新される
        expected_items = [
            "謎の剣 (所持者: 戦士アレン)",
            "不明な指輪 (所持者: 魔法使いベラ)"
        ]
        mock_items_list.set_item_list.assert_called_with(expected_items)
        
        # 所持金が更新される
        mock_gold_label.set_text.assert_called_with("所持金: 1500 G")
        
        # 結果メッセージが更新される
        assert mock_result_box.html_text == "鑑定可能なアイテムが見つかりました"
        mock_result_box.rebuild.assert_called()
    
    def test_refresh_items_no_items(self, mock_ui_setup, sample_service_result):
        """アイテムなしの場合"""
        from src.facilities.ui.magic_guild.magic_identify_panel import MagicIdentifyPanel
        
        rect, parent, ui_manager, controller, service = mock_ui_setup
        
        # モックUI要素
        mock_items_list = Mock()
        mock_result_box = Mock()
        
        # アイテムなしの結果
        result = sample_service_result(
            success=True,
            data={"items": [], "party_gold": 500}
        )
        service.execute_action.return_value = result
        
        panel = Mock()
        panel.service = service
        panel.items_list = mock_items_list
        panel.gold_label = Mock()
        panel.result_box = mock_result_box
        
        MagicIdentifyPanel._refresh_items(panel)
        
        # 空リストが設定される
        mock_items_list.set_item_list.assert_called_with([])
        
        # デフォルトメッセージが表示される
        assert mock_result_box.html_text == "鑑定が必要なアイテムはありません"
    
    def test_refresh_items_failure(self, mock_ui_setup, sample_service_result):
        """アイテム更新失敗"""
        from src.facilities.ui.magic_guild.magic_identify_panel import MagicIdentifyPanel
        
        rect, parent, ui_manager, controller, service = mock_ui_setup
        
        # モックUI要素
        mock_items_list = Mock()
        mock_result_box = Mock()
        
        # 失敗結果
        result = sample_service_result(
            success=False,
            message="アイテム取得に失敗しました"
        )
        service.execute_action.return_value = result
        
        panel = Mock()
        panel.service = service
        panel.items_list = mock_items_list
        panel.result_box = mock_result_box
        
        MagicIdentifyPanel._refresh_items(panel)
        
        # 空リストが設定される
        mock_items_list.set_item_list.assert_called_with([])
        
        # エラーメッセージが表示される
        assert mock_result_box.html_text == "アイテム取得に失敗しました"


class TestMagicIdentifyPanelEventHandling:
    """MagicIdentifyPanelのイベント処理テスト"""
    
    def test_handle_event_selection_list(self, sample_items_data):
        """選択リストイベントの処理"""
        from src.facilities.ui.magic_guild.magic_identify_panel import MagicIdentifyPanel
        
        panel = Mock()
        panel.items_data = sample_items_data
        panel.items_list = Mock()
        panel.identify_button = Mock()
        panel.result_box = Mock()
        
        # 選択イベントのモック
        event = Mock()
        event.type = pygame_gui.UI_SELECTION_LIST_NEW_SELECTION
        event.ui_element = panel.items_list
        
        # アイテムが選択された
        panel.items_list.get_single_selection.return_value = 0
        
        MagicIdentifyPanel.handle_event(panel, event)
        
        # 選択されたアイテムが設定される
        assert panel.selected_item == "item1"
        
        # 鑑定ボタンが有効化される
        panel.identify_button.enable.assert_called_once()
        
        # 結果ボックスがクリアされる
        assert panel.result_box.html_text == ""
        panel.result_box.rebuild.assert_called_once()
    
    def test_handle_event_selection_invalid_index(self, sample_items_data):
        """無効なインデックス選択の処理"""
        from src.facilities.ui.magic_guild.magic_identify_panel import MagicIdentifyPanel
        
        panel = Mock()
        panel.items_data = sample_items_data
        panel.items_list = Mock()
        panel.identify_button = Mock()
        
        # 選択イベントのモック
        event = Mock()
        event.type = pygame_gui.UI_SELECTION_LIST_NEW_SELECTION
        event.ui_element = panel.items_list
        
        # 範囲外のインデックス
        panel.items_list.get_single_selection.return_value = 10
        
        MagicIdentifyPanel.handle_event(panel, event)
        
        # 鑑定ボタンは有効化されない
        panel.identify_button.enable.assert_not_called()
    
    def test_handle_event_button_pressed(self):
        """ボタン押下イベントの処理"""
        from src.facilities.ui.magic_guild.magic_identify_panel import MagicIdentifyPanel
        
        panel = Mock()
        panel.identify_button = Mock()
        
        # ボタン押下イベントのモック
        event = Mock()
        event.type = pygame_gui.UI_BUTTON_PRESSED
        event.ui_element = panel.identify_button
        
        with patch.object(MagicIdentifyPanel, '_perform_identify') as mock_identify:
            MagicIdentifyPanel.handle_event(panel, event)
            
            mock_identify.assert_called_once()
    
    def test_handle_event_unknown_event(self):
        """未知のイベントの処理"""
        from src.facilities.ui.magic_guild.magic_identify_panel import MagicIdentifyPanel
        
        panel = Mock()
        
        # 未知のイベント
        event = Mock()
        event.type = 999
        
        # エラーが発生しないことを確認
        try:
            MagicIdentifyPanel.handle_event(panel, event)
            assert True
        except Exception as e:
            pytest.fail(f"Unexpected exception: {e}")


class TestMagicIdentifyPanelIdentification:
    """MagicIdentifyPanelの鑑定処理テスト"""
    
    def test_perform_identify_success(self, sample_service_result):
        """鑑定実行成功"""
        from src.facilities.ui.magic_guild.magic_identify_panel import MagicIdentifyPanel
        
        panel = Mock()
        panel.selected_item = "item1"
        panel.service = Mock()
        panel.result_box = Mock()
        panel.identify_button = Mock()
        
        # 確認結果のモック
        confirm_result = sample_service_result(
            success=True,
            result_type=Mock()
        )
        confirm_result.result_type.name = "CONFIRM"
        
        # 実行結果のモック
        execute_result = sample_service_result(
            success=True,
            message="鑑定が完了しました。この剣は+1の魔法武器です。",
            data={"remaining_gold": 900}
        )
        
        panel.service.execute_action.side_effect = [confirm_result, execute_result]
        
        with patch.object(MagicIdentifyPanel, '_refresh_items') as mock_refresh:
            MagicIdentifyPanel._perform_identify(panel)
            
            # サービスが2回呼ばれる（確認→実行）
            assert panel.service.execute_action.call_count == 2
            
            # 結果が表示される
            expected_text = """<b>鑑定結果</b><br>
                <br>
                鑑定が完了しました。この剣は+1の魔法武器です。<br>
                <br>
                <i>残り所持金: 900 G</i>"""
            assert panel.result_box.html_text == expected_text.strip()
            
            # リストが更新される
            mock_refresh.assert_called_once()
            
            # 選択がクリアされる
            assert panel.selected_item is None
            panel.identify_button.disable.assert_called_once()
    
    def test_perform_identify_failure(self, sample_service_result):
        """鑑定実行失敗"""
        from src.facilities.ui.magic_guild.magic_identify_panel import MagicIdentifyPanel
        
        panel = Mock()
        panel.selected_item = "item1"
        panel.service = Mock()
        panel.result_box = Mock()
        
        # 失敗結果のモック
        failure_result = sample_service_result(
            success=False,
            message="所持金が不足しています"
        )
        
        panel.service.execute_action.return_value = failure_result
        
        MagicIdentifyPanel._perform_identify(panel)
        
        # エラーメッセージが表示される
        assert panel.result_box.html_text == "<font color='#FF0000'>所持金が不足しています</font>"
        panel.result_box.rebuild.assert_called_once()
    
    def test_perform_identify_no_selection(self):
        """選択なしでの鑑定実行"""
        from src.facilities.ui.magic_guild.magic_identify_panel import MagicIdentifyPanel
        
        panel = Mock()
        panel.selected_item = None
        panel.service = Mock()
        
        MagicIdentifyPanel._perform_identify(panel)
        
        # サービスが呼ばれない
        panel.service.execute_action.assert_not_called()
    
    def test_perform_identify_confirm_failure(self, sample_service_result):
        """確認段階での失敗"""
        from src.facilities.ui.magic_guild.magic_identify_panel import MagicIdentifyPanel
        
        panel = Mock()
        panel.selected_item = "item1"
        panel.service = Mock()
        panel.result_box = Mock()
        
        # 確認失敗の結果
        confirm_result = sample_service_result(
            success=True,
            result_type=Mock()
        )
        confirm_result.result_type.name = "ERROR"
        
        panel.service.execute_action.return_value = confirm_result
        
        MagicIdentifyPanel._perform_identify(panel)
        
        # サービスが1回だけ呼ばれる
        assert panel.service.execute_action.call_count == 1


class TestMagicIdentifyPanelActions:
    """MagicIdentifyPanelのアクション機能テスト"""
    
    def test_refresh(self):
        """リフレッシュ処理"""
        from src.facilities.ui.magic_guild.magic_identify_panel import MagicIdentifyPanel
        
        panel = Mock()
        panel.selected_item = "item1"
        panel.identify_button = Mock()
        panel.result_box = Mock()
        
        with patch.object(MagicIdentifyPanel, '_refresh_items') as mock_refresh:
            MagicIdentifyPanel.refresh(panel)
            
            # データがリフレッシュされる
            mock_refresh.assert_called_once()
            
            # 選択がクリアされる
            assert panel.selected_item is None
            
            # ボタンが無効化される
            panel.identify_button.disable.assert_called_once()
            
            # 結果ボックスがクリアされる
            assert panel.result_box.html_text == ""
            panel.result_box.rebuild.assert_called_once()
    
    def test_show(self):
        """パネル表示"""
        from src.facilities.ui.magic_guild.magic_identify_panel import MagicIdentifyPanel
        
        panel = Mock()
        panel.container = Mock()
        
        MagicIdentifyPanel.show(panel)
        
        panel.container.show.assert_called_once()
    
    def test_show_no_container(self):
        """コンテナなしでの表示"""
        from src.facilities.ui.magic_guild.magic_identify_panel import MagicIdentifyPanel
        
        panel = Mock()
        panel.container = None
        
        # エラーが発生しないことを確認
        try:
            MagicIdentifyPanel.show(panel)
            assert True
        except Exception as e:
            pytest.fail(f"Unexpected exception: {e}")
    
    def test_hide(self):
        """パネル非表示"""
        from src.facilities.ui.magic_guild.magic_identify_panel import MagicIdentifyPanel
        
        panel = Mock()
        panel.container = Mock()
        
        MagicIdentifyPanel.hide(panel)
        
        panel.container.hide.assert_called_once()
    
    def test_destroy(self):
        """パネル破棄"""
        from src.facilities.ui.magic_guild.magic_identify_panel import MagicIdentifyPanel
        
        panel = Mock()
        panel.container = Mock()
        
        MagicIdentifyPanel.destroy(panel)
        
        panel.container.kill.assert_called_once()