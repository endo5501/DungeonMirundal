"""祝福パネル"""

import pygame
import pygame_gui
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


class BlessingPanel:
    """祝福パネル
    
    パーティに祝福を与えるパネル。
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
        self.description_box: Optional[pygame_gui.elements.UITextBox] = None
        self.blessing_button: Optional[pygame_gui.elements.UIButton] = None
        self.cost_label: Optional[pygame_gui.elements.UILabel] = None
        self.gold_label: Optional[pygame_gui.elements.UILabel] = None
        self.result_label: Optional[pygame_gui.elements.UILabel] = None
        
        self._create_ui()
        self._refresh_info()
    
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
            text="祝福 - パーティに神の加護を",
            manager=self.ui_manager,
            container=self.container
        )
        
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
        
        self.description_box = pygame_gui.elements.UITextBox(
            html_text=description_text,
            relative_rect=pygame.Rect(10, 50, 400, 200),
            manager=self.ui_manager,
            container=self.container
        )
        
        # 祝福ボタン
        self.blessing_button = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect(10, 260, 120, 30),
            text="祝福を受ける",
            manager=self.ui_manager,
            container=self.container
        )
        
        # コスト表示
        self.cost_label = pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect(140, 260, 200, 30),
            text="費用: 500 G",
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
    
    def _refresh_info(self) -> None:
        """情報を更新"""
        if self.service.party:
            party_gold = self.service.party.gold
            self.gold_label.set_text(f"所持金: {party_gold} G")
            
            # 祝福費用
            blessing_cost = self.service.blessing_cost
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
    
    def handle_event(self, event: pygame.event.Event) -> None:
        """イベントを処理"""
        if event.type == pygame_gui.UI_BUTTON_PRESSED:
            if event.ui_element == self.blessing_button:
                self._perform_blessing()
    
    def _perform_blessing(self) -> None:
        """祝福を実行"""
        # 確認
        result = self.service.execute_action("blessing", {})
        
        if result.success and result.result_type.name == "CONFIRM":
            # 確認後実行
            result = self.service.execute_action("blessing", {
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