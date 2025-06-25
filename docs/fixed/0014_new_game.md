# 実装完了

設定画面にて、[新規ゲーム開始]を追加する
[新規ゲーム開始]を押すと、キャラクターなどの情報すべてをクリアした状態でゲームを開始する

✅ **実装完了**

## 実装内容

### 1. 設定メニューに新規ゲーム開始項目を追加

`src/ui/settings_ui.py` の `_create_main_settings_menu()` メソッドに新規ゲーム開始項目を追加：

```python
settings_menu.add_menu_item(
    "新規ゲーム開始",
    self._show_new_game_confirmation
)
```

### 2. 二段階確認ダイアログシステム

#### 第一段階確認 (`_show_new_game_confirmation()`)
- 警告メッセージでセーブデータ削除の危険性を明示
- ユーザーに操作の重要性を理解させる

#### 最終確認 (`_show_final_new_game_confirmation()`)
- より詳細な削除対象の説明（キャラクター、パーティ、進行状況）
- 最後の確認機会を提供

### 3. セーブデータクリア機能 (`_clear_all_save_data()`)

以下のディレクトリ内のすべてのファイルを削除：
```python
save_dirs = [
    Path("saves"),
    Path("saves/characters"),
    Path("saves/parties"), 
    Path("saves/dungeons"),
    Path("saves/game_state")
]
```

### 4. デフォルトパーティ作成 (`_create_default_party()`)

セーブデータクリア後に新しいパーティを自動作成：
```python
default_party = Party("新しい冒険者")
save_manager.save_party(default_party)
```

### 5. タイトル画面遷移 (`_return_to_title()`)

GameManagerを使用してタイトル画面に戻る：
```python
if hasattr(game_manager, 'return_to_title'):
    game_manager.return_to_title()
else:
    # フォールバック: GameStateを使用
    game_manager.set_game_state(GameState.TITLE)
```

### 6. UIDialog修正

UIDialogコンストラクタの`buttons`パラメータが利用できない問題を修正。
手動でUIButtonを作成・追加する方式に変更：

```python
dialog = UIDialog("dialog_id", "title", "message")
button = UIButton("btn_id", "text", x=..., y=...)
button.on_click = callback
dialog.add_element(button)
```

## テストカバレッジ

`test_new_game_feature.py` で以下をテスト：

1. **UI要素の存在確認**：設定メニューに新規ゲーム項目が存在
2. **確認ダイアログ**：両段階の確認ダイアログが正しく表示
3. **セーブデータクリア**：ファイル削除処理の動作
4. **パーティ作成**：デフォルトパーティの自動生成
5. **画面遷移**：タイトル画面への正しい遷移
6. **エラーハンドリング**：失敗時のエラーメッセージ表示

## 安全性の配慮

1. **二段階確認**：誤操作を防ぐ複数の確認ステップ
2. **明確な警告**：データ削除の不可逆性を明示
3. **エラーハンドリング**：処理失敗時の適切なメッセージ表示
4. **ログ記録**：操作の記録でデバッグを支援

## 使用フロー

1. 設定画面を開く
2. "新規ゲーム開始"を選択
3. 第一確認ダイアログで"はい"を選択
4. 最終確認ダイアログで"はい、新規ゲームを開始"を選択
5. セーブデータが完全にクリアされる
6. 新しいデフォルトパーティが作成される
7. タイトル画面に自動遷移

これにより、ユーザーは安全にゲームを最初から開始できるようになりました。
