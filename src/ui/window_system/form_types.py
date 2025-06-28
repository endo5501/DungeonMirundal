"""
Form関連の型定義

循環インポートを避けるための型定義専用モジュール
"""

import pygame_gui
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from enum import Enum


class FormFieldType(Enum):
    """フォームフィールドタイプ"""
    TEXT = "text"
    NUMBER = "number"
    DROPDOWN = "dropdown"
    CHECKBOX = "checkbox"


@dataclass
class FormValidationResult:
    """フォーム検証結果"""
    is_valid: bool
    errors: Dict[str, str]


@dataclass 
class FormField:
    """フォームフィールドの情報"""
    field_id: str
    label: str
    field_type: FormFieldType
    required: bool = False
    ui_element: Optional[pygame_gui.core.UIElement] = None
    validation_rules: Optional[Dict[str, Any]] = None
    options: Optional[List[str]] = None  # ドロップダウン用
    value: Optional[Any] = None