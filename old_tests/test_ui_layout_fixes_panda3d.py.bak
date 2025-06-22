"""UIレイアウト修正テスト"""

import pytest
from unittest.mock import Mock, patch
from src.ui.base_ui import UIInputDialog
from src.overworld.facilities.guild import AdventurersGuild


class TestUILayoutFixes:
    """UIレイアウト修正テスト"""
    
    def test_input_dialog_title_and_message_positions_are_separated(self):
        """UIInputDialogのタイトルとメッセージの位置が分離されていることを確認"""
        with patch('src.ui.base_ui.UIText') as mock_ui_text, \
             patch('src.ui.base_ui.UITextInput'), \
             patch('src.ui.base_ui.DirectFrame'), \
             patch('src.ui.base_ui.DirectButton'):
            
            # UIInputDialogを作成
            dialog = UIInputDialog(
                "test_dialog",
                "テストタイトル",
                "テストメッセージ"
            )
            
            # UITextが2回呼ばれることを確認（タイトルとメッセージ）
            assert mock_ui_text.call_count == 2
            
            # 各呼び出しの位置を確認
            title_call = mock_ui_text.call_args_list[0]
            message_call = mock_ui_text.call_args_list[1]
            
            # タイトルの位置を確認
            title_pos = title_call[1]['pos']  # キーワード引数のpos
            assert title_pos == (0, 0, 0.5), f"タイトル位置が期待値と異なります: {title_pos}"
            
            # メッセージの位置を確認
            message_pos = message_call[1]['pos']
            assert message_pos == (0, 0, -0.2), f"メッセージ位置が期待値と異なります: {message_pos}"
            
            # 位置が十分に離れていることを確認（Z軸で0.7の差）
            z_difference = abs(title_pos[2] - message_pos[2])
            assert z_difference >= 0.7, f"タイトルとメッセージの位置が近すぎます: {z_difference}"
    
    def test_title_position_is_higher_than_message(self):
        """タイトルがメッセージより上に配置されていることを確認"""
        with patch('src.ui.base_ui.UIText') as mock_ui_text, \
             patch('src.ui.base_ui.UITextInput'), \
             patch('src.ui.base_ui.DirectFrame'), \
             patch('src.ui.base_ui.DirectButton'):
            
            dialog = UIInputDialog(
                "test_dialog",
                "テストタイトル", 
                "テストメッセージ"
            )
            
            title_call = mock_ui_text.call_args_list[0]
            message_call = mock_ui_text.call_args_list[1]
            
            title_z = title_call[1]['pos'][2]
            message_z = message_call[1]['pos'][2]
            
            # タイトルのZ値がメッセージより大きい（上にある）ことを確認
            assert title_z > message_z, f"タイトル({title_z})がメッセージ({message_z})より上にありません"
    
    def test_guild_sets_cancel_callback_for_character_creation(self):
        """ギルドがキャラクター作成でキャンセルコールバックを設定することを確認"""
        with patch.object(AdventurersGuild, '__init__', return_value=None):
            guild = AdventurersGuild()
            guild.main_menu = Mock()
            guild.main_menu.element_id = "guild_main_menu"
            
            with patch('src.overworld.facilities.guild.CharacterCreationWizard') as mock_wizard_class, \
                 patch('src.overworld.facilities.guild.ui_manager') as mock_ui_manager:
                
                mock_wizard = Mock()
                mock_wizard_class.return_value = mock_wizard
                
                # キャラクター作成を呼び出し
                guild._show_character_creation()
                
                # ウィザードが作成されることを確認
                mock_wizard_class.assert_called_once()
                
                # on_cancelコールバックが設定されることを確認
                assert hasattr(mock_wizard, 'on_cancel')
                assert mock_wizard.on_cancel == guild._on_character_creation_cancelled
                
                # startが呼ばれることを確認
                mock_wizard.start.assert_called_once()
    
    def test_guild_cancel_callback_restores_main_menu(self):
        """ギルドのキャンセルコールバックがメインメニューを復元することを確認"""
        with patch.object(AdventurersGuild, '__init__', return_value=None):
            guild = AdventurersGuild()
            guild.main_menu = Mock()
            guild.main_menu.element_id = "guild_main_menu"
            
            with patch('src.overworld.facilities.guild.ui_manager') as mock_ui_manager:
                
                # キャンセルコールバックを呼び出し
                guild._on_character_creation_cancelled()
                
                # メインメニューが表示されることを確認
                mock_ui_manager.show_element.assert_called_once_with("guild_main_menu")
    
    def test_guild_cancel_callback_handles_no_main_menu(self):
        """ギルドのキャンセルコールバックがメインメニューなしでもクラッシュしないことを確認"""
        with patch.object(AdventurersGuild, '__init__', return_value=None):
            guild = AdventurersGuild()
            guild.main_menu = None
            
            with patch('src.overworld.facilities.guild.ui_manager'):
                
                # メインメニューがNoneでもクラッシュしないことを確認
                try:
                    guild._on_character_creation_cancelled()
                    test_passed = True
                except Exception as e:
                    test_passed = False
                    pytest.fail(f"メインメニューがNoneの場合にクラッシュしました: {e}")
                
                assert test_passed
    
    def test_character_creation_wizard_default_cancel_handler_exists(self):
        """CharacterCreationWizardにデフォルトキャンセルハンドラーが存在することを確認"""
        from src.ui.character_creation import CharacterCreationWizard
        
        # メソッドが存在することを確認
        assert hasattr(CharacterCreationWizard, '_default_cancel_handler')
        assert callable(getattr(CharacterCreationWizard, '_default_cancel_handler'))
    
    def test_input_dialog_layout_prevents_overlap(self):
        """UIInputDialogのレイアウトがオーバーラップを防ぐことを確認"""
        with patch('src.ui.base_ui.UIText') as mock_ui_text, \
             patch('src.ui.base_ui.UITextInput') as mock_text_input, \
             patch('src.ui.base_ui.DirectFrame'), \
             patch('src.ui.base_ui.DirectButton') as mock_button:
            
            dialog = UIInputDialog(
                "test_dialog",
                "テストタイトル",
                "テストメッセージ"
            )
            
            # 各要素の位置を取得
            title_pos = mock_ui_text.call_args_list[0][1]['pos']  # (0, 0, 0.5)
            message_pos = mock_ui_text.call_args_list[1][1]['pos']  # (0, 0, -0.2)
            text_input_pos = mock_text_input.call_args[1]['pos']  # (0, 0, -0.1)
            
            # ボタンの位置も確認
            ok_button_pos = mock_button.call_args_list[0][1]['pos']  # (-0.3, 0, -0.4)
            cancel_button_pos = mock_button.call_args_list[1][1]['pos']  # (0.3, 0, -0.4)
            
            # すべての要素が異なるZ座標を持つことを確認
            z_positions = [
                title_pos[2],      # 0.5
                text_input_pos[2], # -0.1
                message_pos[2],    # -0.2
                ok_button_pos[2],  # -0.4
                cancel_button_pos[2] # -0.4
            ]
            
            # タイトル、テキスト入力、メッセージが適切に分離されていることを確認
            assert title_pos[2] > text_input_pos[2] > message_pos[2], \
                f"要素の垂直配置が正しくありません: title={title_pos[2]}, input={text_input_pos[2]}, message={message_pos[2]}"
            
            # 隣接する要素間で最低限の間隔があることを確認
            title_input_gap = title_pos[2] - text_input_pos[2]  # 0.6
            input_message_gap = text_input_pos[2] - message_pos[2]  # 0.1
            
            assert title_input_gap >= 0.5, f"タイトルとテキスト入力の間隔が狭すぎます: {title_input_gap}"
            assert input_message_gap >= 0.1, f"テキスト入力とメッセージの間隔が狭すぎます: {input_message_gap}"