#!/usr/bin/env python3
"""施設システム統合テスト

手動テスト tests/manual/test_facility_integration.py を pytest フレームワークに統合
"""

import pytest
from unittest.mock import Mock, patch
from src.overworld.overworld_manager import OverworldManager
from src.character.party import Party
from src.character.character import Character


@pytest.mark.facility
@pytest.mark.integration
class TestFacilitySystemIntegration:
    """施設システム統合テスト"""
    
    @pytest.fixture
    def overworld_manager(self):
        """OverworldManagerのセットアップ"""
        return OverworldManager()
    
    @pytest.fixture
    def mock_party(self):
        """テスト用パーティの作成"""
        mock_party = Mock()
        mock_party.name = "テストパーティ"
        mock_party.gold = 1000
        mock_party.members = []
        return mock_party
    
    def test_facility_registry_initialization(self, overworld_manager):
        """FacilityRegistryが正しく初期化されているかテスト"""
        assert hasattr(overworld_manager, 'facility_registry'), "facility_registryが設定されていない"
        assert overworld_manager.facility_registry is not None, "facility_registryがNone"
    
    def test_facility_service_registration(self, overworld_manager):
        """施設サービスクラスが正しく登録されているかテスト"""
        registry = overworld_manager.facility_registry
        
        expected_facilities = ["guild", "inn", "shop", "temple", "magic_guild"]
        
        for facility_id in expected_facilities:
            assert facility_id in registry.service_classes, f"施設 '{facility_id}' が未登録"
            service_class = registry.service_classes[facility_id]
            assert service_class is not None, f"施設 '{facility_id}' のサービスクラスがNone"
            
            # サービスクラスの基本メソッドを確認
            service_instance = service_class()
            assert hasattr(service_instance, 'get_menu_items'), f"{facility_id}: get_menu_itemsメソッドが不足"
            assert hasattr(service_instance, 'execute_action'), f"{facility_id}: execute_actionメソッドが不足"
            assert hasattr(service_instance, 'can_execute'), f"{facility_id}: can_executeメソッドが不足"
    
    def test_facility_entry_without_party(self, overworld_manager):
        """パーティが設定されていない場合の施設入場テスト"""
        # パーティが設定されていない状態
        assert overworld_manager.current_party is None, "初期状態でパーティが設定されている"
        
        # 施設入場を試行
        result = overworld_manager._enter_facility_new("guild")
        
        assert result is False, "パーティ未設定時にTrueを返してはいけない"
    
    def test_facility_entry_with_party(self, overworld_manager, mock_party):
        """パーティが設定されている場合の施設入場テスト"""
        overworld_manager.current_party = mock_party
        
        registry = overworld_manager.facility_registry
        
        # facility_registryの enter_facility メソッドをモック化
        with patch.object(registry, 'enter_facility', return_value=True) as mock_enter:
            result = overworld_manager._enter_facility_new("guild")
            
            assert result is True, "正常時にFalseを返してはいけない"
            mock_enter.assert_called_once_with("guild", mock_party)
    
    def test_facility_entry_error_handling(self, overworld_manager, mock_party):
        """施設入場時のエラーハンドリングテスト"""
        overworld_manager.current_party = mock_party
        
        registry = overworld_manager.facility_registry
        
        # facility_registryの enter_facility で例外が発生する場合
        with patch.object(registry, 'enter_facility', side_effect=Exception("テストエラー")):
            result = overworld_manager._enter_facility_new("guild")
            
            # エラーが適切にハンドリングされることを確認
            assert result is False, "例外発生時にTrueを返してはいけない"
    
    def test_invalid_facility_entry(self, overworld_manager, mock_party):
        """存在しない施設への入場テスト"""
        overworld_manager.current_party = mock_party
        
        # 存在しない施設IDで入場を試行
        result = overworld_manager._enter_facility_new("nonexistent_facility")
        
        assert result is False, "存在しない施設でTrueを返してはいけない"
    
    @pytest.mark.parametrize("facility_id", ["guild", "inn", "shop", "temple", "magic_guild"])
    def test_individual_facility_entry(self, overworld_manager, mock_party, facility_id):
        """各施設への個別入場テスト"""
        overworld_manager.current_party = mock_party
        
        registry = overworld_manager.facility_registry
        
        with patch.object(registry, 'enter_facility', return_value=True) as mock_enter:
            result = overworld_manager._enter_facility_new(facility_id)
            
            assert result is True, f"施設 '{facility_id}' への入場が失敗"
            mock_enter.assert_called_once_with(facility_id, mock_party)


class TestFacilityServiceClasses:
    """施設サービスクラス個別テスト"""
    
    def test_service_classes_import(self):
        """サービスクラスのインポートテスト"""
        try:
            from src.facilities.services.guild_service import GuildService
            from src.facilities.services.inn_service import InnService
            from src.facilities.services.shop_service import ShopService
            from src.facilities.services.temple_service import TempleService
            from src.facilities.services.magic_guild_service import MagicGuildService
            
            # インポートが成功することを確認
            assert True, "すべてのサービスクラスのインポートが成功"
            
        except ImportError as e:
            pytest.fail(f"サービスクラスのインポートに失敗: {e}")
    
    def test_service_classes_instantiation(self):
        """サービスクラスのインスタンス化テスト"""
        try:
            from src.facilities.services.guild_service import GuildService
            from src.facilities.services.inn_service import InnService
            from src.facilities.services.shop_service import ShopService
            from src.facilities.services.temple_service import TempleService
            from src.facilities.services.magic_guild_service import MagicGuildService
            
            services = [
                ("GuildService", GuildService),
                ("InnService", InnService),
                ("ShopService", ShopService),
                ("TempleService", TempleService),
                ("MagicGuildService", MagicGuildService)
            ]
            
            for name, service_class in services:
                # インスタンス化テスト
                service = service_class()
                assert service is not None, f"{name} のインスタンス化に失敗"
                
                # 必要なメソッドの存在確認
                assert hasattr(service, 'get_menu_items'), f"{name}: get_menu_itemsメソッドが不足"
                assert hasattr(service, 'execute_action'), f"{name}: execute_actionメソッドが不足"
                assert hasattr(service, 'can_execute'), f"{name}: can_executeメソッドが不足"
                
                # メソッドが呼び出し可能であることを確認
                assert callable(getattr(service, 'get_menu_items')), f"{name}: get_menu_itemsが呼び出し可能でない"
                assert callable(getattr(service, 'execute_action')), f"{name}: execute_actionが呼び出し可能でない"
                assert callable(getattr(service, 'can_execute')), f"{name}: can_executeが呼び出し可能でない"
                
        except ImportError as e:
            pytest.fail(f"サービスクラスのインポートに失敗: {e}")
    
    def test_service_classes_interface_compliance(self):
        """サービスクラスのインターフェース準拠テスト"""
        try:
            from src.facilities.services.guild_service import GuildService
            
            service = GuildService()
            
            # get_menu_items の戻り値テスト
            menu_items = service.get_menu_items()
            assert isinstance(menu_items, (list, tuple)), "get_menu_itemsはlistまたはtupleを返すべき"
            
            # can_execute の戻り値テスト（実際のシグネチャに合わせる）
            can_execute_result = service.can_execute("character_creation")
            assert isinstance(can_execute_result, bool), "can_executeはboolを返すべき"
            
            # execute_action の戻り値テスト
            result = service.execute_action("character_creation", {})
            assert result is not None, "execute_actionは何らかの結果を返すべき"
            
        except ImportError:
            pytest.skip("サービスクラスのインポートができないためスキップ")
        except Exception as e:
            # インターフェース不適合の場合はテストを失敗させる
            pytest.fail(f"サービスクラスのインターフェース問題: {e}")