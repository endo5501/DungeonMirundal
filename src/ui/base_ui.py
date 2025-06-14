"""基本UIシステム"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Callable, Any
from enum import Enum
from direct.gui.DirectGui import *
from direct.gui.OnscreenText import OnscreenText
from panda3d.core import TextNode, Vec3
from src.core.config_manager import config_manager
from src.utils.logger import logger


class UIState(Enum):
    """UI状態"""
    HIDDEN = "hidden"
    VISIBLE = "visible"
    MODAL = "modal"


class UIElement:
    """UI要素の基底クラス"""
    
    def __init__(self, element_id: str):
        self.element_id = element_id
        self.state = UIState.HIDDEN
        self.gui_element = None
        self.parent = None
        self.children: List['UIElement'] = []
        
    def show(self):
        """要素を表示"""
        if self.gui_element:
            self.gui_element.show()
        self.state = UIState.VISIBLE
        logger.debug(f"UI要素を表示: {self.element_id}")
    
    def hide(self):
        """要素を非表示"""
        if self.gui_element:
            self.gui_element.hide()
        self.state = UIState.HIDDEN
        logger.debug(f"UI要素を非表示: {self.element_id}")
    
    def destroy(self):
        """要素を破棄"""
        if self.gui_element:
            self.gui_element.destroy()
        self.gui_element = None
        self.state = UIState.HIDDEN
        logger.debug(f"UI要素を破棄: {self.element_id}")
    
    def add_child(self, child: 'UIElement'):
        """子要素を追加"""
        child.parent = self
        self.children.append(child)
    
    def remove_child(self, child: 'UIElement'):
        """子要素を削除"""
        if child in self.children:
            child.parent = None
            self.children.remove(child)


class UIText(UIElement):
    """テキスト表示UI要素"""
    
    def __init__(
        self, 
        element_id: str, 
        text: str,
        pos: tuple = (0, 0),
        scale: float = 0.05,
        color: tuple = (1, 1, 1, 1),
        align: str = "center"
    ):
        super().__init__(element_id)
        
        align_map = {
            "left": TextNode.ALeft,
            "center": TextNode.ACenter,
            "right": TextNode.ARight
        }
        
        self.gui_element = OnscreenText(
            text=text,
            pos=pos,
            scale=scale,
            fg=color,
            align=align_map.get(align, TextNode.ACenter)
        )
        self.hide()  # 初期状態は非表示
    
    def set_text(self, text: str):
        """テキストを設定"""
        if self.gui_element:
            self.gui_element.setText(text)


class UIButton(UIElement):
    """ボタンUI要素"""
    
    def __init__(
        self,
        element_id: str,
        text: str,
        pos: tuple = (0, 0),
        scale: tuple = (0.3, 0.3),
        command: Optional[Callable] = None,
        extraArgs: List = None
    ):
        super().__init__(element_id)
        
        self.command = command
        self.extraArgs = extraArgs or []
        
        self.gui_element = DirectButton(
            text=text,
            pos=Vec3(pos[0], 0, pos[1]),
            scale=Vec3(scale[0], 1, scale[1]),
            command=self._on_click,
            text_scale=0.8,
            relief=DGG.RAISED,
            borderWidth=(0.01, 0.01)
        )
        self.hide()
    
    def _on_click(self):
        """ボタンクリック時の処理"""
        logger.debug(f"ボタンがクリックされました: {self.element_id}")
        if self.command:
            self.command(*self.extraArgs)


class UIMenu(UIElement):
    """メニューUI要素"""
    
    def __init__(self, element_id: str, title: str = ""):
        super().__init__(element_id)
        self.title = title
        self.menu_items: List[Dict[str, Any]] = []
        self.title_text = None
        self.buttons: List[UIButton] = []
        
        if title:
            self.title_text = UIText(
                f"{element_id}_title",
                title,
                pos=(0, 0.8),
                scale=0.08,
                color=(1, 1, 0, 1)
            )
    
    def add_menu_item(self, text: str, command: Callable, args: List = None):
        """メニュー項目を追加"""
        self.menu_items.append({
            'text': text,
            'command': command,
            'args': args or []
        })
        self._rebuild_menu()
    
    def _rebuild_menu(self):
        """メニューを再構築"""
        # 既存ボタンを削除
        for button in self.buttons:
            button.destroy()
        self.buttons.clear()
        
        # 新しいボタンを作成
        start_y = 0.4
        spacing = 0.15
        
        for i, item in enumerate(self.menu_items):
            button = UIButton(
                f"{self.element_id}_btn_{i}",
                item['text'],
                pos=(0, start_y - i * spacing),
                command=item['command'],
                extraArgs=item['args']
            )
            self.buttons.append(button)
            self.add_child(button)
    
    def show(self):
        """メニューを表示"""
        super().show()
        if self.title_text:
            self.title_text.show()
        for button in self.buttons:
            button.show()
    
    def hide(self):
        """メニューを非表示"""
        super().hide()
        if self.title_text:
            self.title_text.hide()
        for button in self.buttons:
            button.hide()
    
    def destroy(self):
        """メニューを破棄"""
        if self.title_text:
            self.title_text.destroy()
        for button in self.buttons:
            button.destroy()
        super().destroy()


class UIDialog(UIElement):
    """ダイアログUI要素"""
    
    def __init__(
        self, 
        element_id: str, 
        title: str, 
        message: str,
        buttons: List[Dict[str, Any]] = None
    ):
        super().__init__(element_id)
        self.title = title
        self.message = message
        
        # 背景
        self.background = DirectFrame(
            frameColor=(0, 0, 0, 0.8),
            frameSize=(-1.5, 1.5, -1, 1),
            pos=(0, 0, 0)
        )
        
        # タイトル
        self.title_text = UIText(
            f"{element_id}_title",
            title,
            pos=(0, 0.6),
            scale=0.06,
            color=(1, 1, 0, 1)
        )
        
        # メッセージ
        self.message_text = UIText(
            f"{element_id}_message",
            message,
            pos=(0, 0.2),
            scale=0.05,
            color=(1, 1, 1, 1)
        )
        
        # ボタン
        self.dialog_buttons = []
        if buttons:
            self._create_buttons(buttons)
        
        self.hide()
    
    def _create_buttons(self, buttons: List[Dict[str, Any]]):
        """ダイアログボタンを作成"""
        button_count = len(buttons)
        start_x = -(button_count - 1) * 0.3 / 2
        
        for i, btn_config in enumerate(buttons):
            button = UIButton(
                f"{self.element_id}_btn_{i}",
                btn_config.get('text', 'OK'),
                pos=(start_x + i * 0.3, -0.3),
                command=btn_config.get('command'),
                extraArgs=btn_config.get('args', [])
            )
            self.dialog_buttons.append(button)
    
    def show(self):
        """ダイアログを表示"""
        super().show()
        self.state = UIState.MODAL
        self.background.show()
        self.title_text.show()
        self.message_text.show()
        for button in self.dialog_buttons:
            button.show()
    
    def hide(self):
        """ダイアログを非表示"""
        super().hide()
        self.background.hide()
        self.title_text.hide()
        self.message_text.hide()
        for button in self.dialog_buttons:
            button.hide()
    
    def destroy(self):
        """ダイアログを破棄"""
        self.background.destroy()
        self.title_text.destroy()
        self.message_text.destroy()
        for button in self.dialog_buttons:
            button.destroy()
        super().destroy()


class UIManager:
    """UI管理システム"""
    
    def __init__(self):
        self.ui_elements: Dict[str, UIElement] = {}
        self.ui_stack: List[str] = []  # 表示順序管理
        self.modal_element: Optional[str] = None
        
        logger.info("UIManagerを初期化しました")
    
    def register_element(self, element: UIElement):
        """UI要素を登録"""
        self.ui_elements[element.element_id] = element
        logger.debug(f"UI要素を登録: {element.element_id}")
    
    def unregister_element(self, element_id: str):
        """UI要素の登録を解除"""
        if element_id in self.ui_elements:
            element = self.ui_elements[element_id]
            element.destroy()
            del self.ui_elements[element_id]
            
            if element_id in self.ui_stack:
                self.ui_stack.remove(element_id)
            
            if self.modal_element == element_id:
                self.modal_element = None
            
            logger.debug(f"UI要素の登録を解除: {element_id}")
    
    def show_element(self, element_id: str, modal: bool = False):
        """UI要素を表示"""
        if element_id not in self.ui_elements:
            logger.warning(f"UI要素が見つかりません: {element_id}")
            return
        
        element = self.ui_elements[element_id]
        
        # モーダル処理
        if modal:
            if self.modal_element:
                self.hide_element(self.modal_element)
            self.modal_element = element_id
            element.state = UIState.MODAL
        
        element.show()
        
        # スタック管理
        if element_id in self.ui_stack:
            self.ui_stack.remove(element_id)
        self.ui_stack.append(element_id)
        
        logger.debug(f"UI要素を表示: {element_id} (modal: {modal})")
    
    def hide_element(self, element_id: str):
        """UI要素を非表示"""
        if element_id not in self.ui_elements:
            logger.warning(f"UI要素が見つかりません: {element_id}")
            return
        
        element = self.ui_elements[element_id]
        element.hide()
        
        if element_id in self.ui_stack:
            self.ui_stack.remove(element_id)
        
        if self.modal_element == element_id:
            self.modal_element = None
        
        logger.debug(f"UI要素を非表示: {element_id}")
    
    def hide_all(self):
        """全UI要素を非表示"""
        for element_id in self.ui_stack.copy():
            self.hide_element(element_id)
        
        self.modal_element = None
        logger.debug("全UI要素を非表示にしました")
    
    def get_element(self, element_id: str) -> Optional[UIElement]:
        """UI要素を取得"""
        return self.ui_elements.get(element_id)
    
    def is_modal_active(self) -> bool:
        """モーダルがアクティブかチェック"""
        return self.modal_element is not None
    
    def get_text(self, key: str) -> str:
        """テキストキーから表示テキストを取得"""
        return config_manager.get_text(key)
    
    def cleanup(self):
        """リソースのクリーンアップ"""
        for element in self.ui_elements.values():
            element.destroy()
        
        self.ui_elements.clear()
        self.ui_stack.clear()
        self.modal_element = None
        
        logger.info("UIManagerをクリーンアップしました")


# グローバルインスタンス
ui_manager = UIManager()