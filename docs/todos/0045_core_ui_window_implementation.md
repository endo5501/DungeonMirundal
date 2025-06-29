# 0045: 核心UIシステム新Window実装

## 目的
UIMenu依存の核心UIシステム（インベントリ、魔法、装備、設定）を新WindowSystemベースに完全移行し、高度なUI機能を提供する。

## 経緯
- WindowSystem移行完了後、核心UIシステムが唯一のUIMenu残存箇所
- 複雑な機能要件のため専用Window実装が必要
- ユーザエクスペリエンス向上と保守性確保を両立

## 対象システム

### 1. InventoryWindow - インベントリ管理
**現状**: `src/ui/inventory_ui.py` (UIMenuベース)
**目標**: 高度なアイテム管理専用Window

#### 機能要件
```python
class InventoryWindow(Window):
    """インベントリ専用ウィンドウ"""
    
    # 基本機能
    - アイテム一覧表示（カテゴリ別フィルタ）
    - アイテム詳細情報表示
    - アイテム使用・装備・破棄
    - ソート機能（名前、種類、価値）
    
    # 高度機能
    - ドラッグ&ドロップによるアイテム移動
    - 複数選択・一括操作
    - 検索・フィルタリング
    - アイテムツールチップ表示
    
    # UI要素
    - グリッドレイアウトでのアイテム表示
    - カテゴリタブ（武器、防具、消耗品等）
    - アイテム詳細パネル
    - 操作ボタン（使用、装備、破棄等）
```

#### 技術仕様
```python
@dataclass
class InventoryConfig:
    """インベントリ設定"""
    grid_size: Tuple[int, int] = (8, 6)  # 8x6グリッド
    item_slot_size: Tuple[int, int] = (64, 64)
    categories: List[str] = field(default_factory=lambda: [
        'weapons', 'armor', 'consumables', 'materials', 'quest'
    ])
    sort_options: List[str] = field(default_factory=lambda: [
        'name', 'type', 'value', 'quantity'
    ])

class InventoryWindow(Window):
    def __init__(self, window_id: str, inventory_config: InventoryConfig):
        super().__init__(window_id)
        self.config = inventory_config
        self.current_category = 'all'
        self.sort_mode = 'name'
        self.selected_items: Set[Item] = set()
```

### 2. MagicWindow - 魔法システム
**現状**: `src/ui/magic_ui.py` (UIMenuベース)
**目標**: 高度な魔法管理専用Window

#### 機能要件
```python
class MagicWindow(Window):
    """魔法システム専用ウィンドウ"""
    
    # 基本機能
    - 習得魔法一覧表示
    - 魔法スロット管理（装備・解除）
    - 魔法詳細情報（効果、消費MP等）
    - 魔法レベル・熟練度表示
    
    # 高度機能
    - スロット別魔法設定（戦闘・探索・回復）
    - 魔法組み合わせプリセット
    - 詠唱シミュレーション
    - 魔法効果プレビュー
    
    # UI要素
    - 魔法スクールタブ（攻撃、回復、補助等）
    - スロット管理パネル
    - 魔法詳細・効果説明パネル
    - プリセット管理パネル
```

#### 技術仕様
```python
@dataclass
class MagicConfig:
    """魔法システム設定"""
    max_slots: int = 10
    schools: List[str] = field(default_factory=lambda: [
        'offensive', 'healing', 'support', 'utility'
    ])
    preset_slots: int = 5

class MagicWindow(Window):
    def __init__(self, window_id: str, magic_config: MagicConfig):
        super().__init__(window_id)
        self.config = magic_config
        self.equipped_spells: Dict[int, Spell] = {}
        self.spell_presets: Dict[str, Dict[int, Spell]] = {}
```

### 3. EquipmentWindow - 装備管理
**現状**: `src/ui/equipment_ui.py` (UIMenuベース)
**目標**: 高度な装備管理専用Window

#### 機能要件
```python
class EquipmentWindow(Window):
    """装備管理専用ウィンドウ"""
    
    # 基本機能
    - キャラクター装備スロット表示
    - 装備可能アイテム一覧
    - 装備・解除操作
    - ステータス変化プレビュー
    
    # 高度機能
    - 装備セット管理（プリセット保存・切替）
    - 装備比較機能
    - 最適装備提案
    - 耐久度管理・修理
    
    # UI要素
    - キャラクターモデル表示
    - 装備スロット（頭、胴、腕、足等）
    - ステータス表示パネル
    - 装備候補リスト
```

#### 技術仕様
```python
@dataclass
class EquipmentConfig:
    """装備管理設定"""
    slots: List[str] = field(default_factory=lambda: [
        'head', 'body', 'arms', 'legs', 'feet',
        'main_hand', 'off_hand', 'accessory1', 'accessory2'
    ])
    preset_count: int = 5

class EquipmentWindow(Window):
    def __init__(self, window_id: str, equipment_config: EquipmentConfig):
        super().__init__(window_id)
        self.config = equipment_config
        self.equipped_items: Dict[str, Item] = {}
        self.equipment_sets: Dict[str, Dict[str, Item]] = {}
```

### 4. SettingsWindow - 設定画面
**現状**: `src/ui/settings_ui.py` (UIMenuベース)
**目標**: 高度な設定管理専用Window

#### 機能要件
```python
class SettingsWindow(Window):
    """設定画面専用ウィンドウ"""
    
    # 基本機能
    - ゲーム設定項目表示・変更
    - 設定カテゴリ管理
    - 設定値の即時プレビュー
    - 設定保存・読み込み
    
    # 高度機能
    - 設定プロファイル管理
    - 詳細設定・上級者向け設定
    - 設定のインポート・エクスポート
    - リアルタイム設定変更反映
    
    # UI要素
    - カテゴリタブ（グラフィック、サウンド、操作等）
    - 設定項目リスト
    - プレビューパネル
    - 保存・リセットボタン
```

#### 技術仕様
```python
@dataclass
class SettingsConfig:
    """設定画面設定"""
    categories: List[str] = field(default_factory=lambda: [
        'graphics', 'audio', 'controls', 'gameplay', 'advanced'
    ])
    profile_count: int = 3

class SettingsWindow(Window):
    def __init__(self, window_id: str, settings_config: SettingsConfig):
        super().__init__(window_id)
        self.config = settings_config
        self.current_settings: Dict[str, Any] = {}
        self.settings_profiles: Dict[str, Dict[str, Any]] = {}
```

## 実装アプローチ

### Phase 1: 基盤実装（4-6週間）
1. **共通基盤クラス実装**
   ```python
   class AdvancedWindow(Window):
       """高度なUI機能を持つWindow基底クラス"""
       
       def __init__(self, window_id: str):
           super().__init__(window_id)
           self.layout_manager = GridLayoutManager()
           self.drag_drop_manager = DragDropManager()
           self.tooltip_manager = TooltipManager()
   ```

2. **レイアウト管理システム**
   ```python
   class GridLayoutManager:
       """グリッドレイアウト管理"""
       def arrange_items(self, items: List[Any], grid_size: Tuple[int, int]) -> Dict[Tuple[int, int], Any]:
           pass
   
   class DragDropManager:
       """ドラッグ&ドロップ管理"""
       def handle_drag_start(self, item: Any, position: Tuple[int, int]) -> None:
           pass
   ```

3. **共通UI要素**
   ```python
   class TabPanel(UIComponent):
       """タブパネル実装"""
       pass
   
   class FilterPanel(UIComponent):
       """フィルタ・検索パネル実装"""
       pass
   
   class DetailPanel(UIComponent):
       """詳細情報パネル実装"""
       pass
   ```

### Phase 2: 個別Window実装（8-12週間）
1. **優先順位での実装**
   - InventoryWindow（最重要）
   - EquipmentWindow（重要）
   - MagicWindow（重要）
   - SettingsWindow（中重要）

2. **TDDアプローチ**
   ```python
   # 各WindowのTDDテスト例
   class TestInventoryWindow:
       def test_inventory_window_displays_items_in_grid(self):
           # Given: アイテムを持つインベントリ
           # When: InventoryWindowを表示
           # Then: グリッド形式で表示される
           pass
   ```

### Phase 3: 統合・最適化（4-6週間）
1. **既存UIMenuとの並行稼働**
2. **段階的移行**
3. **パフォーマンス最適化**
4. **最終テスト・品質確認**

## 技術的挑戦

### 複雑なUI要件
1. **ドラッグ&ドロップ実装**
   ```python
   class DragDropHandler:
       def handle_mouse_drag(self, event: pygame.Event) -> bool:
           # pygame_guiでのドラッグ&ドロップ実装
           pass
   ```

2. **リアルタイム更新**
   ```python
   class RealtimeUpdater:
       def register_update_callback(self, callback: Callable) -> None:
           # リアルタイム設定変更の実装
           pass
   ```

3. **高度なレイアウト**
   ```python
   class AdvancedLayout:
       def calculate_responsive_layout(self, window_size: Tuple[int, int]) -> LayoutConfig:
           # レスポンシブレイアウトの実装
           pass
   ```

### パフォーマンス要件
1. **大量アイテム処理**
   - 仮想化スクロール実装
   - 遅延読み込み対応

2. **スムーズなアニメーション**
   - 60FPS維持
   - GPU加速活用

## テスト戦略

### 単体テスト
```python
class TestInventoryWindow:
    """InventoryWindow単体テスト"""
    
    def test_item_grid_layout(self):
        """グリッドレイアウトテスト"""
        pass
    
    def test_drag_drop_functionality(self):
        """ドラッグ&ドロップテスト"""
        pass
    
    def test_filtering_and_sorting(self):
        """フィルタ・ソートテスト"""
        pass
```

### 統合テスト
```python
class TestCoreUIIntegration:
    """核心UI統合テスト"""
    
    def test_inventory_equipment_integration(self):
        """インベントリ・装備連携テスト"""
        pass
    
    def test_magic_equipment_integration(self):
        """魔法・装備連携テスト"""
        pass
```

### パフォーマンステスト
```python
class TestCoreUIPerformance:
    """核心UIパフォーマンステスト"""
    
    def test_large_inventory_performance(self):
        """大量アイテム処理性能テスト"""
        pass
    
    def test_animation_frame_rate(self):
        """アニメーション性能テスト"""
        pass
```

## 完了条件

### 機能完了条件
- [ ] 4つの核心UI Window実装完了
- [ ] 既存UIMenuと同等以上の機能提供
- [ ] ドラッグ&ドロップ等の高度機能実装
- [ ] リアルタイム更新機能実装

### 品質完了条件
- [ ] 全単体テストの通過
- [ ] 統合テストの通過
- [ ] パフォーマンステストの通過
- [ ] ユーザビリティテストの実施

### 移行完了条件
- [ ] 既存UIMenuからの完全移行
- [ ] データ互換性の確保
- [ ] 設定移行の完了
- [ ] ドキュメント更新の完了

## リスク・対策

### 技術的リスク
1. **pygame_gui制約**
   - 高度なUI実装の技術的限界
   - 対策: カスタムコンポーネント実装

2. **パフォーマンス問題**
   - 複雑UIでの性能劣化
   - 対策: プロファイリング・最適化

### スケジュールリスク
1. **実装複雑度**
   - 想定以上の実装工数
   - 対策: MVP実装→段階的機能追加

2. **品質確保**
   - テスト・品質確認工数
   - 対策: 継続的テスト・早期品質確認

## 期待される効果

### ユーザエクスペリエンス向上
- **操作性向上**: ドラッグ&ドロップ等の直感的操作
- **視認性向上**: 洗練されたレイアウト・デザイン
- **効率性向上**: 高度な検索・フィルタ機能

### 技術的効果
- **保守性向上**: 統一されたWindowSystem
- **拡張性向上**: 新機能追加の容易性
- **品質向上**: 一貫したテスト・品質保証

## 関連ドキュメント
- `docs/todos/0044_uimenu_phased_removal_long_term.md`: UIMenu削除計画
- `docs/window_system.md`: WindowSystem設計書
- `docs/ui_design_guidelines.md`: UI設計ガイドライン
- `docs/todos/0046_final_integration_testing.md`: 最終統合テスト