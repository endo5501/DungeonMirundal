#!/usr/bin/env python3
"""
修正版close_window()メソッドのテストスクリプト
"""

from src.debug.game_debug_client import GameDebugClient
import time

def test_close_window_fix():
    """修正版close_window()メソッドをテストする"""
    client = GameDebugClient()
    
    if not client.wait_for_api():
        print("❌ デバッグAPIに接続できませんでした")
        return False
    
    print("=== 修正版close_window()テスト開始 ===")
    
    # 初期状態確認
    print("1. 初期状態のスクリーンショット取得")
    client.screenshot("test_close_window_1_initial.jpg")
    
    # 初期状態のUI階層を確認
    hierarchy = client.get_ui_hierarchy()
    print(f"初期ウィンドウスタック: {hierarchy.get('window_stack', [])}")
    
    # ダンジョン入口クリック
    print("2. ダンジョン入口をクリック (6キー)")
    client.send_key(54)  # 6キー
    time.sleep(2)
    client.screenshot("test_close_window_2_dungeon_screen.jpg")
    
    # ダンジョン画面の確認
    hierarchy = client.get_ui_hierarchy()
    print(f"ダンジョン画面ウィンドウスタック: {hierarchy.get('window_stack', [])}")
    
    # 街に戻るクリック
    print("3. 街に戻るをクリック (4キー)")
    client.send_key(52)  # 4キー
    time.sleep(2)
    
    # 結果確認
    print("4. 結果確認")
    client.screenshot("test_close_window_3_result.jpg")
    hierarchy = client.get_ui_hierarchy()
    
    print("\n=== 最終状態のウィンドウスタック ===")
    window_stack = hierarchy.get('window_stack', [])
    for i, window in enumerate(window_stack):
        print(f"  {i}: {window}")
    
    # UI要素の確認
    ui_elements = hierarchy.get('ui_elements', [])
    buttons = [elem for elem in ui_elements if elem.get('type') == 'UIButton']
    
    print(f"\n=== UI要素数: {len(ui_elements)} ===")
    print(f"=== ボタン数: {len(buttons)} ===")
    
    if buttons:
        print("\n=== 地上メニューボタンの状態 ===")
        for button in buttons:
            details = button.get('details', {})
            text = details.get('text', 'Unknown')
            visible = button.get('visible', False)
            print(f"  {text}: visible={visible}")
    else:
        print("\n=== ボタン情報は取得できませんでした ===")
        print("（技術的制約により詳細なUI要素情報は取得不可）")
    
    # 成功判定
    # OverworldMainWindowが表示されていることを確認
    overworld_in_stack = any("OverworldMainWindow" in window for window in window_stack)
    dungeon_in_stack = any("DungeonWindow" in window for window in window_stack)
    
    print(f"\n=== テスト結果 ===")
    print(f"OverworldMainWindow表示: {'✅' if overworld_in_stack else '❌'}")
    print(f"DungeonWindow残存: {'❌' if dungeon_in_stack else '✅'}")
    
    success = overworld_in_stack and not dungeon_in_stack
    print(f"テスト結果: {'✅ 成功' if success else '❌ 失敗'}")
    
    print("\n=== テスト完了 ===")
    return success

if __name__ == "__main__":
    test_close_window_fix()