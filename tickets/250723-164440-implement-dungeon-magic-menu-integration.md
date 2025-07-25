---
priority: 2
tags: ["ui", "dungeon", "magic", "menu", "feature", "integration"]
description: "ダンジョンメニューの[魔法]ボタン機能を実装し、既存の魔法システムと連携"
created_at: "2025-07-23T16:44:40Z"
started_at: null  # Do not modify manually
closed_at: null   # Do not modify manually
---

# Ticket Overview

ダンジョンメニューの[魔法]ボタンを押しても現在何も起こらない状態になっている。調査の結果、魔法システム自体は完全に実装済みで非常に充実した機能を持っているが、ダンジョンメニューからの呼び出し処理が未実装であることが判明。既存の高機能魔法システムとダンジョンメニューを適切に連携させる必要がある。

## 問題の詳細

### 現状
- **✅ 魔法システム**: `spells.py`に完全な魔法システムが実装済み（7レベル魔法、3学派、複数タイプ）
- **✅ 魔法UI**: `magic_ui.py`に完全な魔法管理UIが実装済み
- **✅ 魔法ウィンドウ**: WindowSystemベースの魔法ウィンドウが実装済み
- **✅ 設定ファイル**: `spells.yaml`に魔法定義が完全設定済み
- **✅ ダンジョンメニューUI**: [魔法]ボタンは表示されている
- **❌ アクション処理**: ボタンを押しても「未実装」ログが出力されるのみ
- **❌ システム間連携**: ダンジョンメニューと魔法システムが未接続

### 技術的問題
1. **ダンジョンメニューの`execute_menu_action`で魔法処理が未実装**
2. **魔法UIシステム連携のコールバック設定が欠如**
3. **ダンジョンコンテキストでの魔法メニュー表示処理が未実装**

### 影響
- プレイヤーがダンジョン内で魔法確認・使用ができない
- 戦闘や探索での魔法戦略が立てられない
- キャラクターの魔法スロット管理ができない
- 回復・強化・攻撃魔法の活用ができない

## 既存の魔法システムの特徴

### 魔法学派システム
- **Mage**: 攻撃魔法（ファイアボール、マジックミサイル等）
- **Priest**: 神聖魔法（ヒール、ディテクトイービル等）
- **Both**: 汎用魔法（ライト、テレポート等）

### 魔法レベルとスロット
- **レベル1-7**: 各レベルに対応したスロット数（L1:4, L2:3, L3:3, L4:2, L5:2, L6:2, L7:1）
- **スロット管理**: 使用済み・未使用スロットの完全管理
- **遅延初期化**: キャラクター毎の魔法書システム

### 魔法効果タイプ
- 攻撃、回復、強化、弱体化、汎用、蘇生、究極の7タイプ
- 基本値 + 能力値スケーリングによる効果計算

## Tasks

- [ ] ダンジョンメニューの魔法アクション処理を実装
- [ ] `DungeonUIManagerPygame`に魔法メニュー呼び出し機能を追加
- [ ] 魔法UIシステムとの連携設定を実装
- [ ] ダンジョンメニューマネージャーでの魔法コールバック設定
- [ ] ダンジョン内での魔法ウィンドウ表示動作確認
- [ ] 魔法スロット使用・回復の動作確認
- [ ] 複数キャラクターの魔法書表示テスト
- [ ] 魔法詠唱・効果適用機能の動作確認
- [ ] 魔法ウィンドウからの正常な復帰動作確認
- [ ] Run tests before closing and pass all tests (No exceptions)
- [ ] Get developer approval before closing

## 受け入れ条件

- [ ] ダンジョンメニューで[魔法]ボタンを押すと魔法ウィンドウが表示される
- [ ] 魔法ウィンドウでパーティメンバーの切り替えができる
- [ ] キャラクターの魔法スロット状況が正しく表示される
- [ ] 魔法の詠唱・使用・効果適用が正常に動作する
- [ ] 魔法ウィンドウを閉じるとダンジョン画面に戻る
- [ ] ESCキーで魔法ウィンドウが閉じられる
- [ ] ダンジョン内でのUI階層管理が正常に動作する
- [ ] 全てのテストが通過している

## 実装対象ファイル

### 主要修正対象
1. **`src/ui/dungeon/dungeon_ui_manager_pygame.py`**
   - 魔法メニュー呼び出し機能の実装
   - MagicUIシステムとの連携

2. **`src/ui/windows/dungeon_menu_window.py`**  
   - `execute_menu_action()`での`magic`アクション処理実装

3. **`src/ui/windows/dungeon_menu_manager.py`**
   - 魔法コールバックの設定

### 既存活用可能なシステム
- **`src/magic/spells.py`** - 完全な魔法システム
- **`src/ui/magic_ui.py`** - 完全な魔法UI管理システム
- **`src/ui/window_system/magic_window.py`** - WindowSystemベース魔法ウィンドウ
- **`config/spells.yaml`** - 完全な魔法定義設定

## 実装アプローチ

### 1. DungeonUIManagerPygameの拡張
```python
def _open_magic_menu(self):
    """ダンジョン内で魔法メニューを開く"""
    if self.magic_ui:
        self.magic_ui.show_magic_menu()
    else:
        logger.warning("魔法UIシステムが初期化されていません")
```

### 2. ダンジョンメニューとの連携
```python
# dungeon_menu_window.py内
elif action == "magic":
    self.close_menu()
    if "magic" in self.callbacks:
        self.callbacks["magic"]()
```

### 3. コールバック設定
```python
# dungeon_menu_manager.py内
def set_magic_callback(self, callback):
    """魔法コールバックを設定"""
    self.dungeon_menu_window.set_callback("magic", callback)
```

## Notes

### 設計思想
- **既存システム活用**: 高度な魔法システムを最大限活用
- **戦略的価値**: ダンジョン探索での魔法使用戦略の実現
- **UI統一性**: ダンジョン内外での一貫した魔法メニュー操作

### 魔法システムの価値
- **7レベル魔法**: 初級から究極まで段階的魔法成長
- **3学派対応**: メイジ・プリースト・汎用魔法の使い分け
- **戦略的スロット管理**: 限られたスロットでの魔法選択戦略
- **豊富な効果タイプ**: 攻撃・回復・強化・弱体化等の多様な戦術

### 関連システム
- **SpellManager**: 魔法システム統合管理
- **MagicUI**: 魔法メニュー統一インターフェース
- **WindowSystem**: UI階層管理システム
- **キャラクターシステム**: 魔法書・スロット管理

### テスト観点
- 魔法スロット消費・回復の正確性
- 魔法効果計算の正確性
- UI遷移の安定性
- エラー時の適切な処理

### 優先度の理由
魔法はダンジョン探索・戦闘における重要な戦略要素であり、既存の高機能魔法システムが活用できない状態は大きな機能損失。魔法システム自体は完成しているため、比較的短期間で高価値な機能を提供可能。
