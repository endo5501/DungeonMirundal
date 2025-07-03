"""ダンジョン疑似3D描画システム（Pygame完全実装版）"""

from typing import Optional, Tuple
from enum import Enum
import pygame

from src.dungeon.dungeon_manager import DungeonManager, DungeonState, PlayerPosition
from src.dungeon.dungeon_generator import DungeonLevel
from src.character.party import Party
from src.utils.logger import logger
from src.rendering.renderer_config import RendererConfig
from src.rendering.camera import Camera
from src.rendering.raycast_engine import RaycastEngine
from src.rendering.wall_renderer import WallRenderer
from src.rendering.ui_renderer import UIRenderer
from src.rendering.prop_renderer import PropRenderer
from src.rendering.direction_helper import DirectionHelper

# 入力アクション定数
ACTION_MOVE_FORWARD = "move_forward"
ACTION_MOVE_BACKWARD = "move_backward"
ACTION_TURN_LEFT = "turn_left"
ACTION_TURN_RIGHT = "turn_right"


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
    """ダンジョン疑似3D描画システム（Pygame完全実装）"""
    
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
        
        # コンポーネント初期化
        self.camera = Camera(self.config.directions)
        self.raycast_engine = RaycastEngine(self.config.raycast)
        self.wall_renderer = WallRenderer(self.screen, self.config.wall_render, self.config.colors)
        self.ui_renderer = UIRenderer(self.screen, self.config.ui, self.config.colors)
        self.prop_renderer = PropRenderer(self.screen, self.config.prop_render, self.config.colors)
        
        logger.info("DungeonRendererPygame 初期化完了")
    
    def set_dungeon_manager(self, dungeon_manager: DungeonManager):
        """ダンジョンマネージャー設定"""
        self.dungeon_manager = dungeon_manager
        logger.info("ダンジョンマネージャーを設定しました")
    
    def set_party(self, party: Party):
        """パーティ設定"""
        self.current_party = party
        
        # ダンジョンUIマネージャーにもパーティを設定
        if self.dungeon_ui_manager:
            self.dungeon_ui_manager.set_party(party)
        
        logger.info(f"パーティ{party.name}を設定しました")
    
    def set_dungeon_ui_manager(self, dungeon_ui_manager):
        """ダンジョンUIマネージャーを設定"""
        self.dungeon_ui_manager = dungeon_ui_manager
        
        # 現在のパーティが設定されている場合は設定
        if self.current_party:
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
        
        # 画面クリア
        self.screen.fill((0, 0, 0))
        
        # 疑似3D描画
        try:
            self._render_walls_raycast(level, player_position)
            
            # UI描画（簡易版）
            self._render_basic_ui(player_position, level)
            
            # 画面更新
            pygame.display.flip()
            return True
            
        except Exception as e:
            logger.error(f"直接描画エラー: {e}")
            return False
    
    def _render_basic_ui(self, player_position: PlayerPosition, level: DungeonLevel):
        """基本UI描画"""
        try:
            # フォントを取得
            font = pygame.font.Font(None, 24)
        except:
            return
            
        # 位置情報表示
        pos_text = f"Position: ({player_position.x}, {player_position.y}) Level: {player_position.level}"
        text_surface = font.render(pos_text, True, (255, 255, 255))
        self.screen.blit(text_surface, (10, 10))
        
        # 向いている方向
        direction_text = f"Facing: {player_position.facing.value}"
        dir_surface = font.render(direction_text, True, (255, 255, 255))
        self.screen.blit(dir_surface, (10, 40))
        
        # 操作説明
        help_text = "WASD: Move, Space: Menu, ESC: Return"
        help_surface = font.render(help_text, True, (200, 200, 200))
        self.screen.blit(help_surface, (10, self.screen_height - 30))
        
        # キャラクターステータスバーを描画
        if self.dungeon_ui_manager:
            try:
                self.dungeon_ui_manager.render_overlay()
            except Exception as e:
                logger.warning(f"ダンジョンオーバーレイUI描画エラー: {e}")
    
    def render_dungeon(self, dungeon_state: DungeonState, force_render: bool = False) -> bool:
        """ダンジョンを描画（Pygame版）"""
        if not dungeon_state.player_position:
            logger.error("プレイヤー位置が設定されていません")
            return False
        
        try:
            # 画面をクリア
            self.screen.fill(self.colors['black'])
            
            # カメラ位置更新
            self.update_camera_position(dungeon_state.player_position)
            
            # 現在レベルを取得
            current_level = dungeon_state.levels.get(dungeon_state.player_position.level)
            if not current_level:
                logger.error(f"レベル{dungeon_state.player_position.level}が見つかりません")
                return False
            
            # 疑似3D描画を実行
            self._render_pseudo_3d(current_level, dungeon_state.player_position)
            
            # UI要素を描画
            self._render_ui(dungeon_state)
            
            # 画面更新
            pygame.display.flip()
            
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
        # 床と天井を描画
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
            distance, hit_wall = self.raycast_engine.cast_ray(level, player_pos, ray_start, ray_angle)
            
            if hit_wall:
                self.wall_renderer.render_wall_column(ray_index, distance)
    
    def _cast_ray(self, level: DungeonLevel, player_pos: PlayerPosition, angle: float) -> Tuple[float, bool]:
        """レイキャスティング実行"""
        # レイの方向ベクトル
        dx = math.cos(angle)
        dy = math.sin(angle)
        
        # レイの開始位置
        ray_x, ray_y = self._get_ray_start_position(player_pos)
        distance = 0
        
        while distance < self.view_distance:
            ray_x, ray_y, distance = self._advance_ray(ray_x, ray_y, dx, dy, distance)
            
            if self._is_ray_out_of_bounds(ray_x, ray_y, level):
                return distance, True
            
            grid_x, grid_y = int(ray_x), int(ray_y)
            cell = level.get_cell(grid_x, grid_y)
            
            if self._is_wall_hit(cell, ray_x - grid_x, ray_y - grid_y):
                return distance, True
        
        return self.view_distance, False
    
    def _check_wall_collision(self, cell: DungeonCell, local_x: float, local_y: float) -> bool:
        """セル内での壁との衝突をチェック"""
        # より狭い境界での壁チェック（0.05で判定）
        threshold = 0.05
        
        # 西の壁
        if local_x <= threshold and cell.walls.get(Direction.WEST, False):
            return True
        # 東の壁    
        if local_x >= (1.0 - threshold) and cell.walls.get(Direction.EAST, False):
            return True
        # 北の壁
        if local_y <= threshold and cell.walls.get(Direction.NORTH, False):
            return True
        # 南の壁
        if local_y >= (1.0 - threshold) and cell.walls.get(Direction.SOUTH, False):
            return True
        
        return False
    
    def _render_props_3d(self, level: DungeonLevel, player_pos: PlayerPosition):
        """3Dプロップ（階段、宝箱など）を描画"""
        render_range = 5
        
        for x in range(max(0, player_pos.x - render_range),
                      min(level.width, player_pos.x + render_range + 1)):
            for y in range(max(0, player_pos.y - render_range),
                          min(level.height, player_pos.y + render_range + 1)):
                
                cell = level.get_cell(x, y)
                if not cell:
                    continue
                
                # プロップの位置情報を計算
                prop_info = self._calculate_prop_position(x, y, player_pos)
                
                if not prop_info['visible']:
                    continue
                
                screen_x = prop_info['screen_x']
                distance = prop_info['distance']
                
                # プロップを描画
                if cell.cell_type == CellType.STAIRS_UP:
                    self._draw_stairs(screen_x, distance, True)
                elif cell.cell_type == CellType.STAIRS_DOWN:
                    self._draw_stairs(screen_x, distance, False)
                
                if cell.has_treasure:
                    self._draw_treasure(screen_x, distance)
    
    def _draw_stairs(self, screen_x: int, distance: float, is_up: bool):
        """階段を描画"""
        if distance > self.view_distance:
            return
        
        size = self._calculate_prop_size(distance, STAIRS_BASE_SIZE)
        color = COLOR_STAIRS_UP if is_up else COLOR_STAIRS_DOWN
        
        stairs_rect = self._create_centered_rect(screen_x, size)
        pygame.draw.rect(self.screen, color, stairs_rect)
        
        self._draw_stairs_arrow(screen_x, stairs_rect, size, is_up)
    
    def _draw_treasure(self, screen_x: int, distance: float):
        """宝箱を描画"""
        if distance > self.view_distance:
            return
        
        size = self._calculate_prop_size(distance, TREASURE_BASE_SIZE)
        
        treasure_rect = self._create_centered_rect(screen_x, size)
        pygame.draw.rect(self.screen, COLOR_TREASURE, treasure_rect)
        pygame.draw.rect(self.screen, COLOR_TREASURE_DETAIL, treasure_rect, 1)
    
    def _render_ui(self, dungeon_state: DungeonState):
        """UI要素を描画"""
        pos = dungeon_state.player_position
        if not pos:
            return
        
        # コンパス表示
        compass_text = {
            Direction.NORTH: 'N',
            Direction.EAST: 'E',
            Direction.SOUTH: 'S',
            Direction.WEST: 'W'
        }
        compass_surface = self.font_large.render(compass_text[pos.facing], True, self.colors['white'])
        self.screen.blit(compass_surface, (self.screen_width - 60, 20))
        
        # 位置情報表示（英語版で確実に表示）
        position_text = f"Pos: ({pos.x}, {pos.y}) Lv: {pos.level}"
        try:
            position_surface = self.font_small.render(position_text, True, self.colors['white'])
            self.screen.blit(position_surface, (10, 10))
        except:
            # 日本語が表示できない場合は英語で表示
            position_surface = self.font_small.render(position_text, True, self.colors['white'])
            self.screen.blit(position_surface, (10, 10))
        
        # ヘルプテキスト（英語版で確実に表示）
        help_text = "WASD: Move / QE: Turn / ESC: Menu"
        try:
            help_surface = self.font_small.render(help_text, True, self.colors['gray'])
            self.screen.blit(help_surface, (10, self.screen_height - 30))
        except:
            help_surface = self.font_small.render(help_text, True, self.colors['gray'])
            self.screen.blit(help_surface, (10, self.screen_height - 30))
        
        # キャラクターステータスバーを描画
        if self.dungeon_ui_manager:
            try:
                self.dungeon_ui_manager.render_overlay()
            except Exception as e:
                logger.warning(f"ダンジョンステータスバー描画エラー: {e}")
    
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
        """入力処理"""
        if not self.dungeon_manager or not self.dungeon_manager.current_dungeon:
            return False
        
        try:
            if action == ACTION_MOVE_FORWARD:
                return self._handle_move_forward()
            elif action == ACTION_MOVE_BACKWARD:
                return self._handle_move_backward()
            elif action == ACTION_TURN_LEFT:
                return self._handle_turn_left()
            elif action == ACTION_TURN_RIGHT:
                return self._handle_turn_right()
                
        except Exception as e:
            logger.error(f"入力処理中にエラー: {e}")
        
        return False
    
    # GameManagerからの呼び出し用メソッド
    def _move_forward(self):
        """前進（GameManagerからの呼び出し用）"""
        return self.handle_input("move_forward")
    
    def _move_backward(self):
        """後退（GameManagerからの呼び出し用）"""
        return self.handle_input("move_backward")
    
    def _move_horizontal(self, direction_type: str) -> bool:
        """水平移動の統一実装（GameManagerからの呼び出し用）"""
        # ダンジョンマネージャーや現在のダンジョンがない場合は何もしない
        if not self.dungeon_manager or not self.dungeon_manager.current_dungeon:
            return False
            
        # 真のストレイフ移動実装
        current_pos = self.dungeon_manager.current_dungeon.player_position
        facing = current_pos.facing
        
        # 指定された方向を計算
        if direction_type == 'left':
            target_direction = self._get_left_direction(facing)
        elif direction_type == 'right':
            target_direction = self._get_right_direction(facing)
        else:
            raise ValueError(f"不正な方向タイプ: {direction_type}")
        
        # 指定方向に移動を試行
        return self.dungeon_manager.move_player(target_direction)
    
    def _move_left(self):
        """左移動（GameManagerからの呼び出し用）"""
        return self._move_horizontal('left')
    
    def _move_right(self):
        """右移動（GameManagerからの呼び出し用）"""
        return self._move_horizontal('right')
    
    def _turn_left(self):
        """左回転（GameManagerからの呼び出し用）"""
        return self.handle_input("turn_left")
    
    def _turn_right(self):
        """右回転（GameManagerからの呼び出し用）"""
        return self.handle_input("turn_right")
    
    def _show_menu(self):
        """メニュー表示（GameManagerからの呼び出し用）"""
        # TODO: ダンジョン内メニューの実装
        logger.info("ダンジョン内メニューが呼び出されました")
        return True
    
    def auto_recover(self) -> bool:
        """自動復旧処理（GameManagerからの呼び出し用）"""
        logger.info("ダンジョンレンダラーの自動復旧を開始します")
        try:
            # ダンジョンマネージャーが設定されている場合は初期描画を実行
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
            "fov": self.fov,
            "view_distance": self.view_distance,
            "screen_size": (self.screen_width, self.screen_height),
            "camera_position": (self.camera_x, self.camera_y),
            "camera_angle_degrees": math.degrees(self.camera_angle),
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
    
    def _get_direction_angle(self, direction: Direction) -> float:
        """方向をラジアン角度に変換"""
        direction_angles = {
            Direction.NORTH: DIRECTION_ANGLE_NORTH,
            Direction.EAST: DIRECTION_ANGLE_EAST,
            Direction.SOUTH: DIRECTION_ANGLE_SOUTH,
            Direction.WEST: DIRECTION_ANGLE_WEST
        }
        return direction_angles.get(direction, 0)
    
    def _calculate_ray_count(self) -> int:
        """レイキャスティングのレイ数を計算"""
        return self.screen_width // RAY_RESOLUTION_DIVISOR
    
    def _calculate_ray_angle(self, ray_index: int, ray_count: int) -> float:
        """レイの角度を計算"""
        return self.camera_angle + (ray_index - ray_count // 2) * (self.fov * math.pi / 180) / ray_count
    
    def _render_wall_column(self, ray_index: int, distance: float):
        """壁の縦線を描画"""
        wall_height = self._calculate_wall_height(distance)
        wall_top = self._calculate_wall_position(wall_height)
        wall_color = self._calculate_wall_color(distance)
        
        x = ray_index * WALL_RENDER_WIDTH
        wall_rect = pygame.Rect(x, wall_top, WALL_RENDER_WIDTH, wall_height)
        pygame.draw.rect(self.screen, wall_color, wall_rect)
    
    def _calculate_wall_height(self, distance: float) -> int:
        """距離に基づいて壁の高さを計算"""
        wall_height = int(self.wall_height * self.wall_distance_scale / max(distance, MIN_DISTANCE))
        return min(wall_height, self.screen_height)
    
    def _calculate_wall_position(self, wall_height: int) -> int:
        """壁の描画位置（上端）を計算"""
        return (self.screen_height - wall_height) // 2
    
    def _calculate_wall_color(self, distance: float) -> tuple:
        """距離に基づいて壁の色を計算"""
        brightness = max(BRIGHTNESS_MIN, BRIGHTNESS_MAX - distance / self.view_distance)
        return tuple(int(c * brightness) for c in self.colors['wall'])
    
    def _get_ray_start_position(self, player_pos: PlayerPosition) -> tuple:
        """レイの開始位置を取得"""
        # プレイヤーをセルの中央に配置してレイキャスティングを開始
        return float(player_pos.x) + 0.5, float(player_pos.y) + 0.5
    
    def _advance_ray(self, ray_x: float, ray_y: float, dx: float, dy: float, distance: float) -> tuple:
        """レイを前進させる"""
        ray_x += dx * RAYCAST_STEP_SIZE
        ray_y += dy * RAYCAST_STEP_SIZE
        distance += RAYCAST_STEP_SIZE
        return ray_x, ray_y, distance
    
    def _is_ray_out_of_bounds(self, ray_x: float, ray_y: float, level: DungeonLevel) -> bool:
        """レイが範囲外かチェック"""
        return ray_x < 0 or ray_x >= level.width or ray_y < 0 or ray_y >= level.height
    
    def _is_wall_hit(self, cell: DungeonCell, local_x: float, local_y: float) -> bool:
        """壁にヒットしたかチェック"""
        if not cell or cell.cell_type == CellType.WALL:
            return True
        return self._check_wall_collision(cell, local_x, local_y)
    
    def _calculate_prop_position(self, x: int, y: int, player_pos: PlayerPosition) -> dict:
        """プロップの画面位置情報を計算"""
        dx = x - player_pos.x
        dy = y - player_pos.y
        distance = math.sqrt(dx * dx + dy * dy)
        
        if distance > PROP_VISIBILITY_RANGE:
            return {'visible': False}
        
        angle_to_prop = math.atan2(dy, dx)
        relative_angle = angle_to_prop - self.camera_angle
        
        fov_rad = self.fov * math.pi / 180
        if abs(relative_angle) > fov_rad / 2:
            return {'visible': False}
        
        screen_x = int(self.screen_width / 2 + 
                      (relative_angle / (fov_rad / 2)) * (self.screen_width / 2))
        
        return {
            'visible': True,
            'screen_x': screen_x,
            'distance': distance
        }
    
    def _calculate_prop_size(self, distance: float, base_size: int) -> int:
        """距離に基づいてプロップのサイズを計算"""
        return max(MIN_PROP_SIZE, int(base_size / max(distance, PROP_SIZE_DIVISOR)))
    
    def _create_centered_rect(self, screen_x: int, size: int) -> pygame.Rect:
        """中央揃えの矩形を作成"""
        return pygame.Rect(
            screen_x - size // 2, 
            self.screen_height // 2 - size // 2, 
            size, 
            size
        )
    
    def _draw_stairs_arrow(self, screen_x: int, stairs_rect: pygame.Rect, size: int, is_up: bool):
        """階段の矢印を描画"""
        if is_up:
            pygame.draw.polygon(self.screen, COLOR_WHITE, [
                (screen_x, stairs_rect.top),
                (screen_x - size // 4, stairs_rect.bottom - 2),
                (screen_x + size // 4, stairs_rect.bottom - 2)
            ])
        else:
            pygame.draw.polygon(self.screen, COLOR_WHITE, [
                (screen_x, stairs_rect.bottom),
                (screen_x - size // 4, stairs_rect.top + 2),
                (screen_x + size // 4, stairs_rect.top + 2)
            ])
    
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
        opposite = self._get_opposite_direction(facing)
        success, _ = self.dungeon_manager.move_player(opposite)
        if success:
            self.render_dungeon(self.dungeon_manager.current_dungeon)
        return success
    
    def _handle_turn_left(self) -> bool:
        """左回転処理"""
        facing = self.dungeon_manager.current_dungeon.player_position.facing
        left = self._get_left_direction(facing)
        self.dungeon_manager.turn_player(left)
        self.render_dungeon(self.dungeon_manager.current_dungeon)
        return True
    
    def _handle_turn_right(self) -> bool:
        """右回転処理"""
        facing = self.dungeon_manager.current_dungeon.player_position.facing
        right = self._get_right_direction(facing)
        self.dungeon_manager.turn_player(right)
        self.render_dungeon(self.dungeon_manager.current_dungeon)
        return True
    
    def _calculate_direction(self, direction: Direction, direction_type: str) -> Direction:
        """方向計算の統一メソッド"""
        direction_maps = {
            'opposite': {
                Direction.NORTH: Direction.SOUTH,
                Direction.SOUTH: Direction.NORTH,
                Direction.EAST: Direction.WEST,
                Direction.WEST: Direction.EAST
            },
            'left': {
                Direction.NORTH: Direction.WEST,
                Direction.EAST: Direction.NORTH,
                Direction.SOUTH: Direction.EAST,
                Direction.WEST: Direction.SOUTH
            },
            'right': {
                Direction.NORTH: Direction.EAST,
                Direction.EAST: Direction.SOUTH,
                Direction.SOUTH: Direction.WEST,
                Direction.WEST: Direction.NORTH
            }
        }
        
        if direction_type not in direction_maps:
            raise ValueError(f"不正な方向タイプ: {direction_type}")
            
        return direction_maps[direction_type][direction]
    
    def _get_opposite_direction(self, direction: Direction) -> Direction:
        """反対方向を取得"""
        return self._calculate_direction(direction, 'opposite')
    
    def _get_left_direction(self, direction: Direction) -> Direction:
        """左方向を取得"""
        return self._calculate_direction(direction, 'left')
    
    def _get_right_direction(self, direction: Direction) -> Direction:
        """右方向を取得"""
        return self._calculate_direction(direction, 'right')
    
    def cleanup(self):
        """リソースのクリーンアップ"""
        try:
            # 特にクリーンアップが必要なリソースはないが、
            # 将来的にテクスチャやサウンドを使用する場合はここで解放
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