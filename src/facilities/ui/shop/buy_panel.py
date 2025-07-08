"""購入パネル"""

import pygame
import pygame_gui
from typing import Dict, Any, Optional, List, Tuple
import logging
from ..service_panel import ServicePanel
from ...core.service_result import ServiceResult, ResultType

logger = logging.getLogger(__name__)


class BuyPanel(ServicePanel):
    """購入パネル
    
    商品の一覧表示と購入処理を管理する。
    """
    
    def __init__(self, rect: pygame.Rect, parent: pygame_gui.elements.UIPanel,
                 controller, ui_manager: pygame_gui.UIManager):
        """初期化"""
        # ServicePanelを継承しているため、先にデータ属性を全て初期化する必要がある
        # （super().__init__内で_create_ui()が呼ばれるため）
        
        # UI要素
        self.category_buttons: Dict[str, pygame_gui.elements.UIButton] = {}
        self.item_list: Optional[pygame_gui.elements.UISelectionList] = None
        self.detail_panel = None
        self.detail_box = None
        self.quantity_input: Optional[pygame_gui.elements.UITextEntryLine] = None
        self.buy_button: Optional[pygame_gui.elements.UIButton] = None
        self.gold_label: Optional[pygame_gui.elements.UILabel] = None
        self.total_label: Optional[pygame_gui.elements.UILabel] = None
        
        # データ（_create_ui()で参照される可能性があるため先に初期化）
        self.shop_items: Dict[str, Dict[str, Any]] = {}
        self.selected_category: Optional[str] = None
        self.selected_item: Optional[Dict[str, Any]] = None
        self.selected_item_id: Optional[str] = None
        self.displayed_items: List[Tuple[str, Dict[str, Any]]] = []
        
        # ServicePanelの初期化（この中で_create_ui()が呼ばれる）
        super().__init__(rect, parent, controller, "buy", ui_manager)
        
        logger.info("BuyPanel initialized")
    
    def _create_ui(self) -> None:
        """UI要素を作成"""
        # タイトルと所持金表示
        self._create_header()
        
        # カテゴリボタン
        self._create_category_buttons()
        
        # 商品リスト
        self._create_item_list()
        
        # 詳細パネル
        self._create_detail_area()
        
        # 購入コントロール
        self._create_purchase_controls()
        
        # 初期データを読み込み
        self._load_shop_data()
    
    def _create_header(self) -> None:
        """ヘッダーを作成"""
        # タイトル
        title_rect = pygame.Rect(10, 10, 200, 35)
        title_label = pygame_gui.elements.UILabel(
            relative_rect=title_rect,
            text="商品購入",
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
    
    def _create_category_buttons(self) -> None:
        """カテゴリボタンを作成"""
        categories = [
            ("weapons", "武器", "⚔️"),
            ("armor", "防具", "🛡️"),
            ("items", "アイテム", "🧪"),
            ("special", "特殊", "✨")
        ]
        
        button_width = 120
        button_height = 40
        spacing = 10
        start_x = 10
        y_position = 55
        
        for i, (cat_id, cat_name, icon) in enumerate(categories):
            x_position = start_x + i * (button_width + spacing)
            button_rect = pygame.Rect(x_position, y_position, button_width, button_height)
            
            button = self._create_button(
                f"{icon} {cat_name}",
                button_rect,
                container=self.container,
                object_id=f"#category_{cat_id}"
            )
            
            self.category_buttons[cat_id] = button
    
    def _create_item_list(self) -> None:
        """商品リストを作成"""
        # リストラベル
        list_label = pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect(10, 105, 200, 25),
            text="商品一覧",
            manager=self.ui_manager,
            container=self.container
        )
        self.ui_elements.append(list_label)
        
        # アイテムリスト
        list_rect = pygame.Rect(10, 135, 400, 200)
        self.item_list = pygame_gui.elements.UISelectionList(
            relative_rect=list_rect,
            item_list=[],
            manager=self.ui_manager,
            container=self.container,
            allow_multi_select=False
        )
        self.ui_elements.append(self.item_list)
    
    def _create_detail_area(self) -> None:
        """詳細エリアを作成"""
        # 詳細パネルを動的に作成（ItemDetailPanelを使用）
        detail_rect = pygame.Rect(420, 105, self.rect.width - 430, 230)
        
        # プレースホルダー（詳細パネルは選択時に作成）
        detail_label = pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect(420, 105, detail_rect.width, 25),
            text="商品詳細",
            manager=self.ui_manager,
            container=self.container
        )
        self.ui_elements.append(detail_label)
        
        self.detail_box = pygame_gui.elements.UITextBox(
            html_text="商品を選択してください",
            relative_rect=pygame.Rect(420, 135, detail_rect.width, 200),
            manager=self.ui_manager,
            container=self.container
        )
        self.ui_elements.append(self.detail_box)
    
    def _create_purchase_controls(self) -> None:
        """購入コントロールを作成"""
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
        
        # 購入ボタン
        buy_rect = pygame.Rect(170, y_position, 120, 35)
        self.buy_button = self._create_button(
            "購入する",
            buy_rect,
            container=self.container,
            object_id="#buy_button"
        )
        self.buy_button.disable()  # 初期状態は無効
        
        # 合計金額表示
        self.total_label = pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect(300, y_position, 200, 35),
            text="合計: 0 G",
            manager=self.ui_manager,
            container=self.container
        )
        self.ui_elements.append(self.total_label)
    
    def _load_shop_data(self) -> None:
        """商店データを読み込み"""
        # 初期カテゴリで商品を取得
        result = self._execute_service_action("buy", {"category": "weapons"})
        
        if result.is_success() and result.data:
            self.shop_items = result.data.get("items", {})
            party_gold = result.data.get("party_gold", 0)
            self._update_gold_display(party_gold)
            
            # 最初のカテゴリを選択
            self._select_category("weapons")
    
    def _select_category(self, category: str) -> None:
        """カテゴリを選択"""
        self.selected_category = category
        
        # カテゴリボタンのハイライト更新
        for cat_id, button in self.category_buttons.items():
            if cat_id == category:
                # 選択状態にする（スタイル変更）
                if hasattr(button, 'selected'):
                    button.selected = True
            else:
                if hasattr(button, 'selected'):
                    button.selected = False
        
        # 商品リストを更新
        self._update_item_list()
    
    def _update_item_list(self) -> None:
        """商品リストを更新"""
        if not self.item_list:
            return
        
        # 選択されたカテゴリの商品を抽出
        self.displayed_items = []
        item_strings = []
        
        for item_id, item_data in self.shop_items.items():
            if item_data.get("category") == self.selected_category:
                # 表示文字列を作成
                name = item_data["name"]
                price = item_data["price"]
                stock = item_data["stock"]
                
                if stock > 0:
                    item_string = f"{name} - {price} G (在庫: {stock})"
                else:
                    item_string = f"{name} - {price} G (売り切れ)"
                
                item_strings.append(item_string)
                self.displayed_items.append((item_id, item_data))
        
        self.item_list.set_item_list(item_strings)
        
        # 選択をクリア
        self.selected_item = None
        self.selected_item_id = None
        self._update_detail_view()
        self._update_controls()
    
    def _update_detail_view(self) -> None:
        """詳細ビューを更新"""
        if not self.detail_box:
            return
        
        if not self.selected_item:
            self.detail_box.html_text = "商品を選択してください"
            self.detail_box.rebuild()
            return
        
        item = self.selected_item
        
        # 詳細テキストを構築
        detail_text = f"<b>{item['name']}</b><br><br>"
        detail_text += f"{item['description']}<br><br>"
        
        # 効果を表示
        if "stats" in item:
            detail_text += "<b>効果:</b><br>"
            for stat, value in item["stats"].items():
                stat_name = self._get_stat_name(stat)
                detail_text += f"・{stat_name}: +{value}<br>"
        elif "effect" in item:
            detail_text += "<b>効果:</b><br>"
            for effect, value in item["effect"].items():
                effect_text = self._get_effect_text(effect, value)
                detail_text += f"・{effect_text}<br>"
        
        detail_text += f"<br><b>価格:</b> {item['price']} G<br>"
        detail_text += f"<b>在庫:</b> {item['stock']}個"
        
        self.detail_box.html_text = detail_text
        self.detail_box.rebuild()
    
    def _get_stat_name(self, stat: str) -> str:
        """ステータス名を取得"""
        stat_names = {
            "attack": "攻撃力",
            "defense": "防御力",
            "magic": "魔力",
            "speed": "素早さ"
        }
        return stat_names.get(stat, stat)
    
    def _get_effect_text(self, effect: str, value: Any) -> str:
        """効果テキストを取得"""
        if effect == "hp_restore":
            return f"HPを{value}回復"
        elif effect == "mp_restore":
            return f"MPを{value}回復"
        elif effect == "cure_poison":
            return "毒を治療"
        else:
            return f"{effect}: {value}"
    
    def _update_controls(self) -> None:
        """コントロールを更新"""
        # 購入ボタンの有効/無効
        if self.buy_button:
            if self.selected_item and self.selected_item["stock"] > 0:
                self.buy_button.enable()
            else:
                self.buy_button.disable()
        
        # 合計金額を更新
        self._update_total_cost()
    
    def _update_total_cost(self) -> None:
        """合計金額を更新"""
        if not self.total_label or not self.selected_item:
            if self.total_label:
                self.total_label.set_text("合計: 0 G")
            return
        
        try:
            quantity = int(self.quantity_input.get_text())
            quantity = max(1, quantity)
        except:
            quantity = 1
        
        total = self.selected_item["price"] * quantity
        self.total_label.set_text(f"合計: {total} G")
    
    def _update_gold_display(self, gold: int) -> None:
        """所持金表示を更新"""
        if self.gold_label:
            self.gold_label.set_text(f"所持金: {gold} G")
    
    def _execute_purchase(self) -> None:
        """購入を実行"""
        if not self.selected_item_id:
            return
        
        try:
            quantity = int(self.quantity_input.get_text())
            quantity = max(1, min(quantity, self.selected_item["stock"]))
        except:
            quantity = 1
        
        params = {
            "item_id": self.selected_item_id,
            "quantity": quantity,
            "confirmed": True
        }
        
        result = self._execute_service_action("buy", params)
        
        if result.is_success():
            self._show_message(result.message, "info")
            
            # データを再読み込み
            self._load_shop_data()
            
            # 所持金を更新
            if result.data and "remaining_gold" in result.data:
                self._update_gold_display(result.data["remaining_gold"])
        else:
            self._show_message(result.message, "error")
    
    def handle_button_click(self, button: pygame_gui.elements.UIButton) -> bool:
        """ボタンクリックを処理"""
        # カテゴリボタン
        for cat_id, cat_button in self.category_buttons.items():
            if button == cat_button:
                self._select_category(cat_id)
                return True
        
        # 購入ボタン
        if button == self.buy_button:
            self._execute_purchase()
            return True
        
        return False
    
    def handle_selection_list_changed(self, event: pygame.event.Event) -> bool:
        """選択リスト変更イベントを処理"""
        if event.type == pygame_gui.UI_SELECTION_LIST_NEW_SELECTION:
            if event.ui_element == self.item_list:
                selection = self.item_list.get_single_selection()
                if selection is not None:
                    index = self.item_list.item_list.index(selection)
                    if 0 <= index < len(self.displayed_items):
                        self.selected_item_id, self.selected_item = self.displayed_items[index]
                        self._update_detail_view()
                        self._update_controls()
                    else:
                        self.selected_item = None
                        self.selected_item_id = None
                else:
                    self.selected_item = None
                    self.selected_item_id = None
                
                return True
        
        return False
    
    def handle_text_changed(self, event: pygame.event.Event) -> bool:
        """テキスト変更イベントを処理"""
        if hasattr(event, 'ui_element') and event.ui_element == self.quantity_input:
            self._update_total_cost()
            return True
        
        return False