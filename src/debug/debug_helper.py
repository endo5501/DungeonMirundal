"""
デバッグヘルパーツール

よく使うデバッグシナリオを高レベルな関数として提供。
複雑なデバッグ作業を簡潔に実行できるようにする。
"""

import time
import subprocess
import os
import signal
import atexit
from typing import Optional, List, Tuple, Dict, Any
from pathlib import Path
from contextlib import contextmanager

from .game_debug_client import GameDebugClient
from src.utils.logger import logger


class DebugSession:
    """デバッグセッション管理"""
    
    def __init__(self, auto_start: bool = True, headless: bool = False):
        """
        デバッグセッションを初期化
        
        Args:
            auto_start: 自動的にゲームを起動するか
            headless: ヘッドレスモードで起動するか
        """
        self.client = GameDebugClient()
        self.game_process = None
        self.auto_start = auto_start
        self.headless = headless
        self.pid_file = Path("game_debug.pid")
        self.log_file = Path("game_debug.log")
        
        # 終了時のクリーンアップを登録
        atexit.register(self.cleanup)
    
    def start_game(self) -> bool:
        """ゲームを起動"""
        # 既存のプロセスチェック
        if self.pid_file.exists():
            try:
                pid = int(self.pid_file.read_text())
                os.kill(pid, 0)  # プロセスが存在するかチェック
                logger.info(f"Game already running with PID: {pid}")
                return True
            except (ProcessLookupError, ValueError):
                self.pid_file.unlink()
        
        # ゲーム起動
        logger.info("Starting game process...")
        cmd = ["uv", "run", "python", "main.py"]
        if self.headless:
            cmd.extend(["--headless"])
        
        with open(self.log_file, "w") as log:
            self.game_process = subprocess.Popen(
                cmd,
                stdout=log,
                stderr=subprocess.STDOUT,
                preexec_fn=os.setsid
            )
        
        # PIDを保存
        self.pid_file.write_text(str(self.game_process.pid))
        
        # API起動を待機
        if self.client.wait_for_api(max_wait=10.0):
            logger.info(f"Game started successfully (PID: {self.game_process.pid})")
            return True
        else:
            logger.error("Failed to start game API")
            self.stop_game()
            return False
    
    def stop_game(self) -> None:
        """ゲームを停止"""
        if self.game_process:
            try:
                os.killpg(os.getpgid(self.game_process.pid), signal.SIGTERM)
                self.game_process.wait(timeout=5)
            except:
                pass
            self.game_process = None
        
        if self.pid_file.exists():
            try:
                pid = int(self.pid_file.read_text())
                os.kill(pid, signal.SIGTERM)
                time.sleep(0.5)
            except:
                pass
            self.pid_file.unlink()
    
    def cleanup(self) -> None:
        """クリーンアップ処理"""
        if self.auto_start:
            self.stop_game()
    
    def __enter__(self):
        """コンテキストマネージャー開始"""
        if self.auto_start:
            if not self.start_game():
                raise RuntimeError("Failed to start game for debug session")
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """コンテキストマネージャー終了"""
        self.cleanup()


class DebugHelper:
    """高レベルデバッグ機能"""
    
    def __init__(self, client: Optional[GameDebugClient] = None):
        """
        デバッグヘルパーを初期化
        
        Args:
            client: 使用するクライアント（Noneの場合は新規作成）
        """
        self.client = client or GameDebugClient()
    
    def verify_esc_transition(self, save_screenshots: bool = False) -> Dict[str, Any]:
        """
        ESCキーによる画面遷移を検証
        
        Returns:
            検証結果の辞書
        """
        results = {
            "initial_state": None,
            "after_first_esc": None,
            "after_second_esc": None,
            "transitions_correct": False,
            "error": None
        }
        
        try:
            # 初期状態
            if save_screenshots:
                self.client.screenshot("debug_initial.jpg")
            else:
                self.client.screenshot()
            results["initial_state"] = {
                "color": self.client.analyze_background_color(),
                "is_overworld": self.client.is_overworld_background(),
                "is_settings": self.client.is_settings_background()
            }
            
            # 1回目のESC
            self.client.press_escape()
            self.client.wait_for_transition()
            
            if save_screenshots:
                self.client.screenshot("debug_after_esc1.jpg")
            else:
                self.client.screenshot()
            results["after_first_esc"] = {
                "color": self.client.analyze_background_color(),
                "is_overworld": self.client.is_overworld_background(),
                "is_settings": self.client.is_settings_background()
            }
            
            # 2回目のESC
            self.client.press_escape()
            self.client.wait_for_transition()
            
            if save_screenshots:
                self.client.screenshot("debug_after_esc2.jpg")
            else:
                self.client.screenshot()
            results["after_second_esc"] = {
                "color": self.client.analyze_background_color(),
                "is_overworld": self.client.is_overworld_background(),
                "is_settings": self.client.is_settings_background()
            }
            
            # 遷移が正しいかチェック
            results["transitions_correct"] = (
                results["initial_state"]["is_overworld"] and
                results["after_first_esc"]["is_settings"] and
                results["after_second_esc"]["is_overworld"]
            )
            
        except Exception as e:
            results["error"] = str(e)
        
        return results
    
    def capture_transition_sequence(self, 
                                   actions: List[Tuple[str, Any]], 
                                   output_dir: str = "debug_captures") -> List[str]:
        """
        一連のアクションと画面キャプチャを実行
        
        Args:
            actions: (アクション名, パラメータ)のリスト
            output_dir: キャプチャ保存先ディレクトリ
            
        Returns:
            保存したファイルパスのリスト
        """
        Path(output_dir).mkdir(exist_ok=True)
        captured_files = []
        
        # 初期状態をキャプチャ
        initial_path = f"{output_dir}/00_initial.jpg"
        self.client.screenshot(initial_path)
        captured_files.append(initial_path)
        
        # アクションを実行
        for i, (action, params) in enumerate(actions, 1):
            if action == "key":
                self.client.send_key(params)
            elif action == "mouse":
                self.client.send_mouse(**params)
            elif action == "escape":
                self.client.press_escape()
            elif action == "enter":
                self.client.press_enter()
            elif action == "space":
                self.client.press_space()
            elif action == "wait":
                time.sleep(params)
            
            # 遷移待機
            self.client.wait_for_transition()
            
            # キャプチャ
            capture_path = f"{output_dir}/{i:02d}_after_{action}.jpg"
            self.client.screenshot(capture_path)
            captured_files.append(capture_path)
        
        return captured_files
    
    def compare_screenshots(self, path1: str, path2: str) -> Dict[str, Any]:
        """
        2つのスクリーンショットを比較
        
        Returns:
            比較結果の辞書
        """
        from PIL import Image, ImageChops, ImageStat
        
        img1 = Image.open(path1)
        img2 = Image.open(path2)
        
        # サイズチェック
        if img1.size != img2.size:
            return {
                "identical": False,
                "size_mismatch": True,
                "size1": img1.size,
                "size2": img2.size
            }
        
        # 差分計算
        diff = ImageChops.difference(img1, img2)
        stat = ImageStat.Stat(diff)
        
        # 平均差分
        mean_diff = sum(stat.mean) / len(stat.mean)
        
        return {
            "identical": mean_diff < 1.0,
            "mean_difference": mean_diff,
            "max_difference": max(stat.extrema[i][1] for i in range(len(stat.extrema))),
            "color1": self.client.analyze_background_color(img1),
            "color2": self.client.analyze_background_color(img2)
        }


# 便利な関数
@contextmanager
def debug_game_session():
    """ゲームデバッグセッションのコンテキストマネージャー"""
    with DebugSession() as session:
        yield session.client


def quick_debug_esc_issue():
    """ESC問題を素早くデバッグ"""
    with debug_game_session() as client:
        helper = DebugHelper(client)
        results = helper.verify_esc_transition(save_screenshots=True)
        
        print("\n=== ESC Transition Debug Results ===")
        print(f"Initial state: {results['initial_state']}")
        print(f"After 1st ESC: {results['after_first_esc']}")
        print(f"After 2nd ESC: {results['after_second_esc']}")
        print(f"Transitions correct: {results['transitions_correct']}")
        
        if results['error']:
            print(f"Error: {results['error']}")
        
        return results


if __name__ == "__main__":
    # 簡単なテスト実行
    quick_debug_esc_issue()