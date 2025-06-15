"""ダンジョンUI統合システムのテスト"""

import pytest
from unittest.mock import Mock, patch

from src.character.character import Character
from src.character.party import Party
from src.character.stats import BaseStats


class TestDungeonUIIntegration:
    """ダンジョンUI統合のテスト"""
    
    def setup_method(self):
        """各テストメソッドの前に実行"""
        # テスト用パーティ作成
        stats = BaseStats(strength=14, agility=12, intelligence=10, faith=11, luck=13)
        character = Character.create_character("TestHero", "human", "fighter", stats)
        
        self.party = Party(party_id="test_party", name="TestParty")
        self.party.add_character(character)
    
    def test_dungeon_ui_manager_initialization(self):
        """DungeonUIManagerの初期化テスト"""
        from src.ui.dungeon_ui import DungeonUIManager
        
        ui_manager = DungeonUIManager()
        
        # 基本プロパティの確認
        assert ui_manager.main_menu is not None
        assert ui_manager.status_bar is not None
        assert ui_manager.current_menu is None
        assert ui_manager.is_menu_open == False
        
        # パーティ設定
        ui_manager.set_party(self.party)
        assert ui_manager.party == self.party
    
    def test_dungeon_main_menu_creation(self):
        """ダンジョンメインメニューの作成テスト"""
        from src.ui.dungeon_ui import DungeonMainMenu
        
        menu = DungeonMainMenu()
        
        # メニュー項目の確認
        assert len(menu.menu_items) == 7  # 7つのメニュー項目
        assert any(item['action'] == 'inventory' for item in menu.menu_items)
        assert any(item['action'] == 'return_overworld' for item in menu.menu_items)
        
        # コールバック設定
        callback_called = False
        def test_callback():
            nonlocal callback_called
            callback_called = True
        
        menu.set_callback("test_action", test_callback)
        assert "test_action" in menu.callbacks
    
    def test_dungeon_status_bar(self):
        """ダンジョンステータスバーのテスト"""
        from src.ui.dungeon_ui import DungeonStatusBar
        
        status_bar = DungeonStatusBar()
        
        # パーティ設定
        status_bar.set_party(self.party)
        assert status_bar.party == self.party
        
        # 位置情報更新
        location_info = "(5, 3) レベル: 2"
        status_bar.update_location(location_info)
        
        # ステータス更新
        status_bar.update_status()
    
    def test_ui_manager_menu_operations(self):
        """UIマネージャーのメニュー操作テスト"""
        from src.ui.dungeon_ui import DungeonUIManager, DungeonMenuType
        
        ui_manager = DungeonUIManager()
        ui_manager.set_party(self.party)
        
        # メニューを開く
        ui_manager.open_main_menu()
        assert ui_manager.is_menu_open == True
        assert ui_manager.current_menu == DungeonMenuType.MAIN
        
        # メニューを閉じる
        ui_manager.close_all_menus()
        assert ui_manager.is_menu_open == False
        assert ui_manager.current_menu is None
        
        # トグル操作
        ui_manager.toggle_main_menu()
        assert ui_manager.is_menu_open == True
        
        ui_manager.toggle_main_menu()
        assert ui_manager.is_menu_open == False
    
    @patch('src.ui.dungeon_ui.logger')
    def test_callback_execution(self, mock_logger):
        """コールバック実行のテスト"""
        from src.ui.dungeon_ui import DungeonUIManager
        
        ui_manager = DungeonUIManager()
        
        # 外部コールバック設定
        callback_executed = False
        def test_callback():
            nonlocal callback_executed
            callback_executed = True
        
        ui_manager.set_callback("return_overworld", test_callback)
        
        # 地上部帰還のテスト
        ui_manager._return_to_overworld()
        assert callback_executed == True
    
    def test_ui_state_management(self):
        """UI状態管理のテスト"""
        from src.ui.dungeon_ui import DungeonUIManager
        
        ui_manager = DungeonUIManager()
        ui_manager.set_party(self.party)
        
        # ステータスバー表示/非表示
        ui_manager.show_status_bar()
        ui_manager.hide_status_bar()
        
        # 位置情報更新
        location_info = "(10, 7) レベル: 1"
        ui_manager.update_location(location_info)
        
        # パーティステータス更新
        ui_manager.update_party_status()
    
    def test_cleanup(self):
        """リソースクリーンアップのテスト"""
        from src.ui.dungeon_ui import DungeonUIManager
        
        ui_manager = DungeonUIManager()
        ui_manager.set_party(self.party)
        
        # クリーンアップ実行
        ui_manager.cleanup()
        
        # リソースが破棄されていることを確認
        # （実際のPanda3D要素がないため、例外が発生しないことを確認）
        assert True  # クラッシュしなければOK
    
    def test_inventory_integration(self):
        """インベントリ統合のテスト"""
        from src.ui.dungeon_ui import DungeonUIManager
        
        ui_manager = DungeonUIManager()
        ui_manager.set_party(self.party)
        
        # インベントリを開く（実際のUIは作成されないが、ログ出力を確認）
        with patch('src.ui.dungeon_ui.logger') as mock_logger:
            ui_manager._open_inventory()
            mock_logger.info.assert_called_with("インベントリメニューを開きます")
    
    def test_manager_references(self):
        """マネージャー参照設定のテスト"""
        from src.ui.dungeon_ui import DungeonUIManager
        
        ui_manager = DungeonUIManager()
        
        # モックマネージャー
        mock_dungeon_manager = Mock()
        mock_game_manager = Mock()
        
        ui_manager.set_managers(mock_dungeon_manager, mock_game_manager)
        
        assert ui_manager.dungeon_manager == mock_dungeon_manager
        assert ui_manager.game_manager == mock_game_manager


class TestDungeonRendererIntegration:
    """ダンジョンレンダラー統合のテスト"""
    
    def setup_method(self):
        """各テストメソッドの前に実行"""
        # テスト用パーティ作成
        stats = BaseStats(strength=14, agility=12, intelligence=10, faith=11, luck=13)
        character = Character.create_character("TestHero", "human", "fighter", stats)
        
        self.party = Party(party_id="test_party", name="TestParty")
        self.party.add_character(character)
    
    @patch('src.rendering.dungeon_renderer.PANDA3D_AVAILABLE', False)
    def test_renderer_without_panda3d(self):
        """Panda3D無しでのレンダラーテスト"""
        from src.rendering.dungeon_renderer import DungeonRenderer
        
        renderer = DungeonRenderer()
        assert renderer.enabled == False
    
    @patch('src.rendering.dungeon_renderer.ShowBase')
    @patch('src.rendering.dungeon_renderer.PANDA3D_AVAILABLE', True)
    def test_renderer_basic_functionality(self, mock_showbase):
        """レンダラーの基本機能テスト"""
        from src.rendering.dungeon_renderer import DungeonRenderer
        from src.dungeon.dungeon_manager import DungeonManager
        
        # ShowBaseをモック化
        mock_instance = Mock()
        mock_instance.win = Mock()
        mock_instance.camera = Mock()
        mock_instance.cam = Mock()
        mock_instance.render = Mock()
        mock_instance.accept = Mock()
        mock_showbase.return_value = mock_instance
        
        renderer = DungeonRenderer()
        assert renderer.enabled == True
        
        # ダンジョンマネージャー設定
        dungeon_manager = DungeonManager()
        renderer.set_dungeon_manager(dungeon_manager)
        assert renderer.dungeon_manager == dungeon_manager
        
        # パーティ設定
        renderer.set_party(self.party)
        assert renderer.current_party == self.party
    
    def test_ui_integration_methods(self):
        """UI統合メソッドのテスト"""
        from src.rendering.dungeon_renderer import DungeonRenderer
        
        # Panda3D無効状態でのテスト
        with patch('src.rendering.dungeon_renderer.PANDA3D_AVAILABLE', False):
            renderer = DungeonRenderer()
            
            # メソッドが例外を発生させないことを確認
            renderer.set_party(self.party)
            renderer.update_ui()
            renderer._show_menu()
            renderer._return_to_overworld()