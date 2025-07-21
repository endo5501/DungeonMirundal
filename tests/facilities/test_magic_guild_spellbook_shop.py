"""魔術師ギルドの魔術書店機能のテスト"""

import pytest
from unittest.mock import Mock, patch
from src.facilities.services.magic_guild_service import MagicGuildService
from src.facilities.core.service_result import ServiceResult, ResultType
from src.character.party import Party


class TestMagicGuildSpellbookShop:
    """魔術師ギルドの魔術書店機能のテスト"""
    
    @pytest.fixture
    def service(self):
        """テスト用のMagicGuildServiceインスタンス"""
        service = MagicGuildService()
        
        # モックパーティを設定
        service.party = Mock(spec=Party)
        service.party.gold = 1000  # 十分な所持金を設定
        service.party.members = []
        
        return service
    
    def test_handle_buy_without_item_id_returns_inventory(self, service):
        """item_idなしでbuyアクションを実行すると在庫一覧が返される"""
        # Arrange
        params = {}
        
        # Act
        result = service.execute_action("buy", params)
        
        # Assert
        assert result.is_success()
        assert "items" in result.data
        assert "categories" in result.data
        assert "party_gold" in result.data
        assert len(result.data["items"]) > 0  # 在庫が存在する
        
    def test_handle_buy_with_category_filters_items(self, service):
        """カテゴリ指定でbuyアクションを実行するとフィルタされた在庫が返される"""
        # Arrange
        params = {"category": "offensive"}
        
        # Act
        result = service.execute_action("buy", params)
        
        # Assert
        assert result.is_success()
        items = result.data["items"]
        
        # すべてのアイテムがoffensiveカテゴリであることを確認
        for item_id, item_data in items.items():
            assert item_data["category"] == "offensive"
    
    def test_spellbook_categories_are_correct(self, service):
        """魔術書のカテゴリが正しく設定されている"""
        # Act
        result = service.execute_action("buy", {})
        
        # Assert
        categories = result.data["categories"]
        expected_categories = ["offensive", "defensive", "healing", "utility", "special"]
        
        assert len(categories) == 5
        for category in categories:
            assert category["id"] in expected_categories
    
    def test_confirm_purchase_with_sufficient_gold(self, service):
        """十分な所持金がある場合の購入確認"""
        # Arrange
        params = {
            "item_id": "spellbook_fire_1",
            "quantity": 1,
            "buyer_id": "party"
        }
        
        # Act
        result = service.execute_action("buy", params)
        
        # Assert
        assert result.is_success()
        assert result.result_type == ResultType.CONFIRM
        assert "火の魔術書・初級" in result.message
        assert "500 G" in result.message
    
    def test_confirm_purchase_with_insufficient_gold(self, service):
        """所持金不足の場合の購入確認"""
        # Arrange
        service.party.gold = 100  # 不足する金額に設定
        params = {
            "item_id": "spellbook_fire_1",
            "quantity": 1,
            "buyer_id": "party"
        }
        
        # Act
        result = service.execute_action("buy", params)
        
        # Assert
        assert not result.is_success()
        assert result.result_type == ResultType.WARNING
        assert "所持金が不足しています" in result.message
    
    def test_execute_purchase_success(self, service):
        """購入実行が成功する"""
        # Arrange
        params = {
            "item_id": "spellbook_fire_1",
            "quantity": 1,
            "buyer_id": "party",
            "confirmed": True
        }
        initial_gold = service.party.gold
        
        # Act
        result = service.execute_action("buy", params)
        
        # Assert
        assert result.is_success()
        assert result.result_type == ResultType.SUCCESS
        assert "火の魔術書・初級" in result.message
        assert "購入しました" in result.message
        assert service.party.gold == initial_gold - 500  # 金額が減っている
    
    def test_invalid_item_id_fails(self, service):
        """存在しないアイテムIDで購入しようとすると失敗する"""
        # Arrange
        params = {
            "item_id": "invalid_spellbook",
            "quantity": 1,
            "buyer_id": "party"
        }
        
        # Act
        result = service.execute_action("buy", params)
        
        # Assert
        assert not result.is_success()
        assert "取り扱っていません" in result.message
    
    def test_insufficient_stock_fails(self, service):
        """在庫不足の場合は購入できない"""
        # Arrange
        params = {
            "item_id": "spellbook_fire_1",
            "quantity": 10,  # 在庫以上の数量
            "buyer_id": "party"
        }
        
        # Act
        result = service.execute_action("buy", params)
        
        # Assert
        assert not result.is_success()
        assert result.result_type == ResultType.WARNING
        assert "在庫が不足しています" in result.message
    
    def test_spellbook_inventory_structure(self, service):
        """魔術書の在庫データ構造が正しい"""
        # Act
        inventory = service._generate_spellbook_inventory()
        
        # Assert
        assert len(inventory) > 0
        
        # 各魔術書の必須フィールドを確認
        for item_id, item_data in inventory.items():
            assert "name" in item_data
            assert "category" in item_data
            assert "price" in item_data
            assert "stock" in item_data
            assert "description" in item_data
            assert "required_level" in item_data
            assert "spells" in item_data
            assert isinstance(item_data["spells"], list)
            assert len(item_data["spells"]) > 0