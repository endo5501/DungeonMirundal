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
        self.buyer_label: Optional[pygame_gui.elements.UILabel] = None
        self.buyer_dropdown: Optional[pygame_gui.elements.UIDropDownMenu] = None
        
        # データ（_create_ui()で参照される可能性があるため先に初期化）
        self.shop_items: Dict[str, Dict[str, Any]] = {}
        self.selected_category: Optional[str] = None
        self.selected_item: Optional[Dict[str, Any]] = None
        self.selected_item_id: Optional[str] = None
        self.displayed_items: List[Tuple[str, Dict[str, Any]]] = []
        self.selected_buyer: str = "party"  # デフォルトはパーティ共有
        
        # コントローラーへの参照を保存
        self._controller = controller
        
        # ServicePanelの初期化（この中で_create_ui()が呼ばれる）
        super().__init__(rect, parent, controller, "buy", ui_manager)
        
        logger.info("BuyPanel initialized")
    
    def destroy(self) -> None:
        """パネルを破棄（宿屋パターンを採用した強化版）"""
        logger.info("BuyPanel: Starting enhanced destroy process")
        
        # 特定のUI要素を明示的に破棄（宿屋パターン）
        specific_elements = [
            self.item_list,
            self.detail_box,
            self.quantity_input,
            self.buy_button,
            self.gold_label,
            self.total_label,
            self.buyer_label,
            self.buyer_dropdown
        ]
        
        # カテゴリボタンも個別に破棄
        if hasattr(self, 'category_buttons'):
            for button in self.category_buttons.values():
                if button and hasattr(button, 'kill'):
                    specific_elements.append(button)
        
        for element in specific_elements:
            if element and hasattr(element, 'kill'):
                try:
                    element.kill()
                    logger.debug(f"BuyPanel: Destroyed specific element {type(element).__name__}")
                except Exception as e:
                    logger.warning(f"BuyPanel: Failed to destroy {type(element).__name__}: {e}")
        
        # 親クラスのdestroy()を呼び出し
        super().destroy()
        
        # 参照をクリア
        if hasattr(self, 'category_buttons'):
            self.category_buttons.clear()
        self.item_list = None
        self.detail_box = None
        self.quantity_input = None
        self.buy_button = None
        self.gold_label = None
        self.total_label = None
        self.buyer_label = None
        self.buyer_dropdown = None
        
        # データをクリア
        self.shop_items.clear()
        self.displayed_items.clear()
        self.selected_item_id = None
        self.selected_category = None
        self.selected_item = None
        
        logger.info("BuyPanel: Enhanced destroy completed")
    
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
        detail_rect = pygame.Rect(420, 105, self.rect.width - 430, 190)
        
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
            relative_rect=pygame.Rect(420, 135, detail_rect.width, 160),
            manager=self.ui_manager,
            container=self.container,
            object_id="#detail_text_box"
        )
        self.ui_elements.append(self.detail_box)
    
    def _create_purchase_controls(self) -> None:
        """購入コントロールを作成"""
        y_position = 345
        
        # 購入者選択エリア
        buyer_label_rect = pygame.Rect(10, y_position, 80, 30)
        self.buyer_label = pygame_gui.elements.UILabel(
            relative_rect=buyer_label_rect,
            text="購入者:",
            manager=self.ui_manager,
            container=self.container
        )
        self.ui_elements.append(self.buyer_label)
        
        # 購入者ドロップダウン
        buyer_options = self._get_buyer_options()
        buyer_dropdown_rect = pygame.Rect(95, y_position, 200, 30)
        self.buyer_dropdown = pygame_gui.elements.UIDropDownMenu(
            options_list=buyer_options,
            starting_option=buyer_options[0] if buyer_options else "パーティ共有",
            relative_rect=buyer_dropdown_rect,
            manager=self.ui_manager,
            container=self.container
        )
        self.ui_elements.append(self.buyer_dropdown)
        
        # 数量と購入ボタンを下の行に配置
        y_position += 40
        
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
            initial_text="1",
            object_id="#quantity_input"
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
        # 全商品を取得
        result = self._execute_service_action("buy", {})
        
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
        
        # 選択されたカテゴリの商品を再取得
        result = self._execute_service_action("buy", {"category": category})
        
        if result.is_success() and result.data:
            self.shop_items = result.data.get("items", {})
            party_gold = result.data.get("party_gold", 0)
            self._update_gold_display(party_gold)
        
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
                logger.info(f"BuyPanel: 購入ボタンを有効化 - {self.selected_item['name']}")
                self.buy_button.enable()
            else:
                logger.info(f"BuyPanel: 購入ボタンを無効化 - selected_item={self.selected_item is not None}")
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
    
    def _get_buyer_options(self) -> List[str]:
        """購入者オプションを取得"""
        options = ["パーティ共有"]
        
        # パーティメンバーを追加
        if hasattr(self, '_controller') and self._controller:
            party = self._controller.get_party()
            if party:
                for member in party.members:
                    if member.is_alive():
                        options.append(member.name)
        
        return options
    
    def _execute_purchase(self) -> None:
        """購入を実行"""
        logger.info(f"BuyPanel: _execute_purchase called")
        logger.info(f"BuyPanel: selected_item_id: {self.selected_item_id}")
        logger.info(f"BuyPanel: selected_item: {self.selected_item}")
        
        if not self.selected_item_id:
            logger.warning("BuyPanel: No item selected, cannot execute purchase")
            return
        
        try:
            quantity = int(self.quantity_input.get_text())
            quantity = max(1, min(quantity, self.selected_item["stock"]))
            logger.info(f"BuyPanel: Purchase quantity: {quantity}")
        except Exception as e:
            logger.warning(f"BuyPanel: Failed to parse quantity, using default: {e}")
            quantity = 1
        
        # 選択された購入者を取得
        raw_buyer_text = self.buyer_dropdown.selected_option if self.buyer_dropdown else "パーティ共有"
        buyer_id = "party"  # デフォルトはパーティ
        
        logger.info(f"BuyPanel: buyer_dropdown.selected_option = '{raw_buyer_text}'")
        logger.info(f"BuyPanel: buyer_dropdown exists = {self.buyer_dropdown is not None}")
        
        # pygame_guiのUIDropDownMenuが返す値を正しく解析
        buyer_text = raw_buyer_text
        logger.info(f"BuyPanel: Raw buyer_text type: {type(raw_buyer_text)}, repr: {repr(raw_buyer_text)}")
        
        # タプルの場合、最初の要素を取得
        if isinstance(raw_buyer_text, tuple):
            buyer_text = raw_buyer_text[0]
            logger.info(f"BuyPanel: Extracted from tuple: '{buyer_text}'")
        elif isinstance(raw_buyer_text, str):
            # "'('A', 'A')'" のような文字列の場合、最初の値を抽出
            # 正規表現を使用してより確実に解析
            import re
            pattern = r"'?\('([^']+)',\s*'[^']+'\)'?"
            logger.info(f"BuyPanel: Trying regex pattern: {pattern}")
            match = re.match(pattern, raw_buyer_text)
            if match:
                buyer_text = match.group(1)
                logger.info(f"BuyPanel: Extracted buyer_text = '{buyer_text}'")
            else:
                logger.warning(f"BuyPanel: Failed to parse buyer_text with regex: '{raw_buyer_text}'")
                buyer_text = raw_buyer_text
        else:
            logger.warning(f"BuyPanel: Unexpected buyer_text type: {type(raw_buyer_text)}")
            buyer_text = str(raw_buyer_text)
        
        if buyer_text != "パーティ共有" and hasattr(self, '_controller') and self._controller:
            party = self._controller.get_party()
            logger.info(f"BuyPanel: party exists = {party is not None}")
            if party:
                logger.info(f"BuyPanel: party members = {[m.name for m in party.members]}")
                for member in party.members:
                    logger.info(f"BuyPanel: checking member '{member.name}' vs buyer_text '{buyer_text}'")
                    if member.name == buyer_text:
                        buyer_id = member.character_id
                        logger.info(f"BuyPanel: Found matching member, buyer_id = {buyer_id}")
                        break
        
        logger.info(f"BuyPanel: Final buyer_id = {buyer_id}")
        
        params = {
            "item_id": self.selected_item_id,
            "quantity": quantity,
            "buyer_id": buyer_id,
            "confirmed": True
        }
        logger.info(f"BuyPanel: Purchase params: {params}")
        
        result = self._execute_service_action("buy", params)
        logger.info(f"BuyPanel: Purchase result: {result}")
        
        if result.is_success():
            logger.info(f"BuyPanel: Purchase successful: {result.message}")
            self._show_message(result.message, "info")
            
            # 購入結果からデータを直接更新（UI要素の重複作成を避ける）
            if result.data:
                # 所持金を更新
                if "remaining_gold" in result.data:
                    self._update_gold_display(result.data["remaining_gold"])
                
                # 在庫を更新
                if "updated_items" in result.data:
                    self.shop_items = result.data["updated_items"]
                    self._update_item_list()
                elif self.selected_item_id in self.shop_items:
                    # フォールバック：購入したアイテムの在庫を手動で更新
                    purchased_quantity = quantity
                    self.shop_items[self.selected_item_id]["stock"] = max(0, 
                        self.shop_items[self.selected_item_id]["stock"] - purchased_quantity)
                    self._update_item_list()
                
                # 選択をクリア
                self.selected_item = None
                self.selected_item_id = None
                self._update_detail_view()
                self._update_controls()
        else:
            logger.error(f"BuyPanel: Purchase failed: {result.message}")
            self._show_message(result.message, "error")
    
    def handle_button_click(self, button: pygame_gui.elements.UIButton) -> bool:
        """ボタンクリックを処理"""
        logger.info(f"BuyPanel: handle_button_click called with button: {button}")
        
        # カテゴリボタン
        for cat_id, cat_button in self.category_buttons.items():
            if button == cat_button:
                logger.info(f"BuyPanel: Category button clicked: {cat_id}")
                self._select_category(cat_id)
                return True
        
        # アイテムリストの個別ボタン処理
        if self.item_list:
            # UISelectionListの内部ボタンかどうかチェック
            # ボタンのコンテナがUISelectionListの内部にあるかを確認
            try:
                # UISelectionListの内部構造を確認
                if hasattr(self.item_list, 'list_and_scroll_bar_container'):
                    container = self.item_list.list_and_scroll_bar_container
                    if hasattr(container, 'get_container'):
                        list_container = container.get_container()
                        if button.ui_container == list_container:
                            logger.info(f"BuyPanel: Item list button clicked: {button.text}")
                            self._handle_item_button_click(button)
                            return True
                
                # より直接的なチェック: ボタンテキストがアイテムリストの内容と一致するか
                button_text = str(button.text) if button.text else ""
                if button_text and any(item_text.startswith(button_text.split(' - ')[0]) for item_text in self.item_list.item_list):
                    logger.info(f"BuyPanel: Item list button clicked by text match: {button_text}")
                    self._handle_item_button_click(button)
                    return True
            except Exception as e:
                logger.error(f"BuyPanel: Error checking item list button: {e}")
                # フォールバック: テキストベースのチェック
                button_text = str(button.text) if button.text else ""
                if button_text and " - " in button_text and " G " in button_text:
                    logger.info(f"BuyPanel: Item list button clicked by pattern match: {button_text}")
                    self._handle_item_button_click(button)
                    return True
        
        # 購入ボタン
        if button == self.buy_button:
            logger.info(f"BuyPanel: 購入ボタンがクリックされました - {self.selected_item_id}")
            logger.info(f"BuyPanel: 購入ボタンの状態 - enabled: {self.buy_button.is_enabled}")
            logger.info(f"BuyPanel: 選択されたアイテム: {self.selected_item}")
            self._execute_purchase()
            return True
        
        logger.info(f"BuyPanel: Button click not handled")
        return False
    
    def _handle_item_button_click(self, button: pygame_gui.elements.UIButton) -> None:
        """アイテムボタンのクリックを処理"""
        button_text = str(button.text) if button.text else ""
        logger.info(f"BuyPanel: _handle_item_button_click called with button text: {button_text}")
        
        # ボタンテキストからアイテムを検索
        logger.info(f"BuyPanel: Searching for item with text: {button_text}")
        
        # displayed_itemsから該当するアイテムを検索
        for i, (item_id, item_data) in enumerate(self.displayed_items):
            # アイテム表示文字列を再構築して比較
            name = item_data["name"]
            price = item_data["price"]
            stock = item_data["stock"]
            
            if stock > 0:
                expected_text = f"{name} - {price} G (在庫: {stock})"
            else:
                expected_text = f"{name} - {price} G (売り切れ)"
            
            logger.info(f"BuyPanel: Comparing '{button_text}' with '{expected_text}'")
            
            if button_text == expected_text:
                logger.info(f"BuyPanel: Found matching item: {item_id} - {name}")
                self.selected_item_id = item_id
                self.selected_item = item_data
                self._update_detail_view()
                self._update_controls()
                return
        
        logger.warning(f"BuyPanel: No matching item found for button text: {button_text}")
    
    def handle_selection_list_changed(self, event: pygame.event.Event) -> bool:
        """選択リスト変更イベントを処理"""
        logger.info(f"BuyPanel: handle_selection_list_changed called with event type: {event.type}")
        
        if event.type == pygame_gui.UI_SELECTION_LIST_NEW_SELECTION:
            logger.info(f"BuyPanel: UI_SELECTION_LIST_NEW_SELECTION event received")
            logger.info(f"BuyPanel: event.ui_element: {event.ui_element}")
            logger.info(f"BuyPanel: self.item_list: {self.item_list}")
            
            if event.ui_element == self.item_list:
                logger.info(f"BuyPanel: Selection list event matches item_list")
                selection = self.item_list.get_single_selection()
                logger.info(f"BuyPanel: get_single_selection returned: {selection}")
                
                if selection is not None:
                    # UISelectionListの選択されたインデックスを直接取得
                    indices = [i for i, item in enumerate(self.item_list.item_list) if item == selection]
                    logger.info(f"BuyPanel: Found indices: {indices}")
                    logger.info(f"BuyPanel: item_list.item_list: {self.item_list.item_list}")
                    logger.info(f"BuyPanel: displayed_items: {[item[0] for item in self.displayed_items]}")
                    
                    if indices:
                        index = indices[0]
                        logger.info(f"BuyPanel: Using index: {index}")
                        if 0 <= index < len(self.displayed_items):
                            self.selected_item_id, self.selected_item = self.displayed_items[index]
                            logger.info(f"BuyPanel: アイテム選択 - {self.selected_item_id}: {self.selected_item['name']}")
                            self._update_detail_view()
                            self._update_controls()
                        else:
                            logger.warning(f"BuyPanel: Index {index} out of range for displayed_items (length: {len(self.displayed_items)})")
                            self.selected_item = None
                            self.selected_item_id = None
                    else:
                        logger.warning(f"BuyPanel: No matching indices found for selection: {selection}")
                        self.selected_item = None
                        self.selected_item_id = None
                else:
                    logger.info(f"BuyPanel: Selection is None, clearing selection")
                    self.selected_item = None
                    self.selected_item_id = None
                
                return True
            else:
                logger.info(f"BuyPanel: Selection list event does not match item_list")
        
        return False
    
    def handle_text_changed(self, event: pygame.event.Event) -> bool:
        """テキスト変更イベントを処理"""
        if hasattr(event, 'ui_element') and event.ui_element == self.quantity_input:
            self._update_total_cost()
            return True
        
        return False
    
    def handle_dropdown_changed(self, event: pygame.event.Event) -> bool:
        """ドロップダウン変更イベントを処理"""
        if hasattr(event, 'ui_element') and event.ui_element == self.buyer_dropdown:
            # 購入者が変更されたときの処理
            logger.info(f"BuyPanel: Buyer changed to {self.buyer_dropdown.selected_option}")
            return True
        
        return False