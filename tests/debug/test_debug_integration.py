"""
デバッグ機能統合テスト

コンビニエンス関数や統合機能をテストする。
"""

import pytest
import logging
from unittest.mock import Mock, patch
from typing import Dict, Any

# テスト対象のインポート
from src.debug import (
    setup_enhanced_logging,
    log_game_error,
    log_ui_action,
    create_debug_context,
    check_debug_features,
    DebugContext,
    ENHANCED_LOGGING_AVAILABLE,
    MIDDLEWARE_AVAILABLE,
    UI_DEBUG_AVAILABLE
)


class TestDebugIntegration:
    """デバッグ機能統合テストクラス"""
    
    def test_check_debug_features(self):
        """デバッグ機能チェックテスト"""
        features = check_debug_features()
        
        assert isinstance(features, dict)
        assert "enhanced_logging" in features
        assert "debug_middleware" in features
        assert "ui_debug_helper" in features
        
        # 機能フラグと一致することを確認
        assert features["enhanced_logging"] == ENHANCED_LOGGING_AVAILABLE
        assert features["debug_middleware"] == MIDDLEWARE_AVAILABLE
        assert features["ui_debug_helper"] == UI_DEBUG_AVAILABLE
    
    def test_setup_enhanced_logging_with_middleware(self):
        """拡張ロギング設定テスト（ミドルウェア有効）"""
        mock_game = Mock()
        mock_game.handle_event = Mock()
        mock_game.update = Mock()
        mock_game.draw = Mock()
        
        middleware = setup_enhanced_logging(
            mock_game,
            logger_name="test_game",
            enable_middleware=True
        )
        
        if ENHANCED_LOGGING_AVAILABLE and MIDDLEWARE_AVAILABLE:
            # 機能が利用可能な場合
            assert middleware is not None
            assert hasattr(middleware, 'game_instance')
            assert hasattr(middleware, 'enhanced_logger')
        else:
            # 機能が利用不可能な場合
            assert middleware is None
    
    def test_setup_enhanced_logging_without_middleware(self):
        """拡張ロギング設定テスト（ミドルウェア無効）"""
        mock_game = Mock()
        
        middleware = setup_enhanced_logging(
            mock_game,
            enable_middleware=False
        )
        
        # ミドルウェアを無効にした場合はNone
        assert middleware is None
    
    def test_setup_enhanced_logging_with_custom_methods(self):
        """カスタムメソッド指定での拡張ロギング設定テスト"""
        mock_game = Mock()
        mock_game.custom_method = Mock()
        
        custom_methods = ["custom_method"]
        middleware = setup_enhanced_logging(
            mock_game,
            methods_to_wrap=custom_methods
        )
        
        if ENHANCED_LOGGING_AVAILABLE and MIDDLEWARE_AVAILABLE:
            assert middleware is not None
            # カスタムメソッドがラップされていることを確認
            assert "custom_method" in middleware.wrapped_methods
    
    def test_log_game_error_with_enhanced_logging(self):
        """拡張ロギングでのゲームエラーログテスト"""
        test_error = ValueError("Test game error")
        context = {"phase": "initialization", "state": "loading"}
        
        if ENHANCED_LOGGING_AVAILABLE:
            with patch('src.debug.get_enhanced_logger') as mock_get_logger:
                mock_logger = Mock()
                mock_get_logger.return_value = mock_logger
                
                log_game_error(test_error, context=context)
                
                # 拡張ロガーが使用されたことを確認
                mock_get_logger.assert_called_once_with("game_error")
                mock_logger.push_context.assert_called_once_with(context)
                mock_logger.log_ui_error.assert_called_once_with(test_error, None)
                mock_logger.pop_context.assert_called_once()
        else:
            # フォールバック動作のテスト
            with patch('logging.getLogger') as mock_get_logger:
                mock_logger = Mock()
                mock_get_logger.return_value = mock_logger
                
                log_game_error(test_error, context=context)
                
                mock_get_logger.assert_called_once_with("game_error")
                mock_logger.error.assert_called_once_with("Game error: Test game error")
    
    def test_log_ui_action_with_enhanced_logging(self):
        """拡張ロギングでのUI操作ログテスト"""
        action = "button_click"
        element_info = {"id": "main_menu_button", "text": "Start Game"}
        result = "success"
        
        if ENHANCED_LOGGING_AVAILABLE:
            with patch('src.debug.get_enhanced_logger') as mock_get_logger:
                mock_logger = Mock()
                mock_get_logger.return_value = mock_logger
                
                log_ui_action(action, element_info, result)
                
                # 拡張ロガーが使用されたことを確認
                mock_get_logger.assert_called_once_with("ui_action")
                
                # コンテキストプッシュの確認
                push_call = mock_logger.push_context.call_args[0][0]
                assert push_call["action"] == action
                assert push_call["element"] == element_info
                assert push_call["result"] == result
                
                mock_logger.log_with_context.assert_called_once()
                mock_logger.pop_context.assert_called_once()
        else:
            # フォールバック動作のテスト
            with patch('logging.getLogger') as mock_get_logger:
                mock_logger = Mock()
                mock_get_logger.return_value = mock_logger
                
                log_ui_action(action, element_info, result)
                
                mock_get_logger.assert_called_once_with("ui_action")
                mock_logger.info.assert_called_once()
    
    def test_debug_context_creation(self):
        """デバッグコンテキスト作成テスト"""
        description = "test_session"
        context = create_debug_context(description)
        
        assert isinstance(context, DebugContext)
        assert context.description == description
    
    def test_debug_context_manager_normal_flow(self):
        """デバッグコンテキストマネージャー通常フローテスト"""
        if ENHANCED_LOGGING_AVAILABLE:
            with patch('src.debug.get_enhanced_logger') as mock_get_logger:
                mock_logger = Mock()
                mock_get_logger.return_value = mock_logger
                
                with create_debug_context("test_session") as ctx:
                    assert ctx is not None
                    ctx.log("Test message", "INFO")
                
                # プッシュとポップが呼ばれたことを確認
                mock_logger.push_context.assert_called_once()
                mock_logger.pop_context.assert_called_once()
                mock_logger.log_with_context.assert_called_once()
        else:
            # フォールバック動作のテスト
            with patch('logging.getLogger') as mock_get_logger:
                mock_logger = Mock()
                mock_get_logger.return_value = mock_logger
                
                with create_debug_context("test_session") as ctx:
                    ctx.log("Test message", "INFO")
                
                mock_get_logger.assert_called()
                mock_logger.log.assert_called_once()
    
    def test_debug_context_manager_with_exception(self):
        """デバッグコンテキストマネージャー例外発生時テスト"""
        if ENHANCED_LOGGING_AVAILABLE:
            with patch('src.debug.get_enhanced_logger') as mock_get_logger:
                mock_logger = Mock()
                mock_get_logger.return_value = mock_logger
                
                test_exception = RuntimeError("Test exception")
                
                try:
                    with create_debug_context("test_session"):
                        raise test_exception
                except RuntimeError:
                    pass
                
                # 例外時のログ処理が呼ばれたことを確認
                mock_logger.log_ui_error.assert_called_once_with(test_exception)
                mock_logger.pop_context.assert_called_once()
    
    def test_debug_context_log_levels(self):
        """デバッグコンテキストログレベルテスト"""
        if ENHANCED_LOGGING_AVAILABLE:
            with patch('src.debug.get_enhanced_logger') as mock_get_logger:
                mock_logger = Mock()
                mock_get_logger.return_value = mock_logger
                
                with create_debug_context("test_session") as ctx:
                    ctx.log("Debug message", "DEBUG")
                    ctx.log("Info message", "INFO")
                    ctx.log("Warning message", "WARNING")
                    ctx.log("Error message", "ERROR")
                
                # 異なるレベルでログが呼ばれたことを確認
                assert mock_logger.log_with_context.call_count == 4
                
                calls = mock_logger.log_with_context.call_args_list
                assert calls[0][0][0] == logging.DEBUG
                assert calls[1][0][0] == logging.INFO
                assert calls[2][0][0] == logging.WARNING
                assert calls[3][0][0] == logging.ERROR
    
    def test_integration_with_game_instance(self):
        """ゲームインスタンスとの統合テスト"""
        # モックゲームクラス
        class MockGame:
            def __init__(self):
                self.state = "running"
            
            def handle_event(self, event):
                pass
            
            def update(self, dt):
                pass
            
            def draw(self, surface):
                pass
        
        game = MockGame()
        
        # 拡張ロギングを設定
        middleware = setup_enhanced_logging(game)
        
        if middleware is not None:
            # ミドルウェアが適用されたことを確認
            assert hasattr(middleware, 'game_instance')
            assert middleware.game_instance == game
            
            # ラップされたメソッドが存在することを確認
            assert callable(game.handle_event)
            assert callable(game.update)
            assert callable(game.draw)
            
            # 元のメソッドが保存されていることを確認
            assert 'handle_event' in middleware.wrapped_methods
            assert 'update' in middleware.wrapped_methods
            assert 'draw' in middleware.wrapped_methods
    
    def test_feature_flags_consistency(self):
        """機能フラグの一貫性テスト"""
        # インポートが成功した場合、対応するフラグがTrueであることを確認
        if ENHANCED_LOGGING_AVAILABLE:
            from src.debug.enhanced_logger import EnhancedGameLogger
            assert EnhancedGameLogger is not None
        
        if MIDDLEWARE_AVAILABLE:
            from src.debug.debug_middleware import DebugMiddleware
            assert DebugMiddleware is not None
        
        if UI_DEBUG_AVAILABLE:
            from src.debug.ui_debug_helper import UIDebugHelper
            assert UIDebugHelper is not None
    
    def test_error_handling_robustness(self):
        """エラーハンドリングの堅牢性テスト"""
        # 無効な引数でのエラーハンドリング
        try:
            log_game_error(None)  # None例外
        except Exception as e:
            pytest.fail(f"log_game_error should handle None gracefully: {e}")
        
        try:
            log_ui_action("", {})  # 空の引数
        except Exception as e:
            pytest.fail(f"log_ui_action should handle empty args gracefully: {e}")
        
        try:
            with create_debug_context(""):  # 空の説明
                pass
        except Exception as e:
            pytest.fail(f"create_debug_context should handle empty description: {e}")