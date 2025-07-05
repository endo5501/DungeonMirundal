#!/usr/bin/env python3
"""全施設の動作確認テスト

Phase 4 Day 20: 新施設システムの総合動作確認
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from unittest.mock import Mock
from src.facilities.core.facility_registry import FacilityRegistry
from src.character.party import Party


def create_mock_party():
    """モックパーティを作成"""
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
    party.members.append(mock_character)
    
    return party


def test_facility_basic_operations(facility_id: str, party):
    """施設の基本操作をテスト"""
    print(f"\n🔧 {facility_id} の動作確認開始...")
    
    # Facility Registryから施設を取得
    registry = FacilityRegistry.get_instance()
    
    # 施設コントローラーを作成
    controller = registry.create_facility_controller(facility_id)
    if not controller:
        print(f"  ❌ {facility_id}: コントローラー作成失敗")
        return False
    
    try:
        # 施設に入る
        enter_result = controller.enter(party)
        if not enter_result:
            print(f"  ❌ {facility_id}: 入場失敗")
            return False
        print(f"  ✅ {facility_id}: 入場成功")
        
        # メニュー項目を取得
        menu_items = controller.get_menu_items()
        if not menu_items:
            print(f"  ❌ {facility_id}: メニュー項目なし")
            return False
        print(f"  ✅ {facility_id}: メニュー項目取得成功 ({len(menu_items)}項目)")
        
        # 各メニュー項目の表示確認
        for item in menu_items[:3]:  # 最初の3項目のみテスト
            print(f"    - {item.label}: {item.description}")
        
        # exitアクションをテスト
        exit_result = controller.execute_action("exit", {})
        if exit_result and exit_result.is_success():
            print(f"  ✅ {facility_id}: 退出処理成功")
        else:
            print(f"  ⚠️  {facility_id}: 退出処理結果不明")
        
        # 施設から退出
        exit_success = controller.exit()
        if exit_success:
            print(f"  ✅ {facility_id}: 退出成功")
        else:
            print(f"  ❌ {facility_id}: 退出失敗")
            return False
        
        return True
        
    except Exception as e:
        print(f"  💥 {facility_id}: テスト中にエラー - {e}")
        return False


def test_all_facilities():
    """全施設の動作確認"""
    print("🎯 全施設動作確認テスト開始")
    
    # FacilityRegistryにサービスを登録
    registry = FacilityRegistry.get_instance()
    registry.register_all_services()
    print("📋 サービスクラス登録完了")
    
    # モックパーティを作成
    party = create_mock_party()
    print(f"👥 テストパーティ作成: {party.name} (所持金: {party.gold}G)")
    
    # テスト対象施設
    facilities = ["guild", "inn", "shop", "temple", "magic_guild"]
    
    results = {}
    for facility_id in facilities:
        results[facility_id] = test_facility_basic_operations(facility_id, party)
    
    # 結果のまとめ
    print("\n📊 全施設動作確認結果:")
    successful = 0
    for facility_id, success in results.items():
        status = "✅ 成功" if success else "❌ 失敗"
        print(f"  {facility_id}: {status}")
        if success:
            successful += 1
    
    print(f"\n🎉 成功率: {successful}/{len(facilities)} ({100*successful//len(facilities)}%)")
    
    if successful == len(facilities):
        print("🎉 すべての施設が正常に動作しています！")
        return True
    else:
        print("⚠️  一部の施設に問題があります。")
        return False


def test_facility_registry_state():
    """FacilityRegistryの状態確認"""
    print("\n🔍 FacilityRegistry状態確認:")
    
    registry = FacilityRegistry.get_instance()
    
    # 登録されている施設の確認
    facilities = registry.get_facility_list()
    print(f"  登録済み施設: {len(facilities)}個")
    for facility_id in facilities:
        info = registry.get_facility_info(facility_id)
        print(f"    - {facility_id}: {info.get('name', facility_id)}")
    
    # 現在の施設状態
    current_facility = registry.get_current_facility()
    if current_facility:
        print(f"  現在の施設: {current_facility.facility_id}")
    else:
        print("  現在の施設: なし")
    
    return True


if __name__ == "__main__":
    try:
        # FacilityRegistry状態確認
        test_facility_registry_state()
        
        # 全施設動作確認
        success = test_all_facilities()
        
        if success:
            print("\n🎉 全施設動作確認テスト完了 - すべて正常")
        else:
            print("\n❌ 全施設動作確認テスト完了 - 問題あり")
            sys.exit(1)
            
    except Exception as e:
        print(f"\n💥 テスト実行中にエラーが発生: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)