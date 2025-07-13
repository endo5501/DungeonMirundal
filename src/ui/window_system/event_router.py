"""
EventRouter クラス

イベントルーティングとウィンドウ間通信を管理
"""

from typing import Dict, List, Callable, Any, Optional
import pygame
from enum import Enum
from dataclasses import dataclass
from datetime import datetime

from src.utils.logger import logger
from .window import Window, WindowState


class MessagePriority(Enum):
    """メッセージ優先度"""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    CRITICAL = 4


@dataclass
class WindowMessage:
    """ウィンドウ間メッセージ"""
    sender_id: str
    receiver_id: str
    message_type: str
    data: Dict[str, Any]
    priority: MessagePriority
    timestamp: datetime
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()


class EventRouter:
    """
    イベントルーター
    
    統一されたイベント分配システムとウィンドウ間通信を提供する：
    - イベントの適切なルーティング
    - ウィンドウ間メッセージング
    - ブロードキャスト機能
    - イベント監視・ロギング
    """
    
    def __init__(self):
        """イベントルーターを初期化"""
        # メッセージキュー（優先度別）
        self.message_queues: Dict[MessagePriority, List[WindowMessage]] = {
            priority: [] for priority in MessagePriority
        }
        
        # イベントリスナー
        self.global_event_listeners: List[Callable[[pygame.event.Event], bool]] = []
        self.window_event_listeners: Dict[str, List[Callable[[pygame.event.Event], bool]]] = {}
        
        # メッセージハンドラー
        self.message_handlers: Dict[str, Callable[[WindowMessage], None]] = {}
        
        # 統計情報
        self.event_stats = {
            'events_processed': 0,
            'messages_sent': 0,
            'broadcasts_sent': 0,
            'failed_deliveries': 0
        }
        
        # 設定
        self.max_queue_size = 1000
        self.debug_mode = False
        
    
    def route_event(self, event: pygame.event.Event, target_window: Optional[Window] = None) -> bool:
        """
        イベントをルーティング
        
        Args:
            event: Pygameイベント
            target_window: ターゲットウィンドウ（Noneで自動選択）
            
        Returns:
            bool: イベントが処理された場合True
        """
        self.event_stats['events_processed'] += 1
        
        if self.debug_mode:
            logger.debug(f"イベントをルーティング: {event.type} -> {target_window.window_id if target_window else 'auto'}")
        
        # グローバルイベントリスナーを先に処理
        for listener in self.global_event_listeners:
            try:
                if listener(event):
                    return True  # イベントが処理された
            except Exception as e:
                logger.error(f"グローバルイベントリスナーでエラー: {e}")
        
        # ターゲットウィンドウが指定されている場合
        if target_window:
            return self._route_to_window(event, target_window)
        
        return False
    
    def _route_to_window(self, event: pygame.event.Event, window: Window) -> bool:
        """
        特定のウィンドウにイベントをルーティング
        
        Args:
            event: Pygameイベント
            window: ターゲットウィンドウ
            
        Returns:
            bool: イベントが処理された場合True
        """
        if window.state != WindowState.SHOWN:
            return False
        
        # ウィンドウ固有のイベントリスナーを処理
        window_listeners = self.window_event_listeners.get(window.window_id, [])
        for listener in window_listeners:
            try:
                if listener(event):
                    return True
            except Exception as e:
                logger.error(f"ウィンドウイベントリスナーでエラー ({window.window_id}): {e}")
        
        # ウィンドウのイベントハンドラーを呼び出し
        try:
            return window.handle_event(event)
        except Exception as e:
            logger.error(f"ウィンドウイベントハンドラーでエラー ({window.window_id}): {e}")
            return False
    
    def send_message(self, sender_window: Window, receiver_id: str, message_type: str, 
                    data: Dict[str, Any] = None, priority: MessagePriority = MessagePriority.NORMAL) -> bool:
        """
        ウィンドウ間メッセージを送信
        
        Args:
            sender_window: 送信元ウィンドウ
            receiver_id: 受信者ウィンドウID
            message_type: メッセージタイプ
            data: メッセージデータ
            priority: メッセージ優先度
            
        Returns:
            bool: 送信に成功した場合True
        """
        if data is None:
            data = {}
        
        message = WindowMessage(
            sender_id=sender_window.window_id,
            receiver_id=receiver_id,
            message_type=message_type,
            data=data,
            priority=priority,
            timestamp=datetime.now()
        )
        
        # キューに追加
        queue = self.message_queues[priority]
        if len(queue) >= self.max_queue_size:
            logger.warning(f"メッセージキューが満杯です (priority: {priority.name})")
            return False
        
        queue.append(message)
        self.event_stats['messages_sent'] += 1
        
        if self.debug_mode:
            logger.debug(f"メッセージを送信: {sender_window.window_id} -> {receiver_id} ({message_type})")
        
        return True
    
    def broadcast_message(self, sender_window: Window, message_type: str, 
                         data: Dict[str, Any] = None, priority: MessagePriority = MessagePriority.NORMAL) -> int:
        """
        ブロードキャストメッセージを送信
        
        Args:
            sender_window: 送信元ウィンドウ
            message_type: メッセージタイプ
            data: メッセージデータ
            priority: メッセージ優先度
            
        Returns:
            int: 送信されたメッセージ数
        """
        if data is None:
            data = {}
        
        sent_count = 0
        
        # 全てのウィンドウリスナーに送信
        for window_id in self.window_event_listeners.keys():
            if window_id != sender_window.window_id:  # 送信者には送信しない
                if self.send_message(sender_window, window_id, message_type, data, priority):
                    sent_count += 1
        
        self.event_stats['broadcasts_sent'] += 1
        
        if self.debug_mode:
            logger.debug(f"ブロードキャストメッセージを送信: {sender_window.window_id} -> {sent_count} recipients ({message_type})")
        
        return sent_count
    
    def process_message_queue(self, window_registry: Dict[str, Window]) -> int:
        """
        メッセージキューを処理
        
        Args:
            window_registry: ウィンドウレジストリ
            
        Returns:
            int: 処理されたメッセージ数
        """
        processed_count = 0
        
        # 優先度順にメッセージを処理
        for priority in [MessagePriority.CRITICAL, MessagePriority.HIGH, MessagePriority.NORMAL, MessagePriority.LOW]:
            queue = self.message_queues[priority]
            
            while queue:
                message = queue.pop(0)
                
                # 受信者ウィンドウを取得
                receiver_window = window_registry.get(message.receiver_id)
                if not receiver_window:
                    self.event_stats['failed_deliveries'] += 1
                    if self.debug_mode:
                        logger.debug(f"受信者ウィンドウが見つかりません: {message.receiver_id}")
                    continue
                
                # 受信者が表示されていない場合はスキップ
                if receiver_window.state != WindowState.SHOWN:
                    continue
                
                # メッセージを配信
                try:
                    sender_window = window_registry.get(message.sender_id)
                    receiver_window.receive_message(sender_window, message.message_type, message.data)
                    processed_count += 1
                    
                    if self.debug_mode:
                        logger.debug(f"メッセージを配信: {message.sender_id} -> {message.receiver_id} ({message.message_type})")
                
                except Exception as e:
                    logger.error(f"メッセージ配信でエラー: {e}")
                    self.event_stats['failed_deliveries'] += 1
        
        return processed_count
    
    def add_global_event_listener(self, listener: Callable[[pygame.event.Event], bool]) -> None:
        """
        グローバルイベントリスナーを追加
        
        Args:
            listener: イベントリスナー関数
        """
        if listener not in self.global_event_listeners:
            self.global_event_listeners.append(listener)
            logger.debug("グローバルイベントリスナーを追加しました")
    
    def remove_global_event_listener(self, listener: Callable[[pygame.event.Event], bool]) -> None:
        """
        グローバルイベントリスナーを削除
        
        Args:
            listener: イベントリスナー関数
        """
        if listener in self.global_event_listeners:
            self.global_event_listeners.remove(listener)
            logger.debug("グローバルイベントリスナーを削除しました")
    
    def add_window_event_listener(self, window_id: str, listener: Callable[[pygame.event.Event], bool]) -> None:
        """
        ウィンドウ固有のイベントリスナーを追加
        
        Args:
            window_id: ウィンドウID
            listener: イベントリスナー関数
        """
        if window_id not in self.window_event_listeners:
            self.window_event_listeners[window_id] = []
        
        if listener not in self.window_event_listeners[window_id]:
            self.window_event_listeners[window_id].append(listener)
            logger.debug(f"ウィンドウイベントリスナーを追加: {window_id}")
    
    def remove_window_event_listener(self, window_id: str, listener: Callable[[pygame.event.Event], bool]) -> None:
        """
        ウィンドウ固有のイベントリスナーを削除
        
        Args:
            window_id: ウィンドウID
            listener: イベントリスナー関数
        """
        if window_id in self.window_event_listeners:
            listeners = self.window_event_listeners[window_id]
            if listener in listeners:
                listeners.remove(listener)
                logger.debug(f"ウィンドウイベントリスナーを削除: {window_id}")
                
                # リストが空になったら削除
                if not listeners:
                    del self.window_event_listeners[window_id]
    
    def cleanup_window_listeners(self, window_id: str) -> None:
        """
        ウィンドウのイベントリスナーをクリーンアップ
        
        Args:
            window_id: ウィンドウID
        """
        if window_id in self.window_event_listeners:
            del self.window_event_listeners[window_id]
            logger.debug(f"ウィンドウイベントリスナーをクリーンアップ: {window_id}")
    
    def register_message_handler(self, message_type: str, handler: Callable[[WindowMessage], None]) -> None:
        """
        メッセージハンドラーを登録
        
        Args:
            message_type: メッセージタイプ
            handler: ハンドラー関数
        """
        self.message_handlers[message_type] = handler
        logger.debug(f"メッセージハンドラーを登録: {message_type}")
    
    def unregister_message_handler(self, message_type: str) -> None:
        """
        メッセージハンドラーを登録解除
        
        Args:
            message_type: メッセージタイプ
        """
        if message_type in self.message_handlers:
            del self.message_handlers[message_type]
            logger.debug(f"メッセージハンドラーを登録解除: {message_type}")
    
    def clear_message_queues(self) -> None:
        """全てのメッセージキューをクリア"""
        total_cleared = 0
        for queue in self.message_queues.values():
            total_cleared += len(queue)
            queue.clear()
        
        if total_cleared > 0:
            logger.debug(f"メッセージキューをクリア: {total_cleared} messages")
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        統計情報を取得
        
        Returns:
            Dict[str, Any]: 統計情報
        """
        queue_sizes = {f"{priority.name.lower()}_queue": len(queue) 
                      for priority, queue in self.message_queues.items()}
        
        return {
            **self.event_stats,
            **queue_sizes,
            'global_listeners': len(self.global_event_listeners),
            'window_listeners': len(self.window_event_listeners),
            'message_handlers': len(self.message_handlers)
        }
    
    def get_debug_info(self) -> List[str]:
        """
        デバッグ情報を取得
        
        Returns:
            List[str]: デバッグ情報の文字列リスト
        """
        info = []
        
        # 統計情報
        stats = self.get_statistics()
        info.append("EventRouter Statistics:")
        for key, value in stats.items():
            info.append(f"  {key}: {value}")
        
        # メッセージキューの状態
        info.append("\nMessage Queue Status:")
        for priority, queue in self.message_queues.items():
            if queue:
                info.append(f"  {priority.name}: {len(queue)} messages")
                for msg in queue[:3]:  # 最新3件を表示
                    info.append(f"    {msg.sender_id} -> {msg.receiver_id}: {msg.message_type}")
        
        # イベントリスナーの状態
        info.append(f"\nEvent Listeners:")
        info.append(f"  Global: {len(self.global_event_listeners)}")
        info.append(f"  Window-specific: {len(self.window_event_listeners)}")
        for window_id, listeners in self.window_event_listeners.items():
            info.append(f"    {window_id}: {len(listeners)} listeners")
        
        return info
    
    def set_debug_mode(self, enabled: bool) -> None:
        """
        デバッグモードを設定
        
        Args:
            enabled: デバッグモードを有効にするかどうか
        """
        self.debug_mode = enabled
        logger.debug(f"デバッグモードを設定: {enabled}")
    
    def reset(self) -> None:
        """イベントルーターをリセット"""
        self.clear_message_queues()
        self.global_event_listeners.clear()
        self.window_event_listeners.clear()
        self.message_handlers.clear()
        
        # 統計情報をリセット
        for key in self.event_stats:
            self.event_stats[key] = 0
        
        logger.debug("EventRouterをリセットしました")
    
    def __str__(self) -> str:
        stats = self.get_statistics()
        return f"EventRouter(events: {stats['events_processed']}, messages: {stats['messages_sent']})"