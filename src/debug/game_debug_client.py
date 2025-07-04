"""
ゲームデバッグAPIクライアント

Web APIを使用してゲームをデバッグするためのPythonクライアント。
curlコマンドの代わりにPythonコードでAPIを呼び出すことで、
より柔軟で許可不要なデバッグが可能になる。
"""

import requests
import base64
import json
import time
import sys
import argparse
from typing import Optional, Dict, Any, Tuple
from PIL import Image
from io import BytesIO
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

class GameDebugClient:
    """ゲームデバッグAPIクライアント"""
    
    def __init__(self, base_url: str = "http://localhost:8765", timeout: float = 5.0):
        """
        クライアントを初期化
        
        Args:
            base_url: APIサーバーのベースURL
            timeout: リクエストのタイムアウト秒数
        """
        self.base_url = base_url
        self.timeout = timeout
        self.last_screenshot = None
    
    def is_api_available(self) -> bool:
        """APIサーバーが利用可能かチェック"""
        try:
            response = requests.get(f"{self.base_url}/screenshot", timeout=1)
            return response.status_code == 200
        except:
            return False
    
    def wait_for_api(self, max_wait: float = 10.0) -> bool:
        """APIサーバーが利用可能になるまで待機"""
        start_time = time.time()
        while time.time() - start_time < max_wait:
            if self.is_api_available():
                return True
            time.sleep(0.1)
        return False
    
    def screenshot(self, save_path: Optional[str] = None) -> Image.Image:
        """
        現在の画面のスクリーンショットを取得
        
        Args:
            save_path: 保存先パス（指定した場合は画像を保存）
            
        Returns:
            PIL Image オブジェクト
        """
        response = requests.get(f"{self.base_url}/screenshot", timeout=self.timeout)
        response.raise_for_status()
        
        data = response.json()
        image_data = base64.b64decode(data["jpeg"])
        image = Image.open(BytesIO(image_data))
        
        self.last_screenshot = image
        
        if save_path:
            image.save(save_path)
            logger.info(f"Screenshot saved to: {save_path}")
        
        return image
    
    def send_key(self, code: int, down: bool = True, up: bool = True) -> Dict[str, Any]:
        """
        キー入力を送信
        
        Args:
            code: キーコード（例: 27 = ESC）
            down: キー押下イベントを送信
            up: キー離すイベントを送信
            
        Returns:
            APIレスポンス
        """
        results = []
        
        if down:
            response = requests.post(
                f"{self.base_url}/input/key",
                params={"code": code, "down": True},
                timeout=self.timeout
            )
            response.raise_for_status()
            results.append(response.json())
        
        if up:
            time.sleep(0.05)  # 押下と離すの間に少し待機
            response = requests.post(
                f"{self.base_url}/input/key",
                params={"code": code, "down": False},
                timeout=self.timeout
            )
            response.raise_for_status()
            results.append(response.json())
        
        return results[-1] if results else {"ok": True}
    
    def send_mouse(self, x: int, y: int, action: str = "click", button: int = 1) -> Dict[str, Any]:
        """
        マウス入力を送信
        
        Args:
            x, y: 座標
            action: "click", "down", "up", "move"
            button: マウスボタン番号（1=左、2=中、3=右）
            
        Returns:
            APIレスポンス
        """
        if action == "click":
            # クリックは押下と離すの組み合わせ
            self.send_mouse(x, y, "down", button)
            time.sleep(0.05)
            return self.send_mouse(x, y, "up", button)
        
        response = requests.post(
            f"{self.base_url}/input/mouse",
            params={"x": x, "y": y, "action": action, "button": button},
            timeout=self.timeout
        )
        response.raise_for_status()
        return response.json()
    
    def press_escape(self) -> None:
        """ESCキーを押す"""
        self.send_key(27)
    
    def press_enter(self) -> None:
        """Enterキーを押す"""
        self.send_key(13)
    
    def press_space(self) -> None:
        """スペースキーを押す"""
        self.send_key(32)
    
    def wait_for_transition(self, duration: float = 0.5) -> None:
        """画面遷移を待つ"""
        time.sleep(duration)
    
    def analyze_background_color(self, image: Optional[Image.Image] = None) -> Tuple[int, int, int]:
        """
        画像の平均背景色を分析
        
        Args:
            image: 分析する画像（Noneの場合は最後のスクリーンショット）
            
        Returns:
            (R, G, B) の平均色
        """
        if image is None:
            image = self.last_screenshot
        if image is None:
            raise ValueError("No image to analyze")
        
        # RGBに変換
        rgb_image = image.convert('RGB')
        pixels = list(rgb_image.getdata())
        
        if not pixels:
            return (0, 0, 0)
        
        # 平均色を計算
        r_avg = sum(p[0] for p in pixels) / len(pixels)
        g_avg = sum(p[1] for p in pixels) / len(pixels)
        b_avg = sum(p[2] for p in pixels) / len(pixels)
        
        return (int(r_avg), int(g_avg), int(b_avg))
    
    def is_overworld_background(self, color: Optional[Tuple[int, int, int]] = None) -> bool:
        """地上画面の背景色かチェック"""
        if color is None:
            color = self.analyze_background_color()
        r, g, b = color
        return g > r and g > b and g > 120
    
    def is_settings_background(self, color: Optional[Tuple[int, int, int]] = None) -> bool:
        """設定画面の背景色かチェック"""
        if color is None:
            color = self.analyze_background_color()
        r, g, b = color
        return b > r and b > g and r < 70 and g < 70 and b > 60
    
    def get_game_state(self) -> Dict[str, Any]:
        """
        ゲームの現在の状態を取得
        
        Returns:
            ゲーム状態情報
        """
        response = requests.get(f"{self.base_url}/game/state", timeout=self.timeout)
        response.raise_for_status()
        return response.json()
    
    def get_visible_buttons(self) -> Dict[str, Any]:
        """
        現在表示されているボタンの情報を取得
        
        Returns:
            ボタン情報のリスト
        """
        response = requests.get(f"{self.base_url}/game/visible_buttons", timeout=self.timeout)
        response.raise_for_status()
        return response.json()
    
    def click_button_by_text(self, text: str) -> bool:
        """
        テキストでボタンを検索してクリック
        
        Args:
            text: ボタンのテキスト
            
        Returns:
            クリックできたかどうか
        """
        buttons_info = self.get_visible_buttons()
        buttons = buttons_info.get("buttons", [])
        
        for button in buttons:
            if text in button.get("text", ""):
                center = button.get("center", {})
                x, y = center.get("x"), center.get("y")
                if x and y:
                    self.send_mouse(x, y, "click")
                    logger.info(f"Clicked button '{text}' at ({x}, {y})")
                    return True
        
        logger.warning(f"Button with text '{text}' not found")
        return False
    
    def click_button_by_number(self, number: int) -> bool:
        """
        数字キーでボタンをクリック
        
        Args:
            number: ボタン番号（1-9）
            
        Returns:
            クリックできたかどうか
        """
        if not (1 <= number <= 9):
            logger.error(f"Invalid button number: {number}. Must be between 1 and 9")
            return False
        
        try:
            response = requests.post(
                f"{self.base_url}/input/shortcut_key",
                params={"key": str(number)},
                timeout=self.timeout
            )
            response.raise_for_status()
            
            result = response.json()
            if result.get("ok"):
                logger.info(f"Successfully clicked button {number}: {result.get('message')}")
                return True
            else:
                logger.error(f"Failed to click button {number}: {result}")
                return False
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Network error clicking button {number}: {str(e)}")
            return False
        except Exception as e:
            logger.error(f"Error clicking button {number}: {str(e)}")
            return False
    
    def show_button_shortcuts(self, buttons_info: Optional[Dict[str, Any]] = None) -> None:
        """
        現在のボタンとショートカットキーを表示
        
        Args:
            buttons_info: ボタン情報（Noneの場合は自動取得）
        """
        if buttons_info is None:
            buttons_info = self.get_visible_buttons()
        
        buttons = buttons_info.get("buttons", [])
        
        print("=== Available Buttons ===")
        for button in buttons:
            shortcut_key = button.get("shortcut_key")
            text = button.get("text", "")
            if shortcut_key:
                print(f"  {shortcut_key}: {text}")
            else:
                print(f"  -: {text}")
        
        total_count = len(buttons)
        shortcut_count = sum(1 for b in buttons if b.get("shortcut_key"))
        print(f"\nTotal buttons: {total_count}, With shortcuts: {shortcut_count}")
    
    def press_number_key(self, number: int) -> Dict[str, Any]:
        """
        数字キーを直接押す（ショートカットキー機能を使わない場合）
        
        Args:
            number: 数字（1-9）
            
        Returns:
            APIレスポンス
        """
        if not (1 <= number <= 9):
            raise ValueError(f"Invalid number: {number}. Must be between 1 and 9")
        
        # 数字キーのキーコードは 49-57 (1-9)
        key_code = 48 + number  # 0は48、1は49...
        return self.send_key(key_code)
    
    def get_ui_hierarchy(self) -> Optional[Dict[str, Any]]:
        """
        UI階層情報を取得
        
        Returns:
            UI階層情報の辞書、失敗時はNone
        """
        try:
            response = requests.get(
                f"{self.base_url}/ui/hierarchy",
                timeout=self.timeout
            )
            if response.status_code == 200:
                data = response.json()
                return data.get('hierarchy', {})
            else:
                logger.error(f"Failed to get UI hierarchy: {response.status_code}")
                return None
        except Exception as e:
            logger.error(f"Error getting UI hierarchy: {e}")
            return None


def main():
    """コマンドライン実行"""
    parser = argparse.ArgumentParser(description="Game Debug API Client")
    parser.add_argument("command", choices=["screenshot", "key", "mouse", "escape", "enter", "space", "analyze", "buttons", "click"],
                      help="実行するコマンド")
    parser.add_argument("--save", "-s", help="スクリーンショット保存先")
    parser.add_argument("--code", "-c", type=int, help="キーコード")
    parser.add_argument("--x", type=int, help="マウスX座標")
    parser.add_argument("--y", type=int, help="マウスY座標")
    parser.add_argument("--action", default="click", help="マウスアクション")
    parser.add_argument("--wait", "-w", type=float, default=0, help="実行前の待機時間")
    parser.add_argument("--number", "-n", type=int, help="ボタン番号（1-9）")
    parser.add_argument("--text", "-t", help="ボタンテキスト")
    
    args = parser.parse_args()
    
    client = GameDebugClient()
    
    # API待機
    if not client.wait_for_api():
        logger.error("Game API is not available")
        sys.exit(1)
    
    # 待機
    if args.wait > 0:
        time.sleep(args.wait)
    
    # コマンド実行
    if args.command == "screenshot":
        image = client.screenshot(args.save)
        if not args.save:
            logger.info(f"Screenshot captured: {image.size}")
    
    elif args.command == "key":
        if args.code is None:
            logger.error("--code is required for key command")
            sys.exit(1)
        result = client.send_key(args.code)
        logger.info(f"Key sent: {result}")
    
    elif args.command == "mouse":
        if args.x is None or args.y is None:
            logger.error("--x and --y are required for mouse command")
            sys.exit(1)
        result = client.send_mouse(args.x, args.y, args.action)
        logger.info(f"Mouse action sent: {result}")
    
    elif args.command == "escape":
        client.press_escape()
        logger.info("ESC key pressed")
    
    elif args.command == "enter":
        client.press_enter()
        logger.info("Enter key pressed")
    
    elif args.command == "space":
        client.press_space()
        logger.info("Space key pressed")
    
    elif args.command == "analyze":
        client.screenshot()
        color = client.analyze_background_color()
        logger.info(f"Average color: RGB{color}")
        logger.info(f"Is overworld: {client.is_overworld_background(color)}")
        logger.info(f"Is settings: {client.is_settings_background(color)}")
    
    elif args.command == "buttons":
        buttons_info = client.get_visible_buttons()
        client.show_button_shortcuts(buttons_info)
    
    elif args.command == "click":
        if args.number is not None:
            success = client.click_button_by_number(args.number)
            if success:
                logger.info(f"Successfully clicked button {args.number}")
            else:
                logger.error(f"Failed to click button {args.number}")
                sys.exit(1)
        elif args.text is not None:
            success = client.click_button_by_text(args.text)
            if success:
                logger.info(f"Successfully clicked button '{args.text}'")
            else:
                logger.error(f"Failed to click button '{args.text}'")
                sys.exit(1)
        else:
            logger.error("--number or --text is required for click command")
            sys.exit(1)


if __name__ == "__main__":
    main()