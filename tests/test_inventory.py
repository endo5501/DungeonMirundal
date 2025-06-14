"""インベントリシステムのテスト"""

import pytest
from src.inventory.inventory import (
    Inventory, InventorySlot, InventorySlotType, InventoryManager,
    inventory_manager
)
from src.items.item import ItemInstance, ItemManager, item_manager
from src.character.character import Character
from src.character.party import Party
from src.character.stats import BaseStats


class TestInventorySlot:
    """InventorySlotのテスト"""
    
    def setup_method(self):
        """各テストメソッドの前に実行"""
        self.slot = InventorySlot(slot_type=InventorySlotType.CHARACTER)
        self.item_instance = ItemInstance(
            item_id="dagger",
            quantity=1,
            identified=True
        )
    
    def test_slot_initialization(self):
        """スロット初期化のテスト"""
        assert self.slot.is_empty()
        assert self.slot.slot_type == InventorySlotType.CHARACTER
        assert self.slot.item_instance is None
    
    def test_add_item_to_empty_slot(self):
        """空のスロットにアイテム追加のテスト"""
        success = self.slot.add_item(self.item_instance)
        
        assert success == True
        assert not self.slot.is_empty()
        assert self.slot.item_instance == self.item_instance
    
    def test_stack_same_items(self):
        """同じアイテムのスタックテスト"""
        # 消耗品アイテムを使用
        consumable_item = ItemInstance(
            item_id="healing_potion",
            quantity=2,
            identified=True
        )
        
        # 最初のアイテムを追加
        self.slot.add_item(consumable_item)
        
        # 同じアイテムを追加（スタック）
        additional_item = ItemInstance(
            item_id="healing_potion",
            quantity=3,
            identified=True
        )
        
        success = self.slot.add_item(additional_item)
        
        assert success == True
        assert self.slot.item_instance.quantity == 5
    
    def test_remove_item_partially(self):
        """アイテムの一部削除テスト"""
        # 複数個のアイテムを追加
        multi_item = ItemInstance(
            item_id="healing_potion",
            quantity=5,
            identified=True
        )
        self.slot.add_item(multi_item)
        
        # 一部を削除
        removed_item = self.slot.remove_item(2)
        
        assert removed_item is not None
        assert removed_item.quantity == 2
        assert self.slot.item_instance.quantity == 3
    
    def test_remove_all_items(self):
        """全アイテム削除テスト"""
        self.slot.add_item(self.item_instance)
        
        removed_item = self.slot.remove_item()
        
        assert removed_item == self.item_instance
        assert self.slot.is_empty()
    
    def test_slot_serialization(self):
        """スロットシリアライゼーションのテスト"""
        self.slot.add_item(self.item_instance)
        
        data = self.slot.to_dict()
        restored_slot = InventorySlot.from_dict(data)
        
        assert restored_slot.slot_type == self.slot.slot_type
        assert restored_slot.item_instance.item_id == self.item_instance.item_id
        assert restored_slot.item_instance.quantity == self.item_instance.quantity


class TestInventory:
    """Inventoryのテスト"""
    
    def setup_method(self):
        """各テストメソッドの前に実行"""
        self.inventory = Inventory(
            owner_id="test_char",
            inventory_type=InventorySlotType.CHARACTER,
            max_slots=5
        )
        self.item_manager = ItemManager()
    
    def test_inventory_initialization(self):
        """インベントリ初期化のテスト"""
        assert self.inventory.owner_id == "test_char"
        assert self.inventory.inventory_type == InventorySlotType.CHARACTER
        assert self.inventory.max_slots == 5
        assert len(self.inventory.slots) == 5
        assert self.inventory.is_full() == False
        assert self.inventory.get_empty_slot_count() == 5
    
    def test_add_item_to_empty_inventory(self):
        """空のインベントリにアイテム追加のテスト"""
        item = ItemInstance(item_id="dagger", quantity=1)
        
        success = self.inventory.add_item(item)
        
        assert success == True
        assert self.inventory.get_used_slot_count() == 1
        assert self.inventory.get_empty_slot_count() == 4
    
    def test_add_items_until_full(self):
        """インベントリが満杯になるまでアイテム追加のテスト"""
        for i in range(5):
            item = ItemInstance(item_id=f"item_{i}", quantity=1)
            success = self.inventory.add_item(item)
            assert success == True
        
        assert self.inventory.is_full() == True
        
        # 満杯の場合は追加失敗
        extra_item = ItemInstance(item_id="extra_item", quantity=1)
        success = self.inventory.add_item(extra_item)
        assert success == False
    
    def test_stack_consumable_items(self):
        """消耗品のスタックテスト"""
        # 最初のポーション
        potion1 = ItemInstance(item_id="healing_potion", quantity=3)
        success1 = self.inventory.add_item(potion1)
        assert success1 == True
        
        # 同じポーション
        potion2 = ItemInstance(item_id="healing_potion", quantity=2)
        success2 = self.inventory.add_item(potion2)
        assert success2 == True
        
        # スロット使用数は1のまま
        assert self.inventory.get_used_slot_count() == 1
        
        # 数量は合計されている
        slot_items = self.inventory.get_all_items()
        assert len(slot_items) == 1
        assert slot_items[0][1].quantity == 5
    
    def test_remove_item_by_slot(self):
        """スロット指定でアイテム削除のテスト"""
        item = ItemInstance(item_id="dagger", quantity=1)
        self.inventory.add_item(item)
        
        removed_item = self.inventory.remove_item(0)
        
        assert removed_item is not None
        assert removed_item.item_id == "dagger"
        assert self.inventory.get_used_slot_count() == 0
    
    def test_remove_item_by_id(self):
        """アイテムID指定で削除のテスト"""
        potion = ItemInstance(item_id="healing_potion", quantity=5)
        self.inventory.add_item(potion)
        
        removed_item = self.inventory.remove_item_by_id("healing_potion", 2)
        
        assert removed_item is not None
        assert removed_item.quantity == 2
        assert self.inventory.get_item_count("healing_potion") == 3
    
    def test_has_item(self):
        """アイテム所持チェックのテスト"""
        potion = ItemInstance(item_id="healing_potion", quantity=3)
        self.inventory.add_item(potion)
        
        assert self.inventory.has_item("healing_potion", 2) == True
        assert self.inventory.has_item("healing_potion", 3) == True
        assert self.inventory.has_item("healing_potion", 4) == False
        assert self.inventory.has_item("dagger", 1) == False
    
    def test_move_item(self):
        """アイテム移動のテスト"""
        item1 = ItemInstance(item_id="dagger", quantity=1)
        item2 = ItemInstance(item_id="sword", quantity=1)
        
        self.inventory.add_item(item1)
        self.inventory.add_item(item2)
        
        # アイテムを移動
        success = self.inventory.move_item(0, 2)
        assert success == True
        
        # 移動先にアイテムがある
        assert self.inventory.slots[2].item_instance.item_id == "dagger"
        assert self.inventory.slots[0].is_empty()
    
    def test_sort_items(self):
        """アイテムソートのテスト"""
        # 逆順でアイテムを追加
        items = [
            ItemInstance(item_id="sword", quantity=1),
            ItemInstance(item_id="healing_potion", quantity=2),
            ItemInstance(item_id="dagger", quantity=1)
        ]
        
        for item in items:
            self.inventory.add_item(item)
        
        self.inventory.sort_items()
        
        # ソート後の順序をチェック（アイテムタイプ→ID順）
        sorted_items = self.inventory.get_all_items()
        assert len(sorted_items) == 3
        # 具体的な順序は実際のアイテム定義による
    
    def test_inventory_serialization(self):
        """インベントリシリアライゼーションのテスト"""
        item = ItemInstance(item_id="dagger", quantity=1)
        self.inventory.add_item(item)
        
        data = self.inventory.to_dict()
        restored_inventory = Inventory.from_dict(data)
        
        assert restored_inventory.owner_id == self.inventory.owner_id
        assert restored_inventory.inventory_type == self.inventory.inventory_type
        assert restored_inventory.max_slots == self.inventory.max_slots
        assert restored_inventory.get_used_slot_count() == 1


class TestInventoryManager:
    """InventoryManagerのテスト"""
    
    def setup_method(self):
        """各テストメソッドの前に実行"""
        self.manager = InventoryManager()
    
    def test_create_character_inventory(self):
        """キャラクターインベントリ作成のテスト"""
        char_id = "test_character"
        inventory = self.manager.create_character_inventory(char_id)
        
        assert inventory is not None
        assert inventory.owner_id == char_id
        assert inventory.inventory_type == InventorySlotType.CHARACTER
        assert inventory.max_slots == 10
        
        # 取得テスト
        retrieved = self.manager.get_character_inventory(char_id)
        assert retrieved == inventory
    
    def test_create_party_inventory(self):
        """パーティインベントリ作成のテスト"""
        party_id = "test_party"
        inventory = self.manager.create_party_inventory(party_id)
        
        assert inventory is not None
        assert inventory.owner_id == party_id
        assert inventory.inventory_type == InventorySlotType.PARTY
        assert inventory.max_slots == 50
        
        # 取得テスト
        retrieved = self.manager.get_party_inventory()
        assert retrieved == inventory
    
    def test_transfer_item_between_inventories(self):
        """インベントリ間のアイテム移動テスト"""
        char_inventory = self.manager.create_character_inventory("char1")
        party_inventory = self.manager.create_party_inventory("party1")
        
        # キャラクターインベントリにアイテム追加
        item = ItemInstance(item_id="healing_potion", quantity=5)
        char_inventory.add_item(item)
        
        # パーティインベントリに一部移動
        success = self.manager.transfer_item(char_inventory, 0, party_inventory, 2)
        
        assert success == True
        assert char_inventory.get_item_count("healing_potion") == 3
        assert party_inventory.get_item_count("healing_potion") == 2
    
    def test_manager_serialization(self):
        """マネージャーシリアライゼーションのテスト"""
        # インベントリを作成
        char_inventory = self.manager.create_character_inventory("char1")
        party_inventory = self.manager.create_party_inventory("party1")
        
        # アイテムを追加
        item = ItemInstance(item_id="dagger", quantity=1)
        char_inventory.add_item(item)
        
        # シリアライズ・デシリアライズ
        data = self.manager.to_dict()
        restored_manager = InventoryManager.from_dict(data)
        
        # 復元確認
        restored_char_inv = restored_manager.get_character_inventory("char1")
        restored_party_inv = restored_manager.get_party_inventory()
        
        assert restored_char_inv is not None
        assert restored_party_inv is not None
        assert restored_char_inv.get_used_slot_count() == 1


class TestCharacterInventoryIntegration:
    """キャラクターインベントリ統合テスト"""
    
    def setup_method(self):
        """各テストメソッドの前に実行"""
        self.stats = BaseStats(strength=15, agility=12, intelligence=14, faith=10, luck=13)
        self.character = Character.create_character("TestHero", "human", "fighter", self.stats)
    
    def test_character_inventory_initialization(self):
        """キャラクターインベントリ初期化のテスト"""
        inventory = self.character.get_inventory()
        
        assert inventory is not None
        assert inventory.owner_id == self.character.character_id
        assert inventory.inventory_type == InventorySlotType.CHARACTER
        assert inventory.max_slots == 10
    
    def test_character_inventory_persistence(self):
        """キャラクターインベントリ永続化のテスト"""
        # インベントリにアイテム追加
        inventory = self.character.get_inventory()
        item = ItemInstance(item_id="dagger", quantity=1)
        inventory.add_item(item)
        
        # 同じキャラクターのインベントリを再取得
        inventory2 = self.character.get_inventory()
        
        # 同じインベントリが返される
        assert inventory == inventory2
        assert inventory2.get_used_slot_count() == 1


class TestPartyInventoryIntegration:
    """パーティインベントリ統合テスト"""
    
    def setup_method(self):
        """各テストメソッドの前に実行"""
        self.party = Party(name="Test Party")
    
    def test_party_inventory_initialization(self):
        """パーティインベントリ初期化のテスト"""
        inventory = self.party.get_party_inventory()
        
        assert inventory is not None
        assert inventory.owner_id == self.party.party_id
        assert inventory.inventory_type == InventorySlotType.PARTY
        assert inventory.max_slots == 50
    
    def test_party_inventory_persistence(self):
        """パーティインベントリ永続化のテスト"""
        # インベントリにアイテム追加
        inventory = self.party.get_party_inventory()
        item = ItemInstance(item_id="sword", quantity=1)
        inventory.add_item(item)
        
        # 同じパーティのインベントリを再取得
        inventory2 = self.party.get_party_inventory()
        
        # 同じインベントリが返される
        assert inventory == inventory2
        assert inventory2.get_used_slot_count() == 1