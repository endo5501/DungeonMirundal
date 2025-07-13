# 未実装項目リスト（更新版）

## 概要

このドキュメントは、FIXME、TODO、仮実装などのキーワードを元に抽出された、プロジェクト内の未実装項目をまとめたものです。

---

## 優先度: 高

### ダンジョンシステム

- **ダンジョン内メニューの実装**
  - **説明:** ダンジョン探索中に開くメインメニュー（インベントリ、魔法、装備など）が未実装です。
  - **該当箇所:**
    - `src/rendering/dungeon_renderer_pygame_backup.py:462`
    - `src/ui/dungeon_ui_pygame.py:399`
    - `src/ui/windows/dungeon_menu_window.py:298`

- **アイテム使用の本格実装**
  - **説明:** ダンジョンやステータス効果と連携したアイテム使用ロジックが未実装です。
  - **該当箇所:**
    - `src/items/item_usage.py:274,281,288,296,304`

- **探索システムの基本的な実装**
  - **説明:** 探索済みセルの管理や、それに基づく小地図の表示ロジックが不完全です。
  - **該当箇所:**
    - `src/ui/small_map_ui_pygame.py:123`

- **ダンジョン内インタラクション**
  - **説明:** ダンジョン内のオブジェクト（宝箱、罠など）とのインタラクションが未実装です。
  - **該当箇所:**
    - `src/rendering/dungeon_input_handler.py:304`

### UIシステム (WindowSystem)

- **OverworldMainWindowのダイアログ実装**
  - **説明:** 情報表示、キャラクター詳細、確認ダイアログなど、UIの根幹をなす機能が`WindowSystem`へ移行中ですが、まだ実装されていません。
  - **該当箇所:**
    - `src/overworld/overworld_manager.py:1084,1172,1466,1479,1485,1497`

- **DungeonSelectionWindowの実装**
  - **説明:** ダンジョンを選択するためのUIが未実装です。
  - **該当箇所:**
    - `src/overworld/overworld_manager.py:19,815,816`

- **基本的なメッセージダイアログの実装**
  - **説明:** ゲーム全体で利用する汎用的なメッセージダイアログが未実装です。
  - **該当箇所:**
    - `src/facilities/ui/service_panel.py:211`

### 施設 (Facilities)

- **宿屋 (Inn): 保管庫システムの本格実装**
  - **説明:** アイテム保管庫のロジックが仮実装のままです。
  - **該当箇所:**
    - `src/facilities/services/inn_service.py:205,206,330-365`
    - `src/facilities/ui/inn/storage_panel.py:162,175`

- **寺院 (Temple): 祝福・カルマ効果の本格実装**
  - **説明:** 祝福やカルマといった、ゲームの深みに関わるシステムが未実装です。
  - **該当箇所:**
    - `src/facilities/services/temple_service.py:575,576,652`

- **魔法ギルド (Magic Guild): 魔法関連処理の本格実装**
  - **説明:** 魔法の学習、研究、鑑定などのコア機能が仮実装です。
  - **該当箇所:**
    - `src/facilities/services/magic_guild_service.py:181,289`

---

## 優先度: 中

### 機能拡張

- **特別アイテムやヒントの実装**
  - **説明:** 交渉成功時などに手に入る特別な報酬が未実装です。
  - **該当箇所:**
    - `src/core/game_manager.py:1749`

- **ItemInstanceの鑑定状態チェック**
  - **説明:** 未鑑定アイテムの使用可否チェックロジックが不完全です。
  - **該当箇所:**
    - `src/items/item_usage.py:63`

- **設定変更機能**
  - **説明:** ゲーム設定（音量、画面サイズなど）の変更機能が未実装です。
  - **該当箇所:**
    - `src/overworld/overworld_manager.py:1572`

### UI改善

- **ギルド (Guild): UIの改善**
  - **説明:** キャラクター詳細情報の追加や、パーティ名取得処理、UIのハイライトなど、UX向上のための改善が必要です。
  - **該当箇所:**
    - `src/facilities/ui/guild/character_list_panel.py:279`
    - `src/facilities/ui/guild/party_formation_panel.py:291`
    - `src/facilities/ui/guild/character_creation_wizard.py:513,541`

### 仮実装の改善

- **宿屋 (Inn): UIの仮データ・仮実装の置換**
  - **説明:** アイテム管理UIなどが仮実装のままです。
  - **該当箇所:**
    - `src/facilities/ui/inn/item_management_panel.py:182,189,193,206`

- **レンダリング: 仮定の値の置換**
  - **説明:** FOV（視野角）などが固定値になっているため、設定から取得するよう変更が必要です。
  - **該当箇所:**
    - `src/rendering/prop_renderer.py:66`

---

## 優先度: 低

### コード整理・廃止予定

- **廃止予定のフィールドの削除**
  - **説明:** 旧インベントリシステムの `inventory`, `equipped_items` フィールドが残存しています。
  - **該当箇所:**
    - `src/character/character.py:95,96`

- **save_configの有効化**
  - **説明:** 入力設定の保存機能がコメントアウトされています。
  - **該当箇所:**
    - `src/core/game_manager.py:703`

- **翻訳ファイルの更新**
  - **説明:** "ダンジョン入口"のラベルがハードコードされています。
  - **該当箇所:**
    - `src/overworld/overworld_manager.py:334`

### 未実装機能のプレースホルダー

- **宿屋 (Inn): 魔法管理・装備管理**
  - **説明:** 現在は説明文のみ表示されています。
  - **該当箇所:**
    - `src/facilities/ui/inn/spell_management_panel.py:50,54`
    - `src/facilities/ui/inn/equipment_management_panel.py:50,54`