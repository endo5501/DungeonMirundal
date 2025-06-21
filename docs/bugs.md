# Bugs

発生しているバグ(Known bugs)と修正済みのバグをまとめます。
修正後、必ずテストを実施し、修正済みバグ(Fixed bugs)へ移動してください

## Known bugs

### 優先度:高

- [ ] ダンジョンに入った後、3Dのダンジョン画面が描画されない
  - ダンジョン入口からダンジョンに入った後、画面が位置情報とコンパス、操作ガイダンスのUIを除いて表示されない
  - しかし、WASDの操作は受け付け、位置の座標、コンパスは更新される。また、WASDの操作をした瞬間、一瞬だけダンジョンの3Dイメージが表示される
  - 現象発生時の画像は @docs/images/20250621-dungeon.png
  - 入った直後のログは以下の通り:
```
2025-06-21 10:29:23 - dungeon - WARNING - UI要素が見つかりません: dungeon_selection_menu
2025-06-21 10:29:23 - dungeon - INFO - ダンジョン 'beginners_cave' への遷移開始
2025-06-21 10:29:23 - dungeon - INFO - DungeonGeneratorを初期化: seed=beginners_cave_seed
2025-06-21 10:29:23 - dungeon - INFO - ダンジョンレベル1を生成: physical, 22x22
2025-06-21 10:29:23 - dungeon - INFO - ダンジョンbeginners_caveを作成しました
2025-06-21 10:29:23 - dungeon - INFO - パーティTESTがダンジョンbeginners_caveに入りました
2025-06-21 10:29:23 - dungeon - INFO - パーティが地上部から出ました
2025-06-21 10:29:23 - dungeon - INFO - ゲーム状態変更: overworld_exploration -> dungeon_exploration
2025-06-21 10:29:23 - dungeon - INFO - ダンジョンへの遷移が完了しました
2025-06-21 10:29:23 - dungeon - WARNING - 地上部はアクティブではありません
:text(warning): No definition in  for character U+4f4d
:text(warning): No definition in  for character U+7f6e
:text(warning): No definition in  for character U+30ec
:text(warning): No definition in  for character U+30d9
:text(warning): No definition in  for character U+30eb
```
  - 以下の点も問題ないか検討して
    - ライトが無い/シェーダ無効になっていないか
    - VRAM へのアップロードが初フレームに間に合ってないということはないか
    - カメラが迷宮内部に埋まっていないか
    - RenderPipeline / simplepbr はモデルを読む前に初期化してるか？

### 優先度:中

### 優先度:低

## Fixed bugs

