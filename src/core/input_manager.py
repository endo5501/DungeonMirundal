"""入力管理システム"""

import pygame
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


class InputManager:
    """キーボード・コントローラー入力の管理"""
    
    def __init__(self):
        # Pygame用ジョイスティック初期化
        pygame.joystick.init()
        
        # バインディング管理
        self.action_callbacks: Dict[str, Callable] = {}
        self.keyboard_bindings: Dict[str, str] = {}  # キー -> アクション
        self.gamepad_bindings: Dict[str, str] = {}   # ボタン -> アクション
        
        # デバイス管理
        self.joysticks: List[pygame.joystick.Joystick] = []
        self.active_gamepad: Optional[pygame.joystick.Joystick] = None
        
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
        self.setup_controllers()
        
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
        
        logger.info("デフォルトバインディングを設定しました")
    
    def setup_controllers(self):
        """コントローラーのセットアップ"""
        try:
            # 利用可能なジョイスティックを検出
            joystick_count = pygame.joystick.get_count()
            
            for i in range(joystick_count):
                joystick = pygame.joystick.Joystick(i)
                joystick.init()
                self.joysticks.append(joystick)
                
                if self.active_gamepad is None:
                    self.active_gamepad = joystick
                
                logger.info(f"ジョイスティック {i} を検出: {joystick.get_name()}")
            
            if not self.joysticks:
                logger.info("ジョイスティックが検出されませんでした")
                
        except Exception as e:
            logger.error(f"コントローラーセットアップエラー: {e}")
    
    def handle_event(self, event: pygame.event.Event):
        """Pygameイベントを処理"""
        if event.type == pygame.KEYDOWN:
            self._handle_keyboard_event(event.key, True)
        elif event.type == pygame.KEYUP:
            self._handle_keyboard_event(event.key, False)
        elif event.type == pygame.JOYBUTTONDOWN:
            self._handle_joystick_button(event.button, True)
        elif event.type == pygame.JOYBUTTONUP:
            self._handle_joystick_button(event.button, False)
        elif event.type == pygame.JOYHATMOTION:
            self._handle_joystick_hat(event.value)
    
    def _handle_keyboard_event(self, key: int, pressed: bool):
        """キーボードイベントの処理"""
        if not self.keyboard_enabled:
            return
        
        # Pygameキーコードを文字列に変換
        key_name = pygame.key.name(key)
        
        # バインディングをチェック
        if key_name in self.keyboard_bindings:
            action = self.keyboard_bindings[key_name]
            self._handle_action(action, pressed, InputType.KEYBOARD)
    
    def _handle_joystick_button(self, button: int, pressed: bool):
        """ジョイスティックボタンの処理"""
        if not self.controller_enabled or not self.active_gamepad:
            return
        
        # ボタン番号をゲームパッドボタンにマッピング
        button_mapping = {
            0: GamepadButton.FACE_A.value,
            1: GamepadButton.FACE_B.value,
            2: GamepadButton.FACE_X.value,
            3: GamepadButton.FACE_Y.value,
            4: GamepadButton.SHOULDER_LEFT.value,
            5: GamepadButton.SHOULDER_RIGHT.value,
            6: GamepadButton.SELECT.value,
            7: GamepadButton.START.value,
        }
        
        if button in button_mapping:
            button_name = button_mapping[button]
            if button_name in self.gamepad_bindings:
                action = self.gamepad_bindings[button_name]
                self._handle_action(action, pressed, InputType.GAMEPAD)
    
    def _handle_joystick_hat(self, hat_value: Tuple[int, int]):
        """ジョイスティックハット（十字キー）の処理"""
        if not self.controller_enabled:
            return
        
        x, y = hat_value
        
        # 前の状態をリセット
        hat_actions = [
            InputAction.MOVE_FORWARD.value,
            InputAction.MOVE_BACKWARD.value,
            InputAction.TURN_LEFT.value,
            InputAction.TURN_RIGHT.value
        ]
        
        for action in hat_actions:
            self._handle_action(action, False, InputType.GAMEPAD)
        
        # 新しい状態を設定
        if y == 1:  # 上
            self._handle_action(InputAction.MOVE_FORWARD.value, True, InputType.GAMEPAD)
        elif y == -1:  # 下
            self._handle_action(InputAction.MOVE_BACKWARD.value, True, InputType.GAMEPAD)
        
        if x == -1:  # 左
            self._handle_action(InputAction.TURN_LEFT.value, True, InputType.GAMEPAD)
        elif x == 1:  # 右
            self._handle_action(InputAction.TURN_RIGHT.value, True, InputType.GAMEPAD)
    
    
    def _handle_action(self, action: str, pressed: bool, input_type: InputType):
        """アクション処理"""
        if action in self.action_callbacks:
            callback = self.action_callbacks[action]
            try:
                callback(action, pressed, input_type)
            except Exception as e:
                logger.error(f"アクションコールバックエラー {action}: {e}")
    
    def update(self):
        """フレーム毎の更新処理"""
        if not self.controller_enabled or not self.active_gamepad:
            return
        
        # アナログスティックの処理
        self._process_analog_input()
    
    def _process_analog_input(self):
        """アナログスティック入力の処理"""
        if not self.active_gamepad:
            return
        
        try:
            # 左スティック
            if self.active_gamepad.get_numaxes() >= 2:
                self.left_stick_x = self.active_gamepad.get_axis(0)
                self.left_stick_y = self.active_gamepad.get_axis(1)
                
                # デッドゾーン適用
                if abs(self.left_stick_x) < self.analog_deadzone:
                    self.left_stick_x = 0.0
                if abs(self.left_stick_y) < self.analog_deadzone:
                    self.left_stick_y = 0.0
            
            # 右スティック
            if self.active_gamepad.get_numaxes() >= 4:
                self.right_stick_x = self.active_gamepad.get_axis(2)
                self.right_stick_y = self.active_gamepad.get_axis(3)
                
                # デッドゾーン適用
                if abs(self.right_stick_x) < self.analog_deadzone:
                    self.right_stick_x = 0.0
                if abs(self.right_stick_y) < self.analog_deadzone:
                    self.right_stick_y = 0.0
        
        except Exception as e:
            logger.warning(f"アナログ入力処理エラー: {e}")
    
    
    def bind_action(self, action: str, callback: Callable):
        """アクションにコールバックをバインド"""
        self.action_callbacks[action] = callback
        logger.debug(f"アクション '{action}' をバインドしました")
    
    def bind_key_direct(self, key: str, callback: Callable):
        """キーに直接コールバックをバインド"""
        # 簡易実装：キーバインディングに追加
        self.keyboard_bindings[key] = f"direct_{key}"
        self.action_callbacks[f"direct_{key}"] = callback
    
    def cleanup(self):
        """クリーンアップ"""
        # ジョイスティックのクリーンアップ
        for joystick in self.joysticks:
            if joystick.get_init():
                joystick.quit()
        
        pygame.joystick.quit()
        logger.info("入力マネージャーをクリーンアップしました")
    
    def save_bindings(self) -> dict:
        """バインディング設定を保存用辞書として返す"""
        return {
            'keyboard_bindings': self.keyboard_bindings,
            'gamepad_bindings': self.gamepad_bindings,
            'analog_deadzone': self.analog_deadzone,
            'analog_sensitivity': self.analog_sensitivity
        }
    
    def load_bindings(self, bindings_data: dict):
        """バインディング設定を読み込み"""
        if 'keyboard_bindings' in bindings_data:
            self.keyboard_bindings.update(bindings_data['keyboard_bindings'])
        
        if 'gamepad_bindings' in bindings_data:
            self.gamepad_bindings.update(bindings_data['gamepad_bindings'])
        
        if 'analog_deadzone' in bindings_data:
            self.analog_deadzone = bindings_data['analog_deadzone']
        
        if 'analog_sensitivity' in bindings_data:
            self.analog_sensitivity = bindings_data['analog_sensitivity']
        
        logger.info("バインディング設定を読み込みました")
    
    def unbind_action(self, action: str):
        """アクションのバインドを解除"""
        if action in self.action_callbacks:
            del self.action_callbacks[action]
            logger.debug(f"アクション '{action}' のバインドを解除しました")
    
    def bind_key_direct(self, key: str, callback: Callable):
        """キーを直接コールバックにバインド（デバッグ用）"""
        def wrapper():
            callback(f"key_{key}", True, InputType.KEYBOARD)
        
        def wrapper_up():
            callback(f"key_{key}", False, InputType.KEYBOARD)
        
        try:
            # Panda3Dメソッドを削除（Pygame版では不要）
            # self.accept(key, wrapper)
            # self.accept(f"{key}-up", wrapper_up)
            logger.debug(f"キー '{key}' を直接バインドしました")
        except Exception as e:
            logger.error(f"キー '{key}' のバインドに失敗: {e}")
            raise
    
    
    def get_active_gamepad(self) -> Optional[pygame.joystick.Joystick]:
        """アクティブなゲームパッドを取得"""
        return self.active_gamepad
    
    def set_active_gamepad(self, gamepad_index: int) -> bool:
        """アクティブなゲームパッドを設定"""
        if 0 <= gamepad_index < len(self.joysticks):
            self.active_gamepad = self.joysticks[gamepad_index]
            logger.info(f"アクティブコントローラーを変更: {gamepad_index}")
            return True
        else:
            logger.warning(f"コントローラーインデックスが無効です: {gamepad_index}")
            return False
    
    def get_available_controllers(self) -> List[str]:
        """利用可能なコントローラーのリストを取得"""
        return [joystick.get_name() for joystick in self.joysticks]
    
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
            
            # 新しいバインドを設定
            self.keyboard_bindings[key_or_button] = action
            
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
                # キーボードイベントを再バインド（Panda3Dメソッドを削除）
                # self.ignoreAll()
                for key, action in self.keyboard_bindings.items():
                    # Panda3Dメソッドを削除（Pygame版では不要）
                    # self.accept(key, self._on_keyboard_input, [action, True])
                    # self.accept(f"{key}-up", self._on_keyboard_input, [action, False])
                    pass  # forループに実処理が必要
            
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
        
        # イベントを無視（Panda3Dメソッドを削除）
        pass
        
        # データをクリア
        self.action_callbacks.clear()
        self.keyboard_bindings.clear()
        self.gamepad_bindings.clear()
        if hasattr(self, 'devices'):
            self.devices.clear()
        if hasattr(self, 'button_states'):
            self.button_states.clear()
        if hasattr(self, 'previous_button_states'):
            self.previous_button_states.clear()
        
        self.active_gamepad = None
        
        logger.info("拡張入力システムをクリーンアップしました")