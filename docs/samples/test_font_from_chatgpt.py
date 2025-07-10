from pathlib import Path
import pygame
import pygame.freetype as ft

ft.init()
pygame.init()

screen = pygame.display.set_mode((800, 600))
pygame.display.set_caption("クロスプラットフォーム日本語テスト")

# プロジェクト同梱フォントを最優先
asset_dir = Path(__file__).resolve().parent / ".." / ".." / "assets" / "fonts"
candidates = [
    asset_dir / "ipag.ttf",
    asset_dir / "NotoSansCJKJP-Regular.otf",
    # macOS system
    Path("/System/Library/Fonts/Supplemental/ヒラギノ角ゴシック W3.ttc"),
]

font = None
for p in candidates:
    if p.exists():
        try:
            font = ft.Font(str(p), 36)
            print("Loaded:", p)
            break
        except Exception as e:
            print("Failed:", p, e)

if font is None:
    print("Fallback to default")
    font = ft.SysFont("sans-serif", 36)

running = True
while running:
    for e in pygame.event.get():
        if e.type in (pygame.QUIT, pygame.KEYDOWN, pygame.MOUSEBUTTONDOWN):
            running = False

    screen.fill((0, 0, 0))
    y = 50
    for t in ["こんにちは", "冒険者ギルド", "魔法ギルド"]:
        surf, _ = font.render(t, (255, 255, 255))
        screen.blit(surf, (50, y))
        y += 60
    pygame.display.flip()

pygame.quit()