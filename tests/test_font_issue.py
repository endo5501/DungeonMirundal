#!/usr/bin/env python3
"""pygame-gui日本語フォント問題のテスト"""

import pygame
import pygame_gui
import os
import sys


def test_font_functionality():
    """フォント機能のテスト"""
    # Pygameを初期化
    pygame.init()
    screen = pygame.display.set_mode((800, 600))
    pygame.display.set_caption("フォントテスト")
    clock = pygame.time.Clock()

    # テーマファイルパス
    theme_path = "/home/satorue/Dungeon/config/ui_theme.json"

    # 1. 通常のpygame-gui初期化
    print("=== Test 1: 通常のpygame-gui初期化 ===")
    ui_manager1 = pygame_gui.UIManager((800, 600), theme_path)

    # ボタンを作成
    button1 = pygame_gui.elements.UIButton(
        relative_rect=pygame.Rect(50, 50, 200, 50),
        text="テスト1: 日本語",
        manager=ui_manager1
    )

    # 2. フォント事前ロード後の初期化
    print("\n=== Test 2: フォント事前ロード後の初期化 ===")
    japanese_font_path = "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"
    if os.path.exists(japanese_font_path):
        try:
            test_font = pygame.font.Font(japanese_font_path, 14)
            print(f"日本語フォントを事前ロード: {japanese_font_path}")
        except Exception as e:
            print(f"フォントロードエラー: {e}")

    ui_manager2 = pygame_gui.UIManager((800, 600), theme_path)

    button2 = pygame_gui.elements.UIButton(
        relative_rect=pygame.Rect(50, 150, 200, 50),
        text="テスト2: 日本語",
        manager=ui_manager2
    )

    # 3. pygame.font.SysFontの確認
    print("\n=== Test 3: pygame.font.SysFont ===")
    available_fonts = pygame.font.get_fonts()
    print(f"利用可能なフォント数: {len(available_fonts)}")
    if 'noto' in available_fonts:
        print("'noto'フォントが見つかりました")
    else:
        print("'noto'フォントが見つかりません")
        # notoを含むフォントを探す
        noto_fonts = [f for f in available_fonts if 'noto' in f.lower()]
        if noto_fonts:
            print(f"Noto関連フォント: {noto_fonts[:5]}...")

    # 4. 直接Pygameでレンダリング（比較用）
    print("\n=== Test 4: 直接Pygameでレンダリング ===")
    try:
        jp_font = pygame.font.Font(japanese_font_path, 24)
        text_surface = jp_font.render("直接レンダリング: 日本語", True, (255, 255, 255))
        print("直接レンダリング成功")
    except Exception as e:
        print(f"直接レンダリングエラー: {e}")

    pygame.quit()
    assert True


if __name__ == "__main__":
    # メインループはスクリプト直接実行時のみ
    test_font_functionality()
    
    # 直接実行時のメインループ
    pygame.init()
    screen = pygame.display.set_mode((800, 600))
    pygame.display.set_caption("フォントテスト")
    clock = pygame.time.Clock()
    
    theme_path = "/home/satorue/Dungeon/config/ui_theme.json"
    ui_manager1 = pygame_gui.UIManager((800, 600), theme_path)
    ui_manager2 = pygame_gui.UIManager((800, 600), theme_path)
    
    button1 = pygame_gui.elements.UIButton(
        relative_rect=pygame.Rect(50, 50, 200, 50),
        text="テスト1: 日本語",
        manager=ui_manager1
    )
    
    button2 = pygame_gui.elements.UIButton(
        relative_rect=pygame.Rect(50, 150, 200, 50),
        text="テスト2: 日本語",
        manager=ui_manager2
    )
    
    japanese_font_path = "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"
    try:
        jp_font = pygame.font.Font(japanese_font_path, 24)
        text_surface = jp_font.render("直接レンダリング: 日本語", True, (255, 255, 255))
    except Exception as e:
        text_surface = None
    
    running = True
    while running:
        time_delta = clock.tick(60) / 1000.0
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            
            ui_manager1.process_events(event)
            ui_manager2.process_events(event)
        
        ui_manager1.update(time_delta)
        ui_manager2.update(time_delta)
        
        screen.fill((0, 0, 0))
        
        ui_manager1.draw_ui(screen)
        ui_manager2.draw_ui(screen)
        
        # 直接レンダリングのテキストを表示
        if text_surface:
            screen.blit(text_surface, (50, 300))
        
        pygame.display.flip()

    pygame.quit()
    sys.exit()