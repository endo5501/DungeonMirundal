"""鑑定パネル"""

import pygame
import pygame_gui
from typing import Dict, Any, Optional, List, Tuple
import logging
from ..service_panel import ServicePanel
from ...core.service_result import ServiceResult

logger = logging.getLogger(__name__)


class IdentifyPanel(ServicePanel):
    """鑑定パネル
    
    未鑑定アイテムの鑑定処理を管理する。
    """
    
    def __init__(self, rect: pygame.Rect, parent: pygame_gui.elements.UIPanel,
                 controller, ui_manager: pygame_gui.UIManager):
        """初期化"""
        # UI要素
        self.owner_list: Optional[pygame_gui.elements.UISelectionList] = None
        self.item_list: Optional[pygame_gui.elements.UISelectionList] = None
        self.detail_box: Optional[pygame_gui.elements.UITextBox] = None
        self.identify_button: Optional[pygame_gui.elements.UIButton] = None
        self.gold_label: Optional[pygame_gui.elements.UILabel] = None
        self.identify_cost_label: Optional[pygame_gui.elements.UILabel] = None
        self.owner_ids: List[str] = []
        
        # データ
        self.unidentified_items: List[Dict[str, Any]] = []
        self.items_by_owner: Dict[str, List[Dict[str, Any]]] = {}
        self.selected_owner: Optional[str] = None
        self.selected_item: Optional[Dict[str, Any]] = None
        self.displayed_items: List[Dict[str, Any]] = []
        self.identify_cost: int = 100  # デフォルト鑑定料金
        
        # ServicePanelの初期化
        super().__init__(rect, parent, controller, "identify", ui_manager)
        
        logger.info("IdentifyPanel initialized")
    
    def _create_ui(self) -> None:
        """UI要素を作成"""
        # ヘッダー
        self._create_header()
        
        # リストエリア
        self._create_lists()
        
        # 詳細エリア
        self._create_detail_area()
        
        # 鑑定コントロール
        self._create_identify_controls()
        
        # 初期データを読み込み
        self._load_unidentified_items()
    
    def _create_header(self) -> None:
        """ヘッダーを作成"""
        # タイトル
        title_rect = pygame.Rect(10, 10, 200, 35)
        title_label = pygame_gui.elements.UILabel(
            relative_rect=title_rect,
            text="アイテム鑑定",
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
        
        # 鑑定料金表示
        cost_rect = pygame.Rect(220, 10, 300, 35)
        self.identify_cost_label = pygame_gui.elements.UILabel(
            relative_rect=cost_rect,
            text=f"鑑定料金: {self.identify_cost} G/個",
            manager=self.ui_manager,
            container=self.container
        )
        self.ui_elements.append(self.identify_cost_label)
    
    def _create_lists(self) -> None:
        """リストエリアを作成"""
        # 所有者リスト
        owner_label = pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect(10, 55, 200, 25),
            text="所有者",
            manager=self.ui_manager,
            container=self.container
        )
        self.ui_elements.append(owner_label)
        
        owner_rect = pygame.Rect(10, 85, 200, 250)
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
            text="未鑑定アイテム",
            manager=self.ui_manager,
            container=self.container
        )
        self.ui_elements.append(item_label)
        
        item_rect = pygame.Rect(220, 85, 280, 250)
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
    
    def _create_identify_controls(self) -> None:
        """鑑定コントロールを作成"""
        y_position = 345
        
        # 鑑定ボタン
        identify_rect = pygame.Rect(220, y_position, 150, 35)
        self.identify_button = self._create_button(
            "鑑定する",
            identify_rect,
            container=self.container,
            object_id="#identify_button"
        )
        self.identify_button.disable()
    
    def _load_unidentified_items(self) -> None:
        """未鑑定アイテムを読み込み"""
        result = self._execute_service_action("identify", {"list_only": True})
        
        if result.is_success() and result.data:
            self.unidentified_items = result.data.get("items", [])
            self.identify_cost = result.data.get("identify_cost", 100)
            party_gold = result.data.get("party_gold", 0)
            
            # 鑑定料金表示を更新
            if self.identify_cost_label:
                self.identify_cost_label.set_text(f"鑑定料金: {self.identify_cost} G/個")
            
            # 所持金を更新
            self._update_gold_display(party_gold)
            
            # 所有者ごとにアイテムを整理
            self._organize_items_by_owner()
            
            # 所有者リストを更新
            self._update_owner_list()
    
    def _organize_items_by_owner(self) -> None:
        """所有者ごとにアイテムを整理"""
        self.items_by_owner = {}
        
        for item in self.unidentified_items:
            owner_id = item.get("owner_id", "party")
            if owner_id not in self.items_by_owner:
                self.items_by_owner[owner_id] = []
            self.items_by_owner[owner_id].append(item)
    
    def _update_owner_list(self) -> None:
        """所有者リストを更新"""
        if not self.owner_list:
            return
        
        owner_names = []
        owner_ids = []
        
        # 重複を避ける
        added_owners = set()
        
        for item in self.unidentified_items:
            owner_id = item.get("owner_id", "party")
            owner_name = item.get("owner_name", "パーティ")
            
            if owner_id not in added_owners:
                owner_names.append(owner_name)
                owner_ids.append(owner_id)
                added_owners.add(owner_id)
        
        # アイテムがない場合
        if not owner_names:
            self.owner_list.set_item_list(["未鑑定アイテムがありません"])
            self.owner_ids = []
            if self.detail_box:
                self.detail_box.html_text = "未鑑定アイテムがありません"
                self.detail_box.rebuild()
        else:
            self.owner_list.set_item_list(owner_names)
            self.owner_ids = owner_ids
    
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
            name = item.get("name", "未鑑定アイテム")
            quantity = item.get("quantity", 1)
            
            if quantity > 1:
                item_string = f"{name} x{quantity}"
            else:
                item_string = name
            
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
        
        # 未鑑定アイテムの詳細
        detail_text = f"<b>未鑑定アイテム</b><br><br>"
        detail_text += f"カテゴリ: {item.get('category', '不明')}<br>"
        detail_text += f"数量: {item.get('quantity', 1)}<br><br>"
        detail_text += f"<b>鑑定料金:</b> {self.identify_cost} G<br>"
        detail_text += "<br><i>鑑定すると詳細な情報が明らかになります</i>"
        
        self.detail_box.html_text = detail_text
        self.detail_box.rebuild()
    
    def _update_controls(self) -> None:
        """コントロールを更新"""
        if self.identify_button:
            if self.selected_item:
                self.identify_button.enable()
            else:
                self.identify_button.disable()
    
    def _update_gold_display(self, gold: int) -> None:
        """所持金表示を更新"""
        if self.gold_label:
            self.gold_label.set_text(f"所持金: {gold} G")
    
    def _execute_identify(self) -> None:
        """鑑定を実行"""
        if not self.selected_item:
            return
        
        params = {
            "item_id": self.selected_item.get("item_instance_id"),
            "confirmed": True
        }
        
        result = self._execute_service_action("identify", params)
        
        if result.is_success():
            self._show_message(result.message, "info")
            
            # データを再読み込み
            self._load_unidentified_items()
            
            # 所持金を更新
            if result.data and "remaining_gold" in result.data:
                self._update_gold_display(result.data["remaining_gold"])
        else:
            self._show_message(result.message, "error")
    
    def handle_button_click(self, button: pygame_gui.elements.UIButton) -> bool:
        """ボタンクリックを処理"""
        if button == self.identify_button:
            self._execute_identify()
            return True
        
        return False
    
    def handle_selection_list_changed(self, event: pygame.event.Event) -> bool:
        """選択リスト変更イベントを処理"""
        if event.type == pygame_gui.UI_SELECTION_LIST_NEW_SELECTION:
            if event.ui_element == self.owner_list:
                selection = self.owner_list.get_single_selection()
                if selection and self.owner_ids:
                    indices = [i for i, item in enumerate(self.owner_list.item_list) if item == selection]
                    if indices and indices[0] < len(self.owner_ids):
                        self.selected_owner = self.owner_ids[indices[0]]
                        self._update_item_list()
                return True
                
            elif event.ui_element == self.item_list:
                selection = self.item_list.get_single_selection()
                if selection is not None:
                    indices = [i for i, item in enumerate(self.item_list.item_list) if item == selection]
                    if indices:
                        index = indices[0]
                        if 0 <= index < len(self.displayed_items):
                            self.selected_item = self.displayed_items[index]
                            self._update_detail_view()
                            self._update_controls()
                return True
        
        return False