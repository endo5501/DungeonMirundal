# デバッグ機能付きpytestフィクスチャの実装

## 概要

pytest実行時に自動的にデバッグ機能を有効化し、テスト失敗時の詳細な情報を提供するフィクスチャを実装する。

## 背景

施設サブメニューのテスト作成時、UI要素の状態やイベントフローを確認する手段が限られており、テスト失敗時の原因特定が困難だった。

## 実装内容

### 1. 基本フィクスチャ

```python
# tests/fixtures/debug_fixtures.py
@pytest.fixture
def game_with_debug():
    """デバッグ機能付きゲームインスタンス"""
    game = Game()
    debug_middleware = DebugMiddleware(game)
    ui_helper = UIDebugHelper(game)
    
    yield DebugGameWrapper(game, debug_middleware, ui_helper)
    
    # テスト終了時に自動的にUI状態を保存
    if hasattr(pytest, 'current_test_failed') and pytest.current_test_failed:
        ui_helper.dump_ui_hierarchy(f"failed_test_{test_name}.json")

@pytest.fixture
def ui_recorder(game_with_debug):
    """UI操作を記録するフィクスチャ"""
    recorder = GameStateRecorder()
    recorder.start_recording()
    
    yield recorder
    
    # テスト終了時に記録を保存
    test_name = request.node.name
    recorder.save_recording(f"test_recording_{test_name}.json")
```

### 2. 高度なアサーション

```python
# tests/helpers/debug_assertions.py
class DebugAssertions:
    @staticmethod
    def assert_ui_element_exists(ui_helper, object_id: str, timeout: float = 5.0):
        """UI要素の存在を確認（タイムアウト付き）"""
        start_time = time.time()
        while time.time() - start_time < timeout:
            element = ui_helper.find_element_by_id(object_id)
            if element:
                return element
            time.sleep(0.1)
        
        # 失敗時は現在のUI階層をダンプ
        current_state = ui_helper.dump_ui_hierarchy()
        pytest.fail(f"UI element '{object_id}' not found. Current UI state:\n{json.dumps(current_state, indent=2)}")
    
    @staticmethod
    def assert_no_errors_in_log(enhanced_logger, since_timestamp: float):
        """指定時刻以降のエラーログを確認"""
        errors = enhanced_logger.get_errors_since(since_timestamp)
        if errors:
            pytest.fail(f"Errors found in log:\n{json.dumps(errors, indent=2)}")
```

### 3. パラメトライズドテスト用フィクスチャ

```python
@pytest.fixture
def facility_test_scenarios():
    """各施設のテストシナリオ"""
    return {
        "guild": {
            "buttons": ["character_creation", "party_management", "character_list"],
            "expected_windows": ["CharacterCreationWizard", "PartyManagementWindow", "CharacterListWindow"]
        },
        "inn": {
            "buttons": ["rest", "item_management", "talk_to_innkeeper"],
            "expected_dialogs": ["RestDialog", "ItemManagementWindow", "InnkeeperDialog"]
        }
    }

@pytest.mark.parametrize("facility,scenario", 
    [(f, s) for f, s in facility_test_scenarios().items()])
def test_facility_buttons(game_with_debug, facility, scenario):
    """施設ボタンの動作を網羅的にテスト"""
    # デバッグ情報付きでテスト実行
```

### 4. スナップショットテスト

```python
@pytest.fixture
def ui_snapshot():
    """UI状態のスナップショットテスト"""
    def _snapshot(name: str, ui_helper: UIDebugHelper):
        current_state = ui_helper.dump_ui_hierarchy()
        snapshot_file = f"tests/snapshots/{name}.json"
        
        if os.path.exists(snapshot_file):
            with open(snapshot_file, 'r') as f:
                expected_state = json.load(f)
            
            diff = DeepDiff(expected_state, current_state, ignore_order=True)
            if diff:
                # 差分を視覚的に表示
                print(f"Snapshot mismatch for '{name}':")
                print(json.dumps(diff, indent=2))
                pytest.fail(f"UI state does not match snapshot")
        else:
            # 初回実行時はスナップショットを作成
            with open(snapshot_file, 'w') as f:
                json.dump(current_state, f, indent=2)
    
    return _snapshot
```

### 5. エラー再現フィクスチャ

```python
@pytest.fixture
def reproduce_error():
    """記録されたエラーを再現"""
    def _reproduce(error_recording_file: str):
        replayer = GameReplayer()
        game = Game()
        
        # エラー発生直前まで再生
        replayer.replay_until_error(error_recording_file, game)
        
        return game, replayer.get_last_state()
    
    return _reproduce
```

## 効果

- テスト失敗時の原因特定時間を60%削減
- UI回帰テストの自動化
- エラー再現テストの容易化

## 優先度

**中** - テスト品質向上に直結

## 関連ファイル

- 新規作成: `tests/fixtures/debug_fixtures.py`
- 新規作成: `tests/helpers/debug_assertions.py`
- 新規作成: `tests/snapshots/`（ディレクトリ）
- 更新: `tests/conftest.py`

## 実装時の注意

- テスト実行速度への影響を最小化
- CI環境での動作確認
- スナップショットファイルのバージョン管理

---

## 実装記録

（実装時に記録）