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
    
    def render_wall_column(self, ray_index: int, distance: float, wall_type: str = "face", ray_count: int = None):
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
        # 視線を下向きに調整（天井30%、床70%で地面がより見やすく）
        ceiling_height = int(self.screen_height * 0.3)
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
        # 視線を下向きに調整：壁を上寄りに配置して床がより見えるようにする
        ceiling_height = int(self.screen_height * 0.3)
        available_height = self.screen_height - ceiling_height
        
        # 壁の中心を上寄りに調整（available_heightの25%の位置に配置）
        # これにより視線がより下向きになり、床がよく見える
        wall_center = ceiling_height + int(available_height * 0.25)
        return wall_center - (wall_height // 2)
    
    def _calculate_wall_color(self, distance: float, wall_type: str = "face") -> Tuple[int, int, int]:
        """距離と壁タイプに基づいて壁の色を計算"""
        brightness = max(self.wall_config.brightness_min, 
                        self.wall_config.brightness_max - distance / 10.0)  # view_distance
        
        # 壁タイプに応じて基本色を変更
        if wall_type == "corner":
            # 角部分はより明るく（視認性向上）
            base_color = tuple(min(255, int(c * 1.3)) for c in self.color_config.wall)
        elif wall_type == "solid":
            # ソリッドウォールは少し暗く
            base_color = tuple(int(c * 0.8) for c in self.color_config.wall)
        else:  # "face"
            base_color = self.color_config.wall
        
        return tuple(int(c * brightness) for c in base_color)
    
    def _apply_fisheye_correction(self, distance: float, ray_index: int, ray_count: int) -> float:
        """魚眼効果補正を適用"""
        if not ray_count:
            return distance
        
        # 中央からの角度を計算
        center = ray_count // 2
        angle_from_center = abs(ray_index - center) / center
        
        # コサイン補正でエッジでの歪みを軽減
        correction_factor = 1.0 / (1.0 + angle_from_center * 0.3)
        
        return distance * correction_factor