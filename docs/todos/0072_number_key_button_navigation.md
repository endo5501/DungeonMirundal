# TODO 0072: 数字キーによるボタン操作システム実装

## 概要
マウス座標に依存しない確実なボタン操作を実現するため、表示中のボタンに数字キー（1-9）を割り当てて操作できるシステムを実装する。

## 背景・問題
- デバッグAPIでのマウスクリックが座標精度の問題で不安定
- 自動テストでボタンクリックの失敗が頻発
- 施設の「終了」ボタンなどが座標ベースの操作では正確に押せない
- 手動操作では正常に動作するが、自動化されたテストでは信頼性が低い

## 実装計画

### 1. UIシステムでのボタン一覧管理
- [x] 現在表示中のボタンリストを動的に管理する機能
- [x] ボタンに1から順番に数字キーを自動割り当て
- [x] ボタンの表示状態変更時にキー割り当てを更新

### 2. キーボード入力ハンドリング
- [x] 数字キー（1-9）の入力を検出
- [x] 対応するボタンのクリックイベントを発火
- [x] 既存のマウス操作との併用をサポート

### 3. デバッグAPI機能拡張
- [x] `/game/visible_buttons` エンドポイントにショートカットキー情報を追加
- [x] レスポンスに `shortcut_key` フィールドを追加
- [x] 数字キー入力用の新しいエンドポイント追加

### 4. デバッグクライアント機能強化
- [x] `click_button_by_number()` メソッドの実装
- [x] 現在のボタン一覧とショートカットキーを表示する機能
- [x] 数字キーでの操作をサポートするヘルパー関数

### 5. テスト・検証
- [x] 既存のメニューナビゲーションテストを数字キー操作に移行
- [x] 施設の「終了」ボタンが確実に押せることを確認
- [x] すべての施設メニューでの動作を検証

## 期待効果
- 座標に依存しない確実なボタン操作
- 自動テストの信頼性向上
- デバッグ効率の大幅改善
- メニューナビゲーションの問題解決

## 実装詳細

### API仕様変更
```json
// GET /game/visible_buttons のレスポンス例
{
  "buttons": [
    {
      "text": "冒険者ギルド",
      "position": {"x": 200, "y": 245},
      "size": {"width": 150, "height": 30},
      "shortcut_key": "1"
    },
    {
      "text": "商店",
      "position": {"x": 200, "y": 275},
      "size": {"width": 150, "height": 30},
      "shortcut_key": "2"
    }
  ],
  "count": 2
}
```

### 新規エンドポイント
```
POST /input/shortcut_key?key=1
- 指定された数字キーに対応するボタンをクリック
- レスポンス: {"ok": true, "button_clicked": "冒険者ギルド"}
```

### デバッグクライアント使用例
```python
from src.debug.game_debug_client import GameDebugClient

client = GameDebugClient()
# 現在のボタン一覧を表示
buttons = client.get_visible_buttons()
client.show_button_shortcuts(buttons)

# 数字キーでボタンをクリック
client.click_button_by_number(1)  # 1番のボタンをクリック
client.click_button_by_number(4)  # 4番のボタンをクリック
```

## 関連ファイル
- `src/core/dbg_api.py` - デバッグAPIサーバー
- `src/debug/game_debug_client.py` - デバッグクライアント
- `src/core/window_manager.py` - ウィンドウ管理システム
- `src/core/input_manager.py` - 入力管理システム

## 優先度
高（現在のメニューナビゲーションテストが不安定なため）

## 担当者
Claude Code

## 完了条件
- [x] 数字キーでのボタン操作が実装済み
- [x] デバッグAPIが拡張済み
- [x] 既存のテストが数字キー操作に移行済み
- [x] すべての施設メニューで動作確認済み
- [x] ドキュメントが更新済み

## 実装完了

数字キーによるボタン操作システムの実装が完了しました。

### 実装内容

1. **デバッグAPI拡張** (`src/core/dbg_api.py`)
   - `/game/visible_buttons`エンドポイントに`shortcut_key`フィールドを追加
   - `/input/shortcut_key`エンドポイントを新規追加

2. **デバッグクライアント強化** (`src/debug/game_debug_client.py`)
   - `click_button_by_number()`メソッドを実装
   - `show_button_shortcuts()`メソッドを実装
   - `press_number_key()`メソッドを実装
   - コマンドライン機能を拡張（`buttons`, `click`コマンド）

3. **ウィンドウシステム統合** (`src/ui/window_system/window_manager.py`)
   - 数字キー（1-9）入力の自動検出
   - ボタンショートカット処理の実装
   - 表示ボタンの自動番号割り当て

4. **デバッグヘルパー強化** (`src/debug/debug_helper.py`)
   - 数字キー操作をサポートするアクション追加
   - `quick_test_button_navigation()`便利関数を追加
   - `test_all_visible_buttons()`包括テスト関数を追加
   - `demonstrate_number_key_navigation()`デモ関数を追加

5. **テストスイート** (`tests/debug/test_button_navigation.py`)
   - 包括的な単体テストを実装
   - 統合テストを実装
   - エラーケースのテストを実装

### 使用方法

#### APIレベル
```bash
# ボタン一覧の取得（ショートカットキー付き）
curl "http://localhost:8765/game/visible_buttons"

# 数字キーでボタンクリック
curl -X POST "http://localhost:8765/input/shortcut_key?key=1"
```

#### デバッグクライアント
```bash
# ボタン一覧表示
uv run python src/debug/game_debug_client.py buttons

# 数字キーでボタンクリック
uv run python src/debug/game_debug_client.py click --number 1

# テキストでボタンクリック
uv run python src/debug/game_debug_client.py click --text "冒険者ギルド"
```

#### Pythonコード
```python
from src.debug.game_debug_client import GameDebugClient

client = GameDebugClient()
# ボタン一覧表示
buttons = client.get_visible_buttons()
client.show_button_shortcuts(buttons)

# 1番ボタンをクリック
client.click_button_by_number(1)
```

#### 便利関数
```python
from src.debug.debug_helper import quick_test_button_navigation, test_all_visible_buttons

# 基本テスト
quick_test_button_navigation()

# 全ボタンテスト
test_all_visible_buttons()
```

### テスト結果

全ての単体テストが成功し、機能が正常に動作することを確認済み。