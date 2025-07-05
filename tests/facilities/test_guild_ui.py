"""ギルドUIコンポーネントのテスト"""

import pytest
import pygame
import pygame_gui
from unittest.mock import Mock, MagicMock, patch
from src.facilities.ui.guild.character_creation_wizard import CharacterCreationWizard
from src.facilities.ui.guild.party_formation_panel import PartyFormationPanel
from src.facilities.ui.guild.character_list_panel import CharacterListPanel
from src.facilities.core.service_result import ServiceResult, ResultType


class TestCharacterCreationWizard:
    """キャラクター作成ウィザードのテストクラス"""
    
    @pytest.fixture
    def wizard(self):
        """ウィザードのフィクスチャ"""
        # pygame初期化をモック
        with patch('pygame.init'):
            with patch('pygame.display.set_mode'):
                # UIマネージャーのモック
                ui_manager = Mock(spec=pygame_gui.UIManager)
                
                # 親パネルのモック
                parent = Mock(spec=pygame_gui.UIPanel)
                
                # コントローラのモック
                controller = Mock()
                controller.execute_service_action = Mock(
                    return_value=ServiceResult(True, "Success")
                )
                
                # ウィザードを作成
                rect = pygame.Rect(0, 0, 400, 400)
                wizard = CharacterCreationWizard(rect, parent, controller, ui_manager)
                
                yield wizard
    
    def test_wizard_initialization(self, wizard):
        """ウィザード初期化のテスト"""
        # ステップが正しく設定されているか
        assert len(wizard.steps) == 5
        assert wizard.steps[0].id == "name"
        assert wizard.steps[1].id == "race"
        assert wizard.steps[2].id == "stats"
        assert wizard.steps[3].id == "class"
        assert wizard.steps[4].id == "confirm"
        
        # 初期ステップが0か
        assert wizard.current_step_index == 0
        
        # ウィザードデータが初期化されているか
        assert wizard.wizard_data == {}
    
    def test_name_validation(self, wizard):
        """名前検証のテスト"""
        # 空の名前
        assert wizard._validate_name({}) is False
        assert wizard._validate_name({"name": ""}) is False
        
        # 正常な名前
        assert wizard._validate_name({"name": "TestHero"}) is True
        
        # 長すぎる名前
        long_name = "a" * 21
        assert wizard._validate_name({"name": long_name}) is False
    
    def test_race_validation(self, wizard):
        """種族検証のテスト"""
        # 種族未選択
        assert wizard._validate_race({}) is False
        
        # 有効な種族
        valid_races = ["human", "elf", "dwarf", "gnome", "hobbit"]
        for race in valid_races:
            assert wizard._validate_race({"race": race}) is True
        
        # 無効な種族
        assert wizard._validate_race({"race": "invalid_race"}) is False
    
    def test_stats_validation(self, wizard):
        """能力値検証のテスト"""
        # 能力値未設定
        assert wizard._validate_stats({}) is False
        
        # 正常な能力値
        valid_stats = {
            "strength": 15,
            "intelligence": 12,
            "piety": 10,
            "vitality": 14,
            "agility": 11,
            "luck": 13
        }
        assert wizard._validate_stats({"stats": valid_stats}) is True
        
        # 不完全な能力値
        incomplete_stats = {
            "strength": 15,
            "intelligence": 12
            # 他の能力値が不足
        }
        assert wizard._validate_stats({"stats": incomplete_stats}) is False
        
        # 無効な値（3未満）
        invalid_stats = valid_stats.copy()
        invalid_stats["strength"] = 2
        assert wizard._validate_stats({"stats": invalid_stats}) is False
        
        # 無効な値（18超過）
        invalid_stats = valid_stats.copy()
        invalid_stats["strength"] = 19
        assert wizard._validate_stats({"stats": invalid_stats}) is False
    
    def test_class_validation(self, wizard):
        """職業検証のテスト"""
        # 職業未選択
        assert wizard._validate_class({}) is False
        
        # 基本職の検証
        wizard.wizard_data["stats"] = {
            "strength": 10,
            "intelligence": 10,
            "piety": 10,
            "vitality": 10,
            "agility": 10,
            "luck": 10
        }
        
        basic_classes = ["fighter", "priest", "thief", "mage"]
        for char_class in basic_classes:
            assert wizard._validate_class({"class": char_class}) is True
    
    def test_get_available_classes(self, wizard):
        """利用可能職業判定のテスト"""
        # 能力値未設定時は基本職のみ
        wizard.wizard_data = {}
        available = wizard._get_available_classes()
        assert set(available) == {"fighter", "priest", "thief", "mage"}
        
        # 低能力値でも基本職は利用可能
        wizard.wizard_data["stats"] = {
            "strength": 10,
            "intelligence": 10,
            "piety": 10,
            "vitality": 10,
            "agility": 10,
            "luck": 10
        }
        available = wizard._get_available_classes()
        assert set(available) == {"fighter", "priest", "thief", "mage"}
        
        # 高能力値で上級職が利用可能
        wizard.wizard_data["stats"] = {
            "strength": 17,
            "intelligence": 17,
            "piety": 17,
            "vitality": 17,
            "agility": 17,
            "luck": 17
        }
        available = wizard._get_available_classes()
        assert "ninja" in available
        assert "lord" in available
    
    def test_roll_stats(self, wizard):
        """能力値ロールのテスト"""
        # モックを設定して確定的な値を返す
        with patch('random.randint', side_effect=[3, 4, 5] * 6):
            wizard._roll_stats()
            
            # すべての能力値が12（3+4+5）になるはず
            assert wizard.wizard_data["stats"]["strength"] == 12
            assert wizard.wizard_data["stats"]["intelligence"] == 12
            assert wizard.wizard_data["stats"]["piety"] == 12
            assert wizard.wizard_data["stats"]["vitality"] == 12
            assert wizard.wizard_data["stats"]["agility"] == 12
            assert wizard.wizard_data["stats"]["luck"] == 12
    
    def test_complete_wizard(self, wizard):
        """ウィザード完了のテスト"""
        # 完全なデータを設定
        wizard.wizard_data = {
            "name": "TestHero",
            "race": "human",
            "class": "fighter",
            "stats": {
                "strength": 15,
                "intelligence": 10,
                "piety": 10,
                "vitality": 14,
                "agility": 11,
                "luck": 10
            }
        }
        
        # 完了処理を実行
        wizard._complete_wizard()
        
        # サービスアクションが呼ばれたか確認
        wizard.controller.execute_service_action.assert_called_once()
        call_args = wizard.controller.execute_service_action.call_args
        assert call_args[0][0] == "character_creation_complete"
        assert call_args[0][1] == wizard.wizard_data


class TestPartyFormationPanel:
    """パーティ編成パネルのテストクラス"""
    
    @pytest.fixture
    def panel(self):
        """パネルのフィクスチャ"""
        with patch('pygame.init'):
            with patch('pygame.display.set_mode'):
                # UIマネージャーのモック
                ui_manager = Mock(spec=pygame_gui.UIManager)
                
                # 親パネルのモック
                parent = Mock(spec=pygame_gui.UIPanel)
                
                # コントローラのモック
                controller = Mock()
                controller.execute_service_action = Mock(
                    return_value=ServiceResult(True, "Success", data={
                        "members": [],
                        "characters": []
                    })
                )
                
                # パネルを作成
                rect = pygame.Rect(0, 0, 600, 400)
                panel = PartyFormationPanel(rect, parent, controller, ui_manager)
                
                yield panel
    
    def test_panel_initialization(self, panel):
        """パネル初期化のテスト"""
        # データが初期化されているか
        assert panel.party_members == []
        assert panel.available_characters == []
        assert panel.selected_party_index is None
        assert panel.selected_available_index is None
    
    def test_add_member(self, panel):
        """メンバー追加のテスト"""
        # テストデータを設定
        test_character = {
            "id": "char1",
            "name": "TestHero",
            "level": 5,
            "class": "fighter"
        }
        panel.available_characters = [test_character]
        panel.selected_available_index = 0
        
        # 成功レスポンスを設定
        panel.controller.execute_service_action.return_value = ServiceResult(
            True, "メンバーを追加しました"
        )
        
        # メンバー追加を実行
        panel._add_member()
        
        # 検証
        assert len(panel.party_members) == 1
        assert panel.party_members[0] == test_character
        assert len(panel.available_characters) == 0
        assert panel.selected_available_index is None
    
    def test_remove_member(self, panel):
        """メンバー削除のテスト"""
        # テストデータを設定
        test_character = {
            "id": "char1",
            "name": "TestHero",
            "level": 5,
            "class": "fighter"
        }
        panel.party_members = [test_character]
        panel.selected_party_index = 0
        
        # 成功レスポンスを設定
        panel.controller.execute_service_action.return_value = ServiceResult(
            True, "メンバーを削除しました"
        )
        
        # メンバー削除を実行
        panel._remove_member()
        
        # 検証
        assert len(panel.party_members) == 0
        assert len(panel.available_characters) == 1
        assert panel.available_characters[0] == test_character
        assert panel.selected_party_index is None
    
    def test_move_member_up(self, panel):
        """メンバー上移動のテスト"""
        # テストデータを設定
        member1 = {"id": "char1", "name": "Hero1"}
        member2 = {"id": "char2", "name": "Hero2"}
        panel.party_members = [member1, member2]
        panel.selected_party_index = 1
        
        # 成功レスポンスを設定
        panel.controller.execute_service_action.return_value = ServiceResult(
            True, "並び順を変更しました"
        )
        
        # 上移動を実行
        panel._move_member_up()
        
        # 検証
        assert panel.party_members[0] == member2
        assert panel.party_members[1] == member1
        assert panel.selected_party_index == 0
    
    def test_move_member_down(self, panel):
        """メンバー下移動のテスト"""
        # テストデータを設定
        member1 = {"id": "char1", "name": "Hero1"}
        member2 = {"id": "char2", "name": "Hero2"}
        panel.party_members = [member1, member2]
        panel.selected_party_index = 0
        
        # 成功レスポンスを設定
        panel.controller.execute_service_action.return_value = ServiceResult(
            True, "並び順を変更しました"
        )
        
        # 下移動を実行
        panel._move_member_down()
        
        # 検証
        assert panel.party_members[0] == member2
        assert panel.party_members[1] == member1
        assert panel.selected_party_index == 1


class TestCharacterListPanel:
    """キャラクター一覧パネルのテストクラス"""
    
    @pytest.fixture
    def panel(self):
        """パネルのフィクスチャ"""
        with patch('pygame.init'):
            with patch('pygame.display.set_mode'):
                # UIマネージャーのモック
                ui_manager = Mock(spec=pygame_gui.UIManager)
                
                # 親パネルのモック
                parent = Mock(spec=pygame_gui.UIPanel)
                
                # コントローラのモック
                controller = Mock()
                controller.execute_service_action = Mock(
                    return_value=ServiceResult(True, "Success", data={
                        "characters": [],
                        "total": 0
                    })
                )
                
                # パネルを作成
                rect = pygame.Rect(0, 0, 600, 400)
                panel = CharacterListPanel(rect, parent, controller, ui_manager)
                
                yield panel
    
    def test_panel_initialization(self, panel):
        """パネル初期化のテスト"""
        # データが初期化されているか
        assert panel.characters == []
        assert panel.selected_character is None
        assert panel.selected_index is None
        assert panel.current_filter == "all"
        assert panel.current_sort == "name"
    
    def test_filter_change(self, panel):
        """フィルター変更のテスト"""
        # フィルター変更を実行
        panel._handle_filter_change("パーティ外")
        
        # 検証
        assert panel.current_filter == "available"
        
        # サービスアクションが呼ばれたか確認
        panel.controller.execute_service_action.assert_called()
        call_args = panel.controller.execute_service_action.call_args
        assert call_args[0][1]["filter"] == "available"
    
    def test_sort_change(self, panel):
        """ソート変更のテスト"""
        # ソート変更を実行
        panel._handle_sort_change("レベル順")
        
        # 検証
        assert panel.current_sort == "level"
        
        # サービスアクションが呼ばれたか確認
        panel.controller.execute_service_action.assert_called()
        call_args = panel.controller.execute_service_action.call_args
        assert call_args[0][1]["sort"] == "level"
    
    def test_character_selection(self, panel):
        """キャラクター選択のテスト"""
        # テストデータを設定
        test_character = {
            "id": "char1",
            "name": "TestHero",
            "level": 5,
            "race": "human",
            "class": "fighter",
            "hp": "50/50",
            "mp": "10/10",
            "status": "normal",
            "in_party": False
        }
        panel.characters = [test_character]
        
        # モックリストを設定
        panel.character_list = Mock()
        panel.character_list.item_list = ["  TestHero Lv5 fighter"]
        
        # 選択を実行
        panel._handle_character_selection("  TestHero Lv5 fighter")
        
        # 検証
        assert panel.selected_character == test_character
        assert panel.selected_index == 0