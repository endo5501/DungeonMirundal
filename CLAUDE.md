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

## Gemini CLI 連携ガイド

### 目的

ユーザーが **「Geminiと相談しながら進めて」** (または同義語)と指示した場合、または非常に困難なタスクに出会った際、Claude は以降のタスクを **Gemini CLI** と協調しながら進める。
Gemini から得た回答はそのまま提示し、Claude 自身の解説・統合も付け加えることで、両エージェントの知見を融合する。

---

### トリガー

- 正規表現: `/Gemini.*相談しながら/`
- 例:
- 「Geminiと相談しながら進めて」
- 「この件、Geminiと話しつつやりましょう」

---

### 基本フロー

1. **PROMPT 準備**
Claude はユーザーの要件を簡潔にまとめる（長すぎる場合は要点を抽出）

2. **Gemini CLI 呼び出し**
**推奨方法**: `-p`オプションを使用

```bash
gemini -p "相談内容をここに記述"
```

**避けるべき方法**: 

- HERE-DOC構文（EOFエラーの原因）
- 長すぎる引数（引数エラーの原因）

### 実用例

**成功パターン**:
```bash
gemini -p "Pythonプロジェクトのproject_structure.mdを更新したい。現在の構造：config/（設定）、src/（ソース）、tests/（テスト）。Pygame使用、TDD開発。更新案を提案してください。"
```

**避けるべきパターン**:
```bash
# ❌ HERE-DOC（EOFエラー）
gemini <<EOF
長いテキスト...
EOF

# ❌ 長すぎる直接引数（引数エラー）
gemini "非常に長いテキストが続く..."
```

### トラブルシューティング

- **EOFエラー**: HERE-DOC構文を避け、`-p`オプションを使用
- **引数エラー**: テキストを要約して短縮、または複数回に分割
- **Unknown argument**: テキストが引数として認識されない場合は`-p`で明示的にプロンプト指定
