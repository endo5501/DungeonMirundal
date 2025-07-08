"""ウィザードサービスパネルのテスト"""

import pytest
import pygame
import pygame_gui
from unittest.mock import Mock, MagicMock, patch
from dataclasses import dataclass
from enum import Enum


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
            
            panel = WizardServicePanel(rect, parent, controller, service_id, ui_manager)
            
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
            panel.container = Mock()
            panel.steps = sample_character_creation_steps
            panel.current_step_index = 1  # 2番目のステップが現在
            
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
            panel.container = Mock()
            
            with patch('pygame_gui.elements.UIPanel'), \
                 patch.object(WizardServicePanel, '_create_button') as mock_create_button, \
                 patch.object(WizardServicePanel, '_update_navigation_buttons') as mock_update:
                
                panel._create_navigation_buttons(50)
                
                # 3つのボタンが作成される（キャンセル、戻る、次へ）
                assert mock_create_button.call_count == 3
                
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
        
        with patch.object(WizardServicePanel, '_create_step_panel') as mock_create, \
             patch.object(WizardServicePanel, '_update_step_indicator') as mock_indicator, \
             patch.object(WizardServicePanel, '_update_navigation_buttons') as mock_nav:
            
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
        
        step = MockWizardStep("test", "テストステップ", "テスト用のステップです")
        
        with patch('pygame_gui.elements.UIPanel') as mock_panel, \
             patch('pygame_gui.elements.UILabel') as mock_label, \
             patch.object(WizardServicePanel, '_create_step_content') as mock_content:
            
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
        
        with patch.object(WizardServicePanel, '_create_name_input_content') as mock_name:
            WizardServicePanel._create_step_content(panel, step, step_panel)
            
            # 名前入力コンテンツが作成される
            mock_name.assert_called_with(panel, step_panel)
    
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