import logging
import sys
import os
from pathlib import Path
from typing import Optional

# ログシステム定数
DEFAULT_LOGGER_NAME = "dungeon"
DEFAULT_LOG_LEVEL = logging.WARNING
DEFAULT_DEBUG_LEVEL = logging.DEBUG
DEFAULT_ENCODING = "utf-8"
LOG_DIR_NAME = "logs"
LOG_FILE_NAME = "game.log"

# ログフォーマット定数
LOG_FORMAT_STANDARD = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
LOG_DATE_FORMAT = '%Y-%m-%d %H:%M:%S'


def get_log_level_from_env() -> int:
    """環境変数からログレベルを取得"""
    env_level = os.getenv('DUNGEON_LOG_LEVEL', 'WARNING').upper()
    
    level_map = {
        'DEBUG': logging.DEBUG,
        'INFO': logging.INFO,
        'WARNING': logging.WARNING,
        'ERROR': logging.ERROR,
        'CRITICAL': logging.CRITICAL
    }
    
    return level_map.get(env_level, DEFAULT_LOG_LEVEL)


def setup_logger(name: str = DEFAULT_LOGGER_NAME, level: Optional[int] = None) -> logging.Logger:
    """ゲーム用ロガーの設定"""
    logger = logging.getLogger(name)
    
    if _logger_already_configured(logger):
        return logger
    
    # 重複ハンドラーを防ぐため、既存のハンドラーをクリア
    logger.handlers.clear()
    
    # ログレベルを決定（環境変数 > 引数 > デフォルト）
    if level is None:
        level = get_log_level_from_env()
    
    logger.setLevel(level)
    
    # ルートロガーへの伝播を無効化（重複出力防止）
    logger.propagate = False
    
    # フォーマッターの設定
    formatter = _create_log_formatter()
    
    # ハンドラーを追加
    _add_console_handler(logger, level, formatter)
    _add_file_handler(logger, formatter)
    
    return logger

def _logger_already_configured(logger: logging.Logger) -> bool:
    """ロガーが既に設定済みかチェック"""
    # ハンドラーが存在し、かつコンソールハンドラーとファイルハンドラーが両方存在する場合のみ設定済みとする
    if not logger.handlers:
        return False
    
    has_console_handler = any(isinstance(h, logging.StreamHandler) and not isinstance(h, logging.FileHandler) for h in logger.handlers)
    has_file_handler = any(isinstance(h, logging.FileHandler) for h in logger.handlers)
    
    return has_console_handler and has_file_handler

def _create_log_formatter() -> logging.Formatter:
    """ログフォーマッターを作成"""
    return logging.Formatter(
        LOG_FORMAT_STANDARD,
        datefmt=LOG_DATE_FORMAT
    )

def _add_console_handler(logger: logging.Logger, level: int, formatter: logging.Formatter) -> None:
    """コンソールハンドラーを追加"""
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

def _add_file_handler(logger: logging.Logger, formatter: logging.Formatter) -> None:
    """ファイルハンドラーを追加"""
    log_dir = _ensure_log_directory()
    file_handler = logging.FileHandler(
        log_dir / LOG_FILE_NAME, 
        encoding=DEFAULT_ENCODING
    )
    file_handler.setLevel(DEFAULT_DEBUG_LEVEL)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

def _ensure_log_directory() -> Path:
    """ログディレクトリを作成・取得"""
    log_dir = Path(LOG_DIR_NAME)
    log_dir.mkdir(exist_ok=True)
    return log_dir

def create_custom_logger(name: str, level: Optional[int] = None, log_file: Optional[str] = None) -> logging.Logger:
    """カスタムロガーを作成"""
    if level is None:
        level = DEFAULT_LOG_LEVEL
    
    logger = logging.getLogger(name)
    
    if _logger_already_configured(logger):
        return logger
    
    # 重複ハンドラーを防ぐため、既存のハンドラーをクリア
    logger.handlers.clear()
    
    logger.setLevel(level)
    
    # ルートロガーへの伝播を無効化（重複出力防止）
    logger.propagate = False
    
    formatter = _create_log_formatter()
    
    # コンソールハンドラー
    _add_console_handler(logger, level, formatter)
    
    # カスタムファイルハンドラー
    if log_file:
        _add_custom_file_handler(logger, formatter, log_file)
    else:
        _add_file_handler(logger, formatter)
    
    return logger

def _add_custom_file_handler(logger: logging.Logger, formatter: logging.Formatter, log_file: str) -> None:
    """カスタムファイルハンドラーを追加"""
    log_dir = _ensure_log_directory()
    file_handler = logging.FileHandler(
        log_dir / log_file,
        encoding=DEFAULT_ENCODING
    )
    file_handler.setLevel(DEFAULT_DEBUG_LEVEL)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)


# デフォルトロガー - 二重ログ出力防止のため無効化
# logger = setup_logger()

# 代わりに遅延初期化でシングルトンロガーを提供
_default_logger = None

def get_default_logger():
    """デフォルトロガーをシングルトンで取得"""
    global _default_logger
    if _default_logger is None:
        _default_logger = setup_logger()
    return _default_logger

# 後方互換性のため、logger属性も提供
logger = get_default_logger()