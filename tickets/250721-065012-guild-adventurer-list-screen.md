---
priority: 2
tags: ["feature", "ui", "guild", "adventurer-list", "character"]
description: "冒険者ギルドの冒険者一覧画面の実装"
created_at: "2025-07-21T06:50:12Z"
started_at: null  # Do not modify manually
closed_at: null   # Do not modify manually
---

# Ticket Overview

冒険者ギルドの冒険者一覧機能が「実装中」状態となっており、実際の機能が利用できない。冒険者一覧は、登録されている全キャラクターを管理・確認するための重要な機能であり、パーティ編成や個別キャラクター管理に必須の機能として完全実装する必要がある。

## 背景
- 冒険者ギルドのメニューに「冒険者一覧」項目は存在
- 選択すると「実装中」メッセージが表示される
- 冒険者一覧はキャラクター管理の中核機能
- パーティ編成や個別ステータス確認に必要

## Tasks

- [ ] 現在の冒険者ギルドUIとキャラクター管理システムの調査
- [ ] 冒険者一覧画面のUIデザイン設計
- [ ] 登録済みキャラクター取得・表示機能の実装
- [ ] キャラクター基本情報表示（名前、レベル、職業、状態）
- [ ] キャラクター詳細情報表示機能
- [ ] キャラクターソート・フィルタリング機能
- [ ] キャラクター選択・操作メニューの実装
- [ ] パーティメンバー表示（現在のパーティ状態）
- [ ] 死亡・状態異常キャラクターの区別表示
- [ ] キャラクター削除機能の実装
- [ ] ページネーション機能（多数キャラクター対応）
- [ ] 検索機能の実装（名前、職業等で絞り込み）
- [ ] キャラクター詳細画面への遷移機能
- [ ] 日本語テキストの実装
- [ ] ユニットテストの作成
- [ ] 統合テストの実施
- [ ] Run tests before closing and pass all tests (No exceptions)
- [ ] Get developer approval before closing

## 受け入れ条件
- [ ] 冒険者一覧画面が正常に表示される
- [ ] 登録済み全キャラクターが一覧表示される
- [ ] 各キャラクターの基本情報が確認できる
- [ ] キャラクターを選択して詳細情報が確認できる
- [ ] 現在のパーティメンバーが識別できる
- [ ] 死亡・状態異常キャラクターが区別表示される
- [ ] キャラクターの削除が可能
- [ ] ソート・フィルタリングが正常に動作する
- [ ] すべてのテキストが日本語で表示される

## Notes

- 表示する基本情報：
  - キャラクター名
  - 種族・職業
  - レベル
  - HP/最大HP
  - 状態（正常、死亡、状態異常等）
  - パーティメンバー状況
- ソート条件：
  - 名前順（あいうえお順）
  - レベル順（昇順・降順）
  - 職業別
  - 作成日順
- フィルター条件：
  - 職業別
  - 状態別（正常、死亡等）
  - パーティ状況別
- キャラクター操作：
  - 詳細表示
  - パーティ編成への追加/除去
  - キャラクター削除（確認ダイアログ付き）
- 1画面あたりの表示数：10-20キャラクター程度
