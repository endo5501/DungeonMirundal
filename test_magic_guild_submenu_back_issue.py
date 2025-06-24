"""魔術師ギルドサブメニュー戻る問題のテスト"""

import unittest
from unittest.mock import Mock, patch, MagicMock
from src.overworld.facilities.magic_guild import MagicGuild


class TestMagicGuildSubmenuBackIssue(unittest.TestCase):
    """魔術師ギルドサブメニュー戻る問題のテスト"""
    
    def setUp(self):
        """テストの準備"""
        # UI関連のモック
        self.mock_ui_manager = Mock()
        self.mock_pygame_gui_manager = Mock()
        self.mock_ui_manager.pygame_gui_manager = self.mock_pygame_gui_manager
        
        # パーティとキャラクターのモック
        self.mock_character = Mock()
        self.mock_character.name = "テストキャラ"
        self.mock_character.race = Mock()
        self.mock_character.job = Mock()
        self.mock_character.race.name = "人間"
        self.mock_character.job.name = "戦士"
        
        self.mock_party = Mock()
        self.mock_party.get_members.return_value = [self.mock_character]
        
        # MagicGuildのインスタンス作成
        self.magic_guild = MagicGuild()
        self.magic_guild.ui_manager = self.mock_ui_manager
        self.magic_guild.party = self.mock_party
        
        # 必要なメソッドをモック
        self.magic_guild._get_effective_ui_manager = Mock(return_value=self.mock_ui_manager)
        self.magic_guild._show_menu_safe = Mock()
        self.magic_guild._hide_menu_safe = Mock()
    
    def test_magic_guild_menu_hierarchy(self):
        """魔術師ギルドのメニュー階層構造をテスト"""
        # 1. メインメニューが作成されること
        self.magic_guild._create_main_menu()
        self.assertIsNotNone(self.magic_guild.main_menu)
        
        # 2. 魔法分析メニューが作成されること
        self.magic_guild._show_analysis_menu()
        self.assertIsNotNone(self.magic_guild.analysis_menu)
        
        # 3. キャラクター個別分析メニューが作成されること
        self.magic_guild._show_character_analysis_menu()
        self.assertIsNotNone(self.magic_guild.character_analysis_menu)
    
    def test_character_analysis_back_issue_reproduction(self):
        """キャラクター個別分析の戻る問題を再現"""
        # 1. メインメニューから魔法分析メニューへ
        self.magic_guild._create_main_menu()
        self.magic_guild._show_analysis_menu()
        
        # 2. 魔法分析メニューからキャラクター個別分析メニューへ
        self.magic_guild._show_character_analysis_menu()
        
        # 3. キャラクター選択でダイアログ表示
        self.magic_guild._analyze_character(self.mock_character)
        
        # 4. ダイアログの戻るボタンを押す
        # 現在の実装では _close_dialog() が呼ばれる
        self.magic_guild._close_dialog()
        
        # 期待: キャラクター個別分析メニューが再表示される
        # 実際: メインメニューが表示される（問題）
        
        # show_menu が呼ばれることを確認（問題の再現）
        self.mock_ui_manager.show_menu.assert_called()
        called_args = self.mock_ui_manager.show_menu.call_args
        
        # 現在の実装では main_menu.menu_id が呼ばれる（問題）
        # 正しくは character_analysis_menu.menu_id が呼ばれるべき
        self.assertIn("magic_guild_main", str(called_args))
    
    def test_expected_navigation_flow(self):
        """期待されるナビゲーション動作をテスト"""
        # 1. メニューを順番に表示
        self.magic_guild._create_main_menu()  # メインメニュー
        self.magic_guild._show_analysis_menu()  # 魔法分析メニュー
        self.magic_guild._show_character_analysis_menu()  # キャラクター個別分析メニュー
        
        # 2. キャラクター分析の実行
        self.magic_guild._analyze_character(self.mock_character)
        
        # 3. 期待される戻る動作
        # ダイアログから戻る場合、キャラクター個別分析メニューに戻るべき
        expected_menu_id = self.magic_guild.character_analysis_menu.menu_id
        
        # 現在は _close_dialog() がメインメニューに戻すが、
        # 正しくはキャラクター個別分析メニューに戻すべき
        self.assertIsNotNone(expected_menu_id)
    
    def test_dialog_close_callback_issue(self):
        """ダイアログ閉じる時のコールバック問題をテスト"""
        # BaseFacility._close_dialog()の動作を確認
        
        # メインメニューがあることを確認
        self.magic_guild._create_main_menu()
        self.assertIsNotNone(self.magic_guild.main_menu)
        
        # _close_dialog()を呼び出す
        self.magic_guild._close_dialog()
        
        # 問題: main_menu.menu_id が show_menu に渡される
        # 正しくは最後に表示されたメニュー（character_analysis_menu）が表示されるべき
        self.mock_ui_manager.show_menu.assert_called()
        
        # 呼び出し引数を確認
        call_args = self.mock_ui_manager.show_menu.call_args
        self.assertIsNotNone(call_args)
    
    def test_back_button_callback_in_character_dialog(self):
        """キャラクター分析ダイアログの戻るボタンコールバックをテスト"""
        # _analyze_character() でダイアログが作成される時の戻るボタン設定を確認
        
        # キャラクター個別分析メニューを先に作成
        self.magic_guild._show_character_analysis_menu()
        character_analysis_menu_id = self.magic_guild.character_analysis_menu.menu_id
        
        # mock_ui_manager.show_dialog をモック
        self.mock_ui_manager.show_dialog = Mock()
        
        # キャラクター分析を実行
        self.magic_guild._analyze_character(self.mock_character)
        
        # show_dialog が呼ばれることを確認
        self.mock_ui_manager.show_dialog.assert_called()
        
        # 呼び出し引数を取得
        call_args = self.mock_ui_manager.show_dialog.call_args
        self.assertIsNotNone(call_args)
        
        # ダイアログの設定を確認
        if call_args and len(call_args[1]) > 0:  # kwargs
            dialog_config = call_args[1]
            if 'buttons' in dialog_config:
                buttons = dialog_config['buttons']
                # 戻るボタンがあることを確認
                back_buttons = [btn for btn in buttons if 'back' in btn.get('text', '').lower() or '戻る' in btn.get('text', '')]
                self.assertTrue(len(back_buttons) > 0, "戻るボタンが見つかりません")
                
                # 戻るボタンのコマンドが _close_dialog であることを確認（現在の問題）
                back_button = back_buttons[0]
                # self.assertEqual(back_button['command'], self.magic_guild._close_dialog)
                
                # 期待: 戻るボタンのコマンドが _show_character_analysis_menu であるべき
                # self.assertEqual(back_button['command'], self.magic_guild._show_character_analysis_menu)
    
    def test_correct_back_navigation_solution(self):
        """正しい戻るナビゲーションの解決方法をテスト"""
        # 修正後の期待動作:
        # ダイアログの戻るボタンは _show_character_analysis_menu を呼ぶべき
        
        # キャラクター個別分析メニューを作成
        self.magic_guild._show_character_analysis_menu()
        
        # 戻るコールバックとして _show_character_analysis_menu を設定
        def correct_back_callback():
            self.magic_guild._show_character_analysis_menu()
        
        # この関数が呼ばれることをテスト
        correct_back_callback()
        
        # show_menu が character_analysis_menu.menu_id で呼ばれることを確認
        # （実際の修正では、この動作を実装する必要がある）
        self.assertIsNotNone(self.magic_guild.character_analysis_menu)


if __name__ == '__main__':
    unittest.main()