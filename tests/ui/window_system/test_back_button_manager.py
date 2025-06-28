"""
BackButtonManager のテスト

Extract Classリファクタリングで抽出されたクラスのテスト
"""

import pytest
import pygame
import pygame_gui
from unittest.mock import Mock, patch
from src.ui.window_system.back_button_manager import BackButtonManager, BackButtonConfig


class TestBackButtonManager:
    """BackButtonManager のテストクラス"""
    
    def setup_method(self):
        """各テストメソッドの前に実行される"""
        pygame.init()
        pygame.display.set_mode((1024, 768), pygame.NOFRAME)
    
    def teardown_method(self):
        """各テストメソッドの後に実行される"""
        pygame.quit()
    
    def test_should_add_back_button_returns_true_for_normal_menu(self):
        """通常のメニューでは戻るボタンを追加することを確認"""
        # Given: 通常のメニュー設定
        menu_config = {
            'title': 'Normal Menu',
            'buttons': [
                {'id': 'btn1', 'text': 'Button 1', 'action': 'action1'}
            ]
        }
        
        # When: BackButtonManagerを作成
        manager = BackButtonManager(menu_config)
        
        # Then: 戻るボタンを追加する必要がある
        assert manager.should_add_back_button() is True
    
    def test_should_add_back_button_returns_false_for_root_menu(self):
        """ルートメニューでは戻るボタンを追加しないことを確認"""
        # Given: ルートメニュー設定
        menu_config = {
            'title': 'Root Menu',
            'buttons': [
                {'id': 'btn1', 'text': 'Button 1', 'action': 'action1'}
            ],
            'is_root': True
        }
        
        # When: BackButtonManagerを作成
        manager = BackButtonManager(menu_config)
        
        # Then: 戻るボタンを追加する必要がない
        assert manager.should_add_back_button() is False
    
    def test_should_add_back_button_returns_false_when_back_button_exists(self):
        """既に戻るボタンが存在する場合は追加しないことを確認"""
        # Given: 既に戻るボタンがあるメニュー設定
        menu_config = {
            'title': 'Menu with Back',
            'buttons': [
                {'id': 'btn1', 'text': 'Button 1', 'action': 'action1'},
                {'id': 'back', 'text': 'Back', 'action': 'window_back'}
            ]
        }
        
        # When: BackButtonManagerを作成
        manager = BackButtonManager(menu_config)
        
        # Then: 戻るボタンを追加する必要がない
        assert manager.should_add_back_button() is False
    
    def test_create_back_button_config_with_default_text(self):
        """デフォルトテキストで戻るボタン設定が作成されることを確認"""
        # Given: 通常のメニュー設定
        menu_config = {
            'title': 'Test Menu',
            'buttons': [
                {'id': 'btn1', 'text': 'Button 1', 'action': 'action1'}
            ]
        }
        
        # When: BackButtonManagerを作成
        manager = BackButtonManager(menu_config)
        
        # Then: デフォルト設定の戻るボタン設定が作成される
        assert manager.back_button_config is not None
        assert manager.back_button_config.text == '戻る'
        assert manager.back_button_config.id == 'back'
        assert manager.back_button_config.action == 'window_back'
    
    def test_create_back_button_config_with_custom_text(self):
        """カスタムテキストで戻るボタン設定が作成されることを確認"""
        # Given: カスタム戻るボタンテキストを含むメニュー設定
        menu_config = {
            'title': 'Test Menu',
            'buttons': [
                {'id': 'btn1', 'text': 'Button 1', 'action': 'action1'}
            ],
            'back_button_text': 'メインメニューに戻る'
        }
        
        # When: BackButtonManagerを作成
        manager = BackButtonManager(menu_config)
        
        # Then: カスタムテキストの戻るボタン設定が作成される
        assert manager.back_button_config is not None
        assert manager.back_button_config.text == 'メインメニューに戻る'
    
    def test_create_back_button_creates_menu_button(self):
        """戻るボタンのMenuButtonが正しく作成されることを確認"""
        # Given: 戻るボタンが必要なメニュー設定
        menu_config = {
            'title': 'Test Menu',
            'buttons': [
                {'id': 'btn1', 'text': 'Button 1', 'action': 'action1'}
            ]
        }
        manager = BackButtonManager(menu_config)
        
        # UIマネージャーとパネルをモック
        ui_manager = pygame_gui.UIManager((1024, 768))
        panel = pygame_gui.elements.UIPanel(
            relative_rect=pygame.Rect(0, 0, 400, 300),
            manager=ui_manager
        )
        button_rect = pygame.Rect(0, 0, 200, 50)
        style = {}
        
        # When: 戻るボタンを作成
        back_button = manager.create_back_button(button_rect, ui_manager, panel, style)
        
        # Then: MenuButtonが正しく作成される
        assert back_button is not None
        assert back_button.id == 'back'
        assert back_button.text == '戻る'
        assert back_button.action == 'window_back'
        assert back_button.ui_element is not None
    
    def test_create_back_button_returns_none_for_root_menu(self):
        """ルートメニューでは戻るボタンが作成されないことを確認"""
        # Given: ルートメニュー設定
        menu_config = {
            'title': 'Root Menu',
            'buttons': [
                {'id': 'btn1', 'text': 'Button 1', 'action': 'action1'}
            ],
            'is_root': True
        }
        manager = BackButtonManager(menu_config)
        
        # When: 戻るボタンを作成しようとする
        back_button = manager.create_back_button(
            pygame.Rect(0, 0, 200, 50), 
            Mock(), 
            Mock(), 
            {}
        )
        
        # Then: Noneが返される
        assert back_button is None
    
    def test_handle_escape_key_for_normal_menu(self):
        """通常のメニューでESCキーが処理されることを確認"""
        # Given: 通常のメニュー設定
        menu_config = {
            'title': 'Test Menu',
            'buttons': [
                {'id': 'btn1', 'text': 'Button 1', 'action': 'action1'}
            ]
        }
        manager = BackButtonManager(menu_config)
        
        # Mock callback
        mock_callback = Mock()
        
        # When: ESCキーを処理
        result = manager.handle_escape_key(mock_callback)
        
        # Then: ESCキーが処理され、適切なメッセージが送信される
        assert result is True
        mock_callback.assert_called_once_with('menu_action', {
            'action': 'window_back',
            'button_id': 'escape'
        })
    
    def test_handle_escape_key_for_root_menu(self):
        """ルートメニューでESCキーが処理されないことを確認"""
        # Given: ルートメニュー設定
        menu_config = {
            'title': 'Root Menu',
            'buttons': [
                {'id': 'btn1', 'text': 'Button 1', 'action': 'action1'}
            ],
            'is_root': True
        }
        manager = BackButtonManager(menu_config)
        
        # Mock callback
        mock_callback = Mock()
        
        # When: ESCキーを処理
        result = manager.handle_escape_key(mock_callback)
        
        # Then: ESCキーが処理されず、コールバックも呼ばれない
        assert result is False
        mock_callback.assert_not_called()
    
    def test_get_additional_button_count(self):
        """追加ボタン数が正しく取得されることを確認"""
        # Given: 通常のメニュー設定
        normal_config = {
            'title': 'Normal Menu',
            'buttons': [{'id': 'btn1', 'text': 'Button 1', 'action': 'action1'}]
        }
        normal_manager = BackButtonManager(normal_config)
        
        # Given: ルートメニュー設定
        root_config = {
            'title': 'Root Menu',
            'buttons': [{'id': 'btn1', 'text': 'Button 1', 'action': 'action1'}],
            'is_root': True
        }
        root_manager = BackButtonManager(root_config)
        
        # When & Then: 追加ボタン数を確認
        assert normal_manager.get_additional_button_count() == 1
        assert root_manager.get_additional_button_count() == 0