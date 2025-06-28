"""
FormWindow のテスト

t-wada式TDDによるテストファースト開発
"""

import pytest
import pygame
import pygame_gui
from unittest.mock import Mock, patch
from src.ui.window_system import Window, WindowState
from src.ui.window_system.form_window import FormWindow, FormField, FormFieldType, FormValidationResult


class TestFormWindow:
    """FormWindow のテストクラス"""
    
    def setup_method(self):
        """各テストメソッドの前に実行される"""
        pygame.init()
        pygame.display.set_mode((1, 1), pygame.NOFRAME)
    
    def teardown_method(self):
        """各テストメソッドの後に実行される"""
        pygame.quit()
    
    def test_form_window_inherits_from_window(self):
        """FormWindowがWindowクラスを継承することを確認"""
        # Given: フォーム設定
        form_config = {
            'title': 'Test Form',
            'fields': [
                {'id': 'name', 'label': 'Name', 'type': 'text', 'required': True}
            ]
        }
        
        # When: FormWindowを作成
        form_window = FormWindow('test_form', form_config)
        
        # Then: Windowクラスを継承している
        assert isinstance(form_window, Window)
        assert form_window.window_id == 'test_form'
        assert form_window.form_config == form_config
        assert form_window.modal is False  # デフォルトは非モーダル
    
    def test_form_validates_config_structure(self):
        """フォーム設定の構造が検証されることを確認"""
        # Given: 不正なフォーム設定
        
        # When: fieldsが無い設定でFormWindowを作成しようとする
        # Then: 例外が発生する
        with pytest.raises(ValueError, match="Form config must contain 'fields'"):
            FormWindow('invalid_form', {})
        
        # When: fieldsが空の設定でFormWindowを作成しようとする
        # Then: 例外が発生する
        with pytest.raises(ValueError, match="Form config 'fields' cannot be empty"):
            FormWindow('empty_form', {'fields': []})
    
    def test_form_creates_text_input_field(self):
        """テキスト入力フィールドが作成されることを確認"""
        # Given: テキストフィールド設定
        form_config = {
            'title': 'Text Form',
            'fields': [
                {'id': 'username', 'label': 'Username', 'type': 'text', 'required': True}
            ]
        }
        
        form_window = FormWindow('text_form', form_config)
        form_window.create()
        
        # Then: テキストフィールドが作成される
        assert len(form_window.fields) == 1
        text_field = form_window.fields[0]
        assert text_field.field_id == 'username'
        assert text_field.label == 'Username'
        assert text_field.field_type == FormFieldType.TEXT
        assert text_field.required is True
        assert text_field.ui_element is not None
    
    def test_form_creates_number_input_field(self):
        """数値入力フィールドが作成されることを確認"""
        # Given: 数値フィールド設定
        form_config = {
            'fields': [
                {'id': 'age', 'label': 'Age', 'type': 'number', 'min': 0, 'max': 120}
            ]
        }
        
        form_window = FormWindow('number_form', form_config)
        form_window.create()
        
        # Then: 数値フィールドが作成される
        assert len(form_window.fields) == 1
        number_field = form_window.fields[0]
        assert number_field.field_id == 'age'
        assert number_field.field_type == FormFieldType.NUMBER
        assert number_field.validation_rules['min'] == 0
        assert number_field.validation_rules['max'] == 120
    
    def test_form_creates_dropdown_field(self):
        """ドロップダウンフィールドが作成されることを確認"""
        # Given: ドロップダウンフィールド設定
        form_config = {
            'fields': [
                {
                    'id': 'category', 
                    'label': 'Category', 
                    'type': 'dropdown',
                    'options': ['Option 1', 'Option 2', 'Option 3']
                }
            ]
        }
        
        form_window = FormWindow('dropdown_form', form_config)
        form_window.create()
        
        # Then: ドロップダウンフィールドが作成される
        assert len(form_window.fields) == 1
        dropdown_field = form_window.fields[0]
        assert dropdown_field.field_id == 'category'
        assert dropdown_field.field_type == FormFieldType.DROPDOWN
        assert dropdown_field.options == ['Option 1', 'Option 2', 'Option 3']
    
    def test_form_creates_checkbox_field(self):
        """チェックボックスフィールドが作成されることを確認"""
        # Given: チェックボックスフィールド設定
        form_config = {
            'fields': [
                {'id': 'agree', 'label': 'I agree to terms', 'type': 'checkbox'}
            ]
        }
        
        form_window = FormWindow('checkbox_form', form_config)
        form_window.create()
        
        # Then: チェックボックスフィールドが作成される
        assert len(form_window.fields) == 1
        checkbox_field = form_window.fields[0]
        assert checkbox_field.field_id == 'agree'
        assert checkbox_field.field_type == FormFieldType.CHECKBOX
    
    def test_form_validates_required_fields(self):
        """必須フィールドの検証が行われることを確認"""
        # Given: 必須フィールドを含むフォーム
        form_config = {
            'fields': [
                {'id': 'name', 'label': 'Name', 'type': 'text', 'required': True},
                {'id': 'email', 'label': 'Email', 'type': 'text', 'required': True}
            ]
        }
        
        form_window = FormWindow('validation_form', form_config)
        form_window.create()
        
        # When: 必須フィールドが空の状態で検証
        validation_result = form_window.validate_form()
        
        # Then: 検証が失敗する
        assert validation_result.is_valid is False
        assert len(validation_result.errors) == 2
        assert 'name' in validation_result.errors
        assert 'email' in validation_result.errors
    
    def test_form_validates_number_range(self):
        """数値範囲の検証が行われることを確認"""
        # Given: 数値フィールドを含むフォーム
        form_config = {
            'fields': [
                {'id': 'score', 'label': 'Score', 'type': 'number', 'min': 0, 'max': 100}
            ]
        }
        
        form_window = FormWindow('range_form', form_config)
        form_window.create()
        
        # When: 範囲外の値を設定
        form_window.set_field_value('score', '150')
        validation_result = form_window.validate_form()
        
        # Then: 検証が失敗する
        assert validation_result.is_valid is False
        assert 'score' in validation_result.errors
        assert 'out of range' in validation_result.errors['score'].lower()
    
    def test_form_submit_with_valid_data(self):
        """有効なデータでフォームが送信されることを確認"""
        # Given: フォーム
        form_config = {
            'fields': [
                {'id': 'name', 'label': 'Name', 'type': 'text', 'required': True}
            ]
        }
        
        form_window = FormWindow('submit_form', form_config)
        form_window.create()
        
        # When: 有効なデータを設定して送信
        form_window.set_field_value('name', 'John Doe')
        
        with patch.object(form_window, 'send_message') as mock_send:
            result = form_window.submit_form()
        
        # Then: 送信が成功する
        assert result is True
        mock_send.assert_called_once_with('form_submitted', {
            'form_id': 'submit_form',
            'data': {'name': 'John Doe'}
        })
    
    def test_form_submit_fails_with_invalid_data(self):
        """無効なデータでフォーム送信が失敗することを確認"""
        # Given: 必須フィールドを含むフォーム
        form_config = {
            'fields': [
                {'id': 'name', 'label': 'Name', 'type': 'text', 'required': True}
            ]
        }
        
        form_window = FormWindow('fail_form', form_config)
        form_window.create()
        
        # When: 無効なデータで送信
        with patch.object(form_window, 'send_message') as mock_send:
            result = form_window.submit_form()
        
        # Then: 送信が失敗する
        assert result is False
        mock_send.assert_not_called()
    
    def test_form_cancel_sends_message(self):
        """フォームキャンセルでメッセージが送信されることを確認"""
        # Given: フォーム
        form_config = {
            'fields': [
                {'id': 'name', 'label': 'Name', 'type': 'text'}
            ]
        }
        
        form_window = FormWindow('cancel_form', form_config)
        form_window.create()
        
        # When: キャンセル
        with patch.object(form_window, 'send_message') as mock_send:
            form_window.cancel_form()
        
        # Then: キャンセルメッセージが送信される
        mock_send.assert_called_once_with('form_cancelled', {
            'form_id': 'cancel_form'
        })
    
    def test_form_keyboard_navigation(self):
        """キーボードナビゲーションが動作することを確認"""
        # Given: 複数フィールドを含むフォーム
        form_config = {
            'fields': [
                {'id': 'field1', 'label': 'Field 1', 'type': 'text'},
                {'id': 'field2', 'label': 'Field 2', 'type': 'text'},
                {'id': 'field3', 'label': 'Field 3', 'type': 'text'}
            ]
        }
        
        form_window = FormWindow('nav_form', form_config)
        form_window.create()
        
        # When: Tabキーでナビゲーション
        tab_event = Mock()
        tab_event.type = pygame.KEYDOWN
        tab_event.key = pygame.K_TAB
        tab_event.mod = 0  # modifierなし
        
        form_window.handle_event(tab_event)
        
        # Then: フォーカスが次のフィールドに移動
        assert form_window.focused_field_index == 1
        
        # When: Shift+Tabで前のフィールドに移動
        shift_tab_event = Mock()
        shift_tab_event.type = pygame.KEYDOWN
        shift_tab_event.key = pygame.K_TAB
        shift_tab_event.mod = pygame.KMOD_SHIFT
        
        form_window.handle_event(shift_tab_event)
        
        # Then: フォーカスが前のフィールドに移動
        assert form_window.focused_field_index == 0
    
    def test_form_enter_key_submits_form(self):
        """Enterキーでフォームが送信されることを確認"""
        # Given: フォーム
        form_config = {
            'fields': [
                {'id': 'name', 'label': 'Name', 'type': 'text', 'required': True}
            ]
        }
        
        form_window = FormWindow('enter_form', form_config)
        form_window.create()
        form_window.set_field_value('name', 'Test User')
        
        # When: Enterキーを押す
        enter_event = Mock()
        enter_event.type = pygame.KEYDOWN
        enter_event.key = pygame.K_RETURN
        
        with patch.object(form_window, 'send_message') as mock_send:
            result = form_window.handle_event(enter_event)
        
        # Then: フォームが送信される
        assert result is True
        mock_send.assert_called_once_with('form_submitted', {
            'form_id': 'enter_form',
            'data': {'name': 'Test User'}
        })
    
    def test_form_escape_key_cancels_form(self):
        """ESCキーでフォームがキャンセルされることを確認"""
        # Given: フォーム
        form_config = {
            'fields': [
                {'id': 'name', 'label': 'Name', 'type': 'text'}
            ]
        }
        
        form_window = FormWindow('esc_form', form_config)
        form_window.create()
        
        # When: ESCキーを押す
        with patch.object(form_window, 'send_message') as mock_send:
            result = form_window.handle_escape()
        
        # Then: フォームがキャンセルされる
        assert result is True
        mock_send.assert_called_once_with('form_cancelled', {
            'form_id': 'esc_form'
        })
    
    def test_form_cleanup_removes_ui_elements(self):
        """クリーンアップでUI要素が適切に削除されることを確認"""
        # Given: 作成されたフォーム
        form_config = {
            'fields': [
                {'id': 'field1', 'label': 'Field 1', 'type': 'text'},
                {'id': 'field2', 'label': 'Field 2', 'type': 'dropdown', 'options': ['A', 'B']}
            ]
        }
        
        form_window = FormWindow('cleanup_form', form_config)
        form_window.create()
        
        # When: クリーンアップを実行
        form_window.cleanup_ui()
        
        # Then: UI要素が削除される
        assert len(form_window.fields) == 0
        assert form_window.ui_manager is None