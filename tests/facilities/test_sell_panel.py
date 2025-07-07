"""売却パネルのテスト"""

import pytest
import pygame
import pygame_gui
from unittest.mock import Mock, MagicMock, patch
from src.facilities.core.service_result import ServiceResult


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
def sample_sellable_items():
    """サンプル売却可能アイテム"""
    return [
        {
            "id": "item1",
            "name": "古い剣",
            "type": "weapon",
            "base_price": 400,
            "sell_price": 200,
            "quantity": 1,
            "owner": "戦士アレン",
            "owner_id": "char1",
            "description": "使い古された鉄の剣"
        },
        {
            "id": "item2",
            "name": "ヒールポーション",
            "type": "consumable",
            "base_price": 50,
            "sell_price": 25,
            "quantity": 3,
            "owner": "魔法使いベラ",
            "owner_id": "char2",
            "description": "HPを回復するポーション"
        },
        {
            "id": "item3",
            "name": "革の鎧",
            "type": "armor", 
            "base_price": 300,
            "sell_price": 150,
            "quantity": 1,
            "owner": "戦士アレン",
            "owner_id": "char1",
            "description": "軽量な革製の防具"
        }
    ]


@pytest.fixture
def sample_service_result():
    """サンプルサービス結果"""
    def create_result(success=True, data=None, message=""):
        result = ServiceResult(success=success, data=data, message=message)
        return result
    return create_result


class TestSellPanelBasic:
    """SellPanelの基本機能テスト"""
    
    def test_initialization(self, mock_controller, mock_ui_setup):
        """正常に初期化される"""
        from src.facilities.ui.shop.sell_panel import SellPanel
        
        rect, parent, ui_manager = mock_ui_setup
        
        with patch('src.facilities.ui.service_panel.ServicePanel.__init__', return_value=None):
            panel = SellPanel(rect, parent, mock_controller, ui_manager)
            
            # 初期状態の確認
            assert panel.owner_list is None
            assert panel.item_list is None
            assert panel.detail_box is None
            assert panel.quantity_input is None
            assert panel.sell_button is None
            assert panel.gold_label is None
            assert panel.sell_info_label is None
            
            # データの初期状態
            assert panel.sellable_items == []
            assert panel.items_by_owner == {}
            assert panel.selected_owner is None
            assert panel.selected_item is None
            assert panel.displayed_items == []
            assert panel.sell_rate == 0.5
    
    def test_create_ui_elements(self, mock_controller, mock_ui_setup):
        """UI要素が正常に作成される"""
        from src.facilities.ui.shop.sell_panel import SellPanel
        
        rect, parent, ui_manager = mock_ui_setup
        
        with patch('src.facilities.ui.service_panel.ServicePanel.__init__', return_value=None):
            panel = Mock()
            panel.rect = rect
            panel.ui_manager = ui_manager
            panel.container = Mock()
            panel.ui_elements = []
            
            with patch.object(SellPanel, '_create_header') as mock_header, \
                 patch.object(SellPanel, '_create_lists') as mock_lists, \
                 patch.object(SellPanel, '_create_detail_area') as mock_detail, \
                 patch.object(SellPanel, '_create_sell_controls') as mock_controls, \
                 patch.object(SellPanel, '_load_sellable_items') as mock_load:
                
                SellPanel._create_ui(panel)
                
                # 各UI作成メソッドが呼ばれる
                mock_header.assert_called_once()
                mock_lists.assert_called_once()
                mock_detail.assert_called_once()
                mock_controls.assert_called_once()
                mock_load.assert_called_once()


class TestSellPanelUICreation:
    """SellPanelのUI作成テスト"""
    
    def test_create_header(self):
        """ヘッダーの作成"""
        from src.facilities.ui.shop.sell_panel import SellPanel
        
        panel = Mock()
        panel.rect = pygame.Rect(0, 0, 800, 600)
        panel.ui_manager = Mock()
        panel.container = Mock()
        panel.ui_elements = []
        
        with patch('pygame_gui.elements.UILabel') as mock_label:
            SellPanel._create_header(panel)
            
            # タイトルと所持金ラベルが作成される
            assert mock_label.call_count == 2
    
    def test_create_lists(self):
        """リストの作成"""
        from src.facilities.ui.shop.sell_panel import SellPanel
        
        panel = Mock()
        panel.ui_manager = Mock()
        panel.container = Mock()
        panel.ui_elements = []
        
        with patch('pygame_gui.elements.UILabel') as mock_label, \
             patch('pygame_gui.elements.UISelectionList') as mock_list:
            
            SellPanel._create_lists(panel)
            
            # オーナーとアイテムのラベル
            assert mock_label.call_count == 2
            
            # オーナーとアイテムのリスト
            assert mock_list.call_count == 2
    
    def test_create_sell_controls(self):
        """売却コントロールの作成"""
        from src.facilities.ui.shop.sell_panel import SellPanel
        
        panel = Mock()
        panel.ui_manager = Mock()
        panel.container = Mock()
        panel.ui_elements = []
        
        with patch('pygame_gui.elements.UILabel') as mock_label, \
             patch('pygame_gui.elements.UITextEntryLine') as mock_entry, \
             patch('pygame_gui.elements.UIButton') as mock_button:
            
            SellPanel._create_sell_controls(panel)
            
            # 数量ラベル、入力フィールド、売却ボタンが作成される
            assert mock_label.call_count == 2  # 数量ラベル、売却情報ラベル
            mock_entry.assert_called_once()
            mock_button.assert_called_once()


class TestSellPanelDataLoading:
    """SellPanelのデータ読み込みテスト"""
    
    def test_load_sellable_items_success(self, mock_controller, sample_sellable_items, sample_service_result):
        """売却可能アイテムの読み込み成功"""
        from src.facilities.ui.shop.sell_panel import SellPanel
        
        panel = Mock()
        panel.controller = mock_controller
        panel.sell_rate = 0.5
        
        # サービス結果のモック
        result = sample_service_result(
            success=True,
            data={
                "items": sample_sellable_items,
                "party_gold": 1000,
                "sell_rate": 0.6
            }
        )
        
        with patch.object(SellPanel, '_execute_service_action', return_value=result), \
             patch.object(SellPanel, '_organize_items_by_owner') as mock_organize, \
             patch.object(SellPanel, '_update_owner_list') as mock_owner, \
             patch.object(SellPanel, '_update_gold_display') as mock_gold:
            
            SellPanel._load_sellable_items(panel)
            
            # データが設定される
            assert panel.sellable_items == sample_sellable_items
            assert panel.sell_rate == 0.6
            
            # UI更新メソッドが呼ばれる
            mock_organize.assert_called_once()
            mock_owner.assert_called_once()
            mock_gold.assert_called_with(panel, 1000)
    
    def test_load_sellable_items_failure(self, mock_controller, sample_service_result):
        """売却可能アイテムの読み込み失敗"""
        from src.facilities.ui.shop.sell_panel import SellPanel
        
        panel = Mock()
        panel.controller = mock_controller
        panel.sellable_items = []
        
        # 失敗結果
        result = sample_service_result(success=False)
        
        with patch.object(SellPanel, '_execute_service_action', return_value=result), \
             patch.object(SellPanel, '_show_message') as mock_message:
            
            SellPanel._load_sellable_items(panel)
            
            # エラーメッセージが表示される
            mock_message.assert_called()
            
            # データは空のまま
            assert panel.sellable_items == []
    
    def test_organize_items_by_owner(self, sample_sellable_items):
        """オーナー別アイテム整理"""
        from src.facilities.ui.shop.sell_panel import SellPanel
        
        panel = Mock()
        panel.sellable_items = sample_sellable_items
        panel.items_by_owner = {}
        
        SellPanel._organize_items_by_owner(panel)
        
        # オーナー別に整理される
        assert "戦士アレン" in panel.items_by_owner
        assert "魔法使いベラ" in panel.items_by_owner
        
        # 戦士アレンのアイテムが2個
        assert len(panel.items_by_owner["戦士アレン"]) == 2
        
        # 魔法使いベラのアイテムが1個
        assert len(panel.items_by_owner["魔法使いベラ"]) == 1


class TestSellPanelOwnerSelection:
    """SellPanelのオーナー選択テスト"""
    
    def test_handle_owner_selection_valid(self, sample_sellable_items):
        """有効なオーナー選択の処理"""
        from src.facilities.ui.shop.sell_panel import SellPanel
        
        panel = Mock()
        panel.items_by_owner = {
            "戦士アレン": [sample_sellable_items[0], sample_sellable_items[2]],
            "魔法使いベラ": [sample_sellable_items[1]]
        }
        panel.selected_owner = None
        panel.selected_item = None
        
        with patch.object(SellPanel, '_update_item_list') as mock_update, \
             patch.object(SellPanel, '_clear_item_selection') as mock_clear:
            
            SellPanel._handle_owner_selection(panel, "戦士アレン")
            
            # オーナーが設定される
            assert panel.selected_owner == "戦士アレン"
            
            # アイテムリストが更新される
            mock_update.assert_called_once()
            
            # アイテム選択がクリアされる
            mock_clear.assert_called_once()
    
    def test_handle_owner_selection_invalid(self):
        """無効なオーナー選択の処理"""
        from src.facilities.ui.shop.sell_panel import SellPanel
        
        panel = Mock()
        panel.items_by_owner = {"戦士アレン": []}
        
        with patch.object(SellPanel, '_update_item_list') as mock_update:
            SellPanel._handle_owner_selection(panel, "存在しないオーナー")
            
            # アイテムリストは更新されない
            mock_update.assert_not_called()
    
    def test_update_item_list_by_owner(self, sample_sellable_items):
        """オーナー別アイテムリスト更新"""
        from src.facilities.ui.shop.sell_panel import SellPanel
        
        panel = Mock()
        panel.selected_owner = "戦士アレン"
        panel.items_by_owner = {
            "戦士アレン": [sample_sellable_items[0], sample_sellable_items[2]]
        }
        panel.item_list = Mock()
        
        SellPanel._update_item_list(panel)
        
        # アイテムリストが設定される
        expected_items = [
            "古い剣 x1 (200G)",
            "革の鎧 x1 (150G)"
        ]
        panel.item_list.set_item_list.assert_called_with(expected_items)
        
        # 表示アイテムリストが設定される
        assert len(panel.displayed_items) == 2
    
    def test_update_item_list_no_owner(self):
        """オーナー未選択でのアイテムリスト更新"""
        from src.facilities.ui.shop.sell_panel import SellPanel
        
        panel = Mock()
        panel.selected_owner = None
        panel.item_list = Mock()
        
        SellPanel._update_item_list(panel)
        
        # 空リストが設定される
        panel.item_list.set_item_list.assert_called_with([])
        assert panel.displayed_items == []


class TestSellPanelItemSelection:
    """SellPanelのアイテム選択テスト"""
    
    def test_handle_item_selection_valid(self, sample_sellable_items):
        """有効なアイテム選択の処理"""
        from src.facilities.ui.shop.sell_panel import SellPanel
        
        panel = Mock()
        panel.displayed_items = [sample_sellable_items[0], sample_sellable_items[1]]
        panel.selected_item = None
        
        with patch.object(SellPanel, '_update_detail_display') as mock_detail, \
             patch.object(SellPanel, '_update_sell_controls') as mock_controls:
            
            SellPanel._handle_item_selection(panel, 0)
            
            # 選択されたアイテムが設定される
            assert panel.selected_item == sample_sellable_items[0]
            
            # 詳細表示と売却コントロールが更新される
            mock_detail.assert_called_once()
            mock_controls.assert_called_once()
    
    def test_handle_item_selection_invalid_index(self, sample_sellable_items):
        """無効なインデックスでの選択処理"""
        from src.facilities.ui.shop.sell_panel import SellPanel
        
        panel = Mock()
        panel.displayed_items = [sample_sellable_items[0]]
        
        with patch.object(SellPanel, '_update_detail_display') as mock_detail:
            SellPanel._handle_item_selection(panel, 5)  # 範囲外
            
            # 詳細表示は更新されない
            mock_detail.assert_not_called()
    
    def test_clear_item_selection(self):
        """アイテム選択のクリア"""
        from src.facilities.ui.shop.sell_panel import SellPanel
        
        panel = Mock()
        panel.selected_item = {"id": "test"}
        panel.quantity_input = Mock()
        
        with patch.object(SellPanel, '_update_detail_display') as mock_detail, \
             patch.object(SellPanel, '_update_sell_controls') as mock_controls:
            
            SellPanel._clear_item_selection(panel)
            
            # 選択がクリアされる
            assert panel.selected_item is None
            
            # 数量入力がリセットされる
            panel.quantity_input.set_text.assert_called_with("1")
            
            # 表示が更新される
            mock_detail.assert_called_once()
            mock_controls.assert_called_once()


class TestSellPanelSell:
    """SellPanelの売却処理テスト"""
    
    def test_handle_sell_success(self, sample_sellable_items, sample_service_result):
        """売却処理成功"""
        from src.facilities.ui.shop.sell_panel import SellPanel
        
        panel = Mock()
        panel.selected_item = sample_sellable_items[1]  # ヒールポーション x3
        panel.quantity_input = Mock()
        panel.quantity_input.get_text.return_value = "2"
        
        # 売却結果のモック
        result = sample_service_result(
            success=True,
            message="ヒールポーション x2を50Gで売却しました",
            data={"remaining_gold": 1050}
        )
        
        with patch.object(SellPanel, '_execute_service_action', return_value=result), \
             patch.object(SellPanel, '_show_message') as mock_message, \
             patch.object(SellPanel, '_load_sellable_items') as mock_reload, \
             patch.object(SellPanel, '_clear_item_selection') as mock_clear:
            
            SellPanel._handle_sell(panel)
            
            # サービスが呼ばれる
            SellPanel._execute_service_action.assert_called_with(
                panel, "sell", {
                    "item_id": "item2",
                    "owner_id": "char2",
                    "quantity": 2
                }
            )
            
            # 成功メッセージが表示される
            mock_message.assert_called_with(panel, "ヒールポーション x2を50Gで売却しました", "success")
            
            # データが再読み込みされる
            mock_reload.assert_called_once()
            
            # 選択がクリアされる
            mock_clear.assert_called_once()
    
    def test_handle_sell_failure(self, sample_sellable_items, sample_service_result):
        """売却処理失敗"""
        from src.facilities.ui.shop.sell_panel import SellPanel
        
        panel = Mock()
        panel.selected_item = sample_sellable_items[0]
        panel.quantity_input = Mock()
        panel.quantity_input.get_text.return_value = "1"
        
        # 失敗結果
        result = sample_service_result(
            success=False,
            message="このアイテムは売却できません"
        )
        
        with patch.object(SellPanel, '_execute_service_action', return_value=result), \
             patch.object(SellPanel, '_show_message') as mock_message:
            
            SellPanel._handle_sell(panel)
            
            # エラーメッセージが表示される
            mock_message.assert_called_with(panel, "このアイテムは売却できません", "error")
    
    def test_handle_sell_no_selection(self):
        """選択なしでの売却処理"""
        from src.facilities.ui.shop.sell_panel import SellPanel
        
        panel = Mock()
        panel.selected_item = None
        
        with patch.object(SellPanel, '_execute_service_action') as mock_service:
            SellPanel._handle_sell(panel)
            
            # サービスが呼ばれない
            mock_service.assert_not_called()
    
    def test_handle_sell_invalid_quantity(self, sample_sellable_items):
        """無効な数量での売却処理"""
        from src.facilities.ui.shop.sell_panel import SellPanel
        
        panel = Mock()
        panel.selected_item = sample_sellable_items[0]
        panel.quantity_input = Mock()
        panel.quantity_input.get_text.return_value = "abc"  # 無効な数値
        
        with patch.object(SellPanel, '_show_message') as mock_message, \
             patch.object(SellPanel, '_execute_service_action') as mock_service:
            
            SellPanel._handle_sell(panel)
            
            # エラーメッセージが表示される
            mock_message.assert_called_with(panel, "有効な数量を入力してください", "error")
            
            # サービスが呼ばれない
            mock_service.assert_not_called()
    
    def test_handle_sell_quantity_exceeds_stock(self, sample_sellable_items):
        """所持数を超える数量での売却処理"""
        from src.facilities.ui.shop.sell_panel import SellPanel
        
        panel = Mock()
        panel.selected_item = sample_sellable_items[0]  # quantity: 1
        panel.quantity_input = Mock()
        panel.quantity_input.get_text.return_value = "5"  # 所持数を超える
        
        with patch.object(SellPanel, '_show_message') as mock_message, \
             patch.object(SellPanel, '_execute_service_action') as mock_service:
            
            SellPanel._handle_sell(panel)
            
            # エラーメッセージが表示される
            mock_message.assert_called_with(panel, "所持数を超える数量は売却できません", "error")
            
            # サービスが呼ばれない
            mock_service.assert_not_called()


class TestSellPanelEventHandling:
    """SellPanelのイベント処理テスト"""
    
    def test_handle_selection_list_changed_owner_list(self):
        """オーナーリスト選択変更イベントの処理"""
        from src.facilities.ui.shop.sell_panel import SellPanel
        
        panel = Mock()
        panel.owner_list = Mock()
        panel.item_list = Mock()
        panel.items_by_owner = {"戦士アレン": [], "魔法使いベラ": []}
        
        # 選択変更イベント
        event = Mock()
        event.type = pygame_gui.UI_SELECTION_LIST_NEW_SELECTION
        event.ui_element = panel.owner_list
        
        # 選択されたオーナー
        panel.owner_list.get_single_selection.return_value = "戦士アレン"
        
        with patch.object(SellPanel, '_handle_owner_selection') as mock_selection:
            result = SellPanel.handle_selection_list_changed(panel, event)
            
            assert result is True
            mock_selection.assert_called_with(panel, "戦士アレン")
    
    def test_handle_selection_list_changed_item_list(self):
        """アイテムリスト選択変更イベントの処理"""
        from src.facilities.ui.shop.sell_panel import SellPanel
        
        panel = Mock()
        panel.owner_list = Mock()
        panel.item_list = Mock()
        
        # 選択変更イベント
        event = Mock()
        event.type = pygame_gui.UI_SELECTION_LIST_NEW_SELECTION
        event.ui_element = panel.item_list
        
        # 選択インデックス
        panel.item_list.get_single_selection.return_value = 1
        
        with patch.object(SellPanel, '_handle_item_selection') as mock_selection:
            result = SellPanel.handle_selection_list_changed(panel, event)
            
            assert result is True
            mock_selection.assert_called_with(panel, 1)
    
    def test_handle_button_click_sell_button(self):
        """売却ボタンクリックの処理"""
        from src.facilities.ui.shop.sell_panel import SellPanel
        
        panel = Mock()
        panel.sell_button = Mock()
        
        with patch.object(SellPanel, '_handle_sell') as mock_sell:
            result = SellPanel.handle_button_click(panel, panel.sell_button)
            
            assert result is True
            mock_sell.assert_called_once()
    
    def test_handle_button_click_unknown(self):
        """未知のボタンクリックの処理"""
        from src.facilities.ui.shop.sell_panel import SellPanel
        
        panel = Mock()
        panel.sell_button = Mock()
        
        unknown_button = Mock()
        
        result = SellPanel.handle_button_click(panel, unknown_button)
        
        assert result is False


class TestSellPanelUIUpdates:
    """SellPanelのUI更新テスト"""
    
    def test_update_gold_display(self):
        """所持金表示の更新"""
        from src.facilities.ui.shop.sell_panel import SellPanel
        
        panel = Mock()
        panel.gold_label = Mock()
        
        SellPanel._update_gold_display(panel, 2500)
        
        panel.gold_label.set_text.assert_called_with("所持金: 2500 G")
    
    def test_update_owner_list(self):
        """オーナーリストの更新"""
        from src.facilities.ui.shop.sell_panel import SellPanel
        
        panel = Mock()
        panel.items_by_owner = {"戦士アレン": [], "魔法使いベラ": []}
        panel.owner_list = Mock()
        
        SellPanel._update_owner_list(panel)
        
        # オーナーリストが設定される
        expected_owners = ["戦士アレン", "魔法使いベラ"]
        panel.owner_list.set_item_list.assert_called_with(expected_owners)
    
    def test_update_sell_controls_with_selection(self, sample_sellable_items):
        """選択ありでの売却コントロール更新"""
        from src.facilities.ui.shop.sell_panel import SellPanel
        
        panel = Mock()
        panel.selected_item = sample_sellable_items[0]
        panel.sell_button = Mock()
        panel.sell_info_label = Mock()
        
        SellPanel._update_sell_controls(panel)
        
        # 売却ボタンが有効化される
        panel.sell_button.enable.assert_called_once()
        
        # 売却情報が更新される
        panel.sell_info_label.set_text.assert_called_with("売却価格: 200G")
    
    def test_update_sell_controls_no_selection(self):
        """選択なしでの売却コントロール更新"""
        from src.facilities.ui.shop.sell_panel import SellPanel
        
        panel = Mock()
        panel.selected_item = None
        panel.sell_button = Mock()
        panel.sell_info_label = Mock()
        
        SellPanel._update_sell_controls(panel)
        
        # 売却ボタンが無効化される
        panel.sell_button.disable.assert_called_once()
        
        # 売却情報がクリアされる
        panel.sell_info_label.set_text.assert_called_with("")
    
    def test_update_detail_display_with_item(self, sample_sellable_items):
        """アイテムありでの詳細表示更新"""
        from src.facilities.ui.shop.sell_panel import SellPanel
        
        panel = Mock()
        panel.selected_item = sample_sellable_items[0]
        panel.detail_box = Mock()
        
        SellPanel._update_detail_display(panel)
        
        # 詳細情報が設定される
        expected_html = ("<b>古い剣</b><br>"
                        "種類: weapon<br>"
                        "基本価格: 400G<br>"
                        "売却価格: 200G<br>"
                        "所持者: 戦士アレン<br>"
                        "<br>"
                        "使い古された鉄の剣")
        assert panel.detail_box.html_text == expected_html
        panel.detail_box.rebuild.assert_called_once()
    
    def test_update_detail_display_no_item(self):
        """アイテムなしでの詳細表示更新"""
        from src.facilities.ui.shop.sell_panel import SellPanel
        
        panel = Mock()
        panel.selected_item = None
        panel.detail_box = Mock()
        
        SellPanel._update_detail_display(panel)
        
        # 詳細情報がクリアされる
        assert panel.detail_box.html_text == ""
        panel.detail_box.rebuild.assert_called_once()


class TestSellPanelRefresh:
    """SellPanelのリフレッシュ機能テスト"""
    
    def test_refresh(self):
        """パネルのリフレッシュ"""
        from src.facilities.ui.shop.sell_panel import SellPanel
        
        panel = Mock()
        
        with patch.object(SellPanel, '_load_sellable_items') as mock_load, \
             patch.object(SellPanel, '_clear_item_selection') as mock_clear:
            
            SellPanel.refresh(panel)
            
            # データが再読み込みされる
            mock_load.assert_called_once()
            
            # 選択がクリアされる
            mock_clear.assert_called_once()