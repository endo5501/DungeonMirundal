# コード重複解析によるリファクタリング計画

## 概要

`similarity-py`による意味的類似度分析の結果、複数のクラスで深刻なコード重複が検出されました。
本文書は、検出された重複の詳細分析と系統的なリファクタリング計画を記載しています。

## 重複検出結果サマリー

### 重要度レベル：緊急（100%重複）

| クラス | 重複メソッド | 類似度 | 影響度 |
|--------|-------------|--------|--------|
| MagicUI | show_spellbook_management 系統 | 100% | 高 |
| DungeonRendererPygame | 方向判定メソッド群 | 100% | 高 |
| DungeonRendererPygame | _move_left vs _move_right | 100% | 高 |
| StatusEffectManager | filter_effects_by_* 系統 | 100% | 中 |

### 重要度レベル：高（87-96%重複）

| クラス | 重複メソッド | 類似度 | 影響度 |
|--------|-------------|--------|--------|
| SaveManager | save_game vs _update_metadata | 87.61% | 高 |
| SaveManager | load_game vs import_save | 89.45% | 高 |
| SaveManager | get_save_path vs get_backup_path | 91.29% | 中 |
| DebugHelper | verify_esc_transition vs capture_transition_sequence | 89.92% | 中 |

## 詳細分析とリファクタリング戦略

### 1. MagicUI クラス（最優先）

**問題点：**
- `show_spellbook_management`, `show_slot_management`, `show_spell_learning`, `show_spell_casting`, `show_party_magic_overview` が100%同一実装
- すべて `pass` のみのスタブメソッド

**リファクタリング戦略：**
```python
# 現在の実装（重複）
def show_spellbook_management(self):
    pass

def show_slot_management(self):
    pass

# リファクタリング後
def _show_magic_interface(self, interface_type: str, **kwargs):
    """魔法インターフェース表示の共通実装"""
    # 共通ロジックを実装
    pass

def show_spellbook_management(self):
    return self._show_magic_interface("spellbook")

def show_slot_management(self):
    return self._show_magic_interface("slot")
```

**利益：**
- コード行数削減：約40行 → 15行
- 将来の実装時の一貫性保証

### 2. DungeonRendererPygame クラス（高優先）

**問題点：**
- 方向判定メソッド（`_get_opposite_direction`, `_get_left_direction`, `_get_right_direction`）が100%同一
- 移動メソッド（`_move_left`, `_move_right`）が100%同一
- UI描画メソッドで87-94%の重複

**リファクタリング戦略：**

#### 2.1 方向判定の統合
```python
# 現在の実装（重複）
def _get_opposite_direction(self):
    # 同一実装

def _get_left_direction(self):
    # 同一実装

# リファクタリング後
def _calculate_direction(self, direction_type: str):
    """方向計算の統一メソッド"""
    direction_map = {
        'opposite': lambda d: (d + 2) % 4,
        'left': lambda d: (d - 1) % 4,
        'right': lambda d: (d + 1) % 4
    }
    return direction_map[direction_type](self.current_direction)
```

#### 2.2 移動メソッドの統合
```python
# リファクタリング後
def _move_horizontal(self, direction: int):
    """水平移動の統一実装"""
    # 左右移動の共通ロジック
    pass

def _move_left(self):
    return self._move_horizontal(-1)

def _move_right(self):
    return self._move_horizontal(1)
```

**利益：**
- コード行数削減：約200行 → 80行
- バグ修正時の工数削減
- テスト容易性向上

### 3. SaveManager クラス（高優先）

**問題点：**
- ファイル操作ロジックで87-96%の重複
- セーブ・ロード処理の冗長性

**リファクタリング戦略：**

#### 3.1 ファイル操作の基底メソッド作成
```python
class SaveManager:
    def _execute_file_operation(self, operation_type: str, file_path: str, **kwargs):
        """ファイル操作の統一インターフェース"""
        try:
            # 共通エラーハンドリング
            # 共通ログ出力
            # 共通バリデーション
            
            operation_map = {
                'save': self._do_save_operation,
                'load': self._do_load_operation,
                'backup': self._do_backup_operation
            }
            return operation_map[operation_type](file_path, **kwargs)
            
        except Exception as e:
            # 統一エラーハンドリング
            self._handle_file_error(operation_type, file_path, e)
```

**利益：**
- エラーハンドリングの一貫性
- ファイル操作のテスト容易性向上
- ログ出力の統一

### 4. SettingsWindow クラス（中優先）

**問題点：**
- UI要素作成メソッドで88-100%の重複
- タブ管理ロジックの冗長性

**リファクタリング戦略：**

#### 4.1 UI要素生成の統合
```python
class SettingsWindow:
    def _create_ui_element(self, element_type: str, config: dict):
        """UI要素作成の統一メソッド"""
        element_factory = {
            'tab_container': self._create_container,
            'content_container': self._create_container,
            'button_container': self._create_container
        }
        return element_factory[element_type](config)
```

**利益：**
- UI生成ロジックの一貫性
- レイアウト変更時の影響範囲限定

## 実装順序とスケジュール

### Phase 1: 緊急対応（100%重複の解消）
1. **MagicUI** の重複メソッド統合（0.5日）
2. **DungeonRendererPygame** の方向判定メソッド統合（1日）
3. **テスト実行とデバッグ**（0.5日）

### Phase 2: 高重複度の解消（87-96%重複）
1. **SaveManager** のファイル操作統合（2日）
2. **DungeonRendererPygame** の移動メソッド統合（1日）
3. **テスト実行とデバッグ**（1日）

### Phase 3: 中重複度の解消（85-90%重複）
1. **SettingsWindow** のUI生成統合（1.5日）
2. **その他クラス** の重複解消（2日）
3. **総合テストとリグレッションテスト**（1日）

## リスク評価と対策

### リスク：高
- **DungeonRendererPygame**: ゲーム描画の核心部分、バグ発生時の影響甚大
- **対策**: 段階的リファクタリング、各ステップでのvisualテスト実行

### リスク：中
- **SaveManager**: セーブデータ破損の可能性
- **対策**: バックアップ機能の事前強化、テストデータでの検証

### リスク：低
- **MagicUI**: 未実装メソッドのリファクタリング
- **対策**: 実装時の一貫性確保のみ

## 成果指標

### 定量的指標
- コード行数削減：約400行 → 200行（50%削減目標）
- 重複度90%以上のメソッド：完全解消
- 重複度80%以上のメソッド：50%削減

### 定性的指標
- 保守性向上：バグ修正時の影響範囲限定
- テスト容易性向上：モック作成の簡素化
- 実装一貫性向上：新機能追加時のガイドライン確立

## 完了条件

1. `similarity-py ./src` で重複度90%以上のメソッドがゼロ
2. 既存テストがすべて通過
3. Visual regression testで画面表示に変化なし
4. セーブ・ロード機能の動作確認完了
5. リファクタリング後のパフォーマンス劣化なし

## 備考

- リファクタリング中は新機能開発を一時停止
- 各フェーズ完了時にcommit実行
- テスト失敗時は即座にrevert実行
- 本計画書は進捗に応じて随時更新