---
priority: 2
tags: ["cleanup", "mage-guild", "refactor", "removal"]
description: "魔法分析機能を削除し、魔術師ギルドを魔術書購入機能のみに特化"
created_at: "2025-07-21T13:43:09Z"
started_at: null  # Do not modify manually
closed_at: null   # Do not modify manually
---

# Ticket Overview

魔術師ギルドの魔法分析機能を削除し、魔術書購入機能のみに特化する。魔法分析機能は元の機能要件に含まれておらず、ゲームフローとの整合性も低いため、コードの整理とシンプル化を目的として削除する。

## 背景
- 魔法分析機能は元の機能要件に含まれていない後付け機能
- 魔法習得は宿屋で行うため、魔術師ギルドでの分析機能の価値が不明
- 現在の実装はハードコードされたテストデータのみで実用性なし
- 完全実装には多大な工数が必要で工数対効果が低い
- 技術的問題（RecursionError）は修正済みだが機能自体は不要

## Tasks

- [ ] 魔術師ギルドの現在の機能を調査・整理
- [ ] 魔法分析メニュー項目をget_menu_items()から削除
- [ ] SpellAnalysisPanelクラスとファイルを削除
- [ ] MagicGuildServiceから分析関連コードを削除
  - [ ] analyze_magic関連メソッドの削除
  - [ ] execute_spell_analysis関連メソッドの削除
  - [ ] _get_spell_info()等のテストデータメソッドの削除
- [ ] MagicGuildServiceのcreate_service_panel()から分析パネル作成コードを削除
- [ ] テストファイルの削除・修正
  - [ ] test_spell_analysis_panel.pyの削除
  - [ ] magic_guild_service関連テストの更新
- [ ] 不要なインポートの削除
- [ ] 魔術書購入機能のみが正常動作することを確認
- [ ] UIの一貫性確認（ナビゲーションパネル等）
- [ ] ユニットテストの実行・修正
- [ ] 統合テストの実施
- [ ] Run tests before closing and pass all tests (No exceptions)
- [ ] Get developer approval before closing

## 受け入れ条件
- [ ] 魔法分析メニューが魔術師ギルドから削除される
- [ ] SpellAnalysisPanelが完全に削除される
- [ ] MagicGuildServiceに分析関連コードが残存しない
- [ ] 魔術書購入機能が正常に動作する
- [ ] ナビゲーションが適切に更新される
- [ ] 全テストがパスする
- [ ] コードベースが整理され、不要な複雑性が除去される
- [ ] 魔術師ギルドのUIがシンプルで分かりやすくなる

## 削除対象ファイル・コード

### 完全削除対象
- `src/facilities/ui/magic_guild/spell_analysis_panel.py`
- `tests/facilities/test_spell_analysis_panel.py`

### 部分削除対象
- `src/facilities/services/magic_guild_service.py`
  - `analyze_magic`メニュー項目
  - `_handle_analyze_magic()`メソッド
  - `_handle_execute_spell_analysis()`メソッド
  - `_get_characters_with_spells()`メソッド
  - `_get_analyzable_spells_for_character()`メソッド
  - `_get_spell_info()`メソッド（ハードコードデータ）
  - `_get_test_spells_for_class()`メソッド
  - `_confirm_analyze()`、`_execute_analyze()`メソッド
  - SpellAnalysisPanel作成コード

### 保持対象
- 魔術書購入機能（spellbook_shop関連）
- BuyPanelとの連携
- 魔術書在庫生成機能

## Notes

- この作業により魔術師ギルドがシンプルで理解しやすくなる
- 魔術書購入→宿屋での習得という明確なゲームフローに集約
- 不要なコードの削除によりメンテナンス性が向上
- 将来的な機能拡張時の複雑性も軽減
- RecursionError修正作業で得られた知見は他機能の参考になる