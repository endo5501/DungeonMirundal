#!/usr/bin/env python3
"""
基本的なpygameでの日本語フォントテスト（pygame_gui使用せず）
"""
import pygame
import sys
import os


# --- 省略: import群 ---

def load_jp_font(size=24):
    # まず同梱フォントを優先
    local_fonts = ["assets/fonts/NotoSansJP-Regular.otf"]
    for f in local_fonts:
        if os.path.exists(f):
            try:
                return pygame.font.Font(f, size), f
            except Exception:
                pass

    # 次にシステムフォント候補
    for name in ["Hiragino Sans", "YuGothic", "Apple SD Gothic Neo"]:
        path = pygame.font.match_font(name)
        if path:
            return pygame.font.Font(path, size), path

    # 最後の手段
    return pygame.font.Font(None, size), None


    # あとは同じ…
def test_basic_pygame_font():
    """基本的なpygameでの日本語フォント表示テスト"""
    pygame.init()
    
    # 画面設定
    screen = pygame.display.set_mode((800, 600))
    font, loaded = load_jp_font()
    print("Loaded font:", loaded)
    pygame.display.set_caption('基本pygame日本語フォントテスト')

    # load_jp_font() で取得したフォントをそのまま使用
    valid_font = font
    if valid_font is None:
        # 念のためのフォールバック
        print("デフォルトフォントを使用（load_jp_font が None を返した）")
        valid_font = pygame.font.Font(None, 24)
    
    # 日本語テキスト
    japanese_texts = [
        "こんにちは",
        "冒険者ギルド", 
        "宿屋",
        "商店",
        "寺院",
        "魔法ギルド"
    ]
    
    # テキストを描画
    text_surfaces = []
    for text in japanese_texts:
        try:
            # 白色でテキストを描画
            text_surface = valid_font.render(text, True, (255, 255, 255))
            text_surfaces.append((text, text_surface))
            print(f"✓ テキスト描画成功: {text}")
        except Exception as e:
            print(f"✗ テキスト描画失敗: {text} - {e}")
    
    # メインループ
    clock = pygame.time.Clock()
    running = True
    
    print("ウィンドウを表示中... ESCキーまたはクリックで終了")
    
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                running = False
        
        # 画面を黒でクリア
        screen.fill((0, 0, 0))
        
        # 各テキストを描画
        y_offset = 50
        for text, surface in text_surfaces:
            screen.blit(surface, (50, y_offset))
            y_offset += 60
        
        # フォント情報も表示
        if valid_font:
            info_text = f"使用フォント: {loaded or 'default'}"
            info_surface = pygame.font.Font(None, 18).render(info_text, True, (150, 150, 150))
            screen.blit(info_surface, (50, 500))
        
        pygame.display.flip()
        clock.tick(60)
    
    pygame.quit()
    print("基本pygameテスト終了")

if __name__ == "__main__":
    test_basic_pygame_font()