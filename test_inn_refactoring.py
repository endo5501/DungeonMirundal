"""宿屋リファクタリングのテスト"""

import pytest
import pygame
from unittest.mock import Mock, patch

from src.overworld.facilities.inn_refactored import Inn
from src.character.party import Party
from src.character.character import Character
from src.core.config_manager import config_manager


class TestInnRefactoring:
    """宿屋リファクタリングのテスト"""
    
    def setup_method(self):
        """テストセットアップ"""
        pygame.init()
        
        # パーティとキャラクターのモック
        self.mock_party = Mock(spec=Party)
        self.mock_character = Mock(spec=Character)
        self.mock_character.name = "テスト戦士"
        self.mock_character.character_class = "warrior"
        
        self.mock_party.get_all_characters.return_value = [self.mock_character]
        self.mock_party.name = "テストパーティ"
        
        # 宿屋インスタンス作成
        self.inn = Inn()
        
        # config_managerのモック設定
        self.config_texts = {
            "facility.inn": "宿屋",
            "inn.rumors.title": "酒場の噂話",
            "inn.rumors.dungeon_title": "ダンジョンの噂",
            "inn.rumors.dungeon_message": "恐ろしいダンジョンがあるという話だ...",
            "inn.innkeeper.title": "宿屋の主人",
            "inn.innkeeper.conversation.adventure_title": "冒険について",
            "inn.innkeeper.conversation.adventure_message": "冒険者よ、気をつけて旅をするんだ。",
            "inn.travel_info.title": "旅の情報",
            "inn.travel_info.content": "旅には気をつけて、しっかりと準備をしてから出発しよう。",
            "menu.back": "戻る",
            "common.back": "戻る"
        }
    
    def teardown_method(self):
        """テスト後処理"""
        if pygame.get_init():
            pygame.quit()
    
    def test_inn_initialization(self):
        """宿屋の初期化をテスト"""
        assert self.inn.facility_id == "inn"
        assert self.inn.facility_type.value == "inn"
        assert not self.inn.is_active
    
    def test_menu_setup(self):
        """メニューセットアップをテスト"""
        from src.ui.base_ui_pygame import UIMenu
        
        menu = UIMenu("test_menu", "テストメニュー")
        self.inn._setup_menu_items(menu)
        
        # メニュー項目が追加されていることを確認
        assert len(menu.elements) > 0
        
        # 各メニュー項目の存在確認
        menu_texts = [element.text for element in menu.elements if hasattr(element, 'text')]
        expected_menus = ["冒険の準備", "アイテム預かり", "宿屋の主人と話す", "旅の情報を聞く", "酒場の噂話", "パーティ名を変更"]
        
        for expected_menu in expected_menus:
            assert any(expected_menu in text for text in menu_texts)
    
    def test_enter_exit_flow(self):
        """入場・退場フローをテスト"""
        # 入場前の状態確認
        assert not self.inn.is_active
        assert self.inn.current_party is None
        
        # UIマネージャーをモック
        mock_ui_manager = Mock()
        
        with patch('src.overworld.base_facility.ui_manager', mock_ui_manager):
            # 入場
            result = self.inn.enter(self.mock_party)
            assert result is True
            assert self.inn.is_active
            assert self.inn.current_party == self.mock_party
        
        # 退場
        result = self.inn.exit()
        assert result is True
        assert not self.inn.is_active
        assert self.inn.current_party is None
    
    def test_innkeeper_conversation(self):
        """宿屋の主人会話をテスト"""
        with patch.object(config_manager, 'get_text') as mock_get_text:
            mock_get_text.side_effect = lambda key: self.config_texts.get(key, f"未設定({key})")
            
            # show_information_dialogをモック
            self.inn.show_information_dialog = Mock(return_value=True)
            
            # 会話実行
            self.inn._talk_to_innkeeper()
            
            # ダイアログが表示されることを確認
            self.inn.show_information_dialog.assert_called_once()
            
            # 引数の確認
            call_args = self.inn.show_information_dialog.call_args
            assert len(call_args[0]) >= 2
            assert "宿屋の主人" in call_args[0][0]
            assert len(call_args[0][1]) > 0
    
    def test_travel_info_display(self):
        """旅の情報表示をテスト"""
        with patch.object(config_manager, 'get_text') as mock_get_text:
            mock_get_text.side_effect = lambda key: self.config_texts.get(key, f"未設定({key})")
            
            # show_information_dialogをモック
            self.inn.show_information_dialog = Mock(return_value=True)
            
            # 旅の情報表示実行
            self.inn._show_travel_info()
            
            # ダイアログが表示されることを確認
            self.inn.show_information_dialog.assert_called_once()
            
            # 引数の確認
            call_args = self.inn.show_information_dialog.call_args
            assert call_args[0][0] == "旅の情報"
            assert "旅には気をつけて" in call_args[0][1]
    
    def test_tavern_rumors_display(self):
        """酒場の噂話表示をテスト"""
        with patch.object(config_manager, 'get_text') as mock_get_text:
            mock_get_text.side_effect = lambda key: self.config_texts.get(key, f"未設定({key})")
            
            # show_information_dialogをモック
            self.inn.show_information_dialog = Mock(return_value=True)
            
            # 噂話表示実行
            self.inn._show_tavern_rumors()
            
            # ダイアログが表示されることを確認
            self.inn.show_information_dialog.assert_called_once()
            
            # 引数の確認
            call_args = self.inn.show_information_dialog.call_args
            assert "酒場の噂話" in call_args[0][0]
            assert len(call_args[0][1]) > 0
    
    def test_party_name_validation(self):
        """パーティ名バリデーションをテスト"""
        # 正常な名前
        assert self.inn._validate_party_name("勇者パーティ") == "勇者パーティ"
        
        # 空文字列
        with patch.object(config_manager, 'get_text') as mock_get_text:
            mock_get_text.return_value = "デフォルト名"
            assert self.inn._validate_party_name("") == "デフォルト名"
            assert self.inn._validate_party_name("   ") == "デフォルト名"
        
        # 長すぎる名前
        long_name = "あ" * 50
        assert len(self.inn._validate_party_name(long_name)) == 30
        
        # 危険な文字の除去
        dangerous_name = "パーティ<script>alert('test')</script>"
        safe_name = self.inn._validate_party_name(dangerous_name)
        assert "<script>" not in safe_name
        assert "alert" not in safe_name
        assert "script" not in safe_name
    
    def test_adventure_preparation_menu(self):
        """冒険準備メニューをテスト"""
        self.inn.current_party = self.mock_party
        
        # show_submenuをモック
        self.inn.show_submenu = Mock(return_value=True)
        
        # 冒険準備メニュー実行
        self.inn._show_adventure_preparation()
        
        # サブメニューが表示されることを確認
        self.inn.show_submenu.assert_called_once()
        
        # メニューの内容確認
        call_args = self.inn.show_submenu.call_args
        menu = call_args[0][0]
        assert menu.title == "冒険の準備"
        assert len(menu.elements) > 0
    
    def test_item_organization_without_party(self):
        """パーティなしでのアイテム整理をテスト"""
        # パーティが設定されていない状態
        self.inn.current_party = None
        
        # アイテム整理実行（エラーが発生しないことを確認）
        self.inn._show_item_organization()
        
        # 特に例外が発生しないことを確認
        assert True
    
    def test_cleanup_on_exit(self):
        """退場時のクリーンアップをテスト"""
        # storage_view_listを設定
        self.inn.storage_view_list = Mock()
        
        # 退場処理実行
        self.inn._on_exit()
        
        # クリーンアップが実行されることを確認
        assert self.inn.storage_view_list is None or self.inn.storage_view_list.hide.called
    
    def test_refactored_code_size(self):
        """リファクタリング後のコードサイズをテスト"""
        import inspect
        
        # メソッド数を確認
        methods = [method for method in dir(self.inn) if callable(getattr(self.inn, method)) and not method.startswith('__')]
        
        # リファクタリング前（89個）と比較して大幅に減少していることを確認
        # BaseFacilityから継承されたメソッドも含まれるため、65個程度が妥当
        assert len(methods) < 70, f"メソッド数が多すぎます: {len(methods)}"
        
        # ファイルサイズの確認（行数）
        source_lines = inspect.getsourcelines(Inn)[0]
        line_count = len(source_lines)
        
        # リファクタリング前（2125行）と比較して大幅に減少していることを確認
        assert line_count < 500, f"行数が多すぎます: {line_count}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])