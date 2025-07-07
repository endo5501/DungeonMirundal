"""ClassChangeSystemの基本テスト（簡素版）"""

import unittest
from unittest.mock import Mock, patch

from src.character.class_change import (
    ClassChangeRequirements, ClassChangeValidator, ClassChangeManager,
    MIN_LEVEL_FOR_CLASS_CHANGE, DEFAULT_CLASS_CHANGE_COST
)


class TestClassChangeRequirements(unittest.TestCase):
    """ClassChangeRequirementsのテスト"""
    
    def test_initialization_default(self):
        """デフォルト初期化のテスト"""
        requirements = ClassChangeRequirements()
        
        self.assertEqual(requirements.min_level, 1)
        self.assertEqual(requirements.required_stats, {})
        self.assertEqual(requirements.required_gold, 0)
    
    def test_initialization_with_values(self):
        """値指定初期化のテスト"""
        required_stats = {"strength": 15, "dexterity": 12}
        requirements = ClassChangeRequirements(
            min_level=10,
            required_stats=required_stats,
            required_gold=500
        )
        
        self.assertEqual(requirements.min_level, 10)
        self.assertEqual(requirements.required_stats, required_stats)
        self.assertEqual(requirements.required_gold, 500)
    
    def test_post_init_none_stats(self):
        """required_statsがNoneの場合のpost_initテスト"""
        requirements = ClassChangeRequirements(required_stats=None)
        
        self.assertEqual(requirements.required_stats, {})


class TestClassChangeValidatorBasic(unittest.TestCase):
    """ClassChangeValidatorの基本テスト"""
    
    def setUp(self):
        """テスト前のセットアップ"""
        # モックキャラクターを作成
        self.mock_character = Mock()
        self.mock_character.character_class = "fighter"
        self.mock_character.experience = Mock()
        self.mock_character.experience.level = 15
        self.mock_character.base_stats = Mock()
        self.mock_character.base_stats.strength = 18
        self.mock_character.base_stats.intelligence = 15
    
    @patch('src.character.class_change.config_manager')
    def test_can_change_class_no_config(self, mock_config_manager):
        """設定なしの場合のテスト"""
        mock_config_manager.load_config.return_value = {}
        
        can_change, errors = ClassChangeValidator.can_change_class(self.mock_character, "mage")
        
        self.assertFalse(can_change)
        self.assertGreater(len(errors), 0)
    
    @patch('src.character.class_change.config_manager')
    def test_can_change_class_valid_config(self, mock_config_manager):
        """有効な設定での成功テスト"""
        mock_config = {
            "classes": {
                "mage": {
                    "requirements": {}
                }
            }
        }
        mock_config_manager.load_config.return_value = mock_config
        
        can_change, errors = ClassChangeValidator.can_change_class(self.mock_character, "mage")
        
        self.assertTrue(can_change)
        self.assertEqual(len(errors), 0)
    
    @patch('src.character.class_change.config_manager')
    def test_get_available_classes_basic(self, mock_config_manager):
        """利用可能クラス取得の基本テスト"""
        mock_config = {
            "classes": {
                "mage": {},
                "priest": {}
            }
        }
        mock_config_manager.load_config.return_value = mock_config
        
        # can_change_classをモック
        with patch.object(ClassChangeValidator, 'can_change_class') as mock_can_change:
            mock_can_change.side_effect = [
                (True, []),   # mage
                (False, [])   # priest
            ]
            
            available = ClassChangeValidator.get_available_classes(self.mock_character)
            
            self.assertIn("mage", available)
            self.assertNotIn("priest", available)


class TestClassChangeManagerBasic(unittest.TestCase):
    """ClassChangeManagerの基本テスト"""
    
    def setUp(self):
        """テスト前のセットアップ"""
        self.mock_character = Mock()
        self.mock_character.name = "Test Hero"
        self.mock_character.character_class = "fighter"
    
    @patch('src.character.class_change.ClassChangeValidator')
    def test_change_class_validation_failure(self, mock_validator):
        """クラスチェンジ検証失敗のテスト"""
        mock_validator.can_change_class.return_value = (False, ["レベル不足"])
        
        success, message = ClassChangeManager.change_class(self.mock_character, "mage")
        
        self.assertFalse(success)
        self.assertIn("クラスチェンジできません", message)
        self.assertIn("レベル不足", message)
    
    @patch('src.character.class_change.config_manager')
    def test_get_class_change_info_empty_config(self, mock_config_manager):
        """空設定での情報取得テスト"""
        mock_config_manager.load_config.return_value = {"classes": {}}
        
        info = ClassChangeManager.get_class_change_info(self.mock_character, "nonexistent")
        
        self.assertEqual(info, {})
    
    @patch('src.character.class_change.config_manager')
    def test_get_class_change_info_basic(self, mock_config_manager):
        """基本的な情報取得テスト"""
        mock_config = {
            "classes": {
                "mage": {
                    "requirements": {"intelligence": 15}
                },
                "fighter": {}
            }
        }
        mock_config_manager.load_config.return_value = mock_config
        mock_config_manager.get_text.return_value = "Test Class"
        
        info = ClassChangeManager.get_class_change_info(self.mock_character, "mage")
        
        self.assertEqual(info["target_class"], "mage")
        self.assertEqual(info["current_class"], "fighter")
        self.assertEqual(info["requirements"], {"intelligence": 15})
        self.assertIn("hp_multiplier", info)
        self.assertIn("mp_multiplier", info)


class TestClassChangeConstants(unittest.TestCase):
    """ClassChange定数のテスト"""
    
    def test_constants_values(self):
        """定数値のテスト"""
        self.assertEqual(MIN_LEVEL_FOR_CLASS_CHANGE, 10)
        self.assertEqual(DEFAULT_CLASS_CHANGE_COST, 1000)


if __name__ == '__main__':
    unittest.main()