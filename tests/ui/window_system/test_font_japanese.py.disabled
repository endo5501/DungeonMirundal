"""日本語フォント表示のテスト"""

import pytest
import pygame
import pygame_gui
from src.ui.window_system.window_manager import WindowManager
from src.ui.window_system.menu_window import MenuWindow


class TestJapaneseFont:
    """日本語フォント表示のテスト"""
    
    @pytest.fixture
    def setup_pygame(self):
        """Pygame環境のセットアップ"""
        pygame.init()
        screen = pygame.display.set_mode((800, 600))
        clock = pygame.time.Clock()
        yield screen, clock
        pygame.quit()
    
    def test_window_manager_japanese_font(self, setup_pygame):
        """WindowManagerで日本語フォントが正しく表示されるかテスト"""
        screen, clock = setup_pygame
        
        # WindowManagerを初期化
        window_manager = WindowManager.get_instance()
        window_manager.initialize_pygame(screen, clock)
        
        # 日本語テキストを含むメニュー設定
        menu_config = {
            'title': 'メインメニュー',
            'buttons': [
                {'id': 'new_game', 'text': '新しいゲーム', 'action': 'new_game'},
                {'id': 'load_game', 'text': 'ゲームをロード', 'action': 'load_game'},
                {'id': 'settings', 'text': '設定', 'action': 'settings'},
                {'id': 'exit', 'text': '終了', 'action': 'exit'}
            ]
        }
        
        # MenuWindowを作成
        menu_window = MenuWindow('test_menu', menu_config)
        
        # ウィンドウをレジストリに追加
        window_manager.window_registry['test_menu'] = menu_window
        
        # ウィンドウを表示
        window_manager.show_window(menu_window)
        
        # UI要素が作成されているか確認
        assert menu_window.ui_manager is not None
        assert len(menu_window.buttons) == 5  # 4 + 戻るボタン
        
        # ボタンのテキストが正しく設定されているか確認
        button_texts = [button.text for button in menu_window.buttons]
        expected_texts = ['新しいゲーム', 'ゲームをロード', '設定', '終了', '戻る']
        assert button_texts == expected_texts
        
        # 日本語テキストが文字化けしていないことを確認
        for button in menu_window.buttons:
            # 文字化けの典型的なパターンをチェック
            assert '?' not in button.text
            assert '�' not in button.text
            assert '□' not in button.text
        
        # タイトルラベルが存在するか確認
        assert hasattr(menu_window, 'title_label')
        
        # WindowManagerをクリーンアップ
        window_manager.close_window(menu_window)
        WindowManager._instance = None