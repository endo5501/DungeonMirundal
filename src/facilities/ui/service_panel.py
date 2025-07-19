"""サービスパネルの基底クラス"""

import pygame
import pygame_gui
from typing import Optional, Dict, Any, List
import logging
from abc import ABC, abstractmethod
from ..core.facility_controller import FacilityController
from ..core.service_result import ServiceResult
from .ui_element_manager import UIElementManager, DestructionMixin

logger = logging.getLogger(__name__)


class ServicePanel(ABC, DestructionMixin):
    """サービスパネルの基底クラス
    
    各施設サービスのUI表示を担当する基底クラス。
    サービス固有のUIを作成し、ユーザーインタラクションを処理する。
    """
    
    def __init__(self, rect: pygame.Rect, parent: pygame_gui.elements.UIPanel, 
                 controller: FacilityController, service_id: str,
                 ui_manager: pygame_gui.UIManager):
        """初期化
        
        Args:
            rect: パネルの矩形領域
            parent: 親パネル
            controller: 施設コントローラー
            service_id: サービスID
            ui_manager: UIマネージャー
        """
        # DestructionMixinを初期化
        super().__init__()
        
        self.rect = rect
        self.parent = parent
        self.controller = controller
        self.service_id = service_id
        self.ui_manager = ui_manager
        
        # メインコンテナ
        self.container = pygame_gui.elements.UIPanel(
            relative_rect=rect,
            manager=ui_manager,
            container=parent,
            element_id=f"{service_id}_panel"
        )
        
        # UIElementManagerを初期化
        self.ui_element_manager = UIElementManager(ui_manager, self.container)
        
        # 後方互換性のためのUI要素リスト（非推奨）
        self.ui_elements: List[pygame_gui.core.UIElement] = []
        self.is_visible = False
        
        # ボタンインデックスのカウンター（ショートカットキー用）
        self._button_index_counter = 0
        
        # 初期化
        self._create_ui()
        
        logger.info(f"ServicePanel created: {service_id}")
    
    @abstractmethod
    def _create_ui(self) -> None:
        """UI要素を作成（サブクラスで実装）"""
        pass
    
    def show(self) -> None:
        """パネルを表示"""
        self.container.show()
        self.is_visible = True
        self._on_show()
    
    def hide(self) -> None:
        """パネルを非表示"""
        self.container.hide()
        self.is_visible = False
        self._on_hide()
    
    def refresh(self) -> None:
        """コンテンツを更新"""
        self._refresh_content()
    
    def destroy(self) -> None:
        """パネルを破棄（統一された破棄処理）"""
        logger.info(f"ServicePanel.destroy() called for: {self.service_id}")
        
        # UIElementManagerを使用して統一的に破棄
        if self.ui_element_manager and not self.ui_element_manager.is_destroyed:
            try:
                self.ui_element_manager.destroy_all()
                logger.debug(f"ServicePanel: UIElementManager destroyed for {self.service_id}")
            except Exception as e:
                logger.error(f"ServicePanel: Failed to destroy UIElementManager for {self.service_id}: {e}")
        
        # 後方互換性のためのui_elementsリストを破棄
        if self.ui_elements:
            destroyed_count = 0
            for element in self.ui_elements[:]:  # コピーを作って安全に反復
                try:
                    if hasattr(element, 'kill'):
                        element.kill()
                        destroyed_count += 1
                except Exception as e:
                    logger.warning(f"ServicePanel: Failed to kill element {element}: {e}")
            self.ui_elements.clear()
            logger.debug(f"ServicePanel: Destroyed {destroyed_count} legacy UI elements from list")
        
        # コンテナを破棄
        if self.container and hasattr(self.container, 'kill'):
            try:
                self.container.kill()
                logger.debug(f"ServicePanel: Container killed for {self.service_id}")
            except Exception as e:
                logger.error(f"ServicePanel: Failed to destroy container for {self.service_id}: {e}")
        
        # 属性をクリア
        self.container = None
        self.ui_element_manager = None
        
        logger.info(f"ServicePanel destroyed: {self.service_id}")
    
    # 保護されたメソッド（サブクラスでオーバーライド可能）
    
    def _on_show(self) -> None:
        """表示時の処理"""
        pass
    
    def _on_hide(self) -> None:
        """非表示時の処理"""
        pass
    
    def _refresh_content(self) -> None:
        """コンテンツ更新処理（サブクラスでオーバーライド）"""
        pass
    
    # ヘルパーメソッド
    
    def _execute_service_action(self, action_id: str, params: Optional[Dict[str, Any]] = None) -> ServiceResult:
        """サービスアクションを実行
        
        Args:
            action_id: アクションID
            params: パラメータ
            
        Returns:
            実行結果
        """
        return self.controller.execute_service(action_id, params)
    
    def _create_label(self, element_id: str, text: str, rect: pygame.Rect, 
                     container: Optional[pygame_gui.core.UIContainer] = None) -> pygame_gui.elements.UILabel:
        """ラベルを作成（UIElementManager使用）
        
        Args:
            element_id: 要素ID
            text: ラベルテキスト
            rect: 矩形領域
            container: コンテナ（省略時はself.container）
            
        Returns:
            作成したラベル
        """
        if self.ui_element_manager and not self.ui_element_manager.is_destroyed:
            return self.ui_element_manager.create_label(element_id, text, rect, container)
        else:
            # フォールバック（レガシー）
            if container is None:
                container = self.container
                
            label = pygame_gui.elements.UILabel(
                relative_rect=rect,
                text=text,
                manager=self.ui_manager,
                container=container
            )
            self.ui_elements.append(label)
            return label
    
    def _create_button(self, element_id: str, text: str, rect: pygame.Rect,
                      container: Optional[pygame_gui.core.UIContainer] = None,
                      object_id: Optional[str] = None,
                      on_click: Optional[callable] = None) -> pygame_gui.elements.UIButton:
        """ボタンを作成（UIElementManager使用）
        
        Args:
            element_id: 要素ID
            text: ボタンテキスト
            rect: 矩形領域
            container: コンテナ（省略時はself.container）
            object_id: オブジェクトID
            on_click: クリック時のコールバック
            
        Returns:
            作成したボタン
        """
        if self.ui_element_manager and not self.ui_element_manager.is_destroyed:
            button = self.ui_element_manager.create_button(
                element_id, text, rect, container, on_click, object_id=object_id
            )
        else:
            # フォールバック（レガシー）
            if container is None:
                container = self.container
                
            button = pygame_gui.elements.UIButton(
                relative_rect=rect,
                text=text,
                manager=self.ui_manager,
                container=container,
                object_id=object_id
            )
            self.ui_elements.append(button)
        
        # ショートカットキー情報を設定
        if self._button_index_counter < 9:  # 1-9の数字キーまで対応
            button.button_index = self._button_index_counter
            button.shortcut_key = str(self._button_index_counter + 1)
            self._button_index_counter += 1
        
        return button
    
    def _create_text_box(self, element_id: str, initial_text: str, rect: pygame.Rect,
                        container: Optional[pygame_gui.core.UIContainer] = None) -> pygame_gui.elements.UITextBox:
        """テキストボックスを作成（UIElementManager使用）
        
        Args:
            element_id: 要素ID
            initial_text: 初期テキスト
            rect: 矩形領域
            container: コンテナ（省略時はself.container）
            
        Returns:
            作成したテキストボックス
        """
        if self.ui_element_manager and not self.ui_element_manager.is_destroyed:
            return self.ui_element_manager.create_text_box(element_id, initial_text, rect, container)
        else:
            # フォールバック（レガシー）
            if container is None:
                container = self.container
                
            text_box = pygame_gui.elements.UITextBox(
                html_text=initial_text,
                relative_rect=rect,
                manager=self.ui_manager,
                container=container
            )
            self.ui_elements.append(text_box)
            return text_box
    
    def _create_selection_list(self, element_id: str, rect: pygame.Rect,
                              item_list: List[str],
                              container: Optional[pygame_gui.core.UIContainer] = None) -> pygame_gui.elements.UISelectionList:
        """選択リストを作成（UIElementManager使用）
        
        Args:
            element_id: 要素ID
            rect: 矩形領域
            item_list: 選択項目リスト
            container: コンテナ（省略時はself.container）
            
        Returns:
            作成した選択リスト
        """
        if self.ui_element_manager and not self.ui_element_manager.is_destroyed:
            return self.ui_element_manager.create_selection_list(element_id, rect, item_list, container)
        else:
            # フォールバック（レガシー）
            if container is None:
                container = self.container
                
            selection_list = pygame_gui.elements.UISelectionList(
                relative_rect=rect,
                item_list=item_list,
                manager=self.ui_manager,
                container=container
            )
            self.ui_elements.append(selection_list)
            return selection_list
    
    def _create_text_entry(self, element_id: str, text: str, rect: pygame.Rect,
                          container: Optional[pygame_gui.core.UIContainer] = None,
                          placeholder_text: str = "", **kwargs) -> Optional[pygame_gui.elements.UITextEntryLine]:
        """テキスト入力フィールドを作成（UIElementManager統合）
        
        Args:
            element_id: 要素ID
            text: 初期テキスト
            rect: 矩形領域
            container: コンテナ（省略時はself.container）
            placeholder_text: プレースホルダーテキスト
            **kwargs: その他の引数
            
        Returns:
            作成したテキスト入力フィールド
        """
        if self.ui_element_manager and not self.ui_element_manager.is_destroyed:
            return self.ui_element_manager.create_text_entry(
                element_id, rect, initial_text=text, container=container, 
                placeholder_text=placeholder_text, **kwargs
            )
        else:
            # フォールバック（レガシー）
            if container is None:
                container = self.container
                
            text_entry = pygame_gui.elements.UITextEntryLine(
                relative_rect=rect,
                manager=self.ui_manager,
                container=container,
                initial_text=text,
                placeholder_text=placeholder_text,
                **kwargs
            )
            self.ui_elements.append(text_entry)
            return text_entry
    
    def _show_message(self, message: str, message_type: str = "info") -> None:
        """メッセージを表示
        
        Args:
            message: メッセージテキスト
            message_type: メッセージタイプ（info, warning, error）
        """
        # TODO: メッセージダイアログの実装
        logger.info(f"Message ({message_type}): {message}")
    
    def get_debug_info(self) -> Dict[str, Any]:
        """デバッグ情報を取得
        
        Returns:
            デバッグ情報
        """
        debug_info = {
            "service_id": self.service_id,
            "is_visible": self.is_visible,
            "container_valid": self.container is not None,
            "legacy_ui_elements_count": len(self.ui_elements),
            "destruction_verified": getattr(self, 'destruction_verified', False)
        }
        
        if self.ui_element_manager:
            debug_info["ui_element_manager"] = self.ui_element_manager.get_debug_info()
        
        return debug_info


class StandardServicePanel(ServicePanel):
    """標準的なサービスパネル
    
    アクションベースのシンプルなサービス用パネル。
    """
    
    def _create_ui(self) -> None:
        """UI要素を作成"""
        # タイトル
        title_rect = pygame.Rect(10, 10, self.rect.width - 20, 30)
        self._create_label("title", f"Service: {self.service_id}", title_rect)
        
        # サービス説明
        desc_rect = pygame.Rect(10, 50, self.rect.width - 20, 60)
        description = self._get_service_description()
        self._create_text_box("description", description, desc_rect)
        
        # アクションボタン
        self._create_action_buttons()
    
    def _get_service_description(self) -> str:
        """サービスの説明を取得"""
        # メニュー項目から説明を取得
        menu_items = self.controller.get_menu_items()
        for item in menu_items:
            if item.id == self.service_id:
                return item.description or f"{item.label}サービス"
        return "サービスの説明"
    
    def _create_action_buttons(self) -> None:
        """アクションボタンを作成"""
        # 基本的なアクションボタン（実行）
        action_rect = pygame.Rect(
            self.rect.width // 2 - 60,
            self.rect.height - 60,
            120,
            40
        )
        
        self.action_button = self._create_button(
            "action_button",
            "実行",
            action_rect,
            object_id=f"{self.service_id}_execute"
        )
    
    def handle_button_click(self, button: pygame_gui.elements.UIButton) -> bool:
        """ボタンクリックを処理
        
        Args:
            button: クリックされたボタン
            
        Returns:
            処理したらTrue
        """
        if button == self.action_button:
            # サービスを実行
            result = self._execute_service_action(self.service_id)
            
            # 結果を表示
            if result.is_success():
                self._show_message(result.message, "info")
            else:
                self._show_message(result.message, "error")
            
            return True
        
        return False