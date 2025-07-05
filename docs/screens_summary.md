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

## 💡 今後の開発・修正時の指針

### 新しい画面追加時
1. `Window`クラスを継承した新クラス作成
2. `WindowManager`に登録
3. 遷移元でメッセージ送信の実装
4. 遷移先でメッセージ受信ハンドラー実装

### 画面遷移の修正時
1. メッセージタイプの確認
2. 送信元と受信先の確認
3. WindowStackの状態確認
4. ESCキー処理の確認

### パフォーマンス最適化時
1. UI要素の適切な破棄（`cleanup_ui()`）
2. WindowPoolの活用
3. 不要なUIManagerの重複回避

---

**作成日:** 2025年7月5日  
**対象ゲーム:** Dungeon - Wizardry風1人称探索RPG  
**目的:** 不具合発生時・開発時の参照資料