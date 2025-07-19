"""祝福パネル"""

import pygame
import pygame_gui
from typing import Dict, Any, Optional
import logging
from ..service_panel import ServicePanel

logger = logging.getLogger(__name__)


class BlessingPanel(ServicePanel):
    """祝福パネル
    
    パーティに祝福を与えるパネル。
    """
    
    def __init__(self, rect: pygame.Rect, parent: pygame_gui.elements.UIPanel,
                 controller, ui_manager: pygame_gui.UIManager):
        """初期化"""
        super().__init__(rect, parent, controller, "blessing", ui_manager)
        
        # UI要素
        self.title_label: Optional[pygame_gui.elements.UILabel] = None
        self.description_box: Optional[pygame_gui.elements.UITextBox] = None
        self.blessing_button: Optional[pygame_gui.elements.UIButton] = None
        self.cost_label: Optional[pygame_gui.elements.UILabel] = None
        self.gold_label: Optional[pygame_gui.elements.UILabel] = None
        self.result_label: Optional[pygame_gui.elements.UILabel] = None
        
        logger.info("BlessingPanel initialized")
    
    def _create_ui(self) -> None:
        """UI要素を作成"""
        self._create_header()
        self._create_description()
        self._create_action_controls()
        self._create_status_display()
        
        # 初期データを読み込み
        self._refresh_info()
    
    def _create_header(self) -> None:
        """ヘッダーを作成"""
        # タイトル
        title_rect = pygame.Rect(10, 10, 300, 30)
        if self.ui_element_manager and not self.ui_element_manager.is_destroyed:
            self.title_label = self.ui_element_manager.create_label(
                "title_label", "祝福 - パーティに神の加護を", title_rect
            )
        else:
            # フォールバック
            self.title_label = pygame_gui.elements.UILabel(
                relative_rect=title_rect,
                text="祝福 - パーティに神の加護を",
                manager=self.ui_manager,
                container=self.container
            )
            self.ui_elements.append(self.title_label)
    
    def _create_description(self) -> None:
        """説明エリアを作成"""
        # 説明
        description_text = """
        <b>祝福の効果:</b><br>
        • 次の戦闘で攻撃力・防御力が上昇<br>
        • クリティカル率が向上<br>
        • 状態異常に対する抵抗力が上昇<br>
        • 効果は1回の戦闘まで持続<br><br>
        
        <i>神の加護により、パーティは一時的に<br>
        強力な力を得ることができます。</i>
        """
        
        description_rect = pygame.Rect(10, 50, 400, 200)
        if self.ui_element_manager and not self.ui_element_manager.is_destroyed:
            self.description_box = self.ui_element_manager.create_text_box(
                "description_box", description_text, description_rect
            )
        else:
            # フォールバック
            self.description_box = pygame_gui.elements.UITextBox(
                html_text=description_text,
                relative_rect=description_rect,
                manager=self.ui_manager,
                container=self.container
            )
            self.ui_elements.append(self.description_box)
    
    def _create_action_controls(self) -> None:
        """アクションコントロールを作成"""
        # 祝福ボタン
        button_rect = pygame.Rect(10, 260, 120, 30)
        if self.ui_element_manager and not self.ui_element_manager.is_destroyed:
            self.blessing_button = self.ui_element_manager.create_button(
                "blessing_button", "祝福を受ける", button_rect
            )
        else:
            # フォールバック
            self.blessing_button = pygame_gui.elements.UIButton(
                relative_rect=button_rect,
                text="祝福を受ける",
                manager=self.ui_manager,
                container=self.container
            )
            self.ui_elements.append(self.blessing_button)
        
        # コスト表示
        cost_rect = pygame.Rect(140, 260, 200, 30)
        if self.ui_element_manager and not self.ui_element_manager.is_destroyed:
            self.cost_label = self.ui_element_manager.create_label(
                "cost_label", "費用: 500 G", cost_rect
            )
        else:
            # フォールバック
            self.cost_label = pygame_gui.elements.UILabel(
                relative_rect=cost_rect,
                text="費用: 500 G",
                manager=self.ui_manager,
                container=self.container
            )
            self.ui_elements.append(self.cost_label)
    
    def _create_status_display(self) -> None:
        """ステータス表示エリアを作成"""
        # 所持金表示
        gold_rect = pygame.Rect(10, 300, 200, 30)
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
        
        # 結果表示
        result_rect = pygame.Rect(10, 340, 400, 30)
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
    
    def _refresh_info(self) -> None:
        """情報を更新"""
        if self.controller and self.controller.service.party:
            party_gold = self.controller.service.party.gold
            self.gold_label.set_text(f"所持金: {party_gold} G")
            
            # 祝福費用
            blessing_cost = getattr(self.controller.service, 'blessing_cost', 500)
            self.cost_label.set_text(f"費用: {blessing_cost} G")
            
            # ボタンの有効/無効
            if party_gold >= blessing_cost:
                self.blessing_button.enable()
            else:
                self.blessing_button.disable()
                self.result_label.set_text("祝福の費用が不足しています")
        else:
            self.gold_label.set_text("所持金: 0 G")
            self.blessing_button.disable()
            self.result_label.set_text("パーティが存在しません")
    
    def handle_button_click(self, button: pygame_gui.elements.UIButton) -> bool:
        """ボタンクリックを処理"""
        if button == self.blessing_button:
            self._perform_blessing()
            return True
        return False
    
    def _perform_blessing(self) -> None:
        """祝福を実行"""
        # 確認
        result = self._execute_service_action("blessing", {})
        
        if result.success and hasattr(result, 'result_type') and result.result_type.name == "CONFIRM":
            # 確認後実行
            result = self._execute_service_action("blessing", {
                "confirmed": True
            })
            
            # 結果を表示
            self.result_label.set_text(result.message)
            
            if result.success:
                # 成功時は情報を更新
                self._refresh_info()
        else:
            # エラーメッセージを表示
            self.result_label.set_text(result.message)
    
    def refresh(self) -> None:
        """パネルをリフレッシュ"""
        self._refresh_info()
        self.result_label.set_text("")