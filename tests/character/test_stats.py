"""キャラクター統計値システムのテスト"""

import pytest
from src.character.stats import BaseStats, StatGenerator, StatValidator


@pytest.mark.unit
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


@pytest.mark.unit
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


@pytest.mark.unit  
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