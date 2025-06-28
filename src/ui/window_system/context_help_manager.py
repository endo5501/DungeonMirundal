"""コンテキストヘルプ管理クラス

Fowler Extract Classパターンにより、HelpWindowからコンテキストヘルプに関する責任を抽出。
単一責任の原則に従い、状況依存ヘルプ・初回ヘルプ・動的ヘルプ表示を専門的に扱う。
"""

from typing import Dict, List, Optional, Any, Callable
from enum import Enum
import time

from src.ui.window_system.help_enums import HelpContext
from src.utils.logger import logger


class HelpTriggerType(Enum):
    """ヘルプトリガータイプ"""
    FIRST_TIME = "first_time"
    CONTEXT_CHANGE = "context_change"
    USER_REQUEST = "user_request"
    AUTOMATIC = "automatic"
    ERROR_STATE = "error_state"


class HelpPriority(Enum):
    """ヘルプ優先度"""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


class HelpRequest:
    """ヘルプリクエスト"""
    
    def __init__(self, context: HelpContext, trigger_type: HelpTriggerType,
                 priority: HelpPriority = HelpPriority.NORMAL, 
                 additional_data: Optional[Dict[str, Any]] = None):
        self.context = context
        self.trigger_type = trigger_type
        self.priority = priority
        self.additional_data = additional_data or {}
        self.timestamp = time.time()
        self.request_id = f"{context.value}_{trigger_type.value}_{int(self.timestamp)}"


class ContextHelpManager:
    """コンテキストヘルプ管理クラス
    
    状況依存ヘルプ・初回ヘルプ・自動ヘルプ表示の制御を担当。
    Extract Classパターンにより、HelpWindowからコンテキスト管理ロジックを分離。
    """
    
    def __init__(self):
        """コンテキストヘルプマネージャー初期化"""
        # 状態管理
        self.current_context: Optional[HelpContext] = None
        self.previous_context: Optional[HelpContext] = None
        self.context_history: List[HelpContext] = []
        
        # 初回ヘルプ管理
        self.first_time_flags: Dict[str, bool] = {}
        self.first_time_shown: bool = False
        
        # 自動ヘルプ設定
        self.auto_help_enabled: bool = True
        self.auto_help_delay: float = 3.0  # 3秒後に自動表示
        self.last_context_change_time: float = 0.0
        
        # コールバック
        self.help_callbacks: Dict[HelpTriggerType, List[Callable]] = {
            trigger: [] for trigger in HelpTriggerType
        }
        
        # ヘルプリクエストキュー
        self.help_request_queue: List[HelpRequest] = []
        
        logger.debug("ContextHelpManagerを初期化しました")
    
    def set_context(self, context: HelpContext, trigger_auto_help: bool = True) -> None:
        """コンテキストを設定
        
        Args:
            context: 新しいコンテキスト
            trigger_auto_help: 自動ヘルプをトリガーするか
        """
        if self.current_context != context:
            self.previous_context = self.current_context
            self.current_context = context
            self.last_context_change_time = time.time()
            
            # コンテキスト履歴を更新
            self.context_history.append(context)
            if len(self.context_history) > 10:  # 履歴を10件に制限
                self.context_history.pop(0)
            
            logger.debug(f"コンテキストを変更: {self.previous_context} -> {context}")
            
            # コンテキスト変更コールバックを実行
            self._execute_callbacks(HelpTriggerType.CONTEXT_CHANGE, {
                'new_context': context,
                'previous_context': self.previous_context
            })
            
            # 自動ヘルプをトリガー
            if trigger_auto_help and self.auto_help_enabled:
                self._queue_auto_help_request(context)
    
    def request_context_help(self, context: Optional[HelpContext] = None,
                           priority: HelpPriority = HelpPriority.NORMAL) -> HelpRequest:
        """コンテキストヘルプをリクエスト
        
        Args:
            context: ヘルプコンテキスト（Noneの場合は現在のコンテキスト）
            priority: リクエスト優先度
            
        Returns:
            HelpRequest: ヘルプリクエスト
        """
        target_context = context or self.current_context
        
        if not target_context:
            logger.warning("コンテキストヘルプリクエストにコンテキストが指定されていません")
            target_context = HelpContext.OVERWORLD  # デフォルト
        
        request = HelpRequest(
            context=target_context,
            trigger_type=HelpTriggerType.USER_REQUEST,
            priority=priority
        )
        
        self.help_request_queue.append(request)
        logger.info(f"コンテキストヘルプをリクエスト: {target_context.value}")
        
        return request
    
    def request_first_time_help(self) -> Optional[HelpRequest]:
        """初回起動時ヘルプをリクエスト
        
        Returns:
            HelpRequest: ヘルプリクエスト、または None（既に表示済み）
        """
        if self.first_time_shown:
            logger.debug("初回ヘルプは既に表示済みです")
            return None
        
        request = HelpRequest(
            context=HelpContext.OVERWORLD,  # 初回ヘルプは地上部コンテキスト
            trigger_type=HelpTriggerType.FIRST_TIME,
            priority=HelpPriority.HIGH,
            additional_data={'is_first_time': True}
        )
        
        self.help_request_queue.append(request)
        self.first_time_shown = True
        
        logger.info("初回起動時ヘルプをリクエストしました")
        return request
    
    def check_first_time_context(self, context_key: str) -> bool:
        """特定のコンテキストが初回かチェック
        
        Args:
            context_key: コンテキストキー
            
        Returns:
            bool: 初回の場合True
        """
        if context_key not in self.first_time_flags:
            self.first_time_flags[context_key] = True
            logger.debug(f"初回コンテキスト検出: {context_key}")
            return True
        return False
    
    def mark_context_visited(self, context_key: str) -> None:
        """コンテキストを訪問済みとしてマーク
        
        Args:
            context_key: コンテキストキー
        """
        self.first_time_flags[context_key] = False
        logger.debug(f"コンテキストを訪問済みとしてマーク: {context_key}")
    
    def get_next_help_request(self) -> Optional[HelpRequest]:
        """次のヘルプリクエストを取得
        
        Returns:
            HelpRequest: 次のヘルプリクエスト、または None
        """
        if not self.help_request_queue:
            return None
        
        # 優先度でソート
        self.help_request_queue.sort(
            key=lambda req: (
                self._get_priority_value(req.priority),
                -req.timestamp  # 新しいリクエストを優先
            ),
            reverse=True
        )
        
        return self.help_request_queue.pop(0)
    
    def clear_help_requests(self) -> None:
        """全てのヘルプリクエストをクリア"""
        cleared_count = len(self.help_request_queue)
        self.help_request_queue.clear()
        logger.debug(f"{cleared_count}件のヘルプリクエストをクリアしました")
    
    def should_show_auto_help(self) -> bool:
        """自動ヘルプを表示すべきかチェック
        
        Returns:
            bool: 自動ヘルプを表示すべき場合True
        """
        if not self.auto_help_enabled:
            return False
        
        if not self.current_context:
            return False
        
        # コンテキスト変更から一定時間経過しているかチェック
        elapsed_time = time.time() - self.last_context_change_time
        return elapsed_time >= self.auto_help_delay
    
    def add_help_callback(self, trigger_type: HelpTriggerType, callback: Callable) -> None:
        """ヘルプコールバックを追加
        
        Args:
            trigger_type: トリガータイプ
            callback: コールバック関数
        """
        if trigger_type in self.help_callbacks:
            self.help_callbacks[trigger_type].append(callback)
            logger.debug(f"ヘルプコールバックを追加: {trigger_type.value}")
    
    def remove_help_callback(self, trigger_type: HelpTriggerType, callback: Callable) -> None:
        """ヘルプコールバックを削除
        
        Args:
            trigger_type: トリガータイプ
            callback: コールバック関数
        """
        if trigger_type in self.help_callbacks:
            try:
                self.help_callbacks[trigger_type].remove(callback)
                logger.debug(f"ヘルプコールバックを削除: {trigger_type.value}")
            except ValueError:
                logger.warning(f"コールバックが見つかりません: {trigger_type.value}")
    
    def enable_auto_help(self, enabled: bool = True, delay: Optional[float] = None) -> None:
        """自動ヘルプを有効/無効化
        
        Args:
            enabled: 有効にするかどうか
            delay: 自動表示遅延時間（秒）
        """
        self.auto_help_enabled = enabled
        if delay is not None:
            self.auto_help_delay = delay
        
        logger.info(f"自動ヘルプを{'有効' if enabled else '無効'}化")
    
    def get_context_history(self, max_count: int = 5) -> List[HelpContext]:
        """コンテキスト履歴を取得
        
        Args:
            max_count: 最大件数
            
        Returns:
            List[HelpContext]: コンテキスト履歴
        """
        return self.context_history[-max_count:] if self.context_history else []
    
    def get_help_statistics(self) -> Dict[str, Any]:
        """ヘルプ統計情報を取得
        
        Returns:
            Dict: 統計情報
        """
        return {
            'current_context': self.current_context.value if self.current_context else None,
            'previous_context': self.previous_context.value if self.previous_context else None,
            'context_history_count': len(self.context_history),
            'first_time_shown': self.first_time_shown,
            'first_time_contexts_count': len([v for v in self.first_time_flags.values() if v]),
            'auto_help_enabled': self.auto_help_enabled,
            'pending_requests': len(self.help_request_queue),
            'callback_counts': {
                trigger.value: len(callbacks) 
                for trigger, callbacks in self.help_callbacks.items()
            }
        }
    
    def _queue_auto_help_request(self, context: HelpContext) -> None:
        """自動ヘルプリクエストをキューに追加"""
        # 同じコンテキストの自動ヘルプが既にキューにある場合はスキップ
        for request in self.help_request_queue:
            if (request.context == context and 
                request.trigger_type == HelpTriggerType.AUTOMATIC):
                return
        
        request = HelpRequest(
            context=context,
            trigger_type=HelpTriggerType.AUTOMATIC,
            priority=HelpPriority.LOW,
            additional_data={'auto_triggered': True}
        )
        
        self.help_request_queue.append(request)
        logger.debug(f"自動ヘルプリクエストをキューに追加: {context.value}")
    
    def _execute_callbacks(self, trigger_type: HelpTriggerType, data: Dict[str, Any]) -> None:
        """コールバックを実行"""
        callbacks = self.help_callbacks.get(trigger_type, [])
        for callback in callbacks:
            try:
                callback(data)
            except Exception as e:
                logger.error(f"ヘルプコールバック実行エラー ({trigger_type.value}): {e}")
    
    def _get_priority_value(self, priority: HelpPriority) -> int:
        """優先度の数値を取得"""
        priority_values = {
            HelpPriority.LOW: 1,
            HelpPriority.NORMAL: 2,
            HelpPriority.HIGH: 3,
            HelpPriority.URGENT: 4
        }
        return priority_values.get(priority, 2)