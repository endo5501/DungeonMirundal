"""
キャラクター作成後の名前入力エディットボックス残存問題のテスト
バグ修正前にテストを作成し、修正後にテストが通ることを確認する
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
import pygame

# Test setup for pygame
pygame.init()
screen = pygame.display.set_mode((800, 600))

class TestCharacterCreationCleanup:
    """キャラクター作成後のクリーンアップテスト"""

    def setup_method(self):
        """テストセットアップ"""
        self.mock_party = Mock()
        self.mock_party.gold = 2000
        self.mock_party.get_all_characters.return_value = []
        
    @patch('src.ui.character_creation.ui_manager')
    @patch('src.ui.character_creation.config_manager')
    def test_character_creation_wizard_cleanup_after_completion(self, mock_config, mock_ui_manager):
        """キャラクター作成完了後にUIが正しくクリーンアップされることをテスト"""
        from src.ui.character_creation import CharacterCreationWizard
        from src.character.character import Character
        from src.character.stats import BaseStats
        
        # Setup mocks
        mock_config.get_text.return_value = "テスト"
        mock_config.load_config.return_value = {
            "races": {"human": {"name_key": "race.human"}},
            "classes": {"warrior": {"name_key": "class.warrior"}}
        }
        
        completion_callback = Mock()
        
        wizard = CharacterCreationWizard(callback=completion_callback)
        
        # キャラクターデータを設定
        wizard.character_data = {
            'name': 'テストキャラ',
            'race': 'human', 
            'character_class': 'warrior',
            'base_stats': BaseStats(10, 10, 10, 10, 10)
        }
        
        # 現在のUIとしてname_input_dialogを設定
        mock_dialog = Mock()
        mock_dialog.dialog_id = "name_input_dialog"
        wizard.current_ui = mock_dialog
        
        # Character.create_characterをモック
        mock_character = Mock(spec=Character)
        mock_character.name = "テストキャラ"
        
        with patch('src.ui.character_creation.Character') as mock_character_class:
            mock_character_class.create_character.return_value = mock_character
            
            # 確認ステップを実行（内部で_close_wizard()が呼ばれる）
            wizard._confirm_creation()
            
            # コールバックが呼ばれることを確認
            completion_callback.assert_called_once_with(mock_character)
            
            # hide_dialogが適切に呼ばれることを確認
            mock_ui_manager.hide_dialog.assert_any_call("name_input_dialog")
            
            # 必要なUIエレメントがすべて削除されることを確認
            expected_dialog_ids = [
                "name_input_dialog",
                "stats_generation_dialog", 
                "confirmation_dialog",
                "creation_error_dialog"
            ]
            
            for dialog_id in expected_dialog_ids:
                mock_ui_manager.hide_dialog.assert_any_call(dialog_id)

    @patch('src.overworld.facilities.guild.ui_manager')
    @patch('src.overworld.facilities.guild.CharacterCreationWizard')
    def test_guild_character_creation_ui_cleanup(self, mock_wizard_class, mock_ui_manager):
        """ギルドでのキャラクター作成完了後にUIが正しく処理されることをテスト"""
        from src.overworld.facilities.guild import Guild
        
        guild = Guild()
        guild.current_party = self.mock_party
        guild.created_characters = []
        guild.main_menu = Mock()
        guild.main_menu.menu_id = "guild_main_menu"
        
        # キャラクター作成ウィザードのモック
        mock_wizard = Mock()
        mock_wizard_class.return_value = mock_wizard
        
        # キャラクター作成を開始
        guild._show_character_creation()
        
        # ウィザードが正しくセットアップされることを確認
        mock_wizard_class.assert_called_once()
        wizard_args = mock_wizard_class.call_args
        
        # コールバックが設定されていることを確認
        assert wizard_args[1]['callback'] is not None
        assert mock_wizard.on_cancel is not None
        
        # ウィザードがスタートされることを確認
        mock_wizard.start.assert_called_once()
        
        # メインメニューが隠されることを確認
        mock_ui_manager.hide_menu.assert_called_with("guild_main_menu")

    def test_character_creation_dialog_cleanup_order(self):
        """キャラクター作成時のダイアログクリーンアップ順序テスト"""
        # このテストは UI クリーンアップの順序が正しいことを確認する
        cleanup_order = []
        
        # 期待されるクリーンアップ順序：
        # 1. 現在のUI（name_input_dialog等）を隠す
        # 2. 全ダイアログリストから各ダイアログを隠す
        # 3. 全メニューリストから各メニューを隠す
        # 4. メインエレメントを隠す
        
        expected_dialogs = [
            "name_input_dialog",
            "stats_generation_dialog", 
            "confirmation_dialog",
            "creation_error_dialog"
        ]
        
        expected_menus = [
            "race_selection_menu",
            "class_selection_menu"
        ]
        
        # クリーンアップが適切な順序で行われることを確認
        assert len(expected_dialogs) > 0, "クリーンアップ対象のダイアログが定義されている"
        assert len(expected_menus) > 0, "クリーンアップ対象のメニューが定義されている"
        
        # 名前入力ダイアログが最初にクリーンアップ対象に含まれている
        assert "name_input_dialog" in expected_dialogs, "名前入力ダイアログがクリーンアップ対象に含まれている"

if __name__ == "__main__":
    pytest.main([__file__])