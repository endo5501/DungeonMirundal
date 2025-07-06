# VSCode デバッグ統合の強化

## 概要

VSCodeとゲームデバッグツールを深く統合し、IDE内から直接デバッグ機能を利用できるようにする。

## 背景

現在はターミナルでコマンドを実行する必要があり、IDEとの切り替えが頻繁。VSCodeの機能を活用してより効率的なデバッグ環境を構築したい。

## 実装内容

### 1. デバッグ設定の拡充

```json
// .vscode/launch.json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "Debug Game with Enhanced Logging",
      "type": "python",
      "request": "launch",
      "program": "${workspaceFolder}/main.py",
      "args": ["--debug-mode", "--enhanced-logging"],
      "env": {
        "GAME_DEBUG": "1",
        "UI_TRACE": "1",
        "AUTO_DIAGNOSE": "1"
      },
      "preLaunchTask": "start-debug-server"
    },
    {
      "name": "Debug Specific Facility",
      "type": "python",
      "request": "launch",
      "program": "${workspaceFolder}/src/debug/facility_debugger.py",
      "args": ["--facility", "${input:facility}"]
    },
    {
      "name": "Replay Bug Recording",
      "type": "python",
      "request": "launch",
      "program": "${workspaceFolder}/src/debug/game_replayer.py",
      "args": ["--file", "${file}"]
    }
  ]
}
```

### 2. カスタムタスク

```json
// .vscode/tasks.json
{
  "version": "2.0.0",
  "tasks": [
    {
      "label": "Capture UI State",
      "type": "shell",
      "command": "uv run python -m src.debug.debug_cli ui-dump --save ${workspaceFolder}/.vscode/ui_state_${timestamp}.json",
      "problemMatcher": []
    },
    {
      "label": "Run Facility Tests",
      "type": "shell",
      "command": "uv run python -m src.debug.debug_cli test-scenario ${input:scenario}",
      "problemMatcher": {
        "pattern": {
          "regexp": "^(FAIL|ERROR):\\s+(.*)\\s+at\\s+(.*):(\\d+)$",
          "severity": 1,
          "message": 2,
          "file": 3,
          "line": 4
        }
      }
    }
  ]
}
```

### 3. コードレンズ統合

```python
# src/debug/vscode_integration.py
class VSCodeDebugIntegration:
    """VSCode用のデバッグ情報を提供"""
    
    def generate_codelens_data(self, file_path: str):
        """ファイル内のデバッグ可能な要素を検出"""
        # UI要素定義の上に「Debug This UI」リンクを表示
        # エラーハンドラの上に「Test Error Case」リンクを表示
```

### 4. デバッグビュー拡張

```typescript
// .vscode/extensions/game-debug-view/src/extension.ts
// カスタムVSCode拡張機能
export function activate(context: vscode.ExtensionContext) {
    // ゲーム状態を表示するサイドバーパネル
    const provider = new GameDebugViewProvider();
    
    // リアルタイムUI階層表示
    // 記録されたセッションの再生コントロール
    // エラー診断結果の表示
}
```

### 5. スニペット

```json
// .vscode/python.code-snippets
{
  "Debug UI Element": {
    "prefix": "debug-ui",
    "body": [
      "from src.debug.ui_debug_helper import UIDebugHelper",
      "helper = UIDebugHelper()",
      "ui_state = helper.dump_ui_hierarchy()",
      "print(f\"UI State: {ui_state}\")"
    ]
  },
  "Add Error Pattern": {
    "prefix": "debug-error-pattern",
    "body": [
      "\"${1:ErrorPattern}\": {",
      "    \"cause\": \"${2:原因}\",",
      "    \"solution\": \"${3:解決策}\",",
      "    \"affected_files\": [\"${4:files}\"],",
      "    \"auto_fix_possible\": ${5:false}",
      "}"
    ]
  }
}
```

## 効果

- IDE内で完結するデバッグワークフロー
- 視覚的なデバッグ情報表示
- ワンクリックでのデバッグ操作実行

## 優先度

**中** - 開発効率向上に寄与するが実装コストも中程度

## 関連ファイル

- 新規作成: `.vscode/launch.json`（拡張）
- 新規作成: `.vscode/tasks.json`（拡張）
- 新規作成: `.vscode/python.code-snippets`
- 新規作成: `src/debug/vscode_integration.py`
- 新規作成: `.vscode/extensions/game-debug-view/`（VSCode拡張）

## 実装時の注意

- VSCodeのバージョン互換性
- 拡張機能の配布方法（チーム内共有）
- パフォーマンスへの影響

---

## 実装記録

（実装時に記録）