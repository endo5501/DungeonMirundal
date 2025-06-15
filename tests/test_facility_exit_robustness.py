"""施設退場時のロバストネステスト"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from src.overworld.overworld_manager import OverworldManager
from src.overworld.base_facility import FacilityManager, BaseFacility, FacilityType
from src.character.party import Party


class MockFacility(BaseFacility):
    """テスト用モック施設"""
    
    def __init__(self, facility_id: str = "test_facility"):
        super().__init__(facility_id, FacilityType.INN, "facility.inn")
    
    def _setup_menu_items(self, menu):
        pass
    
    def _on_enter(self):
        pass
    
    def _on_exit(self):
        pass


class TestFacilityExitRobustness:
    """施設退場時のロバストネステストクラス"""
    
    def setup_method(self):
        """各テストメソッドの前に実行"""
        with patch('src.overworld.overworld_manager.ui_manager'):
            self.overworld_manager = OverworldManager()
        
        # モックパーティの作成
        self.test_party = Mock(spec=Party)
        self.test_party.name = "テストパーティ"
        
        # モック施設とマネージャーの作成
        self.mock_facility = MockFacility("test_inn")
        self.facility_manager = FacilityManager()
        self.facility_manager.register_facility(self.mock_facility)
        
        # オーバーワールドマネージャーに施設マネージャーを設定
        self.overworld_manager.facility_manager = self.facility_manager
        self.facility_manager.set_facility_exit_callback(self.overworld_manager.on_facility_exit)
        
        # 地上部をアクティブにする
        self.overworld_manager.is_active = True
        self.overworld_manager.current_party = self.test_party
    
    def test_facility_exit_with_ui_manager_inconsistency(self):
        """UIManagerとオブジェクトの状態不整合時のテスト"""
        with patch('src.overworld.overworld_manager.ui_manager') as mock_ui:
            # メインメニューオブジェクトは存在するがUIManagerには登録されていない状況
            self.overworld_manager.main_menu = Mock()
            self.overworld_manager.main_menu.element_id = "main_menu"
            
            # get_elementは最初にNoneを返し（未登録状態）、
            # その後_show_main_menuが呼ばれた後は新しいオブジェクトを返す
            mock_ui.get_element.side_effect = [None, Mock()]  # 1回目None、2回目はオブジェクト
            
            # _show_main_menuをモック化
            with patch.object(self.overworld_manager, '_show_main_menu') as mock_show_main:
                # 施設退場
                self.overworld_manager.on_facility_exit()
                
                # メインメニューが再生成されることを確認
                mock_show_main.assert_called_once()
    
    def test_facility_exit_with_show_element_failure(self):
        """show_element呼び出しが失敗する場合のテスト"""
        with patch('src.overworld.overworld_manager.ui_manager') as mock_ui:
            # メインメニューを設定
            self.overworld_manager.main_menu = Mock()
            self.overworld_manager.main_menu.element_id = "main_menu"
            
            # get_elementは成功するがshow_elementが失敗
            mock_ui.get_element.return_value = Mock()
            mock_ui.show_element.side_effect = Exception("表示エラー")
            
            # _show_main_menuをモック化
            with patch.object(self.overworld_manager, '_show_main_menu') as mock_show_main:
                # 施設退場
                self.overworld_manager.on_facility_exit()
                
                # 表示に失敗した後、メニューが再生成されることを確認
                mock_show_main.assert_called_once()
    
    def test_facility_exit_complete_failure_triggers_emergency(self):
        """全ての復元処理が失敗した場合の緊急処理テスト"""
        with patch('src.overworld.overworld_manager.ui_manager') as mock_ui:
            # 全ての操作を失敗させる
            mock_ui.get_element.return_value = None
            
            # _show_main_menuも失敗させる
            with patch.object(self.overworld_manager, '_show_main_menu', side_effect=Exception("再生成失敗")):
                # 緊急回復をモック化
                with patch.object(self.overworld_manager, '_emergency_menu_recovery') as mock_emergency:
                    # 施設退場
                    self.overworld_manager.on_facility_exit()
                    
                    # 緊急回復処理が呼ばれることを確認
                    mock_emergency.assert_called_once()
    
    def test_facility_exit_settings_menu_corruption_recovery(self):
        """設定メニュー破損時の回復テスト"""
        with patch('src.overworld.overworld_manager.ui_manager') as mock_ui:
            # 設定メニューがアクティブだが破損している状況
            self.overworld_manager.settings_menu_active = True
            self.overworld_manager.location_menu = Mock()
            self.overworld_manager.location_menu.element_id = "settings_menu"
            
            # 設定メニューは見つからないが、メインメニューは正常
            self.overworld_manager.main_menu = Mock()
            self.overworld_manager.main_menu.element_id = "main_menu"
            
            # 設定メニューは見つからず、メインメニューは見つかる
            mock_ui.get_element.side_effect = lambda element_id: \
                None if element_id == "settings_menu" else Mock()
            
            # 施設退場
            self.overworld_manager.on_facility_exit()
            
            # 設定メニュー状態がリセットされることを確認
            assert self.overworld_manager.settings_menu_active == False
            assert self.overworld_manager.location_menu is None
            
            # メインメニューが表示されることを確認
            mock_ui.show_element.assert_called_with("main_menu")
    
    def test_facility_exit_menu_restoration_flag_tracking(self):
        """メニュー復元フラグの追跡テスト"""
        with patch('src.overworld.overworld_manager.ui_manager') as mock_ui:
            # 正常なメインメニューを設定
            self.overworld_manager.main_menu = Mock()
            self.overworld_manager.main_menu.element_id = "main_menu"
            mock_ui.get_element.return_value = Mock()
            
            # _show_main_menuをモック化（呼ばれないことを確認するため）
            with patch.object(self.overworld_manager, '_show_main_menu') as mock_show_main:
                # 施設退場
                self.overworld_manager.on_facility_exit()
                
                # メインメニューが正常に表示される場合、再生成は不要
                mock_show_main.assert_not_called()
                mock_ui.show_element.assert_called_with("main_menu")
    
    def test_facility_enter_with_ui_state_checking(self):
        """施設入場時のUI状態チェックテスト"""
        with patch('src.overworld.overworld_manager.ui_manager') as mock_ui:
            # メインメニューを設定
            self.overworld_manager.main_menu = Mock()
            self.overworld_manager.main_menu.element_id = "main_menu"
            
            # UIManagerに正常に登録されている状況
            mock_ui.get_element.return_value = Mock()
            
            # 施設入場処理
            self.overworld_manager._enter_facility("test_inn")
            
            # メインメニューが適切に隠されることを確認
            mock_ui.hide_element.assert_called_with("main_menu")
    
    def test_facility_enter_with_missing_main_menu(self):
        """メインメニューが見つからない状態での施設入場テスト"""
        with patch('src.overworld.overworld_manager.ui_manager') as mock_ui:
            # メインメニューオブジェクトは存在するがUIManagerには未登録
            self.overworld_manager.main_menu = Mock()
            self.overworld_manager.main_menu.element_id = "main_menu"
            mock_ui.get_element.return_value = None
            
            # 施設入場処理
            self.overworld_manager._enter_facility("test_inn")
            
            # hide_elementは呼ばれないことを確認（存在しないため）
            mock_ui.hide_element.assert_not_called()
    
    def test_facility_enter_with_hide_element_failure(self):
        """hide_element失敗時の施設入場テスト"""
        with patch('src.overworld.overworld_manager.ui_manager') as mock_ui:
            # メインメニューを設定
            self.overworld_manager.main_menu = Mock()
            self.overworld_manager.main_menu.element_id = "main_menu"
            
            # get_elementは成功するがhide_elementが失敗
            mock_ui.get_element.return_value = Mock()
            mock_ui.hide_element.side_effect = Exception("非表示エラー")
            
            # 施設入場処理（エラーが発生しても処理は継続する）
            self.overworld_manager._enter_facility("test_inn")
            
            # エラーが発生してもhide_elementが呼ばれることを確認
            mock_ui.hide_element.assert_called_with("main_menu")