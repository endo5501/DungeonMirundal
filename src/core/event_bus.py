"""イベントバスシステム

GameManagerの密結合問題を解決するためのイベント駆動通信システム。
Fowlerの「Replace Data Value with Object」と「Introduce Intermediate Data Structure」を適用。
"""

from typing import Dict, List, Callable, Any, Optional
from dataclasses import dataclass
from abc import ABC, abstractmethod
from enum import Enum
import weakref
import threading
from src.utils.logger import logger


class EventType(Enum):
    """ゲーム内イベントタイプ"""
    # パーティ関連
    PARTY_CREATED = "party_created"
    PARTY_MEMBER_ADDED = "party_member_added"
    PARTY_MEMBER_REMOVED = "party_member_removed"
    PARTY_GOLD_CHANGED = "party_gold_changed"
    
    # ゲーム状態関連
    SCENE_TRANSITION_REQUESTED = "scene_transition_requested"
    SCENE_TRANSITION_COMPLETED = "scene_transition_completed"
    GAME_STATE_CHANGED = "game_state_changed"
    LOCATION_CHANGED = "location_changed"
    GAME_SAVED = "game_saved"
    GAME_LOADED = "game_loaded"
    
    # ダンジョン関連
    DUNGEON_ENTERED = "dungeon_entered"
    DUNGEON_EXITED = "dungeon_exited"
    PLAYER_MOVED = "player_moved"
    ENCOUNTER_TRIGGERED = "encounter_triggered"
    
    # 戦闘関連
    COMBAT_STARTED = "combat_started"
    COMBAT_ENDED = "combat_ended"
    COMBAT_ACTION_EXECUTED = "combat_action_executed"
    
    # キャラクター関連
    CHARACTER_LEVEL_UP = "character_level_up"
    CHARACTER_HP_CHANGED = "character_hp_changed"
    CHARACTER_STATUS_CHANGED = "character_status_changed"
    
    # UI関連
    UI_WINDOW_OPENED = "ui_window_opened"
    UI_WINDOW_CLOSED = "ui_window_closed"
    UI_ACTION_REQUESTED = "ui_action_requested"
    
    # アイテム関連
    ITEM_ACQUIRED = "item_acquired"
    ITEM_USED = "item_used"
    EQUIPMENT_CHANGED = "equipment_changed"


@dataclass
class GameEvent:
    """ゲームイベントのデータクラス"""
    event_type: EventType
    source: str  # イベント発生源の識別子
    data: Dict[str, Any] = None
    timestamp: float = None
    
    def __post_init__(self):
        if self.data is None:
            self.data = {}
        if self.timestamp is None:
            import time
            self.timestamp = time.time()


class EventHandler(ABC):
    """イベントハンドラーの基底クラス"""
    
    @abstractmethod
    def handle_event(self, event: GameEvent) -> bool:
        """
        イベントを処理する
        
        Args:
            event: 処理対象のイベント
            
        Returns:
            bool: イベントが処理された場合True、他のハンドラーにも処理を委ねる場合False
        """
        pass
    
    def get_handled_event_types(self) -> List[EventType]:
        """このハンドラーが処理するイベントタイプのリスト"""
        return []


class EventBus:
    """イベントバスの実装
    
    Singleton パターンで実装し、ゲーム全体で一つのインスタンスを共有する。
    """
    
    _instance: Optional['EventBus'] = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if hasattr(self, '_initialized'):
            return
        
        self._subscribers: Dict[EventType, List[weakref.ref]] = {}
        self._event_queue: List[GameEvent] = []
        self._processing = False
        self._initialized = True
        
        logger.debug("イベントバス初期化完了")
    
    def subscribe(self, event_type: EventType, handler: EventHandler):
        """イベントタイプにハンドラーを登録"""
        if event_type not in self._subscribers:
            self._subscribers[event_type] = []
        
        # WeakRefを使用してハンドラーを保存（メモリリーク防止）
        handler_ref = weakref.ref(handler)
        self._subscribers[event_type].append(handler_ref)
        
        logger.debug(f"イベントハンドラー登録: {event_type.value} -> {handler.__class__.__name__}")
    
    def unsubscribe(self, event_type: EventType, handler: EventHandler):
        """イベントタイプからハンドラーを削除"""
        if event_type not in self._subscribers:
            return
        
        # WeakRefのリストから該当ハンドラーを削除
        self._subscribers[event_type] = [
            ref for ref in self._subscribers[event_type]
            if ref() is not None and ref() != handler
        ]
        
        logger.debug(f"イベントハンドラー削除: {event_type.value} -> {handler.__class__.__name__}")
    
    def publish(self, event: GameEvent):
        """イベントを発行"""
        logger.debug(f"イベント発行: {event.event_type.value} from {event.source}")
        
        # イベントをキューに追加
        self._event_queue.append(event)
        
        # 処理中でなければすぐに処理
        if not self._processing:
            self._process_events()
    
    def publish_immediate(self, event_type: EventType, source: str, data: Dict[str, Any] = None):
        """イベントを即座に発行"""
        event = GameEvent(event_type, source, data)
        self.publish(event)
    
    def _process_events(self):
        """キューに溜まったイベントを処理"""
        if self._processing:
            return
        
        self._processing = True
        
        try:
            while self._event_queue:
                event = self._event_queue.pop(0)
                self._handle_event(event)
        finally:
            self._processing = False
    
    def _handle_event(self, event: GameEvent):
        """単一イベントの処理"""
        event_type = event.event_type
        
        if event_type not in self._subscribers:
            return
        
        # 無効なWeakRefを除去
        valid_handlers = []
        for handler_ref in self._subscribers[event_type]:
            handler = handler_ref()
            if handler is not None:
                valid_handlers.append(handler_ref)
        
        self._subscribers[event_type] = valid_handlers
        
        # 各ハンドラーにイベントを配信
        for handler_ref in valid_handlers:
            handler = handler_ref()
            if handler is not None:
                try:
                    handled = handler.handle_event(event)
                    if handled:
                        # イベントが処理された場合、他のハンドラーには送らない
                        break
                except Exception as e:
                    logger.error(f"イベントハンドラーエラー: {handler.__class__.__name__}: {e}")
    
    def clear_all_subscribers(self):
        """全てのサブスクライバーをクリア（テスト用）"""
        self._subscribers.clear()
        logger.info("全イベントハンドラーをクリアしました")
    
    def get_subscriber_count(self, event_type: EventType) -> int:
        """指定イベントタイプのサブスクライバー数を取得"""
        if event_type not in self._subscribers:
            return 0
        
        # 有効なWeakRefのカウント
        valid_count = 0
        for handler_ref in self._subscribers[event_type]:
            if handler_ref() is not None:
                valid_count += 1
        
        return valid_count


class FunctionEventHandler(EventHandler):
    """関数ベースのイベントハンドラー
    
    クラスを作成せずに関数でイベント処理を行いたい場合に使用。
    """
    
    def __init__(self, handler_func: Callable[[GameEvent], bool], event_types: List[EventType] = None):
        self.handler_func = handler_func
        self.event_types = event_types or []
    
    def handle_event(self, event: GameEvent) -> bool:
        return self.handler_func(event)
    
    def get_handled_event_types(self) -> List[EventType]:
        return self.event_types


# === 便利関数 ===

def get_event_bus() -> EventBus:
    """グローバルイベントバスインスタンスを取得"""
    return EventBus()


def publish_event(event_type: EventType, source: str, data: Dict[str, Any] = None):
    """イベントを発行する便利関数"""
    event_bus = get_event_bus()
    event_bus.publish_immediate(event_type, source, data)


def subscribe_to_event(event_type: EventType, handler: EventHandler):
    """イベントを購読する便利関数"""
    event_bus = get_event_bus()
    event_bus.subscribe(event_type, handler)


def subscribe_function(event_type: EventType, handler_func: Callable[[GameEvent], bool]):
    """関数をイベントハンドラーとして登録する便利関数"""
    event_bus = get_event_bus()
    function_handler = FunctionEventHandler(handler_func, [event_type])
    event_bus.subscribe(event_type, function_handler)
    return function_handler


# === 標準的なイベントハンドラー例 ===

class LoggingEventHandler(EventHandler):
    """ログ出力用イベントハンドラー"""
    
    def __init__(self, log_level: str = "info"):
        self.log_level = log_level
    
    def handle_event(self, event: GameEvent) -> bool:
        message = f"Event: {event.event_type.value} from {event.source}"
        if event.data:
            message += f" - {event.data}"
        
        if self.log_level == "debug":
            logger.debug(message)
        else:
            logger.info(message)
        
        return False  # 他のハンドラーにも処理を委ねる
    
    def get_handled_event_types(self) -> List[EventType]:
        return list(EventType)  # 全イベントタイプをログ出力


class StatisticsEventHandler(EventHandler):
    """統計情報収集用イベントハンドラー"""
    
    def __init__(self):
        self.event_counts: Dict[EventType, int] = {}
    
    def handle_event(self, event: GameEvent) -> bool:
        self.event_counts[event.event_type] = self.event_counts.get(event.event_type, 0) + 1
        return False
    
    def get_handled_event_types(self) -> List[EventType]:
        return list(EventType)
    
    def get_statistics(self) -> Dict[str, int]:
        """統計情報を取得"""
        return {event_type.value: count for event_type, count in self.event_counts.items()}
    
    def reset_statistics(self):
        """統計情報をリセット"""
        self.event_counts.clear()