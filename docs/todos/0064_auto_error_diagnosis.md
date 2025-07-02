# 自動エラー診断システムの実装

## 概要

頻出するエラーパターンを自動的に検出し、原因と解決策を提示する診断システムを実装する。

## 背景

施設サブメニュー修正作業で同様のエラーパターンが繰り返し発生した：
- `AttributeError: 'AdventurersGuild' object has no attribute 'menu_stack_manager'`
- `AttributeError: 'WindowManager' object has no attribute 'show_information_dialog_window'`
- `TypeError: ShopTransactionWindow.__init__() got an unexpected keyword argument 'parent'`

これらは既知のパターンであり、自動診断可能。

## 実装内容

### 1. AutoDiagnosticsクラスの作成

```python
# src/debug/auto_diagnose.py
class AutoDiagnostics:
    ERROR_PATTERNS: Dict[str, ErrorDiagnosis]
    
    def diagnose_error(self, error_message: str) -> Optional[ErrorDiagnosis]
    def suggest_fix(self, diagnosis: ErrorDiagnosis) -> str
    def auto_fix(self, diagnosis: ErrorDiagnosis) -> bool
```

### 2. エラーパターンデータベース

```python
ERROR_PATTERNS = {
    "AttributeError.*menu_stack_manager": {
        "cause": "Window System移行によりmenu_stack_managerが削除",
        "solution": "WindowManager.get_instance()を使用",
        "affected_files": ["src/overworld/facilities/*.py"],
        "auto_fix_possible": True,
        "fix_pattern": {
            "search": r"self\.menu_stack_manager",
            "replace": "WindowManager.get_instance()"
        }
    },
    "TypeError.*unexpected keyword argument 'parent'": {
        "cause": "Window初期化メソッドがparent引数を受け取らない",
        "solution": "__init__メソッドにparent引数を追加",
        "check_command": "grep -n '__init__' {file_path}",
        "manual_fix_required": True
    }
}
```

### 3. VSCode問題マッチャー統合

```json
// .vscode/tasks.json
{
  "problemMatcher": {
    "pattern": {
      "regexp": "^(ERROR|WARNING):\\s+(.*)\\s+\\[DIAGNOSIS:\\s+(.*)\\]$",
      "severity": 1,
      "message": 2,
      "code": 3
    }
  }
}
```

### 4. CLI統合

```bash
# エラーログを分析して診断
uv run python -m src.debug.debug_cli diagnose error.log

# 最新のエラーを診断
uv run python -m src.debug.debug_cli diagnose --latest

# 自動修正を試行
uv run python -m src.debug.debug_cli diagnose --auto-fix
```

## 効果

- 既知エラーの解決時間を80%削減
- 新規開発者の学習曲線を緩和
- エラーパターンの知識を蓄積・共有

## 優先度

**高** - 即座に効果が期待できる

## 関連ファイル

- 新規作成: `src/debug/auto_diagnose.py`
- 新規作成: `src/debug/error_patterns.json`
- 更新: `src/debug/debug_cli.py`

## 実装時の注意

- エラーパターンは定期的に更新
- 誤診断を防ぐため、信頼度スコアを実装
- 自動修正は慎重に（バックアップを作成）

---

## 実装記録

（実装時に記録）