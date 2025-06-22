"""アイテム鑑定機能のテスト"""

import pytest
from src.overworld.facilities.magic_guild import MagicGuild
from src.character.party import Party
from src.character.character import Character
from src.character.stats import BaseStats
from src.items.item import ItemInstance, item_manager


class TestItemIdentification:
    """アイテム鑑定機能のテスト"""
    
    def setup_method(self):
        """各テストメソッドの前に実行"""
        self.magic_guild = MagicGuild()
        
        # テスト用パーティを作成
        stats = BaseStats(strength=15, agility=12, intelligence=14, faith=10, luck=13)
        character = Character.create_character("TestMage", "human", "mage", stats)
        self.party = Party(party_id="test_party")
        self.party.add_character(character)
        self.party.gold = 1000  # 初期ゴールド
        
        self.magic_guild.current_party = self.party
    
    def test_identify_single_unidentified_item(self):
        """単一の未鑑定アイテム鑑定テスト"""
        # パーティインベントリに未鑑定アイテムを追加
        party_inventory = self.party.get_party_inventory()
        
        # 未鑑定のダガーを追加
        unidentified_dagger = ItemInstance(item_id="dagger", quantity=1, identified=False)
        success = party_inventory.add_item(unidentified_dagger)
        assert success
        
        # 鑑定前の状態確認
        assert not unidentified_dagger.identified
        initial_gold = self.party.gold
        
        # 鑑定処理をシミュレート
        item = item_manager.get_item("dagger")
        assert item is not None
        
        identification_cost = self.magic_guild.service_costs['item_identification']
        slot = party_inventory.slots[0]
        
        # 鑑定実行
        self.magic_guild._identify_item(slot, unidentified_dagger, item, identification_cost)
        
        # 鑑定後の状態確認
        assert unidentified_dagger.identified  # 鑑定済みになっている
        assert self.party.gold == initial_gold - identification_cost  # ゴールドが減っている
    
    def test_identify_multiple_unidentified_items(self):
        """複数の未鑑定アイテム鑑定テスト"""
        # パーティインベントリに未鑑定アイテムを複数追加
        party_inventory = self.party.get_party_inventory()
        
        # 未鑑定の回復ポーションを3個追加
        unidentified_potions = ItemInstance(item_id="healing_potion", quantity=3, identified=False)
        success = party_inventory.add_item(unidentified_potions)
        assert success
        
        # 鑑定前の状態確認
        assert not unidentified_potions.identified
        initial_gold = self.party.gold
        
        # 鑑定処理をシミュレート
        item = item_manager.get_item("healing_potion")
        assert item is not None
        
        identification_cost = self.magic_guild.service_costs['item_identification']
        total_cost = identification_cost * unidentified_potions.quantity
        slot = party_inventory.slots[0]
        
        # 鑑定実行
        self.magic_guild._identify_item(slot, unidentified_potions, item, total_cost)
        
        # 鑑定後の状態確認
        assert unidentified_potions.identified  # 鑑定済みになっている
        assert self.party.gold == initial_gold - total_cost  # ゴールドが減っている
    
    def test_identification_insufficient_gold(self):
        """ゴールド不足での鑑定テスト"""
        # パーティインベントリに未鑑定アイテムを追加
        party_inventory = self.party.get_party_inventory()
        
        unidentified_item = ItemInstance(item_id="dagger", quantity=1, identified=False)
        success = party_inventory.add_item(unidentified_item)
        assert success
        
        # ゴールドを不足状態にする
        self.party.gold = 50  # 鑑定費用100Gより少ない
        initial_gold = self.party.gold
        
        # 鑑定処理をシミュレート
        item = item_manager.get_item("dagger")
        identification_cost = self.magic_guild.service_costs['item_identification']
        slot = party_inventory.slots[0]
        
        # 鑑定実行（失敗するはず）
        self.magic_guild._identify_item(slot, unidentified_item, item, identification_cost)
        
        # 状態確認（何も変わらないはず）
        assert not unidentified_item.identified  # 鑑定されていない
        assert self.party.gold == initial_gold  # ゴールドは変わらない
    
    def test_identification_menu_no_unidentified_items(self):
        """未鑑定アイテムがない場合のメニューテスト"""
        # パーティインベントリに鑑定済みアイテムを追加
        party_inventory = self.party.get_party_inventory()
        
        identified_item = ItemInstance(item_id="dagger", quantity=1, identified=True)
        success = party_inventory.add_item(identified_item)
        assert success
        
        # 未鑑定アイテムの検索をシミュレート
        unidentified_items = []
        for slot in party_inventory.slots:
            if not slot.is_empty():
                item_instance = slot.item_instance
                if not item_instance.identified:
                    item = item_manager.get_item(item_instance.item_id)
                    if item:
                        unidentified_items.append((slot, item_instance, item))
        
        # 未鑑定アイテムがないことを確認
        assert len(unidentified_items) == 0
    
    def test_identification_menu_with_mixed_items(self):
        """鑑定済み・未鑑定混在でのメニューテスト"""
        # パーティインベントリに各種アイテムを追加
        party_inventory = self.party.get_party_inventory()
        
        # 鑑定済みアイテム
        identified_item = ItemInstance(item_id="dagger", quantity=1, identified=True)
        party_inventory.add_item(identified_item)
        
        # 未鑑定アイテム
        unidentified_item1 = ItemInstance(item_id="short_sword", quantity=1, identified=False)
        party_inventory.add_item(unidentified_item1)
        
        unidentified_item2 = ItemInstance(item_id="healing_potion", quantity=2, identified=False)
        party_inventory.add_item(unidentified_item2)
        
        # 未鑑定アイテムの検索をシミュレート
        unidentified_items = []
        for slot in party_inventory.slots:
            if not slot.is_empty():
                item_instance = slot.item_instance
                if not item_instance.identified:
                    item = item_manager.get_item(item_instance.item_id)
                    if item:
                        unidentified_items.append((slot, item_instance, item))
        
        # 未鑑定アイテムが2種類あることを確認
        assert len(unidentified_items) == 2
        
        # 各アイテムが正しく検出されることを確認
        unidentified_item_ids = [item.item_id for _, _, item in unidentified_items]
        assert "short_sword" in unidentified_item_ids
        assert "healing_potion" in unidentified_item_ids
    
    def test_identification_cost_calculation(self):
        """鑑定費用計算のテスト"""
        identification_cost = self.magic_guild.service_costs['item_identification']
        assert identification_cost == 100  # 設定で100Gと定義されている
        
        # 単一アイテムの場合
        single_cost = identification_cost * 1
        assert single_cost == 100
        
        # 複数アイテムの場合
        multiple_cost = identification_cost * 5
        assert multiple_cost == 500
    
    def test_integration_identification_workflow(self):
        """鑑定ワークフローの統合テスト"""
        # パーティインベントリに未鑑定アイテムを追加
        party_inventory = self.party.get_party_inventory()
        
        # 複数の異なる種類の未鑑定アイテムを追加
        items_to_identify = [
            ("dagger", 1),
            ("leather_armor", 1),
            ("healing_potion", 3)
        ]
        
        total_expected_cost = 0
        identification_cost = self.magic_guild.service_costs['item_identification']
        
        for item_id, quantity in items_to_identify:
            unidentified_item = ItemInstance(item_id=item_id, quantity=quantity, identified=False)
            party_inventory.add_item(unidentified_item)
            total_expected_cost += identification_cost * quantity
        
        initial_gold = self.party.gold
        
        # 全てのアイテムを鑑定
        for slot in party_inventory.slots:
            if not slot.is_empty():
                item_instance = slot.item_instance
                if not item_instance.identified:
                    item = item_manager.get_item(item_instance.item_id)
                    cost = identification_cost * item_instance.quantity
                    self.magic_guild._identify_item(slot, item_instance, item, cost)
        
        # 結果確認
        assert self.party.gold == initial_gold - total_expected_cost
        
        # 全てのアイテムが鑑定済みになっていることを確認
        for slot in party_inventory.slots:
            if not slot.is_empty():
                assert slot.item_instance.identified
    
    def test_identification_different_item_types(self):
        """異なるアイテムタイプの鑑定テスト"""
        party_inventory = self.party.get_party_inventory()
        
        # 異なるタイプのアイテムをテスト
        test_items = [
            "dagger",        # 武器
            "leather_armor", # 防具
            "healing_potion", # 消耗品
            "torch"          # 道具
        ]
        
        identification_cost = self.magic_guild.service_costs['item_identification']
        
        for item_id in test_items:
            # 未鑑定アイテムを追加
            unidentified_item = ItemInstance(item_id=item_id, quantity=1, identified=False)
            party_inventory.add_item(unidentified_item)
            
            # アイテム情報を取得
            item = item_manager.get_item(item_id)
            assert item is not None
            
            # 鑑定前の状態確認
            assert not unidentified_item.identified
            
            # 鑑定実行
            slot = None
            for s in party_inventory.slots:
                if not s.is_empty() and s.item_instance.item_id == item_id:
                    slot = s
                    break
            
            assert slot is not None
            self.magic_guild._identify_item(slot, unidentified_item, item, identification_cost)
            
            # 鑑定後の状態確認
            assert unidentified_item.identified
            
            # クリーンアップ
            slot.remove_item()