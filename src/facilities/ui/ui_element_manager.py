"""UIElementManager - 統一されたUI要素管理システム"""

import pygame
import pygame_gui
import logging
from typing import Dict, List, Optional, Any, Union, Callable
from abc import ABC, abstractmethod
from contextlib import contextmanager

logger = logging.getLogger(__name__)


class UIElementManager:
    """UI要素の統一管理システム
    
    UI要素の作成、管理、破棄を統一的に処理し、
    メモリリークを防止する。
    """
    
    def __init__(self, ui_manager: pygame_gui.UIManager, container: pygame_gui.core.UIContainer):
        """初期化
        
        Args:
            ui_manager: pygame_gui UIManager
            container: UI要素を格納するコンテナ
        """
        self.ui_manager = ui_manager
        self.container = container
        self.elements: Dict[str, pygame_gui.core.UIElement] = {}
        self.element_groups: Dict[str, List[str]] = {}
        self.destruction_callbacks: Dict[str, List[Callable]] = {}
        self.is_destroyed = False
        
        logger.debug(f"UIElementManager initialized with container: {type(container)}")
    
    def create_label(self, element_id: str, text: str, rect: pygame.Rect, 
                    container: Optional[pygame_gui.core.UIContainer] = None,
                    **kwargs) -> pygame_gui.elements.UILabel:
        """ラベルを作成
        
        Args:
            element_id: 要素ID（一意である必要がある）
            text: ラベルテキスト
            rect: 矩形領域
            container: コンテナ（省略時はself.container）
            **kwargs: その他の引数
            
        Returns:
            作成したラベル
        """
        if element_id in self.elements:
            raise ValueError(f"Element ID '{element_id}' already exists")
        
        if container is None:
            container = self.container
            
        label = pygame_gui.elements.UILabel(
            relative_rect=rect,
            text=text,
            manager=self.ui_manager,
            container=container,
            **kwargs
        )
        
        self.elements[element_id] = label
        logger.debug(f"Created label: {element_id}")
        return label
    
    def create_button(self, element_id: str, text: str, rect: pygame.Rect,
                     container: Optional[pygame_gui.core.UIContainer] = None,
                     on_click: Optional[Callable] = None,
                     **kwargs) -> pygame_gui.elements.UIButton:
        """ボタンを作成
        
        Args:
            element_id: 要素ID（一意である必要がある）
            text: ボタンテキスト
            rect: 矩形領域
            container: コンテナ（省略時はself.container）
            on_click: クリック時のコールバック
            **kwargs: その他の引数
            
        Returns:
            作成したボタン
        """
        if element_id in self.elements:
            raise ValueError(f"Element ID '{element_id}' already exists")
        
        if container is None:
            container = self.container
            
        button = pygame_gui.elements.UIButton(
            relative_rect=rect,
            text=text,
            manager=self.ui_manager,
            container=container,
            **kwargs
        )
        
        self.elements[element_id] = button
        
        # クリックコールバックを設定
        if on_click:
            self.add_destruction_callback(element_id, lambda: None)  # プレースホルダー
        
        logger.debug(f"Created button: {element_id}")
        return button
    
    def create_selection_list(self, element_id: str, rect: pygame.Rect,
                             item_list: List[str],
                             container: Optional[pygame_gui.core.UIContainer] = None,
                             **kwargs) -> pygame_gui.elements.UISelectionList:
        """選択リストを作成
        
        Args:
            element_id: 要素ID（一意である必要がある）
            rect: 矩形領域
            item_list: 選択項目リスト
            container: コンテナ（省略時はself.container）
            **kwargs: その他の引数
            
        Returns:
            作成した選択リスト
        """
        if element_id in self.elements:
            raise ValueError(f"Element ID '{element_id}' already exists")
        
        if container is None:
            container = self.container
            
        selection_list = pygame_gui.elements.UISelectionList(
            relative_rect=rect,
            item_list=item_list,
            manager=self.ui_manager,
            container=container,
            **kwargs
        )
        
        self.elements[element_id] = selection_list
        logger.debug(f"Created selection list: {element_id}")
        return selection_list
    
    def create_text_box(self, element_id: str, html_text: str, rect: pygame.Rect,
                       container: Optional[pygame_gui.core.UIContainer] = None,
                       **kwargs) -> pygame_gui.elements.UITextBox:
        """テキストボックスを作成
        
        Args:
            element_id: 要素ID（一意である必要がある）
            html_text: HTMLテキスト
            rect: 矩形領域
            container: コンテナ（省略時はself.container）
            **kwargs: その他の引数
            
        Returns:
            作成したテキストボックス
        """
        if element_id in self.elements:
            raise ValueError(f"Element ID '{element_id}' already exists")
        
        if container is None:
            container = self.container
            
        text_box = pygame_gui.elements.UITextBox(
            html_text=html_text,
            relative_rect=rect,
            manager=self.ui_manager,
            container=container,
            **kwargs
        )
        
        self.elements[element_id] = text_box
        logger.debug(f"Created text box: {element_id}")
        return text_box
    
    def create_text_entry(self, element_id: str, rect: pygame.Rect,
                         initial_text: str = "",
                         container: Optional[pygame_gui.core.UIContainer] = None,
                         **kwargs) -> pygame_gui.elements.UITextEntryLine:
        """テキスト入力フィールドを作成
        
        Args:
            element_id: 要素ID（一意である必要がある）
            rect: 矩形領域
            initial_text: 初期テキスト
            container: コンテナ（省略時はself.container）
            **kwargs: その他の引数
            
        Returns:
            作成したテキスト入力フィールド
        """
        if element_id in self.elements:
            raise ValueError(f"Element ID '{element_id}' already exists")
        
        if container is None:
            container = self.container
            
        text_entry = pygame_gui.elements.UITextEntryLine(
            relative_rect=rect,
            manager=self.ui_manager,
            container=container,
            initial_text=initial_text,
            **kwargs
        )
        
        self.elements[element_id] = text_entry
        logger.debug(f"Created text entry: {element_id}")
        return text_entry
    
    def create_dropdown(self, element_id: str, rect: pygame.Rect,
                       option_list: List[str],
                       starting_option: str,
                       container: Optional[pygame_gui.core.UIContainer] = None,
                       **kwargs) -> pygame_gui.elements.UIDropDownMenu:
        """ドロップダウンメニューを作成
        
        Args:
            element_id: 要素ID（一意である必要がある）
            rect: 矩形領域
            option_list: 選択肢リスト
            starting_option: 初期選択項目
            container: コンテナ（省略時はself.container）
            **kwargs: その他の引数
            
        Returns:
            作成したドロップダウンメニュー
        """
        if element_id in self.elements:
            raise ValueError(f"Element ID '{element_id}' already exists")
        
        if container is None:
            container = self.container
            
        dropdown = pygame_gui.elements.UIDropDownMenu(
            relative_rect=rect,
            option_list=option_list,
            starting_option=starting_option,
            manager=self.ui_manager,
            container=container,
            **kwargs
        )
        
        self.elements[element_id] = dropdown
        logger.debug(f"Created dropdown: {element_id}")
        return dropdown
    
    def get_element(self, element_id: str) -> Optional[pygame_gui.core.UIElement]:
        """要素を取得
        
        Args:
            element_id: 要素ID
            
        Returns:
            UI要素（存在しない場合はNone）
        """
        return self.elements.get(element_id)
    
    def get_elements_by_group(self, group_name: str) -> List[pygame_gui.core.UIElement]:
        """グループに属する要素を取得
        
        Args:
            group_name: グループ名
            
        Returns:
            グループに属するUI要素のリスト
        """
        if group_name not in self.element_groups:
            return []
        
        elements = []
        for element_id in self.element_groups[group_name]:
            element = self.elements.get(element_id)
            if element:
                elements.append(element)
        
        return elements
    
    def add_to_group(self, element_id: str, group_name: str) -> None:
        """要素をグループに追加
        
        Args:
            element_id: 要素ID
            group_name: グループ名
        """
        if element_id not in self.elements:
            raise ValueError(f"Element ID '{element_id}' not found")
        
        if group_name not in self.element_groups:
            self.element_groups[group_name] = []
        
        if element_id not in self.element_groups[group_name]:
            self.element_groups[group_name].append(element_id)
            logger.debug(f"Added element {element_id} to group {group_name}")
    
    def remove_from_group(self, element_id: str, group_name: str) -> None:
        """要素をグループから削除
        
        Args:
            element_id: 要素ID
            group_name: グループ名
        """
        if group_name in self.element_groups and element_id in self.element_groups[group_name]:
            self.element_groups[group_name].remove(element_id)
            logger.debug(f"Removed element {element_id} from group {group_name}")
    
    def show_group(self, group_name: str) -> None:
        """グループのすべての要素を表示
        
        Args:
            group_name: グループ名
        """
        elements = self.get_elements_by_group(group_name)
        for element in elements:
            element.show()
        logger.debug(f"Showed group: {group_name}")
    
    def hide_group(self, group_name: str) -> None:
        """グループのすべての要素を非表示
        
        Args:
            group_name: グループ名
        """
        elements = self.get_elements_by_group(group_name)
        for element in elements:
            element.hide()
        logger.debug(f"Hid group: {group_name}")
    
    def destroy_element(self, element_id: str) -> None:
        """特定の要素を破棄
        
        Args:
            element_id: 要素ID
        """
        if element_id not in self.elements:
            logger.warning(f"Element ID '{element_id}' not found for destruction")
            return
        
        element = self.elements[element_id]
        
        # 破棄コールバックを実行
        if element_id in self.destruction_callbacks:
            for callback in self.destruction_callbacks[element_id]:
                try:
                    callback()
                except Exception as e:
                    logger.error(f"Error in destruction callback for {element_id}: {e}")
        
        # 要素を破棄
        try:
            element.kill()
            logger.debug(f"Destroyed element: {element_id}")
        except Exception as e:
            logger.error(f"Error destroying element {element_id}: {e}")
        
        # 管理辞書から削除
        del self.elements[element_id]
        
        # グループからも削除
        for group_name, group_elements in self.element_groups.items():
            if element_id in group_elements:
                group_elements.remove(element_id)
        
        # コールバックをクリア
        if element_id in self.destruction_callbacks:
            del self.destruction_callbacks[element_id]
    
    def destroy_group(self, group_name: str) -> None:
        """グループのすべての要素を破棄
        
        Args:
            group_name: グループ名
        """
        if group_name not in self.element_groups:
            logger.warning(f"Group '{group_name}' not found for destruction")
            return
        
        # グループの要素を破棄（コピーを作成してから反復）
        element_ids = self.element_groups[group_name][:]
        for element_id in element_ids:
            self.destroy_element(element_id)
        
        # グループを削除
        del self.element_groups[group_name]
        logger.debug(f"Destroyed group: {group_name}")
    
    def add_destruction_callback(self, element_id: str, callback: Callable) -> None:
        """破棄時のコールバックを追加
        
        Args:
            element_id: 要素ID
            callback: コールバック関数
        """
        if element_id not in self.elements:
            raise ValueError(f"Element ID '{element_id}' not found")
        
        if element_id not in self.destruction_callbacks:
            self.destruction_callbacks[element_id] = []
        
        self.destruction_callbacks[element_id].append(callback)
        logger.debug(f"Added destruction callback for: {element_id}")
    
    @contextmanager
    def element_group(self, group_name: str):
        """要素グループのコンテキストマネージャー
        
        Args:
            group_name: グループ名
            
        Yields:
            UIElementManager自身
        """
        # グループを作成
        if group_name not in self.element_groups:
            self.element_groups[group_name] = []
        
        # 開始時の要素数を記録
        initial_elements = set(self.elements.keys())
        
        try:
            yield self
        finally:
            # 新しく作成された要素をグループに追加
            new_elements = set(self.elements.keys()) - initial_elements
            for element_id in new_elements:
                self.add_to_group(element_id, group_name)
    
    def destroy_all(self) -> None:
        """すべての要素を破棄（完全破棄）"""
        if self.is_destroyed:
            logger.warning("UIElementManager is already destroyed")
            return
        
        logger.info(f"Destroying all elements in UIElementManager ({len(self.elements)} elements)")
        
        # 破棄コールバックを実行
        for element_id, callbacks in self.destruction_callbacks.items():
            for callback in callbacks:
                try:
                    callback()
                except Exception as e:
                    logger.error(f"Error in destruction callback for {element_id}: {e}")
        
        # 要素を破棄
        destroyed_count = 0
        for element_id, element in self.elements.items():
            try:
                element.kill()
                destroyed_count += 1
            except Exception as e:
                logger.error(f"Error destroying element {element_id}: {e}")
        
        # 管理辞書をクリア
        self.elements.clear()
        self.element_groups.clear()
        self.destruction_callbacks.clear()
        
        # 破棄状態をマーク
        self.is_destroyed = True
        
        logger.info(f"UIElementManager destroyed: {destroyed_count} elements")
    
    def get_element_count(self) -> int:
        """管理している要素の数を取得
        
        Returns:
            要素数
        """
        return len(self.elements)
    
    def get_group_count(self) -> int:
        """グループの数を取得
        
        Returns:
            グループ数
        """
        return len(self.element_groups)
    
    def get_debug_info(self) -> Dict[str, Any]:
        """デバッグ情報を取得
        
        Returns:
            デバッグ情報
        """
        return {
            "element_count": len(self.elements),
            "group_count": len(self.element_groups),
            "is_destroyed": self.is_destroyed,
            "elements": list(self.elements.keys()),
            "groups": {group: len(elements) for group, elements in self.element_groups.items()},
            "callback_count": len(self.destruction_callbacks)
        }


class DestructionMixin:
    """破棄処理を強化するMixin"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.destruction_verified = False
        self.destruction_start_time = None
    
    def destroy_with_verification(self) -> bool:
        """検証付きの破棄処理
        
        Returns:
            破棄が成功したかどうか
        """
        import time
        
        if self.destruction_verified:
            logger.warning("destroy_with_verification called on already destroyed object")
            return True
        
        self.destruction_start_time = time.time()
        
        try:
            # 破棄処理を実行
            self.destroy()
            
            # 破棄の検証
            if self.verify_destruction():
                self.destruction_verified = True
                destruction_time = time.time() - self.destruction_start_time
                logger.info(f"Destruction verified in {destruction_time:.3f}s")
                return True
            else:
                logger.error("Destruction verification failed")
                return False
                
        except Exception as e:
            logger.error(f"Error during destruction: {e}")
            return False
    
    def verify_destruction(self) -> bool:
        """破棄の検証
        
        Returns:
            破棄が完了しているかどうか
        """
        # UIElementManagerを持つ場合は検証
        if hasattr(self, 'ui_element_manager'):
            manager = self.ui_element_manager
            if manager and not manager.is_destroyed:
                logger.warning("UIElementManager is not destroyed")
                return False
        
        # containerを持つ場合は検証
        if hasattr(self, 'container') and self.container is not None:
            try:
                # コンテナがまだ有効かチェック
                if hasattr(self.container, 'rect'):
                    logger.warning("Container still has rect attribute")
                    return False
            except Exception:
                # コンテナが無効になっている場合は正常
                pass
        
        return True