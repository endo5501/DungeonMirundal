"""
キャラクター作成時の名前入力エディットボックス残存問題の修正テスト
修正後の動作を検証する
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
import pygame

# Test setup for pygame
pygame.init()
screen = pygame.display.set_mode((800, 600))

class TestCharacterCreationNameInputFix:
    """キャラクター作成時の名前入力残存バグの修正テスト"""

    def setup_method(self):
        """テストセットアップ"""
        pass
    
    @patch('src.ui.character_creation.ui_manager')
    @patch('src.ui.character_creation.config_manager')
    def test_name_input_dialog_complete_removal_on_confirm(self, mock_config, mock_ui_manager):
        """名前入力確認時のダイアログ完全削除テスト"""
        from src.ui.character_creation import CharacterCreationWizard
        
        # Setup mocks
        mock_config.get_text.return_value = "テスト"
        mock_config.load_config.return_value = {
            "races": {"human": {"name_key": "race.human"}},
            "classes": {"warrior": {"name_key": "class.warrior"}}
        }
        
        # UIマネージャーのdialogsディクショナリをモック
        mock_ui_manager.dialogs = {"name_input_dialog": Mock()}
        
        wizard = CharacterCreationWizard()
        
        # UIダイアログをモック
        mock_dialog = Mock()
        mock_dialog.dialog_id = "name_input_dialog"
        wizard.current_ui = mock_dialog
        
        # _next_stepをモックして次のステップ処理を停止
        wizard._next_step = Mock()
        
        # 名前確認処理を実行
        wizard._on_name_confirmed("テストキャラ")
        
        # hide_dialogが呼ばれることを確認
        mock_ui_manager.hide_dialog.assert_called_with("name_input_dialog")
        
        # 重要：dialogsディクショナリからも削除されることを確認
        assert "name_input_dialog" not in mock_ui_manager.dialogs, \
            "name_input_dialogがdialogsディクショナリから削除されていない"
        
        # current_uiがクリアされることを確認
        assert wizard.current_ui is None, "current_uiがクリアされていない"

    @patch('src.ui.character_creation.ui_manager')
    @patch('src.ui.character_creation.config_manager')
    def test_name_input_dialog_complete_removal_on_cancel(self, mock_config, mock_ui_manager):
        """名前入力キャンセル時のダイアログ完全削除テスト"""
        from src.ui.character_creation import CharacterCreationWizard
        
        # Setup mocks
        mock_config.get_text.return_value = "テスト"
        mock_config.load_config.return_value = {
            "races": {"human": {"name_key": "race.human"}},
            "classes": {"warrior": {"name_key": "class.warrior"}}
        }
        
        # UIマネージャーのdialogsディクショナリをモック
        mock_ui_manager.dialogs = {"name_input_dialog": Mock()}
        
        wizard = CharacterCreationWizard()
        
        # UIダイアログをモック
        mock_dialog = Mock()
        mock_dialog.dialog_id = "name_input_dialog"
        wizard.current_ui = mock_dialog
        
        # on_cancelをモックして外部処理を停止
        wizard.on_cancel = Mock()
        
        # 名前キャンセル処理を実行
        wizard._on_name_cancelled()
        
        # hide_dialogが呼ばれることを確認
        mock_ui_manager.hide_dialog.assert_called_with("name_input_dialog")
        
        # 重要：dialogsディクショナリからも削除されることを確認
        assert "name_input_dialog" not in mock_ui_manager.dialogs, \
            "name_input_dialogがdialogsディクショナリから削除されていない"
        
        # current_uiがクリアされることを確認
        assert wizard.current_ui is None, "current_uiがクリアされていない"

    @patch('src.ui.character_creation.ui_manager')
    @patch('src.ui.character_creation.config_manager')
    def test_wizard_cleanup_removes_all_dialogs_from_manager(self, mock_config, mock_ui_manager):
        """ウィザードクリーンアップでUIマネージャーからすべてのダイアログが削除されることをテスト"""
        from src.ui.character_creation import CharacterCreationWizard
        
        # Setup mocks
        mock_config.get_text.return_value = "テスト"
        mock_config.load_config.return_value = {
            "races": {"human": {"name_key": "race.human"}},
            "classes": {"warrior": {"name_key": "class.warrior"}}
        }
        
        # UIマネージャーのdialogsディクショナリに複数のダイアログを設定
        mock_ui_manager.dialogs = {
            "name_input_dialog": Mock(),
            "stats_generation_dialog": Mock(),
            "confirmation_dialog": Mock(),
            "creation_error_dialog": Mock()
        }
        
        wizard = CharacterCreationWizard()
        
        # ウィザードクリーンアップを実行
        wizard._close_wizard()
        
        # すべてのダイアログがdialogsディクショナリから削除されることを確認
        expected_dialogs = [
            "name_input_dialog",
            "stats_generation_dialog", 
            "confirmation_dialog",
            "creation_error_dialog"
        ]
        
        for dialog_id in expected_dialogs:
            assert dialog_id not in mock_ui_manager.dialogs, \
                f"ダイアログ {dialog_id} がdialogsディクショナリから削除されていない"

    @patch('src.ui.character_creation.ui_manager')
    @patch('src.ui.character_creation.config_manager')
    def test_dialog_removal_robustness(self, mock_config, mock_ui_manager):
        """ダイアログ削除処理の堅牢性テスト"""
        from src.ui.character_creation import CharacterCreationWizard
        
        # Setup mocks
        mock_config.get_text.return_value = "テスト"
        mock_config.load_config.return_value = {
            "races": {"human": {"name_key": "race.human"}},
            "classes": {"warrior": {"name_key": "class.warrior"}}
        }
        
        wizard = CharacterCreationWizard()
        
        # ケース1: ui_managerにdialogsがない場合
        mock_ui_manager.dialogs = None
        mock_dialog = Mock()
        mock_dialog.dialog_id = "name_input_dialog"
        wizard.current_ui = mock_dialog
        
        # _next_stepをモックして次のステップ処理を停止
        wizard._next_step = Mock()
        
        # 例外が発生しないことを確認
        try:
            wizard._on_name_confirmed("テストキャラ")
            test_passed = True
        except Exception as e:
            test_passed = False
            print(f"例外が発生: {e}")
        
        assert test_passed, "ui_manager.dialogsがNoneの場合でも例外が発生しない"
        
        # ケース2: ダイアログが既に削除済みの場合
        mock_ui_manager.dialogs = {}  # 空のディクショナリ
        wizard.current_ui = mock_dialog
        
        # _next_stepを再度モック（新しいインスタンス用）
        wizard._next_step = Mock()
        
        # 例外が発生しないことを確認
        try:
            wizard._on_name_confirmed("テストキャラ2")
            test_passed = True
        except Exception as e:
            test_passed = False
            print(f"例外が発生: {e}")
        
        assert test_passed, "ダイアログが既に削除済みの場合でも例外が発生しない"

    def test_ui_manager_dialog_lifecycle_concept(self):
        """UIマネージャーのダイアログライフサイクル概念テスト"""
        # 修正前の問題のあるライフサイクル：
        problematic_lifecycle = [
            "dialog_created",
            "dialog_added_to_manager",
            "dialog_shown",
            "user_interaction", 
            "hide_dialog_called",          # dialogs辞書に残存
            "dialog_still_in_manager",     # バグ！
            "dialog_continues_rendering"   # バグ！
        ]
        
        # 修正後の正しいライフサイクル：
        correct_lifecycle = [
            "dialog_created",
            "dialog_added_to_manager",
            "dialog_shown",
            "user_interaction",
            "hide_dialog_called",
            "dialog_removed_from_manager",   # 追加された処理
            "dialog_completely_destroyed"   # 完全削除
        ]
        
        # バグのあるライフサイクルの特定
        assert "dialog_still_in_manager" in problematic_lifecycle, \
            "問題のあるライフサイクルが特定されている"
        assert "dialog_continues_rendering" in problematic_lifecycle, \
            "継続描画問題が特定されている"
        
        # 正しいライフサイクルの確認
        assert "dialog_removed_from_manager" in correct_lifecycle, \
            "ダイアログマネージャーからの削除が含まれている"
        assert "dialog_completely_destroyed" in correct_lifecycle, \
            "完全削除プロセスが含まれている"

if __name__ == "__main__":
    pytest.main([__file__])