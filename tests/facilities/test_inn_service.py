"""宿屋サービスのテスト"""

import pytest
from unittest.mock import Mock, MagicMock, patch
from src.facilities.services.inn_service import InnService
from src.facilities.core.service_result import ServiceResult, ResultType
from src.facilities.core.facility_service import MenuItem
from game.character import Character
from game.party import Party


class TestInnService:
    """宿屋サービスのテストクラス"""
    
    @pytest.fixture
    def inn_service(self):
        """宿屋サービスのフィクスチャ"""
        with patch('src.facilities.services.inn_service.Game') as mock_game_class:
            # モックゲームインスタンスを設定
            mock_game = Mock()
            mock_game_class.get_instance.return_value = mock_game
            
            # モックモデルを設定
            with patch('src.facilities.services.inn_service.ItemModel') as mock_item_model:
                with patch('src.facilities.services.inn_service.SpellModel') as mock_spell_model:
                    service = InnService()
                    service.item_model = mock_item_model()
                    service.spell_model = mock_spell_model()
                    yield service
    
    @pytest.fixture
    def sample_party(self):
        """サンプルパーティのフィクスチャ"""
        party = Mock(spec=Party)
        party.name = "TestParty"
        party.gold = 1000
        party.members = []
        return party
    
    @pytest.fixture
    def injured_character(self):
        """負傷したキャラクターのフィクスチャ"""
        char = Mock(spec=Character)
        char.id = "char1"
        char.name = "InjuredHero"
        char.level = 5
        char.hp = 20
        char.max_hp = 50
        char.mp = 5
        char.max_mp = 20
        char.status = "normal"
        char.is_alive.return_value = True
        return char
    
    @pytest.fixture
    def healthy_character(self):
        """健康なキャラクターのフィクスチャ"""
        char = Mock(spec=Character)
        char.id = "char2"
        char.name = "HealthyHero"
        char.level = 6
        char.hp = 60
        char.max_hp = 60
        char.mp = 30
        char.max_mp = 30
        char.status = "normal"
        char.is_alive.return_value = True
        return char
    
    def test_get_menu_items(self, inn_service):
        """メニュー項目取得のテスト"""
        # テスト実行
        items = inn_service.get_menu_items()
        
        # 検証
        assert len(items) == 5  # 5つのメニュー項目
        
        # メニュー項目の存在確認
        item_ids = [item.id for item in items]
        assert "rest" in item_ids
        assert "adventure_prep" in item_ids
        assert "storage" in item_ids
        assert "party_name" in item_ids
        assert "exit" in item_ids
        
        # 各項目の型確認
        for item in items:
            assert isinstance(item, MenuItem)
            assert item.label is not None
            assert item.description is not None
    
    def test_rest_cost_calculation(self, inn_service, sample_party, injured_character):
        """休憩料金計算のテスト"""
        # パーティを設定
        sample_party.members = [injured_character]
        inn_service.party = sample_party
        
        # 料金計算
        cost = inn_service._calculate_rest_cost()
        
        # レベル5のキャラクター1人なので、10 * 5 = 50
        assert cost == 50
    
    def test_rest_confirmation(self, inn_service, sample_party, injured_character):
        """休憩確認のテスト"""
        # パーティを設定
        sample_party.members = [injured_character]
        inn_service.party = sample_party
        
        # 確認なしで実行
        result = inn_service.execute_action("rest", {})
        
        # 検証
        assert result.success is True
        assert result.result_type == ResultType.CONFIRM
        assert "休憩料金は" in result.message
        assert result.data["cost"] == 50
    
    def test_rest_execution_success(self, inn_service, sample_party, injured_character):
        """休憩実行（成功）のテスト"""
        # パーティを設定
        sample_party.members = [injured_character]
        inn_service.party = sample_party
        
        # 確認済みで実行
        result = inn_service.execute_action("rest", {"confirmed": True})
        
        # 検証
        assert result.success is True
        assert result.result_type == ResultType.SUCCESS
        assert "回復しました" in result.message
        
        # キャラクターが回復したか確認
        assert injured_character.hp == injured_character.max_hp
        assert injured_character.mp == injured_character.max_mp
        
        # 料金が引かれたか確認
        assert sample_party.gold == 950  # 1000 - 50
    
    def test_rest_insufficient_gold(self, inn_service, sample_party, injured_character):
        """休憩実行（所持金不足）のテスト"""
        # パーティを設定（所持金不足）
        sample_party.members = [injured_character]
        sample_party.gold = 30  # 料金50に対して不足
        inn_service.party = sample_party
        
        # 確認済みで実行
        result = inn_service.execute_action("rest", {"confirmed": True})
        
        # 検証
        assert result.success is False
        assert result.result_type == ResultType.WARNING
        assert "所持金が足りません" in result.message
    
    def test_rest_already_healthy(self, inn_service, sample_party, healthy_character):
        """休憩実行（既に健康）のテスト"""
        # 健康なパーティを設定
        sample_party.members = [healthy_character]
        inn_service.party = sample_party
        
        # 確認済みで実行
        result = inn_service.execute_action("rest", {"confirmed": True})
        
        # 検証
        assert result.success is True
        assert result.result_type == ResultType.INFO
        assert "既に万全の状態" in result.message
    
    def test_can_rest_check(self, inn_service, sample_party, injured_character, healthy_character):
        """休憩可能チェックのテスト"""
        # 負傷者がいる場合
        sample_party.members = [injured_character]
        inn_service.party = sample_party
        assert inn_service._can_rest() is True
        
        # 全員健康な場合
        sample_party.members = [healthy_character]
        assert inn_service._can_rest() is False
        
        # パーティなしの場合
        inn_service.party = None
        assert inn_service._can_rest() is False
    
    def test_adventure_prep_main(self, inn_service, sample_party):
        """冒険準備メイン画面のテスト"""
        inn_service.party = sample_party
        
        # メイン画面を表示
        result = inn_service.execute_action("adventure_prep", {})
        
        # 検証
        assert result.success is True
        assert result.data["panel_type"] == "adventure_prep"
        assert len(result.data["sub_services"]) == 3
        
        # サブサービスの確認
        sub_service_ids = [s["id"] for s in result.data["sub_services"]]
        assert "item_management" in sub_service_ids
        assert "spell_management" in sub_service_ids
        assert "equipment_management" in sub_service_ids
    
    def test_storage_get_contents(self, inn_service):
        """保管庫内容取得のテスト"""
        # 保管庫の内容を取得
        result = inn_service.execute_action("storage", {})
        
        # 検証
        assert result.success is True
        assert "items" in result.data
        assert "capacity" in result.data
        assert "used" in result.data
        assert result.data["capacity"] == 100
    
    def test_party_name_change_input(self, inn_service, sample_party):
        """パーティ名変更（入力画面）のテスト"""
        inn_service.party = sample_party
        
        # 名前未指定で実行
        result = inn_service.execute_action("party_name", {})
        
        # 検証
        assert result.success is True
        assert result.data["input_required"] is True
        assert result.data["current_name"] == "TestParty"
    
    def test_party_name_change_success(self, inn_service, sample_party):
        """パーティ名変更（成功）のテスト"""
        inn_service.party = sample_party
        
        # 新しい名前を指定
        result = inn_service.execute_action("party_name", {"name": "NewPartyName"})
        
        # 検証
        assert result.success is True
        assert result.result_type == ResultType.SUCCESS
        assert "TestParty" in result.message
        assert "NewPartyName" in result.message
        assert sample_party.name == "NewPartyName"
    
    def test_party_name_change_invalid_length(self, inn_service, sample_party):
        """パーティ名変更（無効な長さ）のテスト"""
        inn_service.party = sample_party
        
        # 長すぎる名前
        long_name = "a" * 21
        result = inn_service.execute_action("party_name", {"name": long_name})
        
        # 検証
        assert result.success is False
        assert result.result_type == ResultType.WARNING
        assert "1～20文字" in result.message
    
    def test_exit_action(self, inn_service):
        """退出アクションのテスト"""
        # テスト実行
        result = inn_service.execute_action("exit", {})
        
        # 検証
        assert result.success is True
        assert "退出" in result.message
    
    def test_unknown_action(self, inn_service):
        """不明なアクションのテスト"""
        # テスト実行
        result = inn_service.execute_action("unknown_action", {})
        
        # 検証
        assert result.success is False
        assert "不明なアクション" in result.message