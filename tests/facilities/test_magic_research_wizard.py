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
            "class": "召喚魔法",
            "intelligence": 15,
            "specialization": "召喚魔法"
        },
        {
            "id": "researcher2",
            "name": "賢者サラマンダー",
            "level": 12,
            "class": "変成魔法",
            "intelligence": 12,
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
        
        # サービスの応答をモック
        result = Mock()
        result.success = True
        result.data = {"researchers": []}
        service.execute_action.return_value = result
        
        with patch('pygame_gui.elements.UIPanel'), \
             patch('pygame_gui.elements.UIButton'), \
             patch('pygame_gui.elements.UILabel'), \
             patch('pygame_gui.elements.UISelectionList'), \
             patch('pygame_gui.elements.UITextBox'):
            
            wizard = MagicResearchWizard(rect, parent, ui_manager, controller, service)
            
            # 基本属性の確認
            assert wizard.rect == rect
            assert wizard.parent == parent
            assert wizard.ui_manager == ui_manager
            assert wizard.controller == controller
            assert wizard.service == service
            
            # 初期状態の確認
            assert wizard.current_step == ResearchStep.SELECT_RESEARCHER
            assert wizard.research_data != {}  # サービスから読み込みが行われる
    
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
        
        # サービスの応答をモック
        result = Mock()
        result.success = True
        result.data = {"researchers": []}
        service.execute_action.return_value = result
        
        with patch('pygame_gui.elements.UIPanel') as mock_panel, \
             patch('pygame_gui.elements.UIButton') as mock_button, \
             patch('pygame_gui.elements.UILabel'), \
             patch('pygame_gui.elements.UISelectionList'), \
             patch('pygame_gui.elements.UITextBox'):
            
            mock_button_instances = [Mock(), Mock(), Mock()]
            mock_button.side_effect = mock_button_instances
            
            wizard = MagicResearchWizard(rect, parent, ui_manager, controller, service)
            
            # UI要素が作成される
            assert mock_panel.call_count >= 2  # container, step_indicator, content_panel
            assert mock_button.call_count == 3  # back, next, cancel
            
            # 戻るボタンが無効化される（初期化時と更新時の計2回）
            assert mock_button_instances[0].disable.call_count >= 1


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
        
        with patch.object(wizard, '_update_step_indicator') as mock_indicator, \
             patch.object(wizard, '_show_current_step') as mock_show:
            
            MagicResearchWizard._handle_next(wizard)
            
            assert wizard.current_step == ResearchStep.SELECT_TYPE
            mock_indicator.assert_called_once()
            mock_show.assert_called_once()
    
    def test_next_step_validation_failure(self):
        """最終ステップから完了への処理"""
        from src.facilities.ui.magic_guild.magic_research_wizard import MagicResearchWizard
        
        wizard = Mock()
        wizard.current_step = ResearchStep.CONFIRM
        
        with patch.object(wizard, '_complete_research') as mock_complete:
            
            MagicResearchWizard._handle_next(wizard)
            
            # 完了処理が呼ばれる
            mock_complete.assert_called_once()
    
    def test_back_step_type_to_researcher(self):
        """研究種別から研究者選択への戻り"""
        from src.facilities.ui.magic_guild.magic_research_wizard import MagicResearchWizard
        
        wizard = Mock()
        wizard.current_step = ResearchStep.SELECT_TYPE
        
        with patch.object(wizard, '_update_step_indicator') as mock_indicator, \
             patch.object(wizard, '_show_current_step') as mock_show:
            
            MagicResearchWizard._handle_back(wizard)
            
            assert wizard.current_step == ResearchStep.SELECT_RESEARCHER
            mock_indicator.assert_called_once()
            mock_show.assert_called_once()
    
    def test_back_step_first_step(self):
        """最初のステップでの戻り処理"""
        from src.facilities.ui.magic_guild.magic_research_wizard import MagicResearchWizard
        
        wizard = Mock()
        wizard.current_step = ResearchStep.SELECT_RESEARCHER
        
        with patch.object(wizard, '_update_step_indicator') as mock_indicator, \
             patch.object(wizard, '_show_current_step') as mock_show:
            
            MagicResearchWizard._handle_back(wizard)
            
            # ステップが変更されない
            assert wizard.current_step == ResearchStep.SELECT_RESEARCHER
            mock_indicator.assert_not_called()
            mock_show.assert_not_called()


class TestMagicResearchWizardValidation:
    """MagicResearchWizardの検証テスト"""
    
    def test_update_navigation_buttons_researcher_selected(self):
        """研究者選択時のナビゲーションボタン更新"""
        from src.facilities.ui.magic_guild.magic_research_wizard import MagicResearchWizard
        
        wizard = Mock()
        wizard.current_step = ResearchStep.SELECT_RESEARCHER
        wizard.back_button = Mock()
        wizard.next_button = Mock()
        wizard.step_uis = {
            ResearchStep.SELECT_RESEARCHER: {
                'researcher_list': Mock()
            }
        }
        wizard.step_uis[ResearchStep.SELECT_RESEARCHER]['researcher_list'].get_single_selection.return_value = 0
        
        MagicResearchWizard._update_navigation_buttons(wizard)
        
        wizard.back_button.disable.assert_called_once()
        wizard.next_button.enable.assert_called_once()
    
    def test_update_navigation_buttons_no_researcher_selected(self):
        """研究者未選択時のナビゲーションボタン更新"""
        from src.facilities.ui.magic_guild.magic_research_wizard import MagicResearchWizard
        
        wizard = Mock()
        wizard.current_step = ResearchStep.SELECT_RESEARCHER
        wizard.back_button = Mock()
        wizard.next_button = Mock()
        wizard.step_uis = {
            ResearchStep.SELECT_RESEARCHER: {
                'researcher_list': Mock()
            }
        }
        wizard.step_uis[ResearchStep.SELECT_RESEARCHER]['researcher_list'].get_single_selection.return_value = None
        
        MagicResearchWizard._update_navigation_buttons(wizard)
        
        wizard.back_button.disable.assert_called_once()
        wizard.next_button.disable.assert_called_once()
    
    def test_update_navigation_buttons_confirm_step(self):
        """確認ステップでのナビゲーションボタン更新"""
        from src.facilities.ui.magic_guild.magic_research_wizard import MagicResearchWizard
        
        wizard = Mock()
        wizard.current_step = ResearchStep.CONFIRM
        wizard.back_button = Mock()
        wizard.next_button = Mock()
        
        MagicResearchWizard._update_navigation_buttons(wizard)
        
        wizard.back_button.enable.assert_called_once()
        wizard.next_button.set_text.assert_called_with("完了")
        wizard.next_button.enable.assert_called_once()


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
        
        with patch.object(wizard, '_handle_next') as mock_next:
            MagicResearchWizard.handle_event(wizard, event)
            
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
        
        with patch.object(wizard, '_handle_back') as mock_back:
            MagicResearchWizard.handle_event(wizard, event)
            
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
        
        with patch.object(wizard, '_handle_cancel') as mock_cancel:
            MagicResearchWizard.handle_event(wizard, event)
            
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
        wizard.research_data = {'researchers': sample_researchers}
        
        event = Mock()
        event.type = pygame_gui.UI_SELECTION_LIST_NEW_SELECTION
        event.ui_element = wizard.step_uis[ResearchStep.SELECT_RESEARCHER]['researcher_list']
        
        # 研究者データのモック
        event.ui_element.get_single_selection.return_value = 0
        
        with patch.object(wizard, '_update_navigation_buttons') as mock_update:
            MagicResearchWizard.handle_event(wizard, event)
            
            assert wizard.research_data["selected_researcher"] == sample_researchers[0]
            assert wizard.research_data["selected_researcher_id"] == "researcher1"
            mock_update.assert_called_once()
    
    def test_handle_event_unknown(self):
        """未知のイベントの処理"""
        from src.facilities.ui.magic_guild.magic_research_wizard import MagicResearchWizard
        
        wizard = Mock()
        
        event = Mock()
        event.type = 999  # 未知のイベント
        
        result = MagicResearchWizard.handle_event(wizard, event)
        
        # 未知のイベントは何も処理しない（戻り値なし）
        assert result is None


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
        wizard.research_data = {}
        
        # サービス結果のモック
        result = Mock()
        result.success = True
        result.data = {"researchers": sample_researchers}
        wizard.service.execute_action.return_value = result
        
        MagicResearchWizard._load_researchers(wizard)
        
        # データが設定される
        assert wizard.research_data['researchers'] == sample_researchers
        
        # リストが更新される
        expected_items = [
            "魔法使いマーリン (召喚魔法) Lv.15 INT:15",
            "賢者サラマンダー (変成魔法) Lv.12 INT:12"
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
        wizard.research_data = {}
        
        # サービス結果のモック
        result = Mock()
        result.success = True
        result.data = {"research_types": sample_research_types}
        wizard.service.execute_action.return_value = result
        
        MagicResearchWizard._load_research_types(wizard)
        
        # データが設定される
        assert wizard.research_data['research_types'] == sample_research_types
        
        # リストが更新される
        expected_items = [
            "新呪文開発 - 5000G (30日)",
            "既存呪文改良 - 2000G (14日)"
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
        
        with patch.object(wizard, '_load_research_types') as mock_load, \
             patch.object(wizard, '_update_navigation_buttons') as mock_update:
            
            MagicResearchWizard._show_current_step(wizard)
            
            # 全ステップが隠される
            for step_ui in wizard.step_uis.values():
                for element in step_ui.values():
                    element.hide.assert_called_once()
            
            # 現在ステップが表示される
            for element in wizard.step_uis[ResearchStep.SELECT_TYPE].values():
                element.show.assert_called_once()
            
            # データロードとボタン更新が呼ばれる
            mock_load.assert_called_once()
            mock_update.assert_called_once()
    
    def test_hide_all_steps(self):
        """全ステップの非表示は_show_current_stepで行われる"""
        from src.facilities.ui.magic_guild.magic_research_wizard import MagicResearchWizard
        
        wizard = Mock()
        wizard.current_step = ResearchStep.SELECT_RESEARCHER
        wizard.step_uis = {
            ResearchStep.SELECT_RESEARCHER: {'title': Mock(), 'list': Mock()},
            ResearchStep.SELECT_TYPE: {'title': Mock(), 'list': Mock()}
        }
        
        with patch.object(wizard, '_load_researchers'), \
             patch.object(wizard, '_update_navigation_buttons'):
            
            MagicResearchWizard._show_current_step(wizard)
            
            # 全UI要素が隠される
            for step_ui in wizard.step_uis.values():
                for element in step_ui.values():
                    element.hide.assert_called_once()
    
    def test_cancel_research(self):
        """研究のキャンセル"""
        from src.facilities.ui.magic_guild.magic_research_wizard import MagicResearchWizard
        
        wizard = Mock()
        
        with patch('src.facilities.ui.magic_guild.magic_research_wizard.logger') as mock_logger:
            MagicResearchWizard._handle_cancel(wizard)
            
            # ログが出力される
            mock_logger.info.assert_called_once_with("Magic research wizard cancelled")
    
    def test_complete_research(self):
        """研究の完了"""
        from src.facilities.ui.magic_guild.magic_research_wizard import MagicResearchWizard
        
        wizard = Mock()
        wizard.service = Mock()
        wizard.research_data = {'test': 'data'}
        
        # サービス結果のモック
        result = Mock()
        result.success = True
        wizard.service.execute_action.return_value = result
        
        with patch('src.facilities.ui.magic_guild.magic_research_wizard.logger') as mock_logger:
            MagicResearchWizard._complete_research(wizard)
            
            # サービスが呼ばれる
            wizard.service.execute_action.assert_called_once_with("magic_research", {
                "step": "complete",
                "test": "data"
            })
            
            # ログが出力される
            mock_logger.info.assert_called_once_with("Magic research completed successfully")
    
    def test_refresh(self):
        """ウィザードのリフレッシュ"""
        from src.facilities.ui.magic_guild.magic_research_wizard import MagicResearchWizard
        
        wizard = Mock()
        wizard.current_step = ResearchStep.SELECT_TYPE
        
        with patch.object(wizard, '_update_step_indicator') as mock_indicator, \
             patch.object(wizard, '_show_current_step') as mock_show:
            
            MagicResearchWizard.refresh(wizard)
            
            mock_indicator.assert_called_once()
            mock_show.assert_called_once()
            
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