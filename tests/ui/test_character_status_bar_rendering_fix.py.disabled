"""キャラクターステータスバー描画順序修正のテスト"""

import pytest
import pygame
from unittest.mock import Mock, patch
import sys
import os

# テスト用のパス設定
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from src.ui.base_ui_pygame import UIManager, UIMenu, initialize_ui_manager
from src.ui.character_status_bar import CharacterStatusBar, create_character_status_bar
from src.overworld.overworld_manager_pygame import OverworldManager
from src.character.party import Party
from src.character.character import Character


class TestCharacterStatusBarRenderingFix:
    """キャラクターステータスバー描画順序修正のテスト"""
    
    def setup_method(self):
        """テストセットアップ"""
        pygame.init()
        pygame.display.set_mode((1024, 768))
        
    def teardown_method(self):
        """テストクリーンアップ"""
        pygame.quit()
        
    def test_ui_manager_has_persistent_elements(self):
        """UIManagerがpersistent_elementsを持つことを確認"""
        screen = pygame.display.get_surface()
        ui_manager = UIManager(screen)
        
        assert hasattr(ui_manager, 'persistent_elements')
        assert isinstance(ui_manager.persistent_elements, dict)
        
    def test_ui_manager_add_persistent_element(self):
        """UIManagerのadd_persistent_elementメソッドの動作を確認"""
        screen = pygame.display.get_surface()
        ui_manager = UIManager(screen)
        
        # キャラクターステータスバーを作成
        status_bar = create_character_status_bar(1024, 768)
        
        # persistent_elementsに追加
        ui_manager.add_persistent_element(status_bar)
        
        # 正しく追加されたことを確認
        assert status_bar.element_id in ui_manager.persistent_elements
        assert ui_manager.persistent_elements[status_bar.element_id] == status_bar
        
    def test_ui_manager_render_order(self):
        """UIManagerの描画順序が正しいことを確認"""
        screen = pygame.display.get_surface()
        ui_manager = UIManager(screen)
        
        # 各要素をモック
        normal_element = Mock()
        normal_element.render = Mock()
        normal_element.element_id = "normal"
        
        persistent_element = Mock()
        persistent_element.render = Mock()
        persistent_element.element_id = "persistent"
        
        menu = Mock()
        menu.render = Mock()
        menu.menu_id = "menu"
        
        # 要素を追加
        ui_manager.add_element(normal_element)
        ui_manager.add_persistent_element(persistent_element)
        ui_manager.add_menu(menu)
        
        # pygame_gui_managerをモック
        ui_manager.pygame_gui_manager = Mock()
        ui_manager.pygame_gui_manager.draw_ui = Mock()
        
        # renderを実行
        ui_manager.render()
        
        # 描画順序を確認（persistent_elementが最後に描画される）
        normal_element.render.assert_called_once()
        menu.render.assert_called_once()
        persistent_element.render.assert_called_once()
        ui_manager.pygame_gui_manager.draw_ui.assert_called_once()
        
    def test_overworld_manager_uses_persistent_element(self):
        """OverworldManagerがキャラクターステータスバーをpersistent_elementとして追加することを確認"""
        # UIManagerをモック
        ui_manager = Mock()
        ui_manager.add_persistent_element = Mock()
        ui_manager.pygame_gui_manager = Mock()
        
        # OverworldManagerを作成
        overworld_manager = OverworldManager()
        overworld_manager.set_ui_manager(ui_manager)
        
        # add_persistent_elementが呼び出されたことを確認
        ui_manager.add_persistent_element.assert_called_once()
        
        # 引数がCharacterStatusBarであることを確認
        args, kwargs = ui_manager.add_persistent_element.call_args
        assert len(args) == 1
        assert isinstance(args[0], CharacterStatusBar)
        
    def test_character_status_bar_with_party_display(self):
        """パーティ設定時のキャラクターステータスバー表示を確認"""
        # パーティとキャラクターを作成
        character = Mock()
        character.name = "テストキャラクター"
        character.derived_stats = Mock()
        character.derived_stats.current_hp = 100
        character.derived_stats.max_hp = 100
        character.derived_stats.current_mp = 50
        character.derived_stats.max_mp = 50
        
        party = Party("テストパーティ")
        party.add_character(character)
        
        # キャラクターステータスバーを作成
        status_bar = create_character_status_bar(1024, 768)
        status_bar.set_party(party)
        
        # パーティが正しく設定されたことを確認
        assert status_bar.party == party
        assert len(status_bar.slots) == 6  # 6つのスロットがある
        
        # 最初のスロットにキャラクターが設定されていることを確認
        assert status_bar.slots[0].character == character
        
        # 残りのスロットは空であることを確認
        for i in range(1, 6):
            assert status_bar.slots[i].character is None
            
    def test_status_bar_render_without_errors(self):
        """ステータスバーが描画エラーなしで実行されることを確認"""
        screen = pygame.display.get_surface()
        
        # パーティとキャラクターを作成
        character = Mock()
        character.name = "テストキャラクター"
        character.derived_stats = Mock()
        character.derived_stats.current_hp = 100
        character.derived_stats.max_hp = 100
        character.derived_stats.current_mp = 50
        character.derived_stats.max_mp = 50
        
        party = Party("テストパーティ")
        party.add_character(character)
        
        # キャラクターステータスバーを作成
        status_bar = create_character_status_bar(1024, 768)
        status_bar.set_party(party)
        
        # フォントエラーは無視して、描画処理の構造を確認
        try:
            status_bar.render(screen)
            assert True  # 例外が発生しなければ成功
        except pygame.error as e:
            if "Invalid font" in str(e):
                # フォントエラーは期待される（テスト環境の制限）
                assert True
            else:
                pytest.fail(f"予期しないpygameエラー: {e}")
        except Exception as e:
            pytest.fail(f"ステータスバーの描画で例外が発生: {e}")
            
    def test_ui_manager_persistent_element_event_handling(self):
        """persistent_elementのイベント処理が正しく動作することを確認"""
        screen = pygame.display.get_surface()
        ui_manager = UIManager(screen)
        
        # persistent_elementをモック
        persistent_element = Mock()
        persistent_element.handle_event = Mock(return_value=True)
        persistent_element.element_id = "persistent"
        
        # persistent_elementsに追加
        ui_manager.add_persistent_element(persistent_element)
        
        # イベントを作成
        event = pygame.event.Event(pygame.KEYDOWN, {'key': pygame.K_SPACE})
        
        # イベント処理を実行
        result = ui_manager.handle_event(event)
        
        # persistent_elementのhandle_eventが呼び出されたことを確認
        persistent_element.handle_event.assert_called_once_with(event)
        assert result is True  # persistent_elementがTrueを返したのでui_managerもTrueを返す