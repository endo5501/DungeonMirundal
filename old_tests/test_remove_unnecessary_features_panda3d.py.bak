"""
不要な機能の削除のテスト

change_spec.mdの要求：
- 宿屋の[宿泊について]は不要です。代わりに、ダンジョンから戻った際「無事町に戻り、治療を受けた」というメッセージを出せばよいです。
- 教会の[治療サービス]は不要です

に対応するテスト
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
import sys
import os

# プロジェクトルートをPythonパスに追加
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.overworld.facilities.inn import Inn
from src.overworld.facilities.temple import Temple
from src.character.party import Party


class TestRemoveUnnecessaryFeatures:
    """不要な機能の削除テスト"""

    def setup_method(self):
        """各テストメソッドの前に実行される初期化処理"""
        self.mock_ui_manager = Mock()
        self.mock_config_manager = Mock()
        
        # UIマネージャーのモック設定
        self.mock_ui_manager.register_element = Mock()
        self.mock_ui_manager.show_element = Mock()
        self.mock_ui_manager.hide_element = Mock()
        self.mock_ui_manager.get_text = Mock(side_effect=lambda key, default="": {
            "facility.inn": "宿屋",
            "facility.temple": "教会",
            "common.ok": "OK",
            "common.cancel": "キャンセル",
            "menu.exit": "出る"
        }.get(key, default))
        
        # テスト用パーティを作成
        self.test_party = Mock()
        self.test_party.name = "テストパーティ"
        self.test_party.gold = 1000
        self.test_party.party_id = "test_party_001"

    @patch('src.overworld.base_facility.ui_manager')
    @patch('src.overworld.base_facility.config_manager')
    def test_inn_no_longer_has_lodging_info_menu(self, mock_config_mgr, mock_ui_mgr):
        """
        テスト: 宿屋メニューに「宿泊について」項目が存在しない
        
        期待する動作:
        - 宿屋メニューに「宿泊について」オプションが存在しない
        - 削除された機能にアクセスできない
        """
        # モック設定
        mock_ui_mgr.register_element = self.mock_ui_manager.register_element
        mock_ui_mgr.show_element = self.mock_ui_manager.show_element
        mock_config_mgr.get_text = self.mock_ui_manager.get_text
        
        # 宿屋インスタンス作成
        inn = Inn()
        inn.current_party = self.test_party
        
        # メインメニューを表示
        inn._show_main_menu()
        
        # メニューが登録されることを確認
        assert mock_ui_mgr.register_element.called, "宿屋メニューが登録されていません"
        
        # 登録されたメニューを取得
        register_call = mock_ui_mgr.register_element.call_args
        menu_obj = register_call[0][0]
        
        # 宿泊についてメニュー項目が存在しないことを確認
        menu_texts = [item['text'] for item in menu_obj.menu_items]
        assert not any("宿泊について" in text for text in menu_texts), \
            f"宿泊についてメニュー項目が残っています: {menu_texts}"

    @patch('src.overworld.base_facility.ui_manager')
    @patch('src.overworld.base_facility.config_manager')
    def test_temple_no_longer_has_healing_service_menu(self, mock_config_mgr, mock_ui_mgr):
        """
        テスト: 教会メニューに「治療サービス」項目が存在しない
        
        期待する動作:
        - 教会メニューに「治療サービス」オプションが存在しない
        - 削除された機能にアクセスできない
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
        
        # 治療サービスメニュー項目が存在しないことを確認
        menu_texts = [item['text'] for item in menu_obj.menu_items]
        assert not any("治療サービス" in text for text in menu_texts), \
            f"治療サービスメニュー項目が残っています: {menu_texts}"

    def test_inn_lodging_info_method_removed(self):
        """
        テスト: 宿屋から宿泊情報表示メソッドが削除されている
        
        期待する動作:
        - _show_lodging_info メソッドが存在しない
        - 削除されたメソッドにアクセスできない
        """
        inn = Inn()
        
        # _show_lodging_info メソッドが存在しないことを確認
        assert not hasattr(inn, '_show_lodging_info'), \
            "宿屋に_show_lodging_infoメソッドが残っています"

    def test_temple_healing_methods_removed(self):
        """
        テスト: 教会から治療関連メソッドが削除されている
        
        期待する動作:
        - _show_healing_menu メソッドが存在しない
        - _heal_character メソッドが存在しない
        - _perform_healing メソッドが存在しない
        """
        temple = Temple()
        
        # 治療関連メソッドが存在しないことを確認
        assert not hasattr(temple, '_show_healing_menu'), \
            "教会に_show_healing_menuメソッドが残っています"
        assert not hasattr(temple, '_heal_character'), \
            "教会に_heal_characterメソッドが残っています"
        assert not hasattr(temple, '_perform_healing'), \
            "教会に_perform_healingメソッドが残っています"

    def test_temple_service_costs_updated(self):
        """
        テスト: 教会のサービス料金から治療関連項目が削除されている
        
        期待する動作:
        - service_costs に 'status_heal' キーが存在しない
        - 他の必要なサービス料金は残っている
        """
        temple = Temple()
        
        # 治療関連の料金設定が削除されていることを確認
        assert 'status_heal' not in temple.service_costs, \
            "治療サービスの料金設定が残っています"
        
        # 必要なサービス料金は残っていることを確認
        assert 'resurrection' in temple.service_costs, \
            "蘇生サービスの料金設定が削除されています"
        assert 'ash_restoration' in temple.service_costs, \
            "灰化復活サービスの料金設定が削除されています"
        assert 'blessing' in temple.service_costs, \
            "祝福サービスの料金設定が削除されています"

    @patch('src.overworld.base_facility.ui_manager')
    @patch('src.overworld.base_facility.config_manager')
    def test_inn_still_has_essential_functions(self, mock_config_mgr, mock_ui_mgr):
        """
        テスト: 宿屋の必要な機能は残っている
        
        期待する動作:
        - 宿屋の主人と話す機能が残っている
        - 旅の情報を聞く機能が残っている
        - 酒場の噂話機能が残っている
        - パーティ名変更機能が残っている
        """
        # モック設定
        mock_ui_mgr.register_element = self.mock_ui_manager.register_element
        mock_ui_mgr.show_element = self.mock_ui_manager.show_element
        mock_config_mgr.get_text = self.mock_ui_manager.get_text
        
        # 宿屋インスタンス作成
        inn = Inn()
        inn.current_party = self.test_party
        
        # メインメニューを表示
        inn._show_main_menu()
        
        # 登録されたメニューを取得
        register_call = mock_ui_mgr.register_element.call_args
        menu_obj = register_call[0][0]
        menu_texts = [item['text'] for item in menu_obj.menu_items]
        
        # 必要な機能が残っていることを確認
        assert any("宿屋の主人と話す" in text for text in menu_texts), \
            f"宿屋の主人と話す機能が削除されています: {menu_texts}"
        assert any("旅の情報を聞く" in text for text in menu_texts), \
            f"旅の情報を聞く機能が削除されています: {menu_texts}"
        assert any("酒場の噂話" in text for text in menu_texts), \
            f"酒場の噂話機能が削除されています: {menu_texts}"
        assert any("パーティ名を変更" in text for text in menu_texts), \
            f"パーティ名変更機能が削除されています: {menu_texts}"

    @patch('src.overworld.base_facility.ui_manager')
    @patch('src.overworld.base_facility.config_manager')
    def test_temple_still_has_essential_functions(self, mock_config_mgr, mock_ui_mgr):
        """
        テスト: 教会の必要な機能は残っている
        
        期待する動作:
        - 蘇生サービス機能が残っている
        - 祝福サービス機能が残っている
        - 神父と話す機能が残っている
        - 祈祷書購入機能が残っている
        - 寄付をする機能が残っている
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
        
        # 登録されたメニューを取得
        register_call = mock_ui_mgr.register_element.call_args
        menu_obj = register_call[0][0]
        menu_texts = [item['text'] for item in menu_obj.menu_items]
        
        # 必要な機能が残っていることを確認
        assert any("蘇生サービス" in text for text in menu_texts), \
            f"蘇生サービス機能が削除されています: {menu_texts}"
        assert any("祝福サービス" in text for text in menu_texts), \
            f"祝福サービス機能が削除されています: {menu_texts}"
        assert any("神父と話す" in text for text in menu_texts), \
            f"神父と話す機能が削除されています: {menu_texts}"
        assert any("祈祷書購入" in text for text in menu_texts), \
            f"祈祷書購入機能が削除されています: {menu_texts}"
        assert any("寄付をする" in text for text in menu_texts), \
            f"寄付をする機能が削除されています: {menu_texts}"

    def test_inn_methods_cleanup(self):
        """
        テスト: 宿屋の削除されたメソッドが実際に存在しない
        
        期待する動作:
        - 削除対象のメソッドが完全に削除されている
        - メソッド呼び出しでエラーが発生しない
        """
        inn = Inn()
        
        # 削除されたメソッドのリスト
        removed_methods = ['_show_lodging_info']
        
        for method_name in removed_methods:
            assert not hasattr(inn, method_name), \
                f"削除対象のメソッド {method_name} が残っています"

    def test_temple_methods_cleanup(self):
        """
        テスト: 教会の削除されたメソッドが実際に存在しない
        
        期待する動作:
        - 削除対象のメソッドが完全に削除されている
        - メソッド呼び出しでエラーが発生しない
        """
        temple = Temple()
        
        # 削除されたメソッドのリスト
        removed_methods = ['_show_healing_menu', '_heal_character', '_perform_healing']
        
        for method_name in removed_methods:
            assert not hasattr(temple, method_name), \
                f"削除対象のメソッド {method_name} が残っています"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])