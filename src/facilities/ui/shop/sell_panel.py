"""売却パネル"""

import pygame
import pygame_gui
from typing import Dict, Any, Optional, List, Tuple
import logging
from ..service_panel import ServicePanel

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class SellPanel(ServicePanel):
    """売却パネル
    
    所持アイテムの売却処理を管理する。
    """
    
    def __init__(self, rect: pygame.Rect, parent: pygame_gui.elements.UIPanel,
                 controller, ui_manager: pygame_gui.UIManager):
        """初期化"""
        # ServicePanelを継承しているため、先にデータ属性を全て初期化する必要がある
        # （super().__init__内で_create_ui()が呼ばれるため）
        
        # UI要素
        self.owner_list: Optional[pygame_gui.elements.UISelectionList] = None
        self.item_list: Optional[pygame_gui.elements.UISelectionList] = None
        self.detail_box: Optional[pygame_gui.elements.UITextBox] = None
        self.quantity_input: Optional[pygame_gui.elements.UITextEntryLine] = None
        self.sell_button: Optional[pygame_gui.elements.UIButton] = None
        self.gold_label: Optional[pygame_gui.elements.UILabel] = None
        self.sell_info_label: Optional[pygame_gui.elements.UILabel] = None
        self.sell_price_label: Optional[pygame_gui.elements.UILabel] = None
        self.owner_ids: List[str] = []
        
        # データ（_create_ui()で参照されるため先に初期化）
        self.sellable_items: List[Dict[str, Any]] = []
        self.items_by_owner: Dict[str, List[Dict[str, Any]]] = {}
        self.selected_owner: Optional[str] = None
        self.selected_item: Optional[Dict[str, Any]] = None
        self.displayed_items: List[Dict[str, Any]] = []
        self.sell_rate: float = 0.5
        
        # ServicePanelの初期化（この中で_create_ui()が呼ばれる）
        super().__init__(rect, parent, controller, "sell", ui_manager)
        
        logger.debug("SellPanel initialized")
    
    def destroy(self) -> None:
        """パネルを破棄（宿屋パターンを採用した強化版）"""
        logger.debug("SellPanel: Starting enhanced destroy process")
        
        # 特定のUI要素を明示的に破棄（宿屋パターン）
        specific_elements = [
            self.owner_list,
            self.item_list,
            self.detail_box,
            self.quantity_input,
            self.sell_button,
            self.gold_label,
            self.sell_info_label,
            self.sell_price_label
        ]
        
        for element in specific_elements:
            if element and hasattr(element, 'kill'):
                try:
                    element.kill()
                    logger.debug(f"SellPanel: Destroyed specific element {type(element).__name__}")
                except Exception as e:
                    logger.warning(f"SellPanel: Failed to destroy {type(element).__name__}: {e}")
        
        # 親クラスのdestroy()を呼び出し
        super().destroy()
        
        # 参照をクリア
        self.owner_list = None
        self.item_list = None
        self.detail_box = None
        self.quantity_input = None
        self.sell_button = None
        self.gold_label = None
        self.sell_info_label = None
        self.sell_price_label = None
        
        # データをクリア
        self.sellable_items.clear()
        self.items_by_owner.clear()
        self.owner_ids.clear()
        self.displayed_items.clear()
        self.selected_owner = None
        self.selected_item = None
        
        logger.debug("SellPanel: Enhanced destroy completed")
    
    def set_mode(self, mode: str):
        """パネルモードを設定（identify用）"""
        if mode == "identify":
            # 鑑定モード用の設定
            pass
    
    def _create_ui(self) -> None:
        """UI要素を作成"""
        logger.debug("SellPanel: _create_ui() called")
        
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
        
        # 初期状態の詳細表示を更新
        self._update_detail_view()
        
        logger.debug("SellPanel: _create_ui() completed")
    
    def _create_header(self) -> None:
        """ヘッダーを作成"""
        # タイトル
        title_rect = pygame.Rect(10, 10, 200, 35)
        title_label = self._create_label("title", "アイテム売却", title_rect)
        
        # 所持金表示
        gold_rect = pygame.Rect(self.rect.width - 200, 10, 190, 35)
        self.gold_label = self._create_label("gold_label", "所持金: 0 G", gold_rect)
        
        # 売却レート表示
        rate_rect = pygame.Rect(220, 10, 300, 35)
        self.sell_info_label = self._create_label("sell_info_label", f"買取率: {int(self.sell_rate * 100)}%", rate_rect)
    
    def _create_lists(self) -> None:
        """リストエリアを作成"""
        list_height = 250
        
        # 所有者リスト
        owner_label = self._create_label("owner_label", "所持者", pygame.Rect(10, 55, 200, 25))
        
        owner_rect = pygame.Rect(10, 85, 200, list_height)
        self.owner_list = self._create_selection_list("owner_list", owner_rect, [])
        
        # アイテムリスト
        item_label = self._create_label("item_label", "所持アイテム", pygame.Rect(220, 55, 280, 25))
        
        item_rect = pygame.Rect(220, 85, 280, list_height)
        self.item_list = self._create_selection_list("item_list", item_rect, [])
    
    def _create_detail_area(self) -> None:
        """詳細エリアを作成"""
        # 詳細表示
        detail_label = self._create_label("detail_label", "アイテム詳細", pygame.Rect(510, 55, 280, 25))
        
        detail_rect = pygame.Rect(510, 85, 280, 250)
        self.detail_box = self._create_text_box("detail_box", "アイテムを選択してください", detail_rect)
    
    def _create_sell_controls(self) -> None:
        """売却コントロールを作成"""
        y_position = 345
        
        # 数量ラベル
        quantity_label = self._create_label("quantity_label", "数量:", pygame.Rect(10, y_position, 60, 35))
        
        # 数量入力
        quantity_rect = pygame.Rect(75, y_position, 80, 35)
        if self.ui_element_manager and not self.ui_element_manager.is_destroyed:
            self.quantity_input = self.ui_element_manager.create_text_entry("quantity_input", quantity_rect, initial_text="1")
        else:
            # フォールバック（レガシー）
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
            "sell_button",
            "売却する",
            sell_rect,
            container=self.container,
            object_id="#sell_button"
        )
        self.sell_button.disable()
        
        # 売却金額表示
        self.sell_price_label = self._create_label("sell_price_label", "売却額: 0 G", pygame.Rect(300, y_position, 200, 35))
    
    def _load_sellable_items(self) -> None:
        """売却可能アイテムを読み込み"""
        logger.debug("SellPanel: Loading sellable items")
        result = self._execute_service_action("sell", {})
        
        if result.is_success() and result.data:
            self.sellable_items = result.data.get("items", [])
            self.sell_rate = result.data.get("sell_rate", 0.5)
            party_gold = result.data.get("party_gold", 0)
            
            logger.debug(f"SellPanel: Loaded {len(self.sellable_items)} sellable items")
            
            # 売却レート表示を更新
            if self.sell_info_label:
                self.sell_info_label.set_text(f"買取率: {int(self.sell_rate * 100)}%")
            
            # 所持金を更新
            self._update_gold_display(party_gold)
            
            # パーティ情報を取得
            self.party = self._get_party()
            
            # 所有者ごとにアイテムを整理
            self._organize_items_by_owner()
            
            # 所有者リストを更新
            self._update_owner_list()
        else:
            logger.error(f"SellPanel: 売却可能アイテムの取得に失敗: {result.message if result else 'result is None'}")
    
    def _get_party(self):
        """パーティ情報を取得"""
        try:
            # FacilityControllerからパーティ情報を取得
            if hasattr(self.controller, 'get_party'):
                return self.controller.get_party()
            
            # フォールバック：直接_partyアクセス
            if hasattr(self.controller, '_party') and self.controller._party:
                return self.controller._party
            
            return None
        except Exception as e:
            logger.warning(f"Failed to get party: {e}")
            return None
    
    def _organize_items_by_owner(self) -> None:
        """所有者ごとにアイテムを整理"""
        self.items_by_owner = {}
        
        logger.debug(f"SellPanel: Organizing {len(self.sellable_items)} items by owner")
        
        for item in self.sellable_items:
            # owner_idが存在しない場合のエラー処理を追加
            if "owner_id" not in item:
                logger.warning(f"SellPanel: Item missing owner_id: {item}")
                continue
                
            owner_id = item["owner_id"]
            if owner_id not in self.items_by_owner:
                self.items_by_owner[owner_id] = []
            self.items_by_owner[owner_id].append(item)
        
        logger.debug(f"SellPanel: Items organized by {len(self.items_by_owner)} owners")
    
    def _update_owner_list(self) -> None:
        """所有者リストを更新"""
        if not self.owner_list:
            return
        
        # パーティメンバーを常に表示
        if not self.party:
            self.owner_list.set_item_list(["パーティが存在しません"])
            self.owner_ids = []
            return
        
        # 所有者リストを構築
        owner_names = []
        owner_ids = []
        
        # パーティ共有インベントリを最初に追加
        owner_names.append("共有アイテム")
        owner_ids.append("party")
        
        # 生きているパーティメンバーを所有者として表示
        if hasattr(self.party, 'members'):
            try:
                members = list(self.party.members) if self.party.members else []
                for member in members:
                    if hasattr(member, 'is_alive') and member.is_alive():
                        owner_names.append(member.name)
                        owner_ids.append(member.character_id)
            except (TypeError, AttributeError) as e:
                logger.warning(f"SellPanel: Error accessing party members: {e}")
        
        logger.debug(f"SellPanel: 所有者リストを更新: {owner_names}")
        
        # 所有者リストを更新
        self.owner_list.set_item_list(owner_names)
        self.owner_ids = owner_ids
        
        # 初期選択を設定（共有アイテムを最初に選択）
        if owner_names:
            # pygame_gui 0.6.x では set_selection メソッドが存在しないため、手動で設定
            self.selected_owner = owner_ids[0]
            logger.debug(f"SellPanel: 初期選択を設定: {self.selected_owner}")
            self._update_item_list()
    
    def _update_item_list(self) -> None:
        """アイテムリストを更新"""
        if not self.item_list or not self.selected_owner:
            if self.item_list:
                self.item_list.set_item_list([])
            return
        
        # 選択された所有者のアイテムを表示
        items = self.items_by_owner.get(self.selected_owner, [])
        self.displayed_items = items
        
        logger.debug(f"SellPanel: 所有者 '{self.selected_owner}' のアイテム数: {len(items)}")
        
        if not items:
            # アイテムがない場合のメッセージ
            logger.debug(f"SellPanel: 所有者 '{self.selected_owner}' のアイテムがありません")
            self.item_list.set_item_list(["売却可能なアイテムがありません"])
            self.selected_item = None
            self._update_detail_view()
            self._update_controls()
            return
        
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
        
        logger.debug(f"SellPanel: アイテムリストを更新: {item_strings}")
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
            # アイテムがない場合、状況に応じたメッセージを表示
            if not self.sellable_items:
                self.detail_box.html_text = "売却可能なアイテムがありません。<br><br>アイテムを取得してからお越しください。"
            else:
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
                logger.debug(f"SellPanel: Owner selection changed to: {selection}")
                
                if selection is not None:
                    # 安全にインデックスを取得 - 文字列と辞書両方に対応
                    indices = []
                    for i, item in enumerate(self.owner_list.item_list):
                        if isinstance(item, dict):
                            if item.get('text') == selection:
                                indices.append(i)
                        elif isinstance(item, str):
                            if item == selection:
                                indices.append(i)
                    
                    if indices and indices[0] < len(self.owner_ids):
                        self.selected_owner = self.owner_ids[indices[0]]
                        logger.debug(f"SellPanel: Owner changed to: {self.selected_owner}")
                        self._update_item_list()
                    else:
                        self.selected_owner = None
                        logger.warning(f"SellPanel: Invalid owner selection index")
                else:
                    self.selected_owner = None
                    logger.debug(f"SellPanel: Owner selection cleared")
                    self._update_item_list()
                
                return True
                
            elif event.ui_element == self.item_list:
                # アイテムが選択された
                selection = self.item_list.get_single_selection()
                if selection is not None:
                    # 「売却可能なアイテムがありません」メッセージの場合は無視
                    if selection == "売却可能なアイテムがありません":
                        self.selected_item = None
                        self._update_detail_view()
                        self._update_controls()
                        return True
                    
                    # 安全にインデックスを取得 - 文字列と辞書両方に対応
                    indices = []
                    for i, item in enumerate(self.item_list.item_list):
                        if isinstance(item, dict):
                            if item.get('text') == selection:
                                indices.append(i)
                        elif isinstance(item, str):
                            if item == selection:
                                indices.append(i)
                    if indices and indices[0] < len(self.displayed_items):
                        self.selected_item = self.displayed_items[indices[0]]
                        self._update_detail_view()
                        self._update_controls()
                    else:
                        self.selected_item = None
                else:
                    self.selected_item = None
                    self._update_detail_view()
                    self._update_controls()
                
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