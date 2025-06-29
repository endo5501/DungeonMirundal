# 0041: 施設残存UIMenuクリーンアップ作業

## 目的
施設のFacilityMenuWindow移行後に残存するUIMenu使用箇所を完全に除去し、新WindowSystemへの統一化を完了する。

## 背景・経緯
- 0034でWindowSystem低優先度移行の一環として施設のFacilityMenuWindow移行を実施
- Guild移行は完了、Inn移行は基本構造完了
- しかし各施設内のサブメニューや詳細機能でUIMenuが残存している状況
- 完全な新システム統一化には、これらの残存箇所の対応が必要

## 対象ファイルと残存UIMenu箇所

### 1. src/overworld/facilities/inn.py
**現状**: 基本メニューはFacilityMenuWindow移行済み、サブ機能でUIMenu残存

**残存箇所**:
- `_show_adventure_preparation()` 内のサブメニュー群
- `_show_item_organization()` 内のアイテム管理UI
- `_show_spell_equip_menu()` 系のスペル装備メニュー
- `_show_character_spell_slot_detail()` 系のスペル詳細メニュー
- その他のサブダイアログやセレクションリスト

**影響範囲**: 中～高（アイテム・魔法管理機能）

### 2. src/overworld/facilities/shop.py
**現状**: 未移行（UIMenuベース）

**予想される残存箇所**:
- メインメニューの完全移行
- 購入・売却UI
- アイテム一覧表示
- UISelectionListとの統合

**影響範囲**: 高（商店機能全般）

### 3. src/overworld/facilities/magic_guild.py
**現状**: 未移行（UIMenuベース）

**予想される残存箇所**:
- メインメニューの完全移行
- 魔術書購入UI
- アイテム鑑定機能
- 魔法分析機能

**影響範囲**: 高（魔術師ギルド機能全般）

### 4. src/overworld/facilities/temple.py
**現状**: 未移行（UIMenuベース）

**予想される残存箇所**:
- メインメニューの完全移行
- 蘇生サービスUI
- 祝福サービスUI
- 祈祷書購入機能

**影響範囲**: 高（教会機能全般）

### 5. src/overworld/facilities/guild.py
**現状**: 基本移行完了、一部レガシー処理残存の可能性

**確認事項**:
- キャラクター作成ウィザード統合
- パーティ編成の完全WindowSystem化
- menu_stack_manager依存の除去

**影響範囲**: 低～中（基本移行済み）

## 技術的課題

### UISelectionListとの統合
- 多くの施設でUISelectionListを使用してアイテム・魔法一覧を表示
- 新WindowSystemでのリスト表示方法への置換が必要
- ListWindowやカスタムウィンドウコンポーネントの活用検討

### 複雑なサブメニュー階層
- 特にInnのアイテム・魔法管理は深い階層構造
- WindowStackによる適切な階層管理への変更が必要

### ダイアログシステムの統合
- UIDialog, UIInputDialogからDialogWindowへの移行
- 入力フォーム（パーティ名変更等）のFormWindowへの移行

### 状態管理の統一化
- 各施設固有の状態管理をWindowManagerベースに統一
- レガシーなメニューシステム（menu_stack_manager）からの完全脱却

## 実装方針

### Phase 1: 基本メニュー移行完了
- [ ] Shop基本メニューFacilityMenuWindow移行
- [ ] MagicGuild基本メニューFacilityMenuWindow移行  
- [ ] Temple基本メニューFacilityMenuWindow移行
- [ ] 各施設のhandle_facility_message実装

### Phase 2: サブ機能WindowSystem化
- [ ] Inn残存UIMenuのWindowSystem移行
- [ ] Shop購入・売却UIのWindowSystem移行
- [ ] MagicGuild機能UIのWindowSystem移行
- [ ] Temple機能UIのWindowSystem移行

### Phase 3: 統合・クリーンアップ
- [ ] UISelectionList使用箇所のListWindow化
- [ ] UIDialog/UIInputDialog使用箇所のDialogWindow/FormWindow化
- [ ] menu_stack_manager依存の完全除去
- [ ] レガシーUI要素のインポート削除

## 優先度

### 高優先度
1. **Shop, MagicGuild, Temple基本メニュー移行**
   - ユーザー体験への直接的影響
   - システム統一性の確保

### 中優先度  
2. **Inn残存UIMenu対応**
   - アイテム・魔法管理機能の重要性
   - 複雑なサブメニュー階層の整理

### 低優先度
3. **詳細UI要素の統一化**
   - UISelectionList等の細かい要素
   - より高度なUIコンポーネントへの移行

## 期待される効果

### システム統一化
- 全施設でのFacilityMenuWindow統一使用
- WindowManagerによる一貫したウィンドウ管理
- UIMenuシステムの完全除去

### 保守性向上
- 単一UIシステムによる開発効率向上
- デバッグ・修正作業の簡素化
- 新機能追加の容易化

### パフォーマンス向上
- レガシーシステム除去による軽量化
- メモリ使用量の最適化
- UI応答性の向上

## リスク・制約事項

### 技術的リスク
- 複雑なサブメニュー移行での機能損失
- UISelectionListとの統合困難
- 既存セーブデータとの互換性問題

### スケジュールリスク
- 各施設での詳細テストが必要
- 機能回帰テストの工数増大
- ユーザー受け入れテストの必要性

### 軽減策
- 段階的移行による影響分散
- 豊富なテストケース作成
- ロールバック計画の準備

## 完了条件
- [ ] 全施設でUIMenu使用箇所の完全除去
- [ ] FacilityMenuWindow統一使用の確認
- [ ] UISelectionList等レガシーUI要素の新システム統合
- [ ] 全施設機能の動作確認完了
- [ ] レグレッションテスト通過
- [ ] パフォーマンス劣化なし確認

## 関連ドキュメント
- `docs/todos/0034_window_system_migration_low_priority.md`: 親タスク
- `docs/todos/0032_window_system_migration_high_priority.md`: 高優先度移行
- `docs/todos/0033_window_system_migration_medium_priority.md`: 中優先度移行
- `docs/window_system.md`: WindowSystem設計書

## 作業ログ
- 2025-06-29: Guild基本移行完了、Inn基本移行完了、残存UIMenu課題特定
- TODO: Shop, MagicGuild, Temple基本移行
- TODO: 各施設サブ機能の詳細移行計画策定