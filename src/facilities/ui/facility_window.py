"""施設の統合ウィンドウ"""

import pygame
import pygame_gui
from typing import Dict, Optional, Any
import logging
from src.ui.window_system.window import Window
from src.ui.window_system.window_manager import WindowManager
from ..core.facility_controller import FacilityController

logger = logging.getLogger(__name__)


class FacilityWindow(Window):
    """施設の統合ウィンドウ
    
    すべての施設サービスを一つのウィンドウで統合管理。
    タブベースのナビゲーションで各サービスにアクセス。
    """
    
    def __init__(self, window_id: str, controller: FacilityController = None, facility_controller: FacilityController = None, **kwargs):
        """初期化
        
        Args:
            window_id: ウィンドウID（WindowManager経由の場合は自動設定）
            controller: 施設コントローラー（直接作成時）
            facility_controller: 施設コントローラー（WindowManager経由作成時）
            **kwargs: その他の引数
        """
        # コントローラーを正規化
        self.controller = controller or facility_controller
        if not self.controller:
            raise ValueError("FacilityController is required")
        
        # ウィンドウを初期化
        super().__init__(window_id, parent=kwargs.get('parent'), modal=False)
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
        
        # Window基底クラスのcreate処理を呼び出し
        super().create()
        
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
            logger.debug(f"[DEBUG] NavigationPanel: controller.is_active={self.controller.is_active}, menu_items count={len(menu_items)}")
            
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
            # サービス自体に専用パネル作成を委任
            if hasattr(self.controller.service, 'create_service_panel'):
                logger.debug(f"[DEBUG] Calling create_service_panel for {service_id}")
                custom_panel = self.controller.service.create_service_panel(
                    service_id, content_rect, self.main_panel, self.ui_manager
                )
                if custom_panel:
                    logger.info(f"[DEBUG] Custom panel created for {service_id}: {type(custom_panel)}")
                    return custom_panel
                else:
                    logger.info(f"[DEBUG] create_service_panel returned None for {service_id}")
            else:
                logger.info(f"[DEBUG] Service {self.controller.service.__class__.__name__} has no create_service_panel method")
            
            # 汎用サービスタイプに応じてパネルを作成
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
                # ServicePanelは抽象クラスなので具体的な実装を作成
                return self._create_generic_service_panel(content_rect, service_id, menu_item)
                
        except Exception as e:
            logger.error(f"Exception in create_service_panel for {service_id}: {e}", exc_info=True)
            # フォールバック：シンプルなパネル
            return self._create_fallback_panel(content_rect, service_id)
    
    def _create_generic_service_panel(self, rect: pygame.Rect, service_id: str, menu_item) -> pygame_gui.elements.UIPanel:
        """汎用サービスパネルを作成"""
        panel = pygame_gui.elements.UIPanel(
            relative_rect=rect,
            manager=self.ui_manager,
            container=self.main_panel,
            element_id=f"{service_id}_panel"
        )
        
        # サービス名を表示
        pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect(10, 10, rect.width - 20, 40),
            text=menu_item.label,
            manager=self.ui_manager,
            container=panel
        )
        
        # サービス説明を表示
        if hasattr(menu_item, 'description') and menu_item.description:
            pygame_gui.elements.UILabel(
                relative_rect=pygame.Rect(10, 60, rect.width - 20, 60),
                text=menu_item.description,
                manager=self.ui_manager,
                container=panel
            )
        
        # 実装予定メッセージ
        pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect(10, 140, rect.width - 20, 30),
            text="このサービスは現在実装中です。",
            manager=self.ui_manager,
            container=panel
        )
        
        # パネルにカスタム属性を追加（show/hideメソッド用）
        panel.is_visible = True
        
        # 元のshow/hideメソッドを保存
        original_show = panel.show
        original_hide = panel.hide
        
        def show_panel():
            original_show()
            panel.is_visible = True
            
        def hide_panel():
            original_hide()
            panel.is_visible = False
            
        panel.show = show_panel
        panel.hide = hide_panel
        
        logger.info(f"Generic service panel created: {service_id}")
        return panel
    
    def _create_fallback_panel(self, rect: pygame.Rect, service_id: str) -> pygame_gui.elements.UIPanel:
        """フォールバック用のシンプルなパネルを作成"""
        panel = pygame_gui.elements.UIPanel(
            relative_rect=rect,
            manager=self.ui_manager,
            container=self.main_panel
        )
        
        # サービス名を表示
        pygame_gui.elements.UILabel(
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
        logger.info(f"FacilityWindow closing: {self.window_id}")
        
        # すべてのサービスパネルを詳細に破棄
        for service_id, panel in self.service_panels.items():
            try:
                logger.info(f"Destroying service panel: {service_id}")
                # パネル内のすべてのUI要素を再帰的に削除
                self._recursive_kill_children(panel)
                if hasattr(panel, 'destroy'):
                    panel.destroy()
                elif hasattr(panel, 'kill'):
                    panel.kill()
            except Exception as e:
                logger.error(f"Failed to destroy service panel {service_id}: {e}")
        self.service_panels.clear()
        
        # ナビゲーションパネルを詳細に破棄
        if self.navigation_panel:
            try:
                logger.info("Destroying navigation panel")
                self._recursive_kill_children(self.navigation_panel)
                if hasattr(self.navigation_panel, 'destroy'):
                    self.navigation_panel.destroy()
                elif hasattr(self.navigation_panel, 'kill'):
                    self.navigation_panel.kill()
            except Exception as e:
                logger.error(f"Failed to destroy navigation panel: {e}")
            self.navigation_panel = None
        
        # メインパネルを詳細に破棄
        if self.main_panel:
            try:
                logger.info("Destroying main panel")
                self._recursive_kill_children(self.main_panel)
                self.main_panel.kill()
            except Exception as e:
                logger.error(f"Failed to destroy main panel: {e}")
            self.main_panel = None
        
        # 親クラスのclose処理
        try:
            super().destroy()
        except Exception as e:
            logger.error(f"Failed to destroy window: {e}")
        
        logger.info(f"FacilityWindow closed: {self.window_id}")
    
    def destroy(self) -> None:
        """WindowManagerから呼び出されるdestroy処理"""
        logger.info(f"FacilityWindow destroy called: {self.window_id}")
        self.close()
    
    def _recursive_kill_children(self, element) -> None:
        """UI要素の子要素を再帰的に削除"""
        if hasattr(element, 'get_container') and element.get_container():
            container = element.get_container()
            if hasattr(container, '_layer_thickness'):
                # pygame_guiのUIContainerの場合
                for layer_elements in container._layer_thickness.values():
                    for child_element in list(layer_elements):
                        try:
                            self._recursive_kill_children(child_element)
                            if hasattr(child_element, 'kill'):
                                child_element.kill()
                        except Exception as e:
                            logger.warning(f"Failed to kill child element: {e}")
        
        # 直接の子要素も削除
        if hasattr(element, 'get_container') and element.get_container():
            container = element.get_container()
            if hasattr(container, 'elements'):
                for child in list(container.elements):
                    try:
                        self._recursive_kill_children(child)
                        if hasattr(child, 'kill'):
                            child.kill()
                    except Exception as e:
                        logger.warning(f"Failed to kill container child: {e}")
    
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
        # デバッグ: 数字キーが来たときのログ
        if event.type == pygame.KEYDOWN and pygame.K_1 <= event.key <= pygame.K_9:
            button_number = event.key - pygame.K_1 + 1
            logger.info(f"[DEBUG] FacilityWindow({self.window_id}) received number key: {button_number}")
        
        # pygame_gui のイベント処理
        # WindowManagerの統一UIManagerとは別のUIManagerを使用しているため、
        # ここで処理する必要がある
        ui_consumed = False
        if self.ui_manager:
            # UIManagerがイベントを処理したかチェック
            # テキスト入力系のイベントはpygame_guiが処理する
            if event.type in [pygame.KEYDOWN, pygame.TEXTINPUT, pygame.MOUSEBUTTONDOWN, pygame.MOUSEBUTTONUP, pygame.MOUSEMOTION]:
                self.ui_manager.process_events(event)
                ui_consumed = True
        
        # ESCキー処理
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self.controller.exit()
            return True
        
        # 数字キーショートカット処理（1-9）
        if event.type == pygame.KEYDOWN and pygame.K_1 <= event.key <= pygame.K_9:
            button_number = event.key - pygame.K_1 + 1
            menu_items = self.controller.get_menu_items()
            
            # メニュー項目の番号と対応（exitを除く）
            non_exit_items = [item for item in menu_items if item.id != "exit"]
            
            if 0 < button_number <= len(non_exit_items):
                item = non_exit_items[button_number - 1]
                logger.info(f"[DEBUG] 施設内ショートカット {button_number} -> {item.id} (FacilityWindow処理)")
                self._on_service_selected(item.id)
                return True
        
        # NavigationPanelのボタンクリック処理
        if self.navigation_panel and hasattr(self.navigation_panel, 'handle_button_click'):
            if self.navigation_panel.handle_button_click(event):
                return True
        
        # サービスパネルのイベント処理
        if self.current_service_id and self.current_service_id in self.service_panels:
            service_panel = self.service_panels[self.current_service_id]
            
            # UISelectionListのイベント処理
            if hasattr(service_panel, 'handle_selection_list_changed'):
                if (event.type == pygame_gui.UI_SELECTION_LIST_NEW_SELECTION or
                    event.type == pygame_gui.UI_SELECTION_LIST_DOUBLE_CLICKED_SELECTION):
                    if service_panel.handle_selection_list_changed(event):
                        return True
            
            # ボタンクリック（UI_BUTTON_PRESSED）イベントの処理
            if hasattr(service_panel, 'handle_button_click') and event.type == pygame_gui.UI_BUTTON_PRESSED:
                if service_panel.handle_button_click(event.ui_element):
                    return True
            
            # ENTERキーやその他のキーイベントの処理（ウィザード用）
            if hasattr(service_panel, 'handle_key_event') and event.type == pygame.KEYDOWN:
                if service_panel.handle_key_event(event):
                    return True
        
        # シンプルナビゲーションのボタンクリック処理（フォールバック）
        if hasattr(self, 'nav_buttons') and event.type == pygame_gui.UI_BUTTON_PRESSED:
            for button in self.nav_buttons:
                if event.ui_element == button:
                    self._on_service_selected(button.item_id)
                    return True
        
        # UIManagerがイベントを処理した場合はTrueを返す
        return ui_consumed