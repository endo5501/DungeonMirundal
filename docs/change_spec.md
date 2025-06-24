# Change Specification

変更を希望する仕様について記述する
新仕様(New Specifications)に記載されている仕様を検討し、修正を行ってください
修正後、必ずテストを実施し、変更された仕様(Changed Specifications)へ移動してください

## New Specifications

## Changed Specifications

### 実装済み (2025-06-24)

* [x] 地上画面、およびダンジョン画面で、画面下部にキャラクターの画像(現状は空の領域。後で画像を配置する)、名前、現在HP/最大HPを6つ並べて表示出来るようにする
  - 実装内容: キャラクターステータスバーUIコンポーネントを新規作成
  - 機能: 
    - 画面下部（y=668）に100ピクセル高のステータスバーを配置
    - 6つのキャラクタースロット（各170ピクセル幅）
    - 各スロット内容：キャラクター画像プレースホルダー、名前、現在HP/最大HP
    - HPバー（緑/オレンジ/赤で状態表示）
    - キャラクター状態に応じた画像枠色変更
  - 実装ファイル:
    - `src/ui/character_status_bar.py`: 新規UIコンポーネント
    - `src/overworld/overworld_manager_pygame.py`: 地上画面への統合
    - `src/ui/dungeon_ui_pygame.py`: ダンジョン画面への統合
    - `src/rendering/dungeon_renderer_pygame.py`: ダンジョンレンダラーへの統合
  - テスト: `test_character_status_bar.py`で11項目のテストが全て通過
  - 特徴:
    - パーティメンバーの自動表示/更新
    - 空スロットの適切な表示
    - 日本語フォント対応
    - 異なる画面サイズに対応
    - 状態異常（負傷、意識不明、死亡）の視覚的表示

