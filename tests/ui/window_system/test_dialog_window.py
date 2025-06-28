"""
DialogWindow のテスト

t-wada式TDDによるテストファースト開発
"""

import pytest
import pygame
import pygame_gui
from unittest.mock import Mock, patch
from src.ui.window_system import Window, WindowState
from src.ui.window_system.dialog_window import DialogWindow, DialogType, DialogResult


class TestDialogWindow:
    """DialogWindow のテストクラス"""
    
    def setup_method(self):
        """各テストメソッドの前に実行される"""
        pygame.init()
        pygame.display.set_mode((1, 1), pygame.NOFRAME)
    
    def teardown_method(self):
        """各テストメソッドの後に実行される"""
        pygame.quit()
    
    def test_dialog_window_inherits_from_window(self):
        """DialogWindowがWindowクラスを継承することを確認"""
        # Given: ダイアログ設定
        dialog_type = DialogType.CONFIRMATION
        message = "Are you sure you want to continue?"
        
        # When: DialogWindowを作成
        dialog_window = DialogWindow('test_dialog', dialog_type, message)
        
        # Then: Windowクラスを継承している
        assert isinstance(dialog_window, Window)
        assert dialog_window.window_id == 'test_dialog'
        assert dialog_window.dialog_type == dialog_type
        assert dialog_window.message == message
        assert dialog_window.modal is True  # ダイアログは常にモーダル
    
    def test_information_dialog_has_ok_button_only(self):
        """情報ダイアログがOKボタンのみを持つことを確認"""
        # Given: 情報ダイアログ
        dialog = DialogWindow('info_dialog', DialogType.INFORMATION, "Information message")
        dialog.create()
        
        # Then: OKボタンのみが存在する
        assert len(dialog.buttons) == 1
        assert dialog.buttons[0].text == "OK"
        assert dialog.buttons[0].result == DialogResult.OK
    
    def test_confirmation_dialog_has_yes_no_buttons(self):
        """確認ダイアログがYes/Noボタンを持つことを確認"""
        # Given: 確認ダイアログ
        dialog = DialogWindow('confirm_dialog', DialogType.CONFIRMATION, "Confirm action?")
        dialog.create()
        
        # Then: Yes/Noボタンが存在する
        assert len(dialog.buttons) == 2
        
        # ボタンの順序を確認
        yes_button = next(btn for btn in dialog.buttons if btn.result == DialogResult.YES)
        no_button = next(btn for btn in dialog.buttons if btn.result == DialogResult.NO)
        
        assert yes_button.text == "Yes"
        assert no_button.text == "No"
    
    def test_input_dialog_has_text_field_and_buttons(self):
        """入力ダイアログがテキストフィールドとボタンを持つことを確認"""
        # Given: 入力ダイアログ
        dialog = DialogWindow('input_dialog', DialogType.INPUT, "Enter your name:", 
                            input_config={'placeholder': 'Name here'})
        dialog.create()
        
        # Then: テキストフィールドとOK/Cancelボタンが存在する
        assert dialog.text_input is not None
        assert len(dialog.buttons) == 2
        
        ok_button = next(btn for btn in dialog.buttons if btn.result == DialogResult.OK)
        cancel_button = next(btn for btn in dialog.buttons if btn.result == DialogResult.CANCEL)
        
        assert ok_button.text == "OK"
        assert cancel_button.text == "Cancel"
    
    def test_error_dialog_has_error_styling(self):
        """エラーダイアログがエラー用スタイリングを持つことを確認"""
        # Given: エラーダイアログ
        dialog = DialogWindow('error_dialog', DialogType.ERROR, "An error occurred!")
        dialog.create()
        
        # Then: エラー用のスタイリングが適用される
        assert dialog.style_class == 'error_dialog'
        assert len(dialog.buttons) == 1
        assert dialog.buttons[0].result == DialogResult.OK
    
    def test_success_dialog_has_success_styling(self):
        """成功ダイアログが成功用スタイリングを持つことを確認"""
        # Given: 成功ダイアログ
        dialog = DialogWindow('success_dialog', DialogType.SUCCESS, "Operation completed!")
        dialog.create()
        
        # Then: 成功用のスタイリングが適用される
        assert dialog.style_class == 'success_dialog'
        assert len(dialog.buttons) == 1
        assert dialog.buttons[0].result == DialogResult.OK
    
    def test_dialog_button_click_sets_result(self):
        """ボタンクリックで結果が設定されることを確認"""
        # Given: 確認ダイアログ
        dialog = DialogWindow('result_dialog', DialogType.CONFIRMATION, "Test confirmation")
        dialog.create()
        
        # When: Yesボタンをクリック
        yes_button = next(btn for btn in dialog.buttons if btn.result == DialogResult.YES)
        mock_event = Mock()
        mock_event.type = pygame_gui.UI_BUTTON_PRESSED
        mock_event.ui_element = yes_button.ui_element
        
        with patch.object(dialog, 'send_message') as mock_send:
            result = dialog.handle_event(mock_event)
        
        # Then: 結果が設定され、メッセージが送信される
        assert result is True
        assert dialog.result == DialogResult.YES
        assert mock_send.call_count == 2
        mock_send.assert_any_call('dialog_result', {'result': DialogResult.YES, 'data': None})
        mock_send.assert_any_call('close_requested')
    
    def test_input_dialog_returns_text_data(self):
        """入力ダイアログがテキストデータを返すことを確認"""
        # Given: 入力ダイアログとテキスト入力
        dialog = DialogWindow('input_test', DialogType.INPUT, "Enter text:")
        dialog.create()
        
        # テキスト入力をシミュレート
        dialog.text_input.set_text("test input")
        
        # When: OKボタンをクリック
        ok_button = next(btn for btn in dialog.buttons if btn.result == DialogResult.OK)
        mock_event = Mock()
        mock_event.type = pygame_gui.UI_BUTTON_PRESSED
        mock_event.ui_element = ok_button.ui_element
        
        with patch.object(dialog, 'send_message') as mock_send:
            dialog.handle_event(mock_event)
        
        # Then: 入力されたテキストがデータとして返される
        assert dialog.result == DialogResult.OK
        assert mock_send.call_count == 2
        mock_send.assert_any_call('dialog_result', {'result': DialogResult.OK, 'data': "test input"})
        mock_send.assert_any_call('close_requested')
    
    def test_dialog_esc_key_cancels_dialog(self):
        """ESCキーでダイアログがキャンセルされることを確認"""
        # Given: ダイアログ
        dialog = DialogWindow('esc_dialog', DialogType.CONFIRMATION, "Test ESC")
        dialog.create()
        
        # When: ESCキーを押す
        with patch.object(dialog, 'send_message') as mock_send:
            result = dialog.handle_escape()
        
        # Then: キャンセル結果が設定される
        assert result is True
        assert dialog.result == DialogResult.CANCEL
        assert mock_send.call_count == 2
        mock_send.assert_any_call('dialog_result', {'result': DialogResult.CANCEL, 'data': None})
        mock_send.assert_any_call('close_requested')
    
    def test_dialog_enter_key_activates_default_button(self):
        """Enterキーでデフォルトボタンが実行されることを確認"""
        # Given: 確認ダイアログ（デフォルトはYes）
        dialog = DialogWindow('enter_dialog', DialogType.CONFIRMATION, "Test Enter")
        dialog.create()
        
        # When: Enterキーを押す
        enter_event = Mock()
        enter_event.type = pygame.KEYDOWN
        enter_event.key = pygame.K_RETURN
        
        with patch.object(dialog, 'send_message') as mock_send:
            result = dialog.handle_event(enter_event)
        
        # Then: デフォルトボタン（Yes）が実行される
        assert result is True
        assert dialog.result == DialogResult.YES
        assert mock_send.call_count == 2
        mock_send.assert_any_call('dialog_result', {'result': DialogResult.YES, 'data': None})
        mock_send.assert_any_call('close_requested')
    
    def test_dialog_auto_closes_on_result(self):
        """結果設定時にダイアログが自動的に閉じることを確認"""
        # Given: ダイアログ
        dialog = DialogWindow('auto_close', DialogType.INFORMATION, "Auto close test")
        dialog.create()
        
        # When: ボタンをクリック
        ok_button = dialog.buttons[0]
        mock_event = Mock()
        mock_event.type = pygame_gui.UI_BUTTON_PRESSED
        mock_event.ui_element = ok_button.ui_element
        
        with patch.object(dialog, 'send_message') as mock_send:
            dialog.handle_event(mock_event)
        
        # Then: 閉じるメッセージも送信される
        assert mock_send.call_count == 2
        mock_send.assert_any_call('dialog_result', {'result': DialogResult.OK, 'data': None})
        mock_send.assert_any_call('close_requested')
    
    def test_dialog_supports_custom_buttons(self):
        """カスタムボタンがサポートされることを確認"""
        # Given: カスタムボタン設定
        custom_buttons = [
            {'text': 'Save', 'result': DialogResult.CUSTOM, 'custom_data': 'save'},
            {'text': 'Don\'t Save', 'result': DialogResult.CUSTOM, 'custom_data': 'dont_save'},
            {'text': 'Cancel', 'result': DialogResult.CANCEL}
        ]
        
        dialog = DialogWindow('custom_dialog', DialogType.CUSTOM, "Save changes?", 
                            custom_buttons=custom_buttons)
        dialog.create()
        
        # Then: カスタムボタンが作成される
        assert len(dialog.buttons) == 3
        
        save_button = dialog.buttons[0]
        assert save_button.text == 'Save'
        assert save_button.result == DialogResult.CUSTOM
        assert save_button.custom_data == 'save'
    
    def test_dialog_validates_required_parameters(self):
        """必須パラメータが検証されることを確認"""
        # Given: 不正なパラメータ
        
        # When: 空のメッセージでDialogWindowを作成しようとする
        # Then: 例外が発生する
        with pytest.raises(ValueError, match="Message cannot be empty"):
            DialogWindow('invalid_dialog', DialogType.INFORMATION, "")
        
        # When: 不正なダイアログタイプでDialogWindowを作成しようとする
        # Then: 例外が発生する
        with pytest.raises(ValueError, match="Invalid dialog type"):
            DialogWindow('invalid_type', "invalid_type", "Message")
    
    def test_dialog_cleanup_removes_ui_elements(self):
        """クリーンアップでUI要素が適切に削除されることを確認"""
        # Given: 作成されたダイアログ
        dialog = DialogWindow('cleanup_dialog', DialogType.CONFIRMATION, "Cleanup test")
        dialog.create()
        
        # When: クリーンアップを実行
        dialog.cleanup_ui()
        
        # Then: UI要素が削除される
        assert len(dialog.buttons) == 0
        assert dialog.text_input is None
        assert dialog.ui_manager is None