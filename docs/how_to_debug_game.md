# ゲームデバッグガイド - 効率的なデバッグ方法

## 概要

Dungeonゲームの開発時に利用可能なデバッグツールとAPIについて説明します。ゲーム起動時に自動的にデバッグAPIサーバーが起動し、外部から制御・監視できます。

## 基本設定

- **ベースURL**: `http://localhost:8765`
- **起動方法**: `./scripts/start_game_for_debug.sh` でゲームと同時にAPIサーバーが起動。 `uv run main.py&` はCalude Codeが実行すると処理が戻らなくなるため、使用してはならない
- **プロトコル**: REST API（HTTP）

## 推奨デバッグ方法

### 1. Python APIクライアント（推奨）

最も簡単で柔軟なデバッグ方法です。

```python
from src.debug.game_debug_client import GameDebugClient

client = GameDebugClient()
if client.wait_for_api():
    # スクリーンショット取得
    client.screenshot("debug.jpg")
    
    # マウス操作（座標指定）
    client.send_mouse(400, 300, "down")  # 特定座標をクリック
    client.send_mouse(400, 300, "up")    # ボタンを離す
    
    # UI階層情報確認
    hierarchy = client.get_ui_hierarchy()
    print(f"Window stack: {hierarchy.get('window_stack')}")
    
    # パーティ情報確認
    party_info = client.get_party_info()
    client.display_party_info(party_info)
    
    # キャラクター詳細確認
    char_info = client.get_character_details(0)
    client.display_character_details(0, char_info)
```

### 2. コマンドライン

```bash
# スクリーンショット保存
uv run python src/debug/game_debug_client.py screenshot --save debug.jpg

# 座標クリック
uv run python src/debug/game_debug_client.py mouse --x 400 --y 300

# ESCキー送信
uv run python src/debug/game_debug_client.py escape

# 特定キーコード送信
uv run python src/debug/game_debug_client.py key --code 27

# UI階層をJSON形式で表示
uv run python -m src.debug.debug_cli ui-dump --format json

# UI階層をツリー形式で表示
uv run python -m src.debug.debug_cli ui-dump --format tree

# パーティ情報取得
uv run python src/debug/game_debug_client.py party

# キャラクター詳細情報取得（インデックス0のキャラクター）
uv run python src/debug/game_debug_client.py party_character 0

# 冒険者ギルド登録キャラクター一覧
uv run python src/debug/game_debug_client.py adventure_list

# GameManagerデバッグ情報確認（セーブ・ロード問題の診断）
uv run python src/debug/game_debug_client.py debug_gm
```

### 3. 便利関数

```python
from src.debug.debug_helper import (
    quick_debug_esc_issue,
    quick_test_button_navigation,
    test_all_visible_buttons
)

# ESC遷移問題を素早くデバッグ
quick_debug_esc_issue()

# ボタンナビゲーション機能をテスト
quick_test_button_navigation()

# すべてのボタンをテスト
test_all_visible_buttons()
```

## 主要なAPIエンドポイント

### 基本機能 ✅ 全て利用可能

| エンドポイント | 機能 | レスポンス時間 | 例 |
|---------------|------|------------|-----|
| `GET /screenshot` | スクリーンショット取得 | ~15ms | `curl "http://localhost:8765/screenshot"` |
| `POST /input/key` | キー入力送信 | ~1ms | `curl -X POST "http://localhost:8765/input/key?code=27&down=true"` |
| `POST /input/mouse` | マウス入力送信 | ~1ms | `curl -X POST "http://localhost:8765/input/mouse?x=400&y=300&action=down"` |

### UI階層監視 ✅ 利用可能

| エンドポイント | 機能 | レスポンス時間 | レスポンス例 |
|---------------|------|------------|------------|
| `GET /ui/hierarchy` | UI階層情報取得 | ~1ms | `{"window_stack": ["OverworldMainWindow(...)"], "window_manager_available": true}` |

**提供される情報:**
- WindowManagerの可用性
- リアルタイムウィンドウスタック情報
- 最小限の安全な階層データ

### 入力履歴管理 ✅ 全て利用可能

| エンドポイント | 機能 | レスポンス時間 | 例 |
|---------------|------|------------|-----|
| `GET /history` | 入力履歴取得 | ~1ms | `curl "http://localhost:8765/history"` |
| `DELETE /history` | 履歴クリア | ~2ms | `curl -X DELETE "http://localhost:8765/history"` |

### パーティ・キャラクター情報 ✅ 全て利用可能

| エンドポイント | 機能 | レスポンス時間 | 例 |
|---------------|------|------------|-----|
| `GET /party/info` | パーティ情報取得 | ~1ms | `curl "http://localhost:8765/party/info"` |
| `GET /party/character/{index}` | キャラクター詳細取得 | ~1ms | `curl "http://localhost:8765/party/character/0"` |
| `GET /adventure/list` | 冒険者ギルドリスト取得 | ~1ms | `curl "http://localhost:8765/adventure/list"` |

### デバッグ・診断情報 ✅ 全て利用可能

| エンドポイント | 機能 | レスポンス時間 | 例 |
|---------------|------|------------|-----|
| `GET /debug/game_manager` | GameManagerアクセス診断 | ~1ms | `curl "http://localhost:8765/debug/game_manager"` |

**パーティ・キャラクター情報で提供される情報:**
- パーティ名、ID、所持金
- パーティメンバーの基本情報（名前、レベル、HP/MAX_HP、状態）
- キャラクター詳細（種族、職業、ステータス、装備・所持アイテム）
- 冒険者ギルド登録キャラクター一覧

**デバッグ・診断情報で提供される情報:**
- GameManagerインスタンスの存在・状態確認
- パーティオブジェクトへのアクセス状況
- セーブ・ロード後の参照整合性診断
- 複数の取得方法（キャッシュ、main.py、sys.modules）の成功/失敗状況


## 注意: ボタンナビゲーション機能は制限あり

現在のボタン情報取得機能は技術的制約により実用的な情報を提供できません。代替として、座標指定によるマウス操作を使用してください。

## よくあるデバッグシナリオ

### 1. 施設画面の動作確認

```python
client = GameDebugClient()

# 初期状態を確認
client.screenshot("initial.jpg")

# UI階層情報を確認
hierarchy = client.get_ui_hierarchy()
print(f"Current windows: {hierarchy.get('window_stack')}")

# ESCキー操作
client.press_escape()  # または client.send_key(27)
client.screenshot("after_escape.jpg")
```

### 2. マウス操作テスト

```python
client = GameDebugClient()

# 特定座標でのクリックテスト
test_coordinates = [(400, 300), (500, 400), (300, 200)]

for x, y in test_coordinates:
    client.send_mouse(x, y, action="down")
    client.screenshot(f"click_{x}_{y}.jpg")
    client.send_mouse(x, y, action="up")
```

### 3. ESC遷移問題のデバッグ

```python
from src.debug.debug_helper import quick_debug_esc_issue

# ESC遷移を自動検証
quick_debug_esc_issue()
```

### 4. パーティ・キャラクター情報のデバッグ

```python
client = GameDebugClient()

# パーティ情報の取得と表示
print("=== パーティ情報の確認 ===")
client.display_party_info()

# 全キャラクターの詳細確認
party_info = client.get_party_info()
if party_info and party_info.get("party_exists"):
    character_count = party_info.get("character_count", 0)
    for i in range(character_count):
        print(f"\n=== キャラクター {i} の詳細 ===")
        client.display_character_details(i)

# 冒険者ギルドの確認
print("\n=== 冒険者ギルド登録キャラクター ===")
client.display_adventure_guild_list()
```

### 5. セーブ・ロード問題のデバッグ

```python
client = GameDebugClient()

# セーブ前の状態確認
print("=== セーブ前の状態 ===")
debug_info = client.get_game_manager_debug_info()
if debug_info:
    print(f"GameManager存在: {debug_info.get('game_manager_exists')}")
    print(f"パーティ存在: {debug_info.get('current_party_exists')}")
    
    retrieval_debug = debug_info.get('retrieval_debug', {})
    print(f"キャッシュから取得可能: {retrieval_debug.get('cached_manager_exists')}")
    print(f"main.pyから取得可能: {retrieval_debug.get('main_manager_exists')}")

# ゲーム内でセーブを実行（手動）

# セーブ後の状態確認
print("\n=== セーブ後の状態 ===")
debug_info = client.get_game_manager_debug_info()
if debug_info:
    print(f"GameManager存在: {debug_info.get('game_manager_exists')}")
    print(f"パーティ存在: {debug_info.get('current_party_exists')}")
    
    retrieval_debug = debug_info.get('retrieval_debug', {})
    print(f"キャッシュから取得可能: {retrieval_debug.get('cached_manager_exists')}")
    print(f"main.pyから取得可能: {retrieval_debug.get('main_manager_exists')}")

# パーティ情報が正常に取得できるかテスト
party_info = client.get_party_info()
if party_info and party_info.get("party_exists"):
    print(f"\n✅ パーティ情報取得成功: {party_info['party_name']}")
else:
    print("\n❌ パーティ情報取得失敗")
```

## テスト統合

### pytest での使用

```python
def test_ui_hierarchy(game_api_client):
    """ユーザーインターフェース階層のテスト"""
    # UI階層情報を取得
    hierarchy = game_api_client.get_ui_hierarchy()
    assert hierarchy['window_manager_available'] is True
    assert 'window_stack' in hierarchy
    
def test_screenshot_capture(game_api_client):
    """スクリーンショットキャプチャのテスト"""
    screenshot = game_api_client.get_screenshot()
    assert 'jpeg' in screenshot
    assert 'timestamp' in screenshot
    assert screenshot['size'][0] > 0 and screenshot['size'][1] > 0

def test_party_info(game_api_client):
    """パーティ情報取得のテスト"""
    party_info = game_api_client.get_party_info()
    assert party_info is not None
    assert 'party_exists' in party_info
    assert 'gold' in party_info
    assert 'characters' in party_info
    assert 'character_count' in party_info

def test_character_details(game_api_client):
    """キャラクター詳細取得のテスト"""
    # まずパーティ情報を取得してキャラクターが存在するか確認
    party_info = game_api_client.get_party_info()
    if party_info and party_info.get('party_exists') and party_info.get('character_count', 0) > 0:
        char_info = game_api_client.get_character_details(0)
        assert char_info is not None
        assert 'character_exists' in char_info
        if char_info.get('character_exists'):
            assert 'name' in char_info
            assert 'race' in char_info
            assert 'character_class' in char_info

def test_adventure_guild_list(game_api_client):
    """冒険者ギルドリスト取得のテスト"""
    guild_info = game_api_client.get_adventure_guild_list()
    assert guild_info is not None
    assert 'guild_characters_count' in guild_info
    assert 'guild_characters' in guild_info

def test_game_manager_debug_info(game_api_client):
    """GameManagerデバッグ情報取得のテスト"""
    debug_info = game_api_client.get_game_manager_debug_info()
    assert debug_info is not None
    assert 'game_manager_exists' in debug_info
    assert 'retrieval_debug' in debug_info
    assert 'timestamp' in debug_info
    
    retrieval_debug = debug_info.get('retrieval_debug', {})
    assert 'cached_manager_exists' in retrieval_debug
    assert 'main_module_exists' in retrieval_debug
```

### 統合テストの実行

```bash
# 通常のテスト
uv run pytest

# 統合テストを含む
uv run pytest -m "integration"

# UI階層テスト
uv run pytest tests/debug/test_ui_hierarchy.py -v
```

## デバッグツール一覧

### ファイル構成

```
src/debug/
├── game_debug_client.py      # Python APIクライアント
├── debug_helper.py           # 高レベルデバッグ機能
├── ui_debug_helper.py        # UI階層デバッグ
├── debug_cli.py              # CLI UI階層ダンプツール
├── debug_middleware.py       # 自動エラーログ強化
└── enhanced_logger.py        # 拡張ログシステム

tests/debug/
└── test_ui_hierarchy.py      # UI階層テスト

scripts/
└── start_game_for_debug.sh   # ゲーム自動起動
```

### 使用場面別推奨ツール

| 場面 | 推奨ツール |
|------|------------|
| 日常的なデバッグ | Python APIクライアント |
| マウス操作テスト | 座標指定クリック |
| 自動テスト | pytest + フィクスチャ |
| 複雑なシナリオ | DebugHelper |
| UI構造確認 | debug_cli |
| エラー詳細追跡 | EnhancedGameLogger |
| メソッドデバッグ | DebugMiddleware |

## UI階層デバッグ ✅ 利用可能（安全モード）

### UI階層ダンプツール

ゲームのUI階層を**安全モード**で調査できます。

```bash
# UI階層をJSON形式で表示（推奨）
uv run python -m src.debug.debug_cli ui-dump --format json

# ツリー形式で表示（基本情報のみ）
uv run python -m src.debug.debug_cli ui-dump --format tree

# ファイルに保存
uv run python -m src.debug.debug_cli ui-dump --save ui_hierarchy.json
```

### 取得可能な情報（現在の実装）

**JSON形式:**
```json
{
  "windows": [],
  "ui_elements": [
    {
      "object_id": "#root_container",
      "type": "UIContainer",
      "visible": true,
      "children": [
        {
          "object_id": "None",
          "type": "UIButton",
          "visible": true,
          "text": "冒険者ギルド",
          "shortcut_key": "1",
          "menu": {
            "label": "冒険者ギルド",
            "id": "guild",
            "enabled": true
          }
        }
      ]
    }
  ],
  "window_stack": [
    "OverworldMainWindow(overworld_main, main, stack_depth=0)"
  ],
  "metadata": {
    "format": "enhanced_json",
    "includes_shortcuts": true,
    "includes_hierarchy": true
  }
}
```

**Tree形式:**
```
UI Hierarchy Tree:
├── Window Stack:
│   └── OverworldMainWindow(overworld_main, main, stack_depth=0)
└── UI Elements:
    └── UIContainer (#root_container) [visible]
        ├── UIButton (None) [visible] (text='冒険者ギルド', key=1, label='冒険者ギルド', id=guild)
        ├── UIButton (None) [visible] (text='宿屋', key=2, label='宿屋', id=inn)
        └── UIButton (None) [visible] (text='商店', key=3, label='商店', id=shop)
```

### Python APIでの使用

```python
from src.debug.game_debug_client import GameDebugClient

client = GameDebugClient()
hierarchy = client.get_ui_hierarchy()

# ウィンドウスタックの確認
window_stack = hierarchy.get('window_stack', [])
print(f"現在のウィンドウ: {len(window_stack)}個")

# WindowManagerの利用可能性
wm_available = hierarchy.get('window_manager_available', False)
print(f"WindowManager: {'利用可能' if wm_available else '利用不可'}")
```

### APIエンドポイント

| エンドポイント | 機能 | レスポンス時間 | 実装状況 |
|---------------|------|------------|---------|
| `GET /ui/hierarchy` | UI階層情報取得（安全モード） | ~1ms | ✅ 完全動作 |

**注意**: 現在の実装は安全性を重視し、最小限の情報のみ提供します。詳細なUI要素情報は今後の拡張で追加予定です。

## 拡張ログシステム

### EnhancedGameLogger

エラー発生時により詳細な情報を記録する拡張ログシステムです。

```python
from src.debug.enhanced_logger import get_enhanced_logger

logger = get_enhanced_logger("my_game_module")

# コンテキスト付きログ
logger.push_context({"state": "loading", "file": "map.json"})
logger.log_with_context(logging.INFO, "Loading map data")

# UI要素エラーの詳細ログ
try:
    # UI操作
    pass
except Exception as e:
    logger.log_ui_error(e, ui_element=button)
```

### DebugMiddleware

メソッドを自動的にラップして、エラー時の詳細情報を記録します。

```python
from src.debug.debug_middleware import DebugMiddleware

# ゲームインスタンスに適用
with DebugMiddleware(game_instance):
    game_instance.run()

# 特定のメソッドのみラップ
middleware = DebugMiddleware(game_instance)
middleware.wrap_methods(['handle_event', 'update'])
```

## デバッグセッション管理

### DebugSession

ゲームプロセスの自動起動・停止を管理します。

```python
from src.debug.debug_helper import DebugSession

# 自動起動モード
with DebugSession(auto_start=True) as session:
    # デバッグ処理
    client = session.client
    client.screenshot("debug.jpg")

# 手動管理モード
session = DebugSession(auto_start=False)
session.start_game()
# デバッグ処理
session.stop_game()
```

## トラブルシューティング

### APIサーバーが起動しない

1. ゲームが正常に起動しているか確認: `./scripts/start_game_for_debug.sh`
2. ポート8765が使用中でないか確認: `lsof -i :8765`
3. ファイアウォール設定を確認

### マウス操作が失敗する

```python
# 画面サイズを確認
screenshot = client.get_screenshot()
screen_size = screenshot['size']
print(f"Screen size: {screen_size}")

# 座標指定でクリック（確実）
if x < screen_size[0] and y < screen_size[1]:
    client.send_mouse(x, y, "down")
    client.send_mouse(x, y, "up")
```

### スクリーンショットが取得できない

```bash
# API動作確認
curl -I "http://localhost:8765/screenshot"

# 詳細確認
curl "http://localhost:8765/screenshot" | jq .
```

### セーブ・ロード後にパーティ情報が取得できない

```bash
# GameManagerの状態確認
uv run python src/debug/game_debug_client.py debug_gm

# パーティ情報取得をリトライ
uv run python src/debug/game_debug_client.py party

# デバッグ情報とパーティ情報を連続確認
curl "http://localhost:8765/debug/game_manager" | jq .
curl "http://localhost:8765/party/info" | jq .
```

**対処法**:
1. ゲームを再起動して問題が解決するか確認
2. `debug_gm`コマンドで取得方法の診断を実行
3. ログを確認して動的取得が正常に機能しているかチェック

## 高度なデバッグ機能

### 新機能: パーティ・キャラクター情報の活用

```python
client = GameDebugClient()

# パーティ状態の監視ループ
def monitor_party_status():
    """パーティ状態を定期的に監視"""
    while True:
        party_info = client.get_party_info()
        if party_info and party_info.get("party_exists"):
            print(f"パーティ: {party_info['party_name']} - {party_info['gold']}G")
            
            # HP状況をチェック
            for i, char in enumerate(party_info.get("characters", [])):
                hp_ratio = char['hp'] / max(char['max_hp'], 1)
                status = "🟢" if hp_ratio > 0.7 else "🟡" if hp_ratio > 0.3 else "🔴"
                print(f"  {status} {char['name']}: {char['hp']}/{char['max_hp']} HP")
        
        time.sleep(5)

# 特定キャラクターの装備チェック
def check_character_equipment(character_index=0):
    """キャラクターの装備状況を詳しく分析"""
    char_info = client.get_character_details(character_index)
    if char_info and char_info.get("character_exists"):
        print(f"=== {char_info['name']} の装備分析 ===")
        
        equipment = char_info.get("equipment", [])
        equipment_slots = {}
        for item in equipment:
            equipment_slots[item['slot']] = item['item_name']
        
        # 必要な装備スロットをチェック
        required_slots = ['weapon', 'armor', 'shield', 'helmet']
        for slot in required_slots:
            if slot in equipment_slots:
                print(f"✓ {slot}: {equipment_slots[slot]}")
            else:
                print(f"✗ {slot}: 未装備")

# 冒険者ギルドの管理状況確認
def analyze_guild_management():
    """冒険者ギルドの管理状況を分析"""
    guild_info = client.get_adventure_guild_list()
    party_info = client.get_party_info()
    
    guild_count = guild_info.get("guild_characters_count", 0)
    party_count = party_info.get("character_count", 0) if party_info.get("party_exists") else 0
    
    print(f"登録キャラクター数: {guild_count}")
    print(f"パーティメンバー数: {party_count}")
    print(f"ベンチキャラクター数: {guild_count - party_count}")
    
    if guild_count > 0:
        # レベル分布
        levels = [char.get('level', 1) for char in guild_info.get("guild_characters", [])]
        avg_level = sum(levels) / len(levels)
        print(f"平均レベル: {avg_level:.1f}")
```

### 画面遷移の連続キャプチャ

```python
from src.debug.debug_helper import DebugHelper

helper = DebugHelper()

# アクションシーケンスを定義
actions = [
    ("number", 1),           # 1番ボタンをクリック
    ("wait", 1),             # 1秒待機
    ("escape", None),        # ESCキー
    ("button_text", "設定"), # テキストでボタンクリック
    ("wait", 0.5),
    ("screenshot", None)
]

# 各アクション後の画面をキャプチャ
captured_files = helper.capture_transition_sequence(actions, "debug_sequence")
```

### スクリーンショット比較

```python
# 2つのスクリーンショットを比較
result = helper.compare_screenshots("before.jpg", "after.jpg")
print(f"画像が同一: {result['identical']}")
print(f"平均差分: {result['mean_difference']}")
```

### GameManagerデバッグ機能の活用

```python
client = GameDebugClient()

# セーブ・ロード時の参照問題診断
def diagnose_save_load_issue():
    """セーブ・ロード時のGameManager参照問題を診断"""
    print("=== GameManager診断開始 ===")
    
    # 現在の状態確認
    debug_info = client.get_game_manager_debug_info()
    if debug_info:
        print(f"診断時刻: {debug_info.get('timestamp')}")
        print(f"GameManager存在: {debug_info.get('game_manager_exists')}")
        print(f"パーティアクセス可能: {debug_info.get('current_party_exists')}")
        
        retrieval_debug = debug_info.get('retrieval_debug', {})
        print("\n--- 取得方法別診断 ---")
        print(f"キャッシュ: {'✅' if retrieval_debug.get('cached_manager_exists') else '❌'}")
        print(f"main.py: {'✅' if retrieval_debug.get('main_manager_exists') else '❌'}")
        print(f"sys.modules: {'✅' if retrieval_debug.get('sys_modules_main_exists') else '❌'}")
        
        # 実際のパーティアクセステスト
        party_info = client.get_party_info()
        if party_info and party_info.get('party_exists'):
            print(f"\n✅ パーティ情報取得成功: {party_info['party_name']}")
        else:
            print("\n❌ パーティ情報取得失敗 - セーブ・ロード問題の可能性")
    else:
        print("❌ デバッグ情報の取得に失敗")

# パフォーマンス監視
def monitor_api_performance():
    """APIレスポンス時間を監視"""
    import time
    
    operations = [
        ("party_info", lambda: client.get_party_info()),
        ("debug_info", lambda: client.get_game_manager_debug_info()),
        ("screenshot", lambda: client.get_screenshot())
    ]
    
    for name, operation in operations:
        start_time = time.time()
        result = operation()
        elapsed = (time.time() - start_time) * 1000
        status = "✅" if result else "❌"
        print(f"{status} {name}: {elapsed:.2f}ms")
```

### UI階層の取得（実際の動作例）

```python
# GameDebugClient経由でUI階層を取得
hierarchy = client.get_ui_hierarchy()
if hierarchy:
    print(f"WindowManager: {hierarchy.get('window_manager_available')}")
    print(f"ウィンドウスタック: {hierarchy.get('window_stack')}")
    print(f"ステータス: {hierarchy.get('status')}")

# 実際の出力例:
# WindowManager: True
# ウィンドウスタック: ['OverworldMainWindow(overworld_main, main, stack_depth=0)']
# ステータス: minimal_info_only
```

## APIキーコードリファレンス

主要なキーコード:

| キー | コード |
|------|--------|
| ESC | 27 |
| Enter | 13 |
| Space | 32 |
| 数字1-9 | 49-57 |
| A-Z | 97-122 |
| 矢印キー | 273-276 |

## フォント関連問題

フォント表示（特に日本語文字化け）に関する問題については、専用ドキュメントを参照してください：

- **包括的ガイド**: [@docs/font_system_guide.md](./font_system_guide.md)
- **pygame_gui統合**: [@docs/pygame_gui_font_integration.md](./pygame_gui_font_integration.md)  
- **問題解決**: [@docs/font_troubleshooting_checklist.md](./font_troubleshooting_checklist.md)
- **テストサンプル**: [@docs/samples/font_tests/](./samples/font_tests/)

## まとめ

**🎉 Dungeonゲームのデバッグシステム (2025年7月12日 現在)**

### ✅ 完全利用可能な機能

1. **高速APIエンドポイント**: 全12個のエンドポイントが1-15msで応答
   - スクリーンショット取得
   - キー・マウス入力送信
   - ゲーム状態監視
   - UI階層情報取得（安全モード）
   - 入力履歴管理
   - **新機能**: パーティ情報取得
   - **新機能**: キャラクター詳細取得
   - **新機能**: 冒険者ギルドリスト取得
   - **新機能**: GameManagerデバッグ情報取得

2. **UI監視機能**:
   - WindowManagerからのリアルタイムウィンドウ情報
   - 安全なUI階層デバッグ

3. **パーティ・キャラクター監視機能** (新機能):
   - パーティ基本情報（名前、所持金、メンバー数）
   - キャラクター詳細情報（ステータス、装備、アイテム）
   - 冒険者ギルド登録キャラクター管理

4. **開発ツール**:
   - Python APIクライアント
   - CLIツール
   - 拡張ログシステム
   - **新機能**: セーブ・ロード問題診断ツール

### ⚠️ 使用上の注意

- ボタン情報取得機能は技術的制約により利用不可
- ゲーム状態詳細はアクセス制限により取得不可
- マウス操作は座標指定でのみ対応

これらの制限を理解した上で、安全で効率的なゲームデバッグを実現できます。