#!/usr/bin/env python
"""ESCキーによるクラッシュを調査するスクリプト"""

from src.debug.game_debug_client import GameDebugClient
import time

def investigate_esc_crash():
    client = GameDebugClient()
    
    # APIが利用可能か確認
    if not client.wait_for_api():
        print("Game API is not available. Please ensure the game is running.")
        return
    
    print("Game API is available")
    
    # 1. 現在の画面のスクリーンショットを取得
    print("\n1. Taking screenshot before ESC...")
    client.screenshot("before_esc.jpg")
    print("   Screenshot saved: before_esc.jpg")
    
    # 2. UI階層情報を取得
    print("\n2. Getting UI hierarchy...")
    hierarchy = client.get_ui_hierarchy()
    if hierarchy:
        print(f"   Current window stack: {hierarchy.get('window_stack', [])}")
        print(f"   WindowManager available: {hierarchy.get('window_manager_available')}")
    
    # 3. ゲーム状態を取得（可能な場合）
    print("\n3. Getting game state...")
    try:
        state = client.get_game_state()
        print(f"   Game state: {state}")
    except Exception as e:
        print(f"   Could not get game state: {e}")
    
    # 4. ESCキーを送信
    print("\n4. Sending ESC key...")
    try:
        client.press_escape()
        print("   ESC key sent successfully")
        
        # 少し待機
        time.sleep(1.0)
        
        # クラッシュしていないか確認
        if client.is_api_available():
            print("   Game is still running after ESC")
            
            # クラッシュ後のスクリーンショットを取得
            client.screenshot("after_esc.jpg")
            print("   Screenshot saved: after_esc.jpg")
            
            # UI階層情報を再取得
            hierarchy_after = client.get_ui_hierarchy()
            if hierarchy_after:
                print(f"   Window stack after ESC: {hierarchy_after.get('window_stack', [])}")
        else:
            print("   Game API is no longer available - game may have crashed!")
            
    except Exception as e:
        print(f"   Error while sending ESC: {e}")
        print("   Game may have crashed!")

if __name__ == "__main__":
    investigate_esc_crash()