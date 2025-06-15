# Bugs

発生しているバグ(Known bugs)と修正済みのバグをまとめます。
修正後、必ずテストを実施し、修正済みバグ(Fixed bugs)へ移動してください

## Known bugs




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

