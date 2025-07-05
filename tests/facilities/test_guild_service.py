"""ギルドサービスのテスト"""

import pytest
from unittest.mock import Mock, MagicMock, patch
from src.facilities.services.guild_service import GuildService
from src.facilities.core.service_result import ServiceResult, ResultType
from src.facilities.core.facility_service import MenuItem
from game.character import Character
from game.party import Party


class TestGuildService:
    """ギルドサービスのテストクラス"""
    
    @pytest.fixture
    def guild_service(self):
        """ギルドサービスのフィクスチャ"""
        with patch('src.facilities.services.guild_service.Game') as mock_game_class:
            # モックゲームインスタンスを設定
            mock_game = Mock()
            mock_game_class.get_instance.return_value = mock_game
            
            # モックモデルを設定
            with patch('src.facilities.services.guild_service.CharacterModel') as mock_char_model:
                with patch('src.facilities.services.guild_service.PartyModel') as mock_party_model:
                    service = GuildService()
                    service.character_model = mock_char_model()
                    service.party_model = mock_party_model()
                    yield service
    
    @pytest.fixture
    def sample_character(self):
        """サンプルキャラクターのフィクスチャ"""
        char = Mock(spec=Character)
        char.id = "char1"
        char.name = "TestHero"
        char.level = 5
        char.race = "human"
        char.char_class = "fighter"
        char.hp = 50
        char.max_hp = 50
        char.mp = 10
        char.max_mp = 10
        char.status = "normal"
        return char
    
    @pytest.fixture
    def sample_party(self):
        """サンプルパーティのフィクスチャ"""
        party = Mock(spec=Party)
        party.name = "TestParty"
        party.members = []
        return party
    
    def test_get_menu_items(self, guild_service):
        """メニュー項目取得のテスト"""
        # テスト実行
        items = guild_service.get_menu_items()
        
        # 検証
        assert len(items) == 5  # 5つのメニュー項目
        
        # メニュー項目の存在確認
        item_ids = [item.id for item in items]
        assert "character_creation" in item_ids
        assert "party_formation" in item_ids
        assert "class_change" in item_ids
        assert "character_list" in item_ids
        assert "exit" in item_ids
        
        # 各項目の型確認
        for item in items:
            assert isinstance(item, MenuItem)
            assert item.label is not None
            assert item.description is not None
    
    def test_character_creation_start(self, guild_service):
        """キャラクター作成開始のテスト"""
        # テスト実行
        result = guild_service.execute_action("character_creation", {})
        
        # 検証
        assert result.success is True
        assert result.result_type == ResultType.INFO
        assert result.data["wizard_started"] is True
    
    def test_character_creation_complete_success(self, guild_service):
        """キャラクター作成完了（成功）のテスト"""
        # パラメータを準備
        params = {
            "name": "NewHero",
            "race": "elf",
            "class": "mage",
            "stats": {
                "strength": 10,
                "intelligence": 16,
                "piety": 12,
                "vitality": 11,
                "agility": 13,
                "luck": 10
            }
        }
        
        # モックの設定
        guild_service.character_model.create = Mock()
        guild_service.game.add_character = Mock()
        
        # テスト実行
        result = guild_service.execute_action("character_creation_complete", params)
        
        # 検証
        assert result.success is True
        assert result.result_type == ResultType.SUCCESS
        assert "NewHero" in result.message
        assert "character_id" in result.data
        
        # メソッド呼び出しの確認
        guild_service.character_model.create.assert_called_once()
        guild_service.game.add_character.assert_called_once()
    
    def test_character_creation_complete_missing_params(self, guild_service):
        """キャラクター作成完了（パラメータ不足）のテスト"""
        # 不完全なパラメータ
        params = {
            "name": "NewHero",
            "race": "elf"
            # classとstatsが不足
        }
        
        # テスト実行
        result = guild_service.execute_action("character_creation_complete", params)
        
        # 検証
        assert result.success is False
        assert result.result_type == ResultType.ERROR
        assert "必須項目が不足" in result.message
    
    def test_party_formation_get_info(self, guild_service, sample_party, sample_character):
        """パーティ情報取得のテスト"""
        # パーティを設定
        sample_party.members = [sample_character]
        guild_service.party = sample_party
        
        # テスト実行
        result = guild_service.execute_action("party_formation", {"action": "get_info"})
        
        # 検証
        assert result.success is True
        assert result.data["party_name"] == "TestParty"
        assert result.data["size"] == 1
        assert len(result.data["members"]) == 1
        assert result.data["members"][0]["name"] == "TestHero"
    
    def test_add_party_member_success(self, guild_service, sample_character):
        """パーティメンバー追加（成功）のテスト"""
        # モックの設定
        guild_service.character_model.get = Mock(return_value=sample_character)
        guild_service.party = Mock(spec=Party)
        guild_service.party.members = []
        guild_service.party.add_member = Mock(return_value=True)
        
        # テスト実行
        result = guild_service.execute_action(
            "party_formation",
            {"action": "add_member", "character_id": "char1"}
        )
        
        # 検証
        assert result.success is True
        assert "TestHero" in result.message
        guild_service.party.add_member.assert_called_once_with(sample_character)
    
    def test_add_party_member_full_party(self, guild_service, sample_character):
        """パーティメンバー追加（満員）のテスト"""
        # 満員のパーティを設定
        guild_service.party = Mock(spec=Party)
        guild_service.party.members = [Mock() for _ in range(6)]  # 6人で満員
        
        # テスト実行
        result = guild_service.execute_action(
            "party_formation",
            {"action": "add_member", "character_id": "char1"}
        )
        
        # 検証
        assert result.success is False
        assert "満員" in result.message
    
    def test_remove_party_member_success(self, guild_service, sample_character):
        """パーティメンバー削除（成功）のテスト"""
        # パーティを設定
        guild_service.party = Mock(spec=Party)
        guild_service.party.members = [sample_character]
        guild_service.party.remove_member = Mock(return_value=sample_character)
        
        # テスト実行
        result = guild_service.execute_action(
            "party_formation",
            {"action": "remove_member", "character_id": "char1"}
        )
        
        # 検証
        assert result.success is True
        assert "TestHero" in result.message
        guild_service.party.remove_member.assert_called_once()
    
    def test_class_change_check_requirements(self, guild_service, sample_character):
        """クラス変更（条件確認）のテスト"""
        # レベル不足のキャラクター
        sample_character.level = 3
        guild_service.character_model.get = Mock(return_value=sample_character)
        
        # テスト実行
        result = guild_service.execute_action(
            "class_change",
            {"character_id": "char1", "new_class": "samurai"}
        )
        
        # 検証
        assert result.success is False
        assert result.result_type == ResultType.WARNING
        assert "レベル5以上" in result.message
    
    def test_class_change_success(self, guild_service, sample_character):
        """クラス変更（成功）のテスト"""
        # レベル5のキャラクター
        sample_character.level = 5
        sample_character.change_class = Mock(return_value=True)
        guild_service.character_model.get = Mock(return_value=sample_character)
        guild_service.character_model.update = Mock()
        
        # テスト実行
        result = guild_service.execute_action(
            "class_change",
            {"character_id": "char1", "new_class": "samurai"}
        )
        
        # 検証
        assert result.success is True
        assert result.result_type == ResultType.SUCCESS
        assert "fighter" in result.message
        assert "samurai" in result.message
        sample_character.change_class.assert_called_once_with("samurai")
        guild_service.character_model.update.assert_called_once()
    
    def test_character_list_all(self, guild_service, sample_character):
        """キャラクター一覧（全員）のテスト"""
        # キャラクターリストを設定
        characters = [sample_character, Mock(spec=Character)]
        characters[1].id = "char2"
        characters[1].name = "TestMage"
        characters[1].level = 3
        characters[1].race = "elf"
        characters[1].char_class = "mage"
        characters[1].hp = 20
        characters[1].max_hp = 20
        characters[1].mp = 30
        characters[1].max_mp = 30
        characters[1].status = "normal"
        
        guild_service.character_model.get_all = Mock(return_value=characters)
        guild_service.party = None
        
        # テスト実行
        result = guild_service.execute_action("character_list", {"filter": "all"})
        
        # 検証
        assert result.success is True
        assert result.data["total"] == 2
        assert len(result.data["characters"]) == 2
        assert result.data["characters"][0]["name"] == "TestHero"
        assert result.data["characters"][1]["name"] == "TestMage"
    
    def test_character_list_available_only(self, guild_service, sample_character):
        """キャラクター一覧（パーティ外のみ）のテスト"""
        # キャラクターとパーティを設定
        char2 = Mock(spec=Character)
        char2.id = "char2"
        char2.name = "TestMage"
        characters = [sample_character, char2]
        
        guild_service.character_model.get_all = Mock(return_value=characters)
        guild_service.party = Mock(spec=Party)
        guild_service.party.members = [sample_character]  # char1のみパーティ内
        
        # テスト実行
        result = guild_service.execute_action("character_list", {"filter": "available"})
        
        # 検証
        assert result.success is True
        assert result.data["total"] == 1
        assert result.data["characters"][0]["id"] == "char2"
    
    def test_exit_action(self, guild_service):
        """退出アクションのテスト"""
        # テスト実行
        result = guild_service.execute_action("exit", {})
        
        # 検証
        assert result.success is True
        assert "退出" in result.message
    
    def test_unknown_action(self, guild_service):
        """不明なアクションのテスト"""
        # テスト実行
        result = guild_service.execute_action("unknown_action", {})
        
        # 検証
        assert result.success is False
        assert "不明なアクション" in result.message
    
    def test_can_create_character(self, guild_service):
        """キャラクター作成可能チェックのテスト"""
        # 19体のキャラクター（最大20体まで）
        characters = [Mock() for _ in range(19)]
        guild_service.character_model.get_all = Mock(return_value=characters)
        
        # テスト実行
        assert guild_service._can_create_character() is True
        
        # 20体のキャラクター（最大）
        characters.append(Mock())
        assert guild_service._can_create_character() is False
    
    def test_can_change_class(self, guild_service, sample_character):
        """クラス変更可能チェックのテスト"""
        # レベル5以上のキャラクターが存在
        sample_character.level = 5
        guild_service.character_model.get_all = Mock(return_value=[sample_character])
        
        assert guild_service._can_change_class() is True
        
        # レベル5未満のキャラクターのみ
        sample_character.level = 4
        assert guild_service._can_change_class() is False