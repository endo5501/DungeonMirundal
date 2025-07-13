# フォントシステム完全ガイド

## 概要

このドキュメントは、Dungeon RPGプロジェクトでのフォント関連問題の完全ガイドです。特に、Linux環境で開発されたゲームをmacOSに移植する際に発生した日本語フォント表示問題（文字化け・豆腐文字）の解決経験を基に作成されています。

## 🎯 対象読者

- プロジェクトの新規開発者
- フォント表示問題に遭遇した開発者
- クロスプラットフォーム対応を行う開発者
- pygame/pygame_guiでの日本語表示を実装する開発者

## 📋 問題の背景

### 発生した問題

2025年7月、Linux環境で開発されていたDungeon RPGをmacOSで実行した際、以下の問題が発生：

1. **pygameインポートエラー**: `DIRECTION_LTR`が見つからない
2. **日本語文字化け**: すべての日本語テキストが白い四角（豆腐文字）で表示
3. **pygame_gui固有の問題**: 基本的なpygameでは表示できるがpygame_guiでは文字化け

### 根本原因

- **プラットフォーム依存性**: pygame 2.6.1がmacOSで非互換
- **フォントパス問題**: ハードコードされたLinux固有のフォントパス
- **pygame_guiアーキテクチャ**: テーマ階層とフォントエイリアスシステムの理解不足

## 🔧 解決済みソリューション

### 1. プラットフォーム固有依存関係の管理

**問題**: pygame 2.6.1がmacOSで`DIRECTION_LTR`エラーを引き起こす

**解決策**: `pyproject.toml`でOS別依存関係を定義

```toml
dependencies = [
    # Platform-specific pygame dependencies
    "pygame>=2.6.0,<2.7; sys_platform == 'linux'",
    "pygame-ce>=2.5.0,<2.6; sys_platform == 'darwin'",
    "pygame>=2.5.0,<2.6; sys_platform == 'win32'",
    "pygame-gui>=0.6.0,<0.7",
]
```

**結果**: ゲーム起動に成功

### 2. クロスプラットフォームフォント検出

**問題**: Linux固有フォントパスがハードコード

**解決策**: 動的フォント検出システム

```python
def _load_jp_font_path(self):
    """日本語フォントのパスを取得（クロスプラットフォーム対応）"""
    # まず同梱フォントを優先
    local_fonts = [
        "assets/fonts/NotoSansCJKJP-Regular.otf",
        "assets/fonts/NotoSansJP-Regular.otf", 
        "assets/fonts/ipag.ttf"
    ]
    for f in local_fonts:
        if os.path.exists(f):
            return os.path.abspath(f)

    # 次にシステムフォント候補
    for name in ["Hiragino Sans", "YuGothic", "Apple SD Gothic Neo"]:
        path = pygame.font.match_font(name)
        if path:
            return path

    return None
```

### 3. pygame_gui日本語フォント統合

**問題**: pygame_guiのテーマ階層でdefaultsが無視される

**解決策**: ChatGPTアプローチによるフォントエイリアス登録

```python
def _register_japanese_fonts_to_pygame_gui(self):
    """pygame_guiに日本語フォントを直接登録（ChatGPTアプローチ）"""
    # ① エイリアス "jp_font" として登録
    self.ui_manager.add_font_paths("jp_font", jp_font_path)
    
    # ② 必要なサイズでプリロード
    self.ui_manager.preload_fonts([
        {"name": "jp_font", "style": "regular", "point_size": 14},
        {"name": "jp_font", "style": "regular", "point_size": 16},
        {"name": "jp_font", "style": "regular", "point_size": 18},
        {"name": "jp_font", "style": "regular", "point_size": 20},
        {"name": "jp_font", "style": "regular", "point_size": 24}
    ])
    
    # ③ テーマ設定で階層を考慮した設定
    theme_data = {
        "defaults": {
            "font": {"name": "jp_font", "size": "16", "style": "regular"}
        },
        "button": {  # ボタン専用のフォント設定（階層で上書きされるため）
            "font": {"name": "jp_font", "size": "16", "style": "regular"}
        },
        "label": {   # ラベル専用のフォント設定（階層で上書きされるため）
            "font": {"name": "jp_font", "size": "16", "style": "regular"}
        }
    }
    
    self.ui_manager.get_theme().load_theme(theme_data)
```

**重要ポイント**: `defaults`だけでなく`button`と`label`も明示的に設定する必要がある

## 🏗️ アーキテクチャ理解

### pygame vs pygame_gui フォントシステム

| 側面 | pygame | pygame_gui |
|------|--------|------------|
| **フォント指定方法** | 直接パス指定 | エイリアス名による間接指定 |
| **フォント管理** | 個別管理 | FontDictionary集中管理 |
| **テーマ対応** | なし | 階層的テーマシステム |
| **動的変更** | 困難 | テーマ再読み込みで容易 |

### pygame_guiテーマ階層

```
テーマ優先順位（高→低）:
1. object_id指定 (#my_button)
2. element_type指定 (button)
3. defaults指定 (defaults)
```

**重要**: `button`や`label`の設定が`defaults`より優先されるため、UI要素ごとにフォント設定が必要

## 🔍 デバッグ・診断方法

### 1. 迅速な問題診断

```bash
# 1. フォント検出テスト
uv run python -c "
import pygame
pygame.init()
fonts = ['Hiragino Sans', 'YuGothic', 'Apple SD Gothic Neo']
for name in fonts:
    path = pygame.font.match_font(name)
    print(f'{name}: {path if path else \"見つからない\"}')"

# 2. pygame_gui API確認
uv run python test_pygame_gui_api_check.py

# 3. 簡単なテスト実行
uv run python test_pygame_gui_correct_approach.py
```

### 2. ゲーム内デバッグ

```bash
# ゲーム起動とスクリーンショット
./scripts/start_game_for_debug.sh
uv run python src/debug/game_debug_client.py screenshot --save debug_font.jpg
```

### 3. ログ確認ポイント

成功時のログ例：
```
WindowManager: 日本語フォントを発見: /path/to/font.otf
WindowManager: 日本語フォント登録成功: jp_font -> /path/to/font.otf
WindowManager: 日本語フォント事前ロード完了
WindowManager: 動的テーマ読み込み成功（日本語フォント対応）
```

## 📁 プロジェクト内フォント関連ファイル

### コアファイル

- `src/ui/font_manager_pygame.py` - pygame用フォント管理
- `src/ui/window_system/window_manager.py` - pygame_gui統合
- `config/ui_theme.json` - UIテーマ設定

### テスト・サンプル

- `test_pygame_gui_correct_approach.py` - 成功パターンのサンプル
- `docs/samples/test_font_from_chatgpt.py` - 基本的なフォントテスト

### フォントファイル

- `assets/fonts/NotoSansCJKJP-Regular.otf` - 同梱日本語フォント
- `assets/fonts/ipag.ttf` - IPA Gothic フォント

## 🚀 ベストプラクティス

### 1. クロスプラットフォーム対応

- 同梱フォントを最優先にする
- OS固有フォントはフォールバックとして使用
- 絶対パスではなくプロジェクト相対パスを使用

### 2. pygame_gui使用時

- フォントエイリアス登録を必ず行う
- テーマ階層を理解してUI要素ごとに設定
- プリロードで性能を向上させる

### 3. 開発・保守

- 新しいフォント追加時は各OSでテスト
- ログを活用した問題診断
- 段階的アプローチ（簡単なテストから本格統合へ）

## 🎯 今後の拡張

### 予定されている改善

- [ ] フォント自動フォールバック機能
- [ ] 動的フォントサイズ調整
- [ ] より詳細なフォントメトリクス取得
- [ ] RTL（右から左）言語対応

### 参考資料

- [pygame_gui Font Documentation](https://pygame-gui.readthedocs.io/en/latest/theme_reference/theme_font.html)
- [pygame Font Documentation](https://www.pygame.org/docs/ref/font.html)
- [@docs/pygame_gui_font_integration.md](./pygame_gui_font_integration.md) - 詳細な技術解説
- [@docs/font_troubleshooting_checklist.md](./font_troubleshooting_checklist.md) - 問題解決チェックリスト

---

**作成**: 2025年7月11日  
**最終更新**: 2025年7月11日  
**貢献者**: Claude Code (フォント問題解決プロジェクト)
