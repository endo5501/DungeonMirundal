"""
MenuWindow のテスト

t-wada式TDDによるテストファースト開発
"""

import pytest
import pygame
import pygame_gui
from unittest.mock import Mock, patch
from src.ui.window_system import Window, WindowState
from src.ui.window_system.menu_window import MenuWindow


class TestMenuWindow:
    """MenuWindow のテストクラス"""
    
    def setup_method(self):
        """各テストメソッドの前に実行される"""
        # Pygame全体の完全初期化（WSL2対応）
        pygame.quit()  # 既存の状態をクリア
        
        # 短い待機時間を追加（WSL2環境でのフォントサブシステム安定化）
        import time
        time.sleep(0.01)
        
        pygame.init()
        
        # ディスプレイの初期化
        self.screen = pygame.display.set_mode((800, 600))  # 十分なサイズで初期化
        
        # フォントモジュールの確実な初期化（WSL2対応）
        if not pygame.font.get_init():
            pygame.font.init()
        
        # フォント初期化後の短い待機
        time.sleep(0.01)
        
        # pygame_gui用UIManagerを初期化
        self.ui_manager = pygame_gui.UIManager((800, 600))
        
        # UIManager初期化後の短い待機
        time.sleep(0.01)
    
    def teardown_method(self):
        """各テストメソッドの後に実行される"""
        import time
        
        # UI要素の完全クリーンアップ
        if hasattr(self, 'ui_manager'):
            try:
                self.ui_manager.clear_and_reset()
                # クリーンアップ後の短い待機
                time.sleep(0.01)
            except:
                pass
        
        # 画面サーフェスのクリア
        if hasattr(self, 'screen'):
            try:
                self.screen.fill((0, 0, 0))
                pygame.display.flip()
            except:
                pass
        
        # ディスプレイの終了
        try:
            if pygame.display.get_init():
                pygame.display.quit()
                time.sleep(0.01)  # ディスプレイ終了後の待機
        except:
            pass
        
        # フォントモジュールの確実な終了（WSL2対応）
        try:
            if pygame.font.get_init():
                pygame.font.quit()
                time.sleep(0.01)  # フォント終了後の待機
        except:
            pass
        
        # Pygame全体の終了
        try:
            if pygame.get_init():
                pygame.quit()
                time.sleep(0.01)  # 全体終了後の待機
        except:
            pass
    
    def test_menu_window_inherits_from_window(self):
        """MenuWindowがWindowクラスを継承することを確認"""
        # Given: メニュー設定
        menu_config = {
            'title': 'Test Menu',
            'buttons': [
                {'id': 'btn1', 'text': 'Button 1', 'action': 'action1'},
                {'id': 'btn2', 'text': 'Button 2', 'action': 'action2'}
            ]
        }
        
        # When: MenuWindowを作成
        menu_window = MenuWindow('test_menu', menu_config)
        
        # Then: Windowクラスを継承している
        assert isinstance(menu_window, Window)
        assert menu_window.window_id == 'test_menu'
        assert menu_window.menu_config == menu_config
    
    def test_menu_window_creates_buttons_from_config(self):
        """設定からボタンが正しく作成されることを確認"""
        # Given: ボタン設定を含むメニュー設定
        menu_config = {
            'title': 'Main Menu',
            'buttons': [
                {'id': 'start', 'text': 'Start Game', 'action': 'start_game'},
                {'id': 'settings', 'text': 'Settings', 'action': 'open_settings'},
                {'id': 'exit', 'text': 'Exit', 'action': 'exit_game'}
            ]
        }
        
        # When: MenuWindowを作成し、UI要素を作成
        menu_window = MenuWindow('main_menu', menu_config)
        menu_window.create()
        
        # Then: 設定通りのボタン + 戻るボタンが作成される
        assert len(menu_window.buttons) == 4  # 元の3つ + 戻るボタン
        assert menu_window.buttons[0].action == 'start_game'
        assert menu_window.buttons[1].action == 'open_settings'
        assert menu_window.buttons[2].action == 'exit_game'
        assert menu_window.buttons[3].action == 'window_back'  # 戻るボタン
    
    def test_menu_window_handles_button_click_events(self):
        """ボタンクリックイベントが正しく処理されることを確認"""
        # Given: メニューウィンドウとモックイベント
        menu_config = {
            'title': 'Test Menu',
            'buttons': [
                {'id': 'test_btn', 'text': 'Test Button', 'action': 'test_action'}
            ]
        }
        menu_window = MenuWindow('test_menu', menu_config)
        menu_window.create()
        
        # Mock button click event
        mock_event = Mock()
        mock_event.type = pygame_gui.UI_BUTTON_PRESSED
        mock_event.ui_element = menu_window.buttons[0].ui_element
        
        # When: ボタンクリックイベントを処理
        with patch.object(menu_window, 'send_message') as mock_send:
            result = menu_window.handle_event(mock_event)
        
        # Then: 適切なメッセージが送信される
        assert result is True
        mock_send.assert_called_once_with('menu_action', {'action': 'test_action', 'button_id': 'test_btn'})
    
    def test_menu_window_supports_keyboard_navigation(self):
        """キーボードナビゲーションがサポートされることを確認"""
        # Given: 複数ボタンのメニューウィンドウ
        menu_config = {
            'title': 'Navigation Test',
            'buttons': [
                {'id': 'btn1', 'text': 'Button 1', 'action': 'action1'},
                {'id': 'btn2', 'text': 'Button 2', 'action': 'action2'},
                {'id': 'btn3', 'text': 'Button 3', 'action': 'action3'}
            ]
        }
        menu_window = MenuWindow('nav_menu', menu_config)
        menu_window.create()
        
        # When: 下矢印キーを押す
        down_event = Mock()
        down_event.type = pygame.KEYDOWN
        down_event.key = pygame.K_DOWN
        
        menu_window.handle_event(down_event)
        
        # Then: 選択されたボタンインデックスが更新される
        assert menu_window.selected_button_index == 1
        
        # When: 上矢印キーを押す
        up_event = Mock()
        up_event.type = pygame.KEYDOWN
        up_event.key = pygame.K_UP
        
        menu_window.handle_event(up_event)
        
        # Then: 選択されたボタンインデックスが戻る
        assert menu_window.selected_button_index == 0
    
    def test_menu_window_wraps_navigation_at_boundaries(self):
        """ナビゲーションが境界で循環することを確認"""
        # Given: 3つのボタンがあるメニュー
        menu_config = {
            'title': 'Wrap Test',
            'buttons': [
                {'id': 'btn1', 'text': 'Button 1', 'action': 'action1'},
                {'id': 'btn2', 'text': 'Button 2', 'action': 'action2'},
                {'id': 'btn3', 'text': 'Button 3', 'action': 'action3'}
            ]
        }
        menu_window = MenuWindow('wrap_menu', menu_config)
        menu_window.create()
        
        # When: 最初のボタンで上キーを押す（上端）
        up_event = Mock()
        up_event.type = pygame.KEYDOWN
        up_event.key = pygame.K_UP
        
        menu_window.handle_event(up_event)
        
        # Then: 最後のボタン（戻るボタン）に循環する
        assert menu_window.selected_button_index == 3  # 元の3つ + 戻るボタン
        
        # When: 最後のボタンで下キーを押す（下端）
        down_event = Mock()
        down_event.type = pygame.KEYDOWN
        down_event.key = pygame.K_DOWN
        
        menu_window.handle_event(down_event)
        
        # Then: 最初のボタンに循環する
        assert menu_window.selected_button_index == 0
    
    def test_menu_window_activates_selected_button_with_enter(self):
        """Enterキーで選択されたボタンが実行されることを確認"""
        # Given: 選択されたボタンがあるメニュー
        menu_config = {
            'title': 'Enter Test',
            'buttons': [
                {'id': 'btn1', 'text': 'Button 1', 'action': 'action1'},
                {'id': 'btn2', 'text': 'Button 2', 'action': 'action2'}
            ]
        }
        menu_window = MenuWindow('enter_menu', menu_config)
        menu_window.create()
        menu_window.selected_button_index = 1  # 2番目のボタンを選択
        
        # When: Enterキーを押す
        enter_event = Mock()
        enter_event.type = pygame.KEYDOWN
        enter_event.key = pygame.K_RETURN
        
        with patch.object(menu_window, 'send_message') as mock_send:
            result = menu_window.handle_event(enter_event)
        
        # Then: 選択されたボタンのアクションが実行される
        assert result is True
        mock_send.assert_called_once_with('menu_action', {'action': 'action2', 'button_id': 'btn2'})
    
    def test_menu_window_can_be_disabled_and_enabled(self):
        """メニューの有効/無効切り替えができることを確認"""
        # Given: メニューウィンドウ
        menu_config = {
            'title': 'Enable Test',
            'buttons': [
                {'id': 'btn1', 'text': 'Button 1', 'action': 'action1'}
            ]
        }
        menu_window = MenuWindow('enable_menu', menu_config)
        menu_window.create()
        
        # When: メニューを無効にする
        menu_window.set_enabled(False)
        
        # Then: 無効状態になる
        assert menu_window.enabled is False
        
        # When: 無効状態でイベントを処理
        event = Mock()
        event.type = pygame.KEYDOWN
        event.key = pygame.K_DOWN
        
        result = menu_window.handle_event(event)
        
        # Then: イベントが無視される
        assert result is False
        
        # When: メニューを有効にする
        menu_window.set_enabled(True)
        
        # Then: 有効状態になる
        assert menu_window.enabled is True
    
    def test_menu_window_supports_custom_styling(self):
        """カスタムスタイリングがサポートされることを確認"""
        # Given: スタイル設定を含むメニュー設定
        menu_config = {
            'title': 'Styled Menu',
            'buttons': [
                {'id': 'btn1', 'text': 'Button 1', 'action': 'action1'}
            ],
            'style': {
                'background_color': '#2a2a2a',
                'button_color': '#4a4a4a',
                'text_color': '#ffffff',
                'selected_color': '#6a6a6a'
            }
        }
        
        # When: スタイル付きメニューを作成
        menu_window = MenuWindow('styled_menu', menu_config)
        menu_window.create()
        
        # Then: スタイル設定が適用される
        assert menu_window.style == menu_config['style']
        assert menu_window.buttons[0].style == menu_config['style']
    
    def test_menu_window_validates_config_on_creation(self):
        """作成時にメニュー設定が検証されることを確認"""
        # Given: 不正な設定
        invalid_config = {
            'title': 'Invalid Menu'
            # buttons が欠落
        }
        
        # When: 不正な設定でMenuWindowを作成しようとする
        # Then: 例外が発生する
        with pytest.raises(ValueError, match="Menu config must contain 'buttons'"):
            MenuWindow('invalid_menu', invalid_config)
    
    def test_menu_window_cleanup_removes_ui_elements(self):
        """クリーンアップでUI要素が適切に削除されることを確認"""
        # Given: 作成されたメニューウィンドウ
        menu_config = {
            'title': 'Cleanup Test',
            'buttons': [
                {'id': 'btn1', 'text': 'Button 1', 'action': 'action1'}
            ]
        }
        menu_window = MenuWindow('cleanup_menu', menu_config)
        menu_window.create()
        
        # When: クリーンアップを実行
        menu_window.cleanup_ui()
        
        # Then: UI要素が削除される
        assert len(menu_window.buttons) == 0
        assert menu_window.ui_manager is None
    
    def test_menu_window_automatically_adds_back_button(self):
        """MenuWindowが自動的に戻るボタンを追加することを確認"""
        # Given: 戻るボタンを明示的に含まないメニュー設定
        menu_config = {
            'title': 'Test Menu',
            'buttons': [
                {'id': 'btn1', 'text': 'Button 1', 'action': 'action1'},
                {'id': 'btn2', 'text': 'Button 2', 'action': 'action2'}
            ]
        }
        
        # When: MenuWindowを作成し、UI要素を作成
        menu_window = MenuWindow('test_menu', menu_config)
        menu_window.create()
        
        # Then: 戻るボタンが自動的に追加される
        assert len(menu_window.buttons) == 3  # 元の2つ + 戻るボタン
        back_button = menu_window.buttons[-1]
        assert back_button.id == 'back'
        assert back_button.text == '戻る'
        assert back_button.action == 'window_back'
    
    def test_menu_window_back_button_not_added_to_root_menu(self):
        """ルートメニューには戻るボタンが追加されないことを確認"""
        # Given: ルートメニューとして指定された設定
        menu_config = {
            'title': 'Root Menu',
            'buttons': [
                {'id': 'btn1', 'text': 'Button 1', 'action': 'action1'}
            ],
            'is_root': True
        }
        
        # When: MenuWindowを作成し、UI要素を作成
        menu_window = MenuWindow('root_menu', menu_config)
        menu_window.create()
        
        # Then: 戻るボタンは追加されない
        assert len(menu_window.buttons) == 1
        assert menu_window.buttons[0].id == 'btn1'
    
    def test_menu_window_back_button_sends_window_back_action(self):
        """戻るボタンが押されたときにwindow_backアクションが送信されることを確認"""
        # Given: 戻るボタンが自動追加されたメニュー
        menu_config = {
            'title': 'Test Menu',
            'buttons': [
                {'id': 'btn1', 'text': 'Button 1', 'action': 'action1'}
            ]
        }
        menu_window = MenuWindow('test_menu', menu_config)
        menu_window.create()
        
        # 戻るボタンのUI要素を取得
        back_button = menu_window.buttons[-1]
        
        # When: 戻るボタンがクリックされる
        mock_event = Mock()
        mock_event.type = pygame_gui.UI_BUTTON_PRESSED
        mock_event.ui_element = back_button.ui_element
        
        with patch.object(menu_window, 'send_message') as mock_send:
            result = menu_window.handle_event(mock_event)
        
        # Then: window_backアクションが送信される
        assert result is True
        mock_send.assert_called_once_with('menu_action', {'action': 'window_back', 'button_id': 'back'})
    
    def test_menu_window_escape_key_triggers_back_action(self):
        """ESCキーが押されたときに戻るアクションが実行されることを確認"""
        # Given: メニューウィンドウ
        menu_config = {
            'title': 'Test Menu',
            'buttons': [
                {'id': 'btn1', 'text': 'Button 1', 'action': 'action1'}
            ]
        }
        menu_window = MenuWindow('test_menu', menu_config)
        menu_window.create()
        
        # When: ESCキーが押される
        esc_event = Mock()
        esc_event.type = pygame.KEYDOWN
        esc_event.key = pygame.K_ESCAPE
        
        with patch.object(menu_window, 'send_message') as mock_send:
            result = menu_window.handle_event(esc_event)
        
        # Then: window_backアクションが送信される
        assert result is True
        mock_send.assert_called_once_with('menu_action', {'action': 'window_back', 'button_id': 'escape'})
    
    def test_menu_window_custom_back_button_text(self):
        """カスタムの戻るボタンテキストが使用できることを確認"""
        # Given: カスタム戻るボタンテキストを含む設定
        menu_config = {
            'title': 'Test Menu',
            'buttons': [
                {'id': 'btn1', 'text': 'Button 1', 'action': 'action1'}
            ],
            'back_button_text': 'メインメニューに戻る'
        }
        
        # When: MenuWindowを作成
        menu_window = MenuWindow('test_menu', menu_config)
        menu_window.create()
        
        # Then: カスタムテキストが使用される
        back_button = menu_window.buttons[-1]
        assert back_button.text == 'メインメニューに戻る'