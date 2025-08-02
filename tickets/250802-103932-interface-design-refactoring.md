---
priority: 2
tags: ["architecture", "refactoring", "type-safety", "design-patterns"]
description: "hasattr/getattr使用箇所をインターフェース設計で置き換え、型安全性を向上"
created_at: "2025-08-02T10:39:32Z"
---

# インターフェース設計見直し

## 現状の問題

pyrightエラー修正で大量のhasattr/getattr使用によるランタイムチェックが導入されており、型安全性の根本的な解決になっていない。

### 影響範囲
- battle_integration_manager.py での cleanup メソッドチェック
- 各種UI要素でのメソッド存在確認
- オプショナルな機能の動的チェック

## 目的

- Protocol/ABC（抽象基底クラス）を使用した型安全なインターフェース定義
- ランタイムチェックから静的型チェックへの移行
- 保守性と可読性の向上

## 実施内容

### Phase 1: インターフェース定義
- [ ] Cleanupable Protocol の定義
- [ ] UIComponent Protocol の定義
- [ ] Renderable Protocol の定義
- [ ] その他必要なProtocolの洗い出し

### Phase 2: 既存コードの移行
- [ ] hasattr/getattr使用箇所の特定
- [ ] Protocol実装への段階的移行
- [ ] 型アノテーションの更新

### Phase 3: テストと検証
- [ ] 型チェックの実施
- [ ] ランタイムエラーの確認
- [ ] パフォーマンスへの影響評価

## 期待される成果

- 型安全性の向上
- IDEでの補完・リファクタリング機能の改善
- ランタイムエラーの削減
- コードの意図が明確化

## 技術的詳細

### 例: Cleanupable Protocol
```python
from typing import Protocol

class Cleanupable(Protocol):
    def cleanup(self) -> None:
        ...

# 使用例
def cleanup_resources(obj: Cleanupable) -> None:
    obj.cleanup()  # 型安全にアクセス可能
```

## 参考資料
- [PEP 544 – Protocols](https://www.python.org/dev/peps/pep-0544/)
- 現在のhasattr/getattr使用状況分析