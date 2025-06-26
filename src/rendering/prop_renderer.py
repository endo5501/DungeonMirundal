"""プロップ描画レンダラー"""

import math
import pygame
from typing import Dict, Any

from src.dungeon.dungeon_manager import PlayerPosition
from src.dungeon.dungeon_generator import DungeonLevel, CellType
from src.rendering.renderer_config import PropRenderConfig, ColorConfig
from src.rendering.camera import Camera


class PropRenderer:
    """プロップ（階段、宝箱など）描画処理クラス"""
    
    def __init__(self, screen: pygame.Surface, prop_config: PropRenderConfig = None, 
                 color_config: ColorConfig = None):
        self.screen = screen
        self.prop_config = prop_config or PropRenderConfig()
        self.color_config = color_config or ColorConfig()
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
                
                # プロップを描画
                if cell.cell_type == CellType.STAIRS_UP:
                    self._draw_stairs(screen_x, distance, True)
                elif cell.cell_type == CellType.STAIRS_DOWN:
                    self._draw_stairs(screen_x, distance, False)
                
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
    
    def _draw_stairs(self, screen_x: int, distance: float, is_up: bool):
        """階段を描画"""
        if distance > 10.0:  # view_distance
            return
        
        size = self._calculate_prop_size(distance, self.prop_config.stairs_base_size)
        color = self.color_config.stairs_up if is_up else self.color_config.stairs_down
        
        stairs_rect = self._create_centered_rect(screen_x, size)
        pygame.draw.rect(self.screen, color, stairs_rect)
        
        self._draw_stairs_arrow(screen_x, stairs_rect, size, is_up)
    
    def _draw_treasure(self, screen_x: int, distance: float):
        """宝箱を描画"""
        if distance > 10.0:  # view_distance
            return
        
        size = self._calculate_prop_size(distance, self.prop_config.treasure_base_size)
        
        treasure_rect = self._create_centered_rect(screen_x, size)
        pygame.draw.rect(self.screen, self.color_config.treasure, treasure_rect)
        pygame.draw.rect(self.screen, self.color_config.treasure_detail, treasure_rect, 1)
    
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