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
        """UI要素を作成（冪等性保証）"""
        if not self.ui_manager:
            self._initialize_ui_manager()
        
        # 既にUI要素が存在し、生きている場合はスキップ
        if (hasattr(self, 'panel') and self.panel and 
            hasattr(self.panel, 'alive') and self.panel.alive()):
            logger.debug(f"GameMenuWindow UI要素は既に存在: {self.window_id}")
            return
        
        # UI要素を作成
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
        
        for i, item in enumerate(menu_items):
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
            
            # デバッグ用: ボタンインデックスとショートカットキー
            button.button_index = i
            if i < 9:  # 1-9のキーのみ対応
                button.shortcut_key = str(i + 1)
            
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
        """UI要素のクリーンアップ（完全終了時のみ）"""
        # 注意: このメソッドはウィンドウが完全に破棄される時のみ呼び出すべき
        # hide/show操作では呼び出してはならない
        
        # 個別のUI要素を削除
        if hasattr(self, 'panel') and self.panel:
            self.panel.kill()
            self.panel = None
        
        if hasattr(self, 'title_label') and self.title_label:
            self.title_label.kill()
            self.title_label = None
        
        for button in self.menu_buttons:
            if button and hasattr(button, 'kill'):
                button.kill()
        
        # ボタンリストをクリア
        self.menu_buttons.clear()
        
        # UIManagerは削除しない（WindowManagerが管理している）
        # self.ui_manager = None  # これを削除
        
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
        """UI要素を表示する（必要に応じて再作成）"""
        if not self.ui_manager:
            self._initialize_ui_manager()
        
        # UI要素が削除されている場合は再作成
        if not hasattr(self, 'panel') or not self.panel or not self.panel.alive():
            logger.info(f"GameMenuWindow: UI要素が削除されているため再作成します: {self.window_id}")
            self._calculate_layout()
            self._create_panel()
            self._create_title()
            self._create_menu_buttons()
        else:
            # パネルを表示
            if hasattr(self, 'panel') and self.panel:
                self.panel.show()
            
            # ボタンを表示
            for button in self.menu_buttons:
                if button and hasattr(button, 'show'):
                    button.show()
        
        logger.debug(f"GameMenuWindow UI要素を表示: {self.window_id}")