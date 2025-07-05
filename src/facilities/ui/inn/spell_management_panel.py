"""魔法管理パネル"""

import pygame
import pygame_gui
from typing import Dict, Any, Optional, List
import logging
from ..service_panel import ServicePanel

logger = logging.getLogger(__name__)


class SpellManagementPanel(ServicePanel):
    """魔法管理パネル
    
    魔法の装備・解除を管理する。
    """
    
    def __init__(self, rect: pygame.Rect, parent: pygame_gui.UIPanel,
                 controller, ui_manager: pygame_gui.UIManager):
        """初期化"""
        super().__init__(rect, parent, controller, "spell_management", ui_manager)
        
        # UI要素
        self.back_button: Optional[pygame_gui.elements.UIButton] = None
        self.info_label: Optional[pygame_gui.elements.UILabel] = None
        
        logger.info("SpellManagementPanel initialized")
    
    def _create_ui(self) -> None:
        """UI要素を作成"""
        # 戻るボタン
        back_rect = pygame.Rect(10, 10, 80, 35)
        self.back_button = self._create_button(
            "← 戻る",
            back_rect,
            container=self.container,
            object_id="#back_button"
        )
        
        # タイトル
        title_rect = pygame.Rect(100, 10, self.rect.width - 200, 35)
        title_label = pygame_gui.elements.UILabel(
            relative_rect=title_rect,
            text="魔法管理",
            manager=self.ui_manager,
            container=self.container
        )
        self.ui_elements.append(title_label)
        
        # 実装予定の説明
        info_rect = pygame.Rect(50, 100, self.rect.width - 100, 200)
        self.info_label = pygame_gui.elements.UILabel(
            relative_rect=info_rect,
            text="魔法管理機能は実装予定です。\n\nここでは以下の機能を提供予定:\n・習得済み魔法の一覧表示\n・魔法スロットへの装備\n・魔法の詳細情報表示\n・キャラクター別の魔法管理",
            manager=self.ui_manager,
            container=self.container
        )
        self.ui_elements.append(self.info_label)
    
    def handle_button_click(self, button: pygame_gui.elements.UIButton) -> bool:
        """ボタンクリックを処理"""
        if button == self.back_button:
            if hasattr(self.parent, 'handle_back_action'):
                self.parent.handle_back_action()
            return True
        
        return False