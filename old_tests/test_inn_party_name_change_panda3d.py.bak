"""
宿屋のパーティ名変更機能のテスト

change_spec.mdの要求「宿屋にて、パーティ名を変更する機能を追加してほしい」に対応するテスト
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
import sys
import os

# プロジェクトルートをPythonパスに追加
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.overworld.facilities.inn import Inn
from src.character.party import Party
from src.character.character import Character
from src.ui.base_ui import UIMenu, UIInputDialog


class TestInnPartyNameChange:
    """宿屋のパーティ名変更機能テスト"""

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
            "common.ok": "OK",
            "common.cancel": "キャンセル",
            "menu.exit": "出る"
        }.get(key, default))
        
        # テスト用パーティを作成
        self.test_party = Mock()
        self.test_party.name = "初期パーティ名"
        self.test_party.party_id = "test_party_001"

    @patch('src.overworld.base_facility.ui_manager')
    @patch('src.overworld.base_facility.config_manager')
    def test_inn_has_party_name_change_menu_item(self, mock_config_mgr, mock_ui_mgr):
        """
        テスト: 宿屋のメニューにパーティ名変更項目が追加される
        
        期待する動作:
        - 宿屋メニューに「パーティ名を変更」オプションが存在
        - メニュー項目が正しく機能する
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
        
        # パーティ名変更メニュー項目が存在することを確認
        menu_texts = [item['text'] for item in menu_obj.menu_items]
        assert any("パーティ名" in text for text in menu_texts), \
            f"パーティ名変更メニュー項目が見つかりません: {menu_texts}"

    @patch('src.overworld.facilities.inn.ui_manager')
    @patch('src.overworld.base_facility.config_manager')
    def test_party_name_change_dialog_creation(self, mock_config_mgr, mock_ui_mgr):
        """
        テスト: パーティ名変更ダイアログが正しく作成される
        
        期待する動作:
        - パーティ名変更選択時にUIInputDialogが作成される
        - 現在のパーティ名が初期値として設定される
        - 適切なコールバック関数が設定される
        """
        # モック設定
        mock_ui_mgr.register_element = self.mock_ui_manager.register_element
        mock_ui_mgr.show_element = self.mock_ui_manager.show_element
        mock_config_mgr.get_text = self.mock_ui_manager.get_text
        
        # 宿屋インスタンス作成
        inn = Inn()
        inn.current_party = self.test_party
        
        # パーティ名変更機能を呼び出し
        inn._change_party_name()
        
        # UIInputDialogが登録されることを確認
        assert mock_ui_mgr.register_element.called, "パーティ名変更ダイアログが登録されていません"
        
        # 登録されたダイアログを取得
        register_call = mock_ui_mgr.register_element.call_args
        dialog_obj = register_call[0][0]
        
        # UIInputDialogのインスタンスであることを確認
        assert hasattr(dialog_obj, 'text_input'), "UIInputDialogが作成されていません"
        assert hasattr(dialog_obj, 'on_confirm'), "確認コールバックが設定されていません"

    @patch('src.overworld.facilities.inn.ui_manager')
    @patch('src.overworld.base_facility.config_manager')
    def test_party_name_change_execution(self, mock_config_mgr, mock_ui_mgr):
        """
        テスト: パーティ名変更が正しく実行される
        
        期待する動作:
        - 新しい名前が入力された時にパーティ名が更新される
        - 空の名前や無効な名前は適切に処理される
        - 成功メッセージが表示される
        """
        # モック設定
        mock_ui_mgr.register_element = self.mock_ui_manager.register_element
        mock_ui_mgr.show_element = self.mock_ui_manager.show_element
        mock_ui_mgr.hide_element = self.mock_ui_manager.hide_element
        mock_ui_mgr.unregister_element = Mock()
        mock_config_mgr.get_text = self.mock_ui_manager.get_text
        
        # 宿屋インスタンス作成
        inn = Inn()
        inn.current_party = self.test_party
        
        # パーティ名変更の確認処理をテスト
        original_name = self.test_party.name
        new_name = "新しいパーティ名"
        
        # パーティ名変更実行
        inn._on_party_name_confirmed(new_name)
        
        # パーティ名が更新されることを確認
        assert self.test_party.name == new_name, f"パーティ名が更新されていません: {self.test_party.name}"

    @patch('src.overworld.facilities.inn.ui_manager')
    @patch('src.overworld.base_facility.config_manager')
    def test_party_name_validation(self, mock_config_mgr, mock_ui_mgr):
        """
        テスト: パーティ名の検証が正しく行われる
        
        期待する動作:
        - 空の名前は適切なデフォルト名に設定される
        - 長すぎる名前は適切に切り詰められる
        - 無効な文字は適切に処理される
        """
        # モック設定
        mock_ui_mgr.register_element = self.mock_ui_manager.register_element
        mock_ui_mgr.show_element = self.mock_ui_manager.show_element
        mock_ui_mgr.hide_element = self.mock_ui_manager.hide_element
        mock_ui_mgr.unregister_element = Mock()
        mock_config_mgr.get_text = self.mock_ui_manager.get_text
        
        # 宿屋インスタンス作成
        inn = Inn()
        inn.current_party = self.test_party
        
        # 空の名前のテスト
        inn._on_party_name_confirmed("")
        assert self.test_party.name != "", "空の名前が適切に処理されていません"
        
        # 長すぎる名前のテスト
        long_name = "とても長いパーティ名" * 10  # 非常に長い名前
        inn._on_party_name_confirmed(long_name)
        assert len(self.test_party.name) <= 30, f"名前が長すぎます: {len(self.test_party.name)}文字"

    @patch('src.overworld.facilities.inn.ui_manager')
    @patch('src.overworld.base_facility.config_manager')
    def test_party_name_change_cancel(self, mock_config_mgr, mock_ui_mgr):
        """
        テスト: パーティ名変更のキャンセル処理
        
        期待する動作:
        - キャンセル時にパーティ名が変更されない
        - ダイアログが適切に閉じられる
        - 元のメニューに戻る
        """
        # モック設定
        mock_ui_mgr.register_element = self.mock_ui_manager.register_element
        mock_ui_mgr.show_element = self.mock_ui_manager.show_element
        mock_ui_mgr.hide_element = self.mock_ui_manager.hide_element
        mock_ui_mgr.unregister_element = Mock()
        mock_config_mgr.get_text = self.mock_ui_manager.get_text
        
        # 宿屋インスタンス作成
        inn = Inn()
        inn.current_party = self.test_party
        
        # 元の名前を保存
        original_name = self.test_party.name
        
        # キャンセル処理を実行
        inn._on_party_name_cancelled()
        
        # パーティ名が変更されていないことを確認
        assert self.test_party.name == original_name, "キャンセル時にパーティ名が変更されています"
        
        # ダイアログが適切に閉じられることを確認
        assert mock_ui_mgr.hide_element.called, "ダイアログが閉じられていません"

    @patch('src.overworld.facilities.inn.ui_manager')
    @patch('src.overworld.base_facility.config_manager')
    def test_party_name_change_success_message(self, mock_config_mgr, mock_ui_mgr):
        """
        テスト: パーティ名変更成功時のメッセージ表示
        
        期待する動作:
        - 名前変更成功時に適切なメッセージが表示される
        - メッセージに新しいパーティ名が含まれる
        """
        # モック設定
        mock_ui_mgr.register_element = self.mock_ui_manager.register_element
        mock_ui_mgr.show_element = self.mock_ui_manager.show_element
        mock_config_mgr.get_text = self.mock_ui_manager.get_text
        
        # 宿屋インスタンス作成
        inn = Inn()
        inn.current_party = self.test_party
        inn._show_dialog = Mock()  # ダイアログ表示をモック
        
        new_name = "勇者一行"
        
        # パーティ名変更実行
        inn._on_party_name_confirmed(new_name)
        
        # 成功メッセージダイアログが表示されることを確認
        assert inn._show_dialog.called, "成功メッセージが表示されていません"
        
        # ダイアログの内容を確認
        dialog_call = inn._show_dialog.call_args
        message = dialog_call[0][2]  # メッセージ部分
        assert new_name in message, f"成功メッセージに新しいパーティ名が含まれていません: {message}"

    def test_party_name_change_without_party(self):
        """
        テスト: パーティが存在しない場合の処理
        
        期待する動作:
        - パーティが存在しない場合はエラーメッセージを表示
        - 機能が適切に無効化される
        """
        with patch('src.overworld.facilities.inn.ui_manager') as mock_ui_mgr:
            # モック設定
            mock_ui_mgr.register_element = self.mock_ui_manager.register_element
            mock_ui_mgr.show_element = self.mock_ui_manager.show_element
            
            # 宿屋インスタンス作成（パーティなし）
            inn = Inn()
            inn.current_party = None
            inn._show_dialog = Mock()
            
            # パーティ名変更を試行
            inn._change_party_name()
            
            # エラーメッセージが表示されることを確認
            assert inn._show_dialog.called, "エラーメッセージが表示されていません"
            
            # エラーダイアログの内容確認
            dialog_call = inn._show_dialog.call_args
            message = dialog_call[0][2]  # メッセージ部分
            assert "パーティ" in message, f"適切なエラーメッセージが表示されていません: {message}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])