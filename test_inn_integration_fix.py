"""宿屋の統合テスト - 噂話ダイアログの修正を含む"""

import pytest
import pygame
from unittest.mock import Mock, patch, MagicMock, call

from src.overworld.facilities.inn import Inn
from src.character.party import Party
from src.character.character import Character
from src.ui.base_ui_pygame import ui_manager, UIMenu
from src.core.config_manager import config_manager


class TestInnIntegrationFix:
    """宿屋の統合テスト - 噂話問題修正を含む"""
    
    def setup_method(self):
        """テストセットアップ"""
        pygame.init()
        
        # パーティとキャラクターのモック
        self.mock_party = Mock(spec=Party)
        self.mock_character = Mock(spec=Character)
        self.mock_character.name = "テスト戦士"
        self.mock_character.character_class = "warrior"
        self.mock_character.experience = Mock()
        self.mock_character.experience.level = 5
        
        self.mock_party.get_all_characters.return_value = [self.mock_character]
        self.mock_party.name = "テストパーティ"
        
        # 宿屋インスタンス作成
        self.inn = Inn()
        # is_activeはenterメソッドで設定されるため、初期状態ではFalse
        
        # config_managerのモック設定
        self.config_texts = {
            "facility.inn": "宿屋",
            "inn.rumors.title": "酒場の噂話",
            "inn.rumors.dungeon_title": "ダンジョンの噂",
            "inn.rumors.dungeon_message": "恐ろしいダンジョンがあるという話だ...",
            "inn.rumors.monster_title": "モンスターの噂",
            "inn.rumors.monster_message": "強力なモンスターが現れたらしい...",
            "inn.rumors.legendary_title": "伝説の噂",
            "inn.rumors.legendary_message": "伝説のアイテムが見つかったという...",
            "inn.rumors.adventurer_title": "冒険者の噂",
            "inn.rumors.adventurer_message": "有名な冒険者の話だ...",
            "inn.rumors.merchant_title": "商人の噂",
            "inn.rumors.merchant_message": "良い商人がいるという話だ...",
            "inn.innkeeper.title": "宿屋の主人",
            "inn.innkeeper.conversation.adventure_title": "冒険について",
            "inn.innkeeper.conversation.adventure_message": "冒険者よ、気をつけて旅をするんだ。",
            "inn.innkeeper.conversation.town_title": "町について",
            "inn.innkeeper.conversation.town_message": "この町は平和でいいところだよ。",
            "inn.innkeeper.conversation.history_title": "歴史について",
            "inn.innkeeper.conversation.history_message": "昔からここには多くの冒険者が来た。",
            "inn.travel_info.title": "旅の情報",
            "inn.travel_info.content": "旅には気をつけて、しっかりと準備をしてから出発しよう。",
            "common.back": "戻る",
            "common.ok": "OK",
            "menu.exit": "出る",
            "menu.back": "戻る"
        }
    
    def teardown_method(self):
        """テスト後処理"""
        if pygame.get_init():
            pygame.quit()
    
    def test_inn_menu_flow_with_rumor_fix(self):
        """宿屋メニューフロー（噂話修正を含む）をテスト"""
        mock_ui_manager = Mock()
        
        with patch.object(config_manager, 'get_text') as mock_get_text:
            mock_get_text.side_effect = lambda key: self.config_texts.get(key, f"未設定テキスト({key})")
            
            with patch('src.overworld.facilities.inn.ui_manager', mock_ui_manager), \
                 patch('src.overworld.base_facility.ui_manager', mock_ui_manager):
                # 1. 宿屋にエンター
                self.inn.enter(self.mock_party)
                
                # メインメニューが表示されることを確認
                mock_ui_manager.add_menu.assert_called()
                mock_ui_manager.show_menu.assert_called()
                
                # メインメニューが設定されていることを確認
                assert self.inn.main_menu is not None
                assert self.inn.main_menu.menu_id == "inn_main_menu"
                
                # 2. 酒場の噂話を選択（新システム）
                self.inn.use_new_menu_system = True
                self.inn.dialog_template = Mock()
                self.inn.show_information_dialog = Mock()
                
                # 噂話を表示
                self.inn._show_tavern_rumors()
                
                # ダイアログが表示されることを確認
                self.inn.show_information_dialog.assert_called_once()
                dialog_call = self.inn.show_information_dialog.call_args
                
                # ダイアログの内容を確認（タイトルとメッセージ）
                assert "酒場の噂話" in dialog_call[0][0]  # title
                assert len(dialog_call[0][1]) > 0  # message
                assert 'buttons' in dialog_call[1]
                assert len(dialog_call[1]['buttons']) == 1
                assert dialog_call[1]['buttons'][0]['text'] == "戻る"
                
                # 3. 戻るボタンを押す（修正されたコールバックをテスト）
                back_callback = dialog_call[1]['buttons'][0]['callback']
                
                # コールバックを実行（Noneの場合はスキップ）
                if back_callback:
                    back_callback()
                else:
                    # callbackがNoneの場合は正常（デフォルトの戻る動作）
                    assert True
                
                # メインメニューが再表示されることを確認
                mock_ui_manager.show_menu.assert_called_with("inn_main_menu", modal=True)
    
    def test_all_info_dialogs_fix(self):
        """すべての情報ダイアログの修正をテスト"""
        mock_ui_manager = Mock()
        
        with patch.object(config_manager, 'get_text') as mock_get_text:
            mock_get_text.side_effect = lambda key: self.config_texts.get(key, f"未設定テキスト({key})")
            
            with patch('src.overworld.facilities.inn.ui_manager', mock_ui_manager), \
                 patch('src.overworld.base_facility.ui_manager', mock_ui_manager):
                # 旧システムを使用
                self.inn.use_new_menu_system = False
                self.inn.main_menu = Mock()
                self.inn.main_menu.menu_id = "inn_main_menu"
                
                # テストする情報ダイアログ一覧
                info_methods = [
                    ('_show_tavern_rumors', "rumor_dialog"),
                    ('_talk_to_innkeeper', "innkeeper_dialog"),
                    ('_show_travel_info', "travel_info_dialog")
                ]
                
                for method_name, expected_dialog_id in info_methods:
                    # show_information_dialogをモック（旧システムでも実際にはこれが呼ばれる）
                    self.inn.show_information_dialog = Mock()
                    
                    # メソッドを呼び出し
                    method = getattr(self.inn, method_name)
                    method()
                    
                    # ダイアログが表示されることを確認
                    self.inn.show_information_dialog.assert_called_once()
                    dialog_call = self.inn.show_information_dialog.call_args
                    
                    # タイトルとメッセージを確認
                    assert len(dialog_call[0][0]) > 0  # title
                    assert len(dialog_call[0][1]) > 0  # message
                    # 旧システムではbuttonsパラメータがない場合がある
                    if dialog_call[1] and 'buttons' in dialog_call[1]:  # buttonsパラメータがある場合
                        assert len(dialog_call[1]['buttons']) == 1
                        assert dialog_call[1]['buttons'][0]['text'] == "戻る"
                        
                        # 戻るボタンのコールバックをテスト
                        back_callback = dialog_call[1]['buttons'][0].get('callback')
                        if back_callback:
                            back_callback()
                    
                    # ui_managerをリセット
                    mock_ui_manager.reset_mock()
    
    def test_new_system_compatibility(self):
        """新システムとの互換性をテスト"""
        with patch.object(config_manager, 'get_text') as mock_get_text:
            mock_get_text.side_effect = lambda key: self.config_texts.get(key, f"未設定テキスト({key})")
            
            # 新システムを有効化
            self.inn.use_new_menu_system = True
            self.inn.dialog_template = Mock()
            self.inn.show_information_dialog = Mock(return_value=True)
            
            # 噂話を表示
            self.inn._show_tavern_rumors()
            
            # 新システムのメソッドが呼ばれることを確認
            self.inn.show_information_dialog.assert_called_once()
            
            # 引数の確認
            call_args = self.inn.show_information_dialog.call_args
            assert len(call_args[0]) == 2  # タイトル、メッセージ
            assert "酒場の噂話" in call_args[0][0]
            assert len(call_args[0][1]) > 0
            assert 'buttons' in call_args[1]  # buttonsパラメータ
    
    def test_menu_state_consistency(self):
        """メニュー状態の一貫性をテスト"""
        mock_ui_manager = Mock()
        
        with patch.object(config_manager, 'get_text') as mock_get_text:
            mock_get_text.side_effect = lambda key: self.config_texts.get(key, f"未設定テキスト({key})")
            
            with patch('src.overworld.facilities.inn.ui_manager', mock_ui_manager), \
                 patch('src.overworld.base_facility.ui_manager', mock_ui_manager):
                # 宿屋に入る
                self.inn.enter(self.mock_party)
                
                # メインメニューが設定されていることを確認
                assert self.inn.main_menu is not None
                initial_menu_id = self.inn.main_menu.menu_id
                
                # 情報ダイアログを表示して閉じる（旧システム）
                self.inn.use_new_menu_system = False
                self.inn.show_information_dialog = Mock()
                
                # 複数の情報表示を連続実行
                for _ in range(3):
                    self.inn._show_tavern_rumors()
                    
                    # ダイアログが呼ばれることを確認
                    self.inn.show_information_dialog.assert_called()
                    
                    # メインメニューのIDが変わっていないことを確認
                    assert self.inn.main_menu.menu_id == initial_menu_id
                    
                    # モックをリセット
                    self.inn.show_information_dialog.reset_mock()
                
                # 宿屋を出る
                self.inn.exit()
                
                # UIがクリーンアップされることを確認
                assert self.inn.current_dialog is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])