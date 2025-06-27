# 現象

ESC-[設定]-[ゲームプレイ]-[戻る]を押しても戻れません  
`docs/fixed/0006_cannot_return_menu.md` と同様の現象と思われます

# 根本原因

設定UI（SettingsUI）の各カテゴリメニューから戻るボタンを押した際、メイン設定メニューが適切に再表示されない問題がありました。

## 問題の流れ

1. ESC → 設定画面表示（OverworldManager）
2. 設定 → 詳細設定UI（SettingsUI）表示
3. ゲームプレイ → ゲームプレイ設定表示
4. 戻る → `_back_to_main_settings`が呼ばれる
5. **問題**: メイン設定メニューが表示されない

## 技術的な原因

### 1. UIマネージャーの状態管理問題

`_back_to_main_settings`メソッドで`show_settings_menu`を呼び出しても、既に表示されているサブメニューが適切に隠されていないため、新しいメニューが表示されませんでした。

### 2. モーダルメニューの重複

PyGameのUIマネージャーではモーダルメニューが重複表示される際の制御が不十分で、既存のメニューを隠さずに新しいメニューを表示しようとすると正常に動作しないことがありました。

# 修正内容

## 修正ファイル: `src/ui/settings_ui.py`

### 1. `_back_to_main_settings`メソッドの修正（817-827行目）

**修正前**:
```python
def _back_to_main_settings(self):
    """メイン設定に戻る"""
    self.current_category = None
    self.show_settings_menu()
```

**修正後**:
```python
def _back_to_main_settings(self):
    """メイン設定に戻る"""
    self.current_category = None
    # 現在のメニューを隠す
    try:
        if ui_manager is not None:
            ui_manager.hide_all()
    except Exception as e:
        logger.warning(f"メニューを隠す際にエラーが発生しました: {e}")
    # メイン設定メニューを再表示
    self.show_settings_menu()
```

### 2. ダイアログ表示メソッドの修正（862-864行目）

未保存変更確認ダイアログの表示で、`register_element`と`show_element`を使用していた部分を`add_dialog`と`show_dialog`に修正しました。

## 修正の効果

1. **メニュー階層の正常な動作**: サブメニューから戻るボタンを押すと、確実にメイン設定メニューに戻るようになりました
2. **UIの一貫性向上**: すべての設定カテゴリで戻るボタンが正常に動作するようになりました
3. **エラーハンドリング強化**: メニューの隠し処理でエラーが発生しても適切にログに記録され、処理が継続されます

# テスト

## 作成されたテストファイル

`tests/test_settings_menu_return_bug.py` を作成し、以下のテストケースで問題を検証：

1. **ゲームプレイ設定の戻るボタンテスト**: 基本的な戻る動作の確認
2. **全カテゴリの戻るボタンテスト**: すべての設定カテゴリで戻るボタンの一貫性を確認
3. **キーバインド設定の戻るテスト**: 特殊なネストしたメニューでの戻る動作確認
4. **ダイアログ閉じる動作テスト**: ダイアログの適切な終了動作確認
5. **メニュー永続性テスト**: メニューが適切に再表示されることを確認

## テスト結果

```
tests/test_settings_menu_return_bug.py::TestSettingsMenuReturnBug::test_gameplay_settings_return_button_fails PASSED [100%]
tests/test_settings_menu_return_bug.py::TestSettingsMenuReturnBug::test_all_category_return_buttons PASSED [100%]
tests/test_settings_menu_return_bug.py::TestSettingsMenuReturnBug::test_keybind_settings_return_to_controls PASSED [100%]
tests/test_settings_menu_return_bug.py::TestSettingsMenuReturnBug::test_dialog_close_behavior PASSED [100%]
tests/test_settings_menu_return_bug.py::TestSettingsMenuReturnBug::test_menu_persistence_issue PASSED [100%]
```

全5つのテストが成功し、修正が正常に動作することを確認しました。

# 動作確認

修正後は以下の操作が正常に動作します：

1. ESC → 設定画面表示 ✅
2. 設定 → SettingsUI表示 ✅  
3. ゲームプレイ → ゲームプレイ設定表示 ✅
4. 戻る → メイン設定メニューに戻る ✅
5. その他のカテゴリでも同様に戻るボタンが動作 ✅

# 関連する修正

この修正は `docs/fixed/0006_cannot_return_menu.md` で行った施設メニューの戻るボタン修正と同じパターンの問題でした。設定UIでも同様の「親メニューへの適切な戻り処理」が必要でした。

# 影響範囲

- 設定UI（SettingsUI）のメニューナビゲーション
- ESCメニューからの設定画面アクセス
- 既存の機能には影響なし（回帰テスト実行済み）