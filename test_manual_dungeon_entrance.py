#!/usr/bin/env python3
"""
手動でダンジョン入口にアクセスするテスト
"""

from src.debug.game_debug_client import GameDebugClient
import time

def test_manual_dungeon_entrance():
    """手動でダンジョン入口にアクセスするテスト"""
    client = GameDebugClient()
    
    if not client.wait_for_api():
        print("❌ デバッグAPIに接続できませんでした")
        return False
    
    print("=== 手動ダンジョン入口テスト開始 ===")
    
    # 初期状態確認
    print("1. 初期状態のスクリーンショット取得")
    client.screenshot("manual_test_1_initial.jpg")
    
    # 初期状態のUI階層を確認
    hierarchy = client.get_ui_hierarchy()
    print(f"初期ウィンドウスタック: {hierarchy.get('window_stack', [])}")
    
    # 1キー試行
    print("2. 1キー試行")
    client.send_key(49)  # 1キー
    time.sleep(1)
    client.screenshot("manual_test_2_key_1.jpg")
    
    hierarchy = client.get_ui_hierarchy()
    print(f"1キー後ウィンドウスタック: {hierarchy.get('window_stack', [])}")
    
    # 2キー試行
    print("3. 2キー試行")
    client.send_key(50)  # 2キー
    time.sleep(1)
    client.screenshot("manual_test_3_key_2.jpg")
    
    hierarchy = client.get_ui_hierarchy()
    print(f"2キー後ウィンドウスタック: {hierarchy.get('window_stack', [])}")
    
    # 3キー試行
    print("4. 3キー試行")
    client.send_key(51)  # 3キー
    time.sleep(1)
    client.screenshot("manual_test_4_key_3.jpg")
    
    hierarchy = client.get_ui_hierarchy()
    print(f"3キー後ウィンドウスタック: {hierarchy.get('window_stack', [])}")
    
    # 4キー試行
    print("5. 4キー試行")
    client.send_key(52)  # 4キー
    time.sleep(1)
    client.screenshot("manual_test_5_key_4.jpg")
    
    hierarchy = client.get_ui_hierarchy()
    print(f"4キー後ウィンドウスタック: {hierarchy.get('window_stack', [])}")
    
    # 5キー試行
    print("6. 5キー試行")
    client.send_key(53)  # 5キー
    time.sleep(1)
    client.screenshot("manual_test_6_key_5.jpg")
    
    hierarchy = client.get_ui_hierarchy()
    print(f"5キー後ウィンドウスタック: {hierarchy.get('window_stack', [])}")
    
    # 6キー試行
    print("7. 6キー試行")
    client.send_key(54)  # 6キー
    time.sleep(1)
    client.screenshot("manual_test_7_key_6.jpg")
    
    hierarchy = client.get_ui_hierarchy()
    print(f"6キー後ウィンドウスタック: {hierarchy.get('window_stack', [])}")
    
    print("\n=== 手動テスト完了 ===")

if __name__ == "__main__":
    test_manual_dungeon_entrance()