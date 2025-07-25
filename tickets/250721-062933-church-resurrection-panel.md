---
priority: 1
tags: ["feature", "ui", "church", "resurrection", "critical"]
description: "教会のキャラクター蘇生パネルの実装"
created_at: "2025-07-21T06:29:33Z"
started_at: 2025-07-21T07:03:19Z # Do not modify manually
closed_at: 2025-07-21T09:27:29Z # Do not modify manually
---

# Ticket Overview

教会のキャラクター蘇生機能が未実装となっている。死亡したキャラクターを蘇生させる機能は、ゲームプレイにおいて重要な要素であるため、優先的に実装する必要がある。この機能により、プレイヤーは死亡したパーティメンバーを教会で蘇生させることができるようになる。

## 背景
- 教会のサービスパネルに「蘇生」ボタンは存在するが、機能が未実装
- ダンジョン探索で死亡したキャラクターを復活させる手段が必要
- 蘇生には寄付金（ゴールド）が必要で、キャラクターのレベルに応じて金額が変動

## Tasks

- [x] 現在の教会UIと死亡システムの実装状況を調査
- [x] 蘇生対象キャラクター選択UIの設計
- [x] 死亡キャラクターのリスト表示機能の実装
- [x] 蘇生コスト計算ロジックの実装（レベル×基本料金）
- [x] 蘇生確認ダイアログの実装（料金表示含む）
- [x] 蘇生処理の実装（状態変更、HP回復）
- [x] 所持金不足時のエラーハンドリング
- [x] 蘇生成功/失敗のメッセージ表示
- [x] 蘇生後のキャラクターステータス初期化
- [x] パーティへの自動復帰処理
- [x] 日本語メッセージの実装と確認
- [x] ユニットテストの作成
- [x] 統合テストの実施
- [x] Run tests before closing and pass all tests (No exceptions)
- [x] Get developer approval before closing

## 受け入れ条件
- [x] 死亡状態のキャラクターが教会で確認できる
- [x] 蘇生対象を選択できる
- [x] 蘇生に必要な料金が事前に表示される
- [x] 所持金が足りない場合は蘇生できない
- [x] 蘇生後、キャラクターのHPが1で復活する
- [x] 蘇生したキャラクターがパーティに復帰する
- [x] すべてのメッセージが日本語で表示される
- [x] エラー時の適切なフィードバックがある

## Notes

- 蘇生料金の計算式：キャラクターレベル × 100ゴールド（仮）
- 死亡状態は「DEAD」ステータスで管理されている想定
- 蘇生後のHPは1（最小値）とする
- 灰（ASH）状態のキャラクターは別途対応が必要（将来的な拡張）
- パーティメンバー以外の冒険者ギルド登録キャラクターも蘇生可能とする
