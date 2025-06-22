"""その他UI関連バグ修正テスト"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from src.overworld.facilities.guild import AdventurersGuild
from src.overworld.facilities.temple import Temple
from src.overworld.facilities.magic_guild import MagicGuild
from src.overworld.overworld_manager import OverworldManager
from src.character.character import Character
from src.character.stats import BaseStats


class TestOtherUIBugFixes:
    """その他UI関連バグ修正テスト"""
    
    def setup_method(self):
        """各テストメソッドの前に実行"""
        self.mock_party = Mock()
        self.mock_party.characters = {}
        self.mock_party.gold = 1000
        
    def test_guild_party_formation_flow_fix(self):
        """パーティ編成画面でキャラクタ追加後の画面遷移修正テスト"""
        guild = AdventurersGuild()
        guild.current_party = self.mock_party
        
        # キャラクター作成
        mock_character = Mock()
        mock_character.name = "テストキャラ"
        mock_character.character_id = "test_char_1"
        
        # add_character が成功する場合をモック
        self.mock_party.add_character.return_value = True
        
        # 新しいメソッドをモック
        with patch.object(guild, '_close_all_submenus_and_return_to_main') as mock_close, \
             patch.object(guild, '_show_success_message') as mock_success:
            
            guild._add_character_to_party(mock_character)
            
            # 成功メッセージが表示されることを確認
            mock_success.assert_called_once_with("テストキャラ をパーティに追加しました")
            
            # メインメニューに戻る処理が呼ばれることを確認
            mock_close.assert_called_once()
            
            # add_character が呼ばれることを確認
            self.mock_party.add_character.assert_called_once_with(mock_character)
    
    def test_guild_character_list_duplicate_fix(self):
        """冒険者ギルドでメンバー重複表示バグの修正テスト"""
        guild = AdventurersGuild()
        guild.current_party = self.mock_party
        
        # テストキャラクターを作成
        char1 = Mock()
        char1.character_id = "char_1"
        char1.name = "キャラ1"
        char1.experience.level = 5
        char1.get_race_name.return_value = "人間"
        char1.get_class_name.return_value = "戦士"
        char1.derived_stats.current_hp = 50
        char1.derived_stats.max_hp = 50
        char1.derived_stats.current_mp = 10
        char1.derived_stats.max_mp = 10
        
        char2 = Mock()
        char2.character_id = "char_2"
        char2.name = "キャラ2"
        char2.experience.level = 3
        char2.get_race_name.return_value = "エルフ"
        char2.get_class_name.return_value = "魔術師"
        char2.derived_stats.current_hp = 30
        char2.derived_stats.max_hp = 30
        char2.derived_stats.current_mp = 20
        char2.derived_stats.max_mp = 20
        
        # 作成済みキャラクターリスト（char1を含む）
        guild.created_characters = [char1, char2]
        
        # パーティにもchar1が参加（重複の原因）
        self.mock_party.characters = {"char_1": char1}
        
        with patch.object(guild, '_show_dialog') as mock_show_dialog:
            guild._show_character_list()
            
            # ダイアログが呼ばれることを確認
            mock_show_dialog.assert_called_once()
            
            # 呼び出された引数を取得
            call_args = mock_show_dialog.call_args[0]
            char_list_text = call_args[2]  # 3番目の引数がテキスト
            
            # キャラ1が1回だけ表示されることを確認（重複しない）
            char1_count = char_list_text.count("キャラ1")
            assert char1_count == 1, f"キャラ1が{char1_count}回表示されました（期待値: 1回）"
            
            # キャラ2も1回だけ表示されることを確認
            char2_count = char_list_text.count("キャラ2")
            assert char2_count == 1, f"キャラ2が{char2_count}回表示されました（期待値: 1回）"
            
            # パーティ状態の表示を確認
            assert "(パーティ中)" in char_list_text
            assert "(待機中)" in char_list_text
    
    def test_overworld_load_menu_fix(self):
        """設定画面でのゲームロード機能修正テスト"""
        manager = OverworldManager()
        
        # save_manager の get_save_slots をモック
        mock_slots = [
            Mock(slot_id=1, name="冒険者A", party_level=5),
            Mock(slot_id=2, name="冒険者B", party_level=8),
        ]
        
        with patch('src.overworld.overworld_manager.save_manager') as mock_save_manager, \
             patch('src.overworld.overworld_manager.ui_manager') as mock_ui_manager, \
             patch('src.overworld.overworld_manager.UIMenu') as mock_ui_menu:
            
            # get_save_slots の戻り値を設定
            mock_save_manager.get_save_slots.return_value = mock_slots
            
            # UIMenu インスタンスをモック
            mock_menu = Mock()
            mock_ui_menu.return_value = mock_menu
            
            manager._show_load_menu()
            
            # セーブスロット一覧が取得されることを確認
            mock_save_manager.get_save_slots.assert_called_once()
            
            # ロードメニューが作成されることを確認
            mock_ui_menu.assert_called_once_with("load_game_menu", "セーブデータ選択")
            
            # メニューアイテムが追加されることを確認（2つのスロット + 戻るボタン）
            assert mock_menu.add_menu_item.call_count == 3
            
            # UIが正しく登録・表示されることを確認
            mock_ui_manager.register_element.assert_called_once_with(mock_menu)
            mock_ui_manager.show_element.assert_called_once_with(mock_menu.element_id, modal=True)
    
    def test_temple_blessing_dialog_back_button_fix(self):
        """教会の祝福サービスで戻るキー修正テスト"""
        temple = Temple()
        temple.current_party = self.mock_party
        temple.service_costs = {'blessing': 100}
        
        with patch('src.overworld.facilities.temple.ui_manager') as mock_ui_manager, \
             patch('src.overworld.facilities.temple.UIDialog') as mock_ui_dialog:
            
            # UIDialog インスタンスをモック
            mock_dialog = Mock()
            mock_ui_dialog.return_value = mock_dialog
            
            temple._show_blessing_menu()
            
            # UIDialog が作成されることを確認
            mock_ui_dialog.assert_called_once()
            
            # 引数を取得
            call_args = mock_ui_dialog.call_args
            dialog_buttons = call_args[1]['buttons']  # キーワード引数のbuttons
            
            # 戻るボタンが _close_blessing_dialog を呼ぶことを確認
            back_button = next(btn for btn in dialog_buttons if btn['text'] == '戻る')
            assert back_button['command'] == temple._close_blessing_dialog
            
            # ダイアログが正しく登録・表示されることを確認
            mock_ui_manager.register_element.assert_called_once_with(mock_dialog)
            mock_ui_manager.show_element.assert_called_once_with(mock_dialog.element_id, modal=True)
    
    def test_temple_close_blessing_dialog_method(self):
        """教会の祝福ダイアログを閉じるメソッドテスト"""
        temple = Temple()
        temple.main_menu = Mock()
        temple.main_menu.element_id = "temple_main_menu"
        
        with patch('src.overworld.facilities.temple.ui_manager') as mock_ui_manager:
            temple._close_blessing_dialog()
            
            # ダイアログが正しく非表示・登録解除されることを確認
            mock_ui_manager.hide_element.assert_called_once_with("blessing_dialog")
            mock_ui_manager.unregister_element.assert_called_once_with("blessing_dialog")
            
            # メインメニューが再表示されることを確認
            mock_ui_manager.show_element.assert_called_once_with("temple_main_menu")
    
    def test_magic_guild_analysis_intelligence_check_fix(self):
        """魔術師ギルドで魔法分析の知恵チェック修正テスト"""
        magic_guild = MagicGuild()
        
        # エルフ魔術師（知恵20）のテストキャラクター
        character = Mock()
        character.name = "エルフ魔術師"
        character.get_race_name.return_value = "エルフ"
        character.get_class_name.return_value = "魔術師"  # 日本語クラス名
        character.experience.level = 5
        character.base_stats = Mock()
        character.base_stats.intelligence = 20
        character.base_stats.faith = 8
        
        with patch.object(magic_guild, '_show_dialog') as mock_show_dialog:
            magic_guild._analyze_character(character)
            
            # ダイアログが呼ばれることを確認
            mock_show_dialog.assert_called_once()
            
            # 呼び出された引数を取得
            call_args = mock_show_dialog.call_args[0]
            analysis_text = call_args[2]  # 3番目の引数が分析テキスト
            
            # 魔法適性が正しく判定されることを確認
            assert "【魔法適性】" in analysis_text
            assert "攻撃魔法の習得・使用が可能" in analysis_text
            
            # 具体的な使用条件が表示されることを確認
            assert "【魔法使用条件】" in analysis_text
            assert "現在の知恵: 20" in analysis_text
            assert "✓ 攻撃魔法使用可能" in analysis_text
            
            # 信仰心が不足している場合の表示
            assert "現在の信仰心: 8" in analysis_text
            assert "✗ 回復魔法使用可能" in analysis_text
    
    def test_magic_guild_analysis_high_stats_non_magic_class(self):
        """魔術師ギルドで非魔法職の高能力値キャラクター分析テスト"""
        magic_guild = MagicGuild()
        
        # 戦士（知恵・信仰心ともに高い）
        character = Mock()
        character.name = "賢い戦士"
        character.get_race_name.return_value = "人間"
        character.get_class_name.return_value = "戦士"  # 非魔法職
        character.experience.level = 10
        character.base_stats = Mock()
        character.base_stats.intelligence = 15
        character.base_stats.faith = 14
        
        with patch.object(magic_guild, '_show_dialog') as mock_show_dialog:
            magic_guild._analyze_character(character)
            
            # 呼び出された引数を取得
            call_args = mock_show_dialog.call_args[0]
            analysis_text = call_args[2]
            
            # 能力値による限定的な魔法使用が可能と判定されることを確認
            assert "【魔法適性】" in analysis_text
            assert "能力値により限定的な魔法使用が可能" in analysis_text
            assert "知恵により基本的な攻撃魔法が使用可能" in analysis_text
            assert "信仰心により基本的な回復魔法が使用可能" in analysis_text
    
    def test_magic_guild_analysis_low_stats_character(self):
        """魔術師ギルドで低能力値キャラクター分析テスト"""
        magic_guild = MagicGuild()
        
        # 低能力値キャラクター
        character = Mock()
        character.name = "新人冒険者"
        character.get_race_name.return_value = "ホビット"
        character.get_class_name.return_value = "盗賊"
        character.experience.level = 1
        character.base_stats = Mock()
        character.base_stats.intelligence = 8
        character.base_stats.faith = 6
        
        with patch.object(magic_guild, '_show_dialog') as mock_show_dialog:
            magic_guild._analyze_character(character)
            
            # 呼び出された引数を取得
            call_args = mock_show_dialog.call_args[0]
            analysis_text = call_args[2]
            
            # 魔法使用不可と判定されることを確認
            assert "魔法の習得・使用はできません" in analysis_text
            
            # 改善提案が表示されることを確認
            assert "【改善提案】" in analysis_text
            assert "知恵を 4 ポイント上げると攻撃魔法使用可能" in analysis_text
            assert "信仰心を 6 ポイント上げると回復魔法使用可能" in analysis_text