"""方向管理ヘルパー"""

from src.dungeon.dungeon_generator import Direction


class DirectionHelper:
    """方向変換のヘルパークラス"""
    
    @staticmethod
    def get_opposite_direction(direction: Direction) -> Direction:
        """反対方向を取得"""
        opposite_map = {
            Direction.NORTH: Direction.SOUTH,
            Direction.SOUTH: Direction.NORTH,
            Direction.EAST: Direction.WEST,
            Direction.WEST: Direction.EAST
        }
        return opposite_map[direction]
    
    @staticmethod
    def get_left_direction(direction: Direction) -> Direction:
        """左方向を取得"""
        left_map = {
            Direction.NORTH: Direction.WEST,
            Direction.EAST: Direction.NORTH,
            Direction.SOUTH: Direction.EAST,
            Direction.WEST: Direction.SOUTH
        }
        return left_map[direction]
    
    @staticmethod
    def get_right_direction(direction: Direction) -> Direction:
        """右方向を取得"""
        right_map = {
            Direction.NORTH: Direction.EAST,
            Direction.EAST: Direction.SOUTH,
            Direction.SOUTH: Direction.WEST,
            Direction.WEST: Direction.NORTH
        }
        return right_map[direction]