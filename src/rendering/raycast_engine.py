"""レイキャスティングエンジン"""

import math
from typing import Tuple, Optional

from src.dungeon.dungeon_manager import PlayerPosition
from src.dungeon.dungeon_generator import DungeonLevel, DungeonCell, CellType, Direction
from src.rendering.renderer_config import RaycastConfig
from src.rendering.camera import Camera


class RaycastEngine:
    """レイキャスティング処理エンジン"""
    
    def __init__(self, config: RaycastConfig = None):
        self.config = config or RaycastConfig()
    
    def cast_ray(self, level: DungeonLevel, player_pos: PlayerPosition, 
                 ray_start: Tuple[float, float], angle: float) -> Tuple[float, bool]:
        """レイキャスティング実行"""
        # レイの方向ベクトル
        dx = math.cos(angle)
        dy = math.sin(angle)
        
        # レイの開始位置
        ray_x, ray_y = ray_start
        distance = 0.0
        
        while distance < 10.0:  # view_distance
            ray_x, ray_y, distance = self._advance_ray(ray_x, ray_y, dx, dy, distance)
            
            if self._is_ray_out_of_bounds(ray_x, ray_y, level):
                return distance, True
            
            grid_x, grid_y = int(ray_x), int(ray_y)
            cell = level.get_cell(grid_x, grid_y)
            
            if self._is_wall_hit(cell, ray_x - grid_x, ray_y - grid_y):
                return distance, True
        
        return 10.0, False  # view_distance
    
    def _advance_ray(self, ray_x: float, ray_y: float, dx: float, dy: float, distance: float) -> Tuple[float, float, float]:
        """レイを前進させる"""
        ray_x += dx * self.config.step_size
        ray_y += dy * self.config.step_size
        distance += self.config.step_size
        return ray_x, ray_y, distance
    
    def _is_ray_out_of_bounds(self, ray_x: float, ray_y: float, level: DungeonLevel) -> bool:
        """レイが範囲外かチェック"""
        return ray_x < 0 or ray_x >= level.width or ray_y < 0 or ray_y >= level.height
    
    def _is_wall_hit(self, cell: Optional[DungeonCell], local_x: float, local_y: float) -> bool:
        """壁にヒットしたかチェック"""
        if not cell or cell.cell_type == CellType.WALL:
            return True
        return self._check_wall_collision(cell, local_x, local_y)
    
    def _check_wall_collision(self, cell: DungeonCell, local_x: float, local_y: float) -> bool:
        """セル内での壁との衝突をチェック"""
        threshold = self.config.wall_collision_threshold
        
        # 各方向の壁をチェック
        if local_x <= threshold and cell.walls.get(Direction.WEST, False):
            return True
        if local_x >= (1.0 - threshold) and cell.walls.get(Direction.EAST, False):
            return True
        if local_y <= threshold and cell.walls.get(Direction.NORTH, False):
            return True
        if local_y >= (1.0 - threshold) and cell.walls.get(Direction.SOUTH, False):
            return True
        
        return False