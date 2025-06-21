#!/usr/bin/env python3
"""Pygame基本動作テスト"""

import pygame
import sys
from src.utils.logger import logger
from src.core.config_manager import config_manager

def test_pygame_basic():
    """Pygame基本機能のテスト"""
    logger.info("Pygame基本テスト開始")
    
    # Pygame初期化
    pygame.init()
    
    # 画面設定
    screen = pygame.display.set_mode((800, 600))
    pygame.display.set_caption("Pygame基本テスト")
    clock = pygame.time.Clock()
    
    # フォント初期化
    try:
        font = pygame.font.Font(None, 36)
    except:
        font = None
    
    running = True
    frame_count = 0
    
    logger.info("Pygameウィンドウを開きました")
    
    while running and frame_count < 300:  # 約5秒間実行
        # イベント処理
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
        
        # 画面クリア
        screen.fill((0, 50, 100))
        
        # テキスト描画
        if font:
            text = font.render(f"Pygame動作テスト フレーム: {frame_count}", True, (255, 255, 255))
            text_rect = text.get_rect(center=(400, 300))
            screen.blit(text, text_rect)
            
            # FPS表示
            fps_text = font.render(f"FPS: {int(clock.get_fps())}", True, (255, 255, 0))
            screen.blit(fps_text, (10, 10))
        
        # 画面更新
        pygame.display.flip()
        clock.tick(60)
        frame_count += 1
    
    pygame.quit()
    logger.info("Pygame基本テスト完了")
    return True

if __name__ == "__main__":
    test_pygame_basic()