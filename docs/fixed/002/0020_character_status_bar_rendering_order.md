# キャラクターステータスバー描画順序修正

## 問題

`docs/todos/0020_character_view.md`で報告された以下の問題を修正：

1. **地上マップでの問題**: キャラクターステータスバーが地上マップの背景やメニューの裏に表示される
2. **ダンジョンでの問題**: キャラクターステータスバーの描画がちらつく

## 原因分析

### 地上マップでの問題
- UIManagerの描画順序で`elements`が最初に描画され、その後`menus`が描画される
- キャラクターステータスバーが`elements`に追加されているため、メニューに隠れる

### ダンジョンでの問題
- ダンジョンUIマネージャーが独自の描画システムを使用
- `render_overlay`で小地図とステータスバーの描画順序が不安定

## 解決策

### 1. UIManagerの拡張 (`src/ui/base_ui_pygame.py`)

**新機能追加**:
- `persistent_elements`: 常に最前面に表示される要素用のコンテナ
- `add_persistent_element()`: 永続要素を追加するメソッド
- `render()`の描画順序変更: 永続要素を最後に描画

**修正内容**:
```python
def render(self):
    """全UI要素を描画"""
    # 通常要素の描画
    for element in self.elements.values():
        element.render(self.screen, self.default_font)
    
    # メニューの描画
    for menu in self.menus.values():
        menu.render(self.screen, self.default_font)
    
    # ダイアログの描画
    for dialog in self.dialogs.values():
        dialog.render(self.screen, self.default_font)
    
    # pygame-gui要素の描画
    self.pygame_gui_manager.draw_ui(self.screen)
    
    # 永続要素の描画（最前面）
    for element in self.persistent_elements.values():
        element.render(self.screen, self.default_font)
```

### 2. 地上マップでの修正 (`src/overworld/overworld_manager_pygame.py`)

**変更内容**:
- キャラクターステータスバーを`persistent_elements`に追加
- 常に最前面に表示されるよう修正

```python
# UIマネージャーに追加（最前面に表示される永続要素として）
if self.ui_manager and self.character_status_bar:
    self.ui_manager.add_persistent_element(self.character_status_bar)
```

### 3. ダンジョンでの修正 (`src/ui/dungeon_ui_pygame.py`)

**修正内容**:
1. **描画順序の安定化**: `render_overlay()`で小地図を先に、ステータスバーを後に描画
2. **表示状態の保証**: ステータスバー初期化時に強制的に表示状態にする

```python
def render_overlay(self):
    """オーバーレイUI（ステータスバー等）を描画"""
    # 小地図を最初に描画（背景層）
    if self.small_map_ui:
        # ... 小地図描画処理
    
    # キャラクターステータスバーを最後に描画（最前面層）
    if self.character_status_bar:
        self.character_status_bar.render(self.screen, self.font_medium)
```

## テスト

### 地上マップテスト (`tests/ui/test_character_status_bar_rendering_fix.py`)
- UIManagerの`persistent_elements`機能
- 描画順序の検証
- OverworldManagerでの`persistent_element`使用確認

### ダンジョンテスト (`tests/ui/test_dungeon_character_status_bar_fix.py`)
- ダンジョンUIマネージャーの初期化
- パーティ設定の確認
- `render_overlay`の描画順序と例外処理
- ステータスバーの強制表示状態

## 結果

✅ **地上マップ**: キャラクターステータスバーがメニューの前面に正しく表示される
✅ **ダンジョン**: ステータスバーのちらつきが解消され、安定した描画が実現

## 影響範囲

- `src/ui/base_ui_pygame.py`: UIManagerの描画システム拡張
- `src/overworld/overworld_manager_pygame.py`: ステータスバーの登録方法変更
- `src/ui/dungeon_ui_pygame.py`: 描画順序とステータスバー初期化の改善

## 関連ファイル

- **問題報告**: `docs/todos/0020_character_view.md`
- **テストファイル**: 
  - `tests/ui/test_character_status_bar_rendering_fix.py`
  - `tests/ui/test_dungeon_character_status_bar_fix.py`
- **修正ファイル**: 
  - `src/ui/base_ui_pygame.py`
  - `src/overworld/overworld_manager_pygame.py` 
  - `src/ui/dungeon_ui_pygame.py`