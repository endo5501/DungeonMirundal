# 未実装項目リスト

## 優先度: 高

### ダンジョンシステム
- **ダンジョン内メニューの実装**
  - `src/rendering/dungeon_renderer_pygame_backup.py:462`
  - `src/ui/dungeon_ui_pygame.py:399`
  - `src/ui/windows/dungeon_menu_window.py:298`
- **アイテム使用の本格実装**
  - ダンジョンやステータス効果と連携したアイテム使用。
  - `src/items/item_usage.py:274,281,288,296,304`
- **探索システムの基本的な実装**
  - `src/ui/small_map_ui_pygame.py:123`

### UIシステム
- **OverworldMainWindowのダイアログ実装**
  - 情報表示、キャラクター詳細、確認ダイアログなど、UIの根幹をなす機能。
  - `src/overworld/overworld_manager.py:1084,1172,1466,1479,1485,1497`
- **DungeonSelectionWindowの実装**
  - `src/overworld/overworld_manager.py:19,815,816`
- **基本的なメッセージダイアログの実装**
  - `src/facilities/ui/service_panel.py:211`

### 施設 (Facilities)
- **宿屋 (Inn): 保管庫システムの本格実装**
  - `src/facilities/services/inn_service.py:205,206,330-365`
- **寺院 (Temple): 祝福・カルマ効果の本格実装**
  - `src/facilities/services/temple_service.py:575,576,652`
- **ギルド (Guild): キャラクター取得・管理の本格実装**
  - `src/facilities/services/guild_service.py:237,674,676,685`
- **魔法ギルド (Magic Guild): 魔法関連処理の本格実装**
  - `src/facilities/services/magic_guild_service.py:232,267,314,353,411,517,544,554,583,691`

## 優先度: 中

### 機能拡張
- **特別アイテムやヒントの実装**
  - `src/core/game_manager.py:1293`
- **ItemInstanceの鑑定状態チェック**
  - `src/items/item_usage.py:63`
- **実際のアイテム操作**
  - `src/facilities/services/service_utils.py:156,157`
- **魔法使用回数のリセット**
  - `src/overworld/overworld_manager.py:156`
- **設定変更機能**
  - `src/overworld/overworld_manager.py:1457`

### UI改善
- **ギルド: キャラクター詳細情報の追加**
  - `src/facilities/ui/guild/character_list_panel.py:277`
- **ギルド: パーティ名取得処理**
  - `src/facilities/ui/guild/party_formation_panel.py:238`
- **キャラクター作成ウィザードの改善**
  - ハイライトスタイル定義、文字種検証。
  - `src/facilities/ui/guild/character_creation_wizard.py:392,412`
- **魔法研究ウィザードの仮実装の改善**
  - `src/facilities/ui/magic_guild/magic_research_wizard.py:210,316`

### 仮実装の改善
- **宿屋 (Inn): UIの仮データ・仮実装の置換**
  - `src/facilities/ui/inn/storage_panel.py:162,175`
  - `src/facilities/ui/inn/item_management_panel.py:182,189,193,206`
- **レンダリング: 仮定の値を設定から取得**
  - `src/rendering/prop_renderer.py:66`
- **UI: 仮定のメソッドを正式なものに置換**
  - `src/ui/selection_list_ui.py:368`

## 優先度: 低

### コード整理・廃止予定
- **廃止予定のフィールドの削除**
  - `inventory`, `equipped_items`
  - `src/character/character.py:81,82`
- **save_configの有効化**
  - `src/core/game_manager.py:703`
- **翻訳ファイルの更新**
  - "ダンジョン入口"のラベル。
  - `src/overworld/overworld_manager.py:285`

### 未実装機能のプレースホルダー
- **宿屋 (Inn): 魔法管理・装備管理**
  - 現在は説明文のみ表示されている。
  - `src/facilities/ui/inn/spell_management_panel.py:50,54`
  - `src/facilities/ui/inn/equipment_management_panel.py:50,54`
- **施設 (Facilities): 実装予定メッセージ**
  - `src/facilities/ui/facility_window.py:293`
