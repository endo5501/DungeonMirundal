#!/usr/bin/env python3
"""教会メニュー項目のテスト"""

import pytest
import pygame
from unittest.mock import Mock, patch
from src.overworld.facilities.temple import Temple
from src.ui.base_ui_pygame import UIMenu


class TestTempleMenuItems:
    """教会メニュー項目のテスト"""
    
    def setup_method(self):
        """テスト前の初期化"""
        pygame.init()
        self.temple = Temple()
        
    def teardown_method(self):
        """テスト後のクリーンアップ"""
        if pygame.get_init():
            pygame.quit()
    
    def test_temple_menu_items_no_donation(self):
        """教会メニューに寄付が含まれていないことを確認"""
        # メニューを作成
        menu = UIMenu("test_temple_menu", "教会")
        
        # 教会固有のメニュー項目を設定
        self.temple._setup_menu_items(menu)
        
        # メニュー項目を確認
        menu_texts = [element.text for element in menu.elements if hasattr(element, 'text')]
        
        # 期待されるメニュー項目
        assert "蘇生サービス" in menu_texts
        assert "祝福サービス" in menu_texts
        assert "神父と話す" in menu_texts
        assert "祈祷書購入" in menu_texts
        
        # 寄付メニューが含まれていないことを確認
        assert "寄付をする" not in menu_texts
        
        # メニュー項目数を確認（蘇生、祝福、神父と話す、祈祷書購入の4つ）
        assert len(menu.elements) == 4
    
    def test_temple_has_no_donation_methods(self):
        """教会クラスに寄付関連メソッドが存在しないことを確認"""
        # 寄付関連メソッドが削除されていることを確認
        assert not hasattr(self.temple, '_show_donation_menu')
        assert not hasattr(self.temple, '_make_donation')
    
    def test_temple_menu_callback_functions(self):
        """教会メニューのコールバック関数が正しく設定されていることを確認"""
        menu = UIMenu("test_temple_menu", "教会")
        
        # メニュー項目を設定
        self.temple._setup_menu_items(menu)
        
        # 各メニュー項目のコールバックを確認
        assert len(menu.elements) == 4
        
        # 蘇生サービスのコールバック
        assert menu.elements[0].on_click == self.temple._show_resurrection_menu
        
        # 祝福サービスのコールバック
        assert menu.elements[1].on_click == self.temple._show_blessing_menu
        
        # 神父と話すのコールバック
        assert menu.elements[2].on_click == self.temple._talk_to_priest
        
        # 祈祷書購入のコールバック
        assert menu.elements[3].on_click == self.temple._show_prayerbook_shop
    
    def test_temple_service_costs_no_donation(self):
        """教会のサービス料金に寄付関連の項目がないことを確認"""
        # サービス料金が定義されている
        assert hasattr(self.temple, 'service_costs')
        
        # 寄付関連の料金設定がないことを確認
        assert 'donation' not in self.temple.service_costs
        
        # 通常のサービス料金は存在する
        assert 'resurrection' in self.temple.service_costs
        assert 'blessing' in self.temple.service_costs
        assert 'ash_restoration' in self.temple.service_costs


if __name__ == "__main__":
    pytest.main([__file__, "-v"])