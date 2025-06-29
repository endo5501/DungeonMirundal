# 説明

現在、このゲームのメニューの階層移動の問題を解決するため、これまで使用していたUIMenuシステムからWindowSystemの刷新した。
(新WindowSystemについては @docs/window_system.md)

@docs/window_system.md では、移行が完了したと記載されているが、実際のとことは旧来のUIMenuシステムと新WindowSystemが混在しており、うまく機能していない。

# TODO

現在の./src/以下のコードを調査し、UIMenuから MenuWindow やDialogWindow、ListWindow、FormWindowなどへの変更が必要な箇所、削除するべきコードを探し出し、以下に出力してください

# 調査結果

## UIMenu使用状況の詳細分析

### 重要な発見事項

1. **インポートエラーの存在**
   - `help_ui.py`(6行目): `from src.ui.base_ui import UIMenu` → **存在しないファイル**
   - `magic_ui.py`(6行目): `from src.ui.base_ui import UIMenu` → **存在しないファイル**
   
2. **新WindowSystemドキュメントとの不一致**
   - `docs/window_system.md`では「移行完了」とされているが、実際は18ファイルで旧UIMenuが使用中
   - 新旧システムの混在により動作不安定

### 移行が必要なファイル一覧（18ファイル）

#### 緊急修正が必要（インポートエラー）
1. **`src/ui/help_ui.py`** (6行目)
   - 問題: `from src.ui.base_ui import UIMenu` → 存在しないファイル
   - 影響: 4箇所でUIMenu使用（248, 287行目等）
   - 修正: `HelpWindow`への移行

2. **`src/ui/magic_ui.py`** (6行目)
   - 問題: `from src.ui.base_ui import UIMenu` → 存在しないファイル
   - 影響: 8箇所でUIMenu使用（53, 101, 140行目等）
   - 修正: `MagicWindow`への移行

#### 高優先度移行対象
3. **`src/ui/status_effects_ui.py`**
   - UIMenu使用箇所: 36, 72, 154行目
   - 修正: `StatusEffectsWindow`への移行

4. **`src/ui/settings_ui.py`**
   - UIMenu使用箇所: 135, 210, 282, 340, 391, 450, 512行目
   - 修正: `SettingsWindow`への移行（既に新システム実装済み）

#### 中優先度移行対象
5. **`src/ui/equipment_ui.py`** → `EquipmentWindow`
6. **`src/ui/inventory_ui.py`** → `InventoryWindow`
7. **`src/ui/dungeon_ui_pygame.py`** → `BattleUIWindow`
8. **`src/ui/character_creation.py`** → `CharacterCreationWizard`

#### 施設関連移行対象
9. **`src/overworld/facilities/guild.py`**
10. **`src/overworld/facilities/inn.py`**
11. **`src/overworld/facilities/shop.py`**
12. **`src/overworld/facilities/magic_guild.py`**
13. **`src/overworld/facilities/temple.py`**
→ すべて`FacilityMenuWindow`への移行

#### 管理クラス移行対象
14. **`src/overworld/overworld_manager_pygame.py`**
15. **`src/overworld/overworld_manager.py`**
16. **`src/overworld/base_facility.py`**
17. **`src/ui/menu_stack_manager.py`**

#### UIMenu定義元
18. **`src/ui/base_ui_pygame.py`** (366行目)
   - UIMenuクラス定義本体
   - 全移行完了後に削除予定

### 削除すべき旧コード

#### 1. UIMenuクラス関連
- **`src/ui/base_ui_pygame.py`**: UIMenuクラス定義（366行目）
- **関連メソッド**: `add_element()`, `add_menu_item()`, `add_back_button()`

#### 2. 不正なインポート文
- `src/ui/help_ui.py`: `from src.ui.base_ui import UIMenu`
- `src/ui/magic_ui.py`: `from src.ui.base_ui import UIMenu`

### 修正優先順位

#### 最優先（即座修正）
1. **インポートエラー修正**
   - `help_ui.py`, `magic_ui.py`のインポート文修正
   - 一時的に`base_ui_pygame`からのインポートに変更

#### 高優先度（1週間以内）
2. **コア機能の移行**
   - `help_ui.py` → `HelpWindow`
   - `magic_ui.py` → `MagicWindow`
   - `status_effects_ui.py` → `StatusEffectsWindow`

#### 中優先度（2週間以内）
3. **UI機能の移行**
   - `equipment_ui.py`, `inventory_ui.py`, `character_creation.py`等

#### 低優先度（1ヶ月以内）
4. **施設・管理機能の移行**
   - 施設関連ファイル群
   - 管理クラス群

### 技術的課題

1. **アーキテクチャの不一致**
   - 新WindowSystemは実装済みだが、移行が未完了
   - 18ファイルで旧システムが残存

2. **テスト影響範囲**
   - 各ファイル移行時のテスト修正が必要
   - 段階的移行によるテスト整合性確保

3. **依存関係の解決**
   - UIMenuに依存するコードの段階的移行
   - 新旧システム混在期間中の安定性確保
