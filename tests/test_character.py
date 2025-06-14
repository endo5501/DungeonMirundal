"""キャラクターシステムのテスト"""

import pytest
from src.character.character import Character, CharacterStatus, Experience
from src.character.stats import BaseStats, StatGenerator, StatValidator
from src.character.party import Party, PartyPosition
from src.core.config_manager import ConfigManager


class TestBaseStats:
    """BaseStatsのテスト"""
    
    def test_apply_modifiers(self):
        """修正値適用のテスト"""
        stats = BaseStats(strength=10, agility=12, intelligence=8)
        modifiers = {'strength': 1.2, 'agility': 0.8}
        
        modified = stats.apply_modifiers(modifiers)
        
        assert modified.strength == 12  # 10 * 1.2
        assert modified.agility == 9    # 12 * 0.8
        assert modified.intelligence == 8  # 修正なし
    
    def test_add_bonuses(self):
        """ボーナス追加のテスト"""
        stats = BaseStats(strength=10, agility=10)
        bonuses = {'strength': 2, 'luck': 1}
        
        result = stats.add_bonuses(bonuses)
        
        assert result.strength == 12
        assert result.agility == 10
        assert result.luck == 11  # 10 + 1
    
    def test_to_dict_from_dict(self):
        """辞書変換のテスト"""
        stats = BaseStats(strength=15, agility=12, intelligence=14, faith=10, luck=13)
        
        data = stats.to_dict()
        restored = BaseStats.from_dict(data)
        
        assert restored.strength == stats.strength
        assert restored.agility == stats.agility
        assert restored.intelligence == stats.intelligence
        assert restored.faith == stats.faith
        assert restored.luck == stats.luck


class TestStatGenerator:
    """StatGeneratorのテスト"""
    
    def test_roll_3d6(self):
        """3d6ロールのテスト"""
        for _ in range(100):  # 複数回テスト
            result = StatGenerator.roll_3d6()
            assert 3 <= result <= 18
    
    def test_roll_4d6_drop_lowest(self):
        """4d6_drop_lowestのテスト"""
        for _ in range(100):  # 複数回テスト
            result = StatGenerator.roll_4d6_drop_lowest()
            assert 3 <= result <= 18
    
    def test_generate_stats(self):
        """統計値生成のテスト"""
        stats = StatGenerator.generate_stats("3d6")
        
        assert 3 <= stats.strength <= 18
        assert 3 <= stats.agility <= 18
        assert 3 <= stats.intelligence <= 18
        assert 3 <= stats.faith <= 18
        assert 3 <= stats.luck <= 18


class TestStatValidator:
    """StatValidatorのテスト"""
    
    def test_check_class_requirements(self):
        """職業要件チェックのテスト"""
        stats = BaseStats(strength=15, intelligence=12)
        
        # 戦士の要件（力11以上）
        fighter_config = {'requirements': {'strength': 11}}
        assert StatValidator.check_class_requirements(stats, fighter_config) == True
        
        # 魔術師の要件（知力11以上）
        mage_config = {'requirements': {'intelligence': 11}}
        assert StatValidator.check_class_requirements(stats, mage_config) == True
        
        # 忍者の要件（力17以上）
        ninja_config = {'requirements': {'strength': 17}}
        assert StatValidator.check_class_requirements(stats, ninja_config) == False


class TestExperience:
    """Experienceのテスト"""
    
    def test_add_experience(self):
        """経験値追加のテスト"""
        exp = Experience()
        xp_table = {1: 0, 2: 100, 3: 300}
        
        # レベル2まで
        leveled_up = exp.add_experience(150, xp_table)
        assert leveled_up == True
        assert exp.level == 2
        assert exp.current_xp == 150
        
        # レベル3まで
        leveled_up = exp.add_experience(200, xp_table)
        assert leveled_up == True
        assert exp.level == 3
        assert exp.current_xp == 350


class TestCharacter:
    """Characterのテスト"""
    
    def setup_method(self):
        """各テストメソッドの前に実行"""
        # テスト用の統計値
        self.test_stats = BaseStats(
            strength=15, agility=12, intelligence=14, faith=10, luck=13
        )
    
    def test_character_creation(self):
        """キャラクター作成のテスト"""
        character = Character.create_character(
            name="TestHero",
            race="human",
            character_class="fighter",
            base_stats=self.test_stats
        )
        
        assert character.name == "TestHero"
        assert character.race == "human"
        assert character.character_class == "fighter"
        assert character.status == CharacterStatus.GOOD
        assert character.experience.level == 1
    
    def test_take_damage(self):
        """ダメージ処理のテスト"""
        character = Character.create_character(
            name="TestHero", race="human", character_class="fighter", base_stats=self.test_stats
        )
        
        initial_hp = character.derived_stats.current_hp
        character.take_damage(5)
        
        assert character.derived_stats.current_hp == initial_hp - 5
        assert character.status == CharacterStatus.GOOD
    
    def test_heal(self):
        """回復処理のテスト"""
        character = Character.create_character(
            name="TestHero", race="human", character_class="fighter", base_stats=self.test_stats
        )
        
        # ダメージを与えてから回復
        character.take_damage(10)
        damaged_hp = character.derived_stats.current_hp
        character.heal(5)
        
        assert character.derived_stats.current_hp == damaged_hp + 5
    
    def test_serialization(self):
        """シリアライゼーションのテスト"""
        character = Character.create_character(
            name="TestHero", race="human", character_class="fighter", base_stats=self.test_stats
        )
        
        # 辞書化してから復元
        data = character.to_dict()
        restored = Character.from_dict(data)
        
        assert restored.name == character.name
        assert restored.race == character.race
        assert restored.character_class == character.character_class
        assert restored.base_stats.strength == character.base_stats.strength


class TestParty:
    """Partyのテスト"""
    
    def setup_method(self):
        """各テストメソッドの前に実行"""
        self.party = Party(name="Test Party")
        
        # テストキャラクター作成
        stats = BaseStats(strength=15, agility=12, intelligence=14, faith=10, luck=13)
        self.character1 = Character.create_character("Hero1", "human", "fighter", stats)
        self.character2 = Character.create_character("Hero2", "elf", "mage", stats)
    
    def test_add_character(self):
        """キャラクター追加のテスト"""
        success = self.party.add_character(self.character1)
        
        assert success == True
        assert len(self.party.characters) == 1
        assert self.character1.character_id in self.party.characters
    
    def test_remove_character(self):
        """キャラクター削除のテスト"""
        self.party.add_character(self.character1)
        success = self.party.remove_character(self.character1.character_id)
        
        assert success == True
        assert len(self.party.characters) == 0
    
    def test_party_formation(self):
        """パーティ編成のテスト"""
        self.party.add_character(self.character1, PartyPosition.FRONT_1)
        self.party.add_character(self.character2, PartyPosition.BACK_1)
        
        front_chars = self.party.get_front_row_characters()
        back_chars = self.party.get_back_row_characters()
        
        assert len(front_chars) == 1
        assert front_chars[0].character_id == self.character1.character_id
        assert len(back_chars) == 1
        assert back_chars[0].character_id == self.character2.character_id
    
    def test_party_serialization(self):
        """パーティシリアライゼーションのテスト"""
        self.party.add_character(self.character1)
        self.party.add_character(self.character2)
        
        # 辞書化してから復元
        data = self.party.to_dict()
        restored = Party.from_dict(data)
        
        assert restored.name == self.party.name
        assert len(restored.characters) == 2
        assert restored.gold == self.party.gold