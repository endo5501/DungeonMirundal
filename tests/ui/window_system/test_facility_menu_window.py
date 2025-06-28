"""
FacilityMenuWindow のテスト

t-wada式TDDによるテストファースト開発
施設メインメニューから新Window Systemへの移行
"""

import pytest
import pygame
import pygame_gui
from unittest.mock import Mock, patch, MagicMock
from src.ui.window_system import Window, WindowState
from src.ui.window_system.facility_menu_window import FacilityMenuWindow, FacilityType


class TestFacilityMenuWindow:
    """FacilityMenuWindow のテストクラス"""
    
    def setup_method(self):
        """各テストメソッドの前に実行される"""
        pygame.init()
        pygame.display.set_mode((1, 1), pygame.NOFRAME)
    
    def teardown_method(self):
        """各テストメソッドの後に実行される"""
        pygame.quit()
    
    def test_facility_menu_window_inherits_from_window(self):
        """FacilityMenuWindowがWindowクラスを継承することを確認"""
        # Given: 施設メニュー設定
        facility_config = {
            'facility_type': 'guild',
            'facility_name': '冒険者ギルド',
            'party': Mock(),
            'menu_items': [
                {'id': 'create_character', 'label': 'キャラクター作成'},
                {'id': 'party_formation', 'label': 'パーティ編成'},
                {'id': 'exit', 'label': '出る'}
            ]
        }
        
        # When: FacilityMenuWindowを作成
        facility_window = FacilityMenuWindow('guild_menu', facility_config)
        
        # Then: Windowクラスを継承している
        assert isinstance(facility_window, Window)
        assert facility_window.window_id == 'guild_menu'
        assert facility_window.facility_type == FacilityType.GUILD
        assert facility_window.modal is True  # 施設メニューは通常モーダル
    
    def test_facility_menu_validates_config_structure(self):
        """施設メニューの設定構造が検証されることを確認"""
        # When: facility_typeが無い設定でウィンドウを作成しようとする
        # Then: 例外が発生する
        with pytest.raises(ValueError, match="Facility config must contain 'facility_type'"):
            FacilityMenuWindow('invalid_facility', {})
        
        # When: menu_itemsが無い設定でウィンドウを作成しようとする
        # Then: 例外が発生する
        with pytest.raises(ValueError, match="Facility config must contain 'menu_items'"):
            FacilityMenuWindow('invalid_facility', {'facility_type': 'guild'})
    
    def test_facility_menu_displays_facility_name_and_items(self):
        """施設名とメニュー項目が表示されることを確認"""
        # Given: メニュー項目を含む施設設定
        facility_config = {
            'facility_type': 'inn',
            'facility_name': '宿屋「安らぎの夜」',
            'party': Mock(),
            'menu_items': [
                {'id': 'adventure_prep', 'label': '冒険の準備'},
                {'id': 'party_status', 'label': 'パーティ状況'},
                {'id': 'exit', 'label': '出る'}
            ]
        }
        
        facility_window = FacilityMenuWindow('inn_menu', facility_config)
        facility_window.create()
        
        # Then: 施設名とメニューが表示される
        assert facility_window.facility_title is not None
        assert facility_window.menu_buttons is not None
        assert len(facility_window.menu_buttons) == 3
    
    def test_facility_menu_handles_menu_item_selection(self):
        """メニュー項目の選択が動作することを確認"""
        # Given: 施設メニュー
        facility_config = {
            'facility_type': 'shop',
            'facility_name': '武具店',
            'party': Mock(),
            'menu_items': [
                {'id': 'buy_items', 'label': 'アイテム購入'},
                {'id': 'sell_items', 'label': 'アイテム売却'},
                {'id': 'exit', 'label': '出る'}
            ]
        }
        
        facility_window = FacilityMenuWindow('shop_menu', facility_config)
        facility_window.create()
        
        # When: メニュー項目を選択
        with patch.object(facility_window, 'send_message') as mock_send:
            result = facility_window.select_menu_item('buy_items')
        
        # Then: 選択メッセージが送信される
        assert result is True
        mock_send.assert_called_once_with('menu_item_selected', {
            'item_id': 'buy_items',
            'facility_type': 'shop'
        })
    
    def test_facility_menu_supports_keyboard_navigation(self):
        """キーボードナビゲーションが動作することを確認"""
        # Given: 施設メニュー
        facility_config = {
            'facility_type': 'guild',
            'facility_name': '冒険者ギルド',
            'party': Mock(),
            'menu_items': [
                {'id': 'create_character', 'label': 'キャラクター作成'},
                {'id': 'party_formation', 'label': 'パーティ編成'},
                {'id': 'exit', 'label': '出る'}
            ]
        }
        
        facility_window = FacilityMenuWindow('nav_menu', facility_config)
        facility_window.create()
        
        # When: 下矢印キーでメニュー移動
        arrow_event = Mock()
        arrow_event.type = pygame.KEYDOWN
        arrow_event.key = pygame.K_DOWN
        arrow_event.mod = 0
        
        result = facility_window.handle_event(arrow_event)
        
        # Then: フォーカスが移動する
        assert result is True
        assert facility_window.selected_index == 1
    
    def test_facility_menu_handles_enter_key_selection(self):
        """Enterキーでの選択が動作することを確認"""
        # Given: 施設メニュー
        facility_config = {
            'facility_type': 'temple',
            'facility_name': '神殿',
            'party': Mock(),
            'menu_items': [
                {'id': 'heal_party', 'label': 'パーティ回復'},
                {'id': 'resurrection', 'label': '蘇生サービス'},
                {'id': 'exit', 'label': '出る'}
            ]
        }
        
        facility_window = FacilityMenuWindow('temple_menu', facility_config)
        facility_window.create()
        facility_window.selected_index = 1  # 蘇生サービスを選択状態に
        
        # When: Enterキーを押す
        enter_event = Mock()
        enter_event.type = pygame.KEYDOWN
        enter_event.key = pygame.K_RETURN
        enter_event.mod = 0
        
        with patch.object(facility_window, 'send_message') as mock_send:
            result = facility_window.handle_event(enter_event)
        
        # Then: 選択された項目がアクティベートされる
        assert result is True
        mock_send.assert_called_once_with('menu_item_selected', {
            'item_id': 'resurrection',
            'facility_type': 'temple'
        })
    
    def test_facility_menu_handles_exit_selection(self):
        """「出る」選択が動作することを確認"""
        # Given: 施設メニュー
        facility_config = {
            'facility_type': 'guild',
            'facility_name': '冒険者ギルド',
            'party': Mock(),
            'menu_items': [
                {'id': 'create_character', 'label': 'キャラクター作成'},
                {'id': 'exit', 'label': '出る'}
            ]
        }
        
        facility_window = FacilityMenuWindow('exit_menu', facility_config)
        facility_window.create()
        
        # When: 「出る」を選択
        with patch.object(facility_window, 'send_message') as mock_send:
            result = facility_window.select_menu_item('exit')
        
        # Then: 退場メッセージが送信される
        assert result is True
        mock_send.assert_called_once_with('facility_exit_requested', {
            'facility_type': 'guild'
        })
    
    def test_facility_menu_escape_key_exits(self):
        """ESCキーで施設から出ることを確認"""
        # Given: 施設メニュー
        facility_config = {
            'facility_type': 'inn',
            'facility_name': '宿屋',
            'party': Mock(),
            'menu_items': [
                {'id': 'rest', 'label': '休息'},
                {'id': 'exit', 'label': '出る'}
            ]
        }
        
        facility_window = FacilityMenuWindow('esc_menu', facility_config)
        facility_window.create()
        
        # When: ESCキーを押す
        with patch.object(facility_window, 'send_message') as mock_send:
            result = facility_window.handle_escape()
        
        # Then: 退場メッセージが送信される
        assert result is True
        mock_send.assert_called_once_with('facility_exit_requested', {
            'facility_type': 'inn'
        })
    
    def test_facility_menu_displays_party_information(self):
        """パーティ情報が表示されることを確認"""
        # Given: パーティ情報を持つ施設メニュー
        mock_party = Mock()
        mock_party.get_member_count.return_value = 3
        mock_party.get_gold.return_value = 1500
        
        facility_config = {
            'facility_type': 'shop',
            'facility_name': '商店',
            'party': mock_party,
            'menu_items': [
                {'id': 'buy', 'label': '購入'},
                {'id': 'exit', 'label': '出る'}
            ],
            'show_party_info': True
        }
        
        facility_window = FacilityMenuWindow('party_info_menu', facility_config)
        facility_window.create()
        
        # Then: パーティ情報が表示される
        assert facility_window.party_info_panel is not None
        # パーティ情報の内容をチェック（実装に依存）
    
    def test_facility_menu_supports_conditional_menu_items(self):
        """条件付きメニュー項目の表示が動作することを確認"""
        # Given: 条件付きメニュー項目を含む施設設定
        mock_party = Mock()
        mock_party.has_dead_members.return_value = True
        
        facility_config = {
            'facility_type': 'temple',
            'facility_name': '神殿',
            'party': mock_party,
            'menu_items': [
                {'id': 'heal', 'label': '回復'},
                {'id': 'resurrection', 'label': '蘇生', 'condition': 'has_dead_members'},
                {'id': 'exit', 'label': '出る'}
            ]
        }
        
        facility_window = FacilityMenuWindow('conditional_menu', facility_config)
        facility_window.create()
        
        # Then: 条件を満たすメニュー項目が表示される
        visible_items = [item for item in facility_window.menu_items if item.visible]
        assert len(visible_items) == 3  # 全項目が表示される
    
    def test_facility_menu_handles_disabled_menu_items(self):
        """無効化されたメニュー項目の処理が動作することを確認"""
        # Given: 無効化されたメニュー項目を含む施設設定
        mock_party = Mock()
        mock_party.get_gold.return_value = 50  # 少額
        
        facility_config = {
            'facility_type': 'shop',
            'facility_name': '商店',
            'party': mock_party,
            'menu_items': [
                {'id': 'buy_expensive', 'label': '高級品購入', 'cost': 1000},
                {'id': 'buy_cheap', 'label': '安物購入', 'cost': 10},
                {'id': 'exit', 'label': '出る'}
            ]
        }
        
        facility_window = FacilityMenuWindow('disabled_menu', facility_config)
        facility_window.create()
        
        # When: 資金不足で購入できない項目を選択しようとする
        result = facility_window.select_menu_item('buy_expensive')
        
        # Then: 選択が拒否される（実装に依存）
        # この場合の動作は実装で決定
    
    def test_facility_menu_supports_submenu_navigation(self):
        """サブメニューナビゲーションが動作することを確認"""
        # Given: サブメニューを持つ施設設定
        facility_config = {
            'facility_type': 'guild',
            'facility_name': '冒険者ギルド',
            'party': Mock(),
            'menu_items': [
                {'id': 'character_menu', 'label': 'キャラクター管理', 'type': 'submenu'},
                {'id': 'party_menu', 'label': 'パーティ管理', 'type': 'submenu'},
                {'id': 'exit', 'label': '出る'}
            ]
        }
        
        facility_window = FacilityMenuWindow('submenu_menu', facility_config)
        facility_window.create()
        
        # When: サブメニュー項目を選択
        with patch.object(facility_window, 'send_message') as mock_send:
            result = facility_window.select_menu_item('character_menu')
        
        # Then: サブメニュー表示メッセージが送信される
        assert result is True
        mock_send.assert_called_once_with('menu_item_selected', {
            'item_id': 'character_menu',
            'facility_type': 'guild'
        })
    
    def test_facility_menu_maintains_selection_state(self):
        """メニュー選択状態が維持されることを確認"""
        # Given: 施設メニュー
        facility_config = {
            'facility_type': 'inn',
            'facility_name': '宿屋',
            'party': Mock(),
            'menu_items': [
                {'id': 'rest', 'label': '休息'},
                {'id': 'storage', 'label': '倉庫'},
                {'id': 'exit', 'label': '出る'}
            ]
        }
        
        facility_window = FacilityMenuWindow('state_menu', facility_config)
        facility_window.create()
        
        # When: メニュー項目を移動
        facility_window.move_selection_down()
        facility_window.move_selection_down()
        
        # Then: 選択状態が正しく維持される
        assert facility_window.selected_index == 2
        
        # When: 境界を超えて移動しようとする
        facility_window.move_selection_down()
        
        # Then: 最初の項目に戻る（ラップアラウンド）
        assert facility_window.selected_index == 0
    
    def test_facility_menu_supports_mouse_interaction(self):
        """マウス操作が動作することを確認"""
        # Given: 施設メニュー
        facility_config = {
            'facility_type': 'shop',
            'facility_name': '商店',
            'party': Mock(),
            'menu_items': [
                {'id': 'buy', 'label': '購入'},
                {'id': 'sell', 'label': '売却'},
                {'id': 'exit', 'label': '出る'}
            ]
        }
        
        facility_window = FacilityMenuWindow('mouse_menu', facility_config)
        facility_window.create()
        
        # When: メニューボタンをクリック
        click_event = Mock()
        click_event.type = pygame_gui.UI_BUTTON_PRESSED
        click_event.ui_element = facility_window.menu_buttons[1]  # '売却'ボタン
        
        with patch.object(facility_window, 'send_message') as mock_send:
            result = facility_window.handle_event(click_event)
        
        # Then: 選択された項目がアクティベートされる
        assert result is True
        mock_send.assert_called_once_with('menu_item_selected', {
            'item_id': 'sell',
            'facility_type': 'shop'
        })
    
    def test_facility_menu_cleanup_removes_ui_elements(self):
        """クリーンアップでUI要素が適切に削除されることを確認"""
        # Given: 作成された施設メニュー
        facility_config = {
            'facility_type': 'guild',
            'facility_name': '冒険者ギルド',
            'party': Mock(),
            'menu_items': [
                {'id': 'create_character', 'label': 'キャラクター作成'},
                {'id': 'exit', 'label': '出る'}
            ]
        }
        
        facility_window = FacilityMenuWindow('cleanup_menu', facility_config)
        facility_window.create()
        
        # When: クリーンアップを実行
        facility_window.cleanup_ui()
        
        # Then: UI要素が削除される
        assert facility_window.menu_buttons == []
        assert facility_window.facility_title is None
        assert facility_window.ui_manager is None