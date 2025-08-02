"""冒険準備パネル"""

import pygame
import pygame_gui
from typing import Dict, Any, Optional, List, cast
import logging
from ..service_panel import ServicePanel
from ...core.service_result import ServiceResult

logger = logging.getLogger(__name__)


class AdventurePrepPanel(ServicePanel):
    """冒険準備パネル
    
    アイテム管理、魔法管理、装備管理のサブサービスへのナビゲーションを提供。
    """
    
    def __init__(self, rect: pygame.Rect, parent: pygame_gui.elements.UIPanel,
                 controller, ui_manager: pygame_gui.UIManager):
        """初期化"""
        super().__init__(rect, parent, controller, "adventure_prep", ui_manager)
        
        # UI要素
        self.sub_service_buttons: Dict[str, pygame_gui.elements.UIButton] = {}
        self.info_box: Optional[pygame_gui.elements.UITextBox] = None
        self.active_sub_panel: Optional[ServicePanel] = None
        self.sub_panels: Dict[str, ServicePanel] = {}
        
        logger.info("AdventurePrepPanel initialized")
    
    def _create_ui(self) -> None:
        """UI要素を作成"""
        self._create_header()
        self._create_sub_service_buttons()
        self._create_info_display()
    
    def _create_header(self) -> None:
        """ヘッダーを作成"""
        # タイトル
        title_rect = pygame.Rect(10, 10, self.rect.width - 20, 40)
        if self.ui_element_manager and not self.ui_element_manager.is_destroyed:
            title_label = self.ui_element_manager.create_label(
                "title_label", "冒険準備", title_rect
            )
        else:
            # フォールバック
            title_label = pygame_gui.elements.UILabel(
                relative_rect=title_rect,
                text="冒険準備",
                manager=self.ui_manager,
                container=self.container
            )
            self.ui_elements.append(title_label)
    
    def _create_info_display(self) -> None:
        """情報表示エリアを作成"""
        # 情報表示ボックス
        info_rect = pygame.Rect(10, 250, self.rect.width - 20, 100)
        if self.ui_element_manager and not self.ui_element_manager.is_destroyed:
            self.info_box = self.ui_element_manager.create_text_box(
                "info_box", self._get_party_status_text(), info_rect
            )
        else:
            # フォールバック
            self.info_box = pygame_gui.elements.UITextBox(
                html_text=self._get_party_status_text(),
                relative_rect=info_rect,
                manager=self.ui_manager,
                container=self.container
            )
            self.ui_elements.append(self.info_box)
    
    def _create_sub_service_buttons(self) -> None:
        """サブサービスボタンを作成"""
        # サービス定義
        sub_services = [
            {
                "id": "item_management",
                "label": "アイテム管理",
                "description": "アイテムの整理・配分・使用を行います",
                "icon": "📦"
            },
            {
                "id": "spell_management",
                "label": "魔法管理",
                "description": "魔法の装備・解除を管理します",
                "icon": "✨"
            },
            {
                "id": "equipment_management",
                "label": "装備管理",
                "description": "武器・防具の装備を変更します",
                "icon": "⚔️"
            }
        ]
        
        # ボタンレイアウト
        button_width = 250
        button_height = 120
        spacing = 20
        start_x = (self.rect.width - (len(sub_services) * button_width + (len(sub_services) - 1) * spacing)) // 2
        y_position = 80
        
        for i, service in enumerate(sub_services):
            x_position = start_x + i * (button_width + spacing)
            button_rect = pygame.Rect(x_position, y_position, button_width, button_height)
            
            # ボタンを作成
            button_text = f"{service['icon']}\n{service['label']}\n\n{service['description']}"
            
            if self.ui_element_manager and not self.ui_element_manager.is_destroyed:
                button = self.ui_element_manager.create_button(
                    f"sub_service_{service['id']}", button_text, button_rect
                )
            else:
                # フォールバック
                button = pygame_gui.elements.UIButton(
                    relative_rect=button_rect,
                    text=button_text,
                    manager=self.ui_manager,
                    container=self.container,
                    object_id=f"#sub_service_{service['id']}"
                )
                self.ui_elements.append(button)
            
            self.sub_service_buttons[service['id']] = button
    
    def _get_party_status_text(self) -> str:
        """パーティステータステキストを取得"""
        if not self.controller or not self.controller.service.party:
            return "<b>パーティ情報</b><br>パーティが編成されていません"
        
        party = self.controller.service.party
        
        # パーティメンバーの状態を集計
        total_members = len(party.members)
        active_members = len([m for m in party.members if m.is_alive()])
        
        # アイテム数を集計
        total_items = 0
        for member in party.members:
            if hasattr(member, 'get_inventory'):
                inventory = member.get_inventory()
                if inventory:
                    total_items += len(inventory.get_all_items())
        
        status_text = f"<b>パーティ情報</b><br>"
        status_text += f"パーティ名: {party.name}<br>"
        status_text += f"メンバー: {active_members}/{total_members}人<br>"
        status_text += f"所持アイテム: {total_items}個<br>"
        status_text += f"所持金: {party.gold} G"
        
        return status_text
    
    def handle_button_click(self, button: pygame_gui.elements.UIButton) -> bool:
        """ボタンクリックを処理"""
        # サブサービスボタンのチェック
        for service_id, service_button in self.sub_service_buttons.items():
            if button == service_button:
                self._open_sub_service(service_id)
                return True
        
        return False
    
    def _open_sub_service(self, service_id: str) -> None:
        """サブサービスを開く"""
        # 現在のサブパネルを隠す
        if self.active_sub_panel:
            self.active_sub_panel.hide()
        
        # サブパネルが未作成なら作成
        if service_id not in self.sub_panels:
            panel = self._create_sub_panel(service_id)
            if panel:
                self.sub_panels[service_id] = panel
        
        # サブパネルを表示
        if service_id in self.sub_panels:
            self.active_sub_panel = self.sub_panels[service_id]
            self.active_sub_panel.show()
            
            # メインボタンを隠す
            for button in self.sub_service_buttons.values():
                button.hide()
            if self.info_box:
                self.info_box.hide()
    
    def _create_sub_panel(self, service_id: str) -> Optional[ServicePanel]:
        """サブパネルを作成"""
        panel_rect = pygame.Rect(0, 0, self.rect.width, self.rect.height)
        
        if service_id == "item_management":
            from .item_management_panel import ItemManagementPanel
            return ItemManagementPanel(panel_rect, cast(pygame_gui.elements.UIPanel, self.container), self.controller, self.ui_manager)
        elif service_id == "spell_management":
            from .spell_management_panel import SpellManagementPanel
            return SpellManagementPanel(panel_rect, cast(pygame_gui.elements.UIPanel, self.container), self.controller, self.ui_manager)
        elif service_id == "equipment_management":
            from .equipment_management_panel import EquipmentManagementPanel
            return EquipmentManagementPanel(panel_rect, cast(pygame_gui.elements.UIPanel, self.container), self.controller, self.ui_manager)
        
        return None
    
    def show(self) -> None:
        """パネルを表示"""
        super().show()
        
        # サブパネルが表示中でなければメインUIを表示
        if not self.active_sub_panel:
            for button in self.sub_service_buttons.values():
                button.show()
            if self.info_box:
                self.info_box.show()
    
    def hide(self) -> None:
        """パネルを非表示"""
        super().hide()
        
        # すべてのサブパネルも非表示
        for panel in self.sub_panels.values():
            panel.hide()
        
        self.active_sub_panel = None
    
    def refresh(self) -> None:
        """パネルをリフレッシュ"""
        # パーティステータスを更新
        if self.info_box:
            self.info_box.html_text = self._get_party_status_text()
            self.info_box.rebuild()
        
        # アクティブなサブパネルをリフレッシュ
        if self.active_sub_panel:
            self.active_sub_panel.refresh()
    
    def handle_back_action(self) -> bool:
        """戻るアクションを処理"""
        # サブパネルが表示中なら閉じる
        if self.active_sub_panel:
            self.active_sub_panel.hide()
            self.active_sub_panel = None
            
            # メインUIを再表示
            for button in self.sub_service_buttons.values():
                button.show()
            if self.info_box:
                self.info_box.show()
            
            return True
        
        return False