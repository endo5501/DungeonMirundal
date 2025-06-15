# Bugs

発生しているバグ(Known bugs)と修正済みのバグをまとめます。
修正後、必ずテストを実施し、修正済みバグ(Fixed bugs)へ移動してください

## Known bugs

### キャラクタ作成画面
- [ ] キャラクター作成画面にて、"キャラクターの名前を入力してください:"と"名前を入力"のラベルが重なっています。
- [ ] キャラクター作成画面にて、[キャンセル]ボタンが文字化けしています
- [ ] キャラクター作成画面にて、[キャンセル]ボタンを押すとクラッシュします
- [ ] キャラクター作成画面にて、[振り直し]をすると、メニューがおかしくなります

### その他画面
- [ ] パーティ編成画面にて、キャラクタを追加した後、パーティ編成画面が表示される
- [ ] 設定画面にて、[ゲームをロード]を押すと"ロード完了"と表示され、メニューが地上画面のものになります。本来、セーブデータの選択画面が表示されるべきです
- [ ] 教会の祝福サービスにおいて、[戻る]キーが効かない
- [ ] 冒険者ギルドのキャラクター一覧において、メンバーが重複して表示される(2名しかメンバーがいないのに、その2名が2回表示される)
- [ ] 魔術師ギルドで、魔法分析が正しく行われない(エルフ魔術師 知恵:20でも魔法が使えない判定になっていた)

## Fixed bugs

- [x] 施設で[終了]を押すとメニューがすべて消えて操作できなくなる
  - 修正内容: **根本原因修正** - FacilityManagerを通した正しい退場処理フローを実装
  - 詳細: 
    * **根本原因**: BaseFacility._exit_facility()がself.exit()を直接呼び、FacilityManagerを経由していなかった
    * **問題**: FacilityManager.exit_current_facility()が呼ばれないため、on_facility_exit_callbackが実行されずOverworldManager.on_facility_exit()が呼ばれない
    * **解決策**: _exit_facility()をfacility_manager.exit_current_facility()を呼ぶように修正
    * **結果**: [終了]ボタンクリック時にコールバックが正しく実行され、地上部メニューが正常に復元される
  - 関連ファイル: `src/overworld/base_facility.py`, `src/overworld/overworld_manager.py`
  - 修正日: 2025-06-15 (根本原因解決)

- [x] キャラクター作成で名前を変更できない  
  - 修正内容: UITextInputとUIInputDialogクラスを実装。キャラクター作成ウィザードで実際のテキスト入力機能を有効化
  - 関連ファイル: `src/ui/base_ui.py`, `src/ui/character_creation.py`, `tests/test_name_validation.py`
  - 修正日: 2025-06-15

- [x] ダンジョンの入口に入るとクラッシュする
  - 修正内容: **2つの根本原因を修正** - Partyクラスのget_max_levelメソッド追加とUIDialogボタン形式の統一
  - 詳細:
    * **原因1**: DungeonSelectionUIがParty.get_max_level()を呼び出すが、メソッドが存在しなかった
    * **原因2**: UIDialogのボタン引数形式が不一致（タプル形式 vs 辞書形式）
    * **解決策1**: Party.get_max_level()メソッドを実装（パーティの最高レベルを返す）
    * **解決策2**: UIDialogボタンを辞書形式 `{"text": "テキスト", "command": コールバック}` に統一
    * **結果**: ダンジョン選択システムが正常動作、全12テストが通過
  - 関連ファイル: `src/character/party.py`, `src/ui/dungeon_selection_ui.py`, `tests/test_dungeon_selection_ui.py`
  - 修正日: 2025-06-16

- [x] src/rendering/dungeon_renderer.pyのテキストの国際化がなされていません
  - 修正内容: **ウィンドウタイトルの国際化対応** - config_managerを使用した多言語対応システム実装
  - 詳細:
    * **原因**: DungeonRendererのウィンドウタイトルが英語ハードコーディング（"Dungeon Explorer"）
    * **問題**: 日本語環境でも英語タイトルが表示される
    * **解決策**: 
      - config_managerをインポートしてapp.titleテキストキーを取得
      - 日本語/英語設定ファイルにapp.titleを追加（"ダンジョンエクスプローラー"/"Dungeon Explorer"）
      - テキスト取得失敗時のフォールバック機能実装
    * **結果**: 言語設定に応じたウィンドウタイトル表示、国際化テスト6個すべて通過
  - 関連ファイル: `src/rendering/dungeon_renderer.py`, `config/text/ja.yaml`, `config/text/en.yaml`, `tests/test_dungeon_renderer_i18n_simple.py`
  - 修正日: 2025-06-16


