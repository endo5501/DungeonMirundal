"""
拡張ゲームロガー

エラー発生時のコンテキスト情報、UI状態、pygame-gui固有情報を詳細に記録する
拡張ロギングシステム。
"""

import logging
import traceback
import time
import inspect
import json
from typing import Dict, List, Any, Optional, Union
from collections import deque
from datetime import datetime


class EnhancedGameLogger:
    """拡張されたゲームロガー"""
    
    MAX_CONTEXT_STACK_SIZE = 50  # コンテキストスタックの最大サイズ
    
    def __init__(self, name: str):
        """
        拡張ゲームロガーを初期化
        
        Args:
            name: ロガー名
        """
        self.name = name
        self.logger = logging.getLogger(name)
        self.context_stack: deque = deque(maxlen=self.MAX_CONTEXT_STACK_SIZE)
        
        # ロガーの設定（既存のutils.loggerと統合）
        if not self.logger.handlers:
            self._setup_logger()
    
    def _setup_logger(self) -> None:
        """ロガーの基本設定"""
        try:
            from src.utils.logger import setup_logger
            self.logger = setup_logger(self.name)
        except ImportError:
            # フォールバック設定
            self.logger.setLevel(logging.DEBUG)
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
    
    def push_context(self, context: Dict[str, Any]) -> None:
        """
        デバッグコンテキストをプッシュ
        
        Args:
            context: コンテキスト情報
        """
        caller_frame = inspect.currentframe().f_back
        caller_name = caller_frame.f_code.co_name if caller_frame else "unknown"
        
        context_entry = {
            "timestamp": time.time(),
            "context": self._make_serializable(context),
            "caller": caller_name
        }
        
        self.context_stack.append(context_entry)
    
    def pop_context(self) -> Optional[Dict[str, Any]]:
        """
        デバッグコンテキストをポップ
        
        Returns:
            ポップされたコンテキスト、またはNone
        """
        if self.context_stack:
            return self.context_stack.pop()
        return None
    
    def log_with_context(self, level: int, message: str, **kwargs) -> None:
        """
        コンテキスト付きでログ出力
        
        Args:
            level: ログレベル
            message: ログメッセージ
            **kwargs: 追加のキーワード引数
        """
        # 現在のコンテキストスタックをコピー（最新3つまで）
        context_snapshot = list(self.context_stack)[-3:] if self.context_stack else []
        
        # UI状態を取得
        ui_state = self._get_ui_state()
        
        # デバッグ情報を構築
        debug_info = {
            "context_stack": context_snapshot,
            "ui_state": ui_state,
            "timestamp": datetime.now().isoformat(),
            **kwargs
        }
        
        # extraデータとしてログに追加
        extra = {"debug_info": debug_info}
        
        self.logger.log(level, message, extra=extra)
    
    def log_ui_error(self, error: Exception, ui_element: Any = None) -> None:
        """
        UI関連のエラーを詳細にログ
        
        Args:
            error: 発生した例外
            ui_element: 関連するUI要素（オプション）
        """
        error_info = {
            "error_type": type(error).__name__,
            "error_message": str(error),
            "traceback": traceback.format_exc(),
            "ui_element": self._extract_ui_element_info(ui_element) if ui_element else None,
            "timestamp": datetime.now().isoformat()
        }
        
        self.log_with_context(
            logging.ERROR,
            f"UI Error occurred: {type(error).__name__}",
            **error_info
        )
    
    def _get_ui_state(self) -> Dict[str, Any]:
        """
        現在のUI状態を取得
        
        Returns:
            UI状態情報
        """
        try:
            from src.debug.ui_debug_helper import UIDebugHelper
            ui_helper = UIDebugHelper()
            return ui_helper.dump_ui_hierarchy()
        except ImportError:
            return {"error": "UIDebugHelper not available"}
        except Exception as e:
            return {"error": f"Failed to get UI state: {str(e)}"}
    
    def _extract_ui_element_info(self, ui_element: Any) -> Dict[str, Any]:
        """
        UI要素から安全に情報を抽出
        
        Args:
            ui_element: UI要素オブジェクト
            
        Returns:
            UI要素情報
        """
        if ui_element is None:
            return None
        
        info = {
            "type": ui_element.__class__.__name__,
            "object_id": "unknown",
            "object_ids": [],
            "position": {},
            "size": {},
            "visible": False,
            "attributes": {}
        }
        
        try:
            # object_id情報
            if hasattr(ui_element, 'object_ids'):
                ids = ui_element.object_ids
                info['object_id'] = ids[0] if ids else 'unknown'
                info['object_ids'] = ids
            
            # 位置とサイズ情報
            if hasattr(ui_element, 'rect'):
                rect = ui_element.rect
                info['position'] = {'x': rect.x, 'y': rect.y}
                info['size'] = {'width': rect.width, 'height': rect.height}
            
            # 可視性
            if hasattr(ui_element, 'visible'):
                info['visible'] = bool(ui_element.visible)
            
            # 追加属性
            attributes = {}
            for attr_name in ['text', 'enabled', 'tooltip_text']:
                if hasattr(ui_element, attr_name):
                    try:
                        attr_value = getattr(ui_element, attr_name)
                        attributes[attr_name.replace('_text', '')] = self._safe_str(attr_value)
                    except Exception:
                        attributes[attr_name] = "Error getting attribute"
            
            if attributes:
                info['attributes'] = attributes
                
        except Exception as e:
            info['error'] = f"Error extracting UI element info: {str(e)}"
        
        return info
    
    def _safe_str(self, obj: Any) -> str:
        """
        オブジェクトを安全に文字列に変換
        
        Args:
            obj: 変換するオブジェクト
            
        Returns:
            文字列表現
        """
        if obj is None:
            return "None"
        
        try:
            return str(obj)
        except Exception as e:
            return f"Error converting to string: {type(obj).__name__}"
    
    def _make_serializable(self, obj: Any) -> Any:
        """
        オブジェクトをJSON シリアライズ可能な形式に変換
        
        Args:
            obj: 変換するオブジェクト
            
        Returns:
            シリアライズ可能なオブジェクト
        """
        if obj is None:
            return None
        elif isinstance(obj, (str, int, float, bool)):
            return obj
        elif isinstance(obj, (list, tuple)):
            return [self._make_serializable(item) for item in obj]
        elif isinstance(obj, dict):
            return {key: self._make_serializable(value) for key, value in obj.items()}
        else:
            # 複雑なオブジェクトは文字列表現に変換
            return self._safe_str(obj)


# デフォルトインスタンス（遅延初期化）
_default_enhanced_logger = None

def get_enhanced_logger(name: str = "enhanced_game") -> EnhancedGameLogger:
    """
    拡張ゲームロガーを取得
    
    Args:
        name: ロガー名
        
    Returns:
        EnhancedGameLoggerインスタンス
    """
    global _default_enhanced_logger
    if _default_enhanced_logger is None or _default_enhanced_logger.name != name:
        _default_enhanced_logger = EnhancedGameLogger(name)
    return _default_enhanced_logger