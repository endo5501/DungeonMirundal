"""寄付パネルのテスト"""

import pytest
import pygame
import pygame_gui
from unittest.mock import Mock, MagicMock, patch


@pytest.fixture
def mock_ui_setup():
    """UI要素のモック"""
    rect = pygame.Rect(0, 0, 420, 340)
    parent = Mock()
    ui_manager = Mock()
    controller = Mock()
    service = Mock()
    return rect, parent, ui_manager, controller, service


@pytest.fixture
def sample_party():
    """サンプルパーティデータ"""
    party = Mock()
    party.gold = 2500
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


class TestDonationPanelBasic:
    """DonationPanelの基本機能テスト"""
    
    def test_initialization(self, mock_ui_setup):
        """正常に初期化される"""
        from src.facilities.ui.temple.donation_panel import DonationPanel
        
        rect, parent, ui_manager, controller, service = mock_ui_setup
        
        with patch('pygame_gui.elements.UIPanel'), \
             patch('pygame_gui.elements.UILabel'), \
             patch('pygame_gui.elements.UITextBox'), \
             patch('pygame_gui.elements.UITextEntryLine'), \
             patch('pygame_gui.elements.UIButton'), \
             patch.object(DonationPanel, '_refresh_info'):
            
            panel = DonationPanel(rect, parent, ui_manager, controller, service)
            
            # 基本属性の確認
            assert panel.rect == rect
            assert panel.parent == parent
            assert panel.ui_manager == ui_manager
            assert panel.controller == controller
            assert panel.service == service
            
            # プリセットボタンの確認
            assert len(panel.preset_buttons) == 4
    
    def test_create_ui_elements(self, mock_ui_setup):
        """UI要素が正常に作成される"""
        from src.facilities.ui.temple.donation_panel import DonationPanel
        
        rect, parent, ui_manager, controller, service = mock_ui_setup
        
        with patch('pygame_gui.elements.UIPanel') as mock_panel, \
             patch('pygame_gui.elements.UILabel') as mock_label, \
             patch('pygame_gui.elements.UITextBox') as mock_text_box, \
             patch('pygame_gui.elements.UITextEntryLine') as mock_entry, \
             patch('pygame_gui.elements.UIButton') as mock_button, \
             patch.object(DonationPanel, '_refresh_info'):
            
            panel = DonationPanel(rect, parent, ui_manager, controller, service)
            
            # UI要素が作成される
            mock_panel.assert_called_once()
            assert mock_label.call_count == 4  # タイトル、金額ラベル、所持金、結果
            mock_text_box.assert_called_once()  # 説明テキストボックス
            mock_entry.assert_called_once()    # 金額入力
            assert mock_button.call_count == 5  # プリセットボタン4個 + 寄付ボタン1個


class TestDonationPanelInfoRefresh:
    """DonationPanelの情報更新テスト"""
    
    def test_refresh_info_with_gold(self, mock_ui_setup, sample_party):
        """所持金ありでの情報更新"""
        from src.facilities.ui.temple.donation_panel import DonationPanel
        
        panel = Mock()
        panel.service = Mock()
        panel.service.party = sample_party  # 2500 G
        panel.gold_label = Mock()
        panel.donation_button = Mock()
        panel.result_label = Mock()
        
        # プリセットボタンのモック
        preset_buttons = []
        amounts = [100, 500, 1000, 5000]
        for amount in amounts:
            button = Mock()
            preset_buttons.append((button, amount))
        panel.preset_buttons = preset_buttons
        
        DonationPanel._refresh_info(panel)
        
        # 所持金表示が更新される
        panel.gold_label.set_text.assert_called_with("所持金: 2500 G")
        
        # 寄付ボタンが有効化される
        panel.donation_button.enable.assert_called_once()
        
        # プリセットボタンの有効/無効チェック
        for (button, amount) in preset_buttons:
            if amount <= 2500:
                button.enable.assert_called_once()
            else:
                button.disable.assert_called_once()
    
    def test_refresh_info_with_limited_gold(self, mock_ui_setup, sample_party):
        """限られた所持金での情報更新"""
        from src.facilities.ui.temple.donation_panel import DonationPanel
        
        panel = Mock()
        panel.service = Mock()
        sample_party.gold = 800  # 1000 G未満
        panel.service.party = sample_party
        panel.gold_label = Mock()
        panel.donation_button = Mock()
        panel.result_label = Mock()
        
        # プリセットボタンのモック
        preset_buttons = []
        amounts = [100, 500, 1000, 5000]
        for amount in amounts:
            button = Mock()
            preset_buttons.append((button, amount))
        panel.preset_buttons = preset_buttons
        
        DonationPanel._refresh_info(panel)
        
        # 所持金表示が更新される
        panel.gold_label.set_text.assert_called_with("所持金: 800 G")
        
        # 寄付ボタンが有効化される
        panel.donation_button.enable.assert_called_once()
        
        # プリセットボタンの有効/無効チェック
        # 100G, 500G: 有効、1000G, 5000G: 無効
        assert preset_buttons[0][0].enable.called  # 100G
        assert preset_buttons[1][0].enable.called  # 500G
        assert preset_buttons[2][0].disable.called  # 1000G
        assert preset_buttons[3][0].disable.called  # 5000G
    
    def test_refresh_info_no_gold(self, mock_ui_setup, sample_party):
        """所持金なしでの情報更新"""
        from src.facilities.ui.temple.donation_panel import DonationPanel
        
        panel = Mock()
        panel.service = Mock()
        sample_party.gold = 0
        panel.service.party = sample_party
        panel.gold_label = Mock()
        panel.donation_button = Mock()
        panel.result_label = Mock()
        
        # プリセットボタンのモック
        preset_buttons = []
        amounts = [100, 500, 1000, 5000]
        for amount in amounts:
            button = Mock()
            preset_buttons.append((button, amount))
        panel.preset_buttons = preset_buttons
        
        DonationPanel._refresh_info(panel)
        
        # 所持金表示が更新される
        panel.gold_label.set_text.assert_called_with("所持金: 0 G")
        
        # 寄付ボタンが無効化される
        panel.donation_button.disable.assert_called_once()
        
        # 全プリセットボタンが無効化される
        for (button, amount) in preset_buttons:
            button.disable.assert_called_once()
        
        # 不足メッセージが表示される
        panel.result_label.set_text.assert_called_with("寄付する金額がありません")
    
    def test_refresh_info_no_party(self, mock_ui_setup):
        """パーティなしでの情報更新"""
        from src.facilities.ui.temple.donation_panel import DonationPanel
        
        panel = Mock()
        panel.service = Mock()
        panel.service.party = None
        panel.gold_label = Mock()
        panel.donation_button = Mock()
        panel.result_label = Mock()
        
        # プリセットボタンのモック
        preset_buttons = []
        amounts = [100, 500, 1000, 5000]
        for amount in amounts:
            button = Mock()
            preset_buttons.append((button, amount))
        panel.preset_buttons = preset_buttons
        
        DonationPanel._refresh_info(panel)
        
        # 所持金表示がゼロになる
        panel.gold_label.set_text.assert_called_with("所持金: 0 G")
        
        # 寄付ボタンが無効化される
        panel.donation_button.disable.assert_called_once()
        
        # 全プリセットボタンが無効化される
        for (button, amount) in preset_buttons:
            button.disable.assert_called_once()
        
        # エラーメッセージが表示される
        panel.result_label.set_text.assert_called_with("パーティが存在しません")


class TestDonationPanelEventHandling:
    """DonationPanelのイベント処理テスト"""
    
    def test_handle_event_donation_button(self):
        """寄付ボタン押下イベントの処理"""
        from src.facilities.ui.temple.donation_panel import DonationPanel
        
        panel = Mock()
        panel.donation_button = Mock()
        panel.preset_buttons = []
        
        # ボタン押下イベントのモック
        event = Mock()
        event.type = pygame_gui.UI_BUTTON_PRESSED
        event.ui_element = panel.donation_button
        
        with patch.object(panel, '_perform_donation') as mock_donation:
            DonationPanel.handle_event(panel, event)
            
            mock_donation.assert_called_once()
    
    def test_handle_event_preset_button(self):
        """プリセットボタン押下イベントの処理"""
        from src.facilities.ui.temple.donation_panel import DonationPanel
        
        panel = Mock()
        panel.donation_button = Mock()
        panel.amount_input = Mock()
        
        # プリセットボタンのモック
        preset_button = Mock()
        panel.preset_buttons = [(preset_button, 500)]
        
        # ボタン押下イベントのモック
        event = Mock()
        event.type = pygame_gui.UI_BUTTON_PRESSED
        event.ui_element = preset_button
        
        DonationPanel.handle_event(panel, event)
        
        # 金額入力に値が設定される
        panel.amount_input.set_text.assert_called_with("500")
    
    def test_handle_event_unknown_element(self):
        """未知の要素のイベント処理"""
        from src.facilities.ui.temple.donation_panel import DonationPanel
        
        panel = Mock()
        panel.donation_button = Mock()
        panel.preset_buttons = []
        
        # 未知の要素のイベント
        event = Mock()
        event.type = pygame_gui.UI_BUTTON_PRESSED
        event.ui_element = Mock()  # 異なる要素
        
        with patch.object(DonationPanel, '_perform_donation') as mock_donation:
            DonationPanel.handle_event(panel, event)
            
            # 寄付メソッドは呼ばれない
            mock_donation.assert_not_called()


class TestDonationPanelDonationPerformance:
    """DonationPanelの寄付実行テスト"""
    
    def test_perform_donation_success(self, sample_service_result):
        """寄付実行成功"""
        from src.facilities.ui.temple.donation_panel import DonationPanel
        
        panel = Mock()
        panel.amount_input = Mock()
        panel.amount_input.get_text.return_value = "1000"
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
            message="1000Gを寄付しました。神々の加護がありますように"
        )
        
        panel.service.execute_action.side_effect = [confirm_result, execute_result]
        
        with patch.object(panel, '_refresh_info') as mock_refresh:
            DonationPanel._perform_donation(panel)
            
            # サービスが2回呼ばれる（確認、実行）
            assert panel.service.execute_action.call_count == 2
            
            # 確認呼び出し
            panel.service.execute_action.assert_any_call("donation", {
                "amount": 1000
            })
            
            # 実行呼び出し
            panel.service.execute_action.assert_any_call("donation", {
                "amount": 1000,
                "confirmed": True
            })
            
            # 成功メッセージが表示される
            panel.result_label.set_text.assert_called_with("1000Gを寄付しました。神々の加護がありますように")
            
            # 情報がリフレッシュされる
            mock_refresh.assert_called_once()
            
            # 金額入力がリセットされる
            panel.amount_input.set_text.assert_called_with("0")
    
    def test_perform_donation_failure(self, sample_service_result):
        """寄付実行失敗"""
        from src.facilities.ui.temple.donation_panel import DonationPanel
        
        panel = Mock()
        panel.amount_input = Mock()
        panel.amount_input.get_text.return_value = "5000"
        panel.service = Mock()
        panel.result_label = Mock()
        
        # 失敗結果
        result = sample_service_result(
            success=False,
            message="所持金が不足しています"
        )
        panel.service.execute_action.return_value = result
        
        DonationPanel._perform_donation(panel)
        
        # エラーメッセージが表示される
        panel.result_label.set_text.assert_called_with("所持金が不足しています")
    
    def test_perform_donation_invalid_amount(self):
        """無効な金額での寄付実行"""
        from src.facilities.ui.temple.donation_panel import DonationPanel
        
        panel = Mock()
        panel.amount_input = Mock()
        panel.amount_input.get_text.return_value = "abc"  # 無効な数値
        panel.service = Mock()
        panel.result_label = Mock()
        
        DonationPanel._perform_donation(panel)
        
        # エラーメッセージが表示される
        panel.result_label.set_text.assert_called_with("有効な金額を入力してください")
        
        # サービスが呼ばれない
        panel.service.execute_action.assert_not_called()
    
    def test_perform_donation_zero_amount(self):
        """ゼロ金額での寄付実行"""
        from src.facilities.ui.temple.donation_panel import DonationPanel
        
        panel = Mock()
        panel.amount_input = Mock()
        panel.amount_input.get_text.return_value = "0"
        panel.service = Mock()
        panel.result_label = Mock()
        
        DonationPanel._perform_donation(panel)
        
        # エラーメッセージが表示される
        panel.result_label.set_text.assert_called_with("寄付金額は1G以上を指定してください")
        
        # サービスが呼ばれない
        panel.service.execute_action.assert_not_called()
    
    def test_perform_donation_negative_amount(self):
        """負の金額での寄付実行"""
        from src.facilities.ui.temple.donation_panel import DonationPanel
        
        panel = Mock()
        panel.amount_input = Mock()
        panel.amount_input.get_text.return_value = "-100"
        panel.service = Mock()
        panel.result_label = Mock()
        
        DonationPanel._perform_donation(panel)
        
        # エラーメッセージが表示される
        panel.result_label.set_text.assert_called_with("寄付金額は1G以上を指定してください")
        
        # サービスが呼ばれない
        panel.service.execute_action.assert_not_called()


class TestDonationPanelActions:
    """DonationPanelのアクション機能テスト"""
    
    def test_refresh(self):
        """パネルのリフレッシュ"""
        from src.facilities.ui.temple.donation_panel import DonationPanel
        
        panel = Mock()
        panel.amount_input = Mock()
        panel.result_label = Mock()
        
        with patch.object(panel, '_refresh_info') as mock_refresh:
            DonationPanel.refresh(panel)
            
            # 情報がリフレッシュされる
            mock_refresh.assert_called_once()
            
            # 金額入力がリセットされる
            panel.amount_input.set_text.assert_called_with("0")
            
            # 結果表示がクリアされる
            panel.result_label.set_text.assert_called_with("")
    
    def test_show(self):
        """パネル表示"""
        from src.facilities.ui.temple.donation_panel import DonationPanel
        
        panel = Mock()
        panel.container = Mock()
        
        DonationPanel.show(panel)
        
        panel.container.show.assert_called_once()
    
    def test_hide(self):
        """パネル非表示"""
        from src.facilities.ui.temple.donation_panel import DonationPanel
        
        panel = Mock()
        panel.container = Mock()
        
        DonationPanel.hide(panel)
        
        panel.container.hide.assert_called_once()
    
    def test_destroy(self):
        """パネル破棄"""
        from src.facilities.ui.temple.donation_panel import DonationPanel
        
        panel = Mock()
        panel.container = Mock()
        
        DonationPanel.destroy(panel)
        
        panel.container.kill.assert_called_once()
    
    def test_show_hide_destroy_no_container(self):
        """コンテナなしでの表示・非表示・破棄"""
        from src.facilities.ui.temple.donation_panel import DonationPanel
        
        panel = Mock()
        panel.container = None
        
        # エラーが発生しないことを確認
        try:
            DonationPanel.show(panel)
            DonationPanel.hide(panel)
            DonationPanel.destroy(panel)
            assert True
        except Exception as e:
            pytest.fail(f"Unexpected exception: {e}")


class TestDonationPanelUIContent:
    """DonationPanelのUI内容テスト"""
    
    def test_donation_description_content(self, mock_ui_setup):
        """寄付説明の内容確認"""
        from src.facilities.ui.temple.donation_panel import DonationPanel
        
        rect, parent, ui_manager, controller, service = mock_ui_setup
        
        with patch('pygame_gui.elements.UIPanel'), \
             patch('pygame_gui.elements.UILabel'), \
             patch('pygame_gui.elements.UITextBox') as mock_text_box, \
             patch('pygame_gui.elements.UITextEntryLine'), \
             patch('pygame_gui.elements.UIButton'), \
             patch.object(DonationPanel, '_refresh_info'):
            
            panel = DonationPanel(rect, parent, ui_manager, controller, service)
            
            # テキストボックスが作成される
            mock_text_box.assert_called_once()
            
            # 呼び出し引数を確認
            call_args = mock_text_box.call_args
            html_text = call_args[1]['html_text']
            
            # 寄付の効果説明が含まれる
            assert "カルマ値の向上" in html_text
            assert "神の加護による幸運の向上" in html_text
            assert "より良いアイテムの発見確率上昇" in html_text
            assert "慈悲深い行いは必ず報われます" in html_text
    
    def test_preset_amounts(self, mock_ui_setup):
        """プリセット金額の確認"""
        from src.facilities.ui.temple.donation_panel import DonationPanel
        
        rect, parent, ui_manager, controller, service = mock_ui_setup
        
        with patch('pygame_gui.elements.UIPanel'), \
             patch('pygame_gui.elements.UILabel'), \
             patch('pygame_gui.elements.UITextBox'), \
             patch('pygame_gui.elements.UITextEntryLine'), \
             patch('pygame_gui.elements.UIButton'), \
             patch.object(DonationPanel, '_refresh_info'):
            
            panel = DonationPanel(rect, parent, ui_manager, controller, service)
            
            # プリセット金額の確認
            preset_amounts = [amount for (button, amount) in panel.preset_buttons]
            expected_amounts = [100, 500, 1000, 5000]
            
            assert preset_amounts == expected_amounts