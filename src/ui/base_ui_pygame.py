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
                use_font = font_manager.get_default_font()
            except Exception as e:
                logger.warning(f"フォントマネージャーの取得に失敗: {e}")
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
                    use_font = font_manager.get_default_font()
                except Exception as e:
                    logger.warning(f"フォントマネージャーの取得に失敗: {e}")
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
        """メニュー描画"""
        if self.state != UIState.VISIBLE:
            return
        
        # 背景描画（半透明）
        if self.background_color[3] < 255:  # アルファ値がある場合
            overlay = pygame.Surface((screen.get_width(), screen.get_height()))
            overlay.set_alpha(self.background_color[3])
            overlay.fill(self.background_color[:3])
            screen.blit(overlay, (0, 0))
        
        # タイトル描画
        if font and self.title:
            title_surface = font.render(self.title, True, self.title_color)
            title_rect = title_surface.get_rect()
            title_rect.centerx = screen.get_width() // 2
            title_rect.y = 50
            screen.blit(title_surface, title_rect)
        
        # 各要素を描画
        for i, element in enumerate(self.elements):
            # 選択されている要素をハイライト
            if i == self.selected_index:
                highlight_rect = element.rect.inflate(4, 4)
                pygame.draw.rect(screen, (255, 255, 0), highlight_rect, 2)
            
            element.render(screen, font)


class UIDialog(UIMenu):
    """ダイアログシステム"""
    
    def __init__(self, dialog_id: str, title: str, message: str, x: int = 100, y: int = 100, 
                 width: int = 400, height: int = 200):
        super().__init__(dialog_id, title)
        self.message = message
        self.rect = pygame.Rect(x, y, width, height)
        
        # ダイアログ専用設定
        self.background_color = (50, 50, 50, 255)
        self.border_color = (150, 150, 150)
        self.message_color = (200, 200, 200)
        
    def render(self, screen: pygame.Surface, font: Optional[pygame.font.Font] = None):
        """ダイアログ描画"""
        if self.state != UIState.VISIBLE:
            return
        
        # ダイアログ背景
        pygame.draw.rect(screen, self.background_color, self.rect)
        pygame.draw.rect(screen, self.border_color, self.rect, 2)
        
        if font:
            # タイトル描画
            if self.title:
                title_surface = font.render(self.title, True, self.title_color)
                title_rect = title_surface.get_rect()
                title_rect.centerx = self.rect.centerx
                title_rect.y = self.rect.y + 10
                screen.blit(title_surface, title_rect)
            
            # メッセージ描画
            if self.message:
                message_lines = self.message.split('\n')
                y_offset = self.rect.y + 50
                for line in message_lines:
                    message_surface = font.render(line, True, self.message_color)
                    message_rect = message_surface.get_rect()
                    message_rect.centerx = self.rect.centerx
                    message_rect.y = y_offset
                    screen.blit(message_surface, message_rect)
                    y_offset += font.get_height() + 5
        
        # 各要素を描画
        for element in self.elements:
            element.render(screen, font)


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
            self.default_font = pygame.font.Font(None, 24)
            self.title_font = pygame.font.Font(None, 32)
        except Exception as e:
            logger.warning(f"フォント初期化に失敗: {e}")
    
    def add_element(self, element: UIElement):
        """要素を追加"""
        self.elements[element.element_id] = element
    
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