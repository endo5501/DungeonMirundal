# 0030_font_problem.md - pygame-gui日本語フォント表示問題

## 問題概要

WindowManagerベースのMenuWindowシステムにおいて、pygame-guiを使用したUI要素（ボタン、ラベル）で日本語文字が正しく表示されず、文字化けが発生する問題。

## 現象詳細

### 正常動作するシステム
- **既存UIシステム** (`src/ui/base_ui_pygame.py`)
  - pygame-guiを使用
  - 同一のUIテーマファイル (`config/ui_theme.json`) を使用
  - 日本語文字が正常に表示される

### 問題が発生するシステム
- **WindowManagerシステム** (`src/ui/window_system/`)
  - pygame-guiを使用
  - 同一のUIテーマファイルを使用
  - 日本語文字が文字化けする

## 技術的詳細

### UIテーマ設定 (`config/ui_theme.json`)
```json
{
    "defaults": {
        "font": {
            "name": "noto",
            "size": "14",
            "regular_path": "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
            "bold_path": "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc"
        }
    }
}
```

### 既存UIシステムの実装 (正常動作)
```python
# src/ui/base_ui_pygame.py:616
theme_path = "/home/satorue/Dungeon/config/ui_theme.json"
self.pygame_gui_manager = pygame_gui.UIManager((screen.get_width(), screen.get_height()), theme_path)

# フォント初期化
def _initialize_fonts(self):
    from src.ui.font_manager_pygame import font_manager
    self.default_font = font_manager.get_japanese_font(24)
    self.title_font = font_manager.get_japanese_font(32)
```

### WindowManagerシステムの実装 (文字化け発生)
```python
# src/ui/window_system/window_manager.py:102
theme_path = "/home/satorue/Dungeon/config/ui_theme.json"
self.ui_manager = pygame_gui.UIManager((screen.get_width(), screen.get_height()), theme_path)

# 同じフォント初期化処理を実装済み
def _initialize_fonts(self):
    from src.ui.font_manager_pygame import font_manager
    self.default_font = font_manager.get_japanese_font(24)
    self.title_font = font_manager.get_japanese_font(32)
```

## 実装差異の調査

### 1. UIManager作成タイミング
- **既存システム**: ゲーム初期化時に作成
- **WindowManager**: 初回ウィンドウ表示時に作成

### 2. FontManager連携
- **既存システム**: `_initialize_fonts()`で日本語フォント取得
- **WindowManager**: 同じ処理を実装済みだが効果なし

### 3. フォント読み込み順序
- **既存システム**: UIManager作成後にFontManager連携
- **WindowManager**: 同じ順序で実装済み

## ログ分析

### 正常ケース (既存UI)
```
2025-06-28 21:09:35 - INFO - UIテーマを読み込みました: /home/satorue/Dungeon/config/ui_theme.json
2025-06-28 21:09:35 - INFO - 日本語フォントをロードしました: /usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc
```

### 問題ケース (WindowManager)
```
2025-06-28 21:14:05 - INFO - WindowManager: UIテーマを読み込みました: /home/satorue/Dungeon/config/ui_theme.json
2025-06-28 21:14:05 - DEBUG - WindowManager: フォント初期化完了
```

## 推測される原因

### 1. pygame-guiの内部フォント管理
- pygame-guiは独自のフォント管理システムを持つ
- UIManager作成時のフォント登録プロセスに違いがある可能性

### 2. テーマファイル解釈の差異
- 同じテーマファイルでも、UIManager作成コンテキストにより解釈が異なる可能性
- "noto"フォント名の解決方法が異なる可能性

### 3. フォントパス解決の問題
- `regular_path`で指定した絶対パスが適用されていない
- フォントファミリー名("noto")での検索が失敗している

## 試行済み解決策

### 1. 絶対パス指定 ❌
```python
theme_path = "/home/satorue/Dungeon/config/ui_theme.json"  # 既存と同じ
```

### 2. FontManager連携 ❌
```python
def _initialize_fonts(self):  # 既存と同じ実装
    font_manager = get_font_manager()
    self.default_font = font_manager.get_japanese_font(24)
```

### 3. 事前フォント読み込み ❌
```python
pygame.font.init()
test_font = pygame.font.Font(font_path, 16)
```

## 残存する調査項目

### 1. pygame-gui内部フォント状態
```python
# UIManager作成後のフォント状態を確認
print(self.ui_manager.get_theme().get_font_dictionary())
```

### 2. テーマ適用状態の詳細確認
```python
# テーマが正しく読み込まれているか確認
theme = self.ui_manager.get_theme()
font_data = theme.get_font_data('defaults')
```

### 3. フォントファイル直接指定
```python
# テーマファイルを使わずに直接フォント指定
button = pygame_gui.elements.UIButton(
    relative_rect=rect,
    text="テスト",
    manager=ui_manager,
    object_id='#japanese_button'
)
```

## 代替解決策

### 1. 段階的移行アプローチ
- 地上部メニューは既存UIシステムを継続使用
- 施設内メニューのみWindowManagerを使用
- フォント問題解決後に完全統一

### 2. カスタムフォントレンダリング
- pygame-guiを使わずPygameの直接描画
- 既存FontManagerを活用したカスタムUI実装

### 3. ハイブリッドアプローチ
- 日本語テキストは従来のPygame描画
- ボタン枠とイベント処理はpygame-gui
- 表示とロジックの分離

## 優先度と影響

### 🔴 高優先度
- **ユーザビリティ**: 文字化けによりメニュー操作が困難
- **開発効率**: WindowManager統一の利点が活用できない

### 📊 影響範囲
- 地上部メインメニュー
- 施設内メニュー（パーティ編成含む）
- 今後実装予定の全MenuWindowシステム

### ⏰ 対応期限
- **短期**: 代替アプローチでの機能提供
- **中期**: pygame-guiフォント問題の根本解決

## 次のアクション

1. **pygame-gui内部フォント状態の詳細調査**
2. **テーマファイル適用プロセスの差異分析**
3. **必要に応じて代替実装の検討**
4. **フォント問題解決後のWindowManager完全統一**

---

**作成日**: 2025-06-28  
**最終更新**: 2025-06-28  
**担当**: Claude Code  
**関連Issues**: 0025_not_return.md (ナビゲーション統一により解決済み)