"""寄付パネル"""

import pygame
import pygame_gui
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


class DonationPanel:
    """寄付パネル
    
    教会への寄付を行うパネル。
    """
    
    def __init__(self, rect: pygame.Rect, parent: pygame_gui.UIPanel,
                 ui_manager: pygame_gui.UIManager, controller, service):
        """初期化"""
        self.rect = rect
        self.parent = parent
        self.ui_manager = ui_manager
        self.controller = controller
        self.service = service
        
        # UI要素
        self.container: Optional[pygame_gui.UIPanel] = None
        self.title_label: Optional[pygame_gui.elements.UILabel] = None
        self.description_box: Optional[pygame_gui.elements.UITextBox] = None
        self.amount_input: Optional[pygame_gui.elements.UITextEntryLine] = None
        self.donation_button: Optional[pygame_gui.elements.UIButton] = None
        self.preset_buttons: list = []
        self.gold_label: Optional[pygame_gui.elements.UILabel] = None
        self.result_label: Optional[pygame_gui.elements.UILabel] = None
        
        self._create_ui()
        self._refresh_info()
    
    def _create_ui(self) -> None:
        """UI要素を作成"""
        self.container = pygame_gui.UIPanel(
            relative_rect=self.rect,
            manager=self.ui_manager,
            container=self.parent
        )
        
        # タイトル
        self.title_label = pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect(10, 10, 300, 30),
            text="寄付 - 教会への献金",
            manager=self.ui_manager,
            container=self.container
        )
        
        # 説明
        description_text = """
        <b>寄付の効果:</b><br>
        • カルマ値の向上<br>
        • 神の加護による幸運の向上<br>
        • より良いアイテムの発見確率上昇<br><br>
        
        <i>慈悲深い行いは必ず報われます。<br>
        神はあなたの善行を見ておられます。</i>
        """
        
        self.description_box = pygame_gui.elements.UITextBox(
            html_text=description_text,
            relative_rect=pygame.Rect(10, 50, 400, 130),
            manager=self.ui_manager,
            container=self.container
        )
        
        # 金額入力
        amount_label = pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect(10, 190, 100, 25),
            text="金額:",
            manager=self.ui_manager,
            container=self.container
        )
        
        self.amount_input = pygame_gui.elements.UITextEntryLine(
            relative_rect=pygame.Rect(120, 190, 100, 25),
            manager=self.ui_manager,
            container=self.container
        )
        self.amount_input.set_text("0")
        
        # プリセットボタン
        preset_amounts = [100, 500, 1000, 5000]
        self.preset_buttons = []
        
        for i, amount in enumerate(preset_amounts):
            button = pygame_gui.elements.UIButton(
                relative_rect=pygame.Rect(10 + i * 90, 220, 80, 25),
                text=f"{amount} G",
                manager=self.ui_manager,
                container=self.container
            )
            self.preset_buttons.append((button, amount))
        
        # 寄付ボタン
        self.donation_button = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect(10, 260, 100, 30),
            text="寄付する",
            manager=self.ui_manager,
            container=self.container
        )
        
        # 所持金表示
        self.gold_label = pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect(120, 260, 200, 30),
            text="所持金: 0 G",
            manager=self.ui_manager,
            container=self.container
        )
        
        # 結果表示
        self.result_label = pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect(10, 300, 400, 30),
            text="",
            manager=self.ui_manager,
            container=self.container
        )
    
    def _refresh_info(self) -> None:
        """情報を更新"""
        if self.service.party:
            party_gold = self.service.party.gold
            self.gold_label.set_text(f"所持金: {party_gold} G")
            
            # ボタンの有効/無効
            if party_gold > 0:
                self.donation_button.enable()
                for button, amount in self.preset_buttons:
                    if party_gold >= amount:
                        button.enable()
                    else:
                        button.disable()
            else:
                self.donation_button.disable()
                for button, amount in self.preset_buttons:
                    button.disable()
                self.result_label.set_text("寄付する金額がありません")
        else:
            self.gold_label.set_text("所持金: 0 G")
            self.donation_button.disable()
            for button, amount in self.preset_buttons:
                button.disable()
            self.result_label.set_text("パーティが存在しません")
    
    def handle_event(self, event: pygame.event.Event) -> None:
        """イベントを処理"""
        if event.type == pygame_gui.UI_BUTTON_PRESSED:
            if event.ui_element == self.donation_button:
                self._perform_donation()
            else:
                # プリセットボタンかチェック
                for button, amount in self.preset_buttons:
                    if event.ui_element == button:
                        self.amount_input.set_text(str(amount))
                        break
    
    def _perform_donation(self) -> None:
        """寄付を実行"""
        try:
            amount = int(self.amount_input.get_text())
        except ValueError:
            self.result_label.set_text("有効な金額を入力してください")
            return
        
        if amount <= 0:
            self.result_label.set_text("寄付金額は1G以上を指定してください")
            return
        
        # 確認
        result = self.service.execute_action("donation", {
            "amount": amount
        })
        
        if result.success and result.result_type.name == "CONFIRM":
            # 確認後実行
            result = self.service.execute_action("donation", {
                "amount": amount,
                "confirmed": True
            })
            
            # 結果を表示
            self.result_label.set_text(result.message)
            
            if result.success:
                # 成功時は情報を更新
                self._refresh_info()
                self.amount_input.set_text("0")
        else:
            # エラーメッセージを表示
            self.result_label.set_text(result.message)
    
    def refresh(self) -> None:
        """パネルをリフレッシュ"""
        self._refresh_info()
        self.amount_input.set_text("0")
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