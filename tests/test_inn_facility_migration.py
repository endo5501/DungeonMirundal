"""
Inn FacilityMenuWindow移行テスト
"""

import pytest
import inspect
from unittest.mock import Mock

from src.overworld.facilities.inn import Inn
from src.overworld.base_facility import FacilityType


class TestInnFacilityMigration:
    """Inn移行テストクラス"""
    
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
        item_ids = [item['item_id'] for item in menu_items]
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
        
        # 各種メッセージタイプのハンドリング確認
        test_messages = [
            ('menu_item_selected', {'item_id': 'adventure_preparation'}),
            ('menu_item_selected', {'item_id': 'item_storage'}),
            ('menu_item_selected', {'item_id': 'talk_innkeeper'}),
            ('facility_exit_requested', {'facility_type': FacilityType.INN.value})
        ]
        
        for message_type, data in test_messages:
            try:
                # メッセージハンドリングが例外を発生させないことを確認
                result = inn_facility.handle_facility_message(message_type, data)
                assert isinstance(result, bool), "メッセージハンドラーはboolを返す必要があります"
            except Exception as e:
                pytest.fail(f"メッセージハンドリングでエラー: {message_type}, {data} -> {e}")
    
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