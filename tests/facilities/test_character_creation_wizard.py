"""キャラクター作成ウィザードのテスト"""

import pytest
import pygame
import pygame_gui
from unittest.mock import Mock, MagicMock, patch
from src.facilities.ui.wizard_service_panel import WizardStep
from src.facilities.ui.ui_element_manager import UIElementManager


@pytest.fixture
def mock_controller():
    """FacilityControllerのモック"""
    controller = Mock()
    
    # サービスのモック
    mock_service = Mock()
    controller.service = mock_service
    
    return controller


@pytest.fixture
def mock_ui_setup():
    """UI要素のモック"""
    rect = pygame.Rect(0, 0, 800, 600)
    parent = Mock()
    ui_manager = Mock()
    return rect, parent, ui_manager


@pytest.fixture
def mock_wizard_data():
    """ウィザードデータのサンプル"""
    return {
        "name": "テスト戦士",
        "race": "human",
        "stats": {
            "strength": 16,
            "intelligence": 12,
            "faith": 10,
            "vitality": 14,
            "agility": 13,
            "luck": 11
        },
        "class": "fighter"
    }


class TestCharacterCreationWizardBasic:
    """CharacterCreationWizardの基本機能テスト"""
    
    def test_initialization(self, mock_controller, mock_ui_setup):
        """正常に初期化される"""
        from src.facilities.ui.guild.character_creation_wizard import CharacterCreationWizard
        
        rect, parent, ui_manager = mock_ui_setup
        
        with patch('src.facilities.ui.service_panel.ServicePanel.__init__', return_value=None), \
             patch('src.facilities.ui.wizard_service_panel.WizardServicePanel.__init__', return_value=None):
            
            wizard = CharacterCreationWizard(rect, parent, mock_controller, ui_manager)
            
            # 初期状態の確認
            assert wizard.race_buttons == {}
            assert wizard.class_buttons == {}
            assert wizard.stat_labels == {}
            assert wizard.stat_values == {}
            assert wizard.roll_button is None
            assert wizard.confirm_labels == []
    
    def test_load_wizard_steps(self, mock_controller, mock_ui_setup):
        """ウィザードステップが正しく定義される"""
        from src.facilities.ui.guild.character_creation_wizard import CharacterCreationWizard
        
        rect, parent, ui_manager = mock_ui_setup
        
        with patch('src.facilities.ui.service_panel.ServicePanel.__init__', return_value=None), \
             patch('src.facilities.ui.wizard_service_panel.WizardServicePanel.__init__', return_value=None):
            
            wizard = Mock()
            wizard.steps = []
            
            CharacterCreationWizard._load_wizard_steps(wizard)
            
            # 5つのステップが定義される
            assert len(wizard.steps) == 5
            
            # ステップIDを確認
            step_ids = [step.id for step in wizard.steps]
            expected_ids = ["name", "race", "stats", "class", "confirm"]
            assert step_ids == expected_ids


class TestCharacterCreationWizardNameStep:
    """名前入力ステップのテスト"""
    
    def test_create_name_input_content(self, mock_controller, mock_ui_setup):
        """名前入力コンテンツが作成される"""
        from src.facilities.ui.guild.character_creation_wizard import CharacterCreationWizard
        
        wizard = Mock()
        wizard.wizard_data = {}
        wizard.ui_manager = Mock()
        wizard.ui_elements = []
        wizard.container = Mock()
        wizard.container.get_size.return_value = (800, 600)
        
        panel = Mock()
        
        with patch('pygame_gui.elements.UITextEntryLine') as mock_text_entry, \
             patch('pygame_gui.elements.UIButton') as mock_button:
            
            CharacterCreationWizard._create_name_input_content(wizard, panel)
            
            # UI要素が作成される
            mock_text_entry.assert_called_once()
            mock_button.assert_called_once()
            
            # wizard.name_inputが設定される
            assert hasattr(wizard, 'name_input')
    
    def test_create_name_input_with_existing_data(self, mock_controller):
        """既存データがある場合の名前入力"""
        from src.facilities.ui.guild.character_creation_wizard import CharacterCreationWizard
        
        wizard = Mock()
        wizard.wizard_data = {"name": "既存名前"}
        wizard.ui_manager = Mock()
        wizard.ui_elements = []
        wizard.container = Mock()
        wizard.container.get_size.return_value = (800, 600)
        
        panel = Mock()
        mock_name_input = Mock()
        
        with patch('pygame_gui.elements.UITextEntryLine', return_value=mock_name_input), \
             patch('pygame_gui.elements.UIButton'):
            
            CharacterCreationWizard._create_name_input_content(wizard, panel)
            
            # 既存の値が設定される
            mock_name_input.set_text.assert_called_with("既存名前")
    
    def test_validate_name_valid(self):
        """有効な名前の検証"""
        from src.facilities.ui.guild.character_creation_wizard import CharacterCreationWizard
        
        wizard = Mock()
        
        with patch.object(wizard, '_show_message'):
            result = CharacterCreationWizard._validate_name(wizard, {"name": "有効な名前"})
            assert result is True
    
    def test_validate_name_empty(self):
        """空の名前の検証（デバッグモードではデフォルト名を設定しTrueを返す）"""
        from src.facilities.ui.guild.character_creation_wizard import CharacterCreationWizard
        
        wizard = Mock()
        wizard.wizard_data = {}
        
        with patch.object(wizard, '_show_message') as mock_show:
            result = CharacterCreationWizard._validate_name(wizard, {"name": ""})
            
            # デバッグモードではデフォルト名を設定してTrueを返す
            assert result is True
            assert wizard.wizard_data["name"] == "TestCharacter"
    
    def test_validate_name_too_long(self):
        """長すぎる名前の検証"""
        from src.facilities.ui.guild.character_creation_wizard import CharacterCreationWizard
        
        wizard = Mock()
        long_name = "a" * 21  # 21文字
        
        with patch.object(wizard, '_show_message') as mock_show:
            result = CharacterCreationWizard._validate_name(wizard, {"name": long_name})
            
            assert result is False
            mock_show.assert_called_with("名前は20文字以内で入力してください", "warning")


class TestCharacterCreationWizardRaceStep:
    """種族選択ステップのテスト"""
    
    def test_create_race_selection_content(self, mock_controller):
        """種族選択コンテンツが作成される"""
        from src.facilities.ui.guild.character_creation_wizard import CharacterCreationWizard
        
        wizard = Mock()
        wizard.wizard_data = {}
        wizard.ui_manager = Mock()
        wizard.ui_elements = []
        wizard.race_buttons = {}
        
        panel = Mock()
        
        with patch('pygame_gui.elements.UIButton') as mock_button, \
             patch.object(wizard, '_highlight_button'):
            
            CharacterCreationWizard._create_race_selection_content(wizard, panel)
            
            # 5つの種族ボタンが作成される
            assert mock_button.call_count == 5
            
            # 種族ボタンが辞書に追加される
            assert len(wizard.race_buttons) == 5
    
    def test_create_race_selection_with_existing_selection(self):
        """既存選択がある場合の種族選択"""
        from src.facilities.ui.guild.character_creation_wizard import CharacterCreationWizard
        
        wizard = Mock()
        wizard.wizard_data = {"race": "elf"}
        wizard.ui_manager = Mock()
        wizard.ui_elements = []
        wizard.race_buttons = {}
        
        panel = Mock()
        
        with patch('pygame_gui.elements.UIButton') as mock_button, \
             patch.object(wizard, '_highlight_button') as mock_highlight:
            
            CharacterCreationWizard._create_race_selection_content(wizard, panel)
            
            # ハイライトが呼ばれる
            mock_highlight.assert_called()
    
    def test_select_race(self):
        """種族選択の処理"""
        from src.facilities.ui.guild.character_creation_wizard import CharacterCreationWizard
        
        wizard = Mock()
        wizard.wizard_data = {}
        wizard.race_buttons = {
            "human": Mock(),
            "elf": Mock(),
            "dwarf": Mock()
        }
        
        with patch.object(wizard, '_unhighlight_button') as mock_unhighlight, \
             patch.object(wizard, '_highlight_button') as mock_highlight:
            
            CharacterCreationWizard._select_race(wizard, "elf")
            
            # 全ボタンのハイライトが解除される
            assert mock_unhighlight.call_count == 3
            
            # 選択されたボタンがハイライトされる
            mock_highlight.assert_called_with(wizard.race_buttons["elf"])
            
            # データが設定される
            assert wizard.wizard_data["race"] == "elf"
    
    def test_validate_race_valid(self):
        """有効な種族の検証"""
        from src.facilities.ui.guild.character_creation_wizard import CharacterCreationWizard
        
        wizard = Mock()
        
        with patch.object(wizard, '_show_message'):
            result = CharacterCreationWizard._validate_race(wizard, {"race": "human"})
            assert result is True
    
    def test_validate_race_empty(self):
        """種族が選択されていない場合（デバッグモードでは自動的にhumanを設定）"""
        from src.facilities.ui.guild.character_creation_wizard import CharacterCreationWizard
        
        wizard = Mock()
        wizard.wizard_data = {}
        
        data = {"race": None}
        with patch.object(wizard, '_show_message') as mock_show:
            result = CharacterCreationWizard._validate_race(wizard, data)
            
            # デバッグモードでは自動的にhumanを設定してTrueを返す
            assert result is True
            assert wizard.wizard_data["race"] == "human"
            assert data["race"] == "human"
    
    def test_validate_race_invalid(self):
        """無効な種族の検証"""
        from src.facilities.ui.guild.character_creation_wizard import CharacterCreationWizard
        
        wizard = Mock()
        
        with patch.object(wizard, '_show_message') as mock_show:
            result = CharacterCreationWizard._validate_race(wizard, {"race": "invalid_race"})
            
            assert result is False
            mock_show.assert_called_with("無効な種族です", "error")


class TestCharacterCreationWizardStatsStep:
    """能力値決定ステップのテスト"""
    
    def test_create_stats_roll_content(self):
        """能力値決定コンテンツが作成される"""
        from src.facilities.ui.guild.character_creation_wizard import CharacterCreationWizard
        
        wizard = Mock()
        wizard.wizard_data = {}
        wizard.ui_manager = Mock()
        wizard.ui_elements = []
        wizard.stat_labels = {}
        
        panel = Mock()
        
        with patch('pygame_gui.elements.UIButton') as mock_button, \
             patch('pygame_gui.elements.UILabel') as mock_label:
            
            CharacterCreationWizard._create_stats_roll_content(wizard, panel)
            
            # ロールボタンが作成される
            mock_button.assert_called_once()
            
            # 6つの能力値ラベルが作成される
            assert mock_label.call_count == 12  # ラベル名とラベル値で2倍
            
            # stat_labelsに6つの能力値が追加される
            assert len(wizard.stat_labels) == 6
    
    def test_create_stats_roll_with_existing_stats(self):
        """既存能力値がある場合"""
        from src.facilities.ui.guild.character_creation_wizard import CharacterCreationWizard
        
        wizard = Mock()
        wizard.wizard_data = {"stats": {"strength": 15, "intelligence": 12}}
        wizard.ui_manager = Mock()
        wizard.ui_elements = []
        wizard.stat_labels = {}
        
        panel = Mock()
        
        with patch('pygame_gui.elements.UIButton'), \
             patch('pygame_gui.elements.UILabel'), \
             patch.object(wizard, '_display_stats') as mock_display:
            
            CharacterCreationWizard._create_stats_roll_content(wizard, panel)
            
            # 既存の能力値が表示される
            mock_display.assert_called_with({"strength": 15, "intelligence": 12})
    
    def test_roll_stats(self):
        """能力値ロールの処理"""
        from src.facilities.ui.guild.character_creation_wizard import CharacterCreationWizard
        
        wizard = Mock()
        wizard.wizard_data = {}
        
        with patch('random.randint', return_value=4), \
             patch.object(wizard, '_display_stats') as mock_display:
            
            CharacterCreationWizard._roll_stats(wizard)
            
            # 各能力値が3d6でロールされる（4+4+4=12）
            expected_stats = {
                "strength": 12,
                "intelligence": 12,
                "faith": 12,
                "vitality": 12,
                "agility": 12,
                "luck": 12
            }
            
            assert wizard.wizard_data["stats"] == expected_stats
            mock_display.assert_called_with(expected_stats)
    
    def test_display_stats(self):
        """能力値表示の処理"""
        from src.facilities.ui.guild.character_creation_wizard import CharacterCreationWizard
        
        wizard = Mock()
        wizard.stat_labels = {
            "strength": Mock(),
            "intelligence": Mock()
        }
        wizard.roll_button = Mock()
        
        stats = {"strength": 15, "intelligence": 12}
        
        CharacterCreationWizard._display_stats(wizard, stats)
        
        # 各能力値が表示される
        wizard.stat_labels["strength"].set_text.assert_called_with("15")
        wizard.stat_labels["intelligence"].set_text.assert_called_with("12")
        
        # ボタンテキストが変更される
        wizard.roll_button.set_text.assert_called_with("振り直す")
    
    def test_validate_stats_valid(self):
        """有効な能力値の検証"""
        from src.facilities.ui.guild.character_creation_wizard import CharacterCreationWizard
        
        wizard = Mock()
        valid_stats = {
            "strength": 15,
            "intelligence": 12,
            "faith": 10,
            "vitality": 14,
            "agility": 13,
            "luck": 11
        }
        
        with patch.object(wizard, '_show_message'):
            result = CharacterCreationWizard._validate_stats(wizard, {"stats": valid_stats})
            assert result is True
    
    def test_validate_stats_missing(self):
        """能力値が未設定の場合（デバッグモードではデフォルト値を設定）"""
        from src.facilities.ui.guild.character_creation_wizard import CharacterCreationWizard
        
        wizard = Mock()
        wizard.wizard_data = {}
        
        with patch.object(wizard, '_show_message') as mock_show:
            result = CharacterCreationWizard._validate_stats(wizard, {"stats": None})
            
            # デバッグモードではデフォルト値を設定してTrueを返す
            assert result is True
            expected_stats = {
                "strength": 12,
                "intelligence": 12,
                "faith": 12,
                "vitality": 12,
                "agility": 12,
                "luck": 12
            }
            assert wizard.wizard_data["stats"] == expected_stats
    
    def test_validate_stats_incomplete(self):
        """不完全な能力値の検証"""
        from src.facilities.ui.guild.character_creation_wizard import CharacterCreationWizard
        
        wizard = Mock()
        incomplete_stats = {"strength": 15}  # 他の能力値が不足
        
        with patch.object(wizard, '_show_message') as mock_show:
            result = CharacterCreationWizard._validate_stats(wizard, {"stats": incomplete_stats})
            
            assert result is False
            # 最初に見つからない能力値でエラー
            mock_show.assert_called_with("能力値が不完全です: intelligence", "error")
    
    def test_validate_stats_invalid_value(self):
        """無効な能力値の検証"""
        from src.facilities.ui.guild.character_creation_wizard import CharacterCreationWizard
        
        wizard = Mock()
        invalid_stats = {
            "strength": 25,  # 18を超える
            "intelligence": 12,
            "faith": 10,
            "vitality": 14,
            "agility": 13,
            "luck": 11
        }
        
        with patch.object(wizard, '_show_message') as mock_show:
            result = CharacterCreationWizard._validate_stats(wizard, {"stats": invalid_stats})
            
            assert result is False
            mock_show.assert_called_with("無効な能力値です: strength=25", "error")


class TestCharacterCreationWizardClassStep:
    """職業選択ステップのテスト"""
    
    def test_create_class_selection_content(self):
        """職業選択コンテンツが作成される"""
        from src.facilities.ui.guild.character_creation_wizard import CharacterCreationWizard
        
        wizard = Mock()
        wizard.wizard_data = {}
        wizard.ui_manager = Mock()
        wizard.ui_elements = []
        wizard.class_buttons = {}
        
        panel = Mock()
        
        with patch('pygame_gui.elements.UIButton') as mock_button, \
             patch.object(wizard, '_get_available_classes', return_value=["fighter", "mage"]):
            
            CharacterCreationWizard._create_class_selection_content(wizard, panel)
            
            # 8つの職業ボタンが作成される
            assert mock_button.call_count == 8
            
            # 職業ボタンが辞書に追加される
            assert len(wizard.class_buttons) == 8
    
    def test_get_available_classes_no_stats(self):
        """能力値なしの場合の選択可能職業"""
        from src.facilities.ui.guild.character_creation_wizard import CharacterCreationWizard
        
        wizard = Mock()
        wizard.wizard_data = {}
        
        result = CharacterCreationWizard._get_available_classes(wizard)
        
        # 基本職のみ選択可能
        expected = ["fighter", "priest", "thief", "mage"]
        assert result == expected
    
    def test_get_available_classes_with_high_stats(self):
        """高い能力値の場合の選択可能職業"""
        from src.facilities.ui.guild.character_creation_wizard import CharacterCreationWizard
        
        wizard = Mock()
        wizard.wizard_data = {
            "stats": {
                "strength": 17,
                "intelligence": 17,
                "faith": 17,
                "vitality": 17,
                "agility": 17,
                "luck": 17
            }
        }
        
        result = CharacterCreationWizard._get_available_classes(wizard)
        
        # 全職業が選択可能
        expected = ["fighter", "priest", "thief", "mage", "bishop", "samurai", "lord", "ninja"]
        assert result == expected
    
    def test_select_class(self):
        """職業選択の処理"""
        from src.facilities.ui.guild.character_creation_wizard import CharacterCreationWizard
        
        wizard = Mock()
        wizard.wizard_data = {}
        wizard.class_buttons = {
            "fighter": Mock(),
            "mage": Mock()
        }
        
        with patch.object(wizard, '_unhighlight_button') as mock_unhighlight, \
             patch.object(wizard, '_highlight_button') as mock_highlight:
            
            CharacterCreationWizard._select_class(wizard, "mage")
            
            # 全ボタンのハイライトが解除される
            assert mock_unhighlight.call_count == 2
            
            # 選択されたボタンがハイライトされる
            mock_highlight.assert_called_with(wizard.class_buttons["mage"])
            
            # データが設定される
            assert wizard.wizard_data["class"] == "mage"
    
    def test_validate_class_valid(self):
        """有効な職業の検証"""
        from src.facilities.ui.guild.character_creation_wizard import CharacterCreationWizard
        
        wizard = Mock()
        
        with patch.object(wizard, '_get_available_classes', return_value=["fighter", "mage"]), \
             patch.object(wizard, '_show_message'):
            
            result = CharacterCreationWizard._validate_class(wizard, {"class": "fighter"})
            assert result is True
    
    def test_validate_class_empty(self):
        """職業が選択されていない場合（デバッグモードでは自動的にfighterを設定）"""
        from src.facilities.ui.guild.character_creation_wizard import CharacterCreationWizard
        
        wizard = Mock()
        wizard.wizard_data = {}
        
        # _get_available_classesをMock
        wizard._get_available_classes = Mock(return_value=["fighter", "mage", "priest"])
        with patch.object(wizard, '_show_message') as mock_show:
            
            data = {"class": None}
            result = CharacterCreationWizard._validate_class(wizard, data)
            
            # デバッグモードでは自動的にfighterを設定してTrueを返す
            assert result is True
            assert wizard.wizard_data["class"] == "fighter"
            assert data["class"] == "fighter"
    
    def test_validate_class_unavailable(self):
        """選択不可能な職業の検証"""
        from src.facilities.ui.guild.character_creation_wizard import CharacterCreationWizard
        
        wizard = Mock()
        
        with patch.object(wizard, '_get_available_classes', return_value=["fighter"]), \
             patch.object(wizard, '_show_message') as mock_show:
            
            result = CharacterCreationWizard._validate_class(wizard, {"class": "ninja"})
            
            assert result is False
            mock_show.assert_called_with("その職業は選択できません", "error")


class TestCharacterCreationWizardUIElementManager:
    """UIElementManager統合のテスト"""
    
    def test_create_step_content_with_ui_element_manager(self):
        """UIElementManager有効時のステップコンテンツ作成"""
        from src.facilities.ui.guild.character_creation_wizard import CharacterCreationWizard
        
        wizard = Mock()
        wizard.ui_element_manager = Mock(spec=UIElementManager)
        wizard.ui_element_manager.is_destroyed = False
        wizard.wizard_data = {}
        wizard.ui_manager = Mock()
        wizard.ui_elements = []
        
        panel = Mock()
        step = WizardStep(id="name", name="名前入力")
        
        # 各管理版メソッドのモック
        for step_id in ["name", "race", "stats", "class", "confirm"]:
            method_name = f"_create_{step_id}_{'input_' if step_id == 'name' else 'selection_' if step_id in ['race', 'class'] else 'roll_' if step_id == 'stats' else ''}content_managed"
            setattr(wizard, method_name, Mock())
        
        # nameステップのテスト
        CharacterCreationWizard._create_step_content(wizard, step, panel)
        wizard._create_name_input_content_managed.assert_called_once_with(panel)
    
    def test_create_step_content_fallback(self):
        """UIElementManager無効時のフォールバック"""
        from src.facilities.ui.guild.character_creation_wizard import CharacterCreationWizard
        
        wizard = Mock()
        wizard.ui_element_manager = None  # UIElementManagerが無効
        wizard.wizard_data = {}
        wizard.ui_manager = Mock()
        wizard.ui_elements = []
        
        panel = Mock()
        step = WizardStep(id="name", name="名前入力")
        
        # 通常メソッドのモック
        wizard._create_name_input_content = Mock()
        
        CharacterCreationWizard._create_step_content(wizard, step, panel)
        wizard._create_name_input_content.assert_called_once_with(panel)
    
    def test_race_selection_content_managed(self):
        """管理版の種族選択コンテンツ作成"""
        from src.facilities.ui.guild.character_creation_wizard import CharacterCreationWizard
        
        wizard = Mock()
        wizard.race_buttons = {}
        wizard.wizard_data = {"race": "human"}
        wizard._create_button = Mock(return_value=Mock())
        wizard._highlight_button = Mock()
        
        panel = Mock()
        
        CharacterCreationWizard._create_race_selection_content_managed(wizard, panel)
        
        # 5つの種族ボタンが作成される
        assert wizard._create_button.call_count == 5
        
        # 選択済みの種族がハイライトされる
        wizard._highlight_button.assert_called_once()
    
    def test_stats_roll_content_managed(self):
        """管理版の能力値決定コンテンツ作成"""
        from src.facilities.ui.guild.character_creation_wizard import CharacterCreationWizard
        
        wizard = Mock()
        wizard.stat_labels = {}
        wizard.wizard_data = {"stats": {"strength": 15}}
        wizard._create_button = Mock(return_value=Mock())
        wizard._create_label = Mock(return_value=Mock())
        wizard._display_stats = Mock()
        
        panel = Mock()
        
        CharacterCreationWizard._create_stats_roll_content_managed(wizard, panel)
        
        # ロールボタンが作成される
        wizard._create_button.assert_called_once()
        
        # 能力値ラベルが作成される（6つの能力値 × 2（名前と値））
        assert wizard._create_label.call_count == 12
        
        # 既存の能力値が表示される
        wizard._display_stats.assert_called_once_with({"strength": 15})
    
    def test_class_selection_content_managed(self):
        """管理版の職業選択コンテンツ作成"""
        from src.facilities.ui.guild.character_creation_wizard import CharacterCreationWizard
        
        wizard = Mock()
        wizard.class_buttons = {}
        wizard.wizard_data = {"class": "fighter"}
        wizard._create_button = Mock(return_value=Mock())
        wizard._highlight_button = Mock()
        wizard._get_available_classes = Mock(return_value=["fighter", "priest"])
        
        panel = Mock()
        
        CharacterCreationWizard._create_class_selection_content_managed(wizard, panel)
        
        # 8つの職業ボタンが作成される
        assert wizard._create_button.call_count == 8
        
        # 選択済みの職業がハイライトされる
        wizard._highlight_button.assert_called()
    
    def test_confirmation_content_managed(self):
        """管理版の確認画面コンテンツ作成"""
        from src.facilities.ui.guild.character_creation_wizard import CharacterCreationWizard
        
        wizard = Mock()
        wizard.confirm_labels = []
        wizard._create_character_info_lines = Mock(return_value=["名前: テスト", "種族: 人間", "", "職業: 戦士"])
        wizard._create_label = Mock(return_value=Mock())
        
        panel = Mock()
        
        CharacterCreationWizard._create_confirmation_content_managed(wizard, panel)
        
        # 空行を除いた3つのラベルが作成される
        assert wizard._create_label.call_count == 3
        
        # confirm_labelsに追加される
        assert len(wizard.confirm_labels) == 3


class TestCharacterCreationWizardConfirmStep:
    """確認ステップのテスト"""
    
    def test_create_confirmation_content(self, mock_wizard_data):
        """確認画面コンテンツが作成される"""
        from src.facilities.ui.guild.character_creation_wizard import CharacterCreationWizard
        
        wizard = Mock()
        wizard.ui_manager = Mock()
        wizard.ui_elements = []
        
        panel = Mock()
        
        with patch('pygame_gui.elements.UILabel') as mock_label, \
             patch.object(wizard, '_create_character_info_lines', return_value=["名前: テスト", "種族: human", "職業: fighter"]):
            
            CharacterCreationWizard._create_confirmation_content(wizard, panel)
            
            # ラベルが作成される
            assert mock_label.call_count >= 1
            
            # confirm_labelsが設定される
            assert hasattr(wizard, 'confirm_labels')
    
    def test_create_character_summary(self, mock_wizard_data):
        """キャラクター情報サマリーの作成"""
        from src.facilities.ui.guild.character_creation_wizard import CharacterCreationWizard
        
        wizard = Mock()
        wizard.wizard_data = mock_wizard_data
        
        result = CharacterCreationWizard._create_character_summary(wizard)
        
        # 各情報がサマリーに含まれる
        assert "テスト戦士" in result
        assert "人間" in result
        assert "戦士" in result
        assert "筋力: 16" in result
        assert "知力: 12" in result
    
    def test_create_character_summary_missing_data(self):
        """データが不足している場合のサマリー"""
        from src.facilities.ui.guild.character_creation_wizard import CharacterCreationWizard
        
        wizard = Mock()
        wizard.wizard_data = {}
        
        result = CharacterCreationWizard._create_character_summary(wizard)
        
        # 未設定の項目が表示される
        assert "未設定" in result
        assert "--" in result


class TestCharacterCreationWizardButtonHandling:
    """ボタン処理のテスト"""
    
    def test_handle_button_click_roll_button(self):
        """ダイスロールボタンのクリック処理"""
        from src.facilities.ui.guild.character_creation_wizard import CharacterCreationWizard
        
        wizard = Mock()
        wizard.roll_button = Mock()
        
        button = wizard.roll_button
        
        # Mock the super() call directly
        with patch('builtins.super') as mock_super, \
             patch.object(wizard, '_roll_stats') as mock_roll:
            
            mock_super.return_value.handle_button_click.return_value = False
            
            result = CharacterCreationWizard.handle_button_click(wizard, button)
            
            assert result is True
            mock_roll.assert_called_once()
    
    def test_handle_button_click_race_button(self):
        """種族ボタンのクリック処理"""
        from src.facilities.ui.guild.character_creation_wizard import CharacterCreationWizard
        
        wizard = Mock()
        race_button = Mock()
        wizard.race_buttons = {"elf": race_button}
        wizard.class_buttons = {}
        
        # Mock the super() call directly
        with patch('builtins.super') as mock_super, \
             patch.object(wizard, '_select_race') as mock_select:
            
            mock_super.return_value.handle_button_click.return_value = False
            
            result = CharacterCreationWizard.handle_button_click(wizard, race_button)
            
            assert result is True
            mock_select.assert_called_with("elf")
    
    def test_handle_button_click_class_button(self):
        """職業ボタンのクリック処理"""
        from src.facilities.ui.guild.character_creation_wizard import CharacterCreationWizard
        
        wizard = Mock()
        class_button = Mock()
        wizard.race_buttons = {}
        wizard.class_buttons = {"mage": class_button}
        
        # Mock the super() call directly
        with patch('builtins.super') as mock_super, \
             patch.object(wizard, '_select_class') as mock_select:
            
            mock_super.return_value.handle_button_click.return_value = False
            
            result = CharacterCreationWizard.handle_button_click(wizard, class_button)
            
            assert result is True
            mock_select.assert_called_with("mage")
    
    def test_handle_button_click_parent_handled(self):
        """親クラスで処理された場合"""
        from src.facilities.ui.guild.character_creation_wizard import CharacterCreationWizard
        
        wizard = Mock()
        wizard.race_buttons = {}
        wizard.class_buttons = {}
        button = Mock()
        
        # Mock the super() call directly
        with patch('builtins.super') as mock_super:
            mock_super.return_value.handle_button_click.return_value = True
            
            result = CharacterCreationWizard.handle_button_click(wizard, button)
            
            assert result is True
    
    def test_handle_button_click_unknown_button(self):
        """未知のボタンのクリック処理"""
        from src.facilities.ui.guild.character_creation_wizard import CharacterCreationWizard
        
        wizard = Mock()
        wizard.race_buttons = {}
        wizard.class_buttons = {}
        wizard.roll_button = Mock()
        
        unknown_button = Mock()
        
        # Mock the super() call directly
        with patch('builtins.super') as mock_super:
            mock_super.return_value.handle_button_click.return_value = False
            
            result = CharacterCreationWizard.handle_button_click(wizard, unknown_button)
            
            assert result is False


class TestCharacterCreationWizardUIHelpers:
    """UI補助機能のテスト"""
    
    def test_highlight_button(self):
        """ボタンハイライトの処理"""
        from src.facilities.ui.guild.character_creation_wizard import CharacterCreationWizard
        
        wizard = Mock()
        button = Mock()
        
        CharacterCreationWizard._highlight_button(wizard, button)
        
        # selectedアトリビュートが設定される（存在する場合）
        if hasattr(button, 'selected'):
            assert button.selected is True
    
    def test_unhighlight_button(self):
        """ボタンハイライト解除の処理"""
        from src.facilities.ui.guild.character_creation_wizard import CharacterCreationWizard
        
        wizard = Mock()
        button = Mock()
        button.selected = True
        
        CharacterCreationWizard._unhighlight_button(wizard, button)
        
        # selectedアトリビュートがクリアされる
        assert button.selected is False