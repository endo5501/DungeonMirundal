"""
GameMenuWindow クラス

ESCキーで表示されるメインゲームメニュー
"""

import pygame
import pygame_gui
from typing import Dict, List, Any, Optional

from .window import Window
from src.utils.logger import logger


class GameMenuWindow(Window):
    """
    ゲームメニューウィンドウクラス
    
    セーブ/ロード/設定/ゲーム終了のメニューを表示
    """
    
    def __init__(self, window_id: str, menu_config: Dict[str, Any], 
                 parent: Optional[Window] = None, modal: bool = True):
        """
        ゲームメニューウィンドウを初期化
        
        Args:
            window_id: ウィンドウID
            menu_config: メニュー設定辞書
            parent: 親ウィンドウ
            modal: モーダルウィンドウかどうか
        """
        super().__init__(window_id, parent, modal)
        
        self.menu_config = menu_config
        self.menu_buttons: List[pygame_gui.elements.UIButton] = []
        
        # レイアウト設定
        self.BUTTON_WIDTH = 200
        self.BUTTON_HEIGHT = 50
        self.BUTTON_SPACING = 20
        self.MENU_WIDTH = 300
        
        logger.debug(f"GameMenuWindowを初期化: {window_id}")
    
    def create(self) -> None:
        """UI要素を作成"""
        if not self.ui_manager:
            self._initialize_ui_manager()
            self._calculate_layout()
            self._create_panel()
            self._create_title()
            self._create_menu_buttons()
        
        logger.debug(f"GameMenuWindow UI要素を作成: {self.window_id}")
    
    def _initialize_ui_manager(self) -> None:
        """UIManagerを初期化"""
        # WindowManagerのUIManagerを使用
        from .window_manager import WindowManager
        window_manager = WindowManager()
        if window_manager.ui_manager is not None:
            self.ui_manager = window_manager.ui_manager
        else:
            # フォールバック: 独自のUIManagerを作成
            screen_width = 1024
            screen_height = 768
            self.ui_manager = pygame_gui.UIManager((screen_width, screen_height))
    
    def _calculate_layout(self) -> None:
        """レイアウトを計算"""
        screen_width = 1024
        screen_height = 768
        
        # メニューアイテム数を取得
        menu_items = self.menu_config.get('menu_items', [])
        menu_count = len(menu_items)
        
        # メニューの高さを計算
        menu_height = (menu_count * self.BUTTON_HEIGHT + 
                      (menu_count - 1) * self.BUTTON_SPACING + 
                      120)  # タイトル分とパディング
        
        # 画面中央に配置
        self.rect = pygame.Rect(
            (screen_width - self.MENU_WIDTH) // 2,
            (screen_height - menu_height) // 2,
            self.MENU_WIDTH,
            menu_height
        )
    
    def _create_panel(self) -> None:
        """メニューパネルを作成"""
        self.panel = pygame_gui.elements.UIPanel(
            relative_rect=self.rect,
            manager=self.ui_manager
        )
    
    def _create_title(self) -> None:
        """タイトルラベルを作成"""
        title = self.menu_config.get('title', 'ゲームメニュー')
        title_rect = pygame.Rect(20, 20, self.MENU_WIDTH - 40, 40)
        
        self.title_label = pygame_gui.elements.UILabel(
            relative_rect=title_rect,
            text=title,
            manager=self.ui_manager,
            container=self.panel
        )
    
    def _create_menu_buttons(self) -> None:
        """メニューボタンを作成"""
        menu_items = self.menu_config.get('menu_items', [])
        
        y_position = 80  # タイトルの下から開始
        
        for item in menu_items:
            button_rect = pygame.Rect(
                50,  # 左右中央
                y_position,
                self.BUTTON_WIDTH,
                self.BUTTON_HEIGHT
            )
            
            button = pygame_gui.elements.UIButton(
                relative_rect=button_rect,
                text=item.get('label', item.get('id', 'Unknown')),
                manager=self.ui_manager,
                container=self.panel
            )
            
            # ボタンにメニューアイテム情報を保存
            button.menu_item = item
            self.menu_buttons.append(button)
            
            y_position += self.BUTTON_HEIGHT + self.BUTTON_SPACING
    
    def handle_event(self, event: pygame.event.Event) -> bool:
        """イベントを処理"""
        if not self.ui_manager:
            return False
        
        # pygame-guiにイベントを渡す
        self.ui_manager.process_events(event)
        
        # ボタンクリック処理
        if event.type == pygame_gui.UI_BUTTON_PRESSED:
            logger.info(f"GameMenuWindow: ボタンクリック検出! 要素={event.ui_element}")
            for i, button in enumerate(self.menu_buttons):
                logger.debug(f"ボタン{i}: {button} (menu_item: {getattr(button, 'menu_item', 'なし')})")
                if event.ui_element == button:
                    logger.info(f"GameMenuWindow: ボタン{i}がクリックされました")
                    self._handle_menu_selection(button.menu_item)
                    return True
            logger.warning("GameMenuWindow: クリックされたボタンが見つかりませんでした")
        
        return False
    
    def _handle_menu_selection(self, menu_item: Dict[str, Any]) -> None:
        """メニュー選択を処理"""
        action = menu_item.get('action')
        
        logger.info(f"=== GameMenuWindow: メニューアイテム選択 ===")
        logger.info(f"アクション: {action}")
        logger.info(f"メニューアイテム: {menu_item}")
        logger.info(f"メッセージハンドラ存在: {self.message_handler is not None}")
        
        if self.message_handler:
            logger.info("メッセージハンドラに送信中...")
            self.message_handler('menu_item_selected', {
                'action': action,
                'menu_item': menu_item,
                'window_id': self.window_id
            })
            logger.info("メッセージハンドラに送信完了")
        else:
            logger.warning("メッセージハンドラが設定されていません")
        
        logger.info(f"メニューアイテム選択処理完了: {action}")
    
    def handle_escape(self) -> bool:
        """ESCキーの処理"""
        # ゲームメニューを閉じる
        if self.message_handler:
            self.message_handler('game_menu_cancelled', {'window_id': self.window_id})
        
        from .window_manager import WindowManager
        window_manager = WindowManager()
        window_manager.hide_window(self, remove_from_stack=True)
        return True
    
    def cleanup_ui(self) -> None:
        """UI要素のクリーンアップ"""
        # ボタンをクリア
        self.menu_buttons.clear()
        
        # pygame-guiの要素を削除
        if self.ui_manager:
            for element in list(self.ui_manager.get_root_container().elements):
                element.kill()
            self.ui_manager = None
        
        logger.debug(f"GameMenuWindow UI要素をクリーンアップ: {self.window_id}")
    
    def hide_ui_elements(self) -> None:
        """UI要素を非表示にする"""
        if not self.ui_manager:
            return
        
        # パネルを非表示
        if hasattr(self, 'panel') and self.panel:
            self.panel.hide()
        
        # ボタンを非表示
        for button in self.menu_buttons:
            if button:
                button.hide()
        
        logger.debug(f"GameMenuWindow UI要素を非表示: {self.window_id}")
    
    def show_ui_elements(self) -> None:
        """UI要素を表示する"""
        if not self.ui_manager:
            return
        
        # パネルを表示
        if hasattr(self, 'panel') and self.panel:
            self.panel.show()
        
        # ボタンを表示
        for button in self.menu_buttons:
            if button:
                button.show()
        
        logger.debug(f"GameMenuWindow UI要素を表示: {self.window_id}")