"""
Guildの完全FacilityMenuWindow移行テスト

TDDアプローチでGuildクラスをUIMenuから完全にFacilityMenuWindowへ移行する
"""

import pytest
import pygame
from unittest.mock import Mock, patch, MagicMock

from src.overworld.facilities.guild import AdventurersGuild
from src.ui.window_system import WindowManager
from src.ui.window_system.facility_menu_window import FacilityMenuWindow
from src.overworld.base_facility import FacilityType
from src.character.party import Party
from src.character.character import Character


class TestGuildFacilityMenuWindowMigration:
    """Guild完全移行テストクラス"""
    
    @pytest.fixture
    def mock_party(self):
        """モックパーティを作成"""
        party = Mock()
        party.name = "テストパーティ"
        party.gold = 1000
        party.characters = {}
        party.get_member_count = Mock(return_value=0)
        party.get_gold = Mock(return_value=1000)
        party.get_total_max_hp = Mock(return_value=100)
        party.get_total_current_hp = Mock(return_value=100)
        return party
    
    @pytest.fixture
    def guild_facility(self, mock_party):
        """テスト用Guild施設を作成"""
        guild = AdventurersGuild()
        guild.current_party = mock_party
        return guild
    
    def test_guild_uses_facility_menu_window_only(self, guild_facility):
        """GuildがFacilityMenuWindowのみを使用することを確認"""
        # UIMenuのインポートは削除され、FacilityMenuWindowのみを使用
        from src.overworld.facilities.guild import AdventurersGuild
        import inspect
        
        # クラスソースからUIMenuの参照がないことを確認
        source = inspect.getsource(AdventurersGuild)
        assert 'UIMenu' not in source, "GuildクラスはUIMenuを使用してはいけません"
        assert 'FacilityMenuWindow' in source or 'WindowManager' in source, "FacilityMenuWindowまたはWindowManagerを使用する必要があります"
    
    @patch('src.ui.window_system.WindowManager.get_instance')
    def test_guild_show_menu_creates_facility_menu_window(self, mock_window_manager, guild_facility):
        """Guildのshow_menuがFacilityMenuWindowを作成することを確認"""
        # WindowManagerのモック設定
        window_manager = Mock()
        mock_window_manager.return_value = window_manager
        
        # メインメニュー表示をテスト
        guild_facility.show_menu()
        
        # FacilityMenuWindowが作成されることを確認
        window_manager.create_window.assert_called_once()
        args, kwargs = window_manager.create_window.call_args
        
        # 第1引数がFacilityMenuWindowクラスであることを確認
        assert args[0] == FacilityMenuWindow or issubclass(args[0], FacilityMenuWindow)
        
        # 適切なfacility_typeが設定されることを確認
        assert 'facility_type' in kwargs
        assert kwargs['facility_type'] == FacilityType.GUILD.value
    
    def test_guild_menu_configuration(self, guild_facility):
        """Guildメニュー設定が正しく生成されることを確認"""
        # メニュー設定を取得
        menu_config = guild_facility._create_guild_menu_config()
        
        # 必須フィールドの存在確認
        assert 'facility_type' in menu_config
        assert 'facility_name' in menu_config
        assert 'menu_items' in menu_config
        assert 'party' in menu_config
        
        # 施設タイプの確認
        assert menu_config['facility_type'] == FacilityType.GUILD.value
        
        # メニュー項目の確認
        menu_items = menu_config['menu_items']
        assert len(menu_items) >= 4  # キャラクター作成、パーティ編成、キャラクター一覧、クラスチェンジ
        
        # 必須メニュー項目の存在確認
        item_ids = [item['item_id'] for item in menu_items]
        assert 'character_creation' in item_ids
        assert 'party_formation' in item_ids
        assert 'character_list' in item_ids
        assert 'class_change' in item_ids
    
    @patch('src.ui.window_system.WindowManager.get_instance')
    def test_guild_menu_action_handling(self, mock_window_manager, guild_facility):
        """Guildメニューアクション処理が正しく動作することを確認"""
        window_manager = Mock()
        mock_window_manager.return_value = window_manager
        
        # アクションハンドラーのテスト
        test_actions = [
            ('character_creation', guild_facility._show_character_creation),
            ('party_formation', guild_facility._show_party_formation),
            ('character_list', guild_facility._show_character_list),
            ('class_change', guild_facility._show_class_change)
        ]
        
        for action_id, expected_method in test_actions:
            # アクションメッセージを送信
            message_data = {
                'action': action_id,
                'facility_type': FacilityType.GUILD.value
            }
            
            # メソッドが呼び出し可能であることを確認
            assert callable(expected_method), f"{action_id}のハンドラーメソッドが存在しません"
    
    def test_guild_no_ui_menu_dependencies(self, guild_facility):
        """GuildがUIMenuに依存していないことを確認"""
        # guild_facilityインスタンスの属性をチェック
        guild_attrs = dir(guild_facility)
        
        # UIMenu関連の属性がないことを確認
        ui_menu_attrs = [attr for attr in guild_attrs if 'menu' in attr.lower() and 'ui' in attr.lower()]
        
        # menu_stack_managerは段階的移行のため一時的に許可
        allowed_attrs = ['menu_stack_manager']
        forbidden_attrs = [attr for attr in ui_menu_attrs if attr not in allowed_attrs]
        
        assert len(forbidden_attrs) == 0, f"UIMenu関連の属性が残っています: {forbidden_attrs}"
    
    def test_guild_facility_menu_window_integration(self, guild_facility):
        """GuildとFacilityMenuWindowの統合が正しく動作することを確認"""
        # メニュー設定を生成
        menu_config = guild_facility._create_guild_menu_config()
        
        # FacilityMenuWindowが作成可能であることを確認
        try:
            window = FacilityMenuWindow('test_guild_menu', menu_config)
            assert window.facility_type == FacilityType.GUILD
            assert window.menu_items is not None
            assert len(window.menu_items) > 0
        except Exception as e:
            pytest.fail(f"FacilityMenuWindow作成でエラー: {e}")
    
    def test_guild_message_handling_system(self, guild_facility):
        """Guildメッセージハンドリングシステムが正しく動作することを確認"""
        # メッセージハンドラーが存在することを確認
        assert hasattr(guild_facility, 'handle_facility_message'), "メッセージハンドラーが存在しません"
        assert callable(guild_facility.handle_facility_message), "メッセージハンドラーが呼び出し可能ではありません"
        
        # 各種メッセージタイプのハンドリング確認
        test_messages = [
            ('menu_item_selected', {'item_id': 'character_creation'}),
            ('menu_item_selected', {'item_id': 'party_formation'}),
            ('facility_exit_requested', {'facility_type': FacilityType.GUILD.value})
        ]
        
        for message_type, data in test_messages:
            try:
                # メッセージハンドリングが例外を発生させないことを確認
                result = guild_facility.handle_facility_message(message_type, data)
                assert isinstance(result, bool), "メッセージハンドラーはboolを返す必要があります"
            except Exception as e:
                pytest.fail(f"メッセージハンドリングでエラー: {message_type}, {data} -> {e}")


class TestGuildMigrationRequirements:
    """Guild移行要件テストクラス"""
    
    def test_guild_must_have_facility_menu_config_method(self):
        """GuildがFacilityMenuWindow用設定メソッドを持つことを確認"""
        guild = AdventurersGuild()
        assert hasattr(guild, '_create_guild_menu_config'), "Guild設定メソッドが存在しません"
        assert callable(guild._create_guild_menu_config), "Guild設定メソッドが呼び出し可能ではありません"
    
    def test_guild_must_have_message_handler(self):
        """GuildがFacilityMenuWindow用メッセージハンドラーを持つことを確認"""
        guild = AdventurersGuild()
        assert hasattr(guild, 'handle_facility_message'), "メッセージハンドラーが存在しません"
        assert callable(guild.handle_facility_message), "メッセージハンドラーが呼び出し可能ではありません"
    
    def test_guild_show_menu_must_use_window_manager(self):
        """Guildのshow_menuがWindowManagerを使用することを確認"""
        guild = AdventurersGuild()
        
        # show_menuメソッドのソースコードを取得
        import inspect
        source = inspect.getsource(guild.show_menu)
        
        # WindowManagerの使用を確認
        assert 'WindowManager' in source, "show_menuでWindowManagerを使用する必要があります"
        assert 'FacilityMenuWindow' in source, "show_menuでFacilityMenuWindowを使用する必要があります"
    
    def test_guild_character_creation_must_integrate_with_window_system(self):
        """Guildのキャラクター作成が新ウィンドウシステムと統合されることを確認"""
        guild = AdventurersGuild()
        
        # キャラクター作成メソッドのソースを確認
        import inspect
        source = inspect.getsource(guild._show_character_creation)
        
        # 新ウィンドウシステムとの統合を確認
        # WindowManagerまたはウィンドウスタック管理の使用を確認
        has_window_integration = (
            'WindowManager' in source or 
            'window_manager' in source or
            'show_window' in source
        )
        
        assert has_window_integration, "キャラクター作成が新ウィンドウシステムと統合されていません"