"""
FormWindow クラス

フォーム入力用のウィンドウ
"""

import pygame
import pygame_gui
from typing import Dict, List, Any, Optional

from .window import Window
from .form_types import FormField, FormFieldType, FormValidationResult
from .form_validator import FormValidator
from .form_layout_manager import FormLayoutManager
from src.utils.logger import logger


class FormWindow(Window):
    """
    フォームウィンドウクラス
    
    入力フォームの作成と管理を行う
    """
    
    def __init__(self, window_id: str, form_config: Dict[str, Any], 
                 parent: Optional[Window] = None, modal: bool = False):
        """
        フォームウィンドウを初期化
        
        Args:
            window_id: ウィンドウID
            form_config: フォーム設定辞書
            parent: 親ウィンドウ
            modal: モーダルウィンドウかどうか
        """
        super().__init__(window_id, parent, modal)
        
        # 設定の検証
        self._validate_config(form_config)
        
        self.form_config = form_config
        self.fields: List[FormField] = []
        self.focused_field_index = 0
        
        # Extract Classによる専門クラス
        self.validator = FormValidator()
        self.layout_manager = FormLayoutManager()
        
        logger.debug(f"FormWindowを初期化: {window_id}")
    
    def _validate_config(self, config: Dict[str, Any]) -> None:
        """フォーム設定を検証"""
        if 'fields' not in config:
            raise ValueError("Form config must contain 'fields'")
        
        if not isinstance(config['fields'], list):
            raise ValueError("Form config 'fields' must be a list")
        
        if len(config['fields']) == 0:
            raise ValueError("Form config 'fields' cannot be empty")
    
    def create(self) -> None:
        """UI要素を作成"""
        if not self.ui_manager:
            self._initialize_ui_manager()
            self._calculate_layout()
            self._create_panel()
            self._create_title_if_needed()
            self._create_fields()
            self._create_buttons()
        
        logger.debug(f"FormWindow UI要素を作成: {self.window_id}")
    
    def _initialize_ui_manager(self) -> None:
        """UIManagerを初期化"""
        screen_width = 1024
        screen_height = 768
        self.ui_manager = pygame_gui.UIManager((screen_width, screen_height))
    
    def _calculate_layout(self) -> None:
        """フォームのレイアウトを計算"""
        field_count = len(self.form_config['fields'])
        has_title = 'title' in self.form_config
        
        # Extract Methodパターン適用
        self.rect = self.layout_manager.calculate_form_rect(field_count, has_title)
    
    def _create_panel(self) -> None:
        """フォームパネルを作成"""
        self.panel = pygame_gui.elements.UIPanel(
            relative_rect=self.rect,
            manager=self.ui_manager
        )
    
    def _create_title_if_needed(self) -> None:
        """タイトルラベルを作成（必要な場合）"""
        if 'title' in self.form_config:
            title_rect = self.layout_manager.calculate_title_rect(self.rect)
            self.title_label = pygame_gui.elements.UILabel(
                relative_rect=title_rect,
                text=self.form_config['title'],
                manager=self.ui_manager,
                container=self.panel
            )
    
    def _create_fields(self) -> None:
        """フィールドを作成"""
        field_count = len(self.form_config['fields'])
        has_title = 'title' in self.form_config
        field_positions = self.layout_manager.calculate_field_positions(self.rect, field_count, has_title)
        
        for i, field_config in enumerate(self.form_config['fields']):
            position = field_positions[i]
            self._create_field(field_config, position)
    
    def _create_field(self, field_config: Dict[str, Any], position: Dict[str, pygame.Rect]) -> None:
        """個別フィールドを作成"""
        field_type = FormFieldType(field_config['type'])
        
        # ラベルを作成
        label_rect = position['label']
        label_text = field_config['label']
        if field_config.get('required', False):
            label_text += " *"
        
        label = pygame_gui.elements.UILabel(
            relative_rect=label_rect,
            text=label_text,
            manager=self.ui_manager,
            container=self.panel
        )
        
        # 入力要素を作成
        input_rect = position['input']
        ui_element = self._create_input_element(field_type, input_rect, field_config)
        
        # FormFieldオブジェクトを作成
        form_field = FormField(
            field_id=field_config['id'],
            label=field_config['label'],
            field_type=field_type,
            required=field_config.get('required', False),
            ui_element=ui_element,
            validation_rules=self._get_validation_rules(field_config),
            options=field_config.get('options'),
            value=None
        )
        
        self.fields.append(form_field)
    
    def _create_input_element(self, field_type: FormFieldType, rect: pygame.Rect, 
                            config: Dict[str, Any]) -> pygame_gui.core.UIElement:
        """入力要素を作成"""
        if field_type == FormFieldType.TEXT:
            return pygame_gui.elements.UITextEntryLine(
                relative_rect=rect,
                manager=self.ui_manager,
                container=self.panel
            )
        elif field_type == FormFieldType.NUMBER:
            return pygame_gui.elements.UITextEntryLine(
                relative_rect=rect,
                manager=self.ui_manager,
                container=self.panel
            )
        elif field_type == FormFieldType.DROPDOWN:
            options = config.get('options', [])
            return pygame_gui.elements.UIDropDownMenu(
                relative_rect=rect,
                options_list=options,
                starting_option=options[0] if options else '',
                manager=self.ui_manager,
                container=self.panel
            )
        elif field_type == FormFieldType.CHECKBOX:
            return pygame_gui.elements.UIButton(
                relative_rect=rect,
                text='☐ ' + config.get('label', ''),
                manager=self.ui_manager,
                container=self.panel
            )
        else:
            raise ValueError(f"Unsupported field type: {field_type}")
    
    def _get_validation_rules(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """検証ルールを取得"""
        rules = {}
        
        if 'min' in config:
            rules['min'] = config['min']
        if 'max' in config:
            rules['max'] = config['max']
        if 'pattern' in config:
            rules['pattern'] = config['pattern']
        
        return rules
    
    def _create_buttons(self) -> None:
        """ボタンを作成"""
        button_positions = self.layout_manager.calculate_button_positions(self.rect)
        
        # Submitボタン
        submit_rect = button_positions['submit']
        self.submit_button = pygame_gui.elements.UIButton(
            relative_rect=submit_rect,
            text='Submit',
            manager=self.ui_manager,
            container=self.panel
        )
        
        # Cancelボタン
        cancel_rect = button_positions['cancel']
        self.cancel_button = pygame_gui.elements.UIButton(
            relative_rect=cancel_rect,
            text='Cancel',
            manager=self.ui_manager,
            container=self.panel
        )
    
    def handle_event(self, event: pygame.event.Event) -> bool:
        """イベントを処理"""
        if not self.ui_manager:
            return False
        
        # pygame-guiにイベントを渡す
        self.ui_manager.process_events(event)
        
        # キーボードイベント
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_TAB:
                self._handle_tab_navigation(event)
                return True
            elif event.key == pygame.K_RETURN:
                return self._handle_enter_key()
        
        # ボタンクリック処理
        if event.type == pygame_gui.UI_BUTTON_PRESSED:
            if event.ui_element == self.submit_button:
                return self.submit_form()
            elif event.ui_element == self.cancel_button:
                self.cancel_form()
                return True
        
        return False
    
    def _handle_tab_navigation(self, event: pygame.event.Event) -> None:
        """Tabキーナビゲーションを処理"""
        if event.mod & pygame.KMOD_SHIFT:
            # Shift+Tab: 前のフィールドに移動
            self.focused_field_index = (self.focused_field_index - 1) % len(self.fields)
        else:
            # Tab: 次のフィールドに移動
            self.focused_field_index = (self.focused_field_index + 1) % len(self.fields)
    
    def _handle_enter_key(self) -> bool:
        """Enterキーを処理"""
        return self.submit_form()
    
    def handle_escape(self) -> bool:
        """ESCキーの処理"""
        self.cancel_form()
        return True
    
    def set_field_value(self, field_id: str, value: Any) -> bool:
        """フィールドの値を設定"""
        for field in self.fields:
            if field.field_id == field_id:
                field.value = value
                
                # UI要素にも値を設定
                if field.field_type in [FormFieldType.TEXT, FormFieldType.NUMBER]:
                    field.ui_element.set_text(str(value))
                elif field.field_type == FormFieldType.DROPDOWN:
                    if value in field.options:
                        field.ui_element.selected_option = value
                elif field.field_type == FormFieldType.CHECKBOX:
                    # チェックボックスの状態を更新
                    checked = bool(value)
                    prefix = '☑ ' if checked else '☐ '
                    field.ui_element.set_text(prefix + field.label)
                
                return True
        return False
    
    def get_field_value(self, field_id: str) -> Any:
        """フィールドの値を取得"""
        for field in self.fields:
            if field.field_id == field_id:
                if field.field_type in [FormFieldType.TEXT, FormFieldType.NUMBER]:
                    return field.ui_element.get_text()
                elif field.field_type == FormFieldType.DROPDOWN:
                    return field.ui_element.selected_option
                elif field.field_type == FormFieldType.CHECKBOX:
                    return field.ui_element.text.startswith('☑')
        return None
    
    def get_form_data(self) -> Dict[str, Any]:
        """フォーム全体のデータを取得"""
        data = {}
        for field in self.fields:
            data[field.field_id] = self.get_field_value(field.field_id)
        return data
    
    def validate_form(self) -> FormValidationResult:
        """フォームを検証"""
        form_data = self.get_form_data()
        
        # Extract Classパターン適用 - 検証ロジックを専門クラスに委譲
        return self.validator.validate_fields(self.fields, form_data)
    
    def submit_form(self) -> bool:
        """フォームを送信"""
        validation_result = self.validate_form()
        
        if validation_result.is_valid:
            form_data = self.get_form_data()
            self.send_message('form_submitted', {
                'form_id': self.window_id,
                'data': form_data
            })
            logger.debug(f"フォーム送信: {self.window_id}")
            return True
        else:
            logger.debug(f"フォーム検証失敗: {validation_result.errors}")
            return False
    
    def cancel_form(self) -> None:
        """フォームをキャンセル"""
        self.send_message('form_cancelled', {
            'form_id': self.window_id
        })
        logger.debug(f"フォームキャンセル: {self.window_id}")
    
    def cleanup_ui(self) -> None:
        """UI要素のクリーンアップ"""
        # フィールドをクリア
        self.fields.clear()
        
        # pygame-guiの要素を削除
        if self.ui_manager:
            for element in list(self.ui_manager.get_root_container().elements):
                element.kill()
            self.ui_manager = None
        
        logger.debug(f"FormWindow UI要素をクリーンアップ: {self.window_id}")