"""
MenuButton クラス

メニューボタンの情報を保持するデータクラス
"""

import pygame_gui
from typing import Dict, Any, Optional
from dataclasses import dataclass


@dataclass
class MenuButton:
    """メニューボタンの情報"""
    id: str
    text: str
    action: str
    ui_element: Optional[pygame_gui.elements.UIButton] = None
    style: Optional[Dict[str, Any]] = None