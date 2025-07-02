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

（実装時に記録）