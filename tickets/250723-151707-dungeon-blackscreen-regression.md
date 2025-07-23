---
priority: 1
tags: ["bug", "dungeon", "transition", "blackscreen", "critical", "regression"]
description: "ダンジョン入り口からダンジョン遷移時に画面が真っ暗になりUIが消失する問題の修正（回帰バグ）"
created_at: "2025-07-23T15:17:07Z"
started_at: 2025-07-23T15:22:44Z # Do not modify manually
closed_at: 2025-07-23T16:23:07Z # Do not modify manually
---

# Ticket Overview

ダンジョン入り口からダンジョンに入ると、UIが全て消えて画面が真っ暗になる重大な問題が再発している。これは過去にチケット250721-064456で修正済みの問題の回帰バグと思われる。ゲームの核心機能であるダンジョン探索が不可能になっており、緊急の修正が必要。

## 問題の詳細
- ダンジョン入り口での操作は正常
- ダンジョン遷移開始後、画面が真っ暗になる
- UI要素が全て消失する
- キーボード・マウス操作が受け付けられない
- ESCキーでの脱出も不能
- ゲームの強制終了が必要
- 過去の修正（250721-064456）が何らかの理由で機能していない

## Tasks

- [x] 過去の修正内容（250721-064456）の現在の状態を確認
- [x] 関連ファイルの変更履歴を調査（SceneTransitionManager等）
- [x] デバッグログでエラー・例外の確認
- [x] SceneType/EventTypeのインポート状況を再確認
- [x] ダンジョン遷移プロセスの現在の実行フローを調査
- [x] pygame画面描画システムの動作確認
- [x] ダンジョンレンダラーの初期化処理確認
- [x] UI階層・ウィンドウマネージャーの状態確認
- [x] メモリ使用量・リソースリークの確認
- [x] イベントループ・入力処理システムの確認
- [x] 回帰の原因となった変更を特定
- [x] 修正の実装とテスト
- [x] 複数ダンジョンでの遷移テスト実施
- [x] エラー処理・フォールバック機能の確認
- [x] 修正内容の安定性検証
- [x] Run tests before closing and pass all tests (No exceptions)
- [x] Get developer approval before closing

## 受け入れ条件
- [x] ダンジョン選択後、正常にダンジョン画面に遷移する
- [x] ダンジョン内でUI要素が正しく表示される
- [x] キーボード・マウス操作が正常に動作する
- [x] ダンジョンマップが正しく描画される
- [x] プレイヤーの移動が可能
- [x] ESCキーでダンジョンから地上部に復帰できる
- [x] 複数のダンジョンで正常動作を確認
- [x] エラー発生時の適切な処理
- [x] 回帰防止策の実装

## Notes

### 参考情報
- 過去の修正チケット: @tickets/done/250721-064456-dungeon-transition-blackscreen-fix.md
- 前回の主な原因:
  - SceneTypeインポートエラー
  - Enum参照エラー (.value属性の問題)
  - EventType定義不足 (LOCATION_CHANGED)
- 前回の修正ファイル:
  - src/core/event_bus.py
  - src/core/scene/scene_transition_manager.py
  - src/overworld/overworld_manager.py
  - src/core/game_manager.py

### 調査の重点
- 過去の修正が取り消されているか確認
- 新しいコード変更による影響調査
- ダンジョン遷移システムの依存関係変更
- テスト不足による回帰の可能性

### 緊急性
このバグはゲームの核心機能を完全に無効化するため、最高優先度で対応する必要がある。

### 解決詳細

**実際の問題:** 前回のSceneType問題とは異なり、今回は「ダンジョンファイルが見つからない」エラーが根本原因でした。

**発見した原因:**
- `saves/dungeons/`ディレクトリは存在するが、ダンジョンJSONファイルが保存されていない
- DungeonManager.create_dungeon()がメモリ上でダンジョンを作成するが、ファイル保存が後回しになっている
- SceneTransitionManagerのload_dungeon()が失敗した際のフォールバック処理が不十分

**実装した修正（3層アプローチ）:**
1. **SceneTransitionManager修正** (`src/core/scene/scene_transition_manager.py`)
   - load_dungeon()が失敗した際のcreate_dungeon()フォールバック処理を追加
   - エラーハンドリングと復旧機能を強化

2. **DungeonManager修正** (`src/dungeon/dungeon_manager.py`)
   - create_dungeon()でダンジョン作成と同時にファイル保存を実行
   - load_dungeon()での自動復旧機能（ファイルなし時の新規作成）を追加

3. **テスト修正** (`tests/test_dungeon_manager.py`)
   - test_load_nonexistent_dungeon()を新しい自動復旧動作に合わせて更新

**検証結果:**
- ダンジョン遷移が正常に動作することを確認
- セーブデータ初期化後もダンジョンファイルが正しく生成・保存される
- 全941個のテストがパスすることを確認
