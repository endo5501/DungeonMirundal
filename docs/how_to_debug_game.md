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

### APIサーバー情報

- **ベースURL**: `http://localhost:8765`
- **起動方法**: ゲーム起動時に自動的にポート8765で起動
- **プロトコル**: REST API（HTTP）

## デバッグワークフロー

### 1. 基本的なデバッグフロー

```bash
# ゲームの起動（Web APIサーバーも同時に起動）
uv run main.py

# 別のターミナルからcurlコマンドでAPIを利用してデバッグ
curl "http://localhost:8765/screenshot"
curl -X POST "http://localhost:8765/input/key?code=27&down=true"
```

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

## まとめ

Web APIを活用することで、以下のメリットがあります：

1. **安定性**: ゲーム再起動後もAPIエンドポイントは継続利用可能
2. **シンプルさ**: curlコマンドで簡単にテスト可能
3. **自動化**: スクリプトやCI/CDパイプラインでの自動化が容易
4. **デバッグ効率**: Claude Codeセッションを維持したままデバッグ継続
5. **再現性**: コマンドベースでバグの再現手順を正確に記録・実行
6. **視覚的検証**: スクリーンショットによる画面状態の客観的確認

このWeb APIを適切に活用することで、より効率的で品質の高いゲーム開発が可能になります。