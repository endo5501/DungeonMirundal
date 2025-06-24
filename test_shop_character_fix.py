#!/usr/bin/env python3
"""商店の文字化け修正のテスト"""

import pytest
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from src.overworld.facilities.shop import Shop
from src.items.item import Item, ItemType, ItemInstance
from src.utils.logger import logger

class TestShopCharacterFix:
    """商店の文字化け修正のテスト"""
    
    def setup_method(self):
        """テスト前の初期化"""
        self.shop = Shop()
    
    def test_format_item_display_name_no_unicode(self):
        """アイテム表示名にUnicode絵文字が含まれていないことを確認"""
        # テスト用アイテムを作成
        weapon = Item("test_sword", {
            "name_key": "item.test_sword",
            "type": "weapon",
            "price": 100
        })
        
        armor = Item("test_armor", {
            "name_key": "item.test_armor",
            "type": "armor",
            "price": 200
        })
        
        consumable = Item("test_potion", {
            "name_key": "item.test_potion", 
            "type": "consumable",
            "price": 50
        })
        
        tool = Item("test_tool", {
            "name_key": "item.test_tool",
            "type": "tool",
            "price": 75
        })
        
        # 各アイテムタイプの表示名をテスト
        weapon_display = self.shop._format_item_display_name(weapon)
        armor_display = self.shop._format_item_display_name(armor)
        consumable_display = self.shop._format_item_display_name(consumable)
        tool_display = self.shop._format_item_display_name(tool)
        
        # Unicode絵文字が含まれていないことを確認
        assert "⚔" not in weapon_display
        assert "🛡" not in armor_display
        assert "🧪" not in consumable_display
        assert "🔧" not in tool_display
        assert "📦" not in weapon_display
        
        # ASCII文字のアイコンが含まれていることを確認
        assert "[W]" in weapon_display
        assert "[A]" in armor_display
        assert "[C]" in consumable_display
        assert "[T]" in tool_display
        
        # 基本的な表示形式が正しいことを確認
        assert "100G" in weapon_display
        assert "200G" in armor_display
        assert "50G" in consumable_display
        assert "75G" in tool_display
    
    def test_format_sellable_item_display_name_no_unicode(self):
        """売却アイテム表示名にUnicode絵文字が含まれていないことを確認"""
        # テスト用アイテムを作成
        weapon = Item("test_sword", {
            "name_key": "item.test_sword",
            "type": "weapon",
            "price": 100
        })
        
        # アイテムインスタンスを作成
        item_instance = ItemInstance(weapon, quantity=1)
        
        # 表示名を取得
        display_name = self.shop._format_sellable_item_display_name(item_instance, weapon)
        
        # Unicode絵文字が含まれていないことを確認
        assert "⚔" not in display_name
        assert "🛡" not in display_name
        assert "🧪" not in display_name
        assert "🔧" not in display_name
        assert "📦" not in display_name
        
        # ASCII文字のアイコンが含まれていることを確認
        assert "[W]" in display_name
        
        # 基本的な表示形式が正しいことを確認
        # 売却価格は購入価格の半分（50G）
        assert "50G" in display_name
    
    def test_format_sellable_item_display_name_with_quantity(self):
        """複数個のアイテムの売却表示名が正しくフォーマットされることを確認"""
        # テスト用アイテムを作成
        consumable = Item("test_potion", {
            "name_key": "item.test_potion",
            "type": "consumable",
            "price": 60
        })
        
        # 複数個のアイテムインスタンスを作成
        item_instance = ItemInstance(consumable, quantity=5)
        
        # 表示名を取得
        display_name = self.shop._format_sellable_item_display_name(item_instance, consumable)
        
        # Unicode絵文字が含まれていないことを確認
        assert "🧪" not in display_name
        
        # ASCII文字のアイコンが含まれていることを確認
        assert "[C]" in display_name
        
        # 数量と価格の表示が正しいことを確認
        assert "x5" in display_name
        assert "30G" in display_name  # 売却価格（60の半分）
        assert "(各30G)" in display_name
    
    def test_unknown_item_type_handling(self):
        """不明なアイテムタイプの場合のデフォルト処理"""
        # 不明なアイテムタイプを持つアイテムを作成
        unknown_item = Item("test_unknown", {
            "name_key": "item.test_unknown",
            "type": "treasure",  # デフォルトタイプ
            "price": 25
        })
        
        # 表示名を取得
        display_name = self.shop._format_item_display_name(unknown_item)
        
        # デフォルトのASCIIアイコンが使用されることを確認
        assert "[I]" in display_name
        assert "📦" not in display_name
        
        # 基本的な表示形式が正しいことを確認
        assert "25G" in display_name

if __name__ == "__main__":
    pytest.main([__file__, "-v"])