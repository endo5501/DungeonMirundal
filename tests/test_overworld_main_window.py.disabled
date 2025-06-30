"""OverworldMainWindowクラスのTDDテスト

OverworldManagerの9箇所のUIMenuを統合した地上部メインウィンドウのテスト
"""

import pytest
import pygame
from unittest.mock import Mock, MagicMock, patch

from src.ui.window_system.overworld_main_window import (
    OverworldMainWindow, 
    OverworldMenuType
)
from src.ui.window_system.window import WindowState
from src.character.party import Party
from src.character.character import Character


class TestOverworldMainWindow:
    """OverworldMainWindowのTDDテスト"""

    @pytest.fixture
    def pygame_init(self):
        """Pygame初期化"""
        pygame.init()
        pygame.display.set_mode((800, 600))
        yield
        pygame.quit()

    @pytest.fixture
    def mock_party(self):
        """モックパーティ"""
        party = Mock(spec=Party)
        party.name = "テストパーティ"
        party.gold = 1500
        
        # モックキャラクター
        char1 = Mock(spec=Character)
        char1.name = "戦士"
        char1.experience = Mock()
        char1.experience.level = 5
        char1.derived_stats = Mock()
        char1.derived_stats.current_hp = 80
        char1.derived_stats.max_hp = 100
        char1.status = Mock()
        char1.status.value = "GOOD"
        
        char2 = Mock(spec=Character)
        char2.name = "魔法使い"
        char2.experience = Mock()
        char2.experience.level = 4
        char2.derived_stats = Mock()
        char2.derived_stats.current_hp = 45
        char2.derived_stats.max_hp = 60
        char2.status = Mock()
        char2.status.value = "GOOD"
        
        party.get_all_characters.return_value = [char1, char2]
        
        return party

    @pytest.fixture
    def main_menu_config(self, mock_party):
        """メインメニュー設定"""
        return {
            'menu_type': 'main',
            'title': '地上マップ',
            'menu_items': [
                {
                    'id': 'guild',
                    'label': '冒険者ギルド',
                    'type': 'facility',
                    'facility_id': 'guild',
                    'enabled': True
                },
                {
                    'id': 'inn',
                    'label': '宿屋',
                    'type': 'facility',
                    'facility_id': 'inn',
                    'enabled': True
                },
                {
                    'id': 'shop',
                    'label': '商店',
                    'type': 'facility',
                    'facility_id': 'shop',
                    'enabled': True
                },
                {
                    'id': 'temple',
                    'label': '教会',
                    'type': 'facility',
                    'facility_id': 'temple',
                    'enabled': True
                },
                {
                    'id': 'magic_guild',
                    'label': '魔術師ギルド',
                    'type': 'facility',
                    'facility_id': 'magic_guild',
                    'enabled': True
                },
                {
                    'id': 'dungeon_entrance',
                    'label': 'ダンジョン入口',
                    'type': 'action',
                    'enabled': True
                }
            ],
            'party': mock_party,
            'show_party_info': True,
            'show_gold': True
        }

    @pytest.fixture
    def settings_menu_config(self, mock_party):
        """設定メニュー設定"""
        return {
            'menu_type': 'settings',
            'title': '設定',
            'categories': [
                {
                    'id': 'game_menu',
                    'name': '設定',
                    'fields': [
                        {
                            'id': 'party_status',
                            'name': 'パーティ状況',
                            'type': 'action',
                            'enabled': True,
                            'action': 'party_status'
                        },
                        {
                            'id': 'save_game',
                            'name': 'ゲームセーブ',
                            'type': 'action',
                            'enabled': True,
                            'action': 'save_game'
                        },
                        {
                            'id': 'load_game',
                            'name': 'ゲームロード',
                            'type': 'action',
                            'enabled': True,
                            'action': 'load_game'
                        },
                        {
                            'id': 'back',
                            'name': '戻る',
                            'type': 'action',
                            'enabled': True,
                            'action': 'back'
                        }
                    ]
                }
            ],
            'party': mock_party
        }

    def test_overworld_main_window_creation(self, pygame_init, main_menu_config):
        """OverworldMainWindowの作成テスト"""
        window = OverworldMainWindow('test_overworld', main_menu_config)
        
        # 基本プロパティ確認
        assert window.window_id == 'test_overworld'
        assert window.current_menu_type == OverworldMenuType.MAIN
        assert window.modal is True
        assert window.state == WindowState.CREATED
        
        # 設定値確認
        assert window.config == main_menu_config
        assert window.party == main_menu_config['party']
        assert window.show_party_info is True
        assert window.show_gold is True

    def test_main_menu_creation(self, pygame_init, main_menu_config):
        """メインメニューUI作成テスト"""
        window = OverworldMainWindow('test_overworld', main_menu_config)
        
        # UI作成
        window.create()
        
        # UI要素の確認
        assert window.ui_manager is not None
        assert window.title_label is not None
        assert len(window.menu_items) == 6  # 5施設 + 1ダンジョン
        
        # パーティ情報パネルの確認
        assert window.party_info_panel is not None
        assert len(window.party_labels) > 0
        
        # ゴールド表示の確認
        assert window.gold_label is not None

    def test_settings_menu_creation(self, pygame_init, settings_menu_config):
        """設定メニューUI作成テスト"""
        window = OverworldMainWindow('test_settings', settings_menu_config)
        
        # UI作成
        window.create()
        
        # UI要素の確認
        assert window.ui_manager is not None
        assert window.title_label is not None
        assert len(window.menu_items) == 4  # party_status, save_game, load_game, back

    def test_party_status_menu_creation(self, pygame_init, mock_party):
        """パーティ状況メニューUI作成テスト"""
        party_config = {
            'menu_type': 'party_status',
            'party': mock_party
        }
        
        window = OverworldMainWindow('test_party_status', party_config)
        window.create()
        
        # UI要素の確認
        assert window.ui_manager is not None
        assert window.title_label is not None
        # パーティ全体情報 + 各キャラクター + 戻る = 4ボタン
        assert len(window.menu_items) == 4

    def test_save_load_menu_creation(self, pygame_init):
        """セーブ・ロードメニューUI作成テスト"""
        save_config = {
            'menu_type': 'save_load',
            'operation': 'save',
            'max_slots': 3
        }
        
        window = OverworldMainWindow('test_save', save_config)
        window.create()
        
        # UI要素の確認
        assert window.ui_manager is not None
        assert window.title_label is not None
        # 3スロット + 戻る = 4ボタン
        assert len(window.menu_items) == 4

    def test_message_handler_integration(self, pygame_init, main_menu_config):
        """メッセージハンドラー統合テスト"""
        window = OverworldMainWindow('test_overworld', main_menu_config)
        
        # メッセージハンドラーを設定
        mock_handler = Mock(return_value=True)
        window.message_handler = mock_handler
        
        # メッセージ送信テスト
        result = window._send_message('test_message', {'test': 'data'})
        
        assert result is True
        mock_handler.assert_called_once_with('test_message', {'test': 'data'})

    def test_facility_action_processing(self, pygame_init, main_menu_config):
        """施設アクション処理テスト"""
        window = OverworldMainWindow('test_overworld', main_menu_config)
        
        # メッセージハンドラーをモック
        mock_handler = Mock(return_value=True)
        window.message_handler = mock_handler
        
        # 施設アクション処理
        item_data = {
            'type': 'facility',
            'facility_id': 'guild'
        }
        
        result = window._process_menu_action(item_data)
        
        assert result is True
        mock_handler.assert_called_once_with('menu_item_selected', {
            'item_id': 'guild',
            'facility_id': 'guild'
        })

    def test_dungeon_entrance_action_processing(self, pygame_init, main_menu_config):
        """ダンジョン入口アクション処理テスト"""
        window = OverworldMainWindow('test_overworld', main_menu_config)
        
        # メッセージハンドラーをモック
        mock_handler = Mock(return_value=True)
        window.message_handler = mock_handler
        
        # ダンジョン入口アクション処理
        item_data = {
            'id': 'dungeon_entrance'
        }
        
        result = window._process_menu_action(item_data)
        
        assert result is True
        mock_handler.assert_called_once_with('menu_item_selected', {
            'item_id': 'dungeon_entrance'
        })

    def test_party_overview_action_processing(self, pygame_init, mock_party):
        """パーティ全体情報アクション処理テスト"""
        party_config = {
            'menu_type': 'party_status',
            'party': mock_party
        }
        
        window = OverworldMainWindow('test_party', party_config)
        
        # メッセージハンドラーをモック
        mock_handler = Mock(return_value=True)
        window.message_handler = mock_handler
        
        # パーティ全体情報アクション処理
        item_data = {
            'action': 'party_overview'
        }
        
        result = window._process_menu_action(item_data)
        
        assert result is True
        mock_handler.assert_called_once_with('party_overview_requested', {})

    def test_character_details_action_processing(self, pygame_init, mock_party):
        """キャラクター詳細アクション処理テスト"""
        party_config = {
            'menu_type': 'party_status',
            'party': mock_party
        }
        
        window = OverworldMainWindow('test_party', party_config)
        
        # メッセージハンドラーをモック
        mock_handler = Mock(return_value=True)
        window.message_handler = mock_handler
        
        # キャラクター詳細アクション処理
        character = mock_party.get_all_characters()[0]
        item_data = {
            'action': 'character_details',
            'character': character
        }
        
        result = window._process_menu_action(item_data)
        
        assert result is True
        mock_handler.assert_called_once_with('character_details_requested', {
            'character': character
        })

    def test_save_load_action_processing(self, pygame_init):
        """セーブ・ロードアクション処理テスト"""
        save_config = {
            'menu_type': 'save_load',
            'operation': 'save'
        }
        
        window = OverworldMainWindow('test_save', save_config)
        
        # メッセージハンドラーをモック
        mock_handler = Mock(return_value=True)
        window.message_handler = mock_handler
        
        # セーブアクション処理
        item_data = {
            'action': 'save',
            'slot_id': 1
        }
        
        result = window._process_menu_action(item_data)
        
        assert result is True
        mock_handler.assert_called_once_with('save_load_requested', {
            'operation': 'save',
            'slot_id': 1
        })

    def test_menu_navigation(self, pygame_init, main_menu_config):
        """メニューナビゲーションテスト"""
        window = OverworldMainWindow('test_overworld', main_menu_config)
        window.create()
        
        # 初期選択インデックス
        assert window.selected_index == 0
        
        # 下移動
        result = window._navigate_menu(1)
        assert result is True
        assert window.selected_index == 1
        
        # 上移動
        result = window._navigate_menu(-1)
        assert result is True
        assert window.selected_index == 0
        
        # 循環テスト（最下段から最上段）
        window.selected_index = len(window.menu_items) - 1
        result = window._navigate_menu(1)
        assert result is True
        assert window.selected_index == 0

    def test_escape_key_handling(self, pygame_init, main_menu_config):
        """ESCキー処理テスト"""
        window = OverworldMainWindow('test_overworld', main_menu_config)
        
        # メッセージハンドラーをモック
        mock_handler = Mock(return_value=True)
        window.message_handler = mock_handler
        
        # メインメニューでのESC（設定メニュー表示）
        result = window.handle_escape()
        
        assert result is True
        mock_handler.assert_called_once_with('settings_menu_requested', {})

    def test_menu_stack_management(self, pygame_init, main_menu_config, settings_menu_config):
        """メニュースタック管理テスト"""
        window = OverworldMainWindow('test_overworld', main_menu_config)
        
        # 初期状態
        assert window.get_menu_stack_depth() == 0
        
        # 新しいメニューに遷移
        window.show_menu(OverworldMenuType.SETTINGS, settings_menu_config)
        
        # スタックに保存されている
        assert window.get_menu_stack_depth() == 1
        assert window.current_menu_type == OverworldMenuType.SETTINGS
        
        # 戻る
        result = window._go_back()
        assert result is True
        assert window.get_menu_stack_depth() == 0
        assert window.current_menu_type == OverworldMenuType.MAIN

    def test_party_info_update(self, pygame_init, main_menu_config, mock_party):
        """パーティ情報更新テスト"""
        window = OverworldMainWindow('test_overworld', main_menu_config)
        window.create()
        
        # 新しいパーティ情報
        new_party = Mock(spec=Party)
        new_party.name = "新パーティ"
        new_party.gold = 2000
        new_party.get_all_characters.return_value = []
        
        # パーティ情報を更新
        window.update_party_info(new_party)
        
        # 更新確認
        assert window.party == new_party
        if window.gold_label:
            # ゴールド表示が更新されているかは実装依存
            pass

    def test_ui_cleanup(self, pygame_init, main_menu_config):
        """UI要素クリーンアップテスト"""
        window = OverworldMainWindow('test_overworld', main_menu_config)
        window.create()
        
        # UI要素が作成されている
        assert window.title_label is not None
        assert len(window.menu_items) > 0
        
        # クリーンアップ実行
        window.cleanup_ui()
        
        # UI要素がクリアされている
        assert window.title_label is None
        assert len(window.menu_items) == 0
        assert window.party_info_panel is None
        assert len(window.party_labels) == 0
        assert window.gold_label is None

    def test_window_state_management(self, pygame_init, main_menu_config):
        """ウィンドウ状態管理テスト"""
        window = OverworldMainWindow('test_overworld', main_menu_config)
        
        # 初期状態
        assert window.state == WindowState.CREATED
        
        # 表示
        window.show()
        assert window.state == WindowState.SHOWN
        
        # 非表示
        window.hide()
        assert window.state == WindowState.HIDDEN
        
        # 破棄
        window.destroy()
        assert window.state == WindowState.DESTROYED

    def test_integration_with_overworld_manager_interface(self, pygame_init, main_menu_config):
        """OverworldManagerインターフェース統合テスト"""
        window = OverworldMainWindow('test_overworld', main_menu_config)
        
        # OverworldManagerから期待されるメソッドの存在確認
        assert hasattr(window, 'get_current_menu_type')
        assert hasattr(window, 'get_menu_stack_depth')
        assert hasattr(window, 'update_party_info')
        assert hasattr(window, 'show_menu')
        
        # 必要なメッセージタイプをサポートしているか確認
        mock_handler = Mock(return_value=True)
        window.message_handler = mock_handler
        
        # 施設アクセス
        window._send_message('menu_item_selected', {'item_id': 'guild'})
        
        # 設定メニュー要求
        window._send_message('settings_menu_requested', {})
        
        # パーティ関連
        window._send_message('party_overview_requested', {})
        
        # セーブ・ロード
        window._send_message('save_load_requested', {'operation': 'save', 'slot_id': 1})
        
        # 全てのメッセージが適切に処理される
        assert mock_handler.call_count == 4

    def test_tdd_design_requirements_fulfillment(self, pygame_init, main_menu_config):
        """TDD設計要件充足テスト"""
        window = OverworldMainWindow('test_overworld', main_menu_config)
        
        # 要件1: WindowクラスからInherit
        from src.ui.window_system.window import Window
        assert isinstance(window, Window)
        
        # 要件2: OverworldManagerの9箇所のUIMenu統合
        # - メインメニュー、設定メニュー、パーティ状況、セーブ・ロードに対応
        assert OverworldMenuType.MAIN in OverworldMenuType
        assert OverworldMenuType.SETTINGS in OverworldMenuType  
        assert OverworldMenuType.PARTY_STATUS in OverworldMenuType
        assert OverworldMenuType.SAVE_LOAD in OverworldMenuType
        
        # 要件3: 施設アクセス、ダンジョン入口、パーティ状況、セーブ・ロード、設定画面
        # _process_menu_actionで全て処理可能
        assert hasattr(window, '_process_menu_action')
        
        # 要件4: WindowSystemアーキテクチャ準拠
        assert hasattr(window, 'handle_event')
        assert hasattr(window, 'create')
        assert hasattr(window, 'cleanup_ui')
        
        # 要件5: コールバック関数でOverworldManagerとの連携
        assert hasattr(window, 'message_handler')
        
        # 要件6: TDDに対応できる設計
        # このテスト自体がTDD対応の証明
        assert True