# TODO

以下の順に、リファクタリング(Fowler式)を実施していきましょう。

1. ✅ @src/character 以下のコードをFowler式のリファクタリングしましょう。
    明らかに使用されていない処理(特にPanda3D用コード)やファイルは削除しましょう。
    リファクタリング後、テストを実施しエラーを確実に解消してください
    完了後、作業内容をこちらに記載した後一旦commitしてください

   **実施したリファクタリング：**
   - **Remove Duplicated Code**: 重複メソッド削除（can_use_spell, restore_mp, initialize_status_effects, get_race_name, get_class_name）
   - **Extract Method**: 長いcreate_characterメソッドを小さなメソッドに分割
   - **Replace Magic Number with Named Constant**: class_change.pyで定数化（MIN_LEVEL_FOR_CLASS_CHANGE, DEFAULT_CLASS_CHANGE_COST）
   - **Design Consistency**: vitality統計の適切な使用（HPボーナス計算でstrengthからvitalityに変更）
   - **Defensive Programming**: get_race_name/get_class_nameメソッドにdefaultパラメータ追加
   
   **テスト結果：** キャラクター関連の41テストすべて成功

2. ✅ @src/combat 以下のコードをFowler式のリファクタリングしましょう。
    明らかに使用されていない処理(特にPanda3D用コード)やファイルは削除しましょう。
    リファクタリング後、テストを実施しエラーを確実に解消してください
    完了後、作業内容をこちらに記載した後一旦commitしてください

   **実施したリファクタリング：**
   - **Replace Magic Number with Named Constant**: 戦闘定数を13個定数化（命中率、クリティカル率等）
   - **Replace Conditional with Polymorphism**: `_execute_specific_action`をaction_mapでスッキリ
   - **Extract Method**: 長い`_apply_spell_effect`を5つの小さなメソッドに分割
   - **Move Method**: CombatStatsクラスに統計管理メソッドを追加（Data Classからの脱却）
   - **Encapsulate Field**: 統計更新を専用メソッド経由に変更

   **テスト結果：** コンバット関連の32テストすべて成功

3. ✅ @src/core 以下のコードをFowler式のリファクタリングしましょう。
    明らかに使用されていない処理(特にPanda3D用コード)やファイルは削除しましょう。
    リファクタリング後、テストを実施しエラーを確実に解消してください
    完了後、作業内容をこちらに記載した後一旦commitしてください

   **実施したリファクタリング：**
   - **Replace Type Code with Class**: 文字列状態をGameLocation/GameStateのEnumに変更
   - **Remove Duplicated Code**: 重複するload_game_stateメソッドを削除
   - **Extract Method**: 長い_create_test_partyを3つのメソッドに分割（_create_test_character, _create_fallback_party）
   - **Replace Magic Number with Named Constant**: ConfigManagerで6つの定数を追加
   - **Extract Method**: ConfigManagerに_is_invalid_text_formatメソッドを抽出

   **テスト結果：** コア関連の22テストすべて成功

4. ✅ @src/dungeon 以下のコードをFowler式のリファクタリングしましょう。
    明らかに使用されていない処理(特にPanda3D用コード)やファイルは削除しましょう。
    リファクタリング後、テストを実施しエラーを確実に解消してください
    完了後、作業内容をこちらに記載した後一旦commitしてください

   **実施したリファクタリング：**
   - **Replace Magic Number with Named Constant**: ダンジョン生成で19個の定数を追加（サイズ、レート、制限値等）
   - **Extract Method**: 長い_place_special_elementsを3つのメソッドに分割（_place_stairs, _place_treasures, _place_traps）
   - **Remove Duplicated Code**: _direction_to_deltaメソッドの重複を解消（dungeon_generatorを再利用）
   - **Replace Magic Number with Named Constant**: DungeonManagerで5つの定数を追加

   **テスト結果：** ダンジョン関連の27テストすべて成功

5. ✅ @src/effects 以下のコードをFowler式のリファクタリングしましょう。
    明らかに使用されていない処理(特にPanda3D用コード)やファイルは削除しましょう。
    リファクタリング後、テストを実施しエラーを確実に解消してください
    完了後、作業内容をこちらに記載した後一旦commitしてください

   **実施したリファクタリング：**
   - **Replace Magic Number with Named Constant**: 8個の定数を追加（DEFAULT_POISON_DURATION等のデフォルト持続時間・強度、HEALTH_DAMAGE_RATIO等）
   - **Extract Method**: StatusEffectManagerの長いadd_effectメソッドから_should_apply_effectメソッドを抽出
   - **Extract Method**: 長いprocess_turnメソッドから_process_single_effect、_remove_expired_effectsメソッドを抽出
   - **Extract Method**: get_stat_modifiersメソッドから_create_default_modifiers、_apply_effect_modifiersメソッドを抽出
   - **Replace Conditional with Constants**: HPダメージ計算の魔法数20をHEALTH_DAMAGE_RATIOに統一

   **テスト結果：** エフェクト関連の26テストすべて成功

6. ✅ @src/encounter 以下のコードをFowler式のリファクタリングしましょう。
    明らかに使用されていない処理(特にPanda3D用コード)やファイルは削除しましょう。
    リファクタリング後、テストを実施しエラーを確実に解消してください
    完了後、作業内容をこちらに記載した後一旦commitしてください

   **実施したリファクタリング：**
   - **Replace Magic Number with Named Constant**: 15個の定数を追加（MAX_DUNGEON_LEVEL、確率関連定数、しきい値等）
   - **Extract Method**: 長いgenerate_encounterメソッドから_create_encounter_event、_finalize_encounterメソッドを抽出
   - **Extract Method**: _determine_monster_rankメソッドを4つの小さなメソッドに分割（_calculate_base_rank_probabilities等）
   - **Replace Magic Number with Named Constant**: 逃走・交渉確率計算の魔法数をすべて定数に置換
   - **Simplify Conditional**: 確率計算の複雑な条件文をより読みやすい形に改善

   **テスト結果：** エンカウンター関連の23テストすべて成功

7. ✅ @src/equipment 以下のコードをFowler式のリファクタリングしましょう。
    明らかに使用されていない処理(特にPanda3D用コード)やファイルは削除しましょう。
    リファクタリング後、テストを実施しエラーを確実に解消してください
    完了後、作業内容をこちらに記載した後一旦commitしてください

   **実施したリファクタリング：**
   - **Replace Magic Number with Named Constant**: 3個の定数を追加（MIN_CONDITION_FOR_EQUIP、DEFAULT_BONUS_VALUE、INITIAL_TOTAL_WEIGHT）
   - **Extract Method**: _calculate_item_bonusメソッドを3つの小さなメソッドに分割（_get_basic_item_bonus、_apply_additional_bonuses、_apply_condition_modifier）
   - **Extract Method**: can_equip_itemメソッドから検証ロジックを分離（_check_slot_compatibility、_check_class_restriction、_check_item_condition）
   - **Extract Method**: get_total_weightメソッドから_get_item_weightメソッドを抽出
   - **Replace Magic Number with Named Constant**: ボーナス値や重量の初期値をすべて定数に置換

   **テスト結果：** 装備関連の30テストすべて成功

8. ✅ @src/inventory 以下のコードをFowler式のリファクタリングしましょう。
    明らかに使用されていない処理(特にPanda3D用コード)やファイルは削除しましょう。
    リファクタリング後、テストを実施しエラーを確実に解消してください
    完了後、作業内容をこちらに記載した後一旦commitしてください

   **実施したリファクタリング：**
   - **Replace Magic Number with Named Constant**: 6個の定数を追加（DEFAULT_CHARACTER_SLOTS、DEFAULT_PARTY_SLOTS、MINIMUM_REMOVE_QUANTITY等）
   - **Extract Method**: get_total_weightメソッドから_calculate_slot_weightメソッドを抽出
   - **Extract Method**: get_total_valueメソッドから_calculate_slot_valueメソッドを抽出
   - **Extract Method**: sort_itemsメソッドから_get_sort_keyメソッドを抽出
   - **Replace Magic Number with Named Constant**: スロット数、数量、初期値等の魔法数をすべて定数に置換
   - **Simplify Method**: スロット計算ロジックを独立メソッドに分離して可読性向上

   **テスト結果：** インベントリ関連の24テストすべて成功

9. @src/items 以下のコードをFowler式のリファクタリングしましょう。
    明らかに使用されていない処理(特にPanda3D用コード)やファイルは削除しましょう。
    リファクタリング後、テストを実施しエラーを確実に解消してください
    完了後、作業内容をこちらに記載した後一旦commitしてください

10. @src/magic 以下のコードをFowler式のリファクタリングしましょう。
    明らかに使用されていない処理(特にPanda3D用コード)やファイルは削除しましょう。
    リファクタリング後、テストを実施しエラーを確実に解消してください
    完了後、作業内容をこちらに記載した後一旦commitしてください

11. @src/monsters 以下のコードをFowler式のリファクタリングしましょう。
    明らかに使用されていない処理(特にPanda3D用コード)やファイルは削除しましょう。
    リファクタリング後、テストを実施しエラーを確実に解消してください
    完了後、作業内容をこちらに記載した後一旦commitしてください

12. @src/navigation 以下のコードをFowler式のリファクタリングしましょう。
    明らかに使用されていない処理(特にPanda3D用コード)やファイルは削除しましょう。
    リファクタリング後、テストを実施しエラーを確実に解消してください
    完了後、作業内容をこちらに記載した後一旦commitしてください

13. @src/overworld 以下のコードをFowler式のリファクタリングしましょう。
    明らかに使用されていない処理(特にPanda3D用コード)やファイルは削除しましょう。
    リファクタリング後、テストを実施しエラーを確実に解消してください
    完了後、作業内容をこちらに記載した後一旦commitしてください

14. @src/rendering 以下のコードをFowler式のリファクタリングしましょう。
    明らかに使用されていない処理(特にPanda3D用コード)やファイルは削除しましょう。
    リファクタリング後、テストを実施しエラーを確実に解消してください
    完了後、作業内容をこちらに記載した後一旦commitしてください

15. @src/ui 以下のコードをFowler式のリファクタリングしましょう。
    明らかに使用されていない処理(特にPanda3D用コード)やファイルは削除しましょう。
    リファクタリング後、テストを実施しエラーを確実に解消してください
    完了後、作業内容をこちらに記載した後一旦commitしてください

16. @src/utils 以下のコードをFowler式のリファクタリングしましょう。
    明らかに使用されていない処理(特にPanda3D用コード)やファイルは削除しましょう。
    リファクタリング後、テストを実施しエラーを確実に解消してください
    完了後、作業内容をこちらに記載した後一旦commitしてください

