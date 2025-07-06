# インタラクティブデバッグシェルの実装

## 概要

IPythonベースのインタラクティブなデバッグシェルを実装し、ゲーム実行中にリアルタイムでデバッグコマンドを実行できる環境を提供する。

## 背景

現在のデバッグ方法では、毎回curlコマンドやPythonスクリプトを実行する必要があり、試行錯誤的なデバッグには不向き。対話的にゲーム状態を調査・操作できる環境が必要。

## 実装内容

### 1. InteractiveGameDebuggerクラスの作成

```python
# src/debug/interactive_debugger.py
class InteractiveGameDebugger:
    def start_session(self)
    def attach_to_game(self, game_instance)
    def create_debug_namespace(self) -> Dict[str, Callable]
```

### 2. デバッグコマンド

```python
# 利用可能なコマンド例
screenshot()              # 現在の画面をキャプチャ
ui_dump()                # UI階層を表示
press("ESC")             # キー入力送信
click(400, 300)          # マウスクリック
find_ui("next_button")   # UI要素を検索
watch("player.hp")       # 値の変化を監視
breakpoint()             # 実行を一時停止
step()                   # ステップ実行
```

### 3. 高度な機能

```python
# マクロ機能
record_macro("test_facility_menu")
# ... 操作を記録 ...
end_macro()

# 条件付きブレークポイント
set_breakpoint(lambda: game.current_facility == "inn")

# 状態の検査と修正
inspect(game.player)
modify("game.player.gold", 1000)

# UI要素の操作
ui = find_ui("shop_window")
ui.click_button("buy_button")
ui.input_text("item_quantity", "5")
```

### 4. 起動方法

```bash
# 通常のゲーム起動
uv run main.py

# 別ターミナルでデバッグシェルをアタッチ
uv run python -m src.debug.interactive_debugger attach

# または、ゲーム起動時にデバッグシェルを組み込み
uv run main.py --debug-shell
```

### 5. カスタムコマンドの追加

```python
# src/debug/custom_commands.py
@debug_command("test_all_facilities")
def test_all_facilities():
    """すべての施設を順番にテスト"""
    for facility in ["guild", "inn", "shop", "temple"]:
        click_facility(facility)
        screenshot(f"facility_{facility}.jpg")
        press("ESC")
```

## 効果

- デバッグの対話的実行により調査時間を50%削減
- 複雑な操作シーケンスの簡単な実行
- デバッグ中の試行錯誤が容易に

## 優先度

**低** - 便利だが既存ツールでも代替可能

## 関連ファイル

- 新規作成: `src/debug/interactive_debugger.py`
- 新規作成: `src/debug/debug_commands.py`
- 新規作成: `src/debug/custom_commands.py`
- 更新: `main.py`（--debug-shellオプション追加）

## 実装時の注意

- セキュリティ（リモートアクセスの制限）
- ゲームループとの同期（スレッドセーフティ）
- コマンド履歴の保存と再利用

---

## 実装記録

（実装時に記録）