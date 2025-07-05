"""施設システムコア部分のテスト"""

import pytest
from unittest.mock import Mock, MagicMock, patch
from src.facilities.core.facility_service import FacilityService, MenuItem
from src.facilities.core.service_result import ServiceResult, ResultType
from src.facilities.core.facility_controller import FacilityController
from src.facilities.core.facility_registry import FacilityRegistry
from src.facilities.core.config_loader import FacilityConfigLoader
from pathlib import Path
import json


class TestMenuItem:
    """メニュー項目のテストクラス"""
    
    def test_menu_item_creation(self):
        """メニュー項目作成のテスト"""
        item = MenuItem(
            id="test_item",
            label="テスト項目",
            description="これはテスト項目です",
            enabled=True,
            service_type="action"
        )
        
        assert item.id == "test_item"
        assert item.label == "テスト項目"
        assert item.description == "これはテスト項目です"
        assert item.enabled is True
        assert item.service_type == "action"
    
    def test_menu_item_defaults(self):
        """メニュー項目デフォルト値のテスト"""
        item = MenuItem(id="test", label="Test")
        
        assert item.description == ""
        assert item.enabled is True
        assert item.service_type == "action"


class TestServiceResult:
    """サービス結果のテストクラス"""
    
    def test_service_result_creation(self):
        """サービス結果作成のテスト"""
        result = ServiceResult(
            success=True,
            message="成功しました",
            data={"key": "value"},
            result_type=ResultType.SUCCESS
        )
        
        assert result.success is True
        assert result.message == "成功しました"
        assert result.data == {"key": "value"}
        assert result.result_type == ResultType.SUCCESS
    
    def test_is_success(self):
        """成功判定のテスト"""
        # 成功
        result = ServiceResult(True, "OK", result_type=ResultType.SUCCESS)
        assert result.is_success() is True
        
        # 失敗
        result = ServiceResult(False, "Error", result_type=ResultType.ERROR)
        assert result.is_success() is False
    
    def test_is_error(self):
        """エラー判定のテスト"""
        # エラー
        result = ServiceResult(False, "Error", result_type=ResultType.ERROR)
        assert result.is_error() is True
        
        # 成功
        result = ServiceResult(True, "OK", result_type=ResultType.SUCCESS)
        assert result.is_error() is False
    
    def test_requires_confirmation(self):
        """確認要求判定のテスト"""
        # 確認要求
        result = ServiceResult(True, "確認してください", result_type=ResultType.CONFIRM)
        assert result.requires_confirmation() is True
        
        # 確認不要
        result = ServiceResult(True, "OK", result_type=ResultType.SUCCESS)
        assert result.requires_confirmation() is False


class TestFacilityService:
    """施設サービス基底クラスのテストクラス"""
    
    class MockFacilityService(FacilityService):
        """テスト用のモック施設サービス"""
        
        def get_menu_items(self):
            return [
                MenuItem("action1", "アクション1"),
                MenuItem("action2", "アクション2")
            ]
        
        def execute_action(self, action_id, params):
            if action_id == "action1":
                return ServiceResult(True, "アクション1実行")
            else:
                return ServiceResult(False, "不明なアクション")
    
    def test_facility_service_creation(self):
        """施設サービス作成のテスト"""
        service = self.MockFacilityService("test_facility")
        
        assert service.facility_id == "test_facility"
        assert service.party is None
    
    def test_set_party(self):
        """パーティ設定のテスト"""
        service = self.MockFacilityService("test_facility")
        party = Mock()
        
        service.set_party(party)
        assert service.party == party
    
    def test_abstract_methods(self):
        """抽象メソッドのテスト"""
        service = self.MockFacilityService("test_facility")
        
        # get_menu_items
        items = service.get_menu_items()
        assert len(items) == 2
        assert items[0].id == "action1"
        
        # execute_action
        result = service.execute_action("action1", {})
        assert result.success is True
        assert result.message == "アクション1実行"


class TestFacilityController:
    """施設コントローラーのテストクラス"""
    
    @pytest.fixture
    def controller(self):
        """コントローラーのフィクスチャ"""
        service = Mock(spec=FacilityService)
        service.facility_id = "test_facility"
        service.get_menu_items.return_value = [
            MenuItem("action1", "アクション1"),
            MenuItem("exit", "退出")
        ]
        
        controller = FacilityController("test_facility", service)
        yield controller
    
    def test_controller_initialization(self, controller):
        """コントローラー初期化のテスト"""
        assert controller.facility_id == "test_facility"
        assert controller.service is not None
        assert controller.window is None
        assert controller.is_active is False
    
    def test_enter_facility(self, controller):
        """施設入場のテスト"""
        with patch.object(controller, '_create_window') as mock_create:
            controller.enter()
            
            assert controller.is_active is True
            mock_create.assert_called_once()
    
    def test_exit_facility(self, controller):
        """施設退出のテスト"""
        # ウィンドウをモック
        controller.window = Mock()
        controller.is_active = True
        
        with patch.object(controller, '_close_window') as mock_close:
            with patch.object(controller, '_return_to_overworld') as mock_return:
                result = controller.exit()
                
                assert result is True
                assert controller.is_active is False
                mock_close.assert_called_once()
                mock_return.assert_called_once()
    
    def test_execute_service_action(self, controller):
        """サービスアクション実行のテスト"""
        # サービスのモックを設定
        controller.service.execute_action.return_value = ServiceResult(
            True, "アクション成功"
        )
        
        result = controller.execute_service_action("action1", {"param": "value"})
        
        assert result.success is True
        assert result.message == "アクション成功"
        controller.service.execute_action.assert_called_once_with(
            "action1", {"param": "value"}
        )
    
    def test_handle_ui_action_exit(self, controller):
        """UI退出アクションのテスト"""
        controller.is_active = True
        
        with patch.object(controller, 'exit') as mock_exit:
            controller.handle_ui_action("exit", {})
            mock_exit.assert_called_once()
    
    def test_get_menu_items(self, controller):
        """メニュー項目取得のテスト"""
        items = controller.get_menu_items()
        
        assert len(items) == 2
        assert items[0].id == "action1"
        assert items[1].id == "exit"


class TestFacilityRegistry:
    """施設レジストリのテストクラス"""
    
    @pytest.fixture
    def registry(self):
        """レジストリのフィクスチャ"""
        # シングルトンをリセット
        FacilityRegistry._instance = None
        registry = FacilityRegistry.get_instance()
        registry.clear()  # 既存の登録をクリア
        yield registry
        # クリーンアップ
        registry.clear()
        FacilityRegistry._instance = None
    
    def test_singleton_pattern(self):
        """シングルトンパターンのテスト"""
        registry1 = FacilityRegistry.get_instance()
        registry2 = FacilityRegistry.get_instance()
        
        assert registry1 is registry2
    
    def test_register_facility(self, registry):
        """施設登録のテスト"""
        service = Mock(spec=FacilityService)
        service.facility_id = "test_facility"
        
        registry.register("test_facility", service)
        
        assert registry.has_facility("test_facility")
        assert registry.get_service("test_facility") == service
    
    def test_get_controller(self, registry):
        """コントローラー取得のテスト"""
        service = Mock(spec=FacilityService)
        service.facility_id = "test_facility"
        
        registry.register("test_facility", service)
        controller = registry.get_controller("test_facility")
        
        assert controller is not None
        assert controller.facility_id == "test_facility"
        assert controller.service == service
    
    def test_get_nonexistent_facility(self, registry):
        """存在しない施設の取得のテスト"""
        assert registry.get_service("nonexistent") is None
        assert registry.get_controller("nonexistent") is None
        assert registry.has_facility("nonexistent") is False
    
    def test_get_all_facilities(self, registry):
        """全施設取得のテスト"""
        # 複数の施設を登録
        service1 = Mock(spec=FacilityService)
        service1.facility_id = "facility1"
        service2 = Mock(spec=FacilityService)
        service2.facility_id = "facility2"
        
        registry.register("facility1", service1)
        registry.register("facility2", service2)
        
        facilities = registry.get_all_facilities()
        assert len(facilities) == 2
        assert "facility1" in facilities
        assert "facility2" in facilities


class TestFacilityConfigLoader:
    """施設設定ローダーのテストクラス"""
    
    @pytest.fixture
    def temp_config_dir(self, tmp_path):
        """一時設定ディレクトリのフィクスチャ"""
        config_dir = tmp_path / "config"
        config_dir.mkdir()
        return config_dir
    
    @pytest.fixture
    def loader(self, temp_config_dir):
        """ローダーのフィクスチャ"""
        return FacilityConfigLoader(temp_config_dir)
    
    def test_loader_initialization(self, loader, temp_config_dir):
        """ローダー初期化のテスト"""
        assert loader.config_dir == temp_config_dir
        assert loader.config_file == temp_config_dir / "facilities.json"
        assert loader.schema_file == temp_config_dir / "facilities_schema.json"
        assert loader._loaded is False
    
    def test_load_valid_config(self, loader, temp_config_dir):
        """有効な設定読み込みのテスト"""
        # テスト用の設定ファイルを作成
        config_data = {
            "version": "1.0.0",
            "facilities": {
                "test_facility": {
                    "id": "test_facility",
                    "name": "テスト施設",
                    "service_class": "TestService"
                }
            }
        }
        
        config_file = temp_config_dir / "facilities.json"
        with open(config_file, "w", encoding="utf-8") as f:
            json.dump(config_data, f)
        
        # 読み込みテスト
        config = loader.load()
        
        assert config["version"] == "1.0.0"
        assert "test_facility" in config["facilities"]
        assert config["facilities"]["test_facility"]["name"] == "テスト施設"
        assert loader._loaded is True
    
    def test_get_facility_config(self, loader, temp_config_dir):
        """施設設定取得のテスト"""
        # テスト用の設定を準備
        config_data = {
            "version": "1.0.0",
            "facilities": {
                "guild": {
                    "id": "guild",
                    "name": "冒険者ギルド",
                    "services": {
                        "character_creation": {
                            "name": "キャラクター作成",
                            "type": "wizard"
                        }
                    }
                }
            }
        }
        
        config_file = temp_config_dir / "facilities.json"
        with open(config_file, "w", encoding="utf-8") as f:
            json.dump(config_data, f)
        
        # 施設設定を取得
        guild_config = loader.get_facility_config("guild")
        
        assert guild_config["id"] == "guild"
        assert guild_config["name"] == "冒険者ギルド"
        assert "character_creation" in guild_config["services"]
    
    def test_get_service_config(self, loader, temp_config_dir):
        """サービス設定取得のテスト"""
        # テスト用の設定を準備
        config_data = {
            "version": "1.0.0",
            "facilities": {
                "guild": {
                    "id": "guild",
                    "services": {
                        "character_creation": {
                            "name": "キャラクター作成",
                            "type": "wizard",
                            "steps": [
                                {"id": "name", "label": "名前入力"}
                            ]
                        }
                    }
                }
            }
        }
        
        config_file = temp_config_dir / "facilities.json"
        with open(config_file, "w", encoding="utf-8") as f:
            json.dump(config_data, f)
        
        # サービス設定を取得
        service_config = loader.get_service_config("guild", "character_creation")
        
        assert service_config["name"] == "キャラクター作成"
        assert service_config["type"] == "wizard"
        assert len(service_config["steps"]) == 1
    
    def test_fallback_config(self, loader):
        """フォールバック設定のテスト"""
        # 設定ファイルが存在しない場合
        config = loader.load()
        
        # フォールバック設定が返されることを確認
        assert "version" in config
        assert "facilities" in config
        assert "guild" in config["facilities"]
        assert "inn" in config["facilities"]
        assert "shop" in config["facilities"]
        assert "temple" in config["facilities"]
        assert "magic_guild" in config["facilities"]