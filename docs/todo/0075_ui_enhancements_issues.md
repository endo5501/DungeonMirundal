# UI/UX拡張機能の問題と修正項目

## 問題の概要

Phase 5のUI/UX最終調整中に発見された問題をまとめています。

## 🔴 緊急度：高

### 1. カスタム設定の名前設定問題

**問題**:
- `create_custom_difficulty`でカスタム設定を作成する際、名前が正しく "カスタム" に設定されない
- `create_custom_quality`でも同様の問題が発生

**発生箇所**:
- `src/dungeon/quality_settings.py` の `create_custom_difficulty` メソッド
- `src/dungeon/quality_settings.py` の `create_custom_quality` メソッド

**テストケース**:
```python
# tests/test_ui_enhancements.py:267
self.assertEqual(custom.name, "カスタム")
# 実際の結果: "通常"
# 期待値: "カスタム"
```

**原因**:
基本設定の`__dict__`をコピーする際に、`name`や`preset_name`も上書きされている

**修正方法**:
属性設定の順序を調整し、カスタム値を最後に設定する

## 🟡 緊急度：中

### 2. UI設定辞書のキー不一致

**問題**:
- `DungeonUIEnhancer`の`ui_settings`に`ui_animation_speed`キーが存在しない
- `QualitySettings`との統合でキーエラーが発生

**発生箇所**:
- `src/dungeon/ui_enhancements.py` の `ui_settings` 初期化
- `tests/test_ui_enhancements.py` の統合テスト

**エラーメッセージ**:
```
KeyError: 'ui_animation_speed'
```

**修正方法**:
1. `DungeonUIEnhancer`の`ui_settings`に不足しているキーを追加
2. 統合時のキーマッピングを見直し

## 🟢 緊急度：低

### 3. テストカバレッジの向上

**状況**:
- 基本機能のテストは通過している（20/23テストが成功）
- エラーハンドリング、境界値テストの追加が必要

**必要な作業**:
1. カスタム設定の境界値テスト
2. 無効な値での設定テスト
3. ファイル保存・読み込みエラーのテスト

## 修正計画

### Phase 1: 緊急修正
1. カスタム設定の名前設定問題の修正
2. UI設定辞書のキー追加・統合修正

### Phase 2: 機能強化
1. 設定値のバリデーション強化
2. エラーハンドリングの改善
3. 設定ファイルの互換性確保

### Phase 3: テスト充実
1. 境界値テストの追加
2. 統合テストの拡充
3. パフォーマンステストの追加

## 即座に修正可能な項目

### カスタム設定名前問題の修正案

```python
# 修正前
for field_name, field_value in base_settings.__dict__.items():
    if hasattr(custom_settings, field_name):
        setattr(custom_settings, field_name, field_value)

# 修正後  
for field_name, field_value in base_settings.__dict__.items():
    if hasattr(custom_settings, field_name) and field_name not in ['name', 'preset_name']:
        setattr(custom_settings, field_name, field_value)
```

### UI設定辞書の修正案

```python
# DungeonUIEnhancer.__init__の ui_settings に追加
self.ui_settings = {
    # 既存の設定...
    "ui_animation_speed": 1.0,  # 追加
    "ui_response_delay": 0.0,   # 追加
    "notification_duration": 3.0, # 追加
}
```

## 関連ファイル

- `src/dungeon/quality_settings.py` - カスタム設定作成ロジック
- `src/dungeon/ui_enhancements.py` - UI設定管理
- `tests/test_ui_enhancements.py` - 失敗したテスト

## 作業優先度

1. **最優先**: カスタム設定の名前設定修正
2. **高**: UI設定辞書の統合修正
3. **中**: エラーハンドリング強化
4. **低**: テストカバレッジ向上

---

**作成日**: 2025-07-05  
**担当**: Phase 5 UI/UXチーム  
**ステータス**: 修正準備中