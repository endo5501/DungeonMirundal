"""キャラクター作成の名前変更機能の簡易テスト"""

import pytest
from unittest.mock import Mock, patch
from src.ui.character_creation import CharacterCreationWizard


class TestCharacterNameSimple:
    """キャラクター名前変更機能の簡易テストクラス"""
    
    def test_name_confirmation_with_valid_name(self):
        """有効な名前での確認処理テスト"""
        # モックを使用してウィザードを作成
        with patch('src.ui.character_creation.ui_manager'):
            with patch('src.ui.character_creation.config_manager') as mock_config:
                mock_config.get_text.return_value = "テスト文字列"
                wizard = CharacterCreationWizard()
                
                # _next_stepをモック化
                wizard._next_step = Mock()
                wizard.current_ui = None
                
                test_name = "テストヒーロー"
                
                # 名前確認処理を実行
                wizard._on_name_confirmed(test_name)
                
                # 名前が設定されることを確認
                assert wizard.character_data['name'] == test_name
                
                # 次のステップに進むことを確認
                wizard._next_step.assert_called_once()
    
    def test_name_confirmation_with_empty_name(self):
        """空の名前での確認処理テスト"""
        with patch('src.ui.character_creation.ui_manager'):
            with patch('src.ui.character_creation.config_manager') as mock_config:
                mock_config.get_text.return_value = "テスト文字列"
                wizard = CharacterCreationWizard()
                
                wizard._next_step = Mock()
                wizard.current_ui = None
                
                # 空の名前で確認処理を実行
                wizard._on_name_confirmed("")
                
                # デフォルト名が設定されることを確認
                assert wizard.character_data['name'] == "Hero"
                
                # 次のステップに進むことを確認
                wizard._next_step.assert_called_once()
    
    def test_name_confirmation_with_long_name(self):
        """長すぎる名前での確認処理テスト"""
        with patch('src.ui.character_creation.ui_manager'):
            with patch('src.ui.character_creation.config_manager') as mock_config:
                mock_config.get_text.return_value = "テスト文字列"
                wizard = CharacterCreationWizard()
                
                wizard._next_step = Mock()
                wizard.current_ui = None
                
                long_name = "非常に長いキャラクター名前テストケース" # 20文字以上
                
                # 長い名前で確認処理を実行
                wizard._on_name_confirmed(long_name)
                
                # 20文字に切り詰められることを確認
                assert len(wizard.character_data['name']) <= 20
                assert wizard.character_data['name'] == long_name[:20]
    
    def test_name_confirmation_with_special_characters(self):
        """特殊文字を含む名前での確認処理テスト"""
        with patch('src.ui.character_creation.ui_manager'):
            with patch('src.ui.character_creation.config_manager') as mock_config:
                mock_config.get_text.return_value = "テスト文字列"
                wizard = CharacterCreationWizard()
                
                wizard._next_step = Mock()
                wizard.current_ui = None
                
                dangerous_name = "Hero<script>"
                
                # 特殊文字を含む名前で確認処理を実行
                wizard._on_name_confirmed(dangerous_name)
                
                # デフォルト名に置き換えられることを確認
                assert wizard.character_data['name'] == "Hero"
    
    def test_name_cancellation(self):
        """名前入力キャンセル処理テスト"""
        with patch('src.ui.character_creation.ui_manager') as mock_ui:
            with patch('src.ui.character_creation.config_manager') as mock_config:
                mock_config.get_text.return_value = "テスト文字列"
                wizard = CharacterCreationWizard()
                
                # on_cancelコールバックを設定
                on_cancel_mock = Mock()
                wizard.on_cancel = on_cancel_mock
                
                # 現在のUIを設定
                wizard.current_ui = Mock()
                wizard.current_ui.element_id = "test_dialog"
                
                # キャンセル処理を実行
                wizard._on_name_cancelled()
                
                # キャンセルコールバックが呼ばれることを確認
                on_cancel_mock.assert_called_once()
                
                # UIが適切にクリーンアップされることを確認
                mock_ui.hide_element.assert_called_with("test_dialog")
                mock_ui.unregister_element.assert_called_with("test_dialog")
                assert wizard.current_ui is None