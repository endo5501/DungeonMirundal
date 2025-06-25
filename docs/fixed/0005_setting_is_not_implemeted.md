# 現象

設定画面の[設定]が、未実装。

設定画面では、以下の設定ができるようにしてほしい

* 言語切替:日/英

## 実装結果

✅ **完了しました**

### 実装内容

1. **言語切替機能**
   - 日本語/英語の切り替えに対応
   - 設定変更の即座反映
   - `src/ui/settings_ui.py:173-180`にて実装

2. **設定UI統合**
   - 地上部メインメニューから設定画面にアクセス可能
   - `src/overworld/overworld_manager_pygame.py:225-233`で接続

3. **永続化機能**
   - 設定は`config/user_settings.yaml`に保存
   - ゲーム再起動時も設定を保持
   - `src/ui/settings_ui.py:584-602`で実装

4. **包括的テスト**
   - 15個のテストケースで機能を検証
   - 言語切替、永続化、UI操作を網羅
   - `test_settings_functionality.py`で実装

### ファイル変更

- `src/ui/settings_ui.py` - 言語切替機能追加、UIマネージャー互換性修正
- `src/overworld/overworld_manager_pygame.py` - 設定ボタンの実装
- `test_settings_functionality.py` - 包括的テストスイート

### 使用方法

1. 地上部メインメニューで「設定」ボタンを選択
2. 「ゲームプレイ設定」→「言語 / Language」で切り替え
3. 設定は自動保存され、次回起動時も反映される
