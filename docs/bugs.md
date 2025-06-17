# Bugs

発生しているバグ(Known bugs)と修正済みのバグをまとめます。
修正後、必ずテストを実施し、修正済みバグ(Fixed bugs)へ移動してください

## Known bugs

- [ ] ダンジョン入口の入場確認で[はい]を押しても、ダンジョンに入れず、地上メニューに戻ってしまう。修正が完了していないようです
- [ ] 起動時の前回セーブデータの自動ロード(@docs/change_spec.md の対応が不完全)
- [ ] 魔術師ギルドの魔法習得がメンバーに魔術師がいても使用できない

## Fixed bugs

### 優先度:高 (2025-06-17修正完了) - 新規修正

- [x] ダンジョン入口の入場確認で[はい]を押しても、ダンジョンに入れず、地上メニューに戻ってしまう
    - 問題: OverworldManagerとGameManagerでチェック基準が不一致（意識vs生存）
    - 修正: `overworld_manager.py`で`get_conscious_characters()`を`get_living_characters()`に変更
    - ファイル: `src/overworld/overworld_manager.py:575`
    - テスト: `tests/test_dungeon_entrance_logic_fix.py`

### 優先度:中 (2025-06-17修正完了) - 新規修正

- [x] 設定画面でゲームをロード後、[OK]を押すとロード画面のメニューと地上メニューが重なって表示されてしまう
    - 問題: `_back_to_settings_menu`メソッドの重複定義とロード後のメインメニュー表示
    - 修正: 重複メソッドの統合、ロード後に設定メニューに戻るよう修正
    - ファイル: `src/overworld/overworld_manager.py:556`
- [x] 設定画面の[パーティ状況]-[パーティ全体情報]からキャラクター選択ボタンを押すとゲームが落ちる
    - 問題: Characterクラスに`equipment`プロパティ、`get_personal_inventory()`メソッドが不足
    - 修正: 不足していたプロパティとメソッドを追加、BaseStatsにvitality、DerivedStatsに戦闘関連属性を追加
    - ファイル: `src/character/character.py`, `src/character/stats.py`, `src/overworld/overworld_manager.py`
    - テスト: `tests/test_character_details_crash_fix.py`
- [x] 設定画面で[パーティ状況]-[戻る]を押しても、[パーティ状況]のボタンが残り続ける
    - 問題: 重複した`_back_to_settings_menu`メソッド定義による意図しない動作
    - 修正: メソッド統合と呼び出し元に応じた適切な処理を実装
    - ファイル: `src/overworld/overworld_manager.py`

### 優先度:高 (2025-06-17修正完了) - 既存修正

- [x] ダンジョンに入るとUIManager.show_dialog AttributeErrorが発生してクラッシュする
    - 問題: `overworld_manager.py`で`ui_manager.show_dialog()`に存在しない`element_id`パラメータを渡していた
    - 修正: `element_id`パラメータを削除し、デフォルトボタンを使用するように変更
    - ファイル: `src/overworld/overworld_manager.py:732`
- [x] テストパーティ作成で存在しないモジュールをインポートしている
    - 問題: `character_classes`、`races`モジュールが存在しないのにインポートを試行
    - 修正: 文字列で直接種族・職業を指定するように変更
    - ファイル: `src/core/game_manager.py:592-601`

### 優先度:高 (2025-06-16修正完了)

- [x] 全体的にボタンの高さを増加してほしい
    - `base_ui.py`でボタン高さを0.15→0.22に増加
- [x] 地上メニューのレイアウトが使いにくくなっている。地上メニューでは、縦にボタンを配置してほしい
    - `UIMenu._rebuild_menu()`を横配置から縦配置に変更
- [x] 各施設のボタンが重なり合っている。
    - ボタン間の幅を増加してほしい
    - 縦配置により重なり問題を解決
- [x] 設定画面も縦にボタンを配置してほしい
    - 設定画面は`UIMenu`を使用しているため自動的に縦配置に
- [x] 各施設に入った後の[OK]ボタンが、施設の紹介メッセージの上に表示されてしまっている。[OK]ボタンの位置を下げることはできないか
    - `UIDialog._create_buttons()`でボタン位置を-0.3→-0.45に調整

