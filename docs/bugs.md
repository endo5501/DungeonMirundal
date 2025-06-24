# Bugs

発生しているバグ(Known bugs)と修正済みのバグをまとめます。
修正後、必ずテストを実施し、バグ履歴(Bugs history)へ移動してください

## Known bugs

### 優先度:高 (進行不可能)

現在、優先度:高の問題はありません。

### 優先度:中

### 優先度:低

* [ ] [冒険者ギルド]-[クラスチェンジ]が未実装
* [ ] [教会]の[寄付をする]は削除する
* [ ] 設定画面-[設定]が未実装

## Bugs history


### 修正済み (2025-06-24)

* [x] ダンジョンへ遷移したあと、現在位置・レベル・コンパスの基本UIと操作ガイドUI以外灰色となり何も表示されない
  - 修正内容: DungeonRendererPygameクラスにauto_recoverメソッドを追加、初期描画処理を改善
  - 問題: ダンジョン遷移時の自動復旧処理でrender機能が正常に動作していなかった
  - 修正箇所: dungeon_renderer_pygame.py - auto_recover、update_ui、ensure_initial_renderメソッド
  - テスト: test_dungeon_renderer_fixes.pyで自動復旧機能をテスト
  - コミット: (修正済み)

* [x] ダンジョンへ遷移したあと、WASDを入力すると"_turn_right"メソッドが存在しないエラー
  - 修正内容: DungeonRendererPygameクラスに不足していた移動メソッドを追加
  - 問題: GameManagerがDungeonRendererPygameに存在しないメソッド(_turn_right等)を呼び出していた
  - 修正箇所: dungeon_renderer_pygame.py - _move_forward, _move_backward, _move_left, _move_right, _turn_left, _turn_right, _show_menuメソッドを追加
  - テスト: test_dungeon_renderer_fixes.pyで全移動メソッドの存在を確認
  - コミット: (修正済み)

* [x] [商店]-[アイテム購入]の各アイテムの先頭に文字化けした文字が付与されている
  - 修正内容: Unicode絵文字をASCII文字に置換
  - 問題: pygame-guiがUnicode絵文字（⚔🛡🧪🔧📦）を正しく表示できない
  - 修正箇所: shop.py - _format_item_display_name、_format_sellable_item_display_nameメソッド
  - 置換内容: ⚔→[W], 🛡→[A], 🧪→[C], 🔧→[T], 📦→[I]
  - テスト: test_shop_character_fix.pyで絵文字なし表示を確認
  - コミット: (修正済み)

* [x] 各施設の主人との会話、パーティ編成確認、キャラクター一覧、商店在庫確認のダイアログサイズが小さい
  - 修正内容: _show_dialogメソッドにテキスト量に応じた自動サイズ調整機能を追加
  - 問題: UIDialogのデフォルトサイズ(400x200)が小さく、長いテキストがはみ出していた
  - 修正箇所: 
    - base_facility.py: _show_dialogメソッドに動的サイズ計算機能を追加
    - guild.py: パーティ編成確認(700x450)、キャラクター一覧(750x500)
    - shop.py: 在庫確認(700x450)、商店主人との会話(550x350)
    - inn.py: 宿屋主人との会話(550x350)
  - テスト: test_text_display_fixes.pyで適切なサイズ設定を確認
  - コミット: (修正済み)

* [x] 各施設のメッセージUI上の[戻る]ボタンがメッセージの上に表示され、読みにくくなっている
  - 修正内容: ボタンの位置計算を修正してダイアログの下部に配置
  - 問題: ボタンがダイアログの外に配置され、メッセージと重なっていた
  - 修正箇所: base_facility.py - _show_dialogメソッドのボタン位置計算ロジック
  - 変更内容: ボタンをダイアログの右下角から配置するように修正
  - コミット: (修正済み)

### 修正済み (2025-06-23)

* [x] 4階層より深いメニューからの戻る処理が正常に動作していない問題
  - 修正内容: 宿屋のキャラクター別アイテム管理メニューで新メニューシステムを使用するように変更
  - 問題: 4階層目メニューで旧システムの_show_submenuを使用しており、適切なスタック管理ができていなかった
  - 主要修正箇所:
    - inn.py: _show_character_item_management, _show_character_item_detailで新システム対応
    - 戻るボタンのコールバックでback_to_previous_menu()を使用するよう修正
  - テスト: test_menu_architecture_integration.pyで深い階層のメニューナビゲーションを確認
  - コミット: 701bb66

* [x] [魔術師ギルド]-[キャラクター個別分析]-[キャラクタ]を表示したあと、[戻る]が無い問題
  - 修正内容: 魔術師ギルドの全ダイアログに戻るボタンを追加
  - 問題: キャラクター個別分析など複数のダイアログでbuttonsパラメータが省略されていた
  - 修正箇所: _analyze_character, _show_character_spell_usage, _show_spellbook_details等6つのダイアログ
  - テスト: 各ダイアログから適切に戻れることを確認
  - コミット: 2809cf9

* [x] [魔術師ギルド]-[魔術書購入]でのダイアログコールバックエラー
  - 修正内容: 確認ダイアログのコールバック関数で引数の数を統一
  - 問題: DialogTemplateが確認結果のboolean値を渡すが、ラムダ関数が引数を受け取らない設定だった
  - 修正パターン: lambda confirmed=None: action() if confirmed else None
  - 影響範囲: 魔術師ギルド、冒険者ギルド、寺院の確認ダイアログ
  - テスト: 魔術書購入の流れが正常に動作することを確認
  - コミット: 6346f94

* [x] [宿屋]-[酒場の噂話]のあと[OK]を押すとメニューが空になる問題
  - 修正内容: BaseFacilityとInnクラスでダイアログ終了後のメニュー復元処理を改善
  - 問題: ui_managerがNoneの場合やfacility_managerの処理でメインメニューが復元されなかった
  - 主要修正箇所:
    - base_facility.py: _close_dialog, _exit_facilityでの安全性向上
    - inn.py: _show_tavern_rumors, _talk_to_innkeeper, _show_travel_infoでの明示的なメニュー復元
  - テスト: test_inn_tavern_rumors_fix.pyで噂話ダイアログの適切な処理を確認
  - コミット: 7c10fb0

* [x] [冒険者ギルド]-[キャラクタ作成] で名前入力後、名前入力のエディットボックスが残り続ける
  - 修正内容: character_creation.pyで名前入力ダイアログの完全削除処理を実装
  - 問題: UIManager.hide_dialog()はダイアログを非表示にするだけで、dialogsディクショナリからは削除されないため、render()で継続して描画されていた
  - 解決: _on_name_confirmed()と_on_name_cancelled()で`del ui_manager.dialogs[dialog_id]`による完全削除を追加、安全性チェックも実装
  - テスト: test_character_creation_name_input_fix.pyで5項目のテストが全て通過、TDD手法による修正確認
* [x] 設定画面-[ゲームを保存]で保存先スロット選択画面が表示されない
* [x] 設定画面-[ゲームをロード]でロード元スロット選択画面が表示されない
* [x] [宿屋]-[冒険の準備]-[アイテム整理]-[宿屋倉庫の確認]が実装されていない
* [x] [ダンジョン入口]を選択すると、いきなりダンジョンへ遷移する。ダンジョン選択画面を表示するべき
    * ダンジョン選択画面では、ダンジョンの一覧が表示される。一覧には、ダンジョン名、難易度、属性、踏破済みかどうかの情報が表示される
    * [ダンジョンへ入る]で選択したダンジョンへ遷移する
    * [ダンジョン新規生成]で、自動生成したハッシュ値から新規ダンジョンを生成し、一覧に登録する
    * [ダンジョン破棄]で、一覧からダンジョンを破棄する
* [x] [冒険者ギルド]の画面を表示中にESCを押すと、背面の地上メニューのみが設定画面メニューに切り替わる。設定画面へ切り替わるべき

