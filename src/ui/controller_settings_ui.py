"""コントローラー設定UI"""

from typing import Dict, List, Optional, Callable
from enum import Enum

from src.ui.base_ui import UIElement, UIButton, UIText, UIMenu, UIDialog, UIState, ui_manager
from src.core.input_manager import InputManager, InputAction, InputType, GamepadButton
from src.core.config_manager import config_manager
from src.utils.logger import logger


class ControllerSettingsMenu(UIElement):
    """コントローラー設定メニュー"""
    
    def __init__(self, input_manager: InputManager, element_id: str = "controller_settings"):
        super().__init__(element_id)
        
        self.input_manager = input_manager
        self.settings_data = {}
        self.callback_on_close: Optional[Callable] = None
        
        # UI要素
        self.background = None
        self.title_text = None
        self.menu_buttons: List[UIButton] = []
        self.status_texts: List[UIText] = []
        
        self._create_ui()
        self._update_display()
    
    def _create_ui(self):
        """UI要素を作成"""
        from direct.gui.DirectGui import DirectFrame
        from direct.gui.OnscreenText import OnscreenText
        from panda3d.core import TextNode
        
        # 背景
        self.background = DirectFrame(
            frameColor=(0, 0, 0, 0.8),
            frameSize=(-1.5, 1.5, -1, 1),
            pos=(0, 0, 0)
        )
        
        # タイトル
        self.title_text = OnscreenText(
            text="コントローラー設定",
            pos=(0, 0.8),
            scale=0.08,
            fg=(1, 1, 1, 1),
            align=TextNode.ACenter
        )
        
        # メニューボタンを作成
        self._create_menu_buttons()
        
        # ステータステキストを作成
        self._create_status_texts()
        
        # 初期状態は非表示
        self.hide()
    
    def _create_menu_buttons(self):
        """メニューボタンを作成"""
        menu_items = [
            {"text": "コントローラー有効/無効", "action": "toggle_controller"},
            {"text": "アクティブコントローラー選択", "action": "select_controller"},
            {"text": "ボタン設定", "action": "button_settings"},
            {"text": "アナログ設定", "action": "analog_settings"},
            {"text": "設定をリセット", "action": "reset_settings"},
            {"text": "設定をテスト", "action": "test_controller"},
            {"text": "設定を保存", "action": "save_settings"},
            {"text": "戻る", "action": "close"}
        ]
        
        start_y = 0.5
        button_height = 0.08
        
        for i, item in enumerate(menu_items):
            y_pos = start_y - i * button_height
            
            button = UIButton(
                f"{self.element_id}_btn_{item['action']}",
                item['text'],
                pos=(0, y_pos),
                scale=(0.3, 0.04),
                command=self._on_menu_click,
                extraArgs=[item['action']]
            )
            
            self.menu_buttons.append(button)
    
    def _create_status_texts(self):
        """ステータステキストを作成"""
        from direct.gui.OnscreenText import OnscreenText
        from panda3d.core import TextNode
        
        # コントローラー状態表示
        self.controller_status_text = OnscreenText(
            text="",
            pos=(-1.3, -0.3),
            scale=0.04,
            fg=(1, 1, 1, 1),
            align=TextNode.ALeft
        )
        
        # アナログ設定表示
        self.analog_status_text = OnscreenText(
            text="",
            pos=(-1.3, -0.6),
            scale=0.04,
            fg=(1, 1, 1, 1),
            align=TextNode.ALeft
        )
        
        # ヘルプテキスト
        self.help_text = OnscreenText(
            text="コントローラーを接続してから設定してください",
            pos=(0, -0.9),
            scale=0.03,
            fg=(0.7, 0.7, 0.7, 1),
            align=TextNode.ACenter
        )
    
    def _update_display(self):
        """表示を更新"""
        status = self.input_manager.get_input_status()
        
        # コントローラー状態
        controller_text = f"コントローラー: {'有効' if status['controller_enabled'] else '無効'}\n"
        if status['active_gamepad']:
            controller_text += f"アクティブ: {status['active_gamepad']}\n"
        else:
            controller_text += "アクティブ: なし\n"
        
        available = status['available_controllers']
        controller_text += f"検出数: {len(available)}個"
        
        self.controller_status_text.setText(controller_text)
        
        # アナログ設定
        analog_text = f"デッドゾーン: {status['analog_deadzone']:.2f}\n"
        analog_text += f"感度: {status['analog_sensitivity']:.2f}\n"
        analog_text += f"左スティック: ({status['left_stick'][0]:.2f}, {status['left_stick'][1]:.2f})\n"
        analog_text += f"右スティック: ({status['right_stick'][0]:.2f}, {status['right_stick'][1]:.2f})"
        
        self.analog_status_text.setText(analog_text)
    
    def _on_menu_click(self, action: str):
        """メニュークリック処理"""
        logger.info(f"コントローラー設定メニュー選択: {action}")
        
        if action == "toggle_controller":
            self._toggle_controller()
        elif action == "select_controller":
            self._show_controller_selection()
        elif action == "button_settings":
            self._show_button_settings()
        elif action == "analog_settings":
            self._show_analog_settings()
        elif action == "reset_settings":
            self._reset_settings()
        elif action == "test_controller":
            self._test_controller()
        elif action == "save_settings":
            self._save_settings()
        elif action == "close":
            self.hide()
            if self.callback_on_close:
                self.callback_on_close()
    
    def _toggle_controller(self):
        """コントローラー有効/無効切り替え"""
        current_state = self.input_manager.controller_enabled
        self.input_manager.enable_controller(not current_state)
        
        if not current_state:
            # 有効化した場合、コントローラーを再検索
            self.input_manager.setup_controllers()
        
        self._update_display()
        
        state_text = "有効" if not current_state else "無効"
        self._show_message(f"コントローラーを{state_text}にしました")
    
    def _show_controller_selection(self):
        """コントローラー選択ダイアログ"""
        available = self.input_manager.get_available_controllers()
        
        if not available:
            self._show_message("利用可能なコントローラーがありません")
            return
        
        selection_menu = UIMenu("controller_selection", "コントローラー選択")
        
        for controller_name in available:
            active_mark = " [アクティブ]" if controller_name == self.input_manager.get_active_gamepad().name else ""
            selection_menu.add_menu_item(
                f"{controller_name}{active_mark}",
                self._select_controller,
                [controller_name]
            )
        
        selection_menu.add_menu_item("キャンセル", self._close_selection_menu)
        
        ui_manager.register_element(selection_menu)
        ui_manager.show_element(selection_menu.element_id, modal=True)
    
    def _select_controller(self, controller_name: str):
        """コントローラーを選択"""
        success = self.input_manager.set_active_gamepad(controller_name)
        if success:
            self._update_display()
            self._show_message(f"{controller_name}をアクティブにしました")
        else:
            self._show_message(f"{controller_name}の設定に失敗しました")
        
        self._close_selection_menu()
    
    def _close_selection_menu(self):
        """選択メニューを閉じる"""
        ui_manager.hide_element("controller_selection")
    
    def _show_button_settings(self):
        """ボタン設定ダイアログ"""
        button_menu = UIMenu("button_settings", "ボタン設定")
        
        # 主要なアクション
        actions = [
            (InputAction.CONFIRM, "確定"),
            (InputAction.CANCEL, "キャンセル"),
            (InputAction.ACTION, "アクション"),
            (InputAction.MENU, "メニュー"),
            (InputAction.INVENTORY, "インベントリ"),
            (InputAction.MAGIC, "魔法"),
            (InputAction.EQUIPMENT, "装備"),
            (InputAction.STATUS, "ステータス")
        ]
        
        for action, description in actions:
            button_menu.add_menu_item(
                f"{description}の設定",
                self._configure_button,
                [action.value, description]
            )
        
        button_menu.add_menu_item("戻る", self._close_button_settings)
        
        ui_manager.register_element(button_menu)
        ui_manager.show_element(button_menu.element_id, modal=True)
    
    def _configure_button(self, action: str, description: str):
        """ボタン設定"""
        # 現在のバインドを取得
        bindings = self.input_manager.get_binding_info()
        current_button = None
        
        for button, bound_action in bindings["gamepad"].items():
            if bound_action == action:
                current_button = button
                break
        
        current_text = f"現在: {current_button}" if current_button else "現在: 未設定"
        
        dialog_text = f"{description}のボタンを設定します。\n\n{current_text}\n\n"
        dialog_text += "設定したいボタンを押してください..."
        
        # ボタン設定ダイアログを表示
        # 実際の実装では、ボタン入力待ちの状態にする
        self._show_message(f"{description}の設定は今後実装予定です")
        self._close_button_settings()
    
    def _close_button_settings(self):
        """ボタン設定メニューを閉じる"""
        ui_manager.hide_element("button_settings")
    
    def _show_analog_settings(self):
        """アナログ設定ダイアログ"""
        analog_menu = UIMenu("analog_settings", "アナログ設定")
        
        analog_menu.add_menu_item("デッドゾーン設定", self._set_deadzone)
        analog_menu.add_menu_item("感度設定", self._set_sensitivity)
        analog_menu.add_menu_item("デフォルトに戻す", self._reset_analog)
        analog_menu.add_menu_item("戻る", self._close_analog_settings)
        
        ui_manager.register_element(analog_menu)
        ui_manager.show_element(analog_menu.element_id, modal=True)
    
    def _set_deadzone(self):
        """デッドゾーン設定"""
        current = self.input_manager.analog_deadzone
        
        # 簡易的な設定（実際の実装では数値入力UIが必要）
        new_values = [0.1, 0.2, 0.3, 0.4, 0.5]
        value_menu = UIMenu("deadzone_selection", "デッドゾーン選択")
        
        for value in new_values:
            mark = " [現在]" if abs(value - current) < 0.05 else ""
            value_menu.add_menu_item(
                f"{value:.1f}{mark}",
                self._apply_deadzone,
                [value]
            )
        
        value_menu.add_menu_item("キャンセル", self._close_deadzone_selection)
        
        ui_manager.register_element(value_menu)
        ui_manager.show_element(value_menu.element_id, modal=True)
    
    def _apply_deadzone(self, value: float):
        """デッドゾーン適用"""
        self.input_manager.set_analog_deadzone(value)
        self._update_display()
        self._show_message(f"デッドゾーンを{value:.1f}に設定しました")
        self._close_deadzone_selection()
    
    def _close_deadzone_selection(self):
        """デッドゾーン選択を閉じる"""
        ui_manager.hide_element("deadzone_selection")
        self._close_analog_settings()
    
    def _set_sensitivity(self):
        """感度設定"""
        current = self.input_manager.analog_sensitivity
        
        new_values = [0.5, 0.75, 1.0, 1.25, 1.5, 2.0]
        value_menu = UIMenu("sensitivity_selection", "感度選択")
        
        for value in new_values:
            mark = " [現在]" if abs(value - current) < 0.05 else ""
            value_menu.add_menu_item(
                f"{value:.2f}{mark}",
                self._apply_sensitivity,
                [value]
            )
        
        value_menu.add_menu_item("キャンセル", self._close_sensitivity_selection)
        
        ui_manager.register_element(value_menu)
        ui_manager.show_element(value_menu.element_id, modal=True)
    
    def _apply_sensitivity(self, value: float):
        """感度適用"""
        self.input_manager.set_analog_sensitivity(value)
        self._update_display()
        self._show_message(f"感度を{value:.2f}に設定しました")
        self._close_sensitivity_selection()
    
    def _close_sensitivity_selection(self):
        """感度選択を閉じる"""
        ui_manager.hide_element("sensitivity_selection")
        self._close_analog_settings()
    
    def _reset_analog(self):
        """アナログ設定リセット"""
        self.input_manager.set_analog_deadzone(0.3)
        self.input_manager.set_analog_sensitivity(1.0)
        self._update_display()
        self._show_message("アナログ設定をデフォルトに戻しました")
        self._close_analog_settings()
    
    def _close_analog_settings(self):
        """アナログ設定メニューを閉じる"""
        ui_manager.hide_element("analog_settings")
    
    def _reset_settings(self):
        """設定リセット"""
        confirm_dialog = UIDialog(
            "reset_confirm",
            "設定リセット確認",
            "すべてのコントローラー設定をデフォルトに戻しますか？",
            buttons=[
                {"text": "リセット", "command": self._confirm_reset},
                {"text": "キャンセル", "command": self._close_reset_dialog}
            ]
        )
        
        ui_manager.register_element(confirm_dialog)
        ui_manager.show_element(confirm_dialog.element_id, modal=True)
    
    def _confirm_reset(self):
        """リセット実行"""
        # デフォルト設定に戻す
        self.input_manager.set_analog_deadzone(0.3)
        self.input_manager.set_analog_sensitivity(1.0)
        self.input_manager.enable_controller(True)
        
        # デフォルトバインディングを再設定
        self.input_manager._setup_default_bindings()
        
        self._update_display()
        self._show_message("設定をデフォルトに戻しました")
        self._close_reset_dialog()
    
    def _close_reset_dialog(self):
        """リセットダイアログを閉じる"""
        ui_manager.hide_element("reset_confirm")
    
    def _test_controller(self):
        """コントローラーテスト"""
        if not self.input_manager.get_active_gamepad():
            self._show_message("アクティブなコントローラーがありません")
            return
        
        # テストダイアログを表示
        test_text = "コントローラーをテストしています...\n\n"
        test_text += "ボタンを押すかスティックを動かしてください\n"
        test_text += "ESCキーで終了"
        
        test_dialog = UIDialog(
            "controller_test",
            "コントローラーテスト",
            test_text,
            buttons=[
                {"text": "終了", "command": self._close_test_dialog}
            ]
        )
        
        ui_manager.register_element(test_dialog)
        ui_manager.show_element(test_dialog.element_id, modal=True)
    
    def _close_test_dialog(self):
        """テストダイアログを閉じる"""
        ui_manager.hide_element("controller_test")
    
    def _save_settings(self):
        """設定保存"""
        try:
            # 設定をconfig_managerに保存
            bindings_data = self.input_manager.save_bindings()
            config_manager.save_config("input_settings", bindings_data)
            
            self._show_message("設定を保存しました")
            logger.info("コントローラー設定を保存しました")
            
        except Exception as e:
            self._show_message(f"設定保存に失敗: {str(e)}")
            logger.error(f"コントローラー設定保存エラー: {e}")
    
    def _show_message(self, message: str):
        """メッセージ表示"""
        dialog = UIDialog(
            "controller_message",
            "コントローラー設定",
            message,
            buttons=[
                {"text": "OK", "command": self._close_message_dialog}
            ]
        )
        
        ui_manager.register_element(dialog)
        ui_manager.show_element(dialog.element_id, modal=True)
    
    def _close_message_dialog(self):
        """メッセージダイアログを閉じる"""
        ui_manager.hide_element("controller_message")
    
    def set_close_callback(self, callback: Callable):
        """閉じるコールバックを設定"""
        self.callback_on_close = callback
    
    def show(self):
        """メニューを表示"""
        super().show()
        self.state = UIState.MODAL
        self.background.show()
        self.title_text.show()
        self.controller_status_text.show()
        self.analog_status_text.show()
        self.help_text.show()
        
        for button in self.menu_buttons:
            button.show()
        
        self._update_display()
        logger.debug("コントローラー設定メニューを表示")
    
    def hide(self):
        """メニューを非表示"""
        super().hide()
        self.background.hide()
        self.title_text.hide()
        self.controller_status_text.hide()
        self.analog_status_text.hide()
        self.help_text.hide()
        
        for button in self.menu_buttons:
            button.hide()
        
        logger.debug("コントローラー設定メニューを非表示")
    
    def destroy(self):
        """メニューを破棄"""
        if self.background:
            self.background.destroy()
        if self.title_text:
            self.title_text.destroy()
        if self.controller_status_text:
            self.controller_status_text.destroy()
        if self.analog_status_text:
            self.analog_status_text.destroy()
        if self.help_text:
            self.help_text.destroy()
        
        for button in self.menu_buttons:
            button.destroy()
        
        super().destroy()


# グローバルインスタンス
controller_settings_ui = None

def create_controller_settings_ui(input_manager: InputManager) -> ControllerSettingsMenu:
    """コントローラー設定UIを作成"""
    global controller_settings_ui
    if not controller_settings_ui:
        controller_settings_ui = ControllerSettingsMenu(input_manager)
    return controller_settings_ui