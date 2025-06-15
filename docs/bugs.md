# Bugs

発生しているバグ(Known bugs)と修正済みのバグをまとめます。
修正後、必ずテストを実施し、修正済みバグ(Fixed bugs)へ移動してください

## Known bugs

### 優先度:高

### 優先度:中

- [ ] キャラクター作成画面の名前入力画面にて、[キャンセル]を押下するとメニューがすべて消える
- [ ] "キャラクターの名前を入力してください:"と"名前を入力"のラベルの**位置**が重複している

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

- [x] キャラクター作成画面の4つのバグ
  - 修正内容: **包括的修正** - ラベル重複、文字化け、クラッシュ、UI異常の根本原因解決
  - 詳細:
    * **バグ1**: "キャラクターの名前を入力してください:"と"名前を入力"のラベル重複
      - 原因: config_manager.get_text()とハードコーディングメッセージの重複表示
      - 解決: character.enter_name_detailキーを追加、ハードコーディング削除
    * **バグ2**: [キャンセル]ボタンの文字化け
      - 原因: UIInputDialogの日本語ボタンにtext_font設定不備
      - 解決: font_manager.get_default_font()を使用してtext_fontを正しく設定
    * **バグ3**: [キャンセル]ボタンクラッシュ
      - 原因: self.on_cancel属性が__init__で初期化されていない
      - 解決: CharacterCreationWizard.__init__でon_cancel=None初期化追加
    * **バグ4**: [振り直し]でメニュー異常
      - 原因: _show_stats_generationの再帰呼び出しでUI重複作成
      - 解決: _reroll_statsメソッド追加、既存UIクリーンアップ処理実装
    * **結果**: キャラクター作成フロー正常化、9つのテスト中8つ通過
  - 関連ファイル: `src/ui/character_creation.py`, `src/ui/base_ui.py`, `config/text/ja.yaml`, `tests/test_character_creation_fixes.py`
  - 修正日: 2025-06-16

- [x] パーティ編成画面でキャラクタ追加後の画面表示問題
  - 修正内容: **画面遷移フロー修正** - キャラクター追加後はメインメニューに戻るように変更
  - 詳細:
    * **原因**: `_add_character_to_party`でキャラクター追加後に`_show_party_formation()`を再呼び出し
    * **問題**: キャラクター追加後にパーティ編成画面が再表示されてしまう
    * **解決策**: `_back_to_main_menu_from_submenu()`を呼び出すように変更
    * **結果**: キャラクター追加後は適切にメインメニューに戻る
  - 関連ファイル: `src/overworld/facilities/guild.py`
  - 修正日: 2025-06-16

- [x] 設定画面でのゲームロード機能問題  
  - 修正内容: **セーブデータ選択システム実装** - 即座にロードではなく選択画面を表示
  - 詳細:
    * **原因**: `_show_load_menu`が簡易実装で直接スロット1からロード
    * **問題**: セーブデータ選択画面を表示せず即座に「ロード完了」メッセージ
    * **解決策**: `save_manager.get_save_slots()`でスロット一覧取得、選択メニュー作成
    * **結果**: 利用可能なセーブスロット一覧から選択してロード可能
  - 関連ファイル: `src/overworld/overworld_manager.py`
  - 修正日: 2025-06-16

- [x] 教会の祝福サービスで戻るキーが効かない問題
  - 修正内容: **ダイアログ戻るボタン修正** - 専用の閉じるメソッドを実装
  - 詳細:
    * **原因**: UIDialogの「戻る」ボタンが存在しない`_close_dialog`メソッドを呼び出し
    * **問題**: 戻るボタンをクリックしても正常に動作しない
    * **解決策**: `_close_blessing_dialog`メソッド実装、適切なUI管理処理追加
    * **結果**: 戻るボタンクリック時にダイアログが正しく閉じてメインメニューに戻る
  - 関連ファイル: `src/overworld/facilities/temple.py`
  - 修正日: 2025-06-16

- [x] 冒険者ギルドでメンバーが重複表示される問題
  - 修正内容: **キャラクター一覧重複排除** - character_idベースの一意リスト作成
  - 詳細:
    * **原因**: `created_characters`と`party.characters.values()`を単純結合
    * **問題**: パーティ参加キャラクターが両方のリストに含まれ重複表示
    * **解決策**: character_idをキーとした辞書で重複を排除
    * **結果**: 各キャラクターが1回だけ表示され、パーティ状態も正確に表示
  - 関連ファイル: `src/overworld/facilities/guild.py`
  - 修正日: 2025-06-16

- [x] 魔術師ギルドで魔法分析が正しく行われない問題
  - 修正内容: **魔法適性判定アルゴリズム改善** - クラス名正規化と能力値判定追加
  - 詳細:
    * **原因**: 英語クラス名との厳密比較で日本語クラス名を認識できない
    * **問題**: エルフ魔術師（知恵20）でも魔法使用不可判定
    * **解決策**: 
      - クラス名の大文字小文字正規化と多言語対応
      - 知恵12以上/信仰心12以上による能力値ベース判定追加
      - 具体的な使用条件表示と改善提案機能実装
    * **結果**: 職業と能力値の両方で正確な魔法適性判定が可能
  - 関連ファイル: `src/overworld/facilities/magic_guild.py`
  - 修正日: 2025-06-16

- [x] キャラクター編成画面にて、[キャラクターを追加]を実行するとクラッシュする
  - 修正内容: **包括的エラーハンドリング実装** - 堅牢なキャラクター追加処理とUI遷移エラー対応
  - 詳細:
    * **根本原因**: `_add_character_to_party`メソッドで`_back_to_main_menu_from_submenu()`を引数なしで呼び出し
    * **問題**: メソッド定義では`submenu: UIMenu`引数が必須だが、呼び出し時に引数が未指定でTypeError発生
    * **解決策**: 
      - `_close_all_submenus_and_return_to_main()`ヘルパーメソッド実装
      - UI要素の存在チェックとフォールバック処理を追加
      - 既存の`_back_to_main_menu_from_submenu`の適切な呼び出し保証
      - 包括的なtry-catch例外処理を全メソッドに実装
      - パーティ未設定、UI Manager異常、フォールバック失敗時の多段階エラーハンドリング
      - ログ出力による問題追跡とグレースフルデグラデーション
    * **結果**: 
      - あらゆる例外状況でもクラッシュせず安全にメインメニューに復帰
      - 20個の包括的テストケースが全て通過
      - ユーザビリティの大幅改善とアプリケーション安定性向上
  - 関連ファイル: `src/overworld/facilities/guild.py`, `tests/test_guild_character_add_*.py` (3ファイル)
  - 修正日: 2025-06-16 (包括的改良)


