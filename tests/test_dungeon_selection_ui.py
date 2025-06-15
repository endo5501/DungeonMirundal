"""ダンジョン選択UIのテスト"""

import pytest
from unittest.mock import Mock, patch
from src.ui.dungeon_selection_ui import DungeonSelectionUI
from src.character.party import Party
from src.character.character import Character
from src.character.stats import BaseStats


class TestDungeonSelectionUI:
    """ダンジョン選択UIのテスト"""
    
    def setup_method(self):
        """各テストメソッドの前に実行"""
        self.dungeon_ui = DungeonSelectionUI()
        
        # テスト用パーティを作成
        self.party = Party(party_id="test_party")
        
        # レベル10のキャラクターを作成（複数ダンジョンにアクセス可能）
        stats = BaseStats(strength=15, agility=12, intelligence=14, faith=10, luck=13)
        character = Character.create_character("TestHero", "human", "fighter", stats)
        character.experience.level = 10  # レベル10に設定
        
        self.party.add_character(character)
    
    def test_load_dungeons_config(self):
        """ダンジョン設定読み込みテスト"""
        config = self.dungeon_ui._load_dungeons_config()
        
        # 設定が正しく読み込まれていることを確認
        assert "dungeons" in config
        assert len(config["dungeons"]) > 0
        
        # 各ダンジョンに必要な情報が含まれていることを確認
        for dungeon_id, dungeon_info in config["dungeons"].items():
            assert "name" in dungeon_info
            assert "difficulty" in dungeon_info
            assert "floors" in dungeon_info
            assert "unlock_condition" in dungeon_info
    
    def test_get_available_dungeons_level_1(self):
        """レベル1パーティの利用可能ダンジョンテスト"""
        # レベル1のキャラクターを作成
        stats = BaseStats(strength=10, agility=10, intelligence=10, faith=10, luck=10)
        character = Character.create_character("Newbie", "human", "fighter", stats)
        character.experience.level = 1
        
        party = Party(party_id="newbie_party")
        party.add_character(character)
        
        available = self.dungeon_ui._get_available_dungeons(party)
        
        # レベル1では始まりの洞窟と練習用ダンジョンのみアクセス可能
        available_names = [d["name"] for d in available]
        assert "始まりの洞窟" in available_names
        assert "練習用ダンジョン" in available_names
        
        # 高レベルダンジョンはアクセス不可
        assert "古の遺跡" not in available_names
        assert "魔の迷宮" not in available_names
        assert "竜の巣窟" not in available_names
    
    def test_get_available_dungeons_level_10(self):
        """レベル10パーティの利用可能ダンジョンテスト"""
        available = self.dungeon_ui._get_available_dungeons(self.party)
        
        # レベル10では複数のダンジョンにアクセス可能
        available_names = [d["name"] for d in available]
        assert "始まりの洞窟" in available_names
        assert "古の遺跡" in available_names
        assert "魔の迷宮" in available_names
        assert "練習用ダンジョン" in available_names
        
        # 最高レベルダンジョンはまだアクセス不可
        assert "竜の巣窟" not in available_names
    
    def test_get_available_dungeons_level_20(self):
        """レベル20パーティの利用可能ダンジョンテスト"""
        # レベル20のキャラクターを作成
        self.party.characters[0].experience.level = 20
        
        available = self.dungeon_ui._get_available_dungeons(self.party)
        
        # レベル20では全ダンジョンにアクセス可能
        available_names = [d["name"] for d in available]
        assert "始まりの洞窟" in available_names
        assert "古の遺跡" in available_names
        assert "魔の迷宮" in available_names
        assert "竜の巣窟" in available_names
        assert "練習用ダンジョン" in available_names
    
    def test_check_unlock_condition(self):
        """アンロック条件チェックテスト"""
        # always条件は常にTrue
        assert self.dungeon_ui._check_unlock_condition("always", 1) == True
        
        # レベル条件のテスト
        assert self.dungeon_ui._check_unlock_condition("level_5", 4) == False
        assert self.dungeon_ui._check_unlock_condition("level_5", 5) == True
        assert self.dungeon_ui._check_unlock_condition("level_5", 10) == True
        
        assert self.dungeon_ui._check_unlock_condition("level_10", 9) == False
        assert self.dungeon_ui._check_unlock_condition("level_10", 10) == True
        
        assert self.dungeon_ui._check_unlock_condition("level_15", 14) == False
        assert self.dungeon_ui._check_unlock_condition("level_15", 15) == True
    
    def test_format_dungeon_display_name(self):
        """ダンジョン表示名フォーマットテスト"""
        dungeon = {
            "name": "始まりの洞窟",
            "difficulty": 1,
            "recommended_level": "1-3",
            "attribute": "物理",
            "floors": 5
        }
        
        display_name = self.dungeon_ui._format_dungeon_display_name(dungeon)
        
        # 期待される形式で表示されることを確認
        assert "始まりの洞窟" in display_name
        assert "★" in display_name  # 難易度星表示
        assert "1-3" in display_name  # 推奨レベル
        assert "物理" in display_name  # 属性
        assert "5階" in display_name  # 階数
    
    @patch('src.ui.base_ui.ui_manager.show_menu')
    def test_show_dungeon_selection(self, mock_show_menu):
        """ダンジョン選択表示テスト"""
        mock_on_selected = Mock()
        mock_on_cancel = Mock()
        
        self.dungeon_ui.show_dungeon_selection(
            self.party, 
            mock_on_selected, 
            mock_on_cancel
        )
        
        # メニューが表示されることを確認
        mock_show_menu.assert_called_once()
        
        # コールバックが正しく設定されることを確認
        assert self.dungeon_ui.on_dungeon_selected == mock_on_selected
        assert self.dungeon_ui.on_cancel == mock_on_cancel
        assert self.dungeon_ui.current_party == self.party
    
    @patch('src.ui.base_ui.ui_manager.show_dialog')
    def test_show_no_dungeons_dialog(self, mock_show_dialog):
        """利用可能ダンジョンなしダイアログテスト"""
        # パーティを空にしてダンジョンアクセス不可状態を作る
        empty_party = Party(party_id="empty_party")
        
        mock_on_cancel = Mock()
        
        self.dungeon_ui.show_dungeon_selection(
            empty_party,
            Mock(),
            mock_on_cancel
        )
        
        # ダイアログが表示されることを確認
        mock_show_dialog.assert_called_once()
    
    @patch('src.ui.base_ui.ui_manager.show_dialog')
    def test_show_dungeon_confirmation(self, mock_show_dialog):
        """ダンジョン確認ダイアログテスト"""
        dungeon_info = {
            "name": "始まりの洞窟",
            "description": "テスト用ダンジョン",
            "difficulty": 1,
            "recommended_level": "1-3",
            "attribute": "物理",
            "floors": 5
        }
        
        self.dungeon_ui._show_dungeon_confirmation("beginners_cave", dungeon_info)
        
        # 確認ダイアログが表示されることを確認
        mock_show_dialog.assert_called_once()
        
        # ダイアログの内容に必要な情報が含まれることを確認
        call_args = mock_show_dialog.call_args[0][0]
        assert call_args.title == "ダンジョン入場確認"
        assert "始まりの洞窟" in call_args.message
        assert "1-3" in call_args.message
        assert "物理" in call_args.message
        assert "5階" in call_args.message
    
    def test_select_dungeon_invalid_id(self):
        """無効なダンジョンID選択テスト"""
        # ログ出力のテストは実装の詳細なので、例外が発生しないことを確認
        try:
            self.dungeon_ui._select_dungeon("invalid_dungeon_id")
            # エラーが発生しないことを確認（実装によってはreturnで早期終了）
        except Exception as e:
            pytest.fail(f"無効なダンジョンIDでの処理で例外が発生: {e}")
    
    @patch('src.ui.base_ui.ui_manager.close_current_menu')
    def test_confirm_dungeon_selection(self, mock_close_menu):
        """ダンジョン選択確定テスト"""
        mock_on_selected = Mock()
        self.dungeon_ui.on_dungeon_selected = mock_on_selected
        
        self.dungeon_ui._confirm_dungeon_selection("beginners_cave")
        
        # メニューが閉じられることを確認
        mock_close_menu.assert_called_once()
        
        # コールバックが呼ばれることを確認
        mock_on_selected.assert_called_once_with("beginners_cave")
    
    @patch('src.ui.base_ui.ui_manager.close_current_menu')
    def test_cancel_selection(self, mock_close_menu):
        """選択キャンセルテスト"""
        mock_on_cancel = Mock()
        self.dungeon_ui.on_cancel = mock_on_cancel
        
        self.dungeon_ui._cancel_selection()
        
        # メニューが閉じられることを確認
        mock_close_menu.assert_called_once()
        
        # キャンセルコールバックが呼ばれることを確認
        mock_on_cancel.assert_called_once()