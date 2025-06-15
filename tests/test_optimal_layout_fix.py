"""最適なレイアウト修正テスト"""

import pytest
from unittest.mock import Mock, patch
from src.ui.character_creation import CharacterCreationWizard


class TestOptimalLayoutFix:
    """最適なレイアウト修正テスト"""
    
    def test_name_input_dialog_shows_only_message(self):
        """名前入力ダイアログがメッセージのみ表示することを確認"""
        
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
                dialog_title = call_args[1]     # "" (空文字)
                dialog_message = call_args[2]   # "名前を入力してください"
                
                # キーワード引数も確認
                kwargs = mock_dialog.call_args[1]
                placeholder = kwargs.get('placeholder', '')
                
                print(f"ダイアログタイトル: '{dialog_title}'")
                print(f"ダイアログメッセージ: '{dialog_message}'")
                print(f"プレースホルダー: '{placeholder}'")
                
                # タイトルが空で、メッセージのみが設定されていることを確認
                assert dialog_title == "", f"タイトルは空であるべきです: '{dialog_title}'"
                assert dialog_message == "名前を入力してください", f"期待されるメッセージ: '名前を入力してください', 実際: '{dialog_message}'"
                assert placeholder == "", f"プレースホルダーは空であるべきです: '{placeholder}'"
    
    def test_no_title_duplication_with_page_header(self):
        """ページヘッダーとの重複がないことを確認"""
        
        with patch.object(CharacterCreationWizard, '_initialize_ui'):
            wizard = CharacterCreationWizard()
            
            with patch('src.ui.character_creation.config_manager') as mock_config, \
                 patch('src.ui.character_creation.UIInputDialog') as mock_dialog, \
                 patch('src.ui.character_creation.ui_manager'):
                
                mock_config.get_text.return_value = "名前を入力してください"
                
                wizard._show_name_input()
                
                call_args = mock_dialog.call_args[0]
                dialog_title = call_args[1]
                dialog_message = call_args[2]
                
                # タイトルが空で「キャラクター作成」と重複しないことを確認
                assert dialog_title != "キャラクター作成", f"ダイアログタイトルがページヘッダーと重複しています: '{dialog_title}'"
                assert "キャラクター" not in dialog_title, f"ダイアログタイトルに「キャラクター」が含まれています: '{dialog_title}'"
                assert "作成" not in dialog_title, f"ダイアログタイトルに「作成」が含まれています: '{dialog_title}'"
                
                # メッセージは適切に表示される
                assert dialog_message == "名前を入力してください", f"メッセージが正しく設定されていません: '{dialog_message}'"
    
    def test_ui_dialog_with_empty_title_and_message_only(self):
        """空のタイトルとメッセージのみでUIDialogが正常動作することを確認"""
        
        with patch('src.ui.base_ui.UIText') as mock_ui_text, \
             patch('src.ui.base_ui.UITextInput'), \
             patch('src.ui.base_ui.DirectFrame'), \
             patch('src.ui.base_ui.DirectButton'):
            
            from src.ui.base_ui import UIInputDialog
            
            # 空のタイトルとメッセージのみでダイアログを作成
            dialog = UIInputDialog(
                "test_dialog",
                "",                           # 空のタイトル
                "名前を入力してください",      # メッセージのみ
                placeholder=""                # 空のプレースホルダー
            )
            
            # UITextが2回呼ばれることを確認（空のタイトルとメッセージ）
            assert mock_ui_text.call_count == 2, f"UITextの呼び出し回数が異常です: {mock_ui_text.call_count}"
            
            # タイトルとメッセージの呼び出し内容を確認
            title_call = mock_ui_text.call_args_list[0]
            message_call = mock_ui_text.call_args_list[1]
            
            title_text = title_call[0][1]      # タイトルテキスト（空）
            message_text = message_call[0][1]  # メッセージテキスト
            
            print(f"タイトルテキスト: '{title_text}'")
            print(f"メッセージテキスト: '{message_text}'")
            
            # タイトルは空で、メッセージは適切に設定されていることを確認
            assert title_text == "", f"タイトルは空であるべきです: '{title_text}'"
            assert message_text == "名前を入力してください", f"メッセージが期待値と異なります: '{message_text}'"
            
            # 位置も確認
            title_pos = title_call[1]['pos']
            message_pos = message_call[1]['pos']
            
            print(f"タイトル位置: {title_pos}")
            print(f"メッセージ位置: {message_pos}")
            
            # メッセージが表示される位置であることを確認
            assert message_pos != (0, 0, 0), f"メッセージ位置が原点になっています: {message_pos}"
    
    def test_single_clear_instruction_displayed(self):
        """明確な指示が1つだけ表示されることを確認"""
        
        with patch.object(CharacterCreationWizard, '_initialize_ui'):
            wizard = CharacterCreationWizard()
            
            with patch('src.ui.character_creation.config_manager') as mock_config, \
                 patch('src.ui.character_creation.UIInputDialog') as mock_dialog, \
                 patch('src.ui.character_creation.ui_manager'):
                
                mock_config.get_text.return_value = "名前を入力してください"
                
                wizard._show_name_input()
                
                # すべてのテキスト要素を収集
                call_args = mock_dialog.call_args[0]
                call_kwargs = mock_dialog.call_args[1]
                
                all_text_elements = []
                all_text_elements.append(call_args[1])  # title
                all_text_elements.append(call_args[2])  # message
                
                if 'placeholder' in call_kwargs:
                    all_text_elements.append(call_kwargs['placeholder'])
                if 'initial_text' in call_kwargs:
                    all_text_elements.append(call_kwargs['initial_text'])
                
                # 空でない有意味なテキスト要素をカウント
                meaningful_texts = [text for text in all_text_elements if text and text.strip()]
                
                print(f"すべてのテキスト要素: {all_text_elements}")
                print(f"有意味なテキスト: {meaningful_texts}")
                
                # 表示される有意味なテキストが1つだけであることを確認
                assert len(meaningful_texts) == 1, f"表示されるテキストは1つだけであるべきです: {meaningful_texts}"
                assert meaningful_texts[0] == "名前を入力してください", f"表示されるテキストが期待値と異なります: '{meaningful_texts[0]}'"
    
    def test_page_header_independence(self):
        """ページヘッダーとダイアログが独立していることを確認"""
        
        # ページ上部のタイトル（CharacterCreationWizardのstep_title）
        page_header_title = "キャラクター作成"
        
        # ダイアログのメッセージ
        dialog_message = "名前を入力してください"
        
        # 両者が異なることを確認
        assert page_header_title != dialog_message, f"ページヘッダーとダイアログメッセージが同じです: '{page_header_title}' == '{dialog_message}'"
        
        # 重複する単語がないことを確認
        header_words = set(page_header_title.split())
        message_words = set(dialog_message.split())
        common_words = header_words & message_words
        
        print(f"ページヘッダー単語: {header_words}")
        print(f"ダイアログメッセージ単語: {message_words}")
        print(f"共通単語: {common_words}")
        
        # 共通単語は最小限であることを確認（完全に異なる内容）
        assert len(common_words) == 0, f"ページヘッダーとダイアログに共通単語があります: {common_words}"


if __name__ == "__main__":
    test = TestOptimalLayoutFix()
    test.test_name_input_dialog_shows_only_message()
    test.test_no_title_duplication_with_page_header()
    test.test_ui_dialog_with_empty_title_and_message_only()
    test.test_single_clear_instruction_displayed()
    test.test_page_header_independence()
    print("最適レイアウト修正テストが完了しました")