# GameManager.py リファクタリング計画詳細

## 📋 概要
- **作成日**: 2025年7月19日
- **対象**: src/core/game_manager.py (1,982行)
- **目的**: モノリシックなクラスの責任分離とコード重複の解消

## 🔍 分析結果

### similarity-py検出結果
- **高重複メソッド**:
  - `transition_to_dungeon` ↔ `_main_loop`: 92.49%類似
  - `_main_loop` ↔ `_handle_combat_fled`: 94.84%類似
  - `load_game_state` ↔ `_main_loop`: 91.03%類似
  - `_handle_ui_events` ↔ `_main_loop`: 92.23%類似

### 現在の責任混在
1. **メインループ管理** (327行)
2. **戦闘状態管理** (250行)
3. **入力処理** (190行)
4. **シーン遷移** (180行)
5. **セーブ/ロード** (120行)
6. **UI管理** (100行)
7. **デバッグ機能** (80行)

## 🎯 Phase 1: Core Loop Refactoring

### 1. MainLoopManager抽出
**対象メソッド**:
```python
# 行数: 327行 → 100行程度に統合
- _main_loop(): 1190-1293 (103行) ← 旧バージョン（削除対象）
- _main_loop_refactored(): 1058-1100 (42行) ← メイン実装
- _handle_ui_events(): 1102-1133 (31行)
- _update_systems(): 1135-1157 (22行)
- _render_frame(): 1159-1188 (29行)
```

**新クラス設計**:
```python
# src/core/loop/main_loop_manager.py
class MainLoopManager(EventAwareComponent):
    def __init__(self, screen, clock, target_fps=60)
    def run_main_loop() -> None
    def handle_frame_events(events: List) -> bool
    def update_systems(time_delta: float) -> None
    def render_frame() -> None
    def stop() -> None
```

### 2. CombatStateManager抽出
**対象メソッド**:
```python
# 行数: 250行
- start_combat(): 1519-1552 (33行)
- check_combat_state(): 1554-1568 (14行)
- end_combat(): 1570-1601 (31行)
- _handle_combat_victory(): 1603-1637 (34行)
- _handle_combat_defeat(): 1639-1673 (34行)
- _handle_combat_fled(): 1675-1719 (44行)
- _handle_combat_negotiated(): 1721-1753 (32行)
- trigger_encounter(): 1480-1517 (37行)
```

**新クラス設計**:
```python
# src/core/combat/combat_state_manager.py
class CombatStateManager(EventAwareComponent):
    def start_combat(monsters) -> bool
    def check_combat_state() -> None
    def end_combat() -> None
    def handle_combat_result(result_type: str) -> None
    def trigger_encounter(encounter_type: str, level: int) -> None
```

### 3. InputHandlerCoordinator作成
**対象メソッド**:
```python
# 行数: 190行
- _setup_input(): 211-252 (41行)
- _on_menu_action(): 295-309 (14行)
- _on_confirm_action(): 311-314 (3行)
- _on_cancel_action(): 316-319 (3行)
- _on_action_action(): 321-354 (33行)
- _on_debug_toggle(): 356-361 (5行)
- _on_3d_stage_advance(): 363-385 (22行)
- _on_3d_stage_reset(): 387-394 (7行)
- _on_pause_action(): 396-400 (4行)
- _on_inventory_action(): 402-408 (6行)
- _on_magic_action(): 410-416 (6行)
- _on_equipment_action(): 418-424 (6行)
- _on_status_action(): 426-432 (6行)
- _on_camp_action(): 434-440 (6行)
- _on_help_action(): 442-462 (20行)
- _on_movement_action(): 464-485 (21行)
```

**新クラス設計**:
```python
# src/core/input/input_handler_coordinator.py
class InputHandlerCoordinator(EventAwareComponent):
    def register_input_handler(priority: int, handler) -> None
    def process_input_event(event) -> bool
    def setup_input_bindings() -> None
    def handle_action(action: str, pressed: bool, input_type) -> bool
```

## 🏗️ 共通インターフェース

### GameComponent基底クラス
```python
# src/core/interfaces/game_component.py
class GameComponent(ABC):
    @abstractmethod
    def initialize(self, context: Dict[str, Any]) -> bool: pass
    @abstractmethod
    def cleanup(self) -> None: pass

class EventAwareComponent(GameComponent):
    @abstractmethod
    def handle_game_event(self, event: Any) -> bool: pass
```

## 📋 実装手順

### Step 1: インターフェース作成
1. `src/core/interfaces/game_component.py` 作成
2. 基底クラスの実装

### Step 2: MainLoopManager実装
1. `src/core/loop/main_loop_manager.py` 作成
2. メソッド移行と重複削除
3. GameManagerでの統合

### Step 3: CombatStateManager実装
1. `src/core/combat/combat_state_manager.py` 作成
2. 戦闘関連メソッドの移行
3. イベント駆動化

### Step 4: InputHandlerCoordinator実装
1. `src/core/input/input_handler_coordinator.py` 作成
2. 入力処理の優先順位システム構築
3. アクションハンドラーの統合

### Step 5: GameManager簡素化
1. 抽出されたメソッドの削除
2. 新コンポーネントとの統合
3. テスト実行

## 🎯 期待される効果

### コード品質
- **行数削減**: 1,982行 → 800行程度（GameManager）
- **重複解消**: similarity-pyで検出された90%類似の重複削除
- **可読性**: 各クラス200-300行の適切なサイズ

### 保守性
- **単一責任**: 各クラスが明確な責任を持つ
- **テスト容易**: 機能別の独立したテスト
- **拡張性**: 新機能追加時の影響範囲限定

## ⚠️ 注意事項

### 既存機能の保持
- ゲーム動作に影響を与えない漸進的リファクタリング
- 既存のイベントシステムとの互換性維持
- UIシステム（WindowManager）との連携保持

### テスト方針
- 各Phase完了後のゲーム動作確認
- デバッグAPIを活用した動作検証
- 段階的なコミット（機能単位）

## 📅 スケジュール
- **Phase 1完了目標**: リファクタリング開始から2週間以内
- **全体完了目標**: 6週間以内

---
**作成者**: Claude Code  
**最終更新**: 2025年7月19日