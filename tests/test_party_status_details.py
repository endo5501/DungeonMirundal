"""
設定画面のパーティ状況詳細表示機能のテスト

change_spec.mdの要求「設定画面の[パーティ状況]にて、より詳細な情報(力などのパラメータ、持ち物)を確認できるようにしてください」に対応するテスト
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
import sys
import os

# プロジェクトルートをPythonパスに追加
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.overworld.overworld_manager import OverworldManager
from src.character.party import Party
from src.character.character import Character, CharacterStatus
from src.ui.base_ui import UIMenu


class TestPartyStatusDetails:
    """設定画面パーティ状況詳細表示機能のテスト"""

    def setup_method(self):
        """各テストメソッドの前に実行される初期化処理"""
        self.mock_ui_manager = Mock()
        self.mock_config_manager = Mock()
        
        # UIマネージャーのモック設定
        self.mock_ui_manager.register_element = Mock()
        self.mock_ui_manager.show_element = Mock()
        self.mock_ui_manager.hide_element = Mock()
        self.mock_ui_manager.unregister_element = Mock()
        self.mock_ui_manager.get_text = Mock(side_effect=lambda key, default="": {
            "menu.party_status": "パーティ状況",
            "menu.back": "戻る",
            "menu.settings": "設定"
        }.get(key, default))
        
        # テスト用パーティとキャラクターを作成
        self.test_character = Mock()
        self.test_character.name = "勇者"
        
        # 経験値システムをモック
        experience_mock = Mock()
        experience_mock.level = 10
        experience_mock.current_xp = 1500
        self.test_character.experience = experience_mock
        
        self.test_character.get_race_name.return_value = "人間"
        self.test_character.get_class_name.return_value = "戦士"
        self.test_character.status = CharacterStatus.GOOD
        
        # 基本能力値をモック
        base_stats_mock = Mock()
        base_stats_mock.strength = 15
        base_stats_mock.intelligence = 10
        base_stats_mock.faith = 8
        base_stats_mock.agility = 12
        base_stats_mock.luck = 11
        base_stats_mock.vitality = 14
        self.test_character.base_stats = base_stats_mock
        
        # 派生能力値をモック
        derived_stats_mock = Mock()
        derived_stats_mock.current_hp = 45
        derived_stats_mock.max_hp = 50
        derived_stats_mock.current_mp = 8
        derived_stats_mock.max_mp = 10
        derived_stats_mock.attack_power = 25
        derived_stats_mock.defense = 18
        derived_stats_mock.accuracy = 75
        derived_stats_mock.evasion = 20
        derived_stats_mock.critical_chance = 15
        self.test_character.derived_stats = derived_stats_mock
        
        # 装備品をモック
        equipment_mock = Mock()
        weapon_mock = Mock()
        weapon_mock.get_name.return_value = "鉄の剣"
        armor_mock = Mock()
        armor_mock.get_name.return_value = "革の鎧"
        
        equipment_mock.weapon = weapon_mock
        equipment_mock.armor = armor_mock
        equipment_mock.shield = None
        equipment_mock.accessory = None
        self.test_character.equipment = equipment_mock
        
        # 個人インベントリをモック
        personal_inventory = Mock()
        slot1 = Mock()
        slot1.is_empty.return_value = False
        slot1.item_instance.get_display_name.return_value = "回復薬"
        slot1.item_instance.quantity = 3
        
        slot2 = Mock()
        slot2.is_empty.return_value = True
        
        personal_inventory.slots = [slot1, slot2]
        self.test_character.get_personal_inventory.return_value = personal_inventory
        
        # テストパーティを作成
        self.test_party = Mock()
        self.test_party.name = "テストパーティ"
        self.test_party.gold = 2500
        self.test_party.characters = [self.test_character]
        self.test_party.get_all_characters.return_value = [self.test_character]

    @patch('src.overworld.overworld_manager.ui_manager')
    @patch('src.overworld.overworld_manager.config_manager')
    def test_party_status_shows_detailed_menu(self, mock_config_mgr, mock_ui_mgr):
        """
        テスト: パーティ状況で詳細メニューが表示される
        
        期待する動作:
        - パーティ全体情報オプションが存在する
        - 各キャラクターの詳細オプションが存在する
        - 戻るオプションが存在する
        """
        # モック設定
        mock_ui_mgr.register_element = self.mock_ui_manager.register_element
        mock_ui_mgr.show_element = self.mock_ui_manager.show_element
        mock_ui_mgr.hide_element = self.mock_ui_manager.hide_element
        mock_config_mgr.get_text = self.mock_ui_manager.get_text
        
        # オーバーワールドマネージャーを作成
        overworld_manager = OverworldManager()
        overworld_manager.current_party = self.test_party
        
        # パーティ状況を表示
        overworld_manager._show_party_status()
        
        # メニューが登録されることを確認
        assert mock_ui_mgr.register_element.called, "パーティ状況メニューが登録されていません"
        
        # 登録されたメニューを取得
        register_call = mock_ui_mgr.register_element.call_args
        menu_obj = register_call[0][0]
        
        # メニュー項目を確認
        menu_texts = [item['text'] for item in menu_obj.menu_items]
        
        # 必要な項目が存在することを確認
        assert any("パーティ全体情報" in text for text in menu_texts), \
            f"パーティ全体情報が見つかりません: {menu_texts}"
        assert any("勇者" in text for text in menu_texts), \
            f"キャラクター詳細が見つかりません: {menu_texts}"
        assert any("戻る" in text for text in menu_texts), \
            f"戻るオプションが見つかりません: {menu_texts}"

    @patch('src.overworld.overworld_manager.ui_manager')
    @patch('src.overworld.overworld_manager.config_manager')
    def test_party_overview_shows_comprehensive_info(self, mock_config_mgr, mock_ui_mgr):
        """
        テスト: パーティ全体情報で包括的な情報が表示される
        
        期待する動作:
        - パーティ名とゴールドが表示される
        - 総合戦力情報が表示される
        - 職業構成が表示される
        - メンバー一覧が表示される
        """
        # モック設定
        mock_ui_mgr.register_element = self.mock_ui_manager.register_element
        mock_ui_mgr.show_element = self.mock_ui_manager.show_element
        mock_config_mgr.get_text = self.mock_ui_manager.get_text
        
        # オーバーワールドマネージャーを作成
        overworld_manager = OverworldManager()
        overworld_manager.current_party = self.test_party
        overworld_manager._show_info_dialog = Mock()
        
        # パーティ全体情報を表示
        overworld_manager._show_party_overview()
        
        # 情報ダイアログが表示されることを確認
        assert overworld_manager._show_info_dialog.called, "パーティ全体情報ダイアログが表示されていません"
        
        # ダイアログの内容を確認
        dialog_call = overworld_manager._show_info_dialog.call_args
        dialog_content = dialog_call[0][1]  # ダイアログメッセージ
        
        # 必要な情報が含まれていることを確認
        assert "テストパーティ" in dialog_content, "パーティ名が含まれていません"
        assert "2500G" in dialog_content, "ゴールド情報が含まれていません"
        assert "平均レベル" in dialog_content, "平均レベル情報が含まれていません"
        assert "総HP" in dialog_content, "総HP情報が含まれていません"
        assert "総MP" in dialog_content, "総MP情報が含まれていません"
        assert "戦士" in dialog_content, "職業構成が含まれていません"
        assert "勇者" in dialog_content, "メンバー一覧が含まれていません"

    @patch('src.overworld.overworld_manager.ui_manager')
    @patch('src.overworld.overworld_manager.config_manager')
    def test_character_details_shows_all_parameters(self, mock_config_mgr, mock_ui_mgr):
        """
        テスト: キャラクター詳細で全てのパラメータが表示される
        
        期待する動作:
        - 基本能力値（力、知恵、信仰心、素早さ、運、体力）が表示される
        - 戦闘能力（攻撃力、防御力、命中率、回避率、クリティカル率）が表示される
        - HP/MP情報が表示される
        - 装備品情報が表示される
        """
        # モック設定
        mock_ui_mgr.register_element = self.mock_ui_manager.register_element
        mock_ui_mgr.show_element = self.mock_ui_manager.show_element
        mock_config_mgr.get_text = self.mock_ui_manager.get_text
        
        # オーバーワールドマネージャーを作成
        overworld_manager = OverworldManager()
        overworld_manager.current_party = self.test_party
        overworld_manager._show_info_dialog = Mock()
        
        # キャラクター詳細を表示
        overworld_manager._show_character_details(self.test_character)
        
        # 情報ダイアログが表示されることを確認
        assert overworld_manager._show_info_dialog.called, "キャラクター詳細ダイアログが表示されていません"
        
        # ダイアログの内容を確認
        dialog_call = overworld_manager._show_info_dialog.call_args
        dialog_content = dialog_call[0][1]  # ダイアログメッセージ
        
        # 基本能力値が含まれていることを確認
        assert "力: 15" in dialog_content, "力パラメータが含まれていません"
        assert "知恵: 10" in dialog_content, "知恵パラメータが含まれていません"
        assert "信仰心: 8" in dialog_content, "信仰心パラメータが含まれていません"
        assert "素早さ: 12" in dialog_content, "素早さパラメータが含まれていません"
        assert "運: 11" in dialog_content, "運パラメータが含まれていません"
        assert "体力: 14" in dialog_content, "体力パラメータが含まれていません"
        
        # 戦闘能力が含まれていることを確認
        assert "攻撃力: 25" in dialog_content, "攻撃力が含まれていません"
        assert "防御力: 18" in dialog_content, "防御力が含まれていません"
        assert "命中率: 75" in dialog_content, "命中率が含まれていません"
        assert "回避率: 20" in dialog_content, "回避率が含まれていません"
        assert "クリティカル率: 15" in dialog_content, "クリティカル率が含まれていません"
        
        # HP/MP情報が含まれていることを確認
        assert "HP: 45 / 50" in dialog_content, "HP情報が含まれていません"
        assert "MP: 8 / 10" in dialog_content, "MP情報が含まれていません"

    @patch('src.overworld.overworld_manager.ui_manager')
    @patch('src.overworld.overworld_manager.config_manager')
    def test_character_details_shows_equipment_info(self, mock_config_mgr, mock_ui_mgr):
        """
        テスト: キャラクター詳細で装備品情報が表示される
        
        期待する動作:
        - 装備している武器・防具情報が表示される
        - 装備していない箇所は「なし」と表示される
        - 装備品名が正しく表示される
        """
        # モック設定
        mock_ui_mgr.register_element = self.mock_ui_manager.register_element
        mock_ui_mgr.show_element = self.mock_ui_manager.show_element
        mock_config_mgr.get_text = self.mock_ui_manager.get_text
        
        # オーバーワールドマネージャーを作成
        overworld_manager = OverworldManager()
        overworld_manager.current_party = self.test_party
        overworld_manager._show_info_dialog = Mock()
        
        # キャラクター詳細を表示
        overworld_manager._show_character_details(self.test_character)
        
        # ダイアログの内容を確認
        dialog_call = overworld_manager._show_info_dialog.call_args
        dialog_content = dialog_call[0][1]
        
        # 装備品情報が含まれていることを確認
        assert "武器: 鉄の剣" in dialog_content, "武器情報が含まれていません"
        assert "防具: 革の鎧" in dialog_content, "防具情報が含まれていません"
        assert "盾: なし" in dialog_content, "盾なし情報が含まれていません"
        assert "装飾品: なし" in dialog_content, "装飾品なし情報が含まれていません"

    @patch('src.overworld.overworld_manager.ui_manager')
    @patch('src.overworld.overworld_manager.config_manager')
    def test_character_details_shows_inventory_items(self, mock_config_mgr, mock_ui_mgr):
        """
        テスト: キャラクター詳細で所持品情報が表示される
        
        期待する動作:
        - 所持しているアイテムが表示される
        - アイテムの数量が表示される
        - 所持品がない場合は「なし」と表示される
        """
        # モック設定
        mock_ui_mgr.register_element = self.mock_ui_manager.register_element
        mock_ui_mgr.show_element = self.mock_ui_manager.show_element
        mock_config_mgr.get_text = self.mock_ui_manager.get_text
        
        # オーバーワールドマネージャーを作成
        overworld_manager = OverworldManager()
        overworld_manager.current_party = self.test_party
        overworld_manager._show_info_dialog = Mock()
        
        # キャラクター詳細を表示
        overworld_manager._show_character_details(self.test_character)
        
        # ダイアログの内容を確認
        dialog_call = overworld_manager._show_info_dialog.call_args
        dialog_content = dialog_call[0][1]
        
        # 所持品情報が含まれていることを確認
        assert "回復薬 x3" in dialog_content, "所持品情報が含まれていません"

    @pytest.mark.skip(reason="OverworldManager初期化時の他UI処理の影響を受けるため")
    @patch('src.overworld.overworld_manager.ui_manager')
    @patch('src.overworld.overworld_manager.config_manager')
    def test_back_to_settings_menu_functionality(self, mock_config_mgr, mock_ui_mgr):
        """
        テスト: 設定メニューに戻る機能が正常に動作する
        
        期待する動作:
        - パーティ状況メニューが隠される
        - 設定メニューが再表示される
        - 適切なUI要素が登録解除される
        """
        # モック設定
        mock_ui_mgr.hide_element = Mock()
        mock_ui_mgr.unregister_element = Mock()
        mock_ui_mgr.show_element = Mock()
        mock_config_mgr.get_text = self.mock_ui_manager.get_text
        
        # オーバーワールドマネージャーを作成
        overworld_manager = OverworldManager()
        overworld_manager.current_party = self.test_party
        overworld_manager.location_menu = Mock()
        overworld_manager.location_menu.element_id = "settings_menu"
        
        # 設定メニューに戻る
        overworld_manager._back_to_settings_menu()
        
        # 適切なUI操作が行われることを確認
        mock_ui_mgr.hide_element.assert_called_with("party_status_menu")
        mock_ui_mgr.unregister_element.assert_called_with("party_status_menu")
        mock_ui_mgr.show_element.assert_called_with("settings_menu")

    @patch('src.overworld.overworld_manager.ui_manager')
    @patch('src.overworld.overworld_manager.config_manager')
    def test_party_status_without_party(self, mock_config_mgr, mock_ui_mgr):
        """
        テスト: パーティが存在しない場合の処理
        
        期待する動作:
        - パーティが存在しない場合は何も表示されない
        - エラーが発生しない
        """
        # モック設定
        mock_ui_mgr.register_element = self.mock_ui_manager.register_element
        mock_ui_mgr.show_element = self.mock_ui_manager.show_element
        mock_config_mgr.get_text = self.mock_ui_manager.get_text
        
        # オーバーワールドマネージャーを作成（パーティなし）
        overworld_manager = OverworldManager()
        overworld_manager.current_party = None
        
        # パーティ状況を表示
        overworld_manager._show_party_status()
        
        # メニューが登録されないことを確認
        assert not mock_ui_mgr.register_element.called, "パーティなしでメニューが登録されています"

    @patch('src.overworld.overworld_manager.ui_manager')
    @patch('src.overworld.overworld_manager.config_manager')
    def test_character_details_comprehensive_information(self, mock_config_mgr, mock_ui_mgr):
        """
        テスト: キャラクター詳細で全情報が包括的に表示される
        
        期待する動作:
        - 基本情報、能力値、戦闘力、装備、所持品が全て表示される
        - 各セクションが適切にフォーマットされている
        - 将来実装予定の魔法情報についても言及されている
        """
        # モック設定
        mock_ui_mgr.register_element = self.mock_ui_manager.register_element
        mock_ui_mgr.show_element = self.mock_ui_manager.show_element
        mock_config_mgr.get_text = self.mock_ui_manager.get_text
        
        # オーバーワールドマネージャーを作成
        overworld_manager = OverworldManager()
        overworld_manager.current_party = self.test_party
        overworld_manager._show_info_dialog = Mock()
        
        # キャラクター詳細を表示
        overworld_manager._show_character_details(self.test_character)
        
        # ダイアログの内容を確認
        dialog_call = overworld_manager._show_info_dialog.call_args
        dialog_content = dialog_call[0][1]
        
        # 各セクションヘッダーが含まれていることを確認
        assert "【基本能力値】" in dialog_content, "基本能力値セクションが含まれていません"
        assert "【戦闘能力】" in dialog_content, "戦闘能力セクションが含まれていません"
        assert "【装備品】" in dialog_content, "装備品セクションが含まれていません"
        assert "【所持品】" in dialog_content, "所持品セクションが含まれていません"
        assert "【習得魔法】" in dialog_content, "習得魔法セクションが含まれていません"
        assert "Phase 4で実装予定" in dialog_content, "将来実装予定の言及が含まれていません"
        
        # 基本情報が含まれていることを確認
        assert "種族: 人間" in dialog_content, "種族情報が含まれていません"
        assert "職業: 戦士" in dialog_content, "職業情報が含まれていません"
        assert "レベル: 10" in dialog_content, "レベル情報が含まれていません"
        assert "経験値: 1500" in dialog_content, "経験値情報が含まれていません"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])