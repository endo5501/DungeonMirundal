"""装備管理パネル"""

import pygame
import pygame_gui
from typing import Dict, Any, Optional, List
import logging
from ..service_panel import ServicePanel

logger = logging.getLogger(__name__)


class EquipmentManagementPanel(ServicePanel):
    """装備管理パネル
    
    武器・防具の装備変更を管理する。
    """
    
    def __init__(self, rect: pygame.Rect, parent: pygame_gui.elements.UIPanel,
                 controller, ui_manager: pygame_gui.UIManager):
        """初期化"""
        super().__init__(rect, parent, controller, "equipment_management", ui_manager)
        
        # UI要素
        self.back_button: Optional[pygame_gui.elements.UIButton] = None
        self.info_label: Optional[pygame_gui.elements.UILabel] = None
        
        logger.info("EquipmentManagementPanel initialized")
    
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
            text="装備管理",
            manager=self.ui_manager,
            container=self.container
        )
        self.ui_elements.append(title_label)
        
        # 実装予定の説明
        info_rect = pygame.Rect(50, 100, self.rect.width - 100, 200)
        self.info_label = pygame_gui.elements.UILabel(
            relative_rect=info_rect,
            text="装備管理機能は実装予定です。\n\nここでは以下の機能を提供予定:\n・現在の装備状況表示\n・武器・防具の変更\n・装備による能力値変化の表示\n・装備の最適化機能",
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