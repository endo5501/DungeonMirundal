# 現象

ESC-[パーティ状況]を押下しても、パーティ状況を表示するウィンドウが表示されない
@docs/how_to_debug_game.md を使ってデバッグをしながら解決しましょう

# 注意

修正の際は、t_wada式のTDDを使用して修正すること
修正完了後、全体テスト(uv run pytest)を実行し、エラーが出ていたら修正すること
作業完了後、このファイルに原因と修正内容について記載すること

# 原因と修正内容 (修正完了: 2025-07-02)

## 根本原因
1. **WindowManager API誤用**: `show_window()` メソッドが `modal=True` パラメータを受け付けないにも関わらず使用していた
2. **不正な参照**: `GameManager.get_instance()` を使用していたが、正しくは `WindowManager.get_instance()` を使用すべきだった
3. **DialogWindow初期化不完全**: UIManager設定やcreate()呼び出し、レジストリ登録が不足していた

## 修正内容

### 1. TDDアプローチでテスト作成
- `tests/test_party_status_display.py` を作成
- 3つの主要テストケースを実装:
  - パーティ状況ボタンで画面遷移するテスト
  - パーティ情報が正しく表示されるテスト
  - ESCキーで設定メニューに戻るテスト

### 2. コードの修正 (`src/overworld/overworld_manager_pygame.py`)
- `GameManager.get_instance()` → `WindowManager.get_instance()` に修正
- DialogWindowコンストラクタを正しいシグネチャに修正:
  ```python
  # 修正前
  dialog = DialogWindow("party_status_dialog")
  dialog.setup_dialog(title="パーティ状況", message=info_text, ...)
  
  # 修正後
  dialog = DialogWindow(
      window_id="party_status_dialog",
      dialog_type=DialogType.INFORMATION,
      message=info_text
  )
  ```
- 必要なUI設定を追加:
  ```python
  dialog.ui_manager = window_manager.ui_manager
  dialog.create()
  window_manager.window_registry[dialog.window_id] = dialog
  ```
- 不正なパラメータを削除: `show_window(dialog, modal=True)` → `show_window(dialog)`

### 3. 動作確認
- 全テストが成功: `uv run pytest -m integration tests/test_party_status_display.py`
- モーダルダイアログが正常に表示されることを確認
- ESCキーでの戻り動作が正常に機能することを確認

## 修正結果
- パーティ状況ボタンクリックでモーダルダイアログが正常に表示される
- パーティ情報（名前、メンバー数、ゴールド、キャラクター詳細）が適切に表示される
- ESCキーで設定メニューに正常に戻る
- WindowSystemベースのモーダルダイアログが完全に機能する

## 使用したデバッグツール
- デバッグAPI (`scripts/start_game_for_debug.sh`)
- Python APIクライアント (`src/debug/game_debug_client.py`)
- 高レベルデバッグヘルパー (`src/debug/debug_helper.py`)
- pytest統合テスト環境
