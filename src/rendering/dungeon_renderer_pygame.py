"""リファクタリング済みダンジョン疑似3D描画システム（Pygame完全実装版）

Fowlerのリファクタリング手法を適用:
- Extract Class: 入力処理をDungeonInputHandlerに分離
- Move Method: 入力関連メソッドを入力ハンドラーに移動
- Single Responsibility: 描画に特化したクラスに変更
"""

from enum import Enum
from typing import Optional
import pygame

from src.dungeon.dungeon_manager import DungeonManager, DungeonState, PlayerPosition
from src.dungeon.dungeon_generator import DungeonLevel
from src.character.party import Party
from src.rendering.dungeon_input_handler import DungeonInputHandler, DungeonInputAction
from src.utils.logger import logger
from src.rendering.renderer_config import RendererConfig
from src.rendering.camera import Camera
from src.rendering.raycast_engine import RaycastEngine
from src.rendering.wall_renderer import WallRenderer
from src.rendering.ui_renderer import UIRenderer
from src.rendering.prop_renderer import PropRenderer
from src.rendering.direction_helper import DirectionHelper


class ViewMode(Enum):
    """表示モード"""
    FIRST_PERSON = "first_person"    # 1人称視点
    THIRD_PERSON = "third_person"    # 3人称視点
    MAP_VIEW = "map_view"            # マップビュー


class RenderQuality(Enum):
    """レンダリング品質"""
    LOW = "low"
    MEDIUM = "medium" 
    HIGH = "high"


class DungeonRendererPygame:
    """ダンジョン疑似3D描画システム（Pygame完全実装）
    
    リファクタリング版：描画に特化し、入力処理を分離。
    """
    
    def __init__(self, screen=None, config: RendererConfig = None):
        logger.info("DungeonRendererPygame 初期化開始")
        
        # 設定初期化
        self.config = config or RendererConfig()
        
        # Pygame初期化
        if not pygame.get_init():
            pygame.init()
        
        # 画面設定
        self.screen = screen
        if not self.screen:
            self.screen = pygame.display.set_mode(self.config.screen.size)
            pygame.display.set_caption("ダンジョンエクスプローラー")
        
        # 基本属性
        self.enabled = True
        self.dungeon_manager = None
        self.current_party = None
        self.dungeon_ui_manager = None
        
        # 疑似3D描画設定
        self.view_mode = ViewMode.FIRST_PERSON
        self.render_quality = RenderQuality.MEDIUM
        
        # 描画コンポーネント初期化
        self.camera = Camera(self.config.directions)
        self.raycast_engine = RaycastEngine(self.config.raycast)
        self.wall_renderer = WallRenderer(self.screen, self.config.wall_render, self.config.colors)
        self.ui_renderer = UIRenderer(self.screen, self.config.ui, self.config.colors)
        self.prop_renderer = PropRenderer(self.screen, self.config.prop_render, self.config.colors)
        
        # 入力ハンドラー（分離されたコンポーネント）
        self.input_handler = DungeonInputHandler()
        
        logger.info("DungeonRendererPygame 初期化完了")
    
    # === 新しい入力システムのアクセサー ===
    
    def get_input_handler(self) -> DungeonInputHandler:
        """入力ハンドラーを取得"""
        return self.input_handler
    
    def handle_key_input(self, key: int) -> bool:
        """キー入力を直接処理"""
        result = self.input_handler.handle_key_input(key)
        if result:
            logger.debug(f"キー入力処理: {result.message}")
            return result.success
        return False
    
    def handle_action_input(self, action: DungeonInputAction) -> bool:
        """アクション入力を直接処理"""
        result = self.input_handler.handle_action(action)
        if result.success:
            logger.debug(f"アクション処理成功: {result.message}")
        else:
            logger.warning(f"アクション処理失敗: {result.message}")
        return result.success
    
    def set_dungeon_manager(self, dungeon_manager: DungeonManager):
        """ダンジョンマネージャー設定"""
        self.dungeon_manager = dungeon_manager
        # 入力ハンドラーにも設定
        self.input_handler.set_dungeon_manager(dungeon_manager)
        logger.info("ダンジョンマネージャーを設定しました")
    
    def set_party(self, party: Party):
        """パーティ設定"""
        # 循環参照防止：既に同じパーティが設定されている場合はスキップ
        if self.current_party is party:
            return
            
        self.current_party = party
        
        # ダンジョンUIマネージャーにもパーティを設定
        if self.dungeon_ui_manager:
            self.dungeon_ui_manager.set_party(party)
        
        if party is not None:
            logger.info(f"パーティ{party.name}を設定しました")
        else:
            logger.info("ダンジョンレンダラーのパーティをクリアしました")
    
    def set_dungeon_ui_manager(self, dungeon_ui_manager):
        """ダンジョンUIマネージャーを設定"""
        # 循環参照防止：既に同じUIマネージャーが設定されている場合はスキップ
        if self.dungeon_ui_manager is dungeon_ui_manager:
            return
            
        self.dungeon_ui_manager = dungeon_ui_manager
        
        # 現在のパーティが設定されている場合は設定
        if self.current_party and dungeon_ui_manager:
            dungeon_ui_manager.set_party(self.current_party)
        
        logger.info("ダンジョンUIマネージャーを設定しました")
    
    def update_ui(self):
        """UI更新（互換性メソッド）"""
        # ダンジョンが設定されている場合は再描画を実行
        if self.dungeon_manager and self.dungeon_manager.current_dungeon:
            self.ensure_initial_render(self.dungeon_manager.current_dungeon)
    
    def render_dungeon_view(self, player_position: PlayerPosition, level: DungeonLevel) -> bool:
        """ダンジョンビューを描画（GameManagerからの呼び出し用）"""
        try:
            # 直接描画処理を実行
            return self._render_direct(player_position, level)
        except Exception as e:
            logger.error(f"ダンジョンビュー描画エラー: {e}")
            return False
    
    def _render_direct(self, player_position: PlayerPosition, level: DungeonLevel) -> bool:
        """直接描画処理"""
        if not self.screen:
            return False
        
        # 疑似3D描画
        try:
            # 床と天井を先に描画（背景クリアの役割も担う）
            self.wall_renderer.render_floor_and_ceiling()
            
            # 壁面描画
            self._render_walls_raycast(level, player_position)
            
            # UI描画（簡易版）
            self.ui_renderer.render_basic_ui(player_position, level)
            
            # ダンジョンUIマネージャーのオーバーレイ（小地図等）も描画
            if self.dungeon_ui_manager:
                try:
                    # ダンジョン状態を構築
                    if self.dungeon_manager and self.dungeon_manager.current_dungeon:
                        dungeon_state = self.dungeon_manager.current_dungeon
                        if hasattr(self.dungeon_ui_manager, 'set_dungeon_state'):
                            self.dungeon_ui_manager.set_dungeon_state(dungeon_state)
                        self.dungeon_ui_manager.render_overlay()
                except Exception as e:
                    logger.warning(f"直接描画でのオーバーレイエラー: {e}")
            
            # 画面更新はGameManagerに任せる
            # pygame.display.flip()  # コメントアウト：重複を避ける
            return True
            
        except Exception as e:
            logger.error(f"直接描画エラー: {e}")
            return False
    
    def render_dungeon(self, dungeon_state: DungeonState, force_render: bool = False) -> bool:  # noqa: ARG002
        """ダンジョンを描画（Pygame版）"""
        if not dungeon_state.player_position:
            logger.error("プレイヤー位置が設定されていません")
            return False
        
        try:
            # カメラ位置更新
            self.update_camera_position(dungeon_state.player_position)
            
            # 現在レベルを取得
            current_level = dungeon_state.levels.get(dungeon_state.player_position.level)
            if not current_level:
                logger.error(f"レベル{dungeon_state.player_position.level}が見つかりません")
                return False
            
            # 疑似3D描画を実行（背景クリアも含む）
            self._render_pseudo_3d(current_level, dungeon_state.player_position)
            
            # UI要素を描画
            self.ui_renderer.render_game_ui(dungeon_state, self.dungeon_ui_manager)
            
            # 画面更新はGameManagerに任せる
            # pygame.display.flip()  # コメントアウト：重複を避ける
            
            logger.debug(f"ダンジョンレベル{current_level.level}を描画しました")
            return True
            
        except Exception as e:
            logger.error(f"ダンジョン描画エラー: {e}")
            return False
    
    def update_camera_position(self, player_pos: PlayerPosition):
        """カメラ位置更新（Pygame版）"""
        self.camera.update_from_player(player_pos)
    
    def _render_pseudo_3d(self, level: DungeonLevel, player_pos: PlayerPosition):
        """疑似3D描画（レイキャスティング風）"""
        # 床と天井を先に描画（これが背景クリアの役割も担う）
        self.wall_renderer.render_floor_and_ceiling()
        
        # 壁面をレイキャスティングで描画
        self._render_walls_raycast(level, player_pos)
        
        # プロップ（階段、宝箱など）を描画
        self.prop_renderer.render_props_3d(level, player_pos, self.camera)
    
    def _render_walls_raycast(self, level: DungeonLevel, player_pos: PlayerPosition):
        """レイキャスティングによる壁面描画"""
        # レイキャスティングの準備
        ray_count = self.config.raycast.calculate_ray_count(self.screen.get_width())
        ray_start = self.camera.get_ray_start_position(player_pos)
        
        for ray_index in range(ray_count):
            ray_angle = self.camera.calculate_ray_angle(ray_index, ray_count, self.config.camera.fov_radians)
            distance, hit_wall, wall_type = self.raycast_engine.cast_ray(level, player_pos, ray_start, ray_angle)
            
            if hit_wall:
                from src.rendering.wall_renderer import WallType
                self.wall_renderer.render_wall_column(ray_index, distance, wall_type or WallType.FACE.value, ray_count)
    
    def ensure_initial_render(self, dungeon_state: DungeonState) -> bool:
        """初期レンダリングを確実に実行"""
        logger.info("初期ダンジョンレンダリングを開始します")
        
        try:
            success = self.render_dungeon(dungeon_state)
            
            if success:
                logger.info("初期レンダリングが完了しました")
            else:
                logger.warning("初期レンダリングに失敗しました")
            
            return success
            
        except Exception as e:
            logger.error(f"初期レンダリング中にエラーが発生しました: {e}")
            return False
    
    def handle_input(self, action: str) -> bool:
        """入力処理（後方互換性用）"""
        # 入力ハンドラーに委譲
        result = self.input_handler.handle_string_action(action)
        
        if result.success:
            logger.debug(f"入力処理成功: {result.message}")
            return True
        else:
            logger.warning(f"入力処理失敗: {result.message}")
            return False
    
    # GameManagerからの呼び出し用メソッド（後方互換性用）
    def _move_forward(self):
        """前進（GameManagerからの呼び出し用）"""
        result = self.input_handler.handle_action(DungeonInputAction.MOVE_FORWARD)
        return result.success
    
    def _move_backward(self):
        """後退（GameManagerからの呼び出し用）"""
        result = self.input_handler.handle_action(DungeonInputAction.MOVE_BACKWARD)
        return result.success
    
    def _move_left(self):
        """左移動（GameManagerからの呼び出し用）"""
        result = self.input_handler.handle_action(DungeonInputAction.MOVE_LEFT)
        return result.success
    
    def _move_right(self):
        """右移動（GameManagerからの呼び出し用）"""
        result = self.input_handler.handle_action(DungeonInputAction.MOVE_RIGHT)
        return result.success
    
    def _turn_left(self):
        """左回転（GameManagerからの呼び出し用）"""
        result = self.input_handler.handle_action(DungeonInputAction.TURN_LEFT)
        return result.success
    
    def _turn_right(self):
        """右回転（GameManagerからの呼び出し用）"""
        result = self.input_handler.handle_action(DungeonInputAction.TURN_RIGHT)
        return result.success
    
    def _show_menu(self):
        """メニュー表示（GameManagerからの呼び出し用）"""
        result = self.input_handler.handle_action(DungeonInputAction.SHOW_MENU)
        return result.success
    
    def auto_recover(self) -> bool:
        """自動復旧処理（GameManagerからの呼び出し用）"""
        logger.info("ダンジョンレンダラーの自動復旧を開始します")
        try:
            if self.dungeon_manager and self.dungeon_manager.current_dungeon:
                success = self.ensure_initial_render(self.dungeon_manager.current_dungeon)
                if success:
                    logger.info("ダンジョンレンダラーの自動復旧に成功しました")
                    return True
                else:
                    logger.warning("初期描画に失敗しました")
                    return False
            else:
                logger.warning("ダンジョンマネージャーまたは現在のダンジョンが設定されていません")
                return False
        except Exception as e:
            logger.error(f"自動復旧中にエラー: {e}")
            return False
    
    def get_debug_info(self) -> dict:
        """デバッグ情報を取得"""
        debug_info = {
            "status": "enabled" if self.enabled else "disabled",
            "render_quality": self.render_quality.value,
            "view_mode": self.view_mode.value,
            "fov": self.config.camera.fov,
            "view_distance": self.config.camera.view_distance,
            "screen_size": self.config.screen.size,
            "camera_position": self.camera.get_position(),
            "camera_angle_degrees": self.camera.state.angle_degrees,
            "dungeon_manager_set": self.dungeon_manager is not None,
            "current_party_set": self.current_party is not None
        }
        
        if self.dungeon_manager and self.dungeon_manager.current_dungeon:
            pos = self.dungeon_manager.current_dungeon.player_position
            if pos:
                debug_info["player_position"] = {
                    "x": pos.x,
                    "y": pos.y,
                    "level": pos.level,
                    "facing": pos.facing.value
                }
        
        return debug_info
    
    def _handle_move_forward(self) -> bool:
        """前進処理"""
        facing = self.dungeon_manager.current_dungeon.player_position.facing
        success, _ = self.dungeon_manager.move_player(facing)
        if success:
            self.render_dungeon(self.dungeon_manager.current_dungeon)
        return success
    
    def _handle_move_backward(self) -> bool:
        """後退処理"""
        facing = self.dungeon_manager.current_dungeon.player_position.facing
        opposite = DirectionHelper.get_opposite_direction(facing)
        success, _ = self.dungeon_manager.move_player(opposite)
        if success:
            self.render_dungeon(self.dungeon_manager.current_dungeon)
        return success
    
    def _handle_turn_left(self) -> bool:
        """左回転処理"""
        facing = self.dungeon_manager.current_dungeon.player_position.facing
        left = DirectionHelper.get_left_direction(facing)
        self.dungeon_manager.turn_player(left)
        self.render_dungeon(self.dungeon_manager.current_dungeon)
        return True
    
    def _handle_turn_right(self) -> bool:
        """右回転処理"""
        facing = self.dungeon_manager.current_dungeon.player_position.facing
        right = DirectionHelper.get_right_direction(facing)
        self.dungeon_manager.turn_player(right)
        self.render_dungeon(self.dungeon_manager.current_dungeon)
        return True
    
    def cleanup(self):
        """リソースのクリーンアップ"""
        try:
            logger.info("DungeonRendererPygame リソースをクリーンアップしました")
        except Exception as e:
            logger.error(f"クリーンアップ中にエラー: {e}")


# グローバルインスタンス
dungeon_renderer_pygame = None

def create_pygame_renderer(screen=None) -> DungeonRendererPygame:
    """Pygameレンダラー作成"""
    global dungeon_renderer_pygame
    if not dungeon_renderer_pygame:
        dungeon_renderer_pygame = DungeonRendererPygame(screen)
    return dungeon_renderer_pygame