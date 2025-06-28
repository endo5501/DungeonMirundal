"""
Settings関連の型定義

SettingsWindow用の型定義専用モジュール
"""

import pygame_gui
from typing import Dict, List, Any, Optional, Callable, Union
from dataclasses import dataclass
from enum import Enum


class SettingsCategory(Enum):
    """設定カテゴリ"""
    GAMEPLAY = "gameplay"
    CONTROLS = "controls"
    AUDIO = "audio"
    GRAPHICS = "graphics"
    ACCESSIBILITY = "accessibility"


class SettingsFieldType(Enum):
    """設定フィールドタイプ"""
    SLIDER = "slider"
    DROPDOWN = "dropdown"
    CHECKBOX = "checkbox"
    TEXT_INPUT = "text_input"
    BUTTON = "button"
    KEYBIND = "keybind"


@dataclass
class SettingsField:
    """設定フィールドの情報"""
    field_id: str
    label: str
    field_type: SettingsFieldType
    category: str
    default_value: Any = None
    current_value: Any = None
    min_value: Optional[Union[int, float]] = None
    max_value: Optional[Union[int, float]] = None
    options: Optional[List[str]] = None
    validation_func: Optional[Callable[[Any], bool]] = None
    ui_element: Optional[pygame_gui.core.UIElement] = None
    description: Optional[str] = None
    requires_restart: bool = False


@dataclass
class SettingsTab:
    """設定タブの情報"""
    tab_id: str
    label: str
    fields: List[SettingsField]
    is_active: bool = False
    ui_element: Optional[pygame_gui.core.UIElement] = None
    icon: Optional[str] = None


@dataclass
class SettingsValidationResult:
    """設定検証結果"""
    is_valid: bool
    errors: Dict[str, str]
    warnings: Dict[str, str] = None
    
    def __post_init__(self):
        if self.warnings is None:
            self.warnings = {}


@dataclass
class SettingsChangeEvent:
    """設定変更イベント"""
    field_id: str
    old_value: Any
    new_value: Any
    category: str
    requires_restart: bool = False