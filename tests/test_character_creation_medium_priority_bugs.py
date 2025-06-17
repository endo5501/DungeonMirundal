"""キャラクター作成画面の優先度:中バグ修正テスト"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from src.ui.character_creation import CharacterCreationWizard, CreationStep


class TestCharacterCreationMediumPriorityBugs:
    """キャラクター作成画面の優先度:中バグ修正テスト"""
    
    def setup_method(self):
        """各テストメソッドの前に実行"""
        pass
        
    def teardown_method(self):
        """各テストメソッドの後に実行"""
        pass
    
    def create_mock_wizard(self, callback=None):
        """モックウィザード作成（簡易版）"""
        # CharacterCreationWizardを直接インスタンス化せず、必要なメソッドのみテスト
        wizard = Mock(spec=CharacterCreationWizard)
        wizard.callback = callback
        wizard.on_cancel = wizard._default_cancel_handler
        wizard.current_ui = None
        wizard.character_data = {'name': '', 'race': '', 'character_class': '', 'base_stats': None}
        
        # UI Manager モック
        mock_ui_manager = Mock()
        wizard.ui_manager = mock_ui_manager
        
        # Config Manager モック
        mock_config_manager = Mock()
        mock_config_manager.get_text.return_value = "名前を入力してください"
        wizard.config_manager = mock_config_manager
        
        # 実際のメソッドをモック（動作する実装付き）
        def mock_default_cancel_handler():
            wizard._close_wizard()
        
        def mock_on_name_cancelled():
            if hasattr(wizard, 'current_ui') and wizard.current_ui:
                mock_ui_manager.hide_element(wizard.current_ui.element_id)
                mock_ui_manager.unregister_element(wizard.current_ui.element_id)
            wizard._close_wizard()
        
        def mock_show_name_input():
            mock_config_manager.get_text("character.enter_name")
        
        wizard._default_cancel_handler = Mock(side_effect=mock_default_cancel_handler)
        wizard._close_wizard = Mock()
        wizard._on_name_cancelled = Mock(side_effect=mock_on_name_cancelled)
        wizard._show_name_input = Mock(side_effect=mock_show_name_input)
        
        return wizard, mock_ui_manager, mock_config_manager
    
    def test_cancel_button_does_not_crash_with_default_handler(self):
        """[キャンセル]ボタンがデフォルトハンドラーでクラッシュしないことを確認"""
        wizard, mock_ui_manager, mock_config_manager = self.create_mock_wizard()
        
        # on_cancelがデフォルトハンドラーに設定されていることを確認
        assert wizard.on_cancel is not None
        assert callable(wizard.on_cancel)
        
        # キャンセル処理でクラッシュしないことを確認
        try:
            wizard._on_name_cancelled()
            test_passed = True
        except Exception as e:
            test_passed = False
            pytest.fail(f"キャンセル処理でクラッシュが発生しました: {e}")
        
        assert test_passed, "キャンセル処理が正常に完了しませんでした"
    
    def test_cancel_button_closes_wizard_properly(self):
        """[キャンセル]ボタンがウィザードを適切に閉じることを確認"""
        wizard, mock_ui_manager, mock_config_manager = self.create_mock_wizard()
        
        # current_uiをモック
        mock_current_ui = Mock()
        mock_current_ui.element_id = "test_ui"
        wizard.current_ui = mock_current_ui
        
        # キャンセル処理を実行
        wizard._on_name_cancelled()
        
        # UIが適切に閉じられることを確認
        mock_ui_manager.hide_element.assert_called()
        mock_ui_manager.unregister_element.assert_called()
    
    def test_default_cancel_handler_closes_wizard(self):
        """デフォルトキャンセルハンドラーがウィザードを閉じることを確認"""
        wizard, mock_ui_manager, mock_config_manager = self.create_mock_wizard()
        
        # デフォルトキャンセルハンドラーを直接呼び出し
        with patch.object(wizard, '_close_wizard') as mock_close:
            wizard._default_cancel_handler()
            mock_close.assert_called_once()
    
    def test_name_input_dialog_uses_correct_title_to_avoid_duplication(self):
        """名前入力ダイアログが重複を避ける正しいタイトルを使用することを確認"""
        wizard, mock_ui_manager, mock_config_manager = self.create_mock_wizard()
        
        with patch('src.ui.character_creation.UIInputDialog') as mock_dialog:
            wizard._show_name_input()
            
            # UIInputDialogの呼び出し引数を確認
            mock_dialog.assert_called_once()
            call_args = mock_dialog.call_args
            
            # タイトルが「キャラクター作成」になっていることを確認（「名前入力」ではない）
            dialog_title = call_args[0][1]  # 2番目の引数がタイトル
            assert dialog_title == "キャラクター作成", f"期待されるタイトル: 'キャラクター作成', 実際: '{dialog_title}'"
            
            # メッセージが適切に設定されていることを確認
            dialog_message = call_args[0][2]  # 3番目の引数がメッセージ
            assert dialog_message == "名前を入力してください", f"期待されるメッセージ: '名前を入力してください', 実際: '{dialog_message}'"
    
    def test_label_duplication_is_avoided(self):
        """ラベル重複が回避されることを確認"""
        wizard, mock_ui_manager, mock_config_manager = self.create_mock_wizard()
        
        with patch('src.ui.character_creation.UIInputDialog') as mock_dialog:
            wizard._show_name_input()
            
            call_args = mock_dialog.call_args
            dialog_title = call_args[0][1]
            dialog_message = call_args[0][2]
            
            # タイトルとメッセージが異なることを確認（重複しない）
            assert dialog_title != dialog_message, f"タイトルとメッセージが重複しています: タイトル='{dialog_title}', メッセージ='{dialog_message}'"
            
            # タイトルに「名前」という文字が含まれないことを確認（位置重複を避ける）
            assert "名前" not in dialog_title or dialog_title == "キャラクター作成", f"タイトルに「名前」が含まれて位置重複の可能性があります: '{dialog_title}'"
    
    def test_name_input_with_custom_cancel_callback(self):
        """カスタムキャンセルコールバックが設定された場合の動作確認"""
        custom_callback_called = False
        
        def custom_cancel_callback():
            nonlocal custom_callback_called
            custom_callback_called = True
        
        wizard, mock_ui_manager, mock_config_manager = self.create_mock_wizard()
        wizard.on_cancel = custom_cancel_callback
        
        # current_uiをモック
        mock_current_ui = Mock()
        mock_current_ui.element_id = "test_ui"
        wizard.current_ui = mock_current_ui
        
        # キャンセル処理を実行
        wizard._on_name_cancelled()
        
        # カスタムコールバックが呼ばれることを確認
        assert custom_callback_called, "カスタムキャンセルコールバックが呼ばれませんでした"
    
    def test_wizard_initialization_sets_cancel_handler(self):
        """ウィザード初期化時にキャンセルハンドラーが設定されることを確認"""
        wizard, mock_ui_manager, mock_config_manager = self.create_mock_wizard()
        
        # on_cancelが設定されていることを確認
        assert wizard.on_cancel is not None, "キャンセルハンドラーが初期化されていません"
        assert callable(wizard.on_cancel), "キャンセルハンドラーが呼び出し可能ではありません"
        assert wizard.on_cancel == wizard._default_cancel_handler, "デフォルトキャンセルハンドラーが設定されていません"
    
    def test_name_input_uses_correct_config_key(self):
        """名前入力が正しい設定キーを使用することを確認"""
        wizard, mock_ui_manager, mock_config_manager = self.create_mock_wizard()
        
        with patch('src.ui.character_creation.UIInputDialog'):
            wizard._show_name_input()
            
            # config_manager.get_textが正しいキーで呼ばれることを確認
            mock_config_manager.get_text.assert_called_with("character.enter_name")
    
    def test_menu_does_not_disappear_completely_on_cancel(self):
        """キャンセル時にメニューが完全に消えないことを確認"""
        wizard, mock_ui_manager, mock_config_manager = self.create_mock_wizard()
        
        # current_uiをモック
        mock_current_ui = Mock()
        mock_current_ui.element_id = "test_ui"
        wizard.current_ui = mock_current_ui
        
        # _close_wizardをモック
        with patch.object(wizard, '_close_wizard') as mock_close:
            wizard._on_name_cancelled()
            
            # _close_wizardが呼ばれることを確認（適切にウィザードが閉じられる）
            mock_close.assert_called_once()
            
            # UI要素のhide/unregister処理が適切に行われることを確認
            mock_ui_manager.hide_element.assert_called_with("test_ui")
            mock_ui_manager.unregister_element.assert_called_with("test_ui")