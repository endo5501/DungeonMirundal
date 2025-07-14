#!/usr/bin/env python3
"""ESCキー動作の統合テスト

手動テスト tests/manual/test_esc_fix.py を pytest フレームワークに統合
"""

import pytest
import time
import json
from src.debug.game_debug_client import GameDebugClient


@pytest.mark.integration
@pytest.mark.ui
class TestEscBehaviorIntegration:
    """ESCキー動作統合テスト"""
    
    @pytest.fixture(scope="class")
    def game_client(self):
        """ゲームデバッグクライアントのセットアップ"""
        client = GameDebugClient()
        if not client.wait_for_api(timeout=10):
            pytest.skip("ゲームAPIが利用できません")
        yield client
    
    def test_esc_opens_settings_window(self, game_client):
        """ESCキーで設定ウィンドウが開くことをテスト"""
        # 初期状態のUI階層を取得
        initial_hierarchy = game_client.get_ui_hierarchy()
        assert initial_hierarchy is not None, "初期UI階層の取得に失敗"
        
        initial_window_count = len(initial_hierarchy.get('window_stack', []))
        
        # ESCキーを押して設定ウィンドウを開く
        game_client.send_key(27)  # ESC key code
        time.sleep(1)  # ウィンドウ遷移待機
        
        # 設定ウィンドウが開いたことを確認
        settings_hierarchy = game_client.get_ui_hierarchy()
        assert settings_hierarchy is not None, "設定画面のUI階層取得に失敗"
        
        settings_window_count = len(settings_hierarchy.get('window_stack', []))
        assert settings_window_count > initial_window_count, "ESCキーで設定ウィンドウが開かない"
        
        # 設定ウィンドウの存在確認
        window_stack = settings_hierarchy.get('window_stack', [])
        settings_window_found = any('settings' in window.lower() for window in window_stack)
        assert settings_window_found, f"設定ウィンドウが見つからない: {window_stack}"
    
    def test_esc_closes_settings_window(self, game_client):
        """ESCキーで設定ウィンドウが閉じることをテスト"""
        # 設定ウィンドウを開く
        initial_hierarchy = game_client.get_ui_hierarchy()
        initial_window_count = len(initial_hierarchy.get('window_stack', []))
        
        game_client.send_key(27)  # 設定ウィンドウを開く
        time.sleep(1)
        
        # 設定ウィンドウが開いていることを確認
        settings_hierarchy = game_client.get_ui_hierarchy()
        settings_window_count = len(settings_hierarchy.get('window_stack', []))
        assert settings_window_count > initial_window_count, "設定ウィンドウが開いていない"
        
        # ESCキーで設定ウィンドウを閉じる
        game_client.send_key(27)
        time.sleep(1)
        
        # 設定ウィンドウが閉じたことを確認
        final_hierarchy = game_client.get_ui_hierarchy()
        final_window_count = len(final_hierarchy.get('window_stack', []))
        assert final_window_count == initial_window_count, "ESCキーで設定ウィンドウが閉じない"
    
    def test_esc_behavior_complete_cycle(self, game_client):
        """ESCキーの完全サイクルテスト（開く→閉じる）"""
        # Step 1: 初期状態の記録
        initial_hierarchy = game_client.get_ui_hierarchy()
        initial_stack = initial_hierarchy.get('window_stack', [])
        
        # Step 2: ESCキーで設定ウィンドウを開く
        game_client.send_key(27)
        time.sleep(1)
        
        opened_hierarchy = game_client.get_ui_hierarchy()
        opened_stack = opened_hierarchy.get('window_stack', [])
        
        # 設定ウィンドウが開いたことを確認
        assert len(opened_stack) > len(initial_stack), "設定ウィンドウが開かない"
        
        # Step 3: ESCキーで設定ウィンドウを閉じる
        game_client.send_key(27)
        time.sleep(1)
        
        closed_hierarchy = game_client.get_ui_hierarchy()
        closed_stack = closed_hierarchy.get('window_stack', [])
        
        # 元の状態に戻ったことを確認
        assert len(closed_stack) == len(initial_stack), "元の状態に戻らない"
        assert closed_stack == initial_stack, "ウィンドウスタックが初期状態と一致しない"
    
    def test_multiple_esc_presses(self, game_client):
        """複数回のESCキー押下テスト"""
        initial_hierarchy = game_client.get_ui_hierarchy()
        initial_window_count = len(initial_hierarchy.get('window_stack', []))
        
        # 3回連続でESCキーを押す
        for i in range(3):
            game_client.send_key(27)
            time.sleep(0.5)
            
            hierarchy = game_client.get_ui_hierarchy()
            window_count = len(hierarchy.get('window_stack', []))
            
            if i == 0:
                # 1回目: 設定ウィンドウが開く
                assert window_count > initial_window_count, f"1回目のESCで設定ウィンドウが開かない"
            elif i == 1:
                # 2回目: 設定ウィンドウが閉じる
                assert window_count == initial_window_count, f"2回目のESCで設定ウィンドウが閉じない"
            else:
                # 3回目: 何も変化しない（または再度設定ウィンドウが開く）
                # この動作は実装により異なるため、エラーが発生しないことのみ確認
                assert hierarchy is not None, "3回目のESC後にUI階層が取得できない"
    
    @pytest.mark.slow
    def test_esc_behavior_performance(self, game_client):
        """ESCキー動作のパフォーマンステスト"""
        import time
        
        # ESCキー操作の応答時間を測定
        start_time = time.time()
        
        # 設定ウィンドウを開く
        game_client.send_key(27)
        time.sleep(0.1)  # 最小待機時間
        
        # UI階層が更新されるまでの時間を測定
        max_wait_time = 2.0  # 最大2秒
        hierarchy = None
        
        while time.time() - start_time < max_wait_time:
            hierarchy = game_client.get_ui_hierarchy()
            if hierarchy and len(hierarchy.get('window_stack', [])) > 1:
                break
            time.sleep(0.1)
        
        response_time = time.time() - start_time
        
        assert hierarchy is not None, "UI階層の取得がタイムアウト"
        assert response_time < max_wait_time, f"ESCキー応答時間が遅すぎる: {response_time:.2f}秒"
        
        # パフォーマンスログ出力
        print(f"ESCキー応答時間: {response_time:.3f}秒")
    
    def test_esc_error_handling(self, game_client):
        """ESCキー操作のエラーハンドリングテスト"""
        # 初期状態を記録
        initial_hierarchy = game_client.get_ui_hierarchy()
        
        # 短時間で連続してESCキーを押す（競合状態のテスト）
        for _ in range(5):
            game_client.send_key(27)
            time.sleep(0.05)  # 非常に短い間隔
        
        time.sleep(1)  # 処理の完了を待つ
        
        # システムが安定した状態になることを確認
        final_hierarchy = game_client.get_ui_hierarchy()
        assert final_hierarchy is not None, "連続ESCキー後にUI階層が取得できない"
        assert final_hierarchy.get('window_manager_available', False), "WindowManagerが利用不可能になった"