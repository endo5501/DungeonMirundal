# フォントテストサンプル集

このディレクトリには、Dungeon RPGプロジェクトでのフォント問題解決過程で作成されたテストファイルが含まれています。

## 📁 ファイル構成

### 成功パターン

#### `test_pygame_gui_correct_approach.py` ⭐ **推奨**
ChatGPTアプローチに基づく完全に動作するpygame_gui日本語フォントテスト

**特徴**:
- フォントエイリアス登録
- テーマ階層対応（button/label設定）
- 複数サイズのプリロード
- 完全な動作例

**使用法**:
```bash
cd /Users/endo5501/Work/DungeonMirundal
uv run python docs/samples/font_tests/test_pygame_gui_correct_approach.py
```

### デバッグツール

#### `test_pygame_gui_api_check.py`
pygame_gui 0.6.14の利用可能APIメソッドを調査

**用途**:
- pygame_guiバージョン確認
- 利用可能メソッド一覧表示
- API互換性確認

#### `test_pygame_gui_system_font.py`
システムフォントのみを使用したテスト

**用途**:
- システムフォント動作確認
- 同梱フォントなしでのテスト
- 基本的な動作検証

## 🚀 使用方法

### 1. 基本的なテスト実行

```bash
# プロジェクトルートディレクトリから実行
cd /Users/endo5501/Work/DungeonMirundal

# 推奨テスト（完全動作例）
uv run python docs/samples/font_tests/test_pygame_gui_correct_approach.py

# API確認
uv run python docs/samples/font_tests/test_pygame_gui_api_check.py

# システムフォントテスト
uv run python docs/samples/font_tests/test_pygame_gui_system_font.py
```

### 2. カスタムテスト作成

成功パターンを基に独自のテストを作成：

```python
# my_font_test.py
import pygame
import pygame_gui
import os
import sys
sys.path.append('docs/samples/font_tests')

# 成功パターンをインポート
from test_pygame_gui_correct_approach import load_jp_font_path

def my_test():
    pygame.init()
    screen = pygame.display.set_mode((800, 600))
    manager = pygame_gui.UIManager((800, 600))
    
    # フォント設定（成功パターンを使用）
    jp_font_path = load_jp_font_path()
    if jp_font_path:
        manager.add_font_paths("jp_font", jp_font_path)
        manager.preload_fonts([{"name": "jp_font", "style": "regular", "point_size": 20}])
        
        theme_data = {
            "defaults": {"font": {"name": "jp_font", "size": "20"}},
            "button": {"font": {"name": "jp_font", "size": "20"}}
        }
        manager.get_theme().load_theme(theme_data)
        
        # カスタムUI要素を追加
        # ...
        
if __name__ == "__main__":
    my_test()
```

## 🔧 トラブルシューティング

### よくある問題

1. **モジュールが見つからない**:
```bash
# プロジェクトルートから実行していることを確認
pwd  # /Users/endo5501/Work/DungeonMirundal であること
```

2. **フォントファイルが見つからない**:
```bash
# フォントファイル存在確認
ls -la assets/fonts/
```

3. **ImportError**:
```bash
# 依存関係確認
uv run python -c "import pygame, pygame_gui; print('OK')"
```

### デバッグモード

詳細なログでテスト実行：

```bash
# 詳細ログ付きで実行
PYTHONPATH=. uv run python -v docs/samples/font_tests/test_pygame_gui_correct_approach.py
```

## 📚 関連ドキュメント

- [フォントシステム完全ガイド](../../font_system_guide.md)
- [pygame_gui日本語フォント統合ガイド](../../pygame_gui_font_integration.md)
- [フォント問題トラブルシューティングチェックリスト](../../font_troubleshooting_checklist.md)

## 🎯 学習パス

1. **初心者**: `test_pygame_gui_api_check.py` でAPI確認
2. **基本**: `test_pygame_gui_system_font.py` でシステムフォント理解
3. **実践**: `test_pygame_gui_correct_approach.py` で完全実装理解
4. **応用**: カスタムテスト作成

---

**作成**: 2025年7月11日  
**目的**: フォント問題解決の知見保存と将来の開発者支援