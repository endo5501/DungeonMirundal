"""
FacilityService基底クラスのテスト

施設サービスの基底クラスの基本機能をテストする
"""

import pytest
from unittest.mock import Mock
from src.facilities.core.facility_service import FacilityService, MenuItem
from src.facilities.core.service_result import ServiceResult
from src.character.party import Party


class TestFacilityService:
    """FacilityService基底クラスのテスト"""
    
    def create_concrete_service(self):
        """テスト用の具象サービスクラスを作成"""
        class TestService(FacilityService):
            def get_menu_items(self):
                return [
                    MenuItem("test1", "テスト1", service_type="action"),
                    MenuItem("test2", "テスト2", service_type="wizard")
                ]
            
            def execute_action(self, action_id, params):
                if action_id == "test1":
                    return ServiceResult.ok("アクション実行成功")
                elif action_id == "error":
                    return ServiceResult.error("エラーが発生しました")
                else:
                    return ServiceResult.error("不明なアクション")
            
            def can_execute(self, action_id):
                return action_id in ["test1", "test2"]
            
            def get_action_cost(self, action_id):
                costs = {"test1": 100, "test2": 200}
                return costs.get(action_id, 0)
        
        return TestService("test_facility")
    
    def test_initialization(self):
        """初期化テスト"""
        service = self.create_concrete_service()
        
        assert service.facility_id == "test_facility"
        assert service.party is None
        assert service._service_data == {}
    
    def test_party_management(self):
        """パーティ管理テスト"""
        service = self.create_concrete_service()
        party_mock = Mock(spec=Party)
        
        # パーティ設定前
        assert service.has_party() is False
        assert service.get_party() is None
        
        # パーティ設定
        service.set_party(party_mock)
        assert service.has_party() is True
        assert service.get_party() == party_mock
    
    def test_service_data_management(self):
        """サービスデータ管理テスト"""
        service = self.create_concrete_service()
        
        # 初期状態
        assert service.get_service_data("key1") is None
        assert service.get_service_data("key1", "default") == "default"
        
        # データ設定
        service.set_service_data("key1", "value1")
        service.set_service_data("key2", {"nested": "data"})
        
        assert service.get_service_data("key1") == "value1"
        assert service.get_service_data("key2") == {"nested": "data"}
        assert service.get_service_data("nonexistent") is None
        
        # データクリア
        service.clear_service_data()
        assert service.get_service_data("key1") is None
        assert service.get_service_data("key2") is None
    
    def test_welcome_message(self):
        """歓迎メッセージテスト"""
        service = self.create_concrete_service()
        expected = "test_facilityへようこそ！"
        assert service.get_welcome_message() == expected
    
    def test_menu_items(self):
        """メニュー項目テスト"""
        service = self.create_concrete_service()
        items = service.get_menu_items()
        
        assert len(items) == 2
        assert items[0].id == "test1"
        assert items[0].label == "テスト1"
        assert items[0].service_type == "action"
        assert items[1].id == "test2"
        assert items[1].label == "テスト2"
        assert items[1].service_type == "wizard"
    
    def test_action_execution(self):
        """アクション実行テスト"""
        service = self.create_concrete_service()
        
        # 正常な実行
        result = service.execute_action("test1", {})
        assert result.is_success() is True
        assert result.message == "アクション実行成功"
        
        # エラーケース
        error_result = service.execute_action("error", {})
        assert error_result.is_error() is True
        assert error_result.message == "エラーが発生しました"
        
        # 不明なアクション
        unknown_result = service.execute_action("unknown", {})
        assert unknown_result.is_error() is True
        assert "不明なアクション" in unknown_result.message
    
    def test_can_execute(self):
        """実行可能性チェックテスト"""
        service = self.create_concrete_service()
        
        assert service.can_execute("test1") is True
        assert service.can_execute("test2") is True
        assert service.can_execute("unknown") is False
    
    def test_action_cost(self):
        """アクションコストテスト"""
        service = self.create_concrete_service()
        
        assert service.get_action_cost("test1") == 100
        assert service.get_action_cost("test2") == 200
        assert service.get_action_cost("unknown") == 0
    
    def test_can_afford_action_no_party(self):
        """パーティなしでの支払い能力テスト"""
        service = self.create_concrete_service()
        
        # パーティが設定されていない場合
        assert service.can_afford_action("test1") is False
        assert service.can_afford_action("test2") is False
    
    def test_can_afford_action_with_party(self):
        """パーティありでの支払い能力テスト"""
        service = self.create_concrete_service()
        party_mock = Mock(spec=Party)
        
        # ゴールド不足
        party_mock.gold = 50
        service.set_party(party_mock)
        assert service.can_afford_action("test1") is False  # cost: 100
        assert service.can_afford_action("test2") is False  # cost: 200
        
        # ゴールド十分
        party_mock.gold = 150
        assert service.can_afford_action("test1") is True   # cost: 100
        assert service.can_afford_action("test2") is False  # cost: 200
        
        # ゴールド豊富
        party_mock.gold = 500
        assert service.can_afford_action("test1") is True   # cost: 100
        assert service.can_afford_action("test2") is True   # cost: 200
    
    def test_validate_action_params_default(self):
        """アクションパラメータ検証のデフォルト実装テスト"""
        service = self.create_concrete_service()
        
        # デフォルト実装は常にTrue
        assert service.validate_action_params("test1", {}) is True
        assert service.validate_action_params("test1", {"param": "value"}) is True
        assert service.validate_action_params("unknown", {}) is True


class TestMenuItem:
    """MenuItemクラスのテスト"""
    
    def test_initialization_minimal(self):
        """最小限の初期化テスト"""
        item = MenuItem("test_id", "テストラベル")
        
        assert item.id == "test_id"
        assert item.label == "テストラベル"
        assert item.icon is None
        assert item.enabled is True
        assert item.service_type == "action"
        assert item.description is None
    
    def test_initialization_full(self):
        """完全な初期化テスト"""
        item = MenuItem(
            id="full_test",
            label="フルテスト",
            icon="test_icon.png",
            enabled=False,
            service_type="wizard",
            description="テスト項目の説明"
        )
        
        assert item.id == "full_test"
        assert item.label == "フルテスト"
        assert item.icon == "test_icon.png"
        assert item.enabled is False
        assert item.service_type == "wizard"
        assert item.description == "テスト項目の説明"
    
    def test_to_dict(self):
        """辞書変換テスト"""
        item = MenuItem(
            id="dict_test",
            label="辞書テスト",
            icon="icon.png",
            enabled=True,
            service_type="list",
            description="辞書変換のテスト"
        )
        
        expected = {
            'id': "dict_test",
            'label': "辞書テスト",
            'icon': "icon.png",
            'enabled': True,
            'service_type': "list",
            'description': "辞書変換のテスト"
        }
        
        assert item.to_dict() == expected
    
    def test_to_dict_minimal(self):
        """最小限設定での辞書変換テスト"""
        item = MenuItem("min_test", "最小テスト")
        
        expected = {
            'id': "min_test",
            'label': "最小テスト",
            'icon': None,
            'enabled': True,
            'service_type': "action",
            'description': None
        }
        
        assert item.to_dict() == expected