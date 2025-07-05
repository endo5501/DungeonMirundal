"""施設の統合ウィンドウ"""

import pygame
import pygame_gui
from typing import Dict, Optional, List, Any
import logging
from src.ui.window_system.window import Window
from src.ui.window_system.window_manager import WindowManager
from ..core.facility_controller import FacilityController
from ..core.service_result import ServiceResult

logger = logging.getLogger(__name__)


class FacilityWindow(Window):
    """施設の統合ウィンドウ
    
    すべての施設サービスを一つのウィンドウで統合管理。
    タブベースのナビゲーションで各サービスにアクセス。
    """
    
    def __init__(self, controller: FacilityController):
        """初期化
        
        Args:
            controller: 施設コントローラー
        """
        # ウィンドウIDを施設IDから生成
        window_id = f"{controller.facility_id}_window"
        super().__init__(window_id, parent=None, modal=False)
        
        self.controller = controller
        self.main_panel: Optional[pygame_gui.elements.UIPanel] = None
        self.navigation_panel = None  # NavigationPanel
        self.service_panels: Dict[str, Any] = {}  # ServicePanel instances
        self.current_service_id: Optional[str] = None
        
        # UI要素のサイズ設定
        self.window_width = 900
        self.window_height = 600
        self.nav_height = 60
        self.content_padding = 10
        
        logger.info(f"FacilityWindow created: {window_id}")
    
    def create(self) -> None:
        """UI要素を作成"""
        # WindowManagerから必要な情報を取得
        window_manager = WindowManager.get_instance()
        if window_manager:
            self.ui_manager = window_manager.ui_manager
            screen = pygame.display.get_surface()
            if screen:
                # 画面中央に配置
                screen_rect = screen.get_rect()
                self.rect = pygame.Rect(
                    (screen_rect.width - self.window_width) // 2,
                    (screen_rect.height - self.window_height) // 2,
                    self.window_width,
                    self.window_height
                )
            else:
                # デフォルト位置
                self.rect = pygame.Rect(50, 50, self.window_width, self.window_height)
        else:
            logger.error("WindowManager not available")
            return
        
        # メインパネル作成
        self._create_main_panel()
        
        # ナビゲーションパネル作成
        self._create_navigation()
        
        # 初期サービスを表示
        self._show_initial_service()
        
        logger.info(f"FacilityWindow UI created: {self.window_id}")
    
    def _create_main_panel(self) -> None:
        """メインパネルを作成"""
        self.main_panel = pygame_gui.elements.UIPanel(
            relative_rect=self.rect,
            manager=self.ui_manager,
            element_id=f"{self.controller.facility_id}_main_panel"
        )
        
        # タイトルバー
        title_rect = pygame.Rect(0, 0, self.window_width, 40)
        title_text = self._get_facility_title()
        
        self.title_label = pygame_gui.elements.UILabel(
            relative_rect=title_rect,
            text=title_text,
            manager=self.ui_manager,
            container=self.main_panel
        )
    
    def _create_navigation(self) -> None:
        """ナビゲーションパネルを作成"""
        try:
            from .navigation_panel import NavigationPanel
            
            # ナビゲーションエリア
            nav_rect = pygame.Rect(
                0, 40,
                self.window_width,
                self.nav_height
            )
            
            # メニュー項目を取得
            menu_items = self.controller.get_menu_items()
            
            self.navigation_panel = NavigationPanel(
                rect=nav_rect,
                parent=self.main_panel,
                menu_items=menu_items,
                on_select_callback=self._on_service_selected,
                ui_manager=self.ui_manager
            )
            
        except ImportError:
            logger.warning("NavigationPanel not available, using simple buttons")
            self._create_simple_navigation()
    
    def _create_simple_navigation(self) -> None:
        """シンプルなナビゲーションボタンを作成（フォールバック）"""
        menu_items = self.controller.get_menu_items()
        
        button_width = 120
        button_height = 40
        button_spacing = 10
        x_offset = 10
        y_offset = 45
        
        self.nav_buttons = []
        
        for i, item in enumerate(menu_items):
            button_rect = pygame.Rect(
                x_offset + i * (button_width + button_spacing),
                y_offset,
                button_width,
                button_height
            )
            
            button = pygame_gui.elements.UIButton(
                relative_rect=button_rect,
                text=item.label,
                manager=self.ui_manager,
                container=self.main_panel
            )
            button.item_id = item.id  # カスタム属性として保存
            self.nav_buttons.append(button)
    
    def _show_initial_service(self) -> None:
        """初期サービスを表示"""
        menu_items = self.controller.get_menu_items()
        if menu_items:
            # exitではない最初の項目を選択
            for item in menu_items:
                if item.id != "exit":
                    self._show_service(item.id)
                    break
    
    def _on_service_selected(self, service_id: str) -> None:
        """サービスが選択された時の処理
        
        Args:
            service_id: 選択されたサービスID
        """
        logger.info(f"Service selected: {service_id}")
        
        if service_id == "exit":
            # 施設から退出
            self.controller.exit()
        else:
            # サービスを表示
            self._show_service(service_id)
    
    def _show_service(self, service_id: str) -> None:
        """サービスを表示
        
        Args:
            service_id: 表示するサービスID
        """
        # 現在のサービスを隠す
        if self.current_service_id and self.current_service_id in self.service_panels:
            self.service_panels[self.current_service_id].hide()
        
        # 新しいサービスパネルを作成/表示
        if service_id not in self.service_panels:
            panel = self._create_service_panel(service_id)
            if panel:
                self.service_panels[service_id] = panel
        
        if service_id in self.service_panels:
            self.service_panels[service_id].show()
            self.current_service_id = service_id
            
            # ナビゲーションの選択状態を更新
            if self.navigation_panel:
                self.navigation_panel.set_selected(service_id)
    
    def _create_service_panel(self, service_id: str) -> Optional[Any]:
        """サービスパネルを作成
        
        Args:
            service_id: サービスID
            
        Returns:
            作成したサービスパネル（失敗時None）
        """
        # コンテンツエリアの定義
        content_rect = pygame.Rect(
            self.content_padding,
            40 + self.nav_height + self.content_padding,
            self.window_width - 2 * self.content_padding,
            self.window_height - 40 - self.nav_height - 2 * self.content_padding
        )
        
        # メニュー項目を検索
        menu_item = None
        for item in self.controller.get_menu_items():
            if item.id == service_id:
                menu_item = item
                break
        
        if not menu_item:
            logger.error(f"Menu item not found: {service_id}")
            return None
        
        try:
            # サービスタイプに応じてパネルを作成
            if menu_item.service_type == "wizard":
                from .wizard_service_panel import WizardServicePanel
                return WizardServicePanel(
                    rect=content_rect,
                    parent=self.main_panel,
                    controller=self.controller,
                    service_id=service_id,
                    ui_manager=self.ui_manager
                )
            else:
                from .service_panel import ServicePanel
                return ServicePanel(
                    rect=content_rect,
                    parent=self.main_panel,
                    controller=self.controller,
                    service_id=service_id,
                    ui_manager=self.ui_manager
                )
                
        except ImportError as e:
            logger.error(f"Failed to import service panel: {e}")
            # フォールバック：シンプルなパネル
            return self._create_fallback_panel(content_rect, service_id)
    
    def _create_fallback_panel(self, rect: pygame.Rect, service_id: str) -> pygame_gui.elements.UIPanel:
        """フォールバック用のシンプルなパネルを作成"""
        panel = pygame_gui.elements.UIPanel(
            relative_rect=rect,
            manager=self.ui_manager,
            container=self.main_panel
        )
        
        # サービス名を表示
        label = pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect(10, 10, rect.width - 20, 30),
            text=f"Service: {service_id}",
            manager=self.ui_manager,
            container=panel
        )
        
        return panel
    
    def _get_facility_title(self) -> str:
        """施設タイトルを取得"""
        # 設定から取得
        title = self.controller.get_config("name")
        if title:
            return title
        
        # デフォルト
        facility_names = {
            "guild": "冒険者ギルド",
            "inn": "宿屋",
            "shop": "商店",
            "temple": "教会",
            "magic_guild": "魔法ギルド"
        }
        return facility_names.get(self.controller.facility_id, self.controller.facility_id)
    
    def show(self) -> None:
        """ウィンドウを表示"""
        if self.main_panel:
            self.main_panel.show()
        super().show()
    
    def hide(self) -> None:
        """ウィンドウを非表示"""
        if self.main_panel:
            self.main_panel.hide()
        super().hide()
    
    def close(self) -> None:
        """ウィンドウを閉じる"""
        # すべてのサービスパネルを破棄
        for panel in self.service_panels.values():
            if hasattr(panel, 'destroy'):
                panel.destroy()
            elif hasattr(panel, 'kill'):
                panel.kill()
        self.service_panels.clear()
        
        # ナビゲーションパネルを破棄
        if self.navigation_panel:
            if hasattr(self.navigation_panel, 'destroy'):
                self.navigation_panel.destroy()
        
        # メインパネルを破棄
        if self.main_panel:
            self.main_panel.kill()
        
        # 親クラスのclose処理
        super().destroy()
        
        logger.info(f"FacilityWindow closed: {self.window_id}")
    
    def refresh_content(self) -> None:
        """コンテンツを更新"""
        # 現在のサービスパネルを更新
        if self.current_service_id and self.current_service_id in self.service_panels:
            panel = self.service_panels[self.current_service_id]
            if hasattr(panel, 'refresh'):
                panel.refresh()
        
        # ナビゲーションを更新（メニュー項目の有効/無効が変わる可能性）
        if self.navigation_panel:
            menu_items = self.controller.get_menu_items()
            self.navigation_panel.update_menu_items(menu_items)
    
    def handle_event(self, event: pygame.event.Event) -> bool:
        """イベント処理
        
        Args:
            event: pygame イベント
            
        Returns:
            イベントを処理したらTrue
        """
        # pygame_gui のイベント処理
        if self.ui_manager:
            self.ui_manager.process_events(event)
        
        # ESCキー処理
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self.controller.exit()
            return True
        
        # シンプルナビゲーションのボタンクリック処理
        if hasattr(self, 'nav_buttons') and event.type == pygame_gui.UI_BUTTON_PRESSED:
            for button in self.nav_buttons:
                if event.ui_element == button:
                    self._on_service_selected(button.item_id)
                    return True
        
        return False