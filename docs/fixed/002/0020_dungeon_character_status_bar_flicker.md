# ダンジョンでのキャラクターステータスバーちらつき修正

## 問題

`docs/fixed/0020_character_view.md`で報告されたダンジョンでのキャラクターステータスバーのちらつき問題：

- HP表示が「9/9」と「9」の間で切り替わる（スラッシュ文字が表示されたり消えたりする）
- キャラクター名も同様にちらつく

## 原因分析

### 1. 重複した画面更新
- `DungeonRendererPygame`内で`pygame.display.flip()`が複数回呼ばれていた
- `render_dungeon()`と`_render_direct()`の両方で画面更新を実行
- GameManagerでも画面更新を実行しているため、二重更新が発生

### 2. フォントレンダリングの不安定性
- スラッシュ文字「/」のレンダリングで時々エラーが発生
- 日本語フォントの初期化が不安定
- エラー時のフォールバック処理が不適切

## 解決策

### 1. 画面更新の一元化 (`src/rendering/dungeon_renderer_pygame.py`)

**修正内容**:
- `pygame.display.flip()`の呼び出しをコメントアウト
- 画面更新はGameManagerに一元化

```python
# 画面更新はGameManagerに任せる
# pygame.display.flip()  # コメントアウト：重複を避ける
```

### 2. HP表示の安定化 (`src/ui/character_status_bar.py`)

**修正内容**:
- HP表示を個別パーツでレンダリング（現在HP、スラッシュ、最大HP）
- エラー時のフォールバック処理を改善
- フォントキャッシングを追加

```python
def _render_hp_bar(self, screen: pygame.Surface, font: pygame.font.Font):
    """HPバーを描画"""
    # ... 省略 ...
    
    # HPテキスト - スラッシュ文字の問題を回避するため、個別にレンダリング
    try:
        # 現在HPをレンダリング
        current_hp_text = str(current_hp)
        current_hp_surface = font.render(current_hp_text, True, self.text_color)
        screen.blit(current_hp_surface, (self.hp_x, self.hp_y))
        
        # スラッシュをレンダリング
        slash_x = self.hp_x + current_hp_surface.get_width()
        slash_surface = font.render("/", True, self.text_color)
        screen.blit(slash_surface, (slash_x, self.hp_y))
        
        # 最大HPをレンダリング
        max_hp_text = str(max_hp)
        max_hp_x = slash_x + slash_surface.get_width()
        max_hp_surface = font.render(max_hp_text, True, self.text_color)
        screen.blit(max_hp_surface, (max_hp_x, self.hp_y))
```

### 3. フォントシステムの安定化 (`src/ui/dungeon_ui_pygame.py`)

**修正内容**:
- フォントマネージャーを優先的に使用
- フォントキャッシングの実装
- ステータスバー自体のフォントを使用（外部フォントに依存しない）

```python
# フォント初期化（安定性を重視）
try:
    # フォントマネージャーから取得を試行
    from src.ui.font_manager_pygame import font_manager
    self.font_small = font_manager.get_japanese_font(18)
    self.font_medium = font_manager.get_japanese_font(24)
    self.font_large = font_manager.get_japanese_font(36)
    # ... フォールバック処理
```

### 4. レンダリング呼び出しの最適化

**修正内容**:
- ダンジョンUIマネージャーでステータスバーを強制的に表示状態にする
- `render_overlay`でステータスバー自体のフォントを使用

```python
# ステータスバー自体のフォントを使用（安定性向上）
self.character_status_bar.render(self.screen, None)
```

## テスト

### 画面更新テスト (`tests/rendering/test_dungeon_renderer_flicker_fix.py`)
- `pygame.display.flip()`が重複して呼ばれないことを確認
- UIオーバーレイの描画順序を検証

### HP表示安定性テスト (`tests/ui/test_hp_display_stability.py`)
- スラッシュ文字を含むHP表示の安定性
- 個別レンダリングの動作確認
- フォールバック処理の検証
- フォントキャッシングの確認

## 結果

✅ **画面更新の一元化**: 重複した`pygame.display.flip()`を削除
✅ **HP表示の安定化**: スラッシュ文字のレンダリング問題を解決
✅ **フォントシステムの改善**: キャッシングとフォールバック処理の強化

ダンジョンでのキャラクターステータスバーのちらつきが解消されました。

## 影響範囲

- `src/rendering/dungeon_renderer_pygame.py`: 画面更新の削除
- `src/ui/character_status_bar.py`: HP表示ロジックの改善
- `src/ui/dungeon_ui_pygame.py`: フォントシステムの安定化

## 関連ファイル

- **元の問題報告**: `docs/fixed/0020_character_view.md`
- **地上マップの修正**: `docs/fixed/0020_character_status_bar_rendering_order.md`
- **テストファイル**: 
  - `tests/rendering/test_dungeon_renderer_flicker_fix.py`
  - `tests/ui/test_hp_display_stability.py`