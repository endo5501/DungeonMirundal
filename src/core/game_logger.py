# game_logger.py ── ゲーム内部ログシステム（現在無効化）
# 二重ログ出力問題により一時的に無効化されています
GAME_LOGGER_ENABLED = False
import logging
import threading
from datetime import datetime
from collections import deque
from typing import Optional, List, Dict, Any
from enum import Enum

class LogLevel(str, Enum):
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"

class GameLogEntry:
    """ゲームログエントリー"""
    def __init__(self, level: str, message: str, category: str = "general", extra: Optional[Dict[str, Any]] = None):
        self.timestamp = datetime.now()
        self.level = level
        self.message = message
        self.category = category
        self.extra = extra or {}
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "timestamp": self.timestamp.isoformat(),
            "level": self.level,
            "category": self.category,
            "message": self.message,
            "extra": self.extra
        }

class GameLogger:
    """ゲーム専用のログ管理システム"""
    
    def __init__(self, max_entries: int = 10000, auto_register_handler: bool = False):
        self.max_entries = max_entries
        self.logs: deque[GameLogEntry] = deque(maxlen=max_entries)
        self.lock = threading.Lock()
        
        # カテゴリ別のログカウンター
        self.category_counts: Dict[str, int] = {}
        self.level_counts: Dict[str, int] = {
            "DEBUG": 0, "INFO": 0, "WARNING": 0, "ERROR": 0, "CRITICAL": 0
        }
        
        # Pythonの標準ログハンドラーとして登録（デフォルトは無効）
        if auto_register_handler:
            self.handler = GameLogHandler(self)
        else:
            self.handler = None
        
    def add_log(self, level: str, message: str, category: str = "general", extra: Optional[Dict[str, Any]] = None):
        """ログエントリーを追加"""
        with self.lock:
            entry = GameLogEntry(level, message, category, extra)
            self.logs.append(entry)
            
            # カウンターを更新
            self.level_counts[level] = self.level_counts.get(level, 0) + 1
            self.category_counts[category] = self.category_counts.get(category, 0) + 1
    
    def get_logs(self, 
                 limit: Optional[int] = None, 
                 level: Optional[str] = None,
                 category: Optional[str] = None,
                 since: Optional[datetime] = None) -> List[Dict[str, Any]]:
        """フィルタリングされたログを取得"""
        with self.lock:
            filtered_logs = []
            
            for log in reversed(self.logs):  # 新しい順
                # フィルタリング
                if level and log.level != level:
                    continue
                if category and log.category != category:
                    continue
                if since and log.timestamp < since:
                    continue
                
                filtered_logs.append(log.to_dict())
                
                if limit and len(filtered_logs) >= limit:
                    break
            
            return filtered_logs
    
    def get_stats(self) -> Dict[str, Any]:
        """ログ統計を取得"""
        with self.lock:
            return {
                "total_logs": len(self.logs),
                "by_level": dict(self.level_counts),
                "by_category": dict(self.category_counts),
                "oldest_log": self.logs[0].timestamp.isoformat() if self.logs else None,
                "newest_log": self.logs[-1].timestamp.isoformat() if self.logs else None
            }
    
    def clear(self):
        """すべてのログをクリア"""
        with self.lock:
            self.logs.clear()
            self.category_counts.clear()
            self.level_counts = {
                "DEBUG": 0, "INFO": 0, "WARNING": 0, "ERROR": 0, "CRITICAL": 0
            }
    
    def search(self, query: str, limit: int = 100) -> List[Dict[str, Any]]:
        """メッセージ内のテキストを検索"""
        with self.lock:
            results = []
            query_lower = query.lower()
            
            for log in reversed(self.logs):
                if query_lower in log.message.lower():
                    results.append(log.to_dict())
                    if len(results) >= limit:
                        break
            
            return results

class GameLogHandler(logging.Handler):
    """Python logging と統合するためのハンドラー"""
    
    def __init__(self, game_logger: GameLogger):
        super().__init__()
        self.game_logger = game_logger
    
    def emit(self, record: logging.LogRecord):
        """ログレコードを処理"""
        try:
            # カテゴリを抽出（logger名から）
            category = record.name.split('.')[-1] if '.' in record.name else record.name
            
            # 追加情報を収集
            extra = {}
            if hasattr(record, 'game_state'):
                extra['game_state'] = record.game_state
            if hasattr(record, 'player_action'):
                extra['player_action'] = record.player_action
            if hasattr(record, 'error_code'):
                extra['error_code'] = record.error_code
            
            self.game_logger.add_log(
                level=record.levelname,
                message=self.format(record),
                category=category,
                extra=extra
            )
        except Exception:
            self.handleError(record)

class DummyGameLogger:
    """無効化時に使用するダミーロガー"""
    def add_log(self, *args, **kwargs):
        pass
    
    def get_logs(self, *args, **kwargs):
        return []
    
    def get_stats(self, *args, **kwargs):
        return {}
    
    def clear(self, *args, **kwargs):
        pass
    
    def search(self, *args, **kwargs):
        return []

# シングルトンインスタンス
_game_logger: Optional[GameLogger] = None

def get_game_logger() -> GameLogger:
    """ゲームログインスタンスを取得"""
    if not GAME_LOGGER_ENABLED:
        # 無効化されているため、何もしないダミーを返す
        return DummyGameLogger()
    
    global _game_logger
    if _game_logger is None:
        _game_logger = GameLogger(auto_register_handler=False)  # 明示的に無効化
    return _game_logger

def setup_game_logging(root_logger_name: str = "game", enable_standard_logging: bool = False):
    """ゲームログシステムをセットアップ"""
    if not GAME_LOGGER_ENABLED:
        return logging.getLogger(root_logger_name)
        
    game_logger = get_game_logger()
    
    # 標準ログシステムとの統合は無効にする（二重出力を防ぐ）
    if enable_standard_logging and game_logger.handler is not None:
        # ルートゲームロガーを設定
        logger = logging.getLogger(root_logger_name)
        logger.addHandler(game_logger.handler)
        logger.setLevel(logging.DEBUG)
        return logger
    else:
        # 標準ログシステムには追加しない
        logger = logging.getLogger(root_logger_name)
        return logger

# 便利な関数
def log_game_event(message: str, category: str = "event", **extra):
    """ゲームイベントをログ"""
    if not GAME_LOGGER_ENABLED:
        return
    get_game_logger().add_log("INFO", message, category, extra)

def log_player_action(action: str, details: Dict[str, Any]):
    """プレイヤーアクションをログ"""
    if not GAME_LOGGER_ENABLED:
        return
    get_game_logger().add_log(
        "INFO", 
        f"Player action: {action}", 
        "player", 
        {"action": action, "details": details}
    )

def log_battle_event(event: str, participants: List[str], result: Dict[str, Any]):
    """戦闘イベントをログ"""
    if not GAME_LOGGER_ENABLED:
        return
    get_game_logger().add_log(
        "INFO",
        f"Battle event: {event}",
        "battle",
        {"event": event, "participants": participants, "result": result}
    )

def log_error(error_msg: str, error_code: Optional[str] = None, **extra):
    """エラーをログ"""
    if not GAME_LOGGER_ENABLED:
        return
    extra_data = {"error_code": error_code} if error_code else {}
    extra_data.update(extra)
    get_game_logger().add_log("ERROR", error_msg, "error", extra_data)