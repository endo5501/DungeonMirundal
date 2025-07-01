"""
Inn FacilityMenuWindow移行テスト
"""

import pytest
import inspect
import pygame
from unittest.mock import Mock

from src.overworld.facilities.inn import Inn
from src.overworld.base_facility import FacilityType


class TestInnFacilityMigration:
    """Inn移行テストクラス"""
    
    def setup_method(self):
        """各テストメソッドの前に実行される"""
        pygame.init()
        pygame.display.set_mode((1, 1), pygame.NOFRAME)
        
        # WindowManagerレジストリをクリア
        try:
            from src.ui.window_system.window_manager import WindowManager
            window_manager = WindowManager.get_instance()
            window_manager.window_registry.clear()
            window_manager.window_stack.stack.clear()
        except Exception:
            pass
    
    def teardown_method(self):
        """各テストメソッドの後に実行される"""
        # WindowManagerレジストリをクリア
        try:
            from src.ui.window_system.window_manager import WindowManager
            window_manager = WindowManager.get_instance()
            window_manager.window_registry.clear()
            window_manager.window_stack.stack.clear()
        except Exception:
            pass
        pygame.quit()
    
    @pytest.fixture
    def mock_party(self):
        """モックパーティを作成"""
        party = Mock()
        party.name = "テストパーティ"
        party.gold = 1000
        party.characters = {}
        return party
    
    @pytest.fixture
    def inn_facility(self, mock_party):
        """テスト用Inn施設を作成"""
        inn = Inn()
        inn.current_party = mock_party
        return inn
    
    def test_inn_uses_facility_menu_window_only(self, inn_facility):
        """InnがFacilityMenuWindowのみを使用することを確認"""
        from src.overworld.facilities.inn import Inn
        import inspect
        
        # クラスソースからUIMenuの参照がないことを確認
        source = inspect.getsource(Inn)
        assert 'UIMenu' not in source, "InnクラスはUIMenuを使用してはいけません"
        assert 'FacilityMenuWindow' in source or 'WindowManager' in source, "FacilityMenuWindowまたはWindowManagerを使用する必要があります"
    
    def test_inn_menu_configuration(self, inn_facility):
        """Innメニュー設定が正しく生成されることを確認"""
        # メニュー設定を取得
        menu_config = inn_facility._create_inn_menu_config()
        
        # 必須フィールドの存在確認
        assert 'facility_type' in menu_config
        assert 'facility_name' in menu_config
        assert 'menu_items' in menu_config
        assert 'party' in menu_config
        
        # 施設タイプの確認
        assert menu_config['facility_type'] == FacilityType.INN.value
        
        # メニュー項目の確認
        menu_items = menu_config['menu_items']
        assert len(menu_items) >= 6  # 6つの主要メニュー項目 + exit
        
        # 必須メニュー項目の存在確認
        item_ids = [item['id'] for item in menu_items]
        assert 'adventure_preparation' in item_ids
        assert 'item_storage' in item_ids
        assert 'talk_innkeeper' in item_ids
        assert 'travel_info' in item_ids
        assert 'tavern_rumors' in item_ids
        assert 'change_party_name' in item_ids
        assert 'exit' in item_ids
    
    def test_inn_message_handler(self, inn_facility):
        """Innメッセージハンドラーが正しく動作することを確認"""
        # メッセージハンドラーが存在することを確認
        assert hasattr(inn_facility, 'handle_facility_message'), "メッセージハンドラーが存在しません"
        assert callable(inn_facility.handle_facility_message), "メッセージハンドラーが呼び出し可能ではありません"
        
        # UI作成メソッドをモック化してUI関連エラーを完全回避
        from unittest.mock import Mock, patch
        
        with patch.object(inn_facility, '_show_adventure_service', return_value=True) as mock_adventure, \
             patch.object(inn_facility, '_show_item_service', return_value=True) as mock_storage, \
             patch.object(inn_facility, '_talk_to_innkeeper', return_value=True) as mock_innkeeper, \
             patch.object(inn_facility, '_handle_exit', return_value=True) as mock_exit:
            
            # 各種メッセージタイプのハンドリング確認
            test_cases = [
                ('menu_item_selected', {'item_id': 'adventure_preparation'}, mock_adventure),
                ('menu_item_selected', {'item_id': 'item_storage'}, mock_storage), 
                ('menu_item_selected', {'item_id': 'talk_innkeeper'}, mock_innkeeper),
                ('facility_exit_requested', {'facility_type': FacilityType.INN.value}, mock_exit)
            ]
            
            for message_type, data, expected_mock in test_cases:
                # メッセージハンドリング実行
                result = inn_facility.handle_facility_message(message_type, data)
                
                # 結果の確認
                assert isinstance(result, bool), f"メッセージハンドラーはboolを返す必要があります: {message_type}"
                assert result is True, f"メッセージハンドリングが成功する必要があります: {message_type}"
                
                # 対応するメソッドが呼び出されたことを確認
                expected_mock.assert_called_once()
                expected_mock.reset_mock()
    
    def test_inn_must_have_facility_menu_config_method(self):
        """InnがFacilityMenuWindow用設定メソッドを持つことを確認"""
        inn = Inn()
        assert hasattr(inn, '_create_inn_menu_config'), "Inn設定メソッドが存在しません"
        assert callable(inn._create_inn_menu_config), "Inn設定メソッドが呼び出し可能ではありません"
    
    def test_inn_show_menu_must_use_window_manager(self):
        """Innのshow_menuがWindowManagerを使用することを確認"""
        inn = Inn()
        
        # show_menuメソッドのソースコードを取得
        import inspect
        source = inspect.getsource(inn.show_menu)
        
        # WindowManagerの使用を確認
        assert 'WindowManager' in source, "show_menuでWindowManagerを使用する必要があります"
        assert 'FacilityMenuWindow' in source, "show_menuでFacilityMenuWindowを使用する必要があります"