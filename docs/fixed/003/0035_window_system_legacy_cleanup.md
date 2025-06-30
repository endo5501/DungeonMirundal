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

### Phase 1-2 完了条件 ✅ **完了済み**
- [x] ✅ **低優先度移行の完了確認** (0034完了済み)
- [x] ✅ 中優先度移行の完了確認（0033完了済み）
- [x] ✅ 残存UIMenu使用箇所の再調査（完了）

### Phase 3 完了条件 ✅ **部分完了**
- [x] ✅ legacyファイルの削除（4ファイル削除完了）
- [x] ✅ WindowSystemマネージャーコメント更新
- [x] ✅ 新WindowSystem正常動作確認
- [ ] 🔄 UIMenuテストの新WindowSystemテスト化（将来作業）
- [ ] 🔄 統合テストの更新（将来作業）

### Phase 4 完了条件 🔄 **MenuStackManager移行待ち**
- [ ] 🔄 UIMenuクラスの完全削除（0043 Phase 2以降で実施）
- [ ] 🔄 base_ui_pygame.pyのクリーンアップ（0043との調整後）
- [ ] 🔄 全テストの通過確認（段階的実施）
- [ ] 🔄 レガシーインポート文の削除（0043との連携）

## 現在の状況（2025-06-29更新）
**0035レガシーUIMenuクリーンアップの第一段階が完了しました。**

### 実施した作業
1. **legacyファイル削除**: 4ファイルを削除
   - `src/ui/character_creation_legacy.py` ✅
   - `src/ui/equipment_ui_legacy.py` ✅
   - `src/ui/dungeon_ui_pygame_legacy.py` ✅
   - `src/ui/inventory_ui_legacy.py` ✅

2. **WindowSystemマネージャー更新**: コメント・ドキュメント文字列の更新
   - inventory_manager.py ✅
   - equipment_manager.py ✅  
   - character_creation_manager.py ✅
   - dungeon_menu_manager.py ✅

3. **動作確認**: 新WindowSystemが正常動作確認済み ✅

### 成果
- **ファイル数削減**: 4個のlegacyファイル削除
- **ドキュメント品質向上**: 移行完了後の正確な記述に更新
- **システム安定性確認**: WindowSystem単体での正常動作確認

### 残存作業の方針
**Phase 4の完全UIMenu除去は0043のMenuStackManager段階的移行と連携して実施**
- MenuStackManager：Phase 1（基盤強化）継続中
- UIMenuクラス：地上部施設システムで現在も使用中
- 完全除去：0043のPhase 2以降で段階的実施

### 次回アクション
0043のMenuStackManager移行進展に合わせ、UIMenuクラスの段階的除去を実施。現在は安定稼働期間として位置づけ。

## 関連ドキュメント
- `docs/todos/0032_window_system_migration_high_priority.md`: 高優先度移行（完了）
- `docs/todos/0033_window_system_migration_medium_priority.md`: 中優先度移行
- `docs/todos/0034_window_system_migration_low_priority.md`: 低優先度移行
- `docs/window_system.md`: WindowSystem設計書

## 注意事項
- 急速な削除は避け、段階的に実施すること
- 各Phase完了後に全体テストを実施すること
- ダンジョンUIの移行は特に慎重に行うこと