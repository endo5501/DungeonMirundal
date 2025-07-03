"""
SettingsWindow のテスト

t-wada式TDDによるテストファースト開発
既存設定UIから新Window Systemへの移行
"""

import pytest
import pygame
import pygame_gui
from unittest.mock import Mock, patch, MagicMock
from src.ui.window_system import Window, WindowState
from src.ui.window_system.settings_window import SettingsWindow, SettingsTab


class TestSettingsWindow:
    """SettingsWindow のテストクラス"""
    
    def setup_method(self):
        """各テストメソッドの前に実行される"""
        pygame.init()
        pygame.display.set_mode((1, 1), pygame.NOFRAME)
    
    def teardown_method(self):
        """各テストメソッドの後に実行される"""
        pygame.quit()
    
    def test_settings_window_inherits_from_window(self):
        """SettingsWindowがWindowクラスを継承することを確認"""
        # Given: 設定ウィンドウ設定
        settings_config = {
            'title': 'Settings',
            'categories': ['gameplay', 'controls', 'audio', 'graphics']
        }
        
        # When: SettingsWindowを作成
        settings_window = SettingsWindow('settings', settings_config)
        
        # Then: Windowクラスを継承している
        assert isinstance(settings_window, Window)
        assert settings_window.window_id == 'settings'
        assert settings_window.settings_config == settings_config
        assert settings_window.modal is True  # 設定は通常モーダル
    
    def test_settings_validates_config_structure(self):
        """設定の構造が検証されることを確認"""
        # Given: 不正な設定
        
        # When: categoriesが無い設定でSettingsWindowを作成しようとする
        # Then: 例外が発生する
        with pytest.raises(ValueError, match="Settings config must contain 'categories'"):
            SettingsWindow('invalid_settings', {})
        
        # When: categoriesが空の設定でSettingsWindowを作成しようとする
        # Then: 例外が発生する
        with pytest.raises(ValueError, match="Settings config 'categories' cannot be empty"):
            SettingsWindow('empty_settings', {'categories': []})
    
    def test_settings_creates_tabs_from_categories(self):
        """カテゴリからタブが作成されることを確認"""
        # Given: タブ設定
        settings_config = {
            'categories': [
                {'id': 'gameplay', 'label': 'ゲームプレイ'},
                {'id': 'audio', 'label': '音声設定'},
                {'id': 'graphics', 'label': '表示設定'}
            ]
        }
        
        settings_window = SettingsWindow('tab_settings', settings_config)
        settings_window.create()
        
        # Then: タブが作成される
        assert len(settings_window.tabs) == 3
        gameplay_tab = settings_window.tabs[0]
        assert gameplay_tab.tab_id == 'gameplay'
        assert gameplay_tab.label == 'ゲームプレイ'
        assert gameplay_tab.is_active is True  # 最初のタブがアクティブ
        
        audio_tab = settings_window.tabs[1]
        assert audio_tab.tab_id == 'audio'
        assert audio_tab.is_active is False
    
    def test_settings_loads_current_values(self):
        """現在の設定値が読み込まれることを確認"""
        # Given: 設定値を含む設定
        settings_config = {
            'categories': [
                {
                    'id': 'audio',
                    'fields': [
                        {'id': 'master_volume', 'type': 'slider', 'min': 0.0, 'max': 1.0},
                        {'id': 'music_volume', 'type': 'slider', 'min': 0.0, 'max': 1.0}
                    ]
                }
            ]
        }
        
        # モックで現在の設定値を設定
        mock_current_settings = {
            'master_volume': 0.8,
            'music_volume': 0.6
        }
        
        with patch.object(SettingsWindow, '_load_current_settings', return_value=mock_current_settings):
            settings_window = SettingsWindow('value_settings', settings_config)
            settings_window.create()
        
        # Then: 設定値が読み込まれる
        assert settings_window.current_settings['master_volume'] == 0.8
        assert settings_window.current_settings['music_volume'] == 0.6
    
    def test_settings_tab_switching(self):
        """タブ切り替えが動作することを確認"""
        # Given: 複数タブを持つ設定
        settings_config = {
            'categories': [
                {'id': 'gameplay', 'label': 'ゲームプレイ'},
                {'id': 'audio', 'label': '音声設定'}
            ]
        }
        
        settings_window = SettingsWindow('switch_settings', settings_config)
        settings_window.create()
        
        # When: 2番目のタブに切り替え
        settings_window.switch_tab(1)
        
        # Then: タブが切り替わる
        assert settings_window.tabs[0].is_active is False
        assert settings_window.tabs[1].is_active is True
        assert settings_window.current_tab_index == 1
    
    def test_settings_field_value_changes(self):
        """設定フィールドの値変更が動作することを確認"""
        # Given: フィールドを含む設定
        settings_config = {
            'categories': [
                {
                    'id': 'audio',
                    'fields': [
                        {'id': 'master_volume', 'type': 'slider', 'min': 0.0, 'max': 1.0}
                    ]
                }
            ]
        }
        
        settings_window = SettingsWindow('change_settings', settings_config)
        settings_window.create()
        
        # When: フィールド値を変更
        settings_window.set_field_value('master_volume', 0.7)
        
        # Then: 値が変更される
        assert settings_window.get_field_value('master_volume') == 0.7
        assert 'master_volume' in settings_window.pending_changes
        assert settings_window.pending_changes['master_volume'] == 0.7
    
    def test_settings_validation_for_invalid_values(self):
        """無効な値に対する検証が動作することを確認"""
        # Given: 検証ルールを持つ設定
        settings_config = {
            'categories': [
                {
                    'id': 'audio',
                    'fields': [
                        {'id': 'master_volume', 'type': 'slider', 'min': 0.0, 'max': 1.0}
                    ]
                }
            ]
        }
        
        settings_window = SettingsWindow('validation_settings', settings_config)
        settings_window.create()
        
        # When: 範囲外の値を設定しようとする
        result = settings_window.set_field_value('master_volume', 1.5)
        
        # Then: 設定が拒否される
        assert result is False
        assert settings_window.get_field_value('master_volume') != 1.5
    
    def test_settings_apply_changes(self):
        """設定変更の適用が動作することを確認"""
        # Given: 変更のある設定
        settings_config = {
            'categories': [
                {
                    'id': 'audio',
                    'fields': [
                        {'id': 'master_volume', 'type': 'slider', 'min': 0.0, 'max': 1.0}
                    ]
                }
            ]
        }
        
        settings_window = SettingsWindow('apply_settings', settings_config)
        settings_window.create()
        settings_window.set_field_value('master_volume', 0.9)
        
        # When: 変更を適用
        with patch.object(settings_window, 'send_message') as mock_send:
            result = settings_window.apply_changes()
        
        # Then: 変更が適用される
        assert result is True
        assert settings_window.current_settings['master_volume'] == 0.9
        assert len(settings_window.pending_changes) == 0
        mock_send.assert_called_once_with('settings_applied', {
            'settings': settings_window.current_settings
        })
    
    def test_settings_cancel_changes(self):
        """設定変更のキャンセルが動作することを確認"""
        # Given: 変更のある設定
        settings_config = {
            'categories': [
                {
                    'id': 'audio',
                    'fields': [
                        {'id': 'master_volume', 'type': 'slider', 'min': 0.0, 'max': 1.0}
                    ]
                }
            ]
        }
        
        settings_window = SettingsWindow('cancel_settings', settings_config)
        settings_window.create()
        original_value = settings_window.get_field_value('master_volume')
        settings_window.set_field_value('master_volume', 0.9)
        
        # When: 変更をキャンセル
        with patch.object(settings_window, 'send_message') as mock_send:
            settings_window.cancel_changes()
        
        # Then: 変更がキャンセルされる
        assert settings_window.get_field_value('master_volume') == original_value
        assert len(settings_window.pending_changes) == 0
        mock_send.assert_called_once_with('settings_cancelled')
    
    def test_settings_reset_to_defaults(self):
        """デフォルト値へのリセットが動作することを確認"""
        # Given: 変更のある設定
        settings_config = {
            'categories': [
                {
                    'id': 'audio',
                    'fields': [
                        {'id': 'master_volume', 'type': 'slider', 'min': 0.0, 'max': 1.0, 'default': 1.0}
                    ]
                }
            ]
        }
        
        settings_window = SettingsWindow('reset_settings', settings_config)
        settings_window.create()
        settings_window.set_field_value('master_volume', 0.5)
        
        # When: デフォルトにリセット
        settings_window.reset_to_defaults()
        
        # Then: デフォルト値にリセットされる
        assert settings_window.get_field_value('master_volume') == 1.0
    
    def test_settings_keyboard_navigation(self):
        """キーボードナビゲーションが動作することを確認"""
        # Given: 複数タブを持つ設定
        settings_config = {
            'categories': [
                {'id': 'gameplay', 'label': 'ゲームプレイ'},
                {'id': 'audio', 'label': '音声設定'}
            ]
        }
        
        settings_window = SettingsWindow('nav_settings', settings_config)
        settings_window.create()
        
        # When: Tabキーでタブ切り替え
        tab_event = Mock()
        tab_event.type = pygame.KEYDOWN
        tab_event.key = pygame.K_TAB
        tab_event.mod = pygame.KMOD_CTRL
        
        result = settings_window.handle_event(tab_event)
        
        # Then: 次のタブに移動
        assert result is True
        assert settings_window.current_tab_index == 1
    
    def test_settings_escape_key_cancels(self):
        """ESCキーでキャンセルされることを確認"""
        # Given: 設定ウィンドウ
        settings_config = {
            'categories': [
                {'id': 'gameplay', 'label': 'ゲームプレイ'}
            ]
        }
        
        settings_window = SettingsWindow('esc_settings', settings_config)
        settings_window.create()
        
        # When: ESCキーを押す
        with patch.object(settings_window, 'send_message') as mock_send:
            result = settings_window.handle_escape()
        
        # Then: キャンセルされる
        assert result is True
        mock_send.assert_called_once_with('settings_cancelled')
    
    def test_settings_enter_key_applies(self):
        """Enterキーで適用されることを確認"""
        # Given: 設定ウィンドウ
        settings_config = {
            'categories': [
                {'id': 'gameplay', 'label': 'ゲームプレイ'}
            ]
        }
        
        settings_window = SettingsWindow('enter_settings', settings_config)
        settings_window.create()
        
        # When: Enterキーを押す
        enter_event = Mock()
        enter_event.type = pygame.KEYDOWN
        enter_event.key = pygame.K_RETURN
        enter_event.mod = 0
        
        with patch.object(settings_window, 'send_message') as mock_send:
            result = settings_window.handle_event(enter_event)
        
        # Then: 設定が適用される
        assert result is True
        mock_send.assert_called_once_with('settings_applied', {
            'settings': settings_window.current_settings
        })
    
    def test_settings_saves_to_file(self):
        """設定がファイルに保存されることを確認"""
        # Given: 設定ウィンドウ
        settings_config = {
            'categories': [
                {
                    'id': 'audio',
                    'fields': [
                        {'id': 'master_volume', 'type': 'slider', 'min': 0.0, 'max': 1.0}
                    ]
                }
            ]
        }
        
        settings_window = SettingsWindow('save_settings', settings_config)
        settings_window.create()
        settings_window.set_field_value('master_volume', 0.8)
        
        # When: 設定を保存
        with patch.object(settings_window.loader, 'save_settings') as mock_save:
            settings_window.apply_changes()
        
        # Then: ファイル保存が実行される
        mock_save.assert_called_once_with(settings_window.current_settings)
    
    def test_settings_cleanup_removes_ui_elements(self):
        """クリーンアップでUI要素が適切に削除されることを確認"""
        # Given: 作成された設定ウィンドウ
        settings_config = {
            'categories': [
                {'id': 'gameplay', 'label': 'ゲームプレイ'}
            ]
        }
        
        settings_window = SettingsWindow('cleanup_settings', settings_config)
        settings_window.create()
        
        # When: クリーンアップを実行
        settings_window.cleanup_ui()
        
        # Then: UI要素が削除される
        assert len(settings_window.tabs) == 0
        assert settings_window.ui_manager is None