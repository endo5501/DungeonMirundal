# pygame_gui 日本語フォント統合ガイド

## 概要

pygame_guiでの日本語フォント表示は、通常のpygameよりも複雑です。このガイドでは、pygame_gui 0.6.14での正しい日本語フォント統合方法を詳しく解説します。

## 🔑 重要な概念

### フォントエイリアスシステム

pygame_guiは**フォントエイリアス**という概念を使用します：

```python
# ❌ 間違い：パスを直接指定
theme_data = {
    "defaults": {
        "font": {
            "name": "/path/to/font.otf",  # これは動作しない
            "size": "16"
        }
    }
}

# ✅ 正しい：エイリアス名を使用
manager.add_font_paths("jp_font", "/path/to/font.otf")  # エイリアス登録
theme_data = {
    "defaults": {
        "font": {
            "name": "jp_font",  # エイリアス名を使用
            "size": "16"
        }
    }
}
```

### テーマ階層システム

pygame_guiのテーマは階層構造を持ちます：

```
優先順位（高→低）:
1. object_id指定 (#my_button)
2. element_type指定 (button, label, etc.)
3. defaults指定
```

**重要**: `button`や`label`の設定が`defaults`より優先されるため、単に`defaults`を設定するだけでは不十分です。

## 🎯 ChatGPTアプローチ（推奨解決策）

### 完全な実装例

```python
def setup_japanese_font_for_pygame_gui(ui_manager, jp_font_path):
    """pygame_guiに日本語フォントを正しく統合"""
    
    # Step 1: フォントエイリアス登録
    try:
        ui_manager.add_font_paths("jp_font", jp_font_path)
        print(f"✓ フォント登録成功: jp_font -> {jp_font_path}")
    except Exception as e:
        print(f"✗ フォント登録失敗: {e}")
        return False
    
    # Step 2: プリロード（性能向上のため）
    try:
        ui_manager.preload_fonts([
            {"name": "jp_font", "style": "regular", "point_size": 14},
            {"name": "jp_font", "style": "regular", "point_size": 16},
            {"name": "jp_font", "style": "regular", "point_size": 18},
            {"name": "jp_font", "style": "regular", "point_size": 20},
            {"name": "jp_font", "style": "regular", "point_size": 24}
        ])
        print("✓ フォントプリロード成功")
    except Exception as e:
        print(f"⚠ フォントプリロード失敗: {e}")
    
    # Step 3: テーマ階層を考慮した設定
    theme_data = {
        "defaults": {
            "font": {
                "name": "jp_font",
                "size": "16",
                "style": "regular"
            }
        },
        # 重要：UI要素ごとに明示的に設定
        "button": {
            "font": {
                "name": "jp_font",
                "size": "16",
                "style": "regular"
            }
        },
        "label": {
            "font": {
                "name": "jp_font", 
                "size": "16",
                "style": "regular"
            }
        },
        "text_box": {
            "font": {
                "name": "jp_font",
                "size": "14",
                "style": "regular"
            }
        }
    }
    
    # Step 4: テーマ適用
    try:
        ui_manager.get_theme().load_theme(theme_data)
        print("✓ テーマ読み込み成功")
        return True
    except Exception as e:
        print(f"✗ テーマ読み込み失敗: {e}")
        return False
```

### 使用例

```python
import pygame
import pygame_gui
import os

def test_japanese_font_integration():
    pygame.init()
    
    # 画面設定
    screen = pygame.display.set_mode((800, 600))
    manager = pygame_gui.UIManager((800, 600))
    
    # 日本語フォントパス取得
    jp_font_path = "assets/fonts/NotoSansCJKJP-Regular.otf"
    if not os.path.exists(jp_font_path):
        print("フォントファイルが見つかりません")
        return
    
    # フォント統合
    if setup_japanese_font_for_pygame_gui(manager, jp_font_path):
        # 日本語UI要素作成
        button = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect(100, 100, 200, 50),
            text="冒険者ギルド",
            manager=manager
        )
        
        label = pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect(100, 200, 300, 30),
            text="日本語表示テスト成功！",
            manager=manager
        )
        
        # メインループ
        clock = pygame.time.Clock()
        running = True
        
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
            
            screen.fill((50, 50, 50))
            manager.draw_ui(screen)
            pygame.display.flip()
    
    pygame.quit()

if __name__ == "__main__":
    test_japanese_font_integration()
```

## 🔧 API詳細

### add_font_paths()

```python
manager.add_font_paths(
    font_name,           # エイリアス名（文字列）
    regular_path,        # 通常フォントのパス
    bold_path=None,      # 太字フォントのパス（オプション）
    italic_path=None,    # イタリックフォントのパス（オプション）
    bold_italic_path=None # 太字イタリックフォントのパス（オプション）
)
```

### preload_fonts()

```python
manager.preload_fonts([
    {
        "name": "エイリアス名",
        "style": "regular|bold|italic|bold_italic",
        "point_size": サイズ（整数）
    }
])
```

### load_theme()

```python
# 辞書からテーマを読み込み
manager.get_theme().load_theme(theme_dict)

# ファイルからテーマを読み込み
manager.get_theme().load_theme("path/to/theme.json")
```

## 🐛 よくある問題と解決策

### 1. 豆腐文字（□）が表示される

**原因**: フォントエイリアスが正しく登録されていない

**解決策**:
```python
# フォント登録状況を確認
theme = manager.get_theme()
font_dict = theme.get_font_dictionary()
print("登録済みフォント:", font_dict.loaded_fonts.keys())

# 正しく登録し直す
manager.add_font_paths("jp_font", jp_font_path)
```

### 2. ボタンだけ文字化けする

**原因**: テーマ階層で`button`設定が`defaults`を上書き

**解決策**:
```python
theme_data = {
    "defaults": {"font": {"name": "jp_font", "size": "16"}},
    "button": {"font": {"name": "jp_font", "size": "16"}}  # 明示的に設定
}
```

### 3. 特定のサイズだけ文字化け

**原因**: プリロードされていないサイズを使用

**解決策**:
```python
# 使用するサイズを事前にプリロード
manager.preload_fonts([
    {"name": "jp_font", "style": "regular", "point_size": 必要なサイズ}
])
```

### 4. load_theme_from_dict()が見つからない

**原因**: pygame_gui 0.6.14では`load_theme()`を使用

**解決策**:
```python
# ❌ 古いAPI
manager.get_theme().load_theme_from_dict(theme_data)

# ✅ 正しいAPI
manager.get_theme().load_theme(theme_data)
```

## 📊 デバッグ方法

### 1. フォント登録状況の確認

```python
def debug_font_registration(manager):
    """フォント登録状況をデバッグ"""
    theme = manager.get_theme()
    font_dict = theme.get_font_dictionary()
    
    print("=== フォント登録状況 ===")
    print(f"登録済みフォント: {list(font_dict.loaded_fonts.keys())}")
    
    # 特定のフォントをテスト
    try:
        font = font_dict.find_font("jp_font", 16, bold=False, italic=False)
        print(f"jp_font (16px): {'見つかった' if font else '見つからない'}")
    except Exception as e:
        print(f"jp_font テストエラー: {e}")
```

### 2. テーマ設定の確認

```python
def debug_theme_settings(manager):
    """テーマ設定をデバッグ"""
    theme = manager.get_theme()
    
    # ボタンのフォント設定を確認
    button_font_info = theme.get_font_info(
        object_ids=[],
        element_ids=["button"],
        element_name="button"
    )
    print(f"ボタンフォント情報: {button_font_info}")
```

### 3. 簡易テストファイル作成

```python
# test_font_quick.py
import pygame
import pygame_gui

def quick_font_test():
    pygame.init()
    screen = pygame.display.set_mode((400, 300))
    manager = pygame_gui.UIManager((400, 300))
    
    # フォント設定
    font_path = "assets/fonts/NotoSansCJKJP-Regular.otf"
    manager.add_font_paths("test_font", font_path)
    
    theme_data = {
        "defaults": {"font": {"name": "test_font", "size": "20"}},
        "button": {"font": {"name": "test_font", "size": "20"}}
    }
    manager.get_theme().load_theme(theme_data)
    
    # テストボタン
    button = pygame_gui.elements.UIButton(
        relative_rect=pygame.Rect(50, 50, 300, 50),
        text="日本語テスト",
        manager=manager
    )
    
    # 最小ループ
    for _ in range(180):  # 3秒間表示
        manager.update(1/60)
        screen.fill((100, 100, 100))
        manager.draw_ui(screen)
        pygame.display.flip()
        pygame.time.wait(16)
    
    pygame.quit()

if __name__ == "__main__":
    quick_font_test()
```

## 🌟 プロジェクト統合例

### WindowManagerでの実装

プロジェクトの`src/ui/window_system/window_manager.py`では以下のように統合されています：

```python
def _register_japanese_fonts_to_pygame_gui(self):
    """pygame_guiに日本語フォントを直接登録（ChatGPTアプローチ）"""
    try:
        # 日本語フォントパスを取得
        jp_font_path = self._load_jp_font_path()
        if not jp_font_path:
            logger.warning("WindowManager: 日本語フォントが見つかりません")
            return
        
        logger.info(f"WindowManager: 日本語フォントを発見: {jp_font_path}")
        
        # ① エイリアス "jp_font" として登録
        self.ui_manager.add_font_paths("jp_font", jp_font_path)
        logger.info(f"WindowManager: 日本語フォント登録成功: jp_font -> {jp_font_path}")
        
        # ② 必要なサイズでプリロード
        self.ui_manager.preload_fonts([
            {"name": "jp_font", "style": "regular", "point_size": 14},
            {"name": "jp_font", "style": "regular", "point_size": 16},
            {"name": "jp_font", "style": "regular", "point_size": 18},
            {"name": "jp_font", "style": "regular", "point_size": 20},
            {"name": "jp_font", "style": "regular", "point_size": 24}
        ])
        logger.info("WindowManager: 日本語フォント事前ロード完了")
        
        # ③ テーマ設定で名前だけ指定（ChatGPTアプローチ）
        theme_data = {
            "defaults": {
                "font": {"name": "jp_font", "size": "16", "style": "regular"}
            },
            "button": {
                "font": {"name": "jp_font", "size": "16", "style": "regular"}
            },
            "label": {
                "font": {"name": "jp_font", "size": "16", "style": "regular"}
            }
        }
        
        self.ui_manager.get_theme().load_theme(theme_data)
        logger.info("WindowManager: 動的テーマ読み込み成功（日本語フォント対応）")
                
    except Exception as e:
        logger.error(f"WindowManager: 日本語フォント登録処理でエラー: {e}")
```

## 📚 参考資料

### 公式ドキュメント
- [pygame_gui Font Documentation](https://pygame-gui.readthedocs.io/en/latest/theme_reference/theme_font.html)
- [pygame_gui Theme Guide](https://pygame-gui.readthedocs.io/en/latest/theme_guide.html)

### プロジェクト内関連ファイル
- `test_pygame_gui_correct_approach.py` - 動作する完全例
- `src/ui/window_system/window_manager.py` - プロダクション実装
- `assets/fonts/` - 同梱フォントファイル

### 関連ドキュメント
- [@docs/font_system_guide.md](./font_system_guide.md) - 包括的フォントガイド
- [@docs/font_troubleshooting_checklist.md](./font_troubleshooting_checklist.md) - 問題解決チェックリスト

---

**作成**: 2025年7月11日  
**最終更新**: 2025年7月11日  
**検証環境**: pygame-ce 2.5.5, pygame_gui 0.6.14, macOS