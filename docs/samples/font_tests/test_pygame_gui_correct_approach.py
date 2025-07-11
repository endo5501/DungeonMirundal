#!/usr/bin/env python3
"""
ChatGPTの助言に従った正しいpygame_guiフォント設定
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

def test_pygame_gui_correct_approach():
    """ChatGPTの助言に従った正しいアプローチでテスト"""
    pygame.init()
    
    # 画面設定
    window_size = (800, 600)
    screen = pygame.display.set_mode(window_size)
    pygame.display.set_caption('pygame_gui 正しいアプローチテスト')
    
    # 日本語フォントパスを取得
    jp_font_path = load_jp_font_path()
    print(f"日本語フォントパス: {jp_font_path}")
    
    if not jp_font_path:
        print("日本語フォントが見つかりません")
        return
    
    # UIマネージャー初期化
    manager = pygame_gui.UIManager(window_size)
    
    # ① エイリアス "jp_font" として登録
    try:
        # add_font_pathsは (font_name, regular_path, bold_path=None, italic_path=None, bold_italic_path=None) 形式
        manager.add_font_paths("jp_font", jp_font_path)
        print(f"✓ フォントパス登録成功: jp_font -> {jp_font_path}")
    except Exception as e:
        print(f"✗ フォントパス登録失敗: {e}")
        return
    
    # ② 必要なら先にプリロード（大きめのサイズで）
    try:
        manager.preload_fonts([{
            "name": "jp_font",
            "style": "regular",
            "point_size": 24
        }])
        print("✓ フォントプリロード成功")
    except Exception as e:
        print(f"✗ フォントプリロード失敗: {e}")
    
    # ③ テーマでは名前だけ指定（パスじゃない）
    theme_data = {
        "defaults": {
            "font": {
                "name": "jp_font",  # エイリアス名を使用
                "size": "24",
                "style": "regular"
            },
            "colours": {
                "normal_text": "#FFFFFF",
                "normal_bg": "#25292e",
                "normal_border": "#DDDDDD"
            }
        },
        "button": {  # ボタン専用のフォント設定を追加
            "font": {
                "name": "jp_font",
                "size": "24",
                "style": "regular"
            }
        },
        "label": {   # ラベル専用のフォント設定を追加
            "font": {
                "name": "jp_font",
                "size": "24",
                "style": "regular"
            }
        }
    }
    
    try:
        # load_theme()を使用（辞書データも受け付ける）
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
        text="正しいアプローチテスト",
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
    print("pygame_gui 正しいアプローチテスト終了")

if __name__ == "__main__":
    test_pygame_gui_correct_approach()