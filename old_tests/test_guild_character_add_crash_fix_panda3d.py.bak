"""キャラクター編成画面での[キャラクターを追加]クラッシュ修正テスト"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from src.overworld.facilities.guild import AdventurersGuild
from src.character.character import Character


class TestGuildCharacterAddCrashFix:
    """キャラクター編成画面での[キャラクターを追加]クラッシュ修正テスト"""
    
    def setup_method(self):
        """各テストメソッドの前に実行"""
        self.guild = AdventurersGuild()
        self.mock_party = Mock()
        self.mock_party.characters = {}
        self.mock_party.gold = 1000
        self.guild.current_party = self.mock_party
        
    def test_add_character_to_party_success_no_crash(self):
        """キャラクター追加成功時にクラッシュしないことを確認"""
        # テストキャラクターを作成
        mock_character = Mock()
        mock_character.name = "テストキャラ"
        mock_character.character_id = "test_char_1"
        
        # add_character が成功する場合をモック
        self.mock_party.add_character.return_value = True
        
        # 必要なメソッドをモック
        with patch.object(self.guild, '_show_success_message') as mock_success, \
             patch.object(self.guild, '_close_all_submenus_and_return_to_main') as mock_close_submenus:
            
            # この操作がクラッシュしないことを確認
            try:
                self.guild._add_character_to_party(mock_character)
                test_passed = True
            except Exception as e:
                test_passed = False
                pytest.fail(f"キャラクター追加でクラッシュが発生しました: {e}")
            
            # 正常に処理が完了することを確認
            assert test_passed, "キャラクター追加処理がクラッシュしました"
            
            # 成功メッセージが表示されることを確認
            mock_success.assert_called_once_with("テストキャラ をパーティに追加しました")
            
            # メニュー閉じる処理が呼ばれることを確認
            mock_close_submenus.assert_called_once()
            
            # add_character が呼ばれることを確認
            self.mock_party.add_character.assert_called_once_with(mock_character)
    
    def test_add_character_to_party_failure_no_crash(self):
        """キャラクター追加失敗時にクラッシュしないことを確認"""
        # テストキャラクターを作成
        mock_character = Mock()
        mock_character.name = "テストキャラ"
        mock_character.character_id = "test_char_1"
        
        # add_character が失敗する場合をモック
        self.mock_party.add_character.return_value = False
        
        # 必要なメソッドをモック
        with patch.object(self.guild, '_show_error_message') as mock_error:
            
            # この操作がクラッシュしないことを確認
            try:
                self.guild._add_character_to_party(mock_character)
                test_passed = True
            except Exception as e:
                test_passed = False
                pytest.fail(f"キャラクター追加失敗時にクラッシュが発生しました: {e}")
            
            # 正常に処理が完了することを確認
            assert test_passed, "キャラクター追加失敗処理がクラッシュしました"
            
            # エラーメッセージが表示されることを確認
            mock_error.assert_called_once_with("キャラクターの追加に失敗しました")
            
            # add_character が呼ばれることを確認
            self.mock_party.add_character.assert_called_once_with(mock_character)
    
    def test_close_all_submenus_method_exists(self):
        """_close_all_submenus_and_return_to_mainメソッドが存在することを確認"""
        # メソッドが存在することを確認
        assert hasattr(self.guild, '_close_all_submenus_and_return_to_main')
        assert callable(self.guild._close_all_submenus_and_return_to_main)
    
    def test_close_all_submenus_with_existing_menu(self):
        """add_character_menuが存在する場合の処理テスト"""
        mock_add_menu = Mock()
        
        with patch('src.overworld.facilities.guild.ui_manager') as mock_ui_manager, \
             patch.object(self.guild, '_back_to_main_menu_from_submenu') as mock_back_to_main:
            
            # get_elementがadd_menuを返すようにモック
            mock_ui_manager.get_element.return_value = mock_add_menu
            
            self.guild._close_all_submenus_and_return_to_main()
            
            # get_elementが正しく呼ばれることを確認
            mock_ui_manager.get_element.assert_called_once_with("add_character_menu")
            
            # _back_to_main_menu_from_submenuが正しい引数で呼ばれることを確認
            mock_back_to_main.assert_called_once_with(mock_add_menu)
    
    def test_close_all_submenus_with_fallback(self):
        """add_character_menuが存在しない場合のフォールバック処理テスト"""
        with patch('src.overworld.facilities.guild.ui_manager') as mock_ui_manager, \
             patch.object(self.guild, '_back_to_main_menu_fallback') as mock_fallback:
            
            # get_elementがNoneを返すようにモック（メニューが存在しない）
            mock_ui_manager.get_element.return_value = None
            
            self.guild._close_all_submenus_and_return_to_main()
            
            # get_elementが正しく呼ばれることを確認
            mock_ui_manager.get_element.assert_called_once_with("add_character_menu")
            
            # フォールバックメソッドが呼ばれることを確認
            mock_fallback.assert_called_once()
    
    def test_back_to_main_menu_fallback_method_exists(self):
        """_back_to_main_menu_fallbackメソッドが存在することを確認"""
        # メソッドが存在することを確認
        assert hasattr(self.guild, '_back_to_main_menu_fallback')
        assert callable(self.guild._back_to_main_menu_fallback)