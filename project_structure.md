# プロジェクト構造設計

## ディレクトリ構成

```
dungeon/
├── main.py                 # エントリーポイント
├── config/                 # 設定ファイル
│   ├── game_config.yaml   # ゲーム設定
│   ├── characters.yaml    # キャラクター定義
│   ├── items.yaml         # アイテム定義
│   ├── monsters.yaml      # モンスター定義
│   ├── spells.yaml        # 魔術・祈祷定義
│   └── text/              # 多言語対応テキスト
│       ├── ja.yaml        # 日本語
│       └── en.yaml        # 英語
├── src/                   # ソースコード
│   ├── core/              # コア機能
│   │   ├── __init__.py
│   │   ├── game_manager.py
│   │   ├── config_manager.py
│   │   ├── save_manager.py
│   │   └── input_manager.py
│   ├── character/         # キャラクター関連
│   │   ├── __init__.py
│   │   ├── character.py
│   │   ├── party.py
│   │   └── stats.py
│   ├── ui/                # UI関連
│   │   ├── __init__.py
│   │   ├── base_ui.py
│   │   ├── menu.py
│   │   ├── inventory.py
│   │   └── dialog.py
│   ├── overworld/         # 地上部
│   │   ├── __init__.py
│   │   ├── facilities/
│   │   │   ├── __init__.py
│   │   │   ├── guild.py
│   │   │   ├── inn.py
│   │   │   ├── shop.py
│   │   │   ├── temple.py
│   │   │   └── magic_guild.py
│   │   └── overworld_manager.py
│   ├── dungeon/           # ダンジョン関連
│   │   ├── __init__.py
│   │   ├── dungeon_generator.py
│   │   ├── dungeon_renderer.py
│   │   ├── navigation.py
│   │   └── encounters.py
│   ├── combat/            # 戦闘システム
│   │   ├── __init__.py
│   │   ├── combat_manager.py
│   │   ├── monster.py
│   │   └── battle_ui.py
│   ├── items/             # アイテムシステム
│   │   ├── __init__.py
│   │   ├── item.py
│   │   ├── inventory.py
│   │   └── equipment.py
│   └── utils/             # ユーティリティ
│       ├── __init__.py
│       ├── constants.py
│       ├── helpers.py
│       └── logger.py
├── assets/                # リソース
│   ├── models/           # 3Dモデル
│   ├── textures/         # テクスチャ
│   ├── sounds/           # サウンド
│   └── ui/               # UI画像
├── saves/                # セーブデータ
├── tests/                # テストファイル
├── docs/                 # 開発計画・TODO管理
│   ├── phase1_todos.md
│   ├── phase2_todos.md
│   ├── phase3_todos.md
│   ├── phase4_todos.md
│   └── phase5_todos.md
├── pyproject.toml
├── CLAUDE.md
└── README.md
```

## 設計方針

### モジュール分離
- 各機能を独立したモジュールとして設計
- 依存関係を最小限に抑制
- テスト容易性を重視

### 設定外部化
- ハードコーディング禁止
- YAML形式での設定管理
- 多言語対応のテキスト分離

### データ管理
- キャラクター、アイテム、モンスター等の定義は外部ファイル
- セーブデータの構造化
- 設定変更の動的反映