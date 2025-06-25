"""ダンジョン疑似3D描画システム（Pygame完全実装版）"""

from typing import Dict, List, Tuple, Optional, Any
from enum import Enum
import math
import pygame

from src.dungeon.dungeon_manager import DungeonManager, DungeonState, PlayerPosition
from src.dungeon.dungeon_generator import DungeonLevel, DungeonCell, CellType, Direction, DungeonAttribute
from src.character.party import Party
from src.utils.logger import logger
from src.core.config_manager import config_manager


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
    
    def __init__(self, screen=None):
        logger.info("DungeonRendererPygame 初期化開始")
        
        # Pygame初期化
        if not pygame.get_init():
            pygame.init()
        
        # 画面設定
        self.screen = screen
        if not self.screen:
            self.screen = pygame.display.set_mode((1024, 768))
            pygame.display.set_caption("ダンジョンエクスプローラー")
        
        self.screen_width = self.screen.get_width()
        self.screen_height = self.screen.get_height()
        
        # 基本属性
        self.enabled = True
        self.dungeon_manager = None
        self.current_party = None
        self.dungeon_ui_manager = None
        
        # 疑似3D描画設定
        self.view_mode = ViewMode.FIRST_PERSON
        self.render_quality = RenderQuality.MEDIUM
        self.fov = 75
        self.view_distance = 10
        
        # カメラ設定（1人称視点）
        self.camera_x = 0
        self.camera_y = 0
        self.camera_angle = 0  # ラジアン
        
        # 描画設定
        self.wall_height = 64
        self.wall_distance_scale = 50
        
        # UI要素
        self.ui_elements = {}
        
        # フォント初期化（日本語対応）
        try:
            # 日本語対応フォントを使用
            self.font_small = pygame.font.SysFont('notosanscjk,hiragino,meiryo,msgothic', 18)
            self.font_medium = pygame.font.SysFont('notosanscjk,hiragino,meiryo,msgothic', 24)
            self.font_large = pygame.font.SysFont('notosanscjk,hiragino,meiryo,msgothic', 36)
        except:
            # フォールバック：システムデフォルト
            self.font_small = pygame.font.SysFont(None, 18)
            self.font_medium = pygame.font.SysFont(None, 24)
            self.font_large = pygame.font.SysFont(None, 36)
        
        # 色設定
        self.colors = {
            'black': (0, 0, 0),
            'white': (255, 255, 255),
            'gray': (128, 128, 128),
            'dark_gray': (64, 64, 64),
            'floor': (101, 67, 33),
            'ceiling': (51, 51, 51),
            'wall': (102, 102, 102)
        }
        
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
        # プレイヤー位置をワールド座標に変換
        self.camera_x = player_pos.x
        self.camera_y = player_pos.y
        
        # 向きを角度に変換
        # 数学的な座標系では:
        # - 0度は東（+X方向）
        # - 90度（π/2）は北（-Y方向、画面上では上）
        # - 180度（π）は西（-X方向）
        # - 270度（3π/2）は南（+Y方向、画面上では下）
        direction_angles = {
            Direction.NORTH: -math.pi/2,    # -90度（北を向く）
            Direction.EAST: 0,               # 0度（東を向く）
            Direction.SOUTH: math.pi/2,      # 90度（南を向く）
            Direction.WEST: math.pi          # 180度（西を向く）
        }
        self.camera_angle = direction_angles.get(player_pos.facing, 0)
        
        logger.debug(f"カメラ位置更新: ({self.camera_x}, {self.camera_y}) 角度: {math.degrees(self.camera_angle)}°")
    
    def _render_pseudo_3d(self, level: DungeonLevel, player_pos: PlayerPosition):
        """疑似3D描画（レイキャスティング風）"""
        # 床と天井を描画
        self._render_floor_and_ceiling()
        
        # 壁面をレイキャスティングで描画
        self._render_walls_raycast(level, player_pos)
        
        # プロップ（階段、宝箱など）を描画
        self._render_props_3d(level, player_pos)
    
    def _render_floor_and_ceiling(self):
        """床と天井を描画"""
        # 床（下半分）
        floor_rect = pygame.Rect(0, self.screen_height // 2, self.screen_width, self.screen_height // 2)
        pygame.draw.rect(self.screen, self.colors['floor'], floor_rect)
        
        # 天井（上半分）
        ceiling_rect = pygame.Rect(0, 0, self.screen_width, self.screen_height // 2)
        pygame.draw.rect(self.screen, self.colors['ceiling'], ceiling_rect)
    
    def _render_walls_raycast(self, level: DungeonLevel, player_pos: PlayerPosition):
        """レイキャスティングによる壁面描画"""
        # レイキャスティングの準備
        ray_count = self.screen_width // 2  # 解像度調整
        
        for ray_index in range(ray_count):
            # レイの角度を計算
            ray_angle = self.camera_angle + (ray_index - ray_count // 2) * (self.fov * math.pi / 180) / ray_count
            
            # レイキャストを実行
            distance, hit_wall = self._cast_ray(level, player_pos, ray_angle)
            
            if hit_wall:
                # 壁の高さを距離に応じて計算
                wall_height = int(self.wall_height * self.wall_distance_scale / max(distance, 1))
                wall_height = min(wall_height, self.screen_height)
                
                # 壁の描画位置を計算
                wall_top = (self.screen_height - wall_height) // 2
                wall_bottom = wall_top + wall_height
                
                # 壁の明度を距離に応じて調整
                brightness = max(0.3, 1.0 - distance / self.view_distance)
                wall_color = tuple(int(c * brightness) for c in self.colors['wall'])
                
                # 壁を描画
                x = ray_index * 2  # レイ幅を2ピクセルに
                wall_rect = pygame.Rect(x, wall_top, 2, wall_height)
                pygame.draw.rect(self.screen, wall_color, wall_rect)
    
    def _cast_ray(self, level: DungeonLevel, player_pos: PlayerPosition, angle: float) -> Tuple[float, bool]:
        """レイキャスティング実行"""
        # レイの方向ベクトル
        dx = math.cos(angle)
        dy = math.sin(angle)
        
        # レイの開始位置
        ray_x = float(player_pos.x)
        ray_y = float(player_pos.y)
        
        # レイを進める
        step_size = 0.1
        distance = 0
        
        while distance < self.view_distance:
            ray_x += dx * step_size
            ray_y += dy * step_size
            distance += step_size
            
            # グリッド座標に変換
            grid_x = int(ray_x)
            grid_y = int(ray_y)
            
            # 範囲外チェック
            if grid_x < 0 or grid_x >= level.width or grid_y < 0 or grid_y >= level.height:
                return distance, True
            
            # セルをチェック
            cell = level.get_cell(grid_x, grid_y)
            if not cell or cell.cell_type == CellType.WALL:
                return distance, True
            
            # 壁の存在をチェック
            if self._check_wall_collision(cell, ray_x - grid_x, ray_y - grid_y):
                return distance, True
        
        return self.view_distance, False
    
    def _check_wall_collision(self, cell: DungeonCell, local_x: float, local_y: float) -> bool:
        """セル内での壁との衝突をチェック"""
        # セルの境界での壁チェック
        if local_x <= 0.1 and cell.walls.get(Direction.WEST, False):
            return True
        if local_x >= 0.9 and cell.walls.get(Direction.EAST, False):
            return True
        if local_y <= 0.1 and cell.walls.get(Direction.NORTH, False):
            return True
        if local_y >= 0.9 and cell.walls.get(Direction.SOUTH, False):
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
                
                # プレイヤーからの距離と角度を計算
                dx = x - player_pos.x
                dy = y - player_pos.y
                distance = math.sqrt(dx * dx + dy * dy)
                
                if distance > render_range:
                    continue
                
                # 角度計算
                angle_to_prop = math.atan2(dy, dx)
                relative_angle = angle_to_prop - self.camera_angle
                
                # 視野内かチェック
                fov_rad = self.fov * math.pi / 180
                if abs(relative_angle) > fov_rad / 2:
                    continue
                
                # 画面上の位置を計算
                screen_x = int(self.screen_width / 2 + 
                              (relative_angle / (fov_rad / 2)) * (self.screen_width / 2))
                
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
        
        # 距離に応じてサイズを調整
        size = max(5, int(20 / max(distance, 0.5)))
        
        # 色を設定
        color = (200, 200, 150) if is_up else (150, 150, 200)
        
        # 階段を描画
        stairs_rect = pygame.Rect(screen_x - size // 2, self.screen_height // 2 - size // 2, size, size)
        pygame.draw.rect(self.screen, color, stairs_rect)
        
        # 階段の印を描画
        if is_up:
            pygame.draw.polygon(self.screen, (255, 255, 255), [
                (screen_x, stairs_rect.top),
                (screen_x - size // 4, stairs_rect.bottom - 2),
                (screen_x + size // 4, stairs_rect.bottom - 2)
            ])
        else:
            pygame.draw.polygon(self.screen, (255, 255, 255), [
                (screen_x, stairs_rect.bottom),
                (screen_x - size // 4, stairs_rect.top + 2),
                (screen_x + size // 4, stairs_rect.top + 2)
            ])
    
    def _draw_treasure(self, screen_x: int, distance: float):
        """宝箱を描画"""
        if distance > self.view_distance:
            return
        
        # 距離に応じてサイズを調整
        size = max(4, int(15 / max(distance, 0.5)))
        
        # 金色で宝箱を描画
        color = (255, 215, 0)
        treasure_rect = pygame.Rect(screen_x - size // 2, self.screen_height // 2 - size // 2, size, size)
        pygame.draw.rect(self.screen, color, treasure_rect)
        
        # 宝箱の詳細を描画
        pygame.draw.rect(self.screen, (200, 180, 0), treasure_rect, 1)
    
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
            if action == "move_forward":
                facing = self.dungeon_manager.current_dungeon.player_position.facing
                success, message = self.dungeon_manager.move_player(facing)
                if success:
                    self.render_dungeon(self.dungeon_manager.current_dungeon)
                return success
                
            elif action == "move_backward":
                facing = self.dungeon_manager.current_dungeon.player_position.facing
                opposite = {
                    Direction.NORTH: Direction.SOUTH,
                    Direction.SOUTH: Direction.NORTH,
                    Direction.EAST: Direction.WEST,
                    Direction.WEST: Direction.EAST
                }
                success, message = self.dungeon_manager.move_player(opposite[facing])
                if success:
                    self.render_dungeon(self.dungeon_manager.current_dungeon)
                return success
                
            elif action == "turn_left":
                facing = self.dungeon_manager.current_dungeon.player_position.facing
                left = {
                    Direction.NORTH: Direction.WEST,
                    Direction.WEST: Direction.SOUTH,
                    Direction.SOUTH: Direction.EAST,
                    Direction.EAST: Direction.NORTH
                }
                self.dungeon_manager.turn_player(left[facing])
                self.render_dungeon(self.dungeon_manager.current_dungeon)
                return True
                
            elif action == "turn_right":
                facing = self.dungeon_manager.current_dungeon.player_position.facing
                right = {
                    Direction.NORTH: Direction.EAST,
                    Direction.EAST: Direction.SOUTH,
                    Direction.SOUTH: Direction.WEST,
                    Direction.WEST: Direction.NORTH
                }
                self.dungeon_manager.turn_player(right[facing])
                self.render_dungeon(self.dungeon_manager.current_dungeon)
                return True
                
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
    
    def _move_left(self):
        """左移動（GameManagerからの呼び出し用）"""
        # 左移動は左回転 + 前進 + 右回転として実装
        self.handle_input("turn_left")
        result = self.handle_input("move_forward")
        self.handle_input("turn_right")
        return result
    
    def _move_right(self):
        """右移動（GameManagerからの呼び出し用）"""
        # 右移動は右回転 + 前進 + 左回転として実装
        self.handle_input("turn_right")
        result = self.handle_input("move_forward")
        self.handle_input("turn_left")
        return result
    
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