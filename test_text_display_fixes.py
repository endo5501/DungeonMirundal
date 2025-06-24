#!/usr/bin/env python3
"""テキスト表示問題の修正テスト"""

import pytest
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from unittest.mock import Mock, patch
from src.overworld.base_facility import BaseFacility
from src.overworld.facilities.guild import AdventurersGuild
from src.overworld.facilities.shop import Shop
from src.overworld.facilities.inn import Inn
from src.utils.logger import logger

class TestFacility(BaseFacility):
    """テスト用の施設クラス"""
    
    def _setup_menu_items(self, menu):
        """テスト用のメニューアイテム設定"""
        pass
    
    def _on_enter(self):
        """施設入場時の処理"""
        pass
    
    def _on_exit(self):
        """施設退場時の処理"""
        pass

class TestTextDisplayFixes:
    """テキスト表示問題の修正テスト"""
    
    def setup_method(self):
        """テスト前の初期化"""
        from src.overworld.base_facility import FacilityType
        self.base_facility = TestFacility("test_facility", FacilityType.SHOP, "facility.test_facility")
        self.guild = AdventurersGuild()
        self.shop = Shop()
        self.inn = Inn()
    
    def test_show_dialog_auto_sizing(self):
        """_show_dialogメソッドのテキスト量に応じた自動サイズ調整をテスト"""
        # モックUIマネージャーを設定
        with patch('src.overworld.base_facility.ui_manager') as mock_ui_manager:
            mock_ui_manager.hide_dialog = Mock()
            mock_ui_manager.add_dialog = Mock()
            mock_ui_manager.show_dialog = Mock()
            
            # 短いメッセージの場合
            short_message = "短いメッセージ"
            self.base_facility._show_dialog("test_short", "テスト", short_message)
            
            # UIDialogが適切なサイズで作成されることを確認
            assert self.base_facility.current_dialog is not None
            assert self.base_facility.current_dialog.rect.width == 500  # デフォルト幅
            assert self.base_facility.current_dialog.rect.height >= 300  # 最小高さ
            
            # 長いメッセージの場合
            long_message = "とても長いメッセージです。" * 20 + "\n" * 10
            self.base_facility._show_dialog("test_long", "テスト", long_message)
            
            # より大きなサイズで作成されることを確認
            assert self.base_facility.current_dialog.rect.width >= 600  # より大きな幅
            assert self.base_facility.current_dialog.rect.height >= 400  # より大きな高さ
    
    def test_show_dialog_custom_sizing(self):
        """_show_dialogメソッドのカスタムサイズ指定をテスト"""
        with patch('src.overworld.base_facility.ui_manager') as mock_ui_manager:
            mock_ui_manager.hide_dialog = Mock()
            mock_ui_manager.add_dialog = Mock()
            mock_ui_manager.show_dialog = Mock()
            
            # カスタムサイズを指定
            custom_width = 800
            custom_height = 600
            
            self.base_facility._show_dialog(
                "test_custom", 
                "テスト", 
                "カスタムサイズメッセージ",
                width=custom_width,
                height=custom_height
            )
            
            # 指定されたサイズで作成されることを確認
            assert self.base_facility.current_dialog.rect.width == custom_width
            assert self.base_facility.current_dialog.rect.height == custom_height
    
    def test_guild_current_formation_dialog_size(self):
        """冒険者ギルドのパーティ編成確認ダイアログのサイズをテスト"""
        with patch('src.overworld.base_facility.ui_manager') as mock_ui_manager:
            mock_ui_manager.hide_dialog = Mock()
            mock_ui_manager.add_dialog = Mock()
            mock_ui_manager.show_dialog = Mock()
            
            # モックパーティを設定
            from src.character.party import Party
            mock_party = Mock(spec=Party)
            mock_party.characters = {}
            self.guild.current_party = mock_party
            
            # パーティ編成フォーマッターをモック
            with patch.object(self.guild, '_format_party_formation', return_value="テストパーティ編成"):
                self.guild._show_current_formation()
                
                # 適切なサイズで作成されることを確認
                assert self.guild.current_dialog is not None
                assert self.guild.current_dialog.rect.width == 700
                assert self.guild.current_dialog.rect.height == 450
    
    def test_guild_character_list_dialog_size(self):
        """冒険者ギルドのキャラクター一覧ダイアログのサイズをテスト"""
        with patch('src.overworld.base_facility.ui_manager') as mock_ui_manager:
            mock_ui_manager.hide_dialog = Mock()
            mock_ui_manager.add_dialog = Mock()
            mock_ui_manager.show_dialog = Mock()
            
            # モックキャラクターとパーティを設定
            from src.character.party import Party
            mock_party = Mock(spec=Party)
            mock_party.characters = {}
            self.guild.current_party = mock_party
            
            # モックキャラクターを作成
            mock_char = Mock()
            mock_char.character_id = "test_char_1"
            mock_char.name = "テストキャラ"
            mock_char.experience = Mock()
            mock_char.experience.level = 1
            mock_char.get_race_name = Mock(return_value="人間")
            mock_char.get_class_name = Mock(return_value="戦士")
            mock_char.derived_stats = Mock()
            mock_char.derived_stats.current_hp = 10
            mock_char.derived_stats.max_hp = 10
            mock_char.derived_stats.current_mp = 5
            mock_char.derived_stats.max_mp = 5
            
            self.guild.created_characters = [mock_char]
            
            self.guild._show_character_list()
            
            # 適切なサイズで作成されることを確認
            assert self.guild.current_dialog is not None
            assert self.guild.current_dialog.rect.width == 750
            assert self.guild.current_dialog.rect.height == 500
    
    def test_shop_inventory_dialog_size(self):
        """商店の在庫確認ダイアログのサイズをテスト"""
        with patch('src.overworld.base_facility.ui_manager') as mock_ui_manager:
            mock_ui_manager.hide_dialog = Mock()
            mock_ui_manager.add_dialog = Mock()
            mock_ui_manager.show_dialog = Mock()
            
            # モック在庫を設定
            self.shop.inventory = []
            
            self.shop._show_inventory()
            
            # 適切なサイズで作成されることを確認
            assert self.shop.current_dialog is not None
            assert self.shop.current_dialog.rect.width == 700
            assert self.shop.current_dialog.rect.height == 450
    
    def test_inn_innkeeper_dialog_size(self):
        """宿屋の主人との会話ダイアログのサイズをテスト"""
        with patch('src.overworld.base_facility.ui_manager') as mock_ui_manager:
            mock_ui_manager.hide_dialog = Mock()
            mock_ui_manager.add_dialog = Mock()
            mock_ui_manager.show_dialog = Mock()
            
            # 旧システムを使用するように設定
            self.inn.use_new_menu_system = False
            
            self.inn._talk_to_innkeeper()
            
            # 適切なサイズで作成されることを確認
            assert self.inn.current_dialog is not None
            assert self.inn.current_dialog.rect.width == 550
            assert self.inn.current_dialog.rect.height == 350
    
    def test_shop_shopkeeper_dialog_size(self):
        """商店の主人との会話ダイアログのサイズをテスト"""
        with patch('src.overworld.base_facility.ui_manager') as mock_ui_manager:
            mock_ui_manager.hide_dialog = Mock()
            mock_ui_manager.add_dialog = Mock()
            mock_ui_manager.show_dialog = Mock()
            
            self.shop._talk_to_shopkeeper()
            
            # 適切なサイズで作成されることを確認
            assert self.shop.current_dialog is not None
            assert self.shop.current_dialog.rect.width == 550
            assert self.shop.current_dialog.rect.height == 350
    
    def test_dialog_sizing_calculation_logic(self):
        """ダイアログサイズ計算ロジックのテスト"""
        with patch('src.overworld.base_facility.ui_manager') as mock_ui_manager:
            mock_ui_manager.hide_dialog = Mock()
            mock_ui_manager.add_dialog = Mock()
            mock_ui_manager.show_dialog = Mock()
            
            # 改行の多いメッセージ
            multi_line_message = "\n".join([f"行 {i}" for i in range(20)])
            self.base_facility._show_dialog("test_multiline", "テスト", multi_line_message)
            
            # 行数に応じた高さ調整が行われることを確認
            assert self.base_facility.current_dialog.rect.height >= 500
            
            # 非常に長い1行メッセージ
            very_long_message = "非常に長いメッセージです。" * 50
            self.base_facility._show_dialog("test_verylong", "テスト", very_long_message)
            
            # メッセージ長に応じた幅調整が行われることを確認
            assert self.base_facility.current_dialog.rect.width >= 700

if __name__ == "__main__":
    pytest.main([__file__, "-v"])