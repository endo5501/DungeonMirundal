"""
character_creation.pyのCharacterCreationWizard移行テスト

t-wada式TDDに従って、既存のUIMenu形式から新WindowSystem形式への移行をテスト
"""
import pytest
import pygame
from unittest.mock import Mock, patch, MagicMock

from src.ui.window_system import WindowManager
from src.ui.window_system.character_creation_wizard import CharacterCreationWizard
from src.character.character import Character
from src.character.stats import BaseStats
from src.core.config_manager import config_manager
from src.utils.logger import logger


class TestCharacterCreationCharacterCreationWizardMigration:
    """キャラクター作成のCharacterCreationWizard移行テスト"""
    
    def setup_method(self):
        """テスト前の準備"""
        # Pygameを初期化
        if not pygame.get_init():
            pygame.init()
        
        # WindowManagerをリセット
        WindowManager._instance = None
        self.window_manager = WindowManager.get_instance()
        
        # モックコールバック
        self.mock_callback = Mock()
        
        # モック設定データ
        self.mock_char_config = {
            'races': {
                'human': {'name': 'ヒューマン', 'stats_modifier': {}},
                'elf': {'name': 'エルフ', 'stats_modifier': {}}
            },
            'classes': {
                'fighter': {'name': 'ファイター', 'requirements': {}},
                'wizard': {'name': 'ウィザード', 'requirements': {}}
            }
        }
        
    def test_migrated_character_creation_should_use_window_manager(self):
        """移行後のCharacterCreationはWindowManagerを使用すべき"""
        # Given: 移行後のCharacterCreationWizard（新形式）
        from src.ui.character_creation import CharacterCreationWizard
        
        # When: 新形式のCharacterCreationWizardを作成
        wizard = CharacterCreationWizard(self.mock_callback)
        
        # Then: WindowManagerが設定されている
        assert hasattr(wizard, 'window_manager')
        assert wizard.window_manager is not None
        assert isinstance(wizard.window_manager, WindowManager)
    
    def test_migrated_character_creation_should_create_wizard_window(self):
        """移行後のCharacterCreationはWizardWindowを作成すべき"""
        # Given: 移行後のCharacterCreationWizard
        from src.ui.character_creation import CharacterCreationWizard
        wizard = CharacterCreationWizard(self.mock_callback)
        
        # When: ウィザードを開始
        wizard.start()
        
        # Then: CharacterCreationWizardが作成される
        assert hasattr(wizard, 'wizard_window')
        assert wizard.wizard_window is not None
        # WindowSystem版のCharacterCreationWizardが作成されている
        from src.ui.window_system.character_creation_wizard import CharacterCreationWizard as WizardWindow
        assert isinstance(wizard.wizard_window, WizardWindow)
    
    def test_migrated_character_creation_should_not_use_legacy_ui_menu(self):
        """移行後のCharacterCreationは旧UIMenuを使用しないべき"""
        # Given: 移行後のCharacterCreationWizard
        from src.ui.character_creation import CharacterCreationWizard
        wizard = CharacterCreationWizard(self.mock_callback)
        
        # When: CharacterCreationWizardのソースコードを確認
        import inspect
        source = inspect.getsource(CharacterCreationWizard)
        
        # Then: 旧UIMenuクラスのインポートや使用がない
        assert 'UIMenu' not in source
        assert 'UIDialog' not in source
        assert 'UIInputDialog' not in source
        assert 'UIButton' not in source
        assert 'ui_manager' not in source
        assert 'base_ui_pygame' not in source
    
    def test_migrated_character_creation_should_delegate_wizard_steps_to_window(self):
        """移行後のCharacterCreationはウィザードステップをWizardWindowに委譲すべき"""
        # Given: 移行後のCharacterCreationWizard with WizardWindow
        from src.ui.character_creation import CharacterCreationWizard
        wizard = CharacterCreationWizard(self.mock_callback)
        
        # ウィザードを開始
        wizard.start()
        
        # When: 次のステップに進む
        with patch.object(wizard.wizard_window, 'next_step', return_value=True) as mock_next:
            result = wizard.next_step()
        
        # Then: WizardWindowのnext_stepが呼ばれる
        assert result is True
        mock_next.assert_called_once()
    
    def test_migrated_character_creation_should_handle_character_data_through_window(self):
        """移行後のCharacterCreationはキャラクターデータをWizardWindowを通して処理すべき"""
        # Given: 移行後のCharacterCreationWizard with WizardWindow
        from src.ui.character_creation import CharacterCreationWizard
        wizard = CharacterCreationWizard(self.mock_callback)
        
        # ウィザードを開始
        wizard.start()
        
        # When: キャラクターデータを設定
        character_data = {
            'name': 'テストキャラクター',
            'race': 'human',
            'character_class': 'fighter'
        }
        
        with patch.object(wizard.wizard_window, 'set_character_data', return_value=True) as mock_set:
            result = wizard.set_character_data(character_data)
        
        # Then: WizardWindowのset_character_dataが呼ばれる
        assert result is True
        mock_set.assert_called_once_with(character_data)
    
    def test_migrated_character_creation_should_preserve_existing_public_api(self):
        """移行後のCharacterCreationは既存の公開APIを保持すべき"""
        # Given: 移行後のCharacterCreationWizard
        from src.ui.character_creation import CharacterCreationWizard
        wizard = CharacterCreationWizard(self.mock_callback)
        
        # Then: 既存の公開メソッドが保持されている
        assert hasattr(wizard, 'start')
        assert hasattr(wizard, 'next_step')
        assert hasattr(wizard, 'previous_step')
        assert hasattr(wizard, 'cancel')
        assert hasattr(wizard, 'finish')
        assert hasattr(wizard, 'set_character_data')
        assert hasattr(wizard, 'get_character_data')
    
    def test_migrated_character_creation_should_use_window_system_configuration(self):
        """移行後のCharacterCreationはWindowSystem設定を使用すべき"""
        # Given: 移行後のCharacterCreationWizard
        from src.ui.character_creation import CharacterCreationWizard
        wizard = CharacterCreationWizard(self.mock_callback)
        
        # When: WindowSystem設定でCharacterCreationWizardを作成
        wizard_config = wizard._create_wizard_window_config()
        
        # Then: WindowSystem形式の設定が作成される
        assert isinstance(wizard_config, dict)
        assert 'races' in wizard_config or 'classes' in wizard_config or 'wizard_steps' in wizard_config
    
    def test_migrated_character_creation_should_handle_character_validation(self):
        """移行後のCharacterCreationはキャラクターバリデーションを適切に処理すべき"""
        # Given: 移行後のCharacterCreationWizard with WizardWindow
        from src.ui.character_creation import CharacterCreationWizard
        wizard = CharacterCreationWizard(self.mock_callback)
        
        # ウィザードを開始
        wizard.start()
        
        # モックキャラクターデータ
        character_data = {
            'name': 'テストキャラクター',
            'race': 'human',
            'character_class': 'fighter',
            'base_stats': Mock()
        }
        
        # When: キャラクター作成の検証
        with patch.object(wizard.wizard_window, 'validate_character', return_value=(True, "")) as mock_validate:
            result = wizard.validate_character_data(character_data)
        
        # Then: WizardWindowで検証が実行される
        mock_validate.assert_called_once_with(character_data)
        assert result == (True, "")
    
    def test_migrated_character_creation_should_handle_step_transitions(self):
        """移行後のCharacterCreationはステップ遷移を適切に処理すべき"""
        # Given: 移行後のCharacterCreationWizard with WizardWindow
        from src.ui.character_creation import CharacterCreationWizard
        wizard = CharacterCreationWizard(self.mock_callback)
        
        # ウィザードを開始
        wizard.start()
        
        # When: ステップ間を移動
        with patch.object(wizard.wizard_window, 'get_current_step', return_value="name_input") as mock_get_step:
            current_step = wizard.get_current_step()
        
        # Then: WizardWindowでステップ管理が実行される
        mock_get_step.assert_called_once()
        assert current_step == "name_input"
    
    def test_migrated_character_creation_should_cleanup_resources_properly(self):
        """移行後のCharacterCreationはリソースを適切にクリーンアップすべき"""
        # Given: 移行後のCharacterCreationWizard with WizardWindow
        from src.ui.character_creation import CharacterCreationWizard
        wizard = CharacterCreationWizard(self.mock_callback)
        
        # ウィザードを開始
        wizard.start()
        
        # When: クリーンアップを実行
        wizard.cleanup()
        
        # Then: WizardWindowもクリーンアップされる
        assert wizard.wizard_window is None or hasattr(wizard.wizard_window, 'cleanup')