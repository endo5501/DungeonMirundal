"""TempleServiceのユニットテスト"""

import pytest
from unittest.mock import Mock, MagicMock
from src.facilities.services.temple_service import TempleService
from src.facilities.core.service_result import ServiceResult, ResultType
from src.character.character import Character
from src.character.party import Party


class TestTempleService:
    """TempleServiceのテストクラス"""
    
    def setup_method(self):
        """テスト前の準備"""
        self.temple_service = TempleService()
        
        # モックパーティを作成
        self.mock_party = Mock(spec=Party)
        self.mock_party.gold = 1000
        self.mock_party.members = []
        self.temple_service.party = self.mock_party
        
        # モックキャラクターを作成
        self.mock_dead_character = Mock(spec=Character)
        self.mock_dead_character.id = "test_char_1"
        self.mock_dead_character.name = "テストキャラクター"
        self.mock_dead_character.level = 5
        self.mock_dead_character.status = "dead"
        self.mock_dead_character.vitality = 10
        self.mock_dead_character.hp = 0
        
    def test_calculate_resurrect_cost_normal(self):
        """通常の蘇生費用計算をテスト"""
        cost = self.temple_service._calculate_resurrect_cost(self.mock_dead_character)
        expected_cost = 5 * 100  # レベル5 × 100ゴールド
        assert cost == expected_cost
        
    def test_calculate_resurrect_cost_ashes(self):
        """灰状態の蘇生費用計算をテスト"""
        self.mock_dead_character.status = "ashes"
        cost = self.temple_service._calculate_resurrect_cost(self.mock_dead_character)
        expected_cost = int(5 * 100 * 1.5)  # レベル5 × 100 × 1.5倍
        assert cost == expected_cost
    
    def test_has_dead_members_true(self):
        """死亡メンバーがいる場合のテスト"""
        self.mock_party.members = [self.mock_dead_character]
        assert self.temple_service._has_dead_members() is True
        
    def test_has_dead_members_false(self):
        """死亡メンバーがいない場合のテスト"""
        alive_character = Mock(spec=Character)
        alive_character.status = "normal"
        self.mock_party.members = [alive_character]
        assert self.temple_service._has_dead_members() is False
        
    def test_get_dead_members_success(self):
        """死亡メンバー取得の成功テスト"""
        self.mock_party.members = [self.mock_dead_character]
        result = self.temple_service._get_dead_members()
        
        assert result.success is True
        assert len(result.data["members"]) == 1
        assert result.data["members"][0]["name"] == "テストキャラクター"
        assert result.data["members"][0]["cost"] == 500  # レベル5 × 100
        
    def test_get_dead_members_empty(self):
        """死亡メンバーがいない場合のテスト"""
        self.mock_party.members = []
        result = self.temple_service._get_dead_members()
        
        assert result.success is True
        assert result.result_type == ResultType.INFO
        assert "蘇生が必要なメンバーはいません" in result.message
        
    def test_confirm_resurrect_success(self):
        """蘇生確認の成功テスト"""
        self.mock_party.members = [self.mock_dead_character]
        result = self.temple_service._confirm_resurrect("test_char_1")
        
        assert result.success is True
        assert result.result_type == ResultType.CONFIRM
        assert "テストキャラクター" in result.message
        assert "500 G" in result.message  # コスト表示
        
    def test_confirm_resurrect_insufficient_gold(self):
        """所持金不足での蘇生確認テスト"""
        self.mock_party.gold = 100  # 不足
        self.mock_party.members = [self.mock_dead_character]
        result = self.temple_service._confirm_resurrect("test_char_1")
        
        assert result.success is False
        assert result.result_type == ResultType.WARNING
        assert "蘇生費用が不足しています" in result.message
        
    def test_confirm_resurrect_no_vitality(self):
        """生命力不足での蘇生確認テスト"""
        self.mock_dead_character.vitality = 0
        self.mock_party.members = [self.mock_dead_character]
        result = self.temple_service._confirm_resurrect("test_char_1")
        
        assert result.success is False
        assert result.result_type == ResultType.ERROR
        assert "生命力が尽きているため蘇生できません" in result.message
        
    def test_execute_resurrect_success(self):
        """蘇生実行の成功テスト"""
        self.mock_party.members = [self.mock_dead_character]
        result = self.temple_service._execute_resurrect("test_char_1")
        
        assert result.success is True
        assert result.result_type == ResultType.SUCCESS
        assert self.mock_dead_character.status == "normal"
        assert self.mock_dead_character.hp == 1
        assert self.mock_dead_character.vitality == 9  # 10 - 1
        assert self.mock_party.gold == 500  # 1000 - 500
        
    def test_execute_resurrect_character_not_found(self):
        """存在しないキャラクターでの蘇生実行テスト"""
        self.mock_party.members = []
        result = self.temple_service._execute_resurrect("nonexistent_char")
        
        assert result.success is False
        assert "キャラクターが見つかりません" in result.message
        
    def test_handle_resurrect_flow(self):
        """蘇生フロー全体のテスト"""
        # 初回呼び出し：メンバーリスト取得
        self.mock_party.members = [self.mock_dead_character]
        result = self.temple_service._handle_resurrect({})
        
        assert result.success is True
        assert "蘇生対象を選択してください" in result.message
        
        # 確認段階
        result = self.temple_service._handle_resurrect({"character_id": "test_char_1"})
        assert result.success is True
        assert result.result_type == ResultType.CONFIRM
        
        # 実行段階
        result = self.temple_service._handle_resurrect({
            "character_id": "test_char_1", 
            "confirmed": True
        })
        assert result.success is True
        assert result.result_type == ResultType.SUCCESS
        
    def test_menu_items(self):
        """メニュー項目のテスト"""
        self.mock_party.members = [self.mock_dead_character]
        menu_items = self.temple_service.get_menu_items()
        
        resurrect_item = next((item for item in menu_items if item.id == "resurrect"), None)
        assert resurrect_item is not None
        assert resurrect_item.label == "蘇生"
        assert resurrect_item.enabled is True
        
        blessing_item = next((item for item in menu_items if item.id == "blessing"), None)
        assert blessing_item is not None
        assert blessing_item.label == "祝福"
        assert blessing_item.enabled is True


class TestTempleServiceIntegration:
    """TempleServiceの統合テスト"""
    
    def setup_method(self):
        """テスト前の準備"""
        self.temple_service = TempleService()
        
    def test_can_execute_actions(self):
        """アクション実行可能性のテスト"""
        # パーティがない場合
        assert self.temple_service.can_execute("resurrect") is False
        assert self.temple_service.can_execute("blessing") is False
        assert self.temple_service.can_execute("exit") is True
        
    def test_execute_unknown_action(self):
        """不明なアクション実行のテスト"""
        result = self.temple_service.execute_action("unknown_action", {})
        assert result.success is False
        assert "不明なアクション" in result.message


if __name__ == "__main__":
    pytest.main([__file__, "-v"])