# 0043: MenuStackManager役割見直し・段階的移行計画

**ステータス**: 🔄 0044（UIMenu段階的削除計画）に統合

## 目的
WindowManager導入後のアーキテクチャにおけるMenuStackManagerクラスの役割を見直し、機能重複の解消と段階的移行戦略を策定する。

## 2025-06-29更新
**本タスクは0044（UIMenu段階的削除 - 長期計画）に統合されました。**
- MenuStackManagerはUIMenuシステムの一部として、0044の段階的削除計画に含まれます
- 以下の内容は参考資料として保持しますが、実施は0044の計画に従います

## 背景・経緯
- WindowSystemの段階的導入により、MenuStackManagerとWindowManagerの機能重複が発生
- BaseFacility、OverworldManagerでハイブリッド実装が継続中
- レガシーUIMenuシステムのサポート層としての役割が明確化
- 完全なWindowSystem統一化に向けた次のステップとして位置づけ

## 現状分析（2025-06-29調査結果）

### MenuStackManagerの主要使用箇所
1. **BaseFacility**: WindowManagerと併用（ハイブリッド実装）
2. **OverworldManager**: レガシーサポート・フォールバック用途
3. **DialogTemplate**: 密結合による依存関係
4. **AdventurersGuild**: 限定的使用（パーティ編成等）
5. **Shop**: サブメニュー管理での使用

### 機能重複分析

#### 重複している機能
- **ウィンドウスタック管理**: 階層的なUI管理
- **戻る処理**: go_back() vs back_to_previous()
- **ESCキー処理**: 両システムで類似パターン
- **モーダル管理**: ウィンドウ/メニューの表示制御

#### MenuStackManager固有機能
- **MenuType分類**: FACILITY_MAIN, SUBMENU, DIALOG等
- **施設固有戻り処理**: back_to_facility_main()等
- **UIMenuベースサポート**: レガシーシステム互換性
- **DialogTemplate連携**: 既存の密結合

#### WindowManager優位機能
- **統一されたウィンドウ管理**: より抽象化された設計
- **pygame_gui統合**: モダンなUI技術スタック
- **型安全性**: 堅牢な実装パターン
- **将来拡張性**: 新機能追加の柔軟性

## 段階的移行戦略

### Phase 1: 基盤強化（短期: 3-6ヶ月）

#### 目標
- 並行運用の安定化
- WindowManager機能拡張
- 新規開発のWindowManager化

#### 具体的作業
- [ ] WindowManagerにMenuType相当の概念を追加
- [ ] 施設固有戻り処理をWindowManager.window_stackで実現
- [ ] DialogTemplateのWindowManager対応版を作成
- [ ] 新規機能開発ガイドライン策定（WindowManager優先）
- [ ] 両システム対応テストケース作成

#### 完了条件
- WindowManagerがMenuStackManagerの主要機能をカバー
- 新規開発でのWindowManager使用が標準化
- ハイブリッド実装の安定動作確認

### Phase 2: 機能移行（中期: 6-12ヶ月）

#### 目標
- DialogTemplate再設計
- 施設システム統一
- レガシーコード識別

#### 具体的作業
- [ ] DialogTemplateのWindowManagerベース再実装
- [ ] BaseFacilityでのWindowManager優先化強化
- [ ] OverworldManagerの完全WindowManager化
- [ ] UIMenuからpygame_guiへの段階的移行
- [ ] レガシーコードのマーキングと文書化

#### 完了条件
- DialogTemplateがWindowManagerベースで動作
- 全施設でWindowManagerが主要システム
- UIMenuシステムの段階的縮小開始

### Phase 3: レガシー除去（長期: 12ヶ月以降）

#### 目標
- MenuStackManagerの段階的廃止
- 完全WindowManagerアーキテクチャ
- コードベース簡素化

#### 具体的作業
- [ ] MenuStackManager使用箇所の段階的削除
- [ ] UIMenuシステムの完全廃止
- [ ] アーキテクチャの最適化
- [ ] パフォーマンス向上
- [ ] 技術債務の完全解消

#### 完了条件
- MenuStackManagerの完全削除
- 単一WindowSystemによる統一UI
- 保守性・拡張性の大幅向上

## 継続使用の妥当性判断

### ~~現在の方針: **継続使用を推奨**~~ → **0044に統合**

#### 支持要因（参考）
- ✅ 安定した動作実績
- ✅ レガシーコードとの高い互換性
- ✅ 段階的移行におけるリスク軽減
- ✅ DialogTemplateとの密結合による移行コスト

#### 0044での対応方針
- 🔄 UIMenuシステムの一部として段階的削除
- 🔄 Phase 2（中リスク削除）で対応予定
- 🔄 施設システムWindowSystem化の一環として実施
- 🔄 4-8週間の移行期間を想定

## アーキテクチャ移行パターン

### 現在の実装パターン
```python
class BaseFacility:
    def __init__(self):
        # ハイブリッド実装
        self.window_manager = WindowManager.get_instance()  # 新システム
        self.menu_stack_manager = None  # レガシーサポート
    
    def _show_main_menu_unified(self):
        try:
            self._show_main_menu_window_manager()  # WindowManager優先
        except ImportError:
            self._show_main_menu_new()  # MenuStackManagerフォールバック
```

### 目標実装パターン（Phase 3）
```python
class BaseFacility:
    def __init__(self):
        # WindowManager完全統一
        self.window_manager = WindowManager.get_instance()
        # menu_stack_manager削除
    
    def _show_main_menu(self):
        # WindowManagerのみ使用
        self._show_main_menu_window_manager()
```

## リスク・軽減策

### 技術的リスク
- **レガシーコード破綻**: 段階的移行による影響分散
- **DialogTemplate移行失敗**: 事前のプロトタイプ作成
- **パフォーマンス劣化**: プロファイリングと最適化

### スケジュールリスク
- **移行期間延長**: 明確なマイルストーン設定
- **リソース不足**: 優先度管理と段階的実施
- **テスト工数増大**: 自動テストの充実

### 軽減策
- 豊富なテストケース作成
- ロールバック計画の詳細化
- 段階的移行によるリスク分散
- 定期的な進捗評価とアジャスト

## マイルストーン・評価指標

### Phase 1評価指標
- [ ] WindowManagerの機能拡張完了度
- [ ] 新規開発でのWindowManager使用率
- [ ] ハイブリッド実装の安定性

### Phase 2評価指標
- [ ] DialogTemplate移行進捗
- [ ] UIMenuシステム依存度減少
- [ ] 全体アーキテクチャの統一度

### Phase 3評価指標
- [ ] MenuStackManager除去進捗
- [ ] システム統一化完了度
- [ ] パフォーマンス改善効果

## 完了条件（0044で実施）
- [ ] ~~Phase 1: WindowManager機能拡張とハイブリッド実装安定化~~ → 0044 Phase 2で対応
- [ ] ~~Phase 2: DialogTemplate再設計と施設システム統一~~ → 0044 Phase 2で対応
- [ ] ~~Phase 3: MenuStackManager完全除去とアーキテクチャ最適化~~ → 0044 Phase 2で対応
- [ ] 全システムでのWindowManager統一使用
- [ ] レガシーコードの完全除去
- [ ] パフォーマンス劣化なし確認

**注**: 本タスクの完了条件は0044（UIMenu段階的削除計画）のPhase 2として実施されます。

## 期待される効果

### システム統一化
- 単一WindowSystemによる完全統一
- アーキテクチャの一貫性確保
- 機能重複の完全解消

### 保守性向上
- コードベースの簡素化
- 技術債務の解消
- デバッグ・修正作業の効率化

### 拡張性向上
- 新機能追加の容易化
- モジュール間の疎結合化
- 将来技術への適応性向上

## 関連ドキュメント
- `docs/todos/0034_window_system_migration_low_priority.md`: 親タスク
- `docs/todos/0042_management_functions_window_system_integration.md`: 管理機能統合
- `docs/todos/0044_uimenu_phased_removal_long_term.md`: UIMenu段階的削除計画（本タスクの移管先）
- `docs/window_system.md`: WindowSystem設計書

## 作業ログ
- 2025-06-29: 詳細分析レポート作成、現状調査完了
- 2025-06-29: 段階的移行戦略策定、3フェーズ計画確定
- 2025-06-29: 継続使用妥当性判断、条件付き継続を決定
- 2025-06-29: **0044（UIMenu段階的削除計画）に統合**

### 統合の理由
1. **UIMenuシステムの一部**: MenuStackManagerはUIMenuシステムの中間層として機能
2. **削除タイミングの一致**: UIMenu削除時に同時に対応することが効率的
3. **優先度の整合**: 両者とも長期的な技術債務解消として位置づけ
4. **作業効率**: 個別対応より統合的アプローチが効果的

### 0044での扱い
- MenuStackManagerは0044のPhase 2（中リスク削除）で対応予定
- UISelectionListと共にListWindow等への移行を実施
- 施設システムの完全WindowSystem化の一環として処理