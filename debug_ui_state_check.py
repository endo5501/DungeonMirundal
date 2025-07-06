#!/usr/bin/env python3
"""UI状態確認スクリプト - 冒険者ギルドのパネル状態を確認"""

import time
from src.debug.game_debug_client import GameDebugClient

def main():
    client = GameDebugClient()
    
    # APIが利用可能になるまで待機
    if not client.wait_for_api():
        print("Error: API server is not available")
        return
    
    print("UI状態確認を開始します...")
    
    # 1. 初期スクリーンショットを取得
    print("\n1. 初期状態のスクリーンショット取得")
    client.screenshot("debug_1_initial.jpg")
    hierarchy = client.get_ui_hierarchy()
    print(f"   Window stack: {hierarchy.get('window_stack', [])}")
    time.sleep(1)
    
    # 2. 冒険者ギルドをクリック
    print("\n2. 冒険者ギルドをクリック (286, 121)")
    client.send_mouse(286, 121, "down")
    time.sleep(0.1)
    client.send_mouse(286, 121, "up")
    time.sleep(1.5)  # 画面遷移を待つ
    
    client.screenshot("debug_2_guild_entered.jpg")
    hierarchy = client.get_ui_hierarchy()
    print(f"   Window stack: {hierarchy.get('window_stack', [])}")
    
    # 3. ギルド内でパネル切り替え
    print("\n3. ギルド内でパネル切り替え")
    
    # パーティ編成パネル（座標推定）
    print("   3-1. パーティ編成パネルをクリック")
    client.send_mouse(400, 200, "down")
    time.sleep(0.1)
    client.send_mouse(400, 200, "up")
    time.sleep(1)
    client.screenshot("debug_3_1_party_panel.jpg")
    
    # クラス変更パネル（座標推定）
    print("   3-2. クラス変更パネルをクリック")
    client.send_mouse(400, 250, "down")
    time.sleep(0.1)
    client.send_mouse(400, 250, "up")
    time.sleep(1)
    client.screenshot("debug_3_2_class_panel.jpg")
    
    # 別のパネルに切り替え
    print("   3-3. 別のパネルをクリック")
    client.send_mouse(400, 300, "down")
    time.sleep(0.1)
    client.send_mouse(400, 300, "up")
    time.sleep(1)
    client.screenshot("debug_3_3_other_panel.jpg")
    
    hierarchy = client.get_ui_hierarchy()
    print(f"   Window stack after panel switches: {hierarchy.get('window_stack', [])}")
    
    # 4. ESCキーで退出
    print("\n4. ESCキーで退出")
    client.send_key(27)  # ESCキー
    time.sleep(1.5)  # 画面遷移を待つ
    
    client.screenshot("debug_4_after_esc.jpg")
    hierarchy = client.get_ui_hierarchy()
    print(f"   Window stack: {hierarchy.get('window_stack', [])}")
    
    # 5. 再度冒険者ギルドをクリック
    print("\n5. 再度冒険者ギルドをクリック")
    client.send_mouse(286, 121, "down")
    time.sleep(0.1)
    client.send_mouse(286, 121, "up")
    time.sleep(1.5)  # 画面遷移を待つ
    
    client.screenshot("debug_5_guild_reentered.jpg")
    
    # 6. UI階層情報を詳細に取得
    print("\n6. UI階層情報の詳細確認")
    hierarchy = client.get_ui_hierarchy()
    print(f"   WindowManager available: {hierarchy.get('window_manager_available', False)}")
    print(f"   Window stack: {hierarchy.get('window_stack', [])}")
    print(f"   Status: {hierarchy.get('status', 'unknown')}")
    
    # 再度パネルをクリックして状態を確認
    print("\n   再度パネルをクリックして状態確認")
    client.send_mouse(400, 200, "down")
    time.sleep(0.1)
    client.send_mouse(400, 200, "up")
    time.sleep(1)
    client.screenshot("debug_6_panel_check.jpg")
    
    # 7. 最終スクリーンショット
    print("\n7. 最終スクリーンショット")
    client.screenshot("debug_7_final.jpg")
    hierarchy = client.get_ui_hierarchy()
    print(f"   Final window stack: {hierarchy.get('window_stack', [])}")
    
    print("\n確認完了！")
    print("生成されたスクリーンショット:")
    print("  - debug_1_initial.jpg: 初期状態")
    print("  - debug_2_guild_entered.jpg: ギルド入場後")
    print("  - debug_3_1_party_panel.jpg: パーティ編成パネル")
    print("  - debug_3_2_class_panel.jpg: クラス変更パネル")
    print("  - debug_3_3_other_panel.jpg: 別のパネル")
    print("  - debug_4_after_esc.jpg: ESC退出後")
    print("  - debug_5_guild_reentered.jpg: ギルド再入場後")
    print("  - debug_6_panel_check.jpg: パネル状態確認")
    print("  - debug_7_final.jpg: 最終状態")

if __name__ == "__main__":
    main()