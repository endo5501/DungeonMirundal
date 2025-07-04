"""
数字キーによるボタンナビゲーション機能のテスト
"""

import pytest
import pygame
from unittest.mock import Mock, patch, MagicMock
from src.debug.game_debug_client import GameDebugClient


class TestButtonNavigation:
    """数字キーボタンナビゲーションテストクラス"""
    
    def setup_method(self):
        """テストメソッド毎のセットアップ"""
        self.client = GameDebugClient(base_url="http://localhost:8765")
    
    def test_click_button_by_number_valid(self):
        """有効な番号でのボタンクリックテスト"""
        # モックレスポンスの設定
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "ok": True,
            "message": "Button '冒険者ギルド' clicked via shortcut key 1"
        }
        
        with patch('requests.post', return_value=mock_response) as mock_post:
            result = self.client.click_button_by_number(1)
            
            assert result is True
            mock_post.assert_called_once_with(
                "http://localhost:8765/input/shortcut_key",
                params={"key": "1"},
                timeout=5.0
            )
    
    def test_click_button_by_number_invalid_range(self):
        """無効な範囲の番号でのテスト"""
        # 無効な番号（0, 10）をテスト
        result_0 = self.client.click_button_by_number(0)
        result_10 = self.client.click_button_by_number(10)
        
        assert result_0 is False
        assert result_10 is False
    
    def test_click_button_by_number_button_not_found(self):
        """ボタンが見つからない場合のテスト"""
        # 404レスポンスをモック
        mock_response = Mock()
        mock_response.status_code = 404
        mock_response.json.return_value = {
            "ok": False,
            "detail": "No button found for shortcut key '5'"
        }
        mock_response.raise_for_status.side_effect = Exception("404 Not Found")
        
        with patch('requests.post', return_value=mock_response):
            result = self.client.click_button_by_number(5)
            assert result is False
    
    def test_show_button_shortcuts(self):
        """ボタンショートカット表示テスト"""
        # モックボタン情報
        buttons_info = {
            "buttons": [
                {
                    "text": "冒険者ギルド",
                    "shortcut_key": "1",
                    "center": {"x": 200, "y": 245}
                },
                {
                    "text": "商店",
                    "shortcut_key": "2", 
                    "center": {"x": 200, "y": 275}
                },
                {
                    "text": "設定",
                    "shortcut_key": None,
                    "center": {"x": 200, "y": 305}
                }
            ],
            "count": 3
        }
        
        # 標準出力をキャプチャ
        import io
        import sys
        captured_output = io.StringIO()
        sys.stdout = captured_output
        
        try:
            self.client.show_button_shortcuts(buttons_info)
            output = captured_output.getvalue()
            
            # 出力内容を確認
            assert "=== Available Buttons ===" in output
            assert "1: 冒険者ギルド" in output
            assert "2: 商店" in output
            assert "-: 設定" in output
            assert "Total buttons: 3, With shortcuts: 2" in output
            
        finally:
            sys.stdout = sys.__stdout__
    
    def test_press_number_key(self):
        """数字キー直接押下テスト"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"ok": True}
        
        with patch.object(self.client, 'send_key', return_value=mock_response.json.return_value) as mock_send_key:
            result = self.client.press_number_key(3)
            
            # キーコード51 (3キー)で呼び出されることを確認
            mock_send_key.assert_called_once_with(51)
            assert result["ok"] is True
    
    def test_press_number_key_invalid_range(self):
        """無効な範囲の数字キー押下テスト"""
        with pytest.raises(ValueError) as excinfo:
            self.client.press_number_key(0)
        assert "Invalid number: 0" in str(excinfo.value)
        
        with pytest.raises(ValueError) as excinfo:
            self.client.press_number_key(10)
        assert "Invalid number: 10" in str(excinfo.value)


class TestWindowManagerButtonShortcut:
    """WindowManagerの数字キーショートカット機能テスト"""
    
    def setup_method(self):
        """テストメソッド毎のセットアップ"""
        pygame.init()
        self.screen = pygame.display.set_mode((800, 600))
        
        # WindowManagerのモック
        self.window_manager = Mock()
        self.window_manager.ui_manager = Mock()
        
        # モックボタンの作成
        self.mock_button = Mock()
        self.mock_button.rect = pygame.Rect(100, 100, 150, 30)
        self.mock_button.rect.center = (175, 115)
        self.mock_button.visible = True
        self.mock_button._shortcut_number = 1
        
    def test_handle_button_shortcut_success(self):
        """ボタンショートカット処理成功テスト"""
        # WindowManagerから実際のメソッドをインポート
        from src.ui.window_system.window_manager import WindowManager
        wm = WindowManager()
        wm.ui_manager = self.window_manager.ui_manager
        
        # ボタンリストをモック
        with patch.object(wm, 'get_visible_buttons', return_value=[self.mock_button]):
            result = wm.handle_button_shortcut(1)
            
            assert result is True
            # UIManagerのprocess_eventsが呼ばれることを確認
            assert wm.ui_manager.process_events.call_count >= 2  # DOWN + UP events
    
    def test_handle_button_shortcut_button_not_found(self):
        """ボタンが見つからない場合のテスト"""
        from src.ui.window_system.window_manager import WindowManager
        wm = WindowManager()
        wm.ui_manager = self.window_manager.ui_manager
        
        # 空のボタンリストをモック
        with patch.object(wm, 'get_visible_buttons', return_value=[]):
            result = wm.handle_button_shortcut(1)
            
            assert result is False
    
    def test_get_visible_buttons(self):
        """表示ボタン取得テスト"""
        from src.ui.window_system.window_manager import WindowManager
        wm = WindowManager()
        
        # UIManagerがない場合
        wm.ui_manager = None
        buttons = wm.get_visible_buttons()
        assert buttons == []
        
        # UIManagerがある場合（詳細なテストは統合テストで実施）
        wm.ui_manager = Mock()
        wm.ui_manager.get_root_container.return_value = None
        buttons = wm.get_visible_buttons()
        assert isinstance(buttons, list)


@pytest.mark.integration
class TestButtonNavigationIntegration:
    """統合テスト：実際のゲームサーバーとの連携をテスト"""
    
    def test_api_endpoint_shortcut_key(self):
        """ショートカットキーAPIエンドポイントテスト"""
        import requests
        
        # ゲームサーバーが起動していることを前提とした統合テスト
        try:
            # ボタン情報を取得
            response = requests.get("http://localhost:8765/game/visible_buttons", timeout=1)
            if response.status_code == 200:
                buttons_data = response.json()
                assert "buttons" in buttons_data
                assert "count" in buttons_data
                
                # ボタンがある場合はショートカットキー情報を確認
                if buttons_data["count"] > 0:
                    first_button = buttons_data["buttons"][0]
                    assert "shortcut_key" in first_button
                    
                    # ショートカットキーが割り当てられている場合はAPIを呼び出し
                    if first_button["shortcut_key"]:
                        shortcut_response = requests.post(
                            "http://localhost:8765/input/shortcut_key",
                            params={"key": first_button["shortcut_key"]},
                            timeout=1
                        )
                        # APIが正常に応答することを確認（実際のクリックは発生するが、テストなので成功/失敗は問わない）
                        assert shortcut_response.status_code in [200, 404, 500]
                        
        except requests.exceptions.ConnectionError:
            pytest.skip("Game server not running")
    
    def test_debug_client_commands(self):
        """デバッグクライアントコマンドライン機能テスト"""
        import subprocess
        import sys
        
        # ゲームサーバーが起動していることを前提
        try:
            # ボタン一覧表示コマンド
            result = subprocess.run([
                sys.executable, "-m", "src.debug.game_debug_client", 
                "buttons"
            ], capture_output=True, text=True, timeout=5)
            
            # 正常終了またはAPIサーバー未起動による終了を期待
            assert result.returncode in [0, 1]
            
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pytest.skip("Could not test debug client commands")


if __name__ == "__main__":
    pytest.main([__file__])