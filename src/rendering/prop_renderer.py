"""プロップ描画レンダラー"""

import math
import pygame
from typing import Dict, Any, Optional

from src.dungeon.dungeon_manager import PlayerPosition
from src.dungeon.dungeon_generator import DungeonLevel, CellType
from src.rendering.renderer_config import PropRenderConfig, ColorConfig
from src.rendering.camera import Camera


class PropRenderer:
    """プロップ（階段、宝箱など）描画処理クラス"""
    
    def __init__(self, screen: pygame.Surface, prop_config: Optional[PropRenderConfig] = None, 
                 color_config: Optional[ColorConfig] = None):
        self.screen = screen
        self.prop_config = prop_config if prop_config is not None else PropRenderConfig()
        self.color_config = color_config if color_config is not None else ColorConfig()
        self.screen_width = screen.get_width()
        self.screen_height = screen.get_height()
    
    def render_props_3d(self, level: DungeonLevel, player_pos: PlayerPosition, camera: Camera):
        """3Dプロップを描画"""
        for x in range(max(0, player_pos.x - self.prop_config.visibility_range),
                      min(level.width, player_pos.x + self.prop_config.visibility_range + 1)):
            for y in range(max(0, player_pos.y - self.prop_config.visibility_range),
                          min(level.height, player_pos.y + self.prop_config.visibility_range + 1)):
                
                cell = level.get_cell(x, y)
                if not cell:
                    continue
                
                # プロップの位置情報を計算
                prop_info = self._calculate_prop_position(x, y, player_pos, camera)
                
                if not prop_info['visible']:
                    continue
                
                screen_x = prop_info['screen_x']
                distance = prop_info['distance']
                
                # プレイヤーが現在位置にいるかどうかをチェック
                is_player_on_cell = (x == player_pos.x and y == player_pos.y)
                
                # プロップを描画
                if cell.cell_type == CellType.STAIRS_UP:
                    self._draw_stairs(screen_x, distance, True, is_player_on_cell)
                elif cell.cell_type == CellType.STAIRS_DOWN:
                    self._draw_stairs(screen_x, distance, False, is_player_on_cell)
                elif cell.cell_type == CellType.EXIT:
                    self._draw_exit(screen_x, distance, is_player_on_cell)
                
                if cell.has_treasure:
                    self._draw_treasure(screen_x, distance)
    
    def _calculate_prop_position(self, x: int, y: int, player_pos: PlayerPosition, 
                                camera: Camera) -> Dict[str, Any]:
        """プロップの画面位置情報を計算"""
        dx = x - player_pos.x
        dy = y - player_pos.y
        distance = math.sqrt(dx * dx + dy * dy)
        
        if distance > self.prop_config.visibility_range:
            return {'visible': False}
        
        angle_to_prop = math.atan2(dy, dx)
        relative_angle = angle_to_prop - camera.get_angle()
        
        # FOVを75度と仮定（設定から取得すべき）
        fov_rad = 75 * math.pi / 180
        if abs(relative_angle) > fov_rad / 2:
            return {'visible': False}
        
        screen_x = int(self.screen_width / 2 + 
                      (relative_angle / (fov_rad / 2)) * (self.screen_width / 2))
        
        return {
            'visible': True,
            'screen_x': screen_x,
            'distance': distance
        }
    
    def _draw_stairs(self, screen_x: int, distance: float, is_up: bool, is_player_on: bool = False):
        """階段を描画"""
        if distance > 10.0:  # view_distance
            return
        
        size = self._calculate_prop_size(distance, self.prop_config.stairs_base_size)
        base_color = self.color_config.stairs_up if is_up else self.color_config.stairs_down
        
        # プレイヤーが階段の上にいる場合、色を強調
        if is_player_on:
            # 点滅効果のための時間ベース計算
            import time
            flash_intensity = int(abs(math.sin(time.time() * 5)) * 100) + 155  # 155-255の範囲で点滅
            highlight_color = (min(255, base_color[0] + flash_intensity // 2),
                             min(255, base_color[1] + flash_intensity // 2), 
                             min(255, base_color[2] + flash_intensity // 2))
            color = highlight_color
        else:
            color = base_color
        
        stairs_rect = self._create_centered_rect(screen_x, size)
        pygame.draw.rect(self.screen, color, stairs_rect)
        
        # プレイヤーが上にいる場合、枠線を追加
        if is_player_on:
            pygame.draw.rect(self.screen, (255, 255, 255), stairs_rect, 3)
        
        self._draw_stairs_arrow(screen_x, stairs_rect, size, is_up)
    
    def _draw_treasure(self, screen_x: int, distance: float):
        """宝箱を描画"""
        if distance > 10.0:  # view_distance
            return
        
        size = self._calculate_prop_size(distance, self.prop_config.treasure_base_size)
        
        treasure_rect = self._create_centered_rect(screen_x, size)
        pygame.draw.rect(self.screen, self.color_config.treasure, treasure_rect)
        pygame.draw.rect(self.screen, self.color_config.treasure_detail, treasure_rect, 1)
    
    def _draw_exit(self, screen_x: int, distance: float, is_player_on: bool = False):
        """地上への出口を描画"""
        if distance > 10.0:  # view_distance
            return
        
        size = self._calculate_prop_size(distance, self.prop_config.stairs_base_size)
        
        # プレイヤーが出口の上にいる場合、光の強度を増す
        if is_player_on:
            import time
            flash_intensity = int(abs(math.sin(time.time() * 4)) * 50) + 50  # より強い光
            base_brightness = 255
            bright_yellow = (255, 255, min(255, 200 + flash_intensity))
            bright_gold = (255, min(255, 215 + flash_intensity), 0)
            bright_white = (255, 255, 255)
        else:
            bright_yellow = (255, 255, 200)
            bright_gold = (255, 215, 0)
            bright_white = (255, 255, 255)
        
        # 出口の外枠を描画（明るい色で目立たせる）
        exit_rect = self._create_centered_rect(screen_x, size)
        pygame.draw.rect(self.screen, bright_yellow, exit_rect)  # 明るい黄色
        
        # プレイヤーが上にいる場合、外枠を太くする
        border_width = 4 if is_player_on else 2
        pygame.draw.rect(self.screen, bright_gold, exit_rect, border_width)  # ゴールドの枠
        
        # 出口の光を表現（内側に光のグラデーション効果）
        inner_rect = exit_rect.inflate(-size//4, -size//4)
        pygame.draw.rect(self.screen, bright_white, inner_rect)
        
        # 太陽のシンボルを描画（出口を示す）
        center_x = exit_rect.centerx
        center_y = exit_rect.centery
        radius = size // 6
        pygame.draw.circle(self.screen, bright_gold, (center_x, center_y), radius)
        
        # 光線を描画（プレイヤーが上にいる場合はより多くの光線）
        angle_step = 30 if is_player_on else 45
        line_width = 3 if is_player_on else 2
        for angle in range(0, 360, angle_step):
            rad = angle * math.pi / 180
            start_x = center_x + radius * math.cos(rad)
            start_y = center_y + radius * math.sin(rad)
            end_x = center_x + (radius * 2) * math.cos(rad)
            end_y = center_y + (radius * 2) * math.sin(rad)
            pygame.draw.line(self.screen, bright_gold, 
                           (int(start_x), int(start_y)), 
                           (int(end_x), int(end_y)), line_width)
    
    def _calculate_prop_size(self, distance: float, base_size: int) -> int:
        """距離に基づいてプロップのサイズを計算"""
        return max(self.prop_config.min_size, 
                  int(base_size / max(distance, self.prop_config.size_divisor)))
    
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
            pygame.draw.polygon(self.screen, self.color_config.white, [
                (screen_x, stairs_rect.top),
                (screen_x - size // 4, stairs_rect.bottom - 2),
                (screen_x + size // 4, stairs_rect.bottom - 2)
            ])
        else:
            pygame.draw.polygon(self.screen, self.color_config.white, [
                (screen_x, stairs_rect.bottom),
                (screen_x - size // 4, stairs_rect.top + 2),
                (screen_x + size // 4, stairs_rect.top + 2)
            ])