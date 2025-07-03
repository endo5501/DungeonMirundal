"""
デバッグユーティリティパッケージ

拡張ロギング、デバッグミドルウェア、UIデバッグ機能を提供
"""

from typing import Any, Optional, List, Dict

# 拡張ロギング機能
try:
    from .enhanced_logger import EnhancedGameLogger, get_enhanced_logger
    ENHANCED_LOGGING_AVAILABLE = True
except ImportError:
    ENHANCED_LOGGING_AVAILABLE = False

# デバッグミドルウェア
try:
    from .debug_middleware import DebugMiddleware, with_enhanced_logging, create_debug_session
    MIDDLEWARE_AVAILABLE = True
except ImportError:
    MIDDLEWARE_AVAILABLE = False

# UIデバッグヘルパー
try:
    from .ui_debug_helper import UIDebugHelper
    UI_DEBUG_AVAILABLE = True
except ImportError:
    UI_DEBUG_AVAILABLE = False


# コンビニエンス関数
def setup_enhanced_logging(game_instance: Any, 
                         logger_name: str = "game",
                         enable_middleware: bool = True,
                         methods_to_wrap: Optional[List[str]] = None) -> Optional[DebugMiddleware]:
    """
    ゲームインスタンスに拡張ロギング機能を設定
    
    Args:
        game_instance: ゲームインスタンス
        logger_name: ロガー名
        enable_middleware: ミドルウェアを有効にするか
        methods_to_wrap: ラップするメソッド名のリスト
        
    Returns:
        設定されたDebugMiddlewareインスタンス、または None
    """
    if not ENHANCED_LOGGING_AVAILABLE or not MIDDLEWARE_AVAILABLE:
        return None
    
    if enable_middleware:
        middleware = DebugMiddleware(game_instance)
        if methods_to_wrap:
            middleware.wrap_methods(methods_to_wrap)
        else:
            middleware.wrap_with_enhanced_logging()
        return middleware
    
    return None


def log_game_error(error: Exception, 
                  context: Optional[Dict[str, Any]] = None,
                  ui_element: Any = None,
                  logger_name: str = "game_error") -> None:
    """
    ゲームエラーを拡張ロギングで記録
    
    Args:
        error: 発生した例外
        context: コンテキスト情報
        ui_element: 関連するUI要素
        logger_name: ロガー名
    """
    if not ENHANCED_LOGGING_AVAILABLE:
        # フォールバック
        import logging
        logging.getLogger(logger_name).error(f"Game error: {str(error)}")
        return
    
    logger = get_enhanced_logger(logger_name)
    
    if context:
        logger.push_context(context)
    
    try:
        logger.log_ui_error(error, ui_element)
    finally:
        if context:
            logger.pop_context()


def log_ui_action(action: str, 
                 element_info: Dict[str, Any],
                 result: Optional[str] = None,
                 logger_name: str = "ui_action") -> None:
    """
    UI操作を拡張ロギングで記録
    
    Args:
        action: 操作内容
        element_info: UI要素情報
        result: 操作結果
        logger_name: ロガー名
    """
    if not ENHANCED_LOGGING_AVAILABLE:
        # フォールバック
        import logging
        logging.getLogger(logger_name).info(f"UI action: {action} on {element_info}")
        return
    
    logger = get_enhanced_logger(logger_name)
    
    context = {
        "action": action,
        "element": element_info,
        "result": result
    }
    
    logger.push_context(context)
    try:
        import logging
        logger.log_with_context(logging.INFO, f"UI action: {action}")
    finally:
        logger.pop_context()


def create_debug_context(description: str = "debug_session") -> 'DebugContext':
    """
    デバッグコンテキストを作成
    
    Args:
        description: セッションの説明
        
    Returns:
        DebugContextインスタンス
    """
    return DebugContext(description)


class DebugContext:
    """デバッグセッション用のコンテキストマネージャー"""
    
    def __init__(self, description: str = "debug_session"):
        self.description = description
        self.logger = None
        if ENHANCED_LOGGING_AVAILABLE:
            self.logger = get_enhanced_logger(f"session.{description}")
    
    def __enter__(self):
        if self.logger:
            self.logger.push_context({"session": self.description, "phase": "start"})
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.logger:
            if exc_type:
                self.logger.log_ui_error(exc_val)
            self.logger.pop_context()
    
    def log(self, message: str, level: str = "INFO", **kwargs):
        """コンテキスト内でログ出力"""
        if self.logger:
            import logging
            log_level = getattr(logging, level.upper(), logging.INFO)
            self.logger.log_with_context(log_level, message, **kwargs)
        else:
            # フォールバック
            import logging
            logging.getLogger(f"session.{self.description}").log(
                getattr(logging, level.upper(), logging.INFO), 
                message
            )


# 機能可用性チェック関数
def check_debug_features() -> Dict[str, bool]:
    """
    利用可能なデバッグ機能をチェック
    
    Returns:
        機能の可用性辞書
    """
    return {
        "enhanced_logging": ENHANCED_LOGGING_AVAILABLE,
        "debug_middleware": MIDDLEWARE_AVAILABLE,
        "ui_debug_helper": UI_DEBUG_AVAILABLE
    }


# パッケージレベルのエクスポート
__all__ = [
    # コンビニエンス関数
    "setup_enhanced_logging",
    "log_game_error", 
    "log_ui_action",
    "create_debug_context",
    "check_debug_features",
    
    # クラス
    "DebugContext",
    
    # 機能フラグ
    "ENHANCED_LOGGING_AVAILABLE",
    "MIDDLEWARE_AVAILABLE", 
    "UI_DEBUG_AVAILABLE"
]

# 条件付きエクスポート
if ENHANCED_LOGGING_AVAILABLE:
    __all__.extend(["EnhancedGameLogger", "get_enhanced_logger"])

if MIDDLEWARE_AVAILABLE:
    __all__.extend(["DebugMiddleware", "with_enhanced_logging", "create_debug_session"])

if UI_DEBUG_AVAILABLE:
    __all__.extend(["UIDebugHelper"])