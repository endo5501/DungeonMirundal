# Bugs

発生しているバグ(Known bugs)と修正済みのバグをまとめます。
修正後、必ずテストを実施し、修正済みバグ(Fixed bugs)へ移動してください

## Known bugs

### 優先度:高

### 優先度:低

## Fixed bugs

### 優先度:高 (2025-06-18修正完了) - 新規修正

- [x] [ダンジョン入口]を選択すると、ダンジョンが一つしか表示されない。複数登録可能か確認してください
    - 問題: DungeonSelectionUIは正常に複数ダンジョンを表示していた、設定確認により問題なし
    - 修正: ダンジョン設定（config/dungeons.yaml）の確認、複数ダンジョンが正常に登録・表示されることを確認
    - ファイル: `config/dungeons.yaml`, `src/ui/dungeon_selection_ui.py`
- [x] [ダンジョン入口]からダンジョンへ入ると、以下ログを出力してダンジョンへの遷移に失敗する(地上部に戻る)
    - 問題: GameManagerでダンジョン作成とenter_dungeonの処理順序が逆、DungeonGeneratorでdungeon_idパラメータ不足
    - 修正: transition_to_dungeonでcreate_dungeonを先に実行、generate_levelメソッドにdungeon_idパラメータ追加
    - ファイル: `src/core/game_manager.py`, `src/dungeon/dungeon_generator.py`, `src/dungeon/dungeon_manager.py`

### 優先度:低 (2025-06-18修正完了) - 新規修正

- [x] 商店の[在庫確認]を実行するとクラッシュする
    - 問題: ConfigManager.get_text()メソッドでキーワード引数が使用不可、TypeError発生
    - 修正: config_manager.get_text(key, parameter=value)を.format(parameter=value)形式に変更
    - ファイル: `src/overworld/facilities/shop.py`
- [x] 商店の[アイテム購入]から[武器]などを実行するとクラッシュする
    - 問題: 商店在庫確認と同じConfigManager.get_text()のキーワード引数問題
    - 修正: 購入成功メッセージ、カテゴリ表示、売却メッセージ等の文字列フォーマット修正
    - ファイル: `src/overworld/facilities/shop.py`

### 優先度:高 (2025-06-18修正完了) - バッチ修正

- [x] [ダンジョン入口]を実行するとクラッシュする
    - 問題: DirectScrolledListのscrollBarWidthパラメータが無効、生存メンバーチェック不備、テキスト設定エラー
    - 修正: `src/ui/dungeon_selection_ui.py`で無効パラメータ削除、`src/core/game_manager.py`でテストパーティ初期化改善、`src/core/config_manager.py`でdefaultパラメータ対応
    - ファイル: `src/ui/dungeon_selection_ui.py`, `src/core/game_manager.py`, `src/core/config_manager.py`
- [x] ダンジョン入口の入場確認で[はい]を押しても、ダンジョンに入れず、地上メニューに戻ってしまう
    - 問題: テストパーティのHP/MP初期化不備により生存判定でfalse、SaveSlotオブジェクトのプロパティアクセス不正
    - 修正: テストキャラクターのderived_stats初期化処理追加、SaveSlotの辞書アクセスをプロパティアクセスに修正
    - ファイル: `src/core/game_manager.py`, `src/overworld/overworld_manager.py`
- [x] テキスト設定ファイル不足によるエラーメッセージ表示問題
    - 問題: config_manager.get_textメソッドがdefaultパラメータ未対応
    - 修正: defaultパラメータ対応により適切なフォールバック処理を実装
    - ファイル: `src/core/config_manager.py`

### 優先度:中 (2025-06-18修正完了) - バッチ修正

- [x] 起動時の前回セーブデータの自動ロード(@docs/change_spec.md の対応が不完全)
    - 問題: SaveSlotオブジェクトを辞書としてアクセス、存在しないtimestampプロパティを使用
    - 修正: latest_save['slot_id'] → latest_save.slot_id、slot.timestamp → slot.last_saved
    - ファイル: `src/core/game_manager.py`, `src/overworld/overworld_manager.py`
- [x] [ゲームを保存]を押すとゲームがクラッシュする
    - 問題: CharacterクラスのシリアライゼーションでJSON非対応オブジェクト、属性不足
    - 修正: 防御的属性チェックとエラーハンドリング強化、詳細ログ出力追加
    - ファイル: `src/core/save_manager.py`, `src/character/character.py`, `src/overworld/overworld_manager.py`

### 優先度:低 (2025-06-18修正完了) - バッチ修正

- [x] 魔術師ギルドでは、魔術は魔術書から習得するので、[魔法習得]は削除して魔術書を購入出来る[魔術書購入]を追加するべき
    - 修正: 「魔法習得」メニューを「魔術書購入」に変更、カテゴリ別魔術書ショップシステム実装
    - 攻撃・回復・補助・高位魔法の魔術書を購入可能、ゴールド決済システム搭載
    - ファイル: `src/overworld/facilities/magic_guild.py`

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

