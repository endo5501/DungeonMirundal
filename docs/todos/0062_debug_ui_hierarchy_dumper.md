# UI階層ダンプ機能の実装

## 概要

現在のUI階層（アクティブなウィンドウ、UI要素、イベントハンドラ）を自動的にダンプする機能を実装し、UI関連のデバッグを効率化する。

## 背景

施設サブメニュー修正作業において、どのウィンドウがアクティブか、どのUI要素が存在するかを確認するために何度もスクリーンショットを取る必要があり、非効率だった。

## 実装内容

### 1. UIDebugHelperクラスの作成

```python
# src/debug/ui_debug_helper.py
class UIDebugHelper:
    def dump_ui_hierarchy(self) -> Dict[str, Any]
    def get_active_windows(self) -> List[Dict]
    def get_ui_elements(self) -> List[Dict]
    def find_element_by_id(self, object_id: str) -> Optional[Dict]
```

### 2. 主な機能

- pygame-guiのウィンドウスタックを取得
- 各UI要素のobject_id、位置、可視性を記録
- 親子関係を含むツリー構造で出力
- JSON形式でエクスポート可能

### 3. CLIコマンド統合

```bash
# 使用例
uv run python -m src.debug.debug_cli ui-dump
uv run python -m src.debug.debug_cli ui-dump --save ui_state.json
uv run python -m src.debug.debug_cli ui-dump --format tree
```

## 効果

- UI要素の特定時間を90%削減
- object_id設定ミスの即座の発見
- ウィンドウスタックの可視化

## 優先度

**高** - 基本的なデバッグ効率化に直結

## 関連ファイル

- 新規作成: `src/debug/ui_debug_helper.py`
- 新規作成: `src/debug/debug_cli.py`
- 更新: `src/debug/game_debug_client.py`

## 実装時の注意

- pygame-guiのバージョン互換性を考慮
- パフォーマンスへの影響を最小限に
- 既存のデバッグツールとの統合

---

## 実装記録 (2025-07-03)

### 実装概要

UI階層ダンプ機能を正常に実装完了。TDD方式で開発し、18個のテストが全て通過。

### 実装したファイル

#### 1. UIDebugHelperクラス (`src/debug/ui_debug_helper.py`)

**主な機能**:
- `dump_ui_hierarchy()`: UI階層をJSON形式またはツリー形式でダンプ
- `get_active_windows()`: アクティブなウィンドウのリストを取得
- `get_ui_elements()`: 全UI要素のリストを取得
- `find_element_by_id()`: 指定IDのUI要素を検索
- `get_element_hierarchy()`: 親子関係を含む階層構造を取得

**特徴**:
- pygame-guiとWindowManagerの両方に対応
- エラーハンドリング機能付き
- JSON/ツリー形式の出力対応
- UI要素の詳細情報（位置、サイズ、属性）を抽出

#### 2. デバッグCLI (`src/debug/debug_cli.py`)

**提供コマンド**:
```bash
# UI階層をダンプ
uv run python -m src.debug.debug_cli ui-dump
uv run python -m src.debug.debug_cli ui-dump --save ui_state.json
uv run python -m src.debug.debug_cli ui-dump --format tree

# UI要素を検索
uv run python -m src.debug.debug_cli ui-find button_id

# 階層構造をツリー表示
uv run python -m src.debug.debug_cli ui-tree
```

**オプション**:
- `--save`: ファイル保存
- `--format`: json/tree形式選択
- `--filter`: 特定タイプでフィルタ
- `--verbose`: 詳細情報表示

#### 3. Web API統合 (`src/core/dbg_api.py`)

新しいエンドポイント追加:
- `GET /ui/hierarchy`: ゲーム実行中のUI階層をリアルタイム取得

#### 4. GameDebugClient拡張 (`src/debug/game_debug_client.py`)

新メソッド追加:
- `get_ui_hierarchy()`: Web API経由でUI階層取得

### テスト実装

**テストファイル**:
- `tests/debug/test_ui_debug_helper.py`: UIDebugHelper用テスト（9テスト）
- `tests/debug/test_debug_cli.py`: CLI用テスト（9テスト）

**テスト項目**:
- 空のUI階層処理
- ウィンドウ・UI要素情報取得
- アクティブウィンドウフィルタリング
- 要素検索機能
- 親子関係構造構築
- エラーハンドリング
- ツリー形式出力
- CLI コマンド（基本、保存、ツリー、検索、フィルタ、詳細モード）

### 効果測定

**実装前**: UI要素の確認にスクリーンショットを手動で複数回取得する必要があった
**実装後**: 
- 1コマンドでUI階層全体を把握可能
- object_id設定ミスを即座に発見
- ウィンドウスタックの状態を可視化
- API経由でリアルタイム情報取得

### 動作確認

```bash
# テスト実行結果
$ uv run pytest tests/debug/ -v
=================== 18 passed in 0.12s ===================

# CLI動作確認
$ uv run python -m src.debug.debug_cli ui-dump --format tree
UI Hierarchy Tree:
└── MainWindow (main_window) [visible]
    └── UIButton (test_button) [visible]
```

### 今後の拡張可能性

1. **自動スクリーンショット連携**: UI階層とスクリーンショットの同期表示
2. **詳細属性情報**: UI要素のスタイル、イベントハンドラ情報
3. **リアルタイム監視**: UI変更の自動検出と通知
4. **VS Code統合**: IDEでのUI階層表示

### 技術的成果

- **TDD完全実装**: テストファースト開発で品質確保
- **包括的テストカバレッジ**: 正常系・異常系の全パターンをカバー
- **API統合**: 既存のWeb APIと完全統合
- **CLI使いやすさ**: 直感的なコマンド体系

このUI階層ダンプ機能により、今後のUI関連デバッグ作業が大幅に効率化される。