"""
CharacterCreationWizard のテスト

t-wada式TDDによるテストファースト開発
既存キャラクター作成UIから新Window Systemへの移行
"""

import pytest
import pygame
import pygame_gui
from unittest.mock import Mock, patch, MagicMock
from src.ui.window_system import Window, WindowState
from src.ui.window_system.character_creation_wizard import CharacterCreationWizard, WizardStep


class TestCharacterCreationWizard:
    """CharacterCreationWizard のテストクラス"""
    
    def setup_method(self):
        """各テストメソッドの前に実行される"""
        pygame.init()
        pygame.display.set_mode((1, 1), pygame.NOFRAME)
        
        # pygame_guiフォント警告を最小化（テスト環境）
        import warnings
        warnings.filterwarnings("ignore", category=UserWarning, module="pygame_gui")
    
    def teardown_method(self):
        """各テストメソッドの後に実行される"""
        pygame.quit()
    
    def test_character_creation_wizard_inherits_from_window(self):
        """CharacterCreationWizardがWindowクラスを継承することを確認"""
        # Given: ウィザード設定
        wizard_config = {
            'character_classes': ['戦士', '魔法使い', '僧侶'],
            'races': ['人間', 'エルフ', 'ドワーフ']
        }
        
        # When: CharacterCreationWizardを作成
        wizard = CharacterCreationWizard('character_wizard', wizard_config)
        
        # Then: Windowクラスを継承している
        assert isinstance(wizard, Window)
        assert wizard.window_id == 'character_wizard'
        assert wizard.wizard_config.character_classes == wizard_config['character_classes']
        assert wizard.wizard_config.races == wizard_config['races']
        assert wizard.modal is True  # ウィザードは通常モーダル
    
    def test_wizard_validates_config_structure(self):
        """ウィザードの設定構造が検証されることを確認"""
        # Given: 不正な設定
        
        # When: character_classesが無い設定でウィザードを作成しようとする
        # Then: 例外が発生する
        with pytest.raises(ValueError, match="Wizard config must contain 'character_classes'"):
            CharacterCreationWizard('invalid_wizard', {})
        
        # When: racesが無い設定でウィザードを作成しようとする
        # Then: 例外が発生する
        with pytest.raises(ValueError, match="Wizard config must contain 'races'"):
            CharacterCreationWizard('invalid_wizard', {'character_classes': ['戦士']})
    
    def test_wizard_initializes_with_name_input_step(self):
        """ウィザードが名前入力ステップで初期化されることを確認"""
        # Given: ウィザード設定
        wizard_config = {
            'character_classes': ['戦士', '魔法使い'],
            'races': ['人間', 'エルフ']
        }
        
        wizard = CharacterCreationWizard('name_wizard', wizard_config)
        wizard.create()
        
        # Then: 名前入力ステップで開始される
        assert wizard.current_step == WizardStep.NAME_INPUT
        assert wizard.current_step_index == 0
        assert wizard.character_data['name'] == ''
    
    def test_wizard_creates_all_required_steps(self):
        """ウィザードが必要なステップを全て作成することを確認"""
        # Given: ウィザード設定
        wizard_config = {
            'character_classes': ['戦士', '魔法使い'],
            'races': ['人間', 'エルフ']
        }
        
        wizard = CharacterCreationWizard('steps_wizard', wizard_config)
        wizard.create()
        
        # Then: 全ステップが作成される
        expected_steps = [
            WizardStep.NAME_INPUT,
            WizardStep.RACE_SELECTION,
            WizardStep.STATS_GENERATION,
            WizardStep.CLASS_SELECTION,
            WizardStep.CONFIRMATION
        ]
        assert wizard.steps == expected_steps
        assert len(wizard.steps) == 5
    
    def test_wizard_validates_name_input(self):
        """名前入力の検証が動作することを確認"""
        # Given: 名前入力ステップのウィザード
        wizard_config = {
            'character_classes': ['戦士'],
            'races': ['人間']
        }
        
        wizard = CharacterCreationWizard('name_validation_wizard', wizard_config)
        wizard.create()
        
        # When: 空の名前を設定しようとする
        result = wizard.set_character_name('')
        
        # Then: 設定が拒否される
        assert result is False
        assert wizard.character_data['name'] == ''
        
        # When: 有効な名前を設定する
        result = wizard.set_character_name('勇者')
        
        # Then: 設定が受け入れられる
        assert result is True
        assert wizard.character_data['name'] == '勇者'
    
    def test_wizard_advances_to_next_step(self):
        """ウィザードが次のステップに進むことを確認"""
        # Given: ウィザード
        wizard_config = {
            'character_classes': ['戦士'],
            'races': ['人間']
        }
        
        wizard = CharacterCreationWizard('advance_wizard', wizard_config)
        wizard.create()
        wizard.set_character_name('勇者')
        
        # When: 次のステップに進む
        result = wizard.next_step()
        
        # Then: 種族選択ステップに進む
        assert result is True
        assert wizard.current_step == WizardStep.RACE_SELECTION
        assert wizard.current_step_index == 1
    
    def test_wizard_prevents_advance_with_invalid_data(self):
        """無効なデータでの次のステップ進行を防ぐことを確認"""
        # Given: 名前未設定のウィザード
        wizard_config = {
            'character_classes': ['戦士'],
            'races': ['人間']
        }
        
        wizard = CharacterCreationWizard('invalid_advance_wizard', wizard_config)
        wizard.create()
        
        # When: 名前未設定で次のステップに進もうとする
        result = wizard.next_step()
        
        # Then: 進行が阻止される
        assert result is False
        assert wizard.current_step == WizardStep.NAME_INPUT
        assert wizard.current_step_index == 0
    
    def test_wizard_goes_back_to_previous_step(self):
        """ウィザードが前のステップに戻ることを確認"""
        # Given: 種族選択ステップのウィザード
        wizard_config = {
            'character_classes': ['戦士'],
            'races': ['人間', 'エルフ']
        }
        
        wizard = CharacterCreationWizard('back_wizard', wizard_config)
        wizard.create()
        wizard.set_character_name('勇者')
        wizard.next_step()  # 種族選択へ
        
        # When: 前のステップに戻る
        result = wizard.previous_step()
        
        # Then: 名前入力ステップに戻る
        assert result is True
        assert wizard.current_step == WizardStep.NAME_INPUT
        assert wizard.current_step_index == 0
    
    def test_wizard_prevents_back_from_first_step(self):
        """最初のステップから戻ることを防ぐことを確認"""
        # Given: 最初のステップのウィザード
        wizard_config = {
            'character_classes': ['戦士'],
            'races': ['人間']
        }
        
        wizard = CharacterCreationWizard('first_step_wizard', wizard_config)
        wizard.create()
        
        # When: 最初のステップから戻ろうとする
        result = wizard.previous_step()
        
        # Then: 戻れない
        assert result is False
        assert wizard.current_step == WizardStep.NAME_INPUT
        assert wizard.current_step_index == 0
    
    def test_wizard_race_selection_functionality(self):
        """種族選択の機能が動作することを確認"""
        # Given: 種族選択ステップのウィザード
        wizard_config = {
            'character_classes': ['戦士'],
            'races': ['人間', 'エルフ', 'ドワーフ']
        }
        
        wizard = CharacterCreationWizard('race_wizard', wizard_config)
        wizard.create()
        wizard.set_character_name('勇者')
        wizard.next_step()  # 種族選択へ
        
        # When: 種族を選択
        result = wizard.set_character_race('エルフ')
        
        # Then: 種族が設定される
        assert result is True
        assert wizard.character_data['race'] == 'エルフ'
    
    def test_wizard_stats_generation_functionality(self):
        """ステータス生成の機能が動作することを確認"""
        # Given: ステータス生成ステップのウィザード
        wizard_config = {
            'character_classes': ['戦士'],
            'races': ['人間']
        }
        
        wizard = CharacterCreationWizard('stats_wizard', wizard_config)
        wizard.create()
        wizard.set_character_name('勇者')
        wizard.next_step()  # 種族選択へ
        wizard.set_character_race('人間')
        wizard.next_step()  # ステータス生成へ
        
        # When: ステータスを生成
        result = wizard.generate_stats()
        
        # Then: ステータスが生成される
        assert result is True
        assert 'strength' in wizard.character_data
        assert 'dexterity' in wizard.character_data
        assert 'constitution' in wizard.character_data
        assert 'intelligence' in wizard.character_data
        assert 'wisdom' in wizard.character_data
        assert 'charisma' in wizard.character_data
    
    def test_wizard_class_selection_functionality(self):
        """職業選択の機能が動作することを確認"""
        # Given: 職業選択ステップのウィザード
        wizard_config = {
            'character_classes': ['戦士', '魔法使い', '僧侶'],
            'races': ['人間']
        }
        
        wizard = CharacterCreationWizard('class_wizard', wizard_config)
        wizard.create()
        wizard.set_character_name('勇者')
        wizard.next_step()  # 種族選択へ
        wizard.set_character_race('人間')
        wizard.next_step()  # ステータス生成へ
        wizard.generate_stats()
        wizard.next_step()  # 職業選択へ
        
        # When: 職業を選択
        result = wizard.set_character_class('魔法使い')
        
        # Then: 職業が設定される
        assert result is True
        assert wizard.character_data['character_class'] == '魔法使い'
    
    def test_wizard_completion_with_valid_data(self):
        """有効なデータでウィザードが完了することを確認"""
        # Given: 全データ設定済みのウィザード
        wizard_config = {
            'character_classes': ['戦士'],
            'races': ['人間']
        }
        
        wizard = CharacterCreationWizard('complete_wizard', wizard_config)
        wizard.create()
        
        # 全ステップを完了
        wizard.set_character_name('勇者')
        wizard.next_step()
        wizard.set_character_race('人間')
        wizard.next_step()
        wizard.generate_stats()
        wizard.next_step()
        wizard.set_character_class('戦士')
        wizard.next_step()  # 確認ステップへ
        
        # When: ウィザードを完了
        with patch.object(wizard, 'send_message') as mock_send:
            result = wizard.complete_wizard()
        
        # Then: 完了処理が実行される
        assert result is True
        mock_send.assert_called_once_with('character_created', {
            'character_data': wizard.character_data
        })
    
    def test_wizard_cancellation_functionality(self):
        """ウィザードのキャンセル機能が動作することを確認"""
        # Given: ウィザード
        wizard_config = {
            'character_classes': ['戦士'],
            'races': ['人間']
        }
        
        wizard = CharacterCreationWizard('cancel_wizard', wizard_config)
        wizard.create()
        wizard.set_character_name('勇者')
        
        # When: ウィザードをキャンセル
        with patch.object(wizard, 'send_message') as mock_send:
            result = wizard.cancel_wizard()
        
        # Then: キャンセル処理が実行される
        assert result is True
        mock_send.assert_called_once_with('character_creation_cancelled')
    
    def test_wizard_keyboard_navigation(self):
        """キーボードナビゲーションが動作することを確認"""
        # Given: ウィザード
        wizard_config = {
            'character_classes': ['戦士'],
            'races': ['人間']
        }
        
        wizard = CharacterCreationWizard('nav_wizard', wizard_config)
        wizard.create()
        wizard.set_character_name('勇者')
        
        # When: Tabキーで次のステップ
        tab_event = Mock()
        tab_event.type = pygame.KEYDOWN
        tab_event.key = pygame.K_TAB
        tab_event.mod = 0
        
        result = wizard.handle_event(tab_event)
        
        # Then: 次のステップに進む
        assert result is True
        assert wizard.current_step == WizardStep.RACE_SELECTION
    
    def test_wizard_escape_key_cancels(self):
        """ESCキーでキャンセルされることを確認"""
        # Given: ウィザード
        wizard_config = {
            'character_classes': ['戦士'],
            'races': ['人間']
        }
        
        wizard = CharacterCreationWizard('esc_wizard', wizard_config)
        wizard.create()
        
        # When: ESCキーを押す
        with patch.object(wizard, 'send_message') as mock_send:
            result = wizard.handle_escape()
        
        # Then: キャンセルされる
        assert result is True
        mock_send.assert_called_once_with('character_creation_cancelled')
    
    def test_wizard_cleanup_removes_ui_elements(self):
        """クリーンアップでUI要素が適切に削除されることを確認"""
        # Given: 作成されたウィザード
        wizard_config = {
            'character_classes': ['戦士'],
            'races': ['人間']
        }
        
        wizard = CharacterCreationWizard('cleanup_wizard', wizard_config)
        wizard.create()
        
        # When: クリーンアップを実行
        wizard.cleanup_ui()
        
        # Then: UI要素が削除される
        assert wizard.steps == []
        assert wizard.character_data == {}
        assert wizard.ui_manager is None