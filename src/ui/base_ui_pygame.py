"""基本UIシステム（Pygame版）"""

from typing import Dict, List, Optional, Callable, Any
from enum import Enum
import pygame
import pygame_gui
from src.utils.logger import logger

# UI基本定数
DEFAULT_UI_WIDTH = 100
DEFAULT_UI_HEIGHT = 30
DEFAULT_FONT_SIZE = 24
DEFAULT_BORDER_WIDTH = 1

# UI色定数
DEFAULT_BACKGROUND_COLOR = (50, 50, 50)
DEFAULT_BORDER_COLOR = (100, 100, 100)
DEFAULT_TEXT_COLOR = (255, 255, 255)
TRANSPARENT_COLOR = (0, 0, 0, 0)
HOVER_BRIGHTNESS_OFFSET = 30
PRESS_BRIGHTNESS_OFFSET = -30
COLOR_MIN_VALUE = 0
COLOR_MAX_VALUE = 255

# UI空白・マージン定数
DEFAULT_SPACING = 10
DEFAULT_MARGIN = 5
DEFAULT_PADDING = 8

# テキスト折り返し定数
EMPTY_LINE_FALLBACK = [""]
SPACE_CHAR = " "
NEWLINE_CHAR = "\n"


def wrap_text(text: str, font: pygame.font.Font, max_width: int) -> List[str]:
    """テキストを指定幅で折り返す"""
    if not text:
        return EMPTY_LINE_FALLBACK
    
    words = text.split(SPACE_CHAR)
    lines = []
    current_line = ""
    
    for word in words:
        if NEWLINE_CHAR in word:
            lines.extend(_process_word_with_newlines(word, current_line, font, max_width))
            current_line = lines.pop() if lines else ""
        else:
            current_line = _process_regular_word(word, current_line, lines, font, max_width)
    
    if current_line.strip():
        lines.append(current_line.strip())
    
    return lines if lines else EMPTY_LINE_FALLBACK

def _process_word_with_newlines(word: str, current_line: str, font: pygame.font.Font, max_width: int) -> List[str]:
    """改行文字を含む単語を処理"""
    word_parts = word.split(NEWLINE_CHAR)
    result_lines = []
    
    for i, part in enumerate(word_parts):
        if i > 0:  # 改行後の部分
            if current_line.strip():
                result_lines.append(current_line.strip())
            current_line = part
        else:  # 改行前の部分
            current_line = _try_add_word_to_line(part, current_line, result_lines, font, max_width)
    
    result_lines.append(current_line)
    return result_lines

def _process_regular_word(word: str, current_line: str, lines: List[str], font: pygame.font.Font, max_width: int) -> str:
    """通常の単語を処理"""
    return _try_add_word_to_line(word, current_line, lines, font, max_width)

def _try_add_word_to_line(word: str, current_line: str, lines: List[str], font: pygame.font.Font, max_width: int) -> str:
    """単語を行に追加を試行"""
    test_line = current_line + (SPACE_CHAR if current_line else "") + word
    if font.size(test_line)[0] <= max_width:
        return test_line
    else:
        if current_line.strip():
            lines.append(current_line.strip())
        return word



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
    
    def __init__(self, element_id: str, x: int = 0, y: int = 0, width: int = DEFAULT_UI_WIDTH, height: int = DEFAULT_UI_HEIGHT):
        self.element_id = element_id
        self.state = UIState.HIDDEN
        self.rect = pygame.Rect(x, y, width, height)
        self.parent = None
        self.children: List['UIElement'] = []
        
        # 描画設定
        self.background_color = DEFAULT_BACKGROUND_COLOR
        self.border_color = DEFAULT_BORDER_COLOR
        self.text_color = DEFAULT_TEXT_COLOR
        self.border_width = DEFAULT_BORDER_WIDTH
        
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
        bg_color = self._calculate_background_color()
        
        pygame.draw.rect(screen, bg_color, self.rect)
        self._render_border(screen)
    
    def _calculate_background_color(self) -> tuple:
        """背景色を状態に応じて計算"""
        bg_color = self.background_color
        if self.is_hovered:
            bg_color = tuple(min(COLOR_MAX_VALUE, c + HOVER_BRIGHTNESS_OFFSET) for c in bg_color)
        if self.is_pressed:
            bg_color = tuple(max(COLOR_MIN_VALUE, c + PRESS_BRIGHTNESS_OFFSET) for c in bg_color)
        return bg_color
    
    def _render_border(self, screen: pygame.Surface):
        """ボーダーを描画"""
        if self.border_width > 0:
            pygame.draw.rect(screen, self.border_color, self.rect, self.border_width)


class UIText(UIElement):
    """テキスト表示要素"""
    
    def __init__(self, element_id: str, text: str, x: int = 0, y: int = 0, 
                 font_size: int = DEFAULT_FONT_SIZE, alignment: UIAlignment = UIAlignment.LEFT):
        super().__init__(element_id, x, y)
        self.text = text
        self.font_size = font_size
        self.alignment = alignment
        self.font = None
        
        # テキスト専用設定
        self.background_color = TRANSPARENT_COLOR  # 透明
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
                use_font = font_manager.get_japanese_font(DEFAULT_FONT_SIZE)
                if not use_font:
                    use_font = font_manager.get_default_font()
            except Exception as e:
                logger.warning(f"フォントマネージャーの取得に失敗: {e}")
                # フォールバック：デフォルトフォント（英語のみ）
                use_font = pygame.font.Font(None, DEFAULT_FONT_SIZE)
                if not use_font:
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
                    use_font = font_manager.get_japanese_font(DEFAULT_FONT_SIZE)
                    if not use_font:
                        use_font = font_manager.get_default_font()
                except Exception as e:
                    logger.warning(f"フォントマネージャーの取得に失敗: {e}")
                    # フォールバック：デフォルトフォント（英語のみ）
                    use_font = pygame.font.Font(None, 24)
                    if not use_font:
                        return  # フォントが取得できない場合は描画しない
            
            # テキストをレンダリング（折り返し対応）
            try:
                # ボタン内でのテキスト幅制限（マージンを考慮）
                max_text_width = self.rect.width - 20
                
                # テキストを折り返し
                wrapped_lines = wrap_text(self.text, use_font, max_text_width)
                
                # 複数行テキストの描画
                line_height = use_font.get_height()
                total_height = len(wrapped_lines) * line_height
                start_y = self.rect.centery - total_height // 2
                
                for i, line in enumerate(wrapped_lines):
                    text_surface = use_font.render(line, True, self.text_color)
                    text_rect = text_surface.get_rect()
                    text_rect.centerx = self.rect.centerx
                    text_rect.y = start_y + i * line_height
                    screen.blit(text_surface, text_rect)
                    
            except Exception as e:
                logger.warning(f"ボタンテキストレンダリングエラー: {e}")
                # フォールバック：システムフォント使用
                try:
                    fallback_font = pygame.font.Font(None, 20)
                    text_surface = fallback_font.render(self.text[:20] + "..." if len(self.text) > 20 else self.text, True, self.text_color)
                    text_rect = text_surface.get_rect(center=self.rect.center)
                    screen.blit(text_surface, text_rect)
                except:
                    pass  # 最終的にも失敗した場合は背景のみ描画


# UIMenuクラス・UIDialogクラスは削除されました（Phase 4.5: UIMenuクラス本体削除）
# WindowSystemベースのメニュー・ダイアログ機能を使用してください


class UIManager:
    """UIマネージャー"""
    
    def __init__(self, screen: pygame.Surface):
        self.screen = screen
        self.elements: Dict[str, UIElement] = {}
        self.menus: Dict[str, Any] = {}  # UIMenu削除済み - レガシー互換性のため
        self.dialogs: Dict[str, Any] = {}  # UIDialog削除済み - レガシー互換性のため
        self.persistent_elements: Dict[str, UIElement] = {}  # 常に最前面に表示される要素
        self.modal_stack: List[str] = []  # モーダル要素のスタック
        
        # pygame-gui マネージャー（テーマファイル付き）
        import warnings
        try:
            theme_path = "config/ui_theme.json"
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                self.pygame_gui_manager = pygame_gui.UIManager((screen.get_width(), screen.get_height()), theme_path)
            logger.info(f"UIテーマを読み込みました: {theme_path}")
        except Exception as e:
            logger.warning(f"UIテーマの読み込みに失敗、デフォルトテーマを使用: {e}")
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                self.pygame_gui_manager = pygame_gui.UIManager((screen.get_width(), screen.get_height()))
        
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
            
            # pygame_guiフォント統合を実行（警告を抑制）
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                font_manager.initialize_pygame_gui_fonts(self.pygame_gui_manager)
                
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
    
    def add_persistent_element(self, element: UIElement):
        """永続要素を追加（常に最前面に表示）"""
        self.persistent_elements[element.element_id] = element
    
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
        elif element_id in self.persistent_elements:
            self.persistent_elements[element_id].show()
        elif element_id in self.menus:
            self.show_menu(element_id, modal)
        elif element_id in self.dialogs:
            self.show_dialog(element_id)
    
    def hide_element(self, element_id: str):
        """要素を非表示（互換性のため）"""
        if element_id in self.elements:
            self.elements[element_id].hide()
        elif element_id in self.persistent_elements:
            self.persistent_elements[element_id].hide()
        elif element_id in self.menus:
            self.hide_menu(element_id)
        elif element_id in self.dialogs:
            self.hide_dialog(element_id)
    
    def unregister_element(self, element_id: str):
        """要素の登録を解除（互換性のため）"""
        if element_id in self.elements:
            del self.elements[element_id]
        elif element_id in self.persistent_elements:
            del self.persistent_elements[element_id]
        elif element_id in self.menus:
            del self.menus[element_id]
        elif element_id in self.dialogs:
            del self.dialogs[element_id]
    
    def add_menu(self, menu: Any):  # UIMenu削除済み - レガシー互換性のため
        """メニューを追加（非推奨：WindowSystemを使用してください）"""
        if hasattr(menu, 'menu_id'):
            self.menus[menu.menu_id] = menu
    
    def add_dialog(self, dialog: Any):  # UIDialog削除済み - レガシー互換性のため
        """ダイアログを追加（非推奨：WindowSystemを使用してください）"""
        if hasattr(dialog, 'dialog_id'):
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
    
    def hide_all(self):
        """すべてのモーダル要素（ダイアログ・メニュー）を非表示"""
        # モーダルスタックの要素をすべて非表示にする
        for modal_id in self.modal_stack.copy():  # コピーを作成して安全にイテレート
            if modal_id in self.dialogs:
                self.hide_dialog(modal_id)
            elif modal_id in self.menus:
                self.hide_menu(modal_id)
        
        # すべての通常要素も非表示にする
        for element in self.elements.values():
            element.hide()
        
        # モーダルスタックをクリア
        self.modal_stack.clear()
        
        logger.debug("すべてのUI要素を非表示にしました")
    
    def handle_event(self, event: pygame.event.Event) -> bool:
        """イベント処理（モーダルスタックを考慮）"""
        # pygame-guiイベント処理
        self.pygame_gui_manager.process_events(event)
        
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
        
        # 永続要素処理
        for element in self.persistent_elements.values():
            if element.handle_event(event):
                return True
        
        return False
    
    def update(self, time_delta: float):
        """UI更新処理"""
        self.pygame_gui_manager.update(time_delta)
    
    def render(self):
        """全UI要素を描画"""
        # 通常要素の描画
        for element in self.elements.values():
            element.render(self.screen, self.default_font)
        
        # メニューの描画
        for menu in self.menus.values():
            menu.render(self.screen, self.default_font)
        
        # ダイアログの描画
        for dialog in self.dialogs.values():
            dialog.render(self.screen, self.default_font)
        
        # pygame-gui要素の描画
        self.pygame_gui_manager.draw_ui(self.screen)
        
        # 永続要素の描画（最前面）
        for element in self.persistent_elements.values():
            element.render(self.screen, self.default_font)


# グローバルインスタンス（互換性のため）
ui_manager = None

def initialize_ui_manager(screen: pygame.Surface):
    """UIマネージャーを初期化"""
    global ui_manager
    ui_manager = UIManager(screen)
    return ui_manager


class UIInputDialog(UIElement):
    """入力ダイアログ"""
    
    def __init__(self, dialog_id: str, title: str, message: str, 
                 initial_text: str = "", placeholder: str = "",
                 on_confirm: callable = None, on_cancel: callable = None):
        super().__init__(dialog_id, x=200, y=150, width=400, height=250)
        self.title = title
        self.message = message
        self.input_text = initial_text
        self.placeholder = placeholder
        self.on_confirm = on_confirm
        self.on_cancel = on_cancel
        self.is_active = False
        self.elements: List[UIElement] = []  # 子要素リスト
        
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
    
    def add_element(self, element: UIElement):
        """要素を追加"""
        self.elements.append(element)
        element.parent = self
    
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
        
        # 子要素のイベント処理
        for element in self.elements:
            if element.handle_event(event):
                return True
        
        # 親クラスのイベント処理
        return super().handle_event(event)
    
    def show(self):
        """ダイアログを表示"""
        super().show()
        for element in self.elements:
            element.show()
    
    def hide(self):
        """ダイアログを非表示"""
        super().hide()
        for element in self.elements:
            element.hide()
    
    def render(self, screen: pygame.Surface, font: Optional[pygame.font.Font] = None):
        """入力ダイアログの描画"""
        if self.state != UIState.VISIBLE:
            return
        
        # ダイアログ背景描画
        pygame.draw.rect(screen, (50, 50, 50), self.rect)
        pygame.draw.rect(screen, (150, 150, 150), self.rect, 2)
        
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
        
        # タイトルとメッセージの描画
        if use_font:
            # タイトル描画
            if self.title:
                try:
                    title_surface = use_font.render(self.title, True, (255, 255, 255))
                    title_rect = title_surface.get_rect()
                    title_rect.centerx = self.rect.centerx
                    title_rect.y = self.rect.y + 10
                    screen.blit(title_surface, title_rect)
                except Exception as e:
                    logger.warning(f"タイトル描画エラー: {e}")
            
            # メッセージ描画
            if self.message:
                try:
                    message_surface = use_font.render(self.message, True, (200, 200, 200))
                    message_rect = message_surface.get_rect()
                    message_rect.centerx = self.rect.centerx
                    message_rect.y = self.rect.y + 50
                    screen.blit(message_surface, message_rect)
                except Exception as e:
                    logger.warning(f"メッセージ描画エラー: {e}")
        
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
        
        # 子要素（ボタン等）を描画
        for element in self.elements:
            element.render(screen, font)