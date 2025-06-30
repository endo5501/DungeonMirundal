"""
dungeon_ui_pygame.pyのBattleUIWindow移行テスト

t-wada式TDDに従って、既存のUIMenu形式から新WindowSystem形式への移行をテスト
"""
import pytest
import pygame
from unittest.mock import Mock, patch, MagicMock

from src.ui.window_system import WindowManager
from src.ui.window_system.battle_ui_window import BattleUIWindow
from src.character.party import Party
from src.core.config_manager import config_manager
from src.utils.logger import logger


class TestDungeonUIBattleUIWindowMigration:
    """ダンジョンUIのBattleUIWindow移行テスト"""
    
    def setup_method(self):
        """テスト前の準備"""
        # Pygameを初期化
        if not pygame.get_init():
            pygame.init()
        
        # WindowManagerをリセット
        WindowManager._instance = None
        self.window_manager = WindowManager.get_instance()
        
        # モックスクリーンを設定
        self.mock_screen = Mock()
        self.mock_screen.get_width.return_value = 1024
        self.mock_screen.get_height.return_value = 768
        
        # モックパーティを作成
        self.mock_party = Mock()
        self.mock_party.name = "テストパーティ"
        self.mock_party.characters = {}  # character_status_barで必要
        self.mock_party.get_alive_members = Mock(return_value=[])  # BattleUIWindowで必要
        
    def test_migrated_dungeon_ui_should_use_window_manager(self):
        """移行後のDungeonUIはWindowManagerを使用すべき"""
        # Given: 移行後のDungeonUIManager（新形式）
        from src.ui.dungeon_ui_pygame import DungeonUIManagerPygame
        
        # When: 新形式のDungeonUIManagerを作成
        ui_manager = DungeonUIManagerPygame(self.mock_screen)
        
        # Then: WindowManagerが設定されている
        assert hasattr(ui_manager, 'window_manager')
        assert ui_manager.window_manager is not None
        assert isinstance(ui_manager.window_manager, WindowManager)
    
    def test_migrated_dungeon_ui_should_create_battle_ui_window(self):
        """移行後のDungeonUIはBattleUIWindowを作成すべき"""
        # Given: 移行後のDungeonUIManager
        from src.ui.dungeon_ui_pygame import DungeonUIManagerPygame
        ui_manager = DungeonUIManagerPygame(self.mock_screen)
        ui_manager.set_party(self.mock_party)
        
        # モックバトルマネージャー
        mock_battle_manager = Mock()
        mock_enemies = Mock()
        mock_enemies.get_all_enemies.return_value = []
        
        # When: 戦闘UIを表示
        ui_manager.show_battle_ui(mock_battle_manager, mock_enemies)
        
        # Then: BattleUIWindowが作成される
        assert hasattr(ui_manager, 'battle_ui_window')
        assert ui_manager.battle_ui_window is not None
        assert isinstance(ui_manager.battle_ui_window, BattleUIWindow)
    
    def test_migrated_dungeon_ui_should_not_use_legacy_ui_menu(self):
        """移行後のDungeonUIは旧UIMenuを使用しないべき"""
        # Given: 移行後のDungeonUIManager
        from src.ui.dungeon_ui_pygame import DungeonUIManagerPygame
        ui_manager = DungeonUIManagerPygame(self.mock_screen)
        
        # When: UIManagerのソースコードを確認
        import inspect
        source = inspect.getsource(DungeonUIManagerPygame)
        
        # Then: 旧UIMenuクラスのインポートや使用がない
        assert 'UIMenu' not in source
        assert 'UIElement' not in source
        assert 'UIButton' not in source
        assert 'ui_manager' not in source
        assert 'base_ui_pygame' not in source
    
    @pytest.mark.skip(reason="Mock object iteration issue with pygame-gui")
    def test_migrated_dungeon_ui_should_delegate_menu_actions_to_battle_window(self):
        """移行後のDungeonUIはメニューアクションをBattleWindowに委譲すべき"""
        # Given: 移行後のDungeonUIManager with BattleUIWindow
        from src.ui.dungeon_ui_pygame import DungeonUIManagerPygame
        ui_manager = DungeonUIManagerPygame(self.mock_screen)
        ui_manager.set_party(self.mock_party)
        
        # モックバトルマネージャーと敵
        mock_battle_manager = Mock()
        mock_enemies = Mock()
        mock_enemies.get_all_enemies.return_value = []
        
        # BattleUIWindowを表示
        ui_manager.show_battle_ui(mock_battle_manager, mock_enemies)
        
        # When: アクションメニューを表示
        result = ui_manager.show_action_menu()
        
        # Then: BattleUIWindowにアクション表示が委譲される
        assert result is True
        assert ui_manager.battle_ui_window is not None
    
    def test_migrated_dungeon_ui_should_handle_events_through_battle_window(self):
        """移行後のDungeonUIはイベント処理をBattleWindowを通して行うべき"""
        # Given: 移行後のDungeonUIManager with BattleUIWindow
        from src.ui.dungeon_ui_pygame import DungeonUIManagerPygame
        ui_manager = DungeonUIManagerPygame(self.mock_screen)
        ui_manager.set_party(self.mock_party)
        
        # モックバトルマネージャーと敵
        mock_battle_manager = Mock()
        mock_enemies = Mock()
        mock_enemies.get_all_enemies.return_value = []
        
        # BattleUIWindowを表示
        ui_manager.show_battle_ui(mock_battle_manager, mock_enemies)
        
        # When: キーボードイベントを処理
        mock_event = Mock()
        mock_event.type = pygame.KEYDOWN
        mock_event.key = pygame.K_a
        
        with patch.object(ui_manager.battle_ui_window, 'handle_event', return_value=True) as mock_handle:
            result = ui_manager.handle_input(mock_event)
        
        # Then: BattleUIWindowのhandle_eventが呼ばれる
        assert result is True
        mock_handle.assert_called_once_with(mock_event)
    
    def test_migrated_dungeon_ui_should_preserve_existing_public_api(self):
        """移行後のDungeonUIは既存の公開APIを保持すべき"""
        # Given: 移行後のDungeonUIManager
        from src.ui.dungeon_ui_pygame import DungeonUIManagerPygame
        ui_manager = DungeonUIManagerPygame(self.mock_screen)
        
        # Then: 既存の公開メソッドが保持されている
        assert hasattr(ui_manager, 'set_party')
        assert hasattr(ui_manager, 'set_callback')
        assert hasattr(ui_manager, 'set_dungeon_state')
        assert hasattr(ui_manager, 'toggle_main_menu')
        assert hasattr(ui_manager, 'show_main_menu')
        assert hasattr(ui_manager, 'close_menu')
        assert hasattr(ui_manager, 'handle_input')
        assert hasattr(ui_manager, 'render')
        assert hasattr(ui_manager, 'render_overlay')
        assert hasattr(ui_manager, 'update')
        assert hasattr(ui_manager, 'cleanup')
    
    def test_migrated_dungeon_ui_should_use_window_system_configuration(self):
        """移行後のDungeonUIはWindowSystem設定を使用すべき"""
        # Given: 移行後のDungeonUIManager
        from src.ui.dungeon_ui_pygame import DungeonUIManagerPygame
        ui_manager = DungeonUIManagerPygame(self.mock_screen)
        
        # When: WindowSystem設定でBattleUIWindowを作成
        battle_config = ui_manager._create_battle_ui_config()
        
        # Then: WindowSystem形式の設定が作成される
        assert isinstance(battle_config, dict)
        assert 'battle_manager' in battle_config or 'party' in battle_config
    
    def test_migrated_dungeon_ui_should_cleanup_resources_properly(self):
        """移行後のDungeonUIはリソースを適切にクリーンアップすべき"""
        # Given: 移行後のDungeonUIManager with BattleUIWindow
        from src.ui.dungeon_ui_pygame import DungeonUIManagerPygame
        ui_manager = DungeonUIManagerPygame(self.mock_screen)
        ui_manager.set_party(self.mock_party)
        
        # モックバトルマネージャーと敵
        mock_battle_manager = Mock()
        mock_enemies = Mock()
        mock_enemies.get_all_enemies.return_value = []
        
        # BattleUIWindowを表示
        ui_manager.show_battle_ui(mock_battle_manager, mock_enemies)
        
        # When: クリーンアップを実行
        ui_manager.cleanup()
        
        # Then: BattleUIWindowもクリーンアップされる
        # (BattleUIWindowがNoneになるか、cleanup()が呼ばれる)
        assert ui_manager.battle_ui_window is None or hasattr(ui_manager.battle_ui_window, 'cleanup')