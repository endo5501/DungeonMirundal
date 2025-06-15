# Bugs

発生しているバグ(Known bugs)と修正済みのバグをまとめます。
修正後、必ずテストを実施し、修正済みバグ(Fixed bugs)へ移動してください

## Known bugs




## Fixed bugs

- [x] 施設で[終了]を押すとメニューがすべて消えて操作できなくなる
  - 修正内容: 施設退場時のメニュー復元処理を強化。フェイルセーフ機能とエラー回復処理を実装
  - 関連ファイル: `src/overworld/overworld_manager.py`, `tests/test_facility_exit_bug.py`
  - 修正日: 2025-06-15

- [x] キャラクター作成で名前を変更できない  
  - 修正内容: UITextInputとUIInputDialogクラスを実装。キャラクター作成ウィザードで実際のテキスト入力機能を有効化
  - 関連ファイル: `src/ui/base_ui.py`, `src/ui/character_creation.py`, `tests/test_name_validation.py`
  - 修正日: 2025-06-15

