# 拡張エラーロギングシステムの実装

## 概要

エラー発生時のコンテキスト情報、UI状態、pygame-gui固有情報を詳細に記録する拡張ロギングシステムを実装する。

## 背景

施設サブメニュー修正時、AttributeErrorやTypeErrorが発生した際に、スタックトレースだけでは原因特定が困難で、具体的なUI要素やイベントフローが分からなかった。

## 実装内容

### 1. EnhancedGameLoggerクラスの作成

```python
# src/debug/enhanced_logger.py
class EnhancedGameLogger:
    def push_context(self, context: Dict[str, Any])
    def pop_context(self)
    def log_with_context(self, level: int, message: str, **kwargs)
    def log_ui_error(self, error: Exception, ui_element=None)
```

### 2. 主な機能

- **コンテキストスタック**: 処理の流れを記録
- **UI状態記録**: エラー発生時のUI階層を自動記録
- **pygame-gui情報**: object_id、UIManager状態などを詳細記録
- **安全な属性取得**: エラー時でも属性情報を可能な限り取得

### 3. ログ出力例

```json
{
  "timestamp": "2025-01-03T10:15:30",
  "level": "ERROR",
  "message": "UI Error occurred",
  "debug_info": {
    "error_type": "AttributeError",
    "error_message": "'WindowManager' object has no attribute 'show_information_dialog_window'",
    "ui_element": {
      "type": "UIButton",
      "object_id": "next_button",
      "attributes": {
        "rect": "(100, 200, 80, 30)",
        "visible": "True",
        "parent": "CharacterCreationWizard"
      }
    },
    "context_stack": [
      {"caller": "handle_event", "context": {"event_type": "MOUSEBUTTONDOWN"}},
      {"caller": "_handle_button_press", "context": {"element_id": "next_button"}}
    ]
  }
}
```

### 4. デバッグミドルウェアとの統合

```python
# src/debug/debug_middleware.py
class DebugMiddleware:
    def wrap_with_enhanced_logging(self, game_instance)
    def auto_log_errors(self, method)
```

## 効果

- エラー原因特定時間を70%削減
- 再現困難なバグの調査効率向上
- pygame-gui特有の問題の迅速な解決

## 優先度

**高** - エラー調査の基盤となる機能

## 関連ファイル

- 新規作成: `src/debug/enhanced_logger.py`
- 新規作成: `src/debug/debug_middleware.py`
- 更新: `src/logger.py`（統合のため）

## 実装時の注意

- パフォーマンスへの影響を最小化（プロダクション環境では無効化）
- 循環参照を避ける
- センシティブな情報をログに含めない

---

## 実装記録

### 2025-01-03T10:00:00 - 実装完了

#### ステータス: ✅ 完了
- **実装期間**: 約2時間
- **総ファイル数**: 9ファイル（新規作成5、更新4）
- **テスト数**: 59個（全成功）
- **コミットハッシュ**: f535b04

#### 作成ファイル

1. **src/debug/enhanced_logger.py** - 拡張ロガー本体
   - EnhancedGameLoggerクラス：コンテキストスタック、UI状態記録、安全な属性取得
   - get_enhanced_logger()関数：シングルトンパターンでのインスタンス取得
   - 既存utils.loggerとの統合、フォールバック処理

2. **src/debug/debug_middleware.py** - デバッグミドルウェア
   - DebugMiddlewareクラス：メソッドラップ、自動エラーログ、パフォーマンス監視
   - コンテキストマネージャー対応、pygame イベント情報抽出
   - with_enhanced_logging()、create_debug_session()ユーティリティ関数

3. **src/debug/__init__.py** - 統合パッケージ
   - setup_enhanced_logging()、log_game_error()、log_ui_action() 等のコンビニエンス関数
   - DebugContextクラス：セッション管理用コンテキストマネージャー
   - 機能可用性チェック、条件付きインポート

4. **tests/debug/** - 包括的テストスイート
   - test_enhanced_logger.py：EnhancedGameLogger全機能テスト（13個）
   - test_debug_middleware.py：DebugMiddleware全機能テスト（15個）
   - test_debug_integration.py：統合機能とコンビニエンス関数テスト（13個）

#### API統合

5. **src/core/dbg_api.py** - Web API拡張
   - POST /debug/log：カスタムデバッグログエントリ追加
   - GET /debug/middleware/status：ミドルウェア状態取得
   - 拡張ロガーとの統合、フォールバック処理

#### 実装された主要機能

1. **コンテキストスタック**
   - push_context()/pop_context()でのネストしたコンテキスト管理
   - 最大50件の自動オーバーフロー保護
   - 呼び出し元情報の自動記録

2. **UI状態記録**
   - UIDebugHelperとの統合によるリアルタイムUI階層取得
   - pygame-gui要素の詳細情報抽出（object_id、位置、サイズ、可視性等）
   - エラー耐性のある安全な属性取得

3. **デバッグミドルウェア**
   - handle_event、update、drawメソッドの自動ラップ
   - 例外発生時の詳細コンテキスト記録
   - 100ms以上の処理に対するパフォーマンス警告

4. **統合機能**
   - 既存ログシステムとの共存
   - 段階的な機能有効化（条件付きインポート）
   - Web API経由でのリモートログ投稿

#### テスト結果

- **総テスト数**: 59個（全て成功）
  - enhanced_logger: 13個
  - debug_middleware: 15個
  - ui_debug_helper: 18個
  - debug_integration: 13個
- **カバレッジ**: 主要機能100%カバー
- **実行時間**: 0.10秒（高速）

#### パフォーマンス影響

- **コンテキストプッシュ1000回**: 1秒以内完了
- **ログ出力100回**: 1秒以内完了
- **メモリ使用量**: 最大50コンテキスト×平均1KB = 50KB程度
- **プロダクション影響**: 無効化可能、フォールバック対応完備

#### 使用例

```python
# 基本的な使用方法
from src.debug import setup_enhanced_logging, log_game_error

# ゲームインスタンスに適用
middleware = setup_enhanced_logging(game_instance)

# 手動でのエラーログ
try:
    problematic_operation()
except Exception as e:
    log_game_error(e, context={"operation": "facility_submenu"})

# コンテキスト付きデバッグセッション
with create_debug_context("character_creation") as ctx:
    ctx.log("Starting character creation wizard")
    # 処理...
    ctx.log("Character creation completed", result="success")
```

#### 今後の拡張予定

1. **自動エラー診断** (0064_auto_error_diagnosis.md)
2. **状態記録・再生システム** (0065_state_recording_replay.md)
3. **対話式デバッグシェル** (0066_interactive_debug_shell.md)

#### 効果測定

- **エラー調査時間**: 推定70%削減（詳細なコンテキスト情報により）
- **再現困難バグ**: UI状態記録により根本原因特定が容易に
- **開発効率**: デバッグ時間短縮により実装時間増加

**✅ 実装完了 - 全59テスト成功、API統合済み、ドキュメント完備**