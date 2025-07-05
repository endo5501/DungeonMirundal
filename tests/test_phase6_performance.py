"""Phase 6 Day 3: パフォーマンス最適化・ボトルネック特定テスト"""

import pytest
import time
import psutil
import os
from unittest.mock import MagicMock, patch

from src.core.game_manager import GameManager
from src.character.party import Party
from src.character.character import Character
from src.rendering.dungeon_renderer_pygame import DungeonRendererPygame
from src.ui.dungeon_ui_pygame import DungeonUIManagerPygame


class TestPhase6Performance:
    """Phase 6 パフォーマンス最適化・ボトルネック特定テスト"""
    
    def test_character_creation_performance(self):
        """キャラクター作成のパフォーマンステスト"""
        start_time = time.time()
        characters = []
        
        # 100キャラクター作成のパフォーマンス測定
        for i in range(100):
            character = Character(f"perf_test_{i}", "human", "fighter")
            characters.append(character)
        
        creation_time = time.time() - start_time
        
        # クリーンアップ
        for character in characters:
            if hasattr(character, 'cleanup'):
                character.cleanup()
        characters.clear()
        
        # 100キャラクター作成が1秒以内に完了
        assert creation_time < 1.0, f"キャラクター作成が遅すぎます: {creation_time:.3f}秒"
        
        # 1キャラクターあたりの平均作成時間
        avg_time_per_char = creation_time / 100
        assert avg_time_per_char < 0.01, f"キャラクター作成平均時間: {avg_time_per_char:.3f}秒"
    
    def test_party_operations_performance(self):
        """パーティ操作のパフォーマンステスト"""
        # パーティ作成
        party = Party("performance_test_party")
        
        # キャラクター作成・追加のパフォーマンス測定
        start_time = time.time()
        characters = []
        
        for i in range(50):
            character = Character(f"party_member_{i}", "human", "fighter")
            characters.append(character)
            if i < 6:  # パーティは最大6人
                party.add_character(character)
        
        addition_time = time.time() - start_time
        
        # パーティ操作のパフォーマンス測定
        start_time = time.time()
        
        # 生存キャラクター取得を100回実行
        for _ in range(100):
            living = party.get_living_characters()
            assert len(living) <= 6
        
        operation_time = time.time() - start_time
        
        # クリーンアップ
        party.cleanup()
        for character in characters:
            if hasattr(character, 'cleanup'):
                character.cleanup()
        
        # パフォーマンス検証
        assert addition_time < 0.5, f"パーティ追加処理が遅すぎます: {addition_time:.3f}秒"
        assert operation_time < 0.1, f"パーティ操作が遅すぎます: {operation_time:.3f}秒"
    
    def test_ui_rendering_performance_mock(self):
        """UI描画のパフォーマンステスト（Mock使用）"""
        with patch('pygame.init'), \
             patch('pygame.get_init', return_value=True), \
             patch('pygame.display.set_mode') as mock_set_mode, \
             patch('pygame.display.Info') as mock_info:
            
            # Mockスクリーンを設定
            mock_screen = MagicMock()
            mock_screen.get_width.return_value = 1024
            mock_screen.get_height.return_value = 768
            mock_set_mode.return_value = mock_screen
            mock_info.return_value = MagicMock()
            
            # UIマネージャー作成
            ui_manager = DungeonUIManagerPygame(screen=mock_screen)
            
            # 描画パフォーマンス測定
            start_time = time.time()
            
            # 描画処理を100回実行
            for _ in range(100):
                ui_manager.render_overlay()
                ui_manager.update()
            
            render_time = time.time() - start_time
            
            # クリーンアップ
            ui_manager.cleanup()
            
            # パフォーマンス検証（Mock環境なので緩い基準）
            assert render_time < 1.0, f"UI描画が遅すぎます: {render_time:.3f}秒"
            
            # 1回あたりの描画時間
            avg_render_time = render_time / 100
            assert avg_render_time < 0.01, f"UI描画平均時間: {avg_render_time:.3f}秒"
    
    def test_dungeon_renderer_performance_mock(self):
        """ダンジョンレンダラーのパフォーマンステスト（Mock使用）"""
        with patch('pygame.init'), \
             patch('pygame.get_init', return_value=True), \
             patch('pygame.display.set_mode') as mock_set_mode:
            
            # Mockスクリーンを設定
            mock_screen = MagicMock()
            mock_screen.get_width.return_value = 1024
            mock_screen.get_height.return_value = 768
            mock_set_mode.return_value = mock_screen
            
            # レンダラー作成
            renderer = DungeonRendererPygame(screen=mock_screen)
            
            # レンダリングパフォーマンス測定
            start_time = time.time()
            
            # UI更新を50回実行
            for _ in range(50):
                renderer.update_ui()
            
            update_time = time.time() - start_time
            
            # クリーンアップ
            renderer.cleanup()
            
            # パフォーマンス検証
            assert update_time < 1.0, f"レンダラー更新が遅すぎます: {update_time:.3f}秒"
    
    def test_system_integration_performance(self):
        """システム統合パフォーマンステスト"""
        # CPU使用率測定開始
        process = psutil.Process(os.getpid())
        initial_cpu = process.cpu_percent()
        
        start_time = time.time()
        
        # 統合システムテスト
        characters = []
        parties = []
        
        # 複数のパーティとキャラクターを作成
        for party_idx in range(5):
            party = Party(f"performance_party_{party_idx}")
            parties.append(party)
            
            for char_idx in range(4):
                character = Character(
                    f"perf_char_{party_idx}_{char_idx}", 
                    "human", 
                    "fighter"
                )
                characters.append(character)
                party.add_character(character)
        
        # パーティ操作を実行
        for party in parties:
            for _ in range(10):
                living = party.get_living_characters()
                conscious = party.get_conscious_characters()
                assert len(living) <= 4
                assert len(conscious) <= 4
        
        total_time = time.time() - start_time
        final_cpu = process.cpu_percent()
        
        # クリーンアップ
        for party in parties:
            party.cleanup()
        for character in characters:
            if hasattr(character, 'cleanup'):
                character.cleanup()
        
        # パフォーマンス検証
        assert total_time < 2.0, f"統合テストが遅すぎます: {total_time:.3f}秒"
        
        # CPU使用率チェック（増加が50%以下）
        cpu_increase = final_cpu - initial_cpu
        if cpu_increase > 50:
            print(f"警告: CPU使用率が大幅に増加しました: {cpu_increase:.1f}%")
    
    def test_memory_efficiency_under_load(self):
        """負荷時のメモリ効率テスト"""
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss
        
        # 大量のオブジェクト作成・操作・削除
        for cycle in range(3):
            objects = []
            
            # 大量作成
            for i in range(100):
                character = Character(f"memory_test_{cycle}_{i}", "human", "fighter")
                party = Party(f"memory_party_{cycle}_{i}")
                party.add_character(character)
                objects.append((character, party))
            
            # 操作実行
            for character, party in objects:
                party.get_living_characters()
                if hasattr(character, 'get_status'):
                    character.get_status()
            
            # クリーンアップ
            for character, party in objects:
                party.cleanup()
                character.cleanup()
            
            objects.clear()
            
            # メモリ使用量チェック
            current_memory = process.memory_info().rss
            memory_increase = current_memory - initial_memory
            
            # サイクルごとに5MB以下の増加
            cycle_limit = 5 * 1024 * 1024
            if memory_increase > cycle_limit:
                print(f"警告: サイクル {cycle} でメモリ使用量が {memory_increase / 1024 / 1024:.2f}MB 増加")
        
        # 最終メモリ使用量チェック
        final_memory = process.memory_info().rss
        total_increase = final_memory - initial_memory
        
        # 10MB以下の増加を目標
        assert total_increase < 10 * 1024 * 1024, f"メモリ使用量異常: {total_increase / 1024 / 1024:.2f}MB 増加"
    
    def test_response_time_consistency(self):
        """レスポンス時間の一貫性テスト"""
        response_times = []
        
        # 複数回の操作で応答時間を測定
        for i in range(20):
            start_time = time.time()
            
            # 標準的な操作を実行
            character = Character(f"response_test_{i}", "human", "fighter")
            party = Party(f"response_party_{i}")
            party.add_character(character)
            
            living = party.get_living_characters()
            conscious = party.get_conscious_characters()
            
            # クリーンアップ
            party.cleanup()
            character.cleanup()
            
            response_time = time.time() - start_time
            response_times.append(response_time)
        
        # 統計計算
        avg_response = sum(response_times) / len(response_times)
        max_response = max(response_times)
        min_response = min(response_times)
        
        # 一貫性チェック
        assert avg_response < 0.01, f"平均応答時間が遅すぎます: {avg_response:.3f}秒"
        assert max_response < 0.05, f"最大応答時間が遅すぎます: {max_response:.3f}秒"
        
        # 応答時間のばらつきチェック
        variance = max_response - min_response
        assert variance < 0.03, f"応答時間のばらつきが大きすぎます: {variance:.3f}秒"
    
    def test_concurrent_operations_simulation(self):
        """同時操作のシミュレーションテスト"""
        import threading
        import queue
        
        results = queue.Queue()
        
        def worker_function(worker_id):
            """ワーカー関数"""
            start_time = time.time()
            
            try:
                # 各ワーカーが独立してオブジェクトを操作
                character = Character(f"worker_{worker_id}", "human", "fighter")
                party = Party(f"worker_party_{worker_id}")
                party.add_character(character)
                
                # 複数回の操作
                for _ in range(10):
                    party.get_living_characters()
                    party.get_conscious_characters()
                
                # クリーンアップ
                party.cleanup()
                character.cleanup()
                
                execution_time = time.time() - start_time
                results.put(('success', worker_id, execution_time))
                
            except Exception as e:
                results.put(('error', worker_id, str(e)))
        
        # 5つのワーカーを同時実行
        threads = []
        for i in range(5):
            thread = threading.Thread(target=worker_function, args=(i,))
            threads.append(thread)
            thread.start()
        
        # 全スレッドの完了を待機
        for thread in threads:
            thread.join(timeout=5.0)  # 5秒でタイムアウト
        
        # 結果の検証
        success_count = 0
        total_time = 0
        
        while not results.empty():
            result_type, worker_id, data = results.get()
            if result_type == 'success':
                success_count += 1
                total_time += data
            else:
                print(f"Worker {worker_id} エラー: {data}")
        
        # 全ワーカーが成功
        assert success_count == 5, f"同時操作で失敗が発生: {5 - success_count} 個のワーカーが失敗"
        
        # 平均実行時間
        avg_time = total_time / success_count if success_count > 0 else 0
        assert avg_time < 0.5, f"同時操作の平均実行時間が遅すぎます: {avg_time:.3f}秒"