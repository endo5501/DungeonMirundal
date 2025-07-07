"""魔法研究ウィザードのテスト"""

import pytest
import pygame
import pygame_gui
from unittest.mock import Mock, MagicMock, patch
from src.facilities.ui.magic_guild.magic_research_wizard import ResearchStep


@pytest.fixture
def mock_ui_setup():
    """UI要素のモック"""
    rect = pygame.Rect(0, 0, 500, 420)
    parent = Mock()
    ui_manager = Mock()
    controller = Mock()
    service = Mock()
    return rect, parent, ui_manager, controller, service


@pytest.fixture
def sample_researchers():
    """サンプル研究者データ"""
    return [
        {
            "id": "researcher1",
            "name": "魔法使いマーリン",
            "level": 15,
            "specialization": "召喚魔法"
        },
        {
            "id": "researcher2",
            "name": "賢者サラマンダー",
            "level": 12,
            "specialization": "変成魔法"
        }
    ]


@pytest.fixture
def sample_research_types():
    """サンプル研究種別データ"""
    return [
        {
            "id": "spell_creation",
            "name": "新呪文開発",
            "description": "全く新しい呪文を研究開発します",
            "cost": 5000,
            "duration": 30
        },
        {
            "id": "spell_improvement",
            "name": "既存呪文改良",
            "description": "既存の呪文を改良して効果を向上させます",
            "cost": 2000,
            "duration": 14
        }
    ]


class TestMagicResearchWizardBasic:
    """MagicResearchWizardの基本機能テスト"""
    
    def test_initialization(self, mock_ui_setup):
        """正常に初期化される"""
        from src.facilities.ui.magic_guild.magic_research_wizard import MagicResearchWizard
        
        rect, parent, ui_manager, controller, service = mock_ui_setup
        
        with patch('pygame_gui.elements.UIPanel'), \
             patch('pygame_gui.elements.UIButton'), \
             patch('pygame_gui.elements.UILabel'), \
             patch('pygame_gui.elements.UISelectionList'), \
             patch('pygame_gui.elements.UITextBox'), \
             patch.object(MagicResearchWizard, '_create_step_uis'), \
             patch.object(MagicResearchWizard, '_show_current_step'):
            
            wizard = MagicResearchWizard(rect, parent, ui_manager, controller, service)
            
            # 基本属性の確認
            assert wizard.rect == rect
            assert wizard.parent == parent
            assert wizard.ui_manager == ui_manager
            assert wizard.controller == controller
            assert wizard.service == service
            
            # 初期状態の確認
            assert wizard.current_step == ResearchStep.SELECT_RESEARCHER
            assert wizard.research_data == {}
            assert wizard.step_uis == {}
    
    def test_research_step_enum(self):
        """ResearchStepの列挙型テスト"""
        assert ResearchStep.SELECT_RESEARCHER.value == 1
        assert ResearchStep.SELECT_TYPE.value == 2
        assert ResearchStep.CONFIGURE.value == 3
        assert ResearchStep.CONFIRM.value == 4
    
    def test_create_ui_elements(self, mock_ui_setup):
        """UI要素が正常に作成される"""
        from src.facilities.ui.magic_guild.magic_research_wizard import MagicResearchWizard
        
        rect, parent, ui_manager, controller, service = mock_ui_setup
        
        with patch('pygame_gui.elements.UIPanel') as mock_panel, \
             patch('pygame_gui.elements.UIButton') as mock_button, \
             patch.object(MagicResearchWizard, '_create_step_indicator') as mock_indicator, \
             patch.object(MagicResearchWizard, '_create_step_uis'), \
             patch.object(MagicResearchWizard, '_show_current_step'):
            
            mock_button_instances = [Mock(), Mock(), Mock()]
            mock_button.side_effect = mock_button_instances
            
            wizard = MagicResearchWizard(rect, parent, ui_manager, controller, service)
            
            # UI要素が作成される
            assert mock_panel.call_count == 2  # container, content_panel
            mock_indicator.assert_called_once()
            assert mock_button.call_count == 3  # back, next, cancel
            
            # 戻るボタンが初期無効化される
            mock_button_instances[0].disable.assert_called_once()


class TestMagicResearchWizardStepIndicator:
    """MagicResearchWizardのステップインジケーターテスト"""
    
    def test_create_step_indicator(self, mock_ui_setup):
        """ステップインジケーターの作成"""
        from src.facilities.ui.magic_guild.magic_research_wizard import MagicResearchWizard
        
        wizard = Mock()
        wizard.ui_manager = Mock()
        wizard.container = Mock()
        wizard.current_step = ResearchStep.SELECT_TYPE  # 2番目のステップ
        
        with patch('pygame_gui.elements.UIPanel') as mock_panel, \
             patch('pygame_gui.elements.UILabel') as mock_label:
            
            MagicResearchWizard._create_step_indicator(wizard)
            
            # ステップインジケーターパネルが作成される
            mock_panel.assert_called_once()
            
            # 4つのステップラベルが作成される
            assert mock_label.call_count == 4
    
    def test_step_indicator_states(self):
        """ステップインジケーターの状態表示"""
        from src.facilities.ui.magic_guild.magic_research_wizard import MagicResearchWizard
        
        wizard = Mock()
        wizard.ui_manager = Mock()
        wizard.container = Mock()
        wizard.current_step = ResearchStep.CONFIGURE  # 3番目のステップ
        
        label_texts = []
        
        def capture_label_text(*args, **kwargs):
            mock_label = Mock()
            # relative_rectから text= を探す
            if 'text' in kwargs:
                label_texts.append(kwargs['text'])
            return mock_label
        
        with patch('pygame_gui.elements.UIPanel'), \
             patch('pygame_gui.elements.UILabel', side_effect=capture_label_text):
            
            MagicResearchWizard._create_step_indicator(wizard)
            
            # ステップ状態を確認
            assert len(label_texts) == 4
            assert "✓ 研究者選択" in label_texts[0]  # 完了済み
            assert "✓ 研究種別" in label_texts[1]   # 完了済み
            assert "▶ 詳細設定" in label_texts[2]   # 現在
            assert "○ 確認" in label_texts[3]       # 未完了


class TestMagicResearchWizardStepNavigation:
    """MagicResearchWizardのステップナビゲーションテスト"""
    
    def test_next_step_researcher_to_type(self):
        """研究者選択から研究種別へのナビゲーション"""
        from src.facilities.ui.magic_guild.magic_research_wizard import MagicResearchWizard
        
        wizard = Mock()
        wizard.current_step = ResearchStep.SELECT_RESEARCHER
        wizard.research_data = {"researcher_id": "researcher1"}
        
        with patch.object(MagicResearchWizard, '_validate_current_step', return_value=True), \
             patch.object(MagicResearchWizard, '_show_current_step') as mock_show:
            
            MagicResearchWizard._next_step(wizard)
            
            assert wizard.current_step == ResearchStep.SELECT_TYPE
            mock_show.assert_called_once()
    
    def test_next_step_validation_failure(self):
        """ステップ検証失敗時のナビゲーション"""
        from src.facilities.ui.magic_guild.magic_research_wizard import MagicResearchWizard
        
        wizard = Mock()
        wizard.current_step = ResearchStep.SELECT_RESEARCHER
        
        with patch.object(MagicResearchWizard, '_validate_current_step', return_value=False), \
             patch.object(MagicResearchWizard, '_show_current_step') as mock_show:
            
            MagicResearchWizard._next_step(wizard)
            
            # ステップが変更されない
            assert wizard.current_step == ResearchStep.SELECT_RESEARCHER
            mock_show.assert_not_called()
    
    def test_back_step_type_to_researcher(self):
        """研究種別から研究者選択への戻り"""
        from src.facilities.ui.magic_guild.magic_research_wizard import MagicResearchWizard
        
        wizard = Mock()
        wizard.current_step = ResearchStep.SELECT_TYPE
        
        with patch.object(MagicResearchWizard, '_show_current_step') as mock_show:
            MagicResearchWizard._back_step(wizard)
            
            assert wizard.current_step == ResearchStep.SELECT_RESEARCHER
            mock_show.assert_called_once()
    
    def test_back_step_first_step(self):
        """最初のステップでの戻り処理"""
        from src.facilities.ui.magic_guild.magic_research_wizard import MagicResearchWizard
        
        wizard = Mock()
        wizard.current_step = ResearchStep.SELECT_RESEARCHER
        
        with patch.object(MagicResearchWizard, '_show_current_step') as mock_show:
            MagicResearchWizard._back_step(wizard)
            
            # ステップが変更されない
            assert wizard.current_step == ResearchStep.SELECT_RESEARCHER
            mock_show.assert_not_called()


class TestMagicResearchWizardValidation:
    """MagicResearchWizardの検証テスト"""
    
    def test_validate_researcher_selection_valid(self):
        """有効な研究者選択の検証"""
        from src.facilities.ui.magic_guild.magic_research_wizard import MagicResearchWizard
        
        wizard = Mock()
        wizard.research_data = {"researcher_id": "researcher1"}
        
        result = MagicResearchWizard._validate_researcher_selection(wizard)
        
        assert result is True
    
    def test_validate_researcher_selection_invalid(self):
        """無効な研究者選択の検証"""
        from src.facilities.ui.magic_guild.magic_research_wizard import MagicResearchWizard
        
        wizard = Mock()
        wizard.research_data = {}
        
        with patch.object(MagicResearchWizard, '_show_validation_error') as mock_error:
            result = MagicResearchWizard._validate_researcher_selection(wizard)
            
            assert result is False
            mock_error.assert_called_with(wizard, "研究者を選択してください")
    
    def test_validate_research_type_valid(self):
        """有効な研究種別の検証"""
        from src.facilities.ui.magic_guild.magic_research_wizard import MagicResearchWizard
        
        wizard = Mock()
        wizard.research_data = {"research_type": "spell_creation"}
        
        result = MagicResearchWizard._validate_research_type(wizard)
        
        assert result is True
    
    def test_validate_research_type_invalid(self):
        """無効な研究種別の検証"""
        from src.facilities.ui.magic_guild.magic_research_wizard import MagicResearchWizard
        
        wizard = Mock()
        wizard.research_data = {"researcher_id": "researcher1"}
        
        with patch.object(MagicResearchWizard, '_show_validation_error') as mock_error:
            result = MagicResearchWizard._validate_research_type(wizard)
            
            assert result is False
            mock_error.assert_called_with(wizard, "研究種別を選択してください")
    
    def test_validate_current_step(self):
        """現在ステップの検証"""
        from src.facilities.ui.magic_guild.magic_research_wizard import MagicResearchWizard
        
        wizard = Mock()
        wizard.current_step = ResearchStep.SELECT_RESEARCHER
        
        with patch.object(MagicResearchWizard, '_validate_researcher_selection', return_value=True) as mock_validate:
            result = MagicResearchWizard._validate_current_step(wizard)
            
            assert result is True
            mock_validate.assert_called_once()


class TestMagicResearchWizardEventHandling:
    """MagicResearchWizardのイベント処理テスト"""
    
    def test_handle_event_next_button(self):
        """次へボタンのイベント処理"""
        from src.facilities.ui.magic_guild.magic_research_wizard import MagicResearchWizard
        
        wizard = Mock()
        wizard.next_button = Mock()
        
        event = Mock()
        event.type = pygame_gui.UI_BUTTON_PRESSED
        event.ui_element = wizard.next_button
        
        with patch.object(MagicResearchWizard, '_next_step') as mock_next:
            result = MagicResearchWizard.handle_event(wizard, event)
            
            assert result is True
            mock_next.assert_called_once()
    
    def test_handle_event_back_button(self):
        """戻るボタンのイベント処理"""
        from src.facilities.ui.magic_guild.magic_research_wizard import MagicResearchWizard
        
        wizard = Mock()
        wizard.back_button = Mock()
        wizard.next_button = Mock()
        
        event = Mock()
        event.type = pygame_gui.UI_BUTTON_PRESSED
        event.ui_element = wizard.back_button
        
        with patch.object(MagicResearchWizard, '_back_step') as mock_back:
            result = MagicResearchWizard.handle_event(wizard, event)
            
            assert result is True
            mock_back.assert_called_once()
    
    def test_handle_event_cancel_button(self):
        """キャンセルボタンのイベント処理"""
        from src.facilities.ui.magic_guild.magic_research_wizard import MagicResearchWizard
        
        wizard = Mock()
        wizard.cancel_button = Mock()
        wizard.next_button = Mock()
        wizard.back_button = Mock()
        
        event = Mock()
        event.type = pygame_gui.UI_BUTTON_PRESSED
        event.ui_element = wizard.cancel_button
        
        with patch.object(MagicResearchWizard, '_cancel_research') as mock_cancel:
            result = MagicResearchWizard.handle_event(wizard, event)
            
            assert result is True
            mock_cancel.assert_called_once()
    
    def test_handle_event_selection_list(self, sample_researchers):
        """選択リストのイベント処理"""
        from src.facilities.ui.magic_guild.magic_research_wizard import MagicResearchWizard
        
        wizard = Mock()
        wizard.current_step = ResearchStep.SELECT_RESEARCHER
        wizard.step_uis = {
            ResearchStep.SELECT_RESEARCHER: {
                'researcher_list': Mock()
            }
        }
        wizard.research_data = {}
        
        event = Mock()
        event.type = pygame_gui.UI_SELECTION_LIST_NEW_SELECTION
        event.ui_element = wizard.step_uis[ResearchStep.SELECT_RESEARCHER]['researcher_list']
        
        # 研究者データのモック
        wizard.researchers_data = sample_researchers
        event.ui_element.get_single_selection.return_value = 0
        
        with patch.object(MagicResearchWizard, '_update_buttons') as mock_update:
            result = MagicResearchWizard.handle_event(wizard, event)
            
            assert result is True
            assert wizard.research_data["researcher_id"] == "researcher1"
            mock_update.assert_called_once()
    
    def test_handle_event_unknown(self):
        """未知のイベントの処理"""
        from src.facilities.ui.magic_guild.magic_research_wizard import MagicResearchWizard
        
        wizard = Mock()
        
        event = Mock()
        event.type = 999  # 未知のイベント
        
        result = MagicResearchWizard.handle_event(wizard, event)
        
        assert result is False


class TestMagicResearchWizardDataManagement:
    """MagicResearchWizardのデータ管理テスト"""
    
    def test_load_researchers_data(self, sample_researchers):
        """研究者データの読み込み"""
        from src.facilities.ui.magic_guild.magic_research_wizard import MagicResearchWizard
        
        wizard = Mock()
        wizard.service = Mock()
        wizard.step_uis = {
            ResearchStep.SELECT_RESEARCHER: {
                'researcher_list': Mock()
            }
        }
        
        # サービス結果のモック
        result = Mock()
        result.success = True
        result.data = {"researchers": sample_researchers}
        wizard.service.execute_action.return_value = result
        
        MagicResearchWizard._load_researchers_data(wizard)
        
        # データが設定される
        assert wizard.researchers_data == sample_researchers
        
        # リストが更新される
        expected_items = [
            "魔法使いマーリン (Lv.15, 召喚魔法)",
            "賢者サラマンダー (Lv.12, 変成魔法)"
        ]
        wizard.step_uis[ResearchStep.SELECT_RESEARCHER]['researcher_list'].set_item_list.assert_called_with(expected_items)
    
    def test_load_research_types_data(self, sample_research_types):
        """研究種別データの読み込み"""
        from src.facilities.ui.magic_guild.magic_research_wizard import MagicResearchWizard
        
        wizard = Mock()
        wizard.service = Mock()
        wizard.step_uis = {
            ResearchStep.SELECT_TYPE: {
                'type_list': Mock()
            }
        }
        
        # サービス結果のモック
        result = Mock()
        result.success = True
        result.data = {"research_types": sample_research_types}
        wizard.service.execute_action.return_value = result
        
        MagicResearchWizard._load_research_types_data(wizard)
        
        # データが設定される
        assert wizard.research_types_data == sample_research_types
        
        # リストが更新される
        expected_items = [
            "新呪文開発 (費用: 5000G, 期間: 30日)",
            "既存呪文改良 (費用: 2000G, 期間: 14日)"
        ]
        wizard.step_uis[ResearchStep.SELECT_TYPE]['type_list'].set_item_list.assert_called_with(expected_items)


class TestMagicResearchWizardActions:
    """MagicResearchWizardのアクション機能テスト"""
    
    def test_show_current_step(self):
        """現在ステップの表示"""
        from src.facilities.ui.magic_guild.magic_research_wizard import MagicResearchWizard
        
        wizard = Mock()
        wizard.current_step = ResearchStep.SELECT_TYPE
        wizard.step_uis = {
            ResearchStep.SELECT_RESEARCHER: {'title': Mock()},
            ResearchStep.SELECT_TYPE: {'title': Mock()},
            ResearchStep.CONFIGURE: {'title': Mock()},
            ResearchStep.CONFIRM: {'title': Mock()}
        }
        
        with patch.object(MagicResearchWizard, '_hide_all_steps') as mock_hide, \
             patch.object(MagicResearchWizard, '_update_buttons') as mock_update, \
             patch.object(MagicResearchWizard, '_update_step_indicator') as mock_indicator:
            
            MagicResearchWizard._show_current_step(wizard)
            
            # 全ステップが隠される
            mock_hide.assert_called_once()
            
            # 現在ステップが表示される
            for element in wizard.step_uis[ResearchStep.SELECT_TYPE].values():
                element.show.assert_called_once()
            
            # ボタンとインジケーターが更新される
            mock_update.assert_called_once()
            mock_indicator.assert_called_once()
    
    def test_hide_all_steps(self):
        """全ステップの非表示"""
        from src.facilities.ui.magic_guild.magic_research_wizard import MagicResearchWizard
        
        wizard = Mock()
        wizard.step_uis = {
            ResearchStep.SELECT_RESEARCHER: {'title': Mock(), 'list': Mock()},
            ResearchStep.SELECT_TYPE: {'title': Mock(), 'list': Mock()}
        }
        
        MagicResearchWizard._hide_all_steps(wizard)
        
        # 全UI要素が隠される
        for step_ui in wizard.step_uis.values():
            for element in step_ui.values():
                element.hide.assert_called_once()
    
    def test_cancel_research(self):
        """研究のキャンセル"""
        from src.facilities.ui.magic_guild.magic_research_wizard import MagicResearchWizard
        
        wizard = Mock()
        wizard.controller = Mock()
        
        MagicResearchWizard._cancel_research(wizard)
        
        # コントローラーの戻る処理が呼ばれる
        wizard.controller.back.assert_called_once()
    
    def test_show_validation_error(self):
        """検証エラーの表示"""
        from src.facilities.ui.magic_guild.magic_research_wizard import MagicResearchWizard
        
        wizard = Mock()
        
        with patch('pygame_gui.windows.UIMessageWindow') as mock_window:
            MagicResearchWizard._show_validation_error(wizard, "エラーメッセージ")
            
            mock_window.assert_called_once()
    
    def test_refresh(self):
        """ウィザードのリフレッシュ"""
        from src.facilities.ui.magic_guild.magic_research_wizard import MagicResearchWizard
        
        wizard = Mock()
        wizard.current_step = ResearchStep.SELECT_TYPE
        
        with patch.object(MagicResearchWizard, '_show_current_step') as mock_show:
            MagicResearchWizard.refresh(wizard)
            
            # 初期ステップに戻る
            assert wizard.current_step == ResearchStep.SELECT_RESEARCHER
            
            # データがクリアされる
            assert wizard.research_data == {}
            
            # 現在ステップが表示される
            mock_show.assert_called_once()
    
    def test_show_hide_destroy(self):
        """表示・非表示・破棄の処理"""
        from src.facilities.ui.magic_guild.magic_research_wizard import MagicResearchWizard
        
        wizard = Mock()
        wizard.container = Mock()
        
        # 表示
        MagicResearchWizard.show(wizard)
        wizard.container.show.assert_called_once()
        
        # 非表示
        MagicResearchWizard.hide(wizard)
        wizard.container.hide.assert_called_once()
        
        # 破棄
        MagicResearchWizard.destroy(wizard)
        wizard.container.kill.assert_called_once()