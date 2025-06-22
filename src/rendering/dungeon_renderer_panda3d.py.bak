"""ダンジョン疑似3D描画システム（Pygame完全移行版）"""

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


class DungeonRenderer:
    """ダンジョン疑似3D描画システム（Pygame完全実装）"""
    
    def __init__(self, screen=None):
        logger.info("DungeonRenderer Pygame版で初期化開始")
        
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
        
        # フォント初期化
        try:
            self.font_small = pygame.font.Font(None, 24)
            self.font_medium = pygame.font.Font(None, 32)
            self.font_large = pygame.font.Font(None, 48)
        except:
            self.font_small = pygame.font.SysFont('arial', 18)
            self.font_medium = pygame.font.SysFont('arial', 24)
            self.font_large = pygame.font.SysFont('arial', 36)
        
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
        
        logger.info("DungeonRenderer Pygame版初期化完了")
        
    
    def set_dungeon_manager(self, dungeon_manager: DungeonManager):
        """ダンジョンマネージャー設定"""
        self.dungeon_manager = dungeon_manager
        logger.info("ダンジョンマネージャーを設定しました")
    
    def set_party(self, party: Party):
        """パーティ設定"""
        self.current_party = party
        logger.info(f"パーティ{party.name}を設定しました")
    
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
    
    def update_camera_position(self, player_pos: PlayerPosition):
        """カメラ位置更新（Pygame版）"""
        # プレイヤー位置をワールド座標に変換
        self.camera_x = player_pos.x
        self.camera_y = player_pos.y
        
        # 向きを角度に変換
        direction_angles = {
            Direction.NORTH: 0,
            Direction.EAST: math.pi/2,
            Direction.SOUTH: math.pi,
            Direction.WEST: 3*math.pi/2
        }
        self.camera_angle = direction_angles.get(player_pos.facing, 0)
        
        logger.debug(f"カメラ位置更新: ({self.camera_x}, {self.camera_y}) 角度: {math.degrees(self.camera_angle)}°")
    
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
        
        # 位置情報表示
        position_text = f"位置: ({pos.x}, {pos.y}) レベル: {pos.level}"
        position_surface = self.font_small.render(position_text, True, self.colors['white'])
        self.screen.blit(position_surface, (10, 10))
        
        # ヘルプテキスト
        help_text = "WASD: 移動 / QE: 回転 / ESC: メニュー"
        help_surface = self.font_small.render(help_text, True, self.colors['gray'])
        self.screen.blit(help_surface, (10, self.screen_height - 30))
    
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
    
    def cleanup(self):
        """リソースのクリーンアップ"""
        try:
            # 特にクリーンアップが必要なリソースはないが、
            # 将来的にテクスチャやサウンドを使用する場合はここで解放
            logger.info("DungeonRenderer リソースをクリーンアップしました")
        except Exception as e:
            logger.error(f"クリーンアップ中にエラー: {e}")
    
    
    
    
    
    
    
    
    def _force_frame_render(self):
        """強制的にフレームレンダリングを実行"""
        if not self.enabled:
            return
        
        try:
            # Panda3Dに即座にフレームを描画させる
            self.base_instance.graphicsEngine.renderFrame()
            logger.debug("強制フレームレンダリングを実行しました")
        except Exception as e:
            logger.warning(f"強制フレームレンダリングに失敗: {e}")
    
    def ensure_initial_render(self, dungeon_state: DungeonState):
        """初期レンダリングを確実に実行（安全版）"""
        if not self.enabled:
            logger.info("ダンジョンレンダラーが無効化されています")
            return True  # 無効化状態でも成功とする
        
        logger.info("初期ダンジョンレンダリングを開始します")
        
        try:
            # 単純な初期レンダリングのみ実行
            success = self.render_dungeon(dungeon_state)
            
            if success:
                logger.info("初期レンダリングが完了しました")
            else:
                logger.warning("初期レンダリングに失敗しました")
            
            return success
            
        except Exception as e:
            logger.error(f"初期レンダリング中にエラーが発生しました: {e}")
            return False
    
    def _reset_rendering_pipeline(self):
        """レンダリングパイプラインをリセット（無効化版）"""
        if not self.enabled:
            return
        
        # シーンをクリアのみ（危険な操作は無効化）
        self._clear_scene()
        
        logger.debug("レンダリングパイプラインの基本クリアを実行しました")
    
    def _validate_scene_completeness(self) -> bool:
        """シーンの完成度を検証"""
        if not self.enabled:
            return True
        
        # ノード数をチェック
        wall_count = len(self.wall_nodes)
        floor_count = len(self.floor_nodes)
        ceiling_count = len(self.ceiling_nodes)
        
        total_nodes = wall_count + floor_count + ceiling_count
        
        logger.debug(f"シーンノード数: 壁={wall_count}, 床={floor_count}, 天井={ceiling_count}, 合計={total_nodes}")
        
        # 最低限のノードが存在するかチェック
        if total_nodes < 3:  # 最低でも床、天井、1つの壁
            logger.warning(f"シーンノード数が不十分です: {total_nodes}")
            return False
        
        # レンダーノードが適切にアタッチされているかチェック
        for node_dict in [self.wall_nodes, self.floor_nodes, self.ceiling_nodes]:
            for node in node_dict.values():
                if not node.getParent():
                    logger.warning("アタッチされていないノードが見つかりました")
                    return False
        
        return True
    
    def get_debug_info(self) -> dict:
        """デバッグ情報を取得"""
        if not self.enabled:
            return {"status": "disabled"}
        
        debug_info = {
            "status": "enabled",
            "render_quality": self.render_quality.value,
            "view_mode": self.view_mode.value,
            "camera_height": self.camera_height,
            "fov": self.fov,
            "view_distance": self.view_distance,
            "nodes": {
                "walls": len(self.wall_nodes),
                "floors": len(self.floor_nodes),
                "ceilings": len(self.ceiling_nodes),
                "props": len(self.prop_nodes)
            },
            "ui_elements": len(self.ui_elements),
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
        
        # カメラ情報
        if hasattr(self, 'camera'):
            cam_pos = self.camera.getPos()
            cam_hpr = self.camera.getHpr()
            debug_info["camera"] = {
                "position": [cam_pos.x, cam_pos.y, cam_pos.z],
                "hpr": [cam_hpr.x, cam_hpr.y, cam_hpr.z]
            }
        
        return debug_info
    
    def log_debug_info(self):
        """デバッグ情報をログ出力"""
        debug_info = self.get_debug_info()
        logger.info("=== ダンジョンレンダラー デバッグ情報 ===")
        for key, value in debug_info.items():
            logger.info(f"{key}: {value}")
        logger.info("============================================")
    
    def handle_rendering_error(self, error: Exception, context: str = ""):
        """レンダリングエラーのハンドリング"""
        error_msg = f"レンダリングエラー"
        if context:
            error_msg += f" ({context})"
        error_msg += f": {str(error)}"
        
        logger.error(error_msg)
        
        # デバッグ情報も出力
        try:
            self.log_debug_info()
        except Exception as debug_error:
            logger.error(f"デバッグ情報出力中にエラー: {debug_error}")
        
        # エラー回復を試行
        try:
            self._attempt_error_recovery()
        except Exception as recovery_error:
            logger.error(f"エラー回復中にエラー: {recovery_error}")
    
    def _attempt_error_recovery(self):
        """エラー回復を試行"""
        logger.info("レンダリングエラーからの回復を試行します")
        
        # シーンをクリア
        self._clear_scene()
        
        # ライティングを再初期化
        self._initialize_lighting()
        
        # カメラを再初期化
        self._initialize_camera()
        
        logger.info("エラー回復処理が完了しました")
    
    def _update_ui(self, dungeon_state: DungeonState):
        """UI更新（無効化状態でも基本更新実行）"""
        pos = dungeon_state.player_position
        if not pos:
            return
        
        try:
            # コンパス更新
            if 'compass' in self.ui_elements:
                compass_text = {
                    Direction.NORTH: 'N',
                    Direction.EAST: 'E', 
                    Direction.SOUTH: 'S',
                    Direction.WEST: 'W'
                }
                self.ui_elements['compass'].setText(compass_text[pos.facing])
            
            # 位置情報更新
            if 'position' in self.ui_elements:
                position_text = f"位置: ({pos.x}, {pos.y}) レベル: {pos.level}"
                self.ui_elements['position'].setText(position_text)
                
            logger.debug(f"UI更新完了: 位置({pos.x}, {pos.y}), 向き{pos.facing.name}")
            
        except Exception as e:
            logger.warning(f"UI更新中にエラー: {e}")
    
    # 移動・回転ハンドラー
    def _move_forward(self):
        """前進（安全版）"""
        logger.info("WASDキー: 前進操作が呼ばれました")
        try:
            if not self.dungeon_manager:
                logger.warning("ダンジョンマネージャーが設定されていません")
                return
            
            if not self.dungeon_manager.current_dungeon:
                logger.warning("現在のダンジョンが設定されていません")
                return
                
            facing = self.dungeon_manager.current_dungeon.player_position.facing
            success, message = self.dungeon_manager.move_player(facing)
            
            if success:
                logger.info(f"前進移動が成功しました: {message}")
                try:
                    # 無効化状態でもレンダリングとUI更新を実行
                    self.render_dungeon(self.dungeon_manager.current_dungeon)
                    self.update_ui()
                    logger.debug("前進移動の処理が完了しました")
                except Exception as e:
                    logger.error(f"前進移動の処理中にエラー: {e}")
            else:
                logger.info(f"前進移動が失敗しました: {message}")
        except Exception as e:
            logger.error(f"前進移動処理中にエラー: {e}")
    
    def _move_backward(self):
        """後退（安全版）"""
        logger.info("WASDキー: 後退操作が呼ばれました")
        try:
            if not self.dungeon_manager:
                logger.warning("ダンジョンマネージャーが設定されていません")
                return
            
            if not self.dungeon_manager.current_dungeon:
                logger.warning("現在のダンジョンが設定されていません")
                return
                
            facing = self.dungeon_manager.current_dungeon.player_position.facing
            # 後退は前進の逆方向
            opposite = {
                Direction.NORTH: Direction.SOUTH,
                Direction.SOUTH: Direction.NORTH,
                Direction.EAST: Direction.WEST,
                Direction.WEST: Direction.EAST
            }
            success, message = self.dungeon_manager.move_player(opposite[facing])
            
            if success:
                logger.info(f"後退移動が成功しました: {message}")
                try:
                    # 無効化状態でもレンダリングとUI更新を実行
                    self.render_dungeon(self.dungeon_manager.current_dungeon)
                    self.update_ui()
                    logger.debug("後退移動の処理が完了しました")
                except Exception as e:
                    logger.error(f"後退移動の処理中にエラー: {e}")
            else:
                logger.info(f"後退移動が失敗しました: {message}")
        except Exception as e:
            logger.error(f"後退移動処理中にエラー: {e}")
    
    def _move_left(self):
        """左移動（安全版）"""
        logger.info("WASDキー: 左移動操作が呼ばれました")
        try:
            if not self.dungeon_manager:
                logger.warning("ダンジョンマネージャーが設定されていません")
                return
            
            if not self.dungeon_manager.current_dungeon:
                logger.warning("現在のダンジョンが設定されていません")
                return
                
            facing = self.dungeon_manager.current_dungeon.player_position.facing
            # 左移動は現在の向きから左方向
            left = {
                Direction.NORTH: Direction.WEST,
                Direction.WEST: Direction.SOUTH,
                Direction.SOUTH: Direction.EAST,
                Direction.EAST: Direction.NORTH
            }
            success, message = self.dungeon_manager.move_player(left[facing])
            
            if success:
                logger.info(f"左移動が成功しました: {message}")
                try:
                    # 無効化状態でもレンダリングとUI更新を実行
                    self.render_dungeon(self.dungeon_manager.current_dungeon)
                    self.update_ui()
                    logger.debug("左移動の処理が完了しました")
                except Exception as e:
                    logger.error(f"左移動の処理中にエラー: {e}")
            else:
                logger.info(f"左移動が失敗しました: {message}")
        except Exception as e:
            logger.error(f"左移動処理中にエラー: {e}")
    
    def _move_right(self):
        """右移動（安全版）"""
        logger.info("WASDキー: 右移動操作が呼ばれました")
        try:
            if not self.dungeon_manager:
                logger.warning("ダンジョンマネージャーが設定されていません")
                return
            
            if not self.dungeon_manager.current_dungeon:
                logger.warning("現在のダンジョンが設定されていません")
                return
                
            facing = self.dungeon_manager.current_dungeon.player_position.facing
            # 右移動は現在の向きから右方向
            right = {
                Direction.NORTH: Direction.EAST,
                Direction.EAST: Direction.SOUTH,
                Direction.SOUTH: Direction.WEST,
                Direction.WEST: Direction.NORTH
            }
            success, message = self.dungeon_manager.move_player(right[facing])
            
            if success:
                logger.info(f"右移動が成功しました: {message}")
                try:
                    # 無効化状態でもレンダリングとUI更新を実行
                    self.render_dungeon(self.dungeon_manager.current_dungeon)
                    self.update_ui()
                    logger.debug("右移動の処理が完了しました")
                except Exception as e:
                    logger.error(f"右移動の処理中にエラー: {e}")
            else:
                logger.info(f"右移動が失敗しました: {message}")
        except Exception as e:
            logger.error(f"右移動処理中にエラー: {e}")
    
    def _turn_left(self):
        """左回転（安全版）"""
        logger.info("WASDキー: 左回転操作が呼ばれました")
        try:
            if not self.dungeon_manager:
                logger.warning("ダンジョンマネージャーが設定されていません")
                return
            
            if not self.dungeon_manager.current_dungeon:
                logger.warning("現在のダンジョンが設定されていません")
                return
                
            facing = self.dungeon_manager.current_dungeon.player_position.facing
            left = {
                Direction.NORTH: Direction.WEST,
                Direction.WEST: Direction.SOUTH,
                Direction.SOUTH: Direction.EAST,
                Direction.EAST: Direction.NORTH
            }
            self.dungeon_manager.turn_player(left[facing])
            logger.info(f"左回転が成功しました: {left[facing].name}")
            
            try:
                # 無効化状態でもレンダリングとUI更新を実行
                self.render_dungeon(self.dungeon_manager.current_dungeon)
                self.update_ui()
                logger.debug("左回転の処理が完了しました")
            except Exception as e:
                logger.error(f"左回転の処理中にエラー: {e}")
        except Exception as e:
            logger.error(f"左回転処理中にエラー: {e}")
    
    def _turn_right(self):
        """右回転（安全版）"""
        logger.info("WASDキー: 右回転操作が呼ばれました")
        try:
            if not self.dungeon_manager:
                logger.warning("ダンジョンマネージャーが設定されていません")
                return
            
            if not self.dungeon_manager.current_dungeon:
                logger.warning("現在のダンジョンが設定されていません")
                return
                
            facing = self.dungeon_manager.current_dungeon.player_position.facing
            right = {
                Direction.NORTH: Direction.EAST,
                Direction.EAST: Direction.SOUTH,
                Direction.SOUTH: Direction.WEST,
                Direction.WEST: Direction.NORTH
            }
            self.dungeon_manager.turn_player(right[facing])
            logger.info(f"右回転が成功しました: {right[facing].name}")
            
            try:
                # 無効化状態でもレンダリングとUI更新を実行
                self.render_dungeon(self.dungeon_manager.current_dungeon)
                self.update_ui()
                logger.debug("右回転の処理が完了しました")
            except Exception as e:
                logger.error(f"右回転の処理中にエラー: {e}")
        except Exception as e:
            logger.error(f"右回転処理中にエラー: {e}")
    
    def _show_menu(self):
        """メニュー表示"""
        if hasattr(self, 'ui_manager') and self.ui_manager:
            self.ui_manager.toggle_main_menu()
        else:
            logger.info("メニュー表示（UIマネージャー未初期化）")
    
    def _return_to_overworld(self):
        """地上部に帰還"""
        if self.dungeon_manager and hasattr(self.dungeon_manager, 'return_to_overworld'):
            success = self.dungeon_manager.return_to_overworld()
            if success:
                logger.info("地上部への帰還が完了しました")
            else:
                logger.error("地上部への帰還に失敗しました")
        else:
            logger.error("地上部帰還: ダンジョンマネージャーが設定されていません")
    
    def set_game_manager(self, game_manager):
        """ゲームマネージャーを設定"""
        if hasattr(self, 'ui_manager') and self.ui_manager:
            self.ui_manager.set_managers(self.dungeon_manager, game_manager)
        logger.debug("ゲームマネージャーを設定しました")
    
    def update_ui(self):
        """UI情報を更新（安全版）"""
        if not self.dungeon_manager:
            logger.debug("UI更新をスキップ（ダンジョンマネージャー未設定）")
            return
            
        # 無効化状態でも基本UI要素は更新
        if (self.dungeon_manager.current_dungeon and 
            self.dungeon_manager.current_dungeon.player_position):
            pos = self.dungeon_manager.current_dungeon.player_position
            
            try:
                # 基本UI要素の更新（無効化状態でも実行）
                if 'compass' in self.ui_elements:
                    compass_text = {
                        Direction.NORTH: 'N',
                        Direction.EAST: 'E', 
                        Direction.SOUTH: 'S',
                        Direction.WEST: 'W'
                    }
                    self.ui_elements['compass'].setText(compass_text[pos.facing])
                
                if 'position' in self.ui_elements:
                    position_text = f"位置: ({pos.x}, {pos.y}) レベル: {pos.level}"
                    self.ui_elements['position'].setText(position_text)
                    
                logger.debug(f"基本UI更新完了: 位置({pos.x}, {pos.y}), 向き{pos.facing.name}")
                
            except Exception as e:
                logger.warning(f"基本UI更新中にエラー: {e}")
        
        # 高度なUIマネージャーによる更新（有効化時のみ）
        if self.enabled and hasattr(self, 'ui_manager') and self.ui_manager:
            if (self.dungeon_manager.current_dungeon and 
                self.dungeon_manager.current_dungeon.player_position):
                pos = self.dungeon_manager.current_dungeon.player_position
                location_info = f"({pos.x}, {pos.y}) レベル: {pos.level}"
                try:
                    self.ui_manager.update_location(location_info)
                    self.ui_manager.update_party_status()
                    logger.debug("高度なUIマネージャー更新完了")
                except Exception as e:
                    logger.warning(f"高度なUIマネージャー更新中にエラー: {e}")
    
    # ========== 段階的有効化システム ==========
    
    def _safe_initialize_showbase_references(self):
        """ShowBase参照の安全な初期化"""
        if not self.base_instance:
            logger.warning("ShowBaseインスタンスが設定されていません")
            return
        
        try:
            # ShowBaseの基本参照を安全に設定
            self.render = getattr(self.base_instance, 'render', None)
            self.camera = getattr(self.base_instance, 'camera', None)
            self.cam = getattr(self.base_instance, 'cam', None)
            self.win = getattr(self.base_instance, 'win', None)
            self.taskMgr = getattr(self.base_instance, 'taskMgr', None)
            self.loader = getattr(self.base_instance, 'loader', None)
            self.setBackgroundColor = getattr(self.base_instance, 'setBackgroundColor', None)
            
            # 参照の健全性をチェック
            missing_refs = []
            for ref_name in ['render', 'camera', 'cam', 'win']:
                if getattr(self, ref_name, None) is None:
                    missing_refs.append(ref_name)
            
            if missing_refs:
                logger.warning(f"ShowBase参照が不完全です: {missing_refs}")
            else:
                logger.info("ShowBase参照を安全に設定しました")
                
        except Exception as e:
            logger.error(f"ShowBase参照初期化中にエラー: {e}")
            self.initialization_errors.append(f"ShowBase参照: {e}")
    
    def try_enable_basic(self) -> bool:
        """基本3D描画の有効化を試行"""
        logger.info("基本3D描画の有効化を試行します")
        
        try:
            if not self.render or not self.camera:
                logger.error("ShowBase参照が不完全です")
                return False
            
            # 基本的な床と壁を描画
            if self.dungeon_manager and self.dungeon_manager.current_dungeon:
                dungeon = self.dungeon_manager.current_dungeon
                pos = dungeon.player_position
                level = dungeon.levels.get(pos.level) if pos else None
                
                if pos and level:
                    # 現在位置の床を描画
                    self._render_basic_floor(pos.x, pos.y)
                    
                    # 基本的なカメラ設定
                    self.camera.setPos(pos.x * 2.0, -pos.y * 2.0 - 3, self.camera_height)
                    self.camera.setHpr(0, 0, 0)
                
                    self.current_stage = "basic"
                    self.enabled = True
                    logger.info("基本3D描画が有効化されました")
                    return True
                else:
                    logger.error("プレイヤー位置またはレベルデータが不正です")
                    return False
            else:
                logger.error("ダンジョンが設定されていません")
                return False
                
        except Exception as e:
            logger.error(f"基本3D描画有効化中にエラー: {e}")
            return False
    
    def try_enable_full(self) -> bool:
        """完全3D描画の有効化を試行"""
        logger.info("完全3D描画の有効化を試行します")
        
        try:
            # まず基本描画を確認
            if self.current_stage == "disabled" and not self.try_enable_basic():
                return False
            
            # 完全な描画機能を有効化
            if self.dungeon_manager and self.dungeon_manager.current_dungeon:
                # ライティングを追加
                self._setup_lighting()
                
                # 完全なダンジョン描画
                self.render_dungeon(self.dungeon_manager.current_dungeon)
                
                self.current_stage = "full"
                self.enabled = True
                logger.info("完全3D描画が有効化されました")
                return True
            else:
                logger.error("ダンジョンが設定されていません")
                return False
                
        except Exception as e:
            logger.error(f"完全3D描画有効化中にエラー: {e}")
            return False
    
    def auto_recover(self) -> bool:
        """自動復旧を試行（basic → full の順）"""
        logger.info("3D描画の自動復旧を開始します")
        
        # まずbasicを試行
        if self.try_enable_basic():
            logger.info("基本3D描画の復旧が成功しました")
            # 成功したらfullも試行
            if self.try_enable_full():
                logger.info("完全3D描画の復旧が成功しました")
                return True
            else:
                logger.info("基本3D描画のみ復旧しました（完全復旧は失敗）")
                return True
        else:
            logger.warning("3D描画の自動復旧に失敗しました")
            return False
    
    def emergency_disable(self):
        """緊急無効化 - 全ての3D描画を停止"""
        logger.warning("3D描画システムを緊急無効化します")
        
        try:
            # 全ノードを削除
            for node_dict in [self.wall_nodes, self.floor_nodes, self.ceiling_nodes, self.prop_nodes]:
                for node in list(node_dict.values()):
                    try:
                        if hasattr(node, 'removeNode'):
                            node.removeNode()
                    except Exception as e:
                        logger.warning(f"ノード削除中にエラー: {e}")
                node_dict.clear()
            
            # 状態をリセット
            self.current_stage = "disabled"
            self.enabled = False
            
            logger.info("3D描画システムが緊急無効化されました")
            
        except Exception as e:
            logger.error(f"緊急無効化中にエラー: {e}")
    
    def _render_basic_floor(self, x: int, y: int):
        """基本的な床タイルを描画"""
        try:
            from panda3d.core import CardMaker, Vec4
            
            floor_cm = CardMaker(f"basic_floor_{x}_{y}")
            floor_cm.setFrame(-1, 1, -1, 1)
            
            floor_node = self.render.attachNewNode(floor_cm.generate())
            floor_node.setPos(x * 2.0, -y * 2.0, 0)
            floor_node.setHpr(0, -90, 0)  # 水平配置
            floor_node.setColor(0.5, 0.3, 0.1, 1)  # 茶色
            floor_node.setTwoSided(True)
            
            self.floor_nodes[f"basic_{x}_{y}"] = floor_node
            logger.debug(f"基本床タイルを描画: ({x}, {y})")
            
        except Exception as e:
            logger.error(f"基本床描画中にエラー: {e}")
    
    def _setup_lighting(self):
        """基本的なライティングを設定"""
        try:
            from panda3d.core import AmbientLight, DirectionalLight, Vec4
            
            # 環境光
            ambient_light = AmbientLight('ambient')
            ambient_light.setColor(Vec4(0.4, 0.4, 0.5, 1))
            ambient_light_np = self.render.attachNewNode(ambient_light)
            self.render.setLight(ambient_light_np)
            
            # 方向光
            directional_light = DirectionalLight('directional')
            directional_light.setColor(Vec4(0.8, 0.8, 0.7, 1))
            from panda3d.core import Vec3
            directional_light.setDirection(Vec3(-1, -1, -1))
            directional_light_np = self.render.attachNewNode(directional_light)
            self.render.setLight(directional_light_np)
            
            logger.info("基本ライティングを設定しました")
            
        except Exception as e:
            logger.error(f"ライティング設定中にエラー: {e}")
    
    def get_stage_info(self) -> dict:
        """現在の段階情報を取得"""
        return {
            "current_stage": self.current_stage,
            "enabled_flag": self.enabled,
            "node_counts": {
                "walls": len(self.wall_nodes),
                "floors": len(self.floor_nodes),
                "ceilings": len(self.ceiling_nodes),
                "props": len(self.prop_nodes)
            },
            "has_errors": len(self.initialization_errors) > 0,
            "errors": self.initialization_errors.copy()
        }
    
    def manual_recovery_attempt(self) -> bool:
        """手動復旧試行 - スペースキー用"""
        logger.info("手動による3D描画復旧を試行します")
        
        if self.current_stage == "disabled":
            return self.auto_recover()
        elif self.current_stage == "basic":
            return self.try_enable_full()
        elif self.current_stage == "full":
            logger.info("既に完全3D描画が有効化されています")
            return True
        else:
            logger.warning(f"未知の段階です: {self.current_stage}")
            return False
    
    def log_current_status(self):
        """現在の状態をログ出力"""
        info = self.get_stage_info()
        logger.info(f"=== 3D描画システム状態 ===")
        logger.info(f"段階: {info['current_stage']}")
        logger.info(f"有効: {info['enabled_flag']}")
        logger.info(f"ノード数: {info['node_counts']}")
        if info['has_errors']:
            logger.info(f"エラー: {info['errors']}")
        logger.info("===========================")
    
    # ========== 段階別実装メソッド ==========
    
    def _advance_to_stage1a(self) -> bool:
        """Stage 1-A: 最小限のPanda3D接続テスト"""
        logger.info("Stage 1-A: 最小限Panda3D接続テストを開始")
        
        # ShowBase参照が正常かチェック
        if "showbase_references" not in self.enabled_features:
            logger.error("ShowBase参照が設定されていません")
            return False
        
        try:
            # 最小限のテストノードを作成
            if self.render:
                from panda3d.core import CardMaker
                test_cm = CardMaker("stage1a_test")
                test_cm.setFrame(-0.1, 0.1, -0.1, 0.1)
                test_node = self.render.attachNewNode(test_cm.generate())
                test_node.setPos(0, 0, -1)  # カメラから見えない位置
                test_node.setColor(1, 0, 0, 1)  # 赤色
                
                # テストノードをすぐに削除
                test_node.removeNode()
                logger.info("テストノードの作成・削除が成功しました")
                
                self.enabled_features.add("basic_node_operations")
                self.current_stage = "stage1a"
                logger.info("Stage 1-A完了: 基本ノード操作が利用可能")
                return True
            else:
                logger.error("renderノードが利用できません")
                return False
                
        except Exception as e:
            logger.error(f"Stage 1-A中にエラー: {e}")
            return False
    
    def _advance_to_stage1b(self) -> bool:
        """Stage 1-B: 単一床面描画テスト"""
        logger.info("Stage 1-B: 単一床面描画テストを開始")
        
        if "basic_node_operations" not in self.enabled_features:
            logger.error("基本ノード操作が有効化されていません")
            return False
        
        try:
            # 単一の床タイルを作成
            from panda3d.core import CardMaker, Vec4
            
            floor_cm = CardMaker("test_floor_0_0")
            floor_cm.setFrame(-1, 1, -1, 1)
            
            test_floor = self.render.attachNewNode(floor_cm.generate())
            test_floor.setPos(0, 0, 0)  # 原点に配置
            test_floor.setHpr(0, -90, 0)  # 水平配置
            test_floor.setColor(0.5, 0.3, 0.1, 1)  # 茶色
            test_floor.setTwoSided(True)
            
            # テスト用ノードとして保存
            self.floor_nodes["test_single"] = test_floor
            
            logger.info("単一床面の描画が成功しました")
            self.enabled_features.add("single_floor_render")
            self.current_stage = "stage1b"
            
            # カメラの基本位置設定もテスト
            if self.camera:
                self.camera.setPos(0, -3, self.camera_height)
                self.camera.setHpr(0, 0, 0)
                logger.info("カメラ基本位置を設定しました")
                self.enabled_features.add("basic_camera_setup")
            
            return True
            
        except Exception as e:
            logger.error(f"Stage 1-B中にエラー: {e}")
            return False
    
    def _advance_to_stage2a(self) -> bool:
        """Stage 2-A: 壁面描画の段階的追加"""
        logger.info("Stage 2-A: 壁面描画テストを開始")
        
        if "single_floor_render" not in self.enabled_features:
            logger.error("単一床面描画が有効化されていません")
            return False
        
        try:
            # 北壁のみを追加
            from panda3d.core import CardMaker, Vec4
            
            wall_cm = CardMaker("test_wall_north")
            wall_cm.setFrame(-1, 1, 0, 2.5)
            
            north_wall = self.render.attachNewNode(wall_cm.generate())
            north_wall.setPos(0, 1, 1.25)  # 北側に配置
            north_wall.setHpr(0, 0, 0)
            north_wall.setColor(0.6, 0.6, 0.6, 1)  # グレー
            north_wall.setTwoSided(True)
            
            self.wall_nodes["test_north"] = north_wall
            
            logger.info("北壁の描画が成功しました")
            self.enabled_features.add("single_wall_render")
            self.current_stage = "stage2a"
            return True
            
        except Exception as e:
            logger.error(f"Stage 2-A中にエラー: {e}")
            return False
    
    def _advance_to_stage2b(self) -> bool:
        """Stage 2-B: 基本ライティングと天井"""
        logger.info("Stage 2-B: 基本ライティングテストを開始")
        
        if "single_wall_render" not in self.enabled_features:
            logger.error("単一壁面描画が有効化されていません")
            return False
        
        try:
            # 基本的な環境光のみ追加
            from panda3d.core import AmbientLight, Vec4
            
            ambient_light = AmbientLight('test_ambient')
            ambient_light.setColor(Vec4(0.3, 0.3, 0.4, 1))
            ambient_light_np = self.render.attachNewNode(ambient_light)
            self.render.setLight(ambient_light_np)
            
            logger.info("基本環境光を設定しました")
            self.enabled_features.add("basic_lighting")
            
            # 天井も追加
            from panda3d.core import CardMaker
            ceiling_cm = CardMaker("test_ceiling")
            ceiling_cm.setFrame(-1, 1, -1, 1)
            
            test_ceiling = self.render.attachNewNode(ceiling_cm.generate())
            test_ceiling.setPos(0, 0, 2.5)
            test_ceiling.setHpr(0, 90, 0)
            test_ceiling.setColor(0.4, 0.4, 0.4, 1)
            test_ceiling.setTwoSided(True)
            
            self.ceiling_nodes["test_single"] = test_ceiling
            
            logger.info("天井の描画が成功しました")
            self.enabled_features.add("basic_ceiling_render")
            self.current_stage = "stage2b"
            return True
            
        except Exception as e:
            logger.error(f"Stage 2-B中にエラー: {e}")
            return False
    
    def _advance_to_stage3(self) -> bool:
        """Stage 3: 完全機能復旧"""
        logger.info("Stage 3: 完全機能復旧を開始")
        
        required_features = ["basic_lighting", "basic_ceiling_render"]
        if not all(feature in self.enabled_features for feature in required_features):
            logger.error("必要な前段階機能が不足しています")
            return False
        
        try:
            # レガシーenabledフラグを有効化
            self.enabled = True
            logger.info("レガシーenabledフラグを有効化しました")
            
            # 完全な初期化メソッドを実行
            self._initialize_camera()
            self._initialize_lighting()
            
            self.enabled_features.add("full_3d_rendering")
            self.current_stage = "stage3"
            logger.info("Stage 3完了: 完全3D描画システムが有効")
            return True
            
        except Exception as e:
            logger.error(f"Stage 3中にエラー: {e}")
            return False
    
    def emergency_disable(self):
        """緊急無効化"""
        logger.warning("緊急無効化を実行します")
        
        self.enabled = False
        self.current_stage = "disabled"
        self.enabled_features.clear()
        self._emergency_clear_all_nodes()
        
        logger.info("緊急無効化が完了しました")
    
    def manual_advance_next_stage(self) -> bool:
        """手動で次の段階に進行（ゲーム内テスト用）"""
        stage_progression = {
            "disabled": "stage1a",
            "stage1a": "stage1b", 
            "stage1b": "stage2a",
            "stage2a": "stage2b",
            "stage2b": "stage3",
            "stage3": None  # 既に最終段階
        }
        
        next_stage = stage_progression.get(self.current_stage)
        if next_stage:
            logger.info(f"手動段階進行: {self.current_stage} → {next_stage}")
            return self.advance_to_stage(next_stage)
        else:
            logger.info("既に最終段階に到達しています")
            return False
    
    def log_current_status(self):
        """現在の状態をログ出力"""
        info = self.get_stage_info()
        logger.info("=== ダンジョンレンダラー現在状態 ===")
        logger.info(f"段階: {info['current_stage']}")
        logger.info(f"有効機能: {info['enabled_features']}")
        logger.info(f"enabledフラグ: {info['enabled_flag']}")
        logger.info(f"ノード数: {info['node_counts']}")
        if info['has_errors']:
            logger.info(f"エラー: {info['errors']}")
        logger.info("========================================")


# グローバルインスタンス
dungeon_renderer = None

def create_renderer() -> Optional[DungeonRenderer]:
    """レンダラー作成"""
    global dungeon_renderer
    if not dungeon_renderer:
        dungeon_renderer = DungeonRenderer()
    return dungeon_renderer if dungeon_renderer.enabled else None