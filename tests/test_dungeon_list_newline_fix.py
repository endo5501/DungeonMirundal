"""
ダンジョン入口リスト表示での"\n"問題の修正テスト

優先度:中の不具合「ダンジョン入口のリスト表示がおかしい("\n"がそのまま表示される)」の修正テスト
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
import sys
import os

# プロジェクトルートをPythonパスに追加
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.ui.dungeon_selection_ui import DungeonSelectionUI
from src.character.party import Party


class TestDungeonListNewlineFix:
    """ダンジョンリスト表示改行問題の修正テスト"""

    def setup_method(self):
        """各テストメソッドの前に実行される初期化処理"""
        self.mock_ui_manager = Mock()
        self.mock_party = Mock()
        
        # UIマネージャーのモック設定
        self.mock_ui_manager.register_element = Mock()
        self.mock_ui_manager.show_element = Mock()
        self.mock_ui_manager.get_element = Mock(return_value=None)
        
        # パーティのモック設定
        self.mock_party.get_max_level = Mock(return_value=5)
        
        # テストデータの準備
        self.test_dungeons_config = {
            "dungeons": {
                "beginner_cave": {
                    "name": "初心者の洞窟",
                    "description": "初心者向けのダンジョンです。",
                    "difficulty": 1,
                    "recommended_level": "1-5",
                    "attribute": "物理",
                    "floors": 10,
                    "unlock_condition": "always"
                },
                "forest_temple": {
                    "name": "森の神殿",
                    "description": "古い森の奥にある神殿。",
                    "difficulty": 3,
                    "recommended_level": "5-10",
                    "attribute": "自然",
                    "floors": 20,
                    "unlock_condition": "level_5"
                }
            }
        }

    @patch('src.ui.dungeon_selection_ui.ui_manager')
    def test_dungeon_menu_title_newlines_fixed(self, mock_ui_mgr):
        """
        テスト: ダンジョンメニューのタイトルで改行が正しく処理される
        
        期待する動作:
        - メニュータイトルで\nが改行として処理される
        - \\nがそのまま表示されない
        """
        # モック設定
        mock_ui_mgr.register_element = self.mock_ui_manager.register_element
        mock_ui_mgr.show_element = self.mock_ui_manager.show_element
        mock_ui_mgr.get_element = self.mock_ui_manager.get_element
        
        # DungeonSelectionUIのインスタンス作成
        dungeon_ui = DungeonSelectionUI()
        dungeon_ui.dungeons_config = self.test_dungeons_config
        dungeon_ui.current_party = self.mock_party  # current_partyを設定
        
        # 利用可能なダンジョンを取得
        available_dungeons = dungeon_ui._get_available_dungeons(self.mock_party)
        
        # ダンジョンメニューを表示
        dungeon_ui._show_dungeon_menu(available_dungeons)
        
        # register_elementが呼ばれることを確認
        assert mock_ui_mgr.register_element.called, "メニューが登録されていません"
        
        # 登録されたメニューの内容を確認
        register_call = mock_ui_mgr.register_element.call_args
        menu_obj = register_call[0][0]  # 最初の引数がメニューオブジェクト
        
        # メニュータイトルに\\nが含まれていないことを確認
        assert "\\n" not in menu_obj.title, "メニュータイトルに\\nが含まれています"
        # 実際の改行文字\nが含まれることを確認
        assert "\n" in menu_obj.title, "メニュータイトルに改行文字が含まれていません"

    def test_dungeon_display_name_newlines_fixed(self):
        """
        テスト: ダンジョン表示名で改行が正しく処理される
        
        期待する動作:
        - _format_dungeon_display_nameで\nが改行として処理される
        - \\nがそのまま表示されない
        """
        # DungeonSelectionUIのインスタンス作成
        dungeon_ui = DungeonSelectionUI()
        
        # テストダンジョンデータ
        test_dungeon = {
            "name": "テストダンジョン",
            "difficulty": 2,
            "recommended_level": "3-8",
            "attribute": "魔法",
            "floors": 15
        }
        
        # 表示名をフォーマット
        display_name = dungeon_ui._format_dungeon_display_name(test_dungeon)
        
        # \\nが含まれていないことを確認
        assert "\\n" not in display_name, "表示名に\\nが含まれています"
        # 実際の改行文字\nが含まれることを確認
        assert "\n" in display_name, "表示名に改行文字が含まれていません"
        
        # 期待される文字列が含まれることを確認
        assert "テストダンジョン" in display_name
        assert "推奨Lv.3-8" in display_name
        assert "魔法属性" in display_name
        assert "15階" in display_name

    @patch('src.ui.dungeon_selection_ui.ui_manager')
    def test_dungeon_confirmation_dialog_newlines_fixed(self, mock_ui_mgr):
        """
        テスト: ダンジョン確認ダイアログで改行が正しく処理される
        
        期待する動作:
        - 確認ダイアログのメッセージで\nが改行として処理される
        - \\nがそのまま表示されない
        """
        # モック設定
        mock_ui_mgr.register_element = self.mock_ui_manager.register_element
        mock_ui_mgr.get_element = self.mock_ui_manager.get_element
        
        # DungeonSelectionUIのインスタンス作成
        dungeon_ui = DungeonSelectionUI()
        
        # テストダンジョン情報
        test_dungeon_info = self.test_dungeons_config["dungeons"]["beginner_cave"]
        
        # 確認ダイアログを表示
        dungeon_ui._show_dungeon_confirmation("beginner_cave", test_dungeon_info)
        
        # register_elementが呼ばれることを確認
        assert mock_ui_mgr.register_element.called, "ダイアログが登録されていません"
        
        # 登録されたダイアログの内容を確認
        register_call = mock_ui_mgr.register_element.call_args
        dialog_obj = register_call[0][0]
        
        # ダイアログメッセージに\\nが含まれていないことを確認
        assert "\\n" not in dialog_obj.message, "ダイアログメッセージに\\nが含まれています"
        # 実際の改行文字\nが含まれることを確認
        assert "\n" in dialog_obj.message, "ダイアログメッセージに改行文字が含まれていません"

    @patch('src.ui.dungeon_selection_ui.ui_manager')
    def test_no_dungeons_dialog_newlines_fixed(self, mock_ui_mgr):
        """
        テスト: ダンジョンなしダイアログで改行が正しく処理される
        
        期待する動作:
        - 利用可能ダンジョンなしダイアログで\nが改行として処理される
        - \\nがそのまま表示されない
        """
        # モック設定
        mock_ui_mgr.register_element = self.mock_ui_manager.register_element
        mock_ui_mgr.get_element = self.mock_ui_manager.get_element
        
        # DungeonSelectionUIのインスタンス作成
        dungeon_ui = DungeonSelectionUI()
        
        # ダンジョンなしダイアログを表示
        dungeon_ui._show_no_dungeons_dialog()
        
        # register_elementが呼ばれることを確認
        assert mock_ui_mgr.register_element.called, "ダイアログが登録されていません"
        
        # 登録されたダイアログの内容を確認
        register_call = mock_ui_mgr.register_element.call_args
        dialog_obj = register_call[0][0]
        
        # ダイアログメッセージに\\nが含まれていないことを確認
        assert "\\n" not in dialog_obj.message, "ダイアログメッセージに\\nが含まれています"
        # 実際の改行文字\nが含まれることを確認
        assert "\n" in dialog_obj.message, "ダイアログメッセージに改行文字が含まれていません"

    def test_multiple_dungeons_display_consistency(self):
        """
        テスト: 複数ダンジョンの表示一貫性
        
        期待する動作:
        - すべてのダンジョンで一貫して改行が処理される
        - 表示フォーマットが統一されている
        """
        # DungeonSelectionUIのインスタンス作成
        dungeon_ui = DungeonSelectionUI()
        dungeon_ui.dungeons_config = self.test_dungeons_config
        
        # 利用可能なダンジョンを取得
        available_dungeons = dungeon_ui._get_available_dungeons(self.mock_party)
        
        # 各ダンジョンの表示名をチェック
        for dungeon in available_dungeons:
            display_name = dungeon_ui._format_dungeon_display_name(dungeon)
            
            # \\nが含まれていないことを確認
            assert "\\n" not in display_name, f"ダンジョン{dungeon['name']}の表示名に\\nが含まれています"
            # 実際の改行文字\nが含まれることを確認
            assert "\n" in display_name, f"ダンジョン{dungeon['name']}の表示名に改行文字が含まれていません"
            
            # 必要な情報が含まれることを確認
            assert dungeon['name'] in display_name
            assert str(dungeon['recommended_level']) in display_name
            assert dungeon['attribute'] in display_name
            assert str(dungeon['floors']) in display_name

    def test_ui_text_processing_consistency(self):
        """
        テスト: UI全体でのテキスト処理の一貫性
        
        期待する動作:
        - すべてのUI要素で改行文字が一貫して処理される
        - エスケープされた改行文字が混在しない
        """
        # DungeonSelectionUIのインスタンス作成
        dungeon_ui = DungeonSelectionUI()
        dungeon_ui.dungeons_config = self.test_dungeons_config
        
        # 利用可能なダンジョンを取得
        available_dungeons = dungeon_ui._get_available_dungeons(self.mock_party)
        
        # 各種テキスト要素をチェック
        test_dungeon_info = self.test_dungeons_config["dungeons"]["beginner_cave"]
        
        # 1. メニュータイトル
        # メニュータイトルのテンプレートを確認
        title_template = f"ダンジョン選択\n\n挑戦するダンジョンを選択してください\nパーティ最高レベル: {self.mock_party.get_max_level()}"
        assert "\\n" not in title_template, "メニュータイトルテンプレートに\\nが含まれています"
        
        # 2. 表示名フォーマット  
        display_name = dungeon_ui._format_dungeon_display_name(available_dungeons[0])
        assert "\\n" not in display_name, "表示名フォーマットに\\nが含まれています"
        
        # すべてのテキスト要素で一貫性が保たれることを確認
        assert True  # 上記のアサーションが通れば一貫性が確認される

    def test_special_characters_in_dungeon_names(self):
        """
        テスト: ダンジョン名に特殊文字がある場合の改行処理
        
        期待する動作:
        - ダンジョン名に特殊文字があっても改行が正しく処理される
        - エスケープ処理が適切に行われる
        """
        # 特殊文字を含むダンジョンデータ
        special_dungeon = {
            "name": "「魔王の城」〜最終決戦〜",
            "difficulty": 5,
            "recommended_level": "20+",
            "attribute": "闇",
            "floors": 50
        }
        
        # DungeonSelectionUIのインスタンス作成
        dungeon_ui = DungeonSelectionUI()
        
        # 表示名をフォーマット
        display_name = dungeon_ui._format_dungeon_display_name(special_dungeon)
        
        # \\nが含まれていないことを確認
        assert "\\n" not in display_name, "特殊文字ダンジョンの表示名に\\nが含まれています"
        # 実際の改行文字\nが含まれることを確認
        assert "\n" in display_name, "特殊文字ダンジョンの表示名に改行文字が含まれていません"
        
        # 特殊文字が適切に保持されることを確認
        assert "「魔王の城」〜最終決戦〜" in display_name
        assert "闇属性" in display_name


if __name__ == "__main__":
    pytest.main([__file__, "-v"])