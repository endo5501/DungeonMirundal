---
priority: 2
tags: ["code-quality", "refactoring", "type-safety", "anti-pattern"]
description: "hasattr/getattrパターンを型安全な実装に置き換え、コード品質を向上"
created_at: "2025-08-02T10:45:27Z"
---

# hasattr/getattr パターンの排除

## 現状の問題

pyrightエラー修正の過程で、多くのhasattr/getattr呼び出しが導入されており、これらは型安全性の根本的な解決になっていない上、以下の問題を引き起こしている：

### 問題点
1. **型チェックの無効化**: ランタイムチェックに依存し、静的型チェックの利点を失う
2. **パフォーマンス**: 毎回属性の存在をチェックするオーバーヘッド
3. **可読性**: コードの意図が不明確になる
4. **保守性**: リファクタリング時に見落とされやすい

### 影響箇所の例
```python
# battle_integration_manager.py
if self.current_battle_window and hasattr(self.current_battle_window, 'cleanup'):
    cleanup_method = getattr(self.current_battle_window, 'cleanup', None)
    if cleanup_method and callable(cleanup_method):
        cleanup_method()
```

## 目的

- hasattr/getattr パターンを型安全な実装に置き換える
- コードの可読性と保守性を向上
- パフォーマンスの改善
- 静的型チェックの利点を最大限活用

## 実施内容

### Phase 1: 現状分析
- [ ] hasattr/getattr使用箇所の全体調査
- [ ] パターン別の分類（オプショナル機能、ダックタイピング等）
- [ ] 優先度付け（影響度、修正難易度）

### Phase 2: 改善実装
- [ ] Union型やOptional型での明示的な型定義
- [ ] インターフェース（Protocol/ABC）の活用
- [ ] 適切なデフォルト値の設定
- [ ] Factory パターンやStrategy パターンの適用

### Phase 3: 検証とテスト
- [ ] 型チェックの実施
- [ ] パフォーマンステスト
- [ ] 既存機能の動作確認

## 技術的詳細

### Before (現在の問題のあるコード)
```python
# 動的な属性チェック
if hasattr(obj, 'method'):
    result = getattr(obj, 'method')()
```

### After (改善後のコード)

#### 方法1: Protocol使用
```python
from typing import Protocol

class HasMethod(Protocol):
    def method(self) -> None: ...

def process(obj: HasMethod) -> None:
    obj.method()  # 型安全
```

#### 方法2: Union型使用
```python
from typing import Union

class WithMethod:
    def method(self) -> None: ...

class WithoutMethod:
    pass

def process(obj: Union[WithMethod, WithoutMethod]) -> None:
    if isinstance(obj, WithMethod):
        obj.method()  # 型チェックで保証
```

#### 方法3: Optional属性
```python
from typing import Optional, Callable

class Component:
    cleanup: Optional[Callable[[], None]] = None
    
    def __init__(self):
        self.cleanup = None  # or実際の関数

# 使用時
if component.cleanup is not None:
    component.cleanup()  # 型安全
```

## 期待される成果

- 型安全性の向上
- IDEサポートの改善（補完、リファクタリング）
- 実行時エラーの削減
- コードの意図が明確化
- パフォーマンスの向上

## 関連チケット

- [インターフェース設計見直し](./250802-103932-interface-design-refactoring.md)
- [Pyright静的解析エラー修正](./250727-142147-pyright-static-analysis-fixes.md)

## 注意事項

- 既存の動作を変更しない
- 段階的な移行を行う
- テストカバレッジを維持
