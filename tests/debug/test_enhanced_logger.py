"""
EnhancedGameLoggerクラスのテスト

エラー発生時のコンテキスト情報、UI状態、pygame-gui固有情報を詳細に記録する
拡張ロギング機能をテストする。
"""

import pytest
import logging
import json
import time
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
from typing import Dict, List, Any

from src.debug.enhanced_logger import EnhancedGameLogger


class TestEnhancedGameLogger:
    """EnhancedGameLoggerのテストクラス"""
    
    @pytest.fixture
    def logger_instance(self):
        """EnhancedGameLoggerインスタンスを作成"""
        return EnhancedGameLogger("test_logger")
    
    @pytest.fixture
    def mock_ui_element(self):
        """モックのUI要素を作成"""
        element = Mock()
        element.__class__.__name__ = "UIButton"
        element.object_ids = ["test_button"]
        element.rect = Mock(x=100, y=200, width=80, height=30)
        element.visible = 1
        element.text = "Click Me"
        element.enabled = True
        element.tooltip_text = "Test button tooltip"
        return element
    
    def test_logger_initialization(self, logger_instance):
        """ロガーの初期化テスト"""
        assert logger_instance.name == "test_logger"
        assert len(logger_instance.context_stack) == 0
        assert isinstance(logger_instance.logger, logging.Logger)
    
    def test_push_pop_context(self, logger_instance):
        """コンテキストのプッシュ・ポップテスト"""
        # コンテキストをプッシュ
        context1 = {"event_type": "MOUSEBUTTONDOWN", "position": [100, 200]}
        logger_instance.push_context(context1)
        
        assert len(logger_instance.context_stack) == 1
        assert logger_instance.context_stack[0]["context"] == context1
        assert "timestamp" in logger_instance.context_stack[0]
        assert "caller" in logger_instance.context_stack[0]
        
        # 2つ目のコンテキストをプッシュ
        context2 = {"element_id": "test_button", "action": "click"}
        logger_instance.push_context(context2)
        
        assert len(logger_instance.context_stack) == 2
        assert logger_instance.context_stack[1]["context"] == context2
        
        # ポップテスト
        popped = logger_instance.pop_context()
        assert popped["context"] == context2  # 最後にプッシュされた要素がポップされる
        assert len(logger_instance.context_stack) == 1
        
        # 2つ目をポップ
        logger_instance.pop_context()
        assert len(logger_instance.context_stack) == 0
    
    def test_context_stack_overflow_protection(self, logger_instance):
        """コンテキストスタックのオーバーフロー保護テスト"""
        # 最大スタック数を超えてプッシュ
        max_stack_size = logger_instance.MAX_CONTEXT_STACK_SIZE
        
        for i in range(max_stack_size + 5):
            logger_instance.push_context({"test": f"context_{i}"})
        
        # スタックサイズが制限内に収まることを確認
        assert len(logger_instance.context_stack) == max_stack_size
        
        # 最新のコンテキストが保持されることを確認
        latest_context = logger_instance.context_stack[-1]
        assert latest_context["context"]["test"] == f"context_{max_stack_size + 4}"
    
    def test_log_with_context(self, logger_instance):
        """コンテキスト付きログ出力テスト"""
        # コンテキストを設定
        logger_instance.push_context({"method": "handle_event"})
        logger_instance.push_context({"element": "button_click"})
        
        with patch.object(logger_instance.logger, 'log') as mock_log:
            logger_instance.log_with_context(
                logging.ERROR, 
                "Test error message",
                extra_data={"test": "value"}
            )
            
            # ログが呼ばれたことを確認
            mock_log.assert_called_once()
            call_args = mock_log.call_args
            
            assert call_args[0][0] == logging.ERROR
            assert call_args[0][1] == "Test error message"
            
            # extraデータにコンテキストが含まれることを確認
            extra = call_args[1]['extra']
            assert 'debug_info' in extra
            debug_info = extra['debug_info']
            
            assert 'context_stack' in debug_info
            assert len(debug_info['context_stack']) == 2
            assert 'ui_state' in debug_info
            assert debug_info['extra_data'] == {"test": "value"}
    
    def test_log_ui_error(self, logger_instance, mock_ui_element):
        """UI関連エラーログテスト"""
        # テスト用例外を作成
        test_error = AttributeError("'WindowManager' object has no attribute 'show_dialog'")
        
        with patch.object(logger_instance.logger, 'log') as mock_log, \
             patch.object(logger_instance, '_get_ui_state') as mock_ui_state:
            
            mock_ui_state.return_value = {"windows": [], "elements": 1}
            
            logger_instance.log_ui_error(test_error, mock_ui_element)
            
            # ログが呼ばれたことを確認
            mock_log.assert_called_once()
            call_args = mock_log.call_args
            
            assert call_args[0][0] == logging.ERROR
            assert "UI Error occurred" in call_args[0][1]
            
            # UI要素情報が含まれることを確認
            extra = call_args[1]['extra']
            debug_info = extra['debug_info']
            
            assert debug_info['error_type'] == 'AttributeError'
            assert debug_info['error_message'] == "'WindowManager' object has no attribute 'show_dialog'"
            assert 'traceback' in debug_info
            
            ui_element_info = debug_info['ui_element']
            assert ui_element_info['type'] == 'UIButton'
            assert ui_element_info['object_id'] == 'test_button'
            assert ui_element_info['position'] == {'x': 100, 'y': 200}
            assert ui_element_info['size'] == {'width': 80, 'height': 30}
    
    def test_log_ui_error_without_element(self, logger_instance):
        """UI要素なしでのエラーログテスト"""
        test_error = ValueError("Test error without UI element")
        
        with patch.object(logger_instance.logger, 'log') as mock_log:
            logger_instance.log_ui_error(test_error)
            
            mock_log.assert_called_once()
            call_args = mock_log.call_args
            extra = call_args[1]['extra']
            debug_info = extra['debug_info']
            
            assert debug_info['ui_element'] is None
            assert debug_info['error_type'] == 'ValueError'
    
    def test_get_ui_state_with_ui_helper(self, logger_instance):
        """UIDebugHelperを使用したUI状態取得テスト"""
        mock_hierarchy = {
            "windows": [{"id": "main", "type": "MainWindow"}],
            "ui_elements": [{"id": "button1", "type": "UIButton"}],
            "window_stack": ["main"]
        }
        
        with patch('src.debug.ui_debug_helper.UIDebugHelper') as mock_helper_class:
            mock_helper = Mock()
            mock_helper.dump_ui_hierarchy.return_value = mock_hierarchy
            mock_helper_class.return_value = mock_helper
            
            ui_state = logger_instance._get_ui_state()
            
            assert ui_state == mock_hierarchy
            mock_helper.dump_ui_hierarchy.assert_called_once()
    
    def test_get_ui_state_fallback(self, logger_instance):
        """UIDebugHelper利用不可時のフォールバックテスト"""
        with patch('src.debug.ui_debug_helper.UIDebugHelper', side_effect=ImportError):
            ui_state = logger_instance._get_ui_state()
            
            assert ui_state == {"error": "UIDebugHelper not available"}
    
    def test_extract_ui_element_info(self, logger_instance, mock_ui_element):
        """UI要素情報抽出テスト"""
        info = logger_instance._extract_ui_element_info(mock_ui_element)
        
        expected_info = {
            "type": "UIButton",
            "object_id": "test_button",
            "object_ids": ["test_button"],
            "position": {"x": 100, "y": 200},
            "size": {"width": 80, "height": 30},
            "visible": True,
            "attributes": {
                "text": "Click Me",
                "enabled": "True",  # _safe_str()により文字列に変換される
                "tooltip": "Test button tooltip"
            }
        }
        
        assert info == expected_info
    
    def test_extract_ui_element_info_with_error(self, logger_instance):
        """UI要素情報抽出時のエラーハンドリングテスト"""
        # 壊れたmockオブジェクト
        broken_element = Mock()
        broken_element.__class__.__name__ = "BrokenElement"
        broken_element.object_ids = Mock(side_effect=AttributeError("broken"))
        
        info = logger_instance._extract_ui_element_info(broken_element)
        
        assert info["type"] == "BrokenElement"
        assert info["object_id"] == "unknown"
        assert "error" in info
    
    def test_safe_str_conversion(self, logger_instance):
        """安全な文字列変換テスト"""
        # 正常なオブジェクト
        normal_obj = "test string"
        assert logger_instance._safe_str(normal_obj) == "test string"
        
        # str()でエラーを起こすオブジェクト
        broken_obj = Mock()
        broken_obj.__str__ = Mock(side_effect=Exception("broken str"))
        result = logger_instance._safe_str(broken_obj)
        assert "Error converting to string" in result
        
        # Noneオブジェクト
        assert logger_instance._safe_str(None) == "None"
    
    def test_context_serialization(self, logger_instance):
        """コンテキスト情報のシリアライゼーションテスト"""
        # 複雑なオブジェクトを含むコンテキスト
        complex_context = {
            "string": "test",
            "number": 42,
            "list": [1, 2, 3],
            "dict": {"nested": "value"},
            "mock": Mock(),  # シリアライズできないオブジェクト
            "none": None
        }
        
        logger_instance.push_context(complex_context)
        
        with patch.object(logger_instance.logger, 'log') as mock_log:
            logger_instance.log_with_context(logging.INFO, "Test message")
            
            call_args = mock_log.call_args
            extra = call_args[1]['extra']
            debug_info = extra['debug_info']
            
            # JSON シリアライズ可能であることを確認
            context_json = json.dumps(debug_info['context_stack'])
            assert context_json  # エラーなく変換できる
    
    def test_performance_impact(self, logger_instance):
        """パフォーマンス影響テスト"""
        # 大量のコンテキストプッシュでも性能が劣化しないことを確認
        start_time = time.time()
        
        for i in range(1000):
            logger_instance.push_context({"iteration": i})
        
        elapsed = time.time() - start_time
        assert elapsed < 1.0  # 1秒以内で完了することを確認
        
        # ログ出力の性能確認
        with patch.object(logger_instance.logger, 'log'):
            start_time = time.time()
            
            for i in range(100):
                logger_instance.log_with_context(logging.INFO, f"Test message {i}")
            
            elapsed = time.time() - start_time
            assert elapsed < 1.0  # 1秒以内で完了することを確認