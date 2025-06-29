# 0033: WindowSystem移行 - 中優先度作業

## 目的
高優先度移行完了後、UI機能関連ファイルをUIMenuから新WindowSystemへ移行し、システムの統一化を進める。

## 経緯
- 高優先度移行（0032）完了後の次段階作業
- UIコアコンポーネントの新WindowSystem統一化
- フォーカス管理問題の根本的解決に向けた段階的アプローチ

## 対象ファイル（中優先度）

### 1. src/ui/equipment_ui.py → EquipmentWindow
**現状**: UIMenuベースの装備システム
**移行先**: `src/ui/windows/equipment_window.py`

**移行作業**:
- 既存`EquipmentWindow`クラスの活用
- `EquipmentManager`, `EquipmentUIFactory`, `EquipmentValidator`の統合
- t-wada式TDDで開発
- 装備スロット管理、ステータス比較、クイック装備機能の移行
- キーボードナビゲーション対応
- Fowler式リファクタリングを実施

### 2. src/ui/inventory_ui.py → InventoryWindow  
**現状**: UIMenuベースのインベントリシステム
**移行先**: `src/ui/windows/inventory_window.py`

**移行作業**:
- 既存`InventoryWindow`クラスの活用
- `InventoryManager`, `InventoryUIFactory`, `InventoryValidator`の統合
- t-wada式TDDで開発
- アイテムグリッド表示、ドラッグ&ドロップ、重量管理機能の移行
- フィルタリング・ソート機能の統合
- Fowler式リファクタリングを実施

### 3. src/ui/dungeon_ui_pygame.py → BattleUIWindow
**現状**: UIMenuベースの戦闘UI
**移行先**: `src/ui/windows/battle_ui_window.py`

**移行作業**:
- 既存`BattleUIWindow`クラスの活用  
- `BattleUIManager`, `BattleUIFactory`, `BattleValidator`の統合
- t-wada式TDDで開発
- ターン制戦闘UI、アクション選択、ターゲット選択機能の移行
- 戦闘ログ表示機能の統合
- Fowler式リファクタリングを実施

### 4. src/ui/character_creation.py → CharacterCreationWizard
**現状**: UIMenuベースのキャラクター作成
**移行先**: `src/ui/windows/character_creation_wizard.py`

**移行作業**:
- 既存`CharacterCreationWizard`クラスの活用
- `WizardStepManager`, `CharacterBuilder`, `CharacterValidator`の統合
- t-wada式TDDで開発
- 5段階ウィザード、種族・職業選択、能力値生成機能の移行
- Fowler式リファクタリングを実施

## 技術仕様

### 移行パターン（共通）
```python
# 変更前（UIMenu）
class SomeUI:
    def __init__(self):
        self.menu = UIMenu("menu_id", "タイトル")
        self.menu.add_element(...)
    
    def show(self):
        # UIMenu表示ロジック
        pass

# 変更後（WindowSystem）  
class SomeManager:
    def __init__(self):
        self.window_manager = WindowManager.instance
    
    def show_window(self):
        window = self.window_manager.create_window(
            SomeWindow,
            window_id="menu_id", 
            title="タイトル"
        )
        self.window_manager.show_window(window)
```

### 特殊考慮事項

#### Equipment UI
- 装備スロットの視覚的表現
- ステータス変化の即時反映
- 装備可能判定の統合

#### Inventory UI  
- アイテムの動的表示
- 重量制限の視覚化
- カテゴリフィルタリング

#### Battle UI
- リアルタイム戦闘状況表示
- ターン管理との連携
- アクション入力の確実性

#### Character Creation
- ウィザード形式の段階管理
- データ検証の各段階実装
- 戻り処理の安全性

## 依存関係・影響範囲

### 上流依存
- WindowManager, FocusManagerの安定動作
- 高優先度移行（0032）の完了

### 下流影響
- 戦闘システムとの連携
- パーティ管理システムとの統合
- セーブ・ロードシステムとの整合性

### 横断的影響
- テストケースの大幅修正
- 設定データ形式の統一
- エラーハンドリングの一元化

## テスト要件

### 単体テスト
- 各Windowクラスの個別機能テスト
- データ検証ロジックのテスト
- UI要素の表示・非表示テスト

### 統合テスト
- Window間の連携テスト
- フォーカス管理の整合性テスト
- メモリリーク検証

### シナリオテスト
- 実際のゲームプレイ流れでの動作確認
- 長時間プレイでの安定性確認
- エラー発生時の復旧確認

## リスク・制約事項

### 技術的リスク
- 戦闘システムへの影響
- 既存セーブデータとの互換性
- パフォーマンス劣化の可能性

### 業務リスク
- 移行期間中の機能制限
- テスト工数の増大
- バグ修正の複雑化

### 軽減策
- 段階的移行による影響局所化
- 機能別の独立テスト実施
- ~~ロールバック手順の明確化~~ ロールバックについては考慮不要

## 作業スケジュール
- **期間**: 2週間以内
- **順序**: equipment_ui → inventory_ui → character_creation → dungeon_ui_pygame  
- **マイルストーン**:
  - 1週目: equipment_ui, inventory_ui移行
  - 2週目: character_creation, dungeon_ui_pygame移行
- **テスト**: 各2ファイル移行毎に統合テスト実施

## 完了条件
- [ ] ❌ equipment_ui.pyの完全移行（未実施）
- [ ] ❌ inventory_ui.pyの完全移行（未実施）
- [ ] ❌ character_creation.pyの完全移行（未実施）  
- [ ] ❌ dungeon_ui_pygame.pyの完全移行（未実施）
- [ ] ❌ 移行後の統合テスト通過（未実施）
- [ ] ❌ 戦闘システムとの連携確認（未実施）
- [ ] ❌ パフォーマンス劣化なし確認（未実施）
- [ ] ❌ レガシーコード削除（未実施）

## 現在の状況（2025-06-29確認）

### 移行状況の詳細調査結果
全ての対象ファイルが**旧UIMenuシステムのまま**で、新WindowSystemへの移行が**全く実施されていない**状況です。

#### 1. src/ui/equipment_ui.py
- **移行率**: 0% - 未実施
- **現状**: 完全に旧UIMenu形式（UIMenu, UIDialog, ui_manager使用）
- **必要作業**: EquipmentWindowクラスへの完全書き換え
- **複雑度**: ★★★★☆（多数のメニュー階層とダイアログ）

#### 2. src/ui/inventory_ui.py  
- **移行率**: 0% - 未実施
- **現状**: 完全に旧UIMenu形式（UIMenu, UIDialog, ui_manager使用）
- **必要作業**: InventoryWindowクラスへの完全書き換え
- **複雑度**: ★★★★☆（アイテム管理と転送機能）

#### 3. src/ui/dungeon_ui_pygame.py
- **移行率**: 15% - 部分的実装
- **現状**: Pygame用に書き換え済みだが旧UIMenu使用（UIElement, UIButton等）
- **必要作業**: BattleUIWindowクラスへの移行
- **複雑度**: ★★★☆☆（単純なメニューだが描画処理あり）

#### 4. src/ui/character_creation.py
- **移行率**: 0% - 未実施  
- **現状**: 完全に旧UIMenu/UIDialog形式（ウィザード実装）
- **必要作業**: CharacterCreationWizardクラスへの完全書き換え
- **複雑度**: ★★★★★（ウィザード形式で複数ステップ）

### 推奨移行順序
1. **dungeon_ui_pygame.py** - 比較的シンプル、先行移行推奨
2. **equipment_ui.py** - 装備管理機能
3. **inventory_ui.py** - アイテム管理機能  
4. **character_creation.py** - 最複雑、最後に実施

### 作業状況
**0033中優先度移行は未着手の状態です。**高優先度移行（0032）完了後に実施予定。

## 関連ドキュメント
- `docs/todos/0031_change_window_system.md`: 調査結果
- `docs/todos/0032_window_system_migration_high_priority.md`: 高優先度移行
- `docs/todos/0034_window_system_migration_low_priority.md`: 低優先度移行  
- `docs/window_system.md`: WindowSystem設計書