"""壁描画レンダラー"""

import pygame
from typing import Tuple

from src.rendering.renderer_config import WallRenderConfig, ColorConfig


class WallRenderer:
    """壁描画処理クラス"""
    
    def __init__(self, screen: pygame.Surface, wall_config: WallRenderConfig = None, 
                 color_config: ColorConfig = None):
        self.screen = screen
        self.wall_config = wall_config or WallRenderConfig()
        self.color_config = color_config or ColorConfig()
        self.screen_width = screen.get_width()
        self.screen_height = screen.get_height()
    
    def render_wall_column(self, ray_index: int, distance: float):
        """壁の縦線を描画"""
        wall_height = self._calculate_wall_height(distance)
        wall_top = self._calculate_wall_position(wall_height)
        wall_color = self._calculate_wall_color(distance)
        
        x = ray_index * self.wall_config.render_width
        wall_rect = pygame.Rect(x, wall_top, self.wall_config.render_width, wall_height)
        pygame.draw.rect(self.screen, wall_color, wall_rect)
    
    def render_floor_and_ceiling(self):
        """床と天井を描画"""
        # 床（下半分）
        floor_rect = pygame.Rect(0, self.screen_height // 2, 
                                self.screen_width, self.screen_height // 2)
        pygame.draw.rect(self.screen, self.color_config.floor, floor_rect)
        
        # 天井（上半分）
        ceiling_rect = pygame.Rect(0, 0, self.screen_width, self.screen_height // 2)
        pygame.draw.rect(self.screen, self.color_config.ceiling, ceiling_rect)
    
    def _calculate_wall_height(self, distance: float) -> int:
        """距離に基づいて壁の高さを計算"""
        wall_height = int(self.wall_config.height * self.wall_config.distance_scale / 
                         max(distance, self.wall_config.min_distance))
        return min(wall_height, self.screen_height)
    
    def _calculate_wall_position(self, wall_height: int) -> int:
        """壁の描画位置（上端）を計算"""
        return (self.screen_height - wall_height) // 2
    
    def _calculate_wall_color(self, distance: float) -> Tuple[int, int, int]:
        """距離に基づいて壁の色を計算"""
        brightness = max(self.wall_config.brightness_min, 
                        self.wall_config.brightness_max - distance / 10.0)  # view_distance
        return tuple(int(c * brightness) for c in self.color_config.wall)