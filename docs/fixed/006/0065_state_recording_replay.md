# ゲーム状態記録・再生システムの実装

## 概要

ゲームの状態とイベントを記録し、問題が発生した操作手順を完全に再現できるシステムを実装する。

## 背景

施設サブメニューの問題調査時、「時々発生する」「特定の操作順序で発生する」といった再現困難な問題に遭遇。手動での再現試行は時間がかかり、正確性に欠ける。

## 実装内容

### 1. GameStateRecorderクラスの作成

```python
# src/debug/state_recorder.py
class GameStateRecorder:
    def start_recording(self)
    def stop_recording(self)
    def record_state(self, game_state: Dict[str, Any])
    def record_event(self, event: pygame.event.Event)
    def save_recording(self, filename: str)
    def load_recording(self, filename: str) -> Recording
```

### 2. GameReplayerクラスの作成

```python
# src/debug/game_replayer.py
class GameReplayer:
    def replay_recording(self, recording: Recording, game_instance)
    def replay_until(self, timestamp: float)
    def replay_with_breakpoints(self, breakpoints: List[float])
```

### 3. 記録フォーマット

```json
{
  "metadata": {
    "version": "1.0",
    "game_version": "0.1.0",
    "recorded_at": "2025-01-03T10:30:00",
    "duration_seconds": 120.5
  },
  "initial_state": {
    "active_facility": "adventurers_guild",
    "party_members": [...],
    "ui_state": {...}
  },
  "events": [
    {
      "timestamp": 1.234,
      "type": "MOUSEBUTTONDOWN",
      "data": {"pos": [400, 300], "button": 1}
    },
    {
      "timestamp": 2.567,
      "type": "KEYDOWN",
      "data": {"key": 27, "unicode": "\x1b"}
    }
  ],
  "state_snapshots": [
    {
      "timestamp": 5.0,
      "state": {...}
    }
  ]
}
```

### 4. デバッグUI統合

```python
# デバッグモードでの録画制御
class RecordingOverlay:
    def draw_recording_status(self, screen)
    def handle_recording_hotkeys(self, event)
    # F9: 録画開始/停止
    # F10: 最後の10秒を保存
    # F11: インスタントリプレイ
```

### 5. pytest統合

```python
@pytest.fixture
def recorded_game_session():
    """テスト用の記録されたゲームセッション"""
    recorder = GameStateRecorder()
    recorder.start_recording()
    yield recorder
    recorder.save_recording(f"test_recording_{timestamp}.json")
```

## 効果

- 再現困難なバグの確実な再現
- バグレポートの質向上（記録ファイル添付）
- 自動テストケースの生成

## 優先度

**中** - 複雑だが長期的な効果が大きい

## 関連ファイル

- 新規作成: `src/debug/state_recorder.py`
- 新規作成: `src/debug/game_replayer.py`
- 新規作成: `src/debug/recording_overlay.py`
- 更新: `main.py`（記録機能の統合）

## 実装時の注意

- 記録ファイルサイズの管理（圧縮、古い記録の自動削除）
- パフォーマンスへの影響（バッファリング実装）
- プライバシー配慮（プレイヤー名等の匿名化オプション）

---

## 実装記録

（実装時に記録）