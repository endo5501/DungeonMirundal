# Phase 4 重複コード除去計画 - 高類似度重複の完全統合

## 概要

Phase 1-3で100%-96%の重複を除去した後の`similarity-py ./src`再分析結果に基づく、残存する85%-99%重複の体系的リファクタリング計画。特にInn施設クラスの大量重複（90-99%類似）を最優先として対処。

## 重複クラス分析結果

### 優先度: 緊急（90%以上）

#### 1. Inn施設クラス（90-99%重複）
**影響範囲**: 施設システムの中核
**重複パターン**: 
- 複数のInn関連メソッドが90-99%の高い類似度
- 施設運営ロジックの重複実装
- UIハンドリングパターンの重複

**統合戦略**:
```python
# Template Method + Strategy パターンによる統合
class BaseFacilityHandler:
    def handle_facility_operation(self, operation_type: str, **kwargs):
        """施設操作の統一テンプレート"""
        if not self._validate_operation(operation_type, **kwargs):
            return False
        
        result = self._execute_operation(operation_type, **kwargs)
        self._post_operation_cleanup(operation_type, result)
        return result
    
    @abstractmethod
    def _execute_operation(self, operation_type: str, **kwargs):
        """具体的な操作実装（サブクラスで実装）"""
        pass

class InnFacilityHandler(BaseFacilityHandler):
    def _execute_operation(self, operation_type: str, **kwargs):
        operations = {
            'rest': self._handle_rest,
            'room_booking': self._handle_room_booking,
            'healing': self._handle_healing
        }
        return operations.get(operation_type, self._handle_unknown)(**kwargs)
```

### 優先度: 高（85-94%重複）

#### 2. EquipmentManager（85-94%重複）
**重複メソッド数**: 8-12個
**統合アプローチ**: Command Pattern + Unified Interface

```python
class EquipmentOperationCommand:
    """装備操作コマンドの統一インターフェース"""
    
    def execute_equipment_operation(self, operation: str, **params) -> bool:
        """装備操作の統一実行メソッド"""
        operation_map = {
            'equip': self._execute_equip,
            'unequip': self._execute_unequip,
            'swap': self._execute_swap,
            'enhance': self._execute_enhance
        }
        
        if operation not in operation_map:
            raise ValueError(f"Unknown operation: {operation}")
            
        return operation_map[operation](**params)
```

#### 3. DungeonMenuWindow（87-97%重複）
**重複パターン**: メニュー表示ロジック、イベント処理
**統合戦略**: Factory Method + Template Method

```python
class MenuDisplayManager:
    """ダンジョンメニュー表示の統一管理"""
    
    def display_menu(self, menu_type: str, context: dict) -> bool:
        """メニュー表示の統一メソッド"""
        menu_factory = {
            'main': self._create_main_menu,
            'inventory': self._create_inventory_menu,
            'character': self._create_character_menu,
            'save': self._create_save_menu
        }
        
        menu = menu_factory.get(menu_type, self._create_default_menu)(context)
        return self._show_and_handle_menu(menu)
```

#### 4. FormWindow（87-95%重複）
**重複要素**: フォーム validation、submit処理、UI構築
**統合手法**: Builder Pattern + Validator Chain

```python
class FormBuilder:
    """フォーム構築と処理の統一システム"""
    
    def build_form(self, form_config: dict) -> 'Form':
        """設定に基づいてフォームを構築"""
        form = Form()
        
        for field_config in form_config.get('fields', []):
            field = self._create_field(field_config)
            form.add_field(field)
        
        form.set_validator_chain(self._build_validator_chain(form_config))
        return form
    
    def _create_field(self, config: dict) -> 'FormField':
        """フィールド作成の統一メソッド"""
        field_types = {
            'text': TextFormField,
            'number': NumberFormField,
            'select': SelectFormField,
            'checkbox': CheckboxFormField
        }
        
        field_class = field_types.get(config['type'], TextFormField)
        return field_class(config)
```

### 優先度: 中（95%重複、小規模）

#### 5. UIRenderer（95%重複）
**重複箇所**: 2-3メソッド
**簡易統合**: メソッド統合 + パラメータ化

#### 6. PartyPosition（96%重複）  
**重複箇所**: 1-2メソッド
**簡易統合**: 直接的メソッド統合

## Phase 4 実装スケジュール

### Week 1: Inn施設クラス重複除去
**Day 1-2**: 
- Inn関連クラスの詳細分析
- BaseFacilityHandler設計・実装

**Day 3-4**:
- InnFacilityHandler実装
- 既存Innクラスからの移行

**Day 5**:
- テスト実行・修正
- 部分コミット

### Week 2: EquipmentManager & DungeonMenuWindow
**Day 1-3**: EquipmentManager重複除去
**Day 4-5**: DungeonMenuWindow重複除去

### Week 3: FormWindow & 小規模重複
**Day 1-3**: FormWindow重複除去
**Day 4**: UIRenderer, PartyPosition重複除去
**Day 5**: 総合テスト・最終調整

## 重複除去パターン詳細

### Template Method Pattern適用
```python
# 基底クラスでアルゴリズムの骨格を定義
class FacilityOperationTemplate:
    def execute_facility_action(self):
        if not self.validate_prerequisites():
            return False
        
        self.prepare_operation()
        result = self.perform_core_operation()  # 抽象メソッド
        self.finalize_operation(result)
        return result
    
    @abstractmethod
    def perform_core_operation(self):
        """サブクラスで具体的な操作を実装"""
        pass
```

### Strategy Pattern適用
```python
# 操作戦略の切り替え可能な設計
class OperationStrategy:
    @abstractmethod
    def execute(self, context: dict) -> bool:
        pass

class RestOperationStrategy(OperationStrategy):
    def execute(self, context: dict) -> bool:
        # 休息操作の具体実装
        pass

class HealingOperationStrategy(OperationStrategy):
    def execute(self, context: dict) -> bool:
        # 治療操作の具体実装
        pass
```

### Command Pattern適用
```python
# 操作のカプセル化と統一実行
class FacilityCommand:
    def __init__(self, operation: str, params: dict):
        self.operation = operation
        self.params = params
    
    def execute(self) -> bool:
        return self._get_handler().handle(self.operation, self.params)
    
    def undo(self) -> bool:
        return self._get_handler().undo(self.operation, self.params)
```

## テスト戦略

### 1. リファクタリング前テスト
```bash
# 現在のテスト状況を記録
uv run pytest --tb=short > phase4_pre_tests.log
```

### 2. 段階的テスト実行
```bash
# Inn関連テストのみ実行
uv run pytest tests/ -k "inn or facility" -v

# Equipment関連テストのみ実行  
uv run pytest tests/ -k "equipment" -v

# UI関連テストのみ実行
uv run pytest tests/ -k "ui or window" -v
```

### 3. 統合テスト
```bash
# 全テスト実行（リファクタリング後）
uv run pytest
```

## 品質保証

### コード品質チェック
```bash
# リファクタリング後の品質確認
similarity-py ./src  # 重複度の改善確認
uv run pytest       # 機能テスト
```

### 予想される改善効果
- **重複率**: 85-99% → 15-25%に削減
- **保守性**: 統一インターフェースによる大幅改善
- **拡張性**: 新しい施設・装備・メニュー追加の容易化
- **テストカバレッジ**: 統一されたテストパターンによる向上

## リスク管理

### 高リスク項目
1. **Inn施設の複雑性**: 90-99%重複が示す高い結合度
2. **UI連携**: 複数のUIコンポーネント間の相互依存
3. **既存データ互換性**: セーブデータとの互換性維持

### 対策
1. **段階的移行**: 一度に全てを変更せず、小さな単位で移行
2. **既存APIの保持**: 外部からのインターフェースは可能な限り維持
3. **バックアップ戦略**: 重要なクラスは移行前にバックアップ作成

## 成功指標

### 定量的指標
- 重複率: 現在85-99% → 目標25%以下
- テスト通過率: 100%維持
- コード行数: 20-30%削減予想

### 定性的指標  
- 新機能追加の工数削減
- バグ修正の影響範囲縮小
- コードレビューの効率化

## 次フェーズ計画

Phase 4完了後は以下を検討:
- **Phase 5**: 残存する中小規模重複（70-84%）の最適化
- **Performance Optimization**: リファクタリングによるパフォーマンス影響の測定・改善
- **Documentation Update**: 新しいアーキテクチャの文書化

---

**実装開始**: Phase 4計画承認後即座
**完了目標**: 3週間以内
**責任者**: Claude (TDD方式による実装)