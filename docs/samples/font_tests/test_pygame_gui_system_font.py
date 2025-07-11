#!/usr/bin/env python3
"""
システムフォントを直接使用してpygame_guiをテスト
"""
import pygame
import pygame_gui
import os

def test_pygame_gui_system_font():
    """システムフォントを使用したテスト"""
    pygame.init()
    
    # 画面設定
    window_size = (800, 600)
    screen = pygame.display.set_mode(window_size)
    pygame.display.set_caption('pygame_gui システムフォントテスト')
    
    # システムフォントを直接探す
    for name in ["Hiragino Sans", "YuGothic", "Apple SD Gothic Neo"]:
        path = pygame.font.match_font(name)
        if path:
            print(f"システムフォント発見: {name} -> {path}")
            system_font_path = path
            break
    else:
        print("システムフォントが見つかりません")
        return
    
    # UIマネージャー初期化
    manager = pygame_gui.UIManager(window_size)
    
    # システムフォントを登録
    try:
        manager.add_font_paths("system_jp_font", system_font_path)
        print(f"✓ システムフォント登録成功: system_jp_font -> {system_font_path}")
    except Exception as e:
        print(f"✗ システムフォント登録失敗: {e}")
        return
    
    # プリロード
    try:
        manager.preload_fonts([{
            "name": "system_jp_font",
            "style": "regular",
            "point_size": 20
        }])
        print("✓ システムフォントプリロード成功")
    except Exception as e:
        print(f"✗ システムフォントプリロード失敗: {e}")
    
    # テーマ設定
    theme_data = {
        "defaults": {
            "font": {
                "name": "system_jp_font",
                "size": "20",
                "style": "regular"
            },
            "colours": {
                "normal_text": "#FFFFFF",
                "normal_bg": "#25292e",
                "normal_border": "#DDDDDD"
            }
        }
    }
    
    try:
        manager.get_theme().load_theme(theme_data)
        print("✓ システムフォントテーマ読み込み成功")
    except Exception as e:
        print(f"✗ システムフォントテーマ読み込み失敗: {e}")
        return
    
    # シンプルな日本語ボタンを1つだけ作成
    try:
        button = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect(100, 100, 200, 60),
            text="こんにちは",
            manager=manager
        )
        print("✓ 日本語ボタン作成成功")
    except Exception as e:
        print(f"✗ 日本語ボタン作成失敗: {e}")
        return
    
    # メインループ
    clock = pygame.time.Clock()
    running = True
    
    print("ウィンドウを表示中... クリックまたはESCキーで終了")
    
    while running:
        time_delta = clock.tick(60) / 1000.0
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                running = False
            
            manager.process_events(event)
        
        manager.update(time_delta)
        
        screen.fill((50, 50, 50))
        manager.draw_ui(screen)
        
        pygame.display.flip()
    
    pygame.quit()
    print("システムフォントテスト終了")

if __name__ == "__main__":
    test_pygame_gui_system_font()