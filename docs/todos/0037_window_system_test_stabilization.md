# 0037: WindowSystem - テスト安定化作業

## 目的
WindowSystem移行後に発生したテスト失敗の修正とテスト環境の安定化を図る。

## 経緯
- 2025年6月29日: WindowSystem移行完了後のテスト実行で複数の失敗を検出
- 主にフォント関連とStatistics関連のテスト失敗が発生
- 移行の核心機能は正常だが、テスト環境の問題が残存

## 検出された問題

### 1. フォント関連テスト失敗（高優先度）
**影響ファイル**: `tests/ui/window_system/test_menu_window.py`
**エラー**: `pygame.error: Invalid font (font module quit since font created)`
**失敗テスト数**: 12テスト

**失敗テスト一覧**:
- `test_menu_window_handles_button_click_events`
- `test_menu_window_supports_keyboard_navigation`
- `test_menu_window_wraps_navigation_at_boundaries`
- `test_menu_window_activates_selected_button_with_enter`
- `test_menu_window_can_be_disabled_and_enabled`
- `test_menu_window_supports_custom_styling`
- `test_menu_window_cleanup_removes_ui_elements`
- `test_menu_window_automatically_adds_back_button`
- `test_menu_window_back_button_not_added_to_root_menu`
- `test_menu_window_back_button_sends_window_back_action`
- `test_menu_window_escape_key_triggers_back_action`
- `test_menu_window_custom_back_button_text`

### 2. Statistics追跡テスト失敗（中優先度）
**影響ファイル**: `tests/ui/window_system/test_window_integration.py`
**エラー**: `assert 0 == 5` (events_processed統計)
**失敗テスト**:
- `test_statistics_tracking_across_operations`

## 原因分析

### フォント関連問題
- **根本原因**: テスト間でのpygame.fontモジュールの初期化/終了処理の競合
- **発生箇所**: MenuWindowのUILabel作成時のフォント参照
- **環境依存**: WSL2環境でのフォントシステムとの相互作用

### Statistics問題
- **根本原因**: イベント処理統計の取得タイミング問題
- **発生箇所**: WindowManagerのStatisticsManagerでのカウンター更新
- **実装問題**: 統計取得メソッドの呼び出しタイミング

## 修正アプローチ

### Phase 1: フォント関連修正（高優先度）

#### 1.1 テストセットアップの改善
```python
def setup_method(self):
    """テスト前セットアップの改善"""
    # pygame.fontの確実な初期化
    pygame.font.init()
    
def teardown_method(self):
    """テスト後クリーンアップの改善"""
    # pygame.fontの確実な終了処理
    pygame.font.quit()
```

#### 1.2 フォント初期化の安定化
- WindowManagerのフォント初期化タイミング改善
- テスト用モックフォントの導入
- フォント作成時のエラーハンドリング強化

#### 1.3 テスト分離の改善
- テスト間でのpygame状態の完全リセット
- フォントオブジェクトのライフサイクル管理
- テストごとの独立したpygame環境

### Phase 2: Statistics関連修正（中優先度）

#### 2.1 統計カウンター修正
```python
# StatisticsManagerの改善
def get_statistics(self) -> Dict[str, int]:
    """統計情報の確実な取得"""
    # カウンター更新の同期確保
    # 非同期処理での競合状態対策
```

#### 2.2 テストタイミング調整
- イベント処理完了待ちの実装
- 統計更新の同期確保
- テストでの適切な待機処理

### Phase 3: テスト環境全体の安定化（低優先度）

#### 3.1 CI/CD環境での安定性
- WSL2環境でのフォント設定最適化
- テスト実行環境の標準化
- 環境依存テストの分離

#### 3.2 テストカバレッジの改善
- エッジケースのテスト追加
- エラーハンドリングのテスト強化
- パフォーマンステストの追加

## 技術仕様

### フォント修正仕様
```python
# 修正パターン: 安全なフォント初期化
class TestMenuWindow:
    def setup_method(self):
        if not pygame.get_init():
            pygame.init()
        if not pygame.font.get_init():
            pygame.font.init()
            
    def teardown_method(self):
        # UI要素の確実なクリーンアップ
        if hasattr(self, 'ui_manager'):
            self.ui_manager.clear_and_reset()
        # フォントの確実な終了
        pygame.font.quit()
```

### Statistics修正仕様
```python
# 修正パターン: 同期的統計更新
def test_statistics_tracking_across_operations(self):
    # イベント処理の完了を確実に待機
    window_manager.process_all_pending_events()
    
    # 統計の同期的取得
    stats = window_manager.get_statistics()
    assert stats['events_processed'] == expected_count
```

## 期待される効果

### テスト安定性向上
- フォント関連テスト失敗の解消
- Statistics関連テスト失敗の解消
- CI/CD環境での安定したテスト実行

### 開発効率向上
- テスト失敗による開発阻害の解消
- 確実なリグレッション検出
- 品質保証プロセスの安定化

## 完了条件

### Phase 1 完了条件
- [ ] MenuWindowテストの全通過
- [ ] フォント関連エラーの解消
- [ ] テストセットアップ/クリーンアップの改善

### Phase 2 完了条件
- [ ] StatisticsManagerテストの修正
- [ ] test_statistics_tracking_across_operationsの通過
- [ ] イベント処理同期の改善

### Phase 3 完了条件
- [ ] 全WindowSystemテストの安定した通過
- [ ] CI/CD環境での確実な動作
- [ ] テストカバレッジの維持・向上

## 関連ドキュメント
- `docs/todos/0032_window_system_migration_high_priority.md`: WindowSystem移行（完了）
- `docs/window_system.md`: WindowSystem設計書
- `tests/ui/window_system/`: WindowSystemテストスイート

## 注意事項
- フォント問題は環境依存の可能性があり、複数環境での検証が必要
- Statistics問題は並行処理に関連する可能性があり、慎重な修正が必要
- テスト修正は機能動作を変更せず、テスト環境のみを対象とすること