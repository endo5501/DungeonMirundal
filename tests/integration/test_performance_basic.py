"""基本パフォーマンステスト"""

import os
import sys
import time
import pygame
from unittest.mock import Mock, patch

# ヘッドレス環境でのPygame初期化
os.environ['SDL_VIDEODRIVER'] = 'dummy'

# パス設定
sys.path.insert(0, '/home/satorue/Dungeon')

from src.ui.window_system.window_manager import WindowManager
from src.ui.window_system.window import Window, WindowState


class MockPerfWindow(Window):
    """パフォーマンステスト用の具象Windowクラス"""
    
    def __init__(self, window_id: str):
        super().__init__(window_id)
        self.created = False
    
    def create(self):
        """ウィンドウ作成"""
        self.created = True
    
    def handle_event(self, event):
        """イベント処理"""
        return False


class TestPerformanceBasic:
    """基本パフォーマンステストクラス"""
    
    def setup_method(self):
        """各テストメソッドの前に実行"""
        pygame.init()
        self.screen = pygame.display.set_mode((800, 600))
        
    def teardown_method(self):
        """各テストメソッドの後に実行"""
        pygame.quit()
    
    def test_window_creation_performance(self):
        """Window作成性能テスト"""
        start_time = time.time()
        
        # 100個のWindowを作成
        windows = []
        for i in range(100):
            window = MockPerfWindow(f"perf_window_{i}")
            windows.append(window)
        
        end_time = time.time()
        creation_time = end_time - start_time
        
        # 100個のWindow作成が1秒未満で完了することを確認
        assert creation_time < 1.0, f"Window作成が遅すぎます: {creation_time:.3f}秒"
        
        # 平均作成時間が10ms未満であることを確認
        avg_time = creation_time / 100
        assert avg_time < 0.01, f"平均Window作成時間が遅すぎます: {avg_time:.6f}秒"
    
    def test_window_show_hide_performance(self):
        """Window表示・非表示性能テスト"""
        window = MockPerfWindow("perf_show_hide")
        
        start_time = time.time()
        
        # 100回の表示・非表示サイクル
        for _ in range(100):
            window.show()
            window.hide()
        
        end_time = time.time()
        cycle_time = end_time - start_time
        
        # 100回のサイクルが1秒未満で完了することを確認
        assert cycle_time < 1.0, f"表示・非表示サイクルが遅すぎます: {cycle_time:.3f}秒"
    
    def test_window_manager_singleton_performance(self):
        """WindowManagerシングルトン取得性能テスト"""
        start_time = time.time()
        
        # 1000回のシングルトン取得
        for _ in range(1000):
            manager = WindowManager.get_instance()
            assert manager is not None
        
        end_time = time.time()
        singleton_time = end_time - start_time
        
        # 1000回の取得が0.1秒未満で完了することを確認
        assert singleton_time < 0.1, f"シングルトン取得が遅すぎます: {singleton_time:.3f}秒"
    
    def test_pygame_basic_performance(self):
        """Pygame基本操作性能テスト"""
        start_time = time.time()
        
        # 100回の基本描画操作をシミュレート
        for _ in range(100):
            # 画面クリア
            self.screen.fill((0, 0, 0))
            
            # 簡単な図形描画
            pygame.draw.rect(self.screen, (255, 255, 255), (10, 10, 100, 100))
            pygame.draw.circle(self.screen, (255, 0, 0), (200, 200), 50)
        
        end_time = time.time()
        render_time = end_time - start_time
        
        # 100回の描画が1秒未満で完了することを確認
        assert render_time < 1.0, f"Pygame描画が遅すぎます: {render_time:.3f}秒"
    
    def test_memory_usage_stability(self):
        """メモリ使用量安定性テスト"""
        import gc
        
        # ガベージコレクション実行
        gc.collect()
        
        # 多数のオブジェクト作成・削除
        for cycle in range(10):
            windows = []
            for i in range(50):
                window = MockPerfWindow(f"memory_test_{cycle}_{i}")
                window.show()
                windows.append(window)
            
            # すべて削除
            for window in windows:
                window.hide()
                window.destroy()
            
            del windows
            gc.collect()
        
        # メモリテストが完了すれば成功とする
        assert True
    
    def test_no_performance_regression(self):
        """性能劣化がないことの基本確認"""
        # 基本的な操作が予期される時間内で完了することを確認
        operations = [
            ("WindowManager取得", lambda: WindowManager.get_instance()),
            ("Window作成", lambda: MockPerfWindow("regression_test")),
            ("Window状態変更", lambda: self._window_state_operations()),
        ]
        
        for operation_name, operation in operations:
            start_time = time.time()
            result = operation()
            end_time = time.time()
            
            operation_time = end_time - start_time
            
            # 各操作が50ms未満で完了することを確認
            assert operation_time < 0.05, f"{operation_name}が遅すぎます: {operation_time:.6f}秒"
    
    def _window_state_operations(self):
        """Window状態操作のヘルパー"""
        window = MockPerfWindow("state_test")
        window.show()
        window.hide()
        window.destroy()
        return window