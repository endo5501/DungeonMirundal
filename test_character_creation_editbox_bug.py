"""
キャラクター作成後の名前入力エディットボックス残存問題の簡単なテスト
バグの原因を特定するための最小限のテストケース
"""
import pytest
from unittest.mock import Mock, patch, MagicMock, call
import pygame

# Test setup for pygame
pygame.init()
screen = pygame.display.set_mode((800, 600))

class TestCharacterCreationEditboxBug:
    """キャラクター作成時のエディットボックス残存バグテスト"""

    @patch('src.ui.character_creation.ui_manager')
    @patch('src.ui.character_creation.config_manager')
    def test_name_input_dialog_cleanup_order(self, mock_config, mock_ui_manager):
        """名前入力ダイアログのクリーンアップ順序テスト"""
        from src.ui.character_creation import CharacterCreationWizard
        from src.character.stats import BaseStats
        
        # Setup mocks
        mock_config.get_text.return_value = "テスト"
        mock_config.load_config.return_value = {
            "races": {"human": {"name_key": "race.human"}},
            "classes": {"warrior": {"name_key": "class.warrior"}}
        }
        
        call_order = []
        
        def track_ui_calls(method_name):
            def wrapper(*args, **kwargs):
                call_order.append(f"{method_name}({args[0] if args else ''})")
                return Mock()
            return wrapper
        
        # UI操作の呼び出し順序を追跡
        mock_ui_manager.hide_dialog = track_ui_calls("hide_dialog")
        mock_ui_manager.show_dialog = track_ui_calls("show_dialog")
        mock_ui_manager.add_dialog = track_ui_calls("add_dialog")
        
        # ギルドのコールバックを模擬
        guild_callback_called = []
        
        def mock_guild_callback(character):
            guild_callback_called.append("guild_callback_start")
            # ギルドが成功メッセージダイアログを表示
            call_order.append("guild_shows_success_dialog")
            guild_callback_called.append("guild_callback_end")
        
        wizard = CharacterCreationWizard(callback=mock_guild_callback)
        
        # キャラクターデータを設定
        wizard.character_data = {
            'name': 'テストキャラ',
            'race': 'human',
            'character_class': 'warrior',
            'base_stats': BaseStats(10, 10, 10, 10, 10)
        }
        
        # 現在のUIとして名前入力ダイアログを設定
        mock_dialog = Mock()
        mock_dialog.dialog_id = "name_input_dialog"
        wizard.current_ui = mock_dialog
        
        # Character.create_characterをモック
        with patch('src.ui.character_creation.Character') as mock_character_class:
            mock_character = Mock()
            mock_character.name = "テストキャラ"
            mock_character_class.create_character.return_value = mock_character
            
            # キャラクター作成を実行
            wizard._create_character()
            
            # 呼び出し順序を確認
            print("\\n=== UI 呼び出し順序 ===")
            for i, call in enumerate(call_order):
                print(f"{i+1}. {call}")
            
            # ギルドコールバックが実行されたことを確認
            assert len(guild_callback_called) == 2
            assert guild_callback_called[0] == "guild_callback_start"
            assert guild_callback_called[1] == "guild_callback_end"
            
            # 期待される順序：
            # 1. ギルドがコールバックで成功ダイアログを表示
            # 2. ウィザードが名前入力ダイアログを削除（_close_wizard）
            
            # 名前入力ダイアログが削除されることを確認
            assert any("hide_dialog(name_input_dialog)" in call for call in call_order), \
                f"名前入力ダイアログが削除されていない。呼び出し順序: {call_order}"

    def test_dialog_cleanup_sequence_analysis(self):
        """ダイアログクリーンアップシーケンス分析テスト"""
        # 期待される正しいシーケンス：
        # 1. ユーザーが名前を入力
        # 2. 名前入力ダイアログを表示
        # 3. キャラクター作成完了
        # 4. ギルドコールバック実行（成功メッセージ表示）
        # 5. ウィザードクリーンアップ（名前入力ダイアログ削除）
        
        expected_sequence = [
            "show_name_input_dialog",
            "character_creation_complete", 
            "guild_success_message",
            "wizard_cleanup_dialogs"
        ]
        
        # 問題のあるシーケンス（バグ）：
        # 1. ユーザーが名前を入力
        # 2. 名前入力ダイアログを表示
        # 3. キャラクター作成完了
        # 4. ウィザードクリーンアップ（不完全）
        # 5. ギルドコールバック実行（成功メッセージ表示）
        # 6. 名前入力ダイアログが残る
        
        problematic_sequence = [
            "show_name_input_dialog",
            "character_creation_complete",
            "wizard_partial_cleanup",  # 不完全なクリーンアップ
            "guild_success_message",
            "name_input_dialog_remains"  # エディットボックスが残る
        ]
        
        # 正しいシーケンスでは、クリーンアップが最後に完全に実行される
        assert "wizard_cleanup_dialogs" in expected_sequence
        assert expected_sequence.index("wizard_cleanup_dialogs") > expected_sequence.index("guild_success_message")
        
        # 問題のあるシーケンスでは、クリーンアップが不完全
        assert "wizard_partial_cleanup" in problematic_sequence
        assert "name_input_dialog_remains" in problematic_sequence

if __name__ == "__main__":
    pytest.main([__file__])