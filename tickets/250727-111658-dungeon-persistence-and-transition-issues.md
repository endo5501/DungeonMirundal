---
priority: 1
tags: ["bug", "critical", "dungeon-system", "save-load", "persistence", "scene-transition"]
description: "ダンジョン生成後の永続化とシーン遷移に関する重大な問題"
created_at: "2025-07-27T11:16:58Z"
started_at: null  # Do not modify manually
closed_at: null   # Do not modify manually
---

# ダンジョンの永続化と遷移システムの問題

セーブデータを完全削除した状態で新規ゲームを開始し、ダンジョンを生成した際に発生する複数の重大な問題：

## 問題1: ダンジョンデータの永続化失敗
- ダンジョン生成時に`./save/dungeon/`ディレクトリとハッシュ値のみ作成される
- 実際のダンジョンデータ（フロア構造、モンスター配置等）がセーブされない
- セーブ後に再起動してロードすると、生成したダンジョンが消失する

## 問題2: ダンジョンシーン遷移失敗
- 新規生成ダンジョンに入ろうとすると「ダンジョンシーンに切り替え失敗」と表示
- エラー: `'DungeonManager' object has no attribute 'active_dungeons'`
- ダンジョンに入れずに地上に戻される

### 再現手順
1. `./save/`ディレクトリを完全削除
2. ゲーム起動（新規ゲーム状態）
3. ダンジョン入り口に入る
4. 新規ダンジョンを生成
5. 地上に戻ってセーブ
6. ゲーム再起動・ロード
7. ダンジョン入り口に入る → **生成したダンジョンが消失**
8. 新規ダンジョン生成後、そのまま入場を試行 → **遷移失敗**

### ログからの証拠
- `WARNING - ダンジョン情報の保存に失敗しました` (line 110)
- `WARNING - SaveManager or current_save not available for dungeon list` (line 277)
- `ERROR - ダンジョン入場エラー: 'DungeonManager' object has no attribute 'active_dungeons'` (line 159)
- `セーブデータから 0 のダンジョンを読み込みました` (line 289) - 生成したダンジョンが保存されていない

## Tasks

- [ ] SaveManagerでのダンジョンリスト保存処理の問題を調査・修正
- [ ] DungeonManagerの`active_dungeons`属性エラーを解決
- [ ] ダンジョン生成時のファイル永続化タイミングを修正
- [ ] セーブ・ロード時のダンジョンデータ整合性を確保
- [ ] 新規ゲーム状態でのダンジョンシステム初期化を改善
- [ ] ダンジョンシーン遷移処理を修正
- [ ] 永続化されたダンジョンデータの読み込み処理を改善
- [ ] 統合テスト（新規ゲーム→生成→セーブ→ロード→アクセス）を実装
- [ ] Run static analysis (`pyright`) before closing and pass all tests (No exceptions)
- [ ] Run tests (`uv run pytest`) before closing and pass all tests (No exceptions)
- [ ] Get developer approval before closing

## Notes

**優先度: Critical** - ゲームの基本機能（ダンジョン探索）に関わる重大な問題

### 技術的な観点
- SaveManagerのダンジョン情報保存時の警告メッセージが重要な手がかり
- DungeonManagerの構造変更により`active_dungeons`属性が不在の可能性
- ダンジョンファイル生成タイミングと実際のデータ永続化に乖離がある
- 新規ゲーム時の初期化プロセスでダンジョンシステムが不完全な状態になっている

### 影響範囲
- ダンジョン探索機能全般
- セーブ・ロードシステム
- シーン遷移システム
- 新規ゲーム開始プロセス
