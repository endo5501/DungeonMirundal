"""祝福パネルのテスト"""

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
    service.blessing_cost = 500
    return rect, parent, ui_manager, controller, service


@pytest.fixture
def sample_party():
    """サンプルパーティデータ"""
    party = Mock()
    party.gold = 1500
    return party


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


class TestBlessingPanelBasic:
    """BlessingPanelの基本機能テスト"""
    
    def test_initialization(self, mock_ui_setup):
        """正常に初期化される"""
        from src.facilities.ui.temple.blessing_panel import BlessingPanel
        
        rect, parent, ui_manager, controller, service = mock_ui_setup
        
        with patch('pygame_gui.elements.UIPanel'), \
             patch('pygame_gui.elements.UILabel'), \
             patch('pygame_gui.elements.UITextBox'), \
             patch('pygame_gui.elements.UIButton'), \
             patch.object(BlessingPanel, '_refresh_info'):
            
            panel = BlessingPanel(rect, parent, ui_manager, controller, service)
            
            # 基本属性の確認
            assert panel.rect == rect
            assert panel.parent == parent
            assert panel.ui_manager == ui_manager
            assert panel.controller == controller
            assert panel.service == service
    
    def test_create_ui_elements(self, mock_ui_setup):
        """UI要素が正常に作成される"""
        from src.facilities.ui.temple.blessing_panel import BlessingPanel
        
        rect, parent, ui_manager, controller, service = mock_ui_setup
        
        with patch('pygame_gui.elements.UIPanel') as mock_panel, \
             patch('pygame_gui.elements.UILabel') as mock_label, \
             patch('pygame_gui.elements.UITextBox') as mock_text_box, \
             patch('pygame_gui.elements.UIButton') as mock_button, \
             patch.object(BlessingPanel, '_refresh_info'):
            
            panel = BlessingPanel(rect, parent, ui_manager, controller, service)
            
            # UI要素が作成される
            mock_panel.assert_called_once()
            assert mock_label.call_count == 4  # タイトル、コスト、所持金、結果
            mock_text_box.assert_called_once()  # 説明テキストボックス
            mock_button.assert_called_once()   # 祝福ボタン


class TestBlessingPanelInfoRefresh:
    """BlessingPanelの情報更新テスト"""
    
    def test_refresh_info_with_sufficient_gold(self, mock_ui_setup, sample_party):
        """十分な所持金での情報更新"""
        from src.facilities.ui.temple.blessing_panel import BlessingPanel
        
        panel = Mock()
        panel.service = Mock()
        panel.service.party = sample_party  # 1500 G
        panel.service.blessing_cost = 500
        panel.gold_label = Mock()
        panel.cost_label = Mock()
        panel.blessing_button = Mock()
        panel.result_label = Mock()
        
        BlessingPanel._refresh_info(panel)
        
        # 所持金表示が更新される
        panel.gold_label.set_text.assert_called_with("所持金: 1500 G")
        
        # コスト表示が更新される
        panel.cost_label.set_text.assert_called_with("費用: 500 G")
        
        # 祝福ボタンが有効化される
        panel.blessing_button.enable.assert_called_once()
    
    def test_refresh_info_with_insufficient_gold(self, mock_ui_setup, sample_party):
        """不十分な所持金での情報更新"""
        from src.facilities.ui.temple.blessing_panel import BlessingPanel
        
        panel = Mock()
        panel.service = Mock()
        sample_party.gold = 300  # 500 G未満
        panel.service.party = sample_party
        panel.service.blessing_cost = 500
        panel.gold_label = Mock()
        panel.cost_label = Mock()
        panel.blessing_button = Mock()
        panel.result_label = Mock()
        
        BlessingPanel._refresh_info(panel)
        
        # 所持金表示が更新される
        panel.gold_label.set_text.assert_called_with("所持金: 300 G")
        
        # コスト表示が更新される
        panel.cost_label.set_text.assert_called_with("費用: 500 G")
        
        # 祝福ボタンが無効化される
        panel.blessing_button.disable.assert_called_once()
        
        # 不足メッセージが表示される
        panel.result_label.set_text.assert_called_with("祝福の費用が不足しています")
    
    def test_refresh_info_no_party(self, mock_ui_setup):
        """パーティなしでの情報更新"""
        from src.facilities.ui.temple.blessing_panel import BlessingPanel
        
        panel = Mock()
        panel.service = Mock()
        panel.service.party = None
        panel.gold_label = Mock()
        panel.blessing_button = Mock()
        panel.result_label = Mock()
        
        BlessingPanel._refresh_info(panel)
        
        # 所持金表示がゼロになる
        panel.gold_label.set_text.assert_called_with("所持金: 0 G")
        
        # 祝福ボタンが無効化される
        panel.blessing_button.disable.assert_called_once()
        
        # エラーメッセージが表示される
        panel.result_label.set_text.assert_called_with("パーティが存在しません")


class TestBlessingPanelEventHandling:
    """BlessingPanelのイベント処理テスト"""
    
    def test_handle_event_blessing_button(self):
        """祝福ボタン押下イベントの処理"""
        from src.facilities.ui.temple.blessing_panel import BlessingPanel
        
        panel = Mock()
        panel.blessing_button = Mock()
        
        # ボタン押下イベントのモック
        event = Mock()
        event.type = pygame_gui.UI_BUTTON_PRESSED
        event.ui_element = panel.blessing_button
        
        with patch.object(panel, '_perform_blessing') as mock_blessing:
            BlessingPanel.handle_event(panel, event)
            
            mock_blessing.assert_called_once()
    
    def test_handle_event_unknown_element(self):
        """未知の要素のイベント処理"""
        from src.facilities.ui.temple.blessing_panel import BlessingPanel
        
        panel = Mock()
        panel.blessing_button = Mock()
        
        # 未知の要素のイベント
        event = Mock()
        event.type = pygame_gui.UI_BUTTON_PRESSED
        event.ui_element = Mock()  # 異なる要素
        
        with patch.object(BlessingPanel, '_perform_blessing') as mock_blessing:
            BlessingPanel.handle_event(panel, event)
            
            # 祝福メソッドは呼ばれない
            mock_blessing.assert_not_called()


class TestBlessingPanelBlessingPerformance:
    """BlessingPanelの祝福実行テスト"""
    
    def test_perform_blessing_success(self, sample_service_result):
        """祝福実行成功"""
        from src.facilities.ui.temple.blessing_panel import BlessingPanel
        
        panel = Mock()
        panel.service = Mock()
        panel.result_label = Mock()
        
        # 確認結果
        confirm_result = sample_service_result(
            success=True,
            result_type=Mock()
        )
        confirm_result.result_type.name = "CONFIRM"
        
        # 実行結果
        execute_result = sample_service_result(
            success=True,
            message="神の祝福があなたたちに降り注ぎました"
        )
        
        panel.service.execute_action.side_effect = [confirm_result, execute_result]
        
        with patch.object(panel, '_refresh_info') as mock_refresh:
            BlessingPanel._perform_blessing(panel)
            
            # サービスが2回呼ばれる（確認、実行）
            assert panel.service.execute_action.call_count == 2
            
            # 確認呼び出し
            panel.service.execute_action.assert_any_call("blessing", {})
            
            # 実行呼び出し
            panel.service.execute_action.assert_any_call("blessing", {
                "confirmed": True
            })
            
            # 成功メッセージが表示される
            panel.result_label.set_text.assert_called_with("神の祝福があなたたちに降り注ぎました")
            
            # 情報がリフレッシュされる
            mock_refresh.assert_called_once()
    
    def test_perform_blessing_failure(self, sample_service_result):
        """祝福実行失敗"""
        from src.facilities.ui.temple.blessing_panel import BlessingPanel
        
        panel = Mock()
        panel.service = Mock()
        panel.result_label = Mock()
        
        # 失敗結果
        result = sample_service_result(
            success=False,
            message="所持金が不足しています"
        )
        panel.service.execute_action.return_value = result
        
        BlessingPanel._perform_blessing(panel)
        
        # エラーメッセージが表示される
        panel.result_label.set_text.assert_called_with("所持金が不足しています")
    
    def test_perform_blessing_confirm_failure(self, sample_service_result):
        """祝福確認段階での失敗"""
        from src.facilities.ui.temple.blessing_panel import BlessingPanel
        
        panel = Mock()
        panel.service = Mock()
        panel.result_label = Mock()
        
        # 確認段階での失敗
        result = sample_service_result(
            success=False,
            message="現在祝福を受けることができません"
        )
        panel.service.execute_action.return_value = result
        
        BlessingPanel._perform_blessing(panel)
        
        # サービスが1回だけ呼ばれる
        assert panel.service.execute_action.call_count == 1
        
        # エラーメッセージが表示される
        panel.result_label.set_text.assert_called_with("現在祝福を受けることができません")


class TestBlessingPanelActions:
    """BlessingPanelのアクション機能テスト"""
    
    def test_refresh(self):
        """パネルのリフレッシュ"""
        from src.facilities.ui.temple.blessing_panel import BlessingPanel
        
        panel = Mock()
        panel.result_label = Mock()
        
        with patch.object(panel, '_refresh_info') as mock_refresh:
            BlessingPanel.refresh(panel)
            
            # 情報がリフレッシュされる
            mock_refresh.assert_called_once()
            
            # 結果表示がクリアされる
            panel.result_label.set_text.assert_called_with("")
    
    def test_show(self):
        """パネル表示"""
        from src.facilities.ui.temple.blessing_panel import BlessingPanel
        
        panel = Mock()
        panel.container = Mock()
        
        BlessingPanel.show(panel)
        
        panel.container.show.assert_called_once()
    
    def test_hide(self):
        """パネル非表示"""
        from src.facilities.ui.temple.blessing_panel import BlessingPanel
        
        panel = Mock()
        panel.container = Mock()
        
        BlessingPanel.hide(panel)
        
        panel.container.hide.assert_called_once()
    
    def test_destroy(self):
        """パネル破棄"""
        from src.facilities.ui.temple.blessing_panel import BlessingPanel
        
        panel = Mock()
        panel.container = Mock()
        
        BlessingPanel.destroy(panel)
        
        panel.container.kill.assert_called_once()
    
    def test_show_hide_destroy_no_container(self):
        """コンテナなしでの表示・非表示・破棄"""
        from src.facilities.ui.temple.blessing_panel import BlessingPanel
        
        panel = Mock()
        panel.container = None
        
        # エラーが発生しないことを確認
        try:
            BlessingPanel.show(panel)
            BlessingPanel.hide(panel)
            BlessingPanel.destroy(panel)
            assert True
        except Exception as e:
            pytest.fail(f"Unexpected exception: {e}")


class TestBlessingPanelUIContent:
    """BlessingPanelのUI内容テスト"""
    
    def test_blessing_description_content(self, mock_ui_setup):
        """祝福説明の内容確認"""
        from src.facilities.ui.temple.blessing_panel import BlessingPanel
        
        rect, parent, ui_manager, controller, service = mock_ui_setup
        
        with patch('pygame_gui.elements.UIPanel'), \
             patch('pygame_gui.elements.UILabel'), \
             patch('pygame_gui.elements.UITextBox') as mock_text_box, \
             patch('pygame_gui.elements.UIButton'), \
             patch.object(BlessingPanel, '_refresh_info'):
            
            panel = BlessingPanel(rect, parent, ui_manager, controller, service)
            
            # テキストボックスが作成される
            mock_text_box.assert_called_once()
            
            # 呼び出し引数を確認
            call_args = mock_text_box.call_args
            html_text = call_args[1]['html_text']
            
            # 祝福の効果説明が含まれる
            assert "攻撃力・防御力が上昇" in html_text
            assert "クリティカル率が向上" in html_text
            assert "状態異常に対する抵抗力が上昇" in html_text
            assert "効果は1回の戦闘まで持続" in html_text