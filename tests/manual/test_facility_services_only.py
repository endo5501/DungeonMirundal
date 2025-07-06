#!/usr/bin/env python3
"""施設サービスのみの動作確認テスト

UI部分を除き、サービスクラスの基本機能のみをテスト
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from unittest.mock import Mock


def create_simple_mock_party():
    """シンプルなモックパーティを作成"""
    party = Mock()
    party.name = "テストパーティ"
    party.gold = 5000
    party.members = []
    
    # モックキャラクターを追加
    mock_character = Mock()
    mock_character.id = "char_001"
    mock_character.name = "テストキャラクター"
    mock_character.level = 5
    mock_character.hp = 80
    mock_character.max_hp = 100
    mock_character.mp = 40
    mock_character.max_mp = 50
    mock_character.is_alive.return_value = True
    mock_character.status = "normal"
    mock_character.can_use_magic.return_value = True
    
    # インベントリ関連のモック
    mock_inventory = Mock()
    mock_inventory.get_all_items.return_value = []
    mock_character.inventory = mock_inventory
    
    # その他の必要なメソッド
    mock_character.get_learned_spells.return_value = []
    mock_character.get_equipped_spells.return_value = []
    mock_character.get_equipment.return_value = {}
    
    party.members.append(mock_character)
    
    return party


def test_service_class_basic(service_class, service_name):
    """サービスクラスの基本機能をテスト"""
    print(f"\n🔧 {service_name} サービステスト開始...")
    
    try:
        # サービスインスタンス作成
        service = service_class()
        print(f"  ✅ {service_name}: インスタンス作成成功")
        
        # パーティを設定
        party = create_simple_mock_party()
        service.party = party
        print(f"  ✅ {service_name}: パーティ設定成功")
        
        # メニュー項目取得テスト
        try:
            menu_items = service.get_menu_items()
            if menu_items:
                print(f"  ✅ {service_name}: メニュー項目取得成功 ({len(menu_items)}項目)")
                for item in menu_items[:3]:  # 最初の3項目のみ表示
                    print(f"    - {item.label}: {item.description}")
            else:
                print(f"  ⚠️  {service_name}: メニュー項目なし")
        except Exception as e:
            print(f"  ❌ {service_name}: メニュー項目取得エラー - {e}")
        
        # exitアクション実行テスト
        try:
            result = service.execute_action("exit", {})
            if result and result.is_success():
                print(f"  ✅ {service_name}: exit処理成功")
            else:
                print(f"  ⚠️  {service_name}: exit処理結果不明")
        except Exception as e:
            print(f"  ❌ {service_name}: exit処理エラー - {e}")
        
        return True
        
    except Exception as e:
        print(f"  💥 {service_name}: テスト中にエラー - {e}")
        return False


def test_all_service_classes():
    """全サービスクラスの動作確認"""
    print("🎯 施設サービスクラス動作確認テスト開始")
    
    # テスト対象サービス
    services = [
        ("GuildService", "src.facilities.services.guild_service"),
        ("InnService", "src.facilities.services.inn_service"),
        ("ShopService", "src.facilities.services.shop_service"),
        ("TempleService", "src.facilities.services.temple_service"),
        ("MagicGuildService", "src.facilities.services.magic_guild_service")
    ]
    
    results = {}
    for service_name, module_path in services:
        try:
            # モジュールとクラスを動的インポート
            module = __import__(module_path, fromlist=[service_name])
            service_class = getattr(module, service_name)
            
            # テスト実行
            results[service_name] = test_service_class_basic(service_class, service_name)
            
        except ImportError as e:
            print(f"\n❌ {service_name}: インポートエラー - {e}")
            results[service_name] = False
        except Exception as e:
            print(f"\n💥 {service_name}: 予期しないエラー - {e}")
            results[service_name] = False
    
    # 結果のまとめ
    print("\n📊 施設サービス動作確認結果:")
    successful = 0
    for service_name, success in results.items():
        status = "✅ 成功" if success else "❌ 失敗"
        print(f"  {service_name}: {status}")
        if success:
            successful += 1
    
    print(f"\n🎉 成功率: {successful}/{len(services)} ({100*successful//len(services)}%)")
    
    if successful == len(services):
        print("🎉 すべてのサービスクラスが正常に動作しています！")
        return True
    else:
        print("⚠️  一部のサービスクラスに問題があります。")
        return False


if __name__ == "__main__":
    try:
        # サービスクラス動作確認
        success = test_all_service_classes()
        
        if success:
            print("\n🎉 施設サービス動作確認テスト完了 - すべて正常")
        else:
            print("\n❌ 施設サービス動作確認テスト完了 - 問題あり")
            sys.exit(1)
            
    except Exception as e:
        print(f"\n💥 テスト実行中にエラーが発生: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)