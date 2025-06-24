"""宿屋の酒場の噂話後にOKを押すとメニューが空になる問題の修正テスト（更新版）"""

import pytest
import pygame
from unittest.mock import Mock, patch, MagicMock

from src.overworld.facilities.inn import Inn
from src.character.party import Party
from src.character.character import Character
from src.ui.base_ui_pygame import ui_manager
from src.core.config_manager import config_manager


class TestInnTavernRumorsFix:
    """宿屋の噂話メニュー問題修正テスト"""
    
    def setup_method(self):
        """テストセットアップ"""
        pygame.init()
        
        # 必要なオブジェクトをモック
        self.mock_party = Mock(spec=Party)
        self.mock_character = Mock(spec=Character)
        self.mock_character.name = "テストキャラクター"
        self.mock_character.character_class = "warrior"
        self.mock_party.get_all_characters.return_value = [self.mock_character]
        
        # 宿屋インスタンスを作成
        self.inn = Inn()
        self.inn.current_party = self.mock_party
        self.inn.is_active = True
        
        # config_managerをモック
        with patch.object(config_manager, 'get_text') as mock_get_text:
            mock_get_text.return_value = "テストテキスト"
    
    def teardown_method(self):
        """テスト後処理"""
        if pygame.get_init():
            pygame.quit()
    
    def test_tavern_rumors_legacy_system_fix(self):
        """旧システムでの噂話ダイアログ修正をテスト"""
        # 旧システムを使用
        self.inn.use_new_menu_system = False
        
        # メインメニューを設定
        self.inn.main_menu = Mock()
        self.inn.main_menu.menu_id = "inn_main_menu"
        
        # mock_ui_managerを設定
        mock_ui_manager = Mock()
        
        with patch.object(config_manager, 'get_text') as mock_get_text:
            mock_get_text.side_effect = lambda key: {
                "inn.rumors.title": "酒場の噂話",
                "inn.rumors.dungeon_title": "ダンジョンの噂",
                "inn.rumors.dungeon_message": "深いダンジョンがあるらしい",
                "inn.rumors.monster_title": "モンスターの噂",
                "inn.rumors.monster_message": "強力なモンスターが出るらしい",
                "inn.rumors.legendary_title": "伝説の噂",
                "inn.rumors.legendary_message": "伝説のアイテムがあるらしい",
                "inn.rumors.adventurer_title": "冒険者の噂",
                "inn.rumors.adventurer_message": "有名な冒険者がいるらしい",
                "inn.rumors.merchant_title": "商人の噂",
                "inn.rumors.merchant_message": "良い商人がいるらしい",
                "common.back": "戻る"
            }.get(key, "テストテキスト")
            
            with patch('src.overworld.facilities.inn.ui_manager', mock_ui_manager):
                # _show_dialogメソッドをモック
                self.inn._show_dialog = Mock()
                
                # 噂話を表示
                self.inn._show_tavern_rumors()
                
                # _show_dialogが呼ばれたことを確認
                self.inn._show_dialog.assert_called_once()
                
                # ボタンのコールバック関数を取得してテスト
                call_args = self.inn._show_dialog.call_args
                button_callback = call_args[1]['buttons'][0]['command']
                
                # 実際のコールバックが _back_to_main_menu_from_tavern_rumors_dialog であることを確認
                assert button_callback == self.inn._back_to_main_menu_from_tavern_rumors_dialog
    
    def test_travel_info_legacy_system_fix(self):
        """旧システムでの旅の情報ダイアログ修正をテスト"""
        # 旧システムを使用
        self.inn.use_new_menu_system = False
        
        # メインメニューを設定
        self.inn.main_menu = Mock()
        self.inn.main_menu.menu_id = "inn_main_menu"
        
        mock_ui_manager = Mock()
        
        with patch.object(config_manager, 'get_text') as mock_get_text:
            mock_get_text.side_effect = lambda key: {
                "inn.travel_info.title": "旅の情報",
                "inn.travel_info.content": "旅に関する情報です",
                "common.back": "戻る"
            }.get(key, "テストテキスト")
            
            with patch('src.overworld.facilities.inn.ui_manager', mock_ui_manager):
                # _show_dialogメソッドをモック
                self.inn._show_dialog = Mock()
                
                # 旅の情報を表示
                self.inn._show_travel_info()
                
                # _show_dialogが呼ばれたことを確認
                self.inn._show_dialog.assert_called_once()
                
                # ボタンのコールバック関数を取得してテスト
                call_args = self.inn._show_dialog.call_args
                button_callback = call_args[1]['buttons'][0]['command']
                
                # 実際のコールバックが _back_to_main_menu_from_travel_info_dialog であることを確認
                assert button_callback == self.inn._back_to_main_menu_from_travel_info_dialog
    
    def test_innkeeper_conversation_legacy_system_fix(self):
        """旧システムでの宿屋の主人会話ダイアログ修正をテスト"""
        # 旧システムを使用
        self.inn.use_new_menu_system = False
        
        # メインメニューを設定
        self.inn.main_menu = Mock()
        self.inn.main_menu.menu_id = "inn_main_menu"
        
        mock_ui_manager = Mock()
        
        with patch.object(config_manager, 'get_text') as mock_get_text:
            mock_get_text.side_effect = lambda key: {
                "inn.innkeeper.title": "宿屋の主人",
                "inn.innkeeper.conversation.adventure_title": "冒険について",
                "inn.innkeeper.conversation.adventure_message": "冒険者の話です",
                "inn.innkeeper.conversation.town_title": "町について",
                "inn.innkeeper.conversation.town_message": "町の話です",
                "inn.innkeeper.conversation.history_title": "歴史について",
                "inn.innkeeper.conversation.history_message": "歴史の話です",
                "common.back": "戻る"
            }.get(key, "テストテキスト")
            
            with patch('src.overworld.facilities.inn.ui_manager', mock_ui_manager):
                # _show_dialogメソッドをモック
                self.inn._show_dialog = Mock()
                
                # 宿屋の主人会話を表示
                self.inn._talk_to_innkeeper()
                
                # _show_dialogが呼ばれたことを確認
                self.inn._show_dialog.assert_called_once()
                
                # ボタンのコールバック関数を取得してテスト
                call_args = self.inn._show_dialog.call_args
                button_callback = call_args[1]['buttons'][0]['command']
                
                # 実際のコールバックが _back_to_main_menu_from_innkeeper_dialog であることを確認
                assert button_callback == self.inn._back_to_main_menu_from_innkeeper_dialog
    
    def test_new_system_dialog_callbacks(self):
        """新システムでのダイアログコールバックをテスト"""
        # 新システムを有効化
        self.inn.use_new_menu_system = True
        self.inn.show_information_dialog = Mock(return_value=True)
        
        with patch.object(config_manager, 'get_text') as mock_get_text:
            mock_get_text.side_effect = lambda key: {
                "inn.rumors.title": "酒場の噂話",
                "inn.rumors.dungeon_title": "ダンジョンの噂",
                "inn.rumors.dungeon_message": "深いダンジョンがあるらしい",
                "inn.rumors.monster_title": "モンスターの噂",
                "inn.rumors.monster_message": "強力なモンスターが出るらしい",
                "inn.rumors.legendary_title": "伝説の噂",
                "inn.rumors.legendary_message": "伝説のアイテムがあるらしい",
                "inn.rumors.adventurer_title": "冒険者の噂",
                "inn.rumors.adventurer_message": "有名な冒険者がいるらしい",
                "inn.rumors.merchant_title": "商人の噂",
                "inn.rumors.merchant_message": "良い商人がいるらしい"
            }.get(key, "テストテキスト")
            
            # 噂話を表示
            self.inn._show_tavern_rumors()
            
            # show_information_dialogが適切な引数で呼ばれたことを確認
            self.inn.show_information_dialog.assert_called_once()
            
            # 3つの引数（タイトル、メッセージ、コールバック）で呼ばれたかチェック
            call_args = self.inn.show_information_dialog.call_args
            assert len(call_args[0]) == 3  # 引数が3つある
            assert "酒場の噂話" in call_args[0][0]  # タイトルに噂話が含まれる
            assert len(call_args[0][1]) > 0  # メッセージが空でない
            assert callable(call_args[0][2])  # コールバック関数が渡されている
    
    def test_base_facility_close_dialog_fix(self):
        """BaseFacilityの_close_dialog修正をテスト"""
        from src.overworld.base_facility import BaseFacility
        
        # テスト用のBaseFacility継承クラスを作成
        class TestFacility(BaseFacility):
            def _setup_menu_items(self, menu):
                pass
            def _on_enter(self):
                pass
            def _on_exit(self):
                pass
        
        facility = TestFacility("test", Mock(), "test_key")
        
        # current_dialogを設定
        facility.current_dialog = Mock()
        facility.current_dialog.dialog_id = "test_dialog"
        
        # main_menuを設定
        facility.main_menu = Mock()
        facility.main_menu.menu_id = "test_main_menu"
        
        # ui_managerがNoneの場合のテスト
        with patch('src.overworld.base_facility.ui_manager', None):
            # エラーが発生しないことを確認
            facility._close_dialog()
            
            # current_dialogがクリアされることを確認
            assert facility.current_dialog is None
        
        # ui_managerが有効な場合のテスト
        mock_ui_manager = Mock()
        with patch('src.overworld.base_facility.ui_manager', mock_ui_manager):
            # current_dialogを再設定
            facility.current_dialog = Mock()
            facility.current_dialog.dialog_id = "test_dialog2"
            
            facility._close_dialog()
            
            # ui_managerの適切なメソッドが呼ばれることを確認
            mock_ui_manager.hide_dialog.assert_called_with("test_dialog2")
            mock_ui_manager.show_menu.assert_called_with("test_main_menu", modal=True)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])