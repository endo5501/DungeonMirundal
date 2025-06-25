"""ヘルパー関数とユーティリティ

汎用的な処理を提供するヘルパー関数群
"""

from typing import Any, Dict, List, Optional, Union, Callable
import random
import math
from pathlib import Path

# 数値関連定数
PERCENTAGE_MAX = 100
PERCENTAGE_MIN = 0
DICE_FACES_STANDARD = 6
PROBABILITY_CERTAIN = 1.0
PROBABILITY_IMPOSSIBLE = 0.0
ROUNDING_PRECISION = 2

# 文字列関連定数
EMPTY_STRING = ""
DEFAULT_SEPARATOR = ", "
NEWLINE_SEPARATOR = "\\n"
SPACE_CHAR = " "

# ファイル関連定数
DEFAULT_FILE_ENCODING = "utf-8"
BACKUP_SUFFIX = ".bak"


def clamp(value: Union[int, float], min_val: Union[int, float], max_val: Union[int, float]) -> Union[int, float]:
    """値を指定範囲内にクランプ"""
    return max(min_val, min(max_val, value))


def percentage_to_decimal(percentage: Union[int, float]) -> float:
    """パーセンテージを小数に変換"""
    return clamp(percentage, PERCENTAGE_MIN, PERCENTAGE_MAX) / PERCENTAGE_MAX


def decimal_to_percentage(decimal: float) -> float:
    """小数をパーセンテージに変換"""
    return clamp(decimal * PERCENTAGE_MAX, PERCENTAGE_MIN, PERCENTAGE_MAX)


def roll_dice(faces: int = DICE_FACES_STANDARD, count: int = 1) -> int:
    """ダイスロール"""
    if faces <= 0 or count <= 0:
        return 0
    return sum(random.randint(1, faces) for _ in range(count))


def roll_percentage() -> int:
    """パーセンテージダイス（1-100）"""
    return random.randint(1, PERCENTAGE_MAX)


def chance_check(probability: float) -> bool:
    """確率チェック（0.0-1.0）"""
    if probability <= PROBABILITY_IMPOSSIBLE:
        return False
    if probability >= PROBABILITY_CERTAIN:
        return True
    return random.random() < probability


def weighted_choice(choices: Dict[Any, float]) -> Any:
    """重み付き選択"""
    if not choices:
        return None
    
    total_weight = sum(choices.values())
    if total_weight <= 0:
        return random.choice(list(choices.keys()))
    
    rand_val = random.uniform(0, total_weight)
    current_weight = 0
    
    for choice, weight in choices.items():
        current_weight += weight
        if rand_val <= current_weight:
            return choice
    
    return list(choices.keys())[-1]


def interpolate(start: float, end: float, factor: float) -> float:
    """線形補間"""
    factor = clamp(factor, 0.0, 1.0)
    return start + (end - start) * factor


def distance_2d(x1: float, y1: float, x2: float, y2: float) -> float:
    """2D距離計算"""
    return math.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)


def safe_divide(numerator: Union[int, float], denominator: Union[int, float], default: Union[int, float] = 0) -> Union[int, float]:
    """安全な除算（ゼロ除算回避）"""
    if denominator == 0:
        return default
    return numerator / denominator


def round_to_precision(value: float, precision: int = ROUNDING_PRECISION) -> float:
    """指定精度での四捨五入"""
    return round(value, precision)


def format_number_with_commas(number: Union[int, float]) -> str:
    """数値をカンマ区切りでフォーマット"""
    return f"{number:,}"


def join_with_separator(items: List[str], separator: str = DEFAULT_SEPARATOR) -> str:
    """リストを指定区切り文字で結合"""
    return separator.join(str(item) for item in items if item)


def truncate_string(text: str, max_length: int, suffix: str = "...") -> str:
    """文字列を指定長で切り詰め"""
    if len(text) <= max_length:
        return text
    return text[:max_length - len(suffix)] + suffix


def safe_get_dict_value(dictionary: Dict[str, Any], key: str, default: Any = None) -> Any:
    """辞書から安全に値を取得"""
    return dictionary.get(key, default)


def ensure_directory_exists(directory: Union[str, Path]) -> Path:
    """ディレクトリの存在を確保"""
    path = Path(directory)
    path.mkdir(parents=True, exist_ok=True)
    return path


def backup_file(file_path: Union[str, Path], backup_suffix: str = BACKUP_SUFFIX) -> Optional[Path]:
    """ファイルのバックアップを作成"""
    source = Path(file_path)
    if not source.exists():
        return None
    
    backup_path = source.with_suffix(source.suffix + backup_suffix)
    try:
        import shutil
        shutil.copy2(source, backup_path)
        return backup_path
    except Exception:
        return None


def validate_range(value: Union[int, float], min_val: Union[int, float], max_val: Union[int, float]) -> bool:
    """値が指定範囲内かどうかチェック"""
    return min_val <= value <= max_val


def create_lookup_function(mapping: Dict[Any, Any], default: Any = None) -> Callable[[Any], Any]:
    """マッピング辞書からルックアップ関数を作成"""
    def lookup(key: Any) -> Any:
        return mapping.get(key, default)
    return lookup


def batch_process(items: List[Any], processor: Callable[[Any], Any], batch_size: int = 100) -> List[Any]:
    """アイテムをバッチ処理"""
    results = []
    for i in range(0, len(items), batch_size):
        batch = items[i:i + batch_size]
        batch_results = [processor(item) for item in batch]
        results.extend(batch_results)
    return results


def retry_operation(operation: Callable[[], Any], max_retries: int = 3, delay: float = 1.0) -> Any:
    """操作をリトライ"""
    import time
    
    last_exception = None
    for attempt in range(max_retries + 1):
        try:
            return operation()
        except Exception as e:
            last_exception = e
            if attempt < max_retries:
                time.sleep(delay)
                delay *= 2  # 指数バックオフ
            else:
                break
    
    if last_exception:
        raise last_exception