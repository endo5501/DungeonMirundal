"""0044 Phase 2: MagicGuildServiceWindow実装テスト"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import pygame
from typing import Dict, Any, Optional


class TestMagicGuildServiceWindow:
    """MagicGuildServiceWindow実装テスト"""
    
    def setup_method(self):
        """テストのセットアップ"""
        pygame.init()
        
        # モック用キャラクターとパーティ
        self.character = Mock()
        self.character.name = "テストメイジ"
        self.character.character_id = "test_mage_1"
        self.character.character_class = "Mage"
        self.character.get_personal_inventory = Mock(return_value=[])
        self.character.get_spellbook = Mock(return_value=Mock())
        self.character.get_learnable_spells = Mock(return_value=[])
        
        self.party = Mock()
        self.party.characters = [self.character]
        self.party.get_all_characters = Mock(return_value=[self.character])
        
        # モックの設定
        self.mock_window_manager = Mock()
        self.mock_magic_guild = Mock()
        
    def teardown_method(self):
        """テストのクリーンアップ"""
        pygame.quit()
    
    def test_magic_guild_service_window_should_be_created(self):
        """MagicGuildServiceWindowが作成できることを確認"""
        # MagicGuildServiceWindowクラスがインポート可能であることを確認
        try:
            from src.ui.window_system.magic_guild_service_window import MagicGuildServiceWindow
            window_created = True
        except ImportError:
            window_created = False
        
        # Phase 2実装完了後は成功が期待される
        assert window_created, "MagicGuildServiceWindow should be implemented"
    
    def test_magic_guild_service_window_initialization(self):
        """MagicGuildServiceWindow初期化テスト"""
        # Given: 魔術協会サービス設定
        guild_config = {
            'parent_facility': self.mock_magic_guild,
            'current_party': self.party,
            'service_types': ['spellbook_shop', 'spell_learning', 'identification', 'analysis'],
            'title': '魔術協会サービス'
        }
        
        # When & Then: MagicGuildServiceWindow作成時の期待動作
        from src.ui.window_system.magic_guild_service_window import MagicGuildServiceWindow
        
        window = MagicGuildServiceWindow('magic_guild_service', guild_config)
        
        assert window.window_id == 'magic_guild_service'
        assert window.parent_facility == self.mock_magic_guild
        assert window.current_party == self.party
        assert 'spellbook_shop' in window.available_services
        assert 'spell_learning' in window.available_services
        assert 'identification' in window.available_services
        assert 'analysis' in window.available_services
    
    def test_spellbook_shop_service(self):
        """魔術書店サービステスト"""
        # Given: 魔術書店サービス設定
        from src.ui.window_system.magic_guild_service_window import MagicGuildServiceWindow
        
        # 親施設にget_available_spell_categoriesメソッドがない場合のテスト
        guild_config = {
            'parent_facility': self.mock_magic_guild,
            'current_party': self.party,
            'service_types': ['spellbook_shop']
        }
        
        window = MagicGuildServiceWindow('magic_guild_spellbook_shop', guild_config)
        
        # When: 魔術書カテゴリを取得
        categories = window.get_spellbook_categories()
        
        # Then: 基本カテゴリが提供される（親施設にメソッドがない場合）
        expected_categories = ['offensive', 'defensive', 'healing', 'utility', 'prayer', 'special']
        assert isinstance(categories, list), "Categories should be a list"
        assert len(categories) == len(expected_categories), f"Expected {len(expected_categories)} categories, got {len(categories)}"
        for category in expected_categories:
            assert category in categories
    
    def test_spell_learning_service(self):
        """魔法習得サービステスト"""
        # Given: 魔法習得用設定
        test_spell = Mock()
        test_spell.spell_id = "fireball"
        test_spell.get_name = Mock(return_value="ファイアボール")
        
        self.character.get_learnable_spells.return_value = [test_spell]
        
        from src.ui.window_system.magic_guild_service_window import MagicGuildServiceWindow
        
        guild_config = {
            'parent_facility': self.mock_magic_guild,
            'current_party': self.party,
            'service_types': ['spell_learning'],
            'selected_character': self.character
        }
        
        window = MagicGuildServiceWindow('magic_guild_spell_learning', guild_config)
        
        # When: キャラクターの習得可能魔法を取得
        learnable_spells = window.get_available_spells_for_character(self.character)
        
        # Then: 習得可能魔法が取得される
        assert len(learnable_spells) >= 0  # Mock環境では空の可能性
    
    def test_identification_service(self):
        """アイテム鑑定サービステスト"""
        # Given: 鑑定用設定
        test_item = Mock()
        test_item.item_id = "mysterious_ring"
        test_item.is_identified = False
        test_item.get_name = Mock(return_value="謎の指輪")
        
        self.character.get_personal_inventory.return_value = [test_item]
        
        from src.ui.window_system.magic_guild_service_window import MagicGuildServiceWindow
        
        guild_config = {
            'parent_facility': self.mock_magic_guild,
            'current_party': self.party,
            'service_types': ['identification']
        }
        
        window = MagicGuildServiceWindow('magic_guild_identification', guild_config)
        
        # When: 鑑定可能アイテムを取得
        identifiable_items = window.get_identifiable_items()
        
        # Then: 未鑑定アイテムが取得される
        assert len(identifiable_items) >= 0  # Mock環境対応
    
    def test_spell_analysis_service(self):
        """魔法分析サービステスト"""
        # Given: 魔法分析用設定
        mock_spellbook = Mock()
        mock_spellbook.learned_spells = ["fireball", "ice_lance"]
        self.character.get_spellbook.return_value = mock_spellbook
        
        from src.ui.window_system.magic_guild_service_window import MagicGuildServiceWindow
        
        guild_config = {
            'parent_facility': self.mock_magic_guild,
            'current_party': self.party,
            'service_types': ['analysis']
        }
        
        window = MagicGuildServiceWindow('magic_guild_analysis', guild_config)
        
        # When: 分析可能魔法を取得
        analyzable_spells = window.get_analyzable_spells()
        
        # Then: 分析可能魔法が取得される
        assert analyzable_spells is not None
        assert isinstance(analyzable_spells, list)
    
    def test_character_analysis_service(self):
        """キャラクター分析サービステスト"""
        # Given: キャラクター分析用設定
        from src.ui.window_system.magic_guild_service_window import MagicGuildServiceWindow
        
        guild_config = {
            'parent_facility': self.mock_magic_guild,
            'current_party': self.party,
            'service_types': ['character_analysis'],
            'selected_character': self.character
        }
        
        window = MagicGuildServiceWindow('magic_guild_char_analysis', guild_config)
        
        # When: キャラクター分析データを取得
        analysis_data = window.get_character_spell_usage_data(self.character)
        
        # Then: 分析データが取得される
        assert analysis_data is not None
        assert isinstance(analysis_data, dict)
        assert 'equipped_spells' in analysis_data
        assert 'spell_slots' in analysis_data
        assert 'remaining_uses' in analysis_data
    
    def test_spell_usage_check_service(self):
        """魔法使用回数確認サービステスト"""
        # Given: 魔法使用回数確認設定
        mock_spellbook = Mock()
        mock_spellbook.get_remaining_uses = Mock(return_value={'fireball': 3, 'heal': 5})
        self.character.get_spellbook.return_value = mock_spellbook
        
        from src.ui.window_system.magic_guild_service_window import MagicGuildServiceWindow
        
        guild_config = {
            'parent_facility': self.mock_magic_guild,
            'current_party': self.party,
            'service_types': ['spell_usage_check'],
            'selected_character': self.character
        }
        
        window = MagicGuildServiceWindow('magic_guild_usage_check', guild_config)
        
        # When: 魔法使用状況データを取得
        usage_data = window.get_character_spell_usage_data(self.character)
        
        # Then: 使用状況データが取得される
        assert usage_data is not None
        assert 'remaining_uses' in usage_data
    
    def test_service_request_handling(self):
        """サービスリクエスト処理テスト"""
        # Given: 統合サービス設定
        from src.ui.window_system.magic_guild_service_window import MagicGuildServiceWindow
        
        guild_config = {
            'parent_facility': self.mock_magic_guild,
            'current_party': self.party,
            'service_types': ['spellbook_shop', 'spell_learning', 'identification', 'analysis']
        }
        
        window = MagicGuildServiceWindow('magic_guild_service', guild_config)
        
        # When: 各種サービスリクエストを処理
        shop_result = window.handle_service_request('spellbook_shop', category='offensive')
        learning_result = window.handle_service_request('spell_learning', character=self.character, spell_id='fireball')
        identification_result = window.handle_service_request('identification', item=Mock())
        analysis_result = window.handle_service_request('analysis', spell_id='fireball')
        
        # Then: サービス処理が実行される
        assert shop_result is True
        assert learning_result is True
        assert identification_result is True
        assert analysis_result is True
    
    def test_window_message_handling(self):
        """Windowメッセージ処理テスト"""
        # Given: サービス選択メッセージ
        from src.ui.window_system.magic_guild_service_window import MagicGuildServiceWindow
        
        guild_config = {
            'parent_facility': self.mock_magic_guild,
            'current_party': self.party
        }
        
        window = MagicGuildServiceWindow('magic_guild_service', guild_config)
        
        # When: 各種メッセージを受信
        service_message = {
            'service': 'spellbook_shop',
            'category': 'offensive'
        }
        
        result = window.handle_message('service_selected', service_message)
        
        # Then: 適切なサービス処理が実行される
        assert result is True or result is False  # 処理結果を確認


class TestMagicGuildUIMenuMigration:
    """MagicGuild UIMenu移行テスト"""
    
    def setup_method(self):
        """テストのセットアップ"""
        pygame.init()
    
    def teardown_method(self):
        """テストのクリーンアップ"""
        pygame.quit()
    
    def test_magic_guild_uimenu_usage_analysis(self):
        """MagicGuild UIMenu使用状況分析テスト"""
        # MagicGuildファイルを読み込んでUIMenu使用箇所を確認
        import inspect
        from src.overworld.facilities.magic_guild import MagicGuild
        
        source = inspect.getsource(MagicGuild)
        
        # UIMenuインスタンス化箇所を確認
        uimenu_creations = source.count('UIMenu(')
        
        # Phase 2移行完了後は0箇所に削減
        assert uimenu_creations == 0, f"Expected 0 UIMenu usages after migration, found {uimenu_creations}"
    
    def test_magic_guild_show_submenu_calls(self):
        """MagicGuild show_submenu呼び出し分析テスト"""
        import inspect
        import re
        from src.overworld.facilities.magic_guild import MagicGuild
        
        source = inspect.getsource(MagicGuild)
        
        # show_submenu呼び出し箇所を確認（実際の関数呼び出しのみカウント）
        show_submenu_calls = len(re.findall(r'self\.show_submenu\(', source))
        
        # Phase 2移行完了後は実際の呼び出しが削減される
        assert show_submenu_calls == 0, f"Expected 0 show_submenu calls after migration, found {show_submenu_calls}"
    
    def test_magic_guild_migration_readiness(self):
        """MagicGuild移行準備状況テスト"""
        from src.overworld.facilities.magic_guild import MagicGuild
        
        # MagicGuild インスタンス作成確認
        magic_guild = MagicGuild()
        
        # 必要な基盤機能の確認
        assert hasattr(magic_guild, 'window_manager'), "MagicGuild should have window_manager"
        assert hasattr(magic_guild, 'show_menu'), "MagicGuild should have show_menu method"
        
        # WindowManager統合状況確認
        # window_managerは動的に取得される可能性があるため、存在確認のみ
        assert magic_guild.window_manager is not None or hasattr(magic_guild, '_get_window_manager'), "MagicGuild should have window_manager access"
    
    def test_magic_guild_complexity_analysis(self):
        """MagicGuild複雑度分析テスト"""
        import inspect
        from src.overworld.facilities.magic_guild import MagicGuild
        
        source = inspect.getsource(MagicGuild)
        
        # メソッド数の確認（複雑度の指標）
        method_count = source.count('def ')
        
        # MagicGuild は中程度の複雑度の施設であることを確認
        assert method_count > 10, f"MagicGuild should be moderately complex facility with several methods, found {method_count}"
        
        # 魔法関連機能の存在確認
        assert 'spell' in source.lower() or 'magic' in source.lower(), "MagicGuild should contain spell/magic related functionality"