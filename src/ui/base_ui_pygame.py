"""基本UIシステム（Pygame版）"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Callable, Any, Tuple
from enum import Enum
import pygame
from src.core.config_manager import config_manager
from src.utils.logger import logger


class UIState(Enum):
    """UI状態"""
    HIDDEN = "hidden"
    VISIBLE = "visible"
    MODAL = "modal"


class UIAlignment(Enum):
    """UI配置"""
    LEFT = "left"
    CENTER = "center"
    RIGHT = "right"
    TOP = "top"
    MIDDLE = "middle"
    BOTTOM = "bottom"


class UIElement:
    """UI要素の基底クラス（Pygame版）"""
    
    def __init__(self, element_id: str, x: int = 0, y: int = 0, width: int = 100, height: int = 30):
        self.element_id = element_id
        self.state = UIState.HIDDEN
        self.rect = pygame.Rect(x, y, width, height)
        self.parent = None
        self.children: List['UIElement'] = []
        
        # 描画設定
        self.background_color = (50, 50, 50)
        self.border_color = (100, 100, 100)
        self.text_color = (255, 255, 255)
        self.border_width = 1
        
        # イベントハンドラー
        self.on_click: Optional[Callable] = None
        self.on_hover: Optional[Callable] = None
        
        # 状態
        self.is_hovered = False
        self.is_pressed = False
        
    def show(self):
        """要素を表示"""
        self.state = UIState.VISIBLE
        logger.debug(f"UI要素を表示: {self.element_id}")
    
    def hide(self):
        """要素を非表示"""
        self.state = UIState.HIDDEN
        logger.debug(f"UI要素を非表示: {self.element_id}")
    
    def destroy(self):
        """要素を破棄"""
        self.state = UIState.HIDDEN
        logger.debug(f"UI要素を破棄: {self.element_id}")
    
    def handle_event(self, event: pygame.event.Event) -> bool:
        """イベント処理"""
        if self.state != UIState.VISIBLE:
            return False
        
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.rect.collidepoint(event.pos):
                self.is_pressed = True
                if self.on_click:
                    self.on_click()
                return True
        
        elif event.type == pygame.MOUSEBUTTONUP:
            if self.is_pressed:
                self.is_pressed = False
                return True
        
        elif event.type == pygame.MOUSEMOTION:
            old_hovered = self.is_hovered
            self.is_hovered = self.rect.collidepoint(event.pos)
            
            if self.is_hovered and not old_hovered and self.on_hover:
                self.on_hover()
        
        return False
    
    def render(self, screen: pygame.Surface, font: Optional[pygame.font.Font] = None):
        """描画処理"""
        if self.state != UIState.VISIBLE:
            return
        
        # 背景描画
        bg_color = self.background_color
        if self.is_hovered:
            bg_color = tuple(min(255, c + 30) for c in bg_color)
        if self.is_pressed:
            bg_color = tuple(max(0, c - 30) for c in bg_color)
        
        pygame.draw.rect(screen, bg_color, self.rect)
        
        # ボーダー描画
        if self.border_width > 0:
            pygame.draw.rect(screen, self.border_color, self.rect, self.border_width)


class UIText(UIElement):
    """テキスト表示要素"""
    
    def __init__(self, element_id: str, text: str, x: int = 0, y: int = 0, 
                 font_size: int = 24, alignment: UIAlignment = UIAlignment.LEFT):
        super().__init__(element_id, x, y)
        self.text = text
        self.font_size = font_size
        self.alignment = alignment
        self.font = None
        
        # テキスト専用設定
        self.background_color = (0, 0, 0, 0)  # 透明
        self.border_width = 0
        
    def set_font(self, font: pygame.font.Font):
        """フォントを設定"""
        self.font = font
        # テキストサイズに合わせてrectを調整
        if font and self.text:
            text_surface = font.render(self.text, True, self.text_color)
            self.rect.width = text_surface.get_width()
            self.rect.height = text_surface.get_height()
    
    def render(self, screen: pygame.Surface, font: Optional[pygame.font.Font] = None):
        """テキスト描画（安全なフォントレンダリング）"""
        if self.state != UIState.VISIBLE or not self.text:
            return
        
        # フォントを決定
        use_font = self.font or font
        
        # フォントマネージャーを使用してフォントを取得
        if not use_font:
            try:
                from src.ui.font_manager_pygame import font_manager
                use_font = font_manager.get_japanese_font(24)
                if not use_font:
                    use_font = font_manager.get_default_font()
            except Exception as e:
                logger.warning(f"フォントマネージャーの取得に失敗: {e}")
                try:
                    # システムフォントで日本語フォントを試す
                    use_font = pygame.font.SysFont('notosanscjk,noto,ipagothic,takao,hiragino,meiryo,msgothic', 24)
                except:
                    try:
                        use_font = pygame.font.Font(None, 24)
                    except:
                        return  # フォントが取得できない場合は描画しない
        
        # テキストをレンダリング
        try:
            text_surface = use_font.render(self.text, True, self.text_color)
        except Exception as e:
            logger.warning(f"テキストレンダリングエラー: {e}")
            # フォールバック：システムフォント使用
            try:
                fallback_font = pygame.font.Font(None, 24)
                text_surface = fallback_font.render(self.text, True, self.text_color)
            except:
                return  # 最終的にも失敗した場合は描画しない
        
        # 配置を計算
        text_rect = text_surface.get_rect()
        if self.alignment == UIAlignment.CENTER:
            text_rect.center = self.rect.center
        elif self.alignment == UIAlignment.RIGHT:
            text_rect.right = self.rect.right
            text_rect.centery = self.rect.centery
        else:  # LEFT
            text_rect.left = self.rect.left
            text_rect.centery = self.rect.centery
        
        screen.blit(text_surface, text_rect)


class UIButton(UIElement):
    """ボタン要素"""
    
    def __init__(self, element_id: str, text: str, x: int = 0, y: int = 0, 
                 width: int = 120, height: int = 40):
        super().__init__(element_id, x, y, width, height)
        self.text = text
        
        # ボタン専用色設定
        self.background_color = (70, 70, 70)
        self.border_color = (150, 150, 150)
        
    def render(self, screen: pygame.Surface, font: Optional[pygame.font.Font] = None):
        """ボタン描画（安全なフォントレンダリング）"""
        if self.state != UIState.VISIBLE:
            return
        
        # 背景描画
        super().render(screen, font)
        
        # テキスト描画
        if self.text:
            # フォントを決定
            use_font = font
            if not use_font:
                try:
                    from src.ui.font_manager_pygame import font_manager
                    use_font = font_manager.get_japanese_font(24)
                    if not use_font:
                        use_font = font_manager.get_default_font()
                except Exception as e:
                    logger.warning(f"フォントマネージャーの取得に失敗: {e}")
                    try:
                        # システムフォントで日本語フォントを試す
                        use_font = pygame.font.SysFont('notosanscjk,noto,ipagothic,takao,hiragino,meiryo,msgothic', 24)
                    except:
                        try:
                            use_font = pygame.font.Font(None, 24)
                        except:
                            return  # フォントが取得できない場合は描画しない
            
            # テキストをレンダリング
            try:
                text_surface = use_font.render(self.text, True, self.text_color)
                text_rect = text_surface.get_rect(center=self.rect.center)
                screen.blit(text_surface, text_rect)
            except Exception as e:
                logger.warning(f"ボタンテキストレンダリングエラー: {e}")
                # フォールバック：システムフォント使用
                try:
                    fallback_font = pygame.font.Font(None, 24)
                    text_surface = fallback_font.render(self.text, True, self.text_color)
                    text_rect = text_surface.get_rect(center=self.rect.center)
                    screen.blit(text_surface, text_rect)
                except:
                    pass  # 最終的にも失敗した場合は背景のみ描画


class UIMenu:
    """メニューシステム"""
    
    def __init__(self, menu_id: str, title: str = ""):
        self.menu_id = menu_id
        self.title = title
        self.elements: List[UIElement] = []
        self.state = UIState.HIDDEN
        self.selected_index = 0
        
        # メニュー設定
        self.background_color = (30, 30, 30, 200)
        self.title_color = (255, 255, 255)
        
    def add_element(self, element: UIElement):
        """要素を追加"""
        self.elements.append(element)
        element.parent = self
    
    def add_menu_item(self, text: str, callback: callable, args: list = None):
        """メニュー項目を追加（Panda3D互換性のため）"""
        # メニュー項目の位置を自動計算
        item_count = len(self.elements)
        x = 300  # 中央寄り
        y = 150 + (item_count * 50)  # 上から順に配置
        
        button = UIButton(f"{self.menu_id}_item_{len(self.elements)}", text, 
                         x=x, y=y, width=200, height=40)
        if args:
            button.on_click = lambda: callback(*args)
        else:
            button.on_click = callback
        self.add_element(button)
    
    def show(self):
        """メニューを表示"""
        self.state = UIState.VISIBLE
        for element in self.elements:
            element.show()
    
    def hide(self):
        """メニューを非表示"""
        self.state = UIState.HIDDEN
        for element in self.elements:
            element.hide()
    
    def handle_event(self, event: pygame.event.Event) -> bool:
        """イベント処理"""
        if self.state != UIState.VISIBLE:
            return False
        
        # キーボードナビゲーション
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_UP:
                self.selected_index = max(0, self.selected_index - 1)
                return True
            elif event.key == pygame.K_DOWN:
                self.selected_index = min(len(self.elements) - 1, self.selected_index + 1)
                return True
            elif event.key == pygame.K_RETURN or event.key == pygame.K_SPACE:
                if 0 <= self.selected_index < len(self.elements):
                    element = self.elements[self.selected_index]
                    if element.on_click:
                        element.on_click()
                return True
        
        # 各要素のイベント処理
        for element in self.elements:
            if element.handle_event(event):
                return True
        
        return False
    
    def render(self, screen: pygame.Surface, font: Optional[pygame.font.Font] = None):
        """メニュー描画（日本語フォント対応）"""
        if self.state != UIState.VISIBLE:
            return
        
        # フォントを取得（日本語対応）
        use_font = font
        if not use_font:
            try:
                from src.ui.font_manager_pygame import font_manager
                use_font = font_manager.get_japanese_font(24)
                if not use_font:
                    use_font = font_manager.get_default_font()
            except Exception as e:
                logger.warning(f"フォントマネージャーの取得に失敗: {e}")
                try:
                    # システムフォントで日本語フォントを試す
                    use_font = pygame.font.SysFont('notosanscjk,noto,ipagothic,takao,hiragino,meiryo,msgothic', 24)
                except:
                    use_font = pygame.font.Font(None, 24)
        
        # 背景描画（半透明）
        if len(self.background_color) >= 4 and self.background_color[3] < 255:  # アルファ値がある場合
            overlay = pygame.Surface((screen.get_width(), screen.get_height()))
            overlay.set_alpha(self.background_color[3])
            overlay.fill(self.background_color[:3])
            screen.blit(overlay, (0, 0))
        
        # タイトル描画（日本語対応）
        if use_font and self.title:
            try:
                title_surface = use_font.render(self.title, True, self.title_color)
                title_rect = title_surface.get_rect()
                title_rect.centerx = screen.get_width() // 2
                title_rect.y = 50
                screen.blit(title_surface, title_rect)
            except Exception as e:
                logger.warning(f"タイトル描画エラー: {e}")
                # 英語フォールバック
                try:
                    fallback_font = pygame.font.Font(None, 24)
                    title_surface = fallback_font.render(self.title, True, self.title_color)
                    title_rect = title_surface.get_rect()
                    title_rect.centerx = screen.get_width() // 2
                    title_rect.y = 50
                    screen.blit(title_surface, title_rect)
                except:
                    pass
        
        # 各要素を描画
        for i, element in enumerate(self.elements):
            # 選択されている要素をハイライト
            if i == self.selected_index:
                highlight_rect = element.rect.inflate(4, 4)
                pygame.draw.rect(screen, (255, 255, 0), highlight_rect, 2)
            
            element.render(screen, use_font)


class UIDialog(UIMenu):
    """ダイアログシステム"""
    
    def __init__(self, dialog_id: str, title: str, message: str, x: int = 100, y: int = 100, 
                 width: int = 400, height: int = 200):
        super().__init__(dialog_id, title)
        self.dialog_id = dialog_id  # 互換性のため
        self.message = message
        self.rect = pygame.Rect(x, y, width, height)
        
        # ダイアログ専用設定
        self.background_color = (50, 50, 50, 255)
        self.border_color = (150, 150, 150)
        self.message_color = (200, 200, 200)
        
    def render(self, screen: pygame.Surface, font: Optional[pygame.font.Font] = None):
        """ダイアログ描画（日本語フォント対応）"""
        if self.state != UIState.VISIBLE:
            return
        
        # フォントを取得（日本語対応）
        use_font = font
        if not use_font:
            try:
                from src.ui.font_manager_pygame import font_manager
                use_font = font_manager.get_japanese_font(24)
                if not use_font:
                    use_font = font_manager.get_default_font()
            except Exception as e:
                logger.warning(f"フォントマネージャーの取得に失敗: {e}")
                try:
                    # システムフォントで日本語フォントを試す
                    use_font = pygame.font.SysFont('notosanscjk,noto,ipagothic,takao,hiragino,meiryo,msgothic', 24)
                except:
                    use_font = pygame.font.Font(None, 24)
        
        # ダイアログ背景
        pygame.draw.rect(screen, self.background_color, self.rect)
        pygame.draw.rect(screen, self.border_color, self.rect, 2)
        
        if use_font:
            # タイトル描画（日本語対応）
            if self.title:
                try:
                    title_surface = use_font.render(self.title, True, self.title_color)
                    title_rect = title_surface.get_rect()
                    title_rect.centerx = self.rect.centerx
                    title_rect.y = self.rect.y + 10
                    screen.blit(title_surface, title_rect)
                except Exception as e:
                    logger.warning(f"ダイアログタイトル描画エラー: {e}")
            
            # メッセージ描画（日本語対応）
            if self.message:
                message_lines = self.message.split('\n')
                y_offset = self.rect.y + 50
                for line in message_lines:
                    try:
                        message_surface = use_font.render(line, True, self.message_color)
                        message_rect = message_surface.get_rect()
                        message_rect.centerx = self.rect.centerx
                        message_rect.y = y_offset
                        screen.blit(message_surface, message_rect)
                        y_offset += use_font.get_height() + 5
                    except Exception as e:
                        logger.warning(f"メッセージ描画エラー: {e}")
                        y_offset += 25  # フォールバック行高
        
        # 各要素を描画
        for element in self.elements:
            element.render(screen, use_font)


class UIManager:
    """UIマネージャー"""
    
    def __init__(self, screen: pygame.Surface):
        self.screen = screen
        self.elements: Dict[str, UIElement] = {}
        self.menus: Dict[str, UIMenu] = {}
        self.dialogs: Dict[str, UIDialog] = {}
        self.modal_stack: List[str] = []  # モーダル要素のスタック
        
        # フォント初期化
        self.default_font = None
        self.title_font = None
        self._initialize_fonts()
        
    def _initialize_fonts(self):
        """フォント初期化"""
        try:
            from src.ui.font_manager_pygame import font_manager
            # 日本語フォントを優先して取得
            self.default_font = font_manager.get_japanese_font(24)
            self.title_font = font_manager.get_japanese_font(32)
            
            # フォールバック処理
            if not self.default_font:
                self.default_font = font_manager.get_font('default', 24)
            if not self.title_font:
                self.title_font = font_manager.get_font('default', 32)
                
            # 最終フォールバック
            if not self.default_font:
                self.default_font = pygame.font.Font(None, 24)
            if not self.title_font:
                self.title_font = pygame.font.Font(None, 32)
                
        except Exception as e:
            logger.warning(f"フォント初期化に失敗: {e}")
            # 最終フォールバック
            try:
                self.default_font = pygame.font.Font(None, 24)
                self.title_font = pygame.font.Font(None, 32)
            except:
                pass
    
    def add_element(self, element: UIElement):
        """要素を追加"""
        self.elements[element.element_id] = element
    
    def register_element(self, element):
        """要素を登録（互換性のため）"""
        if hasattr(element, 'element_id'):
            self.add_element(element)
        elif hasattr(element, 'menu_id'):
            self.add_menu(element)
        elif hasattr(element, 'dialog_id'):
            self.add_dialog(element)
    
    def show_element(self, element_id: str, modal: bool = False):
        """要素を表示（互換性のため）"""
        if element_id in self.elements:
            self.elements[element_id].show()
        elif element_id in self.menus:
            self.show_menu(element_id, modal)
        elif element_id in self.dialogs:
            self.show_dialog(element_id)
    
    def hide_element(self, element_id: str):
        """要素を非表示（互換性のため）"""
        if element_id in self.elements:
            self.elements[element_id].hide()
        elif element_id in self.menus:
            self.hide_menu(element_id)
        elif element_id in self.dialogs:
            self.hide_dialog(element_id)
    
    def unregister_element(self, element_id: str):
        """要素の登録を解除（互換性のため）"""
        if element_id in self.elements:
            del self.elements[element_id]
        elif element_id in self.menus:
            del self.menus[element_id]
        elif element_id in self.dialogs:
            del self.dialogs[element_id]
    
    def add_menu(self, menu: UIMenu):
        """メニューを追加"""
        self.menus[menu.menu_id] = menu
    
    def add_dialog(self, dialog: UIDialog):
        """ダイアログを追加"""
        self.dialogs[dialog.dialog_id] = dialog
    
    def show_menu(self, menu_id: str, modal: bool = False):
        """メニューを表示"""
        if menu_id in self.menus:
            self.menus[menu_id].show()
            if modal:
                self.modal_stack.append(menu_id)
    
    def hide_menu(self, menu_id: str):
        """メニューを非表示"""
        if menu_id in self.menus:
            self.menus[menu_id].hide()
            if menu_id in self.modal_stack:
                self.modal_stack.remove(menu_id)
    
    def show_dialog(self, dialog_id: str):
        """ダイアログを表示（常にモーダル）"""
        if dialog_id in self.dialogs:
            self.dialogs[dialog_id].show()
            self.modal_stack.append(dialog_id)
    
    def hide_dialog(self, dialog_id: str):
        """ダイアログを非表示"""
        if dialog_id in self.dialogs:
            self.dialogs[dialog_id].hide()
            if dialog_id in self.modal_stack:
                self.modal_stack.remove(dialog_id)
    
    def handle_event(self, event: pygame.event.Event) -> bool:
        """イベント処理（モーダルスタックを考慮）"""
        # モーダル要素が最優先
        if self.modal_stack:
            top_modal = self.modal_stack[-1]
            
            # ダイアログの処理
            if top_modal in self.dialogs:
                return self.dialogs[top_modal].handle_event(event)
            
            # メニューの処理
            if top_modal in self.menus:
                return self.menus[top_modal].handle_event(event)
        
        # 通常のメニュー処理
        for menu in self.menus.values():
            if menu.handle_event(event):
                return True
        
        # 通常の要素処理
        for element in self.elements.values():
            if element.handle_event(event):
                return True
        
        return False
    
    def render(self):
        """全UI要素を描画"""
        # 通常要素の描画
        for element in self.elements.values():
            element.render(self.screen, self.default_font)
        
        # メニューの描画
        for menu in self.menus.values():
            menu.render(self.screen, self.default_font)
        
        # ダイアログの描画（最前面）
        for dialog in self.dialogs.values():
            dialog.render(self.screen, self.default_font)


# グローバルインスタンス（互換性のため）
ui_manager = None

def initialize_ui_manager(screen: pygame.Surface):
    """UIマネージャーを初期化"""
    global ui_manager
    ui_manager = UIManager(screen)
    return ui_manager


class UIInputDialog(UIDialog):
    """入力ダイアログ"""
    
    def __init__(self, dialog_id: str, title: str, message: str, 
                 initial_text: str = "", placeholder: str = "",
                 on_confirm: callable = None, on_cancel: callable = None):
        super().__init__(dialog_id, title, message, x=200, y=150, width=400, height=250)
        self.input_text = initial_text
        self.placeholder = placeholder
        self.on_confirm = on_confirm
        self.on_cancel = on_cancel
        self.is_active = False
        
        # 入力フィールドの位置を設定（メッセージの下に配置）
        self.input_rect = pygame.Rect(self.rect.x + 20, self.rect.y + 120, 
                                     self.rect.width - 40, 30)
        
        # 確認・キャンセルボタンを追加（位置を設定）
        button_y = self.rect.y + self.rect.height - 50
        if on_confirm:
            confirm_button = UIButton(f"{dialog_id}_confirm", "OK", 
                                    x=self.rect.x + 80, y=button_y, 
                                    width=80, height=30)
            confirm_button.on_click = self._confirm_input
            self.add_element(confirm_button)
        
        if on_cancel:
            cancel_button = UIButton(f"{dialog_id}_cancel", "キャンセル", 
                                   x=self.rect.x + 240, y=button_y, 
                                   width=80, height=30)
            cancel_button.on_click = self._cancel_input
            self.add_element(cancel_button)
    
    def _confirm_input(self):
        """入力確認"""
        if self.on_confirm:
            self.on_confirm(self.input_text)
    
    def _cancel_input(self):
        """入力キャンセル"""
        if self.on_cancel:
            self.on_cancel()
    
    def handle_event(self, event: pygame.event.Event) -> bool:
        """入力イベント処理"""
        if self.state != UIState.VISIBLE:
            return False
        
        # テキスト入力処理
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_RETURN:
                self._confirm_input()
                return True
            elif event.key == pygame.K_ESCAPE:
                self._cancel_input()
                return True
            elif event.key == pygame.K_BACKSPACE:
                self.input_text = self.input_text[:-1]
                return True
        elif event.type == pygame.TEXTINPUT:
            self.input_text += event.text
            return True
        
        # 親クラスのイベント処理
        return super().handle_event(event)
    
    def render(self, screen: pygame.Surface, font: Optional[pygame.font.Font] = None):
        """入力ダイアログの描画"""
        # 親クラスの描画（ダイアログ背景とメッセージ）
        super().render(screen, font)
        
        # フォントを取得
        use_font = font
        if not use_font:
            try:
                from src.ui.font_manager_pygame import font_manager
                use_font = font_manager.get_japanese_font(20)
                if not use_font:
                    use_font = font_manager.get_default_font()
            except Exception:
                use_font = pygame.font.Font(None, 20)
        
        # 入力フィールドの描画
        if use_font:
            # 入力フィールドの背景
            pygame.draw.rect(screen, (255, 255, 255), self.input_rect)
            pygame.draw.rect(screen, (100, 100, 100), self.input_rect, 2)
            
            # 入力テキストの描画
            text_to_display = self.input_text if self.input_text else self.placeholder
            text_color = (0, 0, 0) if self.input_text else (128, 128, 128)
            
            if text_to_display:
                try:
                    text_surface = use_font.render(text_to_display, True, text_color)
                    text_rect = text_surface.get_rect()
                    text_rect.left = self.input_rect.left + 5
                    text_rect.centery = self.input_rect.centery
                    
                    # テキストが入力フィールドからはみ出る場合はクリップ
                    clip_rect = self.input_rect.copy()
                    clip_rect.width -= 10
                    screen.set_clip(clip_rect)
                    screen.blit(text_surface, text_rect)
                    screen.set_clip(None)
                except Exception as e:
                    logger.warning(f"入力テキスト描画エラー: {e}")
            
            # カーソルの描画（点滅効果）
            if self.input_text:
                cursor_x = self.input_rect.left + 5
                if self.input_text:
                    try:
                        text_width = use_font.size(self.input_text)[0]
                        cursor_x += text_width
                    except:
                        cursor_x += len(self.input_text) * 10
                
                # 簡易カーソル（縦線）
                pygame.draw.line(screen, (0, 0, 0), 
                               (cursor_x, self.input_rect.top + 5),
                               (cursor_x, self.input_rect.bottom - 5), 2)