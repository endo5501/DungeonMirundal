# UIMenu依存関係分析レポート

## 概要
TODO 0044のUIMenu段階的削除において、現在のUIMenu使用状況と依存関係を詳細に分析する。

## 主要な発見事項

### 1. 並行実装の存在
プロジェクトには**2つの並行するOverworldManager実装**が存在：

**A. src/overworld/overworld_manager.py** (Phase 3で移行済み)
- 1,417行の大規模実装
- WindowSystemに完全移行済み
- OverworldMainWindowによる9箇所のUIMenu統合完了
- テストスイート完備（31テスト、全合格）

**B. src/overworld/overworld_manager_pygame.py** (実際に使用中)
- 1,345行の実装
- game_manager.pyで実際にインポートされ使用
- UIMenuとMenuStackManagerに依存
- レガシーUIシステムを使用

### 2. UIMenu依存コンポーネント

#### 活用中のコンポーネント
1. **overworld_manager_pygame.py**
   - UIMenu直接使用: 4箇所 (main_menu, settings_menu, save_slot_menu, load_slot_menu)
   - MenuStackManager使用: 統一メニュー管理用

2. **src/ui/menu_stack_manager.py**
   - UIMenuベースのスタック管理システム
   - 427行の実装
   - 5つの主要機能：push_menu, pop_menu, handle_escape_key, navigation管理

3. **src/overworld/base_facility.py**
   - MenuStackManagerを初期化・使用
   - DialogTemplateとの連携

#### WindowSystem移行済み
1. **施設ファイル群** (Phase 2完了)
   - shop.py, temple.py, inn.py: UIMenu削除済み、コメント記載
   - WindowSystemベースの*ServiceWindow実装に移行

2. **overworld_manager.py** (Phase 3完了)
   - OverworldMainWindowによる統合実装

### 3. UIMenu使用パターン分析

#### レガシーパターン（削除対象）
```python
# Pygame版で見られるパターン
self.main_menu = UIMenu("overworld_main", "地上マップ")
self.main_menu.add_menu_item("冒険者ギルド", self._enter_guild)
self.ui_manager.add_menu(self.main_menu)
```

#### WindowSystemパターン（目標）
```python
# 既に移行済みパターン
menu_config = self._create_main_menu_config()
self.main_window = OverworldMainWindow('overworld_main', menu_config)
self.window_manager.show_window(self.main_window)
```

## Phase 4移行戦略

### ステップ1: Pygame版OverworldManager統合
**優先度: 最高**

実際に使用されているPygame版をWindowSystemに移行するか、
既存のoverworld_manager.pyとの統合を行う

**オプション案:**
- A. overworld_manager_pygame.pyをベースにWindowSystem機能を追加
- B. overworld_manager.pyの実装をgame_manager.pyで使用するよう変更
- C. 両実装を統合した新しい実装を作成

### ステップ2: MenuStackManager代替
**優先度: 高**

MenuStackManagerの機能をWindowManagerに置き換え：
- push_menu → window_manager.show_window
- pop_menu → window_manager.go_back  
- handle_escape_key → Window.handle_escape

### ステップ3: 段階的UIMenu削除
**優先度: 中**

1. レガシーUIMenu使用箇所を特定
2. WindowSystem実装での置き換え
3. UIMenuクラス本体の削除

## 推奨アクション

### 即座に実行すべき
1. overworld_manager.pyとoverworld_manager_pygame.pyの統合戦略決定
2. 現在使用中のPygame版のWindowSystem移行計画策定

### Phase 4での実行
1. Pygame版OverworldManagerのWindowSystem移行
2. MenuStackManagerからWindowManagerへの移行
3. base_facility.pyのWindowSystem完全移行

## リスク評価

**高リスク:**
- 並行実装による混乱とメンテナンス複雑性
- 実際の使用実装（Pygame版）が未移行

**中リスク:**
- MenuStackManagerに依存するコンポーネントの移行工数

**低リスク:**
- 既存のWindowSystem実装は安定動作確認済み

## 結論

Phase 3で移行したoverworld_manager.pyは優秀な実装であるが、
実際に使用されているのはoverworld_manager_pygame.pyである。

**Phase 4の焦点は、実際に使用されている実装のWindowSystem移行**に
置くべきである。