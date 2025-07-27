"""スキルチェックシステムのテスト"""

import pytest
from unittest.mock import Mock, patch

from src.dungeon.base.skill_check import SkillCheckBase, TrapSkillChecker, TreasureSkillChecker


class TestSkillCheckBase:
    """SkillCheckBaseのテスト"""
    
    def test_basic_success_rate_calculation(self):
        """基本成功率計算のテスト"""
        # Mock character
        character = Mock()
        character.character_class = "thief"
        character.base_stats = Mock()
        character.base_stats.agility = 15
        character.experience = Mock()
        character.experience.level = 5
        
        checker = TrapSkillChecker()
        
        # disarmスキルのテスト
        with patch('random.random', return_value=0.3):  # 30%で固定
            result = checker.can_perform_skill(character, "disarm", 1.0)
            # thief(0.5) + agility bonus(0.1) + level bonus(0.05) + base(0.1) = 0.75
            # 0.3 < 0.75 なので成功するはず
            assert result is True
    
    def test_difficulty_scaling(self):
        """難易度スケーリングのテスト"""
        character = Mock()
        character.character_class = "thief"
        character.base_stats = Mock()
        character.base_stats.agility = 15
        character.experience = Mock()
        character.experience.level = 5
        
        checker = TrapSkillChecker()
        
        # 高難易度でのテスト
        with patch('random.random', return_value=0.3):
            # 難易度2.0で成功率が半分になる
            result = checker.can_perform_skill(character, "disarm", 2.0)
            # 0.75 / 2.0 = 0.375, 0.3 < 0.375 なので成功
            assert result is True
            
            # より高い難易度
            result = checker.can_perform_skill(character, "disarm", 3.0)
            # 0.75 / 3.0 = 0.25, 0.3 > 0.25 なので失敗
            assert result is False


class TestTrapSkillChecker:
    """TrapSkillCheckerのテスト"""
    
    def test_class_bonus_for_detection(self):
        """探知スキルのクラスボーナステスト"""
        checker = TrapSkillChecker()
        
        # Thiefのボーナス
        assert checker._get_class_bonus("thief", "detect") == 0.4
        
        # Ninjaのボーナス
        assert checker._get_class_bonus("ninja", "detect") == 0.3
        
        # 不明なクラス
        assert checker._get_class_bonus("unknown", "detect") == 0.0
    
    def test_class_bonus_for_disarm(self):
        """解除スキルのクラスボーナステスト"""
        checker = TrapSkillChecker()
        
        # Thiefのボーナス
        assert checker._get_class_bonus("thief", "disarm") == 0.5
        
        # Ninjaのボーナス
        assert checker._get_class_bonus("ninja", "disarm") == 0.3
        
        # Rangerのボーナス
        assert checker._get_class_bonus("ranger", "disarm") == 0.1
    
    def test_stat_bonus(self):
        """ステータスボーナステスト"""
        checker = TrapSkillChecker()
        
        stats = Mock()
        stats.intelligence = 16
        stats.agility = 14
        
        # 探知は知力ベース
        assert checker._get_stat_bonus(stats, "detect") == 0.12  # (16-10) * 0.02
        
        # 解除は敏捷ベース
        assert checker._get_stat_bonus(stats, "disarm") == 0.08  # (14-10) * 0.02


class TestTreasureSkillChecker:
    """TreasureSkillCheckerのテスト"""
    
    def test_lock_picking_class_bonus(self):
        """鍵開けクラスボーナステスト"""
        checker = TreasureSkillChecker()
        
        # Thiefのボーナス
        assert checker._get_class_bonus("thief", "lock_picking") == 0.4
        
        # Ninjaのボーナス
        assert checker._get_class_bonus("ninja", "lock_picking") == 0.2
        
        # 不明なクラス
        assert checker._get_class_bonus("warrior", "lock_picking") == 0.0
    
    def test_lock_picking_stat_bonus(self):
        """鍵開けステータスボーナステスト"""
        checker = TreasureSkillChecker()
        
        stats = Mock()
        stats.agility = 18
        
        # 鍵開けは敏捷ベース
        assert checker._get_stat_bonus(stats, "lock_picking") == 0.16  # (18-10) * 0.02


class TestIntegration:
    """統合テスト"""
    
    def test_trap_detection_integration(self):
        """トラップ探知の統合テスト"""
        from src.dungeon.base.skill_check import trap_skill_checker
        
        # 高レベル盗賊キャラクター
        thief = Mock()
        thief.character_class = "thief"
        thief.base_stats = Mock()
        thief.base_stats.intelligence = 16
        thief.experience = Mock()
        thief.experience.level = 10
        
        # 成功率が高いはず
        success_count = 0
        for _ in range(100):
            if trap_skill_checker.can_perform_skill(thief, "detect", 1.0):
                success_count += 1
        
        # 高い成功率を期待（理論値約72%）
        # base(0.1) + thief(0.4) + int bonus(0.12) + level(0.1) = 0.72
        assert success_count > 60
    
    def test_treasure_lock_picking_integration(self):
        """宝箱鍵開けの統合テスト"""
        from src.dungeon.base.skill_check import treasure_skill_checker
        
        # 低レベル戦士キャラクター
        warrior = Mock()
        warrior.character_class = "warrior"
        warrior.base_stats = Mock()
        warrior.base_stats.agility = 10
        warrior.experience = Mock()
        warrior.experience.level = 1
        
        # 成功率が低いはず
        success_count = 0
        for _ in range(100):
            if treasure_skill_checker.can_perform_skill(warrior, "lock_picking", 1.0):
                success_count += 1
        
        # 低い成功率を期待（理論値約11%）
        assert success_count < 25