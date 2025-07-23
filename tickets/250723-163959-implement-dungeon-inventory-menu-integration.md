---
priority: 2
tags: ["ui", "dungeon", "inventory", "menu", "feature", "integration"]
description: "ダンジョンメニューの[インベントリ]ボタン機能を実装し、既存のインベントリシステムと連携"
created_at: "2025-07-23T16:39:59Z"
started_at: null  # Do not modify manually
closed_at: null   # Do not modify manually
---

# Ticket Overview

ダンジョンメニューの[インベントリ]ボタンを押しても現在何も起こらない状態になっている。調査の結果、インベントリシステム自体は完全に実装済みだが、ダンジョンメニューからの呼び出し処理が未実装であることが判明。既存のインベントリ機能とダンジョンメニューを適切に連携させる必要がある。

## 問題の詳細

### 現状
- **✅ インベントリシステム**: 845行の完全なインベントリ管理システムが実装済み
- **✅ インベントリマネージャー**: 162行の統一管理システムが実装済み
- **✅ ダンジョンメニューUI**: [インベントリ]ボタンは表示されている
- **❌ アクション処理**: ボタンを押しても「未実装」ログが出力されるのみ
- **❌ システム間連携**: ダンジョンメニューとインベントリシステムが未接続

### 技術的問題
1. **DungeonUIManagerPygameに`_open_inventory`メソッドが存在しない**
2. **ダンジョンメニューの`execute_menu_action`でインベントリ処理が未実装**
3. **適切なコールバック設定が欠如**

### 影響
- プレイヤーがダンジョン内でアイテム確認・使用ができない
- アイテム管理機能が実質的に利用不可能
- ダンジョン探索時の戦略的アイテム使用ができない

## Tasks

- [ ] `DungeonUIManagerPygame`に`_open_inventory`メソッドを実装
- [ ] `dungeon_menu_window.py`のインベントリアクション処理を実装
- [ ] インベントリマネージャーとの連携設定を追加
- [ ] ダンジョンメニューマネージャーでのコールバック設定を実装
- [ ] ダンジョン内でのインベントリウィンドウ表示動作確認
- [ ] インベントリウィンドウからの正常な復帰動作確認
- [ ] 複数キャラクターのインベントリ表示テスト
- [ ] アイテム使用・移動・破棄機能の動作確認
- [ ] Run tests before closing and pass all tests (No exceptions)
- [ ] Get developer approval before closing

## 受け入れ条件

- [ ] ダンジョンメニューで[インベントリ]ボタンを押すとインベントリウィンドウが表示される
- [ ] インベントリウィンドウでパーティメンバーの切り替えができる
- [ ] アイテムの詳細表示・使用・移動・破棄が正常に動作する
- [ ] インベントリウィンドウを閉じるとダンジョン画面に戻る
- [ ] ESCキーでインベントリウィンドウが閉じられる
- [ ] ダンジョン内でのUI階層管理が正常に動作する
- [ ] 全てのテストが通過している

## 実装対象ファイル

### 主要修正対象
1. **`src/ui/dungeon/dungeon_ui_manager_pygame.py`**
   - `_open_inventory()`メソッドの実装
   - インベントリマネージャーとの連携

2. **`src/ui/windows/dungeon_menu_window.py`**  
   - `execute_menu_action()`での`inventory`アクション処理実装

3. **`src/ui/windows/dungeon_menu_manager.py`**
   - インベントリコールバックの設定

### 既存活用可能なシステム
- **`src/ui/windows/inventory_window.py`** (845行) - 完全実装済み
- **`src/ui/windows/inventory_manager.py`** (162行) - 完全実装済み

## 実装アプローチ

### 1. DungeonUIManagerPygameの拡張
```python
def _open_inventory(self):
    """ダンジョン内でインベントリを開く"""
    if self.inventory_manager:
        self.inventory_manager.show_party_inventory_menu()
    else:
        logger.warning("インベントリマネージャーが初期化されていません")
```

### 2. ダンジョンメニューとの連携
```python
# dungeon_menu_window.py内
elif action == "inventory":
    self.close_menu()
    if "inventory" in self.callbacks:
        self.callbacks["inventory"]()
```

### 3. コールバック設定
```python
# dungeon_menu_manager.py内
def set_inventory_callback(self, callback):
    """インベントリコールバックを設定"""
    self.dungeon_menu_window.set_callback("inventory", callback)
```

## Notes

### 設計思想
- **既存システム活用**: 高機能なインベントリシステムを最大限活用
- **UI統一性**: ダンジョン内UIと地上部UIの一貫した操作感
- **レスポンシブ**: ダンジョン探索中の迅速なアイテム管理

### 関連システム
- **WindowSystem**: UI階層管理システム
- **InventoryManager**: インベントリ統一管理システム  
- **DungeonUIManager**: ダンジョンUI管理システム
- **パーティシステム**: キャラクター間アイテム移動

### テスト観点
- ダンジョン内でのUI表示性能
- メニュー遷移の一貫性
- アイテム操作の完全性
- エラー時の適切な処理

### 優先度の理由
ダンジョン探索において、アイテム確認・使用は基本的な機能であり、現在完全に利用不可能な状態のため中優先度として設定。インベントリシステム自体は完成しているため、比較的短期間で完成可能。
