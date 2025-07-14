"""
パーティ状況表示問題（0053）のテスト

現象: ESC -> [パーティ状況]を押下しても、パーティ状況を表示するウィンドウが表示されない

期待動作:
1. 初期状態: 地上画面
2. ESC押下: 設定メニュー表示
3. パーティ状況ボタンクリック: パーティ状況画面が表示される

実行方法:
- 通常のテスト実行では除外: uv run pytest
- このテストを含める場合: uv run pytest -m integration
- このテストのみ実行: uv run pytest -m integration tests/test_party_status_display.py
"""

import pytest
import time


@pytest.mark.integration
@pytest.mark.slow
class TestPartyStatusDisplay:
    """パーティ状況表示のテスト"""
    
    def test_party_status_button_opens_party_screen(self, game_api_client):
        """テスト1: 設定メニューからパーティ状況ボタンをクリックすると画面が遷移すること"""
        # 初期状態の確認
        game_api_client.screenshot()
        initial_color = game_api_client.analyze_background_color()
        assert game_api_client.is_overworld_background(initial_color), \
            f"初期状態が地上画面ではありません。色: {initial_color}"
        
        # ESCキーで設定メニューを開く
        game_api_client.press_escape()
        game_api_client.wait_for_transition()
        
        game_api_client.screenshot()
        settings_color = game_api_client.analyze_background_color()
        assert game_api_client.is_settings_background(settings_color), \
            f"設定メニューが表示されていません。色: {settings_color}"
        
        # パーティ状況ボタンをクリック（最初のボタン）
        # ボタンの推定位置
        button_x = 200  # ボタンの中央X座標
        button_y = 125  # 最初のボタンのY座標
        
        game_api_client.send_mouse(button_x, button_y, "click")
        game_api_client.wait_for_transition(1.0)
        
        # 画面が変化したことを確認
        game_api_client.screenshot()
        after_click_color = game_api_client.analyze_background_color()
        
        # パーティ状況画面に遷移したことを確認（設定画面とは異なる色になるはず）
        assert after_click_color != settings_color, \
            f"パーティ状況ボタンクリック後も画面が変化していません。色: {after_click_color}"
        
        # 地上画面にも戻っていないことを確認
        assert not game_api_client.is_overworld_background(after_click_color), \
            "パーティ状況画面ではなく地上画面に戻ってしまいました"
    
    def test_party_status_shows_party_information(self, game_api_client, debug_helper):
        """テスト2: パーティ状況画面にパーティ情報が表示されること"""
        # デバッグヘルパーを使用してアクションシーケンスを実行
        captures = debug_helper.capture_transition_sequence([
            ("escape", None),  # 設定メニューを開く
            ("wait", 0.5),
            ("mouse", {"x": 200, "y": 125, "action": "click"}),  # パーティ状況ボタン
            ("wait", 1.0)
        ], output_dir="test_party_status_captures")
        
        # キャプチャが4つあることを確認（初期、ESC後、クリック後）
        assert len(captures) >= 3, f"期待されるキャプチャ数と異なります: {len(captures)}"
        
        # 最後のキャプチャ（パーティ状況画面）が異なることを確認
        comparison = debug_helper.compare_screenshots(captures[1], captures[-1])
        assert not comparison["identical"], "パーティ状況画面が表示されていません"
        
        # 画面の色が変化していることを確認
        color1 = comparison["color1"]  # ESC後（設定メニュー）
        color2 = comparison["color2"]  # クリック後（パーティ状況画面のはず）
        
        assert color1 != color2, \
            f"画面の色が変化していません。設定: {color1}, クリック後: {color2}"
    
    def test_escape_returns_from_party_status(self, game_api_client):
        """テスト3: パーティ状況画面からESCで設定メニューに戻れること"""
        # 設定メニューを開く
        game_api_client.press_escape()
        game_api_client.wait_for_transition()
        
        # パーティ状況を開く
        game_api_client.send_mouse(200, 125, "click")
        game_api_client.wait_for_transition(1.0)
        
        game_api_client.screenshot()
        party_status_color = game_api_client.analyze_background_color()
        
        # ESCキーで戻る
        game_api_client.press_escape()
        game_api_client.wait_for_transition()
        
        game_api_client.screenshot()
        after_esc_color = game_api_client.analyze_background_color()
        
        # 設定メニューに戻ったことを確認
        assert game_api_client.is_settings_background(after_esc_color), \
            f"ESC後に設定メニューに戻りませんでした。色: {after_esc_color}"
        
        # パーティ状況画面から変化したことを確認
        assert after_esc_color != party_status_color, \
            "ESCを押しても画面が変化していません"


if __name__ == "__main__":
    # デバッグ実行用
    from src.debug.game_debug_client import GameDebugClient
    from src.debug.debug_helper import DebugHelper
    
    client = GameDebugClient()
    if client.wait_for_api():
        helper = DebugHelper(client)
        
        # テスト1を手動実行
        print("=== パーティ状況ボタンのテスト ===")
        test = TestPartyStatusDisplay()
        try:
            test.test_party_status_button_opens_party_screen(client)
            print("✓ テスト成功")
        except AssertionError as e:
            print(f"✗ テスト失敗: {e}")