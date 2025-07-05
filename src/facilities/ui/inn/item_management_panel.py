"""アイテム管理パネル"""

import pygame
import pygame_gui
from typing import Dict, Any, Optional, List, Tuple
import logging
from ..service_panel import ServicePanel
from ...core.service_result import ServiceResult

logger = logging.getLogger(__name__)


class ItemManagementPanel(ServicePanel):
    """アイテム管理パネル
    
    パーティメンバー間でのアイテムの移動、使用、破棄を管理する。
    """
    
    def __init__(self, rect: pygame.Rect, parent: pygame_gui.UIPanel,
                 controller, ui_manager: pygame_gui.UIManager):
        """初期化"""
        super().__init__(rect, parent, controller, "item_management", ui_manager)
        
        # UI要素
        self.back_button: Optional[pygame_gui.elements.UIButton] = None
        self.member_list: Optional[pygame_gui.elements.UISelectionList] = None
        self.item_list: Optional[pygame_gui.elements.UISelectionList] = None
        self.action_buttons: Dict[str, pygame_gui.elements.UIButton] = {}
        self.detail_box: Optional[pygame_gui.elements.UITextBox] = None
        
        # データ
        self.party_members: List[Dict[str, Any]] = []
        self.selected_member: Optional[Dict[str, Any]] = None
        self.selected_member_index: Optional[int] = None
        self.selected_item: Optional[Dict[str, Any]] = None
        self.selected_item_index: Optional[int] = None
        self.member_items: Dict[str, List[Dict[str, Any]]] = {}
        
        logger.info("ItemManagementPanel initialized")
    
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
            text="アイテム管理",
            manager=self.ui_manager,
            container=self.container
        )
        self.ui_elements.append(title_label)
        
        # レイアウト
        list_width = (self.rect.width - 40) // 3
        list_height = 250
        
        # メンバーリスト
        member_label = pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect(10, 55, list_width, 25),
            text="パーティメンバー",
            manager=self.ui_manager,
            container=self.container
        )
        self.ui_elements.append(member_label)
        
        member_rect = pygame.Rect(10, 80, list_width, list_height)
        self.member_list = pygame_gui.elements.UISelectionList(
            relative_rect=member_rect,
            item_list=[],
            manager=self.ui_manager,
            container=self.container,
            allow_multi_select=False
        )
        self.ui_elements.append(self.member_list)
        
        # アイテムリスト
        item_label = pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect(list_width + 20, 55, list_width, 25),
            text="所持アイテム",
            manager=self.ui_manager,
            container=self.container
        )
        self.ui_elements.append(item_label)
        
        item_rect = pygame.Rect(list_width + 20, 80, list_width, list_height)
        self.item_list = pygame_gui.elements.UISelectionList(
            relative_rect=item_rect,
            item_list=[],
            manager=self.ui_manager,
            container=self.container,
            allow_multi_select=False
        )
        self.ui_elements.append(self.item_list)
        
        # 詳細表示
        detail_label = pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect(2 * list_width + 30, 55, list_width, 25),
            text="アイテム詳細",
            manager=self.ui_manager,
            container=self.container
        )
        self.ui_elements.append(detail_label)
        
        detail_rect = pygame.Rect(2 * list_width + 30, 80, list_width, list_height)
        self.detail_box = pygame_gui.elements.UITextBox(
            html_text="アイテムを選択してください",
            relative_rect=detail_rect,
            manager=self.ui_manager,
            container=self.container
        )
        self.ui_elements.append(self.detail_box)
        
        # アクションボタン
        self._create_action_buttons()
        
        # 初期データを読み込み
        self._load_party_data()
    
    def _create_action_buttons(self) -> None:
        """アクションボタンを作成"""
        button_width = 100
        button_height = 35
        button_spacing = 10
        y_position = 345
        
        # ボタン定義
        actions = [
            ("transfer", "移動", "他のメンバーに渡す"),
            ("use", "使用", "アイテムを使用する"),
            ("discard", "破棄", "アイテムを捨てる")
        ]
        
        start_x = (self.rect.width - len(actions) * button_width - (len(actions) - 1) * button_spacing) // 2
        
        for i, (action_id, label, tooltip) in enumerate(actions):
            x_position = start_x + i * (button_width + button_spacing)
            button_rect = pygame.Rect(x_position, y_position, button_width, button_height)
            
            button = self._create_button(
                label,
                button_rect,
                container=self.container,
                object_id=f"#action_{action_id}",
                tool_tip_text=tooltip
            )
            
            # 初期状態は無効
            button.disable()
            self.action_buttons[action_id] = button
    
    def _load_party_data(self) -> None:
        """パーティデータを読み込み"""
        if not self.controller or not self.controller.service.party:
            return
        
        party = self.controller.service.party
        
        # メンバーリストを構築
        self.party_members = []
        member_names = []
        
        for member in party.members:
            if member.is_alive():
                member_data = {
                    "id": member.id,
                    "name": member.name,
                    "level": member.level,
                    "class": member.char_class
                }
                self.party_members.append(member_data)
                member_names.append(f"{member.name} Lv{member.level}")
                
                # メンバーのアイテムを取得（仮実装）
                self.member_items[member.id] = self._get_member_items(member)
        
        # メンバーリストを更新
        self.member_list.set_item_list(member_names)
    
    def _get_member_items(self, member) -> List[Dict[str, Any]]:
        """メンバーのアイテムを取得（仮実装）"""
        # TODO: 実際のインベントリシステムと連携
        items = []
        
        # 仮のアイテムデータ
        if hasattr(member, 'inventory') and member.inventory:
            for item in member.inventory.get_all_items():
                items.append({
                    "id": item.id,
                    "name": item.name,
                    "type": item.item_type,
                    "quantity": getattr(item, 'quantity', 1),
                    "description": item.description,
                    "usable": item.is_usable(),
                    "value": item.value
                })
        else:
            # デモ用の仮データ
            if member.char_class == "fighter":
                items = [
                    {"id": "potion1", "name": "ポーション", "type": "consumable", 
                     "quantity": 3, "description": "HPを50回復", "usable": True, "value": 50},
                    {"id": "sword1", "name": "鉄の剣", "type": "weapon",
                     "quantity": 1, "description": "攻撃力+5", "usable": False, "value": 200}
                ]
            elif member.char_class == "mage":
                items = [
                    {"id": "ether1", "name": "エーテル", "type": "consumable",
                     "quantity": 2, "description": "MPを30回復", "usable": True, "value": 100},
                    {"id": "staff1", "name": "魔法の杖", "type": "weapon",
                     "quantity": 1, "description": "魔力+3", "usable": False, "value": 300}
                ]
        
        return items
    
    def _update_item_list(self) -> None:
        """アイテムリストを更新"""
        if not self.selected_member or not self.item_list:
            return
        
        member_id = self.selected_member["id"]
        items = self.member_items.get(member_id, [])
        
        # リストアイテムを構築
        item_names = []
        for item in items:
            if item["quantity"] > 1:
                item_names.append(f"{item['name']} x{item['quantity']}")
            else:
                item_names.append(item["name"])
        
        self.item_list.set_item_list(item_names)
        
        # 選択をクリア
        self.selected_item = None
        self.selected_item_index = None
        self._update_action_buttons()
        self._update_detail_view()
    
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
        detail_text = f"<b>{item['name']}</b><br>"
        detail_text += f"種類: {self._get_item_type_name(item['type'])}<br>"
        detail_text += f"数量: {item['quantity']}<br>"
        detail_text += f"<br>{item['description']}<br>"
        detail_text += f"<br>価値: {item['value']} G"
        
        if item['usable']:
            detail_text += "<br><font color='#00aa00'>使用可能</font>"
        
        self.detail_box.html_text = detail_text
        self.detail_box.rebuild()
    
    def _get_item_type_name(self, item_type: str) -> str:
        """アイテムタイプの表示名を取得"""
        type_names = {
            "consumable": "消費アイテム",
            "weapon": "武器",
            "armor": "防具",
            "accessory": "アクセサリー",
            "key": "重要アイテム",
            "misc": "その他"
        }
        return type_names.get(item_type, item_type)
    
    def _update_action_buttons(self) -> None:
        """アクションボタンの状態を更新"""
        has_item = self.selected_item is not None
        
        # 移動ボタン
        if "transfer" in self.action_buttons:
            # 他にメンバーがいる場合のみ有効
            can_transfer = has_item and len(self.party_members) > 1
            if can_transfer:
                self.action_buttons["transfer"].enable()
            else:
                self.action_buttons["transfer"].disable()
        
        # 使用ボタン
        if "use" in self.action_buttons:
            # 使用可能なアイテムの場合のみ有効
            can_use = has_item and self.selected_item.get("usable", False)
            if can_use:
                self.action_buttons["use"].enable()
            else:
                self.action_buttons["use"].disable()
        
        # 破棄ボタン
        if "discard" in self.action_buttons:
            # 重要アイテム以外は破棄可能
            can_discard = has_item and self.selected_item.get("type") != "key"
            if can_discard:
                self.action_buttons["discard"].enable()
            else:
                self.action_buttons["discard"].disable()
    
    def handle_button_click(self, button: pygame_gui.elements.UIButton) -> bool:
        """ボタンクリックを処理"""
        if button == self.back_button:
            # 親パネルに戻る処理を通知
            if hasattr(self.parent, 'handle_back_action'):
                self.parent.handle_back_action()
            return True
        
        # アクションボタン
        for action_id, action_button in self.action_buttons.items():
            if button == action_button:
                self._execute_action(action_id)
                return True
        
        return False
    
    def handle_selection_list_changed(self, event: pygame.event.Event) -> bool:
        """選択リスト変更イベントを処理"""
        if event.type == pygame_gui.UI_SELECTION_LIST_NEW_SELECTION:
            if event.ui_element == self.member_list:
                # メンバー選択が変更された
                selection = self.member_list.get_single_selection()
                if selection is not None:
                    self.selected_member_index = self.member_list.item_list.index(selection)
                    if 0 <= self.selected_member_index < len(self.party_members):
                        self.selected_member = self.party_members[self.selected_member_index]
                        self._update_item_list()
                    else:
                        self.selected_member = None
                else:
                    self.selected_member = None
                    self.selected_member_index = None
                    self._update_item_list()
                
                return True
                
            elif event.ui_element == self.item_list:
                # アイテム選択が変更された
                selection = self.item_list.get_single_selection()
                if selection is not None and self.selected_member:
                    self.selected_item_index = self.item_list.item_list.index(selection)
                    member_id = self.selected_member["id"]
                    items = self.member_items.get(member_id, [])
                    
                    if 0 <= self.selected_item_index < len(items):
                        self.selected_item = items[self.selected_item_index]
                    else:
                        self.selected_item = None
                else:
                    self.selected_item = None
                    self.selected_item_index = None
                
                self._update_action_buttons()
                self._update_detail_view()
                return True
        
        return False
    
    def _execute_action(self, action_id: str) -> None:
        """アクションを実行"""
        if not self.selected_item or not self.selected_member:
            return
        
        params = {
            "sub_action": "item_management",
            "action": action_id,
            "member_id": self.selected_member["id"],
            "item_id": self.selected_item["id"]
        }
        
        result = self._execute_service_action("adventure_prep", params)
        
        if result.is_success():
            self._show_message(result.message, "info")
            # データをリロード
            self._load_party_data()
            if self.selected_member:
                self._update_item_list()
        else:
            self._show_message(result.message, "error")