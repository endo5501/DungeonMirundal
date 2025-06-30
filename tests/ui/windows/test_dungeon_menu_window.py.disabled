"""DungeonMenuWindowのテスト"""

import pytest
from unittest.mock import Mock, patch
import pygame

from src.ui.windows.dungeon_menu_window import DungeonMenuWindow, DungeonMenuType
from src.ui.window_system.window_manager import WindowManager
from src.character.party import Party
from src.character.character import Character


class TestDungeonMenuWindow:
    """DungeonMenuWindowのテストクラス"""

    @pytest.fixture
    def mock_window_manager(self):
        """WindowManagerのモックを作成"""
        with patch('src.ui.window_system.window_manager.WindowManager') as mock_wm_class:
            mock_wm = Mock()
            mock_wm_class.get_instance.return_value = mock_wm
            mock_wm.ui_manager = Mock()
            mock_wm.screen = Mock()
            mock_wm.screen.get_rect.return_value = pygame.Rect(0, 0, 1024, 768)
            mock_wm.screen.get_width.return_value = 1024
            mock_wm.screen.get_height.return_value = 768
            yield mock_wm

    @pytest.fixture
    def mock_party(self):
        """パーティのモックを作成"""
        party = Mock()
        party.name = "テストパーティ"
        
        # キャラクターのモック
        char1 = Mock()
        char1.name = "戦士"
        char1.current_hp = 80
        char1.max_hp = 100
        char1.current_mp = 20
        char1.max_mp = 30
        
        char2 = Mock()
        char2.name = "魔法使い"
        char2.current_hp = 60
        char2.max_hp = 70
        char2.current_mp = 45
        char2.max_mp = 50
        
        party.get_all_characters.return_value = [char1, char2]
        return party

    @pytest.fixture
    def mock_dungeon_state(self):
        """ダンジョン状態のモックを作成"""
        dungeon_state = Mock()
        dungeon_state.player_position = Mock()
        dungeon_state.player_position.x = 5
        dungeon_state.player_position.y = 3
        dungeon_state.current_floor = 2
        dungeon_state.dungeon_name = "テストダンジョン"
        return dungeon_state

    def test_dungeon_menu_window_creation(self, mock_window_manager):
        """DungeonMenuWindowが正しく作成されることを確認"""
        window = DungeonMenuWindow("test_dungeon_menu")
        
        assert window.window_id == "test_dungeon_menu"
        assert window.current_party is None
        assert window.current_menu_type == DungeonMenuType.MAIN
        assert window.is_menu_open is False
        assert window.selected_menu_index == 0

    def test_set_party(self, mock_window_manager, mock_party):
        """パーティの設定が正しく動作することを確認"""
        window = DungeonMenuWindow("test_dungeon_menu")
        window.set_party(mock_party)
        
        assert window.current_party == mock_party

    def test_set_dungeon_state(self, mock_window_manager, mock_dungeon_state):
        """ダンジョン状態の設定が正しく動作することを確認"""
        window = DungeonMenuWindow("test_dungeon_menu")
        window.set_dungeon_state(mock_dungeon_state)
        
        assert window.dungeon_state == mock_dungeon_state

    def test_show_main_menu(self, mock_window_manager):
        """メインメニュー表示が正しく動作することを確認"""
        window = DungeonMenuWindow("test_dungeon_menu")
        
        # createメソッドをモック
        window.create_main_menu = Mock()
        
        window.show_main_menu()
        
        assert window.is_menu_open is True
        assert window.current_menu_type == DungeonMenuType.MAIN
        assert window.selected_menu_index == 0

    def test_close_menu(self, mock_window_manager):
        """メニュー閉じる動作が正しく機能することを確認"""
        window = DungeonMenuWindow("test_dungeon_menu")
        window.is_menu_open = True
        window.current_menu_type = DungeonMenuType.INVENTORY
        
        window.close_menu()
        
        assert window.is_menu_open is False
        assert window.current_menu_type is None

    def test_toggle_main_menu(self, mock_window_manager):
        """メインメニューの表示切替が正しく動作することを確認"""
        window = DungeonMenuWindow("test_dungeon_menu")
        
        # メニューをモック
        window.show_main_menu = Mock()
        window.close_menu = Mock()
        
        # 閉じている状態からトグル → 開く
        window.is_menu_open = False
        window.toggle_main_menu()
        window.show_main_menu.assert_called_once()
        
        # 開いている状態からトグル → 閉じる
        window.is_menu_open = True
        window.toggle_main_menu()
        window.close_menu.assert_called_once()

    def test_set_callback(self, mock_window_manager):
        """コールバック設定が正しく動作することを確認"""
        window = DungeonMenuWindow("test_dungeon_menu")
        
        test_callback = Mock()
        window.set_callback("inventory", test_callback)
        
        assert "inventory" in window.callbacks
        assert window.callbacks["inventory"] == test_callback

    def test_execute_menu_action_callback(self, mock_window_manager):
        """メニューアクション実行（コールバック）が正しく動作することを確認"""
        window = DungeonMenuWindow("test_dungeon_menu")
        
        # コールバックを設定
        inventory_callback = Mock()
        window.set_callback("inventory", inventory_callback)
        
        # インベントリメニューアイテムを選択
        window.selected_menu_index = 0  # "inventory"が最初の項目と仮定
        
        window.close_menu = Mock()
        window.execute_menu_action()
        
        inventory_callback.assert_called_once()
        window.close_menu.assert_called_once()

    def test_execute_menu_action_close(self, mock_window_manager):
        """メニューアクション実行（閉じる）が正しく動作することを確認"""
        window = DungeonMenuWindow("test_dungeon_menu")
        
        # 閉じるアクションのインデックスを設定
        close_index = None
        for i, item in enumerate(window.menu_items):
            if item["action"] == "close":
                close_index = i
                break
        
        if close_index is not None:
            window.selected_menu_index = close_index
            window.close_menu = Mock()
            
            window.execute_menu_action()
            
            window.close_menu.assert_called_once()

    def test_handle_keyboard_input(self, mock_window_manager):
        """キーボード入力処理が正しく動作することを確認"""
        window = DungeonMenuWindow("test_dungeon_menu")
        window.is_menu_open = True
        
        # 上キー
        event_up = Mock()
        event_up.type = pygame.KEYDOWN
        event_up.key = pygame.K_UP
        
        initial_index = window.selected_menu_index
        result = window.handle_input(event_up)
        
        assert result is True
        assert window.selected_menu_index == (initial_index - 1) % len(window.menu_items)
        
        # 下キー
        event_down = Mock()
        event_down.type = pygame.KEYDOWN
        event_down.key = pygame.K_DOWN
        
        current_index = window.selected_menu_index
        result = window.handle_input(event_down)
        
        assert result is True
        assert window.selected_menu_index == (current_index + 1) % len(window.menu_items)

    def test_handle_escape_key(self, mock_window_manager):
        """ESCキー処理が正しく動作することを確認"""
        window = DungeonMenuWindow("test_dungeon_menu")
        window.is_menu_open = True
        
        event_escape = Mock()
        event_escape.type = pygame.KEYDOWN
        event_escape.key = pygame.K_ESCAPE
        
        window.close_menu = Mock()
        result = window.handle_input(event_escape)
        
        assert result is True
        window.close_menu.assert_called_once()

    def test_handle_enter_key(self, mock_window_manager):
        """Enterキー処理が正しく動作することを確認"""
        window = DungeonMenuWindow("test_dungeon_menu")
        window.is_menu_open = True
        
        event_enter = Mock()
        event_enter.type = pygame.KEYDOWN
        event_enter.key = pygame.K_RETURN
        
        window.execute_menu_action = Mock()
        result = window.handle_input(event_enter)
        
        assert result is True
        window.execute_menu_action.assert_called_once()

    def test_menu_not_open_input_handling(self, mock_window_manager):
        """メニューが開いていない時の入力処理"""
        window = DungeonMenuWindow("test_dungeon_menu")
        window.is_menu_open = False
        
        event = Mock()
        event.type = pygame.KEYDOWN
        event.key = pygame.K_UP
        
        result = window.handle_input(event)
        
        assert result is False

    def test_render_menu_elements(self, mock_window_manager):
        """メニュー要素の描画が正しく動作することを確認"""
        window = DungeonMenuWindow("test_dungeon_menu")
        window.is_menu_open = True
        
        # createメソッドをモック
        window.create_main_menu = Mock()
        window.render_menu_background = Mock()
        window.render_menu_items = Mock()
        window.render_help_text = Mock()
        
        window.render()
        
        window.render_menu_background.assert_called_once()
        window.render_menu_items.assert_called_once()
        window.render_help_text.assert_called_once()

    def test_render_overlay_elements(self, mock_window_manager):
        """オーバーレイ要素の描画が正しく動作することを確認"""
        window = DungeonMenuWindow("test_dungeon_menu")
        
        # オーバーレイ要素をモック
        window.render_character_status_bar = Mock()
        window.render_small_map = Mock()
        window.render_location_info = Mock()
        
        window.render_overlay()
        
        window.render_character_status_bar.assert_called_once()
        window.render_small_map.assert_called_once()
        window.render_location_info.assert_called_once()

    def test_update_location_info(self, mock_window_manager, mock_dungeon_state):
        """位置情報更新が正しく動作することを確認"""
        window = DungeonMenuWindow("test_dungeon_menu")
        window.set_dungeon_state(mock_dungeon_state)
        
        location_info = window.get_location_info()
        
        assert "テストダンジョン" in location_info
        assert "2F" in location_info or "Floor 2" in location_info
        assert "(5, 3)" in location_info

    def test_menu_item_validation(self, mock_window_manager):
        """メニュー項目の妥当性確認"""
        window = DungeonMenuWindow("test_dungeon_menu")
        
        # 必要なメニュー項目が存在することを確認
        expected_actions = ["inventory", "magic", "equipment", "camp", "status", "close"]
        actual_actions = [item["action"] for item in window.menu_items]
        
        for expected_action in expected_actions:
            assert expected_action in actual_actions

    def test_window_lifecycle(self, mock_window_manager):
        """ウィンドウのライフサイクルが正しく動作することを確認"""
        window = DungeonMenuWindow("test_dungeon_menu")
        
        # 作成状態の確認
        assert window.window_id == "test_dungeon_menu"
        
        # 表示
        window.create = Mock()
        window.show()
        window.create.assert_called_once()
        
        # 非表示
        window.hide()
        
        # 破棄
        window.destroy()
        assert window.current_party is None
        assert window.dungeon_state is None
        assert window.callbacks == {}

    def test_character_status_integration(self, mock_window_manager, mock_party):
        """キャラクターステータス統合が正しく動作することを確認"""
        window = DungeonMenuWindow("test_dungeon_menu")
        window.set_party(mock_party)
        
        # ステータス情報取得をテスト
        status_info = window.get_party_status_summary()
        
        assert "戦士" in status_info
        assert "魔法使い" in status_info
        assert "80/100" in status_info  # HP情報
        assert "20/30" in status_info   # MP情報

    def test_small_map_integration(self, mock_window_manager, mock_dungeon_state):
        """小地図統合が正しく動作することを確認"""
        window = DungeonMenuWindow("test_dungeon_menu")
        window.set_dungeon_state(mock_dungeon_state)
        
        # 小地図が利用可能であることを確認
        assert window.is_small_map_available()
        
        # 位置情報が正しく取得できることを確認
        position = window.get_player_position()
        assert position == (5, 3)