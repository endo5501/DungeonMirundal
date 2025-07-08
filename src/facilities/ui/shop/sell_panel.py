"""売却パネル"""

import pygame
import pygame_gui
from typing import Dict, Any, Optional, List, Tuple
import logging
from ..service_panel import ServicePanel
from ...core.service_result import ServiceResult

logger = logging.getLogger(__name__)


class SellPanel(ServicePanel):
    """売却パネル
    
    所持アイテムの売却処理を管理する。
    """
    
    def __init__(self, rect: pygame.Rect, parent: pygame_gui.elements.UIPanel,
                 controller, ui_manager: pygame_gui.UIManager):
        """初期化"""
        super().__init__(rect, parent, controller, "sell", ui_manager)
        
        # UI要素
        self.owner_list: Optional[pygame_gui.elements.UISelectionList] = None
        self.item_list: Optional[pygame_gui.elements.UISelectionList] = None
        self.detail_box: Optional[pygame_gui.elements.UITextBox] = None
        self.quantity_input: Optional[pygame_gui.elements.UITextEntryLine] = None
        self.sell_button: Optional[pygame_gui.elements.UIButton] = None
        self.gold_label: Optional[pygame_gui.elements.UILabel] = None
        self.sell_info_label: Optional[pygame_gui.elements.UILabel] = None
        
        # データ
        self.sellable_items: List[Dict[str, Any]] = []
        self.items_by_owner: Dict[str, List[Dict[str, Any]]] = {}
        self.selected_owner: Optional[str] = None
        self.selected_item: Optional[Dict[str, Any]] = None
        self.displayed_items: List[Dict[str, Any]] = []
        self.sell_rate: float = 0.5
        
        logger.info("SellPanel initialized")
    
    def _create_ui(self) -> None:
        """UI要素を作成"""
        # ヘッダー
        self._create_header()
        
        # リストエリア
        self._create_lists()
        
        # 詳細エリア
        self._create_detail_area()
        
        # 売却コントロール
        self._create_sell_controls()
        
        # 初期データを読み込み
        self._load_sellable_items()
    
    def _create_header(self) -> None:
        """ヘッダーを作成"""
        # タイトル
        title_rect = pygame.Rect(10, 10, 200, 35)
        title_label = pygame_gui.elements.UILabel(
            relative_rect=title_rect,
            text="アイテム売却",
            manager=self.ui_manager,
            container=self.container
        )
        self.ui_elements.append(title_label)
        
        # 所持金表示
        gold_rect = pygame.Rect(self.rect.width - 200, 10, 190, 35)
        self.gold_label = pygame_gui.elements.UILabel(
            relative_rect=gold_rect,
            text="所持金: 0 G",
            manager=self.ui_manager,
            container=self.container
        )
        self.ui_elements.append(self.gold_label)
        
        # 売却レート表示
        rate_rect = pygame.Rect(220, 10, 300, 35)
        self.sell_info_label = pygame_gui.elements.UILabel(
            relative_rect=rate_rect,
            text=f"買取率: {int(self.sell_rate * 100)}%",
            manager=self.ui_manager,
            container=self.container
        )
        self.ui_elements.append(self.sell_info_label)
    
    def _create_lists(self) -> None:
        """リストエリアを作成"""
        list_height = 250
        
        # 所有者リスト
        owner_label = pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect(10, 55, 200, 25),
            text="所持者",
            manager=self.ui_manager,
            container=self.container
        )
        self.ui_elements.append(owner_label)
        
        owner_rect = pygame.Rect(10, 85, 200, list_height)
        self.owner_list = pygame_gui.elements.UISelectionList(
            relative_rect=owner_rect,
            item_list=[],
            manager=self.ui_manager,
            container=self.container,
            allow_multi_select=False
        )
        self.ui_elements.append(self.owner_list)
        
        # アイテムリスト
        item_label = pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect(220, 55, 280, 25),
            text="所持アイテム",
            manager=self.ui_manager,
            container=self.container
        )
        self.ui_elements.append(item_label)
        
        item_rect = pygame.Rect(220, 85, 280, list_height)
        self.item_list = pygame_gui.elements.UISelectionList(
            relative_rect=item_rect,
            item_list=[],
            manager=self.ui_manager,
            container=self.container,
            allow_multi_select=False
        )
        self.ui_elements.append(self.item_list)
    
    def _create_detail_area(self) -> None:
        """詳細エリアを作成"""
        # 詳細表示
        detail_label = pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect(510, 55, 280, 25),
            text="アイテム詳細",
            manager=self.ui_manager,
            container=self.container
        )
        self.ui_elements.append(detail_label)
        
        detail_rect = pygame.Rect(510, 85, 280, 250)
        self.detail_box = pygame_gui.elements.UITextBox(
            html_text="アイテムを選択してください",
            relative_rect=detail_rect,
            manager=self.ui_manager,
            container=self.container
        )
        self.ui_elements.append(self.detail_box)
    
    def _create_sell_controls(self) -> None:
        """売却コントロールを作成"""
        y_position = 345
        
        # 数量ラベル
        quantity_label = pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect(10, y_position, 60, 35),
            text="数量:",
            manager=self.ui_manager,
            container=self.container
        )
        self.ui_elements.append(quantity_label)
        
        # 数量入力
        quantity_rect = pygame.Rect(75, y_position, 80, 35)
        self.quantity_input = pygame_gui.elements.UITextEntryLine(
            relative_rect=quantity_rect,
            manager=self.ui_manager,
            container=self.container,
            initial_text="1"
        )
        self.ui_elements.append(self.quantity_input)
        
        # 売却ボタン
        sell_rect = pygame.Rect(170, y_position, 120, 35)
        self.sell_button = self._create_button(
            "売却する",
            sell_rect,
            container=self.container,
            object_id="#sell_button"
        )
        self.sell_button.disable()
        
        # 売却金額表示
        self.sell_price_label = pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect(300, y_position, 200, 35),
            text="売却額: 0 G",
            manager=self.ui_manager,
            container=self.container
        )
        self.ui_elements.append(self.sell_price_label)
    
    def _load_sellable_items(self) -> None:
        """売却可能アイテムを読み込み"""
        result = self._execute_service_action("sell", {})
        
        if result.is_success() and result.data:
            self.sellable_items = result.data.get("items", [])
            self.sell_rate = result.data.get("sell_rate", 0.5)
            party_gold = result.data.get("party_gold", 0)
            
            # 売却レート表示を更新
            if self.sell_info_label:
                self.sell_info_label.set_text(f"買取率: {int(self.sell_rate * 100)}%")
            
            # 所持金を更新
            self._update_gold_display(party_gold)
            
            # 所有者ごとにアイテムを整理
            self._organize_items_by_owner()
            
            # 所有者リストを更新
            self._update_owner_list()
    
    def _organize_items_by_owner(self) -> None:
        """所有者ごとにアイテムを整理"""
        self.items_by_owner = {}
        
        for item in self.sellable_items:
            owner_id = item["owner_id"]
            if owner_id not in self.items_by_owner:
                self.items_by_owner[owner_id] = []
            self.items_by_owner[owner_id].append(item)
    
    def _update_owner_list(self) -> None:
        """所有者リストを更新"""
        if not self.owner_list:
            return
        
        # 所有者名のリストを作成
        owner_names = []
        owner_ids = []
        
        # 重複を避けるため、既に追加した所有者を記録
        added_owners = set()
        
        for item in self.sellable_items:
            owner_id = item["owner_id"]
            owner_name = item["owner_name"]
            
            if owner_id not in added_owners:
                owner_names.append(owner_name)
                owner_ids.append(owner_id)
                added_owners.add(owner_id)
        
        self.owner_list.set_item_list(owner_names)
        self.owner_ids = owner_ids  # IDリストを保持
    
    def _update_item_list(self) -> None:
        """アイテムリストを更新"""
        if not self.item_list or not self.selected_owner:
            if self.item_list:
                self.item_list.set_item_list([])
            return
        
        # 選択された所有者のアイテムを表示
        items = self.items_by_owner.get(self.selected_owner, [])
        self.displayed_items = items
        
        item_strings = []
        for item in items:
            name = item["name"]
            quantity = item["quantity"]
            sell_price = item["sell_price"]
            
            if quantity > 1:
                item_string = f"{name} x{quantity} ({sell_price} G/個)"
            else:
                item_string = f"{name} ({sell_price} G)"
            
            item_strings.append(item_string)
        
        self.item_list.set_item_list(item_strings)
        
        # 選択をクリア
        self.selected_item = None
        self._update_detail_view()
        self._update_controls()
    
    def _update_detail_view(self) -> None:
        """詳細ビューを更新"""
        if not self.detail_box:
            return
        
        if not self.selected_item:
            self.detail_box.html_text = "アイテムを選択してください"
            self.detail_box.rebuild()
            return
        
        item = self.selected_item
        
        # 詳細テキストを構築
        detail_text = f"<b>{item['name']}</b><br><br>"
        detail_text += f"<b>数量:</b> {item['quantity']}<br>"
        detail_text += f"<b>定価:</b> {item['base_price']} G<br>"
        detail_text += f"<b>買取価格:</b> {item['sell_price']} G/個<br>"
        detail_text += f"<br><b>所有者:</b> {item['owner_name']}"
        
        self.detail_box.html_text = detail_text
        self.detail_box.rebuild()
    
    def _update_controls(self) -> None:
        """コントロールを更新"""
        # 売却ボタンの有効/無効
        if self.sell_button:
            if self.selected_item:
                self.sell_button.enable()
            else:
                self.sell_button.disable()
        
        # 数量入力の最大値を設定
        if self.selected_item and self.quantity_input:
            max_quantity = self.selected_item["quantity"]
            self.quantity_input.set_text(str(max_quantity))
        
        # 売却金額を更新
        self._update_sell_price()
    
    def _update_sell_price(self) -> None:
        """売却金額を更新"""
        if not self.sell_price_label or not self.selected_item:
            if self.sell_price_label:
                self.sell_price_label.set_text("売却額: 0 G")
            return
        
        try:
            quantity = int(self.quantity_input.get_text())
            quantity = max(1, min(quantity, self.selected_item["quantity"]))
        except:
            quantity = 1
        
        total = self.selected_item["sell_price"] * quantity
        self.sell_price_label.set_text(f"売却額: {total} G")
    
    def _update_gold_display(self, gold: int) -> None:
        """所持金表示を更新"""
        if self.gold_label:
            self.gold_label.set_text(f"所持金: {gold} G")
    
    def _execute_sell(self) -> None:
        """売却を実行"""
        if not self.selected_item:
            return
        
        try:
            quantity = int(self.quantity_input.get_text())
            quantity = max(1, min(quantity, self.selected_item["quantity"]))
        except:
            quantity = 1
        
        params = {
            "item_id": self.selected_item["id"],
            "quantity": quantity,
            "confirmed": True
        }
        
        result = self._execute_service_action("sell", params)
        
        if result.is_success():
            self._show_message(result.message, "info")
            
            # データを再読み込み
            self._load_sellable_items()
            
            # 所持金を更新
            if result.data and isinstance(result.data, dict) and "new_gold" in result.data:
                self._update_gold_display(result.data["new_gold"])
        else:
            self._show_message(result.message, "error")
    
    def handle_button_click(self, button: pygame_gui.elements.UIButton) -> bool:
        """ボタンクリックを処理"""
        if button == self.sell_button:
            self._execute_sell()
            return True
        
        return False
    
    def handle_selection_list_changed(self, event: pygame.event.Event) -> bool:
        """選択リスト変更イベントを処理"""
        if event.type == pygame_gui.UI_SELECTION_LIST_NEW_SELECTION:
            if event.ui_element == self.owner_list:
                # 所有者が選択された
                selection = self.owner_list.get_single_selection()
                if selection is not None:
                    index = self.owner_list.item_list.index(selection)
                    if 0 <= index < len(self.owner_ids):
                        self.selected_owner = self.owner_ids[index]
                        self._update_item_list()
                    else:
                        self.selected_owner = None
                else:
                    self.selected_owner = None
                    self._update_item_list()
                
                return True
                
            elif event.ui_element == self.item_list:
                # アイテムが選択された
                selection = self.item_list.get_single_selection()
                if selection is not None:
                    index = self.item_list.item_list.index(selection)
                    if 0 <= index < len(self.displayed_items):
                        self.selected_item = self.displayed_items[index]
                        self._update_detail_view()
                        self._update_controls()
                    else:
                        self.selected_item = None
                else:
                    self.selected_item = None
                
                return True
        
        return False
    
    def handle_text_changed(self, event: pygame.event.Event) -> bool:
        """テキスト変更イベントを処理"""
        if hasattr(event, 'ui_element') and event.ui_element == self.quantity_input:
            self._update_sell_price()
            return True
        
        return False
    
    def _refresh_content(self) -> None:
        """コンテンツを更新"""
        self._load_sellable_items()
        self._clear_item_selection()
    
    def _clear_item_selection(self) -> None:
        """アイテム選択をクリア"""
        self.selected_item = None
        if self.quantity_input:
            self.quantity_input.set_text("1")
    
    def _update_sell_controls(self) -> None:
        """売却コントロールを更新"""
        if self.selected_item:
            # アイテムが選択されている場合
            if self.sell_button:
                self.sell_button.enable()
            if self.quantity_input:
                self.quantity_input.enable()
            self._update_sell_price()
        else:
            # アイテムが選択されていない場合
            if self.sell_button:
                self.sell_button.disable()
            if self.quantity_input:
                self.quantity_input.disable()
            if self.total_price_label:
                self.total_price_label.set_text("合計: 0 G")
    
    def _update_detail_display(self) -> None:
        """詳細表示を更新"""
        if self.selected_item and hasattr(self, 'detail_text_box') and self.detail_text_box:
            # アイテムの詳細を表示
            details = f"""
            <b>{self.selected_item['name']}</b><br>
            種類: {self.selected_item.get('type', '不明')}<br>
            単価: {self.selected_item.get('sell_price', 0)} G<br>
            所有者: {self.selected_item.get('owner', '不明')}<br>
            <br>
            {self.selected_item.get('description', '説明なし')}
            """
            self.detail_text_box.html_text = details.strip()
            self.detail_text_box.rebuild()
        elif hasattr(self, 'detail_text_box') and self.detail_text_box:
            # 何も選択されていない場合
            self.detail_text_box.html_text = "アイテムを選択してください"
            self.detail_text_box.rebuild()