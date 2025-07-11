# フォント問題トラブルシューティングチェックリスト

## 🚨 緊急診断（5分で解決）

### 症状別クイック診断

| 症状 | 可能性の高い原因 | 即座の解決策 |
|------|-----------------|--------------|
| **ゲームが起動しない** | pygame互換性問題 | `uv add pygame-ce` (macOS) |
| **日本語が全て□** | フォントパス問題 | フォントファイル存在確認 |
| **一部UI要素のみ□** | pygame_guiテーマ階層 | button/label設定追加 |
| **英語は表示、日本語のみ□** | フォントエイリアス未登録 | `add_font_paths`実行 |
| **フォントは読めるがUI表示されない** | テーマ読み込み失敗 | `load_theme`エラー確認 |

## 🔍 段階的診断フロー

### Step 1: 基本環境確認（2分）

```bash
# 1. pygame導入確認
uv run python -c "import pygame; print(f'pygame: {pygame.version.ver}')"

# 2. pygame_gui導入確認  
uv run python -c "import pygame_gui; print(f'pygame_gui: {pygame_gui.__version__}')"

# 3. フォントファイル存在確認
ls -la assets/fonts/
```

**期待される結果**:
- pygame: 2.5.x (macOS), 2.6.x (Linux)
- pygame_gui: 0.6.14
- フォントファイル: NotoSansCJKJP-Regular.otf, ipag.ttf など

### Step 2: フォント検出テスト（3分）

```bash
# システムフォント検出テスト
uv run python -c "
import pygame
pygame.init()
fonts = ['Hiragino Sans', 'YuGothic', 'Apple SD Gothic Neo', 'Noto Sans CJK JP']
for name in fonts:
    path = pygame.font.match_font(name)
    status = '✓' if path else '✗'
    print(f'{status} {name}: {path or \"見つからない\"}')"
```

**期待される結果**: 少なくとも1つのフォントが見つかる

### Step 3: pygame基本テスト（3分）

```bash
# 基本的なpygameフォント表示テスト
uv run python -c "
import pygame
import os

pygame.init()
screen = pygame.display.set_mode((400, 200))

# フォントテスト
font_path = 'assets/fonts/NotoSansCJKJP-Regular.otf'
if os.path.exists(font_path):
    font = pygame.font.Font(font_path, 24)
    text = font.render('日本語テスト', True, (255, 255, 255))
    screen.blit(text, (50, 50))
    pygame.display.flip()
    pygame.time.wait(2000)
    print('✓ pygame基本テスト成功')
else:
    print('✗ フォントファイルが見つかりません')

pygame.quit()
"
```

### Step 4: pygame_gui テスト（5分）

```bash
# pygame_gui統合テスト
uv run python test_pygame_gui_correct_approach.py
```

**期待される出力**:
```
✓ フォントパス登録成功: jp_font -> /path/to/font.otf
✓ フォントプリロード成功
✓ テーマデータ読み込み成功
✓ ボタン作成成功: こんにちは
```

## 🐛 具体的問題と解決法

### 問題1: "ImportError: cannot import name 'DIRECTION_LTR'"

**原因**: pygame 2.6.1がmacOSで非対応

**解決手順**:
```bash
# 1. 現在のpygameバージョン確認
uv run python -c "import pygame; print(pygame.version.ver)"

# 2. pygame-ceに変更（macOSの場合）
uv remove pygame
uv add pygame-ce

# 3. 確認
uv run python -c "import pygame; print('pygame-ce:', pygame.version.ver)"
```

### 問題2: 全ての日本語が豆腐文字（□）

**原因**: フォントファイルが見つからない

**解決手順**:
```bash
# 1. フォントファイル確認
ls -la assets/fonts/

# 2. ファイルが無い場合はダウンロード
mkdir -p assets/fonts
# Noto Sans CJK JPをダウンロード（オープンソース）
curl -L "https://github.com/googlefonts/noto-cjk/raw/main/Sans/OTF/Japanese/NotoSansCJKjp-Regular.otf" -o assets/fonts/NotoSansCJKJP-Regular.otf

# 3. 権限確認
chmod 644 assets/fonts/*.otf
```

### 問題3: ボタンやラベルのみ文字化け

**原因**: pygame_guiのテーマ階層問題

**解決手順**:
1. 現在のテーマ設定確認:
```python
# デバッグコード追加
theme = manager.get_theme()
button_font = theme.get_font_info([], ["button"], "button")
print(f"ボタンフォント設定: {button_font}")
```

2. 修正:
```python
theme_data = {
    "defaults": {"font": {"name": "jp_font", "size": "16"}},
    "button": {"font": {"name": "jp_font", "size": "16"}},    # 追加
    "label": {"font": {"name": "jp_font", "size": "16"}}     # 追加
}
```

### 問題4: 特定のサイズのみ文字化け

**原因**: プリロードされていないサイズを使用

**解決手順**:
```python
# 使用するすべてのサイズをプリロード
manager.preload_fonts([
    {"name": "jp_font", "style": "regular", "point_size": 12},
    {"name": "jp_font", "style": "regular", "point_size": 14},
    {"name": "jp_font", "style": "regular", "point_size": 16},
    {"name": "jp_font", "style": "regular", "point_size": 18},
    {"name": "jp_font", "style": "regular", "point_size": 20},
    {"name": "jp_font", "style": "regular", "point_size": 24},
])
```

### 問題5: フォント登録は成功するがUI表示されない

**原因**: テーマ読み込みエラー

**解決手順**:
```python
# エラー詳細を確認
try:
    manager.get_theme().load_theme(theme_data)
    print("✓ テーマ読み込み成功")
except Exception as e:
    print(f"✗ テーマエラー詳細: {e}")
    print(f"テーマデータ: {theme_data}")
    
    # フォールバック：シンプルなテーマで再試行
    simple_theme = {
        "defaults": {"font": {"name": "jp_font", "size": "16"}}
    }
    manager.get_theme().load_theme(simple_theme)
```

## 🔧 デバッグツールセット

### 1. 包括的システム診断

```python
# debug_font_system.py
import pygame
import pygame_gui
import os
import sys

def comprehensive_font_diagnosis():
    """包括的フォントシステム診断"""
    print("=== フォントシステム診断 ===")
    
    # プラットフォーム情報
    print(f"プラットフォーム: {sys.platform}")
    
    # pygame情報
    try:
        import pygame
        pygame.init()
        print(f"✓ pygame: {pygame.version.ver}")
    except Exception as e:
        print(f"✗ pygame エラー: {e}")
        return
    
    # pygame_gui情報
    try:
        import pygame_gui
        print(f"✓ pygame_gui: {pygame_gui.__version__}")
    except Exception as e:
        print(f"✗ pygame_gui エラー: {e}")
        return
    
    # フォントファイル確認
    font_files = [
        "assets/fonts/NotoSansCJKJP-Regular.otf",
        "assets/fonts/ipag.ttf"
    ]
    
    for font_file in font_files:
        if os.path.exists(font_file):
            size = os.path.getsize(font_file)
            print(f"✓ {font_file} ({size:,} bytes)")
        else:
            print(f"✗ {font_file} 見つからない")
    
    # システムフォント確認
    system_fonts = ["Hiragino Sans", "YuGothic", "Apple SD Gothic Neo"]
    for name in system_fonts:
        path = pygame.font.match_font(name)
        status = "✓" if path else "✗"
        print(f"{status} システムフォント '{name}': {path or '見つからない'}")
    
    # pygame_gui API確認
    try:
        manager = pygame_gui.UIManager((400, 300))
        print("✓ pygame_gui UIManager作成成功")
        
        # フォント登録テスト
        test_font = font_files[0] if os.path.exists(font_files[0]) else None
        if test_font:
            manager.add_font_paths("test_font", test_font)
            print(f"✓ フォント登録テスト成功: {test_font}")
        else:
            print("✗ テスト用フォントが見つからない")
            
    except Exception as e:
        print(f"✗ pygame_gui テストエラー: {e}")
    
    pygame.quit()
    print("=== 診断完了 ===")

if __name__ == "__main__":
    comprehensive_font_diagnosis()
```

### 2. 最小テストファイル生成

```python
# generate_minimal_test.py
import os

def generate_minimal_font_test():
    """最小限のフォントテストファイルを生成"""
    
    test_code = '''#!/usr/bin/env python3
"""最小限のフォントテスト"""
import pygame
import pygame_gui
import os

def minimal_test():
    pygame.init()
    screen = pygame.display.set_mode((600, 400))
    manager = pygame_gui.UIManager((600, 400))
    
    # フォント設定
    font_path = "assets/fonts/NotoSansCJKJP-Regular.otf"
    if not os.path.exists(font_path):
        print("❌ フォントファイルが見つかりません")
        return False
    
    try:
        # ChatGPTアプローチ
        manager.add_font_paths("jp_font", font_path)
        manager.preload_fonts([{"name": "jp_font", "style": "regular", "point_size": 20}])
        
        theme_data = {
            "defaults": {"font": {"name": "jp_font", "size": "20"}},
            "button": {"font": {"name": "jp_font", "size": "20"}}
        }
        manager.get_theme().load_theme(theme_data)
        
        # テストUI
        button = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect(50, 50, 200, 60),
            text="日本語テスト",
            manager=manager
        )
        
        print("✅ フォント設定成功 - ESCで終了")
        
        # 表示ループ
        clock = pygame.time.Clock()
        running = True
        
        while running:
            time_delta = clock.tick(60) / 1000.0
            
            for event in pygame.event.get():
                if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
                    running = False
                manager.process_events(event)
            
            manager.update(time_delta)
            screen.fill((80, 80, 80))
            manager.draw_ui(screen)
            pygame.display.flip()
        
        return True
        
    except Exception as e:
        print(f"❌ エラー: {e}")
        return False
    finally:
        pygame.quit()

if __name__ == "__main__":
    minimal_test()
'''
    
    with open("test_font_minimal.py", "w", encoding="utf-8") as f:
        f.write(test_code)
    
    print("最小テストファイルを生成しました: test_font_minimal.py")
    print("実行: uv run python test_font_minimal.py")

if __name__ == "__main__":
    generate_minimal_font_test()
```

## 📋 チェックリスト（印刷用）

### 環境セットアップ確認

- [ ] pygame/pygame-ceが正しくインストールされている
- [ ] pygame_gui 0.6.14がインストールされている  
- [ ] フォントファイルが`assets/fonts/`に存在する
- [ ] フォントファイルに読み取り権限がある

### 基本動作確認

- [ ] `import pygame`が成功する
- [ ] `import pygame_gui`が成功する
- [ ] pygameで日本語レンダリングできる
- [ ] システムフォントが1つ以上検出される

### pygame_gui統合確認

- [ ] `UIManager`が作成できる
- [ ] `add_font_paths()`が成功する
- [ ] `preload_fonts()`が警告なしで完了する
- [ ] `load_theme()`でエラーが発生しない
- [ ] UI要素に日本語テキストが表示される

### プロダクション統合確認

- [ ] ゲームが正常に起動する
- [ ] メニューの日本語が表示される
- [ ] すべてのUI要素で文字化けがない
- [ ] 異なる画面でもフォントが一貫している

## 🆘 それでも解決しない場合

### 1. 詳細な情報収集

```bash
# 環境情報を収集
uv run python debug_font_system.py > font_debug_report.txt 2>&1

# ゲームログ確認
./scripts/start_game_for_debug.sh
tail -f game_debug.log | grep -i font
```

### 2. イシュー報告用情報

以下の情報を収集してください：

```
- OS: macOS/Linux/Windows + バージョン
- Python: バージョン
- pygame: バージョン 
- pygame_gui: バージョン
- フォントファイル: サイズと場所
- エラーメッセージ: 完全なスタックトレース
- 実行コマンド: 正確なコマンド
```

### 3. フォールバック手順

1. **デフォルトフォントに戻す**:
```python
# pygame_guiテーマからフォント設定を削除
theme_data = {
    "defaults": {
        "colours": {
            "normal_text": "#FFFFFF"
        }
        # font設定を削除してデフォルトを使用
    }
}
```

2. **基本的なpygameのみ使用**:
```python
# pygame_guiを一時的に無効化してpygameで確認
font = pygame.font.Font("assets/fonts/NotoSansCJKJP-Regular.otf", 24)
text_surface = font.render("テスト", True, (255, 255, 255))
screen.blit(text_surface, (100, 100))
```

## 📚 参考リンク

- [メインガイド: font_system_guide.md](./font_system_guide.md)
- [技術詳細: pygame_gui_font_integration.md](./pygame_gui_font_integration.md)
- [動作サンプル: test_pygame_gui_correct_approach.py](../test_pygame_gui_correct_approach.py)
- [デバッグガイド: how_to_debug_game.md](./how_to_debug_game.md)

---

**作成**: 2025年7月11日  
**対象バージョン**: pygame-ce 2.5.5, pygame_gui 0.6.14  
**テスト環境**: macOS, Linux