"""
DialogWindow クラス

確認・入力ダイアログ用のウィンドウ
"""

import pygame
import pygame_gui
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from enum import Enum

from .window import Window
from src.utils.logger import logger


class DialogType(Enum):
    """ダイアログタイプ"""
    INFORMATION = "information"
    CONFIRMATION = "confirmation"
    INPUT = "input"
    ERROR = "error"
    SUCCESS = "success"
    CUSTOM = "custom"


class DialogResult(Enum):
    """ダイアログ結果"""
    OK = "ok"
    CANCEL = "cancel"
    YES = "yes"
    NO = "no"
    CUSTOM = "custom"


@dataclass
class DialogButton:
    """ダイアログボタンの情報"""
    text: str
    result: DialogResult
    ui_element: Optional[pygame_gui.elements.UIButton] = None
    custom_data: Optional[Any] = None
    is_default: bool = False


class DialogWindow(Window):
    """
    ダイアログウィンドウクラス
    
    モーダルダイアログの作成と管理を行う
    """
    
    def __init__(self, window_id: str, dialog_type: DialogType, message: str,
                 parent: Optional[Window] = None, input_config: Optional[Dict[str, Any]] = None,
                 custom_buttons: Optional[List[Dict[str, Any]]] = None):
        """
        ダイアログウィンドウを初期化
        
        Args:
            window_id: ウィンドウID
            dialog_type: ダイアログタイプ
            message: 表示メッセージ
            parent: 親ウィンドウ
            input_config: 入力設定（INPUT タイプの場合）
            custom_buttons: カスタムボタン設定（CUSTOM タイプの場合）
        """
        super().__init__(window_id, parent, modal=True)  # ダイアログは常にモーダル
        
        # パラメータ検証
        self._validate_parameters(dialog_type, message)
        
        self.dialog_type = dialog_type
        self.message = message
        self.input_config = input_config or {}
        self.custom_buttons_config = custom_buttons or []
        
        # UI要素
        self.buttons: List[DialogButton] = []
        self.text_input: Optional[pygame_gui.elements.UITextEntryLine] = None
        self.message_label: Optional[pygame_gui.elements.UILabel] = None
        
        # 結果
        self.result: Optional[DialogResult] = None
        self.data: Optional[Any] = None
        
        # スタイル
        self.style_class = self._get_style_class()
        
        logger.debug(f"DialogWindowを初期化: {window_id} ({dialog_type.value})")
    
    def _validate_parameters(self, dialog_type: DialogType, message: str) -> None:
        """パラメータを検証"""
        if not isinstance(dialog_type, DialogType):
            raise ValueError("Invalid dialog type")
        
        if not message or not message.strip():
            raise ValueError("Message cannot be empty")
    
    def _get_style_class(self) -> str:
        """ダイアログタイプに応じたスタイルクラスを取得"""
        style_map = {
            DialogType.ERROR: 'error_dialog',
            DialogType.SUCCESS: 'success_dialog',
            DialogType.CONFIRMATION: 'confirmation_dialog',
            DialogType.INFORMATION: 'information_dialog',
            DialogType.INPUT: 'input_dialog',
            DialogType.CUSTOM: 'custom_dialog'
        }
        return style_map.get(self.dialog_type, 'default_dialog')
    
    def create(self) -> None:
        """UI要素を作成"""
        if not self.ui_manager:
            self._initialize_ui_manager()
            self._calculate_dialog_size()
            self._create_dialog_panel()
            self._create_message_label()
            self._create_input_field_if_needed()
            self._create_buttons()
        
        logger.debug(f"DialogWindow UI要素を作成: {self.window_id}")
    
    def _initialize_ui_manager(self) -> None:
        """UIManagerを初期化"""
        screen_width = 1024
        screen_height = 768
        self.ui_manager = pygame_gui.UIManager((screen_width, screen_height))
    
    def _calculate_dialog_size(self) -> None:
        """ダイアログサイズを計算"""
        # 基本サイズ
        dialog_width = 400
        dialog_height = 150
        
        # メッセージに応じて高さを調整
        message_lines = len(self.message.split('\n'))
        dialog_height += message_lines * 20
        
        # 入力フィールドがある場合
        if self.dialog_type == DialogType.INPUT:
            dialog_height += 40
        
        # ボタン数に応じて幅を調整
        button_count = self._get_button_count()
        if button_count > 2:
            dialog_width = max(400, button_count * 120)
        
        # 画面中央に配置
        screen_width = 1024
        screen_height = 768
        dialog_x = (screen_width - dialog_width) // 2
        dialog_y = (screen_height - dialog_height) // 2
        
        self.rect = pygame.Rect(dialog_x, dialog_y, dialog_width, dialog_height)
    
    def _get_button_count(self) -> int:
        """ボタン数を取得"""
        if self.dialog_type == DialogType.CUSTOM:
            return len(self.custom_buttons_config)
        elif self.dialog_type in [DialogType.CONFIRMATION]:
            return 2
        else:
            return 1
    
    def _create_dialog_panel(self) -> None:
        """ダイアログパネルを作成"""
        self.panel = pygame_gui.elements.UIPanel(
            relative_rect=self.rect,
            manager=self.ui_manager
        )
    
    def _create_message_label(self) -> None:
        """メッセージラベルを作成"""
        message_rect = pygame.Rect(20, 20, self.rect.width - 40, 60)
        self.message_label = pygame_gui.elements.UILabel(
            relative_rect=message_rect,
            text=self.message,
            manager=self.ui_manager,
            container=self.panel
        )
    
    def _create_input_field_if_needed(self) -> None:
        """必要に応じて入力フィールドを作成"""
        if self.dialog_type == DialogType.INPUT:
            input_y = 90
            input_rect = pygame.Rect(20, input_y, self.rect.width - 40, 30)
            
            placeholder = self.input_config.get('placeholder', '')
            self.text_input = pygame_gui.elements.UITextEntryLine(
                relative_rect=input_rect,
                manager=self.ui_manager,
                container=self.panel
            )
            
            if placeholder:
                self.text_input.set_text(placeholder)
    
    def _create_buttons(self) -> None:
        """ボタンを作成"""
        if self.dialog_type == DialogType.CUSTOM:
            self._create_custom_buttons()
        else:
            self._create_standard_buttons()
    
    def _create_standard_buttons(self) -> None:
        """標準ボタンを作成"""
        button_configs = self._get_standard_button_configs()
        self._create_buttons_from_configs(button_configs)
    
    def _get_standard_button_configs(self) -> List[Dict[str, Any]]:
        """標準ボタン設定を取得"""
        if self.dialog_type == DialogType.INFORMATION:
            return [{'text': 'OK', 'result': DialogResult.OK, 'is_default': True}]
        elif self.dialog_type == DialogType.ERROR:
            return [{'text': 'OK', 'result': DialogResult.OK, 'is_default': True}]
        elif self.dialog_type == DialogType.SUCCESS:
            return [{'text': 'OK', 'result': DialogResult.OK, 'is_default': True}]
        elif self.dialog_type == DialogType.CONFIRMATION:
            return [
                {'text': 'Yes', 'result': DialogResult.YES, 'is_default': True},
                {'text': 'No', 'result': DialogResult.NO}
            ]
        elif self.dialog_type == DialogType.INPUT:
            return [
                {'text': 'OK', 'result': DialogResult.OK, 'is_default': True},
                {'text': 'Cancel', 'result': DialogResult.CANCEL}
            ]
        else:
            return [{'text': 'OK', 'result': DialogResult.OK, 'is_default': True}]
    
    def _create_custom_buttons(self) -> None:
        """カスタムボタンを作成"""
        self._create_buttons_from_configs(self.custom_buttons_config)
    
    def _create_buttons_from_configs(self, button_configs: List[Dict[str, Any]]) -> None:
        """設定からボタンを作成"""
        button_count = len(button_configs)
        button_width = 80
        button_height = 30
        button_spacing = 10
        
        # ボタン配置の開始位置を計算
        total_button_width = button_count * button_width + (button_count - 1) * button_spacing
        button_start_x = (self.rect.width - total_button_width) // 2
        button_y = self.rect.height - 50
        
        for i, config in enumerate(button_configs):
            button_x = button_start_x + i * (button_width + button_spacing)
            button_rect = pygame.Rect(button_x, button_y, button_width, button_height)
            
            # pygame-guiボタンを作成
            ui_button = pygame_gui.elements.UIButton(
                relative_rect=button_rect,
                text=config['text'],
                manager=self.ui_manager,
                container=self.panel
            )
            
            # DialogButtonオブジェクトを作成
            dialog_button = DialogButton(
                text=config['text'],
                result=config['result'],
                ui_element=ui_button,
                custom_data=config.get('custom_data'),
                is_default=config.get('is_default', False)
            )
            
            self.buttons.append(dialog_button)
    
    def handle_event(self, event: pygame.event.Event) -> bool:
        """イベントを処理"""
        if not self.ui_manager:
            return False
        
        # pygame-guiにイベントを渡す
        self.ui_manager.process_events(event)
        
        # キーボードイベント
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_RETURN:
                return self._handle_enter_key()
        
        # ボタンクリック処理
        if event.type == pygame_gui.UI_BUTTON_PRESSED:
            for button in self.buttons:
                if event.ui_element == button.ui_element:
                    self._set_result(button.result, button.custom_data)
                    return True
        
        return False
    
    def _handle_enter_key(self) -> bool:
        """Enterキーを処理"""
        # デフォルトボタンを実行
        default_button = next((btn for btn in self.buttons if btn.is_default), None)
        if default_button:
            self._set_result(default_button.result, default_button.custom_data)
            return True
        return False
    
    def handle_escape(self) -> bool:
        """ESCキーの処理"""
        self._set_result(DialogResult.CANCEL, None)
        return True
    
    def _set_result(self, result: DialogResult, custom_data: Optional[Any] = None) -> None:
        """結果を設定"""
        self.result = result
        
        # 入力ダイアログの場合はテキスト入力の値を取得
        if self.dialog_type == DialogType.INPUT and result == DialogResult.OK:
            self.data = self.text_input.get_text() if self.text_input else None
        elif custom_data is not None:
            self.data = custom_data
        else:
            self.data = None
        
        # 結果をメッセージで送信
        self.send_message('dialog_result', {'result': result, 'data': self.data})
        
        # ダイアログを閉じる
        self.send_message('close_requested')
        
        logger.debug(f"ダイアログ結果設定: {result.value}, data: {self.data}")
    
    def cleanup_ui(self) -> None:
        """UI要素のクリーンアップ"""
        # ボタンをクリア
        self.buttons.clear()
        
        # 入力フィールドをクリア
        self.text_input = None
        
        # pygame-guiの要素を削除
        if self.ui_manager:
            for element in list(self.ui_manager.get_root_container().elements):
                element.kill()
            self.ui_manager = None
        
        logger.debug(f"DialogWindow UI要素をクリーンアップ: {self.window_id}")