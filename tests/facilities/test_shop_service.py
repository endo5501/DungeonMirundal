"""商店サービスのテスト"""

import pytest
from unittest.mock import Mock, MagicMock, patch
from datetime import datetime, timedelta
from src.facilities.services.shop_service import ShopService
from src.facilities.core.service_result import ServiceResult, ResultType
from src.facilities.core.facility_service import MenuItem
from game.character import Character
from game.party import Party


class TestShopService:
    """商店サービスのテストクラス"""
    
    @pytest.fixture
    def shop_service(self):
        """商店サービスのフィクスチャ"""
        with patch('src.facilities.services.shop_service.Game') as mock_game_class:
            # モックゲームインスタンスを設定
            mock_game = Mock()
            mock_game_class.get_instance.return_value = mock_game
            
            # モックモデルを設定
            with patch('src.facilities.services.shop_service.ItemModel') as mock_item_model:
                service = ShopService()
                service.item_model = mock_item_model()
                
                # 在庫を初期化
                service._generate_shop_inventory()
                yield service
    
    @pytest.fixture
    def sample_party(self):
        """サンプルパーティのフィクスチャ"""
        party = Mock(spec=Party)
        party.name = "TestParty"
        party.gold = 1000
        party.members = []
        return party
    
    @pytest.fixture
    def character_with_items(self):
        """アイテムを持つキャラクターのフィクスチャ"""
        char = Mock(spec=Character)
        char.id = "char1"
        char.name = "Hero"
        char.level = 5
        char.is_alive.return_value = True
        
        # インベントリのモック
        char.inventory = Mock()
        
        # アイテムのモック
        item1 = Mock()
        item1.id = "potion"
        item1.name = "ポーション"
        item1.value = 50
        item1.quantity = 3
        item1.is_key_item.return_value = False
        
        item2 = Mock()
        item2.id = "key_item"
        item2.name = "重要アイテム"
        item2.value = 0
        item2.quantity = 1
        item2.is_key_item.return_value = True
        
        char.inventory.get_all_items.return_value = [item1, item2]
        
        return char
    
    def test_get_menu_items(self, shop_service):
        """メニュー項目取得のテスト"""
        # テスト実行
        items = shop_service.get_menu_items()
        
        # 検証
        assert len(items) == 4  # 4つのメニュー項目
        
        # メニュー項目の存在確認
        item_ids = [item.id for item in items]
        assert "buy" in item_ids
        assert "sell" in item_ids
        assert "identify" in item_ids
        assert "exit" in item_ids
        
        # 各項目の型確認
        for item in items:
            assert isinstance(item, MenuItem)
            assert item.label is not None
            assert item.description is not None
    
    def test_shop_inventory_generation(self, shop_service):
        """商店在庫生成のテスト"""
        # 在庫が生成されているか確認
        assert len(shop_service._shop_inventory) > 0
        
        # 各アイテムの必須フィールドを確認
        for item_id, item_data in shop_service._shop_inventory.items():
            assert "name" in item_data
            assert "category" in item_data
            assert "price" in item_data
            assert "stock" in item_data
            assert "description" in item_data
    
    def test_get_shop_inventory(self, shop_service, sample_party):
        """商店在庫取得のテスト"""
        shop_service.party = sample_party
        
        # カテゴリ指定なしで取得
        result = shop_service.execute_action("buy", {})
        
        # 検証
        assert result.success is True
        assert "items" in result.data
        assert "categories" in result.data
        assert "party_gold" in result.data
        assert result.data["party_gold"] == 1000
    
    def test_get_shop_inventory_by_category(self, shop_service, sample_party):
        """カテゴリ別商店在庫取得のテスト"""
        shop_service.party = sample_party
        
        # 武器カテゴリで取得
        result = shop_service.execute_action("buy", {"category": "weapons"})
        
        # 検証
        assert result.success is True
        items = result.data["items"]
        
        # 武器カテゴリのアイテムのみか確認
        for item_data in items.values():
            assert item_data["category"] == "weapons"
    
    def test_purchase_confirmation(self, shop_service, sample_party):
        """購入確認のテスト"""
        shop_service.party = sample_party
        
        # ポーション購入を確認
        result = shop_service.execute_action("buy", {
            "item_id": "potion",
            "quantity": 2
        })
        
        # 検証
        assert result.success is True
        assert result.result_type == ResultType.CONFIRM
        assert "購入しますか" in result.message
        assert result.data["total_cost"] == 100  # 50 * 2
    
    def test_purchase_execution_success(self, shop_service, sample_party):
        """購入実行（成功）のテスト"""
        shop_service.party = sample_party
        initial_gold = sample_party.gold
        initial_stock = shop_service._shop_inventory["potion"]["stock"]
        
        # 購入を実行
        result = shop_service.execute_action("buy", {
            "item_id": "potion",
            "quantity": 2,
            "confirmed": True
        })
        
        # 検証
        assert result.success is True
        assert result.result_type == ResultType.SUCCESS
        assert "購入しました" in result.message
        
        # 所持金が減っているか
        assert sample_party.gold == initial_gold - 100
        
        # 在庫が減っているか
        assert shop_service._shop_inventory["potion"]["stock"] == initial_stock - 2
    
    def test_purchase_insufficient_gold(self, shop_service, sample_party):
        """購入実行（所持金不足）のテスト"""
        sample_party.gold = 50  # 不足
        shop_service.party = sample_party
        
        # 高額アイテム購入を試みる
        result = shop_service.execute_action("buy", {
            "item_id": "steel_sword",
            "quantity": 1
        })
        
        # 検証
        assert result.success is False
        assert result.result_type == ResultType.WARNING
        assert "所持金が不足" in result.message
    
    def test_purchase_insufficient_stock(self, shop_service, sample_party):
        """購入実行（在庫不足）のテスト"""
        shop_service.party = sample_party
        
        # 在庫以上の数量を購入しようとする
        stock = shop_service._shop_inventory["steel_sword"]["stock"]
        result = shop_service.execute_action("buy", {
            "item_id": "steel_sword",
            "quantity": stock + 1
        })
        
        # 検証
        assert result.success is False
        assert result.result_type == ResultType.WARNING
        assert "在庫が不足" in result.message
    
    def test_get_sellable_items(self, shop_service, sample_party, character_with_items):
        """売却可能アイテム取得のテスト"""
        sample_party.members = [character_with_items]
        shop_service.party = sample_party
        
        # 売却可能アイテムを取得
        result = shop_service.execute_action("sell", {})
        
        # 検証
        assert result.success is True
        items = result.data["items"]
        
        # 重要アイテムは含まれていないか
        assert len(items) == 1  # ポーションのみ
        assert items[0]["name"] == "ポーション"
        assert items[0]["sell_price"] == 25  # 50 * 0.5
    
    def test_sell_confirmation(self, shop_service):
        """売却確認のテスト"""
        # 売却確認
        result = shop_service.execute_action("sell", {
            "item_id": "potion",
            "quantity": 2
        })
        
        # 検証
        assert result.success is True
        assert result.result_type == ResultType.CONFIRM
        assert "売却しますか" in result.message
    
    def test_sell_execution_success(self, shop_service, sample_party):
        """売却実行（成功）のテスト"""
        shop_service.party = sample_party
        initial_gold = sample_party.gold
        
        # 売却を実行
        result = shop_service.execute_action("sell", {
            "item_id": "potion",
            "quantity": 2,
            "confirmed": True
        })
        
        # 検証
        assert result.success is True
        assert result.result_type == ResultType.SUCCESS
        assert "売却しました" in result.message
        
        # 所持金が増えているか
        assert sample_party.gold > initial_gold
    
    def test_identify_cost_check(self, shop_service, sample_party):
        """鑑定料金チェックのテスト"""
        sample_party.gold = 50  # 鑑定料金（100G）より少ない
        shop_service.party = sample_party
        
        # 鑑定を試みる
        result = shop_service.execute_action("identify", {"item_id": "unknown_ring"})
        
        # 検証
        assert result.success is False
        assert result.result_type == ResultType.WARNING
        assert "鑑定料金が不足" in result.message
    
    def test_identify_execution_success(self, shop_service, sample_party):
        """鑑定実行（成功）のテスト"""
        shop_service.party = sample_party
        initial_gold = sample_party.gold
        
        # 鑑定を実行
        result = shop_service.execute_action("identify", {
            "item_id": "unknown_ring",
            "confirmed": True
        })
        
        # 検証
        assert result.success is True
        assert result.result_type == ResultType.SUCCESS
        assert "鑑定完了" in result.message
        
        # 料金が引かれているか
        assert sample_party.gold == initial_gold - shop_service.identify_cost
    
    def test_has_items_to_sell(self, shop_service, sample_party, character_with_items):
        """売却可能アイテムチェックのテスト"""
        # パーティなし
        shop_service.party = None
        assert shop_service._has_items_to_sell() is False
        
        # アイテムを持つキャラクターがいる
        sample_party.members = [character_with_items]
        shop_service.party = sample_party
        assert shop_service._has_items_to_sell() is True
    
    def test_exit_action(self, shop_service):
        """退出アクションのテスト"""
        # テスト実行
        result = shop_service.execute_action("exit", {})
        
        # 検証
        assert result.success is True
        assert "退出" in result.message
    
    def test_unknown_action(self, shop_service):
        """不明なアクションのテスト"""
        # テスト実行
        result = shop_service.execute_action("unknown_action", {})
        
        # 検証
        assert result.success is False
        assert "不明なアクション" in result.message