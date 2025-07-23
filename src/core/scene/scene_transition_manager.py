"""Scene transition management module."""

import logging
from typing import Any, Dict, Optional, Callable
from enum import Enum

from src.core.interfaces import ManagedComponent
from src.utils.logger import logger
from src.utils.constants import GameLocation
from src.core.event_bus import publish_event, EventType


class SceneTransition(Enum):
    """シーン遷移の種類"""
    TO_OVERWORLD = "to_overworld"
    TO_DUNGEON = "to_dungeon"
    WITHIN_DUNGEON = "within_dungeon"
    TO_TOWN = "to_town"
    TO_COMBAT = "to_combat"


class SceneTransitionManager(ManagedComponent):
    """シーン遷移の統合管理
    
    GameManagerから抽出されたシーン遷移処理を統合管理し、
    ゲーム状態の切り替えとロケーション管理を行う。
    """
    
    def __init__(self):
        super().__init__()
        
        # 外部依存コンポーネント
        self.game_config = None
        self.current_location = GameLocation.OVERWORLD
        self.game_state = "main_menu"
        self.current_party = None
        
        # 管理対象コンポーネント
        self.overworld_manager = None
        self.dungeon_manager = None
        self.dungeon_renderer = None
        self.encounter_manager = None
        self.game_manager_ref = None  # GameManagerへの参照
        
        # 遷移履歴とコールバック
        self._transition_history = []
        self._state_change_callbacks = {}
        self._location_change_callbacks = {}
        
        # ダンジョン生成設定
        self._dungeon_configs = {}
    
    def _do_initialize(self, context: Dict[str, Any]) -> bool:
        """SceneTransitionManagerの初期化"""
        try:
            # 必要なコンポーネントを取得
            self.game_config = context.get('game_config')
            self.current_location = context.get('current_location', GameLocation.OVERWORLD)
            self.game_state = context.get('game_state', 'main_menu')
            self.current_party = context.get('current_party')
            
            # 管理対象コンポーネントを取得
            self.overworld_manager = context.get('overworld_manager')
            self.dungeon_manager = context.get('dungeon_manager')
            self.dungeon_renderer = context.get('dungeon_renderer')
            self.encounter_manager = context.get('encounter_manager')
            self.game_manager_ref = context.get('game_manager_ref')  # GameManagerへの参照
            
            # ダンジョン設定を読み込み
            self._load_dungeon_configs()
            
            if not self.game_config:
                logger.error("SceneTransitionManager: game_config not provided")
                return False
            
            logger.info("SceneTransitionManager initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"SceneTransitionManager initialization failed: {e}")
            return False
    
    def _do_cleanup(self) -> None:
        """SceneTransitionManagerのクリーンアップ"""
        self._transition_history.clear()
        self._state_change_callbacks.clear()
        self._location_change_callbacks.clear()
        logger.info("SceneTransitionManager cleaned up")
    
    def handle_game_event(self, event: Any) -> bool:
        """ゲームイベントの処理（現在は使用しない）"""
        return False
    
    def register_state_change_callback(self, state: str, callback: Callable) -> None:
        """状態変更コールバックの登録"""
        if state not in self._state_change_callbacks:
            self._state_change_callbacks[state] = []
        if callback not in self._state_change_callbacks[state]:
            self._state_change_callbacks[state].append(callback)
    
    def register_location_change_callback(self, location: GameLocation, callback: Callable) -> None:
        """ロケーション変更コールバックの登録"""
        if location not in self._location_change_callbacks:
            self._location_change_callbacks[location] = []
        if callback not in self._location_change_callbacks[location]:
            self._location_change_callbacks[location].append(callback)
    
    def set_game_state(self, state: str) -> None:
        """ゲーム状態の設定（GameManagerから抽出）"""
        old_state = self.game_state
        self.game_state = state
        
        # 状態変更をログ出力
        if self.game_config:
            try:
                log_message = self.game_config.get_text("app_log.game_state_changed")
                logger.info(log_message.format(old_state=old_state, new_state=state))
            except Exception:
                logger.info(f"Game state changed: {old_state} -> {state}")
        
        # コールバック実行
        if state in self._state_change_callbacks:
            for callback in self._state_change_callbacks[state]:
                try:
                    callback(old_state, state)
                except Exception as e:
                    logger.error(f"State change callback error for {state}: {e}")
        
        # イベント発行
        publish_event(
            EventType.GAME_STATE_CHANGED,
            "scene_transition_manager",
            {
                "old_state": old_state,
                "new_state": state,
                "timestamp": self._get_timestamp()
            }
        )
    
    def set_current_location(self, location: GameLocation) -> None:
        """現在のロケーション設定"""
        old_location = self.current_location
        self.current_location = location
        
        # ロケーション変更をログ出力（Enumと文字列の両方に対応）
        old_location_str = getattr(old_location, 'value', str(old_location))
        new_location_str = getattr(location, 'value', str(location))
        logger.info(f"Location changed: {old_location_str} -> {new_location_str}")
        
        # コールバック実行
        if location in self._location_change_callbacks:
            for callback in self._location_change_callbacks[location]:
                try:
                    callback(old_location, location)
                except Exception as e:
                    logger.error(f"Location change callback error for {location}: {e}")
        
        # InputHandlerCoordinatorにも位置変更を通知
        if self.game_manager_ref and hasattr(self.game_manager_ref, 'input_handler_coordinator'):
            self.game_manager_ref.input_handler_coordinator.update_location(location)
        
        # GameManagerのcurrent_locationも同期
        if self.game_manager_ref and hasattr(self.game_manager_ref, 'current_location'):
            self.game_manager_ref.current_location = location
        
        # イベント発行（Enumと文字列の両方に対応）
        old_location_value = getattr(old_location, 'value', str(old_location))
        new_location_value = getattr(location, 'value', str(location))
        publish_event(
            EventType.LOCATION_CHANGED,
            "scene_transition_manager",
            {
                "old_location": old_location_value,
                "new_location": new_location_value,
                "timestamp": self._get_timestamp()
            }
        )
    
    def transition_to_dungeon(self, dungeon_id: str = "main_dungeon") -> bool:
        """ダンジョンへの遷移（GameManagerから抽出・改良）"""
        try:
            if not self.current_party:
                if self.game_config:
                    error_msg = self.game_config.get_text("game_manager.party_error_no_party")
                    logger.error(error_msg)
                return False
            
            # 遷移履歴に記録
            self._add_transition_history("to_dungeon", {"dungeon_id": dungeon_id})
            
            # ダンジョンシードを生成
            dungeon_seed = self._generate_dungeon_seed(dungeon_id)
            
            # ダンジョンマネージャーでダンジョンに入場
            if self.dungeon_manager and hasattr(self.dungeon_manager, 'enter_dungeon'):
                # ダンジョンがactive_dungeonsに読み込まれていない場合は読み込み
                if hasattr(self.dungeon_manager, 'load_dungeon') and dungeon_seed not in getattr(self.dungeon_manager, 'active_dungeons', {}):
                    logger.info(f"ダンジョン {dungeon_seed} を active_dungeons に読み込み中...")
                    self.dungeon_manager.load_dungeon(dungeon_seed)
                
                if self.dungeon_manager.enter_dungeon(dungeon_seed, self.current_party):
                    # 地上部マネージャーの終了処理
                    if self.overworld_manager and hasattr(self.overworld_manager, 'exit_overworld'):
                        self.overworld_manager.exit_overworld()
                    
                    # ゲーム状態とロケーションを更新
                    self.set_current_location(GameLocation.DUNGEON)
                    self.set_game_state("dungeon_exploration")
                    
                    # エンカウンターマネージャーにダンジョン状態を設定
                    current_dungeon = self.dungeon_manager.current_dungeon
                    if current_dungeon and self.encounter_manager:
                        self.encounter_manager.set_dungeon(current_dungeon)
                        logger.info("エンカウンターマネージャーにダンジョン状態を設定しました")
                    
                    # ダンジョンUIマネージャーの設定
                    self._setup_dungeon_ui(current_dungeon)
                    
                    # ダンジョンレンダラーの自動復旧
                    self._attempt_dungeon_renderer_recovery(current_dungeon)
                    
                    # SceneManagerでダンジョンシーンに切り替え
                    self._transition_scene_manager_to_dungeon(dungeon_id)
                    
                    if self.game_config:
                        success_msg = self.game_config.get_text("game_manager.dungeon_transition_complete")
                        logger.info(success_msg)
                    
                    return True
                else:
                    if self.game_config:
                        error_msg = self.game_config.get_text("game_manager.dungeon_transition_failed")
                        logger.error(error_msg)
                    return False
            else:
                logger.error("DungeonManager not available or missing enter_dungeon method")
                return False
                
        except Exception as e:
            if self.game_config:
                error_msg = self.game_config.get_text("game_manager.dungeon_transition_error")
                logger.error(error_msg.format(error=e))
            else:
                logger.error(f"Dungeon transition error: {e}")
            return False
    
    def transition_to_overworld(self) -> bool:
        """地上部への遷移（GameManagerから抽出・改良）"""
        try:
            if not self.current_party:
                if self.game_config:
                    error_msg = self.game_config.get_text("game_manager.party_error_no_party")
                    logger.error(error_msg)
                return False
            
            # 遷移履歴に記録
            from_dungeon = (self.current_location == GameLocation.DUNGEON)
            self._add_transition_history("to_overworld", {"from_dungeon": from_dungeon})
            
            # イベントでシーン遷移をリクエスト
            publish_event(
                EventType.SCENE_TRANSITION_REQUESTED,
                "scene_transition_manager",
                {
                    "scene_type": "overworld",
                    "context": {"from_dungeon": from_dungeon}
                }
            )
            
            # ダンジョンからの退出処理
            if from_dungeon and self.dungeon_manager:
                if hasattr(self.dungeon_manager, 'exit_dungeon'):
                    self.dungeon_manager.exit_dungeon()
            
            # ゲーム状態とロケーションを更新
            self.set_current_location(GameLocation.OVERWORLD)
            self.set_game_state("overworld_main")
            
            # オーバーワールドマネージャーの初期化
            if self.overworld_manager and hasattr(self.overworld_manager, 'enter_overworld'):
                self.overworld_manager.enter_overworld()
            
            # SceneManagerで地上部シーンに切り替え
            self._transition_scene_manager_to_overworld()
            
            logger.info("地上部への遷移が完了しました")
            return True
            
        except Exception as e:
            logger.error(f"Overworld transition error: {e}")
            return False
    
    def get_current_location(self) -> GameLocation:
        """現在のロケーション取得"""
        return self.current_location
    
    def get_current_state(self) -> str:
        """現在のゲーム状態取得"""
        return self.game_state
    
    def get_transition_history(self) -> list:
        """遷移履歴取得"""
        return self._transition_history.copy()
    
    def can_transition_to(self, target_location: GameLocation) -> bool:
        """指定のロケーションへの遷移可否確認"""
        # パーティが必要な遷移
        if target_location in [GameLocation.DUNGEON] and not self.current_party:
            return False
        
        # 現在の状態による制限
        if self.game_state in ["combat", "loading", "saving"]:
            return False
        
        # 同じロケーションへの遷移は不要
        if target_location == self.current_location:
            return False
        
        return True
    
    def _load_dungeon_configs(self) -> None:
        """ダンジョン設定の読み込み"""
        try:
            import yaml
            with open("config/dungeons.yaml", 'r', encoding='utf-8') as f:
                dungeons_config = yaml.safe_load(f)
            self._dungeon_configs = dungeons_config.get("dungeons", {})
            logger.info(f"Loaded {len(self._dungeon_configs)} dungeon configurations")
        except Exception as e:
            logger.warning(f"Failed to load dungeon configs: {e}")
            self._dungeon_configs = {}
    
    def _generate_dungeon_seed(self, dungeon_id: str) -> str:
        """ダンジョンIDに基づいてシードを生成（GameManagerから抽出）"""
        # ダンジョンIDがハッシュ値の場合（ダンジョン選択で渡される）は直接使用
        if len(dungeon_id) == 32 and all(c in '0123456789abcdef' for c in dungeon_id):
            # 32文字の16進文字列（MD5ハッシュ）の場合はそのまま使用
            logger.info(f"ハッシュ値をシードとして使用: {dungeon_id[:8]}...")
            return dungeon_id
        
        # 設定ファイルからシード基準を取得
        dungeon_info = self._dungeon_configs.get(dungeon_id, {})
        seed_base = dungeon_info.get("seed_base", dungeon_id)
        
        # 基本シードをベースに一意なシードを生成
        return f"{seed_base}_seed"
    
    def _setup_dungeon_ui(self, current_dungeon) -> None:
        """ダンジョンUI設定"""
        if self.dungeon_renderer and hasattr(self.dungeon_renderer, 'dungeon_ui_manager'):
            if self.dungeon_renderer.dungeon_ui_manager and current_dungeon:
                try:
                    if self.game_config:
                        ui_set_msg = self.game_config.get_text("game_manager.dungeon_ui_set")
                        logger.info(ui_set_msg)
                    self.dungeon_renderer.dungeon_ui_manager.set_dungeon_state(current_dungeon)
                except Exception as e:
                    logger.error(f"Dungeon UI setup error: {e}")
    
    def _attempt_dungeon_renderer_recovery(self, current_dungeon) -> None:
        """ダンジョンレンダラーの自動復旧試行"""
        if not self.dungeon_renderer or not current_dungeon:
            return
        
        try:
            if self.game_config:
                recovery_msg = self.game_config.get_text("game_manager.3d_auto_recovery_attempt")
                logger.info(recovery_msg)
            
            # 自動復旧を試行
            if hasattr(self.dungeon_renderer, 'auto_recover'):
                recovery_success = self.dungeon_renderer.auto_recover()
            else:
                # フォールバック: 旧システムとの互換性
                recovery_success = self.dungeon_renderer.enabled
            
            if recovery_success:
                if self.game_config:
                    success_msg = self.game_config.get_text("game_manager.3d_auto_recovery_success")
                    logger.info(success_msg)
                # UI更新も安全に実行
                try:
                    self.dungeon_renderer.update_ui()
                except Exception as ui_error:
                    if self.game_config:
                        ui_error_msg = self.game_config.get_text("app_log.ui_update_error")
                        logger.warning(ui_error_msg.format(error=ui_error))
            else:
                if self.game_config:
                    failed_msg = self.game_config.get_text("game_manager.3d_auto_recovery_failed")
                    hint_msg = self.game_config.get_text("game_manager.3d_manual_recovery_hint")
                    logger.warning(failed_msg)
                    logger.info(hint_msg)
                
        except Exception as render_error:
            if self.game_config:
                render_error_msg = self.game_config.get_text("game_manager.3d_render_error")
                manual_msg = self.game_config.get_text("game_manager.3d_render_manual_required")
                logger.error(render_error_msg.format(error=render_error))
                logger.info(manual_msg)
            # エラーが発生してもゲーム継続
    
    def _add_transition_history(self, transition_type: str, context: Dict[str, Any]) -> None:
        """遷移履歴の追加"""
        # Enumと文字列の両方に対応
        from_location_value = self.current_location.value if hasattr(self.current_location, 'value') else str(self.current_location)
        history_entry = {
            "type": transition_type,
            "timestamp": self._get_timestamp(),
            "from_location": from_location_value,
            "from_state": self.game_state,
            "context": context
        }
        self._transition_history.append(history_entry)
        
        # 履歴は最大50件まで保持
        if len(self._transition_history) > 50:
            self._transition_history.pop(0)
    
    def _transition_scene_manager_to_dungeon(self, dungeon_id: str) -> None:
        """SceneManagerでダンジョンシーンに切り替え"""
        try:
            # GameManagerからSceneManagerを取得
            import main
            game_manager = getattr(main, 'game_manager', None)
            if game_manager and hasattr(game_manager, 'scene_manager'):
                scene_manager = game_manager.scene_manager
                if scene_manager:
                    # ダンジョンシーンに遷移
                    context = {'dungeon_id': dungeon_id}
                    from src.core.scene_manager import SceneType
                    success = scene_manager.transition_to(SceneType.DUNGEON, context)
                    if success:
                        logger.info(f"SceneManagerでダンジョンシーンに切り替え成功: {dungeon_id}")
                    else:
                        logger.error(f"SceneManagerでダンジョンシーンに切り替え失敗: {dungeon_id}")
                else:
                    logger.warning("SceneManagerが見つかりません")
            else:
                logger.warning("GameManagerまたはSceneManagerが見つかりません")
        except Exception as e:
            logger.error(f"SceneManager遷移中にエラー: {e}")
    
    def _transition_scene_manager_to_overworld(self) -> None:
        """SceneManagerで地上部シーンに切り替え"""
        try:
            # GameManagerからSceneManagerを取得
            import main
            game_manager = getattr(main, 'game_manager', None)
            if game_manager and hasattr(game_manager, 'scene_manager'):
                scene_manager = game_manager.scene_manager
                if scene_manager:
                    # 地上部シーンに遷移
                    from src.core.scene_manager import SceneType
                    success = scene_manager.transition_to(SceneType.OVERWORLD)
                    if success:
                        logger.info("SceneManagerで地上部シーンに切り替え成功")
                    else:
                        logger.error("SceneManagerで地上部シーンに切り替え失敗")
                else:
                    logger.warning("SceneManagerが見つかりません")
            else:
                logger.warning("GameManagerまたはSceneManagerが見つかりません")
        except Exception as e:
            logger.error(f"SceneManager地上部遷移中にエラー: {e}")
    
    def _get_timestamp(self) -> str:
        """現在のタイムスタンプ取得"""
        import datetime
        return datetime.datetime.now().isoformat()