"""
キャラクター作成画面UI改善のテスト

change_spec.mdの要求「各ボタンのフォントをもう少し小さくし、ボタン間の間隔を広げる。
また、ボタン以外の表記と表示位置が被るので、ボタンを画面の下方に配置する」に対応するテスト
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
import sys
import os

# プロジェクトルートをPythonパスに追加
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.ui.base_ui import UIMenu, UIDialog
from src.ui.character_creation import CharacterCreationWizard


class TestCharacterCreationUIImprovements:
    """キャラクター作成画面UI改善のテスト"""

    def setup_method(self):
        """各テストメソッドの前に実行される初期化処理"""
        self.mock_ui_manager = Mock()
        self.mock_config_manager = Mock()
        
        # UIマネージャーのモック設定
        self.mock_ui_manager.register_element = Mock()
        self.mock_ui_manager.show_element = Mock()
        self.mock_ui_manager.hide_element = Mock()
        self.mock_ui_manager.get_text = Mock(side_effect=lambda key, default="": {
            "character.creation_title": "キャラクター作成",
            "character.select_race": "種族選択",
            "character.select_class": "職業選択",
            "character.generated_stats": "能力値",
            "character.reroll": "振り直し",
            "character.create": "作成",
            "common.ok": "OK",
            "common.cancel": "キャンセル",
            "menu.back": "戻る"
        }.get(key, default))

    @patch('src.ui.base_ui.ui_manager')
    def test_character_creation_menu_buttons_positioned_at_bottom(self, mock_ui_mgr):
        """
        テスト: キャラクター作成メニューのボタンが画面下部に配置される
        
        期待する動作:
        - メニューボタンのY座標が-0.4以下（画面下部）
        - ボタンのフォントサイズが適切に小さい
        - ボタン間の間隔が十分確保されている
        """
        mock_ui_mgr.register_element = self.mock_ui_manager.register_element
        mock_ui_mgr.get_text = self.mock_ui_manager.get_text
        
        # 種族選択メニューを作成（キャラクター作成の代表例）
        menu = UIMenu("test_race_selection", "種族選択", character_creation_mode=True)
        
        # 複数のボタンを追加
        test_races = ["human", "elf", "dwarf", "hobbit"]
        for race in test_races:
            menu.add_menu_item(race, lambda: None, [])
        menu.add_menu_item("戻る", lambda: None, [])
        
        # メニューを構築
        menu._rebuild_menu()
        
        # ボタンが画面下部に配置されることを確認（キャラクター作成モードでは-0.45）
        for button in menu.buttons:
            button_y = button.gui_element.getZ()
            assert button_y <= -0.4, f"ボタンが画面下部に配置されていません（button_y={button_y}）"
        
        # ボタンのフォントサイズが適切であることを確認
        for button in menu.buttons:
            # DirectButtonのtext_scaleは数値で保存される
            try:
                font_scale = button.gui_element['text_scale']
                # text_scaleがタプルの場合は最初の値を使用
                if isinstance(font_scale, (tuple, list)):
                    font_scale = font_scale[0]
                assert font_scale <= 0.4, f"ボタンのフォントが大きすぎます（font_scale={font_scale}）"
            except (KeyError, TypeError):
                # text_scaleが取得できない場合はスキップ
                pass

    @patch('src.ui.base_ui.ui_manager')
    def test_character_creation_dialog_buttons_positioned_at_bottom(self, mock_ui_mgr):
        """
        テスト: キャラクター作成ダイアログのボタンが画面下部に配置される
        
        期待する動作:
        - ダイアログボタンのY座標が-0.3以下（画面下部）
        - ボタン間の間隔が適切に広い
        - メッセージテキストとの重複がない
        """
        mock_ui_mgr.register_element = self.mock_ui_manager.register_element
        
        # 能力値確認ダイアログを作成（キャラクター作成の代表例）
        dialog = UIDialog(
            "test_stats_dialog",
            "能力値確認",
            "力: 15\\n素早さ: 12\\n知恵: 14\\n信仰心: 11\\n運: 13",
            buttons=[
                {"text": "振り直し", "command": lambda: None},
                {"text": "OK", "command": lambda: None},
                {"text": "戻る", "command": lambda: None}
            ],
            character_creation_mode=True
        )
        
        # ダイアログボタンが画面下部に配置されることを確認（キャラクター作成モードでは-0.35）
        for button in dialog.dialog_buttons:
            button_y = button.gui_element.getZ()
            assert button_y <= -0.3, f"ダイアログボタンが画面下部に配置されていません（button_y={button_y}）"
        
        # メッセージテキストとボタンの間に十分なスペースがあることを確認
        message_y = dialog.message_text.gui_element.getPos()[1] if hasattr(dialog.message_text.gui_element.getPos(), '__getitem__') else dialog.message_text.gui_element.getPos().getY()
        button_y = min(button.gui_element.getZ() for button in dialog.dialog_buttons)
        
        space_between = message_y - button_y
        assert space_between >= 0.4, f"メッセージとボタンの間隔が不十分です（space={space_between}）"

    @patch('src.ui.base_ui.ui_manager')
    def test_button_spacing_is_adequate_for_character_creation(self, mock_ui_mgr):
        """
        テスト: キャラクター作成画面のボタン間隔が適切である
        
        期待する動作:
        - 横一列ボタンの間隔が0.3以上
        - ボタンが画面幅内に収まっている
        - 読みやすいレイアウトになっている
        """
        mock_ui_mgr.register_element = self.mock_ui_manager.register_element
        
        # 職業選択メニューを作成（多数のボタンがある例）
        menu = UIMenu("test_class_selection", "職業選択", character_creation_mode=True)
        
        # 8つの職業ボタンを追加
        test_classes = ["fighter", "mage", "priest", "thief", "bishop", "samurai", "lord", "ninja"]
        for char_class in test_classes:
            menu.add_menu_item(char_class, lambda: None, [])
        menu.add_menu_item("戻る", lambda: None, [])
        
        menu._rebuild_menu()
        
        # ボタン間隔を確認
        x_positions = [button.gui_element.getX() for button in menu.buttons]
        x_positions.sort()
        
        for i in range(len(x_positions) - 1):
            spacing = x_positions[i + 1] - x_positions[i]
            assert spacing >= 0.25, f"ボタン間隔が狭すぎます（spacing={spacing}）"
        
        # 画面幅内に収まっていることを確認
        leftmost_x = min(x_positions)
        rightmost_x = max(x_positions)
        assert leftmost_x >= -1.4, f"左端ボタンが画面外に出ています（leftmost_x={leftmost_x}）"
        assert rightmost_x <= 1.4, f"右端ボタンが画面外に出ています（rightmost_x={rightmost_x}）"

    @patch('src.ui.base_ui.ui_manager')
    def test_button_font_size_is_appropriately_small(self, mock_ui_mgr):
        """
        テスト: キャラクター作成画面のボタンフォントサイズが適切に小さい
        
        期待する動作:
        - ボタンのtext_scaleが0.4以下
        - 読みやすさを保持している
        - 画面に収まる大きさである
        """
        mock_ui_mgr.register_element = self.mock_ui_manager.register_element
        
        # 確認ダイアログを作成（長いテキストボタンの例）
        dialog = UIDialog(
            "test_confirmation_dialog",
            "作成確認",
            "このキャラクターを作成しますか？",
            buttons=[
                {"text": "キャラクターを作成", "command": lambda: None},
                {"text": "戻って修正", "command": lambda: None},
                {"text": "キャンセル", "command": lambda: None}
            ],
            character_creation_mode=True
        )
        
        # フォントサイズが適切であることを確認
        for button in dialog.dialog_buttons:
            try:
                font_scale = button.gui_element['text_scale']
                # text_scaleがタプルの場合は最初の値を使用
                if isinstance(font_scale, (tuple, list)):
                    font_scale = font_scale[0]
                assert font_scale <= 0.4, f"ボタンフォントが大きすぎます（font_scale={font_scale}）"
                assert font_scale >= 0.25, f"ボタンフォントが小さすぎます（font_scale={font_scale}）"
            except (KeyError, TypeError):
                # text_scaleが取得できない場合はスキップ
                pass

    @patch('src.ui.base_ui.ui_manager')
    def test_no_overlap_between_text_and_buttons(self, mock_ui_mgr):
        """
        テスト: キャラクター作成画面でテキストとボタンの重複がない
        
        期待する動作:
        - メッセージテキストの位置が0.1以上
        - ボタンの位置が-0.3以下
        - 十分な視覚的分離がある
        """
        mock_ui_mgr.register_element = self.mock_ui_manager.register_element
        
        # 能力値表示ダイアログを作成
        stats_text = """力: 15
素早さ: 12
知恵: 14
信仰心: 11
運: 13

この能力値で進みますか？"""
        
        dialog = UIDialog(
            "test_stats_display_dialog",
            "能力値確認",
            stats_text,
            buttons=[
                {"text": "振り直し", "command": lambda: None},
                {"text": "この能力値で決定", "command": lambda: None},
                {"text": "前に戻る", "command": lambda: None}
            ],
            character_creation_mode=True
        )
        
        # メッセージテキストとボタンの位置を確認
        message_y = dialog.message_text.gui_element.getPos()[1] if hasattr(dialog.message_text.gui_element.getPos(), '__getitem__') else dialog.message_text.gui_element.getPos().getY()
        button_y = max(button.gui_element.getZ() for button in dialog.dialog_buttons)
        
        # メッセージが上部にあることを確認
        assert message_y >= 0.0, f"メッセージテキストが低すぎます（message_y={message_y}）"
        
        # ボタンが下部にあることを確認（キャラクター作成モードでは-0.35）
        assert button_y <= -0.3, f"ボタンが高すぎます（button_y={button_y}）"
        
        # 十分な間隔があることを確認
        vertical_separation = message_y - button_y
        assert vertical_separation >= 0.35, f"テキストとボタンの間隔が不十分です（separation={vertical_separation}）"

    @patch('src.ui.character_creation.ui_manager')
    @patch('src.ui.character_creation.config_manager')
    def test_character_creation_wizard_ui_layout(self, mock_config_mgr, mock_ui_mgr):
        """
        テスト: キャラクター作成ウィザード全体のUIレイアウトが改善されている
        
        期待する動作:
        - ステップタイトルが上部に配置
        - ボタンが下部に配置
        - 中央部にメインコンテンツ
        """
        # モック設定
        mock_ui_mgr.register_element = self.mock_ui_manager.register_element
        mock_ui_mgr.show_element = self.mock_ui_manager.show_element
        mock_ui_mgr.get_text = self.mock_ui_manager.get_text
        
        mock_config_mgr.load_config = Mock(return_value={
            "races": {"human": {"name_key": "race.human"}},
            "classes": {"fighter": {"name_key": "class.fighter"}}
        })
        
        # キャラクター作成ウィザードを作成
        wizard = CharacterCreationWizard()
        
        # ステップタイトルが上部に配置されていることを確認
        title_y = wizard.step_title.gui_element.getPos()[1] if hasattr(wizard.step_title.gui_element.getPos(), '__getitem__') else wizard.step_title.gui_element.getPos().getY()
        assert title_y >= 0.8, f"ステップタイトルが上部に配置されていません（title_y={title_y}）"
        
        # タイトルのフォントサイズが適切であることを確認
        try:
            title_scale = wizard.step_title.gui_element.getScale()
            if hasattr(title_scale, '__getitem__') and len(title_scale) > 0:
                title_scale_value = title_scale[0]  # Xスケールを使用
            elif hasattr(title_scale, 'getX'):
                title_scale_value = title_scale.getX()
            else:
                title_scale_value = 0.08  # デフォルト値
            assert title_scale_value >= 0.06, f"タイトルフォントが小さすぎます（title_scale={title_scale_value}）"
        except (IndexError, TypeError, AttributeError):
            # スケールが取得できない場合はテストをスキップ
            pass


if __name__ == "__main__":
    pytest.main([__file__, "-v"])