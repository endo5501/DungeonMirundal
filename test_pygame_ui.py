#!/usr/bin/env python3
"""Pygame UI システムのテスト"""

import pygame
import sys
from src.utils.logger import logger
from src.ui.base_ui_pygame import initialize_ui_manager, UIText, UIButton, UIMenu

def test_pygame_ui():
    """Pygame UI システムのテスト"""
    logger.info("Pygame UI テスト開始")
    
    # Pygame初期化
    pygame.init()
    
    # 画面設定
    screen = pygame.display.set_mode((800, 600))
    pygame.display.set_caption("Pygame UI テスト")
    clock = pygame.time.Clock()
    
    # UIマネージャー初期化
    ui_manager = initialize_ui_manager(screen)
    
    # テストメニューを作成
    menu = UIMenu("test_menu", "テストメニュー")
    
    # ボタンを追加
    start_button = UIButton("start", "ゲーム開始", 300, 200, 200, 50)
    start_button.on_click = lambda: logger.info("ゲーム開始がクリックされました")
    menu.add_element(start_button)
    
    exit_button = UIButton("exit", "終了", 300, 300, 200, 50)
    exit_button.on_click = lambda: logger.info("終了がクリックされました")
    menu.add_element(exit_button)
    
    # メニューをUIマネージャーに追加
    ui_manager.add_menu(menu)
    menu.show()
    
    # テキスト要素を追加
    title_text = UIText("title", "Pygame UI テスト", 400, 100)
    ui_manager.add_element(title_text)
    title_text.show()
    
    running = True
    frame_count = 0
    
    logger.info("Pygame UIテストを開始しました")
    
    while running and frame_count < 600:  # 約10秒間実行
        # イベント処理
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
            else:
                # UIマネージャーでイベント処理
                ui_manager.handle_event(event)
        
        # 画面クリア
        screen.fill((40, 40, 60))
        
        # UI描画
        ui_manager.render()
        
        # FPS表示
        if ui_manager.default_font:
            fps_text = ui_manager.default_font.render(f"FPS: {int(clock.get_fps())}", True, (255, 255, 0))
            screen.blit(fps_text, (10, 10))
        
        # 画面更新
        pygame.display.flip()
        clock.tick(60)
        frame_count += 1
    
    pygame.quit()
    logger.info("Pygame UI テスト完了")
    return True

if __name__ == "__main__":
    test_pygame_ui()