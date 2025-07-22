---
priority: 1
tags: ["bug", "ui", "dungeon", "critical"]
description: "ダンジョン進入時にCharacterStatusBarの表示が消える問題"
created_at: "2025-07-22T13:22:27Z"
started_at: null  # Do not modify manually
closed_at: null   # Do not modify manually
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

- [ ] CharacterStatusBarのダンジョンシーンでの初期化処理を調査
- [ ] DungeonUIManagerとCharacterStatusBarの連携を確認
- [ ] パーティ情報の参照が維持されているか確認
- [ ] UI更新イベントがダンジョンシーンで適切に処理されているか調査
- [ ] CharacterStatusBarの更新処理がダンジョンでも動作するよう修正
- [ ] 地上→ダンジョン→地上の遷移でも表示が維持されることを確認
- [ ] Run tests before closing and pass all tests (No exceptions)
- [ ] Get developer approval before closing

## Notes

- このバグは優先度1（Critical）として設定。プレイヤーがパーティの状態を確認できないため、ゲームプレイに深刻な影響を与える
- CharacterStatusBarコンポーネントとDungeonUIManagerの統合に問題がある可能性が高い
- ダンジョンシーン切り替え時のUI要素の初期化・更新処理を重点的に調査する必要がある
