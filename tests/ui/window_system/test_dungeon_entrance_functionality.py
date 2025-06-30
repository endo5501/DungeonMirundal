"""
ダンジョン入口機能のテスト

ダンジョン入口ボタンが押されても何も発生しない問題をテスト・修正する
"""

import unittest
import pygame
from unittest.mock import Mock, patch

from src.ui.window_system import WindowManager
from src.overworld.overworld_manager_pygame import OverworldManager
from src.character.party import Party
from src.character.character import Character, CharacterStatus


class TestDungeonEntranceFunctionality(unittest.TestCase):
    """ダンジョン入口機能のテスト"""
    
    def setUp(self):
        """テスト前の準備"""
        pygame.init()
        pygame.display.set_mode((1024, 768))
        
        # WindowManagerのインスタンスをリセット
        WindowManager._instance = None
        
        # テスト用パーティを作成
        self.test_party = self._create_test_party()
        
    def tearDown(self):
        """テスト後のクリーンアップ"""
        WindowManager._instance = None
        pygame.quit()
    
    def _create_test_party(self) -> Party:
        """テスト用のパーティを作成"""
        party = Party("テストパーティ")
        party.gold = 1000
        
        character = Character()
        character.name = "テストキャラクター"
        character.status = CharacterStatus.GOOD
        
        party.add_character(character)
        return party
    
    def test_dungeon_entrance_button_should_trigger_dungeon_selection(self):
        """
        ダンジョン入口ボタンが押された際、ダンジョン選択画面が表示されるべき
        
        現在失敗する可能性のあるテスト
        """
        # WindowManagerを初期化
        window_manager = WindowManager.get_instance()
        screen = pygame.display.get_surface()
        clock = pygame.time.Clock()
        window_manager.initialize_pygame(screen, clock)
        
        # OverworldManagerを初期化
        overworld_manager = OverworldManager()
        overworld_manager.set_ui_manager(window_manager.ui_manager)
        overworld_manager.set_party(self.test_party)
        
        # ダンジョン入場コールバックのMock
        mock_dungeon_callback = Mock()
        overworld_manager.set_enter_dungeon_callback(mock_dungeon_callback)
        
        # 地上部に入場
        success = overworld_manager.enter_overworld(self.test_party)
        self.assertTrue(success, "地上部入場が失敗")
        
        # ダンジョン入口ボタンのメッセージを送信
        result = overworld_manager.handle_main_menu_message(
            'menu_item_selected', 
            {'item_id': 'dungeon_entrance'}
        )
        
        # メッセージが処理されることを確認
        self.assertTrue(result, "ダンジョン入口メッセージが処理されませんでした")
    
    def test_on_enter_dungeon_method_functionality(self):
        """
        _on_enter_dungeon()メソッドの機能をテスト
        """
        # WindowManagerを初期化
        window_manager = WindowManager.get_instance()
        screen = pygame.display.get_surface()
        clock = pygame.time.Clock()
        window_manager.initialize_pygame(screen, clock)
        
        # OverworldManagerを初期化
        overworld_manager = OverworldManager()
        overworld_manager.set_ui_manager(window_manager.ui_manager)
        overworld_manager.set_party(self.test_party)
        
        # _on_enter_dungeon()メソッドを直接テスト
        try:
            overworld_manager._on_enter_dungeon()
            print("_on_enter_dungeon() メソッドが正常に実行されました")
        except Exception as e:
            print(f"_on_enter_dungeon() メソッドでエラー: {e}")
            self.fail(f"_on_enter_dungeon() メソッドでエラーが発生: {e}")
    
    def test_show_dungeon_selection_menu_functionality(self):
        """
        _show_dungeon_selection_menu()メソッドの機能をテスト
        """
        # WindowManagerを初期化
        window_manager = WindowManager.get_instance()
        screen = pygame.display.get_surface()
        clock = pygame.time.Clock()
        window_manager.initialize_pygame(screen, clock)
        
        # OverworldManagerを初期化
        overworld_manager = OverworldManager()
        overworld_manager.set_ui_manager(window_manager.ui_manager)
        overworld_manager.set_party(self.test_party)
        
        # UIManagerが設定されていることを確認
        self.assertIsNotNone(overworld_manager.ui_manager, "UIマネージャーが設定されていません")
        
        # _show_dungeon_selection_menu()メソッドを直接テスト
        try:
            overworld_manager._show_dungeon_selection_menu()
            print("_show_dungeon_selection_menu() メソッドが正常に実行されました")
            
            # ダンジョン選択リストが作成されたかチェック
            self.assertIsNotNone(overworld_manager.dungeon_selection_list, 
                               "ダンジョン選択リストが作成されていません")
            
        except Exception as e:
            print(f"_show_dungeon_selection_menu() メソッドでエラー: {e}")
            # エラーの詳細を出力
            import traceback
            traceback.print_exc()
            self.fail(f"_show_dungeon_selection_menu() メソッドでエラーが発生: {e}")
    
    def test_ui_manager_pygame_gui_manager_availability(self):
        """
        UIManagerのpygame_gui_manager属性の可用性をテスト
        
        _show_dungeon_selection_menu()でui_manager.pygame_gui_managerを使用している
        """
        # WindowManagerを初期化
        window_manager = WindowManager.get_instance()
        screen = pygame.display.get_surface()
        clock = pygame.time.Clock()
        window_manager.initialize_pygame(screen, clock)
        
        # UIManagerの確認
        ui_manager = window_manager.ui_manager
        self.assertIsNotNone(ui_manager, "UIManagerが存在しません")
        
        # pygame_gui_manager属性の確認
        if hasattr(ui_manager, 'pygame_gui_manager'):
            print("ui_manager.pygame_gui_manager が利用可能です")
        else:
            print("ui_manager.pygame_gui_manager が利用できません")
            print(f"ui_manager の型: {type(ui_manager)}")
            print(f"ui_manager の属性: {dir(ui_manager)}")
            
            # WindowManagerのUIManagerはpygame_gui.UIManagerインスタンスであるべき
            import pygame_gui
            if isinstance(ui_manager, pygame_gui.UIManager):
                print("UIManagerはpygame_gui.UIManagerインスタンスです")
                # この場合、ui_manager自体をpygame_gui_managerとして使用すべき
            else:
                self.fail("UIManagerがpygame_gui.UIManagerインスタンスではありません")


if __name__ == '__main__':
    unittest.main()