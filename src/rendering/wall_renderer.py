"""壁描画レンダラー"""

import pygame
from typing import Tuple
from enum import Enum

from src.rendering.renderer_config import WallRenderConfig, ColorConfig


class WallType(Enum):
    """壁タイプ定義"""
    FACE = "face"
    CORNER = "corner" 
    SOLID = "solid"


class WallRenderer:
    """壁描画処理クラス"""
    
    def __init__(self, screen: pygame.Surface, wall_config: WallRenderConfig = None, 
                 color_config: ColorConfig = None):
        self.screen = screen
        self.wall_config = wall_config or WallRenderConfig()
        self.color_config = color_config or ColorConfig()
        self.screen_width = screen.get_width()
        self.screen_height = screen.get_height()
    
    def render_wall_column(self, ray_index: int, distance: float, wall_type: str = WallType.FACE.value, ray_count: int = None):
        """壁の縦線を描画"""
        # 広角補正のための距離調整
        corrected_distance = self._apply_fisheye_correction(distance, ray_index, ray_count) if ray_count else distance
        
        wall_height = self._calculate_wall_height(corrected_distance)
        wall_top = self._calculate_wall_position(wall_height)
        wall_color = self._calculate_wall_color(corrected_distance, wall_type)
        
        x = ray_index * self.wall_config.render_width
        wall_rect = pygame.Rect(x, wall_top, self.wall_config.render_width, wall_height)
        pygame.draw.rect(self.screen, wall_color, wall_rect)
    
    def render_floor_and_ceiling(self):
        """床と天井を描画"""
        # 設定から天井比率を取得
        ceiling_height = int(self.screen_height * self.wall_config.ceiling_ratio)
        floor_height = self.screen_height - ceiling_height
        
        # 床（下部）
        floor_rect = pygame.Rect(0, ceiling_height, self.screen_width, floor_height)
        pygame.draw.rect(self.screen, self.color_config.floor, floor_rect)
        
        # 天井（上部）
        ceiling_rect = pygame.Rect(0, 0, self.screen_width, ceiling_height)
        pygame.draw.rect(self.screen, self.color_config.ceiling, ceiling_rect)
    
    def _calculate_wall_height(self, distance: float) -> int:
        """距離に基づいて壁の高さを計算"""
        wall_height = int(self.wall_config.height * self.wall_config.distance_scale / 
                         max(distance, self.wall_config.min_distance))
        return min(wall_height, self.screen_height)
    
    def _calculate_wall_position(self, wall_height: int) -> int:
        """壁の描画位置（上端）を計算"""
        # 設定から天井比率と壁位置比率を取得
        ceiling_height = int(self.screen_height * self.wall_config.ceiling_ratio)
        available_height = self.screen_height - ceiling_height
        
        # 設定から壁の位置比率を取得
        wall_center = ceiling_height + int(available_height * self.wall_config.wall_position_ratio)
        return wall_center - (wall_height // 2)
    
    def _calculate_wall_color(self, distance: float, wall_type: str = WallType.FACE.value) -> Tuple[int, int, int]:
        """距離と壁タイプに基づいて壁の色を計算"""
        brightness = self._calculate_brightness(distance)
        base_color = self._get_base_color_for_wall_type(wall_type)
        return tuple(int(c * brightness) for c in base_color)
    
    def _calculate_brightness(self, distance: float) -> float:
        """距離に基づいて明度を計算"""
        return max(self.wall_config.brightness_min, 
                  self.wall_config.brightness_max - distance / self.wall_config.view_distance)
    
    def _get_base_color_for_wall_type(self, wall_type: str) -> Tuple[int, int, int]:
        """壁タイプに基づいて基本色を取得"""
        if wall_type == WallType.CORNER.value:
            multiplier = self.wall_config.corner_brightness_multiplier
            return tuple(min(255, int(c * multiplier)) for c in self.color_config.wall)
        elif wall_type == WallType.SOLID.value:
            multiplier = self.wall_config.solid_wall_brightness_multiplier
            return tuple(int(c * multiplier) for c in self.color_config.wall)
        else:  # WallType.FACE.value
            return self.color_config.wall
    
    def _apply_fisheye_correction(self, distance: float, ray_index: int, ray_count: int) -> float:
        """魚眼効果補正を適用"""
        if not ray_count:
            return distance
        
        # 中央からの角度を計算
        center = ray_count // 2
        angle_from_center = abs(ray_index - center) / center
        
        # 設定から補正係数を取得
        correction_factor = 1.0 / (1.0 + angle_from_center * self.wall_config.fisheye_correction_factor)
        
        return distance * correction_factor