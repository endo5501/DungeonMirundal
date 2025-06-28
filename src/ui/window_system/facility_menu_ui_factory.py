"""
FacilityMenuUIFactory クラス

施設メニューUI要素作成ファクトリー

Fowler式リファクタリング：Extract Class パターン
"""

import pygame
import pygame_gui
from typing import Dict, List, Any, Optional
from src.ui.window_system.facility_menu_types import (
    FacilityType, FacilityMenuItem, PartyInfo, MenuLayout
)
from src.utils.logger import logger


class FacilityMenuUIFactory:
    """
    施設メニューUI要素作成ファクトリークラス
    
    UI要素の作成、レイアウト、スタイリングを担当
    """
    
    def __init__(self, layout: MenuLayout):
        """
        UI ファクトリーを初期化
        
        Args:
            layout: メニューレイアウト設定
        """
        self.layout = layout
        logger.debug("FacilityMenuUIFactoryを初期化")
    
    def create_main_container(self, rect: pygame.Rect, ui_manager: pygame_gui.UIManager) -> pygame_gui.elements.UIPanel:
        """メインコンテナを作成"""
        container = pygame_gui.elements.UIPanel(
            relative_rect=rect,
            manager=ui_manager
        )
        
        logger.debug(f"メインコンテナ作成: {rect}")
        return container
    
    def create_facility_title(self, facility_type: FacilityType, facility_name: str,
                            container: pygame_gui.elements.UIPanel, 
                            ui_manager: pygame_gui.UIManager) -> pygame_gui.elements.UILabel:
        """施設タイトルを作成"""
        title_text = facility_name or facility_type.display_name
        
        title_rect = pygame.Rect(
            self.layout.padding,
            self.layout.padding,
            self.layout.window_width - (self.layout.padding * 2),
            self.layout.title_height
        )
        
        title_label = pygame_gui.elements.UILabel(
            relative_rect=title_rect,
            text=title_text,
            manager=ui_manager,
            container=container
        )
        
        logger.debug(f"施設タイトル作成: {title_text}")
        return title_label
    
    def create_party_info_panel(self, container: pygame_gui.elements.UIPanel,
                              ui_manager: pygame_gui.UIManager,
                              show_party_info: bool) -> Optional[pygame_gui.elements.UIPanel]:
        """パーティ情報パネルを作成"""
        if not show_party_info:
            return None
        
        y_offset = self.layout.title_height + self.layout.padding * 2
        
        party_rect = pygame.Rect(
            self.layout.padding,
            y_offset,
            self.layout.window_width - (self.layout.padding * 2),
            self.layout.party_info_height
        )
        
        party_panel = pygame_gui.elements.UIPanel(
            relative_rect=party_rect,
            manager=ui_manager,
            container=container
        )
        
        logger.debug("パーティ情報パネル作成")
        return party_panel
    
    def create_party_info_display(self, party_info: PartyInfo, panel: pygame_gui.elements.UIPanel,
                                ui_manager: pygame_gui.UIManager, show_gold: bool) -> pygame_gui.elements.UITextBox:
        """パーティ情報表示を作成"""
        info_lines = []
        info_lines.append(f"パーティメンバー: {party_info.member_count}人")
        
        if show_gold:
            info_lines.append(f"所持金: {party_info.gold}G")
        
        info_lines.append(f"HP: {party_info.current_hp}/{party_info.max_hp}")
        
        info_text = "\\n".join(info_lines)
        
        # 情報ラベルを作成
        info_rect = pygame.Rect(10, 10, 
                               panel.relative_rect.width - 20,
                               panel.relative_rect.height - 20)
        
        party_info_display = pygame_gui.elements.UITextBox(
            relative_rect=info_rect,
            html_text=info_text.replace('\\n', '<br>'),
            manager=ui_manager,
            container=panel
        )
        
        logger.debug("パーティ情報表示作成")
        return party_info_display
    
    def create_menu_buttons(self, menu_items: List[FacilityMenuItem],
                          container: pygame_gui.elements.UIPanel,
                          ui_manager: pygame_gui.UIManager,
                          show_party_info: bool) -> List[pygame_gui.elements.UIButton]:
        """メニューボタンを作成"""
        buttons = []
        
        # メニューエリアの位置を計算
        item_positions = self._calculate_menu_item_positions(len(menu_items), show_party_info)
        
        for i, (menu_item, position) in enumerate(zip(menu_items, item_positions)):
            button_rect = pygame.Rect(
                position['x'], position['y'],
                position['width'], position['height']
            )
            
            button = pygame_gui.elements.UIButton(
                relative_rect=button_rect,
                text=menu_item.label,
                manager=ui_manager,
                container=container
            )
            
            buttons.append(button)
        
        logger.debug(f"メニューボタン作成: {len(buttons)}個")
        return buttons
    
    def apply_button_highlighting(self, buttons: List[pygame_gui.elements.UIButton],
                                selected_index: int) -> None:
        """ボタンのハイライト表示を適用"""
        for i, button in enumerate(buttons):
            text = button.text
            
            if i == selected_index:
                if not text.startswith(">>> "):
                    button.set_text(f">>> {text}")
            else:
                if text.startswith(">>> "):
                    button.set_text(text[4:])
        
        logger.debug(f"ボタンハイライト適用: インデックス {selected_index}")
    
    def apply_button_availability(self, buttons: List[pygame_gui.elements.UIButton],
                                menu_items: List[FacilityMenuItem], party: Any) -> None:
        """ボタンの利用可能性を適用"""
        for button, menu_item in zip(buttons, menu_items):
            is_available = menu_item.is_available(party)
            if is_available:
                button.enable()
            else:
                button.disable()
        
        logger.debug("ボタン利用可能性適用")
    
    def calculate_window_layout(self, menu_item_count: int, show_party_info: bool) -> pygame.Rect:
        """ウィンドウレイアウトを計算"""
        total_menu_height = menu_item_count * (self.layout.menu_item_height + self.layout.menu_spacing)
        
        # 必要な高さを計算
        required_height = (
            self.layout.title_height + 
            (self.layout.party_info_height if show_party_info else 0) +
            total_menu_height + 
            self.layout.padding * 4
        )
        
        # ウィンドウサイズを調整
        window_height = max(self.layout.window_height, required_height)
        
        # 画面中央に配置
        screen_width = 1024
        screen_height = 768
        window_x = (screen_width - self.layout.window_width) // 2
        window_y = (screen_height - window_height) // 2
        
        rect = pygame.Rect(window_x, window_y, self.layout.window_width, window_height)
        logger.debug(f"ウィンドウレイアウト計算: {rect}")
        
        return rect
    
    def _calculate_menu_item_positions(self, item_count: int, show_party_info: bool) -> List[Dict[str, int]]:
        """メニュー項目の位置を計算"""
        y_offset = self.layout.title_height + self.layout.padding
        if show_party_info:
            y_offset += self.layout.party_info_height + self.layout.padding
        
        positions = []
        
        for i in range(item_count):
            y = y_offset + i * (self.layout.menu_item_height + self.layout.menu_spacing)
            
            positions.append({
                'x': self.layout.padding,
                'y': y,
                'width': self.layout.window_width - (self.layout.padding * 2),
                'height': self.layout.menu_item_height
            })
        
        logger.debug(f"メニュー項目位置計算: {len(positions)}個")
        return positions
    
    def cleanup_ui_elements(self, ui_manager: pygame_gui.UIManager) -> None:
        """UI要素をクリーンアップ"""
        if ui_manager:
            for element in list(ui_manager.get_root_container().elements):
                element.kill()
        
        logger.debug("UI要素クリーンアップ完了")