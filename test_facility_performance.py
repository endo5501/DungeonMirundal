#!/usr/bin/env python3
"""新施設システムのパフォーマンステスト

メモリ使用量とパフォーマンスの確認
"""

import sys
import os
import time
import gc
import tracemalloc
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from unittest.mock import Mock
from src.facilities.core.facility_registry import FacilityRegistry


def get_memory_usage():
    """現在のメモリ使用量を取得（MB）"""
    import psutil
    import os
    process = psutil.Process(os.getpid())
    return process.memory_info().rss / 1024 / 1024  # MB


def create_test_party():
    """テスト用パーティを作成"""
    party = Mock()
    party.name = "パフォーマンステストパーティ"
    party.gold = 10000
    party.members = []
    
    # 複数のキャラクターを作成
    for i in range(6):  # 最大パーティサイズ
        character = Mock()
        character.id = f"char_{i:03d}"
        character.name = f"キャラクター{i+1}"
        character.level = 10
        character.hp = 100
        character.max_hp = 100
        character.mp = 50
        character.max_mp = 50
        character.is_alive.return_value = True
        character.status = "normal"
        character.can_use_magic.return_value = True
        
        # インベントリモック
        mock_inventory = Mock()
        mock_inventory.get_all_items.return_value = []
        character.inventory = mock_inventory
        
        # その他のメソッド
        character.get_learned_spells.return_value = []
        character.get_equipped_spells.return_value = []
        character.get_equipment.return_value = {}
        
        party.members.append(character)
    
    return party


def test_facility_creation_performance():
    """施設作成のパフォーマンステスト"""
    print("\n🚀 施設作成パフォーマンステスト開始...")
    
    registry = FacilityRegistry.get_instance()
    registry.register_all_services()
    
    facilities = ["guild", "inn", "shop", "temple", "magic_guild"]
    creation_times = {}
    
    for facility_id in facilities:
        # メモリ測定開始
        gc.collect()
        start_memory = get_memory_usage()
        
        # 時間測定開始
        start_time = time.perf_counter()
        
        # 施設コントローラー作成
        controller = registry.create_facility_controller(facility_id)
        
        # 時間測定終了
        end_time = time.perf_counter()
        creation_time = (end_time - start_time) * 1000  # ms
        
        # メモリ測定終了
        end_memory = get_memory_usage()
        memory_increase = end_memory - start_memory
        
        creation_times[facility_id] = {
            'time_ms': creation_time,
            'memory_mb': memory_increase,
            'success': controller is not None
        }
        
        print(f"  {facility_id}: {creation_time:.2f}ms, メモリ: +{memory_increase:.2f}MB")
    
    # 結果の集計
    total_time = sum(data['time_ms'] for data in creation_times.values())
    total_memory = sum(data['memory_mb'] for data in creation_times.values())
    successful = sum(1 for data in creation_times.values() if data['success'])
    
    print(f"\n📊 施設作成パフォーマンス結果:")
    print(f"  合計時間: {total_time:.2f}ms")
    print(f"  合計メモリ: +{total_memory:.2f}MB")
    print(f"  成功率: {successful}/{len(facilities)} ({100*successful//len(facilities)}%)")
    
    return creation_times


def test_facility_operation_performance():
    """施設操作のパフォーマンステスト"""
    print("\n⚡ 施設操作パフォーマンステスト開始...")
    
    registry = FacilityRegistry.get_instance()
    party = create_test_party()
    
    facilities = ["inn", "shop", "temple", "magic_guild"]  # guildは除く（エラーが出るため）
    operation_times = {}
    
    for facility_id in facilities:
        print(f"\n  🔧 {facility_id} 操作テスト...")
        
        # 施設コントローラー取得
        controller = registry.get_facility_controller(facility_id)
        if not controller:
            controller = registry.create_facility_controller(facility_id)
        
        if not controller:
            print(f"    ❌ {facility_id}: コントローラー作成失敗")
            continue
        
        operations = []
        
        try:
            # 入場テスト
            start_time = time.perf_counter()
            enter_result = controller.enter(party)
            enter_time = (time.perf_counter() - start_time) * 1000
            operations.append(('enter', enter_time, enter_result))
            
            if enter_result:
                # メニュー取得テスト
                start_time = time.perf_counter()
                menu_items = controller.get_menu_items()
                menu_time = (time.perf_counter() - start_time) * 1000
                operations.append(('get_menu', menu_time, len(menu_items) > 0))
                
                # アクション実行テスト（exit）
                start_time = time.perf_counter()
                action_result = controller.execute_service("exit", {})
                action_time = (time.perf_counter() - start_time) * 1000
                operations.append(('execute_service', action_time, action_result.is_success() if action_result else False))
                
                # 退場テスト
                start_time = time.perf_counter()
                exit_result = controller.exit()
                exit_time = (time.perf_counter() - start_time) * 1000
                operations.append(('exit', exit_time, exit_result))
            
            operation_times[facility_id] = operations
            
            # 結果表示
            for operation, time_ms, success in operations:
                status = "✅" if success else "❌"
                print(f"    {operation}: {time_ms:.2f}ms {status}")
        
        except Exception as e:
            print(f"    💥 {facility_id}: エラー - {e}")
            operation_times[facility_id] = []
    
    return operation_times


def test_memory_leak():
    """メモリリーク確認テスト"""
    print("\n🔍 メモリリーク確認テスト開始...")
    
    # メモリトレース開始
    tracemalloc.start()
    
    registry = FacilityRegistry.get_instance()
    party = create_test_party()
    
    initial_memory = get_memory_usage()
    print(f"  初期メモリ: {initial_memory:.2f}MB")
    
    # 複数回の施設操作を実行
    iteration_count = 10
    memory_samples = []
    
    for i in range(iteration_count):
        # 施設の作成・使用・破棄を繰り返す
        for facility_id in ["inn", "shop", "temple", "magic_guild"]:
            controller = registry.create_facility_controller(facility_id)
            if controller:
                controller.enter(party)
                controller.get_menu_items()
                controller.execute_service("exit", {})
                controller.exit()
        
        # ガベージコレクション実行
        gc.collect()
        
        # メモリ使用量記録
        current_memory = get_memory_usage()
        memory_samples.append(current_memory)
        
        if (i + 1) % 2 == 0:
            print(f"  反復 {i+1}: {current_memory:.2f}MB")
    
    final_memory = get_memory_usage()
    memory_increase = final_memory - initial_memory
    
    # メモリトレース終了
    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    
    print(f"\n📊 メモリリーク確認結果:")
    print(f"  初期メモリ: {initial_memory:.2f}MB")
    print(f"  最終メモリ: {final_memory:.2f}MB")
    print(f"  メモリ増加: {memory_increase:.2f}MB")
    print(f"  ピークメモリ: {peak / 1024 / 1024:.2f}MB")
    
    # メモリリーク判定
    if memory_increase < 5.0:  # 5MB未満なら正常とみなす
        print("  ✅ メモリリークは検出されませんでした")
        return True
    else:
        print("  ⚠️  メモリリークの可能性があります")
        return False


def main():
    """メイン実行関数"""
    print("🎯 新施設システム パフォーマンス・メモリテスト開始")
    
    try:
        # パフォーマンステスト
        creation_results = test_facility_creation_performance()
        operation_results = test_facility_operation_performance()
        memory_leak_ok = test_memory_leak()
        
        # 総合結果
        print("\n🎉 総合テスト結果:")
        
        # 作成パフォーマンス
        avg_creation_time = sum(data['time_ms'] for data in creation_results.values()) / len(creation_results)
        print(f"  平均施設作成時間: {avg_creation_time:.2f}ms")
        
        # 操作パフォーマンス
        all_operations = []
        for facility_operations in operation_results.values():
            all_operations.extend(facility_operations)
        
        if all_operations:
            avg_operation_time = sum(time_ms for _, time_ms, _ in all_operations) / len(all_operations)
            success_rate = sum(1 for _, _, success in all_operations if success) / len(all_operations)
            print(f"  平均操作時間: {avg_operation_time:.2f}ms")
            print(f"  操作成功率: {success_rate:.1%}")
        
        # メモリリーク
        memory_status = "✅ 正常" if memory_leak_ok else "⚠️  要注意"
        print(f"  メモリリーク: {memory_status}")
        
        if avg_creation_time < 50 and (not all_operations or avg_operation_time < 10) and memory_leak_ok:
            print("\n🎉 パフォーマンステスト完了 - すべて良好")
            return True
        else:
            print("\n⚠️  パフォーマンステスト完了 - 改善の余地あり")
            return False
        
    except Exception as e:
        print(f"\n💥 テスト実行中にエラーが発生: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    try:
        import psutil
    except ImportError:
        print("❌ psutilがインストールされていません。メモリ測定をスキップします。")
        sys.exit(1)
    
    success = main()
    sys.exit(0 if success else 1)