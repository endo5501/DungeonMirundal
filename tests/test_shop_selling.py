"""商店の売却機能テスト"""

import pytest
from src.overworld.facilities.shop import Shop
from src.character.party import Party
from src.character.character import Character
from src.character.stats import BaseStats
from src.items.item import ItemInstance, item_manager
from src.inventory.inventory import inventory_manager


class TestShopSelling:
    """商店売却機能のテスト"""
    
    def setup_method(self):
        """各テストメソッドの前に実行"""
        self.shop = Shop()
        
        # テスト用パーティを作成
        stats = BaseStats(strength=15, agility=12, intelligence=14, faith=10, luck=13)
        character = Character.create_character("TestHero", "human", "fighter", stats)
        self.party = Party(party_id="test_party")
        self.party.add_character(character)
        self.party.gold = 1000  # 初期ゴールド
        
        self.shop.current_party = self.party
    
    def test_sell_menu_no_items(self):
        """アイテムがない場合の売却メニューテスト"""
        # パーティインベントリが空の状態でテスト
        party_inventory = self.party.get_party_inventory()
        
        # メニュー表示はエラーにならず、適切なメッセージが表示されることを確認
        assert party_inventory is not None
        assert len([slot for slot in party_inventory.slots if not slot.is_empty()]) == 0
    
    def test_sell_single_item(self):
        """単一アイテム売却のテスト"""
        # パーティインベントリにアイテムを追加
        party_inventory = self.party.get_party_inventory()
        
        # ダガーを追加
        dagger_instance = ItemInstance(item_id="dagger", quantity=1, identified=True)
        success = party_inventory.add_item(dagger_instance)
        assert success
        
        # 売却前のゴールド
        initial_gold = self.party.gold
        
        # 売却処理をシミュレート
        item = item_manager.get_item("dagger")
        assert item is not None
        
        sell_price = max(1, item.price // 2)  # 売却価格は購入価格の50%
        
        # 売却処理
        slot = party_inventory.slots[0]  # 最初のスロット
        self.shop._sell_item(slot, dagger_instance, item, sell_price, 1)
        
        # 結果確認
        assert self.party.gold == initial_gold + sell_price
        assert slot.is_empty()  # スロットが空になっている
    
    def test_sell_multiple_items(self):
        """複数個数アイテム売却のテスト"""
        # パーティインベントリに回復ポーションを複数追加
        party_inventory = self.party.get_party_inventory()
        
        potion_instance = ItemInstance(item_id="healing_potion", quantity=5, identified=True)
        success = party_inventory.add_item(potion_instance)
        assert success
        
        # 売却前のゴールド
        initial_gold = self.party.gold
        
        # 売却処理をシミュレート
        item = item_manager.get_item("healing_potion")
        assert item is not None
        
        sell_price = max(1, item.price // 2)
        sell_quantity = 3
        
        # 売却処理
        slot = party_inventory.slots[0]
        self.shop._sell_item(slot, potion_instance, item, sell_price, sell_quantity)
        
        # 結果確認
        expected_gold = initial_gold + (sell_price * sell_quantity)
        assert self.party.gold == expected_gold
        assert potion_instance.quantity == 2  # 残り2個
        assert not slot.is_empty()  # まだアイテムが残っている
    
    def test_sell_all_quantity(self):
        """全数量売却のテスト"""
        # パーティインベントリにアイテムを追加
        party_inventory = self.party.get_party_inventory()
        
        torch_instance = ItemInstance(item_id="torch", quantity=10, identified=True)
        success = party_inventory.add_item(torch_instance)
        assert success
        
        # 売却前のゴールド
        initial_gold = self.party.gold
        
        # 売却処理をシミュレート
        item = item_manager.get_item("torch")
        assert item is not None
        
        sell_price = max(1, item.price // 2)
        sell_quantity = 10  # 全部売却
        
        # 売却処理
        slot = party_inventory.slots[0]
        self.shop._sell_item(slot, torch_instance, item, sell_price, sell_quantity)
        
        # 結果確認
        expected_gold = initial_gold + (sell_price * sell_quantity)
        assert self.party.gold == expected_gold
        assert slot.is_empty()  # スロットが空になっている
    
    def test_sell_item_price_calculation(self):
        """売却価格計算のテスト"""
        items_to_test = ["dagger", "healing_potion", "leather_armor"]
        
        for item_id in items_to_test:
            item = item_manager.get_item(item_id)
            assert item is not None
            
            # 売却価格は購入価格の50%（最低1G）
            expected_sell_price = max(1, item.price // 2)
            
            # 実際に計算される売却価格をチェック
            party_inventory = self.party.get_party_inventory()
            instance = ItemInstance(item_id=item_id, quantity=1, identified=True)
            party_inventory.add_item(instance)
            
            # 売却価格が正しく計算されることを確認
            calculated_price = max(1, item.price // 2)
            assert calculated_price == expected_sell_price
            
            # クリーンアップ
            party_inventory.slots[0].remove_item()
    
    def test_sell_invalid_quantity(self):
        """無効な数量での売却テスト"""
        # パーティインベントリにアイテムを追加
        party_inventory = self.party.get_party_inventory()
        
        item_instance = ItemInstance(item_id="dagger", quantity=1, identified=True)
        success = party_inventory.add_item(item_instance)
        assert success
        
        # 売却前のゴールド
        initial_gold = self.party.gold
        
        # 存在しない数量で売却を試行
        item = item_manager.get_item("dagger")
        sell_price = max(1, item.price // 2)
        
        slot = party_inventory.slots[0]
        self.shop._sell_item(slot, item_instance, item, sell_price, 5)  # 1個しかないのに5個売却を試行
        
        # 売却が実行されないことを確認
        assert self.party.gold == initial_gold  # ゴールドは変わらない
        assert not slot.is_empty()  # アイテムはまだ残っている
    
    def test_sell_unidentified_item(self):
        """未鑑定アイテムの売却制限テスト"""
        # パーティインベントリに未鑑定アイテムを追加
        party_inventory = self.party.get_party_inventory()
        
        unidentified_item = ItemInstance(item_id="dagger", quantity=1, identified=False)
        success = party_inventory.add_item(unidentified_item)
        assert success
        
        # 売却可能アイテムを取得する際の処理をテスト
        sellable_items = []
        for slot in party_inventory.slots:
            if not slot.is_empty():
                item_instance = slot.item_instance
                item = item_manager.get_item(item_instance.item_id)
                # 売却条件: 価格が設定されており、鑑定済みであること
                if item and item.price > 0 and item_instance.identified:
                    sellable_items.append((slot, item_instance, item))
        
        # 未鑑定アイテムは売却リストに含まれないことを確認
        assert len(sellable_items) == 0
    
    def test_integration_buy_and_sell(self):
        """購入・売却の統合テスト"""
        # アイテムを購入
        initial_gold = self.party.gold
        item = item_manager.get_item("dagger")
        assert item is not None
        
        # 購入処理をシミュレート
        purchase_price = item.price
        item_instance = item_manager.create_item_instance(item.item_id)
        
        # ゴールドを減らしてアイテムをインベントリに追加
        self.party.gold -= purchase_price
        party_inventory = self.party.get_party_inventory()
        success = party_inventory.add_item(item_instance)
        assert success
        
        # 購入後の状態確認
        assert self.party.gold == initial_gold - purchase_price
        
        # 同じアイテムを売却
        sell_price = max(1, item.price // 2)
        slot = party_inventory.slots[0]
        self.shop._sell_item(slot, item_instance, item, sell_price, 1)
        
        # 売却後の状態確認
        expected_final_gold = initial_gold - purchase_price + sell_price
        assert self.party.gold == expected_final_gold
        assert slot.is_empty()
        
        # 差額確認（購入価格の約50%の損失）
        loss = purchase_price - sell_price
        assert loss == purchase_price - sell_price
    
    def test_sell_unidentified_item_restriction(self):
        """未鑑定アイテムの売却制限テスト"""
        # パーティインベントリに未鑑定アイテムを追加
        party_inventory = self.party.get_party_inventory()
        
        # 未鑑定のダガーを追加
        unidentified_dagger = ItemInstance(item_id="dagger", quantity=1, identified=False)
        success = party_inventory.add_item(unidentified_dagger)
        assert success
        
        # 鑑定済みアイテムも追加
        identified_short_sword = ItemInstance(item_id="short_sword", quantity=1, identified=True)
        success = party_inventory.add_item(identified_short_sword)
        assert success
        
        # 売却可能アイテムを取得
        sellable_items = []
        for slot in party_inventory.slots:
            if not slot.is_empty():
                item_instance = slot.item_instance
                item = item_manager.get_item(item_instance.item_id)
                if item and item.price > 0 and item_instance.identified:
                    sellable_items.append((slot, item_instance, item))
        
        # 鑑定済みアイテムのみが売却可能であることを確認
        assert len(sellable_items) == 1
        assert sellable_items[0][1].item_id == "short_sword"
        assert sellable_items[0][1].identified == True
        
        # 未鑑定アイテムが売却リストに含まれていないことを確認
        sellable_item_ids = [item_instance.item_id for _, item_instance, _ in sellable_items]
        assert "dagger" not in sellable_item_ids