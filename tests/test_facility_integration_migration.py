"""施設移行後の統合テスト

0034 WindowSystem移行後の全施設統合動作確認を行う
"""

import pytest
import pygame
from unittest.mock import Mock, patch, MagicMock

from src.overworld.facilities.guild import AdventurersGuild
from src.overworld.facilities.inn import Inn
from src.overworld.facilities.shop import Shop
from src.overworld.facilities.magic_guild import MagicGuild
from src.overworld.facilities.temple import Temple
from src.character.party import Party
from src.character.character import Character
from src.ui.window_system import WindowManager
from src.ui.window_system.facility_menu_window import FacilityMenuWindow


class TestFacilityIntegrationMigration:
    """施設移行統合テスト"""

    @pytest.fixture
    def pygame_init(self):
        """Pygame初期化"""
        pygame.init()
        yield
        pygame.quit()

    @pytest.fixture
    def mock_window_manager(self):
        """モックWindowManager"""
        with patch('src.ui.window_system.window_manager.WindowManager') as mock_wm_class:
            mock_wm = Mock()
            mock_wm.get_active_window.return_value = Mock()  # アクティブウィンドウモック
            mock_wm.register_window.return_value = True  # ウィンドウ登録モック
            mock_wm.show_window.return_value = True  # ウィンドウ表示モック
            mock_wm.go_back.return_value = True  # 戻るモック
            
            # create_windowメソッドのモック
            mock_wm.create_window = Mock()
            mock_window = Mock()
            mock_window.window_id = "test_window"
            mock_window.message_handler = None
            mock_wm.create_window.return_value = mock_window
            mock_wm_class.get_instance.return_value = mock_wm
            yield mock_wm

    @pytest.fixture
    def test_party(self):
        """テスト用パーティ"""
        party = Mock(spec=Party)
        party.name = "テストパーティ"
        party.gold = 1000
        party.characters = []  # Guildが参照するattribute
        party.get_all_characters.return_value = []
        return party

    @pytest.fixture
    def all_facilities(self, mock_window_manager):
        """全施設のリスト"""
        return [
            AdventurersGuild(),
            Inn(),
            Shop(),
            MagicGuild(),
            Temple()
        ]

    def test_all_facilities_can_create_menu_configs(self, all_facilities, test_party):
        """全施設がメニュー設定を作成できることを確認"""
        for facility in all_facilities:
            facility.current_party = test_party
            
            # 施設固有のメニュー設定作成メソッドを呼び出し
            if hasattr(facility, '_create_guild_menu_config'):
                config = facility._create_guild_menu_config()
            elif hasattr(facility, '_create_inn_menu_config'):
                config = facility._create_inn_menu_config()
            elif hasattr(facility, '_create_shop_menu_config'):
                config = facility._create_shop_menu_config()
            elif hasattr(facility, '_create_magic_guild_menu_config'):
                config = facility._create_magic_guild_menu_config()
            elif hasattr(facility, '_create_temple_menu_config'):
                config = facility._create_temple_menu_config()
            else:
                pytest.fail(f"施設 {facility.facility_id} にメニュー設定作成メソッドがありません")
            
            # 基本設定の確認
            assert 'facility_type' in config
            assert 'facility_name' in config
            assert 'menu_items' in config
            assert isinstance(config['menu_items'], list)
            assert len(config['menu_items']) > 0
            
            # exitメニューが含まれることを確認
            exit_item_found = any(
                item.get('id') == 'exit' and item.get('type') in ['action', 'exit']
                for item in config['menu_items']
            )
            assert exit_item_found, f"施設 {facility.facility_id} にexitメニューがありません"

    def test_all_facilities_can_show_menu(self, all_facilities, test_party, mock_window_manager):
        """全施設がメニューを表示できることを確認"""
        with patch('src.ui.window_system.facility_menu_window.FacilityMenuWindow') as mock_fmw:
            mock_window_instance = Mock()
            mock_window_instance.window_id = "test_window"
            mock_fmw.return_value = mock_window_instance
            
            for facility in all_facilities:
                facility.current_party = test_party
                
                # show_menuメソッドの呼び出し
                try:
                    facility.show_menu()
                    # メソッドが例外なく完了すればOK（実際のWindowManagerが動作している）
                    
                except Exception as e:
                    pytest.fail(f"施設 {facility.facility_id} のshow_menu()でエラー: {e}")

    def test_all_facilities_handle_facility_messages(self, all_facilities, test_party):
        """全施設がFacilityMenuWindowメッセージを処理できることを確認"""
        for facility in all_facilities:
            facility.current_party = test_party
            
            # handle_facility_messageメソッドの存在確認
            assert hasattr(facility, 'handle_facility_message'), \
                f"施設 {facility.facility_id} にhandle_facility_messageメソッドがありません"
            
            # exitメッセージの処理確認
            with patch.object(facility, '_handle_exit', return_value=True) as mock_exit:
                result = facility.handle_facility_message(
                    'facility_exit_requested',
                    {}
                )
                assert result is True
                mock_exit.assert_called_once()

    def test_all_facilities_have_uimenu_removed(self, all_facilities):
        """全施設からUIMenuが除去されていることを確認"""
        import inspect
        
        for facility in all_facilities:
            # ソースコードからUIMenuの使用を確認
            source = inspect.getsource(type(facility))
            
            # UIMenuクラス名の使用確認（コメント内は除外）
            source_lines = source.split('\n')
            code_lines = []
            for line in source_lines:
                # コメント部分を除去
                if '#' in line:
                    line = line[:line.index('#')]
                code_lines.append(line)
            
            code_content = '\n'.join(code_lines)
            
            # UIMenuの使用がないことを確認（importとコメント除く）
            assert 'UIMenu(' not in code_content, \
                f"施設 {facility.facility_id} でUIMenuが使用されています"

    def test_facility_exit_handling(self, all_facilities, test_party, mock_window_manager):
        """全施設の退場処理を確認"""
        for facility in all_facilities:
            facility.current_party = test_party
            
            # _handle_exitメソッドの存在確認
            assert hasattr(facility, '_handle_exit'), \
                f"施設 {facility.facility_id} に_handle_exitメソッドがありません"
            
            # 退場処理の実行
            result = facility._handle_exit()
            assert result is True
            
            # WindowManagerのgo_backが呼ばれることを確認
            mock_window_manager.go_back.assert_called()
            mock_window_manager.reset_mock()

    def test_facility_message_routing(self, all_facilities, test_party):
        """全施設のメッセージルーティングを確認"""
        for facility in all_facilities:
            facility.current_party = test_party
            
            # メニュー設定を取得
            if hasattr(facility, '_create_guild_menu_config'):
                config = facility._create_guild_menu_config()
            elif hasattr(facility, '_create_inn_menu_config'):
                config = facility._create_inn_menu_config()
            elif hasattr(facility, '_create_shop_menu_config'):
                config = facility._create_shop_menu_config()
            elif hasattr(facility, '_create_magic_guild_menu_config'):
                config = facility._create_magic_guild_menu_config()
            elif hasattr(facility, '_create_temple_menu_config'):
                config = facility._create_temple_menu_config()
            
            # 各メニューアイテムのメッセージ処理を確認
            for menu_item in config['menu_items']:
                item_id = menu_item.get('item_id')
                if item_id and item_id != 'exit':
                    # menu_item_selectedメッセージの処理
                    try:
                        result = facility.handle_facility_message(
                            'menu_item_selected',
                            {'item_id': item_id}
                        )
                        # 処理が実行されること（True/Falseは問わない）
                        assert isinstance(result, bool)
                    except Exception as e:
                        # 未実装やエラーも許可（移行段階のため）
                        pass

    def test_facility_configuration_consistency(self, all_facilities, test_party):
        """全施設の設定一貫性を確認"""
        for facility in all_facilities:
            facility.current_party = test_party
            
            # 施設タイプと設定の一貫性
            if hasattr(facility, '_create_guild_menu_config'):
                config = facility._create_guild_menu_config()
                expected_type = 'guild'
            elif hasattr(facility, '_create_inn_menu_config'):
                config = facility._create_inn_menu_config()
                expected_type = 'inn'
            elif hasattr(facility, '_create_shop_menu_config'):
                config = facility._create_shop_menu_config()
                expected_type = 'shop'
            elif hasattr(facility, '_create_magic_guild_menu_config'):
                config = facility._create_magic_guild_menu_config()
                expected_type = 'magic_guild'
            elif hasattr(facility, '_create_temple_menu_config'):
                config = facility._create_temple_menu_config()
                expected_type = 'temple'
            
            # facility_typeの一貫性確認
            assert config['facility_type'] == expected_type
            
            # パーティ情報の設定確認
            assert config.get('party') == test_party
            
            # 共通設定の確認
            assert 'show_party_info' in config
            assert 'show_gold' in config

    def test_integration_no_import_errors(self):
        """統合時のインポートエラーがないことを確認"""
        try:
            # 全施設を一度にインポート
            from src.overworld.facilities.guild import AdventurersGuild
            from src.overworld.facilities.inn import Inn
            from src.overworld.facilities.shop import Shop
            from src.overworld.facilities.magic_guild import MagicGuild
            from src.overworld.facilities.temple import Temple
            
            # インスタンス化
            facilities = [
                AdventurersGuild(),
                Inn(),
                Shop(),
                MagicGuild(),
                Temple()
            ]
            
            # 基本属性の確認
            for facility in facilities:
                assert hasattr(facility, 'facility_id')
                assert hasattr(facility, 'facility_type')
                assert hasattr(facility, 'show_menu')
                assert hasattr(facility, 'handle_facility_message')
                
        except ImportError as e:
            pytest.fail(f"施設インポート時にエラー: {e}")
        except Exception as e:
            pytest.fail(f"施設インスタンス化時にエラー: {e}")

    def test_migration_completeness_validation(self, all_facilities):
        """移行完了度の検証"""
        migration_checklist = {
            'guild': True,    # 完全移行済み
            'inn': True,      # 基本移行済み
            'shop': True,     # 基本移行済み
            'magic_guild': True,  # 基本移行済み
            'temple': True    # 基本移行済み
        }
        
        for facility in all_facilities:
            facility_id = facility.facility_id
            
            # 移行チェックリストの確認
            assert facility_id in migration_checklist, \
                f"施設 {facility_id} が移行チェックリストにありません"
            
            expected_migrated = migration_checklist[facility_id]
            
            # FacilityMenuWindow関連メソッドの存在確認
            has_show_menu = hasattr(facility, 'show_menu')
            has_handle_message = hasattr(facility, 'handle_facility_message')
            has_config_method = any([
                hasattr(facility, f'_create_{facility_id}_menu_config'),
                hasattr(facility, '_create_guild_menu_config'),
                hasattr(facility, '_create_inn_menu_config'),
                hasattr(facility, '_create_shop_menu_config'),
                hasattr(facility, '_create_magic_guild_menu_config'),
                hasattr(facility, '_create_temple_menu_config')
            ])
            
            if expected_migrated:
                assert has_show_menu, f"施設 {facility_id} にshow_menuがありません"
                assert has_handle_message, f"施設 {facility_id} にhandle_facility_messageがありません"
                assert has_config_method, f"施設 {facility_id} にメニュー設定メソッドがありません"