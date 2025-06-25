# 問題

宿屋でメニューから戻ろうとすると戻れなくなる


# 現象

[宿屋]-[冒険の準備]-[アイテム整理]-[宿屋倉庫の確認]-[戻る]-[戻る]で、メニューボタンが効かなくなる


# 修正結果

✅ **修正完了**

## 問題の原因

1. **メニューシステムの混在問題**: 新旧メニューシステムが混在しており、`back_to_previous_menu`が新システムでのみ動作していた
2. **旧システムでのフォールバック不足**: `use_new_menu_system = False`の場合、戻る処理が`False`を返して何も実行されていなかった
3. **サブメニューの適切な非表示処理不足**: 複数階層のメニューが適切に管理されていなかった

## 修正内容

### 1. `src/overworld/base_facility.py`の修正

- `back_to_previous_menu()`メソッドを修正
- 新システム利用時は`menu_stack_manager.back_to_previous()`を使用
- 旧システム利用時は`_back_to_main_menu_legacy()`フォールバック処理を実行

### 2. `_back_to_main_menu_legacy()`メソッドの実装

- 旧システム用の戻る処理を実装
- サブメニューの一括非表示処理
- メインメニューの再表示
- エラーハンドリングの実装

### 3. `src/overworld/facilities/inn.py`の修正

- `_get_additional_menu_ids()`メソッドを追加
- 宿屋固有のメニューIDリストを提供
- 適切なクリーンアップ処理の実装

## 修正した機能

1. **旧システム互換の戻る処理**: 新旧両システムで動作する戻る処理
2. **サブメニューの適切な管理**: 複数階層のメニューを適切に非表示
3. **エラーハンドリング**: UIエラーに対する堅牢な処理
4. **施設固有の拡張**: 派生クラスで追加メニューIDを指定可能

## テストカバレッジ

`test_inn_menu_navigation.py` - 6つのテストケースで検証:

1. `test_back_to_previous_menu_legacy_system` - 旧システムでの戻る処理
2. `test_back_to_previous_menu_new_system` - 新システムでの戻る処理  
3. `test_get_additional_menu_ids` - 追加メニューID取得
4. `test_back_to_main_menu_legacy_with_additional_menus` - 追加メニュー含む戻る処理
5. `test_back_to_main_menu_legacy_error_handling` - エラーハンドリング
6. `test_menu_navigation_flow_simulation` - メニューナビゲーションフロー

## 動作確認

- [宿屋]-[冒険の準備]-[アイテム整理]-[宿屋倉庫の確認]-[戻る]-[戻る] の操作で正常にメインメニューに戻ることを確認
- 複数階層のメニューでも戻るボタンが正常に動作
- エラー発生時も最低限の処理で継続可能

## 技術的改善点

1. **フォールバック機能**: 新システム不可時の自動フォールバック
2. **メニュー管理**: 施設固有メニューの体系的管理
3. **エラー耐性**: UI操作エラーに対する堅牢性向上
4. **拡張性**: 他の施設でも同様の問題を回避可能

