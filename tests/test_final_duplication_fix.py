"""最終的な重複修正テスト"""

import pytest
from unittest.mock import Mock, patch
from src.ui.character_creation import CharacterCreationWizard


class TestFinalDuplicationFix:
    """最終的な重複修正テスト"""
    
    def test_name_input_dialog_has_no_duplicate_text(self):
        """名前入力ダイアログに重複テキストがないことを確認"""
        
        with patch.object(CharacterCreationWizard, '_initialize_ui'):
            wizard = CharacterCreationWizard()
            
            with patch('src.ui.character_creation.config_manager') as mock_config, \
                 patch('src.ui.character_creation.UIInputDialog') as mock_dialog, \
                 patch('src.ui.character_creation.ui_manager'):
                
                mock_config.get_text.return_value = "名前を入力してください"
                
                wizard._show_name_input()
                
                # UIInputDialogの呼び出し引数を確認
                call_args = mock_dialog.call_args[0]
                dialog_id = call_args[0]        # "name_input_dialog"
                dialog_title = call_args[1]     # "キャラクター作成"
                dialog_message = call_args[2]   # "" (空文字)
                
                # キーワード引数も確認
                kwargs = mock_dialog.call_args[1]
                placeholder = kwargs.get('placeholder', '')
                
                print(f"ダイアログタイトル: '{dialog_title}'")
                print(f"ダイアログメッセージ: '{dialog_message}'")
                print(f"プレースホルダー: '{placeholder}'")
                
                # タイトルのみが設定され、メッセージとプレースホルダーが空であることを確認
                assert dialog_title == "キャラクター作成", f"期待されるタイトル: 'キャラクター作成', 実際: '{dialog_title}'"
                assert dialog_message == "", f"メッセージは空であるべきです: '{dialog_message}'"
                assert placeholder == "", f"プレースホルダーは空であるべきです: '{placeholder}'"
                
                # 重複の可能性があるテキストが含まれていないことを確認
                all_text_elements = [dialog_title, dialog_message, placeholder]
                non_empty_texts = [text for text in all_text_elements if text]
                
                assert len(non_empty_texts) == 1, f"表示されるテキストは1つだけであるべきです: {non_empty_texts}"
                assert non_empty_texts[0] == "キャラクター作成", f"表示されるテキストは'キャラクター作成'のみであるべきです: {non_empty_texts}"
    
    def test_ui_input_dialog_with_empty_message_and_placeholder(self):
        """空のメッセージとプレースホルダーでUIInputDialogが正常動作することを確認"""
        
        with patch('src.ui.base_ui.UIText') as mock_ui_text, \
             patch('src.ui.base_ui.UITextInput') as mock_text_input, \
             patch('src.ui.base_ui.DirectFrame'), \
             patch('src.ui.base_ui.DirectButton'):
            
            from src.ui.base_ui import UIInputDialog
            
            # 空のメッセージとプレースホルダーでダイアログを作成
            dialog = UIInputDialog(
                "test_dialog",
                "キャラクター作成",  # タイトルのみ
                "",                  # 空のメッセージ
                placeholder=""       # 空のプレースホルダー
            )
            
            # UITextが2回呼ばれることを確認（タイトルと空のメッセージ）
            assert mock_ui_text.call_count == 2, f"UITextの呼び出し回数が異常です: {mock_ui_text.call_count}"
            
            # タイトルとメッセージの呼び出し内容を確認
            title_call = mock_ui_text.call_args_list[0]
            message_call = mock_ui_text.call_args_list[1]
            
            title_text = title_call[0][1]      # タイトルテキスト
            message_text = message_call[0][1]  # メッセージテキスト（空）
            
            print(f"タイトルテキスト: '{title_text}'")
            print(f"メッセージテキスト: '{message_text}'")
            
            # タイトルは設定され、メッセージは空であることを確認
            assert title_text == "キャラクター作成", f"タイトルが期待値と異なります: '{title_text}'"
            assert message_text == "", f"メッセージは空であるべきです: '{message_text}'"
            
            # UITextInputも空のプレースホルダーで呼ばれることを確認
            text_input_kwargs = mock_text_input.call_args[1]
            input_placeholder = text_input_kwargs.get('placeholder', '')
            
            print(f"テキスト入力プレースホルダー: '{input_placeholder}'")
            assert input_placeholder == "", f"テキスト入力のプレースホルダーは空であるべきです: '{input_placeholder}'"
    
    def test_no_duplicate_name_related_text_displayed(self):
        """「名前」関連のテキストが重複表示されないことを確認"""
        
        with patch.object(CharacterCreationWizard, '_initialize_ui'):
            wizard = CharacterCreationWizard()
            
            with patch('src.ui.character_creation.config_manager') as mock_config, \
                 patch('src.ui.character_creation.UIInputDialog') as mock_dialog, \
                 patch('src.ui.character_creation.ui_manager'):
                
                # 実際の設定値をシミュレート
                def mock_get_text(key):
                    if key == "character.enter_name":
                        return "名前を入力してください"
                    elif key == "character.enter_name_detail":
                        return "キャラクターの名前を入力してください:"
                    return key
                
                mock_config.get_text.side_effect = mock_get_text
                
                wizard._show_name_input()
                
                # UIInputDialogの全引数を確認
                call_args = mock_dialog.call_args[0]
                call_kwargs = mock_dialog.call_args[1]
                
                all_text_values = []
                all_text_values.append(call_args[1])  # title
                all_text_values.append(call_args[2])  # message
                if len(call_args) > 3:
                    all_text_values.append(call_args[3])  # initial_text
                
                # キーワード引数からもテキストを収集
                for key in ['placeholder', 'initial_text']:
                    if key in call_kwargs:
                        all_text_values.append(call_kwargs[key])
                
                # 「名前」を含むテキストの数をカウント
                name_related_texts = [text for text in all_text_values if text and "名前" in str(text)]
                
                print(f"すべてのテキスト値: {all_text_values}")
                print(f"「名前」を含むテキスト: {name_related_texts}")
                
                # 「名前」を含むテキストが1つ以下であることを確認（重複なし）
                assert len(name_related_texts) <= 1, f"「名前」を含むテキストが重複しています: {name_related_texts}"
                
                # 実際には空のメッセージとプレースホルダーなので、「名前」を含むテキストは0個であるべき
                assert len(name_related_texts) == 0, f"「名前」を含むテキストが表示されています: {name_related_texts}"


if __name__ == "__main__":
    test = TestFinalDuplicationFix()
    test.test_name_input_dialog_has_no_duplicate_text()
    test.test_ui_input_dialog_with_empty_message_and_placeholder()
    test.test_no_duplicate_name_related_text_displayed()
    print("重複修正テストが完了しました")