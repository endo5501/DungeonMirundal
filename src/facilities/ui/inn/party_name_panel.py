"""パーティ名変更パネル"""

import pygame
import pygame_gui
from typing import Dict, Any, Optional
import logging
from ..service_panel import ServicePanel
from ...core.service_result import ServiceResult

logger = logging.getLogger(__name__)


class PartyNamePanel(ServicePanel):
    """パーティ名変更パネル
    
    パーティの名前変更を行う。
    """
    
    def __init__(self, rect: pygame.Rect, parent: pygame_gui.elements.UIPanel,
                 controller, ui_manager: pygame_gui.UIManager):
        """初期化"""
        # UI要素の初期化
        self.current_name_label: Optional[pygame_gui.elements.UILabel] = None
        self.name_input: Optional[pygame_gui.elements.UITextEntryLine] = None
        self.change_button: Optional[pygame_gui.elements.UIButton] = None
        self.cancel_button: Optional[pygame_gui.elements.UIButton] = None
        self.message_label: Optional[pygame_gui.elements.UILabel] = None
        
        # 現在のパーティ名を先に設定（_create_ui()で使用するため）
        self.current_party_name = ""
        if controller and controller.service and controller.service.party:
            self.current_party_name = controller.service.party.name
        
        # 親クラスの初期化（_create_ui()が呼ばれる）
        super().__init__(rect, parent, controller, "party_name", ui_manager)
        
        logger.info("PartyNamePanel initialized")
    
    def _create_ui(self) -> None:
        """UI要素を作成"""
        # タイトル（重複を防ぐため固有IDを設定）
        title_rect = pygame.Rect(10, 10, self.rect.width - 20, 40)
        title_label = pygame_gui.elements.UILabel(
            relative_rect=title_rect,
            text="パーティ名変更",
            manager=self.ui_manager,
            container=self.container,
            object_id="#party_name_panel_title"
        )
        self.ui_elements.append(title_label)
        
        # 現在のパーティ名表示
        current_name_rect = pygame.Rect(10, 60, self.rect.width - 20, 30)
        self.current_name_label = pygame_gui.elements.UILabel(
            relative_rect=current_name_rect,
            text=f"現在のパーティ名: {self.current_party_name}",
            manager=self.ui_manager,
            container=self.container
        )
        self.ui_elements.append(self.current_name_label)
        
        # 新しい名前入力ラベル
        new_name_label_rect = pygame.Rect(10, 110, self.rect.width - 20, 30)
        new_name_label = pygame_gui.elements.UILabel(
            relative_rect=new_name_label_rect,
            text="新しいパーティ名 (1-20文字):",
            manager=self.ui_manager,
            container=self.container
        )
        self.ui_elements.append(new_name_label)
        
        # 名前入力フィールド
        name_input_rect = pygame.Rect(10, 150, self.rect.width - 20, 35)
        self.name_input = pygame_gui.elements.UITextEntryLine(
            relative_rect=name_input_rect,
            manager=self.ui_manager,
            container=self.container,
            initial_text=self.current_party_name
        )
        self.ui_elements.append(self.name_input)
        
        # ボタン
        button_y = 200
        button_width = 120
        button_spacing = 20
        
        # 変更ボタン
        change_button_rect = pygame.Rect(
            (self.rect.width - 2 * button_width - button_spacing) // 2,
            button_y,
            button_width,
            40
        )
        self.change_button = self._create_button(
            "change_button",
            "変更",
            change_button_rect,
            container=self.container,
            object_id="#change_button"
        )
        
        # キャンセルボタン
        cancel_button_rect = pygame.Rect(
            (self.rect.width - 2 * button_width - button_spacing) // 2 + button_width + button_spacing,
            button_y,
            button_width,
            40
        )
        self.cancel_button = self._create_button(
            "cancel_button",
            "キャンセル",
            cancel_button_rect,
            container=self.container,
            object_id="#cancel_button"
        )
        
        # メッセージ表示エリア
        message_rect = pygame.Rect(10, 260, self.rect.width - 20, 40)
        self.message_label = pygame_gui.elements.UILabel(
            relative_rect=message_rect,
            text="",
            manager=self.ui_manager,
            container=self.container
        )
        self.ui_elements.append(self.message_label)
    
    def destroy(self) -> None:
        """パネルを破棄（強化版）"""
        logger.info("PartyNamePanel: Starting enhanced destroy process")
        
        # 特定のUI要素を明示的に破棄
        specific_elements = [
            self.current_name_label,
            self.name_input,
            self.change_button,
            self.cancel_button,
            self.message_label
        ]
        
        for element in specific_elements:
            if element and hasattr(element, 'kill'):
                try:
                    element.kill()
                    logger.debug(f"PartyNamePanel: Destroyed specific element {type(element).__name__}")
                except Exception as e:
                    logger.warning(f"PartyNamePanel: Failed to destroy {type(element).__name__}: {e}")
        
        # 親クラスのdestroy()を呼び出し
        super().destroy()
        
        # 参照をクリア
        self.current_name_label = None
        self.instruction_label = None
        self.name_input = None
        self.change_button = None
        self.cancel_button = None
        self.message_label = None
        self.current_party_name = ""
        
        logger.info("PartyNamePanel: Enhanced destroy completed")
    
    def _show_message(self, message: str, message_type: str = "info") -> None:
        """メッセージを表示"""
        if self.message_label:
            self.message_label.set_text(message)
        logger.info(f"PartyNamePanel message ({message_type}): {message}")
    
    def _change_party_name(self) -> None:
        """パーティ名を変更"""
        if not self.name_input:
            return
        
        new_name = self.name_input.get_text().strip()
        
        if not new_name:
            self._show_message("新しいパーティ名を入力してください", "warning")
            return
        
        if new_name == self.current_party_name:
            self._show_message("現在と同じ名前です", "warning")
            return
        
        # パーティ名変更を実行
        params = {"name": new_name}
        result = self._execute_service_action("party_name", params)
        
        if result.is_success():
            self._show_message(result.message, "success")
            # 現在のパーティ名を更新
            self.current_party_name = new_name
            if self.current_name_label:
                self.current_name_label.set_text(f"現在のパーティ名: {self.current_party_name}")
        else:
            self._show_message(result.message, "error")
    
    def _cancel_change(self) -> None:
        """変更をキャンセル"""
        if self.name_input:
            self.name_input.set_text(self.current_party_name)
        self._show_message("変更をキャンセルしました", "info")
    
    def handle_button_click(self, button: pygame_gui.elements.UIButton) -> bool:
        """ボタンクリックを処理"""
        if button == self.change_button:
            self._change_party_name()
            return True
        elif button == self.cancel_button:
            self._cancel_change()
            return True
        
        return False
    
    def handle_text_entry_finished(self, event: pygame.event.Event) -> bool:
        """テキスト入力完了イベントを処理"""
        if event.type == pygame_gui.UI_TEXT_ENTRY_FINISHED:
            if event.ui_element == self.name_input:
                # Enterキーでパーティ名を変更
                self._change_party_name()
                return True
        
        return False
    
    def refresh(self) -> None:
        """パネルをリフレッシュ"""
        # 現在のパーティ名を更新
        if self.controller and self.controller.service and self.controller.service.party:
            self.current_party_name = self.controller.service.party.name
            if self.current_name_label:
                self.current_name_label.set_text(f"現在のパーティ名: {self.current_party_name}")