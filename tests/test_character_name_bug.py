"""キャラクター作成の名前変更バグのテスト"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from src.ui.character_creation import CharacterCreationWizard, CreationStep
from src.ui.base_ui import UIInputDialog


class TestCharacterNameBug:
    """キャラクター名前変更バグのテストクラス"""
    
    def setup_method(self):
        """各テストメソッドの前に実行"""
        self.on_complete = Mock()
        self.on_cancel = Mock()
        
        with patch('src.ui.character_creation.ui_manager'):
            with patch('src.ui.character_creation.config_manager') as mock_config:
                mock_config.get_text.return_value = "テスト文字列"
                self.wizard = CharacterCreationWizard(callback=self.on_complete)
                # on_cancelを手動で設定
                self.wizard.on_cancel = self.on_cancel
    
    def test_name_input_uses_input_dialog(self):
        """名前入力でUIInputDialogが使用されるテスト"""
        with patch('src.ui.character_creation.ui_manager') as mock_ui:
            with patch('src.ui.character_creation.config_manager') as mock_config:
                mock_config.get_text.return_value = "名前入力"
                
                # 名前入力ステップを実行
                self.wizard._show_name_input()
                
                # UIInputDialogが作成されることを確認
                assert isinstance(self.wizard.current_ui, UIInputDialog)
                assert self.wizard.current_ui.element_id == "name_input_dialog"
    
    def test_name_confirmation_with_valid_name(self):
        """有効な名前での確認処理テスト"""
        test_name = "テストヒーロー"
        
        with patch.object(self.wizard, '_next_step') as mock_next:
            with patch('src.ui.character_creation.ui_manager') as mock_ui:
                # 名前確認処理を実行
                self.wizard._on_name_confirmed(test_name)
                
                # 名前が設定されることを確認
                assert self.wizard.character_data['name'] == test_name
                
                # 次のステップに進むことを確認
                mock_next.assert_called_once()
    
    def test_name_confirmation_with_empty_name(self):
        """空の名前での確認処理テスト"""
        with patch.object(self.wizard, '_next_step') as mock_next:
            with patch('src.ui.character_creation.ui_manager') as mock_ui:
                # 空の名前で確認処理を実行
                self.wizard._on_name_confirmed("")
                
                # デフォルト名が設定されることを確認
                assert self.wizard.character_data['name'] == "Hero"
                
                # 次のステップに進むことを確認
                mock_next.assert_called_once()
    
    def test_name_confirmation_with_whitespace_name(self):
        """空白のみの名前での確認処理テスト"""
        with patch.object(self.wizard, '_next_step') as mock_next:
            with patch('src.ui.character_creation.ui_manager') as mock_ui:
                # 空白のみの名前で確認処理を実行
                self.wizard._on_name_confirmed("   ")
                
                # デフォルト名が設定されることを確認
                assert self.wizard.character_data['name'] == "Hero"
    
    def test_name_confirmation_with_long_name(self):
        """長すぎる名前での確認処理テスト"""
        long_name = "非常に長いキャラクター名前テストケース" # 20文字以上
        
        with patch.object(self.wizard, '_next_step') as mock_next:
            with patch('src.ui.character_creation.ui_manager') as mock_ui:
                # 長い名前で確認処理を実行
                self.wizard._on_name_confirmed(long_name)
                
                # 20文字に切り詰められることを確認
                assert len(self.wizard.character_data['name']) <= 20
                assert self.wizard.character_data['name'] == long_name[:20]
    
    def test_name_confirmation_with_special_characters(self):
        """特殊文字を含む名前での確認処理テスト"""
        dangerous_name = "Hero<script>"
        
        with patch.object(self.wizard, '_next_step') as mock_next:
            with patch('src.ui.character_creation.ui_manager') as mock_ui:
                # 特殊文字を含む名前で確認処理を実行
                self.wizard._on_name_confirmed(dangerous_name)
                
                # デフォルト名に置き換えられることを確認
                assert self.wizard.character_data['name'] == "Hero"
    
    def test_name_cancellation(self):
        """名前入力キャンセル処理テスト"""
        with patch('src.ui.character_creation.ui_manager') as mock_ui:
            # 現在のUIを設定
            self.wizard.current_ui = Mock()
            self.wizard.current_ui.element_id = "test_dialog"
            
            # キャンセル処理を実行
            self.wizard._on_name_cancelled()
            
            # キャンセルコールバックが呼ばれることを確認
            self.on_cancel.assert_called_once()
            
            # UIが適切にクリーンアップされることを確認
            mock_ui.hide_element.assert_called_with("test_dialog")
            mock_ui.unregister_element.assert_called_with("test_dialog")
            assert self.wizard.current_ui is None
    
    def test_name_input_with_initial_value(self):
        """初期値があるときの名前入力テスト"""
        self.wizard.character_data['name'] = "既存の名前"
        
        with patch('src.ui.character_creation.ui_manager') as mock_ui:
            with patch('src.ui.character_creation.config_manager') as mock_config:
                mock_config.get_text.return_value = "名前入力"
                
                # 名前入力ステップを実行
                self.wizard._show_name_input()
                
                # 初期値が設定されることを確認
                assert self.wizard.current_ui.text_input.initial_text == "既存の名前"
    
    def test_character_data_persistence_after_name_change(self):
        """名前変更後にキャラクターデータが保持されるテスト"""
        # 事前にキャラクターデータを設定
        self.wizard.character_data.update({
            'race': 'human',
            'class': 'fighter',
            'stats': {'strength': 15}
        })
        
        with patch.object(self.wizard, '_next_step'):
            with patch('src.ui.character_creation.ui_manager'):
                # 名前を変更
                self.wizard._on_name_confirmed("新しい名前")
                
                # 名前以外のデータが保持されることを確認
                assert self.wizard.character_data['name'] == "新しい名前"
                assert self.wizard.character_data['race'] == 'human'
                assert self.wizard.character_data['class'] == 'fighter'
                assert self.wizard.character_data['stats']['strength'] == 15