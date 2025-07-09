"""ウィザードサービスパネルのテスト"""

import pytest
import pygame
from unittest.mock import Mock, patch
from dataclasses import dataclass


@dataclass
class MockWizardStep:
    """モックウィザードステップ"""
    id: str
    name: str
    description: str = None
    validator: callable = None
    required_fields: list = None
    
    def __post_init__(self):
        if self.required_fields is None:
            self.required_fields = []


@pytest.fixture
def mock_ui_setup():
    """UI要素のモック"""
    rect = pygame.Rect(0, 0, 600, 500)
    parent = Mock()
    controller = Mock()
    service_id = "character_creation"
    ui_manager = Mock()
    return rect, parent, controller, service_id, ui_manager


@pytest.fixture
def sample_character_creation_steps():
    """サンプルキャラクター作成ステップ"""
    return [
        MockWizardStep("name", "名前入力", "キャラクターの名前を入力してください", 
                      required_fields=["name"]),
        MockWizardStep("race", "種族選択", "キャラクターの種族を選択してください",
                      required_fields=["race"]),
        MockWizardStep("stats", "能力値決定", "キャラクターの能力値を決定します",
                      required_fields=["stats"]),
        MockWizardStep("class", "職業選択", "キャラクターの職業を選択してください",
                      required_fields=["class"]),
        MockWizardStep("confirm", "確認", "入力内容を確認してください")
    ]


class TestWizardServicePanelBasic:
    """WizardServicePanelの基本機能テスト"""
    
    def test_initialization(self, mock_ui_setup):
        """正常に初期化される"""
        from src.facilities.ui.wizard_service_panel import WizardServicePanel
        
        rect, parent, controller, service_id, ui_manager = mock_ui_setup
        
        with patch('src.facilities.ui.service_panel.ServicePanel.__init__', return_value=None), \
             patch.object(WizardServicePanel, '_create_ui'):
            panel = WizardServicePanel(rect, parent, controller, service_id, ui_manager)
            
            # Manually set attributes since we're mocking parent init
            panel.rect = rect
            panel.parent = parent
            panel.controller = controller
            panel.service_id = service_id
            panel.ui_manager = ui_manager
            
            # 基本属性の確認
            assert panel.rect == rect
            assert panel.parent == parent
            assert panel.controller == controller
            assert panel.service_id == service_id
            assert panel.ui_manager == ui_manager
            
            # ウィザード固有の初期状態
            assert panel.wizard_data == {}
            assert panel.steps == []
            assert panel.current_step_index == 0
            assert panel.step_panels == {}
            assert panel.step_validators == {}
    
    def test_load_wizard_steps_character_creation(self, mock_ui_setup):
        """キャラクター作成のウィザードステップ読み込み"""
        from src.facilities.ui.wizard_service_panel import WizardServicePanel
        
        rect, parent, controller, service_id, ui_manager = mock_ui_setup
        
        with patch('src.facilities.ui.service_panel.ServicePanel.__init__', return_value=None), \
             patch.object(WizardServicePanel, '_create_ui'):
            panel = WizardServicePanel(rect, parent, controller, service_id, ui_manager)
            # Manually set required attributes since parent init is mocked
            panel.service_id = service_id
            panel.steps = []
            panel._load_wizard_steps()
            
            # キャラクター作成のステップが読み込まれる
            assert len(panel.steps) == 5
            step_ids = [step.id for step in panel.steps]
            expected_ids = ["name", "race", "stats", "class", "confirm"]
            assert step_ids == expected_ids
    
    def test_load_wizard_steps_default(self, mock_ui_setup):
        """デフォルトのウィザードステップ読み込み"""
        from src.facilities.ui.wizard_service_panel import WizardServicePanel
        
        rect, parent, controller, service_id, ui_manager = mock_ui_setup
        service_id = "unknown_service"  # 未知のサービス
        
        with patch('src.facilities.ui.service_panel.ServicePanel.__init__', return_value=None), \
             patch.object(WizardServicePanel, '_create_ui'):
            panel = WizardServicePanel(rect, parent, controller, service_id, ui_manager)
            # Manually set required attributes since parent init is mocked
            panel.service_id = service_id
            panel.steps = []
            panel._load_wizard_steps()
            
            # デフォルトのステップが読み込まれる
            assert len(panel.steps) == 2
            step_ids = [step.id for step in panel.steps]
            expected_ids = ["input", "confirm"]
            assert step_ids == expected_ids


class TestWizardServicePanelUICreation:
    """WizardServicePanelのUI作成テスト"""
    
    def test_create_ui_flow(self, mock_ui_setup):
        """UI作成フローの確認"""
        from src.facilities.ui.wizard_service_panel import WizardServicePanel
        
        rect, parent, controller, service_id, ui_manager = mock_ui_setup
        
        with patch.object(WizardServicePanel, '_load_wizard_steps') as mock_load, \
             patch.object(WizardServicePanel, '_create_step_indicator') as mock_indicator, \
             patch.object(WizardServicePanel, '_create_navigation_buttons') as mock_nav, \
             patch.object(WizardServicePanel, '_show_step') as mock_show, \
             patch('pygame_gui.elements.UIPanel'):
            
            WizardServicePanel(rect, parent, controller, service_id, ui_manager)
            
            # 各作成メソッドが呼ばれる
            mock_load.assert_called_once()
            mock_indicator.assert_called_once()
            mock_nav.assert_called_once()
            mock_show.assert_called_with(0)  # 最初のステップ
    
    def test_create_step_indicator(self, mock_ui_setup, sample_character_creation_steps):
        """ステップインジケーター作成"""
        from src.facilities.ui.wizard_service_panel import WizardServicePanel
        
        rect, parent, controller, service_id, ui_manager = mock_ui_setup
        
        with patch('src.facilities.ui.service_panel.ServicePanel.__init__', return_value=None), \
             patch.object(WizardServicePanel, '_create_ui'):
            panel = WizardServicePanel(rect, parent, controller, service_id, ui_manager)
            # Manually set all required attributes since parent init is mocked
            panel.container = Mock()
            panel.rect = pygame.Rect(0, 0, 600, 500)
            panel.ui_manager = ui_manager
            panel.ui_elements = []
            panel.steps = sample_character_creation_steps
            panel.current_step_index = 1
            
            with patch('pygame_gui.elements.UIPanel') as mock_panel, \
                 patch('pygame_gui.elements.UILabel') as mock_label:
                
                panel._create_step_indicator(60)
                
                # インジケーターパネルが作成される
                mock_panel.assert_called_once()
                
                # 各ステップのラベルが作成される
                assert mock_label.call_count == 5
    
    def test_create_navigation_buttons(self, mock_ui_setup):
        """ナビゲーションボタン作成"""
        from src.facilities.ui.wizard_service_panel import WizardServicePanel
        
        rect, parent, controller, service_id, ui_manager = mock_ui_setup
        
        with patch('src.facilities.ui.service_panel.ServicePanel.__init__', return_value=None), \
             patch.object(WizardServicePanel, '_create_ui'):
            panel = WizardServicePanel(rect, parent, controller, service_id, ui_manager)
            # Manually set all required attributes since parent init is mocked
            panel.container = Mock()
            panel.container.get_size.return_value = (600, 500)
            panel.rect = pygame.Rect(0, 0, 600, 500)
            panel.ui_manager = ui_manager
            panel.ui_elements = []
            
            with patch('pygame_gui.elements.UIPanel'), \
                 patch('pygame_gui.elements.UIButton') as mock_button, \
                 patch.object(panel, '_update_navigation_buttons') as mock_update:
                
                panel._create_navigation_buttons(50)
                
                # 3つのボタンが作成される（キャンセル、戻る、次へ）
                assert mock_button.call_count == 3
                
                # ボタン状態が更新される
                mock_update.assert_called_once()


class TestWizardServicePanelNavigation:
    """WizardServicePanelのナビゲーション機能テスト"""
    
    def test_update_navigation_buttons_first_step(self, mock_ui_setup):
        """最初のステップでのナビゲーションボタン更新"""
        from src.facilities.ui.wizard_service_panel import WizardServicePanel
        
        panel = Mock()
        panel.current_step_index = 0
        panel.steps = [Mock(), Mock(), Mock()]  # 3ステップ
        panel.back_button = Mock()
        panel.next_button = Mock()
        
        WizardServicePanel._update_navigation_buttons(panel)
        
        # 戻るボタンが無効化される
        panel.back_button.disable.assert_called_once()
        
        # 次へボタンのテキストが「次へ」になる
        panel.next_button.set_text.assert_called_with("次へ")
    
    def test_update_navigation_buttons_middle_step(self, mock_ui_setup):
        """中間ステップでのナビゲーションボタン更新"""
        from src.facilities.ui.wizard_service_panel import WizardServicePanel
        
        panel = Mock()
        panel.current_step_index = 1
        panel.steps = [Mock(), Mock(), Mock()]  # 3ステップ
        panel.back_button = Mock()
        panel.next_button = Mock()
        
        WizardServicePanel._update_navigation_buttons(panel)
        
        # 戻るボタンが有効化される
        panel.back_button.enable.assert_called_once()
        
        # 次へボタンのテキストが「次へ」になる
        panel.next_button.set_text.assert_called_with("次へ")
    
    def test_update_navigation_buttons_last_step(self, mock_ui_setup):
        """最後のステップでのナビゲーションボタン更新"""
        from src.facilities.ui.wizard_service_panel import WizardServicePanel
        
        panel = Mock()
        panel.current_step_index = 2
        panel.steps = [Mock(), Mock(), Mock()]  # 3ステップ
        panel.back_button = Mock()
        panel.next_button = Mock()
        
        WizardServicePanel._update_navigation_buttons(panel)
        
        # 戻るボタンが有効化される
        panel.back_button.enable.assert_called_once()
        
        # 次へボタンのテキストが「完了」になる
        panel.next_button.set_text.assert_called_with("完了")
    
    def test_show_step_valid(self, mock_ui_setup, sample_character_creation_steps):
        """有効なステップの表示"""
        from src.facilities.ui.wizard_service_panel import WizardServicePanel
        
        panel = Mock()
        panel.steps = sample_character_creation_steps
        panel.current_step_index = 0
        panel.step_panels = {"name": Mock()}
        # Set required attributes for _show_step
        panel.step_panels["name"].hide = Mock()
        
        with patch.object(panel, '_create_step_panel') as mock_create, \
             patch.object(panel, '_update_step_indicator') as mock_indicator, \
             patch.object(panel, '_update_navigation_buttons') as mock_nav:
            
            WizardServicePanel._show_step(panel, 1)
            
            # 前のステップが隠される
            panel.step_panels["name"].hide.assert_called_once()
            
            # ステップインデックスが更新される
            assert panel.current_step_index == 1
            
            # UI更新メソッドが呼ばれる
            mock_indicator.assert_called_once()
            mock_nav.assert_called_once()
    
    def test_show_step_invalid(self, mock_ui_setup, sample_character_creation_steps):
        """無効なステップインデックスの処理"""
        from src.facilities.ui.wizard_service_panel import WizardServicePanel
        
        panel = Mock()
        panel.steps = sample_character_creation_steps
        panel.current_step_index = 0
        
        # 範囲外のインデックス
        WizardServicePanel._show_step(panel, 10)
        
        # ステップインデックスは変更されない
        assert panel.current_step_index == 0


class TestWizardServicePanelStepContent:
    """WizardServicePanelのステップコンテンツテスト"""
    
    def test_create_step_panel(self, mock_ui_setup):
        """ステップパネルの作成"""
        from src.facilities.ui.wizard_service_panel import WizardServicePanel
        
        panel = Mock()
        panel.ui_manager = Mock()
        panel.content_area = Mock()
        panel.content_area.relative_rect = pygame.Rect(0, 0, 400, 300)
        panel.ui_elements = []
        panel.step_panels = {}
        panel.container = Mock()  # Add missing container
        
        step = MockWizardStep("test", "テストステップ", "テスト用のステップです")
        
        with patch('pygame_gui.elements.UIPanel') as mock_panel, \
             patch('pygame_gui.elements.UILabel') as mock_label, \
             patch.object(panel, '_create_step_content') as mock_content:
            
            WizardServicePanel._create_step_panel(panel, step)
            
            # パネルが作成される
            mock_panel.assert_called_once()
            
            # 説明ラベルが作成される
            mock_label.assert_called_once()
            
            # ステップコンテンツが作成される
            mock_content.assert_called_once()
            
            # ステップパネルが登録される
            assert "test" in panel.step_panels
    
    def test_create_step_content_name_step(self, mock_ui_setup):
        """名前入力ステップのコンテンツ作成"""
        from src.facilities.ui.wizard_service_panel import WizardServicePanel
        
        panel = Mock()
        panel.ui_elements = []
        step_panel = Mock()
        
        step = MockWizardStep("name", "名前入力")
        
        with patch.object(panel, '_create_name_input_content') as mock_name:
            WizardServicePanel._create_step_content(panel, step, step_panel)
            
            # 名前入力コンテンツが作成される
            mock_name.assert_called_once_with(step_panel)
    
    def test_create_step_content_other_step(self, mock_ui_setup):
        """その他のステップのコンテンツ作成"""
        from src.facilities.ui.wizard_service_panel import WizardServicePanel
        
        panel = Mock()
        panel.ui_manager = Mock()
        panel.ui_elements = []
        step_panel = Mock()
        step_panel.relative_rect = pygame.Rect(0, 0, 400, 300)
        
        step = MockWizardStep("other", "その他のステップ")
        
        with patch('pygame_gui.elements.UILabel') as mock_label:
            WizardServicePanel._create_step_content(panel, step, step_panel)
            
            # プレースホルダーラベルが作成される
            mock_label.assert_called_once()
    
    def test_create_name_input_content(self, mock_ui_setup):
        """名前入力コンテンツの作成"""
        from src.facilities.ui.wizard_service_panel import WizardServicePanel
        
        panel = Mock()
        panel.ui_manager = Mock()
        panel.ui_elements = []
        panel.wizard_data = {}  # Add wizard_data attribute
        step_panel = Mock()
        
        with patch('pygame_gui.elements.UITextEntryLine') as mock_entry:
            WizardServicePanel._create_name_input_content(panel, step_panel)
            
            # 名前入力フィールドが作成される
            mock_entry.assert_called_once()
            
            # name_input属性が設定される
            assert hasattr(panel, 'name_input')


class TestWizardServicePanelStepIndicatorStyle:
    """ステップインジケータースタイルのテスト"""
    
    def test_step_indicator_style_enum(self):
        """StepIndicatorStyleの定義確認"""
        from src.facilities.ui.wizard_service_panel import StepIndicatorStyle
        
        # 各スタイルが定義されている
        assert StepIndicatorStyle.COMPLETED.value == "completed"
        assert StepIndicatorStyle.CURRENT.value == "current"
        assert StepIndicatorStyle.PENDING.value == "pending"
        assert StepIndicatorStyle.ERROR.value == "error"


class TestWizardServicePanelActions:
    """WizardServicePanelのアクション機能テスト"""
    
    def test_wizard_data_access(self, mock_ui_setup):
        """ウィザードデータへのアクセス"""
        from src.facilities.ui.wizard_service_panel import WizardServicePanel
        
        rect, parent, controller, service_id, ui_manager = mock_ui_setup
        
        with patch('src.facilities.ui.service_panel.ServicePanel.__init__', return_value=None), \
             patch.object(WizardServicePanel, '_create_ui'):
            panel = WizardServicePanel(rect, parent, controller, service_id, ui_manager)
            
            # 初期状態
            assert panel.wizard_data == {}
            
            # データの設定
            panel.wizard_data["name"] = "テストキャラクター"
            panel.wizard_data["race"] = "人間"
            
            # データの取得
            assert panel.wizard_data["name"] == "テストキャラクター"
            assert panel.wizard_data["race"] == "人間"
    
    def test_step_management(self, mock_ui_setup, sample_character_creation_steps):
        """ステップ管理機能"""
        from src.facilities.ui.wizard_service_panel import WizardServicePanel
        
        rect, parent, controller, service_id, ui_manager = mock_ui_setup
        
        with patch('src.facilities.ui.service_panel.ServicePanel.__init__', return_value=None), \
             patch.object(WizardServicePanel, '_create_ui'):
            panel = WizardServicePanel(rect, parent, controller, service_id, ui_manager)
            panel.steps = sample_character_creation_steps
            
            # 現在のステップ取得
            assert panel.current_step_index == 0
            current_step = panel.steps[panel.current_step_index]
            assert current_step.id == "name"
            
            # ステップ数の確認
            assert len(panel.steps) == 5


class TestWizardServicePanelStepContent:
    """追加のステップコンテンツテスト"""
    
    def test_create_race_selection_content(self):
        """種族選択コンテンツの作成"""
        from src.facilities.ui.wizard_service_panel import WizardServicePanel
        
        panel = Mock()
        panel.ui_manager = Mock()
        panel.ui_elements = []
        step_panel = Mock()
        
        with patch('pygame_gui.elements.UISelectionList') as mock_list:
            WizardServicePanel._create_race_selection_content(panel, step_panel)
            
            # 種族選択リストが作成される
            mock_list.assert_called_once()
            
            # race_selection属性が設定される
            assert hasattr(panel, 'race_selection')
    
    def test_create_stats_roll_content(self):
        """ステータスロールコンテンツの作成"""
        from src.facilities.ui.wizard_service_panel import WizardServicePanel
        
        panel = Mock()
        panel.ui_manager = Mock()
        panel.ui_elements = []
        step_panel = Mock()
        
        with patch('pygame_gui.elements.UILabel') as mock_label:
            WizardServicePanel._create_stats_roll_content(panel, step_panel)
            
            # ステータスラベルが作成される
            mock_label.assert_called_once()
            
            # stats_label属性が設定される
            assert hasattr(panel, 'stats_label')
    
    def test_create_class_selection_content(self):
        """クラス選択コンテンツの作成"""
        from src.facilities.ui.wizard_service_panel import WizardServicePanel
        
        panel = Mock()
        panel.ui_manager = Mock()
        panel.ui_elements = []
        step_panel = Mock()
        
        with patch('pygame_gui.elements.UISelectionList') as mock_list:
            WizardServicePanel._create_class_selection_content(panel, step_panel)
            
            # クラス選択リストが作成される
            mock_list.assert_called_once()
            
            # class_selection属性が設定される
            assert hasattr(panel, 'class_selection')
    
    def test_create_confirmation_content(self):
        """確認コンテンツの作成"""
        from src.facilities.ui.wizard_service_panel import WizardServicePanel
        
        panel = Mock()
        panel.ui_manager = Mock()
        panel.ui_elements = []
        step_panel = Mock()
        
        with patch('pygame_gui.elements.UILabel') as mock_label, \
             patch.object(panel, '_build_confirmation_text', return_value="テスト確認テキスト"):
            WizardServicePanel._create_confirmation_content(panel, step_panel)
            
            # 2つのUILabelが作成される
            assert mock_label.call_count == 2
            
            # confirmation_label属性が設定される
            assert hasattr(panel, 'confirmation_label')
            assert hasattr(panel, 'confirmation_display')


class TestWizardServicePanelNavigation:
    """追加のナビゲーション機能テスト"""
    
    def test_next_step_valid(self, sample_character_creation_steps):
        """有効な次のステップへの遷移"""
        from src.facilities.ui.wizard_service_panel import WizardServicePanel
        
        panel = Mock()
        panel.steps = sample_character_creation_steps
        panel.current_step_index = 0
        panel.wizard_data = {}
        
        # name_inputのモック
        panel.name_input = Mock()
        panel.name_input.get_text.return_value = "テストキャラクター"
        
        with patch.object(panel, '_collect_step_data') as mock_collect, \
             patch.object(panel, '_validate_current_step', return_value=True) as mock_validate, \
             patch.object(panel, '_show_step') as mock_show:
            
            WizardServicePanel.next_step(panel)
            
            # データ収集と検証が呼ばれる
            mock_collect.assert_called_once()
            mock_validate.assert_called_once()
            
            # 次のステップが表示される
            mock_show.assert_called_with(1)
    
    def test_next_step_validation_failure(self, sample_character_creation_steps):
        """バリデーション失敗時の次のステップへの遷移"""
        from src.facilities.ui.wizard_service_panel import WizardServicePanel
        
        panel = Mock()
        panel.steps = sample_character_creation_steps
        panel.current_step_index = 0
        
        with patch.object(panel, '_collect_step_data') as mock_collect, \
             patch.object(panel, '_validate_current_step', return_value=False) as mock_validate, \
             patch.object(panel, '_show_step') as mock_show:
            
            WizardServicePanel.next_step(panel)
            
            # データ収集と検証が呼ばれる
            mock_collect.assert_called_once()
            mock_validate.assert_called_once()
            
            # 次のステップは表示されない
            mock_show.assert_not_called()
    
    def test_next_step_last_step(self, sample_character_creation_steps):
        """最後のステップでの次へボタンクリック"""
        from src.facilities.ui.wizard_service_panel import WizardServicePanel
        
        panel = Mock()
        panel.steps = sample_character_creation_steps
        panel.current_step_index = len(sample_character_creation_steps) - 1
        
        with patch.object(panel, '_collect_step_data') as mock_collect, \
             patch.object(panel, '_validate_current_step', return_value=True) as mock_validate, \
             patch.object(panel, '_complete_wizard') as mock_complete:
            
            WizardServicePanel.next_step(panel)
            
            # データ収集と検証が呼ばれる
            mock_collect.assert_called_once()
            mock_validate.assert_called_once()
            
            # ウィザード完了処理が呼ばれる
            mock_complete.assert_called_once()
    
    def test_previous_step(self, sample_character_creation_steps):
        """前のステップへの遷移"""
        from src.facilities.ui.wizard_service_panel import WizardServicePanel
        
        panel = Mock()
        panel.steps = sample_character_creation_steps
        panel.current_step_index = 2
        
        with patch.object(panel, '_collect_step_data') as mock_collect, \
             patch.object(panel, '_show_step') as mock_show:
            
            WizardServicePanel.previous_step(panel)
            
            # データ収集が呼ばれる
            mock_collect.assert_called_once()
            
            # 前のステップが表示される
            mock_show.assert_called_with(1)
    
    def test_previous_step_first_step(self, sample_character_creation_steps):
        """最初のステップでの戻るボタンクリック"""
        from src.facilities.ui.wizard_service_panel import WizardServicePanel
        
        panel = Mock()
        panel.steps = sample_character_creation_steps
        panel.current_step_index = 0
        
        with patch.object(panel, '_collect_step_data') as mock_collect, \
             patch.object(panel, '_show_step') as mock_show:
            
            WizardServicePanel.previous_step(panel)
            
            # データ収集は呼ばれない
            mock_collect.assert_not_called()
            
            # ステップは変更されない
            mock_show.assert_not_called()


class TestWizardServicePanelCompletion:
    """ウィザード完了処理のテスト"""
    
    def test_complete_wizard_success(self):
        """ウィザード完了処理成功"""
        from src.facilities.ui.wizard_service_panel import WizardServicePanel
        from src.facilities.core.service_result import ServiceResult
        
        panel = Mock()
        panel.service_id = "test_service"
        panel.wizard_data = {"name": "テスト", "race": "人間"}
        panel.step_panels = {}
        
        success_result = ServiceResult(
            success=True,
            message="ウィザードが完了しました"
        )
        
        with patch.object(panel, '_validate_all_steps', return_value=True) as mock_validate, \
             patch.object(panel, '_execute_service_action', return_value=success_result) as mock_execute, \
             patch.object(panel, '_show_message') as mock_message:
            
            WizardServicePanel._complete_wizard(panel)
            
            # 検証が呼ばれる
            mock_validate.assert_called_once()
            
            # サービスアクションが実行される
            mock_execute.assert_called_with("test_service_complete", panel.wizard_data)
            
            # 成功メッセージが表示される
            mock_message.assert_called_with("ウィザードが完了しました", "info")
    
    def test_complete_wizard_validation_failure(self):
        """バリデーション失敗時のウィザード完了処理"""
        from src.facilities.ui.wizard_service_panel import WizardServicePanel
        
        panel = Mock()
        panel.wizard_data = {"name": ""}  # 不完全なデータ
        
        with patch.object(panel, '_validate_all_steps', return_value=False) as mock_validate, \
             patch.object(panel, '_execute_service_action') as mock_execute:
            
            WizardServicePanel._complete_wizard(panel)
            
            # 検証が呼ばれる
            mock_validate.assert_called_once()
            
            # サービスアクションは実行されない
            mock_execute.assert_not_called()
    
    def test_complete_wizard_service_failure(self):
        """サービス失敗時のウィザード完了処理"""
        from src.facilities.ui.wizard_service_panel import WizardServicePanel
        from src.facilities.core.service_result import ServiceResult
        
        panel = Mock()
        panel.service_id = "test_service"
        panel.wizard_data = {"name": "テスト", "race": "人間"}
        
        failure_result = ServiceResult(
            success=False,
            message="エラーが発生しました"
        )
        
        with patch.object(panel, '_validate_all_steps', return_value=True) as mock_validate, \
             patch.object(panel, '_execute_service_action', return_value=failure_result) as mock_execute, \
             patch.object(panel, '_show_message') as mock_message:
            
            WizardServicePanel._complete_wizard(panel)
            
            # エラーメッセージが表示される
            mock_message.assert_called_with("エラーが発生しました", "error")
    
    def test_validate_all_steps(self, sample_character_creation_steps):
        """全ステップの検証"""
        from src.facilities.ui.wizard_service_panel import WizardServicePanel
        
        panel = Mock()
        panel.steps = sample_character_creation_steps
        panel.wizard_data = {
            "name": "テストキャラクター",
            "race": "人間",
            "stats": {"str": 10, "dex": 12},
            "class": "戦士"
        }
        
        with patch.object(panel, '_show_message') as mock_message:
            result = WizardServicePanel._validate_all_steps(panel)
            
            # 全て必須フィールドが埋まっているので成功
            assert result is True
            
            # エラーメッセージは表示されない
            mock_message.assert_not_called()
    
    def test_validate_all_steps_missing_field(self, sample_character_creation_steps):
        """必須フィールドが不足している場合の検証"""
        from src.facilities.ui.wizard_service_panel import WizardServicePanel
        
        panel = Mock()
        panel.steps = sample_character_creation_steps
        panel.wizard_data = {
            "name": "",  # 空の名前
            "race": "人間"
        }
        
        with patch.object(panel, '_show_message') as mock_message:
            result = WizardServicePanel._validate_all_steps(panel)
            
            # バリデーションエラー
            assert result is False
            
            # エラーメッセージが表示される
            mock_message.assert_called_once()


class TestWizardServicePanelButtonHandling:
    """ボタンハンドリングのテスト"""
    
    def test_handle_button_click_next(self):
        """次へボタンクリックの処理"""
        from src.facilities.ui.wizard_service_panel import WizardServicePanel
        
        panel = Mock()
        panel.next_button = Mock()
        panel.back_button = Mock()
        panel.cancel_button = Mock()
        
        with patch.object(panel, 'next_step') as mock_next:
            result = WizardServicePanel.handle_button_click(panel, panel.next_button)
            
            assert result is True
            mock_next.assert_called_once()
    
    def test_handle_button_click_back(self):
        """戻るボタンクリックの処理"""
        from src.facilities.ui.wizard_service_panel import WizardServicePanel
        
        panel = Mock()
        panel.next_button = Mock()
        panel.back_button = Mock()
        panel.cancel_button = Mock()
        
        with patch.object(panel, 'previous_step') as mock_prev:
            result = WizardServicePanel.handle_button_click(panel, panel.back_button)
            
            assert result is True
            mock_prev.assert_called_once()
    
    def test_handle_button_click_cancel(self):
        """キャンセルボタンクリックの処理"""
        from src.facilities.ui.wizard_service_panel import WizardServicePanel
        
        panel = Mock()
        panel.next_button = Mock()
        panel.back_button = Mock()
        panel.cancel_button = Mock()
        
        with patch.object(panel, '_cancel_wizard') as mock_cancel:
            result = WizardServicePanel.handle_button_click(panel, panel.cancel_button)
            
            assert result is True
            mock_cancel.assert_called_once()
    
    def test_cancel_wizard(self):
        """ウィザードのキャンセル処理"""
        from src.facilities.ui.wizard_service_panel import WizardServicePanel
        
        panel = Mock()
        
        with patch.object(panel, '_show_message') as mock_message:
            WizardServicePanel._cancel_wizard(panel)
            
            # キャンセルメッセージが表示される
            mock_message.assert_called_with("ウィザードをキャンセルしました", "info")


class TestWizardServicePanelStepIndicatorUpdate:
    """ステップインジケーター更新のテスト"""
    
    def test_update_step_indicator(self):
        """ステップインジケーターの更新"""
        from src.facilities.ui.wizard_service_panel import WizardServicePanel
        
        panel = Mock()
        panel.indicator_panel = Mock()
        panel.indicator_panel.element_ids = []
        
        with patch.object(panel, '_create_step_indicator') as mock_create:
            WizardServicePanel._update_step_indicator(panel)
            
            # インジケーターが再作成される
            mock_create.assert_called_with(60)


class TestWizardServicePanelDataCollection:
    """データ収集のテスト"""
    
    def test_collect_step_data_name(self, sample_character_creation_steps):
        """名前ステップのデータ収集"""
        from src.facilities.ui.wizard_service_panel import WizardServicePanel
        
        panel = Mock()
        panel.steps = sample_character_creation_steps
        panel.current_step_index = 0  # name step
        panel.wizard_data = {}
        panel.name_input = Mock()
        panel.name_input.get_text.return_value = "テストキャラクター"
        
        WizardServicePanel._collect_step_data(panel)
        
        # 名前が収集される
        assert panel.wizard_data["name"] == "テストキャラクター"
    
    def test_collect_step_data_race(self, sample_character_creation_steps):
        """種族ステップのデータ収集"""
        from src.facilities.ui.wizard_service_panel import WizardServicePanel
        
        panel = Mock()
        panel.steps = sample_character_creation_steps
        panel.current_step_index = 1  # race step
        panel.wizard_data = {}
        panel.race_selection = Mock()
        panel.race_selection.get_single_selection.return_value = 0
        panel.race_data = ["人間", "エルフ", "ドワーフ"]
        
        WizardServicePanel._collect_step_data(panel)
        
        # 種族が収集される
        assert panel.wizard_data["race"] == "人間"
    
    def test_collect_step_data_stats(self, sample_character_creation_steps):
        """ステータスステップのデータ収集"""
        from src.facilities.ui.wizard_service_panel import WizardServicePanel
        
        panel = Mock()
        panel.steps = sample_character_creation_steps
        panel.current_step_index = 2  # stats step
        panel.wizard_data = {}
        panel.stats_data = {"str": 15, "dex": 12, "con": 14}
        
        WizardServicePanel._collect_step_data(panel)
        
        # ステータスが収集される
        assert panel.wizard_data["stats"] == {"str": 15, "dex": 12, "con": 14}
    
    def test_collect_step_data_class(self, sample_character_creation_steps):
        """クラスステップのデータ収集"""
        from src.facilities.ui.wizard_service_panel import WizardServicePanel
        
        panel = Mock()
        panel.steps = sample_character_creation_steps
        panel.current_step_index = 3  # class step
        panel.wizard_data = {}
        panel.class_selection = Mock()
        panel.class_selection.get_single_selection.return_value = 1
        panel.class_data = ["戦士", "魔法使い", "僧侶"]
        
        WizardServicePanel._collect_step_data(panel)
        
        # クラスが収集される
        assert panel.wizard_data["class"] == "魔法使い"
    
    def test_collect_step_data_out_of_range(self, sample_character_creation_steps):
        """範囲外のステップインデックスでのデータ収集"""
        from src.facilities.ui.wizard_service_panel import WizardServicePanel
        
        panel = Mock()
        panel.steps = sample_character_creation_steps
        panel.current_step_index = 10  # out of range
        panel.wizard_data = {}
        
        # エラーが発生しない
        WizardServicePanel._collect_step_data(panel)
        
        # データは変更されない
        assert panel.wizard_data == {}


class TestWizardServicePanelValidation:
    """バリデーションのテスト"""
    
    def test_validate_current_step_with_validator(self, sample_character_creation_steps):
        """カスタムバリデーターがある場合の検証"""
        from src.facilities.ui.wizard_service_panel import WizardServicePanel
        
        panel = Mock()
        panel.steps = sample_character_creation_steps
        panel.current_step_index = 0
        panel.wizard_data = {"name": "テスト"}
        
        # カスタムバリデーターを設定
        custom_validator = Mock(return_value=True)
        panel.steps[0].validator = custom_validator
        
        result = WizardServicePanel._validate_current_step(panel)
        
        # カスタムバリデーターが呼ばれる
        custom_validator.assert_called_with(panel.wizard_data)
        assert result is True
    
    def test_validate_current_step_required_fields(self, sample_character_creation_steps):
        """必須フィールドの検証"""
        from src.facilities.ui.wizard_service_panel import WizardServicePanel
        
        panel = Mock()
        panel.steps = sample_character_creation_steps
        panel.current_step_index = 0
        panel.wizard_data = {"name": "テスト"}
        
        with patch.object(panel, '_show_message') as mock_message:
            result = WizardServicePanel._validate_current_step(panel)
            
            # 必須フィールドが埋まっているので成功
            assert result is True
            mock_message.assert_not_called()
    
    def test_validate_current_step_missing_required(self, sample_character_creation_steps):
        """必須フィールドが不足している場合の検証"""
        from src.facilities.ui.wizard_service_panel import WizardServicePanel
        
        panel = Mock()
        panel.steps = sample_character_creation_steps
        panel.current_step_index = 0
        panel.wizard_data = {}  # nameフィールドが不足
        
        with patch.object(panel, '_show_message') as mock_message:
            result = WizardServicePanel._validate_current_step(panel)
            
            # バリデーションエラー
            assert result is False
            mock_message.assert_called_once()


class TestWizardServicePanelStepPanelManagement:
    """WizardServicePanelのステップパネル管理テスト"""
    
    def test_create_step_panel(self, sample_character_creation_steps):
        """ステップパネルの作成"""
        from src.facilities.ui.wizard_service_panel import WizardServicePanel
        
        panel = Mock()
        panel.content_area = Mock()
        panel.content_area.relative_rect = pygame.Rect(0, 0, 600, 400)
        panel.ui_manager = Mock()
        panel.ui_elements = []
        panel.step_panels = {}
        
        step = sample_character_creation_steps[0]  # name step
        
        with patch('pygame_gui.elements.UIPanel') as mock_panel, \
             patch('pygame_gui.elements.UILabel') as mock_label, \
             patch.object(panel, '_create_step_content') as mock_content:
            
            mock_panel_instance = Mock()
            mock_panel_instance.relative_rect = Mock()
            mock_panel_instance.relative_rect.width = 580
            mock_panel.return_value = mock_panel_instance
            
            WizardServicePanel._create_step_panel(panel, step)
            
            # パネルが作成される
            mock_panel.assert_called_once()
            
            # 説明ラベルが作成される（stepに説明がある場合）
            if step.description:
                mock_label.assert_called_once()
            
            # ステップ固有のコンテンツが作成される
            mock_content.assert_called_with(step, mock_panel_instance)
            
            # step_panelsに追加される
            assert panel.step_panels[step.id] == mock_panel_instance
    
    def test_show_step_valid(self, sample_character_creation_steps):
        """有効なステップの表示"""
        from src.facilities.ui.wizard_service_panel import WizardServicePanel
        
        panel = Mock()
        panel.steps = sample_character_creation_steps
        panel.current_step_index = 0
        panel.step_panels = {}
        
        # 現在のステップパネルをモック
        current_panel = Mock()
        panel.step_panels["name"] = current_panel
        
        with patch.object(panel, '_create_step_panel') as mock_create, \
             patch.object(panel, '_cleanup_step_panel') as mock_cleanup, \
             patch.object(panel, '_update_step_indicator') as mock_indicator, \
             patch.object(panel, '_update_navigation_buttons') as mock_nav:
            
            WizardServicePanel._show_step(panel, 1)  # race step
            
            # 現在のステップパネルがクリーンアップされる
            mock_cleanup.assert_called_once_with("name")
            
            # 新しいステップが作成される（まだ存在しない場合）
            mock_create.assert_called_once()
            
            # インデックスが更新される
            assert panel.current_step_index == 1
            
            # UI要素が更新される
            mock_indicator.assert_called_once()
            mock_nav.assert_called_once()
    
    def test_show_step_invalid_index(self, sample_character_creation_steps):
        """無効なインデックスでのステップ表示"""
        from src.facilities.ui.wizard_service_panel import WizardServicePanel
        
        panel = Mock()
        panel.steps = sample_character_creation_steps
        panel.current_step_index = 0
        
        # ログ出力をモック
        with patch('src.facilities.ui.wizard_service_panel.logger') as mock_logger:
            
            WizardServicePanel._show_step(panel, -1)  # 無効なインデックス
            
            # エラーログが出力される
            mock_logger.error.assert_called_with("Invalid step index: -1")
            
            # current_step_indexは変更されない
            assert panel.current_step_index == 0
    
    def test_show_step_existing_panel(self, sample_character_creation_steps):
        """既存のパネルの表示"""
        from src.facilities.ui.wizard_service_panel import WizardServicePanel
        
        panel = Mock()
        panel.steps = sample_character_creation_steps
        panel.current_step_index = 0
        panel.step_panels = {}
        
        # 既存のパネルをセットアップ
        existing_panel = Mock()
        panel.step_panels["race"] = existing_panel
        
        with patch.object(panel, '_create_step_panel') as mock_create, \
             patch.object(panel, '_update_step_indicator') as mock_indicator, \
             patch.object(panel, '_update_navigation_buttons') as mock_nav:
            
            WizardServicePanel._show_step(panel, 1)  # race step
            
            # 既存のパネルが表示される
            existing_panel.show.assert_called_once()
            
            # 新しいパネルは作成されない
            mock_create.assert_not_called()


class TestWizardServicePanelNameInput:
    """WizardServicePanelの名前入力テスト"""
    
    def test_create_name_input_content(self):
        """名前入力コンテンツの作成"""
        from src.facilities.ui.wizard_service_panel import WizardServicePanel
        
        panel = Mock()
        panel.ui_manager = Mock()
        panel.ui_elements = []
        panel.wizard_data = {}
        
        mock_panel = Mock()
        
        with patch('pygame_gui.elements.UITextEntryLine') as mock_entry:
            mock_entry_instance = Mock()
            mock_entry.return_value = mock_entry_instance
            
            WizardServicePanel._create_name_input_content(panel, mock_panel)
            
            # 名前入力フィールドが作成される
            mock_entry.assert_called_once()
            
            # panelにname_inputが設定される
            assert hasattr(panel, 'name_input')
            assert panel.name_input == mock_entry_instance
            
            # ui_elementsに追加される
            assert mock_entry_instance in panel.ui_elements
    
    def test_create_name_input_content_with_existing_data(self):
        """既存データありでの名前入力コンテンツ作成"""
        from src.facilities.ui.wizard_service_panel import WizardServicePanel
        
        panel = Mock()
        panel.ui_manager = Mock()
        panel.ui_elements = []
        panel.wizard_data = {"name": "既存の名前"}
        
        mock_panel = Mock()
        
        with patch('pygame_gui.elements.UITextEntryLine') as mock_entry:
            mock_entry_instance = Mock()
            mock_entry.return_value = mock_entry_instance
            
            WizardServicePanel._create_name_input_content(panel, mock_panel)
            
            # 既存の値が設定される
            mock_entry_instance.set_text.assert_called_with("既存の名前")


class TestWizardServicePanelHighlight:
    """WizardServicePanelのハイライト機能テスト"""
    
    def test_highlight_button_with_selected_attribute(self):
        """selectedアトリビュートありボタンのハイライト"""
        from src.facilities.ui.wizard_service_panel import WizardServicePanel
        
        panel = Mock()
        button = Mock()
        button.selected = False
        
        WizardServicePanel._highlight_button(panel, button)
        
        # selectedがTrueに設定される
        assert button.selected is True
    
    def test_highlight_button_without_selected_attribute(self):
        """selectedアトリビュートなしボタンのハイライト"""
        from src.facilities.ui.wizard_service_panel import WizardServicePanel
        
        panel = Mock()
        button = Mock(spec=[])  # selectedアトリビュートなし
        
        # エラーが発生しない
        WizardServicePanel._highlight_button(panel, button)
    
    def test_highlight_button_none(self):
        """Noneボタンのハイライト"""
        from src.facilities.ui.wizard_service_panel import WizardServicePanel
        
        panel = Mock()
        
        # エラーが発生しない
        WizardServicePanel._highlight_button(panel, None)
    
    def test_unhighlight_button_with_selected_attribute(self):
        """selectedアトリビュートありボタンのハイライト解除"""
        from src.facilities.ui.wizard_service_panel import WizardServicePanel
        
        panel = Mock()
        button = Mock()
        button.selected = True
        
        WizardServicePanel._unhighlight_button(panel, button)
        
        # selectedがFalseに設定される
        assert button.selected is False
    
    def test_unhighlight_button_without_selected_attribute(self):
        """selectedアトリビュートなしボタンのハイライト解除"""
        from src.facilities.ui.wizard_service_panel import WizardServicePanel
        
        panel = Mock()
        button = Mock(spec=[])  # selectedアトリビュートなし
        
        # エラーが発生しない
        WizardServicePanel._unhighlight_button(panel, button)
    
    def test_unhighlight_button_none(self):
        """Noneボタンのハイライト解除"""
        from src.facilities.ui.wizard_service_panel import WizardServicePanel
        
        panel = Mock()
        
        # エラーが発生しない
        WizardServicePanel._unhighlight_button(panel, None)


class TestWizardServicePanelStepIndicatorUpdate:
    """WizardServicePanelのステップインジケーター更新テスト"""
    
    def test_update_step_indicator_cleanup(self):
        """ステップインジケーターの更新とクリーンアップ"""
        from src.facilities.ui.wizard_service_panel import WizardServicePanel
        
        panel = Mock()
        mock_indicator_panel = Mock()
        panel.indicator_panel = mock_indicator_panel
        
        with patch.object(panel, '_create_step_indicator') as mock_create:
            WizardServicePanel._update_step_indicator(panel)
            
            # 既存のパネルがkillされる
            mock_indicator_panel.kill.assert_called_once()
            
            # インジケーターが再作成される
            mock_create.assert_called_with(60)
            
            # パネルがNoneに設定される
            assert panel.indicator_panel is None
    
    def test_update_step_indicator_no_kill_method(self):
        """killメソッドがない要素での更新"""
        from src.facilities.ui.wizard_service_panel import WizardServicePanel
        
        panel = Mock()
        panel.indicator_panel = Mock()
        
        # killメソッドがない要素
        mock_element = Mock(spec=[])  # killメソッドなし
        panel.indicator_panel.element_ids = [mock_element]
        
        with patch.object(panel, '_create_step_indicator') as mock_create:
            # エラーが発生しない
            WizardServicePanel._update_step_indicator(panel)
            
            # インジケーターが再作成される
            mock_create.assert_called_with(60)


class TestWizardServicePanelEdgeCases:
    """WizardServicePanelのエッジケーステスト"""
    
    def test_validate_current_step_out_of_range(self):
        """範囲外インデックスでの検証"""
        from src.facilities.ui.wizard_service_panel import WizardServicePanel
        
        panel = Mock()
        panel.current_step_index = 10  # 範囲外
        panel.steps = []
        
        result = WizardServicePanel._validate_current_step(panel)
        
        # 範囲外なので失敗
        assert result is False
    
    def test_show_step_current_step_out_of_range(self, sample_character_creation_steps):
        """現在のステップが範囲外の場合の表示"""
        from src.facilities.ui.wizard_service_panel import WizardServicePanel
        
        panel = Mock()
        panel.steps = sample_character_creation_steps
        panel.current_step_index = 10  # 範囲外
        panel.step_panels = {}
        
        with patch.object(panel, '_create_step_panel') as mock_create, \
             patch.object(panel, '_update_step_indicator') as mock_indicator, \
             patch.object(panel, '_update_navigation_buttons') as mock_nav:
            
            WizardServicePanel._show_step(panel, 1)  # race step
            
            # エラーが発生せず、通常の処理が行われる
            assert panel.current_step_index == 1
            mock_create.assert_called_once()
            mock_indicator.assert_called_once()
            mock_nav.assert_called_once()
    
    def test_create_step_panel_no_description(self):
        """説明なしステップでのパネル作成"""
        from src.facilities.ui.wizard_service_panel import WizardServicePanel
        
        panel = Mock()
        panel.content_area = Mock()
        panel.content_area.relative_rect = pygame.Rect(0, 0, 600, 400)
        panel.ui_manager = Mock()
        panel.ui_elements = []
        panel.step_panels = {}
        
        step = MockWizardStep("test", "テスト")  # 説明なし
        
        with patch('pygame_gui.elements.UIPanel') as mock_panel, \
             patch('pygame_gui.elements.UILabel') as mock_label, \
             patch.object(panel, '_create_step_content') as mock_content:
            
            mock_panel_instance = Mock()
            mock_panel.return_value = mock_panel_instance
            
            WizardServicePanel._create_step_panel(panel, step)
            
            # パネルが作成される
            mock_panel.assert_called_once()
            
            # 説明ラベルは作成されない
            mock_label.assert_not_called()
            
            # ステップ固有のコンテンツが作成される
            mock_content.assert_called_with(step, mock_panel_instance)