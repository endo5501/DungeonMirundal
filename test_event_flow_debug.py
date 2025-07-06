#!/usr/bin/env python3
"""
イベントフローデバッグテスト
"""

from src.debug.game_debug_client import GameDebugClient
import time

def test_event_flow():
    """イベントフローを詳細にテストする"""
    client = GameDebugClient()
    
    if not client.wait_for_api():
        print("❌ デバッグAPIに接続できませんでした")
        return False
    
    print("=== イベントフローデバッグテスト開始 ===")
    
    # 初期状態確認
    print("1. 初期状態確認")
    client.screenshot("event_flow_1_initial.jpg")
    
    # 1キーを単発で送信
    print("2. 1キーを単発送信")
    client.send_key(49, down=True)  # 1キー押下
    time.sleep(0.1)
    client.send_key(49, down=False)  # 1キー解放
    time.sleep(1)
    client.screenshot("event_flow_2_after_key_1.jpg")
    
    # ログ確認のための待機
    time.sleep(2)
    
    print("\n=== テスト完了 ===")

if __name__ == "__main__":
    test_event_flow()