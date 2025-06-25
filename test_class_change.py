#!/usr/bin/env python3
"""クラスチェンジ機能のテスト"""

import pytest
import pygame
from unittest.mock import Mock, patch
from src.character.character import Character, Experience, CharacterStatus
from src.character.stats import BaseStats, DerivedStats
from src.character.class_change import ClassChangeValidator, ClassChangeManager
from src.character.party import Party


class TestClassChange:
    """クラスチェンジ機能のテスト"""
    
    def setup_method(self):
        """テスト前の初期化"""
        pygame.init()
        
        # テスト用キャラクター作成
        self.character = Character(
            name="テスト戦士",
            race="human",
            character_class="fighter",
            base_stats=BaseStats(strength=18, agility=12, intelligence=15, faith=12, luck=14),
            experience=Experience(current_xp=5000, level=12)
        )
        
        # 派生ステータスを設定
        self.character.derived_stats = DerivedStats(
            max_hp=80, current_hp=80,
            max_mp=20, current_mp=20
        )
        
    def teardown_method(self):
        """テスト後のクリーンアップ"""
        if pygame.get_init():
            pygame.quit()
    
    @patch('src.character.class_change.config_manager')
    def test_class_change_validation_success(self, mock_config_manager):
        """クラスチェンジ検証成功のテスト"""
        # モック設定データ
        mock_config_manager.load_config.return_value = {
            "classes": {
                "mage": {
                    "requirements": {
                        "intelligence": 11
                    }
                }
            }
        }
        
        # 魔法使いへの転職チェック
        can_change, errors = ClassChangeValidator.can_change_class(self.character, "mage")
        
        if not can_change:
            print(f"Errors: {errors}")
        
        assert can_change
        assert len(errors) == 0
    
    @patch('src.character.class_change.config_manager')
    def test_class_change_validation_level_insufficient(self, mock_config_manager):
        """レベル不足での検証失敗テスト"""
        # レベル不足キャラクター
        low_level_char = Character(
            name="新人",
            character_class="fighter",
            experience=Experience(level=5)
        )
        
        mock_config_manager.load_config.return_value = {
            "classes": {
                "mage": {
                    "requirements": {}
                }
            }
        }
        
        can_change, errors = ClassChangeValidator.can_change_class(low_level_char, "mage")
        
        assert not can_change
        assert any("レベルが不足" in error for error in errors)
    
    @patch('src.character.class_change.config_manager')
    def test_class_change_validation_stat_insufficient(self, mock_config_manager):
        """能力値不足での検証失敗テスト"""
        mock_config_manager.load_config.return_value = {
            "classes": {
                "bishop": {
                    "requirements": {
                        "intelligence": 20,  # 要求値が高すぎる
                        "faith": 20
                    }
                }
            }
        }
        
        can_change, errors = ClassChangeValidator.can_change_class(self.character, "bishop")
        
        assert not can_change
        assert any("intelligence" in error for error in errors)
        assert any("faith" in error for error in errors)
    
    @patch('src.character.class_change.config_manager')
    def test_class_change_validation_same_class(self, mock_config_manager):
        """同じクラスへの転職拒否テスト"""
        mock_config_manager.load_config.return_value = {
            "classes": {
                "fighter": {
                    "requirements": {}
                }
            }
        }
        
        can_change, errors = ClassChangeValidator.can_change_class(self.character, "fighter")
        
        assert not can_change
        assert any("同じクラス" in error for error in errors)
    
    @patch('src.character.class_change.config_manager')
    def test_get_available_classes(self, mock_config_manager):
        """利用可能なクラス取得のテスト"""
        mock_config_manager.load_config.return_value = {
            "classes": {
                "mage": {"requirements": {"intelligence": 10}},
                "priest": {"requirements": {"faith": 8}},
                "thief": {"requirements": {"agility": 11}},
                "bishop": {"requirements": {"intelligence": 20, "faith": 20}}  # 条件厳しすぎ
            }
        }
        
        available_classes = ClassChangeValidator.get_available_classes(self.character)
        
        # intelligenceとfaithが足りるmage、priest、thiefが利用可能
        assert "mage" in available_classes
        assert "priest" in available_classes
        assert "thief" in available_classes
        assert "bishop" not in available_classes  # 条件不足
    
    @patch('src.character.class_change.config_manager')
    def test_class_change_execution_success(self, mock_config_manager):
        """クラスチェンジ実行成功のテスト"""
        mock_config_manager.load_config.return_value = {
            "classes": {
                "mage": {
                    "requirements": {"intelligence": 10},
                    "base_stats": {"intelligence": 3},
                    "hp_multiplier": 0.7,
                    "mp_multiplier": 1.5
                }
            },
            "races": {
                "human": {
                    "base_stats": {},
                    "stat_modifiers": {
                        "strength": 1.0, "agility": 1.0, "intelligence": 1.0,
                        "faith": 1.0, "luck": 1.0
                    }
                }
            }
        }
        
        # StatGeneratorをモック
        with patch('src.character.stats.StatGenerator') as mock_stat_gen:
            mock_stat_gen.calculate_derived_stats.return_value = DerivedStats(
                max_hp=56, current_hp=56,  # 0.7倍
                max_mp=30, current_mp=30   # 1.5倍
            )
            
            old_class = self.character.character_class
            old_level = self.character.experience.level
            
            success, message = ClassChangeManager.change_class(self.character, "mage")
            
            assert success
            assert "mage" in message
            assert self.character.character_class == "mage"
            assert self.character.experience.level == 1  # レベルリセット
            assert self.character.experience.current_xp == 0  # 経験値リセット
    
    @patch('src.character.class_change.config_manager')
    def test_class_change_info_retrieval(self, mock_config_manager):
        """クラスチェンジ情報取得のテスト"""
        mock_config_manager.load_config.return_value = {
            "classes": {
                "fighter": {"name_key": "class.fighter"},
                "mage": {
                    "name_key": "class.mage",
                    "requirements": {"intelligence": 11},
                    "hp_multiplier": 0.7,
                    "mp_multiplier": 1.5,
                    "weapon_types": ["staff", "dagger"],
                    "spell_schools": ["fire", "ice"]
                }
            }
        }
        
        mock_config_manager.get_text.side_effect = lambda key, default=None: {
            "class.fighter": "戦士",
            "class.mage": "魔法使い"
        }.get(key, default or key)
        
        info = ClassChangeManager.get_class_change_info(self.character, "mage")
        
        assert info["target_class"] == "mage"
        assert info["target_name"] == "魔法使い"
        assert info["current_class"] == "fighter"
        assert info["current_name"] == "戦士"
        assert info["hp_multiplier"] == 0.7
        assert info["mp_multiplier"] == 1.5
        assert "staff" in info["weapon_types"]
        assert "fire" in info["spell_schools"]
    
    @patch('src.character.class_change.config_manager')
    def test_hp_mp_adjustment_during_class_change(self, mock_config_manager):
        """クラスチェンジ時のHP/MP調整テスト"""
        mock_config_manager.load_config.return_value = {
            "classes": {
                "mage": {
                    "requirements": {"intelligence": 10},
                    "base_stats": {},
                    "hp_multiplier": 0.5,  # HPが大幅減少
                    "mp_multiplier": 2.0   # MPが大幅増加
                }
            },
            "races": {
                "human": {
                    "base_stats": {},
                    "stat_modifiers": {
                        "strength": 1.0, "agility": 1.0, "intelligence": 1.0,
                        "faith": 1.0, "luck": 1.0
                    }
                }
            }
        }
        
        # 現在のHP/MPを記録
        old_max_hp = self.character.derived_stats.max_hp
        old_max_mp = self.character.derived_stats.max_mp
        
        with patch('src.character.stats.StatGenerator') as mock_stat_gen:
            # 新しい最大値（減少）
            new_max_hp = int(old_max_hp * 0.5)
            new_max_mp = int(old_max_mp * 2.0)
            
            mock_stat_gen.calculate_derived_stats.return_value = DerivedStats(
                max_hp=new_max_hp, current_hp=new_max_hp,
                max_mp=new_max_mp, current_mp=new_max_mp
            )
            
            success, message = ClassChangeManager.change_class(self.character, "mage")
            
            assert success
            # HP減少時は比率で調整、最低1は保証
            assert self.character.derived_stats.current_hp >= 1
            # MP増加時は増加分を加算
            assert self.character.derived_stats.current_mp > old_max_mp


if __name__ == "__main__":
    pytest.main([__file__, "-v"])