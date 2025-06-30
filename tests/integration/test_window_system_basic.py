"""WindowSystem基本統合テスト"""

import os
import sys
import pygame
from unittest.mock import Mock, patch

# ヘッドレス環境でのPygame初期化
os.environ['SDL_VIDEODRIVER'] = 'dummy'

# パス設定
sys.path.insert(0, '/home/satorue/Dungeon')

from src.ui.window_system.window_manager import WindowManager
from src.ui.window_system.window import Window, WindowState
from src.ui.window_system.settings_window import SettingsWindow


class MockWindow(Window):
    """テスト用の具象Windowクラス"""
    
    def __init__(self, window_id: str):
        super().__init__(window_id)
        self.created = False
    
    def create(self):
        """ウィンドウ作成"""
        self.created = True
    
    def handle_event(self, event):
        """イベント処理"""
        return False


class TestWindowSystemBasic:
    """WindowSystem基本統合テストクラス"""
    
    def setup_method(self):
        """各テストメソッドの前に実行"""
        pygame.init()
        self.screen = pygame.display.set_mode((800, 600))
        
    def teardown_method(self):
        """各テストメソッドの後に実行"""
        pygame.quit()
    
    def test_window_manager_singleton(self):
        """WindowManagerシングルトンテスト"""
        manager1 = WindowManager.get_instance()
        manager2 = WindowManager.get_instance()
        
        assert manager1 is manager2
        assert manager1 is not None
    
    def test_basic_window_creation(self):
        """基本Window作成テスト"""
        window_manager = WindowManager.get_instance()
        
        # 基本Windowの作成
        window = MockWindow("test_window")
        assert window.window_id == "test_window"
        assert window.state == WindowState.CREATED
    
    def test_window_show_hide_cycle(self):
        """Window表示・非表示サイクルテスト"""
        window_manager = WindowManager.get_instance()
        window = MockWindow("test_cycle")
        
        # 初期状態は作成済み
        assert window.state == WindowState.CREATED
        
        # 表示
        window.show()
        assert window.state == WindowState.SHOWN
        
        # 非表示
        window.hide()
        assert window.state == WindowState.HIDDEN
    
    def test_window_manager_basic_functionality(self):
        """WindowManagerの基本機能テスト"""
        window_manager = WindowManager.get_instance()
        
        # WindowManagerの基本機能が利用できることを確認
        try:
            # ウィンドウスタックが存在することを確認
            assert hasattr(window_manager, 'window_stack')
            
            # アクティブウィンドウ取得機能
            active_window = window_manager.get_active_window()
            # 初期状態ではNoneまたは何らかのウィンドウ
            assert active_window is None or hasattr(active_window, 'window_id')
            
            # フォーカスウィンドウ取得機能
            focused_window = window_manager.get_focused_window()
            assert focused_window is None or hasattr(focused_window, 'window_id')
            
            # 基本機能が動作することを確認
            assert True
        except Exception as e:
            assert False, f"WindowManager基本機能エラー: {e}"
    
    def test_pygame_integration(self):
        """Pygame統合テスト"""
        # Pygameの基本機能が正常に動作することを確認
        assert pygame.get_init() is True
        assert self.screen is not None
        assert self.screen.get_size() == (800, 600)
    
    def test_window_system_core_imports(self):
        """WindowSystemコアモジュールインポートテスト"""
        try:
            from src.ui.window_system.window import Window
            from src.ui.window_system.window_manager import WindowManager
            from src.ui.window_system.inventory_window import InventoryWindow
            from src.ui.window_system.equipment_window import EquipmentWindow
            from src.ui.window_system.magic_window import MagicWindow
            from src.ui.window_system.settings_window import SettingsWindow
            
            # すべてのインポートが成功したことを確認
            assert True
        except ImportError as e:
            assert False, f"WindowSystemコアモジュールインポートエラー: {e}"
    
    def test_window_system_no_uimenu_references(self):
        """WindowSystemにUIMenu参照がないことを確認"""
        window_manager = WindowManager.get_instance()
        window = MockWindow("test_no_uimenu")
        
        # WindowSystemクラスにUIMenuやUIDialog参照がないことを確認
        window_attrs = dir(window)
        manager_attrs = dir(window_manager)
        
        uimenu_refs = [attr for attr in window_attrs + manager_attrs 
                      if 'uimenu' in attr.lower() or 'uidialog' in attr.lower()]
        
        assert len(uimenu_refs) == 0, f"UIMenu参照が残存: {uimenu_refs}"