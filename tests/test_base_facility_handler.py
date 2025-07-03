"""
BaseFacilityHandler のテスト

t-wada式TDDによるテストファースト開発
Inn施設クラスの90-99%重複を統合するため、共通パターンを抽象化
"""

import pytest
import pygame
from unittest.mock import Mock, patch, MagicMock
from src.overworld.facilities.base_facility_handler import (
    BaseFacilityHandler, FacilityOperationResult, FacilityCommand
)
from src.overworld.facilities.inn_facility_handler import InnFacilityHandler
from src.character.party import Party
from src.character.character import Character
from src.overworld.base_facility import FacilityType
from src.ui.window_system import WindowManager


class TestBaseFacilityHandler:
    """BaseFacilityHandler のテストクラス"""
    
    def setup_method(self):
        """各テストメソッドの前に実行される"""
        pygame.init()
        pygame.display.set_mode((1, 1), pygame.NOFRAME)
        
        # モックパーティとキャラクター
        self.mock_party = Mock(spec=Party)
        self.mock_party.name = "Test Party"
        self.mock_party.gold = 1000
        
        self.mock_character = Mock(spec=Character)
        self.mock_character.name = "Test Character"
    
    def teardown_method(self):
        """各テストメソッドの後に実行される"""
        pygame.quit()
    
    def test_facility_handler_inherits_from_base_facility(self):
        """InnFacilityHandlerがBaseFacilityを継承することを確認"""
        # When: InnFacilityHandlerを作成
        from src.overworld.base_facility import BaseFacility
        handler = InnFacilityHandler()
        
        # Then: BaseFacilityを継承している
        assert isinstance(handler, BaseFacility)
        assert handler.facility_id == 'inn'
        assert handler.facility_type == FacilityType.INN
    
    def test_execute_facility_operation_validates_prerequisites(self):
        """施設操作が前提条件を検証することを確認"""
        # Given: 施設ハンドラー
        handler = InnFacilityHandler()
        
        # When: パーティが設定されていない状態で操作を実行
        result = handler.execute_facility_operation('show_service', service_type='rest')
        
        # Then: 前提条件エラーが返される
        assert isinstance(result, FacilityOperationResult)
        assert result.success is False
        assert result.error_type == 'prerequisite_error'
        assert 'party not set' in result.message.lower()
    
    def test_execute_facility_operation_with_valid_party(self):
        """有効なパーティで施設操作が実行されることを確認"""
        # Given: パーティが設定された施設ハンドラー
        handler = InnFacilityHandler()
        handler.set_party(self.mock_party)
        
        # モック: 具体的な操作実装がFacilityOperationResultを返すように
        mock_result = FacilityOperationResult(success=True, message="操作完了")
        with patch.object(handler, '_execute_operation', return_value=mock_result) as mock_execute:
            # When: 有効な操作を実行
            result = handler.execute_facility_operation('show_service', service_type='rest')
            
            # Then: 操作が実行される
            assert result.success is True
            mock_execute.assert_called_once_with('show_service', service_type='rest')
    
    def test_facility_operation_template_method_pattern(self):
        """Template Methodパターンが正しく動作することを確認"""
        # Given: 施設ハンドラー
        handler = InnFacilityHandler()
        handler.set_party(self.mock_party)
        
        # モック: 各段階のメソッド
        mock_validation_result = FacilityOperationResult(success=True)
        mock_execution_result = FacilityOperationResult(success=True, message="実行完了")
        
        with patch.object(handler, '_validate_operation', return_value=mock_validation_result) as mock_validate, \
             patch.object(handler, '_execute_operation', return_value=mock_execution_result) as mock_execute, \
             patch.object(handler, '_post_operation_cleanup') as mock_cleanup:
            
            # When: 操作を実行
            result = handler.execute_facility_operation('show_service', service_type='rest')
            
            # Then: Template Methodの各段階が実行される
            mock_validate.assert_called_once()
            mock_execute.assert_called_once()
            mock_cleanup.assert_called_once_with('show_service', result)
    
    def test_window_manager_integration_pattern(self):
        """WindowManager統合パターンが動作することを確認"""
        # Given: 施設ハンドラー
        handler = InnFacilityHandler()
        handler.set_party(self.mock_party)
        
        # モック: WindowManagerとウィンドウ作成
        with patch.object(handler.window_manager, 'create_window') as mock_create, \
             patch.object(handler.window_manager, 'show_window') as mock_show:
            
            mock_window = Mock()
            mock_create.return_value = mock_window
            
            # When: ウィンドウ表示操作を実行
            result = handler.show_facility_window('inn_service', {'service_type': 'rest'})
            
            # Then: WindowManagerが使用される
            assert result.success is True
            mock_create.assert_called_once()
            mock_show.assert_called_once()
    
    def test_facility_command_pattern(self):
        """Commandパターンによる操作実行を確認"""
        # Given: 施設ハンドラーと操作コマンド
        handler = InnFacilityHandler()
        handler.set_party(self.mock_party)
        
        command = FacilityCommand(
            operation='show_service',
            params={'service_type': 'rest'},
            handler=handler
        )
        
        # モック: 操作実行がFacilityOperationResultを返すように
        mock_result = FacilityOperationResult(success=True, message="コマンド実行完了")
        with patch.object(handler, '_execute_operation', return_value=mock_result):
            # When: コマンドを実行
            result = command.execute()
            
            # Then: コマンドが実行される
            assert result.success is True
    
    def test_service_window_creation_unified_pattern(self):
        """サービスウィンドウ作成の統一パターンを確認"""
        # Given: 施設ハンドラー
        handler = InnFacilityHandler()
        handler.set_party(self.mock_party)
        
        # When: 異なるサービスウィンドウを作成
        rest_config = handler.create_service_window_config('rest', {'duration': 'full'})
        item_config = handler.create_service_window_config('item_management', {'action': 'deposit'})
        
        # Then: 統一された設定構造が返される
        assert 'window_type' in rest_config
        assert 'facility_config' in rest_config
        assert 'service_config' in rest_config
        
        assert 'window_type' in item_config
        assert 'facility_config' in item_config
        assert 'service_config' in item_config
    
    def test_error_handling_standardization(self):
        """エラーハンドリングの標準化を確認"""
        # Given: 施設ハンドラー
        handler = InnFacilityHandler()
        
        # When: 異なるタイプのエラーが発生
        insufficient_funds_result = handler.handle_error('insufficient_funds', 'パーティのゴールドが不足しています')
        invalid_action_result = handler.handle_error('invalid_action', '無効な操作です')
        
        # Then: 標準化されたエラー結果が返される
        assert isinstance(insufficient_funds_result, FacilityOperationResult)
        assert insufficient_funds_result.success is False
        assert insufficient_funds_result.error_type == 'insufficient_funds'
        
        assert isinstance(invalid_action_result, FacilityOperationResult)
        assert invalid_action_result.success is False
        assert invalid_action_result.error_type == 'invalid_action'
    
    def test_dialog_display_unified_interface(self):
        """ダイアログ表示の統一インターフェースを確認"""
        # Given: 施設ハンドラー
        handler = InnFacilityHandler()
        
        # モック: BaseFacilityのダイアログメソッド
        with patch.object(handler, 'show_information_dialog') as mock_info, \
             patch.object(handler, 'show_error_dialog') as mock_error, \
             patch.object(handler, 'show_success_dialog') as mock_success:
            
            # When: 統一インターフェースでダイアログを表示
            handler.show_dialog('information', 'タイトル', 'メッセージ')
            handler.show_dialog('error', 'エラー', 'エラーメッセージ')
            handler.show_dialog('success', '成功', '成功メッセージ')
            
            # Then: 適切なダイアログメソッドが呼ばれる
            mock_info.assert_called_once_with('タイトル', 'メッセージ')
            mock_error.assert_called_once_with('エラー', 'エラーメッセージ')
            mock_success.assert_called_once_with('成功', '成功メッセージ')
    
    def test_party_validation_pattern(self):
        """パーティ検証パターンの統一を確認"""
        # Given: 施設ハンドラー
        handler = InnFacilityHandler()
        
        # When: パーティ未設定で操作を試行
        result_no_party = handler.validate_party_requirements()
        
        # パーティを設定
        handler.set_party(self.mock_party)
        result_with_party = handler.validate_party_requirements()
        
        # Then: パーティ要件が正しく検証される
        assert result_no_party.success is False
        assert result_no_party.error_type == 'no_party'
        
        assert result_with_party.success is True
    
    def test_cleanup_pattern_consistency(self):
        """クリーンアップパターンの一貫性を確認"""
        # Given: 施設ハンドラー
        handler = InnFacilityHandler()
        
        # モック: UI要素
        mock_ui_elements = [Mock(), Mock(), Mock()]
        handler._active_ui_elements = mock_ui_elements
        
        # When: クリーンアップを実行
        handler.cleanup_ui()
        
        # Then: すべてのUI要素がクリーンアップされる
        for element in mock_ui_elements:
            element.cleanup.assert_called_once()
        
        assert len(handler._active_ui_elements) == 0