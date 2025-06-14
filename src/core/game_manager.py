"""ゲーム管理システム"""

from direct.showbase.ShowBase import ShowBase
from direct.gui.OnscreenText import OnscreenText
from panda3d.core import TextNode, PandaSystem
from src.core.config_manager import config_manager
from src.core.input_manager import InputManager
from src.utils.logger import logger
from src.utils.constants import *


class GameManager(ShowBase):
    """メインゲーム管理クラス"""
    
    def __init__(self):
        # Panda3D基盤の初期化
        super().__init__()
        
        # ゲーム状態
        self.game_state = "startup"
        self.paused = False
        
        # マネージャーの初期化
        self.config = config_manager
        self.input_manager = InputManager()
        
        # 初期設定の読み込み
        self._load_initial_config()
        
        # ウィンドウ設定
        self._setup_window()
        
        # 入力システムの設定
        self._setup_input()
        
        # デバッグ情報の表示
        self._setup_debug_info()
        
        logger.info("GameManagerが初期化されました")
        
    def _load_initial_config(self):
        """初期設定の読み込み"""
        # ゲーム設定の読み込み
        self.game_config = self.config.load_config("game_config")
        
        # 言語設定
        language = self.game_config.get("gameplay", {}).get("language", "ja")
        self.config.set_language(language)
        
        logger.info(f"初期設定を読み込みました: 言語={language}")
        
    def _setup_window(self):
        """ウィンドウの設定"""
        window_config = self.game_config.get("window", {})
        
        # ウィンドウタイトル
        title = window_config.get("title", GAME_TITLE)
        self.win.requestProperties(self.win.getProperties())
        
        # ウィンドウサイズ（設定は起動後のリサイズで適用）
        width = window_config.get("width", WINDOW_WIDTH)
        height = window_config.get("height", WINDOW_HEIGHT)
        
        # FPS制限
        fps = self.game_config.get("graphics", {}).get("fps", FPS)
        globalClock.setMode(globalClock.MLimited)
        globalClock.setFrameRate(fps)
        
        logger.info(f"ウィンドウを設定しました: {width}x{height}, FPS: {fps}")
    
    def _setup_input(self):
        """入力システムの設定"""
        # 基本的な入力ハンドラー
        self.input_manager.bind_action("menu", self._on_menu_key)
        self.input_manager.bind_action("confirm", self._on_confirm_key)
        self.input_manager.bind_action("debug_toggle", self._on_debug_toggle)
        
        # コントローラーのセットアップ
        self.input_manager.setup_controllers()
        
        logger.info("入力システムを設定しました")
    
    def _setup_debug_info(self):
        """デバッグ情報の設定"""
        self.debug_enabled = self.game_config.get("debug", {}).get("enabled", False)
        
        if self.debug_enabled:
            self.debug_text = OnscreenText(
                text="Debug Mode",
                pos=(-0.95, 0.9),
                scale=0.05,
                fg=(1, 1, 0, 1),
                align=TextNode.ALeft
            )
            
            # FPS表示
            if self.game_config.get("debug", {}).get("show_fps", False):
                self.setFrameRateMeter(True)
                
        logger.info(f"デバッグ設定: {'有効' if self.debug_enabled else '無効'}")
    
    def _on_menu_key(self, action: str, pressed: bool):
        """メニューキーの処理"""
        if pressed:
            logger.info("メニューキーが押されました")
            self.toggle_pause()
    
    def _on_confirm_key(self, action: str, pressed: bool):
        """確認キーの処理"""
        if pressed:
            logger.info("確認キーが押されました")
    
    def _on_debug_toggle(self, action: str, pressed: bool):
        """デバッグ切り替えの処理"""
        if pressed:
            self.debug_enabled = not self.debug_enabled
            logger.info(f"デバッグモード切り替え: {'有効' if self.debug_enabled else '無効'}")
    
    def toggle_pause(self):
        """ポーズの切り替え"""
        self.paused = not self.paused
        if self.paused:
            logger.info("ゲームを一時停止しました")
        else:
            logger.info("ゲームを再開しました")
    
    def set_game_state(self, state: str):
        """ゲーム状態の設定"""
        old_state = self.game_state
        self.game_state = state
        logger.info(f"ゲーム状態変更: {old_state} -> {state}")
    
    def get_text(self, key: str) -> str:
        """テキストの取得"""
        return self.config.get_text(key)
    
    def cleanup(self):
        """リソースのクリーンアップ"""
        logger.info("GameManagerをクリーンアップしています")
        
        if hasattr(self, 'input_manager'):
            self.input_manager.cleanup()
            
        self.destroy()
        
    def run_game(self):
        """ゲームの実行"""
        logger.info("ゲームを開始します")
        
        # スタートアップメッセージ
        startup_text = OnscreenText(
            text=self.get_text("system.startup"),
            pos=(0, 0),
            scale=0.1,
            fg=(1, 1, 1, 1),
            align=TextNode.ACenter
        )
        
        # メインループの開始
        self.set_game_state("main_menu")
        self.run()


def create_game() -> GameManager:
    """ゲームインスタンスの作成"""
    logger.info("新しいゲームインスタンスを作成します")
    return GameManager()