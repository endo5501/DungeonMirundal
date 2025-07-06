# Phase 5 セーブ・ロード機能の問題と改善点

## 問題の概要

Phase 5のセーブ・ロード統合テスト中に発見された問題をまとめています。

## 🔴 緊急度：高

### 1. パーティ名の保存・復元問題

**問題**:
- セーブ時にパーティ名が "SimpleTestParty" として設定されているが、ロード時に "New Party" として復元される
- SaveManagerの`save_game`メソッドでパーティ名が正しく処理されていない可能性

**発生箇所**:
- `src/core/save_manager.py` の `save_game` メソッド
- `src/character/party.py` の `to_dict` / `from_dict` メソッド

**テストケース**:
```python
# tests/test_phase5_simple_save.py:67
self.assertEqual(loaded_save.party.name, "SimpleTestParty")
# 実際の結果: "New Party"
# 期待値: "SimpleTestParty"
```

**エラーログ**:
```
2025-07-05 22:17:21 - dungeon - INFO - ゲームを保存しました: スロット 1, パーティ: New Party
2025-07-05 22:17:21 - dungeon - INFO - ゲームをロードしました: スロット 1, パーティ: New Party
```

**調査が必要な点**:
1. `Party.to_dict()` でパーティ名が正しくシリアライズされているか
2. `Party.from_dict()` でパーティ名が正しくデシリアライズされているか
3. `SaveSlot` の `party_name` と `Party` の `name` の整合性
4. セーブファイル（JSON）内でパーティ名がどう保存されているか

## 🟡 緊急度：中

### 2. セーブデータ構造の不整合

**問題**:
- `GameSave` のコンストラクタ署名とテストコードの不一致
- `total_playtime` などのパラメータが `SaveSlot` と `GameSave` で重複している

**解決済み**:
テスト中に修正済みだが、設計の見直しが必要

### 3. セーブ時のフォーマットエラー

**問題**:
- セーブ処理中に `Unknown format code 'd' for object of type 'str'` エラーが発生
- 文字列フォーマットでの型の不一致

**発生箇所**:
- SaveManagerのどこかでstring formatが正しく処理されていない

## 🟢 緊急度：低

### 4. Phase 5特有データの保存確認

**状況**:
- トラップ状態、宝箱開封状態、ボス戦進行状況などのPhase 5特有のデータ
- 基本的な保存・復元は動作するが、完全な統合テストが必要

**必要な作業**:
1. トラップシステムの`opened_treasures`辞書の永続化
2. ボス戦の`active_encounters`の状態保存
3. キャラクターステータス効果の保存・復元
4. ダンジョン進行状況の詳細保存

## 修正計画

### Phase 1: 緊急修正
1. パーティ名の保存・復元問題の根本原因調査
2. `Party.to_dict()` と `Party.from_dict()` の詳細確認
3. セーブファイルの実際の内容確認

### Phase 2: 統合改善
1. `GameSave` と `SaveSlot` の責任分離の明確化
2. Phase 5システムの状態管理インターフェース設計
3. セーブデータのバージョン管理体制

### Phase 3: テスト充実
1. より包括的な統合テストの作成
2. セーブデータ破損時の復旧テスト強化
3. 大容量データの性能テスト

## 関連ファイル

- `src/core/save_manager.py` - セーブ・ロード処理
- `src/character/party.py` - パーティシリアライゼーション
- `tests/test_phase5_simple_save.py` - 問題が発生したテスト
- `tests/test_phase5_save_integration.py` - より詳細な統合テスト

## 作業優先度

1. **最優先**: パーティ名保存問題の修正
2. **高**: セーブデータ構造の統一
3. **中**: Phase 5特有データの完全保存対応
4. **低**: 性能最適化とエラーハンドリング強化

---

**作成日**: 2025-07-05  
**担当**: Phase 5開発チーム  
**ステータス**: 調査中