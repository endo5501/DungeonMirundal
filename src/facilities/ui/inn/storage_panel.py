"""アイテム保管パネル"""

import pygame
import pygame_gui
from typing import Dict, Any, Optional, List
import logging
from ..service_panel import ServicePanel
from ...core.service_result import ServiceResult

logger = logging.getLogger(__name__)


class StoragePanel(ServicePanel):
    """アイテム保管パネル
    
    宿屋の保管庫にアイテムを預け入れ・引き出しする機能を提供。
    """
    
    def __init__(self, rect: pygame.Rect, parent: pygame_gui.UIPanel,
                 controller, ui_manager: pygame_gui.UIManager):
        """初期化"""
        super().__init__(rect, parent, controller, "storage", ui_manager)
        
        # UI要素
        self.inventory_list: Optional[pygame_gui.elements.UISelectionList] = None
        self.storage_list: Optional[pygame_gui.elements.UISelectionList] = None
        self.deposit_button: Optional[pygame_gui.elements.UIButton] = None
        self.withdraw_button: Optional[pygame_gui.elements.UIButton] = None
        self.quantity_input: Optional[pygame_gui.elements.UITextEntryLine] = None
        self.info_box: Optional[pygame_gui.elements.UITextBox] = None
        
        # データ
        self.inventory_items: List[Dict[str, Any]] = []
        self.storage_items: List[Dict[str, Any]] = []
        self.selected_inventory_item: Optional[Dict[str, Any]] = None
        self.selected_storage_item: Optional[Dict[str, Any]] = None
        self.storage_capacity = 100
        
        logger.info("StoragePanel initialized")
    
    def _create_ui(self) -> None:
        """UI要素を作成"""
        # タイトル
        title_rect = pygame.Rect(10, 10, self.rect.width - 20, 40)
        title_label = pygame_gui.elements.UILabel(
            relative_rect=title_rect,
            text="アイテム保管庫",
            manager=self.ui_manager,
            container=self.container
        )
        self.ui_elements.append(title_label)
        
        # レイアウト定数
        list_width = (self.rect.width - 60) // 2
        list_height = 250
        
        # インベントリリスト（左側）
        inv_label = pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect(10, 60, list_width, 25),
            text="所持アイテム",
            manager=self.ui_manager,
            container=self.container
        )
        self.ui_elements.append(inv_label)
        
        inv_rect = pygame.Rect(10, 90, list_width, list_height)
        self.inventory_list = pygame_gui.elements.UISelectionList(
            relative_rect=inv_rect,
            item_list=[],
            manager=self.ui_manager,
            container=self.container,
            allow_multi_select=False
        )
        self.ui_elements.append(self.inventory_list)
        
        # 中央のボタンと入力欄
        center_x = self.rect.width // 2
        
        # 数量入力
        quantity_label = pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect(center_x - 50, 150, 100, 25),
            text="数量:",
            manager=self.ui_manager,
            container=self.container
        )
        self.ui_elements.append(quantity_label)
        
        quantity_rect = pygame.Rect(center_x - 50, 180, 100, 30)
        self.quantity_input = pygame_gui.elements.UITextEntryLine(
            relative_rect=quantity_rect,
            manager=self.ui_manager,
            container=self.container,
            initial_text="1"
        )
        self.ui_elements.append(self.quantity_input)
        
        # 預けるボタン
        deposit_rect = pygame.Rect(center_x - 50, 220, 100, 35)
        self.deposit_button = self._create_button(
            "預ける →",
            deposit_rect,
            container=self.container,
            object_id="#deposit_button"
        )
        
        # 引き出すボタン
        withdraw_rect = pygame.Rect(center_x - 50, 265, 100, 35)
        self.withdraw_button = self._create_button(
            "← 引き出す",
            withdraw_rect,
            container=self.container,
            object_id="#withdraw_button"
        )
        
        # 保管庫リスト（右側）
        storage_label = pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect(self.rect.width - list_width - 10, 60, list_width, 25),
            text="保管庫",
            manager=self.ui_manager,
            container=self.container
        )
        self.ui_elements.append(storage_label)
        
        storage_rect = pygame.Rect(
            self.rect.width - list_width - 10, 90,
            list_width, list_height
        )
        self.storage_list = pygame_gui.elements.UISelectionList(
            relative_rect=storage_rect,
            item_list=[],
            manager=self.ui_manager,
            container=self.container,
            allow_multi_select=False
        )
        self.ui_elements.append(self.storage_list)
        
        # 情報ボックス
        info_rect = pygame.Rect(10, 350, self.rect.width - 20, 40)
        self.info_box = pygame_gui.elements.UITextBox(
            html_text="",
            relative_rect=info_rect,
            manager=self.ui_manager,
            container=self.container
        )
        self.ui_elements.append(self.info_box)
        
        # 初期データを読み込み
        self._load_storage_data()
    
    def _load_storage_data(self) -> None:
        """保管庫データを読み込み"""
        # インベントリアイテムを取得
        result = self._execute_service_action("storage", {"action": "get_inventory"})
        if result.is_success() and result.data:
            self.inventory_items = result.data.get("items", [])
        else:
            # デモ用の仮データ
            self.inventory_items = [
                {"id": "item1", "name": "ポーション", "quantity": 5, "stackable": True},
                {"id": "item2", "name": "エーテル", "quantity": 3, "stackable": True},
                {"id": "item3", "name": "鉄の剣", "quantity": 1, "stackable": False}
            ]
        
        # 保管庫の内容を取得
        result = self._execute_service_action("storage", {})
        if result.is_success() and result.data:
            self.storage_items = result.data.get("items", [])
            self.storage_capacity = result.data.get("capacity", 100)
        else:
            # デモ用の仮データ
            self.storage_items = [
                {"id": "item4", "name": "ハイポーション", "quantity": 10, "stackable": True},
                {"id": "item5", "name": "魔法の杖", "quantity": 1, "stackable": False}
            ]
        
        self._update_lists()
        self._update_info()
        self._update_buttons()
    
    def _update_lists(self) -> None:
        """リストを更新"""
        # インベントリリスト
        if self.inventory_list:
            inv_items = []
            for item in self.inventory_items:
                if item["quantity"] > 1:
                    inv_items.append(f"{item['name']} x{item['quantity']}")
                else:
                    inv_items.append(item["name"])
            self.inventory_list.set_item_list(inv_items)
        
        # 保管庫リスト
        if self.storage_list:
            storage_items = []
            for item in self.storage_items:
                if item["quantity"] > 1:
                    storage_items.append(f"{item['name']} x{item['quantity']}")
                else:
                    storage_items.append(item["name"])
            self.storage_list.set_item_list(storage_items)
    
    def _update_info(self) -> None:
        """情報表示を更新"""
        if not self.info_box:
            return
        
        used_space = sum(item["quantity"] for item in self.storage_items)
        free_space = self.storage_capacity - used_space
        
        info_text = f"<b>保管庫容量:</b> {used_space}/{self.storage_capacity} "
        info_text += f"（空き: {free_space}）"
        
        if self.controller and self.controller.service.party:
            info_text += f"　<b>所持金:</b> {self.controller.service.party.gold} G"
        
        self.info_box.html_text = info_text
        self.info_box.rebuild()
    
    def _update_buttons(self) -> None:
        """ボタンの有効/無効を更新"""
        # 預けるボタン
        if self.deposit_button:
            can_deposit = (self.selected_inventory_item is not None and 
                          self._get_free_space() > 0)
            if can_deposit:
                self.deposit_button.enable()
            else:
                self.deposit_button.disable()
        
        # 引き出すボタン
        if self.withdraw_button:
            can_withdraw = self.selected_storage_item is not None
            if can_withdraw:
                self.withdraw_button.enable()
            else:
                self.withdraw_button.disable()
    
    def _get_free_space(self) -> int:
        """保管庫の空き容量を取得"""
        used_space = sum(item["quantity"] for item in self.storage_items)
        return self.storage_capacity - used_space
    
    def _get_quantity(self) -> int:
        """入力された数量を取得"""
        if not self.quantity_input:
            return 1
        
        try:
            quantity = int(self.quantity_input.get_text())
            return max(1, quantity)
        except ValueError:
            return 1
    
    def _deposit_item(self) -> None:
        """アイテムを預ける"""
        if not self.selected_inventory_item:
            return
        
        quantity = self._get_quantity()
        max_quantity = self.selected_inventory_item["quantity"]
        quantity = min(quantity, max_quantity)
        
        # 空き容量チェック
        free_space = self._get_free_space()
        if quantity > free_space:
            self._show_message(f"保管庫の空き容量が不足しています（空き: {free_space}）", "warning")
            return
        
        params = {
            "action": "deposit",
            "item_id": self.selected_inventory_item["id"],
            "quantity": quantity
        }
        
        result = self._execute_service_action("storage", params)
        
        if result.is_success():
            self._show_message(result.message, "info")
            # データを再読み込み
            self._load_storage_data()
            # 選択をクリア
            self.selected_inventory_item = None
            self.selected_storage_item = None
        else:
            self._show_message(result.message, "error")
    
    def _withdraw_item(self) -> None:
        """アイテムを引き出す"""
        if not self.selected_storage_item:
            return
        
        quantity = self._get_quantity()
        max_quantity = self.selected_storage_item["quantity"]
        quantity = min(quantity, max_quantity)
        
        params = {
            "action": "withdraw",
            "item_id": self.selected_storage_item["id"],
            "quantity": quantity
        }
        
        result = self._execute_service_action("storage", params)
        
        if result.is_success():
            self._show_message(result.message, "info")
            # データを再読み込み
            self._load_storage_data()
            # 選択をクリア
            self.selected_inventory_item = None
            self.selected_storage_item = None
        else:
            self._show_message(result.message, "error")
    
    def handle_button_click(self, button: pygame_gui.elements.UIButton) -> bool:
        """ボタンクリックを処理"""
        if button == self.deposit_button:
            self._deposit_item()
            return True
        elif button == self.withdraw_button:
            self._withdraw_item()
            return True
        
        return False
    
    def handle_selection_list_changed(self, event: pygame.event.Event) -> bool:
        """選択リスト変更イベントを処理"""
        if event.type == pygame_gui.UI_SELECTION_LIST_NEW_SELECTION:
            if event.ui_element == self.inventory_list:
                # インベントリアイテムが選択された
                selection = self.inventory_list.get_single_selection()
                if selection is not None:
                    index = self.inventory_list.item_list.index(selection)
                    if 0 <= index < len(self.inventory_items):
                        self.selected_inventory_item = self.inventory_items[index]
                        # 保管庫の選択をクリア
                        self.selected_storage_item = None
                        if self.storage_list:
                            self.storage_list.set_selected_index(None)
                    else:
                        self.selected_inventory_item = None
                else:
                    self.selected_inventory_item = None
                
                # 数量を設定
                if self.selected_inventory_item and self.quantity_input:
                    max_qty = min(self.selected_inventory_item["quantity"], self._get_free_space())
                    self.quantity_input.set_text(str(max_qty))
                
                self._update_buttons()
                return True
                
            elif event.ui_element == self.storage_list:
                # 保管庫アイテムが選択された
                selection = self.storage_list.get_single_selection()
                if selection is not None:
                    index = self.storage_list.item_list.index(selection)
                    if 0 <= index < len(self.storage_items):
                        self.selected_storage_item = self.storage_items[index]
                        # インベントリの選択をクリア
                        self.selected_inventory_item = None
                        if self.inventory_list:
                            self.inventory_list.set_selected_index(None)
                    else:
                        self.selected_storage_item = None
                else:
                    self.selected_storage_item = None
                
                # 数量を設定
                if self.selected_storage_item and self.quantity_input:
                    self.quantity_input.set_text(str(self.selected_storage_item["quantity"]))
                
                self._update_buttons()
                return True
        
        return False
    
    def refresh(self) -> None:
        """パネルをリフレッシュ"""
        self._load_storage_data()