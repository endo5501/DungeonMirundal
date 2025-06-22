"""キャラクター追加機能の統合テスト"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from src.overworld.facilities.guild import AdventurersGuild
from src.character.character import Character
from src.character.party import Party


class TestGuildCharacterAddIntegration:
    """キャラクター追加機能の統合テスト"""
    
    def setup_method(self):
        """各テストメソッドの前に実行"""
        self.guild = AdventurersGuild()
        
        # リアルなPartyオブジェクトを作成
        self.party = Party()
        self.guild.current_party = self.party
        
        # 作成済みキャラクターのリストを初期化
        self.guild.created_characters = []
        
    def create_test_character(self, name="テストキャラ", char_id="test_char"):
        """テスト用キャラクターを作成"""
        character = Mock()
        character.name = name
        character.character_id = char_id
        character.experience = Mock()
        character.experience.level = 1
        character.get_race_name = Mock(return_value="人間")
        character.get_class_name = Mock(return_value="戦士")
        return character
    
    def test_add_character_to_party_complete_flow(self):
        """キャラクター追加の完全なフローテスト"""
        # テストキャラクターを作成
        test_char = self.create_test_character()
        
        # Partyのadd_characterメソッドをモック
        with patch.object(self.party, 'add_character', return_value=True) as mock_add, \
             patch.object(self.guild, '_show_success_message') as mock_success, \
             patch.object(self.guild, '_close_all_submenus_and_return_to_main') as mock_close:
            
            # キャラクター追加を実行
            self.guild._add_character_to_party(test_char)
            
            # Partyのadd_characterが呼ばれることを確認
            mock_add.assert_called_once_with(test_char)
            
            # 成功メッセージが表示されることを確認
            mock_success.assert_called_once_with("テストキャラ をパーティに追加しました")
            
            # メニュー遷移処理が呼ばれることを確認
            mock_close.assert_called_once()
    
    def test_add_character_failure_handling(self):
        """キャラクター追加失敗時の処理テスト"""
        # テストキャラクターを作成
        test_char = self.create_test_character()
        
        # Partyのadd_characterが失敗する場合をモック
        with patch.object(self.party, 'add_character', return_value=False) as mock_add, \
             patch.object(self.guild, '_show_error_message') as mock_error:
            
            # キャラクター追加を実行
            self.guild._add_character_to_party(test_char)
            
            # Partyのadd_characterが呼ばれることを確認
            mock_add.assert_called_once_with(test_char)
            
            # エラーメッセージが表示されることを確認
            mock_error.assert_called_once_with("キャラクターの追加に失敗しました")
    
    def test_close_all_submenus_actual_implementation(self):
        """_close_all_submenus_and_return_to_mainの実際の実装テスト"""
        # UIManagerとメニュー要素をモック
        with patch('src.overworld.facilities.guild.ui_manager') as mock_ui_manager:
            
            # add_character_menuが存在する場合
            mock_add_menu = Mock()
            mock_ui_manager.get_element.return_value = mock_add_menu
            
            # _back_to_main_menu_from_submenuをモック
            with patch.object(self.guild, '_back_to_main_menu_from_submenu') as mock_back_to_main:
                
                self.guild._close_all_submenus_and_return_to_main()
                
                # 正しいメニューが取得されることを確認
                mock_ui_manager.get_element.assert_called_once_with("add_character_menu")
                
                # 正しい引数で呼ばれることを確認
                mock_back_to_main.assert_called_once_with(mock_add_menu)
    
    def test_close_all_submenus_fallback_path(self):
        """_close_all_submenus_and_return_to_mainのフォールバックパステスト"""
        # UIManagerをモック（add_character_menuが存在しない場合）
        with patch('src.overworld.facilities.guild.ui_manager') as mock_ui_manager:
            
            # add_character_menuが存在しない場合
            mock_ui_manager.get_element.return_value = None
            
            # _back_to_main_menu_fallbackをモック
            with patch.object(self.guild, '_back_to_main_menu_fallback') as mock_fallback:
                
                self.guild._close_all_submenus_and_return_to_main()
                
                # 正しいメニューが取得されることを確認
                mock_ui_manager.get_element.assert_called_once_with("add_character_menu")
                
                # フォールバックが呼ばれることを確認
                mock_fallback.assert_called_once()
    
    def test_back_to_main_menu_fallback_implementation(self):
        """_back_to_main_menu_fallbackの実装テスト"""
        # UIManagerをモック
        with patch('src.overworld.facilities.guild.ui_manager') as mock_ui_manager:
            
            # メインメニューをモック
            self.guild.main_menu = Mock()
            self.guild.main_menu.element_id = "guild_main_menu"
            
            # 一部のメニューが存在する場合
            def mock_get_element(menu_id):
                if menu_id in ["party_formation_menu", "add_character_menu"]:
                    return Mock()  # メニューが存在する
                return None  # メニューが存在しない
            
            mock_ui_manager.get_element.side_effect = mock_get_element
            
            self.guild._back_to_main_menu_fallback()
            
            # 複数のメニューIDでget_elementが呼ばれることを確認
            expected_menu_ids = [
                "party_formation_menu",
                "add_character_menu", 
                "remove_character_menu",
                "position_menu",
                "new_position_menu"
            ]
            
            # get_elementが期待するメニューIDで呼ばれることを確認
            actual_calls = [call[0][0] for call in mock_ui_manager.get_element.call_args_list]
            for menu_id in expected_menu_ids:
                assert menu_id in actual_calls, f"Menu ID '{menu_id}' should be checked"
            
            # 存在するメニューに対してhide_elementとunregister_elementが呼ばれることを確認
            mock_ui_manager.hide_element.assert_any_call("party_formation_menu")
            mock_ui_manager.hide_element.assert_any_call("add_character_menu")
            mock_ui_manager.unregister_element.assert_any_call("party_formation_menu")
            mock_ui_manager.unregister_element.assert_any_call("add_character_menu")
            
            # メインメニューが表示されることを確認
            mock_ui_manager.show_element.assert_called_once_with("guild_main_menu")
    
    def test_character_addition_without_party_crash(self):
        """パーティが設定されていない場合のクラッシュ回避テスト"""
        self.guild.current_party = None
        test_char = self.create_test_character()
        
        # パーティが設定されていない場合でもクラッシュしないことを確認
        try:
            self.guild._add_character_to_party(test_char)
            test_passed = True
        except Exception as e:
            test_passed = False
            pytest.fail(f"パーティ未設定時にクラッシュが発生しました: {e}")
        
        assert test_passed, "パーティ未設定時の処理がクラッシュしました"