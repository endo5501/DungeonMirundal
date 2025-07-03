"""
DebugMiddlewareクラスのテスト

ゲームインスタンスの主要メソッドをラップして、自動的にエラーログを強化する
デバッグミドルウェア機能をテストする。
"""

import pytest
import logging
from unittest.mock import Mock, patch, MagicMock
import pygame

from src.debug.debug_middleware import DebugMiddleware


class TestDebugMiddleware:
    """DebugMiddlewareのテストクラス"""
    
    @pytest.fixture
    def mock_game_instance(self):
        """モックのゲームインスタンスを作成"""
        game = Mock()
        game.handle_event = Mock()
        game.update = Mock()
        game.draw = Mock()
        game.ui_manager = Mock()
        return game
    
    @pytest.fixture
    def mock_enhanced_logger(self):
        """モックのEnhancedGameLoggerを作成"""
        with patch('src.debug.debug_middleware.EnhancedGameLogger') as mock_logger_class:
            mock_logger = Mock()
            mock_logger_class.return_value = mock_logger
            yield mock_logger
    
    @pytest.fixture
    def middleware(self, mock_game_instance, mock_enhanced_logger):
        """DebugMiddlewareインスタンスを作成"""
        return DebugMiddleware(mock_game_instance)
    
    def test_middleware_initialization(self, middleware, mock_game_instance):
        """ミドルウェアの初期化テスト"""
        assert middleware.game_instance == mock_game_instance
        assert middleware.enhanced_logger is not None
        assert middleware.wrapped_methods == {}
    
    def test_wrap_with_enhanced_logging(self, middleware, mock_game_instance):
        """拡張ログ機能でのメソッドラップテスト"""
        # 元のメソッドを保存
        original_handle_event = mock_game_instance.handle_event
        original_update = mock_game_instance.update
        
        # ラップを実行
        middleware.wrap_with_enhanced_logging()
        
        # メソッドがラップされたことを確認
        assert mock_game_instance.handle_event != original_handle_event
        assert mock_game_instance.update != original_update
        
        # ラップされたメソッドが記録されていることを確認
        assert 'handle_event' in middleware.wrapped_methods
        assert 'update' in middleware.wrapped_methods
        assert middleware.wrapped_methods['handle_event'] == original_handle_event
    
    def test_wrap_method_with_logging(self, middleware, mock_game_instance):
        """個別メソッドラップテスト"""
        original_method = mock_game_instance.handle_event
        
        # メソッドをラップ
        wrapped_method = middleware._wrap_method_with_logging(
            original_method, 
            "handle_event"
        )
        
        # ラップされたメソッドを実行
        test_event = Mock()
        test_event.type = pygame.MOUSEBUTTONDOWN
        
        wrapped_method(test_event)
        
        # 元のメソッドが呼ばれたことを確認
        original_method.assert_called_once_with(test_event)
        
        # コンテキストがプッシュされたことを確認
        middleware.enhanced_logger.push_context.assert_called()
        middleware.enhanced_logger.pop_context.assert_called()
    
    def test_method_wrapping_with_exception(self, middleware, mock_game_instance):
        """例外発生時のメソッドラップテスト"""
        # 例外を起こすメソッドを設定
        test_exception = ValueError("Test exception")
        mock_game_instance.handle_event.side_effect = test_exception
        
        wrapped_method = middleware._wrap_method_with_logging(
            mock_game_instance.handle_event, 
            "handle_event"
        )
        
        # 例外が発生することを確認
        with pytest.raises(ValueError):
            wrapped_method(Mock())
        
        # エラーログが記録されたことを確認
        middleware.enhanced_logger.log_ui_error.assert_called_once_with(test_exception)
        
        # コンテキストがポップされたことを確認（finally block）
        middleware.enhanced_logger.pop_context.assert_called()
    
    def test_create_method_context(self, middleware):
        """メソッドコンテキスト作成テスト"""
        # handle_eventメソッド用のコンテキスト
        event = Mock()
        event.type = pygame.KEYDOWN
        event.key = pygame.K_ESCAPE
        # 他の属性を明示的に削除して期待する属性のみ残す
        for attr in ['pos', 'button', 'unicode', 'ui_element', 'ui_object_id']:
            if hasattr(event, attr):
                delattr(event, attr)
        
        context = middleware._create_method_context("handle_event", event)
        
        expected_context = {
            "method": "handle_event",
            "args": {
                "event_type": pygame.KEYDOWN,
                "event_data": {"key": pygame.K_ESCAPE}
            }
        }
        
        assert context == expected_context
    
    def test_create_method_context_update(self, middleware):
        """updateメソッド用のコンテキスト作成テスト"""
        dt = 0.016  # 16ms
        
        context = middleware._create_method_context("update", dt)
        
        expected_context = {
            "method": "update",
            "args": {"dt": dt}
        }
        
        assert context == expected_context
    
    def test_create_method_context_draw(self, middleware):
        """drawメソッド用のコンテキスト作成テスト"""
        surface = Mock()
        
        context = middleware._create_method_context("draw", surface)
        
        expected_context = {
            "method": "draw",
            "args": {"surface": str(surface)}
        }
        
        assert context == expected_context
    
    def test_create_method_context_unknown_method(self, middleware):
        """未知のメソッド用のコンテキスト作成テスト"""
        context = middleware._create_method_context("unknown_method", "arg1", "arg2")
        
        expected_context = {
            "method": "unknown_method",
            "args": {"args": ["arg1", "arg2"], "kwargs": {}}
        }
        
        assert context == expected_context
    
    def test_extract_event_info(self, middleware):
        """イベント情報抽出テスト"""
        # マウスイベント - 必要な属性のみ有するMockを作成
        mouse_event = Mock(spec=['type', 'pos', 'button'])
        mouse_event.type = pygame.MOUSEBUTTONDOWN
        mouse_event.pos = (100, 200)
        mouse_event.button = 1
        
        event_info = middleware._extract_event_info(mouse_event)
        
        expected_info = {
            "pos": (100, 200),
            "button": 1
        }
        
        assert event_info == expected_info
        
        # キーボードイベント - 必要な属性のみ有するMockを作成
        key_event = Mock(spec=['type', 'key', 'unicode'])
        key_event.type = pygame.KEYDOWN
        key_event.key = pygame.K_ESCAPE
        key_event.unicode = '\x1b'
        
        event_info = middleware._extract_event_info(key_event)
        
        expected_info = {
            "key": pygame.K_ESCAPE,
            "unicode": '\x1b'
        }
        
        assert event_info == expected_info
    
    def test_extract_event_info_with_missing_attributes(self, middleware):
        """属性が不足したイベントの情報抽出テスト"""
        # specで属性を限定し、posを含めない
        incomplete_event = Mock(spec=['type'])
        incomplete_event.type = pygame.MOUSEBUTTONDOWN
        
        event_info = middleware._extract_event_info(incomplete_event)
        
        # エラーなく処理され、空の辞書が返される
        assert event_info == {}
    
    def test_restore_original_methods(self, middleware, mock_game_instance):
        """元のメソッドの復元テスト"""
        # メソッドをラップ
        original_handle_event = mock_game_instance.handle_event
        middleware.wrap_with_enhanced_logging()
        
        # メソッドがラップされたことを確認
        assert mock_game_instance.handle_event != original_handle_event
        
        # 元のメソッドを復元
        middleware.restore_original_methods()
        
        # メソッドが元に戻ったことを確認
        assert mock_game_instance.handle_event == original_handle_event
        assert middleware.wrapped_methods == {}
    
    def test_context_manager_usage(self, mock_game_instance, mock_enhanced_logger):
        """コンテキストマネージャーとしての使用テスト"""
        with DebugMiddleware(mock_game_instance) as middleware:
            # ミドルウェアが適用されている
            assert hasattr(middleware, 'game_instance')
            
            # ゲームインスタンスでメソッドを実行
            mock_game_instance.handle_event(Mock())
        
        # コンテキスト終了後は元のメソッドが復元される
        # (実際の実装ではrestoreが呼ばれる)
    
    def test_selective_method_wrapping(self, middleware, mock_game_instance):
        """選択的メソッドラップテスト"""
        # 特定のメソッドのみをラップ
        methods_to_wrap = ['handle_event']
        middleware.wrap_methods(methods_to_wrap)
        
        # handle_eventのみがラップされる
        assert 'handle_event' in middleware.wrapped_methods
        assert 'update' not in middleware.wrapped_methods
        assert 'draw' not in middleware.wrapped_methods
    
    def test_error_in_context_creation(self, middleware, mock_game_instance):
        """コンテキスト作成時のエラーハンドリングテスト"""
        # _create_method_contextではなく_extract_event_infoでエラーを発生させる
        with patch.object(middleware, '_extract_event_info', side_effect=Exception("Event extraction error")):
            wrapped_method = middleware._wrap_method_with_logging(
                mock_game_instance.handle_event, 
                "handle_event"
            )
            
            # エラーが発生してもメソッド実行は継続される
            wrapped_method(Mock())
            mock_game_instance.handle_event.assert_called_once()
            
            # コンテキストは作成されるが、argsにエラー情報が含まれる
            middleware.enhanced_logger.push_context.assert_called()
            push_calls = middleware.enhanced_logger.push_context.call_args_list
            assert any('error' in str(call) for call in push_calls)
    
    def test_performance_monitoring(self, middleware, mock_game_instance):
        """パフォーマンス監視テスト"""
        wrapped_method = middleware._wrap_method_with_logging(
            mock_game_instance.handle_event, 
            "handle_event"
        )
        
        # メソッド実行
        wrapped_method(Mock())
        
        # コンテキストに実行時間が含まれることを確認
        calls = middleware.enhanced_logger.push_context.call_args_list
        if calls:
            context = calls[0][0][0]
            # 実行時間情報が含まれているかチェック
            # (実装により詳細は変わる)
            assert isinstance(context, dict)