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
    
    def destroy(self) -> None:
        """パネルを破棄（宿屋パターンを採用した強化版）"""
        logger.info("IdentifyPanel: Starting enhanced destroy process")
        
        # 特定のUI要素を明示的に破棄（宿屋パターン）
        specific_elements = [
            self.owner_list,
            self.item_list,
            self.detail_box,
            self.identify_button,
            self.gold_label,
            self.identify_cost_label
        ]
        
        for element in specific_elements:
            if element and hasattr(element, 'kill'):
                try:
                    element.kill()
                    logger.debug(f"IdentifyPanel: Destroyed specific element {type(element).__name__}")
                except Exception as e:
                    logger.warning(f"IdentifyPanel: Failed to destroy {type(element).__name__}: {e}")
        
        # 親クラスのdestroy()を呼び出し
        super().destroy()
        
        # 参照をクリア
        self.owner_list = None
        self.item_list = None
        self.detail_box = None
        self.identify_button = None
        self.gold_label = None
        self.identify_cost_label = None
        
        # データをクリア
        self.unidentified_items.clear()
        self.items_by_owner.clear()
        self.owner_ids.clear()
        self.displayed_items.clear()
        self.selected_owner = None
        self.selected_item = None
        
        logger.info("IdentifyPanel: Enhanced destroy completed")
    
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
        title_label = self._create_label("title", "アイテム鑑定", title_rect)
        
        # 所持金表示
        gold_rect = pygame.Rect(self.rect.width - 200, 10, 190, 35)
        self.gold_label = self._create_label("gold_label", "所持金: 0 G", gold_rect)
        
        # 鑑定料金表示
        cost_rect = pygame.Rect(220, 10, 300, 35)
        self.identify_cost_label = self._create_label("identify_cost_label", f"鑑定料金: {self.identify_cost} G/個", cost_rect)
    
    def _create_lists(self) -> None:
        """リストエリアを作成"""
        # 所有者リスト
        owner_label = self._create_label("owner_label", "所有者", pygame.Rect(10, 55, 200, 25))
        
        owner_rect = pygame.Rect(10, 85, 200, 250)
        self.owner_list = self._create_selection_list("owner_list", owner_rect, [])
        
        # アイテムリスト
        item_label = self._create_label("item_label", "未鑑定アイテム", pygame.Rect(220, 55, 280, 25))
        
        item_rect = pygame.Rect(220, 85, 280, 250)
        self.item_list = self._create_selection_list("item_list", item_rect, [])
    
    def _create_detail_area(self) -> None:
        """詳細エリアを作成"""
        # 詳細表示
        detail_label = self._create_label("detail_label", "アイテム詳細", pygame.Rect(510, 55, 280, 25))
        
        detail_rect = pygame.Rect(510, 85, 280, 250)
        self.detail_box = self._create_text_box("detail_box", "アイテムを選択してください", detail_rect)
    
    def _create_identify_controls(self) -> None:
        """鑑定コントロールを作成"""
        y_position = 345
        
        # 鑑定ボタン
        identify_rect = pygame.Rect(220, y_position, 150, 35)
        self.identify_button = self._create_button(
            "identify_button",
            "鑑定する",
            identify_rect,
            container=self.container,
            object_id="#identify_button"
        )
        self.identify_button.disable()
    
    def _load_unidentified_items(self) -> None:
        """未鑑定アイテムを読み込み"""
        result = self._execute_service_action("identify", {"list_only": True})
        
        if result.is_success():
            # データが存在する場合は設定、存在しない場合は初期値を使用
            if result.data:
                self.unidentified_items = result.data.get("items", [])
                self.identify_cost = result.data.get("identify_cost", 100)
                party_gold = result.data.get("party_gold", 0)
            else:
                self.unidentified_items = []
                self.identify_cost = 100
                party_gold = 0
            
            # 鑑定料金表示を更新
            if self.identify_cost_label:
                self.identify_cost_label.set_text(f"鑑定料金: {self.identify_cost} G/個")
            
            # 所持金を更新
            self._update_gold_display(party_gold)
            
            # パーティ情報を取得
            self.party = self._get_party()
            
            # 所有者ごとにアイテムを整理
            self._organize_items_by_owner()
            
            # 所有者リストを更新
            self._update_owner_list()
        else:
            logger.warning(f"IdentifyPanel: Service failed - success: {result.is_success()}, message: {result.message}")
    
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
        
        for item in self.unidentified_items:
            owner_id = item.get("owner_id", "party")
            if owner_id not in self.items_by_owner:
                self.items_by_owner[owner_id] = []
            self.items_by_owner[owner_id].append(item)
    
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
        for member in self.party.members:
            if member.is_alive():
                owner_names.append(member.name)
                owner_ids.append(member.character_id)
        
        # 所有者リストを更新
        self.owner_list.set_item_list(owner_names)
        self.owner_ids = owner_ids
        
        # 初期選択を設定（共有アイテムを最初に選択）
        if owner_names:
            # pygame_gui 0.6.x では set_selection メソッドが存在しないため、手動で設定
            self.selected_owner = owner_ids[0]
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
        
        if not items:
            # アイテムがない場合のメッセージ
            self.item_list.set_item_list(["未鑑定アイテムがありません"])
            self.selected_item = None
            self._update_detail_view()
            self._update_controls()
            return
        
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
                    # 「未鑑定アイテムがありません」メッセージの場合は無視
                    if selection == "未鑑定アイテムがありません":
                        self.selected_item = None
                        self._update_detail_view()
                        self._update_controls()
                        return True
                    
                    indices = [i for i, item in enumerate(self.item_list.item_list) if item == selection]
                    if indices:
                        index = indices[0]
                        if 0 <= index < len(self.displayed_items):
                            self.selected_item = self.displayed_items[index]
                            self._update_detail_view()
                            self._update_controls()
                return True
        
        return False