---
priority: 1
tags: ["bug", "dungeon", "transition", "blackscreen", "critical", "regression"]
description: "ダンジョン入り口からダンジョン遷移時に画面が真っ暗になりUIが消失する問題の修正（回帰バグ）"
created_at: "2025-07-23T15:17:07Z"
started_at: 2025-07-23T15:22:44Z # Do not modify manually
closed_at: null   # Do not modify manually
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

- [ ] 過去の修正内容（250721-064456）の現在の状態を確認
- [ ] 関連ファイルの変更履歴を調査（SceneTransitionManager等）
- [ ] デバッグログでエラー・例外の確認
- [ ] SceneType/EventTypeのインポート状況を再確認
- [ ] ダンジョン遷移プロセスの現在の実行フローを調査
- [ ] pygame画面描画システムの動作確認
- [ ] ダンジョンレンダラーの初期化処理確認
- [ ] UI階層・ウィンドウマネージャーの状態確認
- [ ] メモリ使用量・リソースリークの確認
- [ ] イベントループ・入力処理システムの確認
- [ ] 回帰の原因となった変更を特定
- [ ] 修正の実装とテスト
- [ ] 複数ダンジョンでの遷移テスト実施
- [ ] エラー処理・フォールバック機能の確認
- [ ] 修正内容の安定性検証
- [ ] Run tests before closing and pass all tests (No exceptions)
- [ ] Get developer approval before closing

## 受け入れ条件
- [ ] ダンジョン選択後、正常にダンジョン画面に遷移する
- [ ] ダンジョン内でUI要素が正しく表示される
- [ ] キーボード・マウス操作が正常に動作する
- [ ] ダンジョンマップが正しく描画される
- [ ] プレイヤーの移動が可能
- [ ] ESCキーでダンジョンから地上部に復帰できる
- [ ] 複数のダンジョンで正常動作を確認
- [ ] エラー発生時の適切な処理
- [ ] 回帰防止策の実装

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
