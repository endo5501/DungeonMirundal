#!/usr/bin/env python3
"""
load_jp_fontアプローチでpygame_guiをテスト
"""
import pygame
import pygame_gui
import os

def load_jp_font_path():
    """日本語フォントのパスを取得"""
    # まず同梱フォントを優先（絶対パス）
    current_dir = os.path.dirname(os.path.abspath(__file__))
    local_fonts = [
        os.path.join(current_dir, "assets/fonts/NotoSansCJKJP-Regular.otf"),
        os.path.join(current_dir, "assets/fonts/NotoSansJP-Regular.otf"),
        os.path.join(current_dir, "assets/fonts/ipag.ttf")
    ]
    for f in local_fonts:
        if os.path.exists(f):
            return f

    # 次にシステムフォント候補
    for name in ["Hiragino Sans", "YuGothic", "Apple SD Gothic Neo"]:
        path = pygame.font.match_font(name)
        if path:
            return path

    # 最後の手段
    return None

def test_pygame_gui_with_jp_font():
    """pygame_guiでload_jp_fontアプローチをテスト"""
    pygame.init()
    
    # 画面設定
    window_size = (800, 600)
    screen = pygame.display.set_mode(window_size)
    pygame.display.set_caption('pygame_gui load_jp_fontテスト')
    
    # 日本語フォントパスを取得
    jp_font_path = load_jp_font_path()
    print(f"日本語フォントパス: {jp_font_path}")
    
    if not jp_font_path:
        print("日本語フォントが見つかりません")
        return
    
    # 簡単なテーマファイルを辞書で定義（システムフォントパス使用）
    theme_data = {
        "defaults": {
            "font": {
                "name": jp_font_path,  # システムフォントの絶対パスを直接指定
                "size": "16"
            },
            "colours": {
                "normal_text": "#FFFFFF",
                "normal_bg": "#25292e",
                "normal_border": "#DDDDDD"
            }
        }
    }
    
    # UIマネージャー初期化（テーマ辞書を直接渡す）
    try:
        manager = pygame_gui.UIManager(window_size)
        # テーマデータを読み込み
        manager.get_theme().load_theme(theme_data)
        print("✓ テーマデータ読み込み成功")
    except Exception as e:
        print(f"✗ テーマデータ読み込み失敗: {e}")
        return
    
    # 日本語テキストを含むUI要素を作成
    japanese_texts = [
        "こんにちは",
        "冒険者ギルド", 
        "宿屋",
        "商店",
        "寺院"
    ]
    
    buttons = []
    for i, text in enumerate(japanese_texts):
        try:
            button = pygame_gui.elements.UIButton(
                relative_rect=pygame.Rect(50, 50 + i * 60, 200, 50),
                text=text,
                manager=manager
            )
            buttons.append(button)
            print(f"✓ ボタン作成成功: {text}")
        except Exception as e:
            print(f"✗ ボタン作成失敗: {text} - {e}")
    
    # ラベルも作成
    label = pygame_gui.elements.UILabel(
        relative_rect=pygame.Rect(300, 50, 400, 30),
        text="load_jp_fontアプローチテスト",
        manager=manager
    )
    
    # メインループ
    clock = pygame.time.Clock()
    running = True
    
    print("ウィンドウを表示中... ESCキーで終了")
    
    while running:
        time_delta = clock.tick(60) / 1000.0
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
            
            manager.process_events(event)
        
        manager.update(time_delta)
        
        screen.fill((50, 50, 50))  # ダークグレー背景
        manager.draw_ui(screen)
        
        pygame.display.flip()
    
    pygame.quit()
    print("pygame_gui load_jp_fontテスト終了")

if __name__ == "__main__":
    test_pygame_gui_with_jp_font()