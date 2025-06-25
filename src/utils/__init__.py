"""ユーティリティモジュール

共通定数、ログ機能、ヘルパー関数を提供
"""

from .constants import *
from .logger import setup_logger, create_custom_logger, logger
from .helpers import (
    clamp, percentage_to_decimal, decimal_to_percentage,
    roll_dice, roll_percentage, chance_check, weighted_choice,
    interpolate, distance_2d, safe_divide, round_to_precision,
    format_number_with_commas, join_with_separator, truncate_string,
    safe_get_dict_value, ensure_directory_exists, backup_file,
    validate_range, create_lookup_function, batch_process, retry_operation
)

# デフォルトエクスポート
__all__ = [
    # 定数
    "GAME_TITLE", "WINDOW_WIDTH", "WINDOW_HEIGHT", "FPS",
    "MAX_PARTY_SIZE", "FRONT_ROW_SIZE", "BACK_ROW_SIZE",
    "MAX_INVENTORY_SIZE", "MIN_DUNGEON_FLOORS", "MAX_DUNGEON_FLOORS",
    "ELEMENT_TYPES", "ELEMENT_DAMAGE_MULTIPLIERS",
    "MAX_CHARACTER_LEVEL", "MIN_CHARACTER_LEVEL", "BASE_HP", "BASE_MP",
    "RACES", "CLASSES", "BASIC_CLASSES", "ELITE_CLASSES",
    "UI_SCALE", "MENU_TRANSITION_TIME",
    "CONFIG_DIR", "SAVE_DIR", "ASSET_DIR", "LOG_DIR",
    
    # ロガー関数
    "setup_logger", "create_custom_logger", "logger",
    
    # ヘルパー関数
    "clamp", "percentage_to_decimal", "decimal_to_percentage",
    "roll_dice", "roll_percentage", "chance_check", "weighted_choice",
    "interpolate", "distance_2d", "safe_divide", "round_to_precision",
    "format_number_with_commas", "join_with_separator", "truncate_string",
    "safe_get_dict_value", "ensure_directory_exists", "backup_file",
    "validate_range", "create_lookup_function", "batch_process", "retry_operation"
]

# モジュール情報
__version__ = "1.0.0"
__author__ = "Dungeon RPG Team"