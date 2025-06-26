"""レイキャスティングエンジン"""

import math
from typing import Tuple, Optional

from src.dungeon.dungeon_manager import PlayerPosition
from src.dungeon.dungeon_generator import DungeonLevel, DungeonCell, CellType, Direction
from src.rendering.renderer_config import RaycastConfig
from src.rendering.wall_renderer import WallType


class RaycastEngine:
    """レイキャスティング処理エンジン"""
    
    def __init__(self, config: RaycastConfig = None):
        self.config = config or RaycastConfig()
    
    def cast_ray(self, level: DungeonLevel, player_pos: PlayerPosition,  # noqa: ARG002
                 ray_start: Tuple[float, float], angle: float) -> Tuple[float, bool, Optional[str]]:
        """レイキャスティング実行"""
        # レイの方向ベクトル
        dx = math.cos(angle)
        dy = math.sin(angle)
        
        # レイの開始位置
        ray_x, ray_y = ray_start
        distance = 0.0
        
        while distance < self.config.view_distance:
            ray_x, ray_y, distance = self._advance_ray(ray_x, ray_y, dx, dy, distance)
            
            if self._is_ray_out_of_bounds(ray_x, ray_y, level):
                return distance, True, None
            
            grid_x, grid_y = int(ray_x), int(ray_y)
            cell = level.get_cell(grid_x, grid_y)
            
            wall_type = self._get_wall_hit_type(cell, ray_x - grid_x, ray_y - grid_y)
            if wall_type:
                return distance, True, wall_type
        
        return self.config.view_distance, False, None
    
    def _advance_ray(self, ray_x: float, ray_y: float, dx: float, dy: float, distance: float) -> Tuple[float, float, float]:
        """レイを前進させる"""
        ray_x += dx * self.config.step_size
        ray_y += dy * self.config.step_size
        distance += self.config.step_size
        return ray_x, ray_y, distance
    
    def _is_ray_out_of_bounds(self, ray_x: float, ray_y: float, level: DungeonLevel) -> bool:
        """レイが範囲外かチェック"""
        return ray_x < 0 or ray_x >= level.width or ray_y < 0 or ray_y >= level.height
    
    def _get_wall_hit_type(self, cell: Optional[DungeonCell], local_x: float, local_y: float) -> Optional[str]:
        """壁にヒットした場合の壁タイプを取得"""
        if not cell or cell.cell_type == CellType.WALL:
            return WallType.SOLID.value
        return self._check_wall_collision_type(cell, local_x, local_y)
    
    def _check_wall_collision_type(self, cell: DungeonCell, local_x: float, local_y: float) -> Optional[str]:
        """セル内での壁との衝突をチェックし、壁タイプを返す"""
        threshold = self.config.wall_collision_threshold
        
        # 設定から角検出の閾値倍率を取得
        corner_threshold = threshold * self.config.corner_threshold_multiplier
        
        # 角の判定
        if ((local_x <= corner_threshold or local_x >= (1.0 - corner_threshold)) and 
            (local_y <= corner_threshold or local_y >= (1.0 - corner_threshold))):
            # 実際に角に壁があるかチェック
            if ((local_x <= corner_threshold and cell.walls.get(Direction.WEST, False)) or
                (local_x >= (1.0 - corner_threshold) and cell.walls.get(Direction.EAST, False)) or
                (local_y <= corner_threshold and cell.walls.get(Direction.NORTH, False)) or
                (local_y >= (1.0 - corner_threshold) and cell.walls.get(Direction.SOUTH, False))):
                return WallType.CORNER.value
        
        # 通常の壁面チェック
        if local_x <= threshold and cell.walls.get(Direction.WEST, False):
            return WallType.FACE.value
        if local_x >= (1.0 - threshold) and cell.walls.get(Direction.EAST, False):
            return WallType.FACE.value
        if local_y <= threshold and cell.walls.get(Direction.NORTH, False):
            return WallType.FACE.value
        if local_y >= (1.0 - threshold) and cell.walls.get(Direction.SOUTH, False):
            return WallType.FACE.value
        
        return None