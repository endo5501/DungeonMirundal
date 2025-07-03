"""
デバッグミドルウェア

ゲームインスタンスの主要メソッドをラップして、自動的にエラーログを強化する
ミドルウェアシステム。
"""

import time
import functools
from typing import Dict, List, Any, Optional, Callable
import pygame

from src.debug.enhanced_logger import EnhancedGameLogger


class DebugMiddleware:
    """ゲームデバッグ用ミドルウェア"""
    
    DEFAULT_METHODS_TO_WRAP = ['handle_event', 'update', 'draw']
    
    def __init__(self, game_instance: Any):
        """
        デバッグミドルウェアを初期化
        
        Args:
            game_instance: ラップするゲームインスタンス
        """
        self.game_instance = game_instance
        self.enhanced_logger = EnhancedGameLogger(f"debug.{game_instance.__class__.__name__}")
        self.wrapped_methods: Dict[str, Callable] = {}
        self.auto_wrapped = False
    
    def wrap_with_enhanced_logging(self, methods: Optional[List[str]] = None) -> None:
        """
        指定されたメソッドを拡張ログ機能でラップ
        
        Args:
            methods: ラップするメソッド名のリスト（Noneの場合はデフォルト）
        """
        if methods is None:
            methods = self.DEFAULT_METHODS_TO_WRAP
        
        self.wrap_methods(methods)
        self.auto_wrapped = True
    
    def wrap_methods(self, method_names: List[str]) -> None:
        """
        指定されたメソッドをラップ
        
        Args:
            method_names: ラップするメソッド名のリスト
        """
        for method_name in method_names:
            if hasattr(self.game_instance, method_name):
                original_method = getattr(self.game_instance, method_name)
                
                # 既にラップされていない場合のみラップ
                if method_name not in self.wrapped_methods:
                    wrapped_method = self._wrap_method_with_logging(original_method, method_name)
                    setattr(self.game_instance, method_name, wrapped_method)
                    self.wrapped_methods[method_name] = original_method
    
    def _wrap_method_with_logging(self, method: Callable, method_name: str) -> Callable:
        """
        メソッドを拡張ログ機能でラップ
        
        Args:
            method: ラップする元のメソッド
            method_name: メソッド名
            
        Returns:
            ラップされたメソッド
        """
        @functools.wraps(method)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            
            try:
                # コンテキストをプッシュ
                context = self._create_method_context(method_name, *args, **kwargs)
                context['start_time'] = start_time
                self.enhanced_logger.push_context(context)
                
                # 元のメソッドを実行
                result = method(*args, **kwargs)
                
                # 実行時間を記録
                execution_time = time.time() - start_time
                if execution_time > 0.1:  # 100ms以上の場合は性能ログ
                    self.enhanced_logger.log_with_context(
                        30,  # WARNING レベル
                        f"Slow method execution: {method_name}",
                        execution_time=execution_time
                    )
                
                return result
                
            except Exception as e:
                # エラーログを詳細に記録
                execution_time = time.time() - start_time
                self.enhanced_logger.log_ui_error(e)
                self.enhanced_logger.log_with_context(
                    40,  # ERROR レベル
                    f"Exception in {method_name}",
                    execution_time=execution_time,
                    exception_type=type(e).__name__
                )
                raise
                
            finally:
                # コンテキストをポップ
                try:
                    self.enhanced_logger.pop_context()
                except Exception:
                    # ポップ時のエラーは無視（ログシステム自体の問題を避ける）
                    pass
        
        return wrapper
    
    def _create_method_context(self, method_name: str, *args, **kwargs) -> Dict[str, Any]:
        """
        メソッド実行用のコンテキストを作成
        
        Args:
            method_name: メソッド名
            *args: メソッド引数
            **kwargs: メソッドキーワード引数
            
        Returns:
            コンテキスト情報
        """
        context = {
            "method": method_name,
            "args": {}
        }
        
        try:
            if method_name == "handle_event" and args:
                event = args[0]
                context["args"] = {
                    "event_type": getattr(event, 'type', 'unknown'),
                    "event_data": self._extract_event_info(event)
                }
            elif method_name == "update" and args:
                context["args"] = {"dt": args[0]}
            elif method_name == "draw" and args:
                context["args"] = {"surface": str(args[0])}
            else:
                # 汎用的な引数処理
                context["args"] = {"args": list(args), "kwargs": kwargs}
                
        except Exception as e:
            # コンテキスト作成でエラーが発生した場合
            context["args"] = {"error": f"Failed to create context: {str(e)}"}
            self.enhanced_logger.log_ui_error(e)
        
        return context
    
    def _extract_event_info(self, event: Any) -> Dict[str, Any]:
        """
        pygame イベントから情報を抽出
        
        Args:
            event: pygame イベントオブジェクト
            
        Returns:
            イベント情報
        """
        event_info = {}
        
        try:
            # マウスイベント
            if hasattr(event, 'pos'):
                event_info['pos'] = event.pos
            if hasattr(event, 'button'):
                event_info['button'] = event.button
            
            # キーボードイベント
            if hasattr(event, 'key'):
                event_info['key'] = event.key
            if hasattr(event, 'unicode'):
                event_info['unicode'] = event.unicode
            
            # UI関連イベント
            if hasattr(event, 'ui_element'):
                try:
                    element = event.ui_element
                    event_info['ui_element'] = {
                        'type': element.__class__.__name__,
                        'object_id': getattr(element, 'object_ids', ['unknown'])[0]
                    }
                except Exception:
                    event_info['ui_element'] = 'extraction_failed'
            
            if hasattr(event, 'ui_object_id'):
                try:
                    event_info['ui_object_id'] = str(event.ui_object_id)
                except Exception:
                    event_info['ui_object_id'] = 'extraction_failed'
                    
        except Exception:
            # イベント情報抽出でエラーが発生した場合は空の辞書を返す
            pass
        
        return event_info
    
    def restore_original_methods(self) -> None:
        """元のメソッドを復元"""
        for method_name, original_method in self.wrapped_methods.items():
            setattr(self.game_instance, method_name, original_method)
        
        self.wrapped_methods.clear()
        self.auto_wrapped = False
    
    def __enter__(self):
        """コンテキストマネージャーとして使用する際の開始処理"""
        if not self.auto_wrapped:
            self.wrap_with_enhanced_logging()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """コンテキストマネージャーとして使用する際の終了処理"""
        self.restore_original_methods()


# ユーティリティ関数
def with_enhanced_logging(game_instance: Any, methods: Optional[List[str]] = None):
    """
    ゲームインスタンスに拡張ログ機能を一時的に適用するデコレータ
    
    Args:
        game_instance: ゲームインスタンス
        methods: ラップするメソッド名のリスト
        
    Returns:
        DebugMiddlewareのコンテキストマネージャー
    """
    middleware = DebugMiddleware(game_instance)
    if methods:
        middleware.wrap_methods(methods)
    else:
        middleware.wrap_with_enhanced_logging()
    return middleware

def create_debug_session(game_instance: Any, session_name: str = "debug_session"):
    """
    デバッグセッションを作成
    
    Args:
        game_instance: ゲームインスタンス
        session_name: セッション名
        
    Returns:
        設定済みのDebugMiddleware
    """
    middleware = DebugMiddleware(game_instance)
    middleware.enhanced_logger.name = f"session.{session_name}"
    return middleware