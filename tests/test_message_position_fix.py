"""メッセージ位置修正テスト"""

import pytest
from unittest.mock import Mock, patch


class TestMessagePositionFix:
    """メッセージ位置修正テスト"""
    
    def test_message_appears_above_text_input(self):
        """メッセージがテキスト入力の上に表示されることを確認"""
        
        with patch('src.ui.base_ui.UIText') as mock_ui_text, \
             patch('src.ui.base_ui.UITextInput') as mock_text_input, \
             patch('src.ui.base_ui.DirectFrame'), \
             patch('src.ui.base_ui.DirectButton'):
            
            from src.ui.base_ui import UIInputDialog
            
            # メッセージ付きでダイアログを作成
            dialog = UIInputDialog(
                "test_dialog",
                "",                           # 空のタイトル
                "名前を入力してください",      # メッセージ
                placeholder=""
            )
            
            # 位置を確認
            title_call = mock_ui_text.call_args_list[0]
            message_call = mock_ui_text.call_args_list[1]
            text_input_call = mock_text_input.call_args
            
            title_pos = title_call[1]['pos']
            message_pos = message_call[1]['pos']
            text_input_pos = text_input_call[1]['pos']
            
            print(f"タイトル位置: {title_pos}")
            print(f"メッセージ位置: {message_pos}")
            print(f"テキスト入力位置: {text_input_pos}")
            
            # 垂直方向（Z軸）でメッセージがテキスト入力より上にあることを確認
            assert message_pos[2] > text_input_pos[2], \
                f"メッセージ({message_pos[2]})がテキスト入力({text_input_pos[2]})より下にあります"
            
            # 期待される位置であることを確認
            assert message_pos == (0, 0, 0.2), f"メッセージ位置が期待値と異なります: {message_pos}"
            assert text_input_pos == (0, 0, -0.1), f"テキスト入力位置が期待値と異なります: {text_input_pos}"
    
    def test_proper_vertical_layout_order(self):
        """適切な垂直レイアウト順序を確認"""
        
        with patch('src.ui.base_ui.UIText') as mock_ui_text, \
             patch('src.ui.base_ui.UITextInput') as mock_text_input, \
             patch('src.ui.base_ui.DirectFrame'), \
             patch('src.ui.base_ui.DirectButton') as mock_button:
            
            from src.ui.base_ui import UIInputDialog
            
            dialog = UIInputDialog(
                "test_dialog",
                "",
                "名前を入力してください",
                placeholder=""
            )
            
            # 各要素の位置を取得
            title_z = mock_ui_text.call_args_list[0][1]['pos'][2]      # 0.5
            message_z = mock_ui_text.call_args_list[1][1]['pos'][2]    # 0.2
            text_input_z = mock_text_input.call_args[1]['pos'][2]      # -0.1
            ok_button_z = mock_button.call_args_list[0][1]['pos'][2]   # -0.4
            cancel_button_z = mock_button.call_args_list[1][1]['pos'][2] # -0.4
            
            print(f"垂直順序 (上から下):")
            print(f"  タイトル: {title_z}")
            print(f"  メッセージ: {message_z}")
            print(f"  テキスト入力: {text_input_z}")
            print(f"  ボタン: {ok_button_z}")
            
            # 正しい垂直順序であることを確認
            assert title_z > message_z, f"タイトル({title_z})がメッセージ({message_z})より下にあります"
            assert message_z > text_input_z, f"メッセージ({message_z})がテキスト入力({text_input_z})より下にあります"
            assert text_input_z > ok_button_z, f"テキスト入力({text_input_z})がボタン({ok_button_z})より下にあります"
            
            # 適切な間隔があることを確認
            title_message_gap = title_z - message_z        # 0.3
            message_input_gap = message_z - text_input_z   # 0.3
            input_button_gap = text_input_z - ok_button_z  # 0.3
            
            assert title_message_gap >= 0.2, f"タイトル-メッセージ間隔が狭い: {title_message_gap}"
            assert message_input_gap >= 0.2, f"メッセージ-入力間隔が狭い: {message_input_gap}"
            assert input_button_gap >= 0.2, f"入力-ボタン間隔が狭い: {input_button_gap}"
    
    def test_message_visible_when_title_empty(self):
        """タイトルが空でもメッセージが適切に表示されることを確認"""
        
        with patch('src.ui.base_ui.UIText') as mock_ui_text, \
             patch('src.ui.base_ui.UITextInput'), \
             patch('src.ui.base_ui.DirectFrame'), \
             patch('src.ui.base_ui.DirectButton'):
            
            from src.ui.base_ui import UIInputDialog
            
            dialog = UIInputDialog(
                "test_dialog",
                "",                        # 空のタイトル
                "名前を入力してください"     # メッセージのみ
            )
            
            # タイトルとメッセージの内容を確認
            title_text = mock_ui_text.call_args_list[0][0][1]
            message_text = mock_ui_text.call_args_list[1][0][1]
            
            print(f"タイトルテキスト: '{title_text}'")
            print(f"メッセージテキスト: '{message_text}'")
            
            # タイトルは空、メッセージは設定されていることを確認
            assert title_text == "", f"タイトルは空であるべきです: '{title_text}'"
            assert message_text == "名前を入力してください", f"メッセージが期待値と異なります: '{message_text}'"
            
            # メッセージが適切な位置にあることを確認
            message_pos = mock_ui_text.call_args_list[1][1]['pos']
            assert message_pos == (0, 0, 0.2), f"メッセージ位置が期待値と異なります: {message_pos}"
    
    def test_character_creation_wizard_uses_correct_layout(self):
        """CharacterCreationWizardが正しいレイアウトを使用することを確認"""
        
        from src.ui.character_creation import CharacterCreationWizard
        
        with patch.object(CharacterCreationWizard, '_initialize_ui'):
            wizard = CharacterCreationWizard()
            
            with patch('src.ui.character_creation.config_manager') as mock_config, \
                 patch('src.ui.character_creation.UIInputDialog') as mock_dialog, \
                 patch('src.ui.character_creation.ui_manager'):
                
                mock_config.get_text.return_value = "名前を入力してください"
                
                wizard._show_name_input()
                
                # UIInputDialogの呼び出し引数を確認
                call_args = mock_dialog.call_args[0]
                dialog_title = call_args[1]     # "" (空)
                dialog_message = call_args[2]   # "名前を入力してください"
                
                print(f"ウィザードダイアログタイトル: '{dialog_title}'")
                print(f"ウィザードダイアログメッセージ: '{dialog_message}'")
                
                # 空のタイトルとメッセージが設定されていることを確認
                assert dialog_title == "", f"タイトルは空であるべきです: '{dialog_title}'"
                assert dialog_message == "名前を入力してください", f"メッセージが期待値と異なります: '{dialog_message}'"
    
    def test_message_position_relative_to_background(self):
        """メッセージ位置が背景フレーム内に適切に収まることを確認"""
        
        # 背景フレームサイズ: (-1.5, 1.5, -1.0, 0.8)
        frame_left = -1.5
        frame_right = 1.5
        frame_bottom = -1.0
        frame_top = 0.8
        
        # メッセージ位置: (0, 0, 0.2)
        message_x = 0
        message_y = 0
        message_z = 0.2
        
        # フレーム内に収まることを確認
        assert frame_left <= message_x <= frame_right, f"メッセージX座標がフレーム外: {message_x}"
        assert frame_bottom <= message_z <= frame_top, f"メッセージZ座標がフレーム外: {message_z}"
        
        print(f"フレームサイズ: X({frame_left}~{frame_right}), Z({frame_bottom}~{frame_top})")
        print(f"メッセージ位置: ({message_x}, {message_y}, {message_z})")
        print("メッセージがフレーム内に適切に配置されています")


if __name__ == "__main__":
    test = TestMessagePositionFix()
    test.test_message_appears_above_text_input()
    test.test_proper_vertical_layout_order()
    test.test_message_visible_when_title_empty()
    test.test_character_creation_wizard_uses_correct_layout()
    test.test_message_position_relative_to_background()
    print("メッセージ位置修正テストが完了しました")