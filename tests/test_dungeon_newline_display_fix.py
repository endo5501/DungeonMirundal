"""ダンジョン選択UIの改行文字表示問題のテスト"""

import pytest
from unittest.mock import Mock, patch
from src.ui.dungeon_selection_ui import DungeonSelectionUI
from src.character.party import Party
from src.character.character import Character
from src.character.stats import BaseStats


class TestDungeonNewlineDisplayFix:
    """ダンジョン選択UIの改行文字表示問題のテスト"""
    
    def setup_method(self):
        """各テストメソッドの前に実行"""
        self.dungeon_ui = DungeonSelectionUI()
        
        # テスト用パーティを作成
        self.party = Party(party_id="test_party")
        stats = BaseStats(strength=15, agility=12, intelligence=14, faith=10, luck=13)
        character = Character.create_character("TestHero", "human", "fighter", stats)
        character.experience.level = 10
        self.party.add_character(character)
    
    def test_format_dungeon_display_name_no_escaped_newlines(self):
        """ダンジョン表示名フォーマットでエスケープされた改行文字が含まれないことをテスト"""
        dungeon = {
            "name": "始まりの洞窟",
            "difficulty": 1,
            "recommended_level": "1-3",
            "attribute": "物理",
            "floors": 5
        }
        
        display_name = self.dungeon_ui._format_dungeon_display_name(dungeon)
        
        # \\n（エスケープされた改行文字）が含まれていないことを確認
        assert "\\n" not in display_name, f"表示名にエスケープされた改行文字が含まれています: {display_name}"
        
        # 実際の改行文字（\n）が含まれていることを確認
        assert "\n" in display_name, f"表示名に改行文字が含まれていません: {display_name}"
        
        # 期待される内容が含まれていることを確認
        assert "始まりの洞窟" in display_name
        assert "★" in display_name
        assert "1-3" in display_name
        assert "物理" in display_name
        assert "5階" in display_name
    
    def test_dungeon_menu_title_no_escaped_newlines(self):
        """ダンジョンメニューのタイトルでエスケープされた改行文字が含まれないことをテスト"""
        with patch('src.ui.base_ui.ui_manager.register_element') as mock_register, \
             patch('src.ui.base_ui.ui_manager.show_element'):
            
            # ダンジョン選択を表示
            self.dungeon_ui.show_dungeon_selection(
                self.party, 
                Mock(), 
                Mock()
            )
            
            # UIMenuが登録されたことを確認
            mock_register.assert_called_once()
            registered_menu = mock_register.call_args[0][0]
            
            # タイトルにエスケープされた改行文字が含まれていないことを確認
            assert "\\n" not in registered_menu.title, f"メニュータイトルにエスケープされた改行文字が含まれています: {registered_menu.title}"
            
            # 実際の改行文字が含まれていることを確認
            assert "\n" in registered_menu.title, f"メニュータイトルに改行文字が含まれていません: {registered_menu.title}"
    
    def test_dungeon_confirmation_dialog_no_escaped_newlines(self):
        """ダンジョン確認ダイアログでエスケープされた改行文字が含まれないことをテスト"""
        dungeon_info = {
            "name": "始まりの洞窟",
            "description": "冒険者たちが最初に挑戦する洞窟です。\n比較的弱い魔物が生息しています。",
            "difficulty": 1,
            "recommended_level": "1-3",
            "attribute": "物理",
            "floors": 5
        }
        
        with patch('src.ui.base_ui.ui_manager.register_element') as mock_register, \
             patch('src.ui.base_ui.ui_manager.show_element'):
            
            self.dungeon_ui._show_dungeon_confirmation("beginners_cave", dungeon_info)
            
            # UIDialogが登録されたことを確認
            mock_register.assert_called_once()
            registered_dialog = mock_register.call_args[0][0]
            
            # メッセージにエスケープされた改行文字が含まれていないことを確認
            assert "\\n" not in registered_dialog.message, f"ダイアログメッセージにエスケープされた改行文字が含まれています: {registered_dialog.message}"
            
            # 実際の改行文字が含まれていることを確認
            assert "\n" in registered_dialog.message, f"ダイアログメッセージに改行文字が含まれていません: {registered_dialog.message}"
    
    def test_no_dungeons_dialog_no_escaped_newlines(self):
        """利用可能ダンジョンなしダイアログでエスケープされた改行文字が含まれないことをテスト"""
        with patch('src.ui.base_ui.ui_manager.register_element') as mock_register, \
             patch('src.ui.base_ui.ui_manager.show_element'):
            
            self.dungeon_ui._show_no_dungeons_dialog()
            
            # UIDialogが登録されたことを確認
            mock_register.assert_called_once()
            registered_dialog = mock_register.call_args[0][0]
            
            # メッセージにエスケープされた改行文字が含まれていないことを確認
            assert "\\n" not in registered_dialog.message, f"ダイアログメッセージにエスケープされた改行文字が含まれています: {registered_dialog.message}"
            
            # 実際の改行文字が含まれていることを確認
            assert "\n" in registered_dialog.message, f"ダイアログメッセージに改行文字が含まれていません: {registered_dialog.message}"
    
    def test_dungeon_description_from_config_has_proper_newlines(self):
        """設定ファイルからのダンジョン説明に適切な改行文字が含まれることをテスト"""
        config = self.dungeon_ui._load_dungeons_config()
        
        # 各ダンジョンの説明をチェック
        for dungeon_id, dungeon_info in config.get("dungeons", {}).items():
            description = dungeon_info.get("description", "")
            if description:
                # 説明にエスケープされた改行文字が含まれていないことを確認
                assert "\\n" not in description, f"ダンジョン {dungeon_id} の説明にエスケープされた改行文字が含まれています: {description}"
                
                # 複数行の説明の場合、実際の改行文字が含まれていることを確認
                if "\n" in description:
                    lines = description.split("\n")
                    assert len(lines) > 1, f"ダンジョン {dungeon_id} の説明で改行文字が適切に処理されていません: {description}"
    
    def test_multiline_text_display_formatting(self):
        """複数行テキストの表示フォーマットが正しく処理されることをテスト"""
        # 複数行テキストのサンプル
        multiline_text = "これは1行目\nこれは2行目\nこれは3行目"
        
        # エスケープされた改行文字が含まれていないことを確認
        assert "\\n" not in multiline_text
        
        # 実際の改行文字で分割できることを確認
        lines = multiline_text.split("\n")
        assert len(lines) == 3
        assert lines[0] == "これは1行目"
        assert lines[1] == "これは2行目"
        assert lines[2] == "これは3行目"
    
    def test_display_text_newline_conversion(self):
        """表示テキストでの改行文字変換をテスト"""  
        # 現在の実装で問題となっているパターンをテスト
        problematic_text = "ダンジョン選択\\n\\n挑戦するダンジョンを選択してください"
        
        # この文字列にエスケープされた改行文字が含まれていることを確認（問題状況を再現）
        assert "\\n" in problematic_text
        
        # 正しい改行文字に変換
        corrected_text = problematic_text.replace("\\n", "\n")
        
        # 変換後はエスケープされた改行文字が含まれていないことを確認
        assert "\\n" not in corrected_text
        
        # 実際の改行文字が含まれていることを確認
        assert "\n" in corrected_text
        
        # 正しく分割できることを確認
        lines = corrected_text.split("\n")
        assert "ダンジョン選択" in lines[0]
        assert "挑戦するダンジョンを選択してください" in lines[-1]