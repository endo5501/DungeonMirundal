# ゲームデバッグガイド - 効率的なデバッグ方法

## 概要

Dungeonゲームの開発時に利用可能なデバッグツールとAPIについて説明します。ゲーム起動時に自動的にデバッグAPIサーバーが起動し、外部から制御・監視できます。

## 基本設定

- **ベースURL**: `http://localhost:8765`
- **起動方法**: `uv run main.py` でゲームと同時にAPIサーバーが起動
- **プロトコル**: REST API（HTTP）

## 推奨デバッグ方法

### 1. Python APIクライアント（推奨）

最も簡単で柔軟なデバッグ方法です。

```python
from src.debug.game_debug_client import GameDebugClient

client = GameDebugClient()
if client.wait_for_api():
    # スクリーンショット取得
    client.screenshot("debug.jpg")
    
    # ボタン一覧を表示（新機能）
    buttons = client.get_visible_buttons()
    client.show_button_shortcuts(buttons)
    
    # 数字キーでボタンクリック（新機能）
    client.click_button_by_number(1)  # 1番ボタンをクリック
    
    # テキストでボタンクリック
    client.click_button_by_text("冒険者ギルド")
    
    # ゲーム状態確認
    state = client.get_game_state()
    print(f"Current facility: {state.get('current_facility')}")
```

### 2. コマンドライン

```bash
# ボタン一覧表示
uv run python src/debug/game_debug_client.py buttons

# 数字キーでボタンクリック
uv run python src/debug/game_debug_client.py click --number 1

# テキストでボタンクリック  
uv run python src/debug/game_debug_client.py click --text "冒険者ギルド"

# スクリーンショット保存
uv run python src/debug/game_debug_client.py screenshot --save debug.jpg

# ESCキー送信
uv run python src/debug/game_debug_client.py escape
```

### 3. 便利関数

```python
from src.debug.debug_helper import (
    quick_test_button_navigation,
    test_all_visible_buttons,
    demonstrate_number_key_navigation
)

# ボタンナビゲーション機能をテスト
quick_test_button_navigation()

# すべてのボタンを順番にテスト
test_all_visible_buttons()

# 数字キーナビゲーションのデモ
demonstrate_number_key_navigation()
```

## 主要なAPIエンドポイント

### 基本機能

| エンドポイント | 機能 | 例 |
|---------------|------|-----|
| `GET /screenshot` | スクリーンショット取得 | `curl "http://localhost:8765/screenshot"` |
| `POST /input/key` | キー入力送信 | `curl -X POST "http://localhost:8765/input/key?code=27&down=true"` |
| `POST /input/mouse` | マウス入力送信 | `curl -X POST "http://localhost:8765/input/mouse?x=400&y=300&action=click"` |

### ゲーム状態

| エンドポイント | 機能 | レスポンス |
|---------------|------|----------|
| `GET /game/state` | ゲーム状態取得 | `{"current_state": "...", "current_facility": "..."}` |
| `GET /game/visible_buttons` | 表示ボタン取得 | `{"buttons": [...], "count": 5}` |

### 数字キー操作（新機能）

| エンドポイント | 機能 | 例 |
|---------------|------|-----|
| `POST /input/shortcut_key` | 数字キーでボタンクリック | `curl -X POST "http://localhost:8765/input/shortcut_key?key=1"` |

## 数字キーボタンナビゲーション（新機能）

座標に依存しない確実なボタン操作が可能になりました。

### 特徴

- 表示中のボタンに自動的に1-9の数字が割り当て
- 数字キー押下で対応するボタンを自動クリック
- 座標精度の問題を解決し、テストの信頼性が向上

### 使用例

```python
# ボタン一覧とショートカットキーを表示
client = GameDebugClient()
buttons = client.get_visible_buttons()
client.show_button_shortcuts(buttons)

# 出力例:
# === Available Buttons ===
#   1: 冒険者ギルド
#   2: 商店
#   3: 宿屋
#   4: 設定
# Total buttons: 4, With shortcuts: 4

# 1番ボタン（冒険者ギルド）をクリック
client.click_button_by_number(1)
```

### ゲーム内での数字キー操作

ゲーム本体でも数字キー（1-9）を直接押すことでボタンをクリックできます：

- `1` キー → 1番目のボタンをクリック
- `2` キー → 2番目のボタンをクリック
- ...以下同様

## よくあるデバッグシナリオ

### 1. 施設画面の動作確認

```python
client = GameDebugClient()

# 初期状態を確認
client.screenshot("initial.jpg")

# 冒険者ギルドボタンをクリック（数字キーで確実に）
client.click_button_by_number(1)
client.wait_for_transition()
client.screenshot("guild_opened.jpg")

# ESCで戻る
client.press_escape()
client.screenshot("back_to_main.jpg")
```

### 2. 全ボタンの動作確認

```python
from src.debug.debug_helper import test_all_visible_buttons

# すべてのボタンを自動テスト
results = test_all_visible_buttons()

# 結果確認
for result in results:
    status = "✓" if result["success"] else "✗"
    print(f"{status} Button {result['button_number']}: {result['button_text']}")
```

### 3. ESC遷移問題のデバッグ

```python
from src.debug.debug_helper import quick_debug_esc_issue

# ESC遷移を自動検証
quick_debug_esc_issue()
```

## テスト統合

### pytest での使用

```python
def test_facility_navigation(game_api_client):
    """施設ナビゲーションのテスト"""
    # ボタン一覧を取得
    buttons = game_api_client.get_visible_buttons()
    assert len(buttons['buttons']) > 0
    
    # 1番ボタンをクリック
    success = game_api_client.click_button_by_number(1)
    assert success

def test_button_shortcuts(game_api_client):
    """ボタンショートカットのテスト"""
    buttons = game_api_client.get_visible_buttons()
    
    # ショートカットキーが割り当てられていることを確認
    for i, button in enumerate(buttons['buttons'][:9]):
        assert button['shortcut_key'] == str(i + 1)
```

### 統合テストの実行

```bash
# 通常のテスト
uv run pytest

# 統合テストを含む
uv run pytest -m "integration"

# ボタンナビゲーションテスト
uv run pytest tests/debug/test_button_navigation.py -v
```

## デバッグツール一覧

### ファイル構成

```
src/debug/
├── game_debug_client.py      # Python APIクライアント
├── debug_helper.py           # 高レベルデバッグ機能
└── ui_debug_helper.py        # UI階層デバッグ

tests/debug/
└── test_button_navigation.py # ボタンナビゲーションテスト

scripts/
└── start_game_for_debug.sh   # ゲーム自動起動
```

### 使用場面別推奨ツール

| 場面 | 推奨ツール |
|------|------------|
| 日常的なデバッグ | Python APIクライアント |
| ボタン操作テスト | 数字キーナビゲーション |
| 自動テスト | pytest + フィクスチャ |
| 複雑なシナリオ | DebugHelper |
| UI構造確認 | UIDebugHelper |

## トラブルシューティング

### APIサーバーが起動しない

1. ゲーム（`uv run main.py`）が正常に起動しているか確認
2. ポート8765が使用中でないか確認: `lsof -i :8765`
3. ファイアウォール設定を確認

### ボタンクリックが失敗する

```python
# ボタンが存在するか確認
buttons = client.get_visible_buttons()
client.show_button_shortcuts(buttons)

# 数字キーナビゲーションを使用（推奨）
client.click_button_by_number(1)  # 座標不要で確実

# 従来の座標ベース（非推奨）
# client.click_button_by_text("冒険者ギルド")
```

### スクリーンショットが取得できない

```bash
# API動作確認
curl -I "http://localhost:8765/screenshot"

# 詳細確認
curl "http://localhost:8765/screenshot" | jq .
```

## まとめ

新機能の数字キーボタンナビゲーションにより、以下が実現されました：

1. **確実なボタン操作**: 座標に依存しない安定した操作
2. **テスト信頼性向上**: マウス座標精度問題の解決
3. **デバッグ効率化**: 直感的な数字キー操作
4. **自動化対応**: CI/CDでの安定したテスト実行

これらのツールを活用することで、より効率的で品質の高いゲーム開発が可能になります。