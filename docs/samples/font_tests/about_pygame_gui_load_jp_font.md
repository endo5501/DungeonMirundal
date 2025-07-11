Q. test_pygame_gui_load_jp_font.py が文字化けするのはなぜ？

```test_pygame_gui_load_jp_font.py
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
```

A. ほな、原因をざっくり言うと 「pygame GUI がフォントファイルの“絶対パス”をそのまま名前やと思い込んでるから、日本語フォントを読み込めてへん」 ってことやね。

⸻

どこでコケてるん？

```py
theme_data = {
    "defaults": {
        "font": {
            "name": jp_font_path,   # ← ここ！
            "size": "16"
        }
    }
}
```

* pygame_gui のテーマ JSON（や辞書）は「name に“フォントのエイリアス名”を指定 → FontDictionary に登録されたパスを探す」
という流れでフォントを探すんや。
* せやのに 絶対パス をそのまま突っ込むと、FontDictionary は
1. 「jp_font_path って名前のフォント登録あったっけ？」→ 無い
2. 次に pygame.font.match_font("絶対パス文字列") を呼ぶ → そんなフォント名は当然無い
3. 結果、デフォルト（英語）フォントでレンダリング → 日本語は豆腐／文字化け

⸻

直し方の王道パターン

1) フォントを FontDictionary に登録してから “エイリアス名” で呼ぶ

manager = pygame_gui.UIManager(window_size)

# ① エイリアス "jp_font" として登録

```py
manager.add_font_path("jp_font", jp_font_path)
```

# ② 必要なら先にプリロード

```py
manager.preload_fonts([{
    "name": "jp_font",
    "style": "regular",
    "point_size": 16
}])
```

# ③ テーマでは名前だけ指定（パスじゃない）

```py
theme_data = {
    "defaults": {
        "font": {
            "name": "jp_font",
            "size": "16",
            "style": "regular"
        }
    }
}
manager.get_theme().load_theme(theme_data)
```

これだけで日本語テキストもバッチリ出るはずやで。

2) もしくは UIManager 全体のデフォルトフォントを差し替える

```py
manager = pygame_gui.UIManager(
    window_size,
    # meta 引数を使って `font_path` を一括指定する方法もある
    # (pygame_gui 0.7.0 以降)
    theme_path=None,
    font_path=jp_font_path
)
```

ただしこの方法はアプデで挙動変わる可能性もあるから、
確実＆明示的 にいきたいなら ★1) 推奨や。

⸻

追加でハマりがちなポイント

症状	原因と対策
.ttc を読み込むとまたエラー	FreeType 経由で .ttc 読めるけど、環境依存でハマることがある。Noto Sans JP (.otf / .ttf) が一番安定
フォントは読めたのにボタンだけ豆腐	ボタン用の object_id / クラスごとにフォントが上書きされてる。テーマ階層を確認して「defaults → button」の順でフォント指定が残っとるかチェック
低 DPI 環境でだけ豆腐	16px だと小さすぎてフォントが内蔵ビットマップ落ち⇒グリフ欠け、みたいなケースも。サイズを 20〜24px で試すと一発で直ることもある


⸻

まとめやで

1. jp_font_path を 名前の代わりに突っ込んだのが敗因
2. manager.add_font_path("jp_font", jp_font_path) で エイリアス登録
3. テーマ側は "name": "jp_font" で呼び出す

これで pygame_gui でも日本語表示いけるはずや。
試してみて、まだ豆腐が出るようならまた教えてや〜。