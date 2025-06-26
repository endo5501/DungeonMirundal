# 現象

## Phase 1

@docs/fixed/0002_dont_view_characters.md で修正された画像領域や名前が、おそらく地上マップの背景の裏にあるため、見え方が悪くなっている。
地上マップ画面の背景は完全透明で良いと思う

## Phase 2

試してみたが、やはりキャラクターステータスバーが地上マップの背景の裏に表示される。もしくは、地上マップのメニューボタンを"地上マップ" "パーティ:(パーティ名)|ゴールド:(所持金)G"のレイヤーに配置してしまってはどうか？

また、今回と関係あるかわからないが、ダンジョンに入ると、キャラクターステータスバーの描画がちらつく。

# 状況

## Phase 1:修正完了 ✅

**問題**: キャラクターステータスバーが地上マップの背景に隠れて表示されない

**原因**: キャラクターステータスバーがUIマネージャーの管理下に追加されておらず、描画順序が正しくなかった

**修正内容**:
1. `/home/satorue/Dungeon/src/overworld/overworld_manager_pygame.py`
   - `_initialize_character_status_bar()`でUIマネージャーにステータスバーを追加
   - `render()`メソッドから直接描画コードを削除（UIマネージャーが管理）

2. `/home/satorue/Dungeon/tests/ui/test_character_status_bar_fix.py`
   - 修正を検証するテストを追加

3. `/home/satorue/Dungeon/docs/fixed/0003_overworld_status_bar_rendering.md`
   - 詳細な修正記録を作成

**結果**: キャラクターの画像、名前、HP/MPバーが背景に隠れることなく、画面下部に正常に表示されるようになりました。

**関連ファイル**:
- @docs/fixed/0003_overworld_status_bar_rendering.md - 詳細な修正記録



