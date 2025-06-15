"""施設退場時のメニュー消失バグのテスト"""

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
        """メニュー項目設定"""
        pass
    
    def _on_enter(self):
        """入場時処理"""
        pass
    
    def _on_exit(self):
        """退場時処理"""
        pass


class TestFacilityExitBug:
    """施設退場バグのテストクラス"""
    
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
    
    def test_facility_exit_with_missing_main_menu(self):
        """メインメニューが存在しない場合の施設退場テスト"""
        with patch('src.overworld.overworld_manager.ui_manager') as mock_ui:
            # メインメニューを削除
            self.overworld_manager.main_menu = None
            
            # _show_main_menuをモック化
            with patch.object(self.overworld_manager, '_show_main_menu') as mock_show_main:
                # 施設退場
                self.overworld_manager.on_facility_exit()
                
                # メインメニューが再生成されることを確認
                mock_show_main.assert_called_once()
    
    def test_facility_exit_with_destroyed_main_menu(self):
        """メインメニューが破棄されている場合の施設退場テスト"""
        with patch('src.overworld.overworld_manager.ui_manager') as mock_ui:
            # メインメニューは存在するがUI要素は破棄済み
            self.overworld_manager.main_menu = Mock()
            self.overworld_manager.main_menu.element_id = "main_menu"
            mock_ui.get_element.return_value = None  # 要素が存在しない
            
            # _show_main_menuをモック化
            with patch.object(self.overworld_manager, '_show_main_menu') as mock_show_main:
                # 施設退場
                self.overworld_manager.on_facility_exit()
                
                # メインメニューが再生成されることを確認
                mock_show_main.assert_called_once()
    
    def test_facility_exit_with_corrupted_settings_menu(self):
        """設定メニューが破損している場合の施設退場テスト"""
        with patch('src.overworld.overworld_manager.ui_manager') as mock_ui:
            # 設定メニューが破損している状態を設定
            self.overworld_manager.settings_menu_active = True
            self.overworld_manager.location_menu = Mock()
            self.overworld_manager.location_menu.element_id = "settings_menu"
            mock_ui.get_element.return_value = None  # 設定メニューが存在しない
            
            # メインメニューを設定
            self.overworld_manager.main_menu = Mock()
            self.overworld_manager.main_menu.element_id = "main_menu"
            
            # 施設退場
            self.overworld_manager.on_facility_exit()
            
            # 設定メニュー状態がリセットされることを確認
            assert self.overworld_manager.settings_menu_active == False
            assert self.overworld_manager.location_menu is None
            
            # メインメニューが表示されることを確認（_show_main_menuが実際に呼ばれる）
            mock_ui.show_element.assert_called_with("overworld_main_menu", modal=True)
    
    def test_facility_exit_emergency_recovery(self):
        """緊急回復処理のテスト"""
        with patch('src.overworld.overworld_manager.ui_manager') as mock_ui:
            # show_elementでエラーを発生させる
            mock_ui.show_element.side_effect = Exception("UI表示エラー")
            
            # メインメニューを設定
            self.overworld_manager.main_menu = Mock()
            self.overworld_manager.main_menu.element_id = "main_menu"
            mock_ui.get_element.return_value = self.overworld_manager.main_menu
            
            # 緊急回復処理をモック化
            with patch.object(self.overworld_manager, '_emergency_menu_recovery') as mock_recovery:
                # 施設退場
                self.overworld_manager.on_facility_exit()
                
                # 緊急回復処理が呼ばれることを確認
                mock_recovery.assert_called_once()
    
    def test_emergency_menu_recovery(self):
        """緊急メニュー復元処理のテスト"""
        with patch('src.overworld.overworld_manager.ui_manager'):
            # cleanupとshow_main_menuをモック化
            with patch.object(self.overworld_manager, '_cleanup_ui') as mock_cleanup:
                with patch.object(self.overworld_manager, '_show_main_menu') as mock_show_main:
                    # 緊急回復実行
                    self.overworld_manager._emergency_menu_recovery()
                    
                    # クリーンアップとメニュー再生成が実行されることを確認
                    mock_cleanup.assert_called_once()
                    mock_show_main.assert_called_once()
                    assert self.overworld_manager.settings_menu_active == False
    
    def test_emergency_overworld_reset(self):
        """緊急地上部リセット処理のテスト"""
        # exit_overworldとenter_overworldをモック化
        with patch.object(self.overworld_manager, 'exit_overworld') as mock_exit:
            with patch.object(self.overworld_manager, 'enter_overworld') as mock_enter:
                # 緊急リセット実行
                self.overworld_manager._emergency_overworld_reset()
                
                # 退場・再入場が実行されることを確認
                mock_exit.assert_called_once()
                mock_enter.assert_called_once_with(self.test_party)
    
    def test_emergency_overworld_reset_without_party(self):
        """パーティなしでの緊急地上部リセット処理のテスト"""
        # パーティを削除
        self.overworld_manager.current_party = None
        
        with patch.object(self.overworld_manager, 'exit_overworld') as mock_exit:
            with patch.object(self.overworld_manager, '_show_main_menu') as mock_show_main:
                # 緊急リセット実行
                self.overworld_manager._emergency_overworld_reset()
                
                # 退場とメインメニュー表示が実行されることを確認
                mock_exit.assert_called_once()
                mock_show_main.assert_called_once()
                assert self.overworld_manager.is_active == True
    
    def test_facility_exit_inactive_overworld_does_nothing(self):
        """地上部が非アクティブ時に施設退場処理が何もしないテスト"""
        with patch('src.overworld.overworld_manager.ui_manager') as mock_ui:
            # 地上部を非アクティブにする
            self.overworld_manager.is_active = False
            
            # 施設退場
            self.overworld_manager.on_facility_exit()
            
            # UI操作が一切呼ばれないことを確認
            mock_ui.show_element.assert_not_called()
            mock_ui.get_element.assert_not_called()