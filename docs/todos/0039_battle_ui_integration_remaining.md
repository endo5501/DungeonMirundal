# 0039: BattleUI統合 - 残り作業

## 目的
既存のBattleUIWindow実装とダンジョンシステムの統合、および戦闘UI関連の残り作業を完了する。

## 経緯
- WindowSystem移行作業により、EquipmentWindow、InventoryWindow、CharacterCreationWizard、DungeonMenuWindowの移行が完了
- BattleUIWindowとBattleUIManagerが既に実装されているが、実際のダンジョンシステムとの統合が未完了
- dungeon_ui_pygame.pyには戦闘UI要素が含まれておらず、別途統合が必要

## 現状分析

### 既存実装の確認
- `src/ui/window_system/battle_ui_window.py` - 戦闘UIウィンドウ（実装済み）
- `src/ui/window_system/battle_ui_manager.py` - 戦闘UI管理（実装済み）
- `src/ui/window_system/battle_types.py` - 戦闘UI型定義（実装済み）

### 移行完了済み
- `src/ui/windows/equipment_window.py` - 装備ウィンドウ ✅
- `src/ui/windows/inventory_window.py` - インベントリウィンドウ ✅
- `src/ui/windows/character_creation_wizard.py` - キャラクター作成ウィザード ✅
- `src/ui/windows/dungeon_menu_window.py` - ダンジョンメニューウィンドウ ✅

## 残り作業

### 1. BattleUIWindow統合テスト作成
**ファイル**: `tests/ui/windows/test_battle_ui_integration.py`

**作業内容**:
- 既存BattleUIWindowのテストカバレッジ確認
- ダンジョンシステムとの統合テスト作成
- 戦闘開始〜終了までのフローテスト
- パーティと敵の状態管理テスト

### 2. 戦闘UI統合マネージャー作成
**ファイル**: `src/ui/windows/battle_integration_manager.py`

**作業内容**:
- 既存BattleUIManagerと新WindowSystemの橋渡し
- ダンジョン探索から戦闘画面への遷移管理
- 戦闘終了後のダンジョン画面復帰管理
- パーティ状態の同期管理

### 3. ダンジョン-戦闘UI連携
**ファイル**: `src/ui/windows/dungeon_battle_coordinator.py`

**作業内容**:
- DungeonMenuWindowからBattleUIWindowへの画面遷移
- 戦闘発生時のコンテキスト保存・復元
- 戦闘結果のダンジョン状態への反映
- UI状態の一貫性保証

### 4. 戦闘UIアダプタ作成(オプション)
**ファイル**: `src/ui/battle_ui_adapter.py`

**作業内容**:
- ※:現在、開発中なので旧インタフェースとの互換性維持は必須ではない
- 既存戦闘システムとの互換性維持
- 旧インターフェースから新BattleUIWindowへの橋渡し
- 戦闘関連コールバックの統合管理

### 5. 統合テストスイート作成
**ファイル**: `tests/integration/test_ui_system_integration.py`

**作業内容**:
- 全WindowSystem要素の統合テスト
- ダンジョン探索→戦闘→装備変更→インベントリ管理のフローテスト
- メモリリーク検証
- パフォーマンステスト

## 技術仕様

### BattleUI統合アーキテクチャ
```python
# ダンジョン探索中
DungeonMenuWindow
    ↓ (戦闘発生)
BattleIntegrationManager
    ↓
BattleUIWindow (既存)
    ↓ (戦闘終了)
DungeonBattleCoordinator
    ↓
DungeonMenuWindow (復帰)
```

### データフロー管理
- **戦闘開始時**: パーティ状態、敵情報、ダンジョンコンテキストの保存
- **戦闘中**: BattleUIManagerによる状態管理
- **戦闘終了時**: 結果のダンジョン状態への反映、UI状態復元

### イベント管理
- **戦闘開始イベント**: `battle_start`
- **戦闘終了イベント**: `battle_end`
- **戦闘逃走イベント**: `battle_escape`
- **戦闘勝利イベント**: `battle_victory`
- **戦闘敗北イベント**: `battle_defeat`

## 依存関係・影響範囲

### 上流依存
- WindowManager, FocusManagerの安定動作
- 既存BattleUIWindow, BattleUIManagerの動作確認
- ダンジョンシステムの戦闘発生ロジック

### 下流影響
- ダンジョン探索システムとの統合
- 経験値・レベルアップシステムとの連携
- アイテムドロップシステムとの統合
- セーブ・ロードシステムへの影響

### 横断的影響
- 全UI要素間の一貫性保証
- イベントシステムの統一
- エラーハンドリングの統合

## 実装優先度

### 高優先度
1. **BattleUIWindow統合テスト作成** - 既存実装の動作確認
2. **戦闘UI統合マネージャー作成** - 基本的な統合機能

### 中優先度
3. **ダンジョン-戦闘UI連携** - 画面遷移の実装
4. **戦闘UIアダプタ作成** - 互換性確保

### 低優先度
5. **統合テストスイート作成** - 品質保証

## テスト要件

### 単体テスト
- BattleIntegrationManagerの機能テスト
- DungeonBattleCoordinatorの状態管理テスト
- 各アダプタの互換性テスト

### 統合テスト
- ダンジョン→戦闘→ダンジョンのフローテスト
- 複数戦闘の連続実行テスト
- エラー発生時のUI状態復旧テスト

### シナリオテスト
- 実際のゲームプレイシナリオでの動作確認
- 長時間プレイでの安定性確認
- 戦闘パターンの網羅的テスト

## リスク・制約事項

### 技術的リスク
- 既存BattleUIWindowの未知の制約
- ダンジョンシステムとの状態同期の複雑性
- パフォーマンス影響の可能性

### 業務リスク
- 既存戦闘システムへの影響
- 統合作業の複雑化
- テスト工数の増大

### 軽減策
- 段階的統合による影響局所化
- 既存BattleUIWindowの詳細調査
- プロトタイプによる事前検証

## 完了条件
- [ ] BattleUIWindow統合テスト実装・通過
- [ ] 戦闘UI統合マネージャー実装・テスト通過
- [ ] ダンジョン-戦闘UI連携実装・動作確認
- [ ] 戦闘UIアダプタ実装・互換性確認
- [ ] 統合テストスイート実装・全テスト通過
- [ ] ダンジョン探索→戦闘→結果反映のフロー動作確認
- [ ] 既存戦闘システムとの互換性確認
- [ ] パフォーマンス劣化なし確認

## 現在の状況（2025-06-29更新）
**既存BattleUIWindow実装は存在するが、ダンジョンシステムとの統合が未完了**。

### 前提条件の確認状況
- ✅ WindowManager, FocusManagerの安定動作（0034で確認済み）
- 🔄 既存BattleUIWindow, BattleUIManagerの動作確認（要調査）
- 🔄 ダンジョンシステムの戦闘発生ロジック（要調査）

### 影響範囲
- **優先度**: 中（ゲーム機能完成度）
- **緊急性**: 低（既存実装で最低限動作）
- **依存関係**: ダンジョンシステム設計

### 推奨アプローチ
1. 既存BattleUIWindow実装の詳細調査
2. ダンジョンシステムとの統合ポイント特定
3. 最小限の統合から段階的実装

## 関連ドキュメント
- `docs/todos/0033_window_system_migration_medium_priority.md`: 本移行作業
- `src/ui/window_system/battle_ui_window.py`: 既存戦闘UIウィンドウ実装
- `src/ui/window_system/battle_ui_manager.py`: 既存戦闘UI管理実装
- `docs/window_system.md`: WindowSystem設計書

## 備考
- 既存BattleUIWindowが完成度の高い実装であることを前提とする
- 新たなBattleUIWindow実装ではなく、既存実装の統合に焦点を当てる
- dungeon_ui_pygame.pyの戦闘関連機能が限定的であることを考慮し、主にダンジョンメニューシステムの移行を重視