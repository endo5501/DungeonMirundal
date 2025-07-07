"""冒険準備パネルのテスト"""

import pytest
import pygame
import pygame_gui
from unittest.mock import Mock, MagicMock, patch


@pytest.fixture
def mock_controller():
    """FacilityControllerのモック"""
    controller = Mock()
    
    # サービスとパーティのモック
    mock_service = Mock()
    mock_party = Mock()
    mock_party.name = "テストパーティ"
    mock_party.gold = 1000
    
    # パーティメンバーのモック
    member1 = Mock()
    member1.is_alive.return_value = True
    member1.inventory = Mock()
    member1.inventory.get_all_items.return_value = ["item1", "item2"]
    
    member2 = Mock()
    member2.is_alive.return_value = False
    member2.inventory = Mock()
    member2.inventory.get_all_items.return_value = ["item3"]
    
    mock_party.members = [member1, member2]
    mock_service.party = mock_party
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
def mock_adventure_prep_panel(mock_controller, mock_ui_setup):
    """AdventurePrepPanelの基本モック"""
    rect, parent, ui_manager = mock_ui_setup
    
    # AdventurePrepPanelクラスを完全にモックする
    panel = Mock()
    panel.controller = mock_controller
    panel.service_id = "adventure_prep"
    panel.rect = rect
    panel.container = Mock()
    panel.ui_manager = ui_manager
    panel.ui_elements = []
    
    # 初期状態の属性
    panel.sub_service_buttons = {}
    panel.info_box = None
    panel.active_sub_panel = None
    panel.sub_panels = {}
    
    return panel


class TestAdventurePrepPanelPartyStatus:
    """AdventurePrepPanelのパーティステータス機能テスト"""
    
    def test_get_party_status_text_with_party(self, mock_controller):
        """パーティありの場合のステータステキスト"""
        # 実際のメソッドをテストするため、直接importしてテスト
        from src.facilities.ui.inn.adventure_prep_panel import AdventurePrepPanel
        
        # ServicePanelの初期化をモック
        with patch('src.facilities.ui.service_panel.ServicePanel.__init__', return_value=None):
            # 必要な属性を手動で設定
            panel = Mock()
            panel.controller = mock_controller
            
            # 実際のメソッドを呼び出し
            result = AdventurePrepPanel._get_party_status_text(panel)
            
            assert "パーティ情報" in result
            assert "テストパーティ" in result
            assert "1/2人" in result  # alive/total
            assert "3個" in result    # total items
            assert "1000 G" in result
    
    def test_get_party_status_text_no_party(self):
        """パーティなしの場合のステータステキスト"""
        from src.facilities.ui.inn.adventure_prep_panel import AdventurePrepPanel
        
        # パーティなしのコントローラー
        controller = Mock()
        controller.service.party = None
        
        panel = Mock()
        panel.controller = controller
        
        result = AdventurePrepPanel._get_party_status_text(panel)
        
        assert "パーティが編成されていません" in result
    
    def test_get_party_status_text_no_controller(self):
        """コントローラーなしの場合のステータステキスト"""
        from src.facilities.ui.inn.adventure_prep_panel import AdventurePrepPanel
        
        panel = Mock()
        panel.controller = None
        
        result = AdventurePrepPanel._get_party_status_text(panel)
        
        assert "パーティが編成されていません" in result
    
    def test_get_party_status_text_members_without_inventory(self):
        """インベントリなしのメンバーがいる場合"""
        from src.facilities.ui.inn.adventure_prep_panel import AdventurePrepPanel
        
        controller = Mock()
        mock_service = Mock()
        mock_party = Mock()
        mock_party.name = "テストパーティ"
        mock_party.gold = 500
        
        # インベントリなしのメンバー
        member = Mock()
        member.is_alive.return_value = True
        # inventoryアトリビュートなし
        
        mock_party.members = [member]
        mock_service.party = mock_party
        controller.service = mock_service
        
        panel = Mock()
        panel.controller = controller
        
        result = AdventurePrepPanel._get_party_status_text(panel)
        
        assert "0個" in result  # アイテムなし


class TestAdventurePrepPanelButtonHandling:
    """AdventurePrepPanelのボタン処理テスト"""
    
    def test_handle_button_click_sub_service(self, mock_adventure_prep_panel):
        """サブサービスボタンクリックの処理"""
        from src.facilities.ui.inn.adventure_prep_panel import AdventurePrepPanel
        
        # サブサービスボタンのモック
        item_button = Mock()
        mock_adventure_prep_panel.sub_service_buttons = {"item_management": item_button}
        
        # _open_sub_serviceメソッドをモック
        with patch.object(AdventurePrepPanel, '_open_sub_service') as mock_open:
            result = AdventurePrepPanel.handle_button_click(mock_adventure_prep_panel, item_button)
            
            assert result is True
            mock_open.assert_called_with(mock_adventure_prep_panel, "item_management")
    
    def test_handle_button_click_unknown_button(self, mock_adventure_prep_panel):
        """未知のボタンクリックの処理"""
        from src.facilities.ui.inn.adventure_prep_panel import AdventurePrepPanel
        
        unknown_button = Mock()
        
        result = AdventurePrepPanel.handle_button_click(mock_adventure_prep_panel, unknown_button)
        
        assert result is False


class TestAdventurePrepPanelSubServiceManagement:
    """AdventurePrepPanelのサブサービス管理テスト"""
    
    def test_create_sub_panel_item_management(self, mock_adventure_prep_panel):
        """アイテム管理パネルの作成"""
        from src.facilities.ui.inn.adventure_prep_panel import AdventurePrepPanel
        
        with patch('src.facilities.ui.inn.adventure_prep_panel.ItemManagementPanel') as mock_panel_class:
            mock_panel_instance = Mock()
            mock_panel_class.return_value = mock_panel_instance
            
            result = AdventurePrepPanel._create_sub_panel(mock_adventure_prep_panel, "item_management")
            
            assert result == mock_panel_instance
            mock_panel_class.assert_called_once()
    
    def test_create_sub_panel_spell_management(self, mock_adventure_prep_panel):
        """魔法管理パネルの作成"""
        from src.facilities.ui.inn.adventure_prep_panel import AdventurePrepPanel
        
        with patch('src.facilities.ui.inn.adventure_prep_panel.SpellManagementPanel') as mock_panel_class:
            mock_panel_instance = Mock()
            mock_panel_class.return_value = mock_panel_instance
            
            result = AdventurePrepPanel._create_sub_panel(mock_adventure_prep_panel, "spell_management")
            
            assert result == mock_panel_instance
            mock_panel_class.assert_called_once()
    
    def test_create_sub_panel_equipment_management(self, mock_adventure_prep_panel):
        """装備管理パネルの作成"""
        from src.facilities.ui.inn.adventure_prep_panel import AdventurePrepPanel
        
        with patch('src.facilities.ui.inn.adventure_prep_panel.EquipmentManagementPanel') as mock_panel_class:
            mock_panel_instance = Mock()
            mock_panel_class.return_value = mock_panel_instance
            
            result = AdventurePrepPanel._create_sub_panel(mock_adventure_prep_panel, "equipment_management")
            
            assert result == mock_panel_instance
            mock_panel_class.assert_called_once()
    
    def test_create_sub_panel_unknown_service(self, mock_adventure_prep_panel):
        """未知のサービスの場合はNoneを返す"""
        from src.facilities.ui.inn.adventure_prep_panel import AdventurePrepPanel
        
        result = AdventurePrepPanel._create_sub_panel(mock_adventure_prep_panel, "unknown_service")
        
        assert result is None
    
    def test_open_sub_service_new_panel(self, mock_adventure_prep_panel):
        """新しいサブパネルを開く"""
        from src.facilities.ui.inn.adventure_prep_panel import AdventurePrepPanel
        
        # UIボタンとinfo_boxのモック
        button1 = Mock()
        button2 = Mock()
        mock_adventure_prep_panel.sub_service_buttons = {"btn1": button1, "btn2": button2}
        mock_adventure_prep_panel.info_box = Mock()
        
        # サブパネル作成のモック
        mock_sub_panel = Mock()
        with patch.object(AdventurePrepPanel, '_create_sub_panel', return_value=mock_sub_panel):
            AdventurePrepPanel._open_sub_service(mock_adventure_prep_panel, "item_management")
            
            # サブパネルが作成・保存される
            assert mock_adventure_prep_panel.sub_panels["item_management"] == mock_sub_panel
            assert mock_adventure_prep_panel.active_sub_panel == mock_sub_panel
            
            # サブパネルが表示される
            mock_sub_panel.show.assert_called_once()
            
            # メインUIが隠される
            button1.hide.assert_called_once()
            button2.hide.assert_called_once()
            mock_adventure_prep_panel.info_box.hide.assert_called_once()
    
    def test_open_sub_service_existing_panel(self, mock_adventure_prep_panel):
        """既存のサブパネルを開く"""
        from src.facilities.ui.inn.adventure_prep_panel import AdventurePrepPanel
        
        # UIボタンとinfo_boxのモック
        button = Mock()
        mock_adventure_prep_panel.sub_service_buttons = {"btn": button}
        mock_adventure_prep_panel.info_box = Mock()
        
        # 既存のサブパネル
        existing_panel = Mock()
        mock_adventure_prep_panel.sub_panels = {"spell_management": existing_panel}
        
        AdventurePrepPanel._open_sub_service(mock_adventure_prep_panel, "spell_management")
        
        # 既存パネルが表示される
        assert mock_adventure_prep_panel.active_sub_panel == existing_panel
        existing_panel.show.assert_called_once()
    
    def test_open_sub_service_hide_current(self, mock_adventure_prep_panel):
        """現在のサブパネルを隠して新しいサブパネルを開く"""
        from src.facilities.ui.inn.adventure_prep_panel import AdventurePrepPanel
        
        # UIボタンとinfo_boxのモック
        mock_adventure_prep_panel.sub_service_buttons = {}
        mock_adventure_prep_panel.info_box = Mock()
        
        # 現在アクティブなサブパネル
        current_panel = Mock()
        mock_adventure_prep_panel.active_sub_panel = current_panel
        
        # 新しいサブパネル
        new_panel = Mock()
        with patch.object(AdventurePrepPanel, '_create_sub_panel', return_value=new_panel):
            AdventurePrepPanel._open_sub_service(mock_adventure_prep_panel, "equipment_management")
            
            # 現在のパネルが隠される
            current_panel.hide.assert_called_once()
            
            # 新しいパネルがアクティブになる
            assert mock_adventure_prep_panel.active_sub_panel == new_panel


class TestAdventurePrepPanelVisibility:
    """AdventurePrepPanelの表示/非表示テスト"""
    
    def test_show_without_active_sub_panel(self, mock_adventure_prep_panel):
        """アクティブなサブパネルがない場合の表示"""
        from src.facilities.ui.inn.adventure_prep_panel import AdventurePrepPanel
        
        # UIボタンとinfo_boxのモック
        button1 = Mock()
        button2 = Mock()
        mock_adventure_prep_panel.sub_service_buttons = {"btn1": button1, "btn2": button2}
        mock_adventure_prep_panel.info_box = Mock()
        mock_adventure_prep_panel.active_sub_panel = None
        
        with patch.object(AdventurePrepPanel.__bases__[0], 'show') as mock_super_show:
            AdventurePrepPanel.show(mock_adventure_prep_panel)
            
            # 親クラスのshowが呼ばれる
            mock_super_show.assert_called_once()
            
            # メインUIが表示される
            button1.show.assert_called_once()
            button2.show.assert_called_once()
            mock_adventure_prep_panel.info_box.show.assert_called_once()
    
    def test_show_with_active_sub_panel(self, mock_adventure_prep_panel):
        """アクティブなサブパネルがある場合の表示"""
        from src.facilities.ui.inn.adventure_prep_panel import AdventurePrepPanel
        
        # UIボタンとinfo_boxのモック
        button = Mock()
        mock_adventure_prep_panel.sub_service_buttons = {"btn": button}
        mock_adventure_prep_panel.info_box = Mock()
        
        # アクティブなサブパネルを設定
        active_panel = Mock()
        mock_adventure_prep_panel.active_sub_panel = active_panel
        
        with patch.object(AdventurePrepPanel.__bases__[0], 'show') as mock_super_show:
            AdventurePrepPanel.show(mock_adventure_prep_panel)
            
            # 親クラスのshowが呼ばれる
            mock_super_show.assert_called_once()
            
            # メインUIは表示されない
            button.show.assert_not_called()
    
    def test_hide(self, mock_adventure_prep_panel):
        """パネルの非表示"""
        from src.facilities.ui.inn.adventure_prep_panel import AdventurePrepPanel
        
        # サブパネルを設定
        sub_panel1 = Mock()
        sub_panel2 = Mock()
        mock_adventure_prep_panel.sub_panels = {"panel1": sub_panel1, "panel2": sub_panel2}
        mock_adventure_prep_panel.active_sub_panel = sub_panel1
        
        with patch.object(AdventurePrepPanel.__bases__[0], 'hide') as mock_super_hide:
            AdventurePrepPanel.hide(mock_adventure_prep_panel)
            
            # 親クラスのhideが呼ばれる
            mock_super_hide.assert_called_once()
            
            # すべてのサブパネルが非表示になる
            sub_panel1.hide.assert_called_once()
            sub_panel2.hide.assert_called_once()
            
            # アクティブなサブパネルがクリアされる
            assert mock_adventure_prep_panel.active_sub_panel is None


class TestAdventurePrepPanelRefresh:
    """AdventurePrepPanelのリフレッシュ機能テスト"""
    
    def test_refresh_info_box(self, mock_adventure_prep_panel):
        """情報ボックスのリフレッシュ"""
        from src.facilities.ui.inn.adventure_prep_panel import AdventurePrepPanel
        
        # 情報ボックスのモック
        info_box = Mock()
        mock_adventure_prep_panel.info_box = info_box
        mock_adventure_prep_panel.active_sub_panel = None
        
        with patch.object(AdventurePrepPanel, '_get_party_status_text', return_value="新しいテキスト"):
            AdventurePrepPanel.refresh(mock_adventure_prep_panel)
            
            # 情報ボックスのテキストが更新される
            assert info_box.html_text == "新しいテキスト"
            info_box.rebuild.assert_called_once()
    
    def test_refresh_active_sub_panel(self, mock_adventure_prep_panel):
        """アクティブなサブパネルのリフレッシュ"""
        from src.facilities.ui.inn.adventure_prep_panel import AdventurePrepPanel
        
        # アクティブなサブパネル
        active_panel = Mock()
        mock_adventure_prep_panel.active_sub_panel = active_panel
        mock_adventure_prep_panel.info_box = None
        
        AdventurePrepPanel.refresh(mock_adventure_prep_panel)
        
        # アクティブなサブパネルがリフレッシュされる
        active_panel.refresh.assert_called_once()
    
    def test_refresh_no_info_box(self, mock_adventure_prep_panel):
        """情報ボックスがない場合のリフレッシュ"""
        from src.facilities.ui.inn.adventure_prep_panel import AdventurePrepPanel
        
        mock_adventure_prep_panel.info_box = None
        mock_adventure_prep_panel.active_sub_panel = None
        
        # エラーが発生しないことを確認
        try:
            AdventurePrepPanel.refresh(mock_adventure_prep_panel)
            assert True
        except Exception as e:
            pytest.fail(f"Unexpected exception: {e}")


class TestAdventurePrepPanelBackAction:
    """AdventurePrepPanelの戻るアクション処理テスト"""
    
    def test_handle_back_action_with_active_sub_panel(self, mock_adventure_prep_panel):
        """アクティブなサブパネルがある場合の戻るアクション"""
        from src.facilities.ui.inn.adventure_prep_panel import AdventurePrepPanel
        
        # UIボタンとinfo_boxのモック
        button1 = Mock()
        button2 = Mock()
        mock_adventure_prep_panel.sub_service_buttons = {"btn1": button1, "btn2": button2}
        mock_adventure_prep_panel.info_box = Mock()
        
        # アクティブなサブパネル
        active_panel = Mock()
        mock_adventure_prep_panel.active_sub_panel = active_panel
        
        result = AdventurePrepPanel.handle_back_action(mock_adventure_prep_panel)
        
        assert result is True
        
        # サブパネルが隠される
        active_panel.hide.assert_called_once()
        assert mock_adventure_prep_panel.active_sub_panel is None
        
        # メインUIが再表示される
        button1.show.assert_called_once()
        button2.show.assert_called_once()
        mock_adventure_prep_panel.info_box.show.assert_called_once()
    
    def test_handle_back_action_without_active_sub_panel(self, mock_adventure_prep_panel):
        """アクティブなサブパネルがない場合の戻るアクション"""
        from src.facilities.ui.inn.adventure_prep_panel import AdventurePrepPanel
        
        mock_adventure_prep_panel.active_sub_panel = None
        
        result = AdventurePrepPanel.handle_back_action(mock_adventure_prep_panel)
        
        assert result is False