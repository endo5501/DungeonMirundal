"""教会サービスの直接テスト"""

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

# 直接TempleServiceをインポート
with patch.dict('sys.modules', {
    'game.game': Mock(),
    'game.party': Mock(),
    'game.character': Mock()
}):
    from src.facilities.services.temple_service import TempleService
    from src.facilities.core.service_result import ServiceResult, ResultType
    from src.facilities.core.facility_service import MenuItem


class TestTempleServiceDirect:
    """教会サービスの直接テストクラス"""
    
    @pytest.fixture
    def temple_service(self):
        """教会サービスのフィクスチャ"""
        with patch('src.facilities.services.temple_service.Game') as mock_game_class:
            # モックゲームインスタンスを設定
            mock_game = Mock()
            mock_game_class.get_instance.return_value = mock_game
            
            service = TempleService()
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
    def injured_character(self):
        """負傷キャラクターのフィクスチャ"""
        char = Mock()
        char.id = "char1"
        char.name = "Hero"
        char.level = 5
        char.hp = 30
        char.max_hp = 100
        char.status = "normal"
        char.is_alive.return_value = True
        return char
    
    def test_get_menu_items(self, temple_service):
        """メニュー項目取得のテスト"""
        # テスト実行
        items = temple_service.get_menu_items()
        
        # 検証
        assert len(items) == 6  # 6つのメニュー項目
        
        # メニュー項目の存在確認
        item_ids = [item.id for item in items]
        assert "heal" in item_ids
        assert "resurrect" in item_ids
        assert "cure" in item_ids
        assert "blessing" in item_ids
        assert "donation" in item_ids
        assert "exit" in item_ids
        
        # 各項目の型確認
        for item in items:
            assert isinstance(item, MenuItem)
            assert item.label is not None
            assert item.description is not None
    
    def test_heal_cost_calculation(self, temple_service, injured_character):
        """治療費計算のテスト"""
        # テスト実行
        cost = temple_service._calculate_heal_cost(injured_character)
        
        # 検証 - レベル5、70ダメージ（70/100 = 0.7）、基本料金10G/レベル
        expected_cost = int(5 * 10 * 0.7)  # 35G
        assert cost == expected_cost
    
    def test_heal_no_damage(self, temple_service, injured_character):
        """無傷キャラクターの治療費のテスト"""
        injured_character.hp = injured_character.max_hp  # 無傷に設定
        
        # テスト実行
        cost = temple_service._calculate_heal_cost(injured_character)
        
        # 検証
        assert cost == 0
    
    def test_get_healable_members(self, temple_service, sample_party, injured_character):
        """治療可能メンバー取得のテスト"""
        sample_party.members = [injured_character]
        temple_service.party = sample_party
        
        # テスト実行
        result = temple_service.execute_action("heal", {})
        
        # 検証
        assert result.success is True
        assert "members" in result.data
        assert len(result.data["members"]) == 1
        assert result.data["members"][0]["name"] == "Hero"
        assert result.data["party_gold"] == 1000
    
    def test_exit_action(self, temple_service):
        """退出アクションのテスト"""
        # テスト実行
        result = temple_service.execute_action("exit", {})
        
        # 検証
        assert result.success is True
        assert "退出" in result.message
    
    def test_unknown_action(self, temple_service):
        """不明なアクションのテスト"""
        # テスト実行
        result = temple_service.execute_action("unknown_action", {})
        
        # 検証
        assert result.success is False
        assert "不明なアクション" in result.message