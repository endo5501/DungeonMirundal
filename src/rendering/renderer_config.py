"""ダンジョンレンダラーの設定"""

import math
from dataclasses import dataclass
from typing import Tuple


@dataclass
class ScreenConfig:
    """画面設定"""
    width: int = 1024
    height: int = 768
    
    @property
    def size(self) -> Tuple[int, int]:
        return (self.width, self.height)


@dataclass
class CameraConfig:
    """カメラ設定"""
    fov: float = 90  # 75度から90度に拡大して横方向の視野を広げる
    view_distance: float = 10.0
    
    @property
    def fov_radians(self) -> float:
        return self.fov * math.pi / 180


@dataclass
class RaycastConfig:
    """レイキャスティング設定"""
    step_size: float = 0.05  # より細かいステップで滑らかに
    resolution_divisor: int = 1  # 解像度を上げて滑らかに
    wall_collision_threshold: float = 0.05
    
    def calculate_ray_count(self, screen_width: int) -> int:
        return screen_width // self.resolution_divisor


@dataclass
class WallRenderConfig:
    """壁描画設定"""
    height: int = 64
    distance_scale: float = 50.0
    render_width: int = 1  # 滑らかな描画のため幅を1に
    min_height: int = 1
    min_distance: float = 0.5
    brightness_min: float = 0.3
    brightness_max: float = 1.0


@dataclass
class PropRenderConfig:
    """プロップ描画設定"""
    visibility_range: int = 5
    stairs_base_size: int = 20
    treasure_base_size: int = 15
    min_size: int = 4
    size_divisor: float = 0.5


@dataclass
class UIConfig:
    """UI設定"""
    margin: int = 10
    bottom_margin: int = 30
    compass_x_offset: int = 60
    compass_y_offset: int = 20
    position_text_x: int = 10
    position_text_y: int = 10
    help_text_x: int = 10
    help_text_y_offset: int = 30
    font_size_small: int = 18
    font_size_medium: int = 24
    font_size_large: int = 36


@dataclass
class ColorConfig:
    """色設定"""
    black: Tuple[int, int, int] = (0, 0, 0)
    white: Tuple[int, int, int] = (255, 255, 255)
    gray: Tuple[int, int, int] = (128, 128, 128)
    dark_gray: Tuple[int, int, int] = (64, 64, 64)
    floor: Tuple[int, int, int] = (101, 67, 33)
    ceiling: Tuple[int, int, int] = (51, 51, 51)
    wall: Tuple[int, int, int] = (102, 102, 102)
    stairs_up: Tuple[int, int, int] = (200, 200, 150)
    stairs_down: Tuple[int, int, int] = (150, 150, 200)
    treasure: Tuple[int, int, int] = (255, 215, 0)
    treasure_detail: Tuple[int, int, int] = (200, 180, 0)


@dataclass
class DirectionConfig:
    """方向設定"""
    angle_north: float = -math.pi/2
    angle_east: float = 0
    angle_south: float = math.pi/2
    angle_west: float = math.pi


@dataclass
class RendererConfig:
    """レンダラー統合設定"""
    screen: ScreenConfig = None
    camera: CameraConfig = None
    raycast: RaycastConfig = None
    wall_render: WallRenderConfig = None
    prop_render: PropRenderConfig = None
    ui: UIConfig = None
    colors: ColorConfig = None
    directions: DirectionConfig = None
    
    def __post_init__(self):
        if self.screen is None:
            self.screen = ScreenConfig()
        if self.camera is None:
            self.camera = CameraConfig()
        if self.raycast is None:
            self.raycast = RaycastConfig()
        if self.wall_render is None:
            self.wall_render = WallRenderConfig()
        if self.prop_render is None:
            self.prop_render = PropRenderConfig()
        if self.ui is None:
            self.ui = UIConfig()
        if self.colors is None:
            self.colors = ColorConfig()
        if self.directions is None:
            self.directions = DirectionConfig()