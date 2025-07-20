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
    
    def press_escape(self) -> bool:
        """ESCキーを押す"""
        try:
            result = self.send_key(27)
            return result.get("ok", False)
        except Exception:
            return False
    
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
                # 拡張されたAPIエンドポイントは直接階層情報を返す
                if 'hierarchy' in data:
                    # 旧形式との互換性
                    return data['hierarchy']
                else:
                    # 新形式（直接レスポンス）
                    return data
            else:
                logger.error(f"Failed to get UI hierarchy: {response.status_code}")
                return None
        except Exception as e:
            logger.error(f"Error getting UI hierarchy: {e}")
            return None
    
    def get_party_info(self) -> Optional[Dict[str, Any]]:
        """
        現在のパーティ情報を取得
        
        Returns:
            パーティ情報の辞書、失敗時はNone
        """
        try:
            response = requests.get(
                f"{self.base_url}/party/info",
                timeout=self.timeout
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Error getting party info: {e}")
            return None
    
    def get_character_details(self, character_index: int) -> Optional[Dict[str, Any]]:
        """
        特定のキャラクターの詳細情報を取得
        
        Args:
            character_index: パーティ内のキャラクターインデックス（0から始まる）
            
        Returns:
            キャラクター詳細情報の辞書、失敗時はNone
        """
        try:
            response = requests.get(
                f"{self.base_url}/party/character/{character_index}",
                timeout=self.timeout
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Error getting character details for index {character_index}: {e}")
            return None
    
    def get_adventure_guild_list(self) -> Optional[Dict[str, Any]]:
        """
        冒険者ギルドに登録されたキャラクター一覧を取得
        
        Returns:
            ギルドキャラクター情報の辞書、失敗時はNone
        """
        try:
            response = requests.get(
                f"{self.base_url}/adventure/list",
                timeout=self.timeout
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Error getting adventure guild list: {e}")
            return None
    
    def get_game_manager_debug_info(self) -> Optional[Dict[str, Any]]:
        """
        GameManagerアクセスのデバッグ情報を取得
        
        Returns:
            デバッグ情報の辞書、失敗時はNone
        """
        try:
            response = requests.get(
                f"{self.base_url}/debug/game_manager",
                timeout=self.timeout
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Error getting game manager debug info: {e}")
            return None
    
    def get_facility_ui_debug_info(self) -> Optional[Dict[str, Any]]:
        """
        施設UI専用のデバッグ情報を取得
        
        Returns:
            施設UIデバッグ情報の辞書、失敗時はNone
        """
        try:
            response = requests.get(
                f"{self.base_url}/debug/facility-ui",
                timeout=self.timeout
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Error getting facility UI debug info: {e}")
            return None
    
    def create_ui_snapshot(self) -> Optional[Dict[str, Any]]:
        """
        現在のUI状態のスナップショットを作成
        
        Returns:
            UIスナップショット情報の辞書、失敗時はNone
        """
        try:
            response = requests.get(
                f"{self.base_url}/debug/ui-snapshot",
                timeout=self.timeout
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Error creating UI snapshot: {e}")
            return None
    
    def get_server_status(self) -> Optional[Dict[str, Any]]:
        """
        デバッグサーバの状態を取得
        
        Returns:
            サーバ状態情報の辞書、失敗時はNone
        """
        try:
            response = requests.get(
                f"{self.base_url}/status",
                timeout=self.timeout
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Error getting server status: {e}")
            return None
    
    def add_debug_log(self, level: str, message: str, context: Optional[Dict[str, Any]] = None) -> bool:
        """
        カスタムデバッグログエントリを追加
        
        Args:
            level: ログレベル（DEBUG, INFO, WARNING, ERROR）
            message: ログメッセージ
            context: 追加のコンテキスト情報
            
        Returns:
            成功したかどうか
        """
        try:
            response = requests.post(
                f"{self.base_url}/debug/log",
                params={"level": level, "message": message},
                json=context or {},
                timeout=self.timeout
            )
            response.raise_for_status()
            return response.json().get("ok", False)
        except Exception as e:
            logger.error(f"Error adding debug log: {e}")
            return False
    
    def display_party_info(self, party_info: Optional[Dict[str, Any]] = None) -> None:
        """
        パーティ情報を見やすく表示
        
        Args:
            party_info: パーティ情報（Noneの場合は自動取得）
        """
        if party_info is None:
            party_info = self.get_party_info()
        
        if not party_info:
            print("❌ パーティ情報を取得できませんでした")
            return
        
        print("=== Party Information ===")
        if party_info.get("party_exists"):
            print(f"パーティ名: {party_info.get('party_name', 'Unknown')}")
            print(f"パーティID: {party_info.get('party_id', 'Unknown')}")
            print(f"所持金: {party_info.get('gold', 0)} ゴールド")
            print(f"メンバー数: {party_info.get('character_count', 0)}")
            
            characters = party_info.get("characters", [])
            if characters:
                print("\n--- メンバー一覧 ---")
                for i, char in enumerate(characters):
                    print(f"  {i}: {char.get('name', 'Unknown')} (Lv.{char.get('level', 1)}) - {char.get('hp', 0)}/{char.get('max_hp', 0)} HP - {char.get('status', 'unknown')}")
            else:
                print("メンバーがいません")
        else:
            print("❌ アクティブなパーティがありません")
    
    def display_character_details(self, character_index: int, character_info: Optional[Dict[str, Any]] = None) -> None:
        """
        キャラクター詳細情報を見やすく表示
        
        Args:
            character_index: キャラクターインデックス
            character_info: キャラクター情報（Noneの場合は自動取得）
        """
        if character_info is None:
            character_info = self.get_character_details(character_index)
        
        if not character_info:
            print(f"❌ キャラクター情報を取得できませんでした (index: {character_index})")
            return
        
        if not character_info.get("character_exists"):
            print(f"❌ キャラクター {character_index} は存在しません")
            return
        
        print(f"=== Character Details (Index: {character_index}) ===")
        print(f"名前: {character_info.get('name', 'Unknown')}")
        print(f"種族: {character_info.get('race', 'Unknown')}")
        print(f"職業: {character_info.get('character_class', 'Unknown')}")
        print(f"レベル: {character_info.get('level', 1)}")
        print(f"経験値: {character_info.get('experience', 0)}")
        print(f"HP: {character_info.get('hp', 0)}/{character_info.get('max_hp', 0)}")
        print(f"MP: {character_info.get('mp', 0)}/{character_info.get('max_mp', 0)}")
        print(f"状態: {character_info.get('condition', 'Unknown')}")
        print(f"生存: {'はい' if character_info.get('is_alive', True) else 'いいえ'}")
        
        # 基本ステータス
        stats = character_info.get("stats", {})
        if stats:
            print("\n--- 基本ステータス ---")
            for stat_name, value in stats.items():
                print(f"  {stat_name.title()}: {value}")
        
        # 装備アイテム
        equipment = character_info.get("equipment", [])
        if equipment:
            print("\n--- 装備中のアイテム ---")
            for item in equipment:
                item_desc = f"  * {item.get('slot', 'unknown')}: {item.get('item_name', 'Unknown')}"
                if item.get('item_type'):
                    item_desc += f" ({item['item_type']})"
                if item.get('description'):
                    item_desc += f" - {item['description']}"
                print(item_desc)
        
        # 所持アイテム（インベントリ）
        inventory = character_info.get("inventory", [])
        inventory_count = character_info.get("inventory_count", 0)
        
        print(f"\n--- 所持アイテム (総数: {inventory_count}) ---")
        if inventory:
            for i, item in enumerate(inventory):
                item_desc = f"  {i+1}. {item.get('item_name', 'Unknown')}"
                
                # アイテムタイプ
                if item.get('item_type'):
                    item_desc += f" ({item['item_type']})"
                
                # 数量
                quantity = item.get('quantity', 1)
                if quantity > 1:
                    item_desc += f" x{quantity}"
                
                # 装備可能性
                if item.get('equipable'):
                    item_desc += " [装備可能]"
                
                # 価値
                if item.get('value'):
                    item_desc += f" (価値: {item['value']}G)"
                
                print(item_desc)
                
                # 説明がある場合は改行して表示
                if item.get('description'):
                    print(f"     説明: {item['description']}")
                
                # ステータス修正値がある場合
                if item.get('stats_modifier'):
                    stats_mod = item['stats_modifier']
                    if isinstance(stats_mod, dict) and any(v != 0 for v in stats_mod.values()):
                        mod_str = ", ".join([f"{k}:{v:+d}" for k, v in stats_mod.items() if v != 0])
                        print(f"     効果: {mod_str}")
        elif inventory_count == 0:
            print("  アイテムを所持していません")
        else:
            print(f"  アイテム情報を取得できませんでした（総数: {inventory_count}）")
    
    def display_adventure_guild_list(self, guild_info: Optional[Dict[str, Any]] = None) -> None:
        """
        冒険者ギルド一覧を見やすく表示
        
        Args:
            guild_info: ギルド情報（Noneの場合は自動取得）
        """
        if guild_info is None:
            guild_info = self.get_adventure_guild_list()
        
        if not guild_info:
            print("❌ 冒険者ギルド情報を取得できませんでした")
            return
        
        print("=== Adventure Guild Character List ===")
        character_count = guild_info.get("guild_characters_count", 0)
        print(f"登録キャラクター数: {character_count}")
        
        characters = guild_info.get("guild_characters", [])
        if characters:
            print("\n--- 登録キャラクター一覧 ---")
            for i, char in enumerate(characters):
                print(f"  {i}: {char.get('name', 'Unknown')} ({char.get('race', 'Unknown')}/{char.get('character_class', 'Unknown')}) - Lv.{char.get('level', 1)} - {char.get('hp', 0)}/{char.get('max_hp', 0)} HP - {char.get('status', 'unknown')}")
        else:
            print("登録されたキャラクターがいません")


def main():
    """コマンドライン実行"""
    parser = argparse.ArgumentParser(description="Game Debug API Client")
    parser.add_argument("command", choices=["screenshot", "key", "mouse", "escape", "enter", "space", "analyze", "buttons", "click", "party", "party_character", "adventure_list", "debug_gm", "facility_ui", "ui_snapshot", "server_status", "add_log"],
                      help="実行するコマンド")
    parser.add_argument("--save", "-s", help="スクリーンショット保存先")
    parser.add_argument("--code", "-c", type=int, help="キーコード")
    parser.add_argument("--x", type=int, help="マウスX座標")
    parser.add_argument("--y", type=int, help="マウスY座標")
    parser.add_argument("--action", default="click", help="マウスアクション")
    parser.add_argument("--wait", "-w", type=float, default=0, help="実行前の待機時間")
    parser.add_argument("--number", "-n", type=int, help="ボタン番号（1-9）")
    parser.add_argument("--text", "-t", help="ボタンテキスト")
    parser.add_argument("--level", default="INFO", help="ログレベル（add_logコマンド用）")
    parser.add_argument("--message", "-m", help="ログメッセージ（add_logコマンド用）")
    parser.add_argument("character_index", nargs="?", type=int, help="キャラクターインデックス（party_characterコマンド用）")
    
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
    
    elif args.command == "party":
        client.display_party_info()
    
    elif args.command == "party_character":
        if args.character_index is None:
            logger.error("character_index is required for party_character command")
            sys.exit(1)
        client.display_character_details(args.character_index)
    
    elif args.command == "adventure_list":
        client.display_adventure_guild_list()
    
    elif args.command == "debug_gm":
        debug_info = client.get_game_manager_debug_info()
        if debug_info:
            print("=== GameManager デバッグ情報 ===")
            print(f"タイムスタンプ: {debug_info.get('timestamp', 'Unknown')}")
            print(f"GameManager存在: {debug_info.get('game_manager_exists', False)}")
            print(f"GameManagerタイプ: {debug_info.get('game_manager_type', 'Unknown')}")
            print(f"現在のパーティ存在: {debug_info.get('current_party_exists', False)}")
            
            retrieval_debug = debug_info.get('retrieval_debug', {})
            if retrieval_debug:
                print("\n--- 取得方法デバッグ情報 ---")
                print(f"キャッシュManager存在: {retrieval_debug.get('cached_manager_exists', False)}")
                print(f"mainモジュール存在: {retrieval_debug.get('main_module_exists', False)}")
                print(f"main.game_manager存在: {retrieval_debug.get('main_manager_exists', False)}")
                print(f"sys.modules['main']存在: {retrieval_debug.get('sys_modules_main_exists', False)}")
            
            party_details = debug_info.get('party_details', {})
            if party_details:
                print(f"\n--- パーティ詳細 ---")
                print(f"パーティ名: {party_details.get('name', 'Unknown')}")
                print(f"パーティID: {party_details.get('party_id', 'Unknown')}")
                print(f"パーティタイプ: {party_details.get('party_type', 'Unknown')}")
                print(f"membersプロパティ有: {party_details.get('has_members', False)}")
                print(f"get_all_charactersメソッド有: {party_details.get('has_get_all_characters', False)}")
                print(f"メンバー数: {party_details.get('members_count', 0)}")
                
                # エラー情報があれば表示
                if 'members_error' in party_details:
                    print(f"⚠️ メンバーアクセスエラー: {party_details['members_error']}")
                if 'members_access_error' in party_details:
                    print(f"⚠️ メンバーアクセス問題: {party_details['members_access_error']}")
                if 'characters_from_method' in party_details:
                    print(f"get_all_characters()結果: {party_details['characters_from_method']}人")
                if 'characters_method_error' in party_details:
                    print(f"⚠️ get_all_characters()エラー: {party_details['characters_method_error']}")
        else:
            print("GameManagerデバッグ情報の取得に失敗しました")
    
    elif args.command == "facility_ui":
        facility_info = client.get_facility_ui_debug_info()
        if facility_info:
            print("=== 施設UI デバッグ情報 ===")
            print(json.dumps(facility_info, indent=2, ensure_ascii=False))
        else:
            print("施設UIデバッグ情報の取得に失敗しました")
    
    elif args.command == "ui_snapshot":
        snapshot_info = client.create_ui_snapshot()
        if snapshot_info:
            print("=== UI スナップショット ===")
            print(json.dumps(snapshot_info, indent=2, ensure_ascii=False))
        else:
            print("UIスナップショットの作成に失敗しました")
    
    elif args.command == "server_status":
        status_info = client.get_server_status()
        if status_info:
            print("=== サーバ状態 ===")
            print(json.dumps(status_info, indent=2, ensure_ascii=False))
        else:
            print("サーバ状態の取得に失敗しました")
    
    elif args.command == "add_log":
        if args.message is None:
            logger.error("--message is required for add_log command")
            sys.exit(1)
        
        success = client.add_debug_log(args.level, args.message)
        if success:
            print(f"✅ ログエントリを追加しました: [{args.level}] {args.message}")
        else:
            print("❌ ログエントリの追加に失敗しました")
            sys.exit(1)


if __name__ == "__main__":
    main()