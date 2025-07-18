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
    
    def __init__(self, rect: pygame.Rect, parent: pygame_gui.elements.UIPanel,
                 controller, ui_manager: pygame_gui.UIManager):
        """初期化"""
        # UI要素の初期化（_create_ui()で使用するため先に設定）
        self.inventory_list: Optional[pygame_gui.elements.UISelectionList] = None
        self.storage_list: Optional[pygame_gui.elements.UISelectionList] = None
        self.deposit_button: Optional[pygame_gui.elements.UIButton] = None
        self.withdraw_button: Optional[pygame_gui.elements.UIButton] = None
        self.quantity_input: Optional[pygame_gui.elements.UITextEntryLine] = None
        self.info_box: Optional[pygame_gui.elements.UITextBox] = None
        
        # データの初期化（_create_ui()で使用するため先に設定）
        self.inventory_items: List[Dict[str, Any]] = []
        self.storage_items: List[Dict[str, Any]] = []
        self.selected_inventory_item: Optional[Dict[str, Any]] = None
        self.selected_storage_item: Optional[Dict[str, Any]] = None
        self.storage_capacity = 100
        
        # 宿屋倉庫マネージャーへの参照
        self.storage_manager = None
        if controller and hasattr(controller, 'service') and hasattr(controller.service, 'storage_manager'):
            self.storage_manager = controller.service.storage_manager
        
        # 親クラスの初期化（_create_ui()が呼ばれる）
        super().__init__(rect, parent, controller, "storage", ui_manager)
        
        logger.info("StoragePanel initialized")
    
    def _create_ui(self) -> None:
        """UI要素を作成"""
        # ヘッダー
        self._create_header()
        
        # メインレイアウト
        self._create_main_layout()
        
        # 初期データを読み込み
        self._load_storage_data()
    
    def _create_header(self) -> None:
        """ヘッダーを作成"""
        # タイトル（重複を防ぐため固有IDを設定）
        title_rect = pygame.Rect(10, 10, self.rect.width - 20, 40)
        if self.ui_element_manager and not self.ui_element_manager.is_destroyed:
            title_label = self.ui_element_manager.create_label(
                "storage_panel_title",
                "アイテム管理",
                title_rect,
                object_id="#storage_panel_title"
            )
        else:
            # フォールバック（レガシー）
            title_label = pygame_gui.elements.UILabel(
                relative_rect=title_rect,
                text="アイテム管理",
                manager=self.ui_manager,
                container=self.container,
                object_id="#storage_panel_title"
            )
            self.ui_elements.append(title_label)
    
    def _create_main_layout(self) -> None:
        """メインレイアウトを作成"""
        # パネルの高さを考慮したレイアウト定数
        list_width = min(280, (self.rect.width - 140) // 2)  # 最大幅を制限
        list_height = min(200, self.rect.height - 180)  # パネルの高さに応じて調整
        
        # 左右のマージンを計算
        side_margin = max(10, (self.rect.width - 2 * list_width - 120) // 2)
        
        # インベントリリスト（左側）
        inv_label = self._create_label(
            "inventory_label",
            "所持アイテム",
            pygame.Rect(side_margin, 60, list_width, 25)
        )
        
        inv_rect = pygame.Rect(side_margin, 90, list_width, list_height)
        self.inventory_list = self._create_selection_list("inventory_list", inv_rect, [])
        
        # 中央のコントロールエリア
        self._create_control_area(list_width, side_margin)
        
        # 保管庫リスト（右側）
        storage_label = self._create_label(
            "storage_label",
            "保管庫",
            pygame.Rect(self.rect.width - side_margin - list_width, 60, list_width, 25)
        )
        
        storage_rect = pygame.Rect(
            self.rect.width - side_margin - list_width, 90,
            list_width, list_height
        )
        self.storage_list = self._create_selection_list("storage_list", storage_rect, [])
        
        # 情報ボックス（下部に配置、高さを確保）
        info_y = max(list_height + 100, self.rect.height - 60)
        info_rect = pygame.Rect(10, info_y, self.rect.width - 20, 40)
        self.info_box = self._create_text_box("info_box", "", info_rect)
    
    def _create_control_area(self, list_width: int, side_margin: int) -> None:
        """中央のコントロールエリアを作成"""
        center_x = self.rect.width // 2
        button_y_start = 120  # ボタンの開始位置を上に調整
        
        # 数量入力
        quantity_label = self._create_label(
            "quantity_label",
            "数量:",
            pygame.Rect(center_x - 50, button_y_start, 100, 25)
        )
        
        quantity_rect = pygame.Rect(center_x - 50, button_y_start + 30, 100, 30)
        if self.ui_element_manager and not self.ui_element_manager.is_destroyed:
            self.quantity_input = self.ui_element_manager.create_text_entry(
                "quantity_input",
                quantity_rect,
                initial_text="1"
            )
        else:
            # フォールバック（レガシー）
            self.quantity_input = pygame_gui.elements.UITextEntryLine(
                relative_rect=quantity_rect,
                manager=self.ui_manager,
                container=self.container,
                initial_text="1"
            )
            self.ui_elements.append(self.quantity_input)
        
        # 預けるボタン
        deposit_rect = pygame.Rect(center_x - 50, button_y_start + 70, 100, 35)
        self.deposit_button = self._create_button(
            "deposit_button",
            "預ける →",
            deposit_rect,
            container=self.container,
            object_id="#deposit_button"
        )
        
        # 引き出すボタン
        withdraw_rect = pygame.Rect(center_x - 50, button_y_start + 115, 100, 35)
        self.withdraw_button = self._create_button(
            "withdraw_button",
            "← 引き出す",
            withdraw_rect,
            container=self.container,
            object_id="#withdraw_button"
        )
    
    def _load_storage_data(self) -> None:
        """保管庫データを読み込み"""
        # NavigationPanel再作成を避けるため、直接storage_managerから取得
        if self.storage_manager:
            try:
                # インベントリアイテムを直接取得
                if hasattr(self.storage_manager, 'get_inventory_items'):
                    self.inventory_items = self.storage_manager.get_inventory_items()
                else:
                    self.inventory_items = []
                
                # 保管庫アイテムを直接取得
                if hasattr(self.storage_manager, 'get_storage_items'):
                    self.storage_items = self.storage_manager.get_storage_items()
                else:
                    self.storage_items = []
                
                # 容量を直接取得
                if hasattr(self.storage_manager, 'get_capacity'):
                    self.storage_capacity = self.storage_manager.get_capacity()
                else:
                    self.storage_capacity = 100
                    
                logger.info("StoragePanel: Data loaded directly from storage_manager")
            except Exception as e:
                logger.warning(f"StoragePanel: Failed to load from storage_manager: {e}")
                self._load_demo_data()
        else:
            logger.info("StoragePanel: storage_manager not available, loading demo data")
            self._load_demo_data()
        
        self._update_lists()
        self._update_info()
        self._update_buttons()
    
    def _load_demo_data(self) -> None:
        """デモ用データを読み込み"""
        self.inventory_items = [
            {"id": "item1", "name": "ポーション", "quantity": 5, "stackable": True},
            {"id": "item2", "name": "エーテル", "quantity": 3, "stackable": True},
            {"id": "item3", "name": "鉄の剣", "quantity": 1, "stackable": False}
        ]
        
        self.storage_items = [
            {"id": "item4", "name": "ハイポーション", "quantity": 10, "stackable": True},
            {"id": "item5", "name": "魔法の杖", "quantity": 1, "stackable": False}
        ]
    
    def destroy(self) -> None:
        """パネルを破棄（強化版）"""
        logger.info("StoragePanel: Starting enhanced destroy process")
        
        # 特定のUI要素を明示的に破棄
        specific_elements = [
            self.inventory_list,
            self.storage_list,
            self.deposit_button,
            self.withdraw_button,
            self.quantity_input,
            self.info_box
        ]
        
        for element in specific_elements:
            if element and hasattr(element, 'kill'):
                try:
                    element.kill()
                    logger.debug(f"StoragePanel: Destroyed specific element {type(element).__name__}")
                except Exception as e:
                    logger.warning(f"StoragePanel: Failed to destroy {type(element).__name__}: {e}")
        
        # 親クラスのdestroy()を呼び出し
        super().destroy()
        
        # 参照をクリア
        self.inventory_list = None
        self.storage_list = None
        self.deposit_button = None
        self.withdraw_button = None
        self.quantity_input = None
        self.info_box = None
        self.inventory_items = []
        self.storage_items = []
        self.selected_inventory_item = None
        self.selected_storage_item = None
        
        logger.info("StoragePanel: Enhanced destroy completed")
    
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
        capacity = getattr(self, 'storage_capacity', 100)  # デフォルト値100を設定
        free_space = capacity - used_space
        
        info_text = f"<b>保管庫容量:</b> {used_space}/{capacity} "
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