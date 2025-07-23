---
priority: 2
tags: ["ui", "dungeon", "menu", "cleanup", "ux"]
description: "ダンジョンメニューから[地上に戻る]ボタンを削除し、階段システムによる地上帰還に統一"
created_at: "2025-07-23T16:35:47Z"
started_at: null  # Do not modify manually
closed_at: null   # Do not modify manually
---

# Ticket Overview

現在のダンジョンメニューには[地上に戻る]ボタンが存在するが、この機能は階段システム（チケット250722-132712）によって代替されるべきである。メニューボタンによる地上帰還は、Wizardry風ダンジョンクローラーの世界観とゲームメカニクスに適さないため、削除する必要がある。

## 問題の詳細

- **現状**: ダンジョンメニューに「地上に戻る」ボタンが存在
- **問題**: メニューからの直接帰還は以下の理由で不適切
  - Wizardry風ゲームでは階段や出口を物理的に見つけて脱出するのが基本
  - 緊急脱出的な機能は戦略性と緊張感を削ぐ
  - 階段システム（250722-132712）が実装される予定のため重複機能となる
- **影響範囲**: ダンジョンメニューウィンドウとその関連処理

## 関連チケット

- 250722-132712: ダンジョン階段システムと地上への出口実装 (階段による正当な地上帰還方法)

## Tasks

- [ ] ダンジョンメニューウィンドウから[地上に戻る]メニュー項目を削除
- [ ] `return_overworld` アクションの処理コードを削除
- [ ] 関連するコールバック設定を削除
- [ ] DungeonManagerの`return_to_overworld`メソッドが他で使用されていないか確認
- [ ] GameManagerの`transition_to_overworld`コールバック設定を削除
- [ ] テストファイルからも関連するテストケースを削除
- [ ] ダンジョンメニューUIの動作確認
- [ ] Run tests before closing and pass all tests (No exceptions)
- [ ] Get developer approval before closing

## 受け入れ条件

- [ ] ダンジョンメニューに[地上に戻る]ボタンが表示されない
- [ ] ダンジョンメニューからの地上帰還機能が無効化されている
- [ ] 既存のその他メニュー機能に影響がない
- [ ] 階段システム実装時に競合しない設計になっている
- [ ] 全てのテストが通過している

## 実装対象ファイル

1. `src/ui/windows/dungeon_menu_window.py` - メニュー項目定義の削除
2. `src/dungeon/dungeon_manager.py` - `return_to_overworld`メソッドの削除/無効化
3. `src/core/game_manager.py` - コールバック設定の削除
4. 関連するテストファイル

## Notes

### 設計思想

- **物理的な脱出経路**: プレイヤーは階段や出口を探索して地上に戻る必要がある
- **戦略性の維持**: メニューからの即座脱出を許可すると、リスク管理の戦略要素が失われる
- **一貫した世界観**: Wizardry風RPGでは物理法則に従った移動が基本

### 将来的な考慮事項

- 階段システム完成後は、1階層目に地上への出口が配置される
- 緊急脱出が必要な場合は、魔法アイテム等によるゲーム内システムとして実装する予定
- [ ] Run tests before closing and pass all tests (No exceptions)
- [ ] Get developer approval before closing


## Notes

{{Additional notes or requirements.}}
