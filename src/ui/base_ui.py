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
        
        # フォント設定
        try:
            from src.ui.font_manager import font_manager
            font = font_manager.get_default_font()
        except:
            font = None
        
        self.gui_element = OnscreenText(
            text=text,
            pos=pos,
            scale=scale,
            fg=color,
            align=align_map.get(align, TextNode.ACenter),
            font=font
        )
        self.hide()  # 初期状態は非表示
    
    def set_text(self, text: str):
        """テキストを設定"""
        if self.gui_element:
            self.gui_element.setText(text)
    
    def set_position(self, x: float, y: float):
        """テキストの位置を設定"""
        if self.gui_element:
            # 複数の方法を試して確実に位置を設定
            try:
                self.gui_element.setPos(x, y)
            except:
                try:
                    self.gui_element['pos'] = (x, y)
                except:
                    try:
                        self.gui_element.configure(pos=(x, y))
                    except:
                        pass


class UIButton(UIElement):
    """ボタンUI要素"""
    
    def __init__(
        self,
        element_id: str,
        text: str,
        pos: tuple = (0, 0),
        scale: tuple = (0.3, 0.3),
        command: Optional[Callable] = None,
        extraArgs: List = None,
        text_scale: float = 0.45
    ):
        super().__init__(element_id)
        
        self.command = command
        self.extraArgs = extraArgs or []
        
        # フォント設定
        try:
            from src.ui.font_manager import font_manager
            font = font_manager.get_default_font()
        except:
            font = None
        
        self.gui_element = DirectButton(
            text=text,
            pos=Vec3(pos[0], 0, pos[1]),
            scale=Vec3(scale[0], 1, scale[1]),
            command=self._on_click,
            text_scale=text_scale,  # カスタマイズ可能なフォントサイズ
            relief=DGG.RAISED,
            borderWidth=(0.01, 0.01),
            text_font=font
        )
        self.hide()
    
    def _on_click(self):
        """ボタンクリック時の処理"""
        logger.debug(f"ボタンがクリックされました: {self.element_id}")
        if self.command:
            self.command(*self.extraArgs)


class UIMenu(UIElement):
    """メニューUI要素"""
    
    def __init__(self, element_id: str, title: str = "", alignment: str = "center", 
                 character_creation_mode: bool = False):
        super().__init__(element_id)
        self.title = title
        self.alignment = alignment  # "left", "center", "right"
        self.character_creation_mode = character_creation_mode  # キャラクター作成画面専用モード
        self.menu_items: List[Dict[str, Any]] = []
        self.title_text = None
        self.buttons: List[UIButton] = []
        
        if title:
            # タイトルの位置をalignmentに応じて調整
            title_x = self._get_title_x_position()
            self.title_text = UIText(
                f"{element_id}_title",
                title,
                pos=(title_x, 0.75),
                scale=0.05,  # タイトルのフォントサイズをさらに小さく
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
        """メニューを再構築（横一列配置）"""
        # 既存ボタンを削除
        for button in self.buttons:
            button.destroy()
        self.buttons.clear()
        
        # ボタンを横一列で下部に配置
        button_count = len(self.menu_items)
        if button_count == 0:
            return
        
        # 横配置の設定
        if self.character_creation_mode:
            button_spacing = 0.3  # キャラクター作成画面では広めの間隔
            button_y = -0.45  # キャラクター作成画面では更に下部に配置
        elif self.alignment == "left":
            button_spacing = 0.25  # 左寄せ時は間隔を縮める
            button_y = -0.4  # 下部固定位置
        else:
            button_spacing = 0.4  # 通常の間隔
            button_y = -0.4  # 下部固定位置
        start_x = self._get_button_start_x(button_count, button_spacing)
        
        # ボタンサイズを調整（項目数に応じて）
        if self.character_creation_mode:
            button_scale = (0.25, 0.12)  # キャラクター作成画面では小さめサイズ
        elif button_count <= 4:
            button_scale = (0.3, 0.15)  # 通常サイズ
        else:
            button_scale = (0.25, 0.12)  # 小さめサイズ
        
        for i, item in enumerate(self.menu_items):
            # キャラクター作成モード時は小さいフォント使用
            text_scale = 0.35 if self.character_creation_mode else 0.45
            button = UIButton(
                f"{self.element_id}_btn_{i}",
                item['text'],
                pos=(start_x + i * button_spacing, button_y),
                scale=button_scale,
                command=item['command'],
                extraArgs=item['args'],
                text_scale=text_scale
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
    
    def _get_title_x_position(self) -> float:
        """alignmentに応じたタイトルのX座標を取得"""
        if self.alignment == "left":
            return -1.0  # 左寄せ
        elif self.alignment == "right":
            return 1.0   # 右寄せ
        else:  # center (default)
            return 0.0   # 中央
    
    def _get_button_start_x(self, button_count: int, button_spacing: float) -> float:
        """alignmentに応じたボタン開始X座標を計算"""
        if self.alignment == "left":
            # 左寄せ：固定位置から開始
            return -1.3
        elif self.alignment == "right":
            # 右寄せ：右端から左に向かって配置
            total_width = (button_count - 1) * button_spacing
            return 1.3 - total_width
        else:  # center (default)
            # 中央揃え：中央を基準に左右に展開
            return -(button_count - 1) * button_spacing / 2


class UIDialog(UIElement):
    """ダイアログUI要素"""
    
    def __init__(
        self, 
        element_id: str, 
        title: str, 
        message: str,
        buttons: List[Dict[str, Any]] = None,
        alignment: str = "center",
        character_creation_mode: bool = False
    ):
        super().__init__(element_id)
        self.title = title
        self.message = message
        self.alignment = alignment
        self.character_creation_mode = character_creation_mode
        
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
        button_spacing = 0.6 if self.character_creation_mode else 0.5  # キャラクター作成時は間隔拡大
        start_x = self._get_dialog_button_start_x(button_count, button_spacing)
        button_y = -0.35 if self.character_creation_mode else -0.3  # キャラクター作成時は下部配置
        
        for i, btn_config in enumerate(buttons):
            # キャラクター作成モード時は小さいフォント使用
            text_scale = 0.35 if self.character_creation_mode else 0.45
            button_scale = (0.35, 0.25) if self.character_creation_mode else (0.4, 0.3)
            
            button = UIButton(
                f"{self.element_id}_btn_{i}",
                btn_config.get('text', 'OK'),
                pos=(start_x + i * button_spacing, button_y),
                scale=button_scale,
                command=btn_config.get('command'),
                extraArgs=btn_config.get('args', []),
                text_scale=text_scale
            )
            self.dialog_buttons.append(button)
    
    def _get_dialog_button_start_x(self, button_count: int, button_spacing: float) -> float:
        """alignmentに応じたダイアログボタン開始X座標を計算"""
        if self.alignment == "left":
            # 左寄せ：固定位置から開始
            return -1.0
        elif self.alignment == "right":
            # 右寄せ：右端から左に向かって配置
            total_width = (button_count - 1) * button_spacing
            return 1.0 - total_width
        else:  # center (default)
            # 中央揃え：中央を基準に左右に展開
            return -(button_count - 1) * button_spacing / 2
    
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


class UITextInput(UIElement):
    """テキスト入力UI要素"""
    
    def __init__(
        self, 
        element_id: str, 
        initial_text: str = "",
        max_chars: int = 20,
        placeholder: str = "",
        pos: tuple = (0, 0, 0),
        width: float = 10.0,
        on_change: Optional[Callable[[str], None]] = None
    ):
        super().__init__(element_id)
        self.initial_text = initial_text
        self.max_chars = max_chars
        self.placeholder = placeholder
        self.on_change = on_change
        self.current_text = initial_text
        
        # DirectEntryを使用したテキスト入力フィールド
        self.text_input = DirectEntry(
            text=initial_text,
            scale=0.05,
            pos=pos,
            width=width,
            numLines=1,
            focus=False,
            command=self._on_text_submit,
            focusInCommand=self._on_focus_in,
            focusOutCommand=self._on_focus_out,
            frameColor=(1, 1, 1, 0.8),
            text_fg=(0, 0, 0, 1),
            rolloverSound=None,
            clickSound=None
        )
        
        # プレースホルダーテキスト
        if placeholder and not initial_text:
            self.text_input.set(placeholder)
            self.text_input['text_fg'] = (0.5, 0.5, 0.5, 1)
        
        self.gui_element = self.text_input
        self.is_placeholder_shown = bool(placeholder and not initial_text)
        
        logger.debug(f"テキスト入力を作成: {element_id}")
    
    def _on_text_submit(self, text):
        """テキスト送信時のコールバック"""
        self.current_text = text
        if self.on_change:
            self.on_change(text)
        logger.debug(f"テキスト入力送信: {text}")
    
    def _on_focus_in(self):
        """フォーカス取得時の処理"""
        if self.is_placeholder_shown:
            self.text_input.set("")
            self.text_input['text_fg'] = (0, 0, 0, 1)
            self.is_placeholder_shown = False
        logger.debug(f"テキスト入力フォーカス取得: {self.element_id}")
    
    def _on_focus_out(self):
        """フォーカス失失時の処理"""
        current_text = self.text_input.get()
        if not current_text and self.placeholder:
            self.text_input.set(self.placeholder)
            self.text_input['text_fg'] = (0.5, 0.5, 0.5, 1)
            self.is_placeholder_shown = True
        else:
            self.current_text = current_text
        logger.debug(f"テキスト入力フォーカス失失: {self.element_id}")
    
    def get_text(self) -> str:
        """現在のテキストを取得"""
        if self.is_placeholder_shown:
            return ""
        return self.text_input.get()
    
    def set_text(self, text: str):
        """テキストを設定"""
        self.text_input.set(text)
        self.current_text = text
        self.is_placeholder_shown = False
        if text:
            self.text_input['text_fg'] = (0, 0, 0, 1)
    
    def clear(self):
        """テキストをクリア"""
        self.text_input.set("")
        self.current_text = ""
        self.is_placeholder_shown = False
    
    def set_focus(self, focus: bool = True):
        """フォーカスを設定"""
        if focus:
            self.text_input['focus'] = True
        else:
            self.text_input['focus'] = False
    
    def is_empty(self) -> bool:
        """テキストが空かチェック"""
        return not self.get_text()
    
    def destroy(self):
        """テキスト入力を破棄"""
        if self.text_input:
            self.text_input.destroy()
        super().destroy()


class UIInputDialog(UIElement):
    """テキスト入力付きダイアログ"""
    
    def __init__(
        self,
        element_id: str,
        title: str,
        message: str,
        initial_text: str = "",
        placeholder: str = "",
        on_confirm: Optional[Callable[[str], None]] = None,
        on_cancel: Optional[Callable] = None
    ):
        super().__init__(element_id)
        self.title = title
        self.message = message
        self.on_confirm = on_confirm
        self.on_cancel = on_cancel
        
        # 背景
        self.background = DirectFrame(
            frameColor=(0, 0, 0, 0.8),
            frameSize=(-1.5, 1.5, -1.0, 0.8),
            pos=(0, 0, 0)
        )
        
        # タイトル
        self.title_text = UIText(
            f"{element_id}_title",
            title,
            pos=(0, 0, 0.5),
            scale=0.05,
            color=(1, 1, 0.8, 1)
        )
        
        # メッセージ
        self.message_text = UIText(
            f"{element_id}_message", 
            message,
            pos=(0, 0, 0.2),
            scale=0.04,
            color=(0.9, 0.9, 0.9, 1)
        )
        
        # テキスト入力
        self.text_input = UITextInput(
            f"{element_id}_input",
            initial_text=initial_text,
            placeholder=placeholder,
            pos=(0, 0, -0.1),
            width=15.0
        )
        
        # フォント取得
        try:
            from src.ui.font_manager import font_manager
            font = font_manager.get_default_font()
        except:
            font = None
        
        # ボタン
        self.ok_button = DirectButton(
            text="OK",
            scale=0.06,
            pos=(-0.3, 0, -0.4),
            command=self._on_ok,
            frameColor=(0.2, 0.7, 0.2, 1),
            text_fg=(1, 1, 1, 1),
            text_font=font,
            rolloverSound=None,
            clickSound=None
        )
        
        self.cancel_button = DirectButton(
            text="キャンセル",
            scale=0.06,
            pos=(0.3, 0, -0.4),
            command=self._on_cancel,
            frameColor=(0.7, 0.2, 0.2, 1),
            text_fg=(1, 1, 1, 1),
            text_font=font,
            rolloverSound=None,
            clickSound=None
        )
        
        self.gui_element = self.background
        
        # 子要素リスト
        self.child_elements = [
            self.title_text, 
            self.message_text, 
            self.text_input,
            self.ok_button,
            self.cancel_button
        ]
        
        logger.debug(f"入力ダイアログを作成: {element_id}")
    
    def _on_ok(self):
        """OKボタンが押された時の処理"""
        text = self.text_input.get_text()
        if self.on_confirm:
            self.on_confirm(text)
    
    def _on_cancel(self):
        """キャンセルボタンが押された時の処理"""
        if self.on_cancel:
            self.on_cancel()
    
    def show(self):
        """ダイアログを表示"""
        super().show()
        self.title_text.show()
        self.message_text.show()
        self.text_input.show()
        self.ok_button.show()
        self.cancel_button.show()
        
        # テキスト入力にフォーカスを設定
        self.text_input.set_focus(True)
    
    def hide(self):
        """ダイアログを非表示"""
        super().hide()
        for element in self.child_elements:
            if hasattr(element, 'hide'):
                element.hide()
            else:
                element.hide()
    
    def destroy(self):
        """ダイアログを破棄"""
        for element in self.child_elements:
            if hasattr(element, 'destroy'):
                element.destroy()
            else:
                element.destroy()
        
        if self.ok_button:
            self.ok_button.destroy()
        if self.cancel_button:
            self.cancel_button.destroy()
            
        super().destroy()


# グローバルインスタンス
ui_manager = UIManager()