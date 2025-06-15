"""ゲーム管理システム"""

from direct.showbase.ShowBase import ShowBase
from direct.gui.OnscreenText import OnscreenText
from panda3d.core import TextNode, PandaSystem
from src.core.config_manager import config_manager
from src.core.input_manager import InputManager
from src.overworld.overworld_manager import OverworldManager
from src.dungeon.dungeon_manager import DungeonManager
from src.character.party import Party
from src.rendering.dungeon_renderer import DungeonRenderer
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
        self.current_location = "overworld"  # "overworld" or "dungeon"
        
        # マネージャーの初期化
        self.config = config_manager
        self.input_manager = InputManager()
        self.overworld_manager = None
        self.dungeon_manager = None
        self.dungeon_renderer = None
        
        # 現在のパーティ
        self.current_party = None
        
        # 初期設定の読み込み
        self._load_initial_config()
        
        # ウィンドウ設定
        self._setup_window()
        
        # 入力システムの設定
        self._setup_input()
        
        # 入力設定の読み込み（入力システム初期化後）
        self._load_input_settings()
        
        # デバッグ情報の表示
        self._setup_debug_info()
        
        # 遷移システムの初期化
        self._setup_transition_system()
        
        logger.info("GameManagerが初期化されました")
        
    def _load_initial_config(self):
        """初期設定の読み込み"""
        # ゲーム設定の読み込み
        self.game_config = self.config.load_config("game_config")
        
        # 言語設定
        language = self.game_config.get("gameplay", {}).get("language", "ja")
        self.config.set_language(language)
        
        logger.info(f"初期設定を読み込みました: 言語={language}")
    
    def _load_input_settings(self):
        """入力設定の読み込み"""
        try:
            input_settings = self.config.load_config("input_settings")
            if input_settings and hasattr(self, 'input_manager'):
                self.input_manager.load_bindings(input_settings)
                logger.info("入力設定を読み込みました")
        except Exception as e:
            logger.warning(f"入力設定の読み込みに失敗（デフォルト設定を使用）: {e}")
        
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
        from src.core.input_manager import InputAction
        
        # アクションハンドラーのバインド
        self.input_manager.bind_action(InputAction.MENU.value, self._on_menu_action)
        self.input_manager.bind_action(InputAction.CONFIRM.value, self._on_confirm_action)
        self.input_manager.bind_action(InputAction.CANCEL.value, self._on_cancel_action)
        self.input_manager.bind_action(InputAction.ACTION.value, self._on_action_action)
        self.input_manager.bind_action(InputAction.DEBUG_TOGGLE.value, self._on_debug_toggle)
        self.input_manager.bind_action(InputAction.PAUSE.value, self._on_pause_action)
        
        # ゲーム機能のバインド
        self.input_manager.bind_action(InputAction.INVENTORY.value, self._on_inventory_action)
        self.input_manager.bind_action(InputAction.MAGIC.value, self._on_magic_action)
        self.input_manager.bind_action(InputAction.EQUIPMENT.value, self._on_equipment_action)
        self.input_manager.bind_action(InputAction.STATUS.value, self._on_status_action)
        self.input_manager.bind_action(InputAction.CAMP.value, self._on_camp_action)
        
        # 移動アクションのバインド（ダンジョンレンダラーが処理）
        self.input_manager.bind_action(InputAction.MOVE_FORWARD.value, self._on_movement_action)
        self.input_manager.bind_action(InputAction.MOVE_BACKWARD.value, self._on_movement_action)
        self.input_manager.bind_action(InputAction.MOVE_LEFT.value, self._on_movement_action)
        self.input_manager.bind_action(InputAction.MOVE_RIGHT.value, self._on_movement_action)
        self.input_manager.bind_action(InputAction.TURN_LEFT.value, self._on_movement_action)
        self.input_manager.bind_action(InputAction.TURN_RIGHT.value, self._on_movement_action)
        
        # コントローラーのセットアップ
        self.input_manager.setup_controllers()
        
        logger.info("拡張入力システムを設定しました")
    
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
    
    def _on_menu_action(self, action: str, pressed: bool, input_type):
        """メニューアクションの処理"""
        if pressed:
            logger.info(f"メニューアクション ({input_type.value})")
            
            # ダンジョン内ではメニュー表示
            if self.current_location == "dungeon" and self.dungeon_renderer:
                self.dungeon_renderer._show_menu()
            else:
                self.toggle_pause()
    
    def _on_confirm_action(self, action: str, pressed: bool, input_type):
        """確認アクションの処理"""
        if pressed:
            logger.info(f"確認アクション ({input_type.value})")
    
    def _on_cancel_action(self, action: str, pressed: bool, input_type):
        """キャンセルアクションの処理"""
        if pressed:
            logger.info(f"キャンセルアクション ({input_type.value})")
    
    def _on_action_action(self, action: str, pressed: bool, input_type):
        """アクションボタンの処理"""
        if pressed:
            logger.info(f"アクションボタン ({input_type.value})")
    
    def _on_debug_toggle(self, action: str, pressed: bool, input_type):
        """デバッグ切り替えの処理"""
        if pressed:
            self.debug_enabled = not self.debug_enabled
            logger.info(f"デバッグモード切り替え: {'有効' if self.debug_enabled else '無効'}")
    
    def _on_pause_action(self, action: str, pressed: bool, input_type):
        """ポーズアクションの処理"""
        if pressed:
            logger.info(f"ポーズアクション ({input_type.value})")
            self.toggle_pause()
    
    def _on_inventory_action(self, action: str, pressed: bool, input_type):
        """インベントリアクションの処理"""
        if pressed:
            logger.info(f"インベントリアクション ({input_type.value})")
            if self.current_location == "dungeon" and self.dungeon_renderer:
                if hasattr(self.dungeon_renderer, 'ui_manager') and self.dungeon_renderer.ui_manager:
                    self.dungeon_renderer.ui_manager._open_inventory()
    
    def _on_magic_action(self, action: str, pressed: bool, input_type):
        """魔法アクションの処理"""
        if pressed:
            logger.info(f"魔法アクション ({input_type.value})")
            if self.current_location == "dungeon" and self.dungeon_renderer:
                if hasattr(self.dungeon_renderer, 'ui_manager') and self.dungeon_renderer.ui_manager:
                    self.dungeon_renderer.ui_manager._open_magic()
    
    def _on_equipment_action(self, action: str, pressed: bool, input_type):
        """装備アクションの処理"""
        if pressed:
            logger.info(f"装備アクション ({input_type.value})")
            if self.current_location == "dungeon" and self.dungeon_renderer:
                if hasattr(self.dungeon_renderer, 'ui_manager') and self.dungeon_renderer.ui_manager:
                    self.dungeon_renderer.ui_manager._open_equipment()
    
    def _on_status_action(self, action: str, pressed: bool, input_type):
        """ステータスアクションの処理"""
        if pressed:
            logger.info(f"ステータスアクション ({input_type.value})")
            if self.current_location == "dungeon" and self.dungeon_renderer:
                if hasattr(self.dungeon_renderer, 'ui_manager') and self.dungeon_renderer.ui_manager:
                    self.dungeon_renderer.ui_manager._open_status()
    
    def _on_camp_action(self, action: str, pressed: bool, input_type):
        """キャンプアクションの処理"""
        if pressed:
            logger.info(f"キャンプアクション ({input_type.value})")
            if self.current_location == "dungeon" and self.dungeon_renderer:
                if hasattr(self.dungeon_renderer, 'ui_manager') and self.dungeon_renderer.ui_manager:
                    self.dungeon_renderer.ui_manager._open_camp()
    
    def _on_movement_action(self, action: str, pressed: bool, input_type):
        """移動アクションの処理"""
        if pressed and self.current_location == "dungeon" and self.dungeon_renderer:
            # ダンジョンレンダラーに移動処理を委譲
            from src.core.input_manager import InputAction
            
            if action == InputAction.MOVE_FORWARD.value:
                self.dungeon_renderer._move_forward()
            elif action == InputAction.MOVE_BACKWARD.value:
                self.dungeon_renderer._move_backward()
            elif action == InputAction.MOVE_LEFT.value:
                self.dungeon_renderer._move_left()
            elif action == InputAction.MOVE_RIGHT.value:
                self.dungeon_renderer._move_right()
            elif action == InputAction.TURN_LEFT.value:
                self.dungeon_renderer._turn_left()
            elif action == InputAction.TURN_RIGHT.value:
                self.dungeon_renderer._turn_right()
    
    def toggle_pause(self):
        """ポーズの切り替え"""
        self.paused = not self.paused
        if self.paused:
            logger.info("ゲームを一時停止しました")
        else:
            logger.info("ゲームを再開しました")
    
    def _setup_transition_system(self):
        """遷移システムの初期化"""
        # 地上部マネージャーの初期化
        self.overworld_manager = OverworldManager()
        self.overworld_manager.set_enter_dungeon_callback(self.transition_to_dungeon)
        
        # ダンジョンマネージャーの初期化
        self.dungeon_manager = DungeonManager()
        self.dungeon_manager.set_return_to_overworld_callback(self.transition_to_overworld)
        
        # ダンジョンレンダラーの初期化
        try:
            self.dungeon_renderer = DungeonRenderer()
            if self.dungeon_renderer.enabled:
                self.dungeon_renderer.set_dungeon_manager(self.dungeon_manager)
                self.dungeon_renderer.set_game_manager(self)
                logger.info("ダンジョンレンダラーを初期化しました")
            else:
                logger.warning("ダンジョンレンダラーが無効化されています")
        except Exception as e:
            logger.error(f"ダンジョンレンダラー初期化エラー: {e}")
            self.dungeon_renderer = None
        
        logger.info("遷移システムを初期化しました")
    
    def set_game_state(self, state: str):
        """ゲーム状態の設定"""
        old_state = self.game_state
        self.game_state = state
        logger.info(f"ゲーム状態変更: {old_state} -> {state}")
    
    def set_current_party(self, party: Party):
        """現在のパーティを設定"""
        self.current_party = party
        
        # ダンジョンレンダラーにもパーティを設定
        if self.dungeon_renderer and self.dungeon_renderer.enabled:
            self.dungeon_renderer.set_party(party)
        
        logger.info(f"パーティを設定: {party.name} ({len(party.get_living_characters())}人)")
    
    def get_current_party(self) -> Party:
        """現在のパーティを取得"""
        return self.current_party
    
    def transition_to_dungeon(self):
        """ダンジョンへの遷移"""
        if not self.current_party:
            logger.error("パーティが設定されていません")
            return False
        
        if not self.current_party.get_living_characters():
            logger.error("生存しているパーティメンバーがいません")
            return False
        
        logger.info("ダンジョンへ遷移開始")
        
        # 地上部を退場
        self.overworld_manager.exit_overworld()
        
        # ダンジョンに入場
        success = self.dungeon_manager.enter_dungeon("main_dungeon", self.current_party)
        
        if success:
            self.current_location = "dungeon"
            self.set_game_state("dungeon_exploration")
            
            # ダンジョンが存在しない場合は作成
            if "main_dungeon" not in self.dungeon_manager.active_dungeons:
                self.dungeon_manager.create_dungeon("main_dungeon", "default_seed")
            
            # ダンジョンレンダラーで描画開始
            if self.dungeon_renderer and self.dungeon_renderer.enabled:
                current_dungeon = self.dungeon_manager.current_dungeon
                if current_dungeon:
                    self.dungeon_renderer.render_dungeon(current_dungeon)
                    self.dungeon_renderer.update_ui()
            
            logger.info("ダンジョンへの遷移が完了しました")
            return True
        else:
            logger.error("ダンジョンへの遷移に失敗しました")
            # 地上部に戻る
            self.overworld_manager.enter_overworld(self.current_party)
            return False
    
    def transition_to_overworld(self):
        """地上部への遷移"""
        if not self.current_party:
            logger.error("パーティが設定されていません")
            return False
        
        logger.info("地上部へ遷移開始")
        
        # ダンジョンを退場
        self.dungeon_manager.exit_dungeon()
        
        # 地上部に入場（自動回復付き）
        success = self.overworld_manager.enter_overworld(self.current_party)
        
        if success:
            self.current_location = "overworld"
            self.set_game_state("overworld_exploration")
            logger.info("地上部への遷移が完了しました（自動回復済み）")
            return True
        else:
            logger.error("地上部への遷移に失敗しました")
            return False
    
    def save_game_state(self, slot_id: str) -> bool:
        """ゲーム状態の保存"""
        try:
            # 現在の場所に応じてセーブ
            if self.current_location == "overworld":
                success = self.overworld_manager.save_overworld_state(slot_id)
            elif self.current_location == "dungeon":
                success = self.dungeon_manager.save_dungeon(slot_id)
            else:
                logger.error(f"未知の場所: {self.current_location}")
                return False
            
            if success:
                # 統合状態情報も保存
                state_data = {
                    'current_location': self.current_location,
                    'game_state': self.game_state,
                    'party_id': self.current_party.party_id if self.current_party else None
                }
                
                from src.core.save_manager import save_manager
                save_manager.save_additional_data(slot_id, 'game_state', state_data)
                
                logger.info(f"ゲーム状態を保存しました（場所: {self.current_location}）")
                return True
            else:
                return False
                
        except Exception as e:
            logger.error(f"ゲーム状態保存エラー: {e}")
            return False
    
    def load_game_state(self, slot_id: str) -> bool:
        """ゲーム状態の読み込み"""
        try:
            from src.core.save_manager import save_manager
            
            # 統合状態情報を読み込み
            state_data = save_manager.load_additional_data(slot_id, 'game_state')
            if not state_data:
                logger.error("ゲーム状態データが見つかりません")
                return False
            
            location = state_data.get('current_location', 'overworld')
            game_state = state_data.get('game_state', 'overworld_exploration')
            party_id = state_data.get('party_id')
            
            # パーティを読み込み
            if party_id:
                party_data = save_manager.load_additional_data(slot_id, 'party')
                if party_data:
                    from src.character.party import Party
                    self.current_party = Party.from_dict(party_data)
            
            # 場所に応じて読み込み
            if location == "overworld":
                success = self.overworld_manager.load_overworld_state(slot_id)
                if success and self.current_party:
                    self.overworld_manager.enter_overworld(self.current_party)
            elif location == "dungeon":
                success = self.dungeon_manager.load_dungeon(slot_id)
                if success and self.current_party:
                    # ダンジョン状態を復元
                    pass
            else:
                logger.error(f"未知の場所: {location}")
                return False
            
            if success:
                self.current_location = location
                self.set_game_state(game_state)
                logger.info(f"ゲーム状態を読み込みました（場所: {location}）")
                return True
            else:
                return False
                
        except Exception as e:
            logger.error(f"ゲーム状態読み込みエラー: {e}")
            return False
    
    def get_text(self, key: str) -> str:
        """テキストの取得"""
        return self.config.get_text(key)
    
    def save_input_settings(self):
        """入力設定を保存"""
        try:
            if hasattr(self, 'input_manager'):
                bindings_data = self.input_manager.save_bindings()
                self.config.save_config("input_settings", bindings_data)
                logger.info("入力設定を保存しました")
                return True
        except Exception as e:
            logger.error(f"入力設定保存エラー: {e}")
        return False
    
    def get_input_manager(self):
        """入力マネージャーを取得"""
        return self.input_manager if hasattr(self, 'input_manager') else None
    
    def cleanup(self):
        """リソースのクリーンアップ"""
        logger.info("GameManagerをクリーンアップしています")
        
        # 入力設定を自動保存
        self.save_input_settings()
        
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