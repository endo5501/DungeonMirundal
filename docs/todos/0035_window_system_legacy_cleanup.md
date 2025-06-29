# 0035: WindowSystem - レガシーUIMenuクリーンアップ

## 目的
高優先度移行完了後の残存UIMenuシステムの段階的クリーンアップを実施する。

## 経緯
- 2025年6月29日: `docs/todos/0032_window_system_migration_high_priority.md`の高優先度移行完了
- help_ui.py、magic_ui.py、status_effects_ui.py、settings_ui.pyの新WindowSystemへの移行完了
- 多数のファイルでUIMenuが残存しており、段階的クリーンアップが必要

## 残存UIMenu使用箇所（調査結果）

### 1. テストファイル群
- `tests/test_settings_menu_navigation.py`
- `tests/test_base_ui_pygame.py` - UIMenuクラス自体のテスト
- `tests/test_menu_architecture_integration.py`

### 2. 中・低優先度UIファイル
以下は`docs/todos/0033_window_system_migration_medium_priority.md`、`docs/todos/0034_window_system_migration_low_priority.md`で管理済み：
- `src/ui/inventory_ui.py`
- `src/ui/equipment_ui.py`
- `src/character/character_creation.py`
- その他の地上部施設UI

### 3. 基盤システムファイル
- `src/ui/base_ui_pygame.py` - UIMenuクラス定義本体
- `src/ui/dungeon_ui_pygame.py` - ダンジョンUI（複雑な統合が必要）

## 作業方針

### Phase 1: 中優先度ファイルの移行完了待ち
- `0033_window_system_migration_medium_priority.md`の完了を待つ
- inventory_ui.py、equipment_ui.pyなどの主要UIファイルを優先

### Phase 2: 低優先度ファイルの移行完了待ち  
- `0034_window_system_migration_low_priority.md`の完了を待つ
- character_creation.pyなどの補助UIファイルを移行

### Phase 3: テストファイルの更新
- UIMenuクラステスト → WindowSystemテストに変更
- 統合テストの新WindowSystem対応
- レガシーUIMenu機能テストの削除または更新

### Phase 4: 基盤システムクリーンアップ
- `src/ui/base_ui_pygame.py`からUIMenuクラス削除
- `src/ui/dungeon_ui_pygame.py`の新WindowSystem統合
- 最終的なレガシーコード削除

## 技術的制約

### 削除順序の重要性
1. **依存関係**: UIMenuを使用する全てのファイルを先に移行
2. **テスト整合性**: 移行完了後にテストを更新
3. **段階的実施**: 一度に全削除すると他機能に影響

### リスク要因
- `src/ui/dungeon_ui_pygame.py`は複雑な3D描画と統合されている
- 既存のテストが多数存在し、互換性確保が必要
- base_ui_pygame.pyは多くのファイルでインポートされている

## 完了条件

### Phase 1-2 完了条件
- [ ] 中・低優先度移行の完了確認
- [ ] 残存UIMenu使用箇所の再調査

### Phase 3 完了条件  
- [ ] UIMenuテストの新WindowSystemテスト化
- [ ] 統合テストの更新
- [ ] レガシーテストコードの削除

### Phase 4 完了条件
- [ ] UIMenuクラスの完全削除
- [ ] base_ui_pygame.pyのクリーンアップ
- [ ] 全テストの通過確認
- [ ] レガシーインポート文の削除

## 関連ドキュメント
- `docs/todos/0032_window_system_migration_high_priority.md`: 高優先度移行（完了）
- `docs/todos/0033_window_system_migration_medium_priority.md`: 中優先度移行
- `docs/todos/0034_window_system_migration_low_priority.md`: 低優先度移行
- `docs/window_system.md`: WindowSystem設計書

## 注意事項
- 急速な削除は避け、段階的に実施すること
- 各Phase完了後に全体テストを実施すること
- ダンジョンUIの移行は特に慎重に行うこと