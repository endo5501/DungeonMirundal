"""入力管理システム"""

from direct.showbase.DirectObject import DirectObject
from panda3d.core import InputDevice
from typing import Dict, Callable, Optional, List, Tuple
from enum import Enum
from src.utils.logger import logger


class InputType(Enum):
    """入力タイプ"""
    KEYBOARD = "keyboard"
    GAMEPAD = "gamepad"
    BOTH = "both"


class GamepadButton(Enum):
    """ゲームパッドボタン定義"""
    FACE_A = "face_a"           # A/×ボタン（確定）
    FACE_B = "face_b"           # B/○ボタン（キャンセル）
    FACE_X = "face_x"           # X/□ボタン（アクション）
    FACE_Y = "face_y"           # Y/△ボタン（メニュー）
    SHOULDER_LEFT = "shoulder_l"     # Lボタン
    SHOULDER_RIGHT = "shoulder_r"    # Rボタン
    TRIGGER_LEFT = "trigger_l"       # L2/LTボタン
    TRIGGER_RIGHT = "trigger_r"      # R2/RTボタン
    DPAD_UP = "dpad_up"         # 十字キー上
    DPAD_DOWN = "dpad_down"     # 十字キー下
    DPAD_LEFT = "dpad_left"     # 十字キー左
    DPAD_RIGHT = "dpad_right"   # 十字キー右
    START = "start"             # スタートボタン
    SELECT = "back"             # セレクト/バックボタン
    STICK_LEFT = "lstick"       # 左スティック押し込み
    STICK_RIGHT = "rstick"      # 右スティック押し込み


class InputAction(Enum):
    """入力アクション定義"""
    # 移動系
    MOVE_FORWARD = "move_forward"
    MOVE_BACKWARD = "move_backward"
    MOVE_LEFT = "move_left"
    MOVE_RIGHT = "move_right"
    TURN_LEFT = "turn_left"
    TURN_RIGHT = "turn_right"
    
    # UI系
    MENU = "menu"
    CONFIRM = "confirm"
    CANCEL = "cancel"
    ACTION = "action"
    
    # ゲーム系
    INVENTORY = "inventory"
    MAGIC = "magic"
    EQUIPMENT = "equipment"
    STATUS = "status"
    CAMP = "camp"
    
    # システム系
    DEBUG_TOGGLE = "debug_toggle"
    PAUSE = "pause"
    HELP = "help"


class InputManager(DirectObject):
    """キーボード・コントローラー入力の管理"""
    
    def __init__(self):
        super().__init__()
        
        # バインディング管理
        self.action_callbacks: Dict[str, Callable] = {}
        self.keyboard_bindings: Dict[str, str] = {}  # キー -> アクション
        self.gamepad_bindings: Dict[str, str] = {}   # ボタン -> アクション
        
        # デバイス管理
        self.devices: Dict[str, InputDevice] = {}
        self.active_gamepad: Optional[InputDevice] = None
        
        # 設定
        self.controller_enabled = True
        self.keyboard_enabled = True
        self.analog_deadzone = 0.3
        self.analog_sensitivity = 1.0
        
        # アナログスティック状態
        self.left_stick_x = 0.0
        self.left_stick_y = 0.0
        self.right_stick_x = 0.0
        self.right_stick_y = 0.0
        
        # ボタン状態追跡
        self.button_states: Dict[str, bool] = {}
        self.previous_button_states: Dict[str, bool] = {}
        
        # 初期化
        self._setup_default_bindings()
        self._start_input_polling()
        
        logger.info("拡張入力システムを初期化しました")
        
    def _setup_default_bindings(self):
        """デフォルトキーバインディングの設定"""
        # キーボードバインディング
        keyboard_bindings = {
            # 移動
            "w": InputAction.MOVE_FORWARD.value,
            "s": InputAction.MOVE_BACKWARD.value,
            "a": InputAction.TURN_LEFT.value,
            "d": InputAction.TURN_RIGHT.value,
            "q": InputAction.MOVE_LEFT.value,
            "e": InputAction.MOVE_RIGHT.value,
            
            # UI
            "escape": InputAction.MENU.value,
            "enter": InputAction.CONFIRM.value,
            "space": InputAction.ACTION.value,
            "backspace": InputAction.CANCEL.value,
            
            # ゲーム機能
            "i": InputAction.INVENTORY.value,
            "m": InputAction.MAGIC.value,
            "c": InputAction.EQUIPMENT.value,
            "t": InputAction.STATUS.value,
            "r": InputAction.CAMP.value,
            
            # システム
            "f1": InputAction.DEBUG_TOGGLE.value,
            "p": InputAction.PAUSE.value,
            "h": InputAction.HELP.value,
        }
        
        # ゲームパッドバインディング
        gamepad_bindings = {
            # 移動（十字キー）
            GamepadButton.DPAD_UP.value: InputAction.MOVE_FORWARD.value,
            GamepadButton.DPAD_DOWN.value: InputAction.MOVE_BACKWARD.value,
            GamepadButton.DPAD_LEFT.value: InputAction.TURN_LEFT.value,
            GamepadButton.DPAD_RIGHT.value: InputAction.TURN_RIGHT.value,
            
            # ボタン
            GamepadButton.FACE_A.value: InputAction.CONFIRM.value,
            GamepadButton.FACE_B.value: InputAction.CANCEL.value,
            GamepadButton.FACE_X.value: InputAction.ACTION.value,
            GamepadButton.FACE_Y.value: InputAction.INVENTORY.value,
            
            # ショルダーボタン
            GamepadButton.SHOULDER_LEFT.value: InputAction.MAGIC.value,
            GamepadButton.SHOULDER_RIGHT.value: InputAction.EQUIPMENT.value,
            
            # システム
            GamepadButton.START.value: InputAction.MENU.value,
            GamepadButton.SELECT.value: InputAction.HELP.value,
        }
        
        # バインディングを設定
        self.keyboard_bindings = keyboard_bindings
        self.gamepad_bindings = gamepad_bindings
        
        # キーボードイベントのバインド
        for key, action in keyboard_bindings.items():
            self.accept(key, self._on_keyboard_input, [action, True])
            self.accept(f"{key}-up", self._on_keyboard_input, [action, False])
        
        logger.info("デフォルトバインディングを設定しました")
    
    def _on_keyboard_input(self, action: str, pressed: bool):
        """キーボード入力イベント"""
        if not self.keyboard_enabled:
            return
        
        self._handle_action(action, pressed, InputType.KEYBOARD)
    
    def _on_gamepad_input(self, device_name: str, button: str, pressed: bool):
        """ゲームパッド入力イベント"""
        if not self.controller_enabled:
            return
        
        # ボタンをアクションにマッピング
        if button in self.gamepad_bindings:
            action = self.gamepad_bindings[button]
            self._handle_action(action, pressed, InputType.GAMEPAD)
    
    def _handle_action(self, action: str, pressed: bool, input_type: InputType):
        """アクション処理"""
        if action in self.action_callbacks:
            callback = self.action_callbacks[action]
            try:
                callback(action, pressed, input_type)
            except Exception as e:
                logger.error(f"アクションコールバックエラー {action}: {e}")
    
    def _start_input_polling(self):
        """入力ポーリング開始"""
        # ゲームパッドの定期的な状態チェック
        self.taskMgr.add(self._poll_gamepad_input, "poll_gamepad")
    
    def _poll_gamepad_input(self, task):
        """ゲームパッド入力ポーリング"""
        if not self.controller_enabled or not self.active_gamepad:
            return task.cont
        
        # アナログスティックの処理
        self._process_analog_input()
        
        # ボタン状態の処理
        self._process_button_input()
        
        return task.cont
    
    def _process_analog_input(self):
        """アナログスティック処理"""
        if not self.active_gamepad:
            return
        
        # 左スティック
        try:
            left_x = self.active_gamepad.findAxis(InputDevice.Axis.left_x).value
            left_y = self.active_gamepad.findAxis(InputDevice.Axis.left_y).value
            
            # デッドゾーン適用
            if abs(left_x) < self.analog_deadzone:
                left_x = 0.0
            if abs(left_y) < self.analog_deadzone:
                left_y = 0.0
            
            # 感度適用
            left_x *= self.analog_sensitivity
            left_y *= self.analog_sensitivity
            
            # 値が変化した場合のみ処理
            if abs(left_x - self.left_stick_x) > 0.1 or abs(left_y - self.left_stick_y) > 0.1:
                self.left_stick_x = left_x
                self.left_stick_y = left_y
                self._handle_analog_input("left_stick", left_x, left_y)
        except:
            pass  # アナログスティックが利用できない場合
        
        # 右スティック
        try:
            right_x = self.active_gamepad.findAxis(InputDevice.Axis.right_x).value
            right_y = self.active_gamepad.findAxis(InputDevice.Axis.right_y).value
            
            if abs(right_x) < self.analog_deadzone:
                right_x = 0.0
            if abs(right_y) < self.analog_deadzone:
                right_y = 0.0
            
            right_x *= self.analog_sensitivity
            right_y *= self.analog_sensitivity
            
            if abs(right_x - self.right_stick_x) > 0.1 or abs(right_y - self.right_stick_y) > 0.1:
                self.right_stick_x = right_x
                self.right_stick_y = right_y
                self._handle_analog_input("right_stick", right_x, right_y)
        except:
            pass
    
    def _process_button_input(self):
        """ボタン状態処理"""
        if not self.active_gamepad:
            return
        
        # 前フレームの状態を保存
        self.previous_button_states = self.button_states.copy()
        
        # 現在のボタン状態を取得
        for button_name in self.gamepad_bindings.keys():
            try:
                # Panda3Dのボタン状態取得
                button = self.active_gamepad.findButton(button_name)
                if button:
                    pressed = button.pressed
                    
                    # 状態変化をチェック
                    prev_pressed = self.previous_button_states.get(button_name, False)
                    if pressed != prev_pressed:
                        self._on_gamepad_input(self.active_gamepad.name, button_name, pressed)
                    
                    self.button_states[button_name] = pressed
            except:
                pass  # ボタンが見つからない場合
    
    def _handle_analog_input(self, stick: str, x: float, y: float):
        """アナログ入力処理"""
        # アナログスティックによる移動処理
        if stick == "left_stick":
            # 移動入力に変換
            if abs(y) > 0.5:  # 前後移動
                if y > 0:
                    self._handle_action(InputAction.MOVE_BACKWARD.value, True, InputType.GAMEPAD)
                else:
                    self._handle_action(InputAction.MOVE_FORWARD.value, True, InputType.GAMEPAD)
            
            if abs(x) > 0.5:  # 左右回転
                if x < 0:
                    self._handle_action(InputAction.TURN_LEFT.value, True, InputType.GAMEPAD)
                else:
                    self._handle_action(InputAction.TURN_RIGHT.value, True, InputType.GAMEPAD)
    
    def bind_action(self, action: str, callback: Callable):
        """アクションにコールバックをバインド"""
        self.action_callbacks[action] = callback
        logger.debug(f"アクション '{action}' をバインドしました")
    
    def unbind_action(self, action: str):
        """アクションのバインドを解除"""
        if action in self.action_callbacks:
            del self.action_callbacks[action]
            logger.debug(f"アクション '{action}' のバインドを解除しました")
    
    def setup_controllers(self):
        """コントローラーの設定"""
        if not self.controller_enabled:
            logger.info("コントローラーが無効化されています")
            return
        
        # 既存のデバイスをクリア
        self.devices.clear()
        self.active_gamepad = None
        
        # 利用可能なコントローラーの検索
        try:
            devices = base.devices.getDevices()
            gamepad_count = 0
            
            for device in devices:
                if device.device_class == InputDevice.DeviceClass.gamepad:
                    self.devices[device.name] = device
                    gamepad_count += 1
                    
                    # 最初のゲームパッドをアクティブに設定
                    if not self.active_gamepad:
                        self.active_gamepad = device
                        logger.info(f"アクティブコントローラー: {device.name}")
                    
                    logger.info(f"コントローラーを検出: {device.name}")
            
            if gamepad_count == 0:
                logger.info("コントローラーが見つかりませんでした")
            else:
                logger.info(f"{gamepad_count}個のコントローラーを検出しました")
                
        except Exception as e:
            logger.error(f"コントローラー検出エラー: {e}")
    
    def get_active_gamepad(self) -> Optional[InputDevice]:
        """アクティブなゲームパッドを取得"""
        return self.active_gamepad
    
    def set_active_gamepad(self, device_name: str) -> bool:
        """アクティブなゲームパッドを設定"""
        if device_name in self.devices:
            self.active_gamepad = self.devices[device_name]
            logger.info(f"アクティブコントローラーを変更: {device_name}")
            return True
        else:
            logger.warning(f"コントローラーが見つかりません: {device_name}")
            return False
    
    def get_available_controllers(self) -> List[str]:
        """利用可能なコントローラーのリストを取得"""
        return list(self.devices.keys())
    
    def set_analog_deadzone(self, deadzone: float):
        """アナログデッドゾーンを設定"""
        self.analog_deadzone = max(0.0, min(1.0, deadzone))
        logger.debug(f"アナログデッドゾーン: {self.analog_deadzone}")
    
    def set_analog_sensitivity(self, sensitivity: float):
        """アナログ感度を設定"""
        self.analog_sensitivity = max(0.1, min(3.0, sensitivity))
        logger.debug(f"アナログ感度: {self.analog_sensitivity}")
    
    def customize_binding(self, input_type: InputType, key_or_button: str, action: str):
        """カスタムバインディングを設定"""
        if input_type == InputType.KEYBOARD:
            # 既存のバインドを削除
            for key, bound_action in list(self.keyboard_bindings.items()):
                if bound_action == action:
                    del self.keyboard_bindings[key]
                    self.ignore(key)
                    self.ignore(f"{key}-up")
            
            # 新しいバインドを設定
            self.keyboard_bindings[key_or_button] = action
            self.accept(key_or_button, self._on_keyboard_input, [action, True])
            self.accept(f"{key_or_button}-up", self._on_keyboard_input, [action, False])
            
        elif input_type == InputType.GAMEPAD:
            # 既存のバインドを削除
            for button, bound_action in list(self.gamepad_bindings.items()):
                if bound_action == action:
                    del self.gamepad_bindings[button]
            
            # 新しいバインドを設定
            self.gamepad_bindings[key_or_button] = action
        
        logger.info(f"カスタムバインディング設定: {input_type.value} {key_or_button} -> {action}")
    
    def get_binding_info(self) -> Dict[str, Dict]:
        """バインディング情報を取得"""
        return {
            "keyboard": self.keyboard_bindings.copy(),
            "gamepad": self.gamepad_bindings.copy(),
            "actions": list(self.action_callbacks.keys())
        }
    
    def is_action_pressed(self, action: str) -> bool:
        """アクションが現在押されているかチェック"""
        # キーボードチェック
        for key, bound_action in self.keyboard_bindings.items():
            if bound_action == action:
                # Panda3Dのキー状態をチェック
                if hasattr(base, 'mouseWatcherNode') and base.mouseWatcherNode:
                    if base.mouseWatcherNode.is_button_down(key):
                        return True
        
        # ゲームパッドチェック
        for button, bound_action in self.gamepad_bindings.items():
            if bound_action == action:
                if button in self.button_states:
                    return self.button_states[button]
        
        return False
    
    def enable_keyboard(self, enabled: bool = True):
        """キーボード入力の有効/無効"""
        self.keyboard_enabled = enabled
        logger.info(f"キーボード入力: {'有効' if enabled else '無効'}")
    
    def enable_controller(self, enabled: bool = True):
        """コントローラー入力の有効/無効"""
        self.controller_enabled = enabled
        if enabled:
            self.setup_controllers()
        else:
            self.active_gamepad = None
        logger.info(f"コントローラー入力: {'有効' if enabled else '無効'}")
    
    def get_input_status(self) -> Dict[str, any]:
        """入力システムの状態を取得"""
        return {
            "keyboard_enabled": self.keyboard_enabled,
            "controller_enabled": self.controller_enabled,
            "active_gamepad": self.active_gamepad.name if self.active_gamepad else None,
            "available_controllers": self.get_available_controllers(),
            "analog_deadzone": self.analog_deadzone,
            "analog_sensitivity": self.analog_sensitivity,
            "left_stick": (self.left_stick_x, self.left_stick_y),
            "right_stick": (self.right_stick_x, self.right_stick_y)
        }
    
    def save_bindings(self) -> Dict[str, Dict]:
        """バインディング設定を保存用に取得"""
        return {
            "keyboard_bindings": self.keyboard_bindings.copy(),
            "gamepad_bindings": self.gamepad_bindings.copy(),
            "analog_deadzone": self.analog_deadzone,
            "analog_sensitivity": self.analog_sensitivity,
            "controller_enabled": self.controller_enabled,
            "keyboard_enabled": self.keyboard_enabled
        }
    
    def load_bindings(self, bindings_data: Dict[str, any]):
        """バインディング設定を読み込み"""
        try:
            if "keyboard_bindings" in bindings_data:
                self.keyboard_bindings = bindings_data["keyboard_bindings"]
                # キーボードイベントを再バインド
                self.ignoreAll()
                for key, action in self.keyboard_bindings.items():
                    self.accept(key, self._on_keyboard_input, [action, True])
                    self.accept(f"{key}-up", self._on_keyboard_input, [action, False])
            
            if "gamepad_bindings" in bindings_data:
                self.gamepad_bindings = bindings_data["gamepad_bindings"]
            
            if "analog_deadzone" in bindings_data:
                self.set_analog_deadzone(bindings_data["analog_deadzone"])
            
            if "analog_sensitivity" in bindings_data:
                self.set_analog_sensitivity(bindings_data["analog_sensitivity"])
            
            if "controller_enabled" in bindings_data:
                self.enable_controller(bindings_data["controller_enabled"])
            
            if "keyboard_enabled" in bindings_data:
                self.enable_keyboard(bindings_data["keyboard_enabled"])
            
            logger.info("バインディング設定を読み込みました")
            
        except Exception as e:
            logger.error(f"バインディング読み込みエラー: {e}")
    
    def cleanup(self):
        """リソースのクリーンアップ"""
        # タスクを停止
        if hasattr(self, 'taskMgr'):
            self.taskMgr.remove("poll_gamepad")
        
        # イベントを無視
        self.ignoreAll()
        
        # データをクリア
        self.action_callbacks.clear()
        self.keyboard_bindings.clear()
        self.gamepad_bindings.clear()
        self.devices.clear()
        self.button_states.clear()
        self.previous_button_states.clear()
        
        self.active_gamepad = None
        
        logger.info("拡張入力システムをクリーンアップしました")