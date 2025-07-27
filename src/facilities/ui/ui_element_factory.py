"""UIElement作成の統一化ファクトリー

ServicePanelの重複したUI作成コードを統合し、
Template MethodパターンとFactory Methodパターンで整理します。
"""

import pygame
import pygame_gui
from typing import Optional, Dict, Any, List, Callable, Union
from abc import ABC, abstractmethod
import logging
from .ui_element_manager import UIElementManager

logger = logging.getLogger(__name__)


class UIElementCreationStrategy(ABC):
    """UI要素作成の戦略クラス"""
    
    @abstractmethod
    def create_element(self, element_type: str, element_id: str, 
                      rect: pygame.Rect, container: pygame_gui.core.UIContainer,
                      ui_manager: pygame_gui.UIManager, **kwargs) -> pygame_gui.core.UIElement:
        """UI要素を作成する"""
        pass


class ModernUICreationStrategy(UIElementCreationStrategy):
    """UIElementManagerを使った現代的な作成戦略"""
    
    def __init__(self, ui_element_manager: UIElementManager):
        self.ui_element_manager = ui_element_manager
    
    def create_element(self, element_type: str, element_id: str,
                      rect: pygame.Rect, container: pygame_gui.core.UIContainer,
                      ui_manager: pygame_gui.UIManager, **kwargs) -> pygame_gui.core.UIElement:
        """UIElementManagerを使ってUI要素を作成"""
        if self.ui_element_manager.is_destroyed:
            raise RuntimeError("UIElementManager is destroyed")
        
        creation_methods = {
            'label': self._create_label,
            'button': self._create_button,
            'text_box': self._create_text_box,
            'selection_list': self._create_selection_list,
            'text_entry': self._create_text_entry
        }
        
        method = creation_methods.get(element_type)
        if not method:
            raise ValueError(f"Unsupported element type: {element_type}")
        
        return method(element_id, rect, container, **kwargs)
    
    def _create_label(self, element_id: str, rect: pygame.Rect, 
                     container: pygame_gui.core.UIContainer, **kwargs) -> pygame_gui.elements.UILabel:
        text = kwargs.get('text', '')
        return self.ui_element_manager.create_label(element_id, text, rect, container)
    
    def _create_button(self, element_id: str, rect: pygame.Rect,
                      container: pygame_gui.core.UIContainer, **kwargs) -> pygame_gui.elements.UIButton:
        text = kwargs.get('text', '')
        on_click = kwargs.get('on_click')
        object_id = kwargs.get('object_id')
        return self.ui_element_manager.create_button(
            element_id, text, rect, container, on_click, object_id=object_id
        )
    
    def _create_text_box(self, element_id: str, rect: pygame.Rect,
                        container: pygame_gui.core.UIContainer, **kwargs) -> pygame_gui.elements.UITextBox:
        initial_text = kwargs.get('initial_text', '')
        return self.ui_element_manager.create_text_box(element_id, initial_text, rect, container)
    
    def _create_selection_list(self, element_id: str, rect: pygame.Rect,
                              container: pygame_gui.core.UIContainer, **kwargs) -> pygame_gui.elements.UISelectionList:
        item_list = kwargs.get('item_list', [])
        return self.ui_element_manager.create_selection_list(element_id, rect, item_list, container)
    
    def _create_text_entry(self, element_id: str, rect: pygame.Rect,
                          container: pygame_gui.core.UIContainer, **kwargs) -> pygame_gui.elements.UITextEntryLine:
        initial_text = kwargs.get('initial_text', '')
        placeholder_text = kwargs.get('placeholder_text', '')
        # 他のkwargsをフィルタリング
        filtered_kwargs = {k: v for k, v in kwargs.items() 
                          if k not in ['initial_text', 'placeholder_text']}
        return self.ui_element_manager.create_text_entry(
            element_id, rect, initial_text=initial_text, container=container,
            placeholder_text=placeholder_text, **filtered_kwargs
        )


class LegacyUICreationStrategy(UIElementCreationStrategy):
    """レガシーな直接作成戦略（フォールバック用）"""
    
    def __init__(self, ui_elements_list: List[pygame_gui.core.UIElement]):
        self.ui_elements_list = ui_elements_list
    
    def create_element(self, element_type: str, element_id: str,
                      rect: pygame.Rect, container: pygame_gui.core.UIContainer,
                      ui_manager: pygame_gui.UIManager, **kwargs) -> pygame_gui.core.UIElement:
        """直接pygame_guiを使ってUI要素を作成"""
        creation_methods = {
            'label': self._create_label,
            'button': self._create_button,
            'text_box': self._create_text_box,
            'selection_list': self._create_selection_list,
            'text_entry': self._create_text_entry
        }
        
        method = creation_methods.get(element_type)
        if not method:
            raise ValueError(f"Unsupported element type: {element_type}")
        
        element = method(rect, container, ui_manager, **kwargs)
        self.ui_elements_list.append(element)
        return element
    
    def _create_label(self, rect: pygame.Rect, container: pygame_gui.core.UIContainer,
                     ui_manager: pygame_gui.UIManager, **kwargs) -> pygame_gui.elements.UILabel:
        text = kwargs.get('text', '')
        return pygame_gui.elements.UILabel(
            relative_rect=rect,
            text=text,
            manager=ui_manager,
            container=container
        )
    
    def _create_button(self, rect: pygame.Rect, container: pygame_gui.core.UIContainer,
                      ui_manager: pygame_gui.UIManager, **kwargs) -> pygame_gui.elements.UIButton:
        text = kwargs.get('text', '')
        object_id = kwargs.get('object_id')
        return pygame_gui.elements.UIButton(
            relative_rect=rect,
            text=text,
            manager=ui_manager,
            container=container,
            object_id=object_id
        )
    
    def _create_text_box(self, rect: pygame.Rect, container: pygame_gui.core.UIContainer,
                        ui_manager: pygame_gui.UIManager, **kwargs) -> pygame_gui.elements.UITextBox:
        initial_text = kwargs.get('initial_text', '')
        return pygame_gui.elements.UITextBox(
            html_text=initial_text,
            relative_rect=rect,
            manager=ui_manager,
            container=container
        )
    
    def _create_selection_list(self, rect: pygame.Rect, container: pygame_gui.core.UIContainer,
                              ui_manager: pygame_gui.UIManager, **kwargs) -> pygame_gui.elements.UISelectionList:
        item_list = kwargs.get('item_list', [])
        return pygame_gui.elements.UISelectionList(
            relative_rect=rect,
            item_list=item_list,
            manager=ui_manager,
            container=container
        )
    
    def _create_text_entry(self, rect: pygame.Rect, container: pygame_gui.core.UIContainer,
                          ui_manager: pygame_gui.UIManager, **kwargs) -> pygame_gui.elements.UITextEntryLine:
        initial_text = kwargs.get('initial_text', '')
        placeholder_text = kwargs.get('placeholder_text', '')
        # 他のkwargsをフィルタリング
        filtered_kwargs = {k: v for k, v in kwargs.items() 
                          if k not in ['initial_text', 'placeholder_text']}
        return pygame_gui.elements.UITextEntryLine(
            relative_rect=rect,
            manager=ui_manager,
            container=container,
            initial_text=initial_text,
            placeholder_text=placeholder_text,
            **filtered_kwargs
        )


class UIElementFactory:
    """UI要素作成の統一ファクトリー（Template Method適用）
    
    ServicePanelの重複したUI作成処理を統一し、
    戦略パターンで実装方法を切り替え可能にします。
    """
    
    def __init__(self, ui_manager: pygame_gui.UIManager, container: pygame_gui.core.UIContainer,
                 ui_element_manager: Optional[UIElementManager] = None,
                 ui_elements_list: Optional[List[pygame_gui.core.UIElement]] = None):
        """初期化
        
        Args:
            ui_manager: pygame_gui UIManager
            container: デフォルトコンテナ
            ui_element_manager: UIElementManager（現代的な作成戦略用）
            ui_elements_list: UI要素リスト（レガシー戦略用）
        """
        self.ui_manager = ui_manager
        self.default_container = container
        self.button_index_counter = 0
        
        # 戦略を決定
        if ui_element_manager and not ui_element_manager.is_destroyed:
            self.strategy = ModernUICreationStrategy(ui_element_manager)
        else:
            if ui_elements_list is None:
                ui_elements_list = []
            self.strategy = LegacyUICreationStrategy(ui_elements_list)
        
        logger.debug(f"UIElementFactory initialized with {type(self.strategy).__name__}")
    
    def create_label(self, element_id: str, text: str, rect: pygame.Rect,
                    container: Optional[pygame_gui.core.UIContainer] = None) -> pygame_gui.elements.UILabel:
        """ラベルを作成（Template Method）"""
        return self._create_element('label', element_id, rect, container, text=text)
    
    def create_button(self, element_id: str, text: str, rect: pygame.Rect,
                     container: Optional[pygame_gui.core.UIContainer] = None,
                     object_id: Optional[str] = None,
                     on_click: Optional[Callable] = None) -> pygame_gui.elements.UIButton:
        """ボタンを作成（Template Method + ショートカット機能）"""
        button = self._create_element('button', element_id, rect, container,
                                     text=text, object_id=object_id, on_click=on_click)
        
        # ショートカットキー情報を設定
        self._assign_shortcut_key(button)
        return button
    
    def create_text_box(self, element_id: str, initial_text: str, rect: pygame.Rect,
                       container: Optional[pygame_gui.core.UIContainer] = None) -> pygame_gui.elements.UITextBox:
        """テキストボックスを作成（Template Method）"""
        return self._create_element('text_box', element_id, rect, container, initial_text=initial_text)
    
    def create_selection_list(self, element_id: str, rect: pygame.Rect, item_list: List[str],
                             container: Optional[pygame_gui.core.UIContainer] = None) -> pygame_gui.elements.UISelectionList:
        """選択リストを作成（Template Method）"""
        return self._create_element('selection_list', element_id, rect, container, item_list=item_list)
    
    def create_text_entry(self, element_id: str, rect: pygame.Rect,
                         initial_text: str = "", placeholder_text: str = "",
                         container: Optional[pygame_gui.core.UIContainer] = None,
                         **kwargs) -> pygame_gui.elements.UITextEntryLine:
        """テキスト入力フィールドを作成（Template Method）"""
        return self._create_element('text_entry', element_id, rect, container,
                                   initial_text=initial_text, placeholder_text=placeholder_text, **kwargs)
    
    def _create_element(self, element_type: str, element_id: str, rect: pygame.Rect,
                       container: Optional[pygame_gui.core.UIContainer], **kwargs) -> pygame_gui.core.UIElement:
        """Template Method: UI要素作成の共通テンプレート"""
        # コンテナのデフォルト値設定
        if container is None:
            container = self.default_container
        
        # 戦略を使用して要素を作成
        try:
            element = self.strategy.create_element(
                element_type, element_id, rect, container, self.ui_manager, **kwargs
            )
            logger.debug(f"Created {element_type} '{element_id}' using {type(self.strategy).__name__}")
            return element
        except Exception as e:
            logger.error(f"Failed to create {element_type} '{element_id}': {e}")
            raise
    
    def _assign_shortcut_key(self, button: pygame_gui.elements.UIButton) -> None:
        """ボタンにショートカットキーを割り当て"""
        if self.button_index_counter < 9:  # 1-9の数字キーまで対応
            button.button_index = self.button_index_counter
            button.shortcut_key = str(self.button_index_counter + 1)
            self.button_index_counter += 1
    
    def reset_button_counter(self) -> None:
        """ボタンカウンターをリセット"""
        self.button_index_counter = 0
    
    def get_strategy_type(self) -> str:
        """現在の戦略タイプを取得（デバッグ用）"""
        return type(self.strategy).__name__