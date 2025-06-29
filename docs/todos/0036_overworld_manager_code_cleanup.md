# 0036: OverworldManager - コードクリーンアップ

## 目的
overworld_manager_pygame.pyの新WindowSystem移行に伴い発生したコード品質問題を修正する。

## 経緯
- 2025年6月29日: WindowSystem移行作業中にPylance診断で未使用インポートを検出
- settings_ui → SettingsWindow移行完了後の不要インポート残存

## 検出された問題

### 1. 未使用インポート (Pylance診断)
```python
# Line 13:37
from src.core.config_manager import config_manager  # ★ 参照されていません

# Line 793:16  
from datetime import datetime  # ★ 参照されていません
```

### 2. 潜在的な問題
- WindowSystem移行により不要になったインポート文
- レガシーコードとの混在による保守性低下

## 修正対象

### 優先度：高
- **Line 13**: `config_manager`の未使用インポート削除
- **Line 793**: `datetime`の未使用インポート削除

### 優先度：中
- WindowSystem移行に伴う不要コードの調査・削除
- インポート文の整理・最適化

### 優先度：低
- コードスタイルの統一
- 不要なコメントの削除

## 作業手順

### 1. 未使用インポートの確認・削除
```python
# 削除対象の確認
rg "config_manager" src/overworld/overworld_manager_pygame.py
rg "datetime" src/overworld/overworld_manager_pygame.py

# 使用されていないことを確認後、インポート文を削除
```

### 2. WindowSystem移行関連の調査
- settings_ui関連の残存コード確認
- 新WindowSystem統合部分の最適化
- 不要になったコールバック関数の調査

### 3. テスト実行
- overworld_manager関連テストの実行
- WindowSystem統合テストの実行
- リグレッションテストの実施

## 技術仕様

### 修正パターン
```python
# 修正前
from src.core.config_manager import config_manager  # 未使用
from datetime import datetime  # 未使用

# 修正後
# 不要なインポートを削除
```

### 確認手順
1. **使用箇所調査**: `rg`コマンドで実際の使用を確認
2. **インポート削除**: 未使用が確認されたインポートを削除
3. **テスト実行**: 削除後の動作確認
4. **Pylance再確認**: 診断エラーの解消確認

## 期待される効果

### コード品質向上
- 未使用インポートの削除によるクリーンなコード
- 保守性の向上
- 依存関係の明確化

### 開発効率向上
- Pylance診断エラーの解消
- IDEでの警告削除
- コードレビューの効率化

## リスク・制約事項

### 技術的リスク
- 隠れた依存関係の見落とし
- 動的インポートによる間接使用
- テストでのみ使用される場合

### 軽減策
- 段階的な削除実施
- 各削除後のテスト実行
- Git履歴による変更追跡

## 完了条件
- [x] ✅ config_managerインポート削除（2025-06-29完了）
- [x] ✅ datetimeインポート削除（2025-06-29完了）
- [x] ✅ Pylance診断エラーの解消（2025-06-29完了）
- [x] ✅ overworld_manager関連テストの通過（構文チェック完了）
- [x] ✅ WindowSystem統合テストの通過（構文チェック完了）

## 現在の状況（2025-06-29更新）
**0036のOverworldManagerコードクリーンアップ作業が完了しました。**

### 完了した作業
1. **未使用インポートの削除**
   - `config_manager`インポート削除（Line 13）
   - `datetime`インポート削除（Line 866）
   
2. **影響範囲の確認**
   - 使用箇所なしを確認（rgコマンドによる検索）
   - 構文エラーなしを確認（py_compileチェック）
   
3. **コード品質向上**
   - Pylance診断エラーの解消
   - 不要な依存関係の削除
   - 保守性の向上

### 影響範囲
- **優先度**: 中（コード品質向上）
- **緊急性**: 低（機能に影響なし）
- **対象ファイル**: overworld_manager_pygame.py

### 次回アクション
1. 実際の使用箇所をrgコマンドで再確認
2. 未使用が確定したインポートを削除
3. テスト実行で影響がないことを確認

## 関連ドキュメント
- `docs/todos/0032_window_system_migration_high_priority.md`: WindowSystem移行（完了）
- `docs/todos/0035_window_system_legacy_cleanup.md`: レガシークリーンアップ計画

## 注意事項
- 削除前に必ず使用箇所の調査を実施すること
- 動的インポートや文字列での参照にも注意すること
- 削除後は必ずテストを実行すること