"""経験値システムのテスト"""

import pytest
from src.character.character import Experience


@pytest.mark.unit
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
    
    def test_experience_without_levelup(self):
        """レベルアップしない経験値追加のテスト"""
        exp = Experience()
        xp_table = {1: 0, 2: 100, 3: 300}
        
        # レベルアップに足りない経験値
        leveled_up = exp.add_experience(50, xp_table)
        assert leveled_up == False
        assert exp.level == 1
        assert exp.current_xp == 50
    
    def test_experience_at_max_level(self):
        """最大レベルでの経験値追加のテスト"""
        exp = Experience()
        exp.level = 3  # 最大レベル
        exp.current_xp = 300
        xp_table = {1: 0, 2: 100, 3: 300}
        
        # 最大レベルでは経験値は増えるがレベルアップしない
        leveled_up = exp.add_experience(100, xp_table)
        assert leveled_up == False
        assert exp.level == 3
        assert exp.current_xp == 400