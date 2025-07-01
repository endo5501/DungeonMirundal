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
import requests
import base64
import io
from PIL import Image
import time


@pytest.mark.integration
@pytest.mark.slow
class TestBackgroundDisplayFix:
    """背景表示問題の修正テスト"""
    
    @pytest.fixture(scope="class")
    def api_base_url(self):
        """デバッグAPIのベースURL"""
        return "http://localhost:8765"
    
    def get_screenshot_as_image(self, api_base_url):
        """スクリーンショットを取得してPIL Imageとして返す"""
        try:
            response = requests.get(f"{api_base_url}/screenshot", timeout=5)
            response.raise_for_status()
            data = response.json()
            image_data = base64.b64decode(data["jpeg"])
            return Image.open(io.BytesIO(image_data))
        except Exception as e:
            pytest.fail(f"スクリーンショット取得に失敗: {e}")
    
    def send_escape_key(self, api_base_url):
        """ESCキーを送信"""
        try:
            response = requests.post(
                f"{api_base_url}/input/key",
                params={"code": 27, "down": True},
                timeout=5
            )
            response.raise_for_status()
            time.sleep(0.5)  # UI更新を待つ
        except Exception as e:
            pytest.fail(f"ESCキー送信に失敗: {e}")
    
    def analyze_background_color(self, image):
        """画像の背景色を分析（主要色を抽出）"""
        # 画像をRGBに変換
        rgb_image = image.convert('RGB')
        
        # 各色成分の平均値を計算
        pixels = list(rgb_image.getdata())
        total_pixels = len(pixels)
        
        if total_pixels == 0:
            return (0, 0, 0)
        
        # RGBの平均値を計算
        r_avg = sum(pixel[0] for pixel in pixels) / total_pixels
        g_avg = sum(pixel[1] for pixel in pixels) / total_pixels
        b_avg = sum(pixel[2] for pixel in pixels) / total_pixels
        
        return (int(r_avg), int(g_avg), int(b_avg))
    
    def is_overworld_background(self, avg_color):
        """地上背景（緑系）かどうかを判定"""
        r, g, b = avg_color
        # 地上部は緑が強い (100, 150, 100) 程度
        return g > r and g > b and g > 120
    
    def is_settings_background(self, avg_color):
        """設定背景（濃い青系）かどうかを判定"""
        r, g, b = avg_color
        # 設定画面は青が強く、全体的に暗い (50, 50, 80) 程度
        return b > r and b > g and r < 70 and g < 70 and b > 60
    
    def test_initial_background_is_overworld(self, api_base_url):
        """テスト1: 初期状態が地上画面（緑背景）であること"""
        # 初期画面のスクリーンショットを取得
        image = self.get_screenshot_as_image(api_base_url)
        avg_color = self.analyze_background_color(image)
        
        # デバッグ情報
        print(f"初期画面の平均色: {avg_color}")
        
        # 地上背景であることを確認
        assert self.is_overworld_background(avg_color), \
            f"初期背景が地上画面ではありません。平均色: {avg_color}"
    
    def test_first_escape_shows_settings_background(self, api_base_url):
        """テスト2: 1回目のESC押下で設定画面（濃い青背景）になること"""
        # ESCキーを1回押下
        self.send_escape_key(api_base_url)
        
        # 設定画面のスクリーンショットを取得
        image = self.get_screenshot_as_image(api_base_url)
        avg_color = self.analyze_background_color(image)
        
        # デバッグ情報
        print(f"1回目ESC後の平均色: {avg_color}")
        
        # 設定背景であることを確認
        assert self.is_settings_background(avg_color), \
            f"1回目ESC後の背景が設定画面ではありません。平均色: {avg_color}"
    
    def test_second_escape_returns_to_overworld_background(self, api_base_url):
        """テスト3: 2回目のESC押下で地上画面（緑背景）に戻ること - 現在失敗するテスト"""
        # 既に設定画面にいる状態から2回目のESCキーを押下
        self.send_escape_key(api_base_url)
        
        # 地上画面に戻った後のスクリーンショットを取得
        image = self.get_screenshot_as_image(api_base_url)
        avg_color = self.analyze_background_color(image)
        
        # デバッグ情報
        print(f"2回目ESC後の平均色: {avg_color}")
        
        # これが現在失敗するテスト - 背景が地上画面に戻らない
        assert self.is_overworld_background(avg_color), \
            f"2回目ESC後の背景が地上画面に戻りません。平均色: {avg_color} " \
            f"（期待: 緑系の地上背景、実際: {avg_color}）"
    
    def test_multiple_transitions_work_correctly(self, api_base_url):
        """テスト4: 複数回の画面遷移が正しく動作すること - 現在失敗するテスト"""
        # 初期状態から複数回のESC押下をテスト
        transitions = []
        
        # 初期状態
        image = self.get_screenshot_as_image(api_base_url)
        avg_color = self.analyze_background_color(image)
        transitions.append(("initial", avg_color))
        
        # 3回のESC押下をテスト
        for i in range(3):
            self.send_escape_key(api_base_url)
            image = self.get_screenshot_as_image(api_base_url)
            avg_color = self.analyze_background_color(image)
            transitions.append((f"esc_{i+1}", avg_color))
        
        # デバッグ情報
        for state, color in transitions:
            print(f"{state}: {color}")
        
        # 期待される遷移パターン
        # initial: 地上画面（緑）
        # esc_1: 設定画面（青）
        # esc_2: 地上画面（緑）- 現在失敗
        # esc_3: 設定画面（青）
        
        assert self.is_overworld_background(transitions[0][1]), "初期状態が地上画面ではない"
        assert self.is_settings_background(transitions[1][1]), "1回目ESC後が設定画面ではない"
        assert self.is_overworld_background(transitions[2][1]), "2回目ESC後が地上画面に戻らない（バグ）"
        assert self.is_settings_background(transitions[3][1]), "3回目ESC後が設定画面ではない"


if __name__ == "__main__":
    # 個別テスト実行用
    test_instance = TestBackgroundDisplayFix()
    api_url = "http://localhost:8765"
    
    print("=== 背景表示問題のテスト実行 ===")
    
    try:
        print("1. 初期背景テスト...")
        test_instance.test_initial_background_is_overworld(api_url)
        print("✓ 初期背景テスト合格")
        
        print("2. 1回目ESC背景テスト...")
        test_instance.test_first_escape_shows_settings_background(api_url)
        print("✓ 1回目ESC背景テスト合格")
        
        print("3. 2回目ESC背景テスト...")
        test_instance.test_second_escape_returns_to_overworld_background(api_url)
        print("✓ 2回目ESC背景テスト合格")
        
        print("4. 複数遷移テスト...")
        test_instance.test_multiple_transitions_work_correctly(api_url)
        print("✓ 複数遷移テスト合格")
        
    except AssertionError as e:
        print(f"✗ テスト失敗: {e}")
    except Exception as e:
        print(f"✗ テスト実行エラー: {e}")