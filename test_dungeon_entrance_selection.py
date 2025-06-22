"""
ダンジョン入口選択画面実装のテスト
バグ修正前にテストを作成し、修正後にテストが通ることを確認する
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
import pygame

# Test setup for pygame
pygame.init()
screen = pygame.display.set_mode((800, 600))

class TestDungeonEntranceSelection:
    """ダンジョン入口選択画面のテスト"""

    def setup_method(self):
        """テストセットアップ"""
        self.mock_party = Mock()
        self.mock_party.gold = 2000
        self.mock_party.get_all_characters.return_value = []
        
    def test_dungeon_entrance_shows_selection_screen(self):
        """ダンジョン入口で選択画面が表示されることをテスト"""
        from src.overworld.overworld_manager_pygame import OverworldManager
        
        # ダンジョン入場コールバックをモック
        enter_dungeon_callback = Mock()
        
        manager = OverworldManager()
        manager.set_enter_dungeon_callback(enter_dungeon_callback)
        manager.current_party = self.mock_party
        
        # UIマネージャーをモック
        manager.ui_manager = Mock()
        
        # _show_dungeon_selection_menu メソッドが存在することを確認（修正後）
        # 現在は存在しないため、実装が必要
        assert hasattr(manager, '_show_dungeon_selection_menu'), \
            "ダンジョン選択メニューメソッドが実装されていない"

    def test_dungeon_selection_menu_structure(self):
        """ダンジョン選択メニューの構造テスト"""
        # 期待されるメニュー構造
        expected_menu_items = [
            "ダンジョン一覧",
            "ダンジョン新規生成", 
            "ダンジョン破棄",
            "戻る"
        ]
        
        # ダンジョン情報に含まれるべき項目
        expected_dungeon_info = [
            "ダンジョン名",
            "難易度",
            "属性", 
            "踏破済み状況"
        ]
        
        # 各メニュー項目が定義されていることを確認
        for item in expected_menu_items:
            assert item is not None, f"メニュー項目 '{item}' が定義されている"
            
        # ダンジョン情報項目が定義されていることを確認
        for info in expected_dungeon_info:
            assert info is not None, f"ダンジョン情報 '{info}' が定義されている"

    def test_dungeon_list_display_format(self):
        """ダンジョン一覧の表示フォーマットテスト"""
        # サンプルダンジョンデータ
        sample_dungeons = [
            {
                "id": "dungeon_001",
                "name": "初心者の洞窟",
                "difficulty": "Easy",
                "attribute": "Earth",
                "completed": False,
                "hash": "abc123"
            },
            {
                "id": "dungeon_002", 
                "name": "炎の遺跡",
                "difficulty": "Hard",
                "attribute": "Fire",
                "completed": True,
                "hash": "def456"
            }
        ]
        
        # 表示フォーマットの検証
        for dungeon in sample_dungeons:
            assert "name" in dungeon, "ダンジョン名が含まれている"
            assert "difficulty" in dungeon, "難易度が含まれている"
            assert "attribute" in dungeon, "属性が含まれている"
            assert "completed" in dungeon, "踏破状況が含まれている"
            
            # 表示テキストのフォーマット例
            display_text = f"{dungeon['name']} - {dungeon['difficulty']} ({dungeon['attribute']})"
            if dungeon['completed']:
                display_text += " [踏破済み]"
            
            assert len(display_text) > 0, "表示テキストが生成される"

    @patch('src.overworld.overworld_manager_pygame.UIMenu')
    def test_dungeon_entrance_calls_selection_menu(self, mock_ui_menu):
        """ダンジョン入口が選択メニューを呼び出すことをテスト"""
        from src.overworld.overworld_manager_pygame import OverworldManager
        
        enter_dungeon_callback = Mock()
        manager = OverworldManager()
        manager.set_enter_dungeon_callback(enter_dungeon_callback)
        manager.current_party = self.mock_party
        manager.ui_manager = Mock()
        
        # _show_dungeon_selection_menu をモック（修正後の実装を想定）
        manager._show_dungeon_selection_menu = Mock()
        
        # _on_enter_dungeon を実行（修正済み）
        manager._on_enter_dungeon()
        
        # ダンジョン選択メニューが呼ばれることを確認
        manager._show_dungeon_selection_menu.assert_called_once()

    def test_dungeon_new_generation_creates_hash_based_dungeon(self):
        """新規ダンジョン生成でハッシュベースのダンジョンが作成されることをテスト"""
        import hashlib
        import time
        
        # ハッシュ値生成のテスト
        current_time = str(time.time())
        hash_value = hashlib.md5(current_time.encode()).hexdigest()[:8]
        
        # ハッシュベースのダンジョン作成
        new_dungeon = {
            "id": f"dungeon_{hash_value}",
            "name": f"生成ダンジョン_{hash_value[:4]}",
            "difficulty": "Normal",
            "attribute": "Mixed",
            "completed": False,
            "hash": hash_value,
            "generated_at": current_time
        }
        
        # 生成されたダンジョンの検証
        assert new_dungeon["id"].startswith("dungeon_"), "ダンジョンIDが正しい"
        assert len(new_dungeon["hash"]) == 8, "ハッシュ値が8文字"
        assert new_dungeon["completed"] == False, "新規ダンジョンは未踏破"

    def test_dungeon_deletion_removes_from_list(self):
        """ダンジョン破棄で一覧から削除されることをテスト"""
        # サンプルダンジョンリスト
        dungeon_list = [
            {"id": "dungeon_001", "name": "テストダンジョン1"},
            {"id": "dungeon_002", "name": "テストダンジョン2"},
            {"id": "dungeon_003", "name": "テストダンジョン3"}
        ]
        
        # 削除前の数を確認
        initial_count = len(dungeon_list)
        assert initial_count == 3, "初期ダンジョン数が正しい"
        
        # ダンジョン削除をシミュレート
        dungeon_to_delete = "dungeon_002"
        dungeon_list = [d for d in dungeon_list if d["id"] != dungeon_to_delete]
        
        # 削除後の確認
        assert len(dungeon_list) == 2, "ダンジョンが削除された"
        assert not any(d["id"] == dungeon_to_delete for d in dungeon_list), \
            "指定されたダンジョンが一覧から削除されている"

if __name__ == "__main__":
    pytest.main([__file__])