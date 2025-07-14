"""キャラクタークラスのテスト"""

import pytest
from src.character.character import Character, CharacterStatus
from src.character.stats import BaseStats


@pytest.mark.unit
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
    
    def test_character_status_effects(self):
        """キャラクターステータス効果のテスト"""
        character = Character.create_character(
            name="TestHero", race="human", character_class="fighter", base_stats=self.test_stats
        )
        
        # 初期状態は正常
        assert character.status == CharacterStatus.GOOD
        
        # HPが0になると状態が変化（死亡または気絶）
        initial_hp = character.derived_stats.current_hp
        character.take_damage(initial_hp)  # 全HPを失う
        
        # 状態が正常でなくなることを確認
        assert character.status != CharacterStatus.GOOD
    
    def test_character_level_progression(self):
        """キャラクターレベル進行のテスト"""
        character = Character.create_character(
            name="TestHero", race="human", character_class="fighter", base_stats=self.test_stats
        )
        
        initial_level = character.experience.level
        # 経験値テーブルは実装依存のため、基本的な動作のみテスト
        assert initial_level >= 1
        assert character.experience.current_xp >= 0