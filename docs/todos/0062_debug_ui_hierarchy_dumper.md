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

## 実装記録

（実装時に記録）