"""
MenuWindow クラス

一般的なメニュー表示用のウィンドウ
"""

import pygame
import pygame_gui
from typing import Dict, List, Any, Optional
from dataclasses import dataclass

from .window import Window
from .menu_layout import MenuLayout, LayoutConfig
from .back_button_manager import BackButtonManager
from .menu_button import MenuButton
from src.utils.logger import logger


class MenuWindow(Window):
    """
    メニューウィンドウクラス
    
    設定ベースのメニューUI作成と、キーボード・マウス両方の操作に対応
    """
    
    def __init__(self, window_id: str, menu_config: Dict[str, Any], 
                 parent: Optional[Window] = None, modal: bool = False):
        """
        メニューウィンドウを初期化
        
        Args:
            window_id: ウィンドウID
            menu_config: メニュー設定辞書
            parent: 親ウィンドウ
            modal: モーダルウィンドウかどうか
        """
        super().__init__(window_id, parent, modal)
        
        # 設定の検証
        self._validate_config(menu_config)
        
        self.menu_config = menu_config
        self.buttons: List[MenuButton] = []
        self.selected_button_index = 0
        self.enabled = True
        
        # スタイル設定
        self.style = menu_config.get('style', {})
        
        # レイアウト計算器
        self.layout = MenuLayout()
        
        # 戻るボタンマネージャー
        self.back_button_manager = BackButtonManager(menu_config)
        
        logger.debug(f"MenuWindowを初期化: {window_id}")
    
    def _validate_config(self, config: Dict[str, Any]) -> None:
        """メニュー設定を検証"""
        if 'buttons' not in config:
            raise ValueError("Menu config must contain 'buttons'")
        
        if not isinstance(config['buttons'], list):
            raise ValueError("Menu config 'buttons' must be a list")
        
        # BackButtonManagerが戻るボタンを自動追加するため、空のボタン配列も許可
        # if len(config['buttons']) == 0:
        #     raise ValueError("Menu config 'buttons' cannot be empty")
    
    def create(self) -> None:
        """UI要素を作成"""
        if not self.ui_manager:
            self._initialize_ui_manager()
            self._calculate_layout()
            self._create_panel()
            self._create_title_if_needed()
            self._create_buttons()
        
        logger.debug(f"MenuWindow UI要素を作成: {self.window_id}")
    
    def _initialize_ui_manager(self) -> None:
        """UIManagerを初期化"""
        # WindowManagerから共有UIManagerを取得
        from .window_manager import WindowManager
        window_manager = WindowManager.get_instance()
        
        if hasattr(window_manager, 'ui_manager') and window_manager.ui_manager:
            self.ui_manager = window_manager.ui_manager
            logger.debug(f"MenuWindow: 共有UIManagerを使用: {self.ui_manager}")
        else:
            # WindowManagerにUIManagerがない場合は新規作成
            screen_width = 1024
            screen_height = 768
            self.ui_manager = pygame_gui.UIManager((screen_width, screen_height))
            window_manager.ui_manager = self.ui_manager
            logger.debug(f"MenuWindow: 新規UIManagerを作成: {self.ui_manager}")
        
        logger.debug(f"MenuWindow: UIManager確認完了: {self.ui_manager}")
        logger.debug(f"MenuWindow: UIManagerを設定: {self.ui_manager}")
    
    def _calculate_layout(self) -> None:
        """メニューのレイアウトを計算"""
        # 元のボタン + 戻るボタン（必要な場合）の総数
        original_buttons = self.menu_config['buttons']
        additional_count = self.back_button_manager.get_additional_button_count()
        total_button_count = len(original_buttons) + additional_count
        has_title = 'title' in self.menu_config
        
        self.rect = self.layout.calculate_menu_rect(total_button_count, has_title)
    
    def _create_panel(self) -> None:
        """メニューパネルを作成"""
        self.panel = pygame_gui.elements.UIPanel(
            relative_rect=self.rect,
            manager=self.ui_manager
        )
    
    def _create_title_if_needed(self) -> None:
        """タイトルラベルを作成（必要な場合）"""
        if 'title' in self.menu_config:
            title_rect = self.layout.calculate_title_rect(self.rect)
            self.title_label = pygame_gui.elements.UILabel(
                relative_rect=title_rect,
                text=self.menu_config['title'],
                manager=self.ui_manager,
                container=self.panel
            )
    
    def _create_buttons(self) -> None:
        """ボタンを作成"""
        # 元のボタン + 戻るボタン（必要な場合）の総数
        original_buttons = self.menu_config['buttons']
        additional_count = self.back_button_manager.get_additional_button_count()
        total_button_count = len(original_buttons) + additional_count
        
        has_title = 'title' in self.menu_config
        button_rects = self.layout.calculate_button_rects(self.rect, total_button_count, has_title)
        
        # 元のボタンを作成
        for i, button_config in enumerate(original_buttons):
            button_rect = button_rects[i]
            
            # pygame-guiボタンを作成
            ui_button = pygame_gui.elements.UIButton(
                relative_rect=button_rect,
                text=button_config['text'],
                manager=self.ui_manager,
                container=self.panel
            )
            logger.debug(f"MenuWindow: ボタン作成: {button_config['text']} -> {ui_button}")
            
            # MenuButtonオブジェクトを作成
            menu_button = MenuButton(
                id=button_config['id'],
                text=button_config['text'],
                action=button_config['action'],
                ui_element=ui_button,
                style=self.style
            )
            
            self.buttons.append(menu_button)
        
        # 戻るボタンを追加（必要な場合）
        if additional_count > 0:
            back_button = self.back_button_manager.create_back_button(
                button_rects[len(original_buttons)],
                self.ui_manager,
                self.panel,
                self.style
            )
            if back_button:
                self.buttons.append(back_button)
        
        logger.debug(f"MenuWindow ボタンを作成: {len(self.buttons)}個")
    
    def handle_event(self, event: pygame.event.Event) -> bool:
        """イベントを処理"""
        if not self.enabled:
            return False
        
        if not self.ui_manager:
            return False
        
        # pygame-guiのイベント処理はWindowManagerで行われるため、ここではスキップ
        
        # キーボードナビゲーション
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_DOWN:
                self._navigate_down()
                return True
            elif event.key == pygame.K_UP:
                self._navigate_up()
                return True
            elif event.key == pygame.K_RETURN:
                self._activate_selected_button()
                return True
            elif event.key == pygame.K_ESCAPE:
                self._handle_escape_key()
                return True
        
        # ボタンクリック処理
        try:
            import pygame_gui
            if hasattr(pygame_gui, 'UI_BUTTON_PRESSED') and event.type == pygame_gui.UI_BUTTON_PRESSED:
                logger.debug(f"MenuWindow: ボタンクリックイベント受信: {event.ui_element}")
                for button in self.buttons:
                    if event.ui_element == button.ui_element:
                        logger.debug(f"MenuWindow: ボタンマッチ: {button.action}")
                        self._execute_button_action(button)
                        return True
                logger.debug("MenuWindow: マッチするボタンが見つかりません")
        except ImportError:
            pass
        
        return False
    
    def _navigate_down(self) -> None:
        """下方向のナビゲーション"""
        if len(self.buttons) > 0:
            self.selected_button_index = (self.selected_button_index + 1) % len(self.buttons)
            self._update_button_selection()
    
    def _navigate_up(self) -> None:
        """上方向のナビゲーション"""
        if len(self.buttons) > 0:
            self.selected_button_index = (self.selected_button_index - 1) % len(self.buttons)
            self._update_button_selection()
    
    def _update_button_selection(self) -> None:
        """ボタン選択状態を更新"""
        # 視覚的なフィードバック（実装は後で詳細化）
        logger.debug(f"ボタン選択更新: {self.selected_button_index}")
    
    def _activate_selected_button(self) -> None:
        """選択されたボタンを実行"""
        if 0 <= self.selected_button_index < len(self.buttons):
            selected_button = self.buttons[self.selected_button_index]
            self._execute_button_action(selected_button)
    
    def _execute_button_action(self, button: MenuButton) -> None:
        """ボタンアクションを実行"""
        message_data = {
            'action': button.action,
            'button_id': button.id
        }
        self.send_message('menu_action', message_data)
        logger.debug(f"メニューアクション実行: {button.action}")
    
    def _handle_escape_key(self) -> None:
        """ESCキーが押されたときの処理"""
        self.back_button_manager.handle_escape_key(self.send_message)
    
    def set_enabled(self, enabled: bool) -> None:
        """メニューの有効/無効を設定"""
        self.enabled = enabled
        
        # ボタンの有効/無効も更新
        for button in self.buttons:
            if button.ui_element:
                button.ui_element.disable() if not enabled else button.ui_element.enable()
        
        logger.debug(f"MenuWindow有効状態変更: {enabled}")
    
    def cleanup_ui(self) -> None:
        """UI要素のクリーンアップ"""
        # ボタンをクリア
        for button in self.buttons:
            if button.ui_element:
                button.ui_element.kill()
        self.buttons.clear()
        
        # 個別に作成されたUI要素をクリーンアップ
        if hasattr(self, 'title_label') and self.title_label:
            self.title_label.kill()
            self.title_label = None
            
        if hasattr(self, 'panel') and self.panel:
            self.panel.kill()
            self.panel = None
            
        # カスタム要素もクリーンアップ（例：formation_label）
        if hasattr(self, 'formation_label') and self.formation_label:
            self.formation_label.kill()
            self.formation_label = None
        
        logger.debug(f"MenuWindow UI要素をクリーンアップ: {self.window_id}")