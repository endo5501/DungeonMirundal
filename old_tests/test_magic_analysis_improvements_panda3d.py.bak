"""
魔法分析機能の改善テスト

change_spec.mdの要求：
- 魔術師ギルドの魔法適性分析が、問答無用で300Gかかるのは良くない。
- 魔法分析の[魔法使用回数確認]が未実装です

に対応するテスト
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
import sys
import os

# プロジェクトルートをPythonパスに追加
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.overworld.facilities.magic_guild import MagicGuild
from src.character.party import Party
from src.character.character import Character


class TestMagicAnalysisImprovements:
    """魔法分析機能の改善テスト"""

    def setup_method(self):
        """各テストメソッドの前に実行される初期化処理"""
        self.mock_ui_manager = Mock()
        self.mock_config_manager = Mock()
        
        # UIマネージャーのモック設定
        self.mock_ui_manager.register_element = Mock()
        self.mock_ui_manager.show_element = Mock()
        self.mock_ui_manager.hide_element = Mock()
        self.mock_ui_manager.get_text = Mock(side_effect=lambda key, default="": {
            "facility.magic_guild": "魔術師ギルド",
            "common.ok": "OK",
            "common.yes": "はい",
            "common.no": "いいえ",
            "common.cancel": "キャンセル",
            "menu.exit": "出る",
            "menu.back": "戻る"
        }.get(key, default))
        
        # テスト用キャラクターを作成
        self.test_character_mage = Mock()
        self.test_character_mage.name = "魔術師"
        self.test_character_mage.get_class_name.return_value = "mage"
        self.test_character_mage.get_race_name.return_value = "elf"
        
        # 経験値システムをモック
        experience_mock = Mock()
        experience_mock.level = 8
        self.test_character_mage.experience = experience_mock
        
        # 基本能力値をモック
        base_stats_mock = Mock()
        base_stats_mock.intelligence = 16
        base_stats_mock.faith = 10
        self.test_character_mage.base_stats = base_stats_mock
        
        # 派生能力値をモック
        derived_stats_mock = Mock()
        derived_stats_mock.current_mp = 15
        derived_stats_mock.max_mp = 20
        self.test_character_mage.derived_stats = derived_stats_mock
        
        # テスト用パーティを作成
        self.test_party = Mock()
        self.test_party.name = "テストパーティ"
        self.test_party.gold = 1000
        self.test_party.characters = [self.test_character_mage]  # charactersプロパティを追加
        self.test_party.get_all_characters.return_value = [self.test_character_mage]

    @patch('src.overworld.base_facility.ui_manager')
    @patch('src.overworld.base_facility.config_manager')
    def test_magic_analysis_requires_confirmation(self, mock_config_mgr, mock_ui_mgr):
        """
        テスト: 魔法適性分析が確認ダイアログを表示する
        
        期待する動作:
        - 分析実行前に費用確認ダイアログが表示される
        - ユーザーが確認しないと分析が実行されない
        - 適切な費用と説明が表示される
        """
        # モック設定
        mock_ui_mgr.register_element = self.mock_ui_manager.register_element
        mock_ui_mgr.show_element = self.mock_ui_manager.show_element
        mock_config_mgr.get_text = self.mock_ui_manager.get_text
        
        # 魔術師ギルドインスタンス作成
        magic_guild = MagicGuild()
        magic_guild.current_party = self.test_party
        magic_guild._show_confirmation = Mock()
        
        # 魔法適性分析を実行
        magic_guild._analyze_party_magic_aptitude()
        
        # 確認ダイアログが表示されることを確認
        assert magic_guild._show_confirmation.called, "魔法適性分析の確認ダイアログが表示されていません"
        
        # 確認ダイアログの内容を確認
        confirmation_call = magic_guild._show_confirmation.call_args
        confirmation_text = confirmation_call[0][0]
        
        # 必要な情報が含まれていることを確認
        assert "300G" in confirmation_text, "分析費用が確認ダイアログに含まれていません"
        assert "分析を実行しますか？" in confirmation_text, "確認文言が含まれていません"
        assert "1000G" in confirmation_text, "現在のゴールドが含まれていません"

    @patch('src.overworld.base_facility.ui_manager')
    @patch('src.overworld.base_facility.config_manager')
    def test_magic_analysis_insufficient_gold_error(self, mock_config_mgr, mock_ui_mgr):
        """
        テスト: ゴールド不足時に適切なエラーメッセージが表示される
        
        期待する動作:
        - ゴールドが不足している場合はエラーメッセージが表示される
        - 確認ダイアログは表示されない
        - 分析は実行されない
        """
        # モック設定
        mock_ui_mgr.register_element = self.mock_ui_manager.register_element
        mock_ui_mgr.show_element = self.mock_ui_manager.show_element
        mock_config_mgr.get_text = self.mock_ui_manager.get_text
        
        # ゴールド不足のパーティを作成
        poor_party = Mock()
        poor_party.gold = 100  # 300G未満
        poor_party.characters = [self.test_character_mage]  # charactersプロパティを追加
        poor_party.get_all_characters.return_value = [self.test_character_mage]
        
        # 魔術師ギルドインスタンス作成
        magic_guild = MagicGuild()
        magic_guild.current_party = poor_party
        magic_guild._show_error_message = Mock()
        magic_guild._show_confirmation = Mock()
        
        # 魔法適性分析を実行
        magic_guild._analyze_party_magic_aptitude()
        
        # エラーメッセージが表示されることを確認
        assert magic_guild._show_error_message.called, "ゴールド不足エラーメッセージが表示されていません"
        
        # 確認ダイアログが表示されないことを確認
        assert not magic_guild._show_confirmation.called, "ゴールド不足時に確認ダイアログが表示されています"

    @patch('src.overworld.base_facility.ui_manager')
    @patch('src.overworld.base_facility.config_manager')
    def test_spell_usage_info_menu_implemented(self, mock_config_mgr, mock_ui_mgr):
        """
        テスト: 魔法使用回数確認機能が実装されている
        
        期待する動作:
        - 魔法使用可能なキャラクターがいる場合はメニューが表示される
        - 各キャラクターの詳細情報が確認できる
        - 適切なナビゲーションが提供される
        """
        # モック設定
        mock_ui_mgr.register_element = self.mock_ui_manager.register_element
        mock_ui_mgr.show_element = self.mock_ui_manager.show_element
        mock_config_mgr.get_text = self.mock_ui_manager.get_text
        
        # 魔術師ギルドインスタンス作成
        magic_guild = MagicGuild()
        magic_guild.current_party = self.test_party
        magic_guild._show_submenu = Mock()  # _show_submenuメソッドをモック
        
        # 魔法使用回数確認を実行
        magic_guild._show_spell_usage_info()
        
        # サブメニューが表示されることを確認
        assert magic_guild._show_submenu.called, "魔法使用回数確認サブメニューが表示されていません"
        
        # 渡されたメニューを取得
        submenu_call = magic_guild._show_submenu.call_args
        menu_obj = submenu_call[0][0]
        
        # キャラクター選択項目が存在することを確認
        menu_texts = [item['text'] for item in menu_obj.menu_items]
        assert any("魔術師" in text for text in menu_texts), \
            f"魔法使用可能キャラクターが表示されていません: {menu_texts}"

    @patch('src.overworld.base_facility.ui_manager')
    @patch('src.overworld.base_facility.config_manager')
    def test_spell_usage_info_no_magic_users(self, mock_config_mgr, mock_ui_mgr):
        """
        テスト: 魔法使用可能キャラクターがいない場合の処理
        
        期待する動作:
        - 魔法使用可能キャラクターがいない場合は適切なメッセージが表示される
        - 魔法使用可能クラスの説明が含まれる
        - メニューは表示されない
        """
        # モック設定
        mock_ui_mgr.register_element = self.mock_ui_manager.register_element
        mock_ui_mgr.show_element = self.mock_ui_manager.show_element
        mock_config_mgr.get_text = self.mock_ui_manager.get_text
        
        # 魔法使用不可キャラクターのパーティを作成
        fighter_character = Mock()
        fighter_character.get_class_name.return_value = "fighter"
        
        no_magic_party = Mock()
        no_magic_party.characters = [fighter_character]  # charactersプロパティを追加
        no_magic_party.get_all_characters.return_value = [fighter_character]
        
        # 魔術師ギルドインスタンス作成
        magic_guild = MagicGuild()
        magic_guild.current_party = no_magic_party
        magic_guild._show_dialog = Mock()
        
        # 魔法使用回数確認を実行
        magic_guild._show_spell_usage_info()
        
        # 適切なメッセージダイアログが表示されることを確認
        assert magic_guild._show_dialog.called, "魔法使用不可メッセージが表示されていません"
        
        # ダイアログの内容を確認
        dialog_call = magic_guild._show_dialog.call_args
        message = dialog_call[0][2]  # メッセージ部分
        assert "現在のパーティには魔法を使用できる" in message, "適切なメッセージが表示されていません"
        assert "魔術師" in message, "魔法使用可能クラスの説明が含まれていません"

    @patch('src.overworld.base_facility.ui_manager')
    @patch('src.overworld.base_facility.config_manager')
    def test_character_spell_usage_details(self, mock_config_mgr, mock_ui_mgr):
        """
        テスト: キャラクター個別の魔法使用状況詳細が表示される
        
        期待する動作:
        - キャラクターの基本情報が表示される
        - 魔法適性能力値が表示される
        - 現在のMP状況が表示される
        - 魔法システムの説明が含まれる
        """
        # モック設定
        mock_ui_mgr.register_element = self.mock_ui_manager.register_element
        mock_ui_mgr.show_element = self.mock_ui_manager.show_element
        mock_config_mgr.get_text = self.mock_ui_manager.get_text
        
        # 魔術師ギルドインスタンス作成
        magic_guild = MagicGuild()
        magic_guild.current_party = self.test_party
        magic_guild._show_dialog = Mock()
        
        # キャラクター魔法使用状況詳細を表示
        magic_guild._show_character_spell_usage(self.test_character_mage)
        
        # 詳細ダイアログが表示されることを確認
        assert magic_guild._show_dialog.called, "キャラクター魔法使用状況詳細が表示されていません"
        
        # ダイアログの内容を確認
        dialog_call = magic_guild._show_dialog.call_args
        usage_info = dialog_call[0][2]  # メッセージ部分
        
        # 必要な情報が含まれていることを確認
        assert "魔術師" in usage_info, "キャラクター名が含まれていません"
        assert "知恵: 16" in usage_info, "知恵パラメータが含まれていません"
        assert "信仰心: 10" in usage_info, "信仰心パラメータが含まれていません"
        assert "MP: 15 / 20" in usage_info, "MP情報が含まれていません"
        assert "地上部帰還時に魔力が全回復" in usage_info, "魔法システム説明が含まれていません"

    @patch('src.overworld.base_facility.ui_manager')
    @patch('src.overworld.base_facility.config_manager')
    def test_magic_analysis_confirmation_callback(self, mock_config_mgr, mock_ui_mgr):
        """
        テスト: 魔法適性分析の確認後に実際の分析が実行される
        
        期待する動作:
        - 確認ダイアログで「はい」を選択すると分析が実行される
        - ゴールドが適切に減額される
        - 分析結果が表示される
        """
        # モック設定
        mock_ui_mgr.register_element = self.mock_ui_manager.register_element
        mock_ui_mgr.show_element = self.mock_ui_manager.show_element
        mock_config_mgr.get_text = self.mock_ui_manager.get_text
        
        # 魔術師ギルドインスタンス作成
        magic_guild = MagicGuild()
        magic_guild.current_party = self.test_party
        magic_guild._show_dialog = Mock()
        
        # 初期ゴールド
        initial_gold = self.test_party.gold
        
        # 魔法適性分析実行（確認後の処理）
        magic_guild._perform_party_magic_analysis(300)
        
        # ゴールドが減額されることを確認
        expected_gold = initial_gold - 300
        assert self.test_party.gold == expected_gold, f"ゴールドが正しく減額されていません: {self.test_party.gold}"
        
        # 分析結果ダイアログが表示されることを確認
        assert magic_guild._show_dialog.called, "分析結果ダイアログが表示されていません"

    @patch('src.overworld.base_facility.ui_manager')
    @patch('src.overworld.base_facility.config_manager')
    def test_spell_usage_mp_status_evaluation(self, mock_config_mgr, mock_ui_mgr):
        """
        テスト: MP状況の評価が正しく表示される
        
        期待する動作:
        - MP残量に応じて適切な状態メッセージが表示される
        - パーセンテージが正しく計算される
        - 状態評価が適切に行われる
        """
        # モック設定
        mock_ui_mgr.register_element = self.mock_ui_manager.register_element
        mock_ui_mgr.show_element = self.mock_ui_manager.show_element
        mock_config_mgr.get_text = self.mock_ui_manager.get_text
        
        # 異なるMP状況のキャラクターを作成
        full_mp_character = Mock()
        full_mp_character.name = "フルMP"
        full_mp_character.get_class_name.return_value = "mage"
        full_mp_character.get_race_name.return_value = "elf"
        full_mp_character.experience.level = 8
        full_mp_character.base_stats.intelligence = 16
        full_mp_character.base_stats.faith = 10
        full_mp_character.derived_stats.current_mp = 20
        full_mp_character.derived_stats.max_mp = 20
        
        low_mp_character = Mock()
        low_mp_character.name = "ローMP"
        low_mp_character.get_class_name.return_value = "mage"
        low_mp_character.get_race_name.return_value = "elf"
        low_mp_character.experience.level = 8
        low_mp_character.base_stats.intelligence = 16
        low_mp_character.base_stats.faith = 10
        low_mp_character.derived_stats.current_mp = 2
        low_mp_character.derived_stats.max_mp = 20
        
        # 魔術師ギルドインスタンス作成
        magic_guild = MagicGuild()
        magic_guild.current_party = self.test_party
        magic_guild._show_dialog = Mock()
        
        # フルMPキャラクターの状況確認
        magic_guild._show_character_spell_usage(full_mp_character)
        full_mp_call = magic_guild._show_dialog.call_args
        full_mp_info = full_mp_call[0][2]
        assert "十分な魔力があります" in full_mp_info, "フルMP時の状態評価が正しくありません"
        
        # ローMPキャラクターの状況確認
        magic_guild._show_dialog.reset_mock()
        magic_guild._show_character_spell_usage(low_mp_character)
        low_mp_call = magic_guild._show_dialog.call_args
        low_mp_info = low_mp_call[0][2]
        assert "魔力がほとんどありません" in low_mp_info, "ローMP時の状態評価が正しくありません"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])