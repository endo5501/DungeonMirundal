# 現象

画面下部に @docs/change_spec.md で対応されたはずのパーティのキャラクターの画像領域や名前が表示されない。

## 原因分析 (2025-06-25)

**根本原因**：
- ダンジョンモードで`DungeonRendererPygame`に`DungeonUIManagerPygame`が設定されていなかった
- そのため`dungeon_ui_manager.render_overlay()`が呼ばれず、キャラクターステータスバーが描画されなかった

**詳細調査結果**：
1. 地上部では`OverworldManager`で正常にキャラクターステータスバーが実装・描画されている
2. ダンジョン部では`DungeonRendererPygame._render_basic_ui()`内で`dungeon_ui_manager`の存在チェックをしているが、実際には`None`のため描画処理がスキップされていた
3. `_setup_transition_system()`メソッドで`DungeonUIManagerPygame`のインスタンス作成と設定が欠落していた

## 修正内容 (2025-06-25)

### ファイル: `/home/satorue/Dungeon/src/core/game_manager.py`

**1. インポート追加**
```python
from src.ui.dungeon_ui_pygame import create_pygame_dungeon_ui
```

**2. `_setup_transition_system()`メソッド修正**
```python
# ダンジョンUIマネージャーの初期化と設定
dungeon_ui_manager = create_pygame_dungeon_ui(self.screen)
self.dungeon_renderer.set_dungeon_ui_manager(dungeon_ui_manager)
```

**3. `set_current_party()`メソッド修正**
```python
# ダンジョンUIマネージャーにもパーティを設定
if hasattr(self.dungeon_renderer, 'dungeon_ui_manager') and self.dungeon_renderer.dungeon_ui_manager:
    self.dungeon_renderer.dungeon_ui_manager.set_party(party)
```

## 修正結果 (2025-06-25)

**テスト結果**：
- ✅ `test_character_status_bar.py`の11個のテストが全て通過
- ✅ ゲーム起動時のログで`DungeonUIManagerPygame`の正常な初期化を確認
- ✅ `ダンジョン用キャラクターステータスバーを初期化しました`ログ出力確認
- ✅ `ダンジョンUIマネージャーを設定しました`ログ出力確認

**期待される結果**：
- ダンジョン内でキャラクターのHP/MP、名前、状態が画面下部のステータスバーに表示される
- パーティの変更が即座にステータスバーに反映される
- 6つのキャラクタースロットがダンジョン画面下部に正常に表示される

## 追加修正 (2025-06-25 #2)

**新たに判明した問題**：
- `CharacterStatusBar`が`UIElement`を継承しており、デフォルトで`state = UIState.HIDDEN`で初期化される
- `render`メソッドで`state != UIState.VISIBLE`のチェックがあり、表示されない

**修正内容**：
### ファイル: `/home/satorue/Dungeon/src/ui/character_status_bar.py`

`CharacterStatusBar.__init__()`メソッドに以下を追加：
```python
# 自動的に表示状態にする
self.show()
```

これにより、初期化時に自動的に`state = UIState.VISIBLE`となり、描画されるようになりました。

## 追加修正 (2025-06-25 #3) - ダンジョンでのEmpty表示問題

**問題**：
- 地上部では正常に表示されるが、ダンジョンに入ると全て「Empty」と表示される

**原因**：
- パーティの読み込み時に直接代入（`self.current_party = party`）していたため、`set_current_party()`メソッドが呼ばれていない
- そのため、ダンジョンUIマネージャーにパーティ情報が伝達されていない

**修正内容**：
### ファイル: `/home/satorue/Dungeon/src/core/game_manager.py`

**1. `_try_auto_load()`メソッド（796行目）**：
```python
# 修正前: self.current_party = save_data.party
# 修正後: self.set_current_party(save_data.party)
```

**2. `load_game_state()`メソッド（597-598行目）**：
```python
# 修正前: self.current_party = Party.from_dict(party_data)
# 修正後: 
party = Party.from_dict(party_data)
self.set_current_party(party)
```

**3. `_setup_transition_system()`メソッドに追加（395-397行目）**：
```python
# 現在のパーティが存在する場合は設定
if self.current_party:
    dungeon_ui_manager.set_party(self.current_party)
```

## ステータス

**解決済み** ✅

修正により、地上部・ダンジョンの両方でキャラクターステータスバーが正常に表示され、ダンジョンでもパーティメンバーの情報が正しく表示されるようになりました。

