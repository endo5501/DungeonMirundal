# 0032: WindowSystem移行 - 高優先度作業

## 目的
WindowSystemの新旧システム混在問題を解決するため、高優先度のUIコンポーネントをUIMenuから新WindowSystemへ移行する。

## 経緯
- 2025年6月29日: `docs/todos/0031_change_window_system.md`調査で新旧システム混在が判明
- `docs/window_system.md`では移行完了とされているが、実際は18ファイルで旧UIMenuシステムが残存
- 緊急インポートエラー修正後の次ステップとして高優先度移行を実施

## 対象ファイル（高優先度）

### 1. src/ui/help_ui.py → HelpWindow
**現状**: UIMenuベースのヘルプシステム
**問題**: 
- 現在インポートエラー状態（緊急修正後に正常化予定）
- 4箇所でUIMenu使用（248, 287行目等）

**移行作業**:
- 既存`HelpWindow`クラス（`src/ui/windows/help_window.py`）への置き換え
- `HelpContentManager`, `HelpDisplayManager`等の活用
- t-wada式TDDで開発
- カテゴリ別ヘルプ、コンテキストヘルプ機能の統合
- Fowler式リファクタリングを実施

### 2. src/ui/magic_ui.py → MagicWindow
**現状**: UIMenuベースの魔法システム
**問題**:
- 現在インポートエラー状態（緊急修正後に正常化予定）
- 8箇所でUIMenu使用（53, 101, 140行目等）

**移行作業**:
- 既存`MagicWindow`クラス（`src/ui/windows/magic_window.py`）への置き換え
- `MagicDisplayManager`, `SpellSlotManager`等の活用
- t-wada式TDDで開発
- 魔法スロット管理、パーティ魔法表示機能の統合
- Fowler式リファクタリングを実施

### 3. src/ui/status_effects_ui.py → StatusEffectsWindow
**現状**: UIMenuベースのステータス効果システム
**問題**:
- 3箇所でUIMenu使用（36, 72, 154行目）
- 新WindowSystemとの混在

**移行作業**:
- 既存`StatusEffectsWindow`クラス（`src/ui/windows/status_effects_window.py`）への置き換え
- `StatusEffectManager`, `StatusDisplayManager`等の活用
- t-wada式TDDで開発
- パーティ効果表示、効果除去機能の統合
- Fowler式リファクタリングを実施

### 4. src/ui/settings_ui.py → SettingsWindow
**現状**: UIMenuベースの設定システム
**特記事項**: 新`SettingsWindow`は既に実装済み
**問題**:
- 7箇所でUIMenu使用（135, 210, 282, 340, 391, 450, 512行目）

**移行作業**:
- 既存`SettingsWindow`クラス（`src/ui/windows/settings_window.py`）への置き換え
- t-wada式TDDで開発
- 既存実装の活用により作業簡素化

## 技術仕様

### 移行パターン
```python
# 変更前（UIMenu）
menu = UIMenu("menu_id", "タイトル")
menu.add_element(...)

# 変更後（WindowSystem）
window = WindowManager.instance.create_window(
    SpecificWindow, 
    window_id="menu_id",
    title="タイトル"
)
WindowManager.instance.show_window(window)
```

### 共通移行手順
1. **ファイル構造調査**: 既存UIMenu使用箇所の特定
2. **新Windowクラス確認**: 対応する新WindowSystemクラスの仕様確認
3. **段階的置き換え**: UIMenuインスタンス作成部分から順次置き換え(t-wada式TDD)
4. **リファクタリング**: Fowler式リファクタリング
4. **テスト実行**: 移行後の動作確認
5. **不要コード削除**: 旧UIMenu関連コードの削除

### テスト要件
- 各Windowクラスの既存テストが通過すること
- ~~新旧システム混在期間中の整合性確保~~ 新システムの処理を優先
- リグレッションテストの実施

## 期待される効果

### 問題解決
- フォーカス管理の統一化
- メニュー階層の一貫性確保
- 操作体験の改善

### 開発効率
- デバッグ性の向上
- 保守性の改善
- 新機能追加の容易化

## リスク・制約事項

### 技術的リスク
- 移行期間中の新旧システム混在
- 既存機能の一時的不安定化
- テストケースの修正必要性

### 軽減策
- 段階的移行による影響範囲限定
- 各段階での十分なテスト実施
- ~~ロールバック計画の準備~~ ロールバックについては考慮不要

## 作業スケジュール
- **期間**: 1週間以内
- **順序**: help_ui → magic_ui → status_effects_ui → settings_ui
- **テスト**: 各ファイル移行後に即時実施

## 関連ドキュメント
- `docs/todos/0031_change_window_system.md`: 調査結果
- `docs/window_system.md`: WindowSystem設計書
- `docs/todos/0033_window_system_migration_medium_priority.md`: 中優先度移行計画
- `docs/todos/0034_window_system_migration_low_priority.md`: 低優先度移行計画

## 完了条件

### 新WindowSystemクラス実装 ✅ **完了**
- [x] ✅ HelpWindow実装済み (`src/ui/window_system/help_window.py`)
- [x] ✅ MagicWindow実装済み (`src/ui/window_system/magic_window.py`)
- [x] ✅ StatusEffectsWindow実装済み (`src/ui/window_system/status_effects_window.py`)
- [x] ✅ SettingsWindow実装済み (`src/ui/window_system/settings_window.py`)

### UIMenuからWindowSystemへの実際の移行 🔄 **未完了**
- [ ] 🔄 help_ui.pyの完全移行（UIMenuベース → HelpWindow使用）
- [ ] 🔄 magic_ui.pyの完全移行（UIMenuベース → MagicWindow使用）
- [ ] 🔄 status_effects_ui.pyの完全移行（UIMenuベース → StatusEffectsWindow使用）  
- [ ] 🔄 settings_ui.pyの完全移行（UIMenuベース → SettingsWindow使用）
- [ ] 🔄 移行後の動作確認完了
- [ ] 🔄 テスト整合性確保
- [ ] 🔄 レガシーコード削除

## 現在の状況（2025-06-29確認）

### 実装状況
- ✅ **新WindowSystemクラス**: 全4クラスが完全実装済み
- 🔄 **実際の移行作業**: 旧UIMenuベースファイルが依然として使用中
- 🔄 **統合作業**: 新クラスへの切り替え作業が未実施

### 対象ファイルの現状
1. **src/ui/help_ui.py**: UIMenuベース実装（line 248でUIMenu使用）
2. **src/ui/magic_ui.py**: UIMenuベース実装（multiple UIMenu instances）
3. **src/ui/status_effects_ui.py**: UIMenuベース実装（line 36等でUIMenu使用）
4. **src/ui/settings_ui.py**: UIMenuベース実装（135, 210等でUIMenu使用）

### 次回アクション
新WindowSystemクラスは実装完了しているため、各UIファイルの実際の移行作業（UIMenu使用箇所を新WindowSystemクラス呼び出しに変更）を実施する必要があります。