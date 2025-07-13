# uvでのプラットフォーム別依存関係管理

## 1. 環境マーカーを使用した方法

pyproject.tomlで環境マーカーを使用してOS別の依存関係を定義できます：

```toml
dependencies = [
    # Linux用
    "pygame>=2.6.0,<2.7; sys_platform == 'linux'",
    # macOS用（pygame-ceを使用）
    "pygame-ce>=2.5.0,<2.6; sys_platform == 'darwin'",
    # Windows用
    "pygame>=2.5.0,<2.6; sys_platform == 'win32'",
]
```

### 利用可能な環境マーカー

- `sys_platform`: OS識別子 ('linux', 'darwin', 'win32')
- `platform_machine`: アーキテクチャ ('x86_64', 'arm64', etc.)
- `platform_version`: OSバージョン
- `python_version`: Pythonバージョン ('3.12', '3.11', etc.)
- `implementation_name`: Python実装 ('cpython', 'pypy', etc.)

## 2. 複雑な条件の例

```toml
dependencies = [
    # Python 3.12以上かつLinuxの場合
    "some-package>=1.0; python_version >= '3.12' and sys_platform == 'linux'",
    
    # macOSのARM64（M1/M2）用
    "special-package; sys_platform == 'darwin' and platform_machine == 'arm64'",
    
    # 複数プラットフォーム対応
    "cross-platform-pkg; sys_platform in ['linux', 'darwin']",
]
```

## 3. オプション依存関係の定義

より柔軟な管理のために、オプション依存関係を使用することもできます：

```toml
[project.optional-dependencies]
linux = [
    "pygame>=2.6.0,<2.7",
    "linux-specific-package",
]
macos = [
    "pygame-ce>=2.5.0,<2.6",
    "pyobjc-framework-Cocoa; sys_platform == 'darwin'",
]
windows = [
    "pygame>=2.5.0,<2.6",
    "pywin32; sys_platform == 'win32'",
]
```

インストール時：
```bash
# Linux環境で
uv pip install -e ".[linux]"

# macOS環境で
uv pip install -e ".[macos]"
```

## 4. 開発依存関係の管理

開発環境でもOS別の依存関係を管理できます：

```toml
[tool.uv]
dev-dependencies = [
    "black>=23.0",
    "mypy>=1.0",
    # macOS専用の開発ツール
    "mac-dev-tool; sys_platform == 'darwin'",
]
```

## 5. 実装例：現在のプロジェクト

現在のDungeonプロジェクトでは以下のように設定しています：

```toml
dependencies = [
    # 共通の依存関係
    "pygame-gui>=0.6.9,<0.7",
    
    # OS別のpygame
    "pygame>=2.6.0,<2.7; sys_platform == 'linux'",      # Ubuntu等
    "pygame-ce>=2.5.0,<2.6; sys_platform == 'darwin'",  # macOS
    "pygame>=2.5.0,<2.6; sys_platform == 'win32'",      # Windows
]
```

## 6. トラブルシューティング

### 依存関係の競合

異なるプラットフォームで異なるパッケージを使用する場合（例：pygame vs pygame-ce）、
パッケージ名が異なることを確認してください。

### ロックファイルの管理

`uv.lock`ファイルは全プラットフォームの依存関係を含みます。
チーム開発では、このファイルをコミットすることで、
全員が同じバージョンを使用できます。

### テスト環境

CI/CDで複数のOSでテストする場合、環境マーカーが正しく動作することを確認してください：

```yaml
# GitHub Actions例
strategy:
  matrix:
    os: [ubuntu-latest, macos-latest, windows-latest]
    python-version: ["3.12"]
```

## 7. ベストプラクティス

1. **明示的なバージョン指定**: OS別に異なるバージョンが必要な場合は、明確に指定する
2. **フォールバック**: 可能な場合は、汎用的なパッケージをフォールバックとして用意
3. **ドキュメント化**: OS別の違いをREADMEやCLAUDE.mdに記載
4. **テスト**: 各プラットフォームでの動作を定期的にテスト
