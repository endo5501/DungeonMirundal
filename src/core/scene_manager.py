"""ゲームシーン管理システム

GameManagerの責務を分離し、各ゲーム状態（シーン）を独立したクラスとして管理する。
Fowlerの「Extract Class」パターンを適用。
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from enum import Enum
import pygame
from src.utils.logger import logger
from src.utils.constants import GameLocation


class SceneType(Enum):
    """シーンタイプの定義"""
    STARTUP = "startup"
    OVERWORLD = "overworld"
    DUNGEON = "dungeon"
    COMBAT = "combat"


class GameScene(ABC):
    """ゲームシーンの基底クラス"""
    
    def __init__(self, scene_type: SceneType, scene_manager: 'SceneManager'):
        self.scene_type = scene_type
        self.scene_manager = scene_manager
        self.active = False
    
    @abstractmethod
    def enter(self, context: Dict[str, Any] = None) -> bool:
        """シーンに入る際の処理"""
        pass
    
    @abstractmethod
    def exit(self) -> bool:
        """シーンから出る際の処理"""
        pass
    
    @abstractmethod
    def update(self, delta_time: float):
        """シーンの更新処理"""
        pass
    
    @abstractmethod
    def render(self, screen: pygame.Surface):
        """シーンの描画処理"""
        pass
    
    @abstractmethod
    def handle_event(self, event: pygame.event.Event) -> bool:
        """イベント処理（処理した場合はTrue）"""
        pass


class StartupScene(GameScene):
    """スタートアップシーン"""
    
    def __init__(self, scene_manager: 'SceneManager'):
        super().__init__(SceneType.STARTUP, scene_manager)
    
    def enter(self, context: Dict[str, Any] = None) -> bool:
        logger.info("スタートアップシーンに入りました")
        self.active = True
        return True
    
    def exit(self) -> bool:
        logger.info("スタートアップシーンを終了します")
        self.active = False
        return True
    
    def update(self, delta_time: float):
        # スタートアップ完了後、地上部に遷移
        if self.active:
            self.scene_manager.transition_to(SceneType.OVERWORLD)
    
    def render(self, screen: pygame.Surface):
        # 簡単なスタートアップ画面
        screen.fill((0, 0, 0))
        try:
            font = pygame.font.Font(None, 36)
            text = font.render("ゲーム起動中...", True, (255, 255, 255))
            text_rect = text.get_rect(center=(screen.get_width()//2, screen.get_height()//2))
            screen.blit(text, text_rect)
        except:
            pass
    
    def handle_event(self, event: pygame.event.Event) -> bool:
        return False


class OverworldScene(GameScene):
    """地上部シーン"""
    
    def __init__(self, scene_manager: 'SceneManager'):
        super().__init__(SceneType.OVERWORLD, scene_manager)
        self.overworld_manager = None
    
    def enter(self, context: Dict[str, Any] = None) -> bool:
        logger.info("地上部シーンに入りました")
        self.active = True
        
        # OverworldManagerの取得
        game_manager = self.scene_manager.game_manager
        self.overworld_manager = game_manager.overworld_manager
        
        if self.overworld_manager and game_manager.current_party:
            from_dungeon = context.get('from_dungeon', False) if context else False
            return self.overworld_manager.enter_overworld(game_manager.current_party, from_dungeon)
        
        return True
    
    def exit(self) -> bool:
        logger.info("地上部シーンを終了します")
        self.active = False
        
        if self.overworld_manager:
            self.overworld_manager.exit_overworld()
        
        return True
    
    def update(self, delta_time: float):
        # 地上部マネージャーの更新は不要（Window Systemで統合済み）
        pass
    
    def render(self, screen: pygame.Surface):
        if self.overworld_manager:
            self.overworld_manager.render(screen)
    
    def handle_event(self, event: pygame.event.Event) -> bool:
        # イベント処理は既にGameManagerのメインループで処理済み
        return False


class DungeonScene(GameScene):
    """ダンジョンシーン"""
    
    def __init__(self, scene_manager: 'SceneManager'):
        super().__init__(SceneType.DUNGEON, scene_manager)
        self.dungeon_manager = None
        self.dungeon_renderer = None
    
    def enter(self, context: Dict[str, Any] = None) -> bool:
        logger.info("ダンジョンシーンに入りました")
        self.active = True
        
        # マネージャーの取得
        game_manager = self.scene_manager.game_manager
        self.dungeon_manager = game_manager.dungeon_manager
        self.dungeon_renderer = game_manager.dungeon_renderer
        
        # ダンジョン入場処理
        if context and 'dungeon_id' in context:
            dungeon_id = context['dungeon_id']
            return self._enter_dungeon(dungeon_id)
        
        return True
    
    def exit(self) -> bool:
        logger.info("ダンジョンシーンを終了します")
        self.active = False
        
        if self.dungeon_manager:
            self.dungeon_manager.exit_dungeon()
        
        return True
    
    def update(self, delta_time: float):
        # ダンジョン固有の更新処理
        game_manager = self.scene_manager.game_manager
        
        # パーティ状態監視
        if game_manager.current_party:
            game_manager.check_party_status_in_dungeon()
    
    def render(self, screen: pygame.Surface):
        if self.dungeon_renderer and self.dungeon_manager:
            current_dungeon = self.dungeon_manager.current_dungeon
            if current_dungeon and current_dungeon.player_position:
                current_level = current_dungeon.levels.get(current_dungeon.player_position.level)
                if current_level:
                    self.dungeon_renderer.render_dungeon_view(
                        current_dungeon.player_position,
                        current_level
                    )
                    
                    # ダンジョンUIマネージャーの追加描画
                    if hasattr(self.dungeon_renderer, 'dungeon_ui_manager') and self.dungeon_renderer.dungeon_ui_manager:
                        try:
                            # ダンジョン状態とパーティ情報を確実に設定
                            self.dungeon_renderer.dungeon_ui_manager.set_dungeon_state(current_dungeon)
                            
                            # パーティ情報も毎回確認・設定（描画前の最終チェック）
                            game_manager = self.scene_manager.game_manager
                            if game_manager.current_party:
                                # パーティが設定されていない、または異なる場合のみ設定
                                ui_manager = self.dungeon_renderer.dungeon_ui_manager
                                if ui_manager.current_party != game_manager.current_party:
                                    ui_manager.set_party(game_manager.current_party)
                                    logger.debug("描画前にパーティ情報を再設定しました")
                            
                            self.dungeon_renderer.dungeon_ui_manager.render_overlay()
                        except Exception as e:
                            logger.warning(f"ダンジョンUI描画エラー: {e}")
    
    def handle_event(self, event: pygame.event.Event) -> bool:
        # ダンジョン固有のイベント処理
        # デバッグ: WASDキーの処理をログ出力
        if event.type == pygame.KEYDOWN and event.key in [pygame.K_w, pygame.K_a, pygame.K_s, pygame.K_d]:
            logger.info(f"[DEBUG] DungeonScene.handle_event: WASD キー検出 key={pygame.key.name(event.key)}")
            logger.info(f"[DEBUG] dungeon_renderer存在: {self.dungeon_renderer is not None}")
            if self.dungeon_renderer:
                logger.info(f"[DEBUG] dungeon_ui_manager存在: {hasattr(self.dungeon_renderer, 'dungeon_ui_manager') and self.dungeon_renderer.dungeon_ui_manager is not None}")
        
        if self.dungeon_renderer and hasattr(self.dungeon_renderer, 'dungeon_ui_manager'):
            if self.dungeon_renderer.dungeon_ui_manager:
                result = self.dungeon_renderer.dungeon_ui_manager.handle_input(event)
                if event.type == pygame.KEYDOWN and event.key in [pygame.K_w, pygame.K_a, pygame.K_s, pygame.K_d]:
                    logger.info(f"[DEBUG] DungeonScene: DungeonUIManager処理結果={result}")
                return result
        
        if event.type == pygame.KEYDOWN and event.key in [pygame.K_w, pygame.K_a, pygame.K_s, pygame.K_d]:
            logger.info(f"[DEBUG] DungeonScene: DungeonUIManagerなし、Falseを返します")
        return False
    
    def _enter_dungeon(self, dungeon_id: str) -> bool:
        """ダンジョン入場処理"""
        game_manager = self.scene_manager.game_manager
        
        if not game_manager.current_party:
            logger.error("パーティが存在しません")
            return False
        
        try:
            # ダンジョン作成・入場
            if dungeon_id not in self.dungeon_manager.active_dungeons:
                dungeon_seed = game_manager._generate_dungeon_seed(dungeon_id)
                self.dungeon_manager.create_dungeon(dungeon_id, dungeon_seed)
            
            success = self.dungeon_manager.enter_dungeon(dungeon_id, game_manager.current_party)
            
            if success:
                # エンカウンターマネージャーにダンジョン状態を設定
                current_dungeon = self.dungeon_manager.current_dungeon
                if current_dungeon and game_manager.encounter_manager:
                    game_manager.encounter_manager.set_dungeon(current_dungeon)
                
                # ダンジョンUIマネージャーにダンジョン状態とパーティ情報を設定
                if self.dungeon_renderer and hasattr(self.dungeon_renderer, 'dungeon_ui_manager'):
                    if self.dungeon_renderer.dungeon_ui_manager and current_dungeon:
                        try:
                            # ダンジョン状態を設定
                            self.dungeon_renderer.dungeon_ui_manager.set_dungeon_state(current_dungeon)
                            logger.debug("ダンジョンUIマネージャーにダンジョン状態を設定しました")
                            
                            # パーティ情報も明示的に再設定（ダンジョン遷移時の確実な引き継ぎ）
                            if game_manager.current_party:
                                self.dungeon_renderer.dungeon_ui_manager.set_party(game_manager.current_party)
                                logger.debug("ダンジョンUIマネージャーにパーティを再設定しました")
                                
                        except Exception as e:
                            logger.error(f"ダンジョンUIマネージャーへの状態・パーティ設定でエラー: {e}")
                
                # 3D描画自動復旧
                if self.dungeon_renderer and hasattr(self.dungeon_renderer, 'auto_recover'):
                    recovery_success = self.dungeon_renderer.auto_recover()
                    if recovery_success:
                        logger.info("3D描画自動復旧成功")
                    else:
                        logger.warning("3D描画自動復旧失敗")
                
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"ダンジョン入場エラー: {e}")
            return False


class CombatScene(GameScene):
    """戦闘シーン"""
    
    def __init__(self, scene_manager: 'SceneManager'):
        super().__init__(SceneType.COMBAT, scene_manager)
        self.combat_manager = None
    
    def enter(self, context: Dict[str, Any] = None) -> bool:
        logger.info("戦闘シーンに入りました")
        self.active = True
        
        # 戦闘開始
        game_manager = self.scene_manager.game_manager
        self.combat_manager = game_manager.combat_manager
        
        if context and 'monsters' in context:
            monsters = context['monsters']
            if self.combat_manager and game_manager.current_party:
                return self.combat_manager.start_combat(game_manager.current_party, monsters)
        
        return True
    
    def exit(self) -> bool:
        logger.info("戦闘シーンを終了します")
        self.active = False
        return True
    
    def update(self, delta_time: float):
        # 戦闘状態監視
        game_manager = self.scene_manager.game_manager
        if self.combat_manager:
            game_manager.check_combat_state()
    
    def render(self, screen: pygame.Surface):
        # 戦闘画面の描画（現在はダンジョンビューのまま）
        # 将来的には専用の戦闘画面を実装
        pass
    
    def handle_event(self, event: pygame.event.Event) -> bool:
        # 戦闘固有のイベント処理
        return False


class SceneManager:
    """シーン管理クラス
    
    Fowlerの「Extract Class」パターンにより、GameManagerから
    シーン管理の責務を分離。
    """
    
    def __init__(self, game_manager):
        self.game_manager = game_manager
        self.current_scene: Optional[GameScene] = None
        self.scenes: Dict[SceneType, GameScene] = {}
        
        # シーンの初期化
        self._initialize_scenes()
        
        logger.debug("シーン管理システムを初期化しました")
    
    def _initialize_scenes(self):
        """シーンの初期化"""
        self.scenes[SceneType.STARTUP] = StartupScene(self)
        self.scenes[SceneType.OVERWORLD] = OverworldScene(self)
        self.scenes[SceneType.DUNGEON] = DungeonScene(self)
        self.scenes[SceneType.COMBAT] = CombatScene(self)
    
    def transition_to(self, scene_type: SceneType, context: Dict[str, Any] = None) -> bool:
        """シーン遷移"""
        if scene_type not in self.scenes:
            logger.error(f"未知のシーンタイプ: {scene_type}")
            return False
        
        new_scene = self.scenes[scene_type]
        
        # 現在のシーンを終了
        if self.current_scene and self.current_scene != new_scene:
            self.current_scene.exit()
        
        # 新しいシーンに入る
        success = new_scene.enter(context)
        
        if success:
            self.current_scene = new_scene
            
            # GameManagerの状態も更新
            self._update_game_manager_state(scene_type, context)
            
            logger.info(f"シーン遷移完了: {scene_type.value}")
        else:
            logger.error(f"シーン遷移失敗: {scene_type.value}")
        
        return success
    
    def _update_game_manager_state(self, scene_type: SceneType, context: Dict[str, Any]):
        """GameManagerの状態を更新"""
        if scene_type == SceneType.OVERWORLD:
            self.game_manager.current_location = GameLocation.OVERWORLD
            self.game_manager.set_game_state("overworld_exploration")
        elif scene_type == SceneType.DUNGEON:
            self.game_manager.current_location = GameLocation.DUNGEON
            self.game_manager.set_game_state("dungeon_exploration")
        elif scene_type == SceneType.COMBAT:
            self.game_manager.set_game_state("combat")
        elif scene_type == SceneType.STARTUP:
            self.game_manager.set_game_state("startup")
    
    def update(self, delta_time: float):
        """現在のシーンを更新"""
        if self.current_scene:
            self.current_scene.update(delta_time)
    
    def render(self, screen: pygame.Surface):
        """現在のシーンを描画"""
        if self.current_scene:
            self.current_scene.render(screen)
    
    def handle_event(self, event: pygame.event.Event) -> bool:
        """現在のシーンのイベント処理"""
        # デバッグ: WASDキーの処理をログ出力
        if event.type == pygame.KEYDOWN and event.key in [pygame.K_w, pygame.K_a, pygame.K_s, pygame.K_d]:
            scene_type = self.current_scene.scene_type.value if self.current_scene else "None"
            logger.info(f"[DEBUG] SceneManager.handle_event: WASD キー検出 key={pygame.key.name(event.key)}, current_scene={scene_type}")
        
        if self.current_scene:
            result = self.current_scene.handle_event(event)
            if event.type == pygame.KEYDOWN and event.key in [pygame.K_w, pygame.K_a, pygame.K_s, pygame.K_d]:
                logger.info(f"[DEBUG] SceneManager: シーン処理結果={result}")
            return result
        
        if event.type == pygame.KEYDOWN and event.key in [pygame.K_w, pygame.K_a, pygame.K_s, pygame.K_d]:
            logger.info(f"[DEBUG] SceneManager: current_sceneなし、Falseを返します")
        return False
    
    def get_current_scene_type(self) -> Optional[SceneType]:
        """現在のシーンタイプを取得"""
        if self.current_scene:
            return self.current_scene.scene_type
        return None
    
    # === 便利メソッド ===
    
    def transition_to_overworld(self, from_dungeon: bool = False) -> bool:
        """地上部への遷移"""
        context = {'from_dungeon': from_dungeon}
        return self.transition_to(SceneType.OVERWORLD, context)
    
    def transition_to_dungeon(self, dungeon_id: str = "main_dungeon") -> bool:
        """ダンジョンへの遷移"""
        context = {'dungeon_id': dungeon_id}
        return self.transition_to(SceneType.DUNGEON, context)
    
    def transition_to_combat(self, monsters) -> bool:
        """戦闘への遷移"""
        context = {'monsters': monsters}
        return self.transition_to(SceneType.COMBAT, context)
    
    def is_in_scene(self, scene_type: SceneType) -> bool:
        """指定されたシーンにいるかチェック"""
        return (self.current_scene is not None and 
                self.current_scene.scene_type == scene_type)