"""コントローラー入力システムの簡単なテスト"""

import pytest
from unittest.mock import Mock, patch

def test_input_enums():
    """入力システムのEnum定義テスト"""
    from src.core.input_manager import InputAction, InputType, GamepadButton
    
    # InputActionの基本的な値をチェック
    assert InputAction.MOVE_FORWARD.value == "move_forward"
    assert InputAction.CONFIRM.value == "confirm"
    assert InputAction.MENU.value == "menu"
    
    # InputTypeの値をチェック
    assert InputType.KEYBOARD.value == "keyboard"
    assert InputType.GAMEPAD.value == "gamepad"
    
    # GamepadButtonの値をチェック
    assert GamepadButton.FACE_A.value == "face_a"
    assert GamepadButton.DPAD_UP.value == "dpad_up"


@patch('src.core.input_manager.logger')
@patch('src.core.input_manager.DirectObject')
def test_input_manager_basic_creation(mock_direct_object, mock_logger):
    """入力マネージャーの基本的な作成テスト"""
    from src.core.input_manager import InputManager
    
    # DirectObjectのモック設定
    mock_instance = Mock()
    mock_instance.accept = Mock()
    mock_instance.taskMgr = Mock()
    mock_instance.taskMgr.add = Mock()
    mock_direct_object.return_value = mock_instance
    
    # baseのモック
    mock_base = Mock()
    mock_base.devices = Mock()
    mock_base.devices.getDevices.return_value = []
    
    with patch('builtins.base', mock_base):
        input_manager = InputManager()
        
        # 基本プロパティが設定されていることを確認
        assert hasattr(input_manager, 'keyboard_enabled')
        assert hasattr(input_manager, 'controller_enabled')
        assert hasattr(input_manager, 'analog_deadzone')
        assert hasattr(input_manager, 'analog_sensitivity')


def test_action_binding_logic():
    """アクションバインディングのロジックテスト"""
    from src.core.input_manager import InputManager, InputAction, InputType
    
    # 最小限のモック設定
    with patch.multiple(InputManager, 
                       __init__=lambda x: None,
                       accept=Mock(),
                       taskMgr=Mock()):
        
        input_manager = InputManager()
        input_manager.action_callbacks = {}
        input_manager.keyboard_enabled = True
        input_manager.controller_enabled = True
        
        # アクションバインディングのテスト
        test_callback = Mock()
        action = InputAction.MOVE_FORWARD.value
        
        input_manager.bind_action(action, test_callback)
        assert action in input_manager.action_callbacks
        
        # アクション処理のテスト
        input_manager._handle_action(action, True, InputType.KEYBOARD)
        test_callback.assert_called_once_with(action, True, InputType.KEYBOARD)


def test_analog_settings_logic():
    """アナログ設定のロジックテスト"""
    from src.core.input_manager import InputManager
    
    # 最小限のモック設定
    with patch.multiple(InputManager, __init__=lambda x: None):
        input_manager = InputManager()
        input_manager.analog_deadzone = 0.3
        input_manager.analog_sensitivity = 1.0
        
        # デッドゾーン設定テスト
        input_manager.set_analog_deadzone(0.5)
        assert input_manager.analog_deadzone == 0.5
        
        # 範囲外の値は制限される
        input_manager.set_analog_deadzone(-0.1)
        assert input_manager.analog_deadzone == 0.0
        
        input_manager.set_analog_deadzone(1.5)
        assert input_manager.analog_deadzone == 1.0
        
        # 感度設定テスト
        input_manager.set_analog_sensitivity(2.0)
        assert input_manager.analog_sensitivity == 2.0
        
        # 範囲外の値は制限される
        input_manager.set_analog_sensitivity(0.05)
        assert input_manager.analog_sensitivity == 0.1
        
        input_manager.set_analog_sensitivity(5.0)
        assert input_manager.analog_sensitivity == 3.0


def test_binding_info_structure():
    """バインディング情報の構造テスト"""
    from src.core.input_manager import InputManager
    
    with patch.multiple(InputManager, __init__=lambda x: None):
        input_manager = InputManager()
        input_manager.keyboard_bindings = {"w": "move_forward"}
        input_manager.gamepad_bindings = {"face_a": "confirm"}
        input_manager.action_callbacks = {"move_forward": Mock()}
        
        info = input_manager.get_binding_info()
        
        assert "keyboard" in info
        assert "gamepad" in info
        assert "actions" in info
        assert info["keyboard"]["w"] == "move_forward"
        assert info["gamepad"]["face_a"] == "confirm"
        assert "move_forward" in info["actions"]


def test_input_status_structure():
    """入力状態の構造テスト"""
    from src.core.input_manager import InputManager
    
    with patch.multiple(InputManager, __init__=lambda x: None):
        input_manager = InputManager()
        input_manager.keyboard_enabled = True
        input_manager.controller_enabled = True
        input_manager.active_gamepad = None
        input_manager.analog_deadzone = 0.3
        input_manager.analog_sensitivity = 1.0
        input_manager.left_stick_x = 0.0
        input_manager.left_stick_y = 0.0
        input_manager.right_stick_x = 0.0
        input_manager.right_stick_y = 0.0
        input_manager.devices = {}
        
        status = input_manager.get_input_status()
        
        expected_keys = [
            "keyboard_enabled", "controller_enabled", "active_gamepad",
            "available_controllers", "analog_deadzone", "analog_sensitivity",
            "left_stick", "right_stick"
        ]
        
        for key in expected_keys:
            assert key in status


@patch('src.ui.controller_settings_ui.logger')
@patch('src.ui.controller_settings_ui.ui_manager')
def test_controller_settings_ui_basic(mock_ui_manager, mock_logger):
    """コントローラー設定UIの基本テスト"""
    from src.ui.controller_settings_ui import ControllerSettingsMenu
    
    # InputManagerのモック
    mock_input_manager = Mock()
    mock_input_manager.get_input_status.return_value = {
        "keyboard_enabled": True,
        "controller_enabled": True,
        "active_gamepad": None,
        "available_controllers": [],
        "analog_deadzone": 0.3,
        "analog_sensitivity": 1.0,
        "left_stick": (0.0, 0.0),
        "right_stick": (0.0, 0.0)
    }
    
    # Panda3D UIコンポーネントをモック
    with patch('src.ui.controller_settings_ui.DirectFrame'), \
         patch('src.ui.controller_settings_ui.OnscreenText'), \
         patch('src.ui.controller_settings_ui.UIButton'):
        
        ui = ControllerSettingsMenu(mock_input_manager)
        
        # 基本プロパティの確認
        assert ui.input_manager == mock_input_manager
        assert hasattr(ui, 'settings_data')


def test_controller_integration_with_game_manager():
    """ゲームマネージャーとのコントローラー統合テスト"""
    from src.core.input_manager import InputAction
    
    # 統合テストの基本的な構造確認
    action_types = [
        InputAction.MOVE_FORWARD,
        InputAction.MOVE_BACKWARD, 
        InputAction.TURN_LEFT,
        InputAction.TURN_RIGHT,
        InputAction.MENU,
        InputAction.CONFIRM,
        InputAction.INVENTORY,
        InputAction.MAGIC
    ]
    
    # すべてのアクションが定義されていることを確認
    for action in action_types:
        assert hasattr(action, 'value')
        assert isinstance(action.value, str)


def test_save_load_bindings_structure():
    """バインディング保存・読み込みの構造テスト"""
    from src.core.input_manager import InputManager
    
    with patch.multiple(InputManager, __init__=lambda x: None):
        input_manager = InputManager()
        input_manager.keyboard_bindings = {"w": "move_forward"}
        input_manager.gamepad_bindings = {"face_a": "confirm"}
        input_manager.analog_deadzone = 0.5
        input_manager.analog_sensitivity = 1.5
        input_manager.controller_enabled = False
        input_manager.keyboard_enabled = True
        
        # 保存データの構造をチェック
        saved_data = input_manager.save_bindings()
        
        expected_keys = [
            "keyboard_bindings", "gamepad_bindings", "analog_deadzone",
            "analog_sensitivity", "controller_enabled", "keyboard_enabled"
        ]
        
        for key in expected_keys:
            assert key in saved_data
        
        assert saved_data["keyboard_bindings"]["w"] == "move_forward"
        assert saved_data["gamepad_bindings"]["face_a"] == "confirm"
        assert saved_data["analog_deadzone"] == 0.5