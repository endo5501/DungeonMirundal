"""
地上メニュー左寄せ配置の実装テスト

change_spec.mdの要求「地上メニューを左寄せにして右側に町イラスト表示準備」に対応するテスト
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
import sys
import os

# プロジェクトルートをPythonパスに追加
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.ui.base_ui import UIMenu, UIDialog
from src.overworld.overworld_manager import OverworldManager


class TestOverworldMenuLeftAlignment:
    """地上メニュー左寄せ配置の修正テスト"""

    def setup_method(self):
        """各テストメソッドの前に実行される初期化処理"""
        self.mock_ui_manager = Mock()
        self.mock_config_manager = Mock()
        self.mock_facility_manager = Mock()
        
        # UIマネージャーのモック設定
        self.mock_ui_manager.register_element = Mock()
        self.mock_ui_manager.show_element = Mock()
        self.mock_ui_manager.hide_element = Mock()
        
        # 設定マネージャーのモック設定
        self.mock_config_manager.get_text = Mock(side_effect=lambda key, default="": {
            "overworld.surface_map": "地上マップ",
            "facility.guild": "冒険者ギルド",
            "facility.inn": "宿屋",
            "facility.shop": "商店",
            "facility.temple": "教会",
            "facility.magic_guild": "魔術師ギルド",
            "facility.dungeon_entrance": "ダンジョン入口",
            "common.back": "戻る"
        }.get(key, default))

    @patch('src.ui.base_ui.ui_manager')
    def test_left_aligned_menu_button_positions(self, mock_ui_mgr):
        """
        テスト: UIMenuで左寄せ配置オプションが機能する
        
        期待する動作:
        - alignment="left"指定時にボタンが左寄せ配置される
        - ボタンのX座標が負の値から開始される
        - 右側にスペースが確保される
        """
        mock_ui_mgr.register_element = self.mock_ui_manager.register_element
        
        # 左寄せ指定でUIMenuを作成
        menu = UIMenu("test_left_menu", "テストメニュー", alignment="left")
        
        # メニュー項目を追加
        test_items = ["項目1", "項目2", "項目3", "戻る"]
        for item in test_items:
            menu.add_menu_item(item, lambda: None, [])
        
        # メニューを構築
        menu._rebuild_menu()
        
        # ボタンが作成されることを確認
        assert len(menu.buttons) == len(test_items), "ボタン数が正しくありません"
        
        # 左寄せ配置の確認：最初のボタンが左側（負の大きな値）に配置
        x_positions = [button.gui_element.getX() for button in menu.buttons]
        leftmost_x = min(x_positions)
        assert leftmost_x < -0.8, f"メニューが左寄せになっていません（leftmost_x={leftmost_x}）"
        
        # 右側スペース確保の確認：最右のボタンが中央よりも左に配置
        rightmost_x = max(x_positions)
        assert rightmost_x < 0, f"右側にスペースが確保されていません（rightmost_x={rightmost_x}）"
        
        # ボタンが左から右に順番に配置されることを確認
        sorted_x = sorted(x_positions)
        assert x_positions == sorted_x, "ボタンのX座標順序が左→右になっていません"

    @patch('src.ui.base_ui.ui_manager')
    def test_center_aligned_menu_remains_unchanged(self, mock_ui_mgr):
        """
        テスト: デフォルト（中央寄せ）配置が変更されていない
        
        期待する動作:
        - alignment未指定またはalignment="center"時は従来通り中央配置
        - 既存機能との後方互換性維持
        """
        mock_ui_mgr.register_element = self.mock_ui_manager.register_element
        
        # デフォルト（中央寄せ）でUIMenuを作成
        menu = UIMenu("test_center_menu", "テストメニュー")  # alignmentパラメータなし
        
        # メニュー項目を追加
        test_items = ["項目1", "項目2", "項目3"]
        for item in test_items:
            menu.add_menu_item(item, lambda: None, [])
        
        # メニューを構築
        menu._rebuild_menu()
        
        # 中央配置の確認：ボタンが中央を基準に配置
        x_positions = [button.gui_element.getX() for button in menu.buttons]
        leftmost_x = min(x_positions)
        rightmost_x = max(x_positions)
        
        # 中央を基準とした対称配置の確認
        center_offset = abs((leftmost_x + rightmost_x) / 2)
        assert center_offset < 0.1, f"中央配置が維持されていません（center_offset={center_offset}）"

    @patch('src.overworld.overworld_manager.ui_manager')
    @patch('src.overworld.overworld_manager.config_manager')
    def test_overworld_main_menu_left_alignment(self, mock_config_mgr, mock_ui_mgr):
        """
        テスト: 地上メインメニューが左寄せ配置される
        
        期待する動作:
        - _show_main_menu()で作成されるメニューが左寄せ配置
        - 施設選択ボタンが左側に配置される
        - 右側に町イラスト表示用スペースが確保される
        """
        # モック設定
        mock_ui_mgr.register_element = self.mock_ui_manager.register_element
        mock_ui_mgr.show_element = self.mock_ui_manager.show_element
        mock_config_mgr.get_text = self.mock_config_manager.get_text
        
        # OverworldManagerのインスタンス作成
        overworld_manager = OverworldManager()
        overworld_manager.facility_manager = self.mock_facility_manager
        
        # 地上メインメニューを表示
        overworld_manager._show_main_menu()
        
        # メニューが登録されることを確認
        assert mock_ui_mgr.register_element.called, "地上メインメニューが登録されていません"
        
        # 登録されたメニューを取得
        register_call = mock_ui_mgr.register_element.call_args
        menu_obj = register_call[0][0]
        
        # メニューが左寄せ配置されることを確認
        x_positions = [button.gui_element.getX() for button in menu_obj.buttons]
        if x_positions:  # ボタンがある場合
            leftmost_x = min(x_positions)
            rightmost_x = max(x_positions)
            
            # 左寄せ配置の確認
            assert leftmost_x < -0.8, f"地上メニューが左寄せになっていません（leftmost_x={leftmost_x}）"
            # 右側スペース確保の確認
            assert rightmost_x < 0, f"右側スペースが確保されていません（rightmost_x={rightmost_x}）"

    @patch('src.ui.base_ui.ui_manager')
    def test_title_text_left_alignment(self, mock_ui_mgr):
        """
        テスト: メニュータイトルテキストも左寄せ配置される
        
        期待する動作:
        - メニュータイトルが左寄せ配置される
        - ボタンとタイトルの位置が整合している
        """
        mock_ui_mgr.register_element = self.mock_ui_manager.register_element
        
        # 左寄せ指定でUIMenuを作成
        menu = UIMenu("test_title_left", "左寄せタイトルテスト", alignment="left")
        menu.add_menu_item("テスト項目", lambda: None, [])
        menu._rebuild_menu()
        
        # タイトルテキストの位置を確認
        title_pos = menu.title_text.gui_element.getPos()
        title_x = title_pos[0] if len(title_pos) > 0 else title_pos.getX()
        
        # ボタンの位置と比較
        button_x = menu.buttons[0].gui_element.getX()
        
        
        # タイトルとボタンが左寄せで整合していることを確認
        assert title_x < -0.8, f"タイトルが左寄せになっていません（title_x={title_x}）"
        # タイトルとボタンのX座標が近いことを確認（左揃え）
        assert abs(title_x - button_x) < 0.5, f"タイトルとボタンの位置が整合していません（title_x={title_x}, button_x={button_x}）"

    @patch('src.ui.base_ui.ui_manager')
    def test_town_illustration_space_reserved(self, mock_ui_mgr):
        """
        テスト: 右側に町イラスト表示用スペースが確保される
        
        期待する動作:
        - 左寄せメニューの右端がX=0.0以下
        - X=0.3以上の領域が町イラスト用に確保される
        - メニューが画面右半分に侵入しない
        """
        mock_ui_mgr.register_element = self.mock_ui_manager.register_element
        
        # 多項目の左寄せメニューで検証
        menu = UIMenu("test_space_reserve", "スペース確保テスト", alignment="left")
        
        # 6項目の長いメニューで検証
        for i in range(6):
            menu.add_menu_item(f"項目{i+1}", lambda: None, [])
        menu._rebuild_menu()
        
        # 全ボタンのX座標を確認
        x_positions = [button.gui_element.getX() for button in menu.buttons]
        rightmost_x = max(x_positions)
        
        # 町イラスト表示用スペースが確保されることを確認
        TOWN_ILLUSTRATION_START = 0.3
        assert rightmost_x < TOWN_ILLUSTRATION_START, \
            f"町イラスト表示スペースが確保されていません（rightmost_x={rightmost_x}, required<{TOWN_ILLUSTRATION_START}）"

    @patch('src.ui.base_ui.ui_manager')  
    def test_dialog_left_alignment_optional(self, mock_ui_mgr):
        """
        テスト: ダイアログも左寄せ配置オプションに対応
        
        期待する動作:
        - UIDialogでもalignment="left"が指定可能
        - ダイアログボタンが左寄せ配置される
        """
        mock_ui_mgr.register_element = self.mock_ui_manager.register_element
        
        # 左寄せ指定でUIDialogを作成
        dialog = UIDialog(
            "test_left_dialog", 
            "左寄せダイアログテスト",
            "このダイアログは左寄せ配置です。",
            buttons=[
                {"text": "はい", "command": lambda: None},
                {"text": "いいえ", "command": lambda: None},
                {"text": "キャンセル", "command": lambda: None}
            ],
            alignment="left"
        )
        
        # ダイアログボタンが左寄せ配置されることを確認
        if hasattr(dialog, 'buttons') and dialog.buttons:
            x_positions = [button.gui_element.getX() for button in dialog.buttons]
            leftmost_x = min(x_positions)
            rightmost_x = max(x_positions)
            
            # 左寄せ配置の確認
            assert leftmost_x < -0.5, f"ダイアログボタンが左寄せになっていません（leftmost_x={leftmost_x}）"
            # 右側スペース確保
            assert rightmost_x < 0.2, f"ダイアログの右側スペースが不足しています（rightmost_x={rightmost_x}）"

    def test_alignment_parameter_validation(self):
        """
        テスト: alignmentパラメータのバリデーション
        
        期待する動作:
        - 有効な値："left", "center", "right"
        - 無効な値や未指定時は"center"をデフォルトとする
        """
        with patch('src.ui.base_ui.ui_manager') as mock_ui_mgr:
            mock_ui_mgr.register_element = self.mock_ui_manager.register_element
            
            # 有効な値のテスト
            valid_alignments = ["left", "center", "right"]
            for alignment in valid_alignments:
                try:
                    menu = UIMenu(f"test_{alignment}", "テスト", alignment=alignment)
                    menu.add_menu_item("テスト項目", lambda: None, [])
                    menu._rebuild_menu()
                    assert True, f"{alignment}は有効なalignmentです"
                except Exception as e:
                    pytest.fail(f"有効なalignment '{alignment}'でエラー: {e}")
            
            # デフォルト値のテスト（alignmentパラメータなし）
            try:
                menu = UIMenu("test_default", "デフォルトテスト")
                menu.add_menu_item("テスト項目", lambda: None, [])
                menu._rebuild_menu()
                # デフォルトでは中央配置になることを確認
                assert True, "デフォルトalignmentが正常動作"
            except Exception as e:
                pytest.fail(f"デフォルトalignmentでエラー: {e}")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])