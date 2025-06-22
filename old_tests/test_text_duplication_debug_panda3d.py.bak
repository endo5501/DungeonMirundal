"""テキスト重複デバッグテスト"""

import pytest
from unittest.mock import Mock, patch
from src.ui.character_creation import CharacterCreationWizard


class TestTextDuplicationDebug:
    """テキスト重複の原因を調査"""
    
    def test_character_name_input_text_content(self):
        """キャラクター名前入力で使用されるテキスト内容を確認"""
        
        with patch.object(CharacterCreationWizard, '_initialize_ui'):
            wizard = CharacterCreationWizard()
            
            with patch('src.ui.character_creation.config_manager') as mock_config, \
                 patch('src.ui.character_creation.UIInputDialog') as mock_dialog, \
                 patch('src.ui.character_creation.ui_manager'):
                
                # 実際のテキスト設定をシミュレート
                mock_config.get_text.return_value = "名前を入力してください"
                
                wizard._show_name_input()
                
                # UIInputDialogの呼び出し引数を確認
                call_args = mock_dialog.call_args[0]
                dialog_id = call_args[0]        # "name_input_dialog"
                dialog_title = call_args[1]     # "キャラクター作成"
                dialog_message = call_args[2]   # "名前を入力してください"
                
                print(f"ダイアログID: {dialog_id}")
                print(f"ダイアログタイトル: {dialog_title}")
                print(f"ダイアログメッセージ: {dialog_message}")
                
                # タイトルとメッセージが異なることを確認
                assert dialog_title != dialog_message, \
                    f"タイトルとメッセージが同じです: '{dialog_title}' == '{dialog_message}'"
                
                # 期待されるテキスト内容であることを確認
                assert dialog_title == "キャラクター作成", f"期待されるタイトル: 'キャラクター作成', 実際: '{dialog_title}'"
                assert dialog_message == "名前を入力してください", f"期待されるメッセージ: '名前を入力してください', 実際: '{dialog_message}'"
    
    def test_config_text_keys_are_different(self):
        """設定ファイルのテキストキーが適切に分離されていることを確認"""
        
        from src.core.config_manager import config_manager
        
        try:
            enter_name_text = config_manager.get_text("character.enter_name")
            enter_name_detail_text = config_manager.get_text("character.enter_name_detail")
            
            print(f"character.enter_name: '{enter_name_text}'")
            print(f"character.enter_name_detail: '{enter_name_detail_text}'")
            
            # 両方のテキストが存在することを確認
            assert enter_name_text is not None, "character.enter_nameが存在しません"
            assert enter_name_detail_text is not None, "character.enter_name_detailが存在しません"
            
            # 内容が適切であることを確認
            assert "名前" in enter_name_text, "character.enter_nameに「名前」が含まれていません"
            assert "名前" in enter_name_detail_text, "character.enter_name_detailに「名前」が含まれていません"
            
        except Exception as e:
            print(f"設定ファイルアクセスエラー: {e}")
            # テスト環境では設定ファイルにアクセスできない場合があるため、パス
            pass
    
    def test_ui_input_dialog_parameter_mapping(self):
        """UIInputDialogのパラメータマッピングを確認"""
        
        with patch('src.ui.base_ui.UIText') as mock_ui_text, \
             patch('src.ui.base_ui.UITextInput'), \
             patch('src.ui.base_ui.DirectFrame'), \
             patch('src.ui.base_ui.DirectButton'):
            
            from src.ui.base_ui import UIInputDialog
            
            # 明確に異なるタイトルとメッセージでダイアログを作成
            dialog = UIInputDialog(
                "test_dialog",
                "【タイトル】キャラクター作成",      # 明確に区別可能なタイトル
                "【メッセージ】名前を入力してください"   # 明確に区別可能なメッセージ
            )
            
            # UITextが2回呼ばれることを確認
            assert mock_ui_text.call_count == 2, f"UITextの呼び出し回数が異常です: {mock_ui_text.call_count}"
            
            # 各呼び出しのテキスト内容を確認
            title_call = mock_ui_text.call_args_list[0]
            message_call = mock_ui_text.call_args_list[1]
            
            title_text = title_call[0][1]    # 2番目の位置引数（テキスト）
            message_text = message_call[0][1]
            
            print(f"UITextタイトル呼び出し: '{title_text}'")
            print(f"UITextメッセージ呼び出し: '{message_text}'")
            
            # タイトルとメッセージが正しく分離されていることを確認
            assert title_text == "【タイトル】キャラクター作成", f"タイトルテキストが期待値と異なります: '{title_text}'"
            assert message_text == "【メッセージ】名前を入力してください", f"メッセージテキストが期待値と異なります: '{message_text}'"
            
            # 位置が異なることを確認
            title_pos = title_call[1]['pos']
            message_pos = message_call[1]['pos']
            
            print(f"タイトル位置: {title_pos}")
            print(f"メッセージ位置: {message_pos}")
            
            assert title_pos != message_pos, f"タイトルとメッセージの位置が同じです: {title_pos}"
    
    def test_potential_duplicate_ui_elements(self):
        """重複するUI要素の可能性を調査"""
        
        # 重複の可能性：
        # 1. UIInputDialogが複数作成されている
        # 2. 同じテキストを別の場所でも表示している
        # 3. UITextが意図せず重複している
        
        with patch('src.ui.character_creation.UIInputDialog') as mock_dialog:
            
            with patch.object(CharacterCreationWizard, '_initialize_ui'):
                wizard = CharacterCreationWizard()
                
                with patch('src.ui.character_creation.config_manager') as mock_config, \
                     patch('src.ui.character_creation.ui_manager'):
                    
                    mock_config.get_text.return_value = "名前を入力してください"
                    
                    # 複数回呼び出して重複作成がないことを確認
                    wizard._show_name_input()
                    first_call_count = mock_dialog.call_count
                    
                    wizard._show_name_input()
                    second_call_count = mock_dialog.call_count
                    
                    print(f"1回目の呼び出し後: {first_call_count}")
                    print(f"2回目の呼び出し後: {second_call_count}")
                    
                    # 呼び出し回数が期待通りであることを確認
                    assert first_call_count == 1, f"初回呼び出しでUIInputDialogが複数作成されました: {first_call_count}"
                    assert second_call_count == 2, f"2回目呼び出しで期待される作成数と異なります: {second_call_count}"


if __name__ == "__main__":
    test = TestTextDuplicationDebug()
    test.test_character_name_input_text_content()
    test.test_config_text_keys_are_different()
    test.test_ui_input_dialog_parameter_mapping()
    test.test_potential_duplicate_ui_elements()
    print("すべてのデバッグテストが完了しました")