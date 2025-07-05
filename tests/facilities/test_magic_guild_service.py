"""魔法ギルドサービスのテスト"""

import pytest
from unittest.mock import Mock, MagicMock, patch
import sys

# 必要なモジュールをモック
mock_modules = [
    'game', 'game.game', 'game.party', 'game.character', 'game.items', 'game.items.item',
    'models', 'models.character_model', 'models.item_model', 
    'models.party_model', 'models.spell_model',
    'ui', 'ui.window_system', 'ui.window_system.party_formation_window',
    'character', 'character.character', 'character.character_manager'
]

for module in mock_modules:
    sys.modules[module] = Mock()

from src.facilities.services.magic_guild_service import MagicGuildService
from src.facilities.core.service_result import ServiceResult, ResultType
from src.facilities.core.facility_service import MenuItem


class TestMagicGuildService:
    """魔法ギルドサービスのテストクラス"""
    
    @pytest.fixture
    def magic_guild_service(self):
        """魔法ギルドサービスのフィクスチャ"""
        with patch('src.facilities.services.magic_guild_service.Game') as mock_game_class:
            # モックゲームインスタンスを設定
            mock_game = Mock()
            mock_game_class.get_instance.return_value = mock_game
            
            service = MagicGuildService()
            yield service
    
    @pytest.fixture
    def sample_party(self):
        """サンプルパーティのフィクスチャ"""
        party = Mock()
        party.name = "TestParty"
        party.gold = 1000
        party.members = []
        return party
    
    @pytest.fixture
    def wizard_character(self):
        """魔法使いキャラクターのフィクスチャ"""
        char = Mock()
        char.id = "char1"
        char.name = "Wizard"
        char.level = 5
        char.character_class = "wizard"
        char.is_alive.return_value = True
        char.known_spells = []
        return char
    
    @pytest.fixture
    def advanced_wizard(self):
        """上級魔法使いキャラクターのフィクスチャ"""
        char = Mock()
        char.id = "char2"
        char.name = "Archmage"
        char.level = 15
        char.character_class = "wizard"
        char.intelligence = 18
        char.is_alive.return_value = True
        char.known_spells = ["fire_bolt", "ice_spike"]
        return char
    
    def test_get_menu_items(self, magic_guild_service):
        """メニュー項目取得のテスト"""
        # テスト実行
        items = magic_guild_service.get_menu_items()
        
        # 検証
        assert len(items) == 5  # 5つのメニュー項目
        
        # メニュー項目の存在確認
        item_ids = [item.id for item in items]
        assert "learn_spells" in item_ids
        assert "identify_magic" in item_ids
        assert "analyze_magic" in item_ids
        assert "magic_research" in item_ids
        assert "exit" in item_ids
        
        # 各項目の型確認
        for item in items:
            assert isinstance(item, MenuItem)
            assert item.label is not None
            assert item.description is not None
    
    def test_spell_learning_cost(self, magic_guild_service):
        """魔法学習コストのテスト"""
        # レベル1の魔法
        assert magic_guild_service.spell_learning_costs[1] == 100
        
        # レベル5の魔法
        assert magic_guild_service.spell_learning_costs[5] == 1500
        
        # レベル9の魔法
        assert magic_guild_service.spell_learning_costs[9] == 4500
    
    def test_can_learn_spells_check(self, magic_guild_service, wizard_character):
        """魔法学習可能チェックのテスト"""
        # 魔法使いは学習可能
        assert magic_guild_service._can_learn_spells(wizard_character) is True
        
        # 戦士は学習不可
        warrior = Mock()
        warrior.character_class = "warrior"
        assert magic_guild_service._can_learn_spells(warrior) is False
    
    def test_max_spell_level_calculation(self, magic_guild_service, wizard_character):
        """最大魔法レベル計算のテスト"""
        # レベル5のキャラクター
        max_level = magic_guild_service._get_max_spell_level(wizard_character)
        assert max_level == 3
        
        # レベル15のキャラクター
        wizard_character.level = 15
        max_level = magic_guild_service._get_max_spell_level(wizard_character)
        assert max_level == 8
    
    def test_get_eligible_learners(self, magic_guild_service, sample_party, wizard_character):
        """学習可能キャラクター取得のテスト"""
        sample_party.members = [wizard_character]
        magic_guild_service.party = sample_party
        
        # テスト実行
        result = magic_guild_service.execute_action("learn_spells", {})
        
        # 検証
        assert result.success is True
        assert "characters" in result.data
        assert len(result.data["characters"]) == 1
        assert result.data["characters"][0]["name"] == "Wizard"
    
    def test_get_learnable_spells(self, magic_guild_service, sample_party, wizard_character):
        """学習可能魔法取得のテスト"""
        sample_party.members = [wizard_character]
        magic_guild_service.party = sample_party
        
        # テスト実行
        result = magic_guild_service.execute_action("learn_spells", {
            "character_id": "char1"
        })
        
        # 検証
        assert result.success is True
        assert "spells" in result.data
        assert len(result.data["spells"]) > 0
        assert result.data["party_gold"] == 1000
    
    def test_spell_learning_confirmation(self, magic_guild_service, sample_party, wizard_character):
        """魔法学習確認のテスト"""
        sample_party.members = [wizard_character]
        magic_guild_service.party = sample_party
        
        # テスト実行
        result = magic_guild_service.execute_action("learn_spells", {
            "character_id": "char1",
            "spell_id": "fire_bolt"
        })
        
        # 検証
        assert result.success is True
        assert result.result_type == ResultType.CONFIRM
        assert "学習しますか" in result.message
    
    def test_spell_learning_execution(self, magic_guild_service, sample_party, wizard_character):
        """魔法学習実行のテスト"""
        sample_party.members = [wizard_character]
        magic_guild_service.party = sample_party
        initial_gold = sample_party.gold
        
        # テスト実行
        result = magic_guild_service.execute_action("learn_spells", {
            "character_id": "char1",
            "spell_id": "fire_bolt",
            "confirmed": True
        })
        
        # 検証
        assert result.success is True
        assert result.result_type == ResultType.SUCCESS
        assert "習得しました" in result.message
        assert "fire_bolt" in wizard_character.known_spells
        assert sample_party.gold < initial_gold
    
    def test_identify_magic_cost(self, magic_guild_service):
        """魔法鑑定コストのテスト"""
        assert magic_guild_service.identify_magic_cost == 200
    
    def test_identify_confirmation(self, magic_guild_service, sample_party):
        """鑑定確認のテスト"""
        magic_guild_service.party = sample_party
        
        # テスト実行
        result = magic_guild_service.execute_action("identify_magic", {
            "item_id": "unknown_staff"
        })
        
        # 検証
        assert result.success is True
        assert result.result_type == ResultType.CONFIRM
        assert "鑑定を行いますか" in result.message
        assert result.data["cost"] == 200
    
    def test_identify_execution(self, magic_guild_service, sample_party):
        """鑑定実行のテスト"""
        magic_guild_service.party = sample_party
        initial_gold = sample_party.gold
        
        # テスト実行
        result = magic_guild_service.execute_action("identify_magic", {
            "item_id": "unknown_staff",
            "confirmed": True
        })
        
        # 検証
        assert result.success is True
        assert result.result_type == ResultType.SUCCESS
        assert "鑑定完了" in result.message
        assert sample_party.gold == initial_gold - 200
    
    def test_analyze_cost_calculation(self, magic_guild_service):
        """魔法分析コスト計算のテスト"""
        # レベル1魔法の分析
        cost = magic_guild_service.analyze_cost_per_level * 1
        assert cost == 50
        
        # レベル5魔法の分析
        cost = magic_guild_service.analyze_cost_per_level * 5
        assert cost == 250
    
    def test_get_characters_with_spells(self, magic_guild_service, sample_party, advanced_wizard):
        """魔法を持つキャラクター取得のテスト"""
        sample_party.members = [advanced_wizard]
        magic_guild_service.party = sample_party
        
        # テスト実行
        result = magic_guild_service.execute_action("analyze_magic", {})
        
        # 検証
        assert result.success is True
        assert "characters" in result.data
        assert len(result.data["characters"]) == 1
        assert result.data["characters"][0]["spell_count"] == 2
    
    def test_analyze_execution(self, magic_guild_service, sample_party, advanced_wizard):
        """魔法分析実行のテスト"""
        sample_party.members = [advanced_wizard]
        magic_guild_service.party = sample_party
        initial_gold = sample_party.gold
        
        # テスト実行
        result = magic_guild_service.execute_action("analyze_magic", {
            "character_id": "char2",
            "spell_id": "fire_bolt",
            "confirmed": True
        })
        
        # 検証
        assert result.success is True
        assert result.result_type == ResultType.SUCCESS
        assert "詳細分析結果" in result.message
        assert sample_party.gold < initial_gold
    
    def test_is_advanced_caster(self, magic_guild_service, wizard_character, advanced_wizard):
        """上級魔法使いチェックのテスト"""
        # レベル5は上級でない
        assert magic_guild_service._is_advanced_caster(wizard_character) is False
        
        # レベル15は上級
        assert magic_guild_service._is_advanced_caster(advanced_wizard) is True
    
    def test_research_researcher_selection(self, magic_guild_service, sample_party, advanced_wizard):
        """研究者選択のテスト"""
        sample_party.members = [advanced_wizard]
        magic_guild_service.party = sample_party
        
        # テスト実行
        result = magic_guild_service.execute_action("magic_research", {
            "step": "select_researcher"
        })
        
        # 検証
        assert result.success is True
        assert "researchers" in result.data
        assert len(result.data["researchers"]) == 1
        assert result.data["researchers"][0]["name"] == "Archmage"
    
    def test_has_unidentified_magic_items(self, magic_guild_service, sample_party):
        """未鑑定アイテムチェックのテスト"""
        magic_guild_service.party = sample_party
        
        # 仮実装のため常にTrue
        assert magic_guild_service._has_unidentified_magic_items() is True
    
    def test_exit_action(self, magic_guild_service):
        """退出アクションのテスト"""
        # テスト実行
        result = magic_guild_service.execute_action("exit", {})
        
        # 検証
        assert result.success is True
        assert "退出" in result.message
    
    def test_unknown_action(self, magic_guild_service):
        """不明なアクションのテスト"""
        # テスト実行
        result = magic_guild_service.execute_action("unknown_action", {})
        
        # 検証
        assert result.success is False
        assert "不明なアクション" in result.message