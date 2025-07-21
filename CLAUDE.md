# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 開発環境

### パッケージ管理

- `uv` を使用してPythonパッケージを管理
- 依存関係のインストール: `uv install`
- 新しいパッケージの追加: `uv add package_name`

### 実行コマンド

- アプリケーション実行: `python main.py`
- 仮想環境での実行: `uv run python main.py`
- Pygame依存関係追加: `uv add pygame`
- テスト実行: `uv run pytest`

### ゲームデバッグ

@docs/how_to_debug_game.md

### フォントシステム（日本語対応）

プロジェクトでは日本語フォント表示にpygame/pygame_guiを使用しています。

**フォント関連問題が発生した場合**:

- @docs/font_system_guide.md - 包括的ガイド
- @docs/pygame_gui_font_integration.md - pygame_gui技術詳細  
- @docs/font_troubleshooting_checklist.md - 問題解決チェックリスト
- @docs/samples/font_tests/ - 動作テストサンプル

### ソースコード類似度確認

@docs/how_to_plan_refactoring_by_similarity.md

### Gemini CLI との連携ガイド

課題に行き詰まった時、外部AIであるGeminiと相談して、問題の解決方法を検討しましょう

@docs/how_to_talk_with_gemini.md

## プロジェクト構成

### アーキテクチャ概要

- Python製のクラシックなダンジョン探索RPG
- **Pygame**を使用したWizardry風1人称ダンジョン探索
- 2D技術による疑似3D描画でWizardry風視覚表現を実現
- 外部ファイル（JSON/YAML）による設定管理でハードコーディングを回避
- 地上パートとダンジョン探索パートの二つの主要セクション
- WASD + コントローラー対応

### 設計思想

- **外部ファイル管理**: テキスト、キャラクター、アイテム、モンスター等はすべて外部ファイルで管理
- **多言語化対応**: 翻訳ファイルの差し替えによる多言語化
- **モジュール分離**: コンポーネントの独立性を重視した構造
- **ハッシュベース生成**: ダンジョンの構造や難易度をハッシュ値で決定

### 主要機能領域

- **地上部**: 冒険者ギルド、宿屋、商店、教会等の施設管理
- **ダンジョン**: ランダム生成によるWizardry風1人称探索、戦闘システム
- **キャラクター**: 種族・職業・パーティ編成システム
- **アイテム**: 武器・防具・消費アイテムの管理
- **魔術・祈祷**: スロット装備による魔法システム

### 開発方針

- t-wada式のテスト駆動開発（TDD）を採用
- テストファースト、実装は後
- Fowler式リファクタリングを実施
- テストが通過してからコミット
- 修正完了後はまとめてコミット（コミットメッセージは英語）

詳細TODO: `docs/todos/*.md`

## 作業後のTODO管理

- 作業後、TODOファイルを更新してください

## 関連資料

- [Pygame Documentation](https://www.pygame.org/docs/)

# Ticket Management Instructions

Use `./ticket.sh` for ticket management.

## Working with current-ticket.md

### If current-ticket.md exists in project root
- This file is your work instruction - follow its contents
- When receiving additional instructions from users, document them in this file before proceeding
- Continue working on the active ticket

### If current-ticket.md does not exist in project root
- When receiving user requests, first ask whether to create a new ticket
- Do not start work without confirming ticket creation
- Even small requests should be tracked through the ticket system

## Create New Ticket

1. Create ticket: `./ticket.sh new feature-name`
2. Edit ticket content and description in the generated file

## Start Working on Ticket

1. Check available tickets: `./ticket.sh` list or browse tickets directory
2. Start work: `./ticket.sh start 241225-143502-feature-name`
3. Develop on feature branch (`current-ticket.md` shows active ticket)

## Closing Tickets

1. Before closing:
   - Review `current-ticket.md` content and description
   - Check all tasks in checklist are completed (mark with `[x]`)
   - Get user approval before proceeding
2. Complete: `./ticket.sh close`
