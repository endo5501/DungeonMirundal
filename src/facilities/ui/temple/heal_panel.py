"""治療パネル"""

import pygame
import pygame_gui
from typing import Dict, Any, Optional, List
import logging

logger = logging.getLogger(__name__)


class HealPanel:
    """治療パネル
    
    負傷したキャラクターの治療を行うパネル。
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
        self.members_list: Optional[pygame_gui.elements.UISelectionList] = None
        self.heal_button: Optional[pygame_gui.elements.UIButton] = None
        self.cost_label: Optional[pygame_gui.elements.UILabel] = None
        self.gold_label: Optional[pygame_gui.elements.UILabel] = None
        self.result_label: Optional[pygame_gui.elements.UILabel] = None
        
        # 状態
        self.selected_member: Optional[str] = None
        self.members_data: List[Dict[str, Any]] = []
        
        self._create_ui()
        self._refresh_members()
    
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
            text="治療 - 負傷したメンバーを選択してください",
            manager=self.ui_manager,
            container=self.container
        )
        
        # メンバーリスト
        self.members_list = pygame_gui.elements.UISelectionList(
            relative_rect=pygame.Rect(10, 50, 400, 200),
            item_list=[],
            manager=self.ui_manager,
            container=self.container
        )
        
        # 治療ボタン
        self.heal_button = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect(10, 260, 100, 30),
            text="治療",
            manager=self.ui_manager,
            container=self.container
        )
        self.heal_button.disable()
        
        # コスト表示
        self.cost_label = pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect(120, 260, 200, 30),
            text="費用: -",
            manager=self.ui_manager,
            container=self.container
        )
        
        # 所持金表示
        self.gold_label = pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect(10, 300, 200, 30),
            text="所持金: 0 G",
            manager=self.ui_manager,
            container=self.container
        )
        
        # 結果表示
        self.result_label = pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect(10, 340, 400, 30),
            text="",
            manager=self.ui_manager,
            container=self.container
        )
    
    def _refresh_members(self) -> None:
        """メンバーリストを更新"""
        # 治療可能なメンバーを取得
        result = self.service.execute_action("heal", {})
        
        if result.success and result.data:
            self.members_data = result.data.get("members", [])
            party_gold = result.data.get("party_gold", 0)
            
            # リスト項目を作成
            member_items = []
            for member in self.members_data:
                item_text = f"{member['name']} (Lv.{member['level']}) - HP: {member['hp']} - {member['cost']} G"
                member_items.append(item_text)
            
            # UIリストを更新
            self.members_list.set_item_list(member_items)
            
            # 所持金を更新
            self.gold_label.set_text(f"所持金: {party_gold} G")
            
            # 結果メッセージを更新
            if result.message:
                self.result_label.set_text(result.message)
        else:
            self.members_list.set_item_list([])
            self.result_label.set_text(result.message if result.message else "治療が必要なメンバーはいません")
    
    def handle_event(self, event: pygame.event.Event) -> None:
        """イベントを処理"""
        if event.type == pygame_gui.UI_SELECTION_LIST_NEW_SELECTION:
            if event.ui_element == self.members_list:
                # メンバーが選択された
                selection_index = self.members_list.get_single_selection()
                if selection_index is not None and selection_index < len(self.members_data):
                    selected_member = self.members_data[selection_index]
                    self.selected_member = selected_member["id"]
                    
                    # コスト表示を更新
                    self.cost_label.set_text(f"費用: {selected_member['cost']} G")
                    
                    # 治療ボタンを有効化
                    self.heal_button.enable()
                    
                    # 結果をクリア
                    self.result_label.set_text("")
        
        elif event.type == pygame_gui.UI_BUTTON_PRESSED:
            if event.ui_element == self.heal_button:
                self._perform_heal()
    
    def _perform_heal(self) -> None:
        """治療を実行"""
        if not self.selected_member:
            return
        
        # 確認
        result = self.service.execute_action("heal", {
            "character_id": self.selected_member
        })
        
        if result.success and result.result_type.name == "CONFIRM":
            # 確認後実行
            result = self.service.execute_action("heal", {
                "character_id": self.selected_member,
                "confirmed": True
            })
            
            # 結果を表示
            self.result_label.set_text(result.message)
            
            if result.success:
                # 成功時はリストを更新
                self._refresh_members()
                self.selected_member = None
                self.heal_button.disable()
                self.cost_label.set_text("費用: -")
        else:
            # エラーメッセージを表示
            self.result_label.set_text(result.message)
    
    def refresh(self) -> None:
        """パネルをリフレッシュ"""
        self._refresh_members()
        self.selected_member = None
        self.heal_button.disable()
        self.cost_label.set_text("費用: -")
        self.result_label.set_text("")
    
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