# 現象

ウィンドウを閉じるとすべてのメニューが消える

# 再現方法

[宿屋]-[主人と話す]-[OK]
を行うと、メニューがすべて空になる。
その時、"メニュースタックが空になりました"というログメッセージが表示される。
[ダンジョン入り口]-[戻る]を押下しても同様に発生する

# 調査結果と修正

## 問題1: [宿屋]-[主人と話す]-[OK]パターン ✅ 修正済み

### 根本原因
`DialogTemplate._handle_dialog_close()`で無条件に`menu_stack_manager.back_to_previous()`を呼び出していた。
新メニューシステムでは`show_information_dialog()`がダイアログをメニュースタックに積まないため、
不正なスタック操作でメニューが消失していた。

### 修正内容
- `DialogTemplate._handle_dialog_close()`を修正
- 現在のメニューがDIALOGタイプの場合のみスタック操作を実行
- それ以外の場合はスタック操作をスキップ

### 修正対象ファイル
- `src/ui/dialog_template.py`
- `src/ui/menu_stack_manager.py`

### テストカバレッジ
- `test_dialog_close_issue.py`: ダイアログ閉じる問題のテスト
- `test_menu_stack_issue.py`: メニュースタック管理のテスト

## 問題2: [ダンジョン入り口]-[戻る]パターン ✅ 修正済み

### 根本原因
`CustomSelectionList`の戻るボタンが`kill()`のみを実行し、親メニューへの復帰処理がなかった。
ダンジョン選択画面で戻るボタンを押すと選択リストが破棄されるだけで、メインメニューが復旧されなかった。

### 修正内容
- `CustomSelectionList`に`on_back`コールバック機能を追加
- `OverworldManager._show_dungeon_selection_menu()`で戻るコールバックを設定
- 戻るボタン押下時に`_close_dungeon_selection_menu()`が実行されメインメニューに復帰

### 修正対象ファイル
- `src/ui/selection_list_ui.py`: `on_back`コールバック追加、戻るボタン処理修正
- `src/overworld/overworld_manager_pygame.py`: ダンジョン選択リストに戻るコールバック設定

### テストカバレッジ  
- `test_dungeon_entrance_back_issue.py`: ダンジョン入口戻るボタン問題のテスト

 # TODO
1. ✅ 調査後、上記エラーを検知するテストを作成する
2. ✅ 修正する（宿屋パターンは完了、ダンジョン入り口パターンも完了）
3. ✅ テストが成功することを確認する
4. ⏳ commitする

## 修正内容まとめ
両方のパターンを修正完了:
1. **[宿屋]-[主人と話す]-[OK]**: DialogTemplateのスタック管理を修正
2. **[ダンジョン入り口]-[戻る]**: CustomSelectionListにコールバック機能を追加
