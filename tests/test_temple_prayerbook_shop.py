"""
教会の祈祷書購入機能のテスト

change_spec.mdの要求「教会に[祈祷書購入]というメニューを追加し、
魔術師ギルドの[魔法書購入]ではなく教会の[祈祷書購入]で販売するようにしてください」に対応するテスト
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
import sys
import os

# プロジェクトルートをPythonパスに追加
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.overworld.facilities.temple import Temple
from src.overworld.facilities.magic_guild import MagicGuild
from src.character.party import Party
from src.character.character import Character
from src.ui.base_ui import UIMenu
from src.items.item import Item, ItemType


class TestTemplePrayerbookShop:
    """教会の祈祷書購入機能テスト"""

    def setup_method(self):
        """各テストメソッドの前に実行される初期化処理"""
        self.mock_ui_manager = Mock()
        self.mock_config_manager = Mock()
        self.mock_item_manager = Mock()
        
        # UIマネージャーのモック設定
        self.mock_ui_manager.register_element = Mock()
        self.mock_ui_manager.show_element = Mock()
        self.mock_ui_manager.hide_element = Mock()
        self.mock_ui_manager.get_text = Mock(side_effect=lambda key, default="": {
            "facility.temple": "教会",
            "common.ok": "OK",
            "common.cancel": "キャンセル",
            "menu.exit": "出る",
            "menu.back": "戻る"
        }.get(key, default))
        
        # テスト用パーティを作成
        self.test_party = Mock()
        self.test_party.name = "テストパーティ"
        self.test_party.gold = 1000
        self.test_party.party_id = "test_party_001"

    @patch('src.overworld.base_facility.ui_manager')
    @patch('src.overworld.base_facility.config_manager')
    def test_temple_has_prayerbook_purchase_menu(self, mock_config_mgr, mock_ui_mgr):
        """
        テスト: 教会のメニューに祈祷書購入項目が追加される
        
        期待する動作:
        - 教会メニューに「祈祷書購入」オプションが存在
        - メニュー項目が正しく機能する
        """
        # モック設定
        mock_ui_mgr.register_element = self.mock_ui_manager.register_element
        mock_ui_mgr.show_element = self.mock_ui_manager.show_element
        mock_config_mgr.get_text = self.mock_ui_manager.get_text
        
        # 教会インスタンス作成
        temple = Temple()
        temple.current_party = self.test_party
        
        # メインメニューを表示
        temple._show_main_menu()
        
        # メニューが登録されることを確認
        assert mock_ui_mgr.register_element.called, "教会メニューが登録されていません"
        
        # 登録されたメニューを取得
        register_call = mock_ui_mgr.register_element.call_args
        menu_obj = register_call[0][0]
        
        # 祈祷書購入メニュー項目が存在することを確認
        menu_texts = [item['text'] for item in menu_obj.menu_items]
        assert any("祈祷書購入" in text for text in menu_texts), \
            f"祈祷書購入メニュー項目が見つかりません: {menu_texts}"

    @patch('src.overworld.base_facility.ui_manager')
    @patch('src.overworld.base_facility.config_manager')
    def test_magic_guild_no_longer_has_spellbook_shop(self, mock_config_mgr, mock_ui_mgr):
        """
        テスト: 魔術師ギルドから魔法書購入メニューが削除される
        
        期待する動作:
        - 魔術師ギルドメニューに「魔法書購入」オプションが存在しない
        - 祈祷書購入機能は教会のみで提供される
        """
        # モック設定
        mock_ui_mgr.register_element = self.mock_ui_manager.register_element
        mock_ui_mgr.show_element = self.mock_ui_manager.show_element
        mock_config_mgr.get_text = self.mock_ui_manager.get_text
        
        # 魔術師ギルドインスタンス作成
        magic_guild = MagicGuild()
        magic_guild.current_party = self.test_party
        
        # メインメニューを表示
        magic_guild._show_main_menu()
        
        # メニューが登録されることを確認
        assert mock_ui_mgr.register_element.called, "魔術師ギルドメニューが登録されていません"
        
        # 登録されたメニューを取得
        register_call = mock_ui_mgr.register_element.call_args
        menu_obj = register_call[0][0]
        
        # 魔法書購入メニュー項目が存在しないことを確認
        menu_texts = [item['text'] for item in menu_obj.menu_items]
        assert not any("魔法書購入" in text for text in menu_texts), \
            f"魔法書購入メニュー項目が残っています: {menu_texts}"

    @patch('src.overworld.facilities.temple.item_manager')
    @patch('src.overworld.facilities.temple.ui_manager')
    @patch('src.overworld.base_facility.config_manager')
    def test_prayerbook_shop_displays_available_items(self, mock_config_mgr, mock_ui_mgr, mock_item_mgr):
        """
        テスト: 祈祷書ショップで利用可能なアイテムが表示される
        
        期待する動作:
        - SPELLBOOKタイプのアイテムが祈祷書として表示される
        - 各アイテムの価格が表示される
        - 在庫がない場合は適切なメッセージが表示される
        """
        # モック設定
        mock_ui_mgr.register_element = self.mock_ui_manager.register_element
        mock_ui_mgr.show_element = self.mock_ui_manager.show_element
        mock_config_mgr.get_text = self.mock_ui_manager.get_text
        
        # テスト用祈祷書を作成
        test_prayerbook = Mock(spec=Item)
        test_prayerbook.get_name.return_value = "回復の祈祷書"
        test_prayerbook.price = 500
        test_prayerbook.get_description.return_value = "回復祈祷を習得できる聖なる書物"
        test_prayerbook.get_spell_id.return_value = "heal"
        
        mock_item_mgr.get_items_by_type.return_value = [test_prayerbook]
        
        # 教会インスタンス作成
        temple = Temple()
        temple.current_party = self.test_party
        
        # 祈祷書ショップを表示
        temple._show_prayerbook_shop()
        
        # SPELLBOOKタイプのアイテム取得が呼ばれることを確認
        mock_item_mgr.get_items_by_type.assert_called_with(ItemType.SPELLBOOK)
        
        # サブメニューが登録されることを確認
        assert mock_ui_mgr.register_element.called, "祈祷書ショップメニューが登録されていません"

    @patch('src.overworld.facilities.temple.item_manager')
    @patch('src.overworld.facilities.temple.ui_manager')
    @patch('src.overworld.base_facility.config_manager')
    def test_prayerbook_purchase_execution(self, mock_config_mgr, mock_ui_mgr, mock_item_mgr):
        """
        テスト: 祈祷書購入が正しく実行される
        
        期待する動作:
        - ゴールドが正しく減額される
        - 成功メッセージが表示される
        - ログが出力される
        """
        # モック設定
        mock_ui_mgr.register_element = self.mock_ui_manager.register_element
        mock_ui_mgr.show_element = self.mock_ui_manager.show_element
        mock_ui_mgr.hide_element = self.mock_ui_manager.hide_element
        mock_ui_mgr.unregister_element = Mock()
        mock_config_mgr.get_text = self.mock_ui_manager.get_text
        
        # テスト用祈祷書を作成
        test_prayerbook = Mock(spec=Item)
        test_prayerbook.get_name.return_value = "回復の祈祷書"
        test_prayerbook.price = 300
        test_prayerbook.item_id = "heal_prayerbook"
        
        # 教会インスタンス作成
        temple = Temple()
        temple.current_party = self.test_party
        temple._show_success_message = Mock()  # 成功メッセージをモック
        
        # 初期ゴールド
        initial_gold = self.test_party.gold
        
        # 祈祷書購入実行
        temple._buy_prayerbook(test_prayerbook)
        
        # ゴールドが減額されることを確認
        expected_gold = initial_gold - test_prayerbook.price
        assert self.test_party.gold == expected_gold, f"ゴールドが正しく減額されていません: {self.test_party.gold}"
        
        # 成功メッセージが表示されることを確認
        assert temple._show_success_message.called, "成功メッセージが表示されていません"

    @patch('src.overworld.facilities.temple.item_manager')
    @patch('src.overworld.facilities.temple.ui_manager')
    @patch('src.overworld.base_facility.config_manager')
    def test_prayerbook_purchase_insufficient_gold(self, mock_config_mgr, mock_ui_mgr, mock_item_mgr):
        """
        テスト: ゴールド不足時の祈祷書購入処理
        
        期待する動作:
        - ゴールド不足時は購入できない
        - 適切なエラーメッセージが表示される
        - ゴールドは減額されない
        """
        # モック設定
        mock_ui_mgr.register_element = self.mock_ui_manager.register_element
        mock_ui_mgr.show_element = self.mock_ui_manager.show_element
        mock_config_mgr.get_text = self.mock_ui_manager.get_text
        
        # テスト用祈祷書を作成（高額）
        expensive_prayerbook = Mock(spec=Item)
        expensive_prayerbook.get_name.return_value = "究極回復の祈祷書"
        expensive_prayerbook.price = 2000  # パーティの所持金を超える価格
        expensive_prayerbook.item_id = "ultimate_heal_prayerbook"
        
        # 教会インスタンス作成
        temple = Temple()
        temple.current_party = self.test_party
        temple._show_error_message = Mock()  # エラーメッセージをモック
        
        # 初期ゴールド
        initial_gold = self.test_party.gold
        
        # 祈祷書購入を試行
        temple._buy_prayerbook(expensive_prayerbook)
        
        # ゴールドが減額されていないことを確認
        assert self.test_party.gold == initial_gold, f"ゴールドが不正に減額されています: {self.test_party.gold}"
        
        # エラーメッセージが表示されることを確認
        assert temple._show_error_message.called, "エラーメッセージが表示されていません"

    @patch('src.overworld.facilities.temple.item_manager')
    @patch('src.overworld.facilities.temple.ui_manager')
    @patch('src.overworld.base_facility.config_manager')
    def test_prayerbook_shop_no_items_available(self, mock_config_mgr, mock_ui_mgr, mock_item_mgr):
        """
        テスト: 祈祷書在庫なしの場合の処理
        
        期待する動作:
        - 在庫がない場合は適切なメッセージが表示される
        - ショップメニューは表示されない
        """
        # モック設定
        mock_ui_mgr.register_element = self.mock_ui_manager.register_element
        mock_ui_mgr.show_element = self.mock_ui_manager.show_element
        mock_config_mgr.get_text = self.mock_ui_manager.get_text
        
        # 在庫なしを模擬
        mock_item_mgr.get_items_by_type.return_value = []
        
        # 教会インスタンス作成
        temple = Temple()
        temple.current_party = self.test_party
        temple._show_error_message = Mock()  # エラーメッセージをモック
        
        # 祈祷書ショップを表示
        temple._show_prayerbook_shop()
        
        # エラーメッセージが表示されることを確認
        assert temple._show_error_message.called, "在庫なしメッセージが表示されていません"
        
        # エラーメッセージの内容を確認
        error_call = temple._show_error_message.call_args
        error_message = error_call[0][0]
        assert "在庫" in error_message, f"適切な在庫なしメッセージが表示されていません: {error_message}"

    @patch('src.overworld.facilities.temple.item_manager')
    @patch('src.overworld.facilities.temple.ui_manager')
    @patch('src.overworld.base_facility.config_manager')
    def test_prayerbook_details_display(self, mock_config_mgr, mock_ui_mgr, mock_item_mgr):
        """
        テスト: 祈祷書詳細情報が正しく表示される
        
        期待する動作:
        - 祈祷書の名前、説明、価格が表示される
        - 現在のゴールド残高が表示される
        - 購入可能な場合は購入ボタンが表示される
        """
        # モック設定
        mock_ui_mgr.register_element = self.mock_ui_manager.register_element
        mock_ui_mgr.show_element = self.mock_ui_manager.show_element
        mock_config_mgr.get_text = self.mock_ui_manager.get_text
        
        # テスト用祈祷書を作成
        test_prayerbook = Mock(spec=Item)
        test_prayerbook.get_name.return_value = "光の祈祷書"
        test_prayerbook.price = 400
        test_prayerbook.get_description.return_value = "光の祈祷を習得できる神聖な書物"
        test_prayerbook.get_spell_id.return_value = "light"
        
        # 教会インスタンス作成
        temple = Temple()
        temple.current_party = self.test_party
        
        # 祈祷書詳細を表示
        temple._show_prayerbook_details(test_prayerbook)
        
        # 詳細ダイアログが登録されることを確認
        assert mock_ui_mgr.register_element.called, "祈祷書詳細ダイアログが登録されていません"
        
        # 登録されたダイアログを取得
        register_call = mock_ui_mgr.register_element.call_args
        dialog_obj = register_call[0][0]
        
        # ダイアログのメッセージに必要な情報が含まれていることを確認
        dialog_message = dialog_obj.message
        assert test_prayerbook.get_name() in dialog_message, "祈祷書名が詳細に含まれていません"
        assert str(test_prayerbook.price) in dialog_message, "価格が詳細に含まれていません"
        assert str(self.test_party.gold) in dialog_message, "現在ゴールドが詳細に含まれていません"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])