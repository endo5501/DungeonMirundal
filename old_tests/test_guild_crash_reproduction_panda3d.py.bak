"""キャラクター編成画面クラッシュの再現テスト"""

import pytest
from unittest.mock import Mock, patch, MagicMock, PropertyMock
from src.overworld.facilities.guild import AdventurersGuild
from src.character.character import Character
from src.character.party import Party


class TestGuildCrashReproduction:
    """キャラクター編成画面クラッシュの再現テスト"""
    
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
    
    def test_crash_when_back_to_main_menu_from_submenu_missing_arg(self):
        """_back_to_main_menu_from_submenuに引数を渡さない場合のクラッシュテスト"""
        test_char = self.create_mock_character()
        
        # current_partyのadd_characterが成功を返すようにモック
        with patch.object(self.party, 'add_character', return_value=True):
            
            # _show_success_messageをモック
            with patch.object(self.guild, '_show_success_message'):
                
                # _close_all_submenus_and_return_to_mainをモックして失敗させる
                with patch.object(self.guild, '_close_all_submenus_and_return_to_main') as mock_close:
                    
                    # TypeError を発生させる（引数不足のエラーをシミュレート）
                    mock_close.side_effect = TypeError("_back_to_main_menu_from_submenu() missing 1 required positional argument: 'submenu'")
                    
                    # この場合にクラッシュが発生することを確認
                    with pytest.raises(TypeError, match="missing 1 required positional argument"):
                        self.guild._add_character_to_party(test_char)
    
    def test_crash_when_ui_manager_methods_fail(self):
        """UIManager のメソッドが失敗した場合のクラッシュテスト"""
        test_char = self.create_mock_character()
        
        # current_partyのadd_characterが成功を返すようにモック
        with patch.object(self.party, 'add_character', return_value=True):
            
            # _show_success_messageをモック
            with patch.object(self.guild, '_show_success_message'):
                
                # ui_managerのget_elementが例外を発生させる
                with patch('src.overworld.facilities.guild.ui_manager') as mock_ui_manager:
                    mock_ui_manager.get_element.side_effect = AttributeError("'NoneType' object has no attribute 'element_id'")
                    
                    # この場合にクラッシュが発生することを確認
                    with pytest.raises(AttributeError):
                        self.guild._add_character_to_party(test_char)
    
    def test_crash_when_back_to_main_menu_from_submenu_not_implemented(self):
        """_back_to_main_menu_from_submenuが実装されていない場合のクラッシュテスト"""
        test_char = self.create_mock_character()
        
        # current_partyのadd_characterが成功を返すようにモック
        with patch.object(self.party, 'add_character', return_value=True):
            
            # _show_success_messageをモック
            with patch.object(self.guild, '_show_success_message'):
                
                # _back_to_main_menu_from_submenuメソッドを削除
                if hasattr(self.guild, '_back_to_main_menu_from_submenu'):
                    delattr(self.guild, '_back_to_main_menu_from_submenu')
                
                # この場合にAttributeErrorが発生することを確認
                with pytest.raises(AttributeError, match="has no attribute '_back_to_main_menu_from_submenu'"):
                    self.guild._add_character_to_party(test_char)
    
    def test_original_bug_scenario_direct_call(self):
        """元のバグシナリオ: _back_to_main_menu_from_submenuを直接引数なしで呼ぶ"""
        test_char = self.create_mock_character()
        
        # 元のバグがあった場合のシナリオをシミュレート
        # _add_character_to_partyメソッドを一時的に変更
        original_method = self.guild._add_character_to_party
        
        def buggy_add_character_to_party(character):
            """バグのあるバージョンのメソッド"""
            if not self.guild.current_party:
                return
            
            success = self.guild.current_party.add_character(character)
            
            if success:
                self.guild._show_success_message(f"{character.name} をパーティに追加しました")
                # バグ: 引数なしで呼び出し
                self.guild._back_to_main_menu_from_submenu()  # TypeError発生
            else:
                self.guild._show_error_message("キャラクターの追加に失敗しました")
        
        # メソッドを一時的に置き換え
        self.guild._add_character_to_party = buggy_add_character_to_party
        
        # current_partyのadd_characterが成功を返すようにモック
        with patch.object(self.party, 'add_character', return_value=True):
            
            # _show_success_messageをモック
            with patch.object(self.guild, '_show_success_message'):
                
                # この場合にTypeErrorが発生することを確認
                with pytest.raises(TypeError, match="missing 1 required positional argument"):
                    self.guild._add_character_to_party(test_char)
        
        # メソッドを元に戻す
        self.guild._add_character_to_party = original_method
    
    def test_current_implementation_works_correctly(self):
        """現在の実装が正しく動作することを確認"""
        test_char = self.create_mock_character()
        
        # current_partyのadd_characterが成功を返すようにモック
        with patch.object(self.party, 'add_character', return_value=True):
            
            # 必要なメソッドをモック
            with patch.object(self.guild, '_show_success_message') as mock_success, \
                 patch.object(self.guild, '_close_all_submenus_and_return_to_main') as mock_close:
                
                # 現在の実装でクラッシュしないことを確認
                try:
                    self.guild._add_character_to_party(test_char)
                    test_passed = True
                except Exception as e:
                    test_passed = False
                    pytest.fail(f"現在の実装でクラッシュが発生しました: {e}")
                
                assert test_passed, "現在の実装でクラッシュが発生しました"
                
                # 必要なメソッドが呼ばれることを確認
                mock_success.assert_called_once()
                mock_close.assert_called_once()
    
    def test_potential_issues_in_close_all_submenus(self):
        """_close_all_submenus_and_return_to_mainでの潜在的問題テスト"""
        
        # _back_to_main_menu_from_submenuが例外を発生させる場合
        with patch('src.overworld.facilities.guild.ui_manager') as mock_ui_manager, \
             patch.object(self.guild, '_back_to_main_menu_from_submenu') as mock_back_to_main:
            
            # add_character_menuが存在する場合
            mock_add_menu = Mock()
            mock_ui_manager.get_element.return_value = mock_add_menu
            
            # _back_to_main_menu_from_submenuが例外を発生
            mock_back_to_main.side_effect = Exception("UI transition failed")
            
            # この場合に例外が発生することを確認
            with pytest.raises(Exception, match="UI transition failed"):
                self.guild._close_all_submenus_and_return_to_main()