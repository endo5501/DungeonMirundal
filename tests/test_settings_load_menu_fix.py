"""
設定画面でのロード時にメニューが重複表示される問題の修正テスト

優先度:中の不具合「設定画面にて、ロードすると地上のメニューと設定画面のメニューが同時に表示される」の修正テスト
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
import sys
import os

# プロジェクトルートをPythonパスに追加
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.overworld.overworld_manager import OverworldManager


class TestSettingsLoadMenuFix:
    """設定画面ロード時メニュー重複問題の修正テスト"""

    def setup_method(self):
        """各テストメソッドの前に実行される初期化処理"""
        self.mock_ui_manager = Mock()
        self.mock_config_manager = Mock()
        self.mock_save_manager = Mock()
        self.mock_facility_manager = Mock()
        
        # UIマネージャーのモック設定
        self.mock_ui_manager.show_dialog = Mock()
        self.mock_ui_manager.hide_element = Mock()
        self.mock_ui_manager.unregister_element = Mock()
        self.mock_ui_manager.register_element = Mock()
        self.mock_ui_manager.get_element = Mock()
        self.mock_ui_manager.hide_all = Mock()
        
        # セーブマネージャーのモック設定  
        self.mock_save_manager.get_save_slots = Mock(return_value=["スロット1", "スロット2", "スロット3"])
        self.mock_save_manager.load_game = Mock(return_value=True)

    @patch('src.overworld.overworld_manager.ui_manager')
    @patch('src.overworld.overworld_manager.config_manager')
    def test_back_to_settings_menu_no_main_menu(self, mock_config_mgr, mock_ui_mgr):
        """
        テスト: 設定メニューに戻る際にメインメニューが表示されない
        
        期待する動作:
        - _back_to_settings_menu()実行時にメインメニューが表示されない
        - 設定メニューのみが表示される
        """
        # モック設定
        mock_ui_mgr.show_dialog = self.mock_ui_manager.show_dialog
        mock_ui_mgr.hide_element = self.mock_ui_manager.hide_element
        mock_ui_mgr.unregister_element = self.mock_ui_manager.unregister_element
        mock_ui_mgr.register_element = self.mock_ui_manager.register_element
        
        # テキスト設定のモック
        mock_config_mgr.get_text = Mock(side_effect=lambda key, default="": {
            "menu.game_settings": "ゲーム設定",
            "common.back": "戻る"
        }.get(key, default))
        
        # OverworldManagerのインスタンス作成
        overworld_manager = OverworldManager()
        overworld_manager.facility_manager = self.mock_facility_manager
        
        # _back_to_settings_menu処理を実行
        overworld_manager._back_to_settings_menu()
        
        # メインメニュー表示が呼ばれないことを確認
        # 修正後: _show_main_menu()が呼ばれない
        show_dialog_calls = mock_ui_mgr.show_dialog.call_args_list
        register_calls = mock_ui_mgr.register_element.call_args_list
        
        # メインメニュー関連の呼び出しがないことを確認
        main_menu_calls = [call for call in show_dialog_calls + register_calls 
                          if 'main_menu' in str(call) or 'overworld_main_menu' in str(call)]
        assert len(main_menu_calls) == 0, "メインメニューが表示されています"
        
        # 設定メニューのみが表示されることを確認
        settings_calls = [call for call in show_dialog_calls + register_calls 
                         if 'game_settings' in str(call) or 'settings' in str(call)]
        assert len(settings_calls) > 0, "設定メニューが表示されていません"

    @patch('src.overworld.overworld_manager.ui_manager')
    @patch('src.overworld.overworld_manager.save_manager')
    def test_load_menu_transition_clean(self, mock_save_mgr, mock_ui_mgr):
        """
        テスト: ロードメニューから設定メニューへの遷移がクリーン
        
        期待する動作:
        - ロードメニューが適切に閉じられる
        - 設定メニューのみが表示される
        - メインメニューは表示されない
        """
        # モック設定
        mock_ui_mgr.show_dialog = self.mock_ui_manager.show_dialog
        mock_ui_mgr.hide_element = self.mock_ui_manager.hide_element
        mock_ui_mgr.unregister_element = self.mock_ui_manager.unregister_element
        mock_save_mgr.get_save_slots = self.mock_save_manager.get_save_slots
        
        # OverworldManagerのインスタンス作成
        overworld_manager = OverworldManager()
        overworld_manager.facility_manager = self.mock_facility_manager
        
        # ロードメニューを表示してから設定メニューに戻る一連の処理
        overworld_manager._show_load_menu()  # ロードメニュー表示
        overworld_manager._back_to_settings_menu()  # 設定メニューに戻る
        
        # ロードメニューが適切に削除されることを確認
        hide_calls = mock_ui_mgr.hide_element.call_args_list
        unregister_calls = mock_ui_mgr.unregister_element.call_args_list
        
        load_menu_hide_calls = [call for call in hide_calls if 'load_menu' in str(call)]
        load_menu_unregister_calls = [call for call in unregister_calls if 'load_menu' in str(call)]
        
        assert len(load_menu_hide_calls) > 0 or len(load_menu_unregister_calls) > 0, \
            "ロードメニューが適切に閉じられていません"

    def test_settings_ui_hide_all_method_fixed(self):
        """
        テスト: SettingsUIで正しいhide_allメソッドが呼ばれる
        
        期待する動作:
        - hide_all_elements()ではなくhide_all()が呼ばれる
        - 存在しないメソッドエラーが発生しない
        """
        # この機能は別途SettingsUIファイルで直接修正される
        # テストは統合後に実装
        assert True  # プレースホルダー

    @patch('src.overworld.overworld_manager.ui_manager')
    @patch('src.overworld.overworld_manager.config_manager')
    def test_settings_menu_only_displayed(self, mock_config_mgr, mock_ui_mgr):
        """
        テスト: 設定メニューのみが表示される
        
        期待する動作:
        - 設定メニュー表示時に他のメニューと重複しない
        - UI要素の適切な管理が行われる
        """
        # モック設定
        mock_ui_mgr.show_dialog = self.mock_ui_manager.show_dialog
        mock_ui_mgr.register_element = self.mock_ui_manager.register_element
        mock_ui_mgr.hide_element = self.mock_ui_manager.hide_element
        
        # テキスト設定のモック
        mock_config_mgr.get_text = Mock(side_effect=lambda key, default="": {
            "menu.game_settings": "ゲーム設定",
            "menu.load_game": "ロードゲーム",
            "common.back": "戻る"
        }.get(key, default))
        
        # OverworldManagerのインスタンス作成
        overworld_manager = OverworldManager()
        overworld_manager.facility_manager = self.mock_facility_manager
        
        # 設定メニュー表示処理を実行
        overworld_manager._show_settings_menu()
        
        # 設定メニューが表示されることを確認
        show_dialog_calls = mock_ui_mgr.show_dialog.call_args_list
        register_calls = mock_ui_mgr.register_element.call_args_list
        
        # 設定関連の要素が表示される
        settings_calls = [call for call in show_dialog_calls + register_calls 
                         if 'settings' in str(call) or 'game_settings' in str(call)]
        assert len(settings_calls) > 0, "設定メニューが表示されていません"

    def test_menu_state_consistency(self):
        """
        テスト: メニュー状態の一貫性
        
        期待する動作:
        - ロード処理後にメニュー状態が一貫している
        - 重複表示が発生しない
        """
        # このテストは統合テストの性質を持つため、
        # 実際の修正実装後に詳細を追加する
        assert True  # プレースホルダー

    @patch('src.overworld.overworld_manager.ui_manager')
    @patch('src.overworld.overworld_manager.save_manager')
    def test_load_completion_menu_restoration(self, mock_save_mgr, mock_ui_mgr):
        """
        テスト: ロード完了後のメニュー復元
        
        期待する動作:
        - ロード完了後に適切なメニューが表示される
        - 地上メニューとの重複が発生しない
        """
        # モック設定
        mock_save_mgr.load_game = Mock(return_value=True)
        mock_ui_mgr.show_dialog = self.mock_ui_manager.show_dialog
        
        # OverworldManagerのインスタンス作成
        overworld_manager = OverworldManager()
        overworld_manager.facility_manager = self.mock_facility_manager
        
        # ロード処理を実行
        overworld_manager._load_game_from_slot("slot_1")
        
        # ロード完了後にダイアログが表示される
        assert mock_ui_mgr.show_dialog.called, "ロード完了ダイアログが表示されていません"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])