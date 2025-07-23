---
priority: 2
tags: ["ui", "dungeon", "status", "menu", "feature", "integration"]
description: "ダンジョンメニューの[ステータス]ボタン機能を実装し、既存のステータス管理システムと連携"
created_at: "2025-07-23T16:56:33Z"
started_at: null  # Do not modify manually
closed_at: null   # Do not modify manually
---

# Ticket Overview

ダンジョンメニューの[ステータス]ボタンを押しても現在何も起こらない状態になっている。調査の結果、ステータス管理システム自体は完全に実装済みで包括的なステータス効果管理機能を持っているが、ダンジョンメニューからの呼び出し処理が未実装であることが判明。既存のステータス表示システムとダンジョンメニューを適切に連携させる必要がある。

## 問題の詳細

### 現状
- **✅ ステータス効果システム**: `StatusEffectsWindow`による完全なステータス効果管理が実装済み
- **✅ ステータス表示管理**: `StatusDisplayManager`による表示フォーマット管理が実装済み
- **✅ キャラクターステータスバー**: ダンジョン内HP/MP表示システムが実装済み
- **✅ ダンジョンメニューUI**: [ステータス]ボタンは表示されている
- **❌ アクション処理**: ボタンを押しても「未実装」ログが出力されるのみ
- **❌ システム間連携**: ダンジョンメニューとステータスシステムが未接続

### 技術的問題
1. **`DungeonUIManagerPygame`に`_open_status`メソッドが存在しない**
2. **ダンジョンメニューの`execute_menu_action`でステータス処理が未実装**
3. **GameManagerの`_on_status_action`が存在しない`_open_status`メソッドを呼び出している**

### 影響
- プレイヤーがダンジョン内で詳細ステータス確認ができない
- キャラクターの能力値・レベル・経験値が確認できない
- ステータス効果の詳細確認ができない
- パーティメンバーの状態把握が困難

## 既存のステータスシステムの特徴

### ステータス効果管理
- **StatusEffectsWindow**: WindowSystem準拠の完全なステータス効果ウィンドウ
- **効果管理**: 毒、麻痺、石化、呪い等の状態異常管理
- **効果詳細**: 効果時間、強度、除去可能性の表示
- **効果アクション**: 効果除去、詳細確認等のインタラクション

### ステータス表示システム
- **StatusDisplayManager**: 表示フォーマット・レイアウト管理
- **キャラクター情報**: 基本能力値、レベル、経験値表示
- **装備効果**: 装備による能力値補正の表示
- **パーティ統合**: 複数キャラクターの一覧表示

### キャラクターステータスバー
- **リアルタイム表示**: HP/MP, キャラクター名、状態アイコン
- **6キャラクター対応**: パーティ全体の状況把握
- **ダンジョンUI統合**: 既にダンジョン画面に統合済み

## Tasks

- [ ] `DungeonUIManagerPygame`に`_open_status`メソッドを実装
- [ ] ダンジョンメニューのステータスアクション処理を実装
- [ ] ステータス表示システムとの連携設定を実装
- [ ] ダンジョンメニューマネージャーでのステータスコールバック設定
- [ ] ダンジョン内でのステータスウィンドウ表示動作確認
- [ ] キャラクター詳細ステータス表示機能の動作確認
- [ ] ステータス効果一覧表示・管理機能の動作確認
- [ ] 複数キャラクターのステータス切り替え機能テスト
- [ ] ステータスウィンドウからの正常な復帰動作確認
- [ ] Run tests before closing and pass all tests (No exceptions)
- [ ] Get developer approval before closing

## 受け入れ条件

- [ ] ダンジョンメニューで[ステータス]ボタンを押すとステータスウィンドウが表示される
- [ ] ステータスウィンドウでパーティメンバーの切り替えができる
- [ ] キャラクターの基本ステータス（HP/MP、能力値、レベル）が正しく表示される
- [ ] ステータス効果一覧とその詳細が表示される
- [ ] 装備による能力値補正が正しく表示される
- [ ] ステータスウィンドウを閉じるとダンジョン画面に戻る
- [ ] ESCキーでステータスウィンドウが閉じられる
- [ ] ダンジョン内でのUI階層管理が正常に動作する
- [ ] 全てのテストが通過している

## 実装対象ファイル

### 主要修正対象
1. **`src/ui/dungeon/dungeon_ui_manager_pygame.py`**
   - `_open_status()`メソッドの実装
   - ステータス表示システムとの連携

2. **`src/ui/windows/dungeon_menu_window.py`**  
   - `execute_menu_action()`での`status`アクション処理実装

3. **`src/ui/windows/dungeon_menu_manager.py`**
   - ステータスコールバックの設定

### 既存活用可能なシステム
- **`src/ui/window_system/status_effects_window.py`** - 完全なステータス効果ウィンドウ
- **`src/ui/window_system/status_display_manager.py`** - ステータス表示管理システム
- **`src/ui/character_status_bar.py`** - キャラクターステータスバー

## 実装アプローチ

### 1. DungeonUIManagerPygameの拡張
```python
def _open_status(self):
    """ダンジョン内でステータスを開く"""
    if self.status_manager:
        self.status_manager.show_status_effects_window()
    else:
        logger.warning("ステータスマネージャーが初期化されていません")
```

### 2. ダンジョンメニューとの連携
```python
# dungeon_menu_window.py内
elif action == "status":
    self.close_menu()
    if "status" in self.callbacks:
        self.callbacks["status"]()
```

### 3. コールバック設定
```python
# dungeon_menu_manager.py内
def set_status_callback(self, callback):
    """ステータスコールバックを設定"""
    self.dungeon_menu_window.set_callback("status", callback)
```

## Notes

### 設計思想
- **既存システム活用**: 完成したステータス管理システムを最大限活用
- **情報一元化**: キャラクター情報の集約表示
- **UI統一性**: ダンジョン内外での一貫したステータス表示

### ステータスシステムの価値
- **戦略的情報**: キャラクター能力の正確な把握
- **状態管理**: ステータス効果の詳細確認・管理
- **成長実感**: レベルアップ・能力向上の確認
- **装備効果**: 装備変更による能力変化の確認

### 関連システム
- **StatusEffectsWindow**: ステータス効果統合管理
- **StatusDisplayManager**: ステータス表示統一インターフェース
- **WindowSystem**: UI階層管理システム
- **キャラクターシステム**: 能力値・レベル・経験値管理

### テスト観点
- ステータス値計算の正確性
- ステータス効果表示の正確性
- UI遷移の安定性
- エラー時の適切な処理

### 優先度の理由
ステータス確認はダンジョン探索における基本的な情報収集機能であり、戦略立案に不可欠。既存のステータス管理システムが充実しているため、連携実装により高価値な機能を短期間で提供可能。キャラクター管理の完成により、プレイヤーの満足度向上が期待される。
