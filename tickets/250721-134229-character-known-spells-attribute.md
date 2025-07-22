---
priority: 1
tags: ["feature", "character", "magic", "core"]
description: "Characterクラスにknown_spells属性を追加し、習得魔法管理機能を実装"
created_at: "2025-07-21T13:42:29Z"
started_at: 2025-07-22T13:38:42Z # Do not modify manually
closed_at: 2025-07-22T15:30:13Z # Do not modify manually
---

# Ticket Overview

Characterクラスに`known_spells`属性を追加し、キャラクターの習得魔法を管理する機能を実装する。これは宿屋での魔法管理機能（チケット250721-060706）の前提条件となる重要な基盤機能である。

## 背景
- 現在のCharacterクラスには習得魔法を管理する属性がない
- 宿屋での魔法スロット管理機能実装に必要な基盤機能
- 魔術書使用による魔法習得システムとの連携が必要
- セーブ/ロード時の魔法データ永続化が必要

## Tasks

- [ ] Characterクラスの現在の実装状況を調査
- [ ] known_spells属性の設計（List[str]での魔法ID管理）
- [ ] Character.__init__()にknown_spells初期化を追加
- [ ] 魔法習得メソッド（learn_spell）の実装
- [ ] 魔法忘却メソッド（forget_spell）の実装
- [ ] 習得魔法確認メソッド（has_spell）の実装
- [ ] シリアライゼーション対応（to_dict/from_dict）
- [ ] 職業による魔法習得制限の実装
- [ ] 魔法システムとの統合確認（SpellManagerとの連携）
- [ ] テストデータ用の初期魔法設定機能
- [ ] ユニットテストの作成
- [ ] 統合テストの実施
- [ ] 魔術書使用時の習得処理との連携確認
- [ ] Run tests before closing and pass all tests (No exceptions)
- [ ] Get developer approval before closing

## 受け入れ条件
- [ ] Characterクラスにknown_spells属性が追加される
- [ ] キャラクター作成時に適切な初期魔法が設定される
- [ ] 魔法の習得・忘却が正常に動作する
- [ ] 職業制限が正しく機能する（魔術師は魔術、僧侶は祈祷のみ）
- [ ] セーブ/ロード時にknown_spellsが正しく保存・復元される
- [ ] 既存のキャラクター機能に影響しない
- [ ] SpellManagerとの統合が正常に動作する
- [ ] テスト用魔法データの設定が可能

## 実装詳細

### known_spells属性仕様
```python
class Character:
    def __init__(self, ...):
        self.known_spells: List[str] = []  # 魔法IDのリスト
    
    def learn_spell(self, spell_id: str) -> bool:
        """魔法を習得"""
        pass
    
    def forget_spell(self, spell_id: str) -> bool:
        """魔法を忘却"""
        pass
    
    def has_spell(self, spell_id: str) -> bool:
        """魔法を習得しているか確認"""
        pass
```

### 職業制限
- **mage**: 魔術のみ習得可能
- **priest**: 祈祷のみ習得可能
- **bishop**: 魔術と祈祷の両方習得可能
- **lord**: 魔術と祈祷の両方習得可能（制限レベルあり）

### 初期魔法設定
- キャラクター作成時にレベル1の基本魔法を自動習得
- テスト環境用の魔法データ設定機能

## Notes

- この実装は宿屋の魔法管理機能（チケット250721-060706）の前提条件
- 魔術書使用による魔法習得システムとの統合が重要
- 既存のSpellManagerとの連携を考慮した設計
- セーブデータの互換性を保つための注意が必要
- テスト用データの提供で開発効率を向上
