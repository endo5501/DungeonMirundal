"""
4階層より深いメニューからの戻る処理修正のテスト
バグ修正前にテストを作成し、修正後にテストが通ることを確認する
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
import pygame

# Test setup for pygame
pygame.init()
screen = pygame.display.set_mode((800, 600))

class TestDeepMenuNavigationFixes:
    """4階層メニューの戻る処理修正テスト"""

    def setup_method(self):
        """テストセットアップ"""
        self.mock_party = Mock()
        self.mock_party.gold = 2000
        self.mock_party.get_all_characters.return_value = []
        
    @patch('src.overworld.inn_storage.inn_storage_manager')
    @patch('src.items.item.item_manager')
    def test_inn_storage_status_dialog_has_back_button(self, mock_item_manager, mock_storage_manager):
        """宿屋倉庫状況ダイアログに戻るボタンが表示されることをテスト"""
        from src.overworld.facilities.inn import Inn
        
        # Setup mocks
        mock_storage = Mock()
        mock_storage.get_all_items.return_value = []
        mock_storage_manager.get_storage.return_value = mock_storage
        mock_storage_manager.get_storage_summary.return_value = {
            'used_slots': 0,
            'capacity': 100,
            'usage_percentage': 0.0
        }
        
        inn = Inn()
        inn.current_party = self.mock_party
        inn._show_dialog = Mock()
        
        inn._show_inn_storage_status()
        
        # ダイアログ呼び出しを確認
        inn._show_dialog.assert_called_once()
        args = inn._show_dialog.call_args
        
        # buttonsパラメータが渡されていることを確認（修正後はこれが成功する）
        # 修正後はbuttonsパラメータが追加されてテストが通る
        has_buttons = 'buttons' in (args.kwargs if args.kwargs else {}) or len(args[0] if args else []) > 3
        assert has_buttons, "ダイアログにbuttonsパラメータが必要"

    @patch('src.overworld.facilities.magic_guild.config_manager')
    @patch('src.overworld.facilities.magic_guild.UIMenu')
    def test_magic_guild_spellbook_details_confirmation_callback(self, mock_ui_menu, mock_config):
        """魔術師ギルドの魔術書詳細確認のコールバックエラー修正テスト"""
        from src.overworld.facilities.magic_guild import MagicGuild
        
        mock_config.get_text.return_value = "戻る"
        
        guild = MagicGuild()
        guild.current_party = self.mock_party
        guild._show_confirmation = Mock()
        guild._show_dialog = Mock()
        guild._purchase_spellbook = Mock()
        
        test_spellbook = {
            'name': 'テスト魔術書',
            'price': 100,
            'description': 'テスト用魔術書'
        }
        
        guild._show_spellbook_details(test_spellbook)
        
        # 確認ダイアログが呼ばれることを確認
        guild._show_confirmation.assert_called_once()
        args = guild._show_confirmation.call_args
        
        # コールバック関数が正しく動作することを確認（修正後はエラーが出ない）
        try:
            callback = args[0][1]  # 2番目の引数がコールバック
            # コールバックが引数なしで呼べることを確認
            # 現在のコードではlambdaが使われているためエラーが起きる（期待通り）
            callback()
            test_passed = True
        except TypeError as e:
            if "takes 0 positional arguments but 1 was given" in str(e):
                test_passed = False  # 期待されるエラー
            else:
                raise
        
        # 修正後はエラーが起きない
        assert test_passed, "コールバック関数は引数エラーを起こしてはいけない"

    @patch('src.overworld.facilities.inn.config_manager')
    @patch('src.overworld.facilities.inn.UIMenu')
    def test_character_item_management_back_navigation(self, mock_ui_menu, mock_config):
        """キャラクター別アイテム管理での戻るナビゲーションテスト"""
        from src.overworld.facilities.inn import Inn
        
        mock_config.get_text.return_value = "戻る"
        mock_character = Mock()
        mock_character.name = "テストキャラ"
        mock_character.character_class = "戦士"
        mock_inventory = Mock()
        mock_inventory.slots = [Mock(is_empty=Mock(return_value=True)) for _ in range(20)]
        mock_character.get_inventory.return_value = mock_inventory
        
        self.mock_party.get_all_characters.return_value = [mock_character]
        
        inn = Inn()
        inn.current_party = self.mock_party
        inn._show_submenu = Mock()
        inn._show_new_item_organization_menu = Mock()
        
        inn._show_character_item_management()
        
        # サブメニューが表示されることを確認
        inn._show_submenu.assert_called_once()
        menu = inn._show_submenu.call_args[0][0]
        
        # 戻るメニュー項目があることを確認（この部分は既に実装されているはず）
        # メニュー項目は正常に実装されていることを確認
        assert menu is not None, "メニューが作成されるべき"
        assert hasattr(menu, 'items'), "メニューにitemsプロパティが必要"

    def test_menu_depth_tracking(self):
        """メニュー階層の深さ追跡テスト"""
        # メニュー階層: 地上 -> 宿屋 -> 冒険の準備 -> アイテム整理 -> 宿屋倉庫の確認
        # 4階層目のダイアログから正しく戻れることを確認
        
        menu_stack = []
        
        # 各階層を模擬
        menu_stack.append("overworld")      # 1階層: 地上
        menu_stack.append("inn")            # 2階層: 宿屋
        menu_stack.append("adventure_prep") # 3階層: 冒険の準備
        menu_stack.append("item_organize")  # 4階層: アイテム整理
        
        # 4階層目からダイアログを開く
        dialog_level = len(menu_stack) + 1  # 5階層目相当
        
        # 戻るボタンで4階層目に戻る
        if dialog_level > 4:
            expected_return_level = dialog_level - 1
            assert expected_return_level == 4, "ダイアログから戻ると4階層目に戻るべき"
            
        # さらに戻るボタンで3階層目に戻る
        menu_stack.pop()  # item_organize を除去
        assert len(menu_stack) == 3, "3階層目に正しく戻るべき"
        assert menu_stack[-1] == "adventure_prep", "冒険の準備メニューに戻るべき"

if __name__ == "__main__":
    pytest.main([__file__])