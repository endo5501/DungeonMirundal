"""アイテム詳細パネルのテスト"""

import pytest
import pygame
import pygame_gui
from unittest.mock import Mock, MagicMock, patch


@pytest.fixture
def mock_ui_setup():
    """UI要素のモック"""
    rect = pygame.Rect(0, 0, 300, 200)
    parent = Mock()
    ui_manager = Mock()
    return rect, parent, ui_manager


@pytest.fixture
def sample_item_data():
    """サンプルアイテムデータ"""
    return {
        "weapon": {
            "id": "sword_magic",
            "name": "魔法の剣",
            "type": "weapon",
            "description": "魔力が込められた剣。攻撃力が高い。",
            "price": 2000,
            "stats": {
                "attack": 25,
                "durability": 100,
                "weight": 3.5
            },
            "rarity": "rare",
            "requirements": {
                "level": 5,
                "strength": 15
            }
        },
        "consumable": {
            "id": "potion_mana",
            "name": "マナポーション",
            "type": "consumable",
            "description": "魔力を回復するポーション。",
            "price": 100,
            "effects": {
                "mana_recovery": 50
            },
            "usage": "戦闘中使用可能"
        },
        "armor": {
            "id": "helm_iron",
            "name": "鉄の兜",
            "type": "armor",
            "description": "頭部を守る鉄製の兜。",
            "price": 800,
            "stats": {
                "defense": 8,
                "durability": 80,
                "weight": 2.0
            },
            "slot": "head"
        }
    }


class TestItemDetailPanelBasic:
    """ItemDetailPanelの基本機能テスト"""
    
    def test_initialization(self, mock_ui_setup):
        """正常に初期化される"""
        from src.facilities.ui.shop.item_detail_panel import ItemDetailPanel
        
        rect, parent, ui_manager = mock_ui_setup
        
        with patch('pygame_gui.elements.UIPanel'), \
             patch('pygame_gui.elements.UILabel'), \
             patch('pygame_gui.elements.UITextBox'):
            
            panel = ItemDetailPanel(rect, parent, ui_manager)
            
            # 基本属性の確認
            assert panel.rect == rect
            assert panel.parent == parent
            assert panel.ui_manager == ui_manager
            
            # UI要素の初期状態
            assert panel.container is not None
            assert panel.name_label is not None
            assert panel.description_box is not None
            assert panel.stats_box is not None
    
    def test_create_ui_elements(self, mock_ui_setup):
        """UI要素が正常に作成される"""
        from src.facilities.ui.shop.item_detail_panel import ItemDetailPanel
        
        rect, parent, ui_manager = mock_ui_setup
        
        with patch('pygame_gui.elements.UIPanel') as mock_panel, \
             patch('pygame_gui.elements.UILabel') as mock_label, \
             patch('pygame_gui.elements.UITextBox') as mock_text_box:
            
            panel = ItemDetailPanel(rect, parent, ui_manager)
            
            # UI要素が作成される
            mock_panel.assert_called_once()
            mock_label.assert_called_once()
            assert mock_text_box.call_count == 2  # description_box, stats_box


class TestItemDetailPanelDisplay:
    """ItemDetailPanelの表示機能テスト"""
    
    def test_display_weapon_item(self, mock_ui_setup, sample_item_data):
        """武器アイテムの表示"""
        from src.facilities.ui.shop.item_detail_panel import ItemDetailPanel
        
        panel = Mock()
        panel.name_label = Mock()
        panel.description_box = Mock()
        panel.stats_box = Mock()
        
        weapon_data = sample_item_data["weapon"]
        
        ItemDetailPanel.display_item(panel, weapon_data)
        
        # アイテム名が設定される
        panel.name_label.set_text.assert_called_with("魔法の剣")
        
        # 説明が設定される
        expected_desc = "魔力が込められた剣。攻撃力が高い。"
        assert panel.description_box.html_text == expected_desc
        panel.description_box.rebuild.assert_called_once()
        
        # 統計情報が設定される
        expected_stats = ("<b>武器情報</b><br>"
                         "攻撃力: 25<br>"
                         "耐久度: 100<br>"
                         "重量: 3.5kg<br>"
                         "<br>"
                         "<b>必要条件</b><br>"
                         "レベル: 5<br>"
                         "筋力: 15")
        assert panel.stats_box.html_text == expected_stats
        panel.stats_box.rebuild.assert_called_once()
    
    def test_display_consumable_item(self, mock_ui_setup, sample_item_data):
        """消耗品アイテムの表示"""
        from src.facilities.ui.shop.item_detail_panel import ItemDetailPanel
        
        panel = Mock()
        panel.name_label = Mock()
        panel.description_box = Mock()
        panel.stats_box = Mock()
        
        consumable_data = sample_item_data["consumable"]
        
        ItemDetailPanel.display_item(panel, consumable_data)
        
        # アイテム名が設定される
        panel.name_label.set_text.assert_called_with("マナポーション")
        
        # 効果情報が設定される
        expected_stats = ("<b>効果</b><br>"
                         "マナ回復: 50<br>"
                         "<br>"
                         "<b>使用方法</b><br>"
                         "戦闘中使用可能")
        assert panel.stats_box.html_text == expected_stats
    
    def test_display_armor_item(self, mock_ui_setup, sample_item_data):
        """防具アイテムの表示"""
        from src.facilities.ui.shop.item_detail_panel import ItemDetailPanel
        
        panel = Mock()
        panel.name_label = Mock()
        panel.description_box = Mock()
        panel.stats_box = Mock()
        
        armor_data = sample_item_data["armor"]
        
        ItemDetailPanel.display_item(panel, armor_data)
        
        # アイテム名が設定される
        panel.name_label.set_text.assert_called_with("鉄の兜")
        
        # 防具情報が設定される
        expected_stats = ("<b>防具情報</b><br>"
                         "防御力: 8<br>"
                         "耐久度: 80<br>"
                         "重量: 2.0kg<br>"
                         "装備部位: head")
        assert panel.stats_box.html_text == expected_stats
    
    def test_display_item_none(self):
        """アイテムなしの場合の表示"""
        from src.facilities.ui.shop.item_detail_panel import ItemDetailPanel
        
        panel = Mock()
        panel.name_label = Mock()
        panel.description_box = Mock()
        panel.stats_box = Mock()
        
        ItemDetailPanel.display_item(panel, None)
        
        # 全て空になる
        panel.name_label.set_text.assert_called_with("")
        assert panel.description_box.html_text == ""
        assert panel.stats_box.html_text == ""
        panel.description_box.rebuild.assert_called_once()
        panel.stats_box.rebuild.assert_called_once()
    
    def test_display_item_minimal_data(self):
        """最小限のデータでの表示"""
        from src.facilities.ui.shop.item_detail_panel import ItemDetailPanel
        
        panel = Mock()
        panel.name_label = Mock()
        panel.description_box = Mock()
        panel.stats_box = Mock()
        
        minimal_item = {
            "name": "テストアイテム",
            "description": "テスト用のアイテムです"
        }
        
        ItemDetailPanel.display_item(panel, minimal_item)
        
        # 基本情報のみ表示される
        panel.name_label.set_text.assert_called_with("テストアイテム")
        assert panel.description_box.html_text == "テスト用のアイテムです"
        # 統計情報は空になる
        assert panel.stats_box.html_text == ""


class TestItemDetailPanelUtilities:
    """ItemDetailPanelのユーティリティ機能テスト"""
    
    def test_format_weapon_stats(self, sample_item_data):
        """武器統計情報のフォーマット"""
        from src.facilities.ui.shop.item_detail_panel import ItemDetailPanel
        
        weapon_data = sample_item_data["weapon"]
        
        result = ItemDetailPanel._format_weapon_stats(weapon_data)
        
        expected = ("<b>武器情報</b><br>"
                   "攻撃力: 25<br>"
                   "耐久度: 100<br>"
                   "重量: 3.5kg<br>"
                   "<br>"
                   "<b>必要条件</b><br>"
                   "レベル: 5<br>"
                   "筋力: 15")
        assert result == expected
    
    def test_format_armor_stats(self, sample_item_data):
        """防具統計情報のフォーマット"""
        from src.facilities.ui.shop.item_detail_panel import ItemDetailPanel
        
        armor_data = sample_item_data["armor"]
        
        result = ItemDetailPanel._format_armor_stats(armor_data)
        
        expected = ("<b>防具情報</b><br>"
                   "防御力: 8<br>"
                   "耐久度: 80<br>"
                   "重量: 2.0kg<br>"
                   "装備部位: head")
        assert result == expected
    
    def test_format_consumable_stats(self, sample_item_data):
        """消耗品統計情報のフォーマット"""
        from src.facilities.ui.shop.item_detail_panel import ItemDetailPanel
        
        consumable_data = sample_item_data["consumable"]
        
        result = ItemDetailPanel._format_consumable_stats(consumable_data)
        
        expected = ("<b>効果</b><br>"
                   "マナ回復: 50<br>"
                   "<br>"
                   "<b>使用方法</b><br>"
                   "戦闘中使用可能")
        assert result == expected
    
    def test_format_stats_missing_data(self):
        """データが不足している場合の統計情報フォーマット"""
        from src.facilities.ui.shop.item_detail_panel import ItemDetailPanel
        
        # 必要なフィールドが不足しているデータ
        incomplete_weapon = {
            "type": "weapon",
            "stats": {"attack": 10}  # 他のフィールドなし
        }
        
        result = ItemDetailPanel._format_weapon_stats(incomplete_weapon)
        
        # 利用可能なデータのみ表示される
        assert "攻撃力: 10" in result
        # 不足データは表示されない
        assert "耐久度" not in result
    
    def test_get_rarity_color(self):
        """レアリティカラーの取得"""
        from src.facilities.ui.shop.item_detail_panel import ItemDetailPanel
        
        # 各レアリティのカラー確認
        assert ItemDetailPanel._get_rarity_color("common") == "#FFFFFF"
        assert ItemDetailPanel._get_rarity_color("uncommon") == "#00FF00"
        assert ItemDetailPanel._get_rarity_color("rare") == "#0080FF"
        assert ItemDetailPanel._get_rarity_color("epic") == "#8000FF"
        assert ItemDetailPanel._get_rarity_color("legendary") == "#FF8000"
        
        # 未知のレアリティはデフォルト
        assert ItemDetailPanel._get_rarity_color("unknown") == "#FFFFFF"
    
    def test_format_price_display(self):
        """価格表示のフォーマット"""
        from src.facilities.ui.shop.item_detail_panel import ItemDetailPanel
        
        # 通常の価格
        assert ItemDetailPanel._format_price(1000) == "1,000 G"
        
        # 大きな価格
        assert ItemDetailPanel._format_price(1234567) == "1,234,567 G"
        
        # 0の価格
        assert ItemDetailPanel._format_price(0) == "0 G"


class TestItemDetailPanelVisibility:
    """ItemDetailPanelの表示/非表示テスト"""
    
    def test_show(self):
        """パネルの表示"""
        from src.facilities.ui.shop.item_detail_panel import ItemDetailPanel
        
        panel = Mock()
        panel.container = Mock()
        
        ItemDetailPanel.show(panel)
        
        panel.container.show.assert_called_once()
    
    def test_hide(self):
        """パネルの非表示"""
        from src.facilities.ui.shop.item_detail_panel import ItemDetailPanel
        
        panel = Mock()
        panel.container = Mock()
        
        ItemDetailPanel.hide(panel)
        
        panel.container.hide.assert_called_once()
    
    def test_destroy(self):
        """パネルの破棄"""
        from src.facilities.ui.shop.item_detail_panel import ItemDetailPanel
        
        panel = Mock()
        panel.container = Mock()
        
        ItemDetailPanel.destroy(panel)
        
        panel.container.kill.assert_called_once()
    
    def test_show_hide_destroy_no_container(self):
        """コンテナなしでの表示・非表示・破棄"""
        from src.facilities.ui.shop.item_detail_panel import ItemDetailPanel
        
        panel = Mock()
        panel.container = None
        
        # エラーが発生しないことを確認
        try:
            ItemDetailPanel.show(panel)
            ItemDetailPanel.hide(panel)
            ItemDetailPanel.destroy(panel)
            assert True
        except Exception as e:
            pytest.fail(f"Unexpected exception: {e}")


class TestItemDetailPanelComplex:
    """ItemDetailPanelの複雑な表示テスト"""
    
    def test_display_item_with_enchantments(self):
        """エンチャント付きアイテムの表示"""
        from src.facilities.ui.shop.item_detail_panel import ItemDetailPanel
        
        panel = Mock()
        panel.name_label = Mock()
        panel.description_box = Mock()
        panel.stats_box = Mock()
        
        enchanted_item = {
            "name": "炎の剣+5",
            "type": "weapon",
            "description": "炎の力が込められた強化された剣",
            "stats": {
                "attack": 30,
                "fire_damage": 10,
                "durability": 120
            },
            "enchantments": [
                {"name": "火炎付与", "level": 3},
                {"name": "強化", "level": 5}
            ],
            "rarity": "epic"
        }
        
        ItemDetailPanel.display_item(panel, enchanted_item)
        
        # エンチャント情報が含まれる
        stats_html = panel.stats_box.html_text
        assert "火炎付与" in stats_html
        assert "強化" in stats_html
    
    def test_display_item_with_set_bonus(self):
        """セットボーナス付きアイテムの表示"""
        from src.facilities.ui.shop.item_detail_panel import ItemDetailPanel
        
        panel = Mock()
        panel.name_label = Mock()
        panel.description_box = Mock()
        panel.stats_box = Mock()
        
        set_item = {
            "name": "ドラゴンスケール兜",
            "type": "armor",
            "description": "ドラゴンの鱗で作られた強固な兜",
            "stats": {
                "defense": 15,
                "fire_resistance": 20
            },
            "set_name": "ドラゴンスケールセット",
            "set_bonus": {
                "2_pieces": "火炎耐性+10%",
                "4_pieces": "ドラゴンブレス使用可能"
            }
        }
        
        ItemDetailPanel.display_item(panel, set_item)
        
        # セットボーナス情報が含まれる
        stats_html = panel.stats_box.html_text
        assert "セットボーナス" in stats_html
        assert "ドラゴンブレス" in stats_html