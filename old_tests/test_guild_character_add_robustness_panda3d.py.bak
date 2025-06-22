"""キャラクター追加機能の堅牢性テスト"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from src.overworld.facilities.guild import AdventurersGuild
from src.character.character import Character
from src.character.party import Party


class TestGuildCharacterAddRobustness:
    """キャラクター追加機能の堅牢性テスト"""
    
    def setup_method(self):
        """各テストメソッドの前に実行"""
        self.guild = AdventurersGuild()
        self.party = Party()
        self.guild.current_party = self.party
        
    def create_mock_character(self, name="TestChar", char_id="test_1"):
        """モックキャラクター作成"""
        character = Mock()
        character.name = name
        character.character_id = char_id
        return character
    
    def test_add_character_no_party_handling(self):
        """パーティが設定されていない場合の処理テスト"""
        test_char = self.create_mock_character()
        self.guild.current_party = None
        
        with patch.object(self.guild, '_show_error_message') as mock_error:
            
            # パーティがない場合でもクラッシュしないことを確認
            try:
                self.guild._add_character_to_party(test_char)
                test_passed = True
            except Exception as e:
                test_passed = False
                pytest.fail(f"パーティ未設定時にクラッシュが発生しました: {e}")
            
            assert test_passed
            # エラーメッセージが表示されることを確認
            mock_error.assert_called_once_with("パーティが設定されていません")
    
    def test_add_character_party_add_character_exception(self):
        """party.add_characterで例外が発生した場合の処理テスト"""
        test_char = self.create_mock_character()
        
        # party.add_characterが例外を発生させる
        with patch.object(self.party, 'add_character', side_effect=Exception("Party is full")):
            
            with patch.object(self.guild, '_show_error_message') as mock_error, \
                 patch.object(self.guild, '_back_to_main_menu_fallback') as mock_fallback:
                
                # 例外が発生してもクラッシュしないことを確認
                try:
                    self.guild._add_character_to_party(test_char)
                    test_passed = True
                except Exception as e:
                    test_passed = False
                    pytest.fail(f"party.add_character例外時にクラッシュが発生しました: {e}")
                
                assert test_passed
                # エラーメッセージが表示されることを確認
                mock_error.assert_called_once()
                # フォールバック処理が呼ばれることを確認
                mock_fallback.assert_called_once()
    
    def test_add_character_close_submenus_exception(self):
        """_close_all_submenus_and_return_to_mainで例外が発生した場合の処理テスト"""
        test_char = self.create_mock_character()
        
        with patch.object(self.party, 'add_character', return_value=True):
            
            with patch.object(self.guild, '_show_success_message') as mock_success, \
                 patch.object(self.guild, '_close_all_submenus_and_return_to_main', 
                             side_effect=Exception("UI transition failed")) as mock_close, \
                 patch.object(self.guild, '_back_to_main_menu_fallback') as mock_fallback:
                
                # close_submenusで例外が発生してもクラッシュしないことを確認
                try:
                    self.guild._add_character_to_party(test_char)
                    test_passed = True
                except Exception as e:
                    test_passed = False
                    pytest.fail(f"close_submenus例外時にクラッシュが発生しました: {e}")
                
                assert test_passed
                # 成功メッセージは表示される
                mock_success.assert_called_once()
                # close_submenusが呼ばれる
                mock_close.assert_called_once()
                # フォールバックが呼ばれる
                mock_fallback.assert_called_once()
    
    def test_close_all_submenus_ui_manager_exception(self):
        """_close_all_submenus_and_return_to_mainでui_manager例外が発生した場合のテスト"""
        
        with patch('src.overworld.facilities.guild.ui_manager') as mock_ui_manager:
            
            # ui_manager.get_elementが例外を発生
            mock_ui_manager.get_element.side_effect = Exception("UI Manager Error")
            
            with patch.object(self.guild, '_back_to_main_menu_fallback') as mock_fallback:
                
                # 例外が発生してもクラッシュしないことを確認
                try:
                    self.guild._close_all_submenus_and_return_to_main()
                    test_passed = True
                except Exception as e:
                    test_passed = False
                    pytest.fail(f"ui_manager例外時にクラッシュが発生しました: {e}")
                
                assert test_passed
                # フォールバックが呼ばれることを確認
                mock_fallback.assert_called_once()
    
    def test_close_all_submenus_fallback_also_fails(self):
        """_close_all_submenus_and_return_to_mainとフォールバック両方で例外が発生した場合のテスト"""
        
        # メインメニューをモック
        self.guild.main_menu = Mock()
        self.guild.main_menu.element_id = "guild_main_menu"
        
        with patch('src.overworld.facilities.guild.ui_manager') as mock_ui_manager:
            
            # ui_manager.get_elementが例外を発生
            mock_ui_manager.get_element.side_effect = Exception("UI Manager Error")
            
            with patch.object(self.guild, '_back_to_main_menu_fallback', 
                             side_effect=Exception("Fallback failed")):
                
                # 両方の処理で例外が発生してもクラッシュしないことを確認
                try:
                    self.guild._close_all_submenus_and_return_to_main()
                    test_passed = True
                except Exception as e:
                    test_passed = False
                    pytest.fail(f"フォールバック失敗時にクラッシュが発生しました: {e}")
                
                assert test_passed
                # 最後の手段としてメインメニューが表示されることを確認
                mock_ui_manager.show_element.assert_called_once_with("guild_main_menu")
    
    def test_close_all_submenus_complete_failure_handling(self):
        """すべての処理が失敗した場合でもクラッシュしないことを確認"""
        
        # メインメニューもない状況
        self.guild.main_menu = None
        
        with patch('src.overworld.facilities.guild.ui_manager') as mock_ui_manager:
            
            # すべてのui_manager操作が例外を発生
            mock_ui_manager.get_element.side_effect = Exception("UI Manager Error")
            mock_ui_manager.show_element.side_effect = Exception("Show Element Error")
            
            with patch.object(self.guild, '_back_to_main_menu_fallback', 
                             side_effect=Exception("Fallback failed")):
                
                # 完全に失敗してもクラッシュしないことを確認
                try:
                    self.guild._close_all_submenus_and_return_to_main()
                    test_passed = True
                except Exception as e:
                    test_passed = False
                    pytest.fail(f"完全失敗時にクラッシュが発生しました: {e}")
                
                assert test_passed
    
    def test_add_character_success_path_with_robust_handling(self):
        """成功パスでエラーハンドリングが追加されても正常動作することを確認"""
        test_char = self.create_mock_character()
        
        with patch.object(self.party, 'add_character', return_value=True):
            
            with patch.object(self.guild, '_show_success_message') as mock_success, \
                 patch.object(self.guild, '_close_all_submenus_and_return_to_main') as mock_close:
                
                # 正常パスで問題なく動作することを確認
                try:
                    self.guild._add_character_to_party(test_char)
                    test_passed = True
                except Exception as e:
                    test_passed = False
                    pytest.fail(f"正常パスでクラッシュが発生しました: {e}")
                
                assert test_passed
                mock_success.assert_called_once_with("TestChar をパーティに追加しました")
                mock_close.assert_called_once()
    
    def test_add_character_failure_path_with_robust_handling(self):
        """失敗パスでエラーハンドリングが追加されても正常動作することを確認"""
        test_char = self.create_mock_character()
        
        with patch.object(self.party, 'add_character', return_value=False):
            
            with patch.object(self.guild, '_show_error_message') as mock_error:
                
                # 失敗パスで問題なく動作することを確認
                try:
                    self.guild._add_character_to_party(test_char)
                    test_passed = True
                except Exception as e:
                    test_passed = False
                    pytest.fail(f"失敗パスでクラッシュが発生しました: {e}")
                
                assert test_passed
                mock_error.assert_called_once_with("キャラクターの追加に失敗しました")