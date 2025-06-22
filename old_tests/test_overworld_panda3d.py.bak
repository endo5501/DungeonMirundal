"""地上部システムのテスト"""

import pytest
from src.overworld.base_facility import BaseFacility, FacilityType, FacilityManager
from src.overworld.overworld_manager import OverworldManager, OverworldLocation
from src.overworld.facilities.guild import AdventurersGuild
from src.overworld.facilities.inn import Inn
from src.overworld.facilities.shop import Shop
from src.overworld.facilities.temple import Temple
from src.overworld.facilities.magic_guild import MagicGuild
from src.character.character import Character, CharacterStatus
from src.character.party import Party
from src.character.stats import BaseStats
from src.items.item import Item, ItemManager, ItemInstance, ItemType


class TestFacilityManager:
    """FacilityManagerのテスト"""
    
    def setup_method(self):
        """各テストメソッドの前に実行"""
        self.facility_manager = FacilityManager()
        self.test_party = self._create_test_party()
    
    def _create_test_party(self) -> Party:
        """テスト用パーティの作成"""
        party = Party(name="Test Party")
        stats = BaseStats(strength=15, agility=12, intelligence=14, faith=10, luck=13)
        character = Character.create_character("TestHero", "human", "fighter", stats)
        party.add_character(character)
        return party
    
    def test_register_facility(self):
        """施設登録のテスト"""
        guild = AdventurersGuild()
        self.facility_manager.register_facility(guild)
        
        assert "guild" in self.facility_manager.facilities
        assert self.facility_manager.get_facility("guild") == guild
    
    def test_enter_facility(self):
        """施設入場のテスト"""
        guild = AdventurersGuild()
        self.facility_manager.register_facility(guild)
        
        success = self.facility_manager.enter_facility("guild", self.test_party)
        
        assert success == True
        assert self.facility_manager.current_facility == "guild"
        assert guild.is_active == True
        assert guild.current_party == self.test_party
    
    def test_exit_facility(self):
        """施設退場のテスト"""
        guild = AdventurersGuild()
        self.facility_manager.register_facility(guild)
        
        # 入場してから退場
        self.facility_manager.enter_facility("guild", self.test_party)
        success = self.facility_manager.exit_current_facility()
        
        assert success == True
        assert self.facility_manager.current_facility is None
        assert guild.is_active == False
        assert guild.current_party is None


class TestOverworldManager:
    """OverworldManagerのテスト"""
    
    def setup_method(self):
        """各テストメソッドの前に実行"""
        self.overworld_manager = OverworldManager()
        self.test_party = self._create_test_party()
    
    def _create_test_party(self) -> Party:
        """テスト用パーティの作成"""
        party = Party(name="Test Party")
        stats = BaseStats(strength=15, agility=12, intelligence=14, faith=10, luck=13)
        character = Character.create_character("TestHero", "human", "fighter", stats)
        party.add_character(character)
        return party
    
    def test_enter_overworld(self):
        """地上部入場のテスト"""
        success = self.overworld_manager.enter_overworld(self.test_party)
        
        assert success == True
        assert self.overworld_manager.is_active == True
        assert self.overworld_manager.current_party == self.test_party
        assert self.overworld_manager.current_location == OverworldLocation.TOWN_CENTER
    
    def test_exit_overworld(self):
        """地上部退場のテスト"""
        self.overworld_manager.enter_overworld(self.test_party)
        success = self.overworld_manager.exit_overworld()
        
        assert success == True
        assert self.overworld_manager.is_active == False
        assert self.overworld_manager.current_party is None
    
    def test_auto_recovery_from_dungeon(self):
        """ダンジョンからの自動回復テスト"""
        # キャラクターにダメージを与える
        character = list(self.test_party.characters.values())[0]
        character.take_damage(10)
        character.derived_stats.current_mp = 0
        character.status = CharacterStatus.INJURED
        
        old_hp = character.derived_stats.current_hp
        old_mp = character.derived_stats.current_mp
        old_status = character.status
        
        # ダンジョンから戻る（自動回復あり）
        success = self.overworld_manager.enter_overworld(self.test_party, from_dungeon=True)
        
        assert success == True
        assert character.derived_stats.current_hp == character.derived_stats.max_hp
        assert character.derived_stats.current_mp == character.derived_stats.max_mp
        assert character.status == CharacterStatus.GOOD
    
    def test_auto_recovery_does_not_revive_dead(self):
        """自動回復が死亡キャラクターを蘇生しないテスト"""
        character = list(self.test_party.characters.values())[0]
        character.status = CharacterStatus.DEAD
        
        self.overworld_manager.enter_overworld(self.test_party, from_dungeon=True)
        
        # 死亡状態は回復しない
        assert character.status == CharacterStatus.DEAD


class TestAdventurersGuild:
    """AdventurersGuildのテスト"""
    
    def setup_method(self):
        """各テストメソッドの前に実行"""
        self.guild = AdventurersGuild()
        self.test_party = self._create_test_party()
    
    def _create_test_party(self) -> Party:
        """テスト用パーティの作成"""
        party = Party(name="Test Party")
        return party
    
    def test_guild_initialization(self):
        """ギルド初期化のテスト"""
        assert self.guild.facility_id == "guild"
        assert self.guild.facility_type == FacilityType.GUILD
        assert self.guild.created_characters == []
    
    def test_guild_enter_exit(self):
        """ギルド入退場のテスト"""
        # 入場
        success = self.guild.enter(self.test_party)
        assert success == True
        assert self.guild.is_active == True
        assert self.guild.current_party == self.test_party
        
        # 退場
        success = self.guild.exit()
        assert success == True
        assert self.guild.is_active == False
        assert self.guild.current_party is None


class TestItemSystem:
    """アイテムシステムのテスト"""
    
    def setup_method(self):
        """各テストメソッドの前に実行"""
        self.item_manager = ItemManager()
    
    def test_item_loading(self):
        """アイテム読み込みのテスト"""
        # アイテムが読み込まれているかチェック
        assert len(self.item_manager.items) > 0
        
        # 特定のアイテムが存在するかチェック
        dagger = self.item_manager.get_item("dagger")
        assert dagger is not None
        assert dagger.item_type == ItemType.WEAPON
        assert dagger.get_attack_power() > 0
    
    def test_item_instance_creation(self):
        """アイテムインスタンス作成のテスト"""
        instance = self.item_manager.create_item_instance("healing_potion", quantity=3)
        
        assert instance is not None
        assert instance.item_id == "healing_potion"
        assert instance.quantity == 3
        assert instance.identified == True
        assert instance.condition == 1.0
    
    def test_item_display_name(self):
        """アイテム表示名のテスト"""
        instance = self.item_manager.create_item_instance("dagger", quantity=2)
        display_name = self.item_manager.get_item_display_name(instance)
        
        assert "ダガー" in display_name
        assert "x2" in display_name
    
    def test_item_identification(self):
        """アイテム鑑定のテスト"""
        instance = self.item_manager.create_item_instance("dagger", identified=False)
        
        assert instance.identified == False
        
        success = self.item_manager.identify_item(instance)
        
        assert success == True
        assert instance.identified == True
        
        # 再鑑定は失敗
        success = self.item_manager.identify_item(instance)
        assert success == False
    
    def test_item_sell_price(self):
        """アイテム売却価格のテスト"""
        instance = self.item_manager.create_item_instance("dagger")
        sell_price = self.item_manager.get_sell_price(instance)
        
        dagger = self.item_manager.get_item("dagger")
        expected_price = dagger.get_sell_price()
        
        assert sell_price == expected_price
        assert sell_price > 0
    
    def test_item_condition_affects_price(self):
        """アイテム状態が価格に影響するテスト"""
        instance = self.item_manager.create_item_instance("dagger")
        original_price = self.item_manager.get_sell_price(instance)
        
        # 状態を悪化させる
        instance.condition = 0.5
        damaged_price = self.item_manager.get_sell_price(instance)
        
        assert damaged_price < original_price
    
    def test_item_repair(self):
        """アイテム修理のテスト"""
        instance = self.item_manager.create_item_instance("dagger")
        instance.condition = 0.7
        
        repair_cost = self.item_manager.repair_item(instance)
        assert repair_cost > 0
        
        success = self.item_manager.perform_repair(instance)
        assert success == True
        assert instance.condition == 1.0
        
        # 完全な状態のアイテムは修理不要
        repair_cost = self.item_manager.repair_item(instance)
        assert repair_cost == 0
    
    def test_item_class_restrictions(self):
        """アイテムクラス制限のテスト"""
        staff = self.item_manager.get_item("staff")
        
        # 魔術師は使用可能
        assert staff.can_use("mage") == True
        
        # 戦士は使用不可（スタッフの使用可能クラスに含まれていない）
        assert staff.can_use("fighter") == False
    
    def test_item_serialization(self):
        """アイテムシリアライゼーションのテスト"""
        instance = ItemInstance(
            item_id="dagger",
            quantity=2,
            identified=False,
            condition=0.8
        )
        
        data = instance.to_dict()
        restored = ItemInstance.from_dict(data)
        
        assert restored.item_id == instance.item_id
        assert restored.quantity == instance.quantity
        assert restored.identified == instance.identified
        assert restored.condition == instance.condition


class TestAllFacilities:
    """全施設のテスト"""
    
    def setup_method(self):
        """各テストメソッドの前に実行"""
        self.facility_manager = FacilityManager()
        self.test_party = self._create_test_party()
    
    def _create_test_party(self) -> Party:
        """テスト用パーティの作成"""
        party = Party(name="Test Party")
        stats = BaseStats(strength=15, agility=12, intelligence=14, faith=10, luck=13)
        character = Character.create_character("TestHero", "human", "fighter", stats)
        party.add_character(character)
        party.gold = 1000  # テスト用ゴールド
        return party
    
    def test_all_facilities_initialization(self):
        """全施設の初期化テスト"""
        # 各施設を作成
        guild = AdventurersGuild()
        inn = Inn()
        shop = Shop()
        temple = Temple()
        magic_guild = MagicGuild()
        
        # 施設登録
        self.facility_manager.register_facility(guild)
        self.facility_manager.register_facility(inn)
        self.facility_manager.register_facility(shop)
        self.facility_manager.register_facility(temple)
        self.facility_manager.register_facility(magic_guild)
        
        # 登録確認
        assert len(self.facility_manager.facilities) == 5
        assert "guild" in self.facility_manager.facilities
        assert "inn" in self.facility_manager.facilities
        assert "shop" in self.facility_manager.facilities
        assert "temple" in self.facility_manager.facilities
        assert "magic_guild" in self.facility_manager.facilities
    
    def test_facility_enter_exit_cycle(self):
        """施設の入退場サイクルテスト"""
        # 全施設を登録
        facilities = [
            AdventurersGuild(),
            Inn(),
            Shop(),
            Temple(),
            MagicGuild()
        ]
        
        for facility in facilities:
            self.facility_manager.register_facility(facility)
        
        # 各施設への入退場をテスト
        for facility in facilities:
            # 入場
            success = self.facility_manager.enter_facility(facility.facility_id, self.test_party)
            assert success == True
            assert self.facility_manager.current_facility == facility.facility_id
            assert facility.is_active == True
            assert facility.current_party == self.test_party
            
            # 退場
            success = self.facility_manager.exit_current_facility()
            assert success == True
            assert self.facility_manager.current_facility is None
            assert facility.is_active == False
            assert facility.current_party is None


class TestInn:
    """宿屋のテスト"""
    
    def setup_method(self):
        """各テストメソッドの前に実行"""
        self.inn = Inn()
        self.test_party = self._create_test_party()
    
    def _create_test_party(self) -> Party:
        """テスト用パーティの作成"""
        party = Party(name="Test Party")
        return party
    
    def test_inn_initialization(self):
        """宿屋初期化のテスト"""
        assert self.inn.facility_id == "inn"
        assert self.inn.facility_type == FacilityType.INN
    
    def test_inn_enter_exit(self):
        """宿屋入退場のテスト"""
        # 入場
        success = self.inn.enter(self.test_party)
        assert success == True
        assert self.inn.is_active == True
        assert self.inn.current_party == self.test_party
        
        # 退場
        success = self.inn.exit()
        assert success == True
        assert self.inn.is_active == False
        assert self.inn.current_party is None


class TestShop:
    """商店のテスト"""
    
    def setup_method(self):
        """各テストメソッドの前に実行"""
        self.shop = Shop()
        self.test_party = self._create_test_party()
    
    def _create_test_party(self) -> Party:
        """テスト用パーティの作成"""
        party = Party(name="Test Party")
        party.gold = 1000
        return party
    
    def test_shop_initialization(self):
        """商店初期化のテスト"""
        assert self.shop.facility_id == "shop"
        assert self.shop.facility_type == FacilityType.SHOP
        assert len(self.shop.inventory) > 0  # 基本在庫があること
    
    def test_shop_inventory_management(self):
        """商店在庫管理のテスト"""
        initial_count = len(self.shop.inventory)
        
        # アイテム追加
        self.shop.add_item_to_inventory("test_item")
        assert len(self.shop.inventory) == initial_count + 1
        assert "test_item" in self.shop.inventory
        
        # アイテム削除
        self.shop.remove_item_from_inventory("test_item")
        assert len(self.shop.inventory) == initial_count
        assert "test_item" not in self.shop.inventory
    
    def test_shop_get_inventory_items(self):
        """商店在庫アイテム取得のテスト"""
        items = self.shop.get_inventory_items()
        assert len(items) > 0
        # 在庫にあるアイテムが実際のItemオブジェクトとして取得できることを確認
        for item in items:
            assert hasattr(item, 'item_id')
            assert hasattr(item, 'get_name')


class TestTemple:
    """教会のテスト"""
    
    def setup_method(self):
        """各テストメソッドの前に実行"""
        self.temple = Temple()
        self.test_party = self._create_test_party()
    
    def _create_test_party(self) -> Party:
        """テスト用パーティの作成"""
        party = Party(name="Test Party")
        party.gold = 2000
        return party
    
    def test_temple_initialization(self):
        """教会初期化のテスト"""
        assert self.temple.facility_id == "temple"
        assert self.temple.facility_type == FacilityType.TEMPLE
        assert 'resurrection' in self.temple.service_costs
        assert 'ash_restoration' in self.temple.service_costs
        assert 'blessing' in self.temple.service_costs
    
    def test_temple_service_costs(self):
        """教会サービス料金のテスト"""
        assert self.temple.service_costs['resurrection'] > 0
        assert self.temple.service_costs['ash_restoration'] > self.temple.service_costs['resurrection']
        assert self.temple.service_costs['blessing'] > 0


class TestMagicGuild:
    """魔術師ギルドのテスト"""
    
    def setup_method(self):
        """各テストメソッドの前に実行"""
        self.magic_guild = MagicGuild()
        self.test_party = self._create_test_party()
    
    def _create_test_party(self) -> Party:
        """テスト用パーティの作成"""
        party = Party(name="Test Party")
        party.gold = 3000
        return party
    
    def test_magic_guild_initialization(self):
        """魔術師ギルド初期化のテスト"""
        assert self.magic_guild.facility_id == "magic_guild"
        assert self.magic_guild.facility_type == FacilityType.MAGIC_GUILD
        assert len(self.magic_guild.available_spells) > 0
        assert 'fire' in self.magic_guild.available_spells
        assert 'heal' in self.magic_guild.available_spells
    
    def test_magic_guild_spell_data(self):
        """魔術師ギルド魔法データのテスト"""
        fire_spell = self.magic_guild.available_spells['fire']
        assert 'name' in fire_spell
        assert 'level' in fire_spell
        assert 'cost' in fire_spell
        assert fire_spell['level'] > 0
        assert fire_spell['cost'] > 0
    
    def test_magic_guild_service_costs(self):
        """魔術師ギルドサービス料金のテスト"""
        assert self.magic_guild.service_costs['spell_learning'] > 0
        assert self.magic_guild.service_costs['item_identification'] > 0
        assert self.magic_guild.service_costs['magical_analysis'] > 0