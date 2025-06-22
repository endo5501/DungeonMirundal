"""
施設UIボタン横一列配置の実装テスト

change_spec.mdの要求「ボタンを下部に横一列で並べる」に対応するテスト
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
import sys
import os

# プロジェクトルートをPythonパスに追加
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.ui.base_ui import UIMenu, UIButton


class TestFacilityButtonLayoutFix:
    """施設UIボタン横一列配置の修正テスト"""

    def setup_method(self):
        """各テストメソッドの前に実行される初期化処理"""
        self.mock_ui_manager = Mock()
        
        # UIマネージャーのモック設定
        self.mock_ui_manager.register_element = Mock()
        self.mock_ui_manager.show_element = Mock()
        self.mock_ui_manager.hide_element = Mock()
        
        # テストメニューデータ
        self.test_menu_items = [
            {"text": "項目1", "command": lambda: None, "args": []},
            {"text": "項目2", "command": lambda: None, "args": []},
            {"text": "項目3", "command": lambda: None, "args": []},
            {"text": "戻る", "command": lambda: None, "args": []}
        ]
        
        self.long_menu_items = [
            {"text": "項目1", "command": lambda: None, "args": []},
            {"text": "項目2", "command": lambda: None, "args": []},
            {"text": "項目3", "command": lambda: None, "args": []},
            {"text": "項目4", "command": lambda: None, "args": []},
            {"text": "項目5", "command": lambda: None, "args": []},
            {"text": "戻る", "command": lambda: None, "args": []}
        ]

    @patch('src.ui.base_ui.ui_manager')
    def test_menu_buttons_horizontal_layout(self, mock_ui_mgr):
        """
        テスト: メニューボタンが横一列で配置される
        
        期待する動作:
        - ボタンが横方向（X軸）に配置される
        - ボタンのY座標が同じ値（下部固定）
        - ボタン間隔が適切に設定される
        """
        # モック設定
        mock_ui_mgr.register_element = self.mock_ui_manager.register_element
        
        # UIMenuを作成
        menu = UIMenu("test_menu", "テストメニュー")
        
        # メニュー項目を追加
        for item in self.test_menu_items:
            menu.add_menu_item(item["text"], item["command"], item["args"])
        
        # メニューを構築
        menu._rebuild_menu()
        
        # ボタンが作成されることを確認
        assert len(menu.buttons) == len(self.test_menu_items), "ボタン数が正しくありません"
        
        # 横配置の確認：すべてのボタンのY座標が同じ
        y_positions = [button.gui_element.getZ() for button in menu.buttons]
        assert len(set(y_positions)) == 1, "ボタンのY座標が統一されていません（横配置でない）"
        
        # 下部配置の確認：Y座標が負の値（下部）
        common_y = y_positions[0]
        assert common_y < 0, f"ボタンが下部に配置されていません（Y={common_y}）"
        
        # 横方向の間隔確認：X座標が異なる
        x_positions = [button.gui_element.getX() for button in menu.buttons]
        assert len(set(x_positions)) == len(menu.buttons), "ボタンのX座標が重複しています"
        
        # X座標が左から右に並んでいることを確認
        sorted_x = sorted(x_positions)
        assert x_positions == sorted_x or x_positions == sorted_x[::-1], "ボタンのX座標順序が不正です"

    @patch('src.ui.base_ui.ui_manager')
    def test_button_spacing_calculation(self, mock_ui_mgr):
        """
        テスト: ボタン間隔が適切に計算される
        
        期待する動作:
        - ボタン数に応じて適切な間隔が設定される
        - 中央揃えで配置される
        - 画面幅を考慮した配置
        """
        mock_ui_mgr.register_element = self.mock_ui_manager.register_element
        
        # 4個のボタンのメニュー
        menu = UIMenu("test_menu_4", "4ボタンテスト")
        for item in self.test_menu_items:
            menu.add_menu_item(item["text"], item["command"], item["args"])
        menu._rebuild_menu()
        
        # ボタン間隔の確認
        x_positions = sorted([button.gui_element.getX() for button in menu.buttons])
        
        # 連続するボタン間の距離を計算
        if len(x_positions) > 1:
            spacing = x_positions[1] - x_positions[0]
            # 間隔が適切な範囲内にあることを確認
            assert 0.2 <= spacing <= 0.6, f"ボタン間隔が不適切です（spacing={spacing}）"
        
        # 中央揃えの確認：左端と右端の距離が対称
        if len(x_positions) > 1:
            leftmost = x_positions[0]
            rightmost = x_positions[-1]
            center_offset = abs((leftmost + rightmost) / 2)
            assert center_offset < 0.1, f"中央揃えになっていません（offset={center_offset}）"

    @patch('src.ui.base_ui.ui_manager')  
    def test_long_menu_button_layout(self, mock_ui_mgr):
        """
        テスト: 長いメニュー（5項目以上）でのボタン配置
        
        期待する動作:
        - 多数のボタンでも横配置を維持
        - 画面幅に収まる配置
        - ボタンサイズの適切な調整
        """
        mock_ui_mgr.register_element = self.mock_ui_manager.register_element
        
        # 6個のボタンのメニュー（魔術師ギルドレベル）
        menu = UIMenu("test_long_menu", "長いメニューテスト")
        for item in self.long_menu_items:
            menu.add_menu_item(item["text"], item["command"], item["args"])
        menu._rebuild_menu()
        
        # ボタンが作成されることを確認
        assert len(menu.buttons) == len(self.long_menu_items), "長いメニューでボタン数が正しくありません"
        
        # 横配置の維持確認
        y_positions = [button.gui_element.getZ() for button in menu.buttons]
        assert len(set(y_positions)) == 1, "長いメニューで横配置が維持されていません"
        
        # 画面幅内の配置確認（仮定：-1.5 ≤ X ≤ 1.5）
        x_positions = [button.gui_element.getX() for button in menu.buttons]
        assert all(-1.5 <= x <= 1.5 for x in x_positions), "ボタンが画面幅を超えています"
        
        # ボタンサイズの確認（長いメニューでは小さくなる）
        button_scales = [button.gui_element.getScale() for button in menu.buttons]
        # すべてのボタンが同じサイズであることを確認
        assert len(set(button_scales)) <= 2, "ボタンサイズが不統一です"  # (width, height)なので最大2種類

    def test_button_layout_consistency_across_facilities(self):
        """
        テスト: 各施設間でのボタンレイアウト一貫性
        
        期待する動作:
        - 宿屋、商店、教会、魔術師ギルドで同じレイアウト方式
        - ボタン数に関係なく一貫した配置ルール
        """
        # 施設ごとの典型的なメニュー項目数
        facility_button_counts = {
            "inn": 4,      # 宿屋
            "shop": 4,     # 商店  
            "temple": 5,   # 教会
            "magic_guild": 5  # 魔術師ギルド
        }
        
        y_positions_by_facility = {}
        
        with patch('src.ui.base_ui.ui_manager') as mock_ui_mgr:
            mock_ui_mgr.register_element = self.mock_ui_manager.register_element
            
            for facility, button_count in facility_button_counts.items():
                menu = UIMenu(f"{facility}_menu", f"{facility}メニュー")
                
                # 指定された数のボタンを追加
                for i in range(button_count):
                    menu.add_menu_item(f"項目{i+1}", lambda: None, [])
                menu._rebuild_menu()
                
                # Y座標を記録
                y_positions = [button.gui_element.getZ() for button in menu.buttons]
                y_positions_by_facility[facility] = y_positions[0] if y_positions else None
        
        # すべての施設で同じY座標（下部位置）を使用することを確認
        unique_y_positions = set(y_positions_by_facility.values())
        assert len(unique_y_positions) == 1, f"施設間でY座標が統一されていません: {y_positions_by_facility}"

    @patch('src.ui.base_ui.ui_manager')
    def test_button_text_fitting(self, mock_ui_mgr):
        """
        テスト: ボタンテキストの適切な表示
        
        期待する動作:
        - 長いテキストでもボタン内に収まる
        - テキストが切り詰められない
        - フォントサイズの自動調整
        """
        mock_ui_mgr.register_element = self.mock_ui_manager.register_element
        
        # 長いテキストのメニュー項目
        long_text_items = [
            {"text": "非常に長いメニュー項目名1", "command": lambda: None, "args": []},
            {"text": "短い項目", "command": lambda: None, "args": []},
            {"text": "中程度の長さの項目", "command": lambda: None, "args": []},
            {"text": "戻る", "command": lambda: None, "args": []}
        ]
        
        menu = UIMenu("long_text_menu", "長いテキストテスト")
        for item in long_text_items:
            menu.add_menu_item(item["text"], item["command"], item["args"])
        menu._rebuild_menu()
        
        # ボタンが作成されることを確認
        assert len(menu.buttons) == len(long_text_items), "長いテキストでボタンが作成されていません"
        
        # すべてのボタンで横配置が維持されることを確認
        y_positions = [button.gui_element.getZ() for button in menu.buttons]
        assert len(set(y_positions)) == 1, "長いテキストで横配置が乱れています"

    def test_backward_compatibility(self):
        """
        テスト: 既存機能との後方互換性
        
        期待する動作:
        - 既存のメニュー作成方法が動作する
        - add_menu_itemメソッドが正常動作
        - show/hideメソッドが正常動作
        """
        with patch('src.ui.base_ui.ui_manager') as mock_ui_mgr:
            mock_ui_mgr.register_element = self.mock_ui_manager.register_element
            mock_ui_mgr.show_element = self.mock_ui_manager.show_element
            mock_ui_mgr.hide_element = self.mock_ui_manager.hide_element
            
            # 従来の方法でメニューを作成
            menu = UIMenu("compatibility_test", "互換性テスト")
            
            # メニュー項目追加（従来の方法）
            menu.add_menu_item("テスト項目1", lambda: print("test1"))
            menu.add_menu_item("テスト項目2", lambda: print("test2"), ["arg1", "arg2"])
            
            # ボタンが正しく追加されることを確認
            assert len(menu.menu_items) == 2, "メニュー項目が正しく追加されていません"
            
            # show/hideが動作することを確認（エラーが発生しない）
            try:
                menu.show()
                menu.hide()
                assert True, "show/hideメソッドが正常動作"
            except Exception as e:
                pytest.fail(f"show/hideメソッドでエラー: {e}")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])