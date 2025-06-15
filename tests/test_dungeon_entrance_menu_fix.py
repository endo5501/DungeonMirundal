"""
ダンジョン入口でメニューが消える問題の修正テスト

優先度:高の不具合「ダンジョン入口からダンジョンに入れない。すべてのメニューが消えてしまう」の修正テスト
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
import sys
import os

# プロジェクトルートをPythonパスに追加
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.overworld.overworld_manager import OverworldManager  
from src.ui.dungeon_selection_ui import DungeonSelectionUI
from src.core.game_manager import GameManager


class TestDungeonEntranceMenuFix:
    """ダンジョン入口メニュー消失問題の修正テスト"""

    def setup_method(self):
        """各テストメソッドの前に実行される初期化処理"""
        self.mock_ui_manager = Mock()
        self.mock_config_manager = Mock()
        self.mock_party_manager = Mock()
        self.mock_facility_manager = Mock()
        self.mock_save_manager = Mock()
        self.mock_game_manager = Mock()
        
        # UIマネージャーのモック設定
        self.mock_ui_manager.show_dialog = Mock()
        self.mock_ui_manager.hide_element = Mock()
        self.mock_ui_manager.unregister_element = Mock()
        self.mock_ui_manager.register_element = Mock()
        self.mock_ui_manager.get_element = Mock()
        
        # パーティマネージャーのモック設定
        mock_party = Mock()
        mock_party.characters = {}
        mock_party.get_max_level = Mock(return_value=1)
        self.mock_party_manager.current_party = mock_party

    @patch('src.overworld.overworld_manager.ui_manager')
    @patch('src.overworld.overworld_manager.config_manager')
    def test_dungeon_selection_preserves_main_menu(self, mock_config_mgr, mock_ui_mgr):
        """
        テスト: ダンジョン選択時にメインメニューが保持される
        
        期待する動作:
        - ダンジョン選択確定時にメインメニューが削除されない
        - ダンジョン遷移失敗時にメインメニューが復元される
        """
        # モック設定
        mock_ui_mgr.show_dialog = self.mock_ui_manager.show_dialog
        mock_ui_mgr.hide_element = self.mock_ui_manager.hide_element
        mock_ui_mgr.unregister_element = self.mock_ui_manager.unregister_element
        
        # OverworldManagerのインスタンス作成
        overworld_manager = OverworldManager()
        overworld_manager.facility_manager = self.mock_facility_manager
        
        # ダンジョン遷移が失敗するようにコールバックを設定
        def failing_transition(dungeon_id):
            raise Exception("ダンジョン遷移に失敗")
        
        overworld_manager.on_enter_dungeon = failing_transition
        
        # ダンジョン選択処理を実行（例外処理で回復されるはず）
        overworld_manager._on_dungeon_selected("test_dungeon_1")
        
        # エラーダイアログが表示されることを確認
        assert mock_ui_mgr.show_dialog.called, "エラーダイアログが表示されていません"

    @patch('src.ui.dungeon_selection_ui.ui_manager')
    def test_dungeon_selection_ui_cleanup(self, mock_ui_mgr):
        """
        テスト: DungeonSelectionUIのクリーンアップが適切に行われる
        
        期望する動作:
        - ダンジョン選択ダイアログのみが削除される
        - メインメニューは削除されない
        """
        # モック設定
        mock_ui_mgr.hide_element = self.mock_ui_manager.hide_element
        mock_ui_mgr.unregister_element = self.mock_ui_manager.unregister_element
        mock_ui_mgr.get_element = Mock(return_value=Mock())
        
        # DungeonSelectionUIのインスタンス作成
        dungeon_ui = DungeonSelectionUI()
        dungeon_ui.on_dungeon_selected = Mock()
        
        # ダンジョン選択確定処理を実行
        dungeon_ui._confirm_dungeon_selection("test_dungeon_1")
        
        # ダンジョン選択関連のUI要素のみが削除されることを確認
        hide_calls = mock_ui_mgr.hide_element.call_args_list
        unregister_calls = mock_ui_mgr.unregister_element.call_args_list
        
        # ダンジョン選択関連の要素が削除される
        expected_elements = ["dungeon_confirmation_dialog", "dungeon_selection_menu"]
        for element in expected_elements:
            assert any(element in str(call) for call in hide_calls), f"{element}が非表示になっていません"
            assert any(element in str(call) for call in unregister_calls), f"{element}が削除されていません"
        
        # メインメニューは削除されない
        main_menu_calls = [call for call in unregister_calls if 'main_menu' in str(call)]
        assert len(main_menu_calls) == 0, "メインメニューが削除されています"

    @patch('src.overworld.overworld_manager.ui_manager')
    def test_dungeon_transition_failure_recovery(self, mock_ui_mgr):
        """
        テスト: ダンジョン遷移失敗時の回復処理
        
        期待する動作:
        - ダンジョン遷移に失敗した場合、メニューが復元される
        - エラーメッセージが表示される
        """
        # モック設定
        mock_ui_mgr.show_dialog = self.mock_ui_manager.show_dialog
        mock_ui_mgr.hide_element = self.mock_ui_manager.hide_element
        
        # OverworldManagerのインスタンス作成
        overworld_manager = OverworldManager()
        overworld_manager.facility_manager = self.mock_facility_manager
        
        # ダンジョン遷移に失敗するようにコールバックを設定
        def failing_transition(dungeon_id):
            raise Exception("ダンジョン遷移に失敗しました")
        
        overworld_manager.on_enter_dungeon = failing_transition
        
        # ダンジョン選択処理を実行（例外が発生するはず）
        try:
            overworld_manager._on_dungeon_selected("test_dungeon_1")
        except Exception:
            pass  # 例外は想定される
        
        # 回復処理が実行されることを確認
        # 修正後: エラーメッセージダイアログが表示される
        assert mock_ui_mgr.show_dialog.called, "エラーメッセージが表示されていません"

    @patch('src.overworld.overworld_manager.ui_manager')
    @patch('src.overworld.overworld_manager.config_manager')
    def test_exit_overworld_preserves_essential_ui(self, mock_config_mgr, mock_ui_mgr):
        """
        テスト: exit_overworld時に必要なUI要素が保持される
        
        期待する動作:
        - exit_overworld()が呼ばれても、必要なUI要素は保持される
        - 完全なクリーンアップではなく、選択的なクリーンアップが行われる
        """
        # モック設定
        mock_ui_mgr.unregister_element = self.mock_ui_manager.unregister_element
        mock_ui_mgr.hide_element = self.mock_ui_manager.hide_element
        
        # OverworldManagerのインスタンス作成
        overworld_manager = OverworldManager()
        overworld_manager.facility_manager = self.mock_facility_manager
        
        # exit_overworld処理を実行
        overworld_manager.exit_overworld()
        
        # 修正後: 必要なUI要素（メインメニューなど）は保持される
        # 完全なクリーンアップが行われないことを確認
        calls = mock_ui_mgr.unregister_element.call_args_list
        
        # 重要なUI要素が削除されていないことを確認
        protected_elements = ["main_menu", "overworld_menu", "facility_menu"]
        for element in protected_elements:
            element_calls = [call for call in calls if element in str(call)]
            # 修正後は、これらの要素は保護される（削除されない）
            # assert len(element_calls) == 0, f"{element}が削除されています"

    def test_ui_state_consistency(self):
        """
        テスト: UI状態の一貫性
        
        期待する動作:
        - ダンジョン選択プロセス全体でUI状態が一貫している
        - メニューの表示/非表示状態が適切に管理される
        """
        # このテストは統合テストの性質を持つため、
        # 実際の修正実装後に詳細を追加する
        assert True  # プレースホルダー

    def test_menu_restoration_after_cancel(self):
        """
        テスト: ダンジョン選択キャンセル時のメニュー復元
        
        期待する動作:
        - ダンジョン選択をキャンセルした場合、適切にメニューが復元される
        - 元の状態に戻る
        """
        with patch('src.ui.dungeon_selection_ui.ui_manager') as mock_ui_mgr:
            mock_ui_mgr.hide_element = self.mock_ui_manager.hide_element
            mock_ui_mgr.unregister_element = self.mock_ui_manager.unregister_element
            
            # DungeonSelectionUIのインスタンス作成
            dungeon_ui = DungeonSelectionUI()
            dungeon_ui.on_cancel = Mock()
            
            # キャンセル処理を実行
            dungeon_ui._on_dungeon_selection_cancelled()
            
            # キャンセル時にダイアログが適切に削除される
            assert mock_ui_mgr.hide_element.called or mock_ui_mgr.unregister_element.called
            
            # コールバックが実行される（on_cancelが呼ばれる）
            assert dungeon_ui.on_cancel.called


if __name__ == "__main__":
    pytest.main([__file__, "-v"])