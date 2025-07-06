#!/usr/bin/env python3
"""新施設システム統合テスト

overworld_manager と facility_registry の統合動作確認
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from unittest.mock import Mock, patch
from src.overworld.overworld_manager import OverworldManager
from src.character.party import Party


def test_facility_integration():
    """施設システム統合テスト"""
    print("🔧 新施設システム統合テスト開始")
    
    # OverworldManagerの初期化
    print("📋 OverworldManager初期化...")
    overworld_manager = OverworldManager()
    
    # FacilityRegistryが正しく設定されているか確認
    print("🏢 FacilityRegistry確認...")
    assert hasattr(overworld_manager, 'facility_registry'), "facility_registryが設定されていません"
    
    # 施設サービスクラスが登録されているか確認
    print("🎯 施設サービス登録確認...")
    registry = overworld_manager.facility_registry
    
    expected_facilities = ["guild", "inn", "shop", "temple", "magic_guild"]
    for facility_id in expected_facilities:
        if facility_id in registry.service_classes:
            print(f"  ✅ {facility_id}: {registry.service_classes[facility_id].__name__}")
        else:
            print(f"  ❌ {facility_id}: 未登録")
    
    # モックパーティを作成
    print("👥 モックパーティ作成...")
    mock_party = Mock()
    mock_party.name = "テストパーティ"
    mock_party.gold = 1000
    mock_party.members = []
    
    # 施設入場処理のテスト（モック使用）
    print("🚪 施設入場処理テスト...")
    
    # facility_registryの enter_facility メソッドをモック化
    with patch.object(registry, 'enter_facility', return_value=True) as mock_enter:
        result = overworld_manager._enter_facility_new("guild")
        
        # パーティが設定されていない場合のテスト
        assert result is False, "パーティ未設定時にFalseを返すべき"
        print("  ✅ パーティ未設定時の処理: OK")
        
        # パーティを設定してテスト
        overworld_manager.current_party = mock_party
        result = overworld_manager._enter_facility_new("guild")
        
        # 正常ケースのテスト
        assert result is True, "正常時にTrueを返すべき"
        mock_enter.assert_called_with("guild", mock_party)
        print("  ✅ 正常な施設入場処理: OK")
    
    print("🎉 新施設システム統合テスト完了")
    return True


def test_service_classes():
    """サービスクラステスト"""
    print("🔧 サービスクラステスト開始")
    
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
            # 基本的なインスタンス化テスト
            service = service_class()
            assert hasattr(service, 'get_menu_items'), f"{name}: get_menu_itemsメソッドが不足"
            assert hasattr(service, 'execute_action'), f"{name}: execute_actionメソッドが不足"
            assert hasattr(service, 'can_execute'), f"{name}: can_executeメソッドが不足"
            print(f"  ✅ {name}: インターフェース確認 OK")
        
        print("🎉 サービスクラステスト完了")
        return True
        
    except ImportError as e:
        print(f"❌ サービスクラスインポートエラー: {e}")
        return False


if __name__ == "__main__":
    try:
        # テスト実行
        test1_result = test_facility_integration()
        test2_result = test_service_classes()
        
        if test1_result and test2_result:
            print("\n🎉 すべてのテストが成功しました！")
            print("新施設システムは正常に統合されています。")
        else:
            print("\n❌ テストで問題が検出されました。")
            sys.exit(1)
            
    except Exception as e:
        print(f"\n💥 テスト実行中にエラーが発生: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)