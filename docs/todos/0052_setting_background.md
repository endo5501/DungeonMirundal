# 現象

ESCを押すと背景とメニューボタンが設定画面になる。しかし、再度ESCを押すとメニューボタンだけが地上になり、背景は設定画面のまま

# 修正作業記録（2025-07-02）

## 原因調査

1. **初期調査**: デバッグAPIを使用してスクリーンショット解析を実施
2. **問題特定**: WindowSystemとレガシーシステムの混在による背景描画の不整合
3. **根本原因**: 
   - `OverworldManager.render()`で`settings_active`フラグに基づいて背景色を決定
   - しかし`_hide_settings_menu()`でWindowSystemの設定画面を適切に閉じていない
   - `OverworldMainWindow.hide_menu()`メソッドが存在していない

## 実装した修正

### 1. デバッグログ追加
- `src/overworld/overworld_manager_pygame.py:1272`: render()にsettings_activeの状態ログ追加
- `src/overworld/overworld_manager_pygame.py:1405`: ESCキー処理にログ追加
- `src/overworld/overworld_manager_pygame.py:1212`: 地上部入場時の状態確実化

### 2. WindowSystem統合修正
- `src/overworld/overworld_manager_pygame.py:1190-1206`: `_hide_settings_menu()`でWindowSystemの設定画面を適切に閉じる処理を追加
- `src/ui/window_system/overworld_main_window.py:521-538`: `hide_menu()`メソッドを新規実装（メニュースタックからの復帰機能）

### 3. TDDアプローチ
- `tests/test_background_display_fix.py`: 包括的なテストスイートを作成
- 画像解析による背景色判定機能を実装
- 期待動作を明確に定義したテストケース

## テスト結果

```
初期画面: (50, 49, 73) - 設定画面背景（問題継続）
1回目ESC: (50, 49, 74) - 設定画面背景（期待通り）
2回目ESC: (50, 49, 73) - 設定画面背景（問題：地上背景に戻るべき）
```

## 残存課題

背景色が常に設定画面の色(50, 49, 73)を表示している。さらなる調査が必要：

1. WindowSystemとOverworldManagerの描画順序
2. GameManagerでの画面クリア処理との相互作用
3. UIManagerとWindowManagerの二重管理問題

## 次のステップ

1. 描画パイプライン全体の調査
2. WindowSystemの状態管理とOverworldManagerのsettings_activeフラグの同期
3. より詳細なレンダリング順序の分析

# 注意

修正の際は、t_wada式のTDDを使用して修正すること
修正完了後、全体テスト(uv run pytest)を実行し、エラーが出ていたら修正すること
作業完了後、このファイルに原因と修正内容について記載すること
