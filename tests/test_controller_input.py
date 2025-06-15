"""コントローラー入力システムのテスト"""

import pytest
from unittest.mock import Mock, patch, MagicMock

from src.core.input_manager import (
    InputManager, InputAction, InputType, GamepadButton
)


class TestInputManager:
    """入力マネージャーのテスト"""
    
    @patch('src.core.input_manager.logger')
    @patch('src.core.input_manager.DirectObject.__init__')
    def setup_method(self, mock_direct_object, mock_logger):
        """各テストメソッドの前に実行"""
        # DirectObjectの初期化をモック
        mock_direct_object.return_value = None
        
        # 必要なメソッドをモック
        with patch.object(InputManager, 'accept'), \
             patch.object(InputManager, 'taskMgr') as mock_task_mgr:
            
            mock_task_mgr.add = Mock()
            
            # Panda3Dのbaseをモック
            self.mock_base = Mock()
            self.mock_base.devices = Mock()
            self.mock_base.devices.getDevices.return_value = []
            
            with patch('builtins.base', self.mock_base):
                self.input_manager = InputManager()
    
    def test_input_manager_initialization(self):
        """入力マネージャーの初期化テスト"""
        assert self.input_manager.keyboard_enabled == True
        assert self.input_manager.controller_enabled == True
        assert self.input_manager.analog_deadzone == 0.3
        assert self.input_manager.analog_sensitivity == 1.0
        assert len(self.input_manager.keyboard_bindings) > 0
        assert len(self.input_manager.gamepad_bindings) > 0
    
    def test_keyboard_bindings_setup(self):
        """キーボードバインディング設定テスト"""
        # デフォルトバインディングをチェック
        assert "w" in self.input_manager.keyboard_bindings
        assert self.input_manager.keyboard_bindings["w"] == InputAction.MOVE_FORWARD.value
        assert "escape" in self.input_manager.keyboard_bindings
        assert self.input_manager.keyboard_bindings["escape"] == InputAction.MENU.value
    
    def test_gamepad_bindings_setup(self):
        """ゲームパッドバインディング設定テスト"""
        # デフォルトバインディングをチェック
        assert GamepadButton.FACE_A.value in self.input_manager.gamepad_bindings
        assert self.input_manager.gamepad_bindings[GamepadButton.FACE_A.value] == InputAction.CONFIRM.value
        assert GamepadButton.DPAD_UP.value in self.input_manager.gamepad_bindings
        assert self.input_manager.gamepad_bindings[GamepadButton.DPAD_UP.value] == InputAction.MOVE_FORWARD.value
    
    def test_action_binding(self):
        """アクションバインディングのテスト"""
        test_callback = Mock()
        action = "test_action"
        
        self.input_manager.bind_action(action, test_callback)
        assert action in self.input_manager.action_callbacks
        assert self.input_manager.action_callbacks[action] == test_callback
        
        # アクション実行テスト
        self.input_manager._handle_action(action, True, InputType.KEYBOARD)
        test_callback.assert_called_once_with(action, True, InputType.KEYBOARD)
    
    def test_action_unbinding(self):
        """アクションバインディング解除のテスト"""
        test_callback = Mock()
        action = "test_action"
        
        self.input_manager.bind_action(action, test_callback)
        self.input_manager.unbind_action(action)
        
        assert action not in self.input_manager.action_callbacks
    
    def test_analog_settings(self):
        """アナログ設定のテスト"""
        # デッドゾーン設定
        self.input_manager.set_analog_deadzone(0.5)
        assert self.input_manager.analog_deadzone == 0.5
        
        # 範囲外の値は制限される
        self.input_manager.set_analog_deadzone(-0.1)
        assert self.input_manager.analog_deadzone == 0.0
        
        self.input_manager.set_analog_deadzone(1.5)
        assert self.input_manager.analog_deadzone == 1.0
        
        # 感度設定
        self.input_manager.set_analog_sensitivity(2.0)
        assert self.input_manager.analog_sensitivity == 2.0
        
        # 範囲外の値は制限される
        self.input_manager.set_analog_sensitivity(0.05)
        assert self.input_manager.analog_sensitivity == 0.1
        
        self.input_manager.set_analog_sensitivity(5.0)
        assert self.input_manager.analog_sensitivity == 3.0
    
    def test_keyboard_input_handling(self):
        """キーボード入力処理のテスト"""
        test_callback = Mock()
        action = InputAction.MOVE_FORWARD.value
        
        self.input_manager.bind_action(action, test_callback)
        
        # キーボード入力をシミュレート
        self.input_manager._on_keyboard_input(action, True)
        test_callback.assert_called_once_with(action, True, InputType.KEYBOARD)
        
        test_callback.reset_mock()
        
        # キーボード無効時は呼ばれない
        self.input_manager.enable_keyboard(False)
        self.input_manager._on_keyboard_input(action, True)
        test_callback.assert_not_called()
    
    def test_gamepad_input_handling(self):
        """ゲームパッド入力処理のテスト"""
        test_callback = Mock()
        action = InputAction.CONFIRM.value
        button = GamepadButton.FACE_A.value
        
        self.input_manager.bind_action(action, test_callback)
        
        # ゲームパッド入力をシミュレート
        self.input_manager._on_gamepad_input("test_gamepad", button, True)
        test_callback.assert_called_once_with(action, True, InputType.GAMEPAD)
        
        test_callback.reset_mock()
        
        # コントローラー無効時は呼ばれない
        self.input_manager.enable_controller(False)
        self.input_manager._on_gamepad_input("test_gamepad", button, True)
        test_callback.assert_not_called()
    
    def test_controller_setup(self):
        """コントローラー設定のテスト"""
        # モックゲームパッドを作成
        mock_gamepad = Mock()
        mock_gamepad.name = "Test Controller"
        mock_gamepad.device_class = Mock()
        mock_gamepad.device_class.gamepad = "gamepad"
        
        # デバイスクラスを正しく設定
        with patch('src.core.input_manager.InputDevice') as mock_input_device:
            mock_input_device.DeviceClass.gamepad = "gamepad"
            mock_gamepad.device_class = "gamepad"
            
            self.mock_base.devices.getDevices.return_value = [mock_gamepad]
            
            self.input_manager.setup_controllers()
            
            assert "Test Controller" in self.input_manager.devices
            assert self.input_manager.active_gamepad == mock_gamepad
    
    def test_analog_input_processing(self):
        """アナログ入力処理のテスト"""
        test_callback = Mock()
        
        # 移動アクションをバインド
        self.input_manager.bind_action(InputAction.MOVE_FORWARD.value, test_callback)
        self.input_manager.bind_action(InputAction.TURN_LEFT.value, test_callback)
        
        # アナログ入力をシミュレート（前進）
        self.input_manager._handle_analog_input("left_stick", 0.0, -0.8)
        test_callback.assert_called_with(InputAction.MOVE_FORWARD.value, True, InputType.GAMEPAD)
        
        test_callback.reset_mock()
        
        # アナログ入力をシミュレート（左回転）
        self.input_manager._handle_analog_input("left_stick", -0.8, 0.0)
        test_callback.assert_called_with(InputAction.TURN_LEFT.value, True, InputType.GAMEPAD)
    
    def test_custom_binding(self):
        """カスタムバインディングのテスト"""
        action = InputAction.CONFIRM.value
        new_key = "space"
        
        # カスタムキーボードバインディング
        self.input_manager.customize_binding(InputType.KEYBOARD, new_key, action)
        assert self.input_manager.keyboard_bindings[new_key] == action
        
        # カスタムゲームパッドバインディング
        new_button = GamepadButton.FACE_X.value
        self.input_manager.customize_binding(InputType.GAMEPAD, new_button, action)
        assert self.input_manager.gamepad_bindings[new_button] == action
    
    def test_binding_info_retrieval(self):
        """バインディング情報取得のテスト"""
        info = self.input_manager.get_binding_info()
        
        assert "keyboard" in info
        assert "gamepad" in info
        assert "actions" in info
        
        assert isinstance(info["keyboard"], dict)
        assert isinstance(info["gamepad"], dict)
        assert isinstance(info["actions"], list)
    
    def test_input_status(self):
        """入力状態取得のテスト"""
        status = self.input_manager.get_input_status()
        
        expected_keys = [
            "keyboard_enabled", "controller_enabled", "active_gamepad",
            "available_controllers", "analog_deadzone", "analog_sensitivity",
            "left_stick", "right_stick"
        ]
        
        for key in expected_keys:
            assert key in status
    
    def test_save_load_bindings(self):
        """バインディング保存・読み込みのテスト"""
        # 設定を変更
        self.input_manager.set_analog_deadzone(0.5)
        self.input_manager.set_analog_sensitivity(1.5)
        self.input_manager.enable_controller(False)
        
        # 保存
        saved_data = self.input_manager.save_bindings()
        
        # 設定を初期化
        self.input_manager.set_analog_deadzone(0.3)
        self.input_manager.set_analog_sensitivity(1.0)
        self.input_manager.enable_controller(True)
        
        # 読み込み
        self.input_manager.load_bindings(saved_data)
        
        # 設定が復元されているかチェック
        assert self.input_manager.analog_deadzone == 0.5
        assert self.input_manager.analog_sensitivity == 1.5
        assert self.input_manager.controller_enabled == False
    
    def test_cleanup(self):
        """クリーンアップのテスト"""
        # 何らかのデータを設定
        self.input_manager.bind_action("test", Mock())
        self.input_manager.devices["test"] = Mock()
        
        # クリーンアップ実行
        self.input_manager.cleanup()
        
        # データがクリアされていることを確認
        assert len(self.input_manager.action_callbacks) == 0
        assert len(self.input_manager.devices) == 0
        assert self.input_manager.active_gamepad is None


class TestControllerSettingsUI:
    """コントローラー設定UIのテスト"""
    
    def setup_method(self):
        """各テストメソッドの前に実行"""
        self.mock_input_manager = Mock(spec=InputManager)
        self.mock_input_manager.get_input_status.return_value = {
            "keyboard_enabled": True,
            "controller_enabled": True,
            "active_gamepad": None,
            "available_controllers": [],
            "analog_deadzone": 0.3,
            "analog_sensitivity": 1.0,
            "left_stick": (0.0, 0.0),
            "right_stick": (0.0, 0.0)
        }
    
    @patch('src.ui.controller_settings_ui.DirectFrame')
    @patch('src.ui.controller_settings_ui.OnscreenText')
    def test_controller_settings_ui_creation(self, mock_text, mock_frame):
        """コントローラー設定UI作成のテスト"""
        from src.ui.controller_settings_ui import ControllerSettingsMenu
        
        ui = ControllerSettingsMenu(self.mock_input_manager)
        
        # UI要素が作成されていることを確認
        assert ui.input_manager == self.mock_input_manager
        assert mock_frame.called
        assert mock_text.called
    
    @patch('src.ui.controller_settings_ui.DirectFrame')
    @patch('src.ui.controller_settings_ui.OnscreenText')
    def test_controller_toggle(self, mock_text, mock_frame):
        """コントローラー有効/無効切り替えのテスト"""
        from src.ui.controller_settings_ui import ControllerSettingsMenu
        
        ui = ControllerSettingsMenu(self.mock_input_manager)
        
        # 初期状態は有効
        self.mock_input_manager.controller_enabled = True
        
        # 無効に切り替え
        ui._toggle_controller()
        
        self.mock_input_manager.enable_controller.assert_called_with(False)
    
    @patch('src.ui.controller_settings_ui.DirectFrame')
    @patch('src.ui.controller_settings_ui.OnscreenText')
    def test_analog_settings(self, mock_text, mock_frame):
        """アナログ設定のテスト"""
        from src.ui.controller_settings_ui import ControllerSettingsMenu
        
        ui = ControllerSettingsMenu(self.mock_input_manager)
        
        # デッドゾーン設定
        ui._apply_deadzone(0.5)
        self.mock_input_manager.set_analog_deadzone.assert_called_with(0.5)
        
        # 感度設定
        ui._apply_sensitivity(1.5)
        self.mock_input_manager.set_analog_sensitivity.assert_called_with(1.5)


class TestInputIntegration:
    """入力システム統合テスト"""
    
    def setup_method(self):
        """各テストメソッドの前に実行"""
        self.mock_base = Mock()
        self.mock_base.devices = Mock()
        self.mock_base.devices.getDevices.return_value = []
        
        with patch('src.core.input_manager.base', self.mock_base):
            self.input_manager = InputManager()
    
    def test_input_action_flow(self):
        """入力アクションフローの統合テスト"""
        action_log = []
        
        def test_callback(action, pressed, input_type):
            action_log.append((action, pressed, input_type))
        
        # アクションをバインド
        self.input_manager.bind_action(InputAction.MOVE_FORWARD.value, test_callback)
        
        # キーボード入力をシミュレート
        self.input_manager._on_keyboard_input(InputAction.MOVE_FORWARD.value, True)
        
        # ゲームパッド入力をシミュレート
        self.input_manager._on_gamepad_input("test_pad", GamepadButton.DPAD_UP.value, True)
        
        # 両方の入力が記録されていることを確認
        assert len(action_log) == 2
        assert action_log[0] == (InputAction.MOVE_FORWARD.value, True, InputType.KEYBOARD)
        assert action_log[1] == (InputAction.MOVE_FORWARD.value, True, InputType.GAMEPAD)
    
    def test_input_system_with_game_manager(self):
        """ゲームマネージャーとの統合テスト"""
        from src.core.game_manager import GameManager
        
        with patch('src.core.game_manager.ShowBase'):
            with patch('src.core.game_manager.OnscreenText'):
                with patch('src.core.config_manager.config_manager'):
                    game_manager = GameManager()
                    
                    # 入力マネージャーが正しく初期化されていることを確認
                    assert hasattr(game_manager, 'input_manager')
                    assert isinstance(game_manager.input_manager, InputManager)
                    
                    # アクションがバインドされていることを確認
                    assert InputAction.MENU.value in game_manager.input_manager.action_callbacks
                    assert InputAction.MOVE_FORWARD.value in game_manager.input_manager.action_callbacks