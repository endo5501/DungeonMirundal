#!/usr/bin/env python3
"""
DungeonSelectionWindow のデバッグテストスクリプト
"""

import time
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.debug.game_debug_client import GameDebugClient
from src.debug.debug_helper import DebugHelper

def main():
    """DungeonSelectionWindowのデバッグテストを実行"""
    
    client = GameDebugClient()
    helper = DebugHelper()
    
    # APIが利用可能になるまで待機
    print("デバッグAPIの準備を待機中...")
    if not client.wait_for_api(max_wait=30):
        print("❌ デバッグAPIに接続できませんでした")
        return False
    
    print("✅ デバッグAPIに接続しました")
    
    # 初期状態をキャプチャ
    print("\n📸 初期状態をキャプチャ中...")
    client.screenshot("debug_initial_state.jpg")
    
    # UI階層を確認
    print("\n🔍 UI階層を確認中...")
    hierarchy = client.get_ui_hierarchy()
    if hierarchy:
        print(f"WindowManager利用可能: {hierarchy.get('window_manager_available')}")
        print(f"ウィンドウスタック: {hierarchy.get('window_stack')}")
    
    # ダンジョン入口ボタンを探してクリック
    print("\n🎯 ダンジョン入口ボタンを探してクリック中...")
    
    # 画面の右下あたりにダンジョン入口ボタンがあると仮定
    # 試行する座標（一般的なレイアウトの場合）
    button_coordinates = [
        (400, 500),  # 画面中央下
        (600, 500),  # 画面右下
        (800, 500),  # 画面右下
        (700, 400),  # 画面右中央
        (500, 400),  # 画面中央
    ]
    
    for x, y in button_coordinates:
        print(f"  座標 ({x}, {y}) をクリック中...")
        client.send_mouse(x, y, "down")
        time.sleep(0.1)
        client.send_mouse(x, y, "up")
        time.sleep(1)
        
        # スクリーンショットを撮って状態変化を確認
        filename = f"debug_after_click_{x}_{y}.jpg"
        client.screenshot(filename)
        print(f"  スクリーンショット保存: {filename}")
        
        # UI階層を確認
        hierarchy = client.get_ui_hierarchy()
        if hierarchy:
            window_stack = hierarchy.get('window_stack', [])
            if any('dungeon' in str(w).lower() for w in window_stack):
                print(f"✅ ダンジョン選択ウィンドウが開きました！")
                print(f"現在のウィンドウ: {window_stack}")
                break
    else:
        print("❌ ダンジョン選択ウィンドウが見つかりませんでした")
        return False
    
    # DungeonSelectionWindowが開いた状態での操作テスト
    print("\n🧪 DungeonSelectionWindowの操作テストを開始...")
    
    # 現在の状態をキャプチャ
    client.screenshot("debug_dungeon_selection_opened.jpg")
    
    # [新規作成]ボタンをクリック
    print("\n🆕 [新規作成]ボタンをクリック中...")
    # 新規作成ボタンの座標を推定 (ダンジョン選択ウィンドウ内)
    create_button_coords = [
        (341, 540),  # 計算された座標
        (350, 540),  # 微調整
        (330, 540),  # 微調整
        (350, 530),  # Y軸微調整
        (350, 550),  # Y軸微調整
    ]
    
    for x, y in create_button_coords:
        print(f"  新規作成ボタン座標 ({x}, {y}) をクリック中...")
        client.send_mouse(x, y, "down")
        time.sleep(0.1)
        client.send_mouse(x, y, "up")
        time.sleep(1)
        
        # スクリーンショットを撮って状態変化を確認
        client.screenshot(f"debug_after_create_button_{x}_{y}.jpg")
        
        # 少し待機してみる
        time.sleep(2)
        break
    
    # [街に戻る]ボタンをクリック
    print("\n🏠 [街に戻る]ボタンをクリック中...")
    # 街に戻るボタンの座標を推定
    back_button_coords = [
        (700, 540),  # 計算された座標
        (710, 540),  # 微調整
        (690, 540),  # 微調整
        (700, 530),  # Y軸微調整
        (700, 550),  # Y軸微調整
    ]
    
    for x, y in back_button_coords:
        print(f"  街に戻るボタン座標 ({x}, {y}) をクリック中...")
        client.send_mouse(x, y, "down")
        time.sleep(0.1)
        client.send_mouse(x, y, "up")
        time.sleep(1)
        
        # スクリーンショットを撮って状態変化を確認
        client.screenshot(f"debug_after_back_button_{x}_{y}.jpg")
        
        # UI階層を確認
        hierarchy = client.get_ui_hierarchy()
        if hierarchy:
            window_stack = hierarchy.get('window_stack', [])
            print(f"ウィンドウスタック: {window_stack}")
            if not any('dungeon' in str(w).lower() for w in window_stack):
                print("✅ ダンジョン選択ウィンドウが閉じました")
                break
        
        time.sleep(2)
        break
    
    # 最終状態をキャプチャ
    print("\n📸 最終状態をキャプチャ中...")
    client.screenshot("debug_final_state.jpg")
    
    # 入力履歴を確認
    print("\n📋 入力履歴を確認中...")
    history = client.get_input_history()
    if history:
        print(f"入力履歴: {len(history.get('history', []))} 件")
        for i, entry in enumerate(history.get('history', [])[-5:]):  # 最新5件を表示
            print(f"  {i+1}. {entry}")
    
    print("\n✅ デバッグテストが完了しました")
    print("スクリーンショットファイルを確認して、ボタンの動作を確認してください。")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)