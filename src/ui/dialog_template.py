"""ダイアログテンプレートシステム

統一されたダイアログ表示と標準的なナビゲーションボタンを提供します。
"""

from typing import Dict, List, Optional, Callable, Any, Union
from enum import Enum
import pygame
from src.ui.base_ui_pygame import UIButton, UIElement, ui_manager  # UIDialog: Phase 4.5で削除
# MenuStackManager削除により、MenuTypeインポートも削除
from src.core.config_manager import config_manager
from src.utils.logger import logger


class DialogType(Enum):
    """ダイアログタイプ"""
    INFORMATION = "information"      # 情報表示
    CONFIRMATION = "confirmation"    # 確認
    SELECTION = "selection"          # 選択
    INPUT = "input"                 # 入力
    ERROR = "error"                 # エラー
    SUCCESS = "success"             # 成功
    WARNING = "warning"             # 警告


class ButtonType(Enum):
    """ボタンタイプ"""
    OK = "ok"
    CANCEL = "cancel"
    BACK = "back"
    YES = "yes"
    NO = "no"
    CONFIRM = "confirm"
    CLOSE = "close"


class ButtonTemplate:
    """標準ボタンテンプレート"""
    
    TEMPLATES = {
        ButtonType.OK: {
            'text_key': 'common.ok',
            'default_text': 'OK',
            'color': (100, 150, 100),
            'hotkey': pygame.K_RETURN
        },
        ButtonType.CANCEL: {
            'text_key': 'common.cancel',
            'default_text': 'キャンセル',
            'color': (150, 100, 100),
            'hotkey': pygame.K_ESCAPE
        },
        ButtonType.BACK: {
            'text_key': 'common.back',
            'default_text': '戻る',
            'color': (100, 100, 150),
            'hotkey': pygame.K_ESCAPE
        },
        ButtonType.YES: {
            'text_key': 'common.yes',
            'default_text': 'はい',
            'color': (100, 150, 100),
            'hotkey': pygame.K_y
        },
        ButtonType.NO: {
            'text_key': 'common.no',
            'default_text': 'いいえ',
            'color': (150, 100, 100),
            'hotkey': pygame.K_n
        },
        ButtonType.CONFIRM: {
            'text_key': 'common.confirm',
            'default_text': '確定',
            'color': (100, 150, 100),
            'hotkey': pygame.K_RETURN
        },
        ButtonType.CLOSE: {
            'text_key': 'common.close',
            'default_text': '閉じる',
            'color': (120, 120, 120),
            'hotkey': pygame.K_ESCAPE
        }
    }
    
    @classmethod
    def get_button_text(cls, button_type: ButtonType) -> str:
        """ボタンテキストを取得"""
        template = cls.TEMPLATES.get(button_type, {})
        text_key = template.get('text_key')
        default_text = template.get('default_text', 'OK')
        
        if text_key:
            try:
                return config_manager.get_text(text_key)
            except:
                return default_text
        return default_text
    
    @classmethod
    def get_button_config(cls, button_type: ButtonType) -> Dict[str, Any]:
        """ボタン設定を取得"""
        template = cls.TEMPLATES.get(button_type, {})
        return {
            'text': cls.get_button_text(button_type),
            'color': template.get('color', (100, 100, 100)),
            'hotkey': template.get('hotkey')
        }


class DialogTemplate:
    """ダイアログテンプレートクラス
    
    統一されたダイアログ作成と標準的なボタン配置を提供。
    """
    
    def __init__(self, menu_stack_manager=None):
        self.menu_stack_manager = menu_stack_manager
        self.active_dialogs: Dict[str, UIDialog] = {}
        self.dialog_callbacks: Dict[str, Dict[str, Callable]] = {}
        
        # デフォルト設定
        self.default_dialog_width = 600
        self.default_dialog_height = 400
        self.button_width = 120
        self.button_height = 40
        self.button_spacing = 20
        
        logger.debug("DialogTemplateを初期化しました")
    
    def create_information_dialog(self, dialog_id: str, title: str, message: str, 
                                on_close: Optional[Callable] = None) -> UIDialog:
        """情報表示ダイアログを作成
        
        Args:
            dialog_id: ダイアログID
            title: タイトル
            message: メッセージ
            on_close: 閉じる時のコールバック
            
        Returns:
            UIDialog: 作成されたダイアログ
        """
        dialog = self._create_base_dialog(dialog_id, title, message)
        
        # OKボタンを追加
        ok_button = self._create_button(
            f"{dialog_id}_ok",
            ButtonType.OK,
            lambda: self._handle_dialog_close(dialog_id, on_close)
        )
        
        self._add_buttons_to_dialog(dialog, [ok_button])
        return dialog
    
    def create_confirmation_dialog(self, dialog_id: str, title: str, message: str,
                                 on_confirm: Optional[Callable] = None,
                                 on_cancel: Optional[Callable] = None) -> UIDialog:
        """確認ダイアログを作成
        
        Args:
            dialog_id: ダイアログID
            title: タイトル
            message: メッセージ
            on_confirm: 確認時のコールバック
            on_cancel: キャンセル時のコールバック
            
        Returns:
            UIDialog: 作成されたダイアログ
        """
        dialog = self._create_base_dialog(dialog_id, title, message)
        
        # はい/いいえボタンを追加
        yes_button = self._create_button(
            f"{dialog_id}_yes",
            ButtonType.YES,
            lambda: self._handle_dialog_action(dialog_id, on_confirm, True)
        )
        
        no_button = self._create_button(
            f"{dialog_id}_no",
            ButtonType.NO,
            lambda: self._handle_dialog_action(dialog_id, on_cancel, False)
        )
        
        self._add_buttons_to_dialog(dialog, [yes_button, no_button])
        return dialog
    
    def create_selection_dialog(self, dialog_id: str, title: str, message: str,
                              selections: List[Dict[str, Any]],
                              on_select: Optional[Callable] = None,
                              on_cancel: Optional[Callable] = None) -> UIDialog:
        """選択ダイアログを作成
        
        Args:
            dialog_id: ダイアログID
            title: タイトル
            message: メッセージ
            selections: 選択肢のリスト [{'text': 'テキスト', 'value': 値}, ...]
            on_select: 選択時のコールバック（選択された値を引数として受け取る）
            on_cancel: キャンセル時のコールバック
            
        Returns:
            UIDialog: 作成されたダイアログ
        """
        dialog = self._create_base_dialog(dialog_id, title, message)
        
        buttons = []
        
        # 選択肢ボタンを作成
        for i, selection in enumerate(selections):
            button = UIButton(
                f"{dialog_id}_selection_{i}",
                selection['text'],
                300 + (i % 2) * 150,  # 2列レイアウト
                300 + (i // 2) * 50,  # 行間隔
                self.button_width,
                self.button_height
            )
            
            # クロージャーでvalueをキャプチャ
            value = selection['value']
            button.on_click = lambda v=value: self._handle_dialog_action(
                dialog_id, on_select, v
            )
            buttons.append(button)
        
        # キャンセルボタンを追加
        cancel_button = self._create_button(
            f"{dialog_id}_cancel",
            ButtonType.CANCEL,
            lambda: self._handle_dialog_action(dialog_id, on_cancel, None)
        )
        buttons.append(cancel_button)
        
        self._add_buttons_to_dialog(dialog, buttons)
        return dialog
    
    def create_error_dialog(self, dialog_id: str, title: str, message: str,
                          on_close: Optional[Callable] = None) -> UIDialog:
        """エラーダイアログを作成
        
        Args:
            dialog_id: ダイアログID
            title: タイトル
            message: エラーメッセージ
            on_close: 閉じる時のコールバック
            
        Returns:
            UIDialog: 作成されたダイアログ
        """
        dialog = self._create_base_dialog(dialog_id, title, message)
        
        # エラー用の視覚的な変更
        dialog.background_color = (80, 50, 50)  # 赤みがかった背景
        
        # OKボタンを追加
        ok_button = self._create_button(
            f"{dialog_id}_ok",
            ButtonType.OK,
            lambda: self._handle_dialog_close(dialog_id, on_close)
        )
        
        self._add_buttons_to_dialog(dialog, [ok_button])
        return dialog
    
    def create_success_dialog(self, dialog_id: str, title: str, message: str,
                            on_close: Optional[Callable] = None) -> UIDialog:
        """成功ダイアログを作成
        
        Args:
            dialog_id: ダイアログID
            title: タイトル
            message: 成功メッセージ
            on_close: 閉じる時のコールバック
            
        Returns:
            UIDialog: 作成されたダイアログ
        """
        dialog = self._create_base_dialog(dialog_id, title, message)
        
        # 成功用の視覚的な変更
        dialog.background_color = (50, 80, 50)  # 緑みがかった背景
        
        # OKボタンを追加
        ok_button = self._create_button(
            f"{dialog_id}_ok",
            ButtonType.OK,
            lambda: self._handle_dialog_close(dialog_id, on_close)
        )
        
        self._add_buttons_to_dialog(dialog, [ok_button])
        return dialog
    
    def show_dialog(self, dialog: UIDialog) -> bool:
        """ダイアログを表示
        
        Args:
            dialog: 表示するダイアログ
            
        Returns:
            bool: 成功した場合True
        """
        try:
            # ui_managerがNoneの場合はmenu_stack_managerから取得を試行
            current_ui_manager = ui_manager
            if current_ui_manager is None and self.menu_stack_manager:
                current_ui_manager = self.menu_stack_manager.ui_manager
            
            if current_ui_manager is None:
                logger.warning(f"ui_managerが利用できないため、ダイアログ表示をスキップ: {dialog.dialog_id}")
                return False
            
            self.active_dialogs[dialog.dialog_id] = dialog
            current_ui_manager.add_dialog(dialog)
            current_ui_manager.show_dialog(dialog.dialog_id)
            
            logger.info(f"ダイアログを表示: {dialog.dialog_id}")
            return True
            
        except Exception as e:
            logger.error(f"ダイアログ表示エラー: {e}")
            return False
    
    def hide_dialog(self, dialog_id: str) -> bool:
        """ダイアログを隠す
        
        Args:
            dialog_id: ダイアログID
            
        Returns:
            bool: 成功した場合True
        """
        try:
            if dialog_id in self.active_dialogs:
                # UIマネージャーが利用可能な場合のみhide_dialogを呼ぶ
                if ui_manager:
                    ui_manager.hide_dialog(dialog_id)
                
                # UIマネージャーが利用できなくても内部状態はクリーンアップ
                del self.active_dialogs[dialog_id]
                
                # コールバックもクリーンアップ
                if dialog_id in self.dialog_callbacks:
                    del self.dialog_callbacks[dialog_id]
                
                logger.info(f"ダイアログを隠しました: {dialog_id}")
                return True
            return False
            
        except Exception as e:
            logger.error(f"ダイアログ非表示エラー: {e}")
            # エラーが発生してもactive_dialogsからは削除する
            if dialog_id in self.active_dialogs:
                del self.active_dialogs[dialog_id]
            if dialog_id in self.dialog_callbacks:
                del self.dialog_callbacks[dialog_id]
            return False
    
    def handle_escape_key(self, dialog_id: str) -> bool:
        """ダイアログでのESCキー処理
        
        Args:
            dialog_id: ダイアログID
            
        Returns:
            bool: 処理した場合True
        """
        if dialog_id in self.active_dialogs:
            # 戻るまたはキャンセル処理を実行
            self.hide_dialog(dialog_id)
            
            # メニュースタックマネージャーがある場合は適切に戻る
            if self.menu_stack_manager:
                self.menu_stack_manager.back_to_previous()
            
            return True
        return False
    
    def _create_base_dialog(self, dialog_id: str, title: str, message: str) -> UIDialog:
        """基本ダイアログを作成"""
        dialog = UIDialog(dialog_id, title, message)
        
        # デフォルトサイズと位置を設定
        screen_width = 800  # デフォルト画面幅
        screen_height = 600  # デフォルト画面高
        
        x = (screen_width - self.default_dialog_width) // 2
        y = (screen_height - self.default_dialog_height) // 2
        
        dialog.rect = pygame.Rect(x, y, self.default_dialog_width, self.default_dialog_height)
        
        return dialog
    
    def _create_button(self, button_id: str, button_type: ButtonType, 
                      on_click: Callable) -> UIButton:
        """標準ボタンを作成"""
        config = ButtonTemplate.get_button_config(button_type)
        
        button = UIButton(
            button_id,
            config['text'],
            0, 0,  # 位置は後で設定
            self.button_width,
            self.button_height
        )
        
        button.on_click = on_click
        button.background_color = config['color']
        
        return button
    
    def _add_buttons_to_dialog(self, dialog: UIDialog, buttons: List[UIButton]) -> None:
        """ダイアログにボタンを追加"""
        if not buttons:
            return
        
        # ボタンを下部中央に配置
        total_width = len(buttons) * self.button_width + (len(buttons) - 1) * self.button_spacing
        start_x = dialog.rect.x + (dialog.rect.width - total_width) // 2
        button_y = dialog.rect.y + dialog.rect.height - self.button_height - 20
        
        for i, button in enumerate(buttons):
            button.rect.x = start_x + i * (self.button_width + self.button_spacing)
            button.rect.y = button_y
            dialog.add_element(button)
    
    def _handle_dialog_close(self, dialog_id: str, callback: Optional[Callable]) -> None:
        """ダイアログ閉じる処理"""
        self.hide_dialog(dialog_id)
        
        if callback:
            try:
                callback()
            except Exception as e:
                logger.error(f"ダイアログクローズコールバックエラー: {e}")
        
        # MenuStackManager削除により、メニュー戻り処理も削除
        # WindowSystemが代替機能を提供
        logger.debug(f"ダイアログ {dialog_id} を閉じました（WindowSystem移行済み）")
    
    def _handle_dialog_action(self, dialog_id: str, callback: Optional[Callable], 
                            value: Any) -> None:
        """ダイアログアクション処理"""
        self.hide_dialog(dialog_id)
        
        if callback:
            try:
                if value is not None:
                    callback(value)
                else:
                    callback()
            except Exception as e:
                logger.error(f"ダイアログアクションコールバックエラー: {e}")
        
        # メニュースタックマネージャーがある場合は適切に処理
        if self.menu_stack_manager:
            # 確認系の場合は前のメニューに戻る
            self.menu_stack_manager.back_to_previous()
    
    def cleanup_all_dialogs(self) -> None:
        """全てのダイアログをクリーンアップ"""
        try:
            dialog_ids = list(self.active_dialogs.keys())
            for dialog_id in dialog_ids:
                self.hide_dialog(dialog_id)
            
            logger.info("全てのダイアログをクリーンアップしました")
            
        except Exception as e:
            logger.error(f"ダイアログクリーンアップエラー: {e}")
    
    def get_debug_info(self) -> Dict[str, Any]:
        """デバッグ情報を取得"""
        return {
            'active_dialogs': list(self.active_dialogs.keys()),
            'dialog_count': len(self.active_dialogs),
            'callback_count': len(self.dialog_callbacks)
        }