# ゲームデバッグガイド - Web APIを使用した効率的なデバッグ方法

## 概要

このドキュメントでは、Dungeonゲームの開発時に利用可能なWeb APIを使用した効率的なデバッグ方法について説明します。デバッグ用Web APIは`uv run main.py`でゲームを起動する際に自動的に起動し、ゲームの状態を外部から制御・監視できるツールです。

## Web APIの機能

### 利用可能なエンドポイント

1. **GET /screenshot**
   - ゲームの現在の画面をスクリーンショットとして取得
   - 画面遷移の確認やUI要素の表示状態の検証に使用
   - レスポンス: `{"jpeg": "base64エンコードされた画像データ"}`

2. **POST /input/key**
   - キーボード入力をゲームに送信
   - パラメータ（クエリパラメータ）：
     - `code`: ASCII コード（例：ESCキー = 27）
     - `down`: キーの押下（true）/離す（false）
   - レスポンス: `{"ok": true}`

3. **POST /input/mouse**
   - マウス入力をゲームに送信
   - パラメータ（クエリパラメータ）：
     - `x`, `y`: 座標
     - `action`: "down" | "up" | "move"
     - `button`: ボタン番号（デフォルト: 1）
   - レスポンス: `{"ok": true}`

4. **GET /game/state** （新機能）
   - ゲームの現在の状態を取得
   - 現在のゲーム状態、施設、アクティブウィンドウなどの情報
   - レスポンス: `{"current_state": "...", "current_facility": "...", "active_window": {...}}`

5. **GET /game/visible_buttons** （新機能）
   - 現在表示されているボタンの情報を取得
   - ボタンのテキスト、位置、サイズなどの詳細情報
   - レスポンス: `{"buttons": [...], "count": 5}`

### APIサーバー情報

- **ベースURL**: `http://localhost:8765`
- **起動方法**: ゲーム起動時に自動的にポート8765で起動
- **プロトコル**: REST API（HTTP）

## デバッグワークフロー

### 1. 推奨デバッグフロー（新規：2025年7月）

#### A. スクリプトを使用した自動起動

```bash
# 最も簡単な方法：自動起動スクリプトを使用
./scripts/start_game_for_debug.sh

# ゲームが起動し、APIが利用可能になったら自動的に制御が返される
# ✓ Debug API is ready!
# Game is running (PID: 12345)
# API endpoint: http://localhost:8765
```

#### B. Python APIクライアントを使用

```python
# Python経由でのデバッグ（許可不要、より柔軟）
from src.debug.game_debug_client import GameDebugClient

client = GameDebugClient()
if client.wait_for_api():
    # スクリーンショット取得
    image = client.screenshot("debug.jpg")
    
    # ESCキー送信
    client.press_escape()
    
    # 背景色分析
    color = client.analyze_background_color()
    print(f"Background color: {color}")
    
    # ゲーム状態の確認（新機能）
    state = client.get_game_state()
    print(f"Current facility: {state.get('current_facility')}")
    print(f"Active window: {state.get('active_window')}")
    
    # 表示されているボタンを確認（新機能）
    buttons = client.get_visible_buttons()
    for button in buttons.get('buttons', []):
        print(f"Button: '{button['text']}' at {button['center']}")
    
    # テキストでボタンをクリック（新機能）
    client.click_button_by_text("冒険者ギルド")
```

#### C. コマンドライン経由

```bash
# Python APIクライアントをコマンドラインで使用
uv run python src/debug/game_debug_client.py screenshot --save debug.jpg
uv run python src/debug/game_debug_client.py escape
uv run python src/debug/game_debug_client.py analyze
```

### 2. 従来のデバッグフロー（curlコマンド）

```bash
# ゲームの起動（Web APIサーバーも同時に起動）
uv run main.py

# 別のターミナルからcurlコマンドでAPIを利用してデバッグ
curl "http://localhost:8765/screenshot"
curl -X POST "http://localhost:8765/input/key?code=27&down=true"
```

**注意**: curlコマンドによるデバッグは毎回許可が必要なため、Python APIクライアントの使用を推奨します。

### 2. 画面遷移のテスト

```bash
# 例：設定画面への遷移テスト
# 1. 現在の画面を確認
curl "http://localhost:8765/screenshot" > initial_screen.json

# 2. ESCキーを押下
curl -X POST "http://localhost:8765/input/key?code=27&down=true"
curl -X POST "http://localhost:8765/input/key?code=27&down=false"

# 3. 画面が切り替わったことを確認
curl "http://localhost:8765/screenshot" > after_esc_screen.json
```

### 3. UI要素の動作確認

```bash
# 例：メニュー項目の選択テスト
# 1. 現在のメニュー状態を確認
curl "http://localhost:8765/screenshot" > menu_state.json

# 2. マウスクリック
curl -X POST "http://localhost:8765/input/mouse?x=400&y=300&action=down&button=1"
curl -X POST "http://localhost:8765/input/mouse?x=400&y=300&action=up&button=1"

# 3. 結果を確認
curl "http://localhost:8765/screenshot" > after_click.json
```

## 具体的なデバッグシナリオ

### シナリオ1: 施設画面の表示確認

```bash
# 問題：施設画面が表示されない（0051_facilities_is_not_display.md）

# 1. ゲーム起動後、初期画面を確認
curl "http://localhost:8765/screenshot" | jq -r .jpeg | base64 -d > initial.jpg

# 2. 施設選択メニューが表示されているか視覚的に確認
# （画像ファイルを確認）

# 3. 各施設ボタンをクリックして遷移を確認
curl -X POST "http://localhost:8765/input/mouse?x=200&y=150&action=down"
curl "http://localhost:8765/screenshot" | jq -r .jpeg | base64 -d > facility_click.jpg
```

### シナリオ2: ダイアログウィンドウの動作確認

```bash
# 問題：ダイアログが正しく表示されない

# 1. ダイアログを表示するアクションを実行
curl -X POST "http://localhost:8765/input/key?code=32&down=true"  # スペースキー

# 2. ダイアログの表示状態を確認
curl "http://localhost:8765/screenshot" | jq -r .jpeg | base64 -d > dialog.jpg

# 3. ESCキーでダイアログが閉じるか確認
curl -X POST "http://localhost:8765/input/key?code=27&down=true"
curl "http://localhost:8765/screenshot" | jq -r .jpeg | base64 -d > dialog_closed.jpg
```

### シナリオ3: 戦闘システムのデバッグ

```bash
# 戦闘中の状態確認

# 1. 戦闘画面に遷移（仮定）
curl -X POST "http://localhost:8765/input/key?code=98&down=true"  # 'b'キー

# 2. 戦闘画面の初期状態を確認
curl "http://localhost:8765/screenshot" | jq -r .jpeg | base64 -d > battle_start.jpg

# 3. 攻撃アクションを選択
curl -X POST "http://localhost:8765/input/key?code=49&down=true"  # '1'キー

# 4. 行動後の状態を確認
curl "http://localhost:8765/screenshot" | jq -r .jpeg | base64 -d > after_attack.jpg
```

## スクリプトによる自動化

### デバッグセッション記録スクリプト

```bash
#!/bin/bash
# debug_session.sh

SESSION_DIR="debug_session_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$SESSION_DIR"

echo "デバッグセッション開始: $SESSION_DIR"

# 初期状態のスクリーンショット
curl -s "http://localhost:8765/screenshot" | jq -r .jpeg | base64 -d > "$SESSION_DIR/001_initial.jpg"
echo "初期画面を保存: 001_initial.jpg"

# 操作とスクリーンショットのペア
function capture_and_save() {
    local action="$1"
    local filename="$2"
    
    eval "$action"
    sleep 0.5  # 画面更新を待つ
    curl -s "http://localhost:8765/screenshot" | jq -r .jpeg | base64 -d > "$SESSION_DIR/$filename"
    echo "操作後画面を保存: $filename"
}

# ESCキー押下テスト
capture_and_save "curl -X POST 'http://localhost:8765/input/key?code=27&down=true'" "002_esc_pressed.jpg"

# 結果表示
echo "デバッグセッション完了。ファイルは $SESSION_DIR に保存されました。"
ls -la "$SESSION_DIR"
```

## Claude Codeでの利用方法

```bash
# Claude Codeのターミナル内でAPIを直接呼び出し
curl "http://localhost:8765/screenshot" | jq -r .jpeg | base64 -d > /tmp/screenshot.jpg

# スクリーンショットをClaude Codeで表示
# （Readツールで画像ファイルを読み込むことで表示可能）
```

## TDDとの統合

### 1. テストファースト

```python
# tests/test_facility_display.py
import requests
import base64
from PIL import Image
import io

def test_facility_menu_display():
    """施設メニューが正しく表示されることを確認"""
    
    # 初期画面の取得
    response = requests.get("http://localhost:8765/screenshot")
    screenshot_data = base64.b64decode(response.json()["jpeg"])
    
    # 画像として読み込み
    image = Image.open(io.BytesIO(screenshot_data))
    
    # OCRや画像解析でUI要素の存在を確認
    # （実装は画像処理ライブラリに依存）
    assert image.size[0] > 0  # 画面が取得できていることを確認
```

### 2. 自動化されたビジュアルテスト

```python
# tests/visual_tests/test_screens.py
import requests
import base64
from pathlib import Path
from PIL import Image, ImageChops
import io

class TestVisualRegression:
    def test_main_menu_visual(self):
        # 現在のスクリーンショットを取得
        response = requests.get("http://localhost:8765/screenshot")
        current_data = base64.b64decode(response.json()["jpeg"])
        current_image = Image.open(io.BytesIO(current_data))
        
        # 期待される画像と比較
        expected_path = Path("tests/visual_tests/expected/main_menu.jpg")
        if expected_path.exists():
            expected_image = Image.open(expected_path)
            diff = ImageChops.difference(current_image, expected_image)
            
            # 差異の計算
            stat = ImageStat.Stat(diff)
            mean_diff = sum(stat.mean) / len(stat.mean)
            
            assert mean_diff < 5.0  # 閾値以下の差異は許容
        else:
            # 初回実行時は期待画像として保存
            current_image.save(expected_path)
```

## デバッグのベストプラクティス

### 1. 体系的なスクリーンショット収集

```bash
# デバッグセッションの記録
debug_session/
├── 001_initial_state.jpg
├── 002_after_esc_key.jpg
├── 003_settings_menu.jpg
├── session_commands.txt
└── session_log.txt
```

### 2. 入力シーケンスの記録

```bash
# commands.txt - 再現可能なバグレポート
curl "http://localhost:8765/screenshot" > 001_initial.json
curl -X POST "http://localhost:8765/input/key?code=27&down=true"
curl -X POST "http://localhost:8765/input/key?code=27&down=false"
curl "http://localhost:8765/screenshot" > 002_after_esc.json
curl -X POST "http://localhost:8765/input/mouse?x=400&y=300&action=down"
curl "http://localhost:8765/screenshot" > 003_after_click.json
```

### 3. CI/CDへの統合

```yaml
# .github/workflows/visual_tests.yml
- name: Run Visual Tests
  run: |
    uv run main.py &
    sleep 5
    # APIサーバーの起動確認
    curl --retry 5 --retry-delay 1 "http://localhost:8765/screenshot"
    # テスト実行
    uv run pytest tests/visual_tests/
```

## トラブルシューティング

### APIサーバーが起動しない場合

1. `uv run main.py`でゲームが正常に起動しているか確認
2. ポート8765が他のプロセスに使用されていないか確認：`lsof -i :8765`
3. ファイアウォール設定を確認

### スクリーンショットが取得できない場合

```bash
# APIサーバーの動作確認
curl -I "http://localhost:8765/screenshot"

# レスポンスの確認
curl "http://localhost:8765/screenshot" | jq .
```

### APIレスポンスが正常でない場合

```bash
# エラーレスポンスの詳細確認
curl -v "http://localhost:8765/screenshot"

# ゲームウィンドウがアクティブかどうか確認
```

## 高レベルデバッグツール（2025年7月追加）

### デバッグヘルパーの使用

```python
# 高レベルなデバッグ機能
from src.debug.debug_helper import DebugHelper, debug_game_session

# コンテキストマネージャーでゲームを自動管理
with debug_game_session() as client:
    helper = DebugHelper(client)
    
    # ESC遷移問題を自動検証
    results = helper.verify_esc_transition(save_screenshots=True)
    print(f"Transitions correct: {results['transitions_correct']}")
    
    # アクションシーケンスをキャプチャ
    captures = helper.capture_transition_sequence([
        ("escape", None),
        ("wait", 0.5),
        ("escape", None),
        ("wait", 0.5)
    ])
```

### 簡単なデバッグ実行

```python
# 一行でESC問題をデバッグ
from src.debug.debug_helper import quick_debug_esc_issue
quick_debug_esc_issue()
```

## pytest統合

### integrationテストの実行

```bash
# 通常のテスト（integrationテストは除外）
uv run pytest

# integrationテストを含めて実行
uv run pytest -m "integration or slow"

# 背景表示問題のテストのみ実行
uv run pytest -m integration tests/test_background_display_fix.py

# デバッグヘルパーを使ったテスト
uv run pytest tests/test_background_display_fix.py::TestBackgroundDisplayFix::test_esc_transition_with_debug_helper -v
```

### テストフィクスチャの使用

```python
# pytestテスト内でAPIクライアントを使用
def test_my_feature(game_api_client):
    # ゲームが既に起動している状態
    game_api_client.screenshot()
    game_api_client.press_escape()
    color = game_api_client.analyze_background_color()
    assert color == expected_color

def test_with_debug_helper(debug_helper):
    # 高レベルなデバッグ機能を使用
    results = debug_helper.verify_esc_transition()
    assert results['transitions_correct']
```

## ツール一覧

### ファイル構成

```
scripts/
├── start_game_for_debug.sh    # ゲーム自動起動スクリプト

src/debug/
├── game_debug_client.py       # Python APIクライアント
└── debug_helper.py            # 高レベルデバッグ機能

tests/
├── conftest.py                # pytestフィクスチャ
└── test_background_display_fix.py  # 背景表示問題のテスト
```

### 使用場面別推奨ツール

| 場面 | 推奨ツール |
|------|------------|
| 簡単なデバッグ | `scripts/start_game_for_debug.sh` + Python APIクライアント |
| 自動テスト | pytest + フィクスチャ |
| 複雑なシナリオ | DebugHelper |
| 問題の素早い確認 | `quick_debug_esc_issue()` |
| 画面遷移の検証 | `verify_esc_transition()` |
| CI/CD統合 | pytest integrationマーカー |

## 新規デバッグ機能（2025年1月追加）

### UI階層ダンプ機能

UI要素の構造やobject_idを即座に確認できる機能が追加されました。

#### 利用可能なエンドポイント

1. **GET /ui/hierarchy**
   - 現在のUI階層情報をJSON形式で取得
   - ウィンドウスタック、UI要素、親子関係を含む
   - レスポンス: `{"hierarchy": {...}, "timestamp": "..."}`

#### CLIコマンドでの使用

```bash
# UI階層をコンソールに表示（JSON形式）
uv run python -m src.debug.debug_cli ui-dump

# ツリー形式で見やすく表示
uv run python -m src.debug.debug_cli ui-dump --format tree

# ファイルに保存
uv run python -m src.debug.debug_cli ui-dump --save ui_state.json

# 特定のUI要素を検索
uv run python -m src.debug.debug_cli ui-find "button_id"

# フィルタリング（例：ボタンのみ表示）
uv run python -m src.debug.debug_cli ui-dump --filter "UIButton"
```

#### プログラムでの使用

```python
from src.debug.ui_debug_helper import UIDebugHelper

# UIヘルパーの初期化
ui_helper = UIDebugHelper()

# UI階層をダンプ
hierarchy = ui_helper.dump_ui_hierarchy()
print(f"Active windows: {len(hierarchy['windows'])}")
print(f"UI elements: {len(hierarchy['ui_elements'])}")

# 特定の要素を検索
element = ui_helper.find_element_by_id("save_button")
if element:
    print(f"Found: {element['type']} at {element['position']}")

# アクティブウィンドウの確認
windows = ui_helper.get_active_windows()
for window in windows:
    print(f"Window: {window['title']} (visible: {window['visible']})")
```

### 拡張エラーロギングシステム

エラー発生時のコンテキスト情報を詳細に記録する機能が追加されました。

#### 利用可能なエンドポイント

1. **POST /debug/log**
   - カスタムデバッグログエントリを追加
   - パラメータ：`level`, `message`, `context`
   - レスポンス: `{"ok": true, "message": "..."}`

2. **GET /debug/middleware/status**
   - デバッグミドルウェアの状態を取得
   - レスポンス: `{"middleware_available": true, ...}`

#### ゲームコードでの使用

```python
from src.debug import setup_enhanced_logging, log_game_error, log_ui_action, create_debug_context

# 1. ゲームインスタンスに拡張ロギングを適用
middleware = setup_enhanced_logging(game_instance)

# 2. エラーログ（詳細なコンテキスト付き）
try:
    facility_window.show_submenu()
except AttributeError as e:
    log_game_error(e, 
        context={"facility": "adventurer_guild", "action": "show_submenu"},
        ui_element=facility_window
    )

# 3. UI操作ログ
log_ui_action("button_click", 
    element_info={"id": "save_button", "text": "Save Game"},
    result="success"
)

# 4. デバッグセッション管理
with create_debug_context("facility_debug") as ctx:
    ctx.log("Starting facility menu test")
    # テスト処理...
    ctx.log("Test completed", status="success")
```

#### エラーログの詳細情報

拡張ロギングでは以下の情報が自動的に記録されます：

```json
{
  "timestamp": "2025-01-03T10:15:30",
  "level": "ERROR",
  "message": "UI Error occurred",
  "debug_info": {
    "error_type": "AttributeError",
    "error_message": "'WindowManager' object has no attribute 'show_dialog'",
    "ui_element": {
      "type": "UIButton",
      "object_id": "next_button",
      "position": {"x": 100, "y": 200},
      "size": {"width": 80, "height": 30},
      "visible": true
    },
    "context_stack": [
      {"method": "handle_event", "event_type": "MOUSEBUTTONDOWN"},
      {"method": "_handle_button_press", "element_id": "next_button"}
    ],
    "ui_state": {
      "windows": [...],
      "ui_elements": [...],
      "window_stack": [...]
    }
  }
}
```

### 統合デバッグワークフロー

UI階層ダンプと拡張ロギングを組み合わせた効率的なデバッグ：

```python
# 問題の再現と調査
from src.debug import setup_enhanced_logging, create_debug_context
from src.debug.ui_debug_helper import UIDebugHelper

# 拡張ロギングを有効化
middleware = setup_enhanced_logging(game_instance)

with create_debug_context("ui_investigation") as ctx:
    # 現在のUI状態を記録
    ui_helper = UIDebugHelper()
    initial_state = ui_helper.dump_ui_hierarchy()
    ctx.log("Initial UI state", ui_elements=len(initial_state['ui_elements']))
    
    # 問題の操作を実行
    try:
        trigger_problematic_action()
    except Exception as e:
        # エラー時のUI状態も記録
        error_state = ui_helper.dump_ui_hierarchy()
        ctx.log("Error occurred", 
            error=str(e),
            ui_diff=compare_ui_states(initial_state, error_state)
        )
        raise

# CLIでの確認
# uv run python -m src.debug.debug_cli ui-dump --format tree
```

### デバッグ機能の有効性確認

```python
from src.debug import check_debug_features

# 利用可能な機能を確認
features = check_debug_features()
print("Enhanced logging:", features["enhanced_logging"])
print("Debug middleware:", features["debug_middleware"])
print("UI debug helper:", features["ui_debug_helper"])
```

## まとめ

Web APIとPythonツールを活用することで、以下のメリットがあります：

1. **即座のデバッグ開始**: 自動起動スクリプトで待機時間なし
2. **許可不要**: Pythonコードのため毎回の許可が不要
3. **高レベル機能**: 複雑なデバッグシナリオを簡単に実行
4. **テスト統合**: pytestと完全に統合されたデバッグ環境
5. **自動化対応**: CI/CDパイプラインでの自動化が容易
6. **柔軟性**: コマンドライン、Python、pytest、すべてに対応
7. **UI階層の可視化**: object_idやウィンドウスタックを即座に確認
8. **詳細なエラーコンテキスト**: エラー発生時の完全な状態を記録

これらのツールを適切に活用することで、より効率的で品質の高いゲーム開発が可能になります。