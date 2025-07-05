# ゲーム画面遷移詳細ガイド

## 概要

Dungeonゲームの画面遷移システムとウィンドウ管理の詳細解説です。地上部メニューから開始し、各施設、ダンジョン探索まで、すべての画面遷移とその実装クラス・メソッドを網羅しています。

## 🏗️ 画面システムアーキテクチャ

### 核心システム
- **WindowManager** (`src/ui/window_system/window_manager.py`) - 全画面の統一管理
- **WindowStack** (`src/ui/window_system/window_stack.py`) - 画面階層のLIFO管理
- **OverworldManager** (`src/overworld/overworld_manager_pygame.py`) - 地上部の統括制御
- **GameManager** (`src/core/game_manager.py`) - ゲーム全体の状態管理

## 🎮 画面遷移フロー全体図

```
[スタート画面] 
     ↓
[地上メニュー] ━━━━━ [ESC] ━━━━━ [設定メニュー]
     ↓                           ↓
   施設選択                     [戻る]
     ↓
┌─────────────────┬─────────────┐
│ 施設画面         │ ダンジョン   │
├─────────────────┼─────────────┤
│• ギルド          │ • 入口選択   │
│• 宿屋            │ • 探索画面   │
│• 商店            │ • 戦闘画面   │
│• 教会            │ • メニュー   │
│• 魔法ギルド      │             │
└─────────────────┴─────────────┘
```

## 📱 主要画面一覧

### 1. 地上メインメニュー

**実装クラス:** `OverworldMainWindow`  
**ファイル:** `src/ui/window_system/overworld_main_window.py`

**主要メソッド:**
- `create()` - UI要素作成
- `handle_event()` - イベント処理
- `_process_menu_action()` - メニューアクション処理
- `handle_escape()` - ESCキー処理

**画面遷移メソッド:**
- 施設選択 → `_send_message('menu_item_selected', {'facility_id': facility_id})`
- ダンジョン入口 → `_send_message('menu_item_selected', {'item_id': 'dungeon_entrance'})`
- 設定メニュー → `_send_message('settings_menu_requested', {})`

**メニュータイプ (OverworldMenuType):**
- `MAIN` - メインメニュー（施設・ダンジョン入口）
- `SETTINGS` - 設定メニュー（ESCキー）
- `PARTY_STATUS` - パーティ状況表示
- `SAVE_LOAD` - セーブ・ロード
- `GAME_SETTINGS` - ゲーム設定

### 2. 施設系画面

#### 2.1 共通施設メニュー

**実装クラス:** `FacilityMenuWindow`  
**ファイル:** `src/ui/window_system/facility_menu_window.py`

**遷移ハンドラ:** `OverworldManager.handle_main_menu_message()`  
**ファイル:** `src/overworld/overworld_manager_pygame.py:261-337`

**施設別遷移メソッド:**
- ギルド → `_on_guild()` (`overworld_manager_pygame.py:699-717`)
- 宿屋 → `_on_inn()` (`overworld_manager_pygame.py:718-742`)
- 商店 → `_on_shop()` (`overworld_manager_pygame.py:743-760`)
- 教会 → `_on_temple()` (`overworld_manager_pygame.py:761-778`)
- 魔法ギルド → `_on_magic_guild()` (`overworld_manager_pygame.py:779-796`)

#### 2.2 個別施設の実装

##### ギルド（AdventurersGuild）
**実装クラス:** `AdventurersGuild`  
**ファイル:** `src/overworld/facilities/guild.py`  
**機能:** キャラクター作成、パーティ編成、クラス変更

##### 宿屋（Inn）
**実装クラス:** `Inn`  
**ファイル:** `src/overworld/facilities/inn.py`  
**サービスウィンドウ:** `InnServiceWindow`  
**ファイル:** `src/ui/window_system/inn_service_window.py`  
**ハンドラー:** `InnFacilityHandler`  
**ファイル:** `src/overworld/facilities/inn_facility_handler.py`  
**機能:** 休息、アイテム管理、冒険準備、パーティ名変更

**サービスタイプ:**
- `adventure_prep` - 冒険準備
- `item_management` - アイテム管理
- `magic_management` - 魔術管理
- `equipment_management` - 装備管理
- `spell_slot_management` - 魔法スロット管理
- `party_status` - パーティ状況

##### 商店（Shop）
**実装クラス:** `Shop`  
**ファイル:** `src/overworld/facilities/shop.py`  
**取引ウィンドウ:** `ShopTransactionWindow`  
**ファイル:** `src/ui/window_system/shop_transaction_window.py`  
**機能:** アイテム売買、装備購入

##### 教会（Temple）
**実装クラス:** `Temple`  
**ファイル:** `src/overworld/facilities/temple.py`  
**サービスウィンドウ:** `TempleServiceWindow`  
**ファイル:** `src/ui/window_system/temple_service_window.py`  
**機能:** 治療、蘇生、状態異常回復、祝福

##### 魔法ギルド（MagicGuild）
**実装クラス:** `MagicGuild`  
**ファイル:** `src/overworld/facilities/magic_guild.py`  
**サービスウィンドウ:** `MagicGuildServiceWindow`  
**ファイル:** `src/ui/window_system/magic_guild_service_window.py`  
**機能:** 魔法学習、アイテム鑑定、魔法サービス

#### 2.3 施設共通の遷移パターン

```python
# 1. 地上メニューから施設選択
OverworldMainWindow._process_menu_action()
↓
# 2. メッセージ送信
_send_message('menu_item_selected', {'facility_id': facility_id})
↓
# 3. OverworldManagerで処理
OverworldManager.handle_main_menu_message()
↓
# 4. 施設固有ハンドラ呼び出し
_on_guild() / _on_inn() / _on_shop() / _on_temple() / _on_magic_guild()
↓
# 5. FacilityManagerで施設入場
facility_manager.enter_facility(facility_id, current_party)
↓
# 6. 施設のenter()メソッド実行とウィンドウ表示
facility.enter() → facility._show_main_menu_window_manager()
```

### 3. ダンジョン系画面

#### 3.1 ダンジョン入口・選択

**遷移メソッド:** `OverworldManager._on_enter_dungeon()`  
**ファイル:** `src/overworld/overworld_manager_pygame.py`

**フロー:**
```python
_on_enter_dungeon()
↓
_show_dungeon_selection_menu()  # ダンジョン一覧表示
↓
_enter_selected_dungeon()  # ダンジョン選択処理
↓
GameManager.transition_to_dungeon()  # ゲーム状態遷移
```

#### 3.2 ダンジョン内メニュー

**実装クラス:** `DungeonMenuWindow`  
**ファイル:** `src/ui/windows/dungeon_menu_window.py`  
**マネージャー:** `DungeonMenuManager`  
**ファイル:** `src/ui/windows/dungeon_menu_manager.py`

**メニュー項目:**
- インベントリ管理
- 魔法・祈祷
- 装備管理
- キャンプ
- ステータス表示
- 状態効果確認
- 地上に戻る

#### 3.3 ダンジョン探索UI

**統合UI:** `DungeonUIManager`  
**ファイル:** `src/ui/dungeon_ui_pygame.py`  
**レンダラー:** `DungeonRenderer`  
**ファイル:** `src/rendering/dungeon_renderer_pygame.py`

**構成要素:**
- キャラクターステータスバー（常時表示）
- 小地図UI（位置情報）
- 疑似3D描画（Wizardry風1人称視点）
- 位置情報表示（ダンジョン名、階層、座標）

#### 3.4 戦闘UI

**統合管理:** `BattleIntegrationManager`  
**ファイル:** `src/ui/windows/battle_integration_manager.py`  
**戦闘ウィンドウ:** `BattleUIWindow`  
**ファイル:** `src/ui/window_system/battle_ui_window.py`

**機能:**
- パーティステータス表示
- 敵ステータス表示
- アクションメニュー
- 戦闘ログ
- キーボードショートカット

#### 3.5 地上部復帰

**復帰メソッド:** `GameManager.transition_to_overworld()`  
**コールバック:** `OverworldManager.on_facility_exit()`  
**ファイル:** `src/overworld/overworld_manager_pygame.py:116-133`

## 🔄 画面遷移のデザインパターン

### 1. WindowManagerパターン
- 全ての画面はWindowManagerが一元管理
- WindowStackによるLIFO（後入先出）の階層管理
- モーダルウィンドウのサポート

### 2. メッセージ駆動パターン
- ウィンドウ間の通信はメッセージベース
- `send_message(message_type, data)`による疎結合通信
- イベント駆動型の画面遷移

### 3. ファクトリーパターン
- `FacilityMenuUIFactory` - UI要素の生成
- 設定ベースの動的UI作成
- 再利用可能なコンポーネント設計

### 4. Command パターン
- `FacilityCommand` - 施設操作のコマンド化
- 操作の記録・取り消し対応
- 統一されたインターフェース

## 🎯 ESCキー処理フロー

### 地上部での処理
```python
OverworldMainWindow.handle_escape()
↓
# メイン画面の場合
_send_message('settings_menu_requested', {})
↓
# 設定画面表示
show_menu(OverworldMenuType.SETTINGS, config)
```

### 施設での処理
```python
FacilityMenuWindow.handle_escape()
↓
_handle_exit_selection()
↓
send_message('facility_exit_requested', {'facility_type': facility_type})
↓
OverworldManager.on_facility_exit()
↓
WindowManager.go_back()  # 前の画面に戻る
```

### ダンジョンでの処理
```python
DungeonMenuWindow.handle_escape()
↓
# メニュー閉じる
set_visibility(False)
↓
# ダンジョン探索画面に戻る
```

## 🗂️ ファイル構成と責務

### ウィンドウシステム (`src/ui/window_system/`)
```
window_manager.py           # ウィンドウ管理の核心
window_stack.py             # 画面階層管理
window.py                   # 基底ウィンドウクラス
overworld_main_window.py    # 地上メインメニュー
facility_menu_window.py     # 施設共通メニュー
*_service_window.py         # 各施設のサービス画面
battle_ui_window.py         # 戦闘UI
```

### ダンジョンUI (`src/ui/windows/`)
```
dungeon_menu_window.py      # ダンジョン内メニュー
dungeon_menu_manager.py     # ダンジョンメニュー管理
battle_integration_manager.py  # 戦闘統合管理
```

### 地上部管理 (`src/overworld/`)
```
overworld_manager_pygame.py  # 地上部統括管理
base_facility.py            # 施設基底クラス
facilities/                 # 各施設実装
├── guild.py               # ギルド
├── inn.py                 # 宿屋
├── shop.py                # 商店
├── temple.py              # 教会
└── magic_guild.py         # 魔法ギルド
```

### ゲーム管理 (`src/core/`)
```
game_manager.py             # ゲーム全体状態管理
```

### レンダリング (`src/rendering/`)
```
dungeon_renderer_pygame.py  # ダンジョン疑似3D描画
```

## 🐛 デバッグ時の参照ポイント

### 画面遷移の問題
1. **WindowStack状況確認:** `WindowManager.get_window_stack()`
2. **メッセージ送信ログ:** `OverworldMainWindow._send_message()`のログ
3. **施設入場処理:** `FacilityManager.enter_facility()`のログ

### UI表示の問題
1. **UIManager確認:** `window.ui_manager`の存在確認
2. **UI要素の生存状況:** `button.alive`プロパティ
3. **イベント処理:** `handle_event()`のデバッグログ

### 施設固有の問題
1. **施設初期化:** `initialize_facilities()`の実行確認
2. **パーティ状態:** `current_party`の確認
3. **設定ファイル:** 各施設の設定データ確認

## 🏢 施設内メニュー詳細

### 施設メインメニューからサービスへの遷移

#### 基本遷移パターン
```python
# 1. 施設入場（共通）
facility.enter() → _show_main_menu() → FacilityMenuWindow表示
↓
# 2. メニュー項目選択
FacilityMenuWindow._handle_menu_selection()
↓
# 3. メッセージ送信
send_message('menu_item_selected', {'item_id': service_id})
↓
# 4. 施設でのメッセージ処理
BaseFacility.handle_facility_message()
↓
# 5. サービス固有処理
facility._handle_facility_action() → サービスウィンドウ表示
```

### 施設別サービスウィンドウ

#### ギルド（Guild）
**メインメニュー項目:**
- キャラクター作成 (`character_creation`)
- パーティ編成 (`party_formation`)
- クラス変更 (`class_change`)
- 冒険者登録確認 (`registration_check`)

**特殊処理:** `src/overworld/facilities/guild.py`
- キャラクター作成ウィザード
- パーティ編成インターフェース
- クラス変更システム

#### 宿屋（Inn）
**サービスウィンドウ:** `InnServiceWindow`  
**ファイル:** `src/ui/window_system/inn_service_window.py`

**サービスタイプ:**
- `adventure_prep` - 冒険準備
- `item_management` - アイテム管理
- `magic_management` - 魔術管理
- `equipment_management` - 装備管理
- `spell_slot_management` - 魔法スロット管理
- `party_status` - パーティ状況

**宿屋ハンドラー:** `InnFacilityHandler`  
**ファイル:** `src/overworld/facilities/inn_facility_handler.py`

**統合メニュー数:** 12箇所のレガシーメニューを統合

#### 商店（Shop）
**取引ウィンドウ:** `ShopTransactionWindow`  
**ファイル:** `src/ui/window_system/shop_transaction_window.py`

**取引タイプ:**
- アイテム購入 (`purchase`)
- アイテム売却 (`sell`)
- カテゴリフィルター (`category_filter`)
- 数量選択 (`quantity_selection`)

**主要メソッド:**
- `get_purchasable_items()` - 購入可能アイテム
- `get_sellable_items()` - 売却可能アイテム
- `calculate_purchase_cost()` - 購入費用計算
- `calculate_sell_price()` - 売却価格計算

#### 教会（Temple）
**サービスウィンドウ:** `TempleServiceWindow`  
**ファイル:** `src/ui/window_system/temple_service_window.py`

**サービス:**
- キャラクター治療 (`healing`)
- キャラクター蘇生 (`resurrection`)
- 状態異常回復 (`status_cure`)
- 祝福 (`blessing`)
- 祈祷書販売 (`prayer_book_shop`)

#### 魔法ギルド（MagicGuild）
**サービスウィンドウ:** `MagicGuildServiceWindow`  
**ファイル:** `src/ui/window_system/magic_guild_service_window.py`

**サービスタイプ:**
- `spellbook_shop` - 魔術書店
- `spell_learning` - 魔法習得
- `identification` - アイテム鑑定
- `analysis` - 魔法分析
- `character_analysis` - キャラクター分析
- `spell_usage_check` - 魔法使用回数確認

**主要メソッド:**
- `get_spellbook_categories()` - 魔術書カテゴリ
- `get_available_spells_for_character()` - 習得可能魔法
- `get_identifiable_items()` - 鑑定可能アイテム
- `get_analyzable_spells()` - 分析可能魔法

### 施設サブウィンドウの基底クラス

**基底クラス:** `FacilitySubWindow`  
**ファイル:** `src/ui/window_system/facility_sub_window.py`

**共通機能:**
- `handle_back_navigation()` - 戻り処理
- `get_available_services()` - 利用可能サービス
- `update_context()` / `get_context()` - コンテキスト管理
- `has_party()` / `get_party_members()` - パーティ管理
- `can_provide_service()` - サービス提供可能性
- `handle_service_request()` - サービスリクエスト処理（抽象）

## 🚪 施設退出処理の完全フロー

### 退出のトリガー
1. **「出る」ボタンクリック** - FacilityMenuWindow内のexitボタン
2. **ESCキー押下** - `handle_escape()` → `_handle_exit_selection()`

### 退出処理の流れ

#### 1. FacilityMenuWindow での処理
**ファイル:** `src/ui/window_system/facility_menu_window.py`
```python
def _handle_exit_selection(self) -> bool:
    """「出る」選択を処理"""
    self.send_message('facility_exit_requested', {
        'facility_type': self.facility_type.value
    })
    return True

def handle_escape(self) -> bool:
    """ESCキー処理"""
    return self._handle_exit_selection()
```

#### 2. BaseFacility でのメッセージ処理
**ファイル:** `src/overworld/base_facility.py`
```python
def handle_facility_message(self, message_type: str, data: dict) -> bool:
    if message_type == 'menu_item_selected':
        item_id = data.get('item_id')
        if item_id == 'exit':
            self._exit_facility()
            return True

def _exit_facility(self):
    """施設から出る処理"""
    facility_manager.exit_current_facility()
```

#### 3. FacilityManager での退出管理
**ファイル:** `src/overworld/base_facility.py`
```python
def exit_current_facility(self) -> bool:
    """現在の施設から出る"""
    if self._validate_exit_conditions():
        facility = self.facilities[self.current_facility]
        if facility.exit():
            return self._handle_successful_exit()

def _handle_successful_exit(self) -> bool:
    """成功した退出処理"""
    self.current_facility = None
    if self.on_facility_exit_callback:
        self.on_facility_exit_callback()  # OverworldManagerのコールバック
    return True
```

#### 4. OverworldManager での退出コールバック
**ファイル:** `src/overworld/overworld_manager_pygame.py`
```python
def on_facility_exit(self):
    """施設退場時のコールバック"""
    if self.window_manager:
        success = self.window_manager.go_back()
        if not success:
            self._show_main_menu_unified()  # フォールバック
```

#### 5. WindowManager での画面遷移
**ファイル:** `src/ui/window_system/window_manager.py` / `window_stack.py`
```python
def go_back(self) -> bool:
    """前のウィンドウに戻る"""
    if len(self.stack) <= 1:
        return False
    
    current_window = self.pop()  # 現在のウィンドウをスタックから除去
    current_window.destroy()     # ウィンドウ破棄
    return True
```

### 退出時のクリーンアップ

#### UI要素のクリーンアップ
**ファイル:** `src/overworld/base_facility.py`
```python
def _cleanup_ui_windows(self):
    """WindowSystem関連のクリーンアップ"""
    possible_window_ids = [
        f"{self.facility_id}_main",
        f"{self.facility_id}_main_menu"
    ]
    
    for window_id in possible_window_ids:
        window = self.window_manager.get_window(window_id)
        if window:
            self.window_manager.close_window(window)
```

### 重要な実装上の注意

1. **メッセージの二重処理**
   - `facility_exit_requested`メッセージは送信されるが直接処理されない
   - 実際の処理は`menu_item_selected`で`item_id='exit'`として処理

2. **コールバックベースの設計**
   - FacilityManager → OverworldManager → WindowManager の階層的コールバック

3. **フォールバック機能**
   - `window_manager.go_back()`が失敗した場合の`_show_main_menu_unified()`

## 💡 今後の開発・修正時の指針

### 新しい画面追加時
1. `Window`クラスを継承した新クラス作成
2. `WindowManager`に登録
3. 遷移元でメッセージ送信の実装
4. 遷移先でメッセージ受信ハンドラー実装

### 新しい施設サービス追加時
1. `FacilitySubWindow`を継承したServiceWindow作成
2. `handle_service_request()`の実装
3. 施設クラスでサービス固有の`_handle_facility_action()`追加
4. メニュー設定へのサービス項目追加

### 画面遷移の修正時
1. メッセージタイプの確認
2. 送信元と受信先の確認
3. WindowStackの状態確認
4. ESCキー処理の確認

### 施設退出処理の修正時
1. `_handle_exit_selection()`の動作確認
2. `facility_manager.exit_current_facility()`の実行確認
3. `on_facility_exit_callback`の設定確認
4. `window_manager.go_back()`の結果確認

### パフォーマンス最適化時
1. UI要素の適切な破棄（`cleanup_ui()`）
2. WindowPoolの活用
3. 不要なUIManagerの重複回避
4. 施設切り替え時のリソースクリーンアップ

---

**作成日:** 2025年7月5日  
**対象ゲーム:** Dungeon - Wizardry風1人称探索RPG  
**目的:** 不具合発生時・開発時の参照資料