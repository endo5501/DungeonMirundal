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

（修正時に記録）