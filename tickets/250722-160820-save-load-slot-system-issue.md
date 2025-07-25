---
priority: 2
tags: ["bug", "save-system", "load-system", "data-integrity"]
description: "セーブスロット2以降への保存が正常に反映されない問題"
created_at: "2025-07-22T16:08:20Z"
---

# セーブ/ロードスロットシステム問題

## 現象

複数のセーブスロットが表示されているにも関わらず、スロット2以降にセーブしたデータが正しく独立して保存されない問題。具体的には以下の動作が発生：

1. ゲーム中にセーブ画面でスロット2以降（例：スロット3）を選択してセーブを実行
2. ゲームを終了
3. 再度ゲームを起動し、ロード画面でセーブしたスロット（例：スロット3）を選択してロード
4. **期待**: セーブした時点の状態に復元される
5. **実際**: セーブした状態に戻らない、または異なるスロットのデータがロードされる

## 疑い

現在のセーブ/ロード画面では複数のセーブスロットがUIに表示されているが、内部的には実質1つのセーブデータしか管理されていない可能性がある。各スロット毎に独立したセーブデータの保存・ロードが正常に動作していない。

## 影響

- プレイヤーが複数の進行状況を保存できない
- セーブスロット機能が期待通りに動作しない
- データの整合性に関する不信を招く
- 複数パーティでのプレイスタイルが制限される

## Tasks

- [ ] 現在のセーブ/ロードシステムの実装を調査
- [ ] 各セーブスロットが独立してデータを保存しているか確認
- [ ] セーブファイルの命名規則と保存場所を確認
- [ ] ロード時のスロット選択処理を検証
- [ ] セーブ時のスロット指定処理を検証
- [ ] 各スロット間でのデータ独立性を確保する修正を実装
- [ ] 複数スロット間での保存・ロードが正常動作することをテスト
- [ ] エッジケースの検証（存在しないスロット、破損ファイル等）

## 期待される修正

各セーブスロットが完全に独立してデータを保存・ロードできるように修正：

1. **スロット毎の独立ファイル**: `save_01.json`, `save_02.json`, `save_03.json`等
2. **独立したデータ内容**: 各スロットで異なるパーティ、進行状況、設定を保持
3. **正確なスロット選択**: UI上で選択したスロット番号が確実に保存・ロードに反映
4. **データ整合性**: スロット間でのデータ混同や上書きの防止

## テストケース

- [ ] スロット1にパーティAで保存、スロット2にパーティBで保存後、各スロットから正しいパーティがロードされる
- [ ] 異なる進行状況（場所、所持金、ダンジョン進行度）を持つデータを複数スロットに保存し、それぞれが正確にロードされる
- [ ] セーブスロットの上書き（既存スロットへの再保存）が正常動作する