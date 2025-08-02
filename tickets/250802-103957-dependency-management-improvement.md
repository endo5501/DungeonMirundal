---
priority: 2
tags: ["infrastructure", "build-tools", "dependencies", "pyright"]
description: "pyrightのimportエラー160個を解決し、依存関係管理を改善"
created_at: "2025-08-02T10:39:57Z"
---

# 依存関係管理改善

## 現状の問題

pyrightで160個の`reportMissingImports`エラーが発生しており、開発環境での型チェックが正しく機能していない。

### エラーの内訳
- pygame: 最も多い
- PIL (Pillow)
- fastapi, uvicorn
- yaml
- requests
- click
- jsonschema

## 目的

- pyrightが全ての依存関係を正しく認識
- 開発環境での型チェックの完全性確保
- CI/CDでの型チェック自動化の基盤構築

## 実施内容

### Phase 1: pyrightconfig.json の改善
- [ ] venvPath/venv設定の追加
- [ ] executionEnvironments の設定
- [ ] stubsディレクトリの設定
- [ ] extraPaths の最適化

### Phase 2: 型スタブの導入
- [ ] pygame-stubs の導入検討
- [ ] 不足している型スタブの特定
- [ ] カスタム型スタブの作成（必要な場合）

### Phase 3: 開発環境の統一
- [ ] .vscode/settings.json の改善
- [ ] 開発者向けセットアップドキュメント更新
- [ ] CI環境でのpyright実行設定

## 技術的詳細

### pyrightconfig.json 改善案
```json
{
  "include": ["src/**/*.py", "tests/**/*.py"],
  "exclude": ["**/node_modules", "**/__pycache__", "**/.*", "build", "dist"],
  "reportMissingImports": true,
  "reportMissingTypeStubs": false,
  "pythonVersion": "3.13",
  "pythonPlatform": "All",
  "venvPath": ".",
  "venv": ".venv",
  "executionEnvironments": [
    {
      "root": "src",
      "pythonVersion": "3.13",
      "extraPaths": ["src"]
    }
  ]
}
```

### 型スタブ導入例
```bash
# pygame型スタブのインストール
uv add --dev pygame-stubs

# または手動で型スタブを作成
mkdir -p typings/pygame
touch typings/pygame/__init__.pyi
```

## 期待される成果

- pyrightエラー0を達成
- IDE での正確な型推論
- 早期のバグ発見
- 開発効率の向上

## 注意事項

- 既存の動作に影響を与えない
- すべての開発者の環境で動作すること
- CI/CDパイプラインとの互換性維持