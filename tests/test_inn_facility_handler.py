"""
InnFacilityHandler のテスト

Inn施設クラスの90-99%重複を統合したハンドラーのテスト
具体的なInn機能に焦点を当てた機能テスト
"""

import pytest
import pygame
from unittest.mock import Mock, patch, MagicMock
from src.overworld.facilities.inn_facility_handler import InnFacilityHandler
from src.overworld.facilities.base_facility_handler import FacilityOperationResult
from src.character.party import Party
from src.character.character import Character
from src.overworld.base_facility import FacilityType


class TestInnFacilityHandler:
    """InnFacilityHandler のテストクラス"""
    
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
        
        # Inn設定をモック
        self.mock_config_manager = patch('src.core.config_manager.config_manager')
        self.mock_config = self.mock_config_manager.start()
        self.mock_config.get_text.return_value = "Test Text"
    
    def teardown_method(self):
        """各テストメソッドの後に実行される"""
        self.mock_config_manager.stop()
        pygame.quit()
    
    def test_inn_facility_handler_initialization(self):
        """InnFacilityHandlerの初期化を確認"""
        # When: InnFacilityHandlerを作成
        handler = InnFacilityHandler()
        
        # Then: 正しく初期化される
        assert handler.facility_id == 'inn'
        assert handler.facility_type == FacilityType.INN
        assert handler.current_character is None
        assert handler.current_party is None
    
    def test_inn_service_operations_mapping(self):
        """Inn操作マッピングが正しく動作することを確認"""
        # Given: 設定済みのハンドラー
        handler = InnFacilityHandler()
        handler.set_party(self.mock_party)
        handler.set_character(self.mock_character)  # キャラクター要求操作のため
        
        # When: 各種Inn操作を実行
        operations = [
            'show_adventure_preparation',
            'show_item_management', 
            'show_spell_management',
            'show_equipment_management',
            'talk_to_innkeeper',
            'show_travel_info',
            'show_tavern_rumors'
        ]
        
        for operation in operations:
            with patch.object(handler, 'show_facility_window') as mock_show:
                mock_show.return_value = FacilityOperationResult(success=True)
                
                # When: 操作を実行
                result = handler.execute_facility_operation(operation)
                
                # Then: 成功する
                assert result.success is True, f"Operation {operation} failed"
    
    def test_show_service_unified_handler(self):
        """統一されたサービス表示ハンドラーを確認"""
        # Given: 設定済みのハンドラー
        handler = InnFacilityHandler()
        handler.set_party(self.mock_party)
        
        # モック: ウィンドウ表示
        with patch.object(handler, 'show_facility_window') as mock_show:
            mock_show.return_value = FacilityOperationResult(success=True, message="ウィンドウ表示成功")
            
            # When: サービス表示を実行
            result = handler._handle_show_service('rest', rest_type='basic', duration='full')
            
            # Then: 正しい設定でウィンドウが表示される
            assert result.success is True
            mock_show.assert_called_once_with('inn_service', {
                'service_type': 'rest',
                'party': handler.current_party,
                'character': None,
                'rest_type': 'basic',
                'duration': 'full',
                'cost': 10
            })
    
    def test_inn_service_config_creation(self):
        """Innサービス設定作成の統一メソッドを確認"""
        # Given: ハンドラーとキャラクター
        handler = InnFacilityHandler()
        handler.set_party(self.mock_party)
        handler.set_character(self.mock_character)
        
        # When: 各種サービス設定を作成
        rest_config = handler._create_inn_service_config('rest', rest_type='premium', cost=50)
        item_config = handler._create_inn_service_config('item_management', action='deposit')
        spell_config = handler._create_inn_service_config('spell_management', spell_type='priest')
        
        # Then: 統一された構造で設定が作成される
        # rest設定
        assert rest_config['service_type'] == 'rest'
        assert rest_config['party'] == self.mock_party
        assert rest_config['character'] == self.mock_character
        assert rest_config['rest_type'] == 'premium'
        assert rest_config['cost'] == 50
        
        # item管理設定
        assert item_config['service_type'] == 'item_management'
        assert item_config['action'] == 'deposit'
        
        # spell管理設定
        assert spell_config['service_type'] == 'spell_management'
        assert spell_config['spell_type'] == 'priest'
    
    def test_talk_to_innkeeper_dialog(self):
        """宿屋主人との会話ダイアログを確認"""
        # Given: ハンドラー
        handler = InnFacilityHandler()
        handler.set_party(self.mock_party)
        
        # モック: ダイアログ表示
        with patch.object(handler, 'show_dialog') as mock_dialog:
            mock_dialog.return_value = FacilityOperationResult(success=True)
            
            # When: 宿屋主人との会話を実行
            result = handler._handle_talk_to_innkeeper()
            
            # Then: 情報ダイアログが表示される
            assert result.success is True
            mock_dialog.assert_called_once_with(
                'information',
                'Test Text',  # innkeeper_title
                'Test Text'   # greeting
            )
    
    def test_party_name_change_validation(self):
        """パーティ名変更の検証を確認"""
        # Given: ハンドラー
        handler = InnFacilityHandler()
        handler.set_party(self.mock_party)
        
        # When: 空の名前で変更を試行
        validation_result = handler._validate_specific_operation(
            'change_party_name', 
            new_name='   '  # 空白のみ
        )
        
        # Then: 検証が失敗する
        assert validation_result.success is False
        assert validation_result.error_type == 'invalid_party_name'
        
        # When: 有効な名前で検証
        valid_result = handler._validate_specific_operation(
            'change_party_name', 
            new_name='New Party Name'
        )
        
        # Then: 検証が成功する
        assert valid_result.success is True
    
    def test_party_name_change_execution(self):
        """パーティ名変更の実行を確認"""
        # Given: ハンドラーとパーティ
        handler = InnFacilityHandler()
        handler.set_party(self.mock_party)
        original_name = self.mock_party.name
        
        # When: パーティ名を変更
        result = handler._handle_change_party_name(new_name='New Adventure Party')
        
        # Then: 名前が変更される
        assert result.success is True
        assert self.mock_party.name == 'New Adventure Party'
        assert result.data['old_name'] == original_name
        assert result.data['new_name'] == 'New Adventure Party'
    
    def test_character_required_operations_validation(self):
        """キャラクター要求操作の検証を確認"""
        # Given: ハンドラー（キャラクター未設定）
        handler = InnFacilityHandler()
        handler.set_party(self.mock_party)
        
        # When: キャラクター要求操作を検証
        spell_validation = handler._validate_specific_operation('show_spell_management')
        equipment_validation = handler._validate_specific_operation('show_equipment_management')
        
        # Then: 検証が失敗する
        assert spell_validation.success is False
        assert spell_validation.error_type == 'no_character'
        assert equipment_validation.success is False
        assert equipment_validation.error_type == 'no_character'
        
        # When: キャラクターを設定して検証
        handler.set_character(self.mock_character)
        spell_validation_with_char = handler._validate_specific_operation(
            'show_spell_management', 
            character=self.mock_character
        )
        
        # Then: 検証が成功する
        assert spell_validation_with_char.success is True
    
    def test_inn_menu_config_generation(self):
        """Innメニュー設定生成を確認"""
        # Given: パーティが設定されたハンドラー
        handler = InnFacilityHandler()
        handler.set_party(self.mock_party)
        
        # When: メニュー設定を取得
        menu_config = handler.get_inn_menu_config()
        
        # Then: 正しい構造のメニュー設定が生成される
        assert menu_config['facility_type'] == FacilityType.INN.value
        assert menu_config['party'] == self.mock_party
        assert len(menu_config['menu_items']) == 7  # 6つのアクション + exit
        
        # 各メニュー項目を確認
        menu_ids = [item['id'] for item in menu_config['menu_items']]
        expected_ids = [
            'adventure_preparation', 'item_storage', 'talk_innkeeper',
            'travel_info', 'tavern_rumors', 'change_party_name', 'exit'
        ]
        
        for expected_id in expected_ids:
            assert expected_id in menu_ids
    
    def test_error_handling_consistency(self):
        """エラーハンドリングの一貫性を確認"""
        # Given: ハンドラー
        handler = InnFacilityHandler()
        
        # When: 未知の操作を実行
        result = handler.execute_facility_operation('unknown_operation')
        
        # Then: 適切なエラーが返される
        assert result.success is False
        assert result.error_type == 'unknown_operation'
        assert 'unknown_operation' in result.message
    
    def test_cleanup_operations(self):
        """クリーンアップ操作を確認"""
        # Given: UI要素を持つハンドラー
        handler = InnFacilityHandler()
        mock_ui_elements = [Mock(), Mock()]
        handler._active_ui_elements = mock_ui_elements
        
        # 各UI要素にcleanupメソッドを追加
        for element in mock_ui_elements:
            element.cleanup = Mock()
        
        # When: クリーンアップを実行
        handler.cleanup_ui()
        
        # Then: 全UI要素がクリーンアップされる
        for element in mock_ui_elements:
            element.cleanup.assert_called_once()
        
        assert len(handler._active_ui_elements) == 0