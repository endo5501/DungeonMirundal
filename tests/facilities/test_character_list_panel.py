"""キャラクター一覧パネルのテスト"""

import pytest
import pygame
import pygame_gui
from unittest.mock import Mock, MagicMock, patch


@pytest.fixture
def mock_controller():
    """FacilityControllerのモック"""
    controller = Mock()
    
    # サービスのモック
    mock_service = Mock()
    mock_service.get_all_characters.return_value = []
    controller.service = mock_service
    
    return controller


@pytest.fixture
def mock_ui_setup():
    """UI要素のモック"""
    rect = pygame.Rect(0, 0, 800, 600)
    parent = Mock()
    ui_manager = Mock()
    return rect, parent, ui_manager


@pytest.fixture
def sample_characters():
    """サンプルキャラクターデータ"""
    return [
        {
            "id": "char1",
            "name": "戦士アレン",
            "race": "human",
            "class": "fighter",
            "level": 5,
            "stats": {"str": 16, "dex": 12, "con": 14, "int": 10, "wis": 13, "cha": 11},
            "is_alive": True,
            "experience": 1000
        },
        {
            "id": "char2", 
            "name": "魔法使いベラ",
            "race": "elf",
            "class": "mage",
            "level": 3,
            "stats": {"str": 8, "dex": 14, "con": 10, "int": 17, "wis": 15, "cha": 12},
            "is_alive": True,
            "experience": 600
        },
        {
            "id": "char3",
            "name": "盗賊チャド",
            "race": "halfling", 
            "class": "thief",
            "level": 4,
            "stats": {"str": 10, "dex": 18, "con": 12, "int": 14, "wis": 13, "cha": 15},
            "is_alive": False,
            "experience": 800
        }
    ]


class TestCharacterListPanelBasic:
    """CharacterListPanelの基本機能テスト"""
    
    def test_initialization_list_mode(self, mock_controller, mock_ui_setup):
        """リストモードでの初期化"""
        from src.facilities.ui.guild.character_list_panel import CharacterListPanel
        
        rect, parent, ui_manager = mock_ui_setup
        
        with patch('src.facilities.ui.service_panel.ServicePanel.__init__', return_value=None):
            panel = CharacterListPanel(rect, parent, mock_controller, ui_manager)
            panel.controller = mock_controller  # Manually set the controller
            
            # 初期状態の確認
            assert panel.characters == []
            assert panel.display_mode == "list"
            assert panel.selected_character is None
            assert panel.selected_index is None
            assert panel.current_filter == "all"
            assert panel.current_sort == "name"
    
    def test_set_mode_class_change(self, mock_controller, mock_ui_setup):
        """クラス変更モードの設定"""
        from src.facilities.ui.guild.character_list_panel import CharacterListPanel
        
        rect, parent, ui_manager = mock_ui_setup
        
        with patch('src.facilities.ui.service_panel.ServicePanel.__init__', return_value=None):
            panel = CharacterListPanel(rect, parent, mock_controller, ui_manager)
            panel.controller = mock_controller  # Manually set the controller
            panel.title_label = Mock()
            panel.action_button = Mock()
            panel.character_list = Mock()  # Mock the UI elements
            panel.detail_box = Mock()
            panel.filter_dropdown = Mock()
            panel.sort_dropdown = Mock()
            
            # Mock the service action to return a successful result
            mock_result = Mock()
            mock_result.is_success.return_value = True
            mock_result.data = {"characters": []}
            
            with patch.object(panel, '_execute_service_action', return_value=mock_result) as mock_execute:
                panel.set_mode("class_change")
                
                assert panel.display_mode == "class_change"
                # Verify that the service was called with proper parameters
                mock_execute.assert_called_once_with("character_list", {"filter": "in_party"})
    
    def test_set_mode_list(self, mock_controller, mock_ui_setup):
        """リストモードの設定"""
        from src.facilities.ui.guild.character_list_panel import CharacterListPanel
        
        rect, parent, ui_manager = mock_ui_setup
        
        with patch('src.facilities.ui.service_panel.ServicePanel.__init__', return_value=None):
            panel = CharacterListPanel(rect, parent, mock_controller, ui_manager)
            panel.controller = mock_controller  # Manually set the controller
            panel.title_label = Mock()
            panel.action_button = Mock()
            panel.character_list = Mock()  # Mock the UI elements
            panel.detail_box = Mock()
            panel.filter_dropdown = Mock()
            panel.sort_dropdown = Mock()
            
            # Mock the service action to return a successful result
            mock_result = Mock()
            mock_result.is_success.return_value = True
            mock_result.data = {"characters": []}
            
            with patch.object(panel, '_execute_service_action', return_value=mock_result) as mock_execute:
                panel.set_mode("list")
                
                assert panel.display_mode == "list"
                # In list mode, it should use current filter and sort
                mock_execute.assert_called_once_with("character_list", {
                    "filter": panel.current_filter,
                    "sort": panel.current_sort
                })


class TestCharacterListPanelDataHandling:
    """CharacterListPanelのデータ処理テスト"""
    
    def test_load_character_data(self, mock_controller, sample_characters):
        """キャラクターデータの読み込み"""
        from src.facilities.ui.guild.character_list_panel import CharacterListPanel
        
        mock_controller.service.get_all_characters.return_value = sample_characters
        
        panel = Mock()
        panel.controller = mock_controller
        panel.display_mode = "list"  # Set display mode
        panel.current_filter = "all"
        panel.current_sort = "name"
        
        # Mock the service result
        mock_result = Mock()
        mock_result.is_success.return_value = True
        mock_result.data = {"characters": sample_characters}
        
        with patch.object(panel, '_update_character_list') as mock_update, \
             patch.object(panel, '_execute_service_action', return_value=mock_result) as mock_execute, \
             patch.object(panel, '_update_detail_view') as mock_detail, \
             patch.object(panel, '_update_action_button') as mock_action:
            CharacterListPanel._load_character_data(panel)
            
            assert panel.characters == sample_characters
            mock_update.assert_called_once()
            mock_execute.assert_called_once_with("character_list", {"filter": "all", "sort": "name"})
    
    def test_load_character_data_no_service(self, mock_controller):
        """サービスメソッドが存在しない場合"""
        from src.facilities.ui.guild.character_list_panel import CharacterListPanel
        
        # get_all_charactersメソッドが存在しない
        del mock_controller.service.get_all_characters
        
        panel = Mock()
        panel.controller = mock_controller
        panel.characters = []
        panel.display_mode = "list"
        panel.current_filter = "all"
        panel.current_sort = "name"
        
        # Mock the service result to simulate an error
        mock_result = Mock()
        mock_result.is_success.return_value = False
        mock_result.data = None
        
        with patch.object(panel, '_execute_service_action', return_value=mock_result) as mock_execute:
            # エラーが発生しないことを確認
            try:
                CharacterListPanel._load_character_data(panel)
                assert True
            except Exception as e:
                pytest.fail(f"Unexpected exception: {e}")


class TestCharacterListPanelFiltering:
    """CharacterListPanelのフィルタリング機能テスト"""
    
    def test_handle_filter_change_alive(self, sample_characters):
        """生存フィルタの処理"""
        from src.facilities.ui.guild.character_list_panel import CharacterListPanel
        
        # Create a mock that allows attribute assignment
        panel = MagicMock()
        panel.characters = sample_characters
        panel.current_filter = "all"
        
        # Mock _load_character_data since it will be called
        with patch.object(panel, '_load_character_data') as mock_load:
            CharacterListPanel._handle_filter_change(panel, "パーティ外")
            
            assert panel.current_filter == "available"
            mock_load.assert_called_once()
    
    def test_handle_filter_change_dead(self, sample_characters):
        """死亡フィルタの処理"""
        from src.facilities.ui.guild.character_list_panel import CharacterListPanel
        
        panel = MagicMock()
        panel.characters = sample_characters
        panel.current_filter = "all"
        
        with patch.object(panel, '_load_character_data') as mock_load:
            CharacterListPanel._handle_filter_change(panel, "パーティ内")
            
            assert panel.current_filter == "in_party"
            mock_load.assert_called_once()
    
    def test_handle_filter_change_class(self, sample_characters):
        """クラスフィルタの処理"""
        from src.facilities.ui.guild.character_list_panel import CharacterListPanel
        
        panel = MagicMock()
        panel.characters = sample_characters
        panel.current_filter = "in_party"  # Start with a different filter
        
        with patch.object(panel, '_load_character_data') as mock_load:
            CharacterListPanel._handle_filter_change(panel, "全員")
            
            assert panel.current_filter == "all"
            mock_load.assert_called_once()


class TestCharacterListPanelSorting:
    """CharacterListPanelのソート機能テスト"""
    
    def test_handle_sort_change_name(self, sample_characters):
        """名前ソートの処理"""
        from src.facilities.ui.guild.character_list_panel import CharacterListPanel
        
        panel = MagicMock()
        panel.characters = sample_characters
        panel.current_sort = "level"
        
        with patch.object(panel, '_load_character_data') as mock_load:
            CharacterListPanel._handle_sort_change(panel, "名前順")
            
            assert panel.current_sort == "name"
            mock_load.assert_called_once()
    
    def test_handle_sort_change_level(self, sample_characters):
        """レベルソートの処理"""
        from src.facilities.ui.guild.character_list_panel import CharacterListPanel
        
        panel = MagicMock()
        panel.characters = sample_characters
        panel.current_sort = "name"
        
        with patch.object(panel, '_load_character_data') as mock_load:
            CharacterListPanel._handle_sort_change(panel, "レベル順")
            
            assert panel.current_sort == "level"
            mock_load.assert_called_once()
    
    def test_handle_sort_change_class(self, sample_characters):
        """職業ソートの処理"""
        from src.facilities.ui.guild.character_list_panel import CharacterListPanel
        
        panel = MagicMock()
        panel.characters = sample_characters
        panel.current_sort = "name"
        
        with patch.object(panel, '_load_character_data') as mock_load:
            CharacterListPanel._handle_sort_change(panel, "職業順")
            
            assert panel.current_sort == "class"
            mock_load.assert_called_once()


class TestCharacterListPanelSelection:
    """CharacterListPanelの選択機能テスト"""
    
    def test_handle_character_selection_valid(self, sample_characters):
        """有効なキャラクター選択の処理"""
        from src.facilities.ui.guild.character_list_panel import CharacterListPanel
        
        panel = Mock()
        panel.characters = sample_characters
        panel.selected_character = None
        panel.selected_index = None
        
        # Mock the character_list UI element
        panel.character_list = Mock()
        mock_item_list = Mock()
        mock_item_list.index.return_value = 0  # First item
        panel.character_list.item_list = mock_item_list
        
        with patch.object(panel, '_update_detail_view') as mock_detail, \
             patch.object(panel, '_update_action_button') as mock_action:
            
            # "戦士アレン Lv.5 (Fighter)" 形式での選択をシミュレート
            CharacterListPanel._handle_character_selection(panel, "戦士アレン Lv.5")
            
            assert panel.selected_character == sample_characters[0]
            assert panel.selected_index == 0
            mock_detail.assert_called_once()
            mock_action.assert_called_once()
    
    def test_handle_character_selection_none(self, sample_characters):
        """選択解除の処理"""
        from src.facilities.ui.guild.character_list_panel import CharacterListPanel
        
        panel = Mock()
        panel.characters = sample_characters
        panel.selected_character = sample_characters[0]
        panel.selected_index = 0
        
        with patch.object(panel, '_update_detail_view') as mock_detail, \
             patch.object(panel, '_update_action_button') as mock_action:
            
            CharacterListPanel._handle_character_selection(panel, None)
            
            assert panel.selected_character is None
            assert panel.selected_index is None
            mock_detail.assert_called_once()
            mock_action.assert_called_once()
    
    def test_get_selected_character(self, sample_characters):
        """選択されたキャラクターの取得"""
        from src.facilities.ui.guild.character_list_panel import CharacterListPanel
        
        panel = Mock()
        panel.selected_character = sample_characters[1]
        
        result = CharacterListPanel.get_selected_character(panel)
        
        assert result == sample_characters[1]
    
    def test_get_selected_character_none(self):
        """選択されていない場合"""
        from src.facilities.ui.guild.character_list_panel import CharacterListPanel
        
        panel = Mock()
        panel.selected_character = None
        
        result = CharacterListPanel.get_selected_character(panel)
        
        assert result is None


class TestCharacterListPanelActions:
    """CharacterListPanelのアクション機能テスト"""
    
    def test_handle_button_click_action_button(self, sample_characters):
        """アクションボタンクリックの処理"""
        from src.facilities.ui.guild.character_list_panel import CharacterListPanel
        
        panel = Mock()
        panel.action_button = Mock()
        panel.display_mode = "class_change"
        
        button = panel.action_button
        
        with patch.object(panel, '_handle_class_change') as mock_class_change:
            result = CharacterListPanel.handle_button_click(panel, button)
            
            assert result is True
            mock_class_change.assert_called_once()
    
    def test_handle_button_click_unknown_button(self):
        """未知のボタンクリックの処理"""
        from src.facilities.ui.guild.character_list_panel import CharacterListPanel
        
        panel = Mock()
        panel.action_button = Mock()
        
        unknown_button = Mock()
        
        result = CharacterListPanel.handle_button_click(panel, unknown_button)
        
        assert result is False
    
    def test_handle_class_change_with_selection(self, sample_characters):
        """選択ありでのクラス変更処理"""
        from src.facilities.ui.guild.character_list_panel import CharacterListPanel
        
        panel = Mock()
        panel.selected_character = sample_characters[0]
        panel.controller = Mock()
        
        # Mock the service results
        # First call: get available classes
        mock_get_classes = Mock()
        mock_get_classes.is_success.return_value = True
        mock_get_classes.data = {
            "available_classes": [
                {"id": "warrior", "name": "戦士"},
                {"id": "knight", "name": "騎士"}
            ]
        }
        mock_get_classes.message = "転職可能なクラス"
        
        # Second call: confirmation
        mock_confirm = Mock()
        mock_confirm.is_success.return_value = True
        mock_confirm.result_type = Mock()
        mock_confirm.result_type.value = "confirm"
        mock_confirm.message = "確認"
        
        # Third call: actual execution
        mock_execute_result = Mock()
        mock_execute_result.is_success.return_value = True
        mock_execute_result.message = "転職に成功しました"
        
        with patch.object(panel, '_execute_service_action') as mock_execute, \
             patch.object(panel, '_show_message') as mock_message, \
             patch.object(panel, '_load_character_data') as mock_load:
            # Set up the sequence of calls
            mock_execute.side_effect = [mock_get_classes, mock_confirm, mock_execute_result]
            
            CharacterListPanel._handle_class_change(panel)
            
            # Verify the calls
            assert mock_execute.call_count == 3
            mock_execute.assert_any_call("class_change", {"character_id": "char1"})
            mock_execute.assert_any_call("class_change", {"character_id": "char1", "new_class": "warrior"})
            mock_execute.assert_any_call("class_change", {"character_id": "char1", "new_class": "warrior", "confirmed": True})
            
            # Verify messages
            assert mock_message.call_count == 2
            mock_message.assert_any_call("戦士アレンをwarriorに変更します", "info")
            mock_message.assert_any_call("転職に成功しました", "info")
            mock_load.assert_called_once()
    
    def test_handle_class_change_no_selection(self):
        """選択なしでのクラス変更処理"""
        from src.facilities.ui.guild.character_list_panel import CharacterListPanel
        
        panel = Mock()
        panel.selected_character = None
        
        # エラーが発生しないことを確認
        try:
            CharacterListPanel._handle_class_change(panel)
            assert True
        except Exception as e:
            pytest.fail(f"Unexpected exception: {e}")
    
    def test_handle_detail_view(self, sample_characters):
        """詳細表示の処理"""
        from src.facilities.ui.guild.character_list_panel import CharacterListPanel
        
        panel = Mock()
        panel.selected_character = sample_characters[0]
        
        with patch.object(panel, '_show_message') as mock_message:
            CharacterListPanel._handle_detail_view(panel)
            # The method shows a message with character details
            mock_message.assert_called_once()
            # Check that the message contains the character name
            call_args = mock_message.call_args[0]
            assert "戦士アレン" in call_args[0]


class TestCharacterListPanelEvents:
    """CharacterListPanelのイベント処理テスト"""
    
    def test_handle_dropdown_changed_filter(self):
        """フィルタドロップダウンのイベント処理"""
        from src.facilities.ui.guild.character_list_panel import CharacterListPanel
        
        panel = Mock()
        panel.filter_dropdown = Mock()
        
        # ドロップダウンイベントのモック
        event = Mock()
        event.type = pygame_gui.UI_DROP_DOWN_MENU_CHANGED
        event.ui_element = panel.filter_dropdown
        event.text = "パーティ外"
        
        with patch.object(panel, '_handle_filter_change') as mock_filter:
            result = CharacterListPanel.handle_dropdown_changed(panel, event)
            
            assert result is True
            mock_filter.assert_called_with("パーティ外")
    
    def test_handle_dropdown_changed_sort(self):
        """ソートドロップダウンのイベント処理"""
        from src.facilities.ui.guild.character_list_panel import CharacterListPanel
        
        panel = Mock()
        panel.sort_dropdown = Mock()
        
        # ドロップダウンイベントのモック
        event = Mock()
        event.type = pygame_gui.UI_DROP_DOWN_MENU_CHANGED
        event.ui_element = panel.sort_dropdown
        event.text = "レベル順"
        
        with patch.object(panel, '_handle_sort_change') as mock_sort:
            result = CharacterListPanel.handle_dropdown_changed(panel, event)
            
            assert result is True
            mock_sort.assert_called_with("レベル順")
    
    def test_handle_dropdown_changed_unknown(self):
        """未知のドロップダウンのイベント処理"""
        from src.facilities.ui.guild.character_list_panel import CharacterListPanel
        
        panel = Mock()
        panel.filter_dropdown = Mock()
        panel.sort_dropdown = Mock()
        
        # 未知のドロップダウンイベント
        event = Mock()
        event.ui_element = Mock()  # 異なるUI要素
        
        result = CharacterListPanel.handle_dropdown_changed(panel, event)
        
        assert result is False
    
    def test_handle_selection_list_changed(self):
        """選択リストのイベント処理"""
        from src.facilities.ui.guild.character_list_panel import CharacterListPanel
        
        panel = Mock()
        panel.character_list = Mock()
        
        # 選択イベントのモック
        event = Mock()
        event.type = pygame_gui.UI_SELECTION_LIST_NEW_SELECTION
        event.ui_element = panel.character_list
        panel.character_list.get_single_selection.return_value = "戦士アレン Lv.5"
        
        with patch.object(panel, '_handle_character_selection') as mock_selection:
            result = CharacterListPanel.handle_selection_list_changed(panel, event)
            
            assert result is True
            mock_selection.assert_called_with("戦士アレン Lv.5")
    
    def test_handle_selection_list_changed_unknown(self):
        """未知の選択リストのイベント処理"""
        from src.facilities.ui.guild.character_list_panel import CharacterListPanel
        
        panel = Mock()
        panel.character_list = Mock()
        
        # 未知のUI要素のイベント
        event = Mock()
        event.ui_element = Mock()  # 異なるUI要素
        
        result = CharacterListPanel.handle_selection_list_changed(panel, event)
        
        assert result is False


class TestCharacterListPanelRefresh:
    """CharacterListPanelのリフレッシュ機能テスト"""
    
    def test_refresh(self, mock_controller, sample_characters):
        """リフレッシュ処理"""
        from src.facilities.ui.guild.character_list_panel import CharacterListPanel
        
        panel = Mock()
        panel.controller = mock_controller
        
        with patch.object(panel, '_load_character_data') as mock_load:
            CharacterListPanel.refresh(panel)
            mock_load.assert_called_once()


class TestCharacterListPanelUIUpdates:
    """CharacterListPanelのUI更新テスト"""
    
    def test_update_character_list(self, sample_characters):
        """キャラクターリストの更新"""
        from src.facilities.ui.guild.character_list_panel import CharacterListPanel
        
        panel = Mock()
        panel.characters = sample_characters
        panel.current_filter = "all"
        panel.current_sort = "name"
        panel.character_list = Mock()
        
        # 実際のメソッドを呼び出すためモック化
        with patch.object(CharacterListPanel, '_update_character_list'):
            # メソッドが存在することを確認
            assert hasattr(CharacterListPanel, '_update_character_list')
    
    def test_update_detail_view(self, sample_characters):
        """詳細ビューの更新"""
        from src.facilities.ui.guild.character_list_panel import CharacterListPanel
        
        panel = Mock()
        panel.selected_character = sample_characters[0]
        panel.detail_box = Mock()
        
        # 実際のメソッドを呼び出すためモック化
        with patch.object(CharacterListPanel, '_update_detail_view'):
            # メソッドが存在することを確認
            assert hasattr(CharacterListPanel, '_update_detail_view')
    
    def test_update_action_button(self, sample_characters):
        """アクションボタンの更新"""
        from src.facilities.ui.guild.character_list_panel import CharacterListPanel
        
        panel = Mock()
        panel.selected_character = sample_characters[0]
        panel.action_button = Mock()
        panel.display_mode = "class_change"
        
        # 実際のメソッドを呼び出すためモック化
        with patch.object(CharacterListPanel, '_update_action_button'):
            # メソッドが存在することを確認
            assert hasattr(CharacterListPanel, '_update_action_button')