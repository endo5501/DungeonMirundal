"""魔法学習パネルのテスト"""

import pytest
import pygame
import pygame_gui
from unittest.mock import Mock, MagicMock, patch


@pytest.fixture
def mock_ui_setup():
    """UI要素のモック"""
    rect = pygame.Rect(0, 0, 450, 400)
    parent = Mock()
    ui_manager = Mock()
    controller = Mock()
    service = Mock()
    return rect, parent, ui_manager, controller, service


@pytest.fixture
def sample_characters():
    """サンプルキャラクターデータ"""
    return [
        {
            "id": "char1",
            "name": "見習い魔法使いアリス",
            "level": 3,
            "class": "魔法使い",
            "intelligence": 16,
            "spell_slots": 4
        },
        {
            "id": "char2",
            "name": "司教ボリス",
            "level": 5,
            "class": "司教",
            "faith": 15,
            "spell_slots": 3
        }
    ]


@pytest.fixture
def sample_learnable_spells():
    """サンプル学習可能魔法データ"""
    return [
        {
            "id": "spell1",
            "name": "マジックミサイル",
            "level": 1,
            "school": "召喚",
            "cost": 500,
            "requirements": {"intelligence": 12, "level": 1}
        },
        {
            "id": "spell2",
            "name": "ライトニングボルト",
            "level": 3,
            "school": "召喚",
            "cost": 2000,
            "requirements": {"intelligence": 15, "level": 5}
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


class TestSpellLearningPanelBasic:
    """SpellLearningPanelの基本機能テスト"""
    
    def test_initialization(self, mock_ui_setup):
        """正常に初期化される"""
        from src.facilities.ui.magic_guild.spell_learning_panel import SpellLearningPanel
        
        rect, parent, ui_manager, controller, service = mock_ui_setup
        
        with patch('pygame_gui.elements.UIPanel'), \
             patch('pygame_gui.elements.UILabel'), \
             patch('pygame_gui.elements.UISelectionList'), \
             patch('pygame_gui.elements.UIButton'), \
             patch('pygame_gui.elements.UITextBox'), \
             patch.object(SpellLearningPanel, '_refresh_characters'):
            
            panel = SpellLearningPanel(rect, parent, ui_manager, controller, service)
            
            # 基本属性の確認
            assert panel.rect == rect
            assert panel.parent == parent
            assert panel.ui_manager == ui_manager
            assert panel.controller == controller
            assert panel.service == service
            
            # 初期状態の確認
            assert panel.selected_character is None
            assert panel.selected_spell is None
            assert panel.characters_data == []
            assert panel.spells_data == []
    
    def test_create_ui_elements(self, mock_ui_setup):
        """UI要素が正常に作成される"""
        from src.facilities.ui.magic_guild.spell_learning_panel import SpellLearningPanel
        
        rect, parent, ui_manager, controller, service = mock_ui_setup
        
        with patch('pygame_gui.elements.UIPanel') as mock_panel, \
             patch('pygame_gui.elements.UILabel') as mock_label, \
             patch('pygame_gui.elements.UISelectionList') as mock_list, \
             patch('pygame_gui.elements.UIButton') as mock_button, \
             patch('pygame_gui.elements.UITextBox') as mock_text_box, \
             patch.object(SpellLearningPanel, '_refresh_characters'):
            
            mock_button_instance = Mock()
            mock_button.return_value = mock_button_instance
            
            panel = SpellLearningPanel(rect, parent, ui_manager, controller, service)
            
            # UI要素が作成される
            mock_panel.assert_called_once()
            assert mock_label.call_count == 5  # タイトル、学習者、魔法、コスト、所持金、結果
            assert mock_list.call_count == 2   # キャラクターリスト、魔法リスト
            mock_button.assert_called_once()
            mock_text_box.assert_called_once()
            
            # 学習ボタンが初期無効化される
            mock_button_instance.disable.assert_called_once()


class TestSpellLearningPanelDataLoading:
    """SpellLearningPanelのデータ読み込みテスト"""
    
    def test_refresh_characters_success(self, mock_ui_setup, sample_service_result, sample_characters):
        """キャラクター更新成功"""
        from src.facilities.ui.magic_guild.spell_learning_panel import SpellLearningPanel
        
        panel = Mock()
        panel.service = Mock()
        panel.character_list = Mock()
        panel.gold_label = Mock()
        
        # サービス結果のモック
        result = sample_service_result(
            success=True,
            data={
                "characters": sample_characters,
                "party_gold": 5000
            }
        )
        panel.service.execute_action.return_value = result
        
        SpellLearningPanel._refresh_characters(panel)
        
        # データが設定される
        assert panel.characters_data == sample_characters
        
        # リストが更新される
        expected_items = [
            "見習い魔法使いアリス (Lv.3 魔法使い)",
            "司教ボリス (Lv.5 司教)"
        ]
        panel.character_list.set_item_list.assert_called_with(expected_items)
        
        # 所持金が更新される
        panel.gold_label.set_text.assert_called_with("所持金: 5000 G")
    
    def test_refresh_characters_failure(self, mock_ui_setup, sample_service_result):
        """キャラクター更新失敗"""
        from src.facilities.ui.magic_guild.spell_learning_panel import SpellLearningPanel
        
        panel = Mock()
        panel.service = Mock()
        panel.character_list = Mock()
        panel.characters_data = []
        
        # 失敗結果
        result = sample_service_result(success=False)
        panel.service.execute_action.return_value = result
        
        SpellLearningPanel._refresh_characters(panel)
        
        # 空リストが設定される
        panel.character_list.set_item_list.assert_called_with([])
        assert panel.characters_data == []
    
    def test_refresh_learnable_spells_success(self, mock_ui_setup, sample_service_result, sample_learnable_spells):
        """学習可能魔法更新成功"""
        from src.facilities.ui.magic_guild.spell_learning_panel import SpellLearningPanel
        
        panel = Mock()
        panel.service = Mock()
        panel.selected_character = "char1"
        panel.spell_list = Mock()
        
        # サービス結果のモック
        result = sample_service_result(
            success=True,
            data={"spells": sample_learnable_spells}
        )
        panel.service.execute_action.return_value = result
        
        SpellLearningPanel._refresh_learnable_spells(panel)
        
        # データが設定される
        assert panel.spells_data == sample_learnable_spells
        
        # リストが更新される
        expected_items = [
            "マジックミサイル (Lv.1) 費用: 500G",
            "ライトニングボルト (Lv.3) 費用: 2000G"
        ]
        panel.spell_list.set_item_list.assert_called_with(expected_items)
    
    def test_refresh_learnable_spells_no_character(self):
        """キャラクター未選択での魔法更新"""
        from src.facilities.ui.magic_guild.spell_learning_panel import SpellLearningPanel
        
        panel = Mock()
        panel.selected_character = None
        panel.spell_list = Mock()
        
        SpellLearningPanel._refresh_learnable_spells(panel)
        
        # 空リストが設定される
        panel.spell_list.set_item_list.assert_called_with([])
        assert panel.spells_data == []


class TestSpellLearningPanelEventHandling:
    """SpellLearningPanelのイベント処理テスト"""
    
    def test_handle_event_character_selection(self, sample_characters):
        """キャラクター選択イベントの処理"""
        from src.facilities.ui.magic_guild.spell_learning_panel import SpellLearningPanel
        
        panel = Mock()
        panel.characters_data = sample_characters
        panel.character_list = Mock()
        panel.selected_character = None
        panel.selected_spell = None
        
        # 選択イベントのモック
        event = Mock()
        event.type = pygame_gui.UI_SELECTION_LIST_NEW_SELECTION
        event.ui_element = panel.character_list
        
        # キャラクターが選択された
        panel.character_list.get_single_selection.return_value = 0
        
        with patch.object(SpellLearningPanel, '_refresh_learnable_spells') as mock_refresh, \
             patch.object(SpellLearningPanel, '_update_buttons') as mock_update, \
             patch.object(SpellLearningPanel, '_clear_description') as mock_clear:
            
            SpellLearningPanel.handle_event(panel, event)
            
            # 選択されたキャラクターが設定される
            assert panel.selected_character == "char1"
            
            # 魔法選択がクリアされる
            assert panel.selected_spell is None
            
            # 学習可能魔法リストがリフレッシュされる
            mock_refresh.assert_called_once()
            
            # ボタンが更新される
            mock_update.assert_called_once()
            
            # 説明がクリアされる
            mock_clear.assert_called_once()
    
    def test_handle_event_spell_selection(self, sample_learnable_spells):
        """魔法選択イベントの処理"""
        from src.facilities.ui.magic_guild.spell_learning_panel import SpellLearningPanel
        
        panel = Mock()
        panel.spells_data = sample_learnable_spells
        panel.spell_list = Mock()
        panel.character_list = Mock()
        panel.selected_spell = None
        
        # 選択イベントのモック
        event = Mock()
        event.type = pygame_gui.UI_SELECTION_LIST_NEW_SELECTION
        event.ui_element = panel.spell_list
        
        # 魔法が選択された
        panel.spell_list.get_single_selection.return_value = 1
        
        with patch.object(SpellLearningPanel, '_update_buttons') as mock_update, \
             patch.object(SpellLearningPanel, '_update_spell_description') as mock_description:
            
            SpellLearningPanel.handle_event(panel, event)
            
            # 選択された魔法が設定される
            assert panel.selected_spell == "spell2"
            
            # ボタンが更新される
            mock_update.assert_called_once()
            
            # 説明が更新される
            mock_description.assert_called_once()
    
    def test_handle_event_learn_button(self):
        """学習ボタン押下イベントの処理"""
        from src.facilities.ui.magic_guild.spell_learning_panel import SpellLearningPanel
        
        panel = Mock()
        panel.learn_button = Mock()
        
        # ボタン押下イベントのモック
        event = Mock()
        event.type = pygame_gui.UI_BUTTON_PRESSED
        event.ui_element = panel.learn_button
        
        with patch.object(SpellLearningPanel, '_perform_learning') as mock_learn:
            SpellLearningPanel.handle_event(panel, event)
            
            mock_learn.assert_called_once()
    
    def test_handle_event_selection_invalid_index(self, sample_characters):
        """無効なインデックス選択の処理"""
        from src.facilities.ui.magic_guild.spell_learning_panel import SpellLearningPanel
        
        panel = Mock()
        panel.characters_data = sample_characters
        panel.character_list = Mock()
        
        # 選択イベントのモック
        event = Mock()
        event.type = pygame_gui.UI_SELECTION_LIST_NEW_SELECTION
        event.ui_element = panel.character_list
        
        # 範囲外のインデックス
        panel.character_list.get_single_selection.return_value = 10
        
        with patch.object(SpellLearningPanel, '_refresh_learnable_spells') as mock_refresh:
            SpellLearningPanel.handle_event(panel, event)
            
            # 学習可能魔法リストはリフレッシュされない
            mock_refresh.assert_not_called()


class TestSpellLearningPanelLearning:
    """SpellLearningPanelの学習処理テスト"""
    
    def test_perform_learning_success(self, sample_service_result):
        """学習実行成功"""
        from src.facilities.ui.magic_guild.spell_learning_panel import SpellLearningPanel
        
        panel = Mock()
        panel.selected_character = "char1"
        panel.selected_spell = "spell1"
        panel.service = Mock()
        panel.result_label = Mock()
        
        # 学習結果のモック
        result = sample_service_result(
            success=True,
            message="マジックミサイルの学習が完了しました！",
            data={"remaining_gold": 4500}
        )
        panel.service.execute_action.return_value = result
        
        with patch.object(SpellLearningPanel, '_refresh_characters') as mock_refresh, \
             patch.object(SpellLearningPanel, '_clear_selections') as mock_clear:
            
            SpellLearningPanel._perform_learning(panel)
            
            # サービスが呼ばれる
            panel.service.execute_action.assert_called_with("spell_learning", {
                "character_id": "char1",
                "spell_id": "spell1"
            })
            
            # 成功メッセージが表示される
            panel.result_label.set_text.assert_called_with("マジックミサイルの学習が完了しました！ (残り金: 4500G)")
            
            # データがリフレッシュされる
            mock_refresh.assert_called_once()
            
            # 選択がクリアされる
            mock_clear.assert_called_once()
    
    def test_perform_learning_failure(self, sample_service_result):
        """学習実行失敗"""
        from src.facilities.ui.magic_guild.spell_learning_panel import SpellLearningPanel
        
        panel = Mock()
        panel.selected_character = "char1"
        panel.selected_spell = "spell1"
        panel.service = Mock()
        panel.result_label = Mock()
        
        # 失敗結果のモック
        result = sample_service_result(
            success=False,
            message="知力が不足しています"
        )
        panel.service.execute_action.return_value = result
        
        SpellLearningPanel._perform_learning(panel)
        
        # エラーメッセージが表示される
        panel.result_label.set_text.assert_called_with("エラー: 知力が不足しています")
    
    def test_perform_learning_no_selection(self):
        """選択なしでの学習実行"""
        from src.facilities.ui.magic_guild.spell_learning_panel import SpellLearningPanel
        
        panel = Mock()
        panel.selected_character = None
        panel.selected_spell = None
        panel.service = Mock()
        
        SpellLearningPanel._perform_learning(panel)
        
        # サービスが呼ばれない
        panel.service.execute_action.assert_not_called()
    
    def test_perform_learning_spell_only(self):
        """魔法のみ選択での学習実行"""
        from src.facilities.ui.magic_guild.spell_learning_panel import SpellLearningPanel
        
        panel = Mock()
        panel.selected_character = None
        panel.selected_spell = "spell1"
        panel.service = Mock()
        
        SpellLearningPanel._perform_learning(panel)
        
        # サービスが呼ばれない
        panel.service.execute_action.assert_not_called()


class TestSpellLearningPanelUIUpdates:
    """SpellLearningPanelのUI更新テスト"""
    
    def test_update_buttons_both_selected(self):
        """両方選択済みでのボタン更新"""
        from src.facilities.ui.magic_guild.spell_learning_panel import SpellLearningPanel
        
        panel = Mock()
        panel.selected_character = "char1"
        panel.selected_spell = "spell1"
        panel.learn_button = Mock()
        
        SpellLearningPanel._update_buttons(panel)
        
        # 学習ボタンが有効化される
        panel.learn_button.enable.assert_called_once()
    
    def test_update_buttons_character_only(self):
        """キャラクターのみ選択でのボタン更新"""
        from src.facilities.ui.magic_guild.spell_learning_panel import SpellLearningPanel
        
        panel = Mock()
        panel.selected_character = "char1"
        panel.selected_spell = None
        panel.learn_button = Mock()
        
        SpellLearningPanel._update_buttons(panel)
        
        # 学習ボタンが無効化される
        panel.learn_button.disable.assert_called_once()
    
    def test_update_buttons_none_selected(self):
        """何も選択されていない場合のボタン更新"""
        from src.facilities.ui.magic_guild.spell_learning_panel import SpellLearningPanel
        
        panel = Mock()
        panel.selected_character = None
        panel.selected_spell = None
        panel.learn_button = Mock()
        
        SpellLearningPanel._update_buttons(panel)
        
        # 学習ボタンが無効化される
        panel.learn_button.disable.assert_called_once()
    
    def test_update_spell_description(self, sample_learnable_spells):
        """魔法説明の更新"""
        from src.facilities.ui.magic_guild.spell_learning_panel import SpellLearningPanel
        
        panel = Mock()
        panel.spells_data = sample_learnable_spells
        panel.selected_spell = "spell1"
        panel.description_box = Mock()
        
        SpellLearningPanel._update_spell_description(panel)
        
        # 説明が更新される
        expected_html = ("<b>マジックミサイル</b><br>"
                        "レベル: 1<br>"
                        "系統: 召喚<br>"
                        "費用: 500G<br>"
                        "<br>"
                        "必要条件:<br>"
                        "- 知力: 12以上<br>"
                        "- レベル: 1以上")
        assert panel.description_box.html_text == expected_html
        panel.description_box.rebuild.assert_called_once()
    
    def test_update_spell_description_no_spell(self):
        """魔法未選択での説明更新"""
        from src.facilities.ui.magic_guild.spell_learning_panel import SpellLearningPanel
        
        panel = Mock()
        panel.selected_spell = None
        panel.description_box = Mock()
        
        SpellLearningPanel._update_spell_description(panel)
        
        # 空の説明が設定される
        assert panel.description_box.html_text == ""
        panel.description_box.rebuild.assert_called_once()
    
    def test_clear_description(self):
        """説明のクリア"""
        from src.facilities.ui.magic_guild.spell_learning_panel import SpellLearningPanel
        
        panel = Mock()
        panel.description_box = Mock()
        
        SpellLearningPanel._clear_description(panel)
        
        # 説明がクリアされる
        assert panel.description_box.html_text == ""
        panel.description_box.rebuild.assert_called_once()
    
    def test_clear_selections(self):
        """選択のクリア"""
        from src.facilities.ui.magic_guild.spell_learning_panel import SpellLearningPanel
        
        panel = Mock()
        panel.selected_character = "char1"
        panel.selected_spell = "spell1"
        panel.character_list = Mock()
        panel.spell_list = Mock()
        
        with patch.object(SpellLearningPanel, '_update_buttons') as mock_update, \
             patch.object(SpellLearningPanel, '_clear_description') as mock_clear:
            
            SpellLearningPanel._clear_selections(panel)
            
            # 選択がクリアされる
            assert panel.selected_character is None
            assert panel.selected_spell is None
            
            # リストの選択がクリアされる
            panel.character_list.set_selected_index.assert_called_with(None)
            panel.spell_list.set_selected_index.assert_called_with(None)
            
            # ボタンが更新される
            mock_update.assert_called_once()
            
            # 説明がクリアされる
            mock_clear.assert_called_once()


class TestSpellLearningPanelActions:
    """SpellLearningPanelのアクション機能テスト"""
    
    def test_refresh(self):
        """パネルのリフレッシュ"""
        from src.facilities.ui.magic_guild.spell_learning_panel import SpellLearningPanel
        
        panel = Mock()
        panel.result_label = Mock()
        
        with patch.object(SpellLearningPanel, '_refresh_characters') as mock_refresh, \
             patch.object(SpellLearningPanel, '_clear_selections') as mock_clear:
            
            SpellLearningPanel.refresh(panel)
            
            # データがリフレッシュされる
            mock_refresh.assert_called_once()
            
            # 選択がクリアされる
            mock_clear.assert_called_once()
            
            # 結果ラベルがクリアされる
            panel.result_label.set_text.assert_called_with("")
    
    def test_show(self):
        """パネル表示"""
        from src.facilities.ui.magic_guild.spell_learning_panel import SpellLearningPanel
        
        panel = Mock()
        panel.container = Mock()
        
        SpellLearningPanel.show(panel)
        
        panel.container.show.assert_called_once()
    
    def test_hide(self):
        """パネル非表示"""
        from src.facilities.ui.magic_guild.spell_learning_panel import SpellLearningPanel
        
        panel = Mock()
        panel.container = Mock()
        
        SpellLearningPanel.hide(panel)
        
        panel.container.hide.assert_called_once()
    
    def test_destroy(self):
        """パネル破棄"""
        from src.facilities.ui.magic_guild.spell_learning_panel import SpellLearningPanel
        
        panel = Mock()
        panel.container = Mock()
        
        SpellLearningPanel.destroy(panel)
        
        panel.container.kill.assert_called_once()
    
    def test_show_hide_destroy_no_container(self):
        """コンテナなしでの表示・非表示・破棄"""
        from src.facilities.ui.magic_guild.spell_learning_panel import SpellLearningPanel
        
        panel = Mock()
        panel.container = None
        
        # エラーが発生しないことを確認
        try:
            SpellLearningPanel.show(panel)
            SpellLearningPanel.hide(panel)
            SpellLearningPanel.destroy(panel)
            assert True
        except Exception as e:
            pytest.fail(f"Unexpected exception: {e}")