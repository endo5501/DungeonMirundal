# 0044: UIMenuクラス段階的削除 - 長期計画

**ステータス**: 📋 計画中（長期技術債務解消）

## 目的
WindowSystem移行完了後の長期計画として、UIMenuクラスの段階的・安全な削除を実施し、レガシーコードの完全除去を実現する。

## 経緯
- 2025-06-29: WindowSystem移行（0032,0033,0034）及び関連クリーンアップ作業が完了
- 主要機能は新WindowSystemに移行済み、UIMenuは限定的な箇所でのみ使用
- 技術債務の完全解消と保守性向上のため、段階的削除を実施

## 現状分析（2025-06-29時点）

### UIMenuクラス使用状況
**調査結果**: 全プロジェクト119箇所での使用を確認
- **本番コード**: 54箇所（6ファイル）
- **テストコード**: 20箇所
- **その他（インポート等）**: 45箇所

#### 削除優先度マトリックス
| カテゴリ | リスク | 削除優先度 | 対象ファイル | 代替実装 |
|---------|--------|-----------|-------------|----------|
| レガシー部分 | 低 | 高 | BaseFacilityレガシー部分 | 既存WindowSystem |
| テストコード | 低 | 高 | 一部テストファイル | MockWindow |
| 施設・地上部 | 中 | 中 | 施設サブメニュー | 専用Window |
| 核心UI | 高 | 低 | inventory_ui, magic_ui等 | 新Window実装必要 |

## 段階的削除計画

### Phase 1: 低リスク削除（期間: 2-4週間）
**目標**: 即座削除可能な箇所の除去

#### 対象箇所
1. **BaseFacilityレガシー部分**
   - `src/overworld/base_facility.py`内の古いUIMenu使用箇所
   - 既にWindowSystem移行済みのため安全に削除可能

2. **テストコード内の使用**
   - 古いテストでのUIMenuモック使用
   - MockWindowまたは新WindowSystemテストに置換

3. **未使用インポート**
   - UIMenuをインポートしているが実際には使用していない箇所
   - 静的解析で検出・除去

#### 作業手順
```bash
# 1. 影響範囲調査
rg "UIMenu" --type py -n

# 2. 段階的削除
# - BaseFacilityレガシー部分
# - 未使用インポート
# - テストコード

# 3. テスト実行・確認
uv run pytest tests/
```

#### 完了条件
- [x] BaseFacilityレガシー部分の削除
- [x] テストコードでのUIMenu使用除去（Phase 3対象を除く）
- [x] 未使用インポートの削除
- [x] 全テストの通過確認

### Phase 2: 中リスク削除（期間: 4-8週間）
**目標**: 施設・地上部システムのUIMenu完全除去

#### 対象箇所
1. **施設サブメニュー**
   - Inn: アイテム・魔法管理サブメニュー（12箇所）
   - Shop: 購入・売却UI（5箇所）
   - MagicGuild: 魔術書購入・鑑定UI（7箇所）
   - Temple: 蘇生・祝福サービスUI（4箇所）

2. **地上部管理システム**
   - UISelectionList → ListWindow統合
   - ダイアログシステムの完全WindowSystem化
   - OverworldManager: メインメニュー・設定（17箇所）

3. **MenuStackManager関連**（0043から統合）
   - MenuStackManagerの役割見直し・削除
   - DialogTemplateのWindowManager対応
   - 施設システムの完全WindowSystem化

#### 必要な新実装
```python
# 新しいWindow実装が必要
class ShopTransactionWindow(Window):
    """商店での購入・売却専用ウィンドウ"""
    pass

class TempleServiceWindow(Window):
    """神殿サービス専用ウィンドウ"""
    pass

class ListWindow(Window):
    """リスト表示専用ウィンドウ（UISelectionList代替）"""
    pass
```

#### 作業手順
1. **新Window実装**
   - TDDアプローチで各専用Windowを実装
   - 既存UIMenuと同等機能の提供

2. **段階的移行**
   - 施設ごとに順次移行
   - 各段階でテスト・動作確認

3. **UISelectionList統合**
   - ListWindow実装
   - 全箇所での使用を新Windowに置換

#### 完了条件
- [ ] 施設サブメニューの新Window実装（28箇所）
- [ ] UISelectionList → ListWindow移行
- [ ] 施設システムでのUIMenu使用除去
- [ ] MenuStackManager削除（0043統合）
- [ ] DialogTemplateのWindowManager対応
- [ ] 統合テストの通過確認

### Phase 3: 高リスク削除（期間: 8-18ヶ月）
**目標**: 核心UIシステムの完全移行とUIMenuクラス削除

#### 対象箇所
1. **核心UIシステム**
   - `src/ui/inventory_ui.py`
   - `src/ui/magic_ui.py`
   - `src/ui/equipment_ui.py`
   - `src/ui/settings_ui.py`

2. **UIMenuクラス本体**
   - `src/ui/base_ui_pygame.py`のUIMenuクラス定義
   - 関連メソッド群

#### 必要な新実装
```python
# 高度な専用Window実装が必要
class InventoryWindow(Window):
    """インベントリ専用ウィンドウ"""
    # 複雑なアイテム管理機能
    pass

class MagicWindow(Window):
    """魔法システム専用ウィンドウ"""
    # スロット管理、詠唱システム等
    pass

class EquipmentWindow(Window):
    """装備管理専用ウィンドウ"""
    # 装備スロット、ステータス表示等
    pass

class SettingsWindow(Window):
    """設定画面専用ウィンドウ"""
    # 各種設定項目の管理
    pass
```

#### 作業手順
1. **設計・プロトタイプ**
   - 各UIシステムの詳細設計
   - プロトタイプ実装・検証

2. **段階的実装**
   - 機能ごとに順次実装
   - 既存システムとの並行稼働

3. **完全移行**
   - 全箇所での使用を新Windowに置換
   - UIMenuクラス削除

4. **最終確認**
   - 全機能の動作確認
   - パフォーマンステスト
   - リグレッションテスト

#### 完了条件
- [ ] 核心UI専用Window実装
- [ ] 全UIMenuクラス使用の除去
- [ ] UIMenuクラス定義の削除
- [ ] 最終統合テストの通過

## 技術仕様

### 削除対象の特定
```bash
# UIMenu使用箇所の特定
rg "UIMenu" --type py -A 3 -B 3

# インポート文の確認
rg "from.*UIMenu|import.*UIMenu" --type py

# 継承関係の確認
rg "class.*UIMenu" --type py
```

### 安全な削除手順
```python
# 1. 削除前の影響調査
def analyze_uimenu_usage():
    """UIMenu使用箇所の詳細分析"""
    # 静的解析・依存関係マップ作成
    pass

# 2. 段階的削除
def phased_removal():
    """段階的・安全な削除実施"""
    # Phase毎の削除・テスト・確認
    pass

# 3. 削除後の検証
def verify_removal():
    """削除後の動作検証"""
    # 全機能テスト・パフォーマンス確認
    pass
```

### 代替実装パターン
```python
# UIMenu → Window移行パターン
# 変更前
class OldInventoryUI(UIMenu):
    def __init__(self):
        super().__init__("inventory", "インベントリ")
        
# 変更後
class InventoryWindow(Window):
    def __init__(self, window_id: str):
        super().__init__(window_id)
        self.window_type = "inventory"
```

## リスク管理

### 技術的リスク
1. **機能劣化のリスク**
   - 新Window実装での機能不足
   - ユーザビリティの低下

2. **パフォーマンスリスク**
   - 新実装でのパフォーマンス劣化
   - メモリ使用量の増加

3. **互換性リスク**
   - セーブデータ互換性の問題
   - 設定ファイルとの不整合

### 軽減策
1. **段階的実装**
   - Phase毎の詳細検証
   - 問題発生時の迅速なロールバック

2. **並行稼働期間**
   - 新旧システムの並行稼働
   - 十分な検証期間の確保

3. **豊富なテスト**
   - 単体・統合・リグレッションテスト
   - パフォーマンステストの実施

## スケジュール

### 全体スケジュール（6-18ヶ月）
- **Phase 1**: 2-4週間（低リスク削除）
- **Phase 2**: 4-8週間（中リスク削除）※0043統合により若干延長
- **Phase 3**: 8-18ヶ月（高リスク削除）

### マイルストーン
- **1ヶ月後**: Phase 1完了（低リスク箇所のクリーンアップ）
- **3ヶ月後**: Phase 2完了（施設・MenuStackManager統合）
- **18ヶ月後**: Phase 3完了・UIMenu完全除去

### 優先度と実施タイミング
- **緊急性**: 低（システムは現在安定稼働中）
- **重要性**: 高（長期的な保守性・拡張性に直結）
- **推奨開始時期**: 他の重要タスク完了後、計画的に実施

## 期待される効果

### 技術的効果
- **コード削減**: UIMenuクラス及び関連コード（約2000行以上）の削除
  - UIMenu本体とUIDialog
  - MenuStackManager関連
  - 各施設のレガシー実装
- **保守性向上**: 単一WindowSystemによる統一アーキテクチャ
- **拡張性向上**: 新機能追加の効率化

### 品質効果
- **バグ削減**: レガシーコード除去による潜在バグの解消
- **テスト効率**: 統一されたテストフレームワーク
- **ドキュメント整合性**: アーキテクチャドキュメントの一貫性

### 統合効果（0043統合による追加効果）
- **機能重複解消**: MenuStackManagerとWindowManagerの重複除去
- **アーキテクチャ簡素化**: 中間層の削除による構造簡潔化
- **学習コスト削減**: 単一システムによる理解容易性向上

## 完了条件

### 最終完了条件
- [ ] 全PhaseのUIMenu削除完了
- [ ] UIMenuクラス定義の完全削除
- [ ] 新WindowSystemでの全機能動作確認
- [ ] パフォーマンス劣化なしの確認
- [ ] 全テストスイートの通過
- [ ] ドキュメント更新完了

### 品質基準
- **機能性**: 既存機能の100%互換性
- **パフォーマンス**: 既存レベル以上の維持
- **保守性**: コード複雑度の大幅改善
- **拡張性**: 新機能追加効率の向上

## 作業ログ
- 2025-06-29: 詳細計画策定、現状分析完了（119箇所の使用確認）
- 2025-06-29: 0043（MenuStackManager役割見直し）を本計画に統合
- 2025-06-29: **Phase 1完了** - BaseFacilityレガシー部分削除、テストコードクリーンアップ、未使用インポート除去

## 統合されたタスク
### 0043: MenuStackManager役割見直し
- **統合理由**: MenuStackManagerはUIMenuシステムの一部として機能
- **対応Phase**: Phase 2（中リスク削除）で対応
- **削除タイミング**: 施設システムのWindowSystem化と同時実施

## 関連ドキュメント
- `docs/todos/0034_window_system_migration_low_priority.md`: 移行作業完了記録
- `docs/todos/0042_management_functions_window_system_integration.md`: 管理機能統合（Phase 4移管元）
- `docs/todos/0043_menu_stack_manager_role_review.md`: MenuStackManager見直し（本計画に統合）
- `docs/window_system.md`: WindowSystem設計書
- `docs/todos/0045_core_ui_window_implementation.md`: 核心UI新実装
- `docs/todos/0046_final_integration_testing.md`: 最終統合テスト