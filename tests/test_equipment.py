"""装備システムのテスト"""

import pytest
from src.equipment.equipment import (
    Equipment, EquipmentSlot, EquipmentBonus, EquipmentManager,
    equipment_manager
)
from src.items.item import ItemInstance, ItemManager, item_manager
from src.character.character import Character
from src.character.stats import BaseStats


class TestEquipmentBonus:
    """EquipmentBonusのテスト"""
    
    def test_bonus_initialization(self):
        """ボーナス初期化のテスト"""
        bonus = EquipmentBonus()
        
        assert bonus.strength == 0
        assert bonus.agility == 0
        assert bonus.intelligence == 0
        assert bonus.faith == 0
        assert bonus.luck == 0
        assert bonus.attack_power == 0
        assert bonus.defense == 0
        assert bonus.magic_power == 0
        assert bonus.magic_resistance == 0
    
    def test_bonus_addition(self):
        """ボーナス加算のテスト"""
        bonus1 = EquipmentBonus(strength=5, attack_power=10)
        bonus2 = EquipmentBonus(strength=3, defense=5)
        
        total = bonus1 + bonus2
        
        assert total.strength == 8
        assert total.attack_power == 10
        assert total.defense == 5
    
    def test_bonus_serialization(self):
        """ボーナスシリアライゼーションのテスト"""
        bonus = EquipmentBonus(
            strength=5,
            agility=3,
            attack_power=15,
            defense=8
        )
        
        data = bonus.to_dict()
        restored = EquipmentBonus.from_dict(data)
        
        assert restored.strength == bonus.strength
        assert restored.agility == bonus.agility
        assert restored.attack_power == bonus.attack_power
        assert restored.defense == bonus.defense


class TestEquipment:
    """Equipmentのテスト"""
    
    def setup_method(self):
        """各テストメソッドの前に実行"""
        self.equipment = Equipment(owner_id="test_char")
        self.weapon_item = ItemInstance(
            item_id="dagger",
            quantity=1,
            identified=True
        )
        self.armor_item = ItemInstance(
            item_id="leather_armor",
            quantity=1,
            identified=True
        )
    
    def test_equipment_initialization(self):
        """装備システム初期化のテスト"""
        assert self.equipment.owner_id == "test_char"
        assert len(self.equipment.equipped_items) == 4  # 4つのスロット
        
        for slot in EquipmentSlot:
            assert self.equipment.is_slot_empty(slot)
    
    def test_can_equip_weapon(self):
        """武器装備可能性チェックのテスト"""
        can_equip, reason = self.equipment.can_equip_item(
            self.weapon_item, 
            EquipmentSlot.WEAPON, 
            "fighter"
        )
        
        assert can_equip == True
        assert reason == ""
    
    def test_cannot_equip_wrong_slot_type(self):
        """間違ったスロットタイプの装備不可テスト"""
        can_equip, reason = self.equipment.can_equip_item(
            self.weapon_item, 
            EquipmentSlot.ARMOR, 
            "fighter"
        )
        
        assert can_equip == False
        assert "防具スロットには防具のみ" in reason
    
    def test_cannot_equip_wrong_class(self):
        """クラス制限による装備不可テスト"""
        # スタッフは戦士では使用不可
        staff_item = ItemInstance(item_id="staff", quantity=1, identified=True)
        
        can_equip, reason = self.equipment.can_equip_item(
            staff_item, 
            EquipmentSlot.WEAPON, 
            "fighter"
        )
        
        assert can_equip == False
        assert "使用できません" in reason
    
    def test_equip_item_success(self):
        """アイテム装備成功のテスト"""
        success, message, previous = self.equipment.equip_item(
            self.weapon_item, 
            EquipmentSlot.WEAPON, 
            "fighter"
        )
        
        assert success == True
        assert message == "装備成功"
        assert previous is None
        assert self.equipment.get_equipped_item(EquipmentSlot.WEAPON) == self.weapon_item
    
    def test_equip_item_replace_existing(self):
        """既存装備の置き換えテスト"""
        # 最初の武器を装備
        self.equipment.equip_item(self.weapon_item, EquipmentSlot.WEAPON, "fighter")
        
        # 別の武器を装備（置き換え）
        new_weapon = ItemInstance(item_id="short_sword", quantity=1, identified=True)
        success, message, previous = self.equipment.equip_item(
            new_weapon, 
            EquipmentSlot.WEAPON, 
            "fighter"
        )
        
        assert success == True
        assert previous == self.weapon_item
        assert self.equipment.get_equipped_item(EquipmentSlot.WEAPON) == new_weapon
    
    def test_unequip_item(self):
        """装備解除のテスト"""
        # アイテムを装備
        self.equipment.equip_item(self.weapon_item, EquipmentSlot.WEAPON, "fighter")
        
        # 装備解除
        unequipped = self.equipment.unequip_item(EquipmentSlot.WEAPON)
        
        assert unequipped == self.weapon_item
        assert self.equipment.is_slot_empty(EquipmentSlot.WEAPON)
    
    def test_unequip_empty_slot(self):
        """空スロットの装備解除テスト"""
        unequipped = self.equipment.unequip_item(EquipmentSlot.WEAPON)
        
        assert unequipped is None
    
    def test_calculate_equipment_bonus(self):
        """装備ボーナス計算のテスト"""
        # 武器を装備
        self.equipment.equip_item(self.weapon_item, EquipmentSlot.WEAPON, "fighter")
        
        bonus = self.equipment.calculate_equipment_bonus()
        
        # ダガーの攻撃力をチェック
        dagger = item_manager.get_item("dagger")
        expected_attack = dagger.get_attack_power() if dagger else 0
        
        assert bonus.attack_power == expected_attack
    
    def test_get_equipment_summary(self):
        """装備要約取得のテスト"""
        # 武器と防具を装備
        self.equipment.equip_item(self.weapon_item, EquipmentSlot.WEAPON, "fighter")
        self.equipment.equip_item(self.armor_item, EquipmentSlot.ARMOR, "fighter")
        
        summary = self.equipment.get_equipment_summary()
        
        assert summary['equipped_count'] == 2
        assert summary['total_weight'] > 0
        assert EquipmentSlot.WEAPON.value in summary['items']
        assert EquipmentSlot.ARMOR.value in summary['items']
        assert summary['items'][EquipmentSlot.WEAPON.value] is not None
        assert summary['items'][EquipmentSlot.ARMOR.value] is not None
    
    def test_get_empty_slots(self):
        """空スロット取得のテスト"""
        # 初期状態では全スロットが空
        empty_slots = self.equipment.get_empty_slots()
        assert len(empty_slots) == 4
        
        # 武器を装備
        self.equipment.equip_item(self.weapon_item, EquipmentSlot.WEAPON, "fighter")
        
        empty_slots = self.equipment.get_empty_slots()
        assert len(empty_slots) == 3
        assert EquipmentSlot.WEAPON not in empty_slots
    
    def test_equipment_serialization(self):
        """装備システムシリアライゼーションのテスト"""
        # アイテムを装備
        self.equipment.equip_item(self.weapon_item, EquipmentSlot.WEAPON, "fighter")
        
        data = self.equipment.to_dict()
        restored = Equipment.from_dict(data)
        
        assert restored.owner_id == self.equipment.owner_id
        assert restored.get_equipped_item(EquipmentSlot.WEAPON) is not None
        assert restored.get_equipped_item(EquipmentSlot.WEAPON).item_id == "dagger"


class TestEquipmentManager:
    """EquipmentManagerのテスト"""
    
    def setup_method(self):
        """各テストメソッドの前に実行"""
        self.manager = EquipmentManager()
    
    def test_create_character_equipment(self):
        """キャラクター装備システム作成のテスト"""
        char_id = "test_character"
        equipment = self.manager.create_character_equipment(char_id)
        
        assert equipment is not None
        assert equipment.owner_id == char_id
        
        # 取得テスト
        retrieved = self.manager.get_character_equipment(char_id)
        assert retrieved == equipment
    
    def test_remove_character_equipment(self):
        """キャラクター装備システム削除のテスト"""
        char_id = "test_character"
        self.manager.create_character_equipment(char_id)
        
        # 削除前は存在
        assert self.manager.get_character_equipment(char_id) is not None
        
        # 削除
        self.manager.remove_character_equipment(char_id)
        
        # 削除後は存在しない
        assert self.manager.get_character_equipment(char_id) is None
    
    def test_manager_serialization(self):
        """マネージャーシリアライゼーションのテスト"""
        # 装備システムを作成
        char_equipment = self.manager.create_character_equipment("char1")
        
        # アイテムを装備
        weapon = ItemInstance(item_id="dagger", quantity=1, identified=True)
        char_equipment.equip_item(weapon, EquipmentSlot.WEAPON, "fighter")
        
        # シリアライズ・デシリアライズ
        data = self.manager.to_dict()
        restored_manager = EquipmentManager.from_dict(data)
        
        # 復元確認
        restored_equipment = restored_manager.get_character_equipment("char1")
        assert restored_equipment is not None
        assert restored_equipment.get_equipped_item(EquipmentSlot.WEAPON) is not None


class TestCharacterEquipmentIntegration:
    """キャラクター装備システム統合テスト"""
    
    def setup_method(self):
        """各テストメソッドの前に実行"""
        self.stats = BaseStats(strength=15, agility=12, intelligence=14, faith=10, luck=13)
        self.character = Character.create_character("TestHero", "human", "fighter", self.stats)
    
    def test_character_equipment_initialization(self):
        """キャラクター装備システム初期化のテスト"""
        equipment = self.character.get_equipment()
        
        assert equipment is not None
        assert equipment.owner_id == self.character.character_id
        assert len(equipment.equipped_items) == 4
    
    def test_character_equipment_persistence(self):
        """キャラクター装備システム永続化のテスト"""
        # 装備にアイテムを装備
        equipment = self.character.get_equipment()
        weapon = ItemInstance(item_id="dagger", quantity=1, identified=True)
        equipment.equip_item(weapon, EquipmentSlot.WEAPON, self.character.character_class)
        
        # 同じキャラクターの装備システムを再取得
        equipment2 = self.character.get_equipment()
        
        # 同じ装備システムが返される
        assert equipment == equipment2
        assert equipment2.get_equipped_item(EquipmentSlot.WEAPON) is not None
    
    def test_character_effective_stats(self):
        """キャラクター実効能力値のテスト"""
        # 装備なしの能力値
        base_stats = self.character.get_effective_stats()
        # 種族ボーナスが適用されているため、基本値15よりも高い可能性がある
        expected_strength = self.character.base_stats.strength
        assert base_stats.strength == expected_strength
        
        # 力+5の武器を装備（仮想的なアイテム）
        equipment = self.character.get_equipment()
        weapon = ItemInstance(item_id="dagger", quantity=1, identified=True)
        equipment.equip_item(weapon, EquipmentSlot.WEAPON, self.character.character_class)
        
        # 装備後の能力値（実際のボーナスはアイテム定義による）
        effective_stats = self.character.get_effective_stats()
        # 基本能力値は変わらない（装備ボーナスがある場合は加算される）
        assert effective_stats.strength >= expected_strength
    
    def test_character_attack_power_with_equipment(self):
        """装備込み攻撃力のテスト"""
        # 装備なしの攻撃力
        base_attack = self.character.get_attack_power()
        expected_base_attack = self.character.base_stats.strength
        assert base_attack == expected_base_attack
        
        # 武器を装備
        equipment = self.character.get_equipment()
        weapon = ItemInstance(item_id="dagger", quantity=1, identified=True)
        equipment.equip_item(weapon, EquipmentSlot.WEAPON, self.character.character_class)
        
        # 装備後の攻撃力
        equipped_attack = self.character.get_attack_power()
        
        # 武器の攻撃力分増加している
        dagger = item_manager.get_item("dagger")
        expected_attack = base_attack + (dagger.get_attack_power() if dagger else 0)
        assert equipped_attack == expected_attack
    
    def test_character_defense_with_equipment(self):
        """装備込み防御力のテスト"""
        # 装備なしの防御力
        base_defense = self.character.get_defense()
        expected_base_defense = self.character.base_stats.strength // 2
        assert base_defense == expected_base_defense
        
        # 防具を装備
        equipment = self.character.get_equipment()
        armor = ItemInstance(item_id="leather_armor", quantity=1, identified=True)
        equipment.equip_item(armor, EquipmentSlot.ARMOR, self.character.character_class)
        
        # 装備後の防御力
        equipped_defense = self.character.get_defense()
        
        # 防具の防御力分増加している
        leather_armor = item_manager.get_item("leather_armor")
        expected_defense = base_defense + (leather_armor.get_defense() if leather_armor else 0)
        assert equipped_defense == expected_defense