"""
Window System 動作確認スクリプト

基本的な動作を確認するためのテストプログラム
"""

import pygame
import pygame_gui
import sys
from src.ui.window_system import WindowManager, Window
from src.ui.window_system.simple_test_window import SimpleSimpleTestWindow


def main():
    """メイン関数"""
    # Pygame初期化
    pygame.init()
    
    # 画面設定
    screen_width = 1024
    screen_height = 768
    screen = pygame.display.set_mode((screen_width, screen_height))
    pygame.display.set_caption("Window System Test")
    clock = pygame.time.Clock()
    
    # WindowManagerを初期化
    window_manager = WindowManager.get_instance()
    window_manager.initialize_pygame(screen, clock)
    window_manager.set_debug_mode(True)
    
    # テストウィンドウを作成
    root_window = window_manager.create_window(
        SimpleTestWindow, 
        window_id="root_window", 
        title="Root Window"
    )
    window_manager.show_window(root_window)
    
    print("Window System Test Started")
    print("Controls:")
    print("  ESC: Go back / Close window")
    print("  1: Create modal dialog")
    print("  2: Create child window")
    print("  Q: Quit")
    print()
    
    running = True
    while running:
        time_delta = clock.tick(60) / 1000.0
        
        # イベント処理
        events = pygame.event.get()
        for event in events:
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_q:
                    running = False
                elif event.key == pygame.K_1:
                    # モーダルダイアログを作成
                    modal_window = window_manager.create_window(
                        SimpleTestWindow,
                        window_id=f"modal_{pygame.time.get_ticks()}",
                        title="Modal Dialog",
                        parent=window_manager.get_active_window(),
                        modal=True
                    )
                    window_manager.show_window(modal_window)
                elif event.key == pygame.K_2:
                    # 子ウィンドウを作成
                    child_window = window_manager.create_window(
                        SimpleTestWindow,
                        window_id=f"child_{pygame.time.get_ticks()}",
                        title="Child Window",
                        parent=window_manager.get_active_window()
                    )
                    window_manager.show_window(child_window)
        
        # Window Managerにイベントを渡す
        window_manager.handle_global_events(events)
        
        # システム更新
        window_manager.update(time_delta)
        
        # 描画
        screen.fill((64, 64, 64))  # グレー背景
        window_manager.draw(screen)
        
        # デバッグ情報を表示
        if window_manager.debug_mode:
            debug_info = window_manager.get_debug_info()
            print_debug_info(debug_info)
        
        pygame.display.flip()
    
    # クリーンアップ
    window_manager.cleanup()
    pygame.quit()
    print("Window System Test Ended")


def print_debug_info(debug_info):
    """デバッグ情報を出力（簡略版）"""
    stats_line = debug_info[0] if debug_info else "No debug info"
    if "frames_rendered" in stats_line:
        # フレーム数だけを更新して表示
        parts = stats_line.split(",")
        for part in parts:
            if "frames_rendered" in part:
                print(f"\r{part.strip()}", end="", flush=True)
                break


if __name__ == "__main__":
    main()