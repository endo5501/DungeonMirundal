#!/usr/bin/env python3
"""商店メニュー項目のテスト"""

import pytest
import pygame
from unittest.mock import Mock, patch
from src.overworld.facilities.shop import Shop
from src.ui.base_ui_pygame import UIMenu


class TestShopMenuItems:
    """商店メニュー項目のテスト"""
    
    def setup_method(self):
        """テスト前の初期化"""
        pygame.init()
        self.shop = Shop()
        
    def teardown_method(self):
        """テスト後のクリーンアップ"""
        if pygame.get_init():
            pygame.quit()
    
    @patch('src.overworld.facilities.shop.config_manager')
    def test_shop_menu_items_no_inventory_check(self, mock_config_manager):
        """商店メニューに在庫確認が含まれていないことを確認"""
        # テキスト取得のモック
        mock_config_manager.get_text.side_effect = lambda key: {
            "shop.menu.buy_items": "商品を購入する",
            "shop.menu.sell_items": "商品を売却する",
            "shop.menu.talk_shopkeeper": "店主と話す",
            "shop.menu.check_inventory": "在庫を確認する",  # 削除されたメニュー
        }.get(key, key)
        
        # メニューを作成
        menu = UIMenu("test_shop_menu", "商店")
        
        # 商店固有のメニュー項目を設定
        self.shop._setup_menu_items(menu)
        
        # メニュー項目を確認
        menu_texts = [element.text for element in menu.elements if hasattr(element, 'text')]
        
        # 期待されるメニュー項目
        assert "商品を購入する" in menu_texts
        assert "商品を売却する" in menu_texts
        assert "店主と話す" in menu_texts
        
        # 在庫確認メニューが含まれていないことを確認
        assert "在庫を確認する" not in menu_texts
        
        # メニュー項目数を確認（購入、売却、店主と話すの3つ）
        assert len(menu.elements) == 3
    
    def test_shop_has_no_show_inventory_method(self):
        """商店クラスに_show_inventoryメソッドが存在しないことを確認"""
        # _show_inventoryメソッドが削除されていることを確認
        assert not hasattr(self.shop, '_show_inventory')
    
    def test_shop_menu_callback_functions(self):
        """商店メニューのコールバック関数が正しく設定されていることを確認"""
        menu = UIMenu("test_shop_menu", "商店")
        
        # モックでテキストを設定
        with patch('src.overworld.facilities.shop.config_manager') as mock_config:
            mock_config.get_text.return_value = "テストメニュー"
            
            # メニュー項目を設定
            self.shop._setup_menu_items(menu)
            
            # 各メニュー項目のコールバックを確認
            assert len(menu.elements) == 3
            
            # 購入メニューのコールバック
            assert menu.elements[0].on_click == self.shop._show_buy_menu
            
            # 売却メニューのコールバック
            assert menu.elements[1].on_click == self.shop._show_sell_menu
            
            # 店主と話すのコールバック
            assert menu.elements[2].on_click == self.shop._talk_to_shopkeeper


if __name__ == "__main__":
    pytest.main([__file__, "-v"])