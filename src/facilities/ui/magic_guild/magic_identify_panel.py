"""魔法鑑定パネル"""

import pygame
import pygame_gui
from typing import Dict, Any, Optional, List
import logging

logger = logging.getLogger(__name__)


class MagicIdentifyPanel:
    """魔法鑑定パネル
    
    未知の魔法アイテムを鑑定するパネル。
    """
    
    def __init__(self, rect: pygame.Rect, parent: pygame_gui.elements.UIPanel,
                 ui_manager: pygame_gui.UIManager, controller, service):
        """初期化"""
        self.rect = rect
        self.parent = parent
        self.ui_manager = ui_manager
        self.controller = controller
        self.service = service
        
        # UI要素
        self.container: Optional[pygame_gui.elements.UIPanel] = None
        self.title_label: Optional[pygame_gui.elements.UILabel] = None
        self.items_list: Optional[pygame_gui.elements.UISelectionList] = None
        self.identify_button: Optional[pygame_gui.elements.UIButton] = None
        self.cost_label: Optional[pygame_gui.elements.UILabel] = None
        self.gold_label: Optional[pygame_gui.elements.UILabel] = None
        self.result_box: Optional[pygame_gui.elements.UITextBox] = None
        
        # 状態
        self.selected_item: Optional[str] = None
        self.items_data: List[Dict[str, Any]] = []
        
        self._create_ui()
        self._refresh_items()
    
    def _create_ui(self) -> None:
        """UI要素を作成"""
        self.container = pygame_gui.elements.UIPanel(
            relative_rect=self.rect,
            manager=self.ui_manager,
            container=self.parent
        )
        
        # タイトル
        self.title_label = pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect(10, 10, 300, 30),
            text="魔法鑑定 - 鑑定するアイテムを選択",
            manager=self.ui_manager,
            container=self.container
        )
        
        # アイテムリスト
        self.items_list = pygame_gui.elements.UISelectionList(
            relative_rect=pygame.Rect(10, 50, 400, 180),
            item_list=[],
            manager=self.ui_manager,
            container=self.container
        )
        
        # 鑑定ボタン
        self.identify_button = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect(10, 240, 100, 30),
            text="鑑定",
            manager=self.ui_manager,
            container=self.container
        )
        self.identify_button.disable()
        
        # コスト表示
        self.cost_label = pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect(120, 240, 150, 30),
            text=f"費用: {self.service.identify_magic_cost} G",
            manager=self.ui_manager,
            container=self.container
        )
        
        # 所持金表示
        self.gold_label = pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect(280, 240, 130, 30),
            text="所持金: 0 G",
            manager=self.ui_manager,
            container=self.container
        )
        
        # 結果表示ボックス
        self.result_box = pygame_gui.elements.UITextBox(
            html_text="",
            relative_rect=pygame.Rect(10, 280, 400, 120),
            manager=self.ui_manager,
            container=self.container
        )
    
    def _refresh_items(self) -> None:
        """アイテムリストを更新"""
        # 未鑑定アイテムを取得
        result = self.service.execute_action("identify_magic", {})
        
        if result.success and result.data:
            self.items_data = result.data.get("items", [])
            party_gold = result.data.get("party_gold", 0)
            
            # リスト項目を作成
            item_items = []
            for item in self.items_data:
                item_text = f"{item['name']} (所持者: {item['holder']})"
                item_items.append(item_text)
            
            # UIリストを更新
            self.items_list.set_item_list(item_items)
            
            # 所持金を更新
            self.gold_label.set_text(f"所持金: {party_gold} G")
            
            # 結果メッセージを更新
            if result.message:
                self.result_box.html_text = result.message
                self.result_box.rebuild()
        else:
            self.items_list.set_item_list([])
            message = result.message if result.message else "鑑定が必要なアイテムはありません"
            self.result_box.html_text = message
            self.result_box.rebuild()
    
    def handle_event(self, event: pygame.event.Event) -> None:
        """イベントを処理"""
        if event.type == pygame_gui.UI_SELECTION_LIST_NEW_SELECTION:
            if event.ui_element == self.items_list:
                # アイテムが選択された
                selection_index = self.items_list.get_single_selection()
                if selection_index is not None and selection_index < len(self.items_data):
                    selected_item = self.items_data[selection_index]
                    self.selected_item = selected_item["id"]
                    
                    # 鑑定ボタンを有効化
                    self.identify_button.enable()
                    
                    # 結果をクリア
                    self.result_box.html_text = ""
                    self.result_box.rebuild()
        
        elif event.type == pygame_gui.UI_BUTTON_PRESSED:
            if event.ui_element == self.identify_button:
                self._perform_identify()
    
    def _perform_identify(self) -> None:
        """鑑定を実行"""
        if not self.selected_item:
            return
        
        # 確認
        result = self.service.execute_action("identify_magic", {
            "item_id": self.selected_item
        })
        
        if result.success and result.result_type.name == "CONFIRM":
            # 確認後実行
            result = self.service.execute_action("identify_magic", {
                "item_id": self.selected_item,
                "confirmed": True
            })
            
            # 結果を表示
            if result.success:
                result_text = f"""
                <b>鑑定結果</b><br>
                <br>
                {result.message}<br>
                <br>
                <i>残り所持金: {result.data.get('remaining_gold', 0)} G</i>
                """
                self.result_box.html_text = result_text.strip()
            else:
                self.result_box.html_text = f"<font color='#FF0000'>{result.message}</font>"
            
            self.result_box.rebuild()
            
            if result.success:
                # 成功時はリストを更新
                self._refresh_items()
                self.selected_item = None
                self.identify_button.disable()
        else:
            # エラーメッセージを表示
            self.result_box.html_text = f"<font color='#FF0000'>{result.message}</font>"
            self.result_box.rebuild()
    
    def refresh(self) -> None:
        """パネルをリフレッシュ"""
        self._refresh_items()
        self.selected_item = None
        self.identify_button.disable()
        self.result_box.html_text = ""
        self.result_box.rebuild()
    
    def show(self) -> None:
        """パネルを表示"""
        if self.container:
            self.container.show()
    
    def hide(self) -> None:
        """パネルを非表示"""
        if self.container:
            self.container.hide()
    
    def destroy(self) -> None:
        """パネルを破棄"""
        if self.container:
            self.container.kill()