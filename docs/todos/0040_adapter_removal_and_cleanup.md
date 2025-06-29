# 0040: アダプタ除去とクリーンアップ - 移行完了後作業

## 目的
WindowSystem移行完了後、一時的に作成されたアダプタクラスの除去と、旧UIMenuシステムのクリーンアップを行う。

## 経緯
- WindowSystem移行作業により、以下のアダプタクラスが作成された：
  - `src/ui/equipment_ui_adapter.py`
  - `src/ui/inventory_ui_adapter.py`
  - `src/ui/character_creation_adapter.py`
  - `src/ui/dungeon_ui_adapter.py`
- これらのアダプタは移行期間中の互換性維持のための一時的な実装
- 全システムの移行完了後、アダプタを除去し、新WindowSystemに統一する

## 現状分析

### 移行完了済みコンポーネント
- **EquipmentWindow** ✅
  - 新実装: `src/ui/windows/equipment_window.py`
  - 管理者: `src/ui/windows/equipment_manager.py`
  - アダプタ: `src/ui/equipment_ui_adapter.py` 🔄 (除去対象)

- **InventoryWindow** ✅
  - 新実装: `src/ui/windows/inventory_window.py`
  - 管理者: `src/ui/windows/inventory_manager.py`
  - アダプタ: `src/ui/inventory_ui_adapter.py` 🔄 (除去対象)

- **CharacterCreationWizard** ✅
  - 新実装: `src/ui/windows/character_creation_wizard.py`
  - 管理者: `src/ui/windows/character_creation_manager.py`
  - アダプタ: `src/ui/character_creation_adapter.py` 🔄 (除去対象)

- **DungeonMenuWindow** ✅
  - 新実装: `src/ui/windows/dungeon_menu_window.py`
  - 管理者: `src/ui/windows/dungeon_menu_manager.py`
  - アダプタ: `src/ui/dungeon_ui_adapter.py` 🔄 (除去対象)

### 除去対象の旧システムファイル
- `src/ui/equipment_ui.py` 🗑️ (除去対象)
- `src/ui/inventory_ui.py` 🗑️ (除去対象)
- `src/ui/character_creation.py` 🗑️ (除去対象)
- `src/ui/dungeon_ui_pygame.py` 🗑️ (除去対象)

## 段階的除去計画

### Phase 1: 依存関係の調査と更新
**期間**: 1週間

**作業内容**:
1. **全コードベースでのアダプタ使用箇所調査**
   ```bash
   # 検索対象
   grep -r "equipment_ui_adapter" src/
   grep -r "inventory_ui_adapter" src/
   grep -r "character_creation_adapter" src/
   grep -r "dungeon_ui_adapter" src/
   ```

2. **import文の更新**
   - 旧アダプタimportを新システムimportに変更
   - グローバル変数参照の新システムマネージャーへの変更

3. **インスタンス生成コードの更新**
   - アダプタファクトリ関数の新システムマネージャーへの変更

### Phase 2: アダプタ段階的無効化
**期間**: 1週間

**作業内容**:
1. **アダプタクラスに廃止警告追加**
   ```python
   import warnings
   
   class EquipmentUIAdapter:
       def __init__(self):
           warnings.warn(
               "EquipmentUIAdapter is deprecated. Use equipment_manager directly.",
               DeprecationWarning,
               stacklevel=2
           )
   ```

2. **アダプタ機能の段階的移行**
   - 重要でない機能から新システムへの直接呼び出しに変更
   - 警告ログの追加によるアダプタ使用追跡

3. **テストでのアダプタ使用除去**
   - 全テストコードで新システム直接使用に変更

### Phase 3: アダプタファイル除去
**期間**: 1週間

**作業内容**:
1. **アダプタファイル削除**
   ```bash
   rm src/ui/equipment_ui_adapter.py
   rm src/ui/inventory_ui_adapter.py
   rm src/ui/character_creation_adapter.py
   rm src/ui/dungeon_ui_adapter.py
   ```

2. **関連テストファイル更新**
   - アダプタ関連テストの除去または新システムテストへの変換

3. **import文エラーの修正**
   - アダプタ削除によるimportエラーの修正

### Phase 4: 旧システムファイル除去
**期間**: 1週間

**作業内容**:
1. **旧UIファイルの依存関係確認**
   - 他システムからの参照がないことを確認

2. **旧UIファイル削除**
   ```bash
   rm src/ui/equipment_ui.py
   rm src/ui/inventory_ui.py
   rm src/ui/character_creation.py
   rm src/ui/dungeon_ui_pygame.py
   ```

3. **関連テストファイル更新**
   - 旧システムテストの除去

## 更新が必要なファイルの特定

### 高優先度更新ファイル
- **ゲームメインループ**: `main.py`, `src/game/game_main.py`
- **ダンジョンシステム**: `src/dungeon/dungeon_manager.py`
- **地上システム**: `src/overworld/overworld_manager.py`
- **パーティ管理**: `src/character/party_manager.py`

### 中優先度更新ファイル
- **UI統合**: `src/ui/ui_manager.py`
- **ゲーム設定**: `src/core/game_config.py`
- **セーブシステム**: `src/save/save_manager.py`

### 低優先度更新ファイル
- **ヘルプシステム**: `src/ui/help_ui.py`
- **設定UI**: `src/ui/settings_ui.py`
- **デバッグ機能**: `src/debug/debug_ui.py`

## 新システム統一後のインターフェース

### 装備システム
```python
# 旧
from src.ui.equipment_ui_adapter import equipment_ui
equipment_ui.show_party_equipment_menu(party)

# 新
from src.ui.windows.equipment_manager import equipment_manager
equipment_manager.show_party_equipment_menu(party)
```

### インベントリシステム
```python
# 旧
from src.ui.inventory_ui_adapter import inventory_ui
inventory_ui.show_party_inventory_menu(party)

# 新
from src.ui.windows.inventory_manager import inventory_manager
inventory_manager.show_party_inventory_menu(party)
```

### キャラクター作成
```python
# 旧
from src.ui.character_creation_adapter import create_character_creation_wizard
wizard = create_character_creation_wizard(callback)

# 新
from src.ui.windows.character_creation_manager import character_creation_manager
character_creation_manager.start_character_creation(callback)
```

### ダンジョンUI
```python
# 旧
from src.ui.dungeon_ui_adapter import create_pygame_dungeon_ui
ui = create_pygame_dungeon_ui(screen)

# 新
from src.ui.windows.dungeon_menu_manager import dungeon_menu_manager
dungeon_menu_manager.create_dungeon_menu()
```

## テスト計画

### アダプタ除去前テスト
- [ ] 全機能テストの実行・通過確認
- [ ] 統合テストの実行・通過確認
- [ ] パフォーマンステストの実行・基準値確認

### アダプタ除去後テスト
- [ ] 同等の機能テスト実行・通過確認
- [ ] importエラーなし確認
- [ ] メモリ使用量の改善確認

### 回帰テスト
- [ ] 既存ゲーム機能の動作確認
- [ ] セーブ・ロード機能の動作確認
- [ ] UI遷移の正常性確認

## リスク・制約事項

### 技術的リスク
- **隠れた依存関係**: 調査で見つからない依存関係の存在
- **runtime import**: 動的importによるアダプタ参照
- **設定ファイル参照**: 設定ファイルでのアダプタクラス名参照

### 業務リスク
- **機能退行**: アダプタ除去による既存機能の動作不良
- **テスト工数**: 全機能の再テスト必要
- **リリーススケジュール**: アダプタ除去作業による開発遅延

### 軽減策
- **段階的除去**: 一度に全て除去せず、段階的に実施
- **十分なテスト**: 各段階での詳細なテスト実施
- **ロールバック準備**: 問題発生時の迅速なロールバック体制

## 完了条件
- [ ] 全アダプタファイルの除去
- [ ] 全旧UIシステムファイルの除去
- [ ] 新システムマネージャーへの統一
- [ ] import文の完全更新
- [ ] 全テストの通過
- [ ] パフォーマンス劣化なし確認
- [ ] メモリ使用量の改善確認
- [ ] ドキュメントの更新

## 成果指標

### コード品質指標
- **ファイル数削減**: 4個のアダプタファイル + 4個の旧UIファイル = 8ファイル削除
- **LOC削減**: 約2000行のアダプタコード削除
- **依存関係簡素化**: アダプタ層除去による依存関係の単純化

### パフォーマンス指標
- **メモリ使用量**: アダプタオーバーヘッド除去による削減
- **起動時間**: 不要なimport除去による改善
- **レスポンス性**: 間接呼び出し除去による改善

## 関連ドキュメント
- `docs/todos/0033_window_system_migration_medium_priority.md`: 移行作業本体
- `docs/todos/0039_battle_ui_integration_remaining.md`: 戦闘UI統合作業
- `docs/window_system.md`: WindowSystem設計書
- `docs/phase6_todos.md`: Phase 6統合・最適化計画

## 備考
- このクリーンアップ作業は移行作業完了後の最終フェーズ
- アダプタ除去により、新WindowSystemの利点を最大限活用可能
- 長期的なメンテナンス性とパフォーマンスの改善が期待される