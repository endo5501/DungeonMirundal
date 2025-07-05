"""教会サービスのテスト"""

import pytest
from unittest.mock import Mock, MagicMock, patch
import sys

# 必要なモジュールをモック
mock_modules = [
    'game', 'game.game', 'game.party', 'game.character',
    'models', 'models.character_model', 'models.item_model', 
    'models.party_model', 'models.spell_model',
    'ui', 'ui.window_system', 'ui.window_system.party_formation_window',
    'character', 'character.character', 'character.character_manager'
]

for module in mock_modules:
    sys.modules[module] = Mock()

from src.facilities.services.temple_service import TempleService
from src.facilities.core.service_result import ServiceResult, ResultType
from src.facilities.core.facility_service import MenuItem


class TestTempleService:
    """教会サービスのテストクラス"""
    
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
    
    @pytest.fixture
    def dead_character(self):
        """死亡キャラクターのフィクスチャ"""
        char = Mock()
        char.id = "char2"
        char.name = "Warrior"
        char.level = 8
        char.hp = 0
        char.max_hp = 120
        char.status = "dead"
        char.vitality = 5
        char.is_alive.return_value = False
        return char
    
    @pytest.fixture
    def poisoned_character(self):
        """毒状態キャラクターのフィクスチャ"""
        char = Mock()
        char.id = "char3"
        char.name = "Mage"
        char.level = 4
        char.hp = 50
        char.max_hp = 60
        char.status = "poison"
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
    
    def test_heal_confirmation(self, temple_service, sample_party, injured_character):
        """治療確認のテスト"""
        sample_party.members = [injured_character]
        temple_service.party = sample_party
        
        # テスト実行
        result = temple_service.execute_action("heal", {
            "character_id": "char1"
        })
        
        # 検証
        assert result.success is True
        assert result.result_type == ResultType.CONFIRM
        assert "治療しますか" in result.message
        assert result.data["character_id"] == "char1"
    
    def test_heal_execution_success(self, temple_service, sample_party, injured_character):
        """治療実行（成功）のテスト"""
        sample_party.members = [injured_character]
        temple_service.party = sample_party
        initial_gold = sample_party.gold
        
        # テスト実行
        result = temple_service.execute_action("heal", {
            "character_id": "char1",
            "confirmed": True
        })
        
        # 検証
        assert result.success is True
        assert result.result_type == ResultType.SUCCESS
        assert "回復しました" in result.message
        assert injured_character.hp == injured_character.max_hp
        assert sample_party.gold < initial_gold
    
    def test_resurrect_cost_calculation(self, temple_service, dead_character):
        """蘇生費計算のテスト"""
        # テスト実行
        cost = temple_service._calculate_resurrect_cost(dead_character)
        
        # 検証 - レベル8、基本料金100G/レベル
        expected_cost = 8 * 100  # 800G
        assert cost == expected_cost
    
    def test_resurrect_ashes_cost(self, temple_service, dead_character):
        """灰状態の蘇生費計算のテスト"""
        dead_character.status = "ashes"
        
        # テスト実行
        cost = temple_service._calculate_resurrect_cost(dead_character)
        
        # 検証 - 灰状態は1.5倍
        expected_cost = int(8 * 100 * 1.5)  # 1200G
        assert cost == expected_cost
    
    def test_resurrect_execution_success(self, temple_service, sample_party, dead_character):
        """蘇生実行（成功）のテスト"""
        sample_party.members = [dead_character]
        temple_service.party = sample_party
        initial_gold = sample_party.gold
        initial_vitality = dead_character.vitality
        
        # テスト実行
        result = temple_service.execute_action("resurrect", {
            "character_id": "char2",
            "confirmed": True
        })
        
        # 検証
        assert result.success is True
        assert result.result_type == ResultType.SUCCESS
        assert "蘇生しました" in result.message
        assert dead_character.status == "normal"
        assert dead_character.hp == 1
        assert dead_character.vitality == initial_vitality - 1
        assert sample_party.gold < initial_gold
    
    def test_resurrect_no_vitality(self, temple_service, dead_character):
        """生命力不足の蘇生確認テスト"""
        dead_character.vitality = 0
        
        # テスト実行
        result = temple_service.execute_action("resurrect", {
            "character_id": "char2"
        })
        
        # 検証
        assert result.success is False
        assert result.result_type == ResultType.ERROR
        assert "生命力が尽きている" in result.message
    
    def test_cure_cost_retrieval(self, temple_service):
        """状態異常治療費取得のテスト"""
        # 毒の治療費をテスト
        cost = temple_service.cure_costs["poison"]
        assert cost == 50
        
        # 石化の治療費をテスト
        cost = temple_service.cure_costs["petrification"]
        assert cost == 500
    
    def test_cure_execution_success(self, temple_service, sample_party, poisoned_character):
        """状態回復実行（成功）のテスト"""
        sample_party.members = [poisoned_character]
        temple_service.party = sample_party
        initial_gold = sample_party.gold
        
        # テスト実行
        result = temple_service.execute_action("cure", {
            "character_id": "char3",
            "status_type": "poison",
            "confirmed": True
        })
        
        # 検証
        assert result.success is True
        assert result.result_type == ResultType.SUCCESS
        assert "治りました" in result.message
        assert poisoned_character.status == "normal"
        assert sample_party.gold == initial_gold - 50  # 毒の治療費
    
    def test_blessing_confirmation(self, temple_service, sample_party):
        """祝福確認のテスト"""
        temple_service.party = sample_party
        
        # テスト実行
        result = temple_service.execute_action("blessing", {})
        
        # 検証
        assert result.success is True
        assert result.result_type == ResultType.CONFIRM
        assert "祝福を与えますか" in result.message
        assert result.data["cost"] == 500
    
    def test_blessing_execution_success(self, temple_service, sample_party):
        """祝福実行（成功）のテスト"""
        temple_service.party = sample_party
        initial_gold = sample_party.gold
        
        # テスト実行
        result = temple_service.execute_action("blessing", {
            "confirmed": True
        })
        
        # 検証
        assert result.success is True
        assert result.result_type == ResultType.SUCCESS
        assert "祝福を受けました" in result.message
        assert sample_party.gold == initial_gold - 500
    
    def test_blessing_insufficient_gold(self, temple_service, sample_party):
        """祝福（所持金不足）のテスト"""
        sample_party.gold = 100  # 不足
        temple_service.party = sample_party
        
        # テスト実行
        result = temple_service.execute_action("blessing", {})
        
        # 検証
        assert result.success is False
        assert result.result_type == ResultType.WARNING
        assert "費用が不足" in result.message
    
    def test_donation_confirmation(self, temple_service, sample_party):
        """寄付確認のテスト"""
        temple_service.party = sample_party
        
        # テスト実行
        result = temple_service.execute_action("donation", {
            "amount": 200
        })
        
        # 検証
        assert result.success is True
        assert result.result_type == ResultType.CONFIRM
        assert "200 Gを寄付しますか" in result.message
    
    def test_donation_execution_success(self, temple_service, sample_party):
        """寄付実行（成功）のテスト"""
        temple_service.party = sample_party
        initial_gold = sample_party.gold
        
        # テスト実行
        result = temple_service.execute_action("donation", {
            "amount": 200,
            "confirmed": True
        })
        
        # 検証
        assert result.success is True
        assert result.result_type == ResultType.SUCCESS
        assert "寄付をありがとうございます" in result.message
        assert sample_party.gold == initial_gold - 200
    
    def test_donation_large_amount(self, temple_service, sample_party):
        """大額寄付のテスト"""
        temple_service.party = sample_party
        
        # テスト実行
        result = temple_service.execute_action("donation", {
            "amount": 10000,
            "confirmed": True
        })
        
        # 検証
        assert result.success is True
        assert "多大なる寄付に感謝" in result.message
    
    def test_donation_invalid_amount(self, temple_service, sample_party):
        """不正な寄付金額のテスト"""
        temple_service.party = sample_party
        
        # テスト実行 - 0円寄付
        result = temple_service.execute_action("donation", {
            "amount": 0
        })
        
        # 検証
        assert result.success is False
        assert result.result_type == ResultType.WARNING
        assert "1G以上を指定" in result.message
    
    def test_has_injured_members(self, temple_service, sample_party, injured_character):
        """負傷メンバーチェックのテスト"""
        # 負傷メンバーがいる場合
        sample_party.members = [injured_character]
        temple_service.party = sample_party
        assert temple_service._has_injured_members() is True
        
        # 負傷メンバーがいない場合
        injured_character.hp = injured_character.max_hp
        assert temple_service._has_injured_members() is False
    
    def test_has_dead_members(self, temple_service, sample_party, dead_character):
        """死亡メンバーチェックのテスト"""
        # 死亡メンバーがいる場合
        sample_party.members = [dead_character]
        temple_service.party = sample_party
        assert temple_service._has_dead_members() is True
        
        # 死亡メンバーがいない場合
        dead_character.status = "normal"
        assert temple_service._has_dead_members() is False
    
    def test_has_status_ailments(self, temple_service, sample_party, poisoned_character):
        """状態異常メンバーチェックのテスト"""
        # 状態異常メンバーがいる場合
        sample_party.members = [poisoned_character]
        temple_service.party = sample_party
        assert temple_service._has_status_ailments() is True
        
        # 状態異常メンバーがいない場合
        poisoned_character.status = "normal"
        assert temple_service._has_status_ailments() is False
    
    def test_get_status_name(self, temple_service):
        """状態名取得のテスト"""
        assert temple_service._get_status_name("poison") == "毒"
        assert temple_service._get_status_name("paralysis") == "麻痺"
        assert temple_service._get_status_name("unknown") == "unknown"
    
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