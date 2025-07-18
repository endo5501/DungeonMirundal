# 0093_update_facilities.md - 施設UI統合リファクタリング計画

## 概要

施設UI機能の統合的リファクタリングを実施。過去何度も発生していたパネル破棄処理の不具合を根本的に解決するため、統一されたUI管理システムを導入する。

## 背景

### 発生していた問題
- 画面切替時のパネル破棄処理で頻発する不具合
- 3つの異なる破棄パターンが混在（基本・強化・最高度）
- メモリリークの可能性
- UI階層の複雑性によるデバッグ困難

### 根本原因
- 統一されたUI管理システムの欠如
- 破棄処理の不統一性
- 例外安全性の不足
- デバッグ情報の不足

## 実装済み項目 ✅

### 1. UIElementManager システムの導入
**ファイル**: `src/facilities/ui/ui_element_manager.py`

**機能**:
- 統一されたUI要素管理システム
- 型安全な要素作成メソッド
- グループ管理と階層的破棄機能
- コンテキストマネージャーによる自動管理
- 破棄検証機能

**主要メソッド**:
- `create_label()`, `create_button()`, `create_selection_list()` など
- `destroy_all()` - 例外安全な完全破棄
- `add_to_group()`, `destroy_group()` - グループ管理
- `get_debug_info()` - デバッグ情報取得

### 2. 統一破棄処理システムの実装
**ファイル**: `src/facilities/ui/service_panel.py`

**改善点**:
- `DestructionMixin`による検証付き破棄処理
- `ServicePanel`基底クラスの強化
- UIElementManagerとの統合
- 後方互換性を保ちながらの段階的移行

**新しい破棄フロー**:
```python
def destroy(self) -> None:
    # 1. UIElementManagerによる統一破棄
    self.ui_element_manager.destroy_all()
    
    # 2. 後方互換性のためのlegacy破棄
    for element in self.ui_elements:
        element.kill()
    
    # 3. コンテナとリファレンスのクリア
    self.container.kill()
    self.container = None
```

### 3. デバッグ機能の大幅強化
**ファイル**: `src/core/dbg_api.py`

**新しいAPIエンドポイント**:
- `/debug/facility-ui` - 施設UI専用の詳細分析
- `/debug/ui-snapshot` - UI状態のスナップショット作成

**提供される診断情報**:
- 施設ウィンドウの状態
- サービスパネルの状態
- ナビゲーションパネルの状態
- 破棄処理の完全性診断
- メモリリーク検出

### 4. BuyPanelの完全移行
**ファイル**: `src/facilities/ui/shop/buy_panel.py`

**移行内容**:
- 新しいUIElementManagerを使用するように完全移行
- `_create_label()`, `_create_button()` などの新メソッドを使用
- 従来の`ui_elements`リストと新システムの併用
- フォールバック機能による安全性確保

## 今後の実装計画 📋

### Phase 1: 主要パネルの移行（高優先度）
**期間**: 2-3週間

**対象ファイル**:
- `src/facilities/ui/shop/sell_panel.py`
- `src/facilities/ui/shop/identify_panel.py`
- `src/facilities/ui/inn/storage_panel.py`
- `src/facilities/ui/inn/item_management_panel.py`

**作業内容**:
1. 各パネルでUIElementManagerを使用するように移行
2. 新しい`_create_*`メソッドを使用
3. 破棄処理の統一化
4. テストの更新

### Phase 2: 複雑なパネルの移行（中優先度）
**期間**: 3-4週間

**対象ファイル**:
- `src/facilities/ui/guild/character_list_panel.py`
- `src/facilities/ui/guild/party_formation_panel.py`
- `src/facilities/ui/guild/character_creation_wizard.py`
- `src/facilities/ui/inn/adventure_prep_panel.py`

**作業内容**:
1. 複雑なUI構造の分析
2. 共通UIパターンの抽出
3. 段階的な移行
4. 統合テストの強化

### Phase 3: Temple系の標準化（中優先度）
**期間**: 2週間

**対象ファイル**:
- `src/facilities/ui/temple/blessing_panel.py`
- `src/facilities/ui/temple/resurrect_panel.py`
- `src/facilities/ui/temple/prayer_shop_panel.py`

**作業内容**:
1. ServicePanel継承への移行
2. 統一されたUI作成・破棄パターンの適用
3. 設計の一貫性確保

### Phase 4: 共通UIパターンの抽出（低優先度）
**期間**: 4-5週間

**新しいクラス**:
- `ListDetailPanel` - 左側リスト＋右側詳細の標準パターン
- `DualListPanel` - 双方向リスト管理の標準パターン
- `FormPanel` - フォーム形式の入力パターン

**作業内容**:
1. 共通パターンの抽象化
2. 基底クラスの作成
3. 既存パネルの移行
4. コード重複の削減

## 技術的詳細

### UIElementManager の設計思想
```python
# 統一されたUI要素管理
manager = UIElementManager(ui_manager, container)

# 型安全な要素作成
button = manager.create_button("save_btn", "保存", rect)
label = manager.create_label("title", "タイトル", rect)

# グループ管理
with manager.element_group("form_controls"):
    # このブロック内で作成された要素は自動的にグループに追加
    input_field = manager.create_text_entry("input", rect)
    submit_btn = manager.create_button("submit", "送信", rect)

# 安全な破棄
manager.destroy_group("form_controls")  # グループ単位での破棄
manager.destroy_all()  # 完全破棄
```

### デバッグ情報の活用
```python
# 施設UI専用の診断
debug_info = requests.get("http://localhost:8765/debug/facility-ui").json()

# パネル破棄状況の確認
destruction_status = debug_info["destruction_analysis"]
if destruction_status["destruction_completeness"] == "poor":
    print("破棄処理に問題があります")

# メモリリークの検出
memory_issues = debug_info["ui_memory_issues"]
for issue in memory_issues:
    if issue["type"] == "excessive_elements":
        print(f"要素数が異常: {issue['element_type']} x{issue['count']}")
```

### 段階的移行の戦略
1. **新システムの導入**: UIElementManagerを各パネルに統合
2. **後方互換性の確保**: 既存の`ui_elements`リストも並行して管理
3. **フォールバック機能**: 新システムが失敗した場合の従来方式への切り替え
4. **段階的テスト**: 各パネルの移行完了時に個別テスト
5. **統合テスト**: 全体の整合性確認

## 期待される効果

### 短期的効果（1-2ヶ月）
- パネル破棄処理の不具合根絶
- メモリリークの大幅削減
- デバッグ効率の向上
- 開発者の生産性向上

### 中期的効果（3-6ヶ月）
- コード重複の30-40%削減
- 新しいパネル作成時間の50%短縮
- バグ発生率の大幅減少
- 保守性の向上

### 長期的効果（6ヶ月以上）
- 施設UI全体の設計一貫性
- 新機能追加の容易さ
- システム全体の安定性向上
- 技術的負債の大幅削減

## リスク管理

### 技術的リスク
- **既存機能の破損**: 段階的移行と十分なテストで対処
- **パフォーマンスの劣化**: プロファイリングツールによる監視
- **複雑性の増加**: 明確な設計文書と教育で対処

### プロジェクトリスク
- **作業量の増加**: 優先度を明確にして段階的に実施
- **スケジュールの遅延**: 重要度に応じた調整
- **品質の低下**: 継続的なテストと検証

## 成功指標

### 定量的指標
- パネル破棄処理の例外発生数: 0件/月
- メモリリーク検出件数: 80%削減
- コード重複率: 30-40%削減
- 新パネル作成時間: 50%短縮

### 定性的指標
- 開発者の満足度向上
- バグ報告の質的改善
- コードレビューの効率化
- 新規開発者の学習コスト削減

## 関連文書

- [フォントシステムガイド](../font_system_guide.md)
- [ゲームデバッグガイド](../how_to_debug_game.md)
- [pygame_gui統合ガイド](../pygame_gui_font_integration.md)

## 変更履歴

- 2025-07-19: 初版作成
- 2025-07-19: Phase 1完了（UIElementManager導入、ServicePanel強化、BuyPanel移行）

---

**担当者**: Claude Code  
**作成日**: 2025-07-19  
**最終更新**: 2025-07-19  
**ステータス**: Phase 1完了、継続中