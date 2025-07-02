"""
背景表示問題（0052）のテスト

現象: ESCを押すと背景とメニューボタンが設定画面になる。
しかし、再度ESCを押すとメニューボタンだけが地上になり、背景は設定画面のまま

期待動作:
1. 初期状態: 地上画面（緑背景）
2. ESC押下1回目: 設定画面（濃い青背景）
3. ESC押下2回目: 地上画面（緑背景）に戻る

TDDアプローチ: まずテストを書いて失敗を確認し、その後実装を修正する

実行方法:
- 通常のテスト実行では除外: uv run pytest
- このテストを含める場合: uv run pytest -m "integration or slow"
- このテストのみ実行: uv run pytest -m integration tests/test_background_display_fix.py
"""

import pytest


@pytest.mark.integration
@pytest.mark.slow
class TestBackgroundDisplayFix:
    """背景表示問題の修正テスト（リファクタリング版）"""
    
    def test_initial_background_is_overworld(self, game_api_client):
        """テスト1: 初期状態が地上画面（緑背景）であること"""
        # 初期画面のスクリーンショットを取得
        game_api_client.screenshot()
        avg_color = game_api_client.analyze_background_color()
        
        # デバッグ情報
        print(f"初期画面の平均色: {avg_color}")
        
        # 地上背景であることを確認
        assert game_api_client.is_overworld_background(avg_color), \
            f"初期背景が地上画面ではありません。平均色: {avg_color}"
    
    def test_first_escape_shows_settings_background(self, game_api_client):
        """テスト2: 1回目のESC押下で設定画面（濃い青背景）になること"""
        # ESCキーを1回押下
        game_api_client.press_escape()
        game_api_client.wait_for_transition()
        
        # 設定画面のスクリーンショットを取得
        game_api_client.screenshot()
        avg_color = game_api_client.analyze_background_color()
        
        # デバッグ情報
        print(f"1回目ESC後の平均色: {avg_color}")
        
        # 設定背景であることを確認
        assert game_api_client.is_settings_background(avg_color), \
            f"1回目ESC後の背景が設定画面ではありません。平均色: {avg_color}"
    
    def test_second_escape_returns_to_overworld_background(self, game_api_client):
        """テスト3: 2回目のESC押下で地上画面（緑背景）に戻ること - 現在失敗するテスト"""
        # 既に設定画面にいる状態から2回目のESCキーを押下
        game_api_client.press_escape()
        game_api_client.wait_for_transition()
        
        # 地上画面に戻った後のスクリーンショットを取得
        game_api_client.screenshot()
        avg_color = game_api_client.analyze_background_color()
        
        # デバッグ情報
        print(f"2回目ESC後の平均色: {avg_color}")
        
        # これが現在失敗するテスト - 背景が地上画面に戻らない
        assert game_api_client.is_overworld_background(avg_color), \
            f"2回目ESC後の背景が地上画面に戻りません。平均色: {avg_color} " \
            f"（期待: 緑系の地上背景、実際: {avg_color}）"
    
    def test_multiple_transitions_work_correctly(self, game_api_client):
        """テスト4: 複数回の画面遷移が正しく動作すること - 現在失敗するテスト"""
        # 初期状態から複数回のESC押下をテスト
        transitions = []
        
        # 初期状態
        game_api_client.screenshot()
        avg_color = game_api_client.analyze_background_color()
        transitions.append(("initial", avg_color))
        
        # 3回のESC押下をテスト
        for i in range(3):
            game_api_client.press_escape()
            game_api_client.wait_for_transition()
            game_api_client.screenshot()
            avg_color = game_api_client.analyze_background_color()
            transitions.append((f"esc_{i+1}", avg_color))
        
        # デバッグ情報
        for state, color in transitions:
            print(f"{state}: {color}")
        
        # 期待される遷移パターン
        # initial: 地上画面（緑）
        # esc_1: 設定画面（青）
        # esc_2: 地上画面（緑）- 現在失敗
        # esc_3: 設定画面（青）
        
        assert game_api_client.is_overworld_background(transitions[0][1]), "初期状態が地上画面ではない"
        assert game_api_client.is_settings_background(transitions[1][1]), "1回目ESC後が設定画面ではない"
        assert game_api_client.is_overworld_background(transitions[2][1]), "2回目ESC後が地上画面に戻らない（バグ）"
        assert game_api_client.is_settings_background(transitions[3][1]), "3回目ESC後が設定画面ではない"
    
    def test_esc_transition_with_debug_helper(self, debug_helper):
        """テスト5: デバッグヘルパーを使用したESC遷移テスト"""
        results = debug_helper.verify_esc_transition(save_screenshots=True)
        
        print(f"\n=== Debug Helper Results ===")
        print(f"Initial: {results['initial_state']}")
        print(f"After 1st ESC: {results['after_first_esc']}")
        print(f"After 2nd ESC: {results['after_second_esc']}")
        print(f"Transitions correct: {results['transitions_correct']}")
        
        if results['error']:
            pytest.fail(f"Debug helper error: {results['error']}")
        
        # 現在失敗する予定のテスト
        assert results['transitions_correct'], \
            "ESC transition sequence is not working correctly"


if __name__ == "__main__":
    # 個別テスト実行用（デバッグヘルパーを使用）
    from src.debug.debug_helper import quick_debug_esc_issue
    quick_debug_esc_issue()