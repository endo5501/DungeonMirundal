"""Core game systems テスト (game_manager, input_manager)"""

import pytest
import os
from unittest.mock import Mock, patch, MagicMock
import pygame

# ヘッドレス環境でのPygame初期化
os.environ['SDL_VIDEODRIVER'] = 'dummy'

from src.core.game_manager import GameManager
from src.core.input_manager import InputManager, InputAction, InputType, GamepadButton
from src.character.party import Party
from src.character.character import Character
from src.character.stats import BaseStats


class TestGameManager:
    """GameManagerのテスト"""
    
    def setup_method(self):
        """各テストメソッドの前に実行"""
        # Pygameの初期化（必要最小限）
        pygame.init()
        pygame.display.set_mode((800, 600))
        
        # テスト用パーティ作成
        self.test_party = Party("テストパーティ")
        stats = BaseStats(strength=16, agility=14, intelligence=12, faith=10, vitality=14, luck=12)
        character = Character.create_character("テストキャラ", "human", "fighter", stats)
        self.test_party.add_character(character)
    
    def teardown_method(self):
        """各テストメソッドの後に実行"""
        pygame.quit()
    
    def test_game_manager_initialization(self):
        """GameManagerの初期化テスト"""
        # 関連クラスをモックしてセットアップ
        with patch('src.core.game_manager.OverworldManager') as mock_overworld, \
             patch('src.core.game_manager.DungeonManager') as mock_dungeon, \
             patch('src.core.game_manager.DungeonRendererPygame') as mock_renderer, \
             patch('src.core.game_manager.SaveManager') as mock_save:
            
            # モックの設定
            mock_overworld.return_value = MagicMock()
            mock_dungeon.return_value = MagicMock()
            mock_renderer.return_value = MagicMock()
            mock_save.return_value = MagicMock()
            
            # GameManagerを作成
            game_manager = GameManager()
            
            assert game_manager is not None
            assert game_manager.running is False
            assert game_manager.game_state == "startup"
            assert game_manager.current_location == "overworld"
            assert hasattr(game_manager, 'input_manager')
            assert hasattr(game_manager, 'screen')
    
    def test_set_current_party(self):
        """パーティ設定テスト"""
        with patch('src.core.game_manager.OverworldManager') as mock_overworld, \
             patch('src.core.game_manager.DungeonManager') as mock_dungeon, \
             patch('src.core.game_manager.DungeonRendererPygame') as mock_renderer:
            
            mock_overworld.return_value = MagicMock()
            mock_dungeon.return_value = MagicMock()
            mock_renderer_instance = MagicMock()
            mock_renderer.return_value = mock_renderer_instance
            
            game_manager = GameManager()
            
            # パーティを設定
            game_manager.set_current_party(self.test_party)
            
            assert game_manager.current_party == self.test_party
            assert game_manager.get_current_party() == self.test_party
            
            # ダンジョンレンダラーにもパーティが設定されることを確認
            mock_renderer_instance.set_party.assert_called_once_with(self.test_party)
    
    def test_game_state_changes(self):
        """ゲーム状態変更テスト"""
        with patch('src.core.game_manager.OverworldManager') as mock_overworld, \
             patch('src.core.game_manager.DungeonManager') as mock_dungeon, \
             patch('src.core.game_manager.DungeonRendererPygame') as mock_renderer:
            
            mock_overworld.return_value = MagicMock()
            mock_dungeon.return_value = MagicMock()
            mock_renderer.return_value = MagicMock()
            
            game_manager = GameManager()
            
            # 初期状態の確認
            assert game_manager.game_state == "startup"
            
            # 状態変更
            game_manager.set_game_state("overworld_exploration")
            assert game_manager.game_state == "overworld_exploration"
            
            game_manager.set_game_state("dungeon_exploration")
            assert game_manager.game_state == "dungeon_exploration"
    
    def test_location_transitions(self):
        """場所遷移テスト"""
        with patch('src.core.game_manager.OverworldManager') as mock_overworld, \
             patch('src.core.game_manager.DungeonManager') as mock_dungeon, \
             patch('src.core.game_manager.DungeonRendererPygame') as mock_renderer:
            
            mock_overworld_instance = MagicMock()
            mock_dungeon_instance = MagicMock()
            mock_renderer_instance = MagicMock()
            
            mock_overworld.return_value = mock_overworld_instance
            mock_dungeon.return_value = mock_dungeon_instance
            mock_renderer.return_value = mock_renderer_instance
            
            # マネージャーメソッドの戻り値を設定
            mock_overworld_instance.enter_overworld.return_value = True
            mock_overworld_instance.exit_overworld.return_value = None
            mock_dungeon_instance.enter_dungeon.return_value = True
            mock_dungeon_instance.exit_dungeon.return_value = None
            
            game_manager = GameManager()
            game_manager.set_current_party(self.test_party)
            
            # 地上部への遷移テスト
            result = game_manager.transition_to_overworld()
            assert result is True
            assert game_manager.current_location == "overworld"
            mock_overworld_instance.enter_overworld.assert_called()
    
    def test_pause_toggle(self):
        """ポーズ切り替えテスト"""
        with patch('src.core.game_manager.OverworldManager') as mock_overworld, \
             patch('src.core.game_manager.DungeonManager') as mock_dungeon, \
             patch('src.core.game_manager.DungeonRendererPygame') as mock_renderer:
            
            mock_overworld.return_value = MagicMock()
            mock_dungeon.return_value = MagicMock()
            mock_renderer.return_value = MagicMock()
            
            game_manager = GameManager()
            
            # 初期状態
            assert game_manager.paused is False
            
            # ポーズ切り替え
            game_manager.toggle_pause()
            assert game_manager.paused is True
            
            game_manager.toggle_pause()
            assert game_manager.paused is False
    
    def test_debug_toggle_action(self):
        """デバッグ切り替えアクション"""
        with patch('src.core.game_manager.OverworldManager') as mock_overworld, \
             patch('src.core.game_manager.DungeonManager') as mock_dungeon, \
             patch('src.core.game_manager.DungeonRendererPygame') as mock_renderer:
            
            mock_overworld.return_value = MagicMock()
            mock_dungeon.return_value = MagicMock()
            mock_renderer.return_value = MagicMock()
            
            game_manager = GameManager()
            
            # 初期デバッグ状態
            initial_debug = game_manager.debug_enabled
            
            # デバッグ切り替えアクション実行
            game_manager._on_debug_toggle("debug_toggle", True, InputType.KEYBOARD)
            
            # デバッグ状態が切り替わったことを確認
            assert game_manager.debug_enabled != initial_debug


class TestInputManager:
    """InputManagerのテスト"""
    
    def setup_method(self):
        """各テストメソッドの前に実行"""
        pygame.init()
    
    def teardown_method(self):
        """各テストメソッドの後に実行"""
        pygame.quit()
    
    def test_input_manager_initialization(self):
        """InputManagerの初期化テスト"""
        input_manager = InputManager()
        
        assert input_manager is not None
        assert hasattr(input_manager, 'action_callbacks')
        assert hasattr(input_manager, 'keyboard_bindings')
        assert hasattr(input_manager, 'gamepad_bindings')
        assert input_manager.controller_enabled is True
        assert input_manager.keyboard_enabled is True
        assert input_manager.analog_deadzone == 0.3
    
    def test_default_keyboard_bindings(self):
        """デフォルトキーバインディングテスト"""
        input_manager = InputManager()
        
        # 基本的なキーバインディングの確認
        assert "w" in input_manager.keyboard_bindings
        assert input_manager.keyboard_bindings["w"] == InputAction.MOVE_FORWARD.value
        
        assert "s" in input_manager.keyboard_bindings
        assert input_manager.keyboard_bindings["s"] == InputAction.MOVE_BACKWARD.value
        
        assert "escape" in input_manager.keyboard_bindings
        assert input_manager.keyboard_bindings["escape"] == InputAction.MENU.value
        
        assert "space" in input_manager.keyboard_bindings
        assert input_manager.keyboard_bindings["space"] == InputAction.ACTION.value
    
    def test_default_gamepad_bindings(self):
        """デフォルトゲームパッドバインディングテスト"""
        input_manager = InputManager()
        
        # 基本的なゲームパッドバインディングの確認
        assert GamepadButton.DPAD_UP.value in input_manager.gamepad_bindings
        assert input_manager.gamepad_bindings[GamepadButton.DPAD_UP.value] == InputAction.MOVE_FORWARD.value
        
        assert GamepadButton.FACE_A.value in input_manager.gamepad_bindings
        assert input_manager.gamepad_bindings[GamepadButton.FACE_A.value] == InputAction.CONFIRM.value
        
        assert GamepadButton.FACE_B.value in input_manager.gamepad_bindings
        assert input_manager.gamepad_bindings[GamepadButton.FACE_B.value] == InputAction.CANCEL.value
        
        assert GamepadButton.START.value in input_manager.gamepad_bindings
        assert input_manager.gamepad_bindings[GamepadButton.START.value] == InputAction.MENU.value
    
    def test_action_binding(self):
        """アクションバインディングテスト"""
        input_manager = InputManager()
        
        # テスト用コールバック
        test_callback = Mock()
        
        # アクションをバインド
        input_manager.bind_action("test_action", test_callback)
        
        assert "test_action" in input_manager.action_callbacks
        assert input_manager.action_callbacks["test_action"] == test_callback
    
    def test_key_direct_binding(self):
        """キー直接バインディングテスト"""
        input_manager = InputManager()
        
        # テスト用コールバック
        test_callback = Mock()
        
        # bind_key_directメソッドが例外を投げないことを確認
        try:
            input_manager.bind_key_direct("f2", test_callback)
        except Exception as e:
            pytest.fail(f"bind_key_direct raised an exception: {e}")
        
        # メソッドが正常に呼び出せることを確認（現在の実装ではログ出力のみ）
        assert hasattr(input_manager, 'bind_key_direct')
    
    def test_handle_keyboard_event(self):
        """キーボードイベント処理テスト"""
        input_manager = InputManager()
        
        # テスト用コールバック
        test_callback = Mock()
        input_manager.bind_action(InputAction.MENU.value, test_callback)
        
        # ESCキーのキーコードを取得
        escape_key = pygame.K_ESCAPE
        
        # キーボードイベントをシミュレート
        keydown_event = pygame.event.Event(pygame.KEYDOWN, {'key': escape_key})
        input_manager.handle_event(keydown_event)
        
        # コールバックが呼ばれることを確認
        test_callback.assert_called_once()
    
    def test_analog_deadzone(self):
        """アナログスティックのデッドゾーンテスト"""
        input_manager = InputManager()
        
        # デッドゾーン設定
        assert input_manager.analog_deadzone == 0.3
        
        # デッドゾーン変更
        input_manager.analog_deadzone = 0.5
        assert input_manager.analog_deadzone == 0.5
    
    def test_controller_setup(self):
        """コントローラーセットアップテスト"""
        input_manager = InputManager()
        
        # コントローラーリストが初期化されていることを確認
        assert hasattr(input_manager, 'joysticks')
        assert isinstance(input_manager.joysticks, list)
        
        # setup_controllersメソッドが例外を投げないことを確認
        try:
            input_manager.setup_controllers()
        except Exception as e:
            pytest.fail(f"setup_controllers raised an exception: {e}")
    
    def test_input_type_enum(self):
        """InputType列挙型テスト"""
        assert InputType.KEYBOARD.value == "keyboard"
        assert InputType.GAMEPAD.value == "gamepad"
        assert InputType.BOTH.value == "both"
    
    def test_input_action_enum(self):
        """InputAction列挙型テスト"""
        # 移動系
        assert InputAction.MOVE_FORWARD.value == "move_forward"
        assert InputAction.MOVE_BACKWARD.value == "move_backward"
        assert InputAction.TURN_LEFT.value == "turn_left"
        assert InputAction.TURN_RIGHT.value == "turn_right"
        
        # UI系
        assert InputAction.MENU.value == "menu"
        assert InputAction.CONFIRM.value == "confirm"
        assert InputAction.CANCEL.value == "cancel"
        assert InputAction.ACTION.value == "action"
        
        # ゲーム系
        assert InputAction.INVENTORY.value == "inventory"
        assert InputAction.MAGIC.value == "magic"
        assert InputAction.EQUIPMENT.value == "equipment"
        assert InputAction.STATUS.value == "status"
        assert InputAction.CAMP.value == "camp"
    
    def test_gamepad_button_enum(self):
        """GamepadButton列挙型テスト"""
        # フェイスボタン
        assert GamepadButton.FACE_A.value == "face_a"
        assert GamepadButton.FACE_B.value == "face_b"
        assert GamepadButton.FACE_X.value == "face_x"
        assert GamepadButton.FACE_Y.value == "face_y"
        
        # ショルダーボタン
        assert GamepadButton.SHOULDER_LEFT.value == "shoulder_l"
        assert GamepadButton.SHOULDER_RIGHT.value == "shoulder_r"
        
        # 十字キー
        assert GamepadButton.DPAD_UP.value == "dpad_up"
        assert GamepadButton.DPAD_DOWN.value == "dpad_down"
        assert GamepadButton.DPAD_LEFT.value == "dpad_left"
        assert GamepadButton.DPAD_RIGHT.value == "dpad_right"
    
    def test_update_method(self):
        """updateメソッドテスト"""
        input_manager = InputManager()
        
        # updateメソッドが例外を投げないことを確認
        try:
            input_manager.update()
        except Exception as e:
            pytest.fail(f"update method raised an exception: {e}")
    
    def test_cleanup_method(self):
        """cleanupメソッドテスト"""
        input_manager = InputManager()
        
        # cleanupメソッドが例外を投げないことを確認
        try:
            input_manager.cleanup()
        except Exception as e:
            pytest.fail(f"cleanup method raised an exception: {e}")


class TestGameManagerInputManagerIntegration:
    """GameManagerとInputManagerの連携テスト"""
    
    def setup_method(self):
        """各テストメソッドの前に実行"""
        pygame.init()
        pygame.display.set_mode((800, 600))
    
    def teardown_method(self):
        """各テストメソッドの後に実行"""
        pygame.quit()
    
    def test_input_manager_action_bindings(self):
        """InputManagerのアクションバインディング連携テスト"""
        with patch('src.core.game_manager.OverworldManager') as mock_overworld, \
             patch('src.core.game_manager.DungeonManager') as mock_dungeon, \
             patch('src.core.game_manager.DungeonRendererPygame') as mock_renderer:
            
            mock_overworld.return_value = MagicMock()
            mock_dungeon.return_value = MagicMock()
            mock_renderer.return_value = MagicMock()
            
            game_manager = GameManager()
            
            # InputManagerがGameManagerのメソッドにバインドされていることを確認
            assert InputAction.MENU.value in game_manager.input_manager.action_callbacks
            assert InputAction.CONFIRM.value in game_manager.input_manager.action_callbacks
            assert InputAction.CANCEL.value in game_manager.input_manager.action_callbacks
            assert InputAction.ACTION.value in game_manager.input_manager.action_callbacks
            assert InputAction.DEBUG_TOGGLE.value in game_manager.input_manager.action_callbacks
    
    def test_game_manager_input_event_flow(self):
        """GameManagerの入力イベントフローテスト"""
        with patch('src.core.game_manager.OverworldManager') as mock_overworld, \
             patch('src.core.game_manager.DungeonManager') as mock_dungeon, \
             patch('src.core.game_manager.DungeonRendererPygame') as mock_renderer:
            
            mock_overworld.return_value = MagicMock()
            mock_dungeon.return_value = MagicMock()
            mock_renderer.return_value = MagicMock()
            
            game_manager = GameManager()
            
            # InputManagerがGameManagerで使用可能であることを確認
            assert hasattr(game_manager, 'input_manager')
            assert game_manager.input_manager is not None
            assert isinstance(game_manager.input_manager, InputManager)
    
    def test_action_handler_methods_exist(self):
        """アクションハンドラーメソッドの存在確認"""
        with patch('src.core.game_manager.OverworldManager') as mock_overworld, \
             patch('src.core.game_manager.DungeonManager') as mock_dungeon, \
             patch('src.core.game_manager.DungeonRendererPygame') as mock_renderer:
            
            mock_overworld.return_value = MagicMock()
            mock_dungeon.return_value = MagicMock()
            mock_renderer.return_value = MagicMock()
            
            game_manager = GameManager()
            
            # アクションハンドラーメソッドが存在することを確認
            assert hasattr(game_manager, '_on_menu_action')
            assert hasattr(game_manager, '_on_confirm_action')
            assert hasattr(game_manager, '_on_cancel_action')
            assert hasattr(game_manager, '_on_action_action')
            assert hasattr(game_manager, '_on_debug_toggle')
            assert hasattr(game_manager, '_on_pause_action')
            assert hasattr(game_manager, '_on_inventory_action')
            assert hasattr(game_manager, '_on_magic_action')
            assert hasattr(game_manager, '_on_equipment_action')
            assert hasattr(game_manager, '_on_status_action')
            assert hasattr(game_manager, '_on_camp_action')
            assert hasattr(game_manager, '_on_help_action')
            assert hasattr(game_manager, '_on_movement_action')