"""CharacterCreationWizardのテスト"""

import pytest
from unittest.mock import Mock, patch
import pygame

from src.ui.windows.character_creation_wizard import CharacterCreationWizard, CreationStep
from src.ui.window_system.window_manager import WindowManager
from src.character.character import Character
from src.character.stats import BaseStats


class TestCharacterCreationWizard:
    """CharacterCreationWizardのテストクラス"""

    @pytest.fixture
    def mock_window_manager(self):
        """WindowManagerのモックを作成"""
        with patch('src.ui.window_system.window_manager.WindowManager') as mock_wm_class:
            mock_wm = Mock()
            mock_wm_class.get_instance.return_value = mock_wm
            mock_wm.ui_manager = Mock()
            mock_wm.screen = Mock()
            mock_wm.screen.get_rect.return_value = pygame.Rect(0, 0, 800, 600)
            yield mock_wm

    @pytest.fixture
    def mock_config_manager(self):
        """config_managerのモックを作成"""
        with patch('src.core.config_manager.config_manager') as mock_config:
            mock_config.load_config.return_value = {
                "races": {
                    "human": {"name": "人間", "description": "バランスの良い種族"},
                    "elf": {"name": "エルフ", "description": "魔法に長けた種族"}
                },
                "classes": {
                    "warrior": {"name": "戦士", "description": "物理攻撃に特化"},
                    "wizard": {"name": "魔法使い", "description": "魔法攻撃に特化"}
                }
            }
            mock_config.get_text.return_value = "テストテキスト"
            yield mock_config

    @pytest.fixture
    def mock_character_callback(self):
        """キャラクター作成完了コールバックのモックを作成"""
        return Mock()

    def test_wizard_creation(self, mock_window_manager, mock_config_manager):
        """CharacterCreationWizardが正しく作成されることを確認"""
        wizard = CharacterCreationWizard("test_wizard")
        
        assert wizard.window_id == "test_wizard"
        assert wizard.current_step == CreationStep.NAME_INPUT
        assert wizard.character_data["name"] == ""
        assert wizard.character_data["race"] == ""
        assert wizard.character_data["class"] == ""
        assert wizard.character_data["stats"] is None

    def test_start_wizard(self, mock_window_manager, mock_config_manager, mock_character_callback):
        """ウィザードの開始が正しく動作することを確認"""
        wizard = CharacterCreationWizard("test_wizard", callback=mock_character_callback)
        
        # createメソッドをモック
        wizard.create_name_input_step = Mock()
        
        wizard.start_wizard()
        
        assert wizard.current_step == CreationStep.NAME_INPUT
        wizard.create_name_input_step.assert_called_once()

    def test_set_character_name(self, mock_window_manager, mock_config_manager):
        """キャラクター名設定が正しく動作することを確認"""
        wizard = CharacterCreationWizard("test_wizard")
        
        wizard.set_character_name("テストキャラクター")
        
        assert wizard.character_data["name"] == "テストキャラクター"

    def test_set_character_race(self, mock_window_manager, mock_config_manager):
        """種族設定が正しく動作することを確認"""
        wizard = CharacterCreationWizard("test_wizard")
        
        wizard.set_character_race("human")
        
        assert wizard.character_data["race"] == "human"

    def test_set_character_class(self, mock_window_manager, mock_config_manager):
        """職業設定が正しく動作することを確認"""
        wizard = CharacterCreationWizard("test_wizard")
        
        wizard.set_character_class("warrior")
        
        assert wizard.character_data["class"] == "warrior"

    def test_set_character_stats(self, mock_window_manager, mock_config_manager):
        """ステータス設定が正しく動作することを確認"""
        wizard = CharacterCreationWizard("test_wizard")
        
        stats = Mock(spec=BaseStats)
        stats.strength = 15
        stats.agility = 12
        stats.intelligence = 10
        stats.faith = 8
        stats.luck = 11
        
        wizard.set_character_stats(stats)
        
        assert wizard.character_data["stats"] == stats

    def test_step_progression(self, mock_window_manager, mock_config_manager):
        """ステップ進行が正しく動作することを確認"""
        wizard = CharacterCreationWizard("test_wizard")
        
        # 各ステップの進行をテスト
        wizard.next_step = Mock()
        
        # 名前入力 → 種族選択
        wizard.current_step = CreationStep.NAME_INPUT
        wizard.proceed_to_next_step()
        wizard.next_step.assert_called_with(CreationStep.RACE_SELECTION)
        
        # 種族選択 → ステータス生成
        wizard.current_step = CreationStep.RACE_SELECTION
        wizard.proceed_to_next_step()
        wizard.next_step.assert_called_with(CreationStep.STATS_GENERATION)
        
        # ステータス生成 → 職業選択
        wizard.current_step = CreationStep.STATS_GENERATION
        wizard.proceed_to_next_step()
        wizard.next_step.assert_called_with(CreationStep.CLASS_SELECTION)
        
        # 職業選択 → 確認
        wizard.current_step = CreationStep.CLASS_SELECTION
        wizard.proceed_to_next_step()
        wizard.next_step.assert_called_with(CreationStep.CONFIRMATION)

    def test_step_regression(self, mock_window_manager, mock_config_manager):
        """ステップ後退が正しく動作することを確認"""
        wizard = CharacterCreationWizard("test_wizard")
        
        wizard.previous_step = Mock()
        
        # 確認 → 職業選択
        wizard.current_step = CreationStep.CONFIRMATION
        wizard.go_to_previous_step()
        wizard.previous_step.assert_called_with(CreationStep.CLASS_SELECTION)
        
        # 職業選択 → ステータス生成
        wizard.current_step = CreationStep.CLASS_SELECTION
        wizard.go_to_previous_step()
        wizard.previous_step.assert_called_with(CreationStep.STATS_GENERATION)

    def test_generate_stats(self, mock_window_manager, mock_config_manager):
        """ステータス生成が正しく動作することを確認"""
        wizard = CharacterCreationWizard("test_wizard")
        wizard.character_data["race"] = "human"
        
        with patch('src.character.stats.StatGenerator') as mock_stat_gen_class:
            mock_stat_gen = Mock()
            mock_stat_gen_class.return_value = mock_stat_gen
            
            generated_stats = Mock(spec=BaseStats)
            mock_stat_gen.generate_stats.return_value = generated_stats
            
            wizard.generate_character_stats()
            
            assert wizard.character_data["stats"] == generated_stats
            mock_stat_gen.generate_stats.assert_called_once_with("human")

    def test_reroll_stats(self, mock_window_manager, mock_config_manager):
        """ステータス再生成が正しく動作することを確認"""
        wizard = CharacterCreationWizard("test_wizard")
        wizard.character_data["race"] = "elf"
        
        with patch('src.character.stats.StatGenerator') as mock_stat_gen_class:
            mock_stat_gen = Mock()
            mock_stat_gen_class.return_value = mock_stat_gen
            
            # 初回生成
            first_stats = Mock(spec=BaseStats)
            first_stats.strength = 10
            
            # 再生成
            second_stats = Mock(spec=BaseStats)
            second_stats.strength = 15
            
            mock_stat_gen.generate_stats.side_effect = [first_stats, second_stats]
            
            wizard.generate_character_stats()
            assert wizard.character_data["stats"] == first_stats
            
            wizard.reroll_character_stats()
            assert wizard.character_data["stats"] == second_stats
            
            assert mock_stat_gen.generate_stats.call_count == 2

    def test_validate_character_data(self, mock_window_manager, mock_config_manager):
        """キャラクターデータ検証が正しく動作することを確認"""
        wizard = CharacterCreationWizard("test_wizard")
        
        # 不完全なデータ
        assert not wizard.validate_character_data()
        
        # 完全なデータ
        wizard.character_data = {
            "name": "テストキャラクター",
            "race": "human",
            "class": "warrior",
            "stats": Mock(spec=BaseStats)
        }
        assert wizard.validate_character_data()

    def test_create_character_success(self, mock_window_manager, mock_config_manager, mock_character_callback):
        """キャラクター作成成功ケースをテスト"""
        wizard = CharacterCreationWizard("test_wizard", callback=mock_character_callback)
        
        # 完全なキャラクターデータを設定
        stats = Mock(spec=BaseStats)
        wizard.character_data = {
            "name": "テストキャラクター",
            "race": "human",
            "class": "warrior",
            "stats": stats
        }
        
        with patch('src.character.character.Character') as mock_char_class:
            mock_character = Mock(spec=Character)
            mock_char_class.return_value = mock_character
            
            wizard.create_character()
            
            mock_char_class.assert_called_once_with(
                name="テストキャラクター",
                race="human",
                character_class="warrior",
                base_stats=stats
            )
            mock_character_callback.assert_called_once_with(mock_character)
            assert wizard.current_step == CreationStep.COMPLETED

    def test_cancel_wizard(self, mock_window_manager, mock_config_manager):
        """ウィザードキャンセルが正しく動作することを確認"""
        cancel_callback = Mock()
        wizard = CharacterCreationWizard("test_wizard")
        wizard.set_cancel_callback(cancel_callback)
        
        wizard.cancel_wizard()
        
        cancel_callback.assert_called_once()

    def test_wizard_validation_errors(self, mock_window_manager, mock_config_manager):
        """ウィザードの検証エラーが正しく処理されることを確認"""
        wizard = CharacterCreationWizard("test_wizard")
        
        # 名前が空
        wizard.character_data["name"] = ""
        assert not wizard.validate_step_data(CreationStep.NAME_INPUT)
        
        # 名前が長すぎる
        wizard.character_data["name"] = "a" * 101
        assert not wizard.validate_step_data(CreationStep.NAME_INPUT)
        
        # 有効な名前
        wizard.character_data["name"] = "テストキャラクター"
        assert wizard.validate_step_data(CreationStep.NAME_INPUT)

    def test_show_confirmation_summary(self, mock_window_manager, mock_config_manager):
        """確認画面の概要表示が正しく動作することを確認"""
        wizard = CharacterCreationWizard("test_wizard")
        
        stats = Mock(spec=BaseStats)
        stats.strength = 15
        stats.agility = 12
        stats.intelligence = 10
        stats.faith = 8
        stats.luck = 11
        
        wizard.character_data = {
            "name": "テストキャラクター",
            "race": "human",
            "class": "warrior",
            "stats": stats
        }
        
        summary = wizard.generate_character_summary()
        
        assert "テストキャラクター" in summary
        assert "人間" in summary or "human" in summary
        assert "戦士" in summary or "warrior" in summary

    def test_window_lifecycle(self, mock_window_manager, mock_config_manager):
        """ウィンドウのライフサイクルが正しく動作することを確認"""
        wizard = CharacterCreationWizard("test_wizard")
        
        # 作成状態の確認
        assert wizard.window_id == "test_wizard"
        
        # 表示
        wizard.create = Mock()
        wizard.show()
        wizard.create.assert_called_once()
        
        # 非表示
        wizard.hide()
        
        # 破棄
        wizard.destroy()
        assert wizard.character_data["name"] == ""
        assert wizard.character_data["race"] == ""
        assert wizard.character_data["class"] == ""
        assert wizard.character_data["stats"] is None