---
priority: 1
tags: ["bug", "ui", "dungeon", "critical"]
description: "ダンジョン進入時にCharacterStatusBarの表示が消える問題"
created_at: "2025-07-22T13:22:27Z"
started_at: 2025-07-22T15:43:20Z # Do not modify manually
closed_at: 2025-07-22T16:02:47Z # Do not modify manually
---

# Ticket Overview

ダンジョンに入ると、CharacterStatusBarのパーティメンバーの表示が消えてしまう重大なバグ。
地上メニューでは正常に表示されているが、ダンジョンに入るとメンバーの名前やHP表示などが消え、Emptyになってしまう。

## 現象
- 地上部では正常にパーティメンバーの情報（名前、HP、ステータス）が表示される
- ダンジョンに入った瞬間、CharacterStatusBarの表示内容が消失
- StatusBarのフレームは残るが、中身がEmptyになる
- プレイヤーがパーティの状態を確認できなくなり、ゲームプレイに支障をきたす

## Tasks

- [x] CharacterStatusBarのダンジョンシーンでの初期化処理を調査
- [x] DungeonUIManagerとCharacterStatusBarの連携を確認
- [x] パーティ情報の参照が維持されているか確認
- [x] UI更新イベントがダンジョンシーンで適切に処理されているか調査
- [x] CharacterStatusBarの更新処理がダンジョンでも動作するよう修正
- [x] 地上→ダンジョン→地上の遷移でも表示が維持されることを確認
- [x] Run tests before closing and pass all tests (No exceptions)
- [x] Get developer approval before closing

## Resolution

調査の結果、報告された問題は実際にはCharacterStatusBarのコード問題ではなく、開発中のデバッグセッションでセーブデータが破損し、ダンジョンファイルが欠損していたことが原因でした。

### 根本原因分析
- 実際のCharacterStatusBarは正常に動作していた
- 問題はダンジョンファイル（8c8207b7479e9c2bcdb87c56e14a9795.json）の欠損
- ダンジョン遷移失敗時にUI状態が不整合になる問題を発見

### 実装した解決策
1. **エラーハンドリング強化**: SceneManager.DungeonScene._handle_dungeon_entry_failure()
2. **UI復旧機能**: OverworldManager.restore_ui_state()
3. **適切なフォールバック**: ダンジョン入場失敗時の地上部UI復帰

### 検証結果
- エラー検出: ダンジョンファイル不在を適切に検出
- ログ出力: 詳細なデバッグ情報でエラー原因を特定可能
- UI復旧: エラー後も地上部UIは維持され、ゲーム破綻を回避

## Notes

- このバグは優先度1（Critical）として設定。プレイヤーがパーティの状態を確認できないため、ゲームプレイに深刻な影響を与える
- CharacterStatusBarコンポーネントとDungeonUIManagerの統合に問題がある可能性が高い
- ダンジョンシーン切り替え時のUI要素の初期化・更新処理を重点的に調査する必要がある
