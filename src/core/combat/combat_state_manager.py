"""Combat state management module."""

from typing import Any, Dict, List, Optional
from src.core.interfaces import ManagedComponent
from src.core.event_bus import EventType, publish_event
from src.utils.logger import logger


class CombatStateManager(ManagedComponent):
    """戦闘状態の統合管理
    
    GameManagerから抽出された戦闘関連処理を統合管理し、
    戦闘のライフサイクル全体を責任を持って管理する。
    """
    
    def __init__(self):
        super().__init__()
        
        # 外部依存コンポーネント
        self.combat_manager = None
        self.encounter_manager = None
        self.dungeon_manager = None
        self.current_party = None
        
        # 戦闘状態
        self.game_state = "overworld_exploration"
        self.current_boss_encounter = None
        
        # 戦闘結果処理ハンドラー
        self._victory_handlers: List[callable] = []
        self._defeat_handlers: List[callable] = []
        self._fled_handlers: List[callable] = []
        self._negotiated_handlers: List[callable] = []
    
    def _do_initialize(self, context: Dict[str, Any]) -> bool:
        """CombatStateManagerの初期化"""
        try:
            # 必要なコンポーネントを取得
            self.combat_manager = context.get('combat_manager')
            self.encounter_manager = context.get('encounter_manager')
            self.dungeon_manager = context.get('dungeon_manager')
            self.current_party = context.get('current_party')
            
            # ゲーム状態管理の参照
            self._set_game_state = context.get('set_game_state_callback')
            self._get_game_state = context.get('get_game_state_callback')
            
            if not all([self.combat_manager, self.encounter_manager, self.dungeon_manager]):
                logger.error("CombatStateManager: required components not provided")
                return False
            
            logger.info("CombatStateManager initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"CombatStateManager initialization failed: {e}")
            return False
    
    def _do_cleanup(self) -> None:
        """CombatStateManagerのクリーンアップ"""
        self._victory_handlers.clear()
        self._defeat_handlers.clear()
        self._fled_handlers.clear()
        self._negotiated_handlers.clear()
        logger.info("CombatStateManager cleaned up")
    
    def handle_game_event(self, event: Any) -> bool:
        """ゲームイベントの処理"""
        # 現在は戦闘開始・終了イベントをGameManagerで処理しているため使用しない
        return False
    
    def set_current_party(self, party) -> None:
        """現在のパーティを設定"""
        self.current_party = party
    
    def set_game_state(self, state: str) -> None:
        """ゲーム状態を設定"""
        self.game_state = state
        if self._set_game_state:
            self._set_game_state(state)
    
    def get_game_state(self) -> str:
        """ゲーム状態を取得"""
        if self._get_game_state:
            return self._get_game_state()
        return self.game_state
    
    def register_victory_handler(self, handler: callable) -> None:
        """勝利処理ハンドラーの登録"""
        if handler not in self._victory_handlers:
            self._victory_handlers.append(handler)
    
    def register_defeat_handler(self, handler: callable) -> None:
        """敗北処理ハンドラーの登録"""
        if handler not in self._defeat_handlers:
            self._defeat_handlers.append(handler)
    
    def register_fled_handler(self, handler: callable) -> None:
        """逃走処理ハンドラーの登録"""
        if handler not in self._fled_handlers:
            self._fled_handlers.append(handler)
    
    def register_negotiated_handler(self, handler: callable) -> None:
        """交渉処理ハンドラーの登録"""
        if handler not in self._negotiated_handlers:
            self._negotiated_handlers.append(handler)
    
    def trigger_encounter(self, encounter_type: str = "normal", level: int = 1) -> bool:
        """エンカウンターを発生させる
        
        GameManagerから抽出されたtrigger_encounterメソッド。
        """
        if not self.encounter_manager or not self.current_party:
            logger.error("エンカウンター発生に必要な条件が満たされていません")
            return False
        
        if not self.dungeon_manager.current_dungeon:
            logger.error("ダンジョンが設定されていません")
            return False
        
        try:
            # ダンジョン情報取得
            current_dungeon = self.dungeon_manager.current_dungeon
            player_pos = current_dungeon.player_position
            dungeon_level = current_dungeon.levels.get(player_pos.level)
            
            if not dungeon_level:
                logger.error(f"レベル {player_pos.level} が見つかりません")
                return False
            
            # エンカウンター生成
            location = (player_pos.x, player_pos.y, player_pos.level)
            encounter_event = self.encounter_manager.generate_encounter(
                encounter_type, 
                level, 
                dungeon_level.attribute,
                location
            )
            
            # 戦闘開始
            if encounter_event and encounter_event.monster_group:
                return self.start_combat(encounter_event.monster_group.monsters)
            
            return False
            
        except Exception as e:
            logger.error(f"エンカウンター発生エラー: {e}")
            return False
    
    def start_combat(self, monsters) -> bool:
        """戦闘開始 - イベント駆動版
        
        GameManagerから抽出されたstart_combatメソッド。
        """
        if not self.combat_manager or not self.current_party:
            logger.error("戦闘開始に必要な条件が満たされていません")
            return False
        
        try:
            # イベントで戦闘シーン遷移をリクエスト
            publish_event(
                EventType.SCENE_TRANSITION_REQUESTED,
                "combat_state_manager",
                {
                    "scene_type": "combat",
                    "context": {"monsters": monsters}
                }
            )
            
            # 戦闘開始イベントを発行
            publish_event(
                EventType.COMBAT_STARTED,
                "combat_state_manager",
                {
                    "party": self.current_party,
                    "monsters": monsters,
                    "monster_count": len(monsters)
                }
            )
            
            logger.info(f"戦闘開始: {len(monsters)}体のモンスターと戦闘")
            return True
            
        except Exception as e:
            logger.error(f"戦闘開始エラー: {e}")
            return False
    
    def check_combat_state(self) -> None:
        """戦闘状態の確認・戦闘終了処理
        
        GameManagerから抽出されたcheck_combat_stateメソッド。
        """
        if not self.combat_manager or self.get_game_state() != "combat":
            return
        
        try:
            from src.combat.combat_manager import CombatState
            
            # 戦闘が終了しているかチェック
            if self.combat_manager.combat_state in [CombatState.VICTORY, CombatState.DEFEAT, 
                                                   CombatState.FLED, CombatState.NEGOTIATED]:
                self.end_combat()
                
        except Exception as e:
            logger.error(f"戦闘状態確認エラー: {e}")
    
    def end_combat(self) -> None:
        """戦闘終了処理
        
        GameManagerから抽出されたend_combatメソッド。
        戦闘結果に応じて適切なハンドラーを呼び出す。
        """
        if not self.combat_manager:
            return
        
        try:
            from src.combat.combat_manager import CombatState
            
            combat_result = self.combat_manager.combat_state
            logger.info(f"戦闘終了: {combat_result.value}")
            
            # 戦闘結果に応じた処理
            if combat_result == CombatState.VICTORY:
                self._handle_combat_victory()
                # ボス戦完了処理
                if self.current_boss_encounter:
                    self._handle_boss_encounter_completion(True)
            elif combat_result == CombatState.DEFEAT:
                self._handle_combat_defeat()
                # ボス戦完了処理
                if self.current_boss_encounter:
                    self._handle_boss_encounter_completion(False)
            elif combat_result == CombatState.FLED:
                self._handle_combat_fled()
            elif combat_result == CombatState.NEGOTIATED:
                self._handle_combat_negotiated()
            
            # ダンジョン探索に戻る
            self.set_game_state("dungeon_exploration")
            
        except Exception as e:
            logger.error(f"戦闘終了処理エラー: {e}")
    
    def _handle_combat_victory(self) -> None:
        """戦闘勝利時の処理
        
        登録されたハンドラーを実行し、基本的な勝利処理を行う。
        """
        logger.info("戦闘勝利時の処理開始")
        
        # 登録されたハンドラーを実行
        for handler in self._victory_handlers:
            try:
                handler()
            except Exception as e:
                logger.error(f"Victory handler error: {e}")
        
        logger.info("戦闘勝利処理完了")
    
    def _handle_combat_defeat(self) -> None:
        """戦闘敗北時の処理
        
        登録されたハンドラーを実行し、基本的な敗北処理を行う。
        """
        logger.info("戦闘敗北時の処理開始")
        
        # 登録されたハンドラーを実行
        for handler in self._defeat_handlers:
            try:
                handler()
            except Exception as e:
                logger.error(f"Defeat handler error: {e}")
        
        logger.info("戦闘敗北処理完了")
    
    def _handle_combat_fled(self) -> None:
        """戦闘逃走時の処理
        
        登録されたハンドラーを実行し、基本的な逃走処理を行う。
        """
        logger.info("戦闘逃走時の処理開始")
        
        # 登録されたハンドラーを実行
        for handler in self._fled_handlers:
            try:
                handler()
            except Exception as e:
                logger.error(f"Fled handler error: {e}")
        
        logger.info("戦闘逃走処理完了")
    
    def _handle_combat_negotiated(self) -> None:
        """戦闘交渉時の処理
        
        登録されたハンドラーを実行し、基本的な交渉処理を行う。
        """
        logger.info("戦闘交渉時の処理開始")
        
        # 登録されたハンドラーを実行
        for handler in self._negotiated_handlers:
            try:
                handler()
            except Exception as e:
                logger.error(f"Negotiated handler error: {e}")
        
        logger.info("戦闘交渉処理完了")
    
    def _handle_boss_encounter_completion(self, victory: bool) -> None:
        """ボス戦完了処理
        
        Args:
            victory: 勝利した場合True
        """
        if not self.current_boss_encounter:
            return
        
        try:
            # ボス戦の結果を記録
            logger.info(f"ボス戦完了: {'勝利' if victory else '敗北'}")
            
            # ボス戦状態をクリア
            self.current_boss_encounter = None
            
            # 追加のボス戦処理は将来実装
            # TODO: ボス戦固有の報酬、進行状況更新等
            
        except Exception as e:
            logger.error(f"ボス戦完了処理エラー: {e}")
    
    def set_boss_encounter(self, boss_encounter) -> None:
        """ボス戦の設定"""
        self.current_boss_encounter = boss_encounter
        logger.info("ボス戦が設定されました")
    
    def clear_boss_encounter(self) -> None:
        """ボス戦状態のクリア"""
        self.current_boss_encounter = None
        logger.info("ボス戦状態がクリアされました")