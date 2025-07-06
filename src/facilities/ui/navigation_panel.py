"""ナビゲーションパネル"""

import pygame
import pygame_gui
from typing import List, Optional, Callable, Dict, Any
import logging
from ..core.facility_service import MenuItem

logger = logging.getLogger(__name__)


class NavigationPanel:
    """ナビゲーションパネル
    
    施設内の各サービスへのナビゲーションを提供するタブ形式のパネル。
    """
    
    def __init__(self, rect: pygame.Rect, parent: pygame_gui.elements.UIPanel,
                 menu_items: List[MenuItem], on_select_callback: Callable[[str], None],
                 ui_manager: pygame_gui.UIManager):
        """初期化
        
        Args:
            rect: パネルの矩形領域
            parent: 親パネル
            menu_items: メニュー項目のリスト
            on_select_callback: 項目選択時のコールバック
            ui_manager: UIマネージャー
        """
        self.rect = rect
        self.parent = parent
        self.menu_items = menu_items
        self.on_select_callback = on_select_callback
        self.ui_manager = ui_manager
        
        # UI要素
        self.container: Optional[pygame_gui.elements.UIPanel] = None
        self.nav_buttons: Dict[str, pygame_gui.elements.UIButton] = {}
        self.selected_item_id: Optional[str] = None
        
        # スタイル設定
        self.button_height = 40
        self.button_spacing = 5
        self.button_padding = 10
        
        # UI作成
        self._create_ui()
        
        logger.info("NavigationPanel created")
    
    def _create_ui(self) -> None:
        """UI要素を作成"""
        # コンテナパネル
        self.container = pygame_gui.elements.UIPanel(
            relative_rect=self.rect,
            manager=self.ui_manager,
            container=self.parent,
            element_id="navigation_panel"
        )
        
        # ナビゲーションボタンを作成
        self._create_nav_buttons()
    
    def _create_nav_buttons(self) -> None:
        """ナビゲーションボタンを作成"""
        # ボタンの合計幅を計算
        total_buttons = len(self.menu_items)
        logger.info(f"NavigationPanel: Creating {total_buttons} navigation buttons")
        if total_buttons == 0:
            logger.warning("NavigationPanel: No menu items to create buttons for")
            return
        
        # 横並びレイアウト
        available_width = self.rect.width - 2 * self.button_padding
        button_width = (available_width - (total_buttons - 1) * self.button_spacing) // total_buttons
        
        # 最小/最大幅の制限
        button_width = max(80, min(150, button_width))
        
        # 中央揃えのための開始位置を計算
        total_width = total_buttons * button_width + (total_buttons - 1) * self.button_spacing
        start_x = (self.rect.width - total_width) // 2
        
        # ボタンを作成
        for i, item in enumerate(self.menu_items):
            x = start_x + i * (button_width + self.button_spacing)
            y = (self.rect.height - self.button_height) // 2
            
            button_rect = pygame.Rect(x, y, button_width, self.button_height)
            
            # ボタンのスタイルを決定
            button_style = self._get_button_style(item)
            
            button = pygame_gui.elements.UIButton(
                relative_rect=button_rect,
                text=item.label,
                manager=self.ui_manager,
                container=self.container,
                object_id=button_style['object_id'],
                tool_tip_text=item.description
            )
            
            # 無効化処理
            if not item.enabled:
                button.disable()
            
            # カスタム属性として項目IDを保存
            button.item_id = item.id
            
            self.nav_buttons[item.id] = button
            logger.info(f"NavigationPanel: Created button '{item.label}' at ({x}, {y}) size ({button_width}, {self.button_height})")
        
        logger.info(f"NavigationPanel: Successfully created {len(self.nav_buttons)} buttons")
    
    def _get_button_style(self, item: MenuItem) -> Dict[str, str]:
        """ボタンのスタイルを取得
        
        Args:
            item: メニュー項目
            
        Returns:
            スタイル辞書
        """
        # 特別な項目のスタイル
        if item.id == "exit":
            return {'object_id': '#exit_button'}
        elif item.service_type == "wizard":
            return {'object_id': '#wizard_button'}
        else:
            return {'object_id': '#nav_button'}
    
    def set_selected(self, item_id: str) -> None:
        """選択状態を設定
        
        Args:
            item_id: 選択する項目のID
        """
        # 前の選択を解除
        if self.selected_item_id and self.selected_item_id in self.nav_buttons:
            self._update_button_selected_state(self.selected_item_id, False)
        
        # 新しい選択を設定
        if item_id in self.nav_buttons:
            self.selected_item_id = item_id
            self._update_button_selected_state(item_id, True)
    
    def _update_button_selected_state(self, item_id: str, selected: bool) -> None:
        """ボタンの選択状態を更新
        
        Args:
            item_id: 項目ID
            selected: 選択状態
        """
        button = self.nav_buttons.get(item_id)
        if button:
            # 選択状態の視覚的表現（pygame_guiのテーマで制御）
            if selected:
                button.selected = True
                # 選択時のスタイルクラスを追加
                if hasattr(button, 'add_class'):
                    button.add_class('selected')
            else:
                button.selected = False
                # 選択時のスタイルクラスを削除
                if hasattr(button, 'remove_class'):
                    button.remove_class('selected')
    
    def update_menu_items(self, menu_items: List[MenuItem]) -> None:
        """メニュー項目を更新
        
        Args:
            menu_items: 新しいメニュー項目のリスト
        """
        # 既存のボタンを破棄
        for button in self.nav_buttons.values():
            button.kill()
        self.nav_buttons.clear()
        
        # 新しいメニュー項目を設定
        self.menu_items = menu_items
        
        # ボタンを再作成
        self._create_nav_buttons()
        
        # 選択状態を復元
        if self.selected_item_id and self.selected_item_id in self.nav_buttons:
            self.set_selected(self.selected_item_id)
    
    def handle_button_click(self, event: pygame.event.Event) -> bool:
        """ボタンクリックイベントを処理
        
        Args:
            event: pygameイベント
            
        Returns:
            処理したらTrue
        """
        if event.type == pygame_gui.UI_BUTTON_PRESSED:
            logger.info(f"NavigationPanel: UI_BUTTON_PRESSED event detected")
            # クリックされたボタンを特定
            for item_id, button in self.nav_buttons.items():
                if event.ui_element == button:
                    logger.info(f"NavigationPanel: Button clicked - {item_id}")
                    # 無効なボタンはクリックできない
                    if not button.is_enabled:
                        logger.warning(f"NavigationPanel: Button {item_id} is disabled")
                        return False
                    
                    # コールバックを呼び出し
                    if self.on_select_callback:
                        logger.info(f"NavigationPanel: Calling callback for {item_id}")
                        self.on_select_callback(item_id)
                    else:
                        logger.warning("NavigationPanel: No callback set")
                    
                    # exitボタン以外は選択状態を更新
                    if item_id != "exit":
                        self.set_selected(item_id)
                    
                    return True
            logger.warning("NavigationPanel: UI_BUTTON_PRESSED but no matching button found")
        
        return False
    
    def get_selected_item_id(self) -> Optional[str]:
        """現在選択されている項目IDを取得
        
        Returns:
            選択中の項目ID（ない場合None）
        """
        return self.selected_item_id
    
    def destroy(self) -> None:
        """パネルを破棄"""
        # すべてのボタンを破棄
        for button in self.nav_buttons.values():
            button.kill()
        self.nav_buttons.clear()
        
        # コンテナを破棄
        if self.container:
            self.container.kill()
        
        logger.info("NavigationPanel destroyed")