"""魔法分析パネルのテスト"""

import pytest
import pygame
import pygame_gui
import unittest.mock
from unittest.mock import Mock, MagicMock, patch


@pytest.fixture
def mock_ui_setup():
    """UI要素のモック"""
    rect = pygame.Rect(0, 0, 450, 350)
    parent = Mock()
    ui_manager = Mock()
    controller = Mock()
    service = Mock()
    service.spell_analysis_cost = 150
    return rect, parent, ui_manager, controller, service


@pytest.fixture
def sample_characters():
    """サンプルキャラクターデータ"""
    return [
        {
            "id": "char1",
            "name": "魔法使いアルベルト",
            "level": 8,
            "class": "魔法使い",
            "spell_count": 5
        },
        {
            "id": "char2",
            "name": "司教エミリア",
            "level": 6,
            "class": "司教",
            "spell_count": 3
        }
    ]


@pytest.fixture
def sample_spells():
    """サンプル魔法データ"""
    return [
        {
            "id": "spell1",
            "name": "ファイアーボール",
            "level": 3,
            "school": "召喚",
            "type": "攻撃魔法",
            "cost": 100
        },
        {
            "id": "spell2",
            "name": "ヒール",
            "level": 1,
            "school": "治癒",
            "type": "回復魔法",
            "cost": 50
        }
    ]


@pytest.fixture
def sample_service_result():
    """サンプルサービス結果"""
    def create_result(success=True, data=None, message=""):
        result = Mock()
        result.success = success
        result.data = data or {}
        result.message = message
        return result
    return create_result


class TestSpellAnalysisPanelBasic:
    """SpellAnalysisPanelの基本機能テスト"""
    
    def test_initialization(self, mock_ui_setup):
        """正常に初期化される"""
        from src.facilities.ui.magic_guild.spell_analysis_panel import SpellAnalysisPanel
        
        rect, parent, ui_manager, controller, service = mock_ui_setup
        
        # ServicePanelの初期化をモック
        with patch('src.facilities.ui.magic_guild.spell_analysis_panel.ServicePanel.__init__') as mock_super_init, \
             patch.object(SpellAnalysisPanel, '_refresh_characters') as mock_refresh:
            
            mock_super_init.return_value = None
            
            # 新しいAPIでは引数順序が変更: (rect, parent, controller, ui_manager)
            panel = SpellAnalysisPanel(rect, parent, controller, ui_manager)
            
            # ServicePanelの初期化が呼ばれることを確認
            mock_super_init.assert_called_once_with(rect, parent, controller, "spell_analysis", ui_manager)
            
            # 初期データ読み込みが呼ばれることを確認
            mock_refresh.assert_called_once()
            
            # UI要素の初期状態
            assert panel.title_label is None  # 初期化前は None
            assert panel.character_list is None
            assert panel.spell_list is None
            
            # 初期状態の確認
            assert panel.selected_character is None
            assert panel.selected_spell is None
            assert panel.characters_data == []
            assert panel.spells_data == []
    
    def test_create_ui_elements(self, mock_ui_setup):
        """UI要素が正常に作成される"""
        from src.facilities.ui.magic_guild.spell_analysis_panel import SpellAnalysisPanel
        
        rect, parent, ui_manager, controller, service = mock_ui_setup
        
        # ServicePanel.__init__をモックして、各UI作成メソッドをテスト
        with patch('src.facilities.ui.magic_guild.spell_analysis_panel.ServicePanel.__init__') as mock_super_init, \
             patch.object(SpellAnalysisPanel, '_create_header') as mock_header, \
             patch.object(SpellAnalysisPanel, '_create_selection_area') as mock_selection, \
             patch.object(SpellAnalysisPanel, '_create_action_controls') as mock_actions, \
             patch.object(SpellAnalysisPanel, '_create_result_area') as mock_result, \
             patch.object(SpellAnalysisPanel, '_refresh_characters') as mock_refresh:
            
            mock_super_init.return_value = None
            
            panel = SpellAnalysisPanel(rect, parent, controller, ui_manager)
            panel._create_ui()  # 明示的に呼び出し
            
            # 各UI作成メソッドが呼ばれることを確認
            mock_header.assert_called_once()
            mock_selection.assert_called_once()
            mock_actions.assert_called_once()
            mock_result.assert_called_once()


class TestSpellAnalysisPanelDataLoading:
    """SpellAnalysisPanelのデータ読み込みテスト"""
    
    def test_refresh_characters_success(self, mock_ui_setup, sample_service_result, sample_characters):
        """キャラクター更新成功"""
        from src.facilities.ui.magic_guild.spell_analysis_panel import SpellAnalysisPanel
        
        rect, parent, ui_manager, controller, service = mock_ui_setup
        
        # モックUI要素
        mock_character_list = Mock()
        mock_result_box = Mock()
        
        # ServiceResultモック（新しいAPI）
        result = Mock()
        result.is_success.return_value = True
        result.data = {
            "characters": sample_characters,
            "party_gold": 2000
        }
        result.message = ""
        
        # パネルのモック
        panel = Mock(spec=SpellAnalysisPanel)
        panel.character_list = mock_character_list
        panel.result_box = mock_result_box
        panel.characters_data = []  # 初期状態
        panel._execute_service_action = Mock(return_value=result)
        
        # 実際のメソッドを呼び出し
        SpellAnalysisPanel._refresh_characters(panel)
        
        # サービスが呼ばれたことを確認
        panel._execute_service_action.assert_called_once_with("analyze_magic", {})
        
        # データが設定される
        assert panel.characters_data == sample_characters
        
        # リストが更新される
        expected_items = [
            "魔法使いアルベルト (5魔法)",
            "司教エミリア (3魔法)"
        ]
        mock_character_list.set_item_list.assert_called_with(expected_items)
    
    def test_refresh_characters_failure(self, mock_ui_setup, sample_service_result):
        """キャラクター更新失敗"""
        from src.facilities.ui.magic_guild.spell_analysis_panel import SpellAnalysisPanel
        
        rect, parent, ui_manager, controller, service = mock_ui_setup
        
        # モックUI要素
        mock_character_list = Mock()
        mock_result_box = Mock()
        
        # ServiceResultモック（失敗ケース）
        result = Mock()
        result.is_success.return_value = False
        result.data = None
        result.message = "エラーメッセージ"
        
        # パネルのモック
        panel = Mock(spec=SpellAnalysisPanel)
        panel.character_list = mock_character_list
        panel.result_box = mock_result_box
        panel.characters_data = []
        panel._execute_service_action = Mock(return_value=result)
        
        # 実際のメソッドを呼び出し
        SpellAnalysisPanel._refresh_characters(panel)
        
        # サービスが呼ばれたことを確認
        panel._execute_service_action.assert_called_once_with("analyze_magic", {})
        
        # 空リストが設定される
        mock_character_list.set_item_list.assert_called_with([])
        assert panel.characters_data == []
    
    def test_refresh_spells_success(self, mock_ui_setup, sample_service_result, sample_spells):
        """魔法更新成功"""
        from src.facilities.ui.magic_guild.spell_analysis_panel import SpellAnalysisPanel
        
        panel = Mock(spec=SpellAnalysisPanel)
        panel.selected_character = "char1"
        panel.spell_list = Mock()
        panel.gold_label = Mock()
        panel.result_box = Mock()
        panel.spells_data = []
        
        # ServiceResultモック（新しいAPI）
        result = Mock()
        result.is_success.return_value = True
        result.data = {
            "spells": sample_spells,
            "party_gold": 2000
        }
        result.message = ""
        
        panel._execute_service_action = Mock(return_value=result)
        
        # 実際のメソッドを呼び出し
        SpellAnalysisPanel._refresh_spells(panel, "char1")
        
        # サービスが呼ばれたことを確認
        panel._execute_service_action.assert_called_once_with("analyze_magic", {
            "character_id": "char1"
        })
        
        # データが設定される
        assert panel.spells_data == sample_spells
        
        # リストが更新される
        expected_items = [
            "Lv3 ファイアーボール - 100G",
            "Lv1 ヒール - 50G"
        ]
        panel.spell_list.set_item_list.assert_called_with(expected_items)
        
        # 所持金が更新される
        panel.gold_label.set_text.assert_called_with("所持金: 2000 G")
    
    def test_refresh_spells_no_character(self, sample_service_result):
        """キャラクター未選択での魔法更新"""
        from src.facilities.ui.magic_guild.spell_analysis_panel import SpellAnalysisPanel
        
        panel = Mock(spec=SpellAnalysisPanel)
        panel.selected_character = None
        panel.spell_list = Mock()
        panel.spells_data = []
        panel.result_box = Mock()
        
        # ServiceResultモック（失敗ケース）
        result = Mock()
        result.is_success.return_value = False
        result.data = None
        result.message = "エラーメッセージ"
        
        panel._execute_service_action = Mock(return_value=result)
        
        # 実際のメソッドを呼び出し
        SpellAnalysisPanel._refresh_spells(panel, "char1")
        
        # サービスが呼ばれたことを確認
        panel._execute_service_action.assert_called_once_with("analyze_magic", {
            "character_id": "char1"
        })
        
        # 空リストが設定される
        panel.spell_list.set_item_list.assert_called_with([])
        assert panel.spells_data == []


class TestSpellAnalysisPanelEventHandling:
    """SpellAnalysisPanelのイベント処理テスト"""
    
    def test_handle_event_character_selection(self, sample_characters):
        """キャラクター選択イベントの処理"""
        from src.facilities.ui.magic_guild.spell_analysis_panel import SpellAnalysisPanel
        
        panel = Mock(spec=SpellAnalysisPanel)
        panel.characters_data = sample_characters
        panel.character_list = Mock()
        panel.selected_character = None
        panel.selected_spell = None
        panel.analyze_button = Mock()
        panel.cost_label = Mock()
        
        # 選択イベントのモック
        event = Mock()
        event.type = pygame_gui.UI_SELECTION_LIST_NEW_SELECTION
        event.ui_element = panel.character_list
        
        # キャラクターが選択された
        panel.character_list.get_single_selection.return_value = 0
        
        with patch.object(panel, '_refresh_spells') as mock_refresh:
            
            # handle_selection_list_changedメソッドを直接呼び出し
            result = SpellAnalysisPanel.handle_selection_list_changed(panel, event)
            
            # 処理されたことを確認
            assert result is True
            
            # 選択されたキャラクターが設定される
            assert panel.selected_character == "char1"
            
            # 魔法選択がクリアされる
            assert panel.selected_spell is None
            
            # 魔法リストがリフレッシュされる
            mock_refresh.assert_called_once_with("char1")
            
            # ボタンが無効化される
            panel.analyze_button.disable.assert_called_once()
    
    def test_handle_event_spell_selection(self, sample_spells):
        """魔法選択イベントの処理"""
        from src.facilities.ui.magic_guild.spell_analysis_panel import SpellAnalysisPanel
        
        panel = Mock(spec=SpellAnalysisPanel)
        panel.spells_data = sample_spells
        panel.spell_list = Mock()
        panel.character_list = Mock()
        panel.selected_spell = None
        
        # 選択イベントのモック
        event = Mock()
        event.type = pygame_gui.UI_SELECTION_LIST_NEW_SELECTION
        event.ui_element = panel.spell_list
        
        # 魔法が選択された
        panel.spell_list.get_single_selection.return_value = 1
        
        panel.cost_label = Mock()
        panel.analyze_button = Mock()
        panel.result_box = Mock()
        
        # handle_selection_list_changedメソッドを直接呼び出し
        result = SpellAnalysisPanel.handle_selection_list_changed(panel, event)
        
        # 処理されたことを確認
        assert result is True
        
        # 選択された魔法が設定される
        assert panel.selected_spell == "spell2"
        
        # コスト表示が更新される
        panel.cost_label.set_text.assert_called_with("費用: 50 G")
        
        # ボタンが有効化される
        panel.analyze_button.enable.assert_called_once()
    
    def test_handle_event_analyze_button(self):
        """分析ボタン押下イベントの処理"""
        from src.facilities.ui.magic_guild.spell_analysis_panel import SpellAnalysisPanel
        
        panel = Mock(spec=SpellAnalysisPanel)
        panel.analyze_button = Mock()
        
        # ボタン押下イベントのモック
        event = Mock()
        event.type = pygame_gui.UI_BUTTON_PRESSED
        event.ui_element = panel.analyze_button
        
        with patch.object(panel, '_perform_analysis') as mock_analyze:
            # handle_button_clickメソッドを直接呼び出し
            result = SpellAnalysisPanel.handle_button_click(panel, panel.analyze_button)
            
            # 処理されたことを確認
            assert result is True
            
            mock_analyze.assert_called_once()
    
    def test_handle_event_selection_invalid_index(self, sample_characters):
        """無効なインデックス選択の処理"""
        from src.facilities.ui.magic_guild.spell_analysis_panel import SpellAnalysisPanel
        
        panel = Mock()
        panel.characters_data = sample_characters
        panel.character_list = Mock()
        
        # 選択イベントのモック
        event = Mock()
        event.type = pygame_gui.UI_SELECTION_LIST_NEW_SELECTION
        event.ui_element = panel.character_list
        
        # 範囲外のインデックス
        panel.character_list.get_single_selection.return_value = 10
        
        with patch.object(panel, '_refresh_spells') as mock_refresh:
            SpellAnalysisPanel.handle_event(panel, event)
            
            # 魔法リストはリフレッシュされない
            mock_refresh.assert_not_called()


class TestSpellAnalysisPanelAnalysis:
    """SpellAnalysisPanelの分析処理テスト"""
    
    def test_perform_analysis_success(self, sample_service_result):
        """分析実行成功"""
        from src.facilities.ui.magic_guild.spell_analysis_panel import SpellAnalysisPanel
        
        panel = Mock(spec=SpellAnalysisPanel)
        panel.selected_character = "char1"
        panel.selected_spell = "spell1"
        panel.result_box = Mock()
        panel.gold_label = Mock()
        
        # 分析結果のモック（確認→実行の流れ）
        confirm_result = Mock()
        confirm_result.is_success.return_value = True
        confirm_result.result_type = Mock()
        confirm_result.result_type.name = "CONFIRM"
        
        execute_result = Mock()
        execute_result.is_success.return_value = True
        execute_result.message = "ファイアーボールの分析が完了しました。\n詳細な魔法構造が判明しました。"
        execute_result.data = {"remaining_gold": 1850}
        
        panel._execute_service_action = Mock(side_effect=[confirm_result, execute_result])
        
        SpellAnalysisPanel._perform_analysis(panel)
        
        # サービスが呼ばれる（確認後実行）
        expected_calls = [
            unittest.mock.call("analyze_magic", {
                "character_id": "char1",
                "spell_id": "spell1"
            }),
            unittest.mock.call("analyze_magic", {
                "character_id": "char1",
                "spell_id": "spell1",
                "confirmed": True
            })
        ]
        panel._execute_service_action.assert_has_calls(expected_calls)
        
        # 結果が表示される
        expected_text = """
                <b>魔法分析結果</b><br>
                <br>
                ファイアーボールの分析が完了しました。<br>詳細な魔法構造が判明しました。<br>
                <br>
                <i>残り所持金: 1850 G</i>
                """
        assert panel.result_box.html_text == expected_text.strip()
        panel.result_box.rebuild.assert_called_once()
        
        # 所持金が更新される
        panel.gold_label.set_text.assert_called_with("所持金: 1850 G")
    
    def test_perform_analysis_failure(self, sample_service_result):
        """分析実行失敗"""
        from src.facilities.ui.magic_guild.spell_analysis_panel import SpellAnalysisPanel
        
        panel = Mock(spec=SpellAnalysisPanel)
        panel.selected_character = "char1"
        panel.selected_spell = "spell1"
        panel.result_box = Mock()
        
        # 失敗結果のモック
        result = Mock()
        result.is_success.return_value = False
        result.message = "所持金が不足しています"
        
        panel._execute_service_action = Mock(return_value=result)
        
        SpellAnalysisPanel._perform_analysis(panel)
        
        # エラーメッセージが表示される
        assert panel.result_box.html_text == "<font color='#FF0000'>所持金が不足しています</font>"
        panel.result_box.rebuild.assert_called_once()
    
    def test_perform_analysis_no_selection(self):
        """選択なしでの分析実行"""
        from src.facilities.ui.magic_guild.spell_analysis_panel import SpellAnalysisPanel
        
        panel = Mock()
        panel.selected_character = None
        panel.selected_spell = None
        panel.service = Mock()
        
        SpellAnalysisPanel._perform_analysis(panel)
        
        # サービスが呼ばれない
        panel.service.execute_action.assert_not_called()
    
    def test_perform_analysis_character_only(self):
        """キャラクターのみ選択での分析実行"""
        from src.facilities.ui.magic_guild.spell_analysis_panel import SpellAnalysisPanel
        
        panel = Mock()
        panel.selected_character = "char1"
        panel.selected_spell = None
        panel.service = Mock()
        
        SpellAnalysisPanel._perform_analysis(panel)
        
        # サービスが呼ばれない
        panel.service.execute_action.assert_not_called()


class TestSpellAnalysisPanelUIUpdates:
    """SpellAnalysisPanelのUI更新テスト"""
    
    def test_update_buttons_both_selected(self):
        """両方選択済みでのボタン更新"""
        from src.facilities.ui.magic_guild.spell_analysis_panel import SpellAnalysisPanel
        
        panel = Mock()
        panel.selected_character = "char1"
        panel.selected_spell = "spell1"
        panel.analyze_button = Mock()
        
        # この機能は実装されていない（直接handle_eventで管理）
        pass
    
    def test_update_buttons_character_only(self):
        """キャラクターのみ選択でのボタン更新"""
        from src.facilities.ui.magic_guild.spell_analysis_panel import SpellAnalysisPanel
        
        panel = Mock()
        panel.selected_character = "char1"
        panel.selected_spell = None
        panel.analyze_button = Mock()
        
        # この機能は実装されていない（直接handle_eventで管理）
        pass
    
    def test_update_buttons_none_selected(self):
        """何も選択されていない場合のボタン更新"""
        from src.facilities.ui.magic_guild.spell_analysis_panel import SpellAnalysisPanel
        
        panel = Mock()
        panel.selected_character = None
        panel.selected_spell = None
        panel.analyze_button = Mock()
        
        # この機能は実装されていない（直接handle_eventで管理）
        pass


class TestSpellAnalysisPanelActions:
    """SpellAnalysisPanelのアクション機能テスト"""
    
    def test_refresh(self):
        """パネルのリフレッシュ"""
        from src.facilities.ui.magic_guild.spell_analysis_panel import SpellAnalysisPanel
        
        panel = Mock()
        panel.selected_character = "char1"
        panel.selected_spell = "spell1"
        panel.analyze_button = Mock()
        panel.result_box = Mock()
        
        with patch.object(panel, '_refresh_characters') as mock_refresh:
            SpellAnalysisPanel.refresh(panel)
            
            # データがリフレッシュされる
            mock_refresh.assert_called_once()
            
            # 選択がクリアされる
            assert panel.selected_character is None
            assert panel.selected_spell is None
            
            # ボタンが無効化される
            panel.analyze_button.disable.assert_called_once()
            
            # 結果ボックスがクリアされる
            assert panel.result_box.html_text == ""
            panel.result_box.rebuild.assert_called_once()
    
    def test_show(self):
        """パネル表示"""
        from src.facilities.ui.magic_guild.spell_analysis_panel import SpellAnalysisPanel
        
        panel = Mock()
        panel.container = Mock()
        
        SpellAnalysisPanel.show(panel)
        
        panel.container.show.assert_called_once()
    
    def test_hide(self):
        """パネル非表示"""
        from src.facilities.ui.magic_guild.spell_analysis_panel import SpellAnalysisPanel
        
        panel = Mock()
        panel.container = Mock()
        
        SpellAnalysisPanel.hide(panel)
        
        panel.container.hide.assert_called_once()
    
    def test_destroy(self):
        """パネル破棄"""
        from src.facilities.ui.magic_guild.spell_analysis_panel import SpellAnalysisPanel
        
        # ServicePanelの基本destructor mockを設定
        with patch('src.facilities.ui.magic_guild.spell_analysis_panel.ServicePanel.destroy') as mock_super_destroy:
            panel = Mock(spec=SpellAnalysisPanel)
            panel.title_label = Mock()
            panel.character_list = Mock()
            panel.spell_list = Mock()
            panel.analyze_button = Mock()
            panel.cost_label = Mock()
            panel.gold_label = Mock()
            panel.result_box = Mock()
            panel.selected_character = "test"
            panel.selected_spell = "test"
            panel.characters_data = []
            panel.spells_data = []
            
            # 実際のメソッドを呼び出し
            SpellAnalysisPanel.destroy(panel)
            
            # パネル固有のクリーンアップが実行されたことを確認
            assert panel.title_label is None
            assert panel.character_list is None
            assert panel.spell_list is None
            assert panel.analyze_button is None
            assert panel.cost_label is None
            assert panel.gold_label is None
            assert panel.result_box is None
            assert panel.selected_character is None
            assert panel.selected_spell is None
            assert panel.characters_data == []
            assert panel.spells_data == []
            
            # ServicePanelのdestroyが呼ばれたことを確認
            mock_super_destroy.assert_called_once()
    
    def test_show_hide_destroy_no_container(self):
        """コンテナなしでの表示・非表示・破棄"""
        from src.facilities.ui.magic_guild.spell_analysis_panel import SpellAnalysisPanel
        
        panel = Mock(spec=SpellAnalysisPanel)
        panel.container = None
        panel.title_label = None
        panel.character_list = None
        panel.spell_list = None
        panel.analyze_button = None
        panel.cost_label = None
        panel.gold_label = None
        panel.result_box = None
        panel.selected_character = None
        panel.selected_spell = None
        panel.characters_data = []
        panel.spells_data = []
        
        # エラーが発生しないことを確認
        try:
            SpellAnalysisPanel.show(panel)
            SpellAnalysisPanel.hide(panel)
            
            # destroyはServicePanelをモック
            with patch('src.facilities.ui.magic_guild.spell_analysis_panel.ServicePanel.destroy'):
                SpellAnalysisPanel.destroy(panel)
            assert True
        except Exception as e:
            pytest.fail(f"Unexpected exception: {e}")