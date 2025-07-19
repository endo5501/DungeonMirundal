"""蘇生パネル"""

import pygame
import pygame_gui
from typing import Dict, Any, Optional, List
import logging
from ..service_panel import ServicePanel

logger = logging.getLogger(__name__)


class ResurrectPanel(ServicePanel):
    """蘇生パネル
    
    死亡したキャラクターの蘇生を行うパネル。
    """
    
    def __init__(self, rect: pygame.Rect, parent: pygame_gui.elements.UIPanel,
                 controller, ui_manager: pygame_gui.UIManager):
        """初期化"""
        super().__init__(rect, parent, controller, "resurrect", ui_manager)
        
        # UI要素
        self.title_label: Optional[pygame_gui.elements.UILabel] = None
        self.members_list: Optional[pygame_gui.elements.UISelectionList] = None
        self.resurrect_button: Optional[pygame_gui.elements.UIButton] = None
        self.cost_label: Optional[pygame_gui.elements.UILabel] = None
        self.gold_label: Optional[pygame_gui.elements.UILabel] = None
        self.vitality_label: Optional[pygame_gui.elements.UILabel] = None
        self.result_label: Optional[pygame_gui.elements.UILabel] = None
        
        # 状態
        self.selected_member: Optional[str] = None
        self.members_data: List[Dict[str, Any]] = []
        
        logger.info("ResurrectPanel initialized")
    
    def _create_ui(self) -> None:
        """UI要素を作成"""
        self._create_header()
        self._create_member_list()
        self._create_action_controls()
        self._create_status_display()
        
        # 初期データを読み込み
        self._refresh_members()
    
    def _create_header(self) -> None:
        """ヘッダーを作成"""
        # タイトル
        title_rect = pygame.Rect(10, 10, 300, 30)
        if self.ui_element_manager and not self.ui_element_manager.is_destroyed:
            self.title_label = self.ui_element_manager.create_label(
                "title_label", "蘇生 - 死亡したメンバーを選択してください", title_rect
            )
        else:
            # フォールバック
            self.title_label = pygame_gui.elements.UILabel(
                relative_rect=title_rect,
                text="蘇生 - 死亡したメンバーを選択してください",
                manager=self.ui_manager,
                container=self.container
            )
            self.ui_elements.append(self.title_label)
    
    def _create_member_list(self) -> None:
        """メンバーリストを作成"""
        # メンバーリスト
        list_rect = pygame.Rect(10, 50, 400, 180)
        if self.ui_element_manager and not self.ui_element_manager.is_destroyed:
            self.members_list = self.ui_element_manager.create_selection_list(
                "members_list", [], list_rect
            )
        else:
            # フォールバック
            self.members_list = pygame_gui.elements.UISelectionList(
                relative_rect=list_rect,
                item_list=[],
                manager=self.ui_manager,
                container=self.container
            )
            self.ui_elements.append(self.members_list)
    
    def _create_action_controls(self) -> None:
        """アクションコントロールを作成"""
        # 蘇生ボタン
        button_rect = pygame.Rect(10, 240, 100, 30)
        if self.ui_element_manager and not self.ui_element_manager.is_destroyed:
            self.resurrect_button = self.ui_element_manager.create_button(
                "resurrect_button", "蘇生", button_rect
            )
        else:
            # フォールバック
            self.resurrect_button = pygame_gui.elements.UIButton(
                relative_rect=button_rect,
                text="蘇生",
                manager=self.ui_manager,
                container=self.container
            )
            self.ui_elements.append(self.resurrect_button)
        
        self.resurrect_button.disable()
        
        # コスト表示
        cost_rect = pygame.Rect(120, 240, 200, 30)
        if self.ui_element_manager and not self.ui_element_manager.is_destroyed:
            self.cost_label = self.ui_element_manager.create_label(
                "cost_label", "費用: -", cost_rect
            )
        else:
            # フォールバック
            self.cost_label = pygame_gui.elements.UILabel(
                relative_rect=cost_rect,
                text="費用: -",
                manager=self.ui_manager,
                container=self.container
            )
            self.ui_elements.append(self.cost_label)
    
    def _create_status_display(self) -> None:
        """ステータス表示エリアを作成"""
        # 所持金表示
        gold_rect = pygame.Rect(10, 280, 200, 30)
        if self.ui_element_manager and not self.ui_element_manager.is_destroyed:
            self.gold_label = self.ui_element_manager.create_label(
                "gold_label", "所持金: 0 G", gold_rect
            )
        else:
            # フォールバック
            self.gold_label = pygame_gui.elements.UILabel(
                relative_rect=gold_rect,
                text="所持金: 0 G",
                manager=self.ui_manager,
                container=self.container
            )
            self.ui_elements.append(self.gold_label)
        
        # 生命力表示
        vitality_rect = pygame.Rect(220, 280, 200, 30)
        if self.ui_element_manager and not self.ui_element_manager.is_destroyed:
            self.vitality_label = self.ui_element_manager.create_label(
                "vitality_label", "生命力: -", vitality_rect
            )
        else:
            # フォールバック
            self.vitality_label = pygame_gui.elements.UILabel(
                relative_rect=vitality_rect,
                text="生命力: -",
                manager=self.ui_manager,
                container=self.container
            )
            self.ui_elements.append(self.vitality_label)
        
        # 結果表示
        result_rect = pygame.Rect(10, 320, 400, 30)
        if self.ui_element_manager and not self.ui_element_manager.is_destroyed:
            self.result_label = self.ui_element_manager.create_label(
                "result_label", "", result_rect
            )
        else:
            # フォールバック
            self.result_label = pygame_gui.elements.UILabel(
                relative_rect=result_rect,
                text="",
                manager=self.ui_manager,
                container=self.container
            )
            self.ui_elements.append(self.result_label)
    
    def _refresh_members(self) -> None:
        """メンバーリストを更新"""
        # 蘇生可能なメンバーを取得
        result = self._execute_service_action("resurrect", {})
        
        if result.success and result.data:
            self.members_data = result.data.get("members", [])
            party_gold = result.data.get("party_gold", 0)
            
            # リスト項目を作成
            member_items = []
            for member in self.members_data:
                status_text = "死亡" if member["status"] == "dead" else "灰"
                item_text = f"{member['name']} (Lv.{member['level']}) - {status_text} - 生命力:{member['vitality']} - {member['cost']} G"
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
            self.result_label.set_text(result.message if result.message else "蘇生が必要なメンバーはいません")
    
    def handle_selection_list_changed(self, event: pygame.event.Event) -> bool:
        """リスト選択変更を処理"""
        if event.ui_element == self.members_list:
            # メンバーが選択された
            selection_index = self.members_list.get_single_selection()
            if selection_index is not None and selection_index < len(self.members_data):
                selected_member = self.members_data[selection_index]
                self.selected_member = selected_member["id"]
                
                # コスト表示を更新
                self.cost_label.set_text(f"費用: {selected_member['cost']} G")
                
                # 生命力表示を更新
                self.vitality_label.set_text(f"生命力: {selected_member['vitality']}")
                
                # 蘇生ボタンを有効化（生命力が0以下でない場合）
                if selected_member['vitality'] > 0:
                    self.resurrect_button.enable()
                else:
                    self.resurrect_button.disable()
                    self.result_label.set_text("生命力が尽きているため蘇生できません")
                
                # 結果をクリア（生命力チェック以外）
                if selected_member['vitality'] > 0:
                    self.result_label.set_text("")
            return True
        return False
    
    def handle_button_click(self, button: pygame_gui.elements.UIButton) -> bool:
        """ボタンクリックを処理"""
        if button == self.resurrect_button:
            self._perform_resurrect()
            return True
        return False
    
    def _perform_resurrect(self) -> None:
        """蘇生を実行"""
        if not self.selected_member:
            return
        
        # 確認
        result = self._execute_service_action("resurrect", {
            "character_id": self.selected_member
        })
        
        if result.success and hasattr(result, 'result_type') and result.result_type.name == "CONFIRM":
            # 確認後実行
            result = self._execute_service_action("resurrect", {
                "character_id": self.selected_member,
                "confirmed": True
            })
            
            # 結果を表示
            self.result_label.set_text(result.message)
            
            if result.success:
                # 成功時はリストを更新
                self._refresh_members()
                self.selected_member = None
                self.resurrect_button.disable()
                self.cost_label.set_text("費用: -")
                self.vitality_label.set_text("生命力: -")
        else:
            # エラーメッセージを表示
            self.result_label.set_text(result.message)
    
    def refresh(self) -> None:
        """パネルをリフレッシュ"""
        self._refresh_members()
        self.selected_member = None
        self.resurrect_button.disable()
        self.cost_label.set_text("費用: -")
        self.vitality_label.set_text("生命力: -")
        self.result_label.set_text("")