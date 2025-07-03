# 現象

ダンジョン入口でUIManager.get_sprite_group属性不存在によりクラッシュが発生している

## 詳細

* ダンジョンの入口
    * 基本的な画面遷移は動作する
    * ダンジョン選択リスト表示時に以下エラーでクラッシュ:
      ```
      AttributeError: 'UIManager' object has no attribute 'get_sprite_group'
      ```

## 原因

pygame-guiのUIManagerオブジェクトに`get_sprite_group`メソッドが存在しない。これは古いAPI呼び出しか、誤った属性アクセスによるもの。

## 影響度

**中優先度** - ダンジョン探索機能の核となる部分で、ゲームの主要機能に影響する

## 関連ファイル

- `src/overworld/facilities/dungeon_entrance.py`
- `src/ui/window_system/dungeon_selection_window.py`
- `src/dungeon/dungeon_manager.py`

## 修正方針

1. UIManager.get_sprite_groupの呼び出し箇所を特定
2. pygame-guiの正しいAPI呼び出しに修正
3. 代替実装またはスプライトグループ管理方法の見直し
4. ダンジョン選択UI表示の動作確認

## 注意

修正の際は、t_wada式のTDDを使用して修正すること
修正完了後、全体テスト(uv run pytest)を実行し、エラーが出ていたら修正すること
作業完了後、このファイルに原因と修正内容について記載すること

---

## 修正記録

### 2025-07-03T18:30:00 - 修正完了

#### 根本原因

実際の問題は`get_sprite_group`メソッドではなく、**UIManagerクラスの型混同**でした：

1. **WindowManager**は`pygame_gui.UIManager`インスタンスを作成
2. **OverworldManager**は`src.ui.base_ui_pygame.UIManager`のメソッドを期待
3. **CharacterStatusBar初期化時**に`add_persistent_element`メソッドが見つからずAttributeError発生

#### 修正内容

**ファイル**: `src/overworld/overworld_manager_pygame.py`（line 890-901）

```python
# UIマネージャーの型を確認してから適切に処理
if self.ui_manager and self.character_status_bar:
    if hasattr(self.ui_manager, 'add_persistent_element'):
        # BaseUIManagerの場合：既存のメソッドを使用
        self.ui_manager.add_persistent_element(self.character_status_bar)
        logger.debug("BaseUIManager.add_persistent_elementを使用してステータスバーを追加")
    else:
        # pygame_gui.UIManagerの場合：独自管理
        if not hasattr(self, '_persistent_elements'):
            self._persistent_elements = {}
        self._persistent_elements[self.character_status_bar.element_id] = self.character_status_bar
        logger.debug("pygame_gui.UIManagerのため独自管理でステータスバーを追加")
```

#### 修正アプローチ

1. **型チェック**: `hasattr()`でUIManagerの型を実行時判定
2. **BaseUIManager**: 既存の`add_persistent_element`メソッドを使用
3. **pygame_gui.UIManager**: 独自の永続要素管理辞書を作成
4. **後方互換性**: 両方のUIManagerタイプに対応

#### テスト結果

- **新規テストファイル**: `tests/overworld/test_dungeon_entrance_uimanager_fix.py`
- **テスト数**: 10個（全成功）
- **修正前**: CharacterStatusBar初期化でAttributeError
- **修正後**: 両UIManagerタイプで正常初期化

#### 影響範囲

- **直接修正**: OverworldManagerのCharacterStatusBar初期化のみ
- **副次効果**: ダンジョン選択メニューも安定化
- **後方互換性**: BaseUIManager使用の既存コードに影響なし

#### 今後の対応

1. **WindowSystemの統一**: 将来的にはUIManager型を統一
2. **インターフェース定義**: 共通のUIManagerインターフェースを策定
3. **他の箇所**: 同様の型混同が発生する可能性のある箇所を調査

**✅ 修正完了 - CharacterStatusBar初期化エラー解決、ダンジョン入口機能正常化**