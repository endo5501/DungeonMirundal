"""ダンジョンレンダリング用カメラシステム"""

import math
from dataclasses import dataclass
from typing import Tuple

from src.dungeon.dungeon_manager import PlayerPosition
from src.dungeon.dungeon_generator import Direction
from src.rendering.renderer_config import DirectionConfig
from src.utils.logger import logger


@dataclass
class CameraState:
    """カメラの状態"""
    x: float = 0.0
    y: float = 0.0
    angle: float = 0.0  # ラジアン
    
    @property
    def angle_degrees(self) -> float:
        return math.degrees(self.angle)


class Camera:
    """ダンジョン探索用カメラ"""
    
    def __init__(self, direction_config: DirectionConfig = None):
        self.direction_config = direction_config or DirectionConfig()
        self.state = CameraState()
        
        # 方向マッピング
        self._direction_angles = {
            Direction.NORTH: self.direction_config.angle_north,
            Direction.EAST: self.direction_config.angle_east,
            Direction.SOUTH: self.direction_config.angle_south,
            Direction.WEST: self.direction_config.angle_west
        }
    
    def update_from_player(self, player_pos: PlayerPosition):
        """プレイヤー位置からカメラを更新"""
        self.state.x = player_pos.x
        self.state.y = player_pos.y
        self.state.angle = self._direction_angles.get(player_pos.facing, 0)
        
        logger.debug(f"カメラ位置更新: ({self.state.x}, {self.state.y}) 角度: {self.state.angle_degrees:.1f}°")
    
    def get_position(self) -> Tuple[float, float]:
        """カメラ位置を取得"""
        return (self.state.x, self.state.y)
    
    def get_angle(self) -> float:
        """カメラ角度を取得"""
        return self.state.angle
    
    def get_ray_start_position(self, player_pos: PlayerPosition) -> Tuple[float, float]:
        """レイキャスティングの開始位置を取得"""
        # プレイヤーをセルの中央に配置してレイキャスティングを開始
        return (float(player_pos.x) + 0.5, float(player_pos.y) + 0.5)
    
    def calculate_ray_angle(self, ray_index: int, ray_count: int, fov_radians: float) -> float:
        """レイの角度を計算"""
        return self.state.angle + (ray_index - ray_count // 2) * fov_radians / ray_count