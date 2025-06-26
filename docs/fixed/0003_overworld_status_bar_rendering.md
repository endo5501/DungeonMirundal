# 現象

地上マップでキャラクターの画像や名前が地上マップの背景に隠れて表示されない。

## 原因分析 (2025-06-26)

**根本原因**：
- キャラクターステータスバーがUIマネージャーのelementsに追加されていなかった
- `OverworldManager.render()`メソッド内で直接描画していたが、背景の後に描画されるため見えなかった

**詳細調査結果**：
1. `_initialize_character_status_bar()`でステータスバーは作成されていた
2. しかし、UIマネージャーの管理下に追加されていなかった（`ui_manager.add_element()`が呼ばれていない）
3. `render()`メソッド内で直接`character_status_bar.render()`を呼んでいたが、これは背景描画の後であり、UIマネージャーの描画前だった
4. 結果として、UIマネージャーが管理する他のUI要素（メニューなど）に隠れてしまっていた

## 修正内容 (2025-06-26)

### ファイル: `/home/satorue/Dungeon/src/overworld/overworld_manager_pygame.py`

**1. `_initialize_character_status_bar()`メソッド修正（573-595行目）**
```python
# UIマネージャーに追加（常に表示される要素として）
if self.ui_manager and self.character_status_bar:
    self.ui_manager.add_element(self.character_status_bar)
```

**2. `render()`メソッド修正（1053-1054行目）**
```python
# キャラクターステータスバーの描画はUIマネージャーが行うため、ここでは描画しない
# （UIマネージャーのelementsに追加済み）
```

## 修正結果 (2025-06-26)

**テスト結果**：
- ✅ `test_character_status_bar_fix.py`の3個のテストが全て通過
- ✅ キャラクターステータスバーがUIマネージャーのelementsに正しく追加される
- ✅ UIマネージャーによって適切な順序で描画される
- ✅ 背景やメニューに隠れることなく、常に表示される

**修正の詳細**：
1. キャラクターステータスバーをUIマネージャーの管理下に置くことで、適切なレンダリング順序を保証
2. 二重描画を防ぐため、`OverworldManager.render()`からの直接描画を削除
3. UIマネージャーが他のUI要素と一緒に適切な順序で描画

## ステータス

**解決済み** ✅

修正により、地上マップでキャラクターステータスバーが正常に表示されるようになりました。キャラクターの画像、名前、HP/MPバーが背景やメニューに隠れることなく、画面下部に常に表示されます。