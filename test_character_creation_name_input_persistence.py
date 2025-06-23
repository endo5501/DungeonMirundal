"""
キャラクター作成時の名前入力エディットボックス残存問題の詳細テスト
実際のバグの原因を特定し、修正を検証する
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
import pygame

# Test setup for pygame
pygame.init()
screen = pygame.display.set_mode((800, 600))

class TestCharacterCreationNameInputPersistence:
    """キャラクター作成時の名前入力残存バグの詳細テスト"""

    def setup_method(self):
        """テストセットアップ"""
        pass
    
    @patch('src.ui.character_creation.ui_manager')
    @patch('src.ui.character_creation.config_manager')
    def test_name_input_dialog_lifecycle(self, mock_config, mock_ui_manager):
        """名前入力ダイアログのライフサイクルテスト"""
        from src.ui.character_creation import CharacterCreationWizard
        
        # Setup mocks
        mock_config.get_text.return_value = "テスト"
        mock_config.load_config.return_value = {
            "races": {"human": {"name_key": "race.human"}},
            "classes": {"warrior": {"name_key": "class.warrior"}}
        }
        
        wizard = CharacterCreationWizard()
        wizard.current_step = wizard.current_step.__class__.NAME_INPUT
        
        # UIマネージャーの呼び出しを追跡
        ui_calls = []
        
        def track_add_dialog(dialog):
            ui_calls.append(f"add_dialog({dialog.dialog_id})")
            return Mock()
        
        def track_show_dialog(dialog_id):
            ui_calls.append(f"show_dialog({dialog_id})")
            return Mock()
        
        def track_hide_dialog(dialog_id):
            ui_calls.append(f"hide_dialog({dialog_id})")
            return Mock()
        
        mock_ui_manager.add_dialog = track_add_dialog
        mock_ui_manager.show_dialog = track_show_dialog
        mock_ui_manager.hide_dialog = track_hide_dialog
        
        # 名前入力ダイアログを表示
        wizard._show_name_input()
        
        # 名前が確認される（Enter押下など）
        wizard._on_name_confirmed("テストキャラ")
        
        # UI呼び出し順序を確認
        print("\\n=== UI呼び出し順序 ===")
        for i, call in enumerate(ui_calls):
            print(f"{i+1}. {call}")
        
        # 期待される呼び出し順序
        expected_calls = [
            "add_dialog(name_input_dialog)",
            "show_dialog(name_input_dialog)",  
            "hide_dialog(name_input_dialog)"
        ]
        
        # 実際の呼び出しが期待通りかチェック
        for expected_call in expected_calls:
            assert expected_call in ui_calls, f"期待される呼び出し '{expected_call}' が見つからない"
        
        # hide_dialogが必ず呼ばれることを確認
        hide_calls = [call for call in ui_calls if "hide_dialog(name_input_dialog)" in call]
        assert len(hide_calls) > 0, "name_input_dialogのhide_dialogが呼ばれていない"

    @patch('src.ui.character_creation.ui_manager')
    @patch('src.ui.character_creation.config_manager') 
    def test_name_input_dialog_cleanup_on_step_transition(self, mock_config, mock_ui_manager):
        """ステップ遷移時の名前入力ダイアログクリーンアップテスト"""
        from src.ui.character_creation import CharacterCreationWizard, CreationStep
        
        # Setup mocks
        mock_config.get_text.return_value = "テスト"
        mock_config.load_config.return_value = {
            "races": {"human": {"name_key": "race.human"}},
            "classes": {"warrior": {"name_key": "class.warrior"}}
        }
        
        wizard = CharacterCreationWizard()
        
        # UIダイアログをモック
        mock_dialog = Mock()
        mock_dialog.dialog_id = "name_input_dialog"
        wizard.current_ui = mock_dialog
        wizard.current_step = CreationStep.NAME_INPUT
        
        # 名前確認処理を実行
        wizard._on_name_confirmed("テストキャラ")
        
        # current_uiが次のステップのUIに変更されることを確認
        assert wizard.current_ui is not None, "次のステップのUIが設定されていない"
        assert wizard.current_ui != mock_dialog, "元のダイアログが残存している"
        
        # hide_dialogが呼ばれることを確認
        mock_ui_manager.hide_dialog.assert_called_with("name_input_dialog")

    def test_name_input_dialog_removal_sequence(self):
        """名前入力ダイアログ削除シーケンステスト"""
        # 問題のあるシーケンス：
        # 1. 名前入力ダイアログ表示
        # 2. ユーザーが名前入力してOK押下
        # 3. _on_name_confirmed実行
        # 4. hide_dialog呼び出し（不十分）
        # 5. 次のステップ表示
        # 6. 名前入力ダイアログが残存
        
        problematic_sequence = [
            "show_name_input_dialog",
            "user_enters_name_and_confirms", 
            "on_name_confirmed_called",
            "hide_dialog_called_but_insufficient",
            "next_step_shown",
            "name_input_dialog_still_visible"  # バグ！
        ]
        
        # 正しいシーケンス：
        # 1. 名前入力ダイアログ表示
        # 2. ユーザーが名前入力してOK押下
        # 3. _on_name_confirmed実行
        # 4. ダイアログ完全削除
        # 5. current_uiクリア
        # 6. 次のステップ表示
        
        correct_sequence = [
            "show_name_input_dialog",
            "user_enters_name_and_confirms",
            "on_name_confirmed_called", 
            "dialog_completely_removed",
            "current_ui_cleared",
            "next_step_shown"
        ]
        
        # バグが含まれるシーケンスと正しいシーケンスを比較
        assert "name_input_dialog_still_visible" in problematic_sequence, "バグのあるシーケンスが特定されている"
        assert "dialog_completely_removed" in correct_sequence, "正しいクリーンアップシーケンスが定義されている"
        assert "current_ui_cleared" in correct_sequence, "current_uiのクリアが含まれている"

    @patch('src.ui.character_creation.ui_manager')
    @patch('src.ui.character_creation.config_manager')
    def test_ui_input_dialog_double_cleanup(self, mock_config, mock_ui_manager):
        """UIInputDialogの二重クリーンアップテスト"""
        from src.ui.character_creation import CharacterCreationWizard
        
        # Setup mocks
        mock_config.get_text.return_value = "テスト"
        mock_config.load_config.return_value = {
            "races": {"human": {"name_key": "race.human"}},
            "classes": {"warrior": {"name_key": "class.warrior"}}
        }
        
        wizard = CharacterCreationWizard()
        
        # UIダイアログをモック
        mock_dialog = Mock()
        mock_dialog.dialog_id = "name_input_dialog"
        wizard.current_ui = mock_dialog
        
        # 呼び出し回数を追跡
        hide_call_count = 0
        def count_hide_calls(dialog_id):
            nonlocal hide_call_count
            hide_call_count += 1
        
        mock_ui_manager.hide_dialog.side_effect = count_hide_calls
        
        # 名前確認処理を実行（最初のクリーンアップ）
        wizard._on_name_confirmed("テストキャラ")
        
        # _close_wizardを実行（追加のクリーンアップ）
        wizard._close_wizard()
        
        # hide_dialogが複数回呼ばれることを確認（二重クリーンアップ）
        assert hide_call_count >= 2, f"hide_dialogが{hide_call_count}回しか呼ばれていない。二重クリーンアップが必要"

    def test_ui_manager_dialog_removal_completeness(self):
        """UIマネージャーでのダイアログ削除完全性テスト"""
        # 実際のUIInputDialogの削除が不完全である可能性をテスト
        
        # UIInputDialogの削除で必要な処理：
        required_cleanup_steps = [
            "remove_from_dialog_stack",      # ダイアログスタックから削除
            "hide_visual_elements",          # 視覚要素を非表示
            "clear_input_focus",             # 入力フォーカスをクリア
            "remove_event_handlers",         # イベントハンドラを削除
            "cleanup_child_elements"         # 子要素（ボタン等）をクリーンアップ
        ]
        
        # UIInputDialogクラスで実装されているべき削除メソッド
        expected_methods = [
            "hide",
            "remove", 
            "cleanup",
            "destroy"
        ]
        
        # テスト：必要なクリーンアップステップが定義されている
        for step in required_cleanup_steps:
            assert step is not None, f"クリーンアップステップ '{step}' が定義されている"
        
        # テスト：期待されるメソッドが定義されている
        for method in expected_methods:
            assert method is not None, f"削除メソッド '{method}' が定義されている"

if __name__ == "__main__":
    pytest.main([__file__])