"""魔術書/祈祷書リスト型UI変更のテスト"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import pygame
from src.overworld.facilities.magic_guild import MagicGuild
from src.overworld.facilities.temple import Temple
from src.ui.selection_list_ui import ItemSelectionList
from src.character.party import Party
from src.character.character import Character
from src.items.item import Item, ItemType


class TestSpellBookListUI(unittest.TestCase):
    """魔術書/祈祷書リスト型UIのテスト"""
    
    def setUp(self):
        """テストの準備"""
        pygame.init()
        
        # 魔術ギルドのインスタンス作成
        self.magic_guild = MagicGuild()
        
        # 神殿のインスタンス作成
        self.temple = Temple()
        
        # モックパーティの作成
        self.mock_party = Mock(spec=Party)
        self.mock_party.name = "テストパーティ"
        self.mock_party.gold = 1000
        
        # 施設にパーティを設定
        self.magic_guild.current_party = self.mock_party
        self.temple.current_party = self.mock_party
    
    def tearDown(self):
        """テストの後処理"""
        pygame.quit()
    
    @patch('src.overworld.facilities.magic_guild.ui_manager')
    @patch('src.overworld.facilities.magic_guild.ItemSelectionList')
    def test_magic_guild_uses_item_selection_list(self, mock_item_selection_list, mock_ui_manager):
        """魔術ギルドがItemSelectionListを使用することをテスト"""
        # pygame_gui_managerをモック
        mock_ui_manager.pygame_gui_manager = Mock()
        
        # ItemSelectionListのインスタンスをモック
        mock_instance = Mock()
        mock_item_selection_list.return_value = mock_instance
        
        # _check_pygame_gui_managerメソッドをモック
        with patch.object(self.magic_guild, '_check_pygame_gui_manager', return_value=True):
            # 魔術書購入メニューを表示
            self.magic_guild._show_spellbook_shop_menu()
            
            # ItemSelectionListが作成されることを確認
            mock_item_selection_list.assert_called_once()
            assert hasattr(self.magic_guild, 'spellbook_selection_list')
            assert self.magic_guild.spellbook_selection_list is mock_instance
    
    @patch('src.overworld.facilities.temple.ui_manager')
    @patch('src.overworld.facilities.temple.ItemSelectionList')
    @patch('src.overworld.facilities.temple.item_manager')
    def test_temple_uses_item_selection_list(self, mock_item_manager, mock_item_selection_list, mock_ui_manager):
        """神殿がItemSelectionListを使用することをテスト"""
        # pygame_gui_managerをモック
        mock_ui_manager.pygame_gui_manager = Mock()
        
        # ItemSelectionListのインスタンスをモック
        mock_instance = Mock()
        mock_item_selection_list.return_value = mock_instance
        
        # 祈祷書アイテムをモック
        mock_item = Mock(spec=Item)
        mock_item.get_name.return_value = "テスト祈祷書"
        mock_item.price = 500
        mock_item_manager.get_items_by_type.return_value = [mock_item]
        
        # _check_pygame_gui_managerメソッドをモック
        with patch.object(self.temple, '_check_pygame_gui_manager', return_value=True):
            # 祈祷書購入メニューを表示
            self.temple._show_prayerbook_shop()
            
            # ItemSelectionListが作成されることを確認
            mock_item_selection_list.assert_called_once()
            assert hasattr(self.temple, 'prayerbook_selection_list')
            assert self.temple.prayerbook_selection_list is mock_instance
    
    def test_magic_guild_spellbook_selection_callback(self):
        """魔術ギルドの魔術書選択コールバックのテスト"""
        mock_spellbook = {
            'name': 'ファイア魔術書',
            'price': 300,
            'description': 'テスト魔術書'
        }
        
        # _hide_spellbook_selection_listと_show_spellbook_detailsをモック
        with patch.object(self.magic_guild, '_hide_spellbook_selection_list') as mock_hide, \
             patch.object(self.magic_guild, '_show_spellbook_details_from_dict') as mock_show_details:
            
            # コールバックを実行
            self.magic_guild._on_spellbook_selected_for_purchase(mock_spellbook)
            
            # 適切なメソッドが呼ばれることを確認
            mock_hide.assert_called_once()
            mock_show_details.assert_called_once_with(mock_spellbook)
    
    def test_temple_prayerbook_selection_callback(self):
        """神殿の祈祷書選択コールバックのテスト"""
        mock_item = Mock(spec=Item)
        mock_item.get_name.return_value = "テスト祈祷書"
        
        # _hide_prayerbook_selection_listと_show_prayerbook_detailsをモック
        with patch.object(self.temple, '_hide_prayerbook_selection_list') as mock_hide, \
             patch.object(self.temple, '_show_prayerbook_details') as mock_show_details:
            
            # コールバックを実行
            self.temple._on_prayerbook_selected_for_purchase(mock_item)
            
            # 適切なメソッドが呼ばれることを確認
            mock_hide.assert_called_once()
            mock_show_details.assert_called_once_with(mock_item)
    
    def test_magic_guild_hide_selection_list(self):
        """魔術ギルドの選択リスト非表示のテスト"""
        # モックの選択リストを作成
        mock_selection_list = Mock()
        self.magic_guild.spellbook_selection_list = mock_selection_list
        
        # 選択リストを非表示
        self.magic_guild._hide_spellbook_selection_list()
        
        # 適切なメソッドが呼ばれることを確認
        mock_selection_list.hide.assert_called_once()
        mock_selection_list.kill.assert_called_once()
        assert self.magic_guild.spellbook_selection_list is None
    
    def test_temple_hide_selection_list(self):
        """神殿の選択リスト非表示のテスト"""
        # モックの選択リストを作成
        mock_selection_list = Mock()
        self.temple.prayerbook_selection_list = mock_selection_list
        
        # 選択リストを非表示
        self.temple._hide_prayerbook_selection_list()
        
        # 適切なメソッドが呼ばれることを確認
        mock_selection_list.hide.assert_called_once()
        mock_selection_list.kill.assert_called_once()
        assert self.temple.prayerbook_selection_list is None
    
    def test_magic_guild_handle_ui_selection_events(self):
        """魔術ギルドのUIイベント処理のテスト"""
        # モックの選択リストを作成
        mock_selection_list = Mock()
        mock_selection_list.handle_event.return_value = True
        self.magic_guild.spellbook_selection_list = mock_selection_list
        
        # モックイベントを作成
        mock_event = Mock()
        
        # イベント処理を実行
        result = self.magic_guild._handle_ui_selection_events(mock_event)
        
        # handle_eventが呼ばれ、Trueが返されることを確認
        mock_selection_list.handle_event.assert_called_once_with(mock_event)
        assert result is True
    
    def test_temple_handle_ui_selection_events(self):
        """神殿のUIイベント処理のテスト"""
        # モックの選択リストを作成
        mock_selection_list = Mock()
        mock_selection_list.handle_event.return_value = True
        self.temple.prayerbook_selection_list = mock_selection_list
        
        # モックイベントを作成
        mock_event = Mock()
        
        # イベント処理を実行
        result = self.temple._handle_ui_selection_events(mock_event)
        
        # handle_eventが呼ばれ、Trueが返されることを確認
        mock_selection_list.handle_event.assert_called_once_with(mock_event)
        assert result is True
    
    def test_magic_guild_handle_ui_selection_events_no_list(self):
        """魔術ギルドでリストがない場合のUIイベント処理のテスト"""
        # 選択リストが存在しない状態
        self.magic_guild.spellbook_selection_list = None
        
        # モックイベントを作成
        mock_event = Mock()
        
        # イベント処理を実行
        result = self.magic_guild._handle_ui_selection_events(mock_event)
        
        # Falseが返されることを確認
        assert result is False


if __name__ == '__main__':
    unittest.main()