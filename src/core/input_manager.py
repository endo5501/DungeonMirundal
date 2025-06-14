"""入力管理システム"""

from direct.showbase.DirectObject import DirectObject
from panda3d.core import InputDevice
from typing import Dict, Callable, Optional
from src.utils.logger import logger


class InputManager(DirectObject):
    """キーボード・コントローラー入力の管理"""
    
    def __init__(self):
        super().__init__()
        self.key_bindings: Dict[str, Callable] = {}
        self.devices: Dict[str, InputDevice] = {}
        self.controller_enabled = True
        self.keyboard_enabled = True
        
        # 基本キーバインディング
        self._setup_default_bindings()
        
    def _setup_default_bindings(self):
        """デフォルトキーバインディングの設定"""
        # 移動キー
        self.accept("w", self._on_key_pressed, ["move_forward"])
        self.accept("w-up", self._on_key_released, ["move_forward"])
        self.accept("s", self._on_key_pressed, ["move_backward"])
        self.accept("s-up", self._on_key_released, ["move_backward"])
        self.accept("a", self._on_key_pressed, ["turn_left"])
        self.accept("a-up", self._on_key_released, ["turn_left"])
        self.accept("d", self._on_key_pressed, ["turn_right"])
        self.accept("d-up", self._on_key_released, ["turn_right"])
        
        # システムキー
        self.accept("escape", self._on_key_pressed, ["menu"])
        self.accept("enter", self._on_key_pressed, ["confirm"])
        self.accept("space", self._on_key_pressed, ["action"])
        
        # デバッグキー
        self.accept("f1", self._on_key_pressed, ["debug_toggle"])
        
        logger.info("デフォルトキーバインディングを設定しました")
    
    def _on_key_pressed(self, action: str):
        """キー押下イベント"""
        if not self.keyboard_enabled:
            return
            
        if action in self.key_bindings:
            callback = self.key_bindings[action]
            callback(action, True)
            
    def _on_key_released(self, action: str):
        """キー離しイベント"""
        if not self.keyboard_enabled:
            return
            
        if action in self.key_bindings:
            callback = self.key_bindings[action]
            callback(action, False)
    
    def bind_action(self, action: str, callback: Callable):
        """アクションにコールバックをバインド"""
        self.key_bindings[action] = callback
        logger.debug(f"アクション '{action}' をバインドしました")
    
    def unbind_action(self, action: str):
        """アクションのバインドを解除"""
        if action in self.key_bindings:
            del self.key_bindings[action]
            logger.debug(f"アクション '{action}' のバインドを解除しました")
    
    def setup_controllers(self):
        """コントローラーの設定"""
        if not self.controller_enabled:
            return
            
        # 利用可能なコントローラーの検索
        devices = base.devices.getDevices()
        for device in devices:
            if device.device_class == InputDevice.DeviceClass.gamepad:
                self.devices[device.name] = device
                logger.info(f"コントローラーを検出: {device.name}")
                
                # コントローラーボタンのバインド
                self.accept(f"{device.name}-face_a", self._on_controller_button, ["confirm"])
                self.accept(f"{device.name}-face_b", self._on_controller_button, ["cancel"])
                self.accept(f"{device.name}-face_x", self._on_controller_button, ["action"])
                self.accept(f"{device.name}-face_y", self._on_controller_button, ["menu"])
                
                # 方向パッドのバインド
                self.accept(f"{device.name}-dpad_up", self._on_controller_button, ["move_forward"])
                self.accept(f"{device.name}-dpad_down", self._on_controller_button, ["move_backward"])
                self.accept(f"{device.name}-dpad_left", self._on_controller_button, ["turn_left"])
                self.accept(f"{device.name}-dpad_right", self._on_controller_button, ["turn_right"])
    
    def _on_controller_button(self, action: str):
        """コントローラーボタンイベント"""
        if not self.controller_enabled:
            return
            
        if action in self.key_bindings:
            callback = self.key_bindings[action]
            callback(action, True)
    
    def enable_keyboard(self, enabled: bool = True):
        """キーボード入力の有効/無効"""
        self.keyboard_enabled = enabled
        logger.info(f"キーボード入力: {'有効' if enabled else '無効'}")
    
    def enable_controller(self, enabled: bool = True):
        """コントローラー入力の有効/無効"""
        self.controller_enabled = enabled
        if enabled:
            self.setup_controllers()
        logger.info(f"コントローラー入力: {'有効' if enabled else '無効'}")
    
    def cleanup(self):
        """リソースのクリーンアップ"""
        self.ignoreAll()
        self.key_bindings.clear()
        self.devices.clear()
        logger.info("入力システムをクリーンアップしました")