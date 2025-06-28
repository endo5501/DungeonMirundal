"""
List関連の型定義

ListWindow用の型定義専用モジュール
"""

import pygame_gui
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass
from enum import Enum


class SelectionMode(Enum):
    """選択モード"""
    SINGLE = "single"
    MULTIPLE = "multiple"
    NONE = "none"


class SortOrder(Enum):
    """ソート順"""
    ASCENDING = "asc"
    DESCENDING = "desc"


@dataclass
class ListColumn:
    """リストカラムの情報"""
    column_id: str
    label: str
    width: int
    sortable: bool = True
    resizable: bool = True
    visible: bool = True
    align: str = "left"  # left, center, right
    ui_element: Optional[pygame_gui.core.UIElement] = None


@dataclass 
class ListItem:
    """リストアイテムの情報"""
    item_id: str
    data: Dict[str, Any]
    selected: bool = False
    visible: bool = True
    metadata: Optional[Dict[str, Any]] = None
    ui_element: Optional[pygame_gui.core.UIElement] = None


@dataclass
class ListSortState:
    """リストソート状態"""
    column_id: Optional[str] = None
    order: SortOrder = SortOrder.ASCENDING
    
    
@dataclass
class ListFilterState:
    """リストフィルタ状態"""
    search_text: str = ""
    column_filters: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.column_filters is None:
            self.column_filters = {}