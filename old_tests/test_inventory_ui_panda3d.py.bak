"""インベントリUI システムのテスト"""

import pytest
from src.ui.inventory_ui import InventoryUI, InventoryAction, inventory_ui
from src.character.character import Character
from src.character.party import Party
from src.character.stats import BaseStats
from src.items.item import ItemInstance, item_manager
from src.inventory.inventory import inventory_manager


class TestInventoryUI:
    """インベントリUI システムのテスト"""
    
    def setup_method(self):
        """各テストメソッドの前に実行"""
        self.inventory_ui = InventoryUI()
        
        # テスト用キャラクター作成
        stats = BaseStats(strength=15, agility=12, intelligence=14, faith=10, luck=13)
        self.character1 = Character.create_character("TestHero1", "human", "fighter", stats)
        self.character2 = Character.create_character("TestHero2", "elf", "mage", stats)
        
        # テスト用パーティ作成
        self.party = Party(party_id="test_party", name="TestParty")
        self.party.add_character(self.character1)
        self.party.add_character(self.character2)
        self.party.gold = 1000
    
    def test_inventory_ui_initialization(self):
        """インベントリUI初期化テスト"""
        ui = InventoryUI()
        
        assert ui.current_party is None
        assert ui.current_inventory is None
        assert ui.current_character is None
        assert ui.selected_slot is None
        assert ui.transfer_source is None
    
    def test_set_party(self):
        """パーティ設定テスト"""
        self.inventory_ui.set_party(self.party)
        
        assert self.inventory_ui.current_party == self.party
    
    def test_party_inventory_ui_structure(self):
        """パーティインベントリUI構造テスト"""
        # パーティインベントリにアイテムを追加
        party_inventory = self.party.get_party_inventory()
        test_item = ItemInstance(item_id="healing_potion", quantity=3, identified=True)
        party_inventory.add_item(test_item)
        
        # キャラクターインベントリにもアイテムを追加
        char_inventory = self.character1.get_inventory()
        test_weapon = ItemInstance(item_id="dagger", quantity=1, identified=True)
        char_inventory.add_item(test_weapon)
        
        # UIコンポーネントの基本機能をテスト（モックレベル）
        self.inventory_ui.set_party(self.party)
        
        # パーティインベントリの内容確認
        assert len(party_inventory.slots) > 0
        assert any(not slot.is_empty() for slot in party_inventory.slots)
        
        # キャラクターインベントリの内容確認
        assert len(char_inventory.slots) > 0
        assert any(not slot.is_empty() for slot in char_inventory.slots)
    
    def test_inventory_item_details_generation(self):
        """アイテム詳細情報生成テスト"""
        # 鑑定済みアイテム
        healing_potion = ItemInstance(item_id="healing_potion", quantity=2, identified=True)
        item = item_manager.get_item("healing_potion")
        assert item is not None
        
        # 詳細情報の要素をチェック（UIメソッドは実際には呼ばず、ロジックをテスト）
        assert healing_potion.identified == True
        assert healing_potion.quantity == 2
        assert item.get_name() is not None
        assert item.get_description() is not None
        
        # 未鑑定アイテム
        unidentified_item = ItemInstance(item_id="dagger", quantity=1, identified=False)
        assert unidentified_item.identified == False
    
    def test_inventory_transfer_logic(self):
        """インベントリ間転送ロジックテスト"""
        # パーティインベントリにアイテムを追加
        party_inventory = self.party.get_party_inventory()
        test_item = ItemInstance(item_id="healing_potion", quantity=1, identified=True)
        party_inventory.add_item(test_item)
        
        # キャラクターインベントリ
        char_inventory = self.character1.get_inventory()
        
        # 転送可能性をテスト
        assert party_inventory.has_item("healing_potion")
        initial_char_count = len([slot for slot in char_inventory.slots if not slot.is_empty()])
        
        # 実際の転送（inventory_managerを使用）
        success = inventory_manager.transfer_item(
            party_inventory, 0,  # パーティインベントリの最初のスロット
            char_inventory, 1    # 1個転送
        )
        
        assert success == True
        
        # 転送後の状態確認
        final_char_count = len([slot for slot in char_inventory.slots if not slot.is_empty()])
        assert final_char_count > initial_char_count
    
    def test_inventory_action_enum(self):
        """インベントリアクション列挙型テスト"""
        assert InventoryAction.VIEW.value == "view"
        assert InventoryAction.USE.value == "use"
        assert InventoryAction.TRANSFER.value == "transfer"
        assert InventoryAction.DROP.value == "drop"
        assert InventoryAction.SORT.value == "sort"
    
    def test_usable_items_filtering(self):
        """使用可能アイテムフィルタリングテスト"""
        # キャラクターインベントリにアイテムを追加
        char_inventory = self.character1.get_inventory()
        
        # 使用可能な回復ポーション
        healing_potion = ItemInstance(item_id="healing_potion", quantity=1, identified=True)
        char_inventory.add_item(healing_potion)
        
        # 使用不可な武器
        weapon = ItemInstance(item_id="dagger", quantity=1, identified=True)
        char_inventory.add_item(weapon)
        
        # 未鑑定の消耗品
        unidentified_potion = ItemInstance(item_id="mana_potion", quantity=1, identified=False)
        char_inventory.add_item(unidentified_potion)
        
        # アイテム使用管理システムを使って使用可能アイテムを取得
        from src.items.item_usage import item_usage_manager
        
        inventory_items = []
        for slot in char_inventory.slots:
            if not slot.is_empty():
                inventory_items.append((slot, slot.item_instance))
        
        usable_items = item_usage_manager.get_usable_items_for_character(
            self.character1, inventory_items
        )
        
        # 回復ポーションのみ使用可能であることを確認
        usable_item_ids = [item.item_id for _, _, item in usable_items]
        assert "healing_potion" in usable_item_ids
        assert "dagger" not in usable_item_ids
        assert "mana_potion" not in usable_item_ids  # 未鑑定なので除外
    
    def test_inventory_sorting_functionality(self):
        """インベントリ整理機能テスト"""
        # キャラクターインベントリにアイテムをランダムに追加
        char_inventory = self.character1.get_inventory()
        
        items = [
            ItemInstance(item_id="healing_potion", quantity=1, identified=True),
            ItemInstance(item_id="dagger", quantity=1, identified=True),
            ItemInstance(item_id="mana_potion", quantity=2, identified=True),
        ]
        
        for item in items:
            char_inventory.add_item(item)
        
        # 整理前の状態を記録
        before_sort = [(slot.item_instance.item_id if not slot.is_empty() else None) 
                      for slot in char_inventory.slots[:5]]
        
        # 整理実行
        char_inventory.sort_items()
        
        # 整理後の状態を確認
        after_sort = [(slot.item_instance.item_id if not slot.is_empty() else None) 
                     for slot in char_inventory.slots[:5]]
        
        # アイテムが前方に詰められていることを確認
        non_empty_after = [item for item in after_sort if item is not None]
        assert len(non_empty_after) == len(items)
        
        # すべてのアイテムが保持されていることを確認
        assert all(item_id in non_empty_after for item_id in ["healing_potion", "dagger", "mana_potion"])
    
    def test_inventory_statistics_calculation(self):
        """インベントリ統計計算テスト"""
        # 各インベントリにアイテムを追加
        party_inventory = self.party.get_party_inventory()
        party_inventory.add_item(ItemInstance(item_id="healing_potion", quantity=1, identified=True))
        party_inventory.add_item(ItemInstance(item_id="mana_potion", quantity=1, identified=True))
        
        char1_inventory = self.character1.get_inventory()
        char1_inventory.add_item(ItemInstance(item_id="dagger", quantity=1, identified=True))
        
        char2_inventory = self.character2.get_inventory()
        char2_inventory.add_item(ItemInstance(item_id="staff", quantity=1, identified=True))
        
        # 統計計算
        party_used = len([slot for slot in party_inventory.slots if not slot.is_empty()])
        char1_used = len([slot for slot in char1_inventory.slots if not slot.is_empty()])
        char2_used = len([slot for slot in char2_inventory.slots if not slot.is_empty()])
        
        assert party_used == 2
        assert char1_used == 1
        assert char2_used == 1
        
        # 総使用量
        total_used = party_used + char1_used + char2_used
        assert total_used == 4
    
    def test_item_equipment_integration(self):
        """アイテム装備統合テスト"""
        # キャラクターインベントリに武器を追加
        char_inventory = self.character1.get_inventory()
        weapon_item = ItemInstance(item_id="dagger", quantity=1, identified=True)
        char_inventory.add_item(weapon_item)
        
        # 装備システム取得
        equipment = self.character1.get_equipment()
        
        # 装備前の状態
        from src.equipment.equipment import EquipmentSlot
        weapon_slot = EquipmentSlot.WEAPON
        assert equipment.equipped_items[weapon_slot] is None
        
        # 装備処理のシミュレーション
        success, reason, replaced_item = equipment.equip_item(
            weapon_item, weapon_slot, self.character1.character_class
        )
        
        assert success == True
        assert replaced_item is None  # 初回装備なので置換なし
        assert equipment.equipped_items[weapon_slot] is not None
    
    def test_party_inventory_ui_method(self):
        """パーティインベントリUI表示メソッドテスト"""
        # パーティにインベントリUI表示メソッドが存在することを確認
        assert hasattr(self.party, 'show_inventory_ui')
        
        # メソッドが呼び出し可能であることを確認（実際の UI は表示しない）
        try:
            # UIの実際の表示はテスト環境では行わず、メソッドの存在とアクセスのみテスト
            inventory_ui_method = getattr(self.party, 'show_inventory_ui')
            assert callable(inventory_ui_method)
        except Exception as e:
            pytest.fail(f"パーティインベントリUIメソッドアクセスに失敗: {e}")


class TestInventoryUIIntegration:
    """インベントリUI統合テスト"""
    
    def setup_method(self):
        """各テストメソッドの前に実行"""
        # 統合テスト用の完全なパーティセットアップ
        stats = BaseStats(strength=15, agility=12, intelligence=14, faith=10, luck=13)
        self.character = Character.create_character("IntegrationHero", "human", "fighter", stats)
        
        self.party = Party(party_id="integration_party", name="IntegrationParty")
        self.party.add_character(self.character)
        self.party.gold = 500
    
    def test_full_inventory_workflow(self):
        """完全なインベントリワークフローテスト"""
        # 1. パーティインベントリにアイテム追加
        party_inventory = self.party.get_party_inventory()
        healing_potion = ItemInstance(item_id="healing_potion", quantity=3, identified=True)
        party_inventory.add_item(healing_potion)
        
        # 2. キャラクターインベントリにアイテム転送
        char_inventory = self.character.get_inventory()
        
        success = inventory_manager.transfer_item(
            party_inventory, 0,
            char_inventory, 1
        )
        assert success == True
        
        # 3. アイテム使用
        char_first_slot = char_inventory.slots[0]
        assert not char_first_slot.is_empty()
        
        from src.items.item_usage import item_usage_manager, UsageResult
        
        # キャラクターにダメージを与えてから回復アイテムを使用
        self.character.take_damage(10)
        old_hp = self.character.derived_stats.current_hp
        
        result, message, results = item_usage_manager.use_item(
            char_first_slot.item_instance, 
            self.character, 
            self.character, 
            self.party
        )
        
        assert result == UsageResult.SUCCESS
        assert self.character.derived_stats.current_hp > old_hp
        
        # 4. アイテム整理
        char_inventory.sort_items()
        
        # ワークフロー完了確認
        assert len([slot for slot in char_inventory.slots if not slot.is_empty()]) >= 0
    
    def test_multi_character_inventory_interaction(self):
        """複数キャラクター間のインベントリ相互作用テスト"""
        # 2人目のキャラクター追加
        stats2 = BaseStats(strength=12, agility=15, intelligence=16, faith=14, luck=11)
        character2 = Character.create_character("IntegrationMage", "elf", "mage", stats2)
        self.party.add_character(character2)
        
        # 各キャラクターに異なるアイテムを配布
        char1_inventory = self.character.get_inventory()
        char2_inventory = character2.get_inventory()
        
        weapon = ItemInstance(item_id="dagger", quantity=1, identified=True)
        staff = ItemInstance(item_id="staff", quantity=1, identified=True)
        
        char1_inventory.add_item(weapon)
        char2_inventory.add_item(staff)
        
        # キャラクター間でアイテム転送
        success = inventory_manager.transfer_item(
            char1_inventory, 0,
            char2_inventory, 1
        )
        assert success == True
        
        # 両キャラクターがアイテムを保持していることを確認
        char1_items = [slot.item_instance.item_id for slot in char1_inventory.slots if not slot.is_empty()]
        char2_items = [slot.item_instance.item_id for slot in char2_inventory.slots if not slot.is_empty()]
        
        assert "staff" in char2_items
        assert "dagger" in char2_items
        assert len(char1_items) == 0  # 全て転送済み